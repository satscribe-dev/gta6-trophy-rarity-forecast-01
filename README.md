# gta6-trophy-rarity-forecast-01

Forecast every GTA VI (PS5) trophy's earn rate on Exophase at 2026-11-26T00:00Z,
as five quantiles per trophy, from the house's recorded reads up to the deadline.

## Program

`python3 main.py` (stdlib only). Reads every `*.in` in `$MAKEFUN_INPUT_DIR`
(else `/input`), writes one `*.out` per case to `$MAKEFUN_OUTPUT_DIR` (else
`/output`). Deterministic, ~0.1 s per case, output ~2.8 KB (limit 65,536).

## Method

Work in logit space against `u = ln(1 + hours since 2026-11-19T00:00Z)`.

1. **Collapse history into distinct Exophase snapshots.** Consecutive identical
   reads are one refresh state, not new information. Exophase refreshes on its
   own schedule; a read only shows the rates as of the last refresh before it.
   The launch-night snapshot is then dropped: its rates are a different regime
   (N=638 early players, pre-dilution), and the jump to the first refresh is a
   one-off level shift, not a trend to extrapolate.
2. **Rich history (>= 2 snapshots):** per trophy, a recency-weighted
   (12 h half-life) least-squares line of logit(rate) on `u`, slope shrunk
   toward the pooled slope across trophies. Extrapolate to the target with
   damping beyond 1.5 u-units and an asymmetric cap on the move from the last
   rate (-1.6 / +3.0 logit): the launch-night dilution (-2.9 logit in 15 h,
   as the tracked-player count exploded 638 -> ~10-30k) was a one-off; from
   day 2 to day 7 tracked growth slows while earners only accumulate.
3. **Flat history (1 snapshot):** dilution model. The tracked count grows
   roughly like (1 + t), so with no new earners observed the rate is expected
   to fall by that growth factor; spread is widened because the next refresh
   is unseen. (Near-)100% trophies stay ~100%.
4. **Spread:** predictive logit SD from fit residual + slope uncertainty over
   the extrapolation + refresh jump size (per-refresh jump capped at 1.0 logit:
   the launch-night explosion jump of ~2.9 was a one-off) + small-count noise,
   floored at 0.45 and capped at 2.2. Quantiles are median +/- normal z-scores times the
   spread: pinball loss is a proper scoring rule, so the quantiles written
   are the ones actually believed.
5. Any error falls back to the house persistence baseline, so a case is never
   left invalid.

## Evidence (measured, not claimed)

- **Live Exophase snapshot, 19 Nov 15:12Z** (fetched for research; the program
  itself reads only the case file at runtime): launch night -> day 1, the
  median trophy fell -2.94 logit units (98% of trophies down) as tracked
  players exploded; early trophies (fishing, Chapter 1, Beat Cal) held up.
- **Backtest BT1** (flat launch-night history, checkpoint 03:00Z, scored
  against that live snapshot 12.2 h later): **loss 0.324, coverage 0.89,
  typical miss 0.07 pp** vs house baseline **2.366, coverage 0.05** and
  persistence 2.615. The structural dilution shift lands within 0.001 of the
  grid-search optimum (0.324) without being fitted to it.
- **Practice (p00/p01):** no local grade exists for this competition (the
  server grades; `makefun grade` is not a command) and the kit publishes no
  practice answers, so an exact practice loss cannot be computed locally.
  Under the stated assumption that earners were frozen between launch night
  and the 04:30Z refresh except fishing (~100%), the estimate is ~0.16-0.17
  vs the starter's ~1.69 (RULES states the starter scores ~1.51 on the real
  practice). That estimate is assumption-driven, not measured.
- **Backtest BT2a** (multi-snapshot fitter, snapshot 1 -> live snapshot 17:13Z,
  121 min, NO refresh in between — the page was frozen): v2.3 **loss 0.175**
  vs house baseline **0.029** and persistence 0.000. Still loses: when nothing
  changes, any honest spread pays pinball and persistence wins by construction.
  The fix halved the damage (v2.1: 0.404 -> v2.2 cap: 0.204 -> v2.3: 0.175) by
  killing the spread explosion; the remainder is the insurance cost of a spread
  that pays off when a refresh DOES hit (see BT1: narrow-spread persistence
  scores 2.366 there). Chasing BT2a to 0.029 would mean betting the final has
  no refreshes — contradicted by the refreshes at 04:30Z and pre-15:12Z — so
  no further BT2a-targeted tweak; BT2b (post-real-refresh) is the next signal.
- **Backtest BT2b** (multi-snapshot fitter, real refresh): pending — worker wakes ~02:51 WIB 20 Nov for snapshot 2.
- **Simulation SIMFINAL** (structural, final shape: cut t=48 h, target t=168 h,
  13 refresh snapshots, rates from an earner-growth model): **mine v2.3 0.118**
  vs house curve 0.293 vs house baseline 0.403 vs persistence 0.759
  (v2.2: 0.145; v2: 0.145; v1 LOST at 0.385). Dropping the launch snapshot from
  the fit cut typical miss 1.91 -> 1.07 pp. The sim's dynamics are assumptions,
  so this validates mechanics, not real levels.

## Research notes (not part of the entry)

`~/workspace/makefun/gta6-trophy-rarity-forecast-01-research/`:
`snapshot-20261119T1512Z.json`, `score.py` (exact pinball scorer),
`mkbt.py` / `runbt.py` (backtest builder/runner), `cases/` (bt1, syn1-3).
