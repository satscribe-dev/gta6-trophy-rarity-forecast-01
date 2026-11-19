"""gta6-trophy-rarity-forecast-01: forecast Exophase earn rates for GTA VI (PS5).

Approach (written from scratch for this competition):
  * Collapse the case history into distinct Exophase snapshots (consecutive
    identical reads are one refresh state, not new information).
  * Work in logit space against u = ln(1 + hours since 2026-11-19T00:00Z).
    Per trophy, a recency-weighted least-squares line of logit(rate) on u,
    slope shrunk toward the pooled slope across trophies; extrapolate the
    line to the target, with the total move capped.
  * If history holds a single distinct snapshot (flat page, no refresh seen
    yet), fall back to a dilution model: Exophase's tracked-player count
    grows roughly like (1 + t), so while no new earners are observed the
    rate is expected to fall by the tracked-count growth factor; spread is
    widened because the next refresh is unseen.
  * Quantiles are the median plus/minus normal z-scores times a predictive
    spread built from fit residual, slope uncertainty, refresh jump size
    and small-count noise -- an honest spread, since pinball loss is a
    proper scoring rule.

Python 3.13, standard library only. Deterministic: no randomness, no clock.
Reads every *.in in $MAKEFUN_INPUT_DIR (else /input), writes one *.out per
case to $MAKEFUN_OUTPUT_DIR (else /output).
"""

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0, 0.674, 1.645]

# Launch origin: 2026-11-19T00:00:00Z (the house curve baseline's origin too).
LAUNCH0 = datetime(2026, 11, 19, 0, 0, 0, tzinfo=timezone.utc)

# --- tunables (calibrated on the launch-night -> 19 Nov 15:12Z live snapshot;
#     see research notes; the final history is rich, so these are priors) ---
HALFLIFE_H = 8.0       # recency half-life for the per-trophy line fit: in launch
                       # week the regime turns fast, so the last ~day dominates
SLOPE_PRIOR_SD = 0.40  # logit per unit u: shrinkage strength toward pooled slope
SOFT_CAP_M = 2.0       # soft cap on the extrapolated move: rates saturate
                       # (a line in u does not), so compress large moves
MAX_MOVE_UP = 3.0      # cap on upward |logit move| from last rate
MAX_MOVE_DOWN = 1.6    # cap on downward move: the launch-night dilution
                       # (-2.9 logit in 15 h) was a one-off N explosion; from
                       # day 2 to day 7, N growth slows while earners only
                       # accumulate, so a further fall past -1.6 is unlikely
DAMP_U = 1.5           # beyond this extrapolation in u, damp the move
SLOPE_SE_2PT = 0.60    # default slope s.e. when only 2 snapshots exist
                       # (line is exact through 2 points, so its uncertainty
                       # is unknown, not infinite: keep per-trophy signal)
RESID_FLOOR = 0.15     # floor on per-trophy residual sd (logit)
RESID_CAP = 0.80
SPREAD_FLOOR = 0.45    # floor on total predictive spread (logit)
SPREAD_CAP = 2.20
FLAT_SPREAD = 0.60     # spread when history is a single snapshot
LOGIT_MIN = -9.21      # logit(0.01%)
LOGIT_MAX = 9.21       # logit(99.99%)


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def logit(pct):
    p = clamp(pct, 0.01, 99.99) / 100.0
    return math.log(p / (1.0 - p))


def inv_logit(lg):
    lg = clamp(lg, LOGIT_MIN, LOGIT_MAX)
    return 100.0 / (1.0 + math.exp(-lg))


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def hours_since_launch(dt):
    return (dt - LAUNCH0).total_seconds() / 3600.0


def round4(x):
    scaled = x * 10000
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 10000
    return int(value) if float(value).is_integer() else value


def distinct_snapshots(case):
    """Collapse history into distinct Exophase states.

    Returns list of (t_hours, players_tracked, rates_tuple), one per run of
    identical rates, stamped at the FIRST read of the run (when the state
    first appeared). t is clamped >= 0 (reads just before launch count as 0).
    """
    snaps = []
    prev = None
    for read in case["history"]:
        rates = tuple(read["rates"])
        if rates == prev:
            continue
        prev = rates
        t = max(0.0, hours_since_launch(parse_time(read["at"])))
        snaps.append((t, read.get("players_tracked"), rates))
    return snaps


def wls_line(xs, ys, ws):
    """Weighted least squares y = a + b*x. Returns (a, b, y_wmean, x_wmean,
    resid_sd, se_b). Falls back to flat line when x has no spread."""
    sw = sum(ws)
    xm = sum(w * x for w, x in zip(ws, xs)) / sw
    ym = sum(w * y for w, y in zip(ws, ys)) / sw
    sxx = sum(w * (x - xm) ** 2 for w, x in zip(ws, xs))
    if sxx <= 1e-12:
        return ym, 0.0, ym, xm, 0.0, 1e9
    sxy = sum(w * (x - xm) * (y - ym) for w, x, y in zip(ws, xs, ys))
    b = sxy / sxx
    a = ym - b * xm
    n = len(xs)
    if n > 2:
        sse = sum(w * (y - (a + b * x)) ** 2 for w, x, y in zip(ws, xs, ys))
        dof = max(n - 2, 1)
        resid = math.sqrt(sse / (sw * dof / n)) if sw > 0 else 0.0
    else:
        resid = 0.0
    if n == 2:
        se_b = SLOPE_SE_2PT
    else:
        se_b = resid / math.sqrt(sxx) if resid > 0 and sxx > 0 else 1e9
    return a, b, ym, xm, resid, se_b


def median(values):
    v = sorted(values)
    n = len(v)
    if n == 0:
        return 0.0
    return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])


def forecast_case(case):
    trophies = case["trophies"]
    n_tr = len(trophies)
    target_t = max(0.0, hours_since_launch(parse_time(case["target"])))
    u_target = math.log1p(target_t)
    horizon_days = case["horizon_minutes"] / 1440.0
    snaps = distinct_snapshots(case)
    last_rates = list(snaps[-1][2]) if snaps else [None] * n_tr

    rows = []
    if len(snaps) < 2:
        # --- flat history: dilution model ---------------------------------
        # The page has not refreshed since t_snap; the tracked-player count
        # grows roughly like (1 + t), so with no new earners observed the
        # rate is expected to fall by that growth factor over the horizon.
        t_snap = snaps[0][0] if snaps else 0.0
        growth = math.log1p(target_t) - math.log1p(t_snap)
        # pure dilution; cap it: over a long horizon earners grow too, and
        # the largest dilution ever observed (launch night) was ~-3.2 logit
        shift = max(-growth, -3.5)  # ln(rate ratio) under pure dilution
        spread = max(FLAT_SPREAD, 0.5 * math.sqrt(horizon_days))
        for i, tr in enumerate(trophies):
            r = last_rates[i]
            if r is None:
                r = 0.5
            if r >= 99.5:
                med = 99.9  # (near-)everyone already has it; it stays earned
            else:
                med = inv_logit(logit(r) + shift)
            q = [round4(clamp(inv_logit(logit(med) + z * spread), 0.0, 100.0))
                 for z in Z]
            rows.append({"id": tr["id"], "q": q})
        return {"trophies": rows}

    # --- rich history: per-trophy line in u, shrunk toward pooled slope --
    t_last = snaps[-1][0]
    # refresh jump size: pooled median |logit change| between snapshots.
    # Use recent jumps only (last 36 h): the launch-night explosion jump is
    # stale information for the spread at the deadline.
    jumps = []
    for k in range(1, len(snaps)):
        if snaps[k][0] < t_last - 36.0 and len(snaps) > 3:
            continue
        for i in range(n_tr):
            r0, r1 = snaps[k - 1][2][i], snaps[k][2][i]
            if r0 is not None and r1 is not None:
                jumps.append(abs(logit(r1) - logit(r0)))
    jump = median(jumps) if jumps else 0.30

    fits = []  # per trophy: (b, se_b, resid, y_last, u_wmean, y_wmean, npts, u_range)
    slopes = []
    for i in range(n_tr):
        xs, ys, ws = [], [], []
        for (t, _n, rates) in snaps:
            r = rates[i]
            if r is None:
                continue
            xs.append(math.log1p(t))
            ys.append(logit(r))
            ws.append(0.5 ** ((t_last - t) / HALFLIFE_H))
        if len(xs) >= 2:
            a, b, ym, xm, resid, se_b = wls_line(xs, ys, ws)
            urange = max(xs) - min(xs)
            fits.append((b, se_b, resid, ys[-1], xm, ym, len(xs), urange))
            if urange > 0.05:
                slopes.append(b)
        else:
            fits.append(None)
    pooled_slope = median(slopes) if slopes else 0.0
    pooled_resid = median([f[2] for f in fits if f and f[2] > 0]) if any(
        f and f[2] > 0 for f in fits) else 0.30

    for i, tr in enumerate(trophies):
        r_last = last_rates[i]
        if r_last is None:
            # trophy never seen: fall back to a low rate with a wide spread
            med_logit, spread = logit(0.05), SPREAD_CAP
            q = [round4(clamp(inv_logit(med_logit + z * spread), 0.0, 100.0))
                 for z in Z]
            rows.append({"id": tr["id"], "q": q})
            continue
        y_last = logit(r_last)
        f = fits[i]
        if f is None:
            # single point for this trophy: persistence + refresh-sized spread
            med_logit, spread = y_last, max(0.7, jump)
        else:
            b, se_b, resid, _y, xm, ym, npts, urange = f
            # precision-weighted shrinkage of the slope toward the pooled one
            if se_b < 1e8:
                w_self = 1.0 / (se_b * se_b)
            else:
                w_self = 0.0
            w_pool = 1.0 / (SLOPE_PRIOR_SD * SLOPE_PRIOR_SD)
            b_use = (b * w_self + pooled_slope * w_pool) / (w_self + w_pool)
            du = u_target - xm
            y_hat = ym + b_use * du
            # damp very long extrapolations: a line fitted over ~2 days
            # should not be trusted 2+ u-units out
            if du > DAMP_U:
                y_hat = ym + (y_hat - ym) * (DAMP_U / du)
            # soft-cap the move (rates saturate; a line in u does not),
            # then apply the asymmetric hard caps
            move = y_hat - y_last
            move = move / (1.0 + abs(move) / SOFT_CAP_M)
            y_hat = y_last + clamp(move, -MAX_MOVE_DOWN, MAX_MOVE_UP)
            med_logit = clamp(y_hat, LOGIT_MIN, LOGIT_MAX)
            # predictive spread: fit residual + slope uncertainty over the
            # extrapolation + one refresh jump + small-count noise
            s_res = clamp(resid if resid > 0 else pooled_resid,
                          RESID_FLOOR, RESID_CAP)
            s_slope = (se_b * abs(du)) if se_b < 1e8 else 0.8 * abs(du)
            s_ref = 0.7 * jump
            n_last = snaps[-1][1]
            if n_last:
                e_last = max(r_last * n_last / 100.0, 1.0)
                s_cnt = 0.5 / math.sqrt(e_last)
            else:
                s_cnt = 0.25
            spread = math.sqrt(s_res * s_res + s_slope * s_slope
                               + s_ref * s_ref + s_cnt * s_cnt)
            spread = clamp(spread, SPREAD_FLOOR, SPREAD_CAP)
        q = [round4(clamp(inv_logit(med_logit + z * spread), 0.0, 100.0))
             for z in Z]
        rows.append({"id": tr["id"], "q": q})
    return {"trophies": rows}


def forecast_case_safe(case):
    """Never crash a case: on any error fall back to the house persistence
    baseline (a valid, scored forecast beats an invalid case)."""
    try:
        return forecast_case(case)
    except Exception:
        last = case["history"][-1]["rates"] if case.get("history") else []
        spread = 0.5 * math.sqrt(case["horizon_minutes"] / 1440.0)
        rows = []
        for i, tr in enumerate(case["trophies"]):
            r = last[i] if i < len(last) and last[i] is not None else 0.5
            lg = logit(r)
            rows.append({"id": tr["id"],
                         "q": [round4(clamp(inv_logit(lg + z * spread), 0.0, 100.0))
                               for z in Z]})
        return {"trophies": rows}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case_safe(case)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
