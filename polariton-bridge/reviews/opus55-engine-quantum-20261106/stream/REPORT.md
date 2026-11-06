## Quantum engine, streaming (temporal-blocking) variant (`BRIDGE_ENGINE_CHANGE`, PREDICTION.hbp line 451)

The variant is a new mode, `stream`, selected by name; `point` still runs the dyadic engine's window code. On the line-451 gate it passes everything this lane could run: the toolchain gate, and every field of RECEIPT-GRID.hbp and of RECEIPT-BASELINE.hbp's 58 allowed rows byte for byte except array_bytes. With array_bytes set back to the filed value, the grid file is byte for byte the filed receipt (sha256 4a1a2778…). Two items stay open: the whole-file baseline check, NOT_MEASURED (reason RESERVED: 6 rows of 2 reserved runs), and the hosted CI, NOT_MEASURED because nothing was pushed.

Speed, MEASURED with 3 interleaved repeats: the variant is 1.98× to 2.15× as fast as `point` one run at a time, and 1.93× four runs at a time on the full space N = K = 6561. That is at the low end of the seat's 2-to-3× CONJECTURE. It peaks at 1.04 GB against 1.29 GB.

- **Folder:** `C:/tmp/opus55/bridge-engine-stream-20261106/`
- **Vantage:** WSL2 Ubuntu, rustc 1.81.0, i5-8300H (4 cores, 8 threads, L3 8 MiB), 7.86 GB.
- **Worktree:** read-only at HEAD 38ce248, status clean. No git writes, no push, no GitHub writes.

### What changed (MEASURED)
- **Change:** in `src/bin/polariton_first_correction.rs`, starting from the dyadic engine (8d8afe48), a new mode `stream N K DELTA Y W T[,…] [depth=D] [tile=M] [sabotage=NAME]` with defaults D = 8 and M = 512.
- **The `point` path:** the dense window keeps its exact statements, re-indented under `else`. Ignoring whitespace, the diff removes 13 lines, none inside the window: module text, the signature, 5 allocation lines (now sized by layout), array_bytes, the COST format, the `point` call and the usage line.
- **Size and hashes:** 1080 → 1903 lines, 8 hunks, +846/−56. Source `ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6`, binary `d892971d6c0023534a2cbfac2631a7d983eeeab6853ffb6524b589e74795f270` (599,040 bytes, x86_64-unknown-linux-gnu).
- **Design (DERIVED):**
  - A window runs as sweeps of D Chebyshev levels over shells. At sweep position s, level j works on shell s − 2(j−1), because H moves q by at most 2.
  - Each level keeps 5 shells; a sweep's last two levels go back to full arrays for the next sweep.
  - Each row is gathered from the same products `step` adds: the diagonal, its 3 raising elements, and the 3 elements raising shells q−1 and q−2 into it. Re and Im run in one pass.
  - The accumulation is fused and uses one 64×64 multiply when sign·a fits 64 bits (every coefficient does); otherwise it takes the same 128-bit product as `point`.
  - Shells run in tiles of M rows m. Level j computes a margin of D′−j rows per side, since H moves m by at most 1. A tile keeps the next tile's margin rows of `prev` and `cur` in a strip before overwriting them, and the next tile swaps them back while it runs.
- **array_bytes:** stream prints its own count (96 B per state plus rings plus strips); its COST row prints `array_bytes_point_layout=` (the filed value) beside it.

| Block | stream array_bytes | filed (`point`) array_bytes |
|---|---|---|
| K = 1200 | 35,674,848 | 43,344,120 |
| K = 1600 | 62,926,048 | 76,992,120 |
| K = N = 6561 | 1,039,210,816 | 1,292,189,040 |

### Gate on the delivered binary (MEASURED; `logs/gate-exits.hbp`, 13 rows, all MEASURED_PASS)

| Step | Result |
|---|---|
| rustc | 1.81.0 (eeb90cda1 2024-09-04) |
| `cargo +1.81 fmt -- --check`; `fmt --all -- --check` | exit 0; exit 0 |
| `cargo +1.81 clippy --release -- -D warnings`, fresh target | exit 0 on 6 crates (verbose run): gguf_qnn lib and bin, google_qsim_audit, google_qsim_full24, polariton_first_correction, polariton_three_mode |
| clippy `--release --all-targets`; workflow form `--locked --offline --bin polariton_first_correction` | exit 0; exit 0 |
| `build --release --locked --offline` | exit 0; fresh-target build equals the run binary (d892971d…) |
| float_used | 0: the scanner finds 0 floats in the code over 1903 lines (its self-test finds 6 of 6 planted floats); CI grep `\bf(32\|64)\b` on src and tests is empty |
| CR in source | 0 |
| Unknown-mode usage line | exit 2, empty stdout, names `[tile=M]` |

Gate run 1 is NOT_MEASURED: whole-crate clippy exited 101 because my build tree lacked `data/google-qsim`, which another bin pulls in with `include_str!`. That run is kept in `logs/gate-run1-missing-data/`.

### Reproduction (MEASURED)
- **RECEIPT-GRID.hbp:** 20 of 20 rows, same keys in the same order, 800 fields besides array_bytes, 0 differing. array_bytes differs on all 20 (own layout). With array_bytes set to the filed value the whole file is byte for byte the filed receipt (sha256 4a1a2778…). The stage took 7 min 25 s wall at 4 runs at a time.
- **RECEIPT-BASELINE.hbp:** 40 runs ran. The guard refused 2 before start: plan index 27 and 32 (N = 729, K = 729, y = 2/27, δ = 0 and 1/2). 58 of 58 rows matched, 2,320 fields, 0 differing. The allowed-rows file with `runs=40` equals the filed allowed rows (sha256 ff57d5e8…). The whole file is NOT_MEASURED (reason RESERVED).
- **Smoke test, 351 of 351:**
  - `point` of the variant equals the dyadic binary byte for byte on 20 of 20 configs.
  - `stream` equals the dyadic `point` except array_bytes on all 320 cases: 16 (depth, tile) pairs from (2,2) to (200,512) × 20 configs. The configs cover K = 0..3, K > N, y = 0, y < 0, W = 4 and 7, dyadic t, all 4 sabotages, and tiles down to the depth.
  - 11 bad-argument refusals exit 2 with empty stdout.
- **Controls, 6 of 6:** driven by the repo's unchanged `run_stage.py` with a guarded stream wrapper.
  - The real engine passes the reader's checks.
  - Each sabotage fails exactly the checks CONTROLS.hbp names: leak_understated 2, bessel_short 4, norm_drift 1, drop_even_root 1.
  - The crosscheck passes.
- **Two binaries:** the timed binary 72c7d3cf (source 7853c9d6, which differs by one line, the usage message) and the delivered d892971d give byte-equal stage rows, comparisons, normalized receipts and controls (7 of 7).
- **Guard:** self-test 18 of 18 with no run started. Audit of `logs/guard-log.hbp`: 2,550 model runs started (307 `point`, 2,243 `stream`), 0 at a reserved point, 4 refused before start.

### Timing (MEASURED; one run at a time, arm order rotated per repeat, 3 repeats, timed binary 72c7d3cf; `out/TIMING-*.hbp`)
All rows are at N = 6561, δ = 1/2, y = 1/324. Engine ms per repeat:

| Row | variant `point` | dyadic `point` | stream | stream over `point`: mean (range, spread) | stream over dyadic |
|---|---|---|---|---|---|
| K = 1200, t = 2 | 84,220 / 85,600 / 86,522 | 83,070 / 83,821 / 88,612 | 40,506 / 40,430 / 40,988 | **2.102** (2.079–2.117, 0.038) | 2.095 (2.051–2.162) |
| K = 1600, t = 2 | 171,410 / 172,181 / 174,606 | 168,283 / 170,467 / 170,517 | 79,726 / 80,968 / 80,354 | **2.150** (2.127–2.173, 0.046) | 2.113 (2.105–2.122) |
| K = 6561 full space, t = 1/4 | 579,058 / 576,384 / 579,711 | — | 291,253 / 297,169 / 288,945 | **1.978** (1.940–2.006, 0.066) | — |

- **Checks:** every `point` row equals its filed receipt row; every stream row equals it with array_bytes set to the filed value; on the full space, stream equals the same repeat's `point` (3 of 3).
- **Peak RSS, `point` / stream (kB):** 44,464 / 36,696 at K = 1200; 77,336 / 63,216 at K = 1600; 1,263,972 / 1,016,184 at K = 6561.
- **Baseline path speed:** variant `point` and dyadic `point` agree within run-to-run noise (means +0.3 % at K = 1200, +1.8 % at K = 1600).
- **Other load:** Windows CPU outside WSL during the runs was 0.09 to 1.07 cores at its 30-second peaks (137 samples).
- **Four runs at a time** (the full-space plan's regime; K = 6561, t = 1/64 and 1/32; window 2 plus its read). The speedup there matches the single-run one; both layouts slow about 2× under four-way load on this laptop.

| Repeat | `point` | stream | Ratio |
|---|---|---|---|
| r1 (`point` first) | 69.48 to 69.73 s | 37.10 to 37.68 s | 1.862 |
| r2 (stream first) | 70.64 to 71.45 s | 35.39 to 36.12 s | 1.993 |
| Mean | | | 1.928 (spread 0.131) |

- **Estimate (CONJECTURE):** the 5 full-space runs at δ = +3/5, planned at 10 to 14 hours, would take about 5.0 to 7.5 hours. The cost per window at δ = +3/5 is CANNOT_SEE here (reserved point).
- **Design choices (MEASURED, dev builds, `out/CALIBRATION.hbp`):**
  - The dyadic kernel is instruction-bound on this machine. Its scatter keeps `sum` in memory with checked adds, and its accumulation is a checked 128×128 multiply per element. Window 2 at K = 1600 takes 1.29 s, against 0.52 to 0.61 s for v2.
  - Single runs at K = 6561: one tile and tile 1024 are equal (23.27 / 25.13 s against 23.18 / 25.06 s).
  - Four at a time: tile 512 takes 32.0 to 32.4 s, tile 1024 35.2 to 35.8 s, one tile 41.3 to 41.9 s. Depth 16 takes 39.4 to 40.1 s against 35.6 to 36.0 s for depth 8.
  - The same configuration drifted from 32.0 to 36.0 s between batches as the machine heated, so only interleaved rows compare arms.

### Derivation (DERIVED, checked by the runs above)
- **D1, amplitudes:** the gather sums exactly the set of products `step` scatters into each row. Every partial sum is at most Σ|e||v| ≤ 2^62·max|v|, far inside i128, so the checked adds (overflow-checks = true) take the same path. Floor, range check and minus are the same expressions.
- **D2, terms:** each term (sign·a·v)>>16 is the same integer whether formed 64×64 or 128×128. The sums are order-free, with partial sums ≪ 2^127.
- **D3, wavefront reads:** every read happens after its value is complete. A ring slot is rewritten 5 positions after it is written, after its last read at +4. `prev[q]` is last read at position q and overwritten at q+2(D−2); `cur[q]` is last read at q+2 and overwritten at q+2(D−1), for D ≥ 2.
- **D4, tiles:** level j's rows need level j−1 on its own range. The margin rows the tile before overwrote get the sweep's input back from the strip (tile ≥ D). Each row is accumulated once and handed on once.
- **D5, counts:** `applies` = degree per window for each part whose source is not all zero, as `point` counts it.

### Open items
- **O1:** RECEIPT-BASELINE.hbp whole file, NOT_MEASURED (RESERVED). Needs the operator's word, or the hosted run.
- **O2:** hosted CI, NOT_MEASURED.
- **O3:** Windows MSVC build and its sha256, NOT_MEASURED.
- **O4:** speed at δ = ±3/5, CANNOT_SEE (reserved).
- **O5:** the CI runs `point` only; H10 adds a stream step.
- Recall at `:4796` answered live with count = 0 for BRIDGE_ENGINE_CHANGE, polariton_first_correction and temporal_blocking. That is an index boundary; the files here are the source. This lane did not ask the fabric.

### Slips (each corrected, kept on file)
- Two stray files in `C:\Users\acer\AppData\Local\Temp\`: `pfc_38ce248.rs` and `recall_q.txt`. Both are kept (no deletes outside the folder).
- `$VAR` inside `wsl -lc` three times (it arrived empty). Each was moved into a script file; none started a model run.
- A stray Windows `python3 -` waited on stdin twice. Both were stopped with TaskStop, and no process was left.
- Gate run 1 lacked the data files (above).
- The first tiled build panicked on an empty range past a short shell: `At::own` did not clamp `lo`. Smoke was 211 of 351 until the fix.
- The first dyadic calibration ran under unseen load: 21.8 s, where its own parts give about 10.7 s (DERIVED).
- The timed source's usage line lacked `[tile=M]`. It was fixed in ed75eca8, and gate, smoke, reproductions and controls were rerun with equal results.

### Files (sha256). `BRIDGE-ENGINE-STREAM.hbp`'s 729 BES_FILE rows hash every file in the folder; `verify_files.py` rechecked 738 of 738 rows.
- `BRIDGE-ENGINE-STREAM.hbp` 69471bc612399a2f723109370571c4b43d66fbce9bd74ea6c2cdde2c0f3a2831 (911 rows, `.sha256` sidecar)
- `out/polariton_first_correction.rs` and `build-src/src/bin/polariton_first_correction.rs` ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6
- `out/polariton_first_correction.rs.diff` fcd78a4329b081051b64360465ca13e2de148d3a4c5ea3d63dbad0516512bd61 (applies with `git apply` and GNU `patch`)
- `out/polariton_first_correction.rs.ignore-whitespace.diff` 9fcc3a2332fa51a93f0ff9558622d509c4ef165dac6f98220b9a007c9936c7c1
- `out/HOLDS.txt` 43e985624c98c27d880abd28d419c537f17be54a4b289f9a63e37958f93ba832 (the 13 blocks below) · `out/HOLDS-INDEX.hbp` d91fe34ed97e20a529717dcc72f867139a8e1ad4035c06544e5d137544de7a4a
- `logs/gate-exits.hbp` 8f30f78269bfcf3e1606a39b790ee71cab9aa143f2e264b0eea17054bd7ed30b
- `out/COMPARE-GRID-STREAM.hbp` 7bf42569a26731322b4cf8189e2285cdf17c9e7dcbe4d75410b174e042db9a5e · `out/COMPARE-BASELINE-STREAM.hbp` a32e490cbbce7cd3eda7a5d2774a875c6d125fc2fd182ec821157a0fedca05dc
- `out/RECEIPT-GRID-STREAM.hbp` 7b4e4aad3313a9cc595e12dac372ca8065d7e51dfea6e94b6fcf57461072cd52 · `out/RECEIPT-GRID-STREAM-NORMALIZED.hbp` 4a1a277885015a5e937a028d767c617878ae9a05e75bade9eee3e14f0e07e480
- `out/RECEIPT-BASELINE-STREAM-ALLOWED-RUNS40.hbp` 6fb780cd12e6741a8ccf6039412a33c91f6e3447f1852dabdef64f0e902cde83 · `out/RECEIPT-BASELINE-STREAM-NORMALIZED-ALLOWED-ROWS.hbp` ff57d5e8f8dc5697709f10ed42693ac066e45d534aa112b87ebdefbc1a4a9de0
- COST rows: `out/COST-STREAM-GRID.hbp` 34259d366427467a62adc74a87331993be4361a2c4d85035dbbd1ba56996a392 · `out/COST-STREAM-BASELINE.hbp` 73a8670c1d429499cc4b69e9365ae813e89ff86b618500b02f7c6ed79a63585d · `out/TIMING-COST.hbp` 64ed93bfb03334ef7c14b7423b7cbe85397fb43b7b00d40a65dc3b7ba898af2d
- `out/TIMING-RUNS.hbp` c67c77e75fbe42278d54158a831a8c2df1e267b85fa5dc08c766e3b28086f7a5 · `out/TIMING-SUMMARY.hbp` 57d0002f8f2a8d5e1ee3df50a91b9c11faca7bc95ab2f7eb468a86aaaa7d39ff · `out/PAR4-AB.hbp` 69c04c2478c6ddfa3763bc2aa0a1980680c3b35556e9963a619942c57e65911d · `out/CALIBRATION.hbp` 0a5bb7de6538eaeb25a781d72defdcc8eb8e7cdf98ef01e10036a7261a586ac6
- `out/SMOKE.hbp` d9f5c7755abb7a4c01ed89f4fffb16cc79405bfa0209bc2477f690b275174c9a · `out/CONTROL-CHECKS-STREAM.hbp` 90fd6aed58823173171ddd85bfe7606bc557e74bf70b40e73e2dfce3afa5cd49 · `out/BINARY-AB.hbp` 57f41f294763a37a0db2278a9cda7ebf9b98c1fc22e944e6ecfc20c7dfb5b479 · `out/USAGE-CHECK.hbp` 4a9de7818b5972e5c1e76ffb9a6c37c2a8e608a8cec195baba712b26189a9351 · `out/GUARD-SELFTEST.hbp` f2244aa62b677914a668537b706d54ea828bf8d3fb8c48bb9cfe9dcee9dc465c
- `out/SUMS-CHECK.txt` 7000533490b4615e632886f451ac78bbe920960a2c7327778b3745f84efa317c · `out/H10-TEXT-CHECK.txt` 27e7c4bea60b8de731de203b016cbe703f1714d4788fc2bf23138e4f430e259d
- Binaries:
  - delivered, `target-stream/release/polariton_first_correction`: d892971d6c0023534a2cbfac2631a7d983eeeab6853ffb6524b589e74795f270
  - timed: 72c7d3cf719feed849d097fbe36d5fce319d0b9272fb5a2429089010d16d3932; its first-run outputs are in `runs/binary-72c7d3cf-first-runs/`
  - dyadic control, rebuilt here: cc75d83f0a7e07b1d95bf091455f309d2c3fb64cf8f3485222e53e4c5508b776
- Scripts:
  - reserved.py 8dd437e8c108a9e1e8f1aabce2db15f48e3f273d57f0c441dea6d7426b438406 · guarded.py 631bc5b4ce7c7306d12afa37701b7f49346358b6759c6e78c3889a78e510b5ac · guarded_stage.py 51cc0e842fb5d8029f654e8adc8a49fa196edaca8e2f7e0ac89834cc1037116f · guard_selftest.py 052544e19e45f1ea9506b4b63be1a5303950fa25499ad25183e4d31f428b5d43 · guard_audit.py 730c0eedffa24102e0eabcd9c134c9309d85d7af500146db159a957def162f8e
  - smoke.py a56075cff372cccb3d0880a37ca34bc86f13b3f51ce511e8b9432d056de2cd4a · compare_stream.py 49f66dba42325de7d19c816ad3ebc7ab6efe2dfb97f5e48e27fd3041c53dd8bf · control_checks_stream.py 33f6258e36b935803f1bd3b78ff5430e1b07b0b671b761e8555754697d2e85e5 · cost_rows.py bb79896a4a6c01736daf3bc5e54178b4806cb70feb72a3f69ad7e4637d641acf
  - timing.py 6ec9587fc5dc00a81ee94215ec229e33975ac2d5a33ce594486e55339b9fee12 · timing_cost.py 4429cd6eaee9a0a53c92131568600cc177df37275a4192d61193a3e25f8bacee · par4.sh e1fada184ca962561c72e25bd8f6fc4237f961eedd0b8c84554c163867bb9c00 · par4_ab_rows.py 89e38c8134aceaaf3895ec376802fc359a268b18f829c32f8048d62b5ddafcbe · calib_rows.py 40b34865c6e0a851f74a89f30203431084ee84358b1b44763985a2d3f7f0210e
  - gate.sh 612bc98d3fa8b011891059eb129a6a07274c2c13677be66e70c5d1fb107470e9 · gate_verbose.sh 0462556c57110dc2eeb00acc6430eb1322dfd5ffc15fb4e8022c3bc10c09a015 · float_scan.py (copied unchanged) 304d670c4b6020f4a53c8469e38119541ffe29fdc79300fb1ed99376edcbdbe5
  - make_diff.sh a1002463e1b9ca29ba26fb5408bf114a4603ca32c883c5269c14fb22a06883a4 · hunks_to_holds.py 230ac6de873c608a5c506d5a87e003b5aace0e9d713b2ec08945b7f415ee1a06 · make_holds.py 1258e2f046fcfbe175aa057840072f2a0205ebee503c24e36d2176c7ec40f581 · sums_check.sh c072a34fac60135e16d5cb8e92b22b600a06fe34b37a3160da99121e3e50e1a7 · h10_text_check.sh e6625bfdab862188843c9672e96158091f5945a6409f360710ecbbd1551f1fd2
  - assemble.py 2e6b9f949eb1215ae4524da91f4c9cd906328c376529c23e25c5787f3ea8432a · static_rows.hbp be6952cbb7ae45274dba48c9a7d3d3b46fba60eb0cdea69d9a220c38ea8bd08e · verify_files.py 8147d28f92b9e8eb43c02ab6ed60b942cabb88f422e5acb96c15649813304c71 · win_load.ps1 871f99ce6248fcd86e98fd74475df4b5df1664d2914a9c9589fdcdab1ad6ebd2
  - phase_repro.sh 63039a7b85787d6b5f9af3c7cb908302ea6dff4758b929e2599da6156021db03 · phase_timing.sh 18f779bf4f6792c17ad286bacc823f4a80e409e6bd289084502a887caf63c514 · phase_after.sh f991d549dde65581a1f0febbbc175558b096a262afa4b57f92bf771f6ac5478b · phase_final.sh 3ae805a24e922b0e054b513ad6a7bab9a9fd190a7edfe86eedaa68839312579a
  - The rest are in the BES_FILE rows.

### HOLDS
These are `out/HOLDS.txt` as written. H1 to H8 apply to the dyadic engine (8d8afe48, the dyadic lane's H1 to H8 applied); each OLD occurs exactly once, and applied in order they give ed75eca8… byte for byte. H9 to H13: each OLD occurs once in its file at 38ce248, and H11 creates a new file.

HOLD H1 | file=src/bin/polariton_first_correction.rs | severity=LOW
OLD<<<
//! each window's term bounding that window alone, so the certificate at T is the same sum stopped there. An integer T
//! reads exactly as before.
//!
//! usage: polariton_first_correction point N K DELTA Y W T[,T2,...] [sabotage=NAME]
//!        polariton_first_correction bessel NUM/DEN
//!        polariton_first_correction rows N K DELTA Y
//! W: the window is 2^-W. Each T is an integer or a/2^b with b <= W, a multiple of the window. A sabotage breaks the
//! engine on purpose, and the reader must catch it.
#![forbid(unsafe_code)]
#![deny(
    clippy::float_arithmetic,
>>>
NEW<<<
//! each window's term bounding that window alone, so the certificate at T is the same sum stopped there. An integer T
//! reads exactly as before.
//!
//! The streaming layout (`stream`, `BRIDGE_ENGINE_CHANGE` of polariton-bridge/PREDICTION.hbp for a memory-layout
//! change): the same window, computed shell by shell in sweeps of `depth` Chebyshev levels (temporal blocking). At
//! sweep position s, level j works on shell s - 2(j - 1): H moves q by at most 2, so the level below is complete up to
//! that shell + 2. Each level keeps the 5 shells it is still read on; a sweep's last two levels go back to full arrays
//! for the next sweep. A sweep runs in tiles of `tile` rows m, with a margin of levels - j rows on each side of level j
//! (H moves m by at most 1), so the rows a sweep holds at once stay few on the widest shells. Every amplitude is the
//! same integer as in `point`: each row is gathered from the same products `step` adds, in another order, and an
//! integer sum is the same in any order. So every printed field is the same, but array_bytes, which counts this
//! layout's arrays; the COST row prints it beside the `point` layout's count.
//!
//! usage: polariton_first_correction point N K DELTA Y W T[,T2,...] [sabotage=NAME]
//!        polariton_first_correction stream N K DELTA Y W T[,T2,...] [depth=D] [tile=M] [sabotage=NAME]
//!        polariton_first_correction bessel NUM/DEN
//!        polariton_first_correction rows N K DELTA Y
//! W: the window is 2^-W. Each T is an integer or a/2^b with b <= W, a multiple of the window. A sabotage breaks the
//! engine on purpose, and the reader must catch it. D: Chebyshev levels per sweep, at least 2 (default 8). M: rows per
//! tile, at least D (default 512).
#![forbid(unsafe_code)]
#![deny(
    clippy::float_arithmetic,
>>>
REASON: The module text: what the streaming layout is (sweeps of D Chebyshev levels on the shell wavefront, 5-shell rings per level, tiles of M rows with margins), why every printed field but array_bytes is point's, and the stream usage line with depth= and tile=. Text only; the binary changes by the line numbers its panic messages carry. Applies to the dyadic engine (8d8afe48, the dyadic lane's H1 to H8 applied); the 8 engine HOLDs in order give ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6 byte for byte.

HOLD H2 | file=src/bin/polariton_first_correction.rs | severity=HIGH
OLD<<<
    "CANNOT_SEE".to_string()
}

/// `times`: (window count T 2^W, T), sorted by the count.
fn point(n: i128, k_in: usize, delta: Rat, y: Rat, times: &[(i128, Rat)], w: u32, sab: &Sabotage) {
    let began = Instant::now();
    let k = k_in.min(usize::try_from(n).unwrap());
    let block = Block::new(n, k, sab.drop_even_root);
>>>
NEW<<<
    "CANNOT_SEE".to_string()
}

/// Which arrays a run keeps: `point`'s full vectors, or the streaming sweeps of `depth` levels.
#[derive(Clone, Copy)]
enum Layout {
    Dense,
    Stream { depth: usize, tile: usize },
}

/// Shells a level keeps in the streaming layout: one written at sweep position s is read up to position s + 4.
const RING: usize = 5;

/// The operator rows a shell's gather reads: its own, and those of shells q - 1 and q - 2 that raise into it.
struct ShellRows<'a> {
    d: &'a [i64],
    pair: &'a [i64],
    a: &'a [i64],
    b: &'a [i64],
    a_below: &'a [i64],
    b_below: &'a [i64],
    pair_below: &'a [i64],
    up1: bool,
    up2: bool,
}

fn shell_rows<'a>(block: &Block, op: &'a Op, q: usize) -> ShellRows<'a> {
    let st = &block.start;
    let own = st[q]..st[q + 1];
    let below1 = if q >= 1 { st[q - 1]..st[q] } else { 0..0 };
    let below2 = if q >= 2 { st[q - 2]..st[q - 1] } else { 0..0 };
    ShellRows {
        d: &op.d[own.clone()],
        pair: &op.pair[own.clone()],
        a: &op.a[own.clone()],
        b: &op.b[own],
        a_below: &op.a[below1.clone()],
        b_below: &op.b[below1],
        pair_below: &op.pair[below2],
        up1: q < block.k,
        up2: q + 2 <= block.k,
    }
}

/// Shell q of a full-length vector; empty outside 0..=K.
fn full_shell<'a>(v: &'a [i64], block: &Block, q: Option<usize>) -> &'a [i64] {
    match q {
        Some(q) if q <= block.k => &v[block.start[q]..block.start[q + 1]],
        _ => &[],
    }
}

/// Shell q of one level's ring; empty outside 0..=K.
fn ring_shell(level: &[i64], cap: usize, k: usize, q: Option<usize>) -> &[i64] {
    match q {
        Some(q) if q <= k => {
            let at = (q % RING) * cap;
            &level[at..at + q / 2 + 1]
        }
        _ => &[],
    }
}

/// Row m of shell q of Htilde times the level below, in its general form: each element checked against the shell's
/// edges. The row is gathered: the diagonal, this row's three raising elements, and the three elements that raise
/// shells q - 1 and q - 2 into it, the same products `step` adds into the same row from both ends.
/// below: the level below on shells q - 2 ..= q + 2, indexed by m, empty outside 0..=K.
fn row_sum(rows: &ShellRows, below: &[&[i64]; 5], m: usize) -> i128 {
    let [c_m2, c_m1, c_0, c_1, c_2] = *below;
    let mut s = i128::from(rows.d[m]) * i128::from(c_0[m]);
    if rows.up2 {
        s += i128::from(rows.pair[m]) * i128::from(c_2[m + 1]);
    }
    if rows.up1 {
        s += i128::from(rows.a[m]) * i128::from(c_1[m]);
        let e = rows.b[m];
        if e != 0 {
            s += i128::from(e) * i128::from(c_1[m + 1]);
        }
    }
    if m < rows.a_below.len() {
        s += i128::from(rows.a_below[m]) * i128::from(c_m1[m]);
    }
    if m >= 1 {
        if m <= rows.b_below.len() {
            s += i128::from(rows.b_below[m - 1]) * i128::from(c_m1[m - 1]);
        }
        if m <= rows.pair_below.len() {
            s += i128::from(rows.pair_below[m - 1]) * i128::from(c_m2[m - 1]);
        }
    }
    s
}

/// floor(s 2^-shift) minus the level two below, as `step` writes an amplitude.
fn amplitude(s: i128, shift: u32, minus: Option<i64>) -> i64 {
    let w = i64::try_from(s >> shift).expect("amplitude");
    match minus {
        Some(m) => w - m,
        None => w,
    }
}

/// One Chebyshev level of one part on rows lo..hi of one shell, every row in the general form.
fn shell_level(
    rows: &ShellRows,
    below: [&[i64]; 5],
    minus: Option<&[i64]>,
    shift: u32,
    out: &mut [i64],
    span: (usize, usize),
) {
    for m in span.0..span.1 {
        out[m] = amplitude(row_sum(rows, &below, m), shift, minus.map(|mm| mm[m]));
    }
}

/// The level below cut to the lengths the inside of a shell of n rows reads: shell q - 2 has n - 1 rows, q - 1 at least
/// n - 1, q exactly n, q + 1 at least n and q + 2 n + 1, of which the inside reads the first n - 1, n - 1, n, n, n.
fn cut_inner<'a>(c: &[&'a [i64]; 5], n: usize) -> [&'a [i64]; 5] {
    [
        &c[0][..n - 1],
        &c[1][..n - 1],
        &c[2][..n],
        &c[3][..n],
        &c[4][..n],
    ]
}

/// The sums a level's own rows of a shell go into: each part's sum over the shell (indexed by m), its 64-bit
/// coefficient, and the own rows.
struct Sums<'a> {
    dest: [&'a mut [i128]; 2],
    coef: [i64; 2],
    own: (usize, usize),
}

impl Sums<'_> {
    /// Row m's terms of both parts, when m is one of the own rows.
    fn add(&mut self, m: usize, v0: i64, v1: i64) {
        if m >= self.own.0 && m < self.own.1 {
            self.dest[0][m] += (i128::from(self.coef[0]) * i128::from(v0)) >> 16;
            self.dest[1][m] += (i128::from(self.coef[1]) * i128::from(v1)) >> 16;
        }
    }
}

/// One Chebyshev level of both parts on rows lo..hi of one shell, and with `sums` the own rows' terms. Rows 0 and
/// n - 1 take the general form. Between them, on a shell with q >= 2 that is not one of the block's top two, all seven
/// elements of every row exist and the row is summed without the edge checks; the b element is then added even where
/// it is 0, which adds nothing.
fn shell_level_pair(
    rows: &ShellRows,
    below: [[&[i64]; 5]; 2],
    minus: Option<[&[i64]; 2]>,
    shift: u32,
    out: [&mut [i64]; 2],
    span: (usize, usize),
    mut sums: Option<Sums>,
) {
    let n = rows.d.len();
    let (lo, hi) = span;
    let [out0, out1] = out;
    let inner = rows.up1 && rows.up2 && !rows.pair_below.is_empty();
    let (f_lo, f_hi) = if inner {
        let f_lo = lo.max(1).min(hi);
        (f_lo, hi.min(n - 1).max(f_lo))
    } else {
        (hi, hi)
    };
    for m in (lo..f_lo).chain(f_hi..hi) {
        let v0 = amplitude(row_sum(rows, &below[0], m), shift, minus.map(|mm| mm[0][m]));
        let v1 = amplitude(row_sum(rows, &below[1], m), shift, minus.map(|mm| mm[1][m]));
        out0[m] = v0;
        out1[m] = v1;
        if let Some(s) = sums.as_mut() {
            s.add(m, v0, v1);
        }
    }
    if f_lo >= f_hi {
        return;
    }
    let (d, pair, a, b) = (&rows.d[..n], &rows.pair[..n], &rows.a[..n], &rows.b[..n]);
    let (a_below, b_below, pair_below) = (
        &rows.a_below[..n - 1],
        &rows.b_below[..n - 1],
        &rows.pair_below[..n - 1],
    );
    let [x_m2, x_m1, x_0, x_1, x_2] = cut_inner(&below[0], n);
    let [z_m2, z_m1, z_0, z_1, z_2] = cut_inner(&below[1], n);
    let (minus0, minus1) = match minus {
        Some([m0, m1]) => (&m0[..n], &m1[..n]),
        None => (&[][..], &[][..]),
    };
    let (out0, out1) = (&mut out0[..n], &mut out1[..n]);
    for m in f_lo..f_hi {
        let (e_d, e_p, e_a, e_b) = (
            i128::from(d[m]),
            i128::from(pair[m]),
            i128::from(a[m]),
            i128::from(b[m]),
        );
        let (e_a1, e_b1, e_p2) = (
            i128::from(a_below[m]),
            i128::from(b_below[m - 1]),
            i128::from(pair_below[m - 1]),
        );
        let s0 = e_d * i128::from(x_0[m])
            + e_p * i128::from(x_2[m + 1])
            + e_a * i128::from(x_1[m])
            + e_b * i128::from(x_1[m + 1])
            + e_a1 * i128::from(x_m1[m])
            + e_b1 * i128::from(x_m1[m - 1])
            + e_p2 * i128::from(x_m2[m - 1]);
        let s1 = e_d * i128::from(z_0[m])
            + e_p * i128::from(z_2[m + 1])
            + e_a * i128::from(z_1[m])
            + e_b * i128::from(z_1[m + 1])
            + e_a1 * i128::from(z_m1[m])
            + e_b1 * i128::from(z_m1[m - 1])
            + e_p2 * i128::from(z_m2[m - 1]);
        let (w0, w1) = (
            i64::try_from(s0 >> shift).expect("amplitude"),
            i64::try_from(s1 >> shift).expect("amplitude"),
        );
        let (v0, v1) = if minus0.is_empty() {
            (w0, w1)
        } else {
            (w0 - minus0[m], w1 - minus1[m])
        };
        out0[m] = v0;
        out1[m] = v1;
        if let Some(s) = sums.as_mut() {
            s.add(m, v0, v1);
        }
    }
}

/// The Jacobi-Anger term kk of part 0 (Re) or 1 (Im) as `point` adds it: (into Re, sign a), or None when a = 0.
fn term(table: &[i128], kk: usize, part: usize) -> Option<(bool, i128)> {
    let a = if kk < table.len() {
        table[kk] * if kk == 0 { 1 } else { 2 }
    } else {
        0
    };
    if a == 0 {
        return None;
    }
    let (dest_is_re, sign) = match (kk + part * 3) % 4 {
        0 => (true, 1i128),
        1 => (false, -1i128),
        2 => (true, -1i128),
        _ => (false, 1i128),
    };
    Some((dest_is_re, sign * a))
}

/// acc += (coef v) >> 16 term by term. The product is exact either way: one 64 x 64 multiply when coef fits in 64
/// bits, as every term's does, else the 128-bit product `point` takes.
fn accumulate(acc: &mut [i128], coef: i128, v: &[i64]) {
    match i64::try_from(coef) {
        Ok(small) => {
            let c = i128::from(small);
            for (t, &x) in acc.iter_mut().zip(v) {
                *t += (c * i128::from(x)) >> 16;
            }
        }
        Err(_) => {
            for (t, &x) in acc.iter_mut().zip(v) {
                *t += (coef * i128::from(x)) >> 16;
            }
        }
    }
}

/// What a sweep reads besides the state: the block, the operator and the Bessel table.
struct Ctx<'a> {
    block: &'a Block,
    op: &'a Op,
    table: &'a [i128],
}

/// The streaming layout's sizes: levels per sweep, rows per tile, and rows of the widest shell.
#[derive(Clone, Copy)]
struct Geom {
    depth: usize,
    tile: usize,
    cap: usize,
}

/// One sweep of a window: Chebyshev levels l0 + 1 ..= l0 + levels; `last` when it ends the window.
#[derive(Clone, Copy)]
struct Pass {
    l0: usize,
    levels: usize,
    last: bool,
}

/// Where a sweep is: level j (Chebyshev level kk = l0 + j) on shell q, in the tile of rows m0..m1, computing rows
/// lo..hi: the tile's rows and, below the sweep's top level, a margin of levels - j rows on each side, which the
/// levels above read.
#[derive(Clone, Copy)]
struct At {
    q: usize,
    j: usize,
    kk: usize,
    pass: Pass,
    tile: (usize, usize),
    span: (usize, usize),
}

impl At {
    /// The rows this level adds into the sums and hands to the next sweep: the tile's own.
    fn own(self) -> (usize, usize) {
        let lo = self.span.0.max(self.tile.0).min(self.span.1);
        (lo, self.span.1.min(self.tile.1).max(lo))
    }

    /// The array this level is handed on in, when the sweep is not the window's last: prev (0) for its second-to-last
    /// level, cur (1) for its last.
    fn hand_on(self) -> Option<usize> {
        if self.pass.last || self.j + 2 <= self.pass.levels {
            None
        } else {
            Some(usize::from(self.j == self.pass.levels))
        }
    }
}

/// The level below on shells q - 2 ..= q + 2, and the level two below on shell q (None for level 1 of a window):
/// `cur` for level l0, `prev` for level l0 - 1, the rings (`lower`, levels 1 .. j - 1 of this sweep) for the rest.
fn level_inputs<'a>(
    block: &Block,
    at: At,
    cur: &'a [i64],
    prev: &'a [i64],
    lower: &'a [i64],
) -> ([&'a [i64]; 5], Option<&'a [i64]>) {
    let (k, q, j) = (block.k, at.q, at.j);
    let cap = k / 2 + 1;
    let len = RING * cap;
    let shells = [
        q.checked_sub(2),
        q.checked_sub(1),
        Some(q),
        Some(q + 1),
        Some(q + 2),
    ];
    let below = if j == 1 {
        shells.map(|s| full_shell(cur, block, s))
    } else {
        let level = &lower[(j - 2) * len..(j - 1) * len];
        shells.map(|s| ring_shell(level, cap, k, s))
    };
    let minus = if at.kk == 1 {
        None
    } else if j == 1 {
        Some(full_shell(prev, block, Some(q)))
    } else if j == 2 {
        Some(full_shell(cur, block, Some(q)))
    } else {
        let level = &lower[(j - 3) * len..(j - 2) * len];
        Some(ring_shell(level, cap, k, Some(q)))
    };
    (below, minus)
}

/// Where shell q's strip rows of (part, array: 0 prev, 1 cur) start in a strip buffer.
fn strip_at(g: Geom, q: usize, part: usize, array: usize) -> usize {
    ((q * 2 + part) * 2 + array) * g.depth
}

/// A level's own rows of shell q into the next sweep's input `dest` (prev or cur of one part). Unless the tile is the
/// last, the next tile's margin rows of `dest`, m1 - levels .. m1, first go to the strip that tile will read.
fn hand_on(
    g: Geom,
    block: &Block,
    at: At,
    strips: &mut [Vec<i64>; 2],
    dest: &mut [i64],
    key: (usize, usize),
    own: &[i64],
) {
    let (part, array) = key;
    let base = block.start[at.q];
    let m1 = at.tile.1;
    if m1 < g.cap {
        let (from, end) = (m1 - at.pass.levels, m1.min(at.q / 2 + 1));
        if from < end {
            let s = strip_at(g, at.q, part, array);
            strips[(at.tile.0 / g.tile) % 2][s..s + end - from]
                .copy_from_slice(&dest[base + from..base + end]);
        }
    }
    let (lo, hi) = at.own();
    dest[base + lo..base + hi].copy_from_slice(own);
}

/// The streaming layout's arrays: per part (0: Re, 1: Im) a ring of 5 shells for each level of a sweep, the level
/// before a sweep's input (`prev`, kept only when a window takes more than one sweep), and the window's sums.
/// A sweep runs tile by tile in m, `tile` rows wide. Below its top level a sweep computes, on each side of the tile, a
/// margin of one row more per level down, so a level's rows are always complete from the level below: H moves m by at
/// most 1. When a sweep writes the next one's input, a tile overwrites rows the next tile still reads in its margin;
/// it keeps their old values (`strips`: `depth` rows of each shell, of prev and of cur, per part), and the next tile
/// swaps them back in place while it runs and out again after.
struct Stream {
    geom: Geom,
    ring: [Vec<i64>; 2],
    prev: [Vec<i64>; 2],
    acc_re: Vec<i128>,
    acc_im: Vec<i128>,
    strips: [Vec<i64>; 2],
}

impl Stream {
    fn new(block: &Block, depth: usize, tile: usize, run_degree: usize) -> Stream {
        assert!(depth >= 2 && tile >= depth, "depth and tile");
        let cap = block.k / 2 + 1;
        let ring = depth.min(run_degree) * RING * cap;
        let more_sweeps = depth < run_degree;
        let prev = if more_sweeps { block.dim } else { 0 };
        let strip = if more_sweeps && tile < cap {
            4 * (block.k + 1) * depth
        } else {
            0
        };
        Stream {
            geom: Geom { depth, tile, cap },
            ring: [vec![0; ring], vec![0; ring]],
            prev: [vec![0; prev], vec![0; prev]],
            acc_re: vec![0; block.dim],
            acc_im: vec![0; block.dim],
            strips: [vec![0; strip], vec![0; strip]],
        }
    }

    /// Bytes of the arrays a run holds, counted as `point` counts its 120 per state: the operator's four rows and
    /// the state (48 per state), then this layout's sums, `prev`, rings and strips.
    fn array_bytes(&self, dim: usize) -> usize {
        dim * 48
            + (self.acc_re.len() + self.acc_im.len()) * 16
            + (self.prev[0].len() + self.prev[1].len()) * 8
            + (self.ring[0].len() + self.ring[1].len()) * 8
            + (self.strips[0].len() + self.strips[1].len()) * 8
    }

    /// One window, exp(-i E h Htilde) on Re and Im, written back into `re` and `im` as `point` writes it.
    /// Returns the applications of Htilde `point` counts: one per level for each part whose source is not zero.
    fn window(
        &mut self,
        ctx: &Ctx,
        run_degree: usize,
        re: &mut [i64],
        im: &mut [i64],
        norm_drift: bool,
    ) -> u64 {
        let active = [re.iter().any(|&v| v != 0), im.iter().any(|&v| v != 0)];
        self.acc_re.fill(0);
        self.acc_im.fill(0);
        let g = self.geom;
        let mut l0 = 0;
        loop {
            let levels = g.depth.min(run_degree - l0);
            let pass = Pass {
                l0,
                levels,
                last: l0 + levels == run_degree,
            };
            let mut cur = [&mut *re, &mut *im];
            let mut m0 = 0;
            while m0 < g.cap {
                let m1 = (m0 + g.tile).min(g.cap);
                // The strip the tile before filled.
                let strip = (m0 / g.tile + 1) % 2;
                let swap = !pass.last && m0 > 0;
                if swap {
                    self.swap_margin(ctx.block, &mut cur, m0, levels, strip);
                }
                self.sweep(ctx, pass, &mut cur, active, (m0, m1));
                if swap {
                    self.swap_margin(ctx.block, &mut cur, m0, levels, strip);
                }
                m0 = m1;
            }
            l0 += levels;
            if pass.last {
                break;
            }
        }
        for i in 0..ctx.block.dim {
            re[i] = i64::try_from(self.acc_re[i] >> (Q - 16)).expect("re");
            im[i] = i64::try_from(self.acc_im[i] >> (Q - 16)).expect("im");
            if norm_drift {
                re[i] += re[i] >> 32;
                im[i] += im[i] >> 32;
            }
        }
        (u64::from(active[0]) + u64::from(active[1])) * u64::try_from(run_degree).unwrap()
    }

    /// Rows m0 - levels .. m0 of every shell, in prev and cur of both parts, swapped with the strip the tile before
    /// kept: before a tile, its margin gets the values the sweep started from back; after it, the new ones.
    fn swap_margin(
        &mut self,
        block: &Block,
        cur: &mut [&mut [i64]; 2],
        m0: usize,
        levels: usize,
        strip: usize,
    ) {
        let g = self.geom;
        let from = m0 - levels;
        for q in 0..=block.k {
            let end = m0.min(q / 2 + 1);
            if end <= from {
                continue;
            }
            let base = block.start[q];
            for (part, state) in cur.iter_mut().enumerate() {
                let s = strip_at(g, q, part, 0);
                self.prev[part][base + from..base + end]
                    .swap_with_slice(&mut self.strips[strip][s..s + end - from]);
                let s = strip_at(g, q, part, 1);
                state[base + from..base + end]
                    .swap_with_slice(&mut self.strips[strip][s..s + end - from]);
            }
        }
    }

    /// The levels of one pass on the tile's rows m0..m1, shell by shell, from `prev` (level l0 - 1) and `cur` (level
    /// l0: the state itself in a window's first sweep). At sweep position s level j works on shell s - 2(j - 1).
    fn sweep(
        &mut self,
        ctx: &Ctx,
        pass: Pass,
        cur: &mut [&mut [i64]; 2],
        active: [bool; 2],
        tile: (usize, usize),
    ) {
        let k = ctx.block.k;
        let end = k + 2 * pass.levels.saturating_sub(1);
        // No shell below this one has a row inside the tile's widest margin.
        let first = 2 * tile.0.saturating_sub(pass.levels);
        for s in first..=end {
            if pass.l0 == 0 && s <= k {
                // Level 0, the state itself, into the sums: the tile's own rows.
                let n = s / 2 + 1;
                let base = ctx.block.start[s];
                let r = base + tile.0.min(n)..base + tile.1.min(n);
                for part in 0..2 {
                    if !active[part] {
                        continue;
                    }
                    if let Some((into_re, coef)) = term(ctx.table, 0, part) {
                        let acc = if into_re {
                            &mut self.acc_re[r.clone()]
                        } else {
                            &mut self.acc_im[r.clone()]
                        };
                        accumulate(acc, coef, &cur[part][r.clone()]);
                    }
                }
            }
            for j in 1..=pass.levels {
                let back = 2 * (j - 1);
                if s < back || s - back > k {
                    continue;
                }
                let q = s - back;
                let n = q / 2 + 1;
                let margin = pass.levels - j;
                let span = (
                    tile.0.saturating_sub(margin).min(n),
                    (tile.1 + margin).min(n),
                );
                if span.0 >= span.1 {
                    continue;
                }
                let at = At {
                    q,
                    j,
                    kk: pass.l0 + j,
                    pass,
                    tile,
                    span,
                };
                if active == [true, true] {
                    self.level_pair(ctx, at, cur);
                } else {
                    for (part, &on) in active.iter().enumerate() {
                        if on {
                            self.level_one(ctx, at, part, cur);
                        }
                    }
                }
            }
        }
    }

    /// A level of one part on one shell, its terms, and its hand-on to the next sweep when it is one of the last two.
    fn level_one(&mut self, ctx: &Ctx, at: At, part: usize, cur: &mut [&mut [i64]; 2]) {
        let block = ctx.block;
        let g = self.geom;
        let base = block.start[at.q];
        let rows = shell_rows(block, ctx.op, at.q);
        let (lower, upper) = self.ring[part].split_at_mut((at.j - 1) * RING * g.cap);
        let slot = (at.q % RING) * g.cap;
        let out = &mut upper[slot..slot + at.q / 2 + 1];
        let (below, minus) = level_inputs(block, at, cur[part], &self.prev[part], lower);
        shell_level(&rows, below, minus, shift_of(at.kk), out, at.span);
        let (lo, hi) = at.own();
        if let Some((into_re, coef)) = term(ctx.table, at.kk, part) {
            let acc = if into_re {
                &mut self.acc_re[base + lo..base + hi]
            } else {
                &mut self.acc_im[base + lo..base + hi]
            };
            accumulate(acc, coef, &out[lo..hi]);
        }
        if let Some(array) = at.hand_on() {
            let dest: &mut [i64] = if array == 1 {
                &mut *cur[part]
            } else {
                &mut self.prev[part]
            };
            hand_on(
                g,
                block,
                at,
                &mut self.strips,
                dest,
                (part, array),
                &out[lo..hi],
            );
        }
    }

    /// A level of both parts on one shell, as `level_one` twice, in one pass over the shell's rows.
    fn level_pair(&mut self, ctx: &Ctx, at: At, cur: &mut [&mut [i64]; 2]) {
        let block = ctx.block;
        let g = self.geom;
        let base = block.start[at.q];
        let n = at.q / 2 + 1;
        let rows = shell_rows(block, ctx.op, at.q);
        let split = (at.j - 1) * RING * g.cap;
        let slot = (at.q % RING) * g.cap;
        let [ring0, ring1] = &mut self.ring;
        let (lower0, upper0) = ring0.split_at_mut(split);
        let (lower1, upper1) = ring1.split_at_mut(split);
        let out0 = &mut upper0[slot..slot + n];
        let out1 = &mut upper1[slot..slot + n];
        let (below0, minus0) = level_inputs(block, at, cur[0], &self.prev[0], lower0);
        let (below1, minus1) = level_inputs(block, at, cur[1], &self.prev[1], lower1);
        let minus = match (minus0, minus1) {
            (Some(m0), Some(m1)) => Some([m0, m1]),
            _ => None,
        };
        let (lo, hi) = at.own();
        let terms = [term(ctx.table, at.kk, 0), term(ctx.table, at.kk, 1)];
        // Both terms exist or neither (a depends on kk alone), and they go into different sums.
        let fused = match terms {
            [Some((part0_re, c0)), Some((_, c1))] => match (i64::try_from(c0), i64::try_from(c1)) {
                (Ok(c0), Ok(c1)) => Some((part0_re, [c0, c1])),
                _ => None,
            },
            _ => None,
        };
        let sums = fused.map(|(part0_re, coef)| {
            let (sum_re, sum_im) = (
                &mut self.acc_re[base..base + n],
                &mut self.acc_im[base..base + n],
            );
            Sums {
                dest: if part0_re {
                    [sum_re, sum_im]
                } else {
                    [sum_im, sum_re]
                },
                coef,
                own: (lo, hi),
            }
        });
        shell_level_pair(
            &rows,
            [below0, below1],
            minus,
            shift_of(at.kk),
            [&mut *out0, &mut *out1],
            at.span,
            sums,
        );
        for (part, out) in [(0, &*out0), (1, &*out1)] {
            if let (None, Some((into_re, coef))) = (fused, terms[part]) {
                // A coefficient wider than 64 bits (none is): the 128-bit product, part by part.
                let acc = if into_re {
                    &mut self.acc_re[base + lo..base + hi]
                } else {
                    &mut self.acc_im[base + lo..base + hi]
                };
                accumulate(acc, coef, &out[lo..hi]);
            }
            if let Some(array) = at.hand_on() {
                let dest: &mut [i64] = if array == 1 {
                    &mut *cur[part]
                } else {
                    &mut self.prev[part]
                };
                hand_on(
                    g,
                    block,
                    at,
                    &mut self.strips,
                    dest,
                    (part, array),
                    &out[lo..hi],
                );
            }
        }
    }
}

/// The shift `step` takes: T_1 = Htilde T_0 at 2^-Q, every later level 2 Htilde T at 2^-(Q - 1).
fn shift_of(kk: usize) -> u32 {
    if kk == 1 {
        Q
    } else {
        Q - 1
    }
}

/// `times`: (window count T 2^W, T), sorted by the count.
#[allow(clippy::too_many_arguments)]
fn point(
    n: i128,
    k_in: usize,
    delta: Rat,
    y: Rat,
    times: &[(i128, Rat)],
    w: u32,
    sab: &Sabotage,
    layout: Layout,
) {
    let began = Instant::now();
    let k = k_in.min(usize::try_from(n).unwrap());
    let block = Block::new(n, k, sab.drop_even_root);
>>>
REASON: The streaming layout's code, before `point`: Layout; the gather kernel (row_sum, shell_level, shell_level_pair with Sums); the terms (term, accumulate); the sweep geometry (Geom, Pass, At, level_inputs); the tile hand-on (strip_at, hand_on); Stream (new, array_bytes, window, swap_margin, sweep, level_one, level_pair); shift_of; and point's signature taking the layout (8 parameters, so the clippy allow the repo uses elsewhere). Gate on the whole change: fmt --check exit 0, clippy --release -D warnings exit 0 on all crates in a fresh target, clippy --all-targets exit 0, float_used=0 (scan code_hits=0, CI grep empty), binary d892971d from source ed75eca8, a fresh-target rebuild byte-equal (1). Exact (DERIVED D1 to D5, MEASURED): grid 20 of 20 rows, 800 fields besides array_bytes with 0 differing, and the whole file with array_bytes set to the filed value byte for byte the filed receipt (sha256 4a1a2778); baseline 58 of 58 allowed rows, 2320 fields with 0 differing, the allowed-rows file equal (ff57d5e8), the 6 rows of the 2 reserved runs NOT_MEASURED (reason RESERVED); smoke 351 of 351. Applies to the dyadic engine (8d8afe48, the dyadic lane's H1 to H8 applied); the 8 engine HOLDs in order give ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6 byte for byte.

HOLD H3 | file=src/bin/polariton_first_correction.rs | severity=HIGH
OLD<<<

    let (mut re, mut im) = (vec![0i64; block.dim], vec![0i64; block.dim]);
    re[0] = i64::try_from(ONE).unwrap();
    let mut sum = vec![0i128; block.dim];
    let (mut acc_re, mut acc_im) = (vec![0i128; block.dim], vec![0i128; block.dim]);
    let (mut p0, mut p1, mut p2) = (
        vec![0i64; block.dim],
        vec![0i64; block.dim],
        vec![0i64; block.dim],
    );
    let mut eps_tail = 0i128; // at 2^62, outward
    let mut eps_poly = 0i128;
    let mut eps_round = 0i128;
>>>
NEW<<<

    let (mut re, mut im) = (vec![0i64; block.dim], vec![0i64; block.dim]);
    re[0] = i64::try_from(ONE).unwrap();
    // The point layout's work vectors; the streaming layout keeps its own arrays and leaves these empty.
    let dense = match layout {
        Layout::Dense => block.dim,
        Layout::Stream { .. } => 0,
    };
    let mut sum = vec![0i128; dense];
    let (mut acc_re, mut acc_im) = (vec![0i128; dense], vec![0i128; dense]);
    let (mut p0, mut p1, mut p2) = (vec![0i64; dense], vec![0i64; dense], vec![0i64; dense]);
    let mut stream = match layout {
        Layout::Stream { depth, tile } => Some(Stream::new(&block, depth, tile, run_degree)),
        Layout::Dense => None,
    };
    let ctx = Ctx {
        block: &block,
        op: &op,
        table: &table,
    };
    let mut eps_tail = 0i128; // at 2^62, outward
    let mut eps_poly = 0i128;
    let mut eps_round = 0i128;
>>>
REASON: point's work vectors sized by layout (block.dim for point, 0 for stream, so a stream run holds only its own arrays), the Stream built from depth, tile and the run's degree, and the Ctx the sweeps read. Applies to the dyadic engine (8d8afe48, the dyadic lane's H1 to H8 applied); the 8 engine HOLDs in order give ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6 byte for byte.

HOLD H4 | file=src/bin/polariton_first_correction.rs | severity=HIGH
OLD<<<
        eps_poly += rho;
        eps_round += per_window_units;
        // The window: exp(-i E h Htilde) on Re and on Im.
        acc_re.fill(0);
        acc_im.fill(0);
        for part in 0..2 {
            let source: &[i64] = if part == 0 { &re } else { &im };
            if source.iter().all(|&v| v == 0) {
                continue;
            }
            p0.copy_from_slice(source);
            for kk in 0..=run_degree {
                let a = if kk < table.len() {
                    table[kk] * if kk == 0 { 1 } else { 2 }
                } else {
                    0
                };
                let phase = (kk + part * 3) % 4; // part 1 multiplies by i = (-i)^3
                if a != 0 {
                    let (dest_is_re, sign) = match phase {
                        0 => (true, 1i128),
                        1 => (false, -1i128),
                        2 => (true, -1i128),
                        _ => (false, 1i128),
                    };
                    let cur: &[i64] = if kk == 0 { &p0 } else { &p1 };
                    let target = if dest_is_re { &mut acc_re } else { &mut acc_im };
                    for (t, &v) in target.iter_mut().zip(cur.iter()) {
                        *t += (sign * a * i128::from(v)) >> 16;
                    }
                }
                if kk == run_degree {
                    break;
                }
                if kk == 0 {
                    step(&block, &op, &p0, None, false, &mut sum, &mut p1);
                } else {
                    step(&block, &op, &p1, Some(&p0), true, &mut sum, &mut p2);
                    std::mem::swap(&mut p0, &mut p1);
                    std::mem::swap(&mut p1, &mut p2);
                }
                applies += 1;
            }
        }
        for i in 0..block.dim {
            re[i] = i64::try_from(acc_re[i] >> (Q - 16)).expect("re");
            im[i] = i64::try_from(acc_im[i] >> (Q - 16)).expect("im");
            if sab.norm_drift {
                re[i] += re[i] >> 32;
                im[i] += im[i] >> 32;
            }
        }
        done += 1;
>>>
NEW<<<
        eps_poly += rho;
        eps_round += per_window_units;
        // The window: exp(-i E h Htilde) on Re and on Im.
        if let Some(st) = stream.as_mut() {
            applies += st.window(&ctx, run_degree, &mut re, &mut im, sab.norm_drift);
        } else {
            acc_re.fill(0);
            acc_im.fill(0);
            for part in 0..2 {
                let source: &[i64] = if part == 0 { &re } else { &im };
                if source.iter().all(|&v| v == 0) {
                    continue;
                }
                p0.copy_from_slice(source);
                for kk in 0..=run_degree {
                    let a = if kk < table.len() {
                        table[kk] * if kk == 0 { 1 } else { 2 }
                    } else {
                        0
                    };
                    let phase = (kk + part * 3) % 4; // part 1 multiplies by i = (-i)^3
                    if a != 0 {
                        let (dest_is_re, sign) = match phase {
                            0 => (true, 1i128),
                            1 => (false, -1i128),
                            2 => (true, -1i128),
                            _ => (false, 1i128),
                        };
                        let cur: &[i64] = if kk == 0 { &p0 } else { &p1 };
                        let target = if dest_is_re { &mut acc_re } else { &mut acc_im };
                        for (t, &v) in target.iter_mut().zip(cur.iter()) {
                            *t += (sign * a * i128::from(v)) >> 16;
                        }
                    }
                    if kk == run_degree {
                        break;
                    }
                    if kk == 0 {
                        step(&block, &op, &p0, None, false, &mut sum, &mut p1);
                    } else {
                        step(&block, &op, &p1, Some(&p0), true, &mut sum, &mut p2);
                        std::mem::swap(&mut p0, &mut p1);
                        std::mem::swap(&mut p1, &mut p2);
                    }
                    applies += 1;
                }
            }
            for i in 0..block.dim {
                re[i] = i64::try_from(acc_re[i] >> (Q - 16)).expect("re");
                im[i] = i64::try_from(acc_im[i] >> (Q - 16)).expect("im");
                if sab.norm_drift {
                    re[i] += re[i] >> 32;
                    im[i] += im[i] >> 32;
                }
            }
        }
        done += 1;
>>>
REASON: The window: stream calls Stream::window and adds the applies it returns (degree per window for each part with a nonzero source, as point counts them); point runs its window as before, the same statements re-indented under else (out/polariton_first_correction.rs.ignore-whitespace.diff shows no line of it changed). Applies to the dyadic engine (8d8afe48, the dyadic lane's H1 to H8 applied); the 8 engine HOLDs in order give ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6 byte for byte.

HOLD H5 | file=src/bin/polariton_first_correction.rs | severity=HIGH
OLD<<<
            } else {
                format!("sabotage={}|", sab.name)
            };
            let array_bytes = block.dim * 120;
            println!(
                "POLARITON_FIRST_CORRECTION_READ|{tag}N={big}|K={k}|even_states={}|array_bytes={array_bytes}|u=1|x={}|y={}|delta={}|t={}|window=2^-{w}|c={}|E={}|degree={degree}|reach={reach}|applies={applies}|elem_err_units={}|jbar_e18={}|f_e18={}|A_e18={}|B_e18={}|C1_e18={}|C2_e18={}|A1_e18={}|D2_e18={}|V2_e18={}|energy_e18={}|norm_off_e18={}|eps_tail_e18={}|eps_poly_e18={}|eps_round_e18={}|eps_e18={}|C1_err_e18={}|A1_err_e18={}|V2_lo_e18={}|V2_hi_e18={}|norm_B_s20={bnorm}|tail_max_e18={}|leak_max_e18={}|leak_sum_e18={}|float_used=0|json=0",
                block.dim,
>>>
NEW<<<
            } else {
                format!("sabotage={}|", sab.name)
            };
            let (array_bytes, layout_text) = match &stream {
                Some(st) => (
                    st.array_bytes(block.dim),
                    format!(
                        "|layout=stream|depth={}|tile={}|array_bytes_point_layout={}",
                        st.geom.depth,
                        st.geom.tile,
                        block.dim * 120
                    ),
                ),
                None => (block.dim * 120, String::new()),
            };
            println!(
                "POLARITON_FIRST_CORRECTION_READ|{tag}N={big}|K={k}|even_states={}|array_bytes={array_bytes}|u=1|x={}|y={}|delta={}|t={}|window=2^-{w}|c={}|E={}|degree={degree}|reach={reach}|applies={applies}|elem_err_units={}|jbar_e18={}|f_e18={}|A_e18={}|B_e18={}|C1_e18={}|C2_e18={}|A1_e18={}|D2_e18={}|V2_e18={}|energy_e18={}|norm_off_e18={}|eps_tail_e18={}|eps_poly_e18={}|eps_round_e18={}|eps_e18={}|C1_err_e18={}|A1_err_e18={}|V2_lo_e18={}|V2_hi_e18={}|norm_B_s20={bnorm}|tail_max_e18={}|leak_max_e18={}|leak_sum_e18={}|float_used=0|json=0",
                block.dim,
>>>
REASON: array_bytes per layout: point dim x 120 as before; stream the bytes of the vectors it holds (operator and state 48 per state, sums 32, prev 16 when a window takes more than one sweep, rings, strips). The COST suffix carries the point layout's value beside it; for point the suffix is empty. Applies to the dyadic engine (8d8afe48, the dyadic lane's H1 to H8 applied); the 8 engine HOLDs in order give ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6 byte for byte.

HOLD H6 | file=src/bin/polariton_first_correction.rs | severity=HIGH
OLD<<<
                e18_s60(leak_sum >> 2),
            );
            eprintln!(
                "POLARITON_FIRST_CORRECTION_COST|N={big}|K={k}|even_states={}|array_bytes={array_bytes}|delta={}|y={}|t={}|ms={}|peak_rss_kB={}|json=0",
                block.dim,
                delta.text(),
                y.text(),
>>>
NEW<<<
                e18_s60(leak_sum >> 2),
            );
            eprintln!(
                "POLARITON_FIRST_CORRECTION_COST|N={big}|K={k}|even_states={}|array_bytes={array_bytes}|delta={}|y={}|t={}|ms={}|peak_rss_kB={}{layout_text}|json=0",
                block.dim,
                delta.text(),
                y.text(),
>>>
REASON: The COST row carries the suffix: for stream layout=stream|depth|tile|array_bytes_point_layout (the filed value) beside its own array_bytes; the point row is the same bytes as before. Applies to the dyadic engine (8d8afe48, the dyadic lane's H1 to H8 applied); the 8 engine HOLDs in order give ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6 byte for byte.

HOLD H7 | file=src/bin/polariton_first_correction.rs | severity=HIGH
OLD<<<
                Some(rest) => parse_sabotage(rest),
                None => Sabotage::default(),
            };
            point(n, k, delta, y, &times, w, &sab);
        }
        "bessel" => {
            let z = parse_rat(get(2));
>>>
NEW<<<
                Some(rest) => parse_sabotage(rest),
                None => Sabotage::default(),
            };
            point(n, k, delta, y, &times, w, &sab, Layout::Dense);
        }
        "stream" => {
            let n: i128 = get(2).parse().expect("N");
            let k: usize = get(3).parse().expect("K");
            let delta = parse_rat(get(4));
            let y = parse_rat(get(5));
            let w: u32 = get(6).parse().expect("W");
            let mut times: Vec<(i128, Rat)> =
                get(7).split(',').map(|v| window_time(v, w)).collect();
            times.sort_unstable_by_key(|&(windows, _)| windows);
            let (mut sab, mut depth, mut tile) = (Sabotage::default(), 8usize, 512usize);
            for extra in args.iter().skip(8) {
                if let Some(rest) = extra.strip_prefix("sabotage=") {
                    sab = parse_sabotage(rest);
                } else if let Some(rest) = extra.strip_prefix("depth=") {
                    depth = match rest.parse() {
                        Ok(d) if d >= 2 => d,
                        _ => {
                            eprintln!("depth {rest} is not an integer of at least 2");
                            std::process::exit(2);
                        }
                    };
                } else if let Some(rest) = extra.strip_prefix("tile=") {
                    tile = match rest.parse() {
                        Ok(t) if t >= 1 => t,
                        _ => {
                            eprintln!("tile {rest} is not a positive integer");
                            std::process::exit(2);
                        }
                    };
                } else {
                    eprintln!("unknown argument {extra}");
                    std::process::exit(2);
                }
            }
            if tile < depth {
                eprintln!("tile {tile} is narrower than depth {depth}");
                std::process::exit(2);
            }
            point(
                n,
                k,
                delta,
                y,
                &times,
                w,
                &sab,
                Layout::Stream { depth, tile },
            );
        }
        "bessel" => {
            let z = parse_rat(get(2));
>>>
REASON: main: point passes Layout::Dense; the stream mode reads point's arguments, then depth= (at least 2, default 8), tile= (at least 1 and at least depth, default 512) and sabotage= in any order, and refuses anything else with exit 2 and empty stdout (smoke: 11 refusals). Applies to the dyadic engine (8d8afe48, the dyadic lane's H1 to H8 applied); the 8 engine HOLDs in order give ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6 byte for byte.

HOLD H8 | file=src/bin/polariton_first_correction.rs | severity=LOW
OLD<<<
            rows(n, k, parse_rat(get(4)), parse_rat(get(5)));
        }
        _ => {
            eprintln!("usage: polariton_first_correction point N K DELTA Y W T[,T2,...] [sabotage=NAME] | bessel NUM/DEN | rows N K DELTA Y");
            std::process::exit(2);
        }
    }
>>>
NEW<<<
            rows(n, k, parse_rat(get(4)), parse_rat(get(5)));
        }
        _ => {
            eprintln!("usage: polariton_first_correction point N K DELTA Y W T[,T2,...] [sabotage=NAME] | stream N K DELTA Y W T[,T2,...] [depth=D] [tile=M] [sabotage=NAME] | bessel NUM/DEN | rows N K DELTA Y");
            std::process::exit(2);
        }
    }
>>>
REASON: The usage message names the stream mode and its arguments. Applies to the dyadic engine (8d8afe48, the dyadic lane's H1 to H8 applied); the 8 engine HOLDs in order give ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6 byte for byte.

HOLD H9 | file=polariton-first-correction/SHA256SUMS | severity=HIGH
OLD<<<
ad121216d53abb414016edecec2e44cfef1116394f957130e2b1de080ac8dfc5 ../src/bin/polariton_first_correction.rs
>>>
NEW<<<
ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6 ../src/bin/polariton_first_correction.rs
>>>
REASON: The workflow's step "The frozen row, and this stage's files, at their pins" runs sha256sum --strict -c --quiet SHA256SUMS in polariton-first-correction/, and the file pins the engine source at its 38ce248 hash, so any engine change fails that step at once. Checked (MEASURED, out/SUMS-CHECK.txt): the check exits 0 on 38ce248 as archived, 1 with this source and the filed line ("../src/bin/polariton_first_correction.rs: FAILED"), 0 with NEW. With the dyadic change alone the line takes 8d8afe48e5006cc146dd05bdd4c9bfdc068463b7aaa43faf362386b0a0d59228; the dyadic lane's HOLDS leave this line as filed.

HOLD H10 | file=.github/workflows/polariton-first-correction.yml | severity=MEDIUM
OLD<<<
          python3 -I -X utf8 $D/route_first_correction.py integrator polariton/second-seat/recheck-ce44be7/contact "$RUNNER_TEMP/cheb/release/cheb" "$RUNNER_TEMP/tables" grid.hbp 4
>>>
NEW<<<
          python3 -I -X utf8 $D/route_first_correction.py integrator polariton/second-seat/recheck-ce44be7/contact "$RUNNER_TEMP/cheb/release/cheb" "$RUNNER_TEMP/tables" grid.hbp 4
      - name: The streaming layout reproduces the grid and the baseline's 40 runs outside the bridge's reserved points, every field but array_bytes
        run: |
          set -euo pipefail
          D=polariton-first-correction
          printf '#!/usr/bin/env bash\nshift\nexec "%s" stream "$@"\n' "$PWD/target/release/polariton_first_correction" > stream-engine.sh
          chmod +x stream-engine.sh
          strip() { sed -E 's/\|array_bytes=[0-9]+\|/|array_bytes=X|/' "$1"; }
          python3 -I -X utf8 $D/run_stage.py ./stream-engine.sh $D/PLAN.hbp grid grid-stream.hbp grid-stream-cost.hbp 4
          cat grid-stream-cost.hbp
          cmp <(strip grid-stream.hbp) <(strip $D/RECEIPT-GRID.hbp)
          # The two baseline runs at N = 729, y = 2/27 (delta = 0, 1/2) sit in the bridge's reserved set and stay unrun here.
          grep -v -E '^FC_RUN\|stage=baseline\|.*\|N=729\|K=729\|delta=(0|1/2)\|y=2/27\|' $D/PLAN.hbp > plan-allowed-stream.hbp
          python3 -I -X utf8 $D/run_stage.py ./stream-engine.sh plan-allowed-stream.hbp baseline baseline-stream.hbp baseline-stream-cost.hbp 4
          cat baseline-stream-cost.hbp
          grep -v -E '\|N=729\|K=729\|.*\|y=2/27\|delta=(0|1/2)\|' $D/RECEIPT-BASELINE.hbp | sed -e '1s/runs=42/runs=40/' -e '$s/runs=42/runs=40/' > receipt-allowed-stream.hbp
          cmp <(strip baseline-stream.hbp) <(strip receipt-allowed-stream.hbp)
>>>
REASON: run_stage.py calls the engine's point mode, so the workflow as filed checks the point path only. This step runs the stream mode through the same run_stage.py (a two-line wrapper turns its point into stream) on the grid and on the baseline's 40 allowed runs, and compares each receipt with the filed one with every array_bytes value blanked, which is line 451's gate. Checked on this lane's own stage outputs, text only (MEASURED, out/H10-TEXT-CHECK.txt): both cmp lines exit 0, the plan filter leaves 40 baseline runs, the receipt filter gives 60 lines with sha256 ff57d5e8; the OLD line occurs once in the workflow. The hosted run itself NOT_MEASURED (nothing pushed). About 10 minutes of runner time at this lane's 4-at-a-time stage times (grid 7 min 25 s, baseline 3 min 4 s here).

HOLD H11 | file=polariton-bridge/ENGINE-CHANGES.hbp (after the dyadic lane's H11 row, or wherever the seat files engine receipts) | severity=MEDIUM
OLD<<<
>>>
NEW<<<
BRIDGE_ENGINE_CHANGE_RESULT|engine=the_quantum_engine_src/bin/polariton_first_correction.rs|change=streaming_layout(temporal_blocking_over_shells,tiles_in_m)_as_mode_stream(BRIDGE_ENGINE_CHANGE_line_451)|from_sha256=8d8afe48e5006cc146dd05bdd4c9bfdc068463b7aaa43faf362386b0a0d59228(the_dyadic_engine)|source_sha256=ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6|binary_sha256=d892971d6c0023534a2cbfac2631a7d983eeeab6853ffb6524b589e74795f270(rustc_1.81.0,x86_64-unknown-linux-gnu;a_binary_built_elsewhere_carries_its_own)|defaults=depth_8,tile_512|gate=cargo_+1.81_fmt_--check_exit_0,cargo_+1.81_clippy_--release_--_-D_warnings_exit_0,float_used=0|RECEIPT-GRID.hbp=every_field_but_array_bytes_byte_for_byte(20_rows,800_fields,0_differing),whole_file_with_array_bytes_set_to_filed_sha256_4a1a277885015a5e937a028d767c617878ae9a05e75bade9eee3e14f0e07e480|RECEIPT-BASELINE.hbp=58_of_64_rows(2320_fields,0_differing),6_rows_at_N=729,y=2/27_NOT_MEASURED(reason=RESERVED)|array_bytes=own_layout,beside_the_filed_value_in_the_COST_row|controls=6_of_6_checks(real_passes,each_sabotage_fails_as_CONTROLS.hbp_names,crosscheck_passes)|speedup_over_point_single_runs_interleaved_3_repeats=K1200:2.102_(2.079_to_2.117),K1600:2.150_(2.127_to_2.173),K6561_full_space:1.978_(1.940_to_2.006)|speedup_over_point_4_runs_at_a_time_K6561=1.928_(1.862_to_1.993,2_repeats)|peak_rss_kB_K6561=stream_1016184,point_1263972|timed_binary_sha256=72c7d3cf719feed849d097fbe36d5fce319d0b9272fb5a2429089010d16d3932(source_7853c9d6,one_line_apart:the_unknown-mode_usage_message)|by=opus55,bridge-engine-stream-20261106|tag=MEASURED|json=0
>>>
REASON: Line 451 asks for the change's toolchain gate, the reproduction of every field but array_bytes, and its peak memory and time as COST rows; and, for any engine before a blind run, the changed binary's sha256 in a row. This row files them beside the frozen rows, so PREDICTION.hbp keeps its sha256 fadd8412. The hash is the Linux build's; the blind runs' row needs the hash of the binary that runs them.

HOLD H12 | file=polariton-bridge/README.md | severity=NOTE
OLD<<<

## Order (`BRIDGE_ORDER`)
>>>
NEW<<<

The quantum engine's streaming layout (`stream`, line 451) reproduces both first-correction receipts in every field
but array_bytes. On the full space at N = 6561 (the allowed point delta = 1/2, y = 1/324) it ran 1.978 times as fast
as `point` one run at a time (3 interleaved repeats, spread 1.940 to 2.006) and 1.928 times as fast four at a time
(2 repeats, spread 1.862 to 1.993), MEASURED, at a peak of 1.04 GB against 1.29 GB per run. The hours above are at
`point`'s rate.

## Order (`BRIDGE_ORDER`)
>>>
REASON: The quantum side's paragraph gives the full-space plan at point's rate (about 10 to 14 hours at 4 runs at a time). This paragraph states the measured rate of the streaming layout at that block size, for the seat's choice of engine for those runs; it touches no prediction. With it, polariton-bridge/SHA256SUMS takes H13's line.

HOLD H13 | file=polariton-bridge/SHA256SUMS | severity=NOTE
OLD<<<
1ce815d50a62a08d523c557be5444ec46cc2ba10cbe4504dbd499ba85ad354cc README.md
>>>
NEW<<<
4c506f88a22480f4af6e11d3c4af71e890f5a0529c7ec147875569acdb44535c README.md
>>>
REASON: Only with H12: the README's new sha256, computed from the filed README with H12's NEW applied (LF endings, as filed).
