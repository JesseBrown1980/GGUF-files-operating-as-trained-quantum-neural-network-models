**Verdict: PASS_WITH_HOLDS.** Neither engine change has a correctness defect I could find. What is left is one gate item that needs the operator's word, and some gaps in the CI checks.

All work is in `C:/tmp/opus55/bridge-engine-review-quantum-20261106/`. The worktree is untouched: HEAD 38ce248, status clean. No file in either lane folder is newer than the start of this review. Git writes, pushes and GitHub writes: 0. The one gate item open is the whole-file byte check of `RECEIPT-BASELINE.hbp`: 6 of its rows sit at a reserved point (y = 2/27 at N = 729, plan runs 27 and 32). Those 6 rows are NOT_MEASURED (reason RESERVED) and need the operator's word.

### Gate results (MEASURED, `logs/gate-exits-{orig,dyadic,stream}.hbp`)
Three trees were built, each in a fresh target dir inside my folder: 38ce248 (source ad121216…), dyadic (8d8afe48…) and streaming (ed75eca8…). The toolchain is rustc 1.81.0 (eeb90cda1 2024-09-04).

| Step | orig | dyadic | streaming |
|---|---|---|---|
| `cargo +1.81 fmt -- --check` | 0 | 0 | 0 |
| `fmt --all -- --check` | 0 | 0 | 0 |
| `clippy --release -- -D warnings` | 0 | 0 | 0 |
| `clippy --release --all-targets` | 0 | 0 | 0 |
| clippy in the workflow's form (`--locked --offline --bin`) | 0 | 0 | 0 |
| `build --release --locked --offline` | 0 | 0 | 0 |
| CI grep `\bf(32\|64)\b` in src and tests | 0 hits | 0 hits | 0 hits |
| binary sha256 | 8f06e8b0… (555,192 B) | cc75d83f… (559,544 B) | d892971d… (599,040 B) |

- **Rebuilt binaries:** all three hashes equal the lanes' hashes.
- **Clippy coverage:** a verbose run checks 6 crates on the streaming tree.
- **float_used = 0:** my own scanner (comments, strings, chars and raw strings blanked by a small lexer) finds 0 code hits in 1059, 1080 and 1903 lines, and 0 in the 53 .rs files of src and tests. Its self-test finds 10 of 10 planted floats and gives 0 hits on 16 clean lines.

### Reproduction (MEASURED, byte for byte)
- **Streaming binary, `stream` mode, default layout:** 78 of 78 allowed rows (20 grid, 58 baseline).
  - 3198 fields compared; 78 differ, and all 78 are array_bytes.
  - With the filed array_bytes put back, 78 of 78 rows are byte-equal.
  - array_bytes at K = 1200 is 35,674,848, which matches the layout's own count (DERIVED).
- **Dyadic binary, `point` mode:** 27 of 27 rows (7 grid, 20 baseline), 1107 fields, 0 differing.
- **Streaming binary, `point` mode:** 27 of 27 rows (a different sample), 1107 fields, 0 differing.
- **Slowest rows:** both point-mode samples include the slowest grid row (plan 13: K = 1600, δ = 1/4, y = 1/81) and the slowest baseline row (plan 38: N = 6561, K = 1600, y = 1/81).
- **Same output as 38ce248:** 11 of 11 cases for both changed binaries — integer T including repeated and unsorted times, W = 4, all 4 sabotages, plus the `rows` and `bessel` modes.
- **My own differential tests:** 70 of 70 checks over 12 configs and 26 stream layouts. They cover:
  - the full space at N = 6561 (7 tiles), and N = 6561 at K = 2400 (3 tiles at the default tile);
  - full spaces at N = 729, 243 and 81, with dyadic reads up to 317/64;
  - the 4 sabotages at 8/64 tiles, and K = 1 and N = 6 edge cases;
  - applies = run_degree·(2·T·2^W − 1) on every row;
  - 6 of 6 off-grid or non-positive times refused with exit 2 and empty stdout.
- **Cost on the shared host, 4 runs at a time:** stream-all 60 runs, 2,548,887 engine-ms, peak 63,240 kB. Dyadic sample 21 runs, 2,244,470 ms, peak 77,256 kB. Streaming-binary point sample 22 runs, 1,988,664 ms, peak 77,356 kB.

### Reading the diff (DERIVED)
- **Dyadic, `window_time`:**
  - T is read in lowest terms and accepted when t.n ≥ 1 and t.d divides 2^W.
  - The window count is a checked multiply, and the `%` only runs when t.d ≥ 1.
  - A read happens after window T·2^W, and every eps term is a sum over the windows done.
  - No bound formula and no rounding direction changes.
  - An integer T prints exactly as before.
- **Streaming, the row sums:** each row gathers the same 7 products that `step` scatters into it, with the same floor and the same subtraction. Partial sums stay below 2^127.
- **Streaming, the rings:** ring slot q mod 5 is written at sweep position s, read through s+4 and rewritten at s+5.
- **Streaming, prev and cur:** both are overwritten only after their last read, for depth ≥ 2.
- **Streaming, tile margins:** level j computes L−j margin rows, which is what level j+1 needs.
- **Streaming, strips:** the next tile's margin is saved before the hand-on writes over it, and the two buffers alternate.
- **Streaming, start position:** the sweep's start, 2(T0−L), has 2 positions of slack.
- **Streaming, index arithmetic:** every subtraction is guarded by `checked_sub` or by m0 ≥ tile ≥ depth.
- **"The guard and its opt-in flag":**
  - `stream` is a mode chosen by name.
  - It refuses depth < 2, tile < depth and unknown arguments with exit 2.
  - `window_time` refuses off-grid times.
- **NOTE, in-engine guard:** the quantum engine itself starts at any point. The reserved set is held by the lanes' wrapper scripts and, with the dyadic H9/H10, by the CI filters. Whether to add an in-engine guard is the seat's choice.
- **NOTE, pre-existing code outside the diff:** the per-window bound floor(a) + floor(b) + 1 can sit under 1 unit of 2^-62 below a + b. The √S·2^-42·‖B‖h tail floor in the same window covers it.

### Mutation (MEASURED, `out/MUTANTS.hbp`)
The harness controls M0S and M0D (unmodified sources) pass every check, and their binaries are bit-identical to the reviewed ones. All 10 planted faults are caught by at least one check.

| Mutant | Fault | Filed receipts, default layout, 7 rows | Caught by |
|---|---|---|---|
| M1 | sign | 7/7 differ | receipts, equality checks |
| M2 | factor 2 in `shift_of` | 7/7 differ | receipts, equality checks |
| M3 | dropped term in the fused rows | 7/7 differ | the gate (clippy: unused variable `x_m2`), receipts |
| M3b | dropped edge term, passes clippy | 7/7 differ | receipts, equality checks |
| M4 | off-by-one in `swap_margin`'s start | 1/7 differ (the 2-tile row) | receipts, small tiles |
| M5 | a dyadic read lands one window late | 7/7 pass | equality with the reviewed binary, the applies identity |
| M6 | wrong sum (`own.1` included) | 1/7 differ | receipts, small tiles |
| M7 | the strip buffer is always 0 | 7/7 pass | small tiles only |
| M8 | wrong ring slot | 7/7 differ | everything |
| M9 | 1/3 accepted at W = 6 | 7/7 pass | the off-grid refusal check only |

The filed receipts at the default layout miss M5, M7 and M9. The CI lines proposed in H3 and H5 catch them. Simulated behind my guard (`out/SIM-STEPS.hbp`):
- H3 exits 1 for M4, M6 and M7, and 0 for the reviewed streaming binary.
- H5 exits 1 for M5 and M9, and 0 for both reviewed binaries.

### Reserved-set check (MEASURED)
- **My runs:** the guard self-test gives 23 of 23 right with 0 processes started. My guard log shows 485 runs started (173 `point`, 300 `stream`, 6 `rows`, 6 `bessel`), 0 of them at a reserved point. The 2 reserved plan runs were dropped before start.
- **Dyadic lane:** 229 runs started (156 `point`, 53 `bessel`, 10 `rows`, 10 fockprop), 0 at a reserved point, 13 refusals.
- **Streaming lane:** 2550 runs started (307 `point`, 2243 `stream`), 0 at a reserved point, 4 refusals.
- **Rows in lane files that name a reserved point:** 27 and 24 are refusal records. The streaming lane's other 66 sit in byte-identical copies of 38ce248 files. Run outputs at a reserved point: 0 in both lanes.
- **Read rows vs guard logs:** every READ point in the lane files matches a guard-log row, 66 of 66 and 67 of 67.
- **Binary dumps:** 12 dumps, all at allowed points by their file names.

### Other checks (MEASURED)
- **Lanes' engine holds:** the dyadic H1–H8 applied to ad121216 give 8d8afe48, and the streaming H1–H8 applied on top give ed75eca8. Each OLD occurs once.
- **The lanes' other holds:** every OLD occurs exactly once.
- **CI pin step with the dyadic change alone:** it exits 1 on the engine line, which the dyadic lane's holds leave as filed (my H1 supplies the new line). With the dyadic H12 applied, it also needs the route line (H2).
- **Workflow filters in H9:** 42 → 40 baseline runs; the filtered receipt has 60 lines with sha256 ff57d5e8…; 0 rows at y = 2/27 remain.
- **Workflows after all the holds:** the YAML parses and `bash -n` passes on every `run:` body.
- **Report mismatch:** the streaming lane's report gives its H13 NEW as 4c506f88…. The README with H12 applied hashes to 33fc4804…, which is the line in the lane's own `out/HOLDS.txt` (H6 below).
- **Lane files, text checks:** the streaming lane's smoke file has 351 of 351 rows with pass=1. Its speed-ups recomputed from its own table are 2.102, 2.150 and 1.978 (DERIVED).

### Open items and slips
- **O1:** the whole-file `RECEIPT-BASELINE.hbp` check — NOT_MEASURED, reason RESERVED.
- **O2:** the hosted CI run of the change and of H1–H7 — NOT_MEASURED; this review pushed nothing.
- **O3:** a Windows MSVC build and its sha256 — NOT_MEASURED.
- **O4:** recall `:4796` answered live with count = 0 for both queries. That is an index boundary; the files are the source.
- **O5:** the fabric council query was fired as envelope council-q-1793952425346-zrpnj4 and received; its answer was not read in this lane.
- **Slips, each fixed and kept on file:**
  - S1: a `$v` inside `wsl -lc` arrived empty, and `set -u` stopped the gate before any step ran (`logs/gate-run1-var-arrived-empty/`).
  - S2: a CR count inside a quoted command substitution printed line counts; the real CR count is 0 bytes in all three sources.
  - S3: a `$?` inside `wsl -lc` wrote one non-HBP line, since rewritten.
  - S4: `repro.py` gained its `list:` rule while a phase was running; the rules the phases used are unchanged.

### Files (sha256)
`BRIDGE-ENGINE-REVIEW-QUANTUM.hbp` 6754b2bfa236a530614af5850da7578b034bfd42bb644b9d0a0a7244555f0b36 (403 rows, with a `.sha256` sidecar). Its 246 BERQ_FILE rows hash every file I made: 45 in out/, 41 scripts, 111 logs, 19 in holds-check/, 24 in mut/, plus the 3 sources and 3 binaries. Each out/ file has a `.sha256` sidecar. The main ones:
- `out/HOLDS-REVIEW.txt` d71b5a174a969d679b4c98dc486f27d9ba966d964d4d099ac33119273ef82725
- `out/MUTANTS.hbp` c870e58d603f57b82d0b884e51cc29753bb481019287d209a40726afdf3d4cdf
- `out/REPRO-stream-all.hbp` eaa30d25d2230fdc6529c8cd2b7e8d7ae27f6beaac60bf3192b4014eecec8573
- `out/REPRO-dyadic-third.hbp` f8f06c7e7bd33a1b29298503068024ff470e877603b694f4893c0ba4d5e01f68
- `out/REPRO-streambin-point-third.hbp` 83c701b240a898298e35ab0e1d08eceb36a657ac9377eb01f5c29fa7f04e8467
- `out/DIFF-review.hbp` 39ab12bedaf8eab15600b6ff3ac8a25e74b0ac168b502f81c2ec15fff3280d10
- `out/ORIG-VS-CHANGED.hbp` 19ab352210bceb6dbcdc90c88304e1dae83ef47b7796b45abfde38910c8df3db
- `out/RECEIPT-DYADIC-PROPOSED.hbp` 66e13a71d948dbadfc486d36b22015432e4e8eb92310b8492bb265ad53d94cf9
- `out/SIM-STEPS.hbp` 2db0a5921583a87fff4832aefca7a69ac2adc5f99273ec5685913d3f08730818
- `out/AUDIT-LANES.hbp` 29cf0cc9c6eb3cbd9b1345c659b75cf8d5a74cee8eefe15481b5e727d736864c
- `out/AUDIT-CLASSIFIED.hbp` 8af4517056dac0ee30f64b2a8cf3bde87891c290656dd10874e3acb6492badeb
- `out/SELF-AUDIT.hbp` 4aabb1a9cd92dd54f52988455e0aaf3c38c5c9ff166c64445e37c7827e17b473
- `out/SUMS-CHECK.hbp` fdf7f24d617d3fd98dfd0a8f7aeb4b0499a8779f984114ad1070d9b993acd30c
- `out/FLOAT-SCAN.hbp` 1c4e946f2ea569242461b2c5d778187d5d64979575280494999c8e07c02a9eb6
- `out/GUARD-SELFTEST.hbp` b5a5e536393f834bac81b75d931aeeddb6e10302a3f235156a325a1df8d58402
- `logs/guard-log.hbp` f4cde328acf1a4e11edc8a9dff676ff9ad8e7c113bfcc47507376f48752f1fca
- `scripts/guard.py` 6f2543606e7986d6c884b4eeabf2babc4e4248bb62a8c1f998acf408dd7dda1a
- `scripts/repro.py` 3ca8df9309c12a4ec83095f00006ec921495b2f76acc44af0c2d31e02f9c1b4c
- `scripts/difftest.py` 8d3622163f6573d07884466b6607e968d2056e114f1f9ac31ffd7317f414771f
- `scripts/mutants.py` 30afaa63e3d16decc9a06f629c19ffcedb104cb633a7634ba6ad510b97dcf9e0
- `scripts/float_scan.py` d5aaf40ca0f98d7f61afe509960a510f53a1d21e3e958718e5aed3310d0eacb3
- `scripts/audit_lanes.py` 8d10664ccc664148479fdc57d230e5ab66d254604e8095cc87eba1b9be3cf510
- binaries `target-{orig,dyadic,stream}/release/polariton_first_correction`: 8f06e8b0e5e34f09216b1895c8e5d079fb0659e633be84268c31168ff1c6c830 · cc75d83f0a7e07b1d95bf091455f309d2c3fb64cf8f3485222e53e4c5508b776 · d892971d6c0023534a2cbfac2631a7d983eeeab6853ffb6524b589e74795f270

### HOLDS
Every OLD below was checked to occur exactly once in the file it applies to, in the state named. Applied in order, H1 and H2 give a `SHA256SUMS` with sha256 d681b4db…, which the pin step passes with exit 0.

HOLD H1 | file=polariton-first-correction/SHA256SUMS | severity=MEDIUM
OLD<<<
ad121216d53abb414016edecec2e44cfef1116394f957130e2b1de080ac8dfc5 ../src/bin/polariton_first_correction.rs
>>>
NEW<<<
8d8afe48e5006cc146dd05bdd4c9bfdc068463b7aaa43faf362386b0a0d59228 ../src/bin/polariton_first_correction.rs
>>>
REASON: For the dyadic change merged alone. The workflow's step "The frozen row, and this stage's files, at their pins" runs sha256sum --strict -c --quiet SHA256SUMS, which pins the engine source at its 38ce248 hash; the dyadic lane's holds leave this line as filed. Measured on copies of the 38ce248 files (out/SUMS-CHECK.hbp): exit 0 as filed, exit 1 with the dyadic source and the filed line ("../src/bin/polariton_first_correction.rs: FAILED"), exit 0 with NEW. With the streaming change merged too, the stream lane's H9 (ed75eca8...) takes this line instead.

HOLD H2 | file=polariton-first-correction/SHA256SUMS | severity=LOW
OLD<<<
2567c54ea1098346cc4bb782dcc18e3dfc2873e7078f64779c3bb05a7448c42f route_first_correction.py
>>>
NEW<<<
6ac43bcc06e67e69b55200cc41f23be570b2f25a02a70d6aa960c1333f72b5eb route_first_correction.py
>>>
REASON: Only with the dyadic lane's H12 (the route's tail floor). H12 applied to the 38ce248 route gives sha256 6ac43bcc... (holds-check/route-after-h12.py), and the pin step then fails on the route line (exit 1, "route_first_correction.py: FAILED"); with this line and H1's line it exits 0 (out/SUMS-CHECK.hbp). The dyadic lane's H12 reason names the SHA256SUMS change; this is its text.

HOLD H3 | file=.github/workflows/polariton-first-correction.yml (after the stream lane's H10) | severity=MEDIUM
OLD<<<
          cmp <(strip baseline-stream.hbp) <(strip receipt-allowed-stream.hbp)
>>>
NEW<<<
          cmp <(strip baseline-stream.hbp) <(strip receipt-allowed-stream.hbp)
          # Many tiles and many sweeps, as the full space at N = 6561 takes them (7 tiles of 512 rows): the baseline's 8 runs at
          # N = 729, K = 128 and 192 at tile = depth = 8 and at tile = depth = 3, every field but array_bytes as filed.
          grep -E '^FC_RUN\|stage=baseline\|group=sweep\|N=729\|K=(128|192)\|' $D/PLAN.hbp > plan-small.hbp
          grep -E '^POLARITON_FIRST_CORRECTION_READ\|N=729\|K=(128|192)\|' $D/RECEIPT-BASELINE.hbp > receipt-small.hbp
          for opts in "depth=8 tile=8" "depth=3 tile=3"; do
            printf '#!/usr/bin/env bash\nshift\nexec "%s" stream "$@" %s\n' "$PWD/target/release/polariton_first_correction" "$opts" > stream-small.sh
            chmod +x stream-small.sh
            python3 -I -X utf8 $D/run_stage.py ./stream-small.sh plan-small.hbp baseline small.hbp small-cost.hbp 4
            grep -E '^POLARITON_FIRST_CORRECTION_READ' small.hbp > small-rows.hbp
            cmp <(strip small-rows.hbp) <(strip receipt-small.hbp)
          done
          # The dyadic reads of RECEIPT-DYADIC.hbp in the streaming layout.
          { ./stream-engine.sh point 100 40 1/2 1/20 6 1/64,1/2,33/64,3/2; ./stream-engine.sh point 243 243 -1/4 1/9 6 1/64,1/4,7/8,317/64; } > dyadic-stream.hbp
          cmp <(strip dyadic-stream.hbp) <(strip $D/RECEIPT-DYADIC.hbp)
>>>
REASON: The stream step of the stream lane's H10 runs the grid and the baseline at the default layout, where the largest block (K = 1600, 801 rows per shell) takes 2 tiles; the full-space runs at N = 6561 take 7 tiles of 512 (3281 rows), and from the third tile on the strip buffers alternate in a way 2 tiles never reach. Mutant M7 (hand_on always saves into strip 0) passes all 7 filed rows at the default layout, the two-tile K = 1200 row among them, and fails these lines (exit 1, out/SIM-STEPS.hbp); M4 and M6 fail them too. With the reviewed binary d892971d they exit 0: 8 of 8 rows at each of the two layouts and 8 of 8 dyadic rows (MEASURED, every run behind this review's guard; the hosted run NOT_MEASURED). The 8 runs take 1 to 2 s each. The last three lines read H4's receipt; without H4 they go.

HOLD H4 | file=polariton-first-correction/RECEIPT-DYADIC.hbp (new file) | severity=MEDIUM
OLD<<<
>>>
NEW<<<
POLARITON_FIRST_CORRECTION_READ|N=100|K=40|even_states=441|array_bytes=52920|u=1|x=-1/2|y=1/20|delta=1/2|t=1/64|window=2^-6|c=8|E=34|degree=14|reach=29|applies=14|elem_err_units=2|jbar_e18=302751810830722|f_e18=6055036216614|A_e18=-610356274489195|B_e18=61039590888579|C1_e18=4834289383689|C2_e18=48865836971|A1_e18=12207125489783|D2_e18=1220791817770|V2_e18=15412183766458|energy_e18=40954|norm_off_e18=0|eps_tail_e18=1160448|eps_poly_e18=0|eps_round_e18=131|eps_e18=1160583|C1_err_e18=48242044|A1_err_e18=4769111919|V2_lo_e18=15399989895183|V2_hi_e18=15424382585966|norm_B_s20=17125199|tail_max_e18=4547473|leak_max_e18=0|leak_sum_e18=0|float_used=0|json=0
POLARITON_FIRST_CORRECTION_READ|N=100|K=40|even_states=441|array_bytes=52920|u=1|x=-1/2|y=1/20|delta=1/2|t=1/2|window=2^-6|c=8|E=34|degree=14|reach=29|applies=882|elem_err_units=2|jbar_e18=328461169913141419|f_e18=6569223398262828|A_e18=-629670249749194525|B_e18=67203938393884312|C1_e18=5269792677366743|C2_e18=93725400698740|A1_e18=12593404994983890|D2_e18=1344078767877686|V2_e18=15047446747652011|energy_e18=-73980440|norm_off_e18=4|eps_tail_e18=9554739772572074|eps_poly_e18=6|eps_round_e18=4218|eps_e18=9554739772576303|C1_err_e18=1516099676747523|A1_err_e18=6735217767220145|V2_lo_e18=2528654729891724|V2_hi_e18=49763747038178470|norm_B_s20=17125199|tail_max_e18=7129659162956158|leak_max_e18=132764279126|leak_sum_e18=4431364195|float_used=0|json=0
POLARITON_FIRST_CORRECTION_READ|N=100|K=40|even_states=441|array_bytes=52920|u=1|x=-1/2|y=1/20|delta=1/2|t=33/64|window=2^-6|c=8|E=34|degree=14|reach=29|applies=910|elem_err_units=2|jbar_e18=350569020650187365|f_e18=7011380413003746|A_e18=-669935061315892286|B_e18=71790995589701858|C1_e18=5625862581352993|C2_e18=102935690085590|A1_e18=13398701226317845|D2_e18=1435819911794036|V2_e18=15955348353794696|energy_e18=-82388199|norm_off_e18=4|eps_tail_e18=11711004445022228|eps_poly_e18=6|eps_round_e18=4350|eps_e18=11711004445026589|C1_err_e18=1967748952757284|A1_err_e18=8435407220870842|V2_lo_e18=1622040268576398|V2_hi_e18=65160399605548171|norm_B_s20=17125199|tail_max_e18=8449798022866161|leak_max_e18=237519090839|leak_sum_e18=8142599990|float_used=0|json=0
POLARITON_FIRST_CORRECTION_READ|N=100|K=40|even_states=441|array_bytes=52920|u=1|x=-1/2|y=1/20|delta=1/2|t=3/2|window=2^-6|c=8|E=34|degree=14|reach=29|applies=2674|elem_err_units=2|jbar_e18=4320870588338982046|f_e18=86417411766779640|A_e18=-5681200856624040127|B_e18=951977954461193104|C1_e18=68763584488576157|C2_e18=7049556969334256|A1_e18=113624017132480802|D2_e18=19039559089223861|V2_e18=93875394697226162|energy_e18=-510012504|norm_off_e18=13|eps_tail_e18=3520151971177197624|eps_poly_e18=20|eps_round_e18=12656|eps_e18=3520151971177210304|C1_err_e18=28553144640603720692|A1_err_e18=30722959373443991145|V2_lo_e18=0|V2_hi_e18=-1|norm_B_s20=17125199|tail_max_e18=526487552618618792|leak_max_e18=881051160019192369|leak_sum_e18=147192716337786695|float_used=0|json=0
POLARITON_FIRST_CORRECTION_READ|N=243|K=243|even_states=15006|array_bytes=1800720|u=1|x=-5/4|y=1/9|delta=-1/4|t=1/64|window=2^-6|c=-123|E=185|degree=23|reach=47|applies=23|elem_err_units=2|jbar_e18=975697013342857|f_e18=8030428093356|A_e18=-8239863044763796|B_e18=732544788720350|C1_e18=5017815241565|C2_e18=8315794572|A1_e18=67817802837561|D2_e18=6029175215804|V2_e18=458292519781910|energy_e18=-1370066|norm_off_e18=0|eps_tail_e18=0|eps_poly_e18=0|eps_round_e18=1693|eps_e18=1697|C1_err_e18=8124665|A1_err_e18=1962533632|V2_lo_e18=458265253723151|V2_hi_e18=458319786696542|norm_B_s20=0|tail_max_e18=16598278|leak_max_e18=0|leak_sum_e18=0|float_used=0|json=0
POLARITON_FIRST_CORRECTION_READ|N=243|K=243|even_states=15006|array_bytes=1800720|u=1|x=-5/4|y=1/9|delta=-1/4|t=1/4|window=2^-6|c=-123|E=185|degree=23|reach=47|applies=713|elem_err_units=2|jbar_e18=258915212474750554|f_e18=2130989403084366|A_e18=-2116955412995161794|B_e18=195603895237145771|C1_e18=1456214785043831|C2_e18=5384344315339|A1_e18=17423501341523964|D2_e18=1609908602774862|V2_e18=104235447310387623|energy_e18=-313269588|norm_off_e18=0|eps_tail_e18=0|eps_poly_e18=6|eps_round_e18=27103|eps_e18=27113|C1_err_e18=8148979|A1_err_e18=1962673047|V2_lo_e18=104235423243850692|V2_hi_e18=104235471376927470|norm_B_s20=0|tail_max_e18=16598278|leak_max_e18=0|leak_sum_e18=3|float_used=0|json=0
POLARITON_FIRST_CORRECTION_READ|N=243|K=243|even_states=15006|array_bytes=1800720|u=1|x=-5/4|y=1/9|delta=-1/4|t=7/8|window=2^-6|c=-123|E=185|degree=23|reach=47|applies=2553|elem_err_units=2|jbar_e18=4502944973529581475|f_e18=37061275502301082|A_e18=-26808844831440095894|B_e18=3581940249839823258|C1_e18=42847838513727203|C2_e18=952503307693947|A1_e18=220648928653827949|D2_e18=29480989710615829|V2_e18=568126087626152859|energy_e18=221360248|norm_off_e18=-1|eps_tail_e18=0|eps_poly_e18=24|eps_round_e18=94861|eps_e18=94889|C1_err_e18=8422374|A1_err_e18=1963308987|V2_lo_e18=568126077404237151|V2_hi_e18=568126097848068662|norm_B_s20=0|tail_max_e18=16598278|leak_max_e18=0|leak_sum_e18=12|float_used=0|json=0
POLARITON_FIRST_CORRECTION_READ|N=243|K=243|even_states=15006|array_bytes=1800720|u=1|x=-5/4|y=1/9|delta=-1/4|t=317/64|window=2^-6|c=-123|E=185|degree=23|reach=47|applies=14559|elem_err_units=2|jbar_e18=12824027854877149052|f_e18=105547554361128798|A_e18=-9911909779141928616|B_e18=-11765724811560247478|C1_e18=235770491176793358|C2_e18=10985070968810232|A1_e18=81579504355077601|D2_e18=96837241247409443|V2_e18=14113758464009152|energy_e18=12257098|norm_off_e18=-1|eps_tail_e18=0|eps_poly_e18=137|eps_round_e18=536984|eps_e18=537125|C1_err_e18=8913137|A1_err_e18=1963804646|V2_lo_e18=14113757783974917|V2_hi_e18=14113759144043405|norm_B_s20=0|tail_max_e18=16598278|leak_max_e18=0|leak_sum_e18=68|float_used=0|json=0
>>>
REASON: Every filed receipt reads at integer T, so the byte checks see the window count only at multiples of 64 windows. Mutant M5 (a dyadic read one window late) passes all 7 filed rows and fails a byte check of dyadic reads; mutant M9 (1/3 accepted at W = 6) passes both and fails only a refusal check (out/MUTANTS.hbp). These 8 rows are the reviewed dyadic binary cc75d83f at two allowed points: N = 100, K = 40, delta = 1/2, y = 1/20 at t = 1/64, 1/2, 33/64, 3/2 (a block with leak), and the full space N = 243, delta = -1/4, y = 1/9 at t = 1/64, 1/4, 7/8, 317/64 (317 windows). The streaming binary's point mode prints the same bytes and its stream mode the same but array_bytes (out/RECEIPT-DYADIC-CHECK.hbp). The file is these 8 rows with LF endings and a final LF: 5732 bytes, sha256 66e13a71d948dbadfc486d36b22015432e4e8eb92310b8492bb265ad53d94cf9. H5 is the step that reads it.

HOLD H5 | file=.github/workflows/polariton-first-correction.yml | severity=MEDIUM
OLD<<<
      - name: The route builds the Hamiltonian in the full Fock space and meets the engine's rows, parity, bandwidth and interval
        run: python3 -I -X utf8 polariton-first-correction/route_first_correction.py rows target/release/polariton_first_correction
>>>
NEW<<<
      - name: The route builds the Hamiltonian in the full Fock space and meets the engine's rows, parity, bandwidth and interval
        run: python3 -I -X utf8 polariton-first-correction/route_first_correction.py rows target/release/polariton_first_correction
      - name: Reads at multiples of the window reproduce RECEIPT-DYADIC.hbp at two allowed points, and an off-grid time is refused
        run: |
          set -euo pipefail
          E=target/release/polariton_first_correction
          { $E point 100 40 1/2 1/20 6 1/64,1/2,33/64,3/2; $E point 243 243 -1/4 1/9 6 1/64,1/4,7/8,317/64; } > dyadic.hbp
          cmp dyadic.hbp polariton-first-correction/RECEIPT-DYADIC.hbp
          rc=0
          $E point 100 40 1/2 1/20 6 1/2,1/3 > off-grid.hbp 2> off-grid.err || rc=$?
          test "$rc" = 2
          test ! -s off-grid.hbp
>>>
REASON: The step for H4's receipt, placed after the route's rows step; it applies before or after the lanes' H9 and H10, whose text it leaves as it is. Simulated with the engine behind this review's guard (out/SIM-STEPS.hbp): exit 0 with the dyadic binary cc75d83f and with the streaming binary d892971d; exit 1 with M5 (cmp differs at byte 161 of row 1, t = 1/64) and with M9 (the off-grid run exits 0 and prints 1496 bytes). The runs take under 5 s. Hosted run NOT_MEASURED.

HOLD H6 | file=polariton-bridge/SHA256SUMS | severity=LOW
OLD<<<
1ce815d50a62a08d523c557be5444ec46cc2ba10cbe4504dbd499ba85ad354cc README.md
>>>
NEW<<<
33fc48048de5319a5e2292120b5e4e40e6f0a3762a8137b27d18b3059db2f5e9 README.md
>>>
REASON: Only with the stream lane's H12 (the README paragraph). The stream lane's report prints its H13 NEW as 4c506f88a22480f4af6e11d3c4af71e890f5a0529c7ec147875569acdb44535c; H12 applied to the filed README (LF) gives 33fc48048de5319a5e2292120b5e4e40e6f0a3762a8137b27d18b3059db2f5e9 (holds-check/README-after-h12.md), the line the lane's own out/HOLDS.txt (sha256 43e98562...) carries. This line is the one to apply.

HOLD H7 | file=polariton-bridge/ENGINE-CHANGES.hbp (after the lanes' H11 rows) | severity=MEDIUM
OLD<<<
>>>
NEW<<<
BRIDGE_ENGINE_REVIEW|engine=the_quantum_engine_src/bin/polariton_first_correction.rs|changes=dyadic_reads(source_8d8afe48,binary_cc75d83f)+streaming_layout(source_ed75eca8,binary_d892971d)|by=opus55,bridge-engine-review-quantum-20261106(BRIDGE_ORDER_step_4)|verdict=PASS_WITH_HOLDS|gate=fmt_--check_0,clippy_--release_-D_warnings_0,build_0_on_three_trees_in_fresh_targets,float_used=0|binaries_rebuilt=3_of_3_bit_identical_to_the_lanes'|stream_mode=78_of_78_allowed_rows_every_field_but_array_bytes|point_mode=27_of_27_dyadic_binary,27_of_27_streaming_binary,byte_for_byte,the_slowest_grid_and_baseline_rows_among_them|own_tests=70_of_70(full_space_N=6561_at_7_tiles,K=2400_at_3_tiles,dyadic_reads_to_317/64)|mutants=10_planted,10_caught,7_of_them_by_the_filed_receipts|RECEIPT-BASELINE.hbp_rows_of_plan_27,32=NOT_MEASURED(reason=RESERVED)|reserved_runs_started=0(this_review_485_runs;the_lanes_229_and_2550)|holds=H1_to_H6_of_bridge-engine-review-quantum-20261106/out/HOLDS-REVIEW.txt|tag=MEASURED|json=0
>>>
REASON: BRIDGE_ORDER step 4 is a second-seat review of the engines before the blind runs. This row files this review's result beside the lanes' BRIDGE_ENGINE_CHANGE_RESULT rows, so PREDICTION.hbp keeps its sha256 fadd8412.... Every number in it is a row of BRIDGE-ENGINE-REVIEW-QUANTUM.hbp.
