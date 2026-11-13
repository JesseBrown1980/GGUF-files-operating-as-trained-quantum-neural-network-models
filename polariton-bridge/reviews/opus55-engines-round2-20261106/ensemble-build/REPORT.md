I built twens 0.3.0 and it passes every gate I ran. All four parts are settled at allowed points. It reproduces all 31 raw files of the ensemble lane's LANE-RECEIPT.hbp, plus TEST-RUNS.hbp and TEST-RUNS-T1B.hbp, byte for byte, with every variant on and start index 0. No run touched a reserved point.

One thing needs the seat's attention (H9). The rounding bound is rigorous, but it grows far faster than the real error at late times: by t = 493/64 it is 10^6 to 10^7 times the measured error, so the late read-and-report rows could carry an error term as large as the value itself.

## What changed (source e5682f1d…, built from the review's a740b653…)
- **Part 1, LOCK and FLIP start: no code change was needed (MEASURED).** Both variants already start from VNC's state: c0 = sqrt(N + 3/2 − n(0)), mode 0 real, read with X_NC. C_JFLIP's frozen text says all_else_as_VNC.
  - The controls lane's closed forms (ctrl_closed.py, forms.py, test_predict.py) are leading order: C1 = (2/N)(q² + sig2). The one place they are exact at finite N is t = 0, where BRIDGE_CTRL_PHASE_LOCKED freezes C1_lock = 2/N.
  - VNC's start, read with X_NC, gives exactly that: E[X_NC] = N − 1 (DERIVED). The controls lane's ring start sqrt(N + 1/2), read with X_W, gives 2(N + 1/2)/(N(N − 1)).
- **Part 2, rounding bound (new).** The derivation is in src/main.rs. It covers every product floor, truncation and square root, MODE0's unit vector, and the 2^40 images of the parameters. These are carried through RK4 by the step-map bound Lip ≤ 1 + hμ + h²L²(1 + hL/6 + h²L²/24), where μ is the log-norm bound |∂²H/∂ψ̄²|. The engine prints it in a TWB_ROUND row beside every TWB row, a TWB_PAIR_ROUND row beside every TWB_PAIR row, and per sample in dump.
- **Part 3, noiseless path NL (new).** NL is a mask name beside the seven variants: c0 = sqrt(N), c± = 0, one trajectory per batch, printed in TWB_NL rows.
- **Part 4, provenance.** The head row prints the sha256 of the source files. `.cargo/config.toml` links with `/Brepro` on MSVC. The version is now 0.3.0; the legacy TWENS, TWPAIR and TWCTL rows are unchanged.

## Gate results (MEASURED)

| Check | Result |
|---|---|
| `cargo +1.81 fmt -- --check` | exit 0, empty log |
| `cargo +1.81 clippy --release -- -D warnings`, and with `--all-targets` | exit 0, exit 0 |
| `cargo +1.81 test --release` | 14 passed, 0 failed |
| Float scan (review's lexer) | 0 types, 0 literals, 0 float method calls; self-test finds 6/6 literals and 1/1 type |
| Binary scan | 0 x86 floating-point instructions |
| Reproduction | 31/31 raw files byte-identical (receipt, control triples, 0 CR, binary and source hash all checked; 6204 s engine time); TEST-RUNS 18 runs and T1B 4 runs byte-identical |
| Battery | 32/32: the review's 27 plus K_E, K_ROUND, K_NL, K_START, K_PROV |
| Independent model, K_MODEL (extended to the exact squares) | 4,232 fields, 0 mismatches |
| Independent model, e2_round | 25,485 engine fields and 26,070 bound fields, 0 mismatches each |
| Mutants | 28/28 caught: the review's 15 as in its table, plus my 13 (M16–M28), each caught by a check on its own part |
| CI job, run verbatim in WSL (Ubuntu, rustc 1.81.0) | 6 of 6 steps pass; Linux binary 9ad6f7d6…, identical at two paths |
| Frozen job, on the proposed stage | 3 of 3 steps pass |
| The CI job on GitHub | NOT_MEASURED: nothing pushed |

## Results of the four parts (MEASURED unless tagged)

**Part 1, t = 0, LOCK C1 against the frozen 2/N** (N = 27, 81, 243; 2^21, 2^22, 2^24 samples):

| Start | z against 2/N | z against the ring's value |
|---|---|---|
| twens LOCK (VNC's start, X_NC) | −0.62, +0.49, +0.82 | −44.36, −19.00, −11.92 |
| twctl lock0 (the controls lane's ring, X_W) | +39.66, +19.07, +14.68 | −0.18, +0.19, +2.06 |

- The identity X_NC − X_W = 1/2 holds on every sample of VNC, FLIP, LOCK and MODE0, inside the printed bound at all 30 records. V1 (the ring) misses it by about 1/(2N²) per sample, at least 1.0e5 times its bound.
- At t > 0 the leading-order forms carry the control's own correction (N = 81, y = 0, δ = ±1/2):
  - LOCK sits at z = 0.05 and −0.91 at t = 1/8, then −2.7e-3 to −2.9e-2 relative at t = 1/4 and 1/2.
  - FLIP sits at −3.0e-2 to −1.36e-1. Both are inside the frozen allowance of 1/4.
  - For FLIP the start itself is fixed by the identity and by its sample-by-sample equality with VNC's start.

**Part 2, bound against a 2^-120 run of the same samples from exact inputs** (5 allowed points, dtden 64 and 128):
- 27,621 comparisons (3,972 of them row fields), 0 violations.
- With the bound halved, 20 row fields fail, so the sabotage fails as required. The tightest row field sits at 0.891 of its bound (MODE0's f at t = 0, N = 9); the median is 0.020 to 0.048.
- Cost: the same receipt file takes 42.8 s against 43.9 s without the bound.

**Part 3, NL against traj_int.py (18f2a85b…):**
- Check: |O(dt=1/64) − O_traj| ≤ e_int + rb + tb, plus the frame identities. 168 of 168 at 6 allowed points; the start row is exact at 6 of 6; d/e_int ≈ 0.53.

**Part 4, builds:**
- Three /Brepro builds at three paths give ae6d33e2…; a build without /Brepro gives 29ae4296….

**Reserved points:**
- Engine launches: 5,893 in all, every one checked in code first. 0 at the exact set or its 2^40 aliases, and 0 in a band with samples.
- Band points: 800 launches with zero samples, all refusal checks.
- Guard lift: lift_reserved_guard=1 was passed 32 times, always at (81, 1/2, 1/18) with 0 samples. The local CI run passed it twice more, at the same point.
- The worktree is clean at 2ab8143. No files were written in any earlier lane folder.

## Open items
- **Small N (DERIVED).** At small N the sharp start has no real square root on rare samples, and the engine stops with exit 4. This showed up at N = 9 for LOCK. At N ≥ 81 the chance per sample is about e^-(N+3/2).
- **Bound-mutant coverage (MEASURED).** M18, M21 and M23 shrink parts of the bound that stay covered at the test points. Only the independent bound model (R_BND) catches them.
- **Tool fixes during the run.** The copied build-lane test_dump predated the review's R2 and failed on the real binary; I extended my copy to the exact squares and reran the lane stage for all 28 mutants. I also added zero-bound guards to e2_round and e2_check after M06 aborted the battery, then reran M06 and the final battery.

## Files (all under C:/tmp/opus55/bridge-engine-ensemble2-20261106/; all 1,133 are listed in out/LANE-RECEIPT-E2.hbp, ec4a1e65f58921f58e27f1d2efe0606087b53ca88be27c1fc83255ec705c96b2)

| File | sha256 |
|---|---|
| twens/src/main.rs | e5682f1d180beafe3df22daa64f74b1d5d027cfd9097d7e70bb3f2bbf7b4e810 |
| twens/src/sha256.rs | 7447d1e84a95fe1ab84882938a0344119d017c347809e0f7e929c2e8c27d4621 |
| out/twens-0.3.0-ae6d33e2.exe | ae6d33e24294366ea6b31b4610fb10645cd9786b895398e91139d2507e58adff |
| out/GATE.hbp | 1fdc730d80a52c00ba81b426bd9e0956ccca02845c0f2f4ef9fe54fe592f52d9 |
| out/START-FALSIFIER.hbp | 4be11739f308fe9f7f85beeaf9922da287a43c8b5532e07e1eb3edaa341d0d07 |
| out/ROUND.hbp | 4964c567cecefe567932742bfb075692ba2533dc2f05f81c4baf89202d0cfd3b |
| out/NL.hbp | 0718b0a5bb68b6355c9e20ca5cc2ba09ad85cea40c0475458b4052d7963e5970 |
| out/BOUND-GROWTH.hbp | adabaaf4d499ee4920953676fcf8e8360898e1e9967614af7eb396220a09d31a |
| out/BOUND-GROWTH-ACTUAL.hbp | 77d2bf77c06d58f36bdaed3e52c998d240eef132214c5baf611f67d75454359c |
| out/CORRECTIONS.hbp | 7cf33109bc160930162cf51c9be4a31733f1f27f1487d733057d6018ed00481c |
| out/ENGINE-ROWS.hbp | 88f95e7bd70cfc31f2bf6206681dfb7791d9ffdc4d9880bc485a163d76cc5b9b |
| logs/check_final3.log | 8e922d2658cab96ab57897bec77d92149357a833bd074ec22298990bfdd8e1bb |
| logs/mut_report.log | 8327079940e982fa78f97d22b90d3e41917f7242a43c202cdcdb522bc92fdffa |
| logs/RUNS.hbp | 806bb0dc641564f1f16c526f04fff0912d5e231e641e9dbe9a5043d9c4dc9b3b |

Tools:

| File | sha256 |
|---|---|
| e2_common | 61b56f1e… |
| e2_start | dd78fbd7… |
| e2_round | e3be46c5… |
| e2_nl | 3fabd6dc… |
| e2_repro | 88489f47… |
| e2_repro_ctl | a14b063d… |
| e2_model | 494370f7… |
| e2_check | da71f294… |
| e2_mutate | ce037905… |
| e2_corrections | 6e750957… |
| e2_engine_rows | e68449b6… |
| e2_proposed | 27d9ba55… |
| e2_gate_rows | 2275e03e… |
| tools-lane/test_dump.py | c610da3a… |

## Proposed repo files (in proposed/)

| Path | sha256 |
|---|---|
| polariton-bridge/engines/ensemble/Cargo.toml | ee2f0e6650f8ca7b9cc4bbdacca0e5d26a60f32d5fe7312297ef0214dd3550a8 |
| polariton-bridge/engines/ensemble/Cargo.lock | 9c57df215dea030065e5721271525367be7498f3708cef641cf2c187f2a5bea4 |
| polariton-bridge/engines/ensemble/rust-toolchain.toml | 6646e2db3cd46526264fd4914b3a411ad7bcfad8281a098c8378f6c986843d3a |
| polariton-bridge/engines/ensemble/.cargo/config.toml | a98832b1fd3dbc44fa93ba9bf6e30111f6ca1c562c08707d6460448ba3b84c18 |
| polariton-bridge/engines/ensemble/src/main.rs | e5682f1d180beafe3df22daa64f74b1d5d027cfd9097d7e70bb3f2bbf7b4e810 |
| polariton-bridge/engines/ensemble/src/sha256.rs | 7447d1e84a95fe1ab84882938a0344119d017c347809e0f7e929c2e8c27d4621 |
| polariton-bridge/engines/ensemble/tools/floatscan.py | 3476c64c811b36f7cd67aba4930552b8f5890c38e6ebff8f9cd3cbbfcb6062b9 |
| polariton-bridge/CORRECTIONS.hbp (26 rows) | 7cf33109bc160930162cf51c9be4a31733f1f27f1487d733057d6018ed00481c |
| polariton-bridge/ENGINE-CHANGES.hbp (+5 rows) | 3235389a9f8aec57da7a21ccc0ee44249542af4aff558fd342e2f5caf64aedc8 |
| polariton-bridge/README.md | 2eaded4a75fba983ccf96f02c7b7318634bafc9269809cdfc6dde1fec3074229 |
| polariton-bridge/SHA256SUMS | 61a4afca17ac9ed916ceb6cb344eaf0355a07c419940a65596a708d718d291f5 |
| .github/workflows/polariton-bridge.yml (frozen job unchanged, ensemble job added) | 676ef27377e8ec3bb06767fbfa4df11c2c1c19a941950afa31acb9d946bf8909 |

## HOLDS

HOLD H1 | file=C:/tmp/qnn-bridge-wt/polariton-bridge/CORRECTIONS.hbp | severity=HIGH
OLD<<<
(file absent at 2ab8143)
>>>
NEW<<<
the 28 lines of C:/tmp/opus55/bridge-engine-ensemble2-20261106/out/CORRECTIONS.hbp (sha256 7cf33109bc160930162cf51c9be4a31733f1f27f1487d733057d6018ed00481c)
>>>
REASON: These are the round-1 holds on PREDICTION.hbp as rows beside it: ensemble-1 to ensemble-26, covering the build lane's H1–H4 and H7–H14 and the review's R1, R2, R2s, R4 and R6. Each frozen_text was verified byte for byte: it occurs once on its frozen line. Every row has values_moved=0; the check counts the 352 BRIDGE_AT rows' lock (57/39/256), jflip (82/13/1/60/196), mode0 MET and noiseless fields. H7, H10, H11, R1 and R4 carry this round's measured results. R6 is the READ_DETAIL for F4: the read reports |mean MODE0 − mean VNC| with 3 SE beside the frozen form, and the read stage decides with the operator. H5, H6 and R2r target README.md, so they are H6–H8 below.

HOLD H2 | file=C:/tmp/qnn-bridge-wt/polariton-bridge/ENGINE-CHANGES.hbp | severity=HIGH
OLD<<<
,32=NOT_MEASURED(reason=RESERVED)|reserved_runs_started=0(this_review_485_runs;the_lanes_229_and_2550)|holds=H1_to_H6_of_bridge-engine-review-quantum-20261106/out/HOLDS-REVIEW.txt|tag=MEASURED|json=0
>>>
NEW<<<
,32=NOT_MEASURED(reason=RESERVED)|reserved_runs_started=0(this_review_485_runs;the_lanes_229_and_2550)|holds=H1_to_H6_of_bridge-engine-review-quantum-20261106/out/HOLDS-REVIEW.txt|tag=MEASURED|json=0
<the 5 BRIDGE_ENGINE_CHANGE_RESULT rows of C:/tmp/opus55/bridge-engine-ensemble2-20261106/out/ENGINE-ROWS.hbp, sha256 88f95e7bd70cfc31f2bf6206681dfb7791d9ffdc4d9880bc485a163d76cc5b9b>
>>>
REASON: These are the ensemble integrator's results in the form of the quantum rows: lines 447–450 with the gate, the rounding bound, NL, the LOCK and FLIP starts, and binary provenance. Every number in them is read from this lane's output files by tools/e2_engine_rows.py.

HOLD H3 | file=C:/tmp/qnn-bridge-wt/.github/workflows/polariton-bridge.yml | severity=HIGH
OLD<<<
      - name: LF line endings in every file of the stage
        run: |
          set -euo pipefail
          test "$(find polariton-bridge -type f -exec cat {} + | tr -cd '\r' | wc -c)" = "0"
>>>
NEW<<<
      - name: LF line endings in every file of the stage
        run: |
          set -euo pipefail
          test "$(find polariton-bridge -type f -exec cat {} + | tr -cd '\r' | wc -c)" = "0"
  ensemble:
    name: The ensemble integrator twens 0.3.0, its toolchain gate, and TEST-RUNS-T1B.hbp reproduced byte for byte
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    defaults:
      run:
        working-directory: polariton-bridge/engines/ensemble
    steps:
      - name: Checkout, on a pull request its merge with the base
        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      - name: Rust 1.81 and lints
        run: rustup toolchain install 1.81.0 --profile minimal --component clippy --component rustfmt
      - name: Format, Clippy in both forms, unit tests, build
        run: |
          set -euo pipefail
          cargo +1.81.0 fmt -- --check
          cargo +1.81.0 clippy --locked --offline --release -- -D warnings
          cargo +1.81.0 clippy --locked --offline --release --all-targets -- -D warnings
          cargo +1.81.0 test --locked --offline --release
          cargo +1.81.0 build --locked --offline --release
      - name: Integer types only in the engine's source (float_used=0, the second seat's lexer-based scan, its self-test first)
        run: |
          set -euo pipefail
          python3 -I -X utf8 tools/floatscan.py selftest | tee scan-self.hbp
          grep -q '^RV_FLOATSCAN_SELFTEST|literals_found=6|expected=6|types_found=1|expected=1|' scan-self.hbp
          python3 -I -X utf8 tools/floatscan.py src src/main.rs src/sha256.rs | tee scan.hbp
          grep -q '^RV_FLOATSCAN_SRC_DONE|files=2|code_uses=0|float_used=0|' scan.hbp
      - name: The binary names the source it was compiled from, and that source is this one
        run: |
          set -euo pipefail
          ./target/release/twens version | tee version.hbp
          grep -q "|source_sha256=main.rs:$(sha256sum src/main.rs | cut -d' ' -f1),sha256.rs:$(sha256sum src/sha256.rs | cut -d' ' -f1)|" version.hbp
          grep -q "|binary_sha256=$(sha256sum target/release/twens | cut -d' ' -f1)|" version.hbp
      - name: The guard refuses its neighbourhood bands before any model code (zero samples, no exact reserved point started), and lifts only on lift_reserved_guard=1
        run: |
          set -euo pipefail
          K="u=1 seed=1 start=0 count=0 dtden=64 threads=1 steps=32 ctrl=1099511627776:0:0"
          for pt in "N=81 delta=29/50 y=1/18" "N=6561 delta=-31/50 y=0" "N=729 delta=1/2 y=71/1000"; do
            for mask in VNC NL; do
              rc=0
              ./target/release/twens run $pt $K mask=$mask > refused.hbp 2> refused.err || rc=$?
              test "$rc" = 3
              test ! -s refused.hbp
              grep -q '^TWB_REFUSED|' refused.err
            done
          done
          rc=0
          ./target/release/twens run N=81 delta=1/2 y=1/18 $K mask=VNC lift_reserved_guard=yes > lift.hbp 2> lift.err || rc=$?
          test "$rc" = 2
          ./target/release/twens run N=81 delta=1/2 y=1/18 $K mask=VNC lift_reserved_guard=1 > lift1.hbp
          head -1 lift1.hbp | grep -q '|reserved=0|guard=lifted|'
          ./target/release/twens run N=81 delta=1/2 y=1/18 $K mask=VNC > nolift.hbp
          head -1 nolift.hbp | grep -q '|reserved=0|guard=active|'
      - name: TEST-RUNS-T1B.hbp of the controls lane (its four twctl runs, PREDICTION.hbp BRIDGE_ENGINE_CHANGE lines 447 to 450), byte for byte
        run: |
          set -euo pipefail
          for d in 1/2 -1/2; do
            for ph in fixed random30; do
              ./target/release/twens twctl 6561 $d 1 1/162 1 vac $ph 240000 20261105 64 4 64,128 | grep '^TWCTL|'
            done
          done > TEST-RUNS-T1B.hbp
          test "$(sha256sum TEST-RUNS-T1B.hbp | cut -d' ' -f1)" = "8aee3a7fe77cb6cd6f0daf3291e12b917823e694b83e797bbf78e9cd0958bd0d"
          test "$(tr -cd '\r' < TEST-RUNS-T1B.hbp | wc -c)" = "0"
>>>
REASON: The frozen job's text is unchanged; a diff shows it identical. Every step of the new job ran verbatim in WSL (Ubuntu, rustc 1.81.0): 6 of 6 pass, and T1B came out as 8aee3a7f…. The guard step starts only band points with zero samples and one allowed point, so no exact reserved point is ever started.

HOLD H4 | file=C:/tmp/qnn-bridge-wt/polariton-bridge/engines/ensemble/ | severity=HIGH
OLD<<<
(directory absent at 2ab8143)
>>>
NEW<<<
Cargo.toml, Cargo.lock, rust-toolchain.toml, .cargo/config.toml, src/main.rs, src/sha256.rs, tools/floatscan.py as in C:/tmp/opus55/bridge-engine-ensemble2-20261106/proposed/polariton-bridge/engines/ensemble/ (sha256 in the table above)
>>>
REASON: This is twens 0.3.0 as gated. floatscan.py is the review's rv_floatscan.py byte for byte (3476c64c…), which the CI job runs.

HOLD H5 | file=C:/tmp/qnn-bridge-wt/polariton-bridge/SHA256SUMS | severity=MEDIUM
OLD<<<
fadd84122e820cc03e9a4d6d5dd47fe7118ab4b16e1d4db93a601fb44c90b892 PREDICTION.hbp
33fc48048de5319a5e2292120b5e4e40e6f0a3762a8137b27d18b3059db2f5e9 README.md
a79691a93b46e49ce460c26ef22afcc03d6eca1e63bf2edbc20e96159510f6c9 .gitattributes
5565de09fa595c059a260081a9c4ced4234f056faebee2bf69d50f8aa905287a ENGINE-CHANGES.hbp
>>>
NEW<<<
fadd84122e820cc03e9a4d6d5dd47fe7118ab4b16e1d4db93a601fb44c90b892 PREDICTION.hbp
2eaded4a75fba983ccf96f02c7b7318634bafc9269809cdfc6dde1fec3074229 README.md
a79691a93b46e49ce460c26ef22afcc03d6eca1e63bf2edbc20e96159510f6c9 .gitattributes
3235389a9f8aec57da7a21ccc0ee44249542af4aff558fd342e2f5caf64aedc8 ENGINE-CHANGES.hbp
7cf33109bc160930162cf51c9be4a31733f1f27f1487d733057d6018ed00481c CORRECTIONS.hbp
ee2f0e6650f8ca7b9cc4bbdacca0e5d26a60f32d5fe7312297ef0214dd3550a8 engines/ensemble/Cargo.toml
9c57df215dea030065e5721271525367be7498f3708cef641cf2c187f2a5bea4 engines/ensemble/Cargo.lock
6646e2db3cd46526264fd4914b3a411ad7bcfad8281a098c8378f6c986843d3a engines/ensemble/rust-toolchain.toml
a98832b1fd3dbc44fa93ba9bf6e30111f6ca1c562c08707d6460448ba3b84c18 engines/ensemble/.cargo/config.toml
e5682f1d180beafe3df22daa64f74b1d5d027cfd9097d7e70bb3f2bbf7b4e810 engines/ensemble/src/main.rs
7447d1e84a95fe1ab84882938a0344119d017c347809e0f7e929c2e8c27d4621 engines/ensemble/src/sha256.rs
3476c64c811b36f7cd67aba4930552b8f5890c38e6ebff8f9cd3cbbfcb6062b9 engines/ensemble/tools/floatscan.py
>>>
REASON: These lines pin the new files under the frozen job's check. On the proposed stage the frozen job ran 3 of 3 steps clean: PREDICTION.hbp at its pin, these sums and the review folders' sums, and 0 CR bytes. The README sum assumes H6–H8 are applied.

HOLD H6 | file=C:/tmp/qnn-bridge-wt/polariton-bridge/README.md | severity=LOW
OLD<<<
the fixed mode-0 phase runs
on the first 2^16 samples
>>>
NEW<<<
the uniform-phase partner of VNC's fixed mode-0 phase (MODE0) runs
on the first 2^16 samples
>>>
REASON: This is the build lane's H5, carried. Its OLD text occurs once at 2ab8143.

HOLD H7 | file=C:/tmp/qnn-bridge-wt/polariton-bridge/README.md | severity=LOW
OLD<<<
the fixed mode-0 phase on the first 2^16 samples
>>>
NEW<<<
the uniform-phase partner of VNC's fixed mode-0 phase (MODE0) on the first 2^16 samples
>>>
REASON: This is the build lane's H6, carried. Its OLD text occurs once at 2ab8143.

HOLD H8 | file=C:/tmp/qnn-bridge-wt/polariton-bridge/README.md | severity=LOW
OLD<<<
(Re Z - Re Z_lin)(X - X_lin), and a
  start index, so that each step of the staircase runs as its own batch (`BRIDGE_ENGINE_CHANGE`).
>>>
NEW<<<
(Re Z - Re Z_lin)(X - X_lin), exact sums of squares
  for every variance, and a start index, so that each step of the staircase runs as its own batch (`BRIDGE_ENGINE_CHANGE`).
- The ensemble integrator twens 0.3.0 (`engines/ensemble/`) carries these changes, its per-sample rounding bound printed
  beside every row, the noiseless path the noiseless control reads, and the sha256 of its source in its head row; on
  Windows it links with /Brepro, so a rebuild of that source gives the same binary. It reproduces the ensemble lane's 31
  raw files and the controls lane's TEST-RUNS.hbp and TEST-RUNS-T1B.hbp byte for byte (`ENGINE-CHANGES.hbp`); the holds of
  its rounds on `PREDICTION.hbp` are the rows of `CORRECTIONS.hbp` beside it.
>>>
REASON: This is the review's R2r, plus one bullet on round 2, like the README's paragraph on the quantum engine's streaming layout.

HOLD H9 | file=C:/tmp/qnn-bridge-wt/polariton-bridge/CORRECTIONS.hbp | severity=MEDIUM
OLD<<<
BRIDGE_CORRECTIONS_END|rows=26|frozen_texts_verified=26_of_26(each_once_on_its_line)|json=0
>>>
NEW<<<
BRIDGE_CORRECTION|id=ensemble-27|frozen_line=423|frozen_text=e=3*SE+e_int+e_round+e_q+e_trunc,each_printed_on_the_row|reads_as=e=3*SE+e_int+e_round+e_q+e_trunc,each_printed_on_the_row(e_round_the_engine's_printed_rigorous_bound,TWB_ROUND;where_e_round_exceeds_3*SE,the_read_prints_beside_it_the_measured_difference_of_the_row's_first_2^10_samples_against_a_2^-120_run_of_them)|kind=READ_DETAIL|values_moved=0(the_text_lies_outside_every_closed_form_and_count_of_the_352_BRIDGE_AT_rows)|from=bridge-engine-ensemble2-20261106:bound_growth|tag=NAMED|json=0
BRIDGE_CORRECTIONS_END|rows=27|frozen_texts_verified=27_of_27(each_once_on_its_line)|json=0
>>>
REASON: This is a candidate; the seat chooses. The frozen text occurs once, on line 423 (BRIDGE_READ_RULE). On the noiseless path at N = 6561 the printed state bound is 2.4e-9 to 2.8e-9 at t = 2 and grows to 2.1e-4 to 1.8e-3 at t = 493/64. Relative to the values, that is 1.1e-3 to 9.7e-2 on f and 3.0e-3 to 0.15 on |Z|^2 at t = 493/64. Measured against a 2^-120 run, the real error stays between 1e2 and 4e3 ulps: actual/bound is 0.05 to 0.15 at t ≤ 2 and 1e-7 to 1e-6 at t = 493/64 (out/BOUND-GROWTH.hbp, out/BOUND-GROWTH-ACTUAL.hbp). On the first-order rows the bound is about 1e-7 relative. On the late read-and-report rows, e_round would be as large as the observable. The options are:
- keep the rigorous bound alone;
- print the measured comparison beside it (the row above);
- ask for a tighter amplification factor, such as the per-step norm of the actual RK4 Jacobian along each sample, at extra cost.
