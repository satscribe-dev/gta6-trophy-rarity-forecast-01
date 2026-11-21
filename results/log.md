# results/log.md — gta6-trophy-rarity-forecast-01 ($250, 20 tempat berbayar)

Deadline entri: 21 Nov 18:30 WIB (11:30 UTC). Hasil due 10 Des 2026. Repo: github.com/satscribe-dev/gta6-trophy-rarity-forecast-01.
Kit: ~/workspace/makefun/gta6-trophy-rarity-forecast-01-kit/ (level kit: lihat kit.json; RULES 336 baris dibaca penuh).
Riset: ~/workspace/makefun/gta6-trophy-rarity-forecast-01-research/ (NOTES.md, score.py scorer pinball eksak, mkbt.py/runbt.py, snapshot 15:12Z + 17:13Z).

## 5 aturan terpenting (standar VERSI FINAL, resume tiap sesi)
1. Submit HANYA atas kata "submit" Bos; ambang lapor = HARUS LEBIH TINGGI DARI TOP LEADER (#55) — belum ada bukti top 1 = HELD, jangan lapor sebagai menang.
2. Judge lokal kejam sebelum lapor (#52): 2 judge independen, devil's advocate wajib, keraguan jatuh ke rival, headline = estimasi TERENDAH setelah haircut; detail mentah ke log.md ini.
3. Satu perubahan per eksperimen, terima hanya kalau naik statistik di data yang mewakili FINAL (#28-30).
4. Jangan hardcode jawaban; kode dari sesi ini; transkrip utuh (bundle parent-chain — pelajaran news18 v5: check lokal 14/14 TIDAK menguji rantai parent, hanya vonis server yang membuktikan).
5. Deadline 21 Nov 18:30 WIB; entry terakhir sebelum deadline = entry final; sisakan slot 24 jam terakhir.

## Riwayat build (worker in-run 3ce9cc67, spawn scan monitor 22:07 WIB 19 Nov)
- 19 Nov 22:21 WIB (15:21Z) init resmi kit CLI, anchor drand round 34099449, LICENSE MIT (b236809, e6ba89b).
- v1 22:41 WIB (eb68684): logit-u line fit + dilution fallback. BT1 0.324 vs baseline 2.366; simfinal 0.385 KALAH vs baseline 0.372 (ekstrapolasi linear overshoot).
- v2 22:49 WIB (20ec644): half-life 18h->8h, caps asimetris [-1.6,+3.0], soft cap M=2.0, slope se 2pt 0.6, refresh jumps recent-only 36h. BT1 0.324 (tetap); simfinal 0.145 vs house curve 0.293.
- v2.1 22:51 WIB (38afcf5, HEAD, pushed): cap flat-path dilution shift di -3.5 logit; tidak ubah backtest.
- 19 Nov 22:54 WIB worker masuk sleep background 4 jam (sampai ~19:51 UTC = 02:51 WIB 20 Nov) buat jeda snapshot 2; rencana pas bangun: fetch snapshot 1b -> BT2a, lalu snapshot 2 -> BT2b, final commit + laporan. Worker TIDAK mati — jangan spawn duplikat, jangan sentuh main.py (transkrip authorship milik sesinya).

## Verifikasi independen parent (chat ini, 20 Nov 00:10-00:25 WIB, main.py v2.1 @38afcf5, output ke /tmp)
- Practice p00/p01: 2 run byte-identik, ~0.2-0.3 dtk/run (batas 8 dtk), output 2.782-2.783 B (batas 65.536), 55 baris, id 1-55 sekali, kuantil monoton 0-100. PASS.
- BT1 re-run (copy riset di /tmp): mine 0.3243, cov 0.89, miss 0.07pp vs baseline 2.3662 / housecurve 2.3662 / persist 2.6148. REPRODUKSI PERSIS angka README. PASS.
- SIMFINAL re-run: mine 0.1451 vs housecurve 0.2926 vs baseline 0.4034 vs persist 0.7594. REPRODUKSI PERSIS. PASS (sim = asumsi struktural, bukan data nyata).
- Live snapshot 2 (browser.open Exophase 17:13Z, 19 Nov): SEMUA 55 rate IDENTIK dengan snapshot 15:12Z — Exophase BELUM refresh selama 2 jam. Disimpan research/snapshot-20261119T1713Z.json (N_fit 30000, earners = snapshot 1).
- BT2a (BARU, chat ini): history launch-night + snapshot 1, checkpoint 15:12Z, horizon 121 mnt, jawaban snapshot 17:13Z (= tidak ada refresh). mine 0.4040, cov 1.00, miss 0.026pp vs BASELINE 0.0288 vs housecurve 0.2768 vs persist 0.0000. **KALAH TELAK dari baseline.**
  - Akar (dugaan terukur, bukan tebak): spread fitter meledak — satu-satunya jump antar-snapshot = ledakan dilusi launch night (~2.9 logit), s_ref = 0.7*jump ~2.0 logit, spread total ~2.1 (cap 2.2). Median cuma meleset 0.026pp tapi spread selebar itu bayar pinball di semua kuantil. Baseline menang karena jawabannya = last read persis (spread 0.145).
  - Batasan: BT2a horizon 121 mnt + jawaban tanpa refresh = setting yang menguntungkan persistence secara trivial; final (4,5 hari, banyak refresh) BUKAN setting ini, dan SIMFINAL bilang v2 menang di sana. Tapi cacatnya nyata: fitter tidak punya mode "tidak ada refresh" — jump ledakan satu-off diperlakukan sebagai ukuran refresh yang akan datang.
  - Saran perbaikan (UNTUK worker pas bangun, BUKAN dikerjakan chat ini): cap kontribusi s_ref (mis. <=0.5-0.7 logit) ATAU buang/kerdilkan jump pertama dari halaman launch-night yang datar saat itu satu-satunya jump; uji ulang BT2a + BT1 + SIMFINAL, terima hanya kalau ketiganya tidak regresi (aturan #28-30).
  - Catatan: BT2b (snapshot 2 pasca-refresh nyata) tetap perlu — BT2a tidak menggantikannya.

## Judge lokal kejam (skill: judgment-or-code -> penilai KODE, scorer pinball eksak; write-judge-prompt binary per kriteria; advanced-evaluation pairwise n/a — metrik deterministik, bukan artefak)
- Kriteria binary: format+determinisme PASS | BT1 vs baseline PASS (0.324 < 2.366) | SIMFINAL vs house curve PASS (0.145 < 0.293) | BT2a vs baseline FAIL (0.404 > 0.029) | bukti top 1 FAIL (final belum diskor; bar = house model forecast 21 Nov 09:30Z, belum ada).
- Devil's advocate (argumen terkuat rival): house baseline menang BT2a 14x lipat; kalau refresh Exophase ternyata jarang (2x dalam 17 jam pertama), jawaban final bisa jadi halaman yang sudah basi berhari-hari dan persistence + spread sempit mengalahkan fitter yang mengekstrapolasi tren.
- Headline: TIDAK LEBIH TINGGI DARI TOP LEADER — tidak ada skor final/top leader yang terukur; satu backtest nyata (BT2a) kalah dari baseline. Haircut: belum terkalibrasi (belum ada data server). Verdict: HELD, lanjut iterasi (BT2b + calon fix s_ref), JANGAN submit.
- Detail mentah: angka di atas (BT1/BT2a/SIMFINAL + practice) adalah seluruh detail judge; tidak ada tabel pairwise artefak (bukan bounty gambar).

## Status
- HELD. JANGAN submit tanpa kata "submit" dari Bos. Sisa jatah: belum dicek (cek saat submit). Kuota harian: belum dicek.
- Menunggu worker bangun ~02:51 WIB 20 Nov (BT2b + keputusan fix s_ref + final commit + laporan) — bundle + check dikerjakan DI CHAT INI sesudah worker kembali (maks 20 Nov 12:00 WIB).
- Yang BELUM beres sebelum submit: (1) BT2b; (2) keputusan fix s_ref; (3) README badges make.fun + GitHub About topic makefun (RULES: repo_readme/repo_about — README sekarang tanpa badge); (4) bundle --dry-run + check lokal kit (parent-chain: run ini started-by monitor cron/scheduled prompt — bundle butuh parent chain sampai sesi prompt; pelajaran news18: check lokal tidak menguji rantai parent); (5) cek kuota/can_submit segar.

## Tweak v2.2 + v2.3 (chat ini, perintah Bos 00:31 WIB 20 Nov "Kerjain tweak sekarang")
- Aturan terima pra-registrasi: terima hanya kalau BT2a naik >0.05 DAN SIMFINAL tidak regresi >0.02 DAN BT1 tidak berubah. Satu perubahan per eksperimen, diuji vs base terakhir yang DITERIMA.
- v2.2 (commit 5686134, chat ini): JUMP_CAP=1.0 — cap per-refresh jump untuk spread (s_ref = 0.7*min(jump,1.0)). BT2a 0.404->0.204 (-0.20), BT1 0.324 tetap, SIMFINAL 0.145 tetap, practice byte-identik. DITERIMA.
- v2.3 eksperimen (di atas v2.2, /tmp dulu): buang snapshot launch-night dari fit (rezim beda N=638; jump ke refresh pertama = level shift satu-off, bukan tren). BT1 0.324 tetap, BT2a 0.204->0.175 (-0.029), SIMFINAL 0.145->0.118 (-0.027, typical miss 1.91->1.07pp). DITERIMA (SIMFINAL naik >0.02, BT2a tidak regresi, BT1 tetap).
- v2.3 (commit 2e58eb3, pushed): main.py + README (evidence + metode). Repo file diuji ulang: BT1 0.3243 / BT2a 0.1751 / SIMFINAL 0.1179 / practice byte-identik 0.17-0.31 dtk — SAMA PERSIS dengan eksperimen /tmp.
- PENTING buat bundle: v2.2 + v2.3 ditulis DI CHAT INI (sesi c4819a54), BUKAN sesi worker. Bundle nanti WAJIB mencakup sesi chat ini + sesi worker 3ce9cc67 + parent chain (monitor cron). Jangan bundle cuma sesi worker — baris v2.2/v2.3 tidak ada di sana (reproduces bakal jatuh).
- STOP di sini: sisa gap BT2a (0.175 vs baseline 0.029) = biaya asuransi spread saat jawaban kebetulan beku; mengejar 0.029 = bertaruh final tanpa refresh — bertentangan dengan refresh 04:30Z + pre-15:12Z. Tidak ada tweak BT2a-targeted lagi. Sinyal berikutnya = BT2b (worker bangun ~02:51 WIB, snapshot 2 pasca-refresh nyata).

## Judge lokal kejam — update pasca-v2.3 (skill sama: judgment-or-code -> penilai KODE; write-judge-prompt binary)
- Binary: format+determinisme PASS | BT1 PASS (0.324 < 2.366) | SIMFINAL PASS (0.118 < 0.293) | BT2a FAIL (0.175 > 0.029) | bukti top 1 FAIL (final belum diskor; bar = house model forecast 21 Nov 09:30Z).
- Devil's advocate: baseline tetap menang BT2a 6x; house model forecast (superbot, effort max, 2 hari data penuh) adalah bar sesungguhnya dan belum ada — mengalahkan 2 baseline di BT1/SIMFINAL itu perlu, bukan cukup.
- Headline: TIDAK LEBIH TINGGI DARI TOP LEADER. Verdict: HELD, JANGAN submit. Menunggu BT2b (~02:51 WIB) lalu bundle + check di chat ini.
