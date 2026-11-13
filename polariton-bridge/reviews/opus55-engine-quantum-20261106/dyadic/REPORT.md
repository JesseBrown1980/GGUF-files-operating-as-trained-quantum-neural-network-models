## Quantum engine: dyadic time reads (BRIDGE_ENGINE_CHANGE, PREDICTION.hbp line 445)

The changed engine reads at any multiple of 2^-W, and the frozen times need W = 6. The changed binary reproduces RECEIPT-GRID.hbp byte for byte as a whole file. RECEIPT-BASELINE.hbp reproduces byte for byte on 58 of its 64 rows plus both stage lines. Its other 6 rows sit at a reserved point, so the full-file check of that receipt is NOT_MEASURED (reason RESERVED). Both falsifiers pass.

Folder: `C:/tmp/opus55/bridge-engine-quantum-20261106/`. Vantage: WSL2 Ubuntu, rustc 1.81.0. Worktree read-only (HEAD 38ce248, status clean). No git writes, no push, no GitHub writes.

### What changed
- **The change (MEASURED):** in `src/bin/polariton_first_correction.rs`, each read time T is now an integer or a/2^b with b ≤ W, taken in lowest terms.
  - A read happens after T·2^W windows.
  - A time with T ≤ 0, or whose denominator does not divide 2^W, is refused with exit 2 and no row.
  - The READ and COST rows print T in lowest terms, so an integer T prints exactly as before.
  - The window arithmetic, the Bessel tables, the degree and reach, every eps term, the read-out, the `bessel`/`rows` modes and the sabotages are as before.
- **Size:** 1059 → 1080 lines, 8 hunks, 40 changed lines. Source sha256 ad121216… (38ce248, identical to origin/main bde1035 as fetched) → `8d8afe48e5006cc146dd05bdd4c9bfdc068463b7aaa43faf362386b0a0d59228`.
- **Changed binary sha256:** `cc75d83f0a7e07b1d95bf091455f309d2c3fb64cf8f3485222e53e4c5508b776` (559,544 bytes, x86_64-unknown-linux-gnu).
- **W = 6 (MEASURED, `scripts/find_w.py`):**
  - 352 BRIDGE_AT rows carry 125 distinct t from 1/16 to 493/64, with denominators {1, 2, 4, 8, 16, 32, 64}.
  - The 28 BRIDGE_POINT rows carry 446 time values with the same denominators, and each list matches its BRIDGE_AT times exactly (352 of 352 both ways).
  - The 28 BRIDGE_CLOCK rows write t_q and t_tr as (5/8)ln(r) (50 values, irrational) or undefined (6). Their frozen reads are the BRIDGE_AT times, rounded to 1/64.

### Gate results (MEASURED; exit codes in `logs/gate-exits.hbp`)

| Step | Result |
|---|---|
| rustc | 1.81.0 (eeb90cda1 2024-09-04) |
| `cargo +1.81 fmt -- --check`, and `--all` | exit 0 |
| `cargo +1.81 clippy --release -- -D warnings`, fresh target | exit 0 on all 6 crates (gguf_qnn lib and bin, google_qsim_audit, google_qsim_full24, polariton_first_correction, polariton_three_mode) |
| clippy `--all-targets` | exit 0 |
| workflow form `--locked --offline --bin polariton_first_correction` | exit 0 |
| `build --release --locked --offline` | exit 0; a fresh-target rebuild has the same sha256 cc75d83f… |
| float_used | 0: no f32/f64 or float literal in the code (comments and strings stripped; the scanner finds 6 of 6 planted floats with no false hits); CI grep of `\bf(32\|64)\b` finds nothing |
| RECEIPT-GRID.hbp | whole file byte for byte: sha256 4a1a2778… reproduced, `cmp` exit 0, 20 of 20 rows, 820 fields, 0 differing |
| RECEIPT-BASELINE.hbp | 58 of 58 rows of the 40 allowed runs byte for byte, 2,378 fields, 0 differing; both stage lines are what `run_stage.py` writes |

- **The 6 reserved rows:** two baseline runs (plan index 27 and 32: N = 729, K = 729, y = 2/27, δ = 0 and 1/2, t = 1, 2, 3) are inside the reserved set. My guard refused them before start, so the whole-file sha256 10b26eeb… is NOT_MEASURED (reason RESERVED).
  - Without those 6 rows and with runs=40 in the stage lines, the filed receipt equals what `run_stage.py` writes from my 40 runs byte for byte (sha256 ff57d5e8…).
- **One scripted rerun of the gate is NOT_MEASURED:** it ran in a non-login WSL shell where cargo was not on PATH (exit 127). That record is kept in `logs/gate-run1-no-toolchain-on-PATH/`; the rerun above, with cargo on PATH, is the measurement.
- **Cost (MEASURED, shared host):** another lane's two `twens` processes used about 5 of the 8 threads during my runs. Baseline: 2,939,956 engine-ms against 1,932,884 filed for the same runs (×1.52). Grid: 10,410,916 against 4,947,945 (×2.10). Peak RSS 77,304 kB.
- **Reserved guard:** every model run of this lane (engine, fockprop, exact reference) passed `scripts/reserved.py` first. Self-test 19 of 19 with no run started; 0 runs started at a reserved point.

### Derivation (DERIVED, with MEASURED checks)
The change touches only which window boundary a read lands on. Every certified bound is a sum of per-window terms, so the value printed at T = n·h (h = 2^-W) is the same sum stopped after n windows.

- **D0, reads leave the state alone:** `read()` takes `&re, &im` and writes nothing back, so the state after n windows is one fixed integer sequence whatever times are read. Checked: t = 1 and t = 2 rows are byte-identical with reads at 1/2 and 3/2 between them (4 of 4 small blocks), and the grid's t = 2 rows likewise (4 of 4).
- **D1, Duhamel:** ‖ψ_full(t) − φ(t)‖ ≤ ∫₀ᵗ ‖Bφ‖ds holds for every real t ≥ 0, and at t = nh it is exactly the sum of n window integrals.
- **D2, the Chebyshev and Bessel route:** 2|J_m(τE)| ≤ 2(hE/2)^m/m! for every τ in [0, h], so on each window ‖Bφ(jh+τ)‖ ≤ ‖B‖(‖Π_high φ(jh)‖ + ρ). ρ, the table J_k(E/2^W), the degree and the reach depend on (E, W) only. Checked: the route's Bessel mode passes on the 78 reproduced rows (47 tables, worst 1 unit of 2^-62) and on the 12 dyadic-read rows (4 tables, worst 1 unit).
- **D3, eps_tail:** eps_tail(n) = Σ_{j<n}[h‖B‖(tail_j + ρ + eps_round(j) + eps_poly(j)) + 2^-62], which the code adds window by window. Checked: the route's certificate walk, recomputed at dyadic T, passes at 3/2, 1/2, 33/64 and 3/4 (W = 6) and at 129/128 (W = 7). At T = 1/64 it fails; see the next bullet.
- **The T = 1/64 failure (MEASURED, cause DERIVED):** at one window every tail sits at its floor. The engine prints (⌊√S⌋+1)·2^-42 with S = 399 states (⌊√399⌋ = 19); the walk takes √S·2^-42 + 2^-42.
  - The offsets match that difference exactly: tail_max is off by 2.21686e-13 = (√399 − 19)·2^-42, and eps_tail by 5.6572e-14, which is that times ‖B‖·h. Both are outward bounds of a tail that is exactly 0.
  - With the engine's integer floor in the walk, it passes 10 of 10 (the 6 dyadic cases and the route's own 4 integer cases). Both runs are kept on file.
- **D4:** eps_poly(n) = nρ and eps_round(n) = n·pw; telescoping with the unitary U_h holds for every n.
- **D5, the floor:** tail_j ≥ √S·2^-42 gives eps_tail ≥ t‖B‖(√S·2^-42 + η/2 + (ρ − pw)/2), with η = eps_poly + eps_round at t. That is the review's law at every window count n. Checked at K = 1600 at t = 1/2, 3/2 and 2 (6 reads): printed over the exact window-sum form is 1.000074 to 1.002993; over t‖B‖(√S·2^-42 + η/2) it is 0.99724 to 0.99982.
- **D6, read-out:** |⟨O⟩_full − ⟨O⟩_c| ≤ eps(2‖Oφ_c‖ + ‖O‖eps) + read_err. Its inputs (x_up, s_up, x_norm, s_norm, read_x, read_s) depend on dim, N and the state at the read, and none on T.
- **D7, the time argument:** smoke tests pass 29 of 29. Six off-grid times are refused with exit 2 and empty stdout; t = 3/128 reads at W = 7; repeated and unsorted integer T behave as before; integer-T output, the 4 sabotages and the `rows`/`bessel` modes are byte-equal to the 38ce248 build on the same toolchain.

**fockprop's own certificate (new, DERIVED in rows F1 to F5):** element error ≤ 2^-57 + h·max(2^-f/N, |y|·2^-f), at most 7 per row. Per-term rounding (1/2 + 1/(2j))·2^-56 + |ur|·2^-63 per component, propagated by c_l = Σ g^m·l!/(l+m)!. Per step the error grows by (τ_M + ‖Δ‖)(1 + δ_n) + ‖R_n‖. The block part is a Duhamel sum Σ h‖B‖(b̂_n + δ_n + ρ_T), with the tail norm b̂_n summed outward per step.
- Tested (MEASURED): the exact value (exact_small.py at K = N, 2^-200) lies inside fockprop's and the engine's intervals in 16 of 16 cases.
- Dropping one part of the bound on purpose puts the exact value outside in 15 of 16 reads. The 16th is a 2e-18 offset inside the 2-unit print slack.

### Falsifiers
- **(a) MEASURED_PASS, 2 of 2:** at N = 729, K = 729, δ = 0, y = 1/108 and at N = 2187, K = 1000, δ = 0, y = 1/94, the t = 64/64 row equals the T = 1 row, which equals the filed row, byte for byte (697 and 729 bytes).
- **(b) MEASURED_PASS:** two grid points (N = 6561; δ = 1/2, y = 1/324 and δ = −1/4, y = 1/81), both passed by the guard, read at t = 1/2 and 3/2.
  - Codes: the changed engine at K = 1200 and 1600, and my copy of fockprop (full Fock basis, K = 1200, W chosen automatically as 8 and 9, R = 81).
  - 72 of 72 both-ways memberships hold: each code's C1, A1 and V² inside every other code's certified interval. 36 of 36 interval pairs meet.
  - fockprop minus engine: C1 −123 to −303e-18; A1 at most 1.031e-12, the engine's 2^-24 read-out roots; V² at most 6.85e-12. K = 1600 minus K = 1200: C1 0, A1 ≤ 6e-18, V² ≤ 76e-18.
  - Certified half widths, C1: fockprop 2.38e-11 to 3.98e-9, engine 2.98e-11 to 3.26e-9. A1: fockprop 9.50e-10 to 3.76e-8, engine 1.26e-9 to 3.08e-8.
  - My fockprop read-out equals the numerics lane's `readout_lane.py` on 28 of 28 fields.
- **Small-block note (MEASURED):** both-ways membership can fail with both certificates correct. At K = N on tiny blocks, fockprop's width (about 2e-14) is far below the engine's read-out offset (5.6e-12), so the engine's value falls outside fockprop's interval, while the exact value sits inside both.
- **Controls, 6 of 6:** the real engine passes the reader's checks, each of the 4 sabotages fails exactly the checks CONTROLS.hbp names, and the crosscheck rows pass.

### Open items
- O1: the full-file reproduction of RECEIPT-BASELINE.hbp, which needs the 2 reserved runs (the operator's word; the hosted workflow runs them, see H9).
- O2: the hosted gate on the change's PR — NOT_MEASURED, this lane pushed nothing.
- O3: a Windows MSVC build and its sha256 — NOT_MEASURED.
- O4: the stage reader's baseline and grid modes — NOT_MEASURED; their input holds the 6 reserved rows.
- Recall at :4796 answered live with count = 0 for polariton_first_correction, dyadic and BRIDGE_ENGINE_CHANGE: an index boundary for this work, the files here are the source. The fabric was not asked by this lane.
- My slips, each corrected and kept on file:
  - `git archive` with the machine's core.autocrlf=true wrote CRLF into the `.rs` copies. I rebuilt from LF copies; the binaries are identical either way.
  - A `$VAR` inside `wsl -lc` arrived empty; I moved that check into a script file.
  - The PATH gate run above.
  - A stray `python3 -` waited on stdin; I stopped it.

### Files (sha256)
- `BRIDGE-ENGINE-QUANTUM.hbp`: 434bd5778d4c1ad4804512d46323d73c95cb92ae7380a3911623cc9c72a87d20 (559 rows, `.sha256` sidecar). Its 231 BEQ_FILE rows give the sha256 of every file in the folder, including run outputs, logs and dumps.
- `out/polariton_first_correction.rs` and `build-src/src/bin/polariton_first_correction.rs`: 8d8afe48e5006cc146dd05bdd4c9bfdc068463b7aaa43faf362386b0a0d59228
- `out/polariton_first_correction.rs.diff`: 92cff5b120fb4991a7c74b9abc4e56b41a0bfc895219cf79260492d2081dc6e0. It applies to the 38ce248 file to give the patched sha256 with `git -c core.autocrlf=false apply` and with GNU `patch`.
- `out/ENGINE-HUNKS.txt` 2c085206b0449bc4b821a6525f9ff0f3adf130a21d82ee13b0d7f0f494bcb5ca · `out/HOLDS.txt` f29247d662999cbb18f2bae0c57c308e1802831743b060c006ffab5a49501ace
- `out/RECEIPT-GRID-REPRODUCED.hbp` 4a1a277885015a5e937a028d767c617878ae9a05e75bade9eee3e14f0e07e480 · `out/RECEIPT-BASELINE-REPRODUCED-ALLOWED-ROWS.hbp` 15d7ada02d161c07daa0d706cb57ebf8b08e5157a2a93228ef08998b9c3836d8 · `out/RECEIPT-BASELINE-FILED-ALLOWED-ROWS-RUNS40.hbp` ff57d5e8f8dc5697709f10ed42693ac066e45d534aa112b87ebdefbc1a4a9de0 · `out/RECEIPT-BASELINE-REFUSED-RUNS.hbp` 28096ea3d86964f8151e5b9bbaf79b57c857108f79ac160531f5243695a96a3a
- `out/COMPARE-BASELINE.hbp` eaf9c172bf9767e760026036750289f516199853c03f21ecfcbd2adabc545d92 · `out/COMPARE-GRID.hbp` 4354cfb3179482b87c1738712854890e5f2ab9ad2dce759151a170ed699e6d88 · `out/COST-REPRO.hbp` 3a44ae422831ab9924052c2ec3beca762ef4c2f6a57fc2d2a131d2f922e0b880
- `out/FALSIFIER-A.hbp` 0883ab8d90fbdcf1eb9f9f8348b953f61d274bd3393b69aca8e8e8ff948d0324 · `out/FALSIFIER-B.hbp` af3742a723b295a39d308b8a333653b90e8c2cf38fc922c74fc016979dd2e882 · `out/FOCK-CERT-SELFTEST.hbp` e7115568539ceba68338da15b49b49ff97453f4df365dccb282de141db185360 · `out/FOCK-CERT-SABOTAGE.hbp` 49872f43361e4740c27e692fc774632d44871ae4cf354e56793239568c59c851 · `out/READOUT-CROSSCHECK.hbp` e797b3bb56ed69de2bc0c4076f8dbc48397d0c1b2d34d3e359a0f139092ccc1c
- `out/FIND-W.hbp` 987fadb766d24d67ebc636ebb071310860421af2e2d83f278fe4f7e8b785b1c8 · `out/FLOAT-SCAN.hbp` d34f77b8c7db685116aa3a39de2065494851de8a01f29862c6d6811abf0836aa · `out/GUARD-SELFTEST.hbp` bfd362ceec75d3643799d9e375900be11b45da7560df9482e4db3d91076d9dea · `out/SMOKE.hbp` 8740c4c12340fc626ee298dc156eace5c567e1ef5a7284a6150c3dfaf5610cba · `out/CONTROL-CHECKS.hbp` 25ea7dc7c189d6e04379d71c6ba7f7891531586967e13fdff7586f9dda203464
- `out/ROUTE-ROWS.hbp` bac012833a966e822beed0a9660ec3faffa05e90c0a0cb12415778c40c8c00bb · `out/ROUTE-BESSEL-REPRO.hbp` 27e11f7cf242d67b3b6d7f9cee9fd6d033e46c6b3ba4f526859d0ee839cd8ec9 · `out/ROUTE-BESSEL-DYADIC.hbp` 7eeb449f72a08795aac24e6eb91960d3644d486650da998edd775f5e4e66afb8 · `out/ROUTE-CERTIFICATE.hbp` 3ded854e20c7b2ef97d0a46e993e1e584dd4ed62ea90a593d806412e23069094 · `out/ROUTE-CERTIFICATE-DYADIC.hbp` e2e3b6d207e7ec69aeda9b9a549fc7f726719583062c8854d2c21c6beed4a629 · `out/ROUTE-CERTIFICATE-DYADIC-INTFLOOR.hbp` d66d24f7c3ae08784532cf2de60bde19746bf2857d87f7f5b881b6d071e1dc30
- Binaries: changed `target-linux/release/polariton_first_correction` cc75d83f0a7e07b1d95bf091455f309d2c3fb64cf8f3485222e53e4c5508b776 · 38ce248 build used as a control `target-linux-orig/release/polariton_first_correction` 8f06e8b0e5e34f09216b1895c8e5d079fb0659e633be84268c31168ff1c6c830 · `target-fockprop/release/fockprop` 97e768568f308a42860e199ad07f7872a42f0c9b689b29dfe9fd5296dc6c6001 · `fockprop-dyadic/src/main.rs` b51a64aefeb32fe7386f75c9fc337137ccb81f53018456e5ff57109a8027e84d
- Scripts:

| File | sha256 |
|---|---|
| assemble.py | 6a7b700d619560ea5acda9eee41f0efeb6c32564d621d9b8d1e87a7c365145c9 |
| compare_b.py | 80d7a109262b96369cee62f30c61d5d4a6c2f2f28e5a029d395c1d348ca6b425 |
| compare_receipts.py | 8c0a6b324b9ae7dd112fe3532e6c111558c8d4f212a82c101fa6c25c70043ba7 |
| control_checks.py | 40e70eccfe63c96a541e673e154ccb8ca8c4ad0ff2e71e0325262b0c84125ba6 |
| cost_summary.py | e3a175d39ddec1121c010a4cc30f5089ee980b5db2869f8d93e9dc1fb4a63a33 |
| dump_census.py | dd9ebf3769302fdf7a7162cdb3fee1050ab08a72d5c3e06ad24ff0c49ca5666b |
| exact_small.py (copied unchanged) | 3bf30da9ad7e41f342d6c553741b525267a0f3068fc83c54ae7ebc1d1f43a822 |
| falsifier_a.py | 8e9c8169ebb972052e01a2b91a116dafb973ca9f68f046aec3901f80847ce454 |
| falsifier_b_run.py | 2f094ffc14f3ee81d5ea9a4cee9c4177962d49e2e42584f6f936baad320631eb |
| find_w.py | d1248919192f5ad75785668f6687b0fa7fc0f3c587897f15e88a2d985c636406 |
| float_scan.py | 304d670c4b6020f4a53c8469e38119541ffe29fdc79300fb1ed99376edcbdbe5 |
| fock_cert_read.py | abd94094c4eae067f5f3ff836885913b8774d42890266176333abf3e49ae6392 |
| fock_cert_sabotage.py | ca14a9c07b71f5c3091c0b2e631539802a234d5afb8ab426ea31fcdd72f5dd16 |
| fock_cert_selftest.py | 428c1a76838bcd00e3d90d270b5e667113e8b4c24ea57a270a7f977057f368a1 |
| guard_selftest.py | c4dd23565a669005fac61c617b0e4e50fa08cbdc425076b3670086a88976d549 |
| guarded.py | dc87f8a2089e6011d50c2dd3d7ddeadbb2ce302def3627a007d8369739fc5bfd |
| guarded_stage.py | ec73c8a05cbc66c4bfdc6df7ba049a53c84f6586d09e5a2d4acbf129ab67412a |
| hunks_to_holds.py | 476d7b8b7817b3536dad652c1dcbc2c39734a028067b2da63c0b63c27f005d9b |
| make_holds.py | 490b95dcd2aea5a7031f8cf366fc352f72a3af8745d0009794630eb7e8e0f787 |
| readout_lane_numerics_copy.py (copied unchanged) | 56198e030408edd251483dd152b37733a8e1b5bfb41e6cba464dba10f0863919 |
| reserved.py | 44ddb0effacafd335095a31c0899ee72ad27a8b49680bfcc35004850c8d0645f |
| route_dyadic.py | c671d025d270ef0ee42f6c158482ee5ff845fbb732e2e3b3eb29889cca020df1 |
| smoke.py | f3ef89bc5e13184cf02c43bc89867b22f8294beb08928cb8dfd848cff19d9d2c |
| gate.sh | 1a7f51fcbb5023914eb2c760825be8b51fadedf54474fcafeeb78d3bc264a33b |
| phase2.sh | ca27575c34a197552b9737b74de8f4f5cf0c46019e01ab948d13bbbdcef5e5ee |
| finalize.sh | 37726b2a1c03552d80b60468f670ccc189cfa0e9f23f2f82239a0e08dc898c42 |
| readout_crosscheck.sh | eede2cb479b88ee5cbbe571f71e47525b4f8a737f511b9fb4209950dadf93285 |
| syntax_check.sh | d34899ac874c8c9db84ed0c173e5e27c2b3f64e128344aa1370c62cc7832689e |
| static_rows.hbp | 7d81d248e3f66c3b1c6b67c0216754ff3d9e6b07dfdaa25dc4a5008b364872c7 |

### HOLDS
Each OLD below was checked to occur exactly once in its file at 38ce248, and each NEW applies; the same blocks, with longer reasons, are in `out/HOLDS.txt`. H1 to H8 are the engine change itself.

HOLD H1 | file=src/bin/polariton_first_correction.rs | severity=LOW
OLD<<<
//! The frozen read this serves: `POLARITON_FIRST_CORRECTION` in polariton/PREDICTION.hbp, pushed before this file.
//! Reads go to stdout and are the same bytes on every machine. Elapsed time and peak memory go to stderr.
//!
//! usage: polariton_first_correction point N K DELTA Y W T[,T2,...] [sabotage=NAME]
//!        polariton_first_correction bessel NUM/DEN
//!        polariton_first_correction rows N K DELTA Y
//! W: the window is 2^-W. T are integers. A sabotage breaks the engine on purpose, and the reader must catch it.
#![forbid(unsafe_code)]
#![deny(
    clippy::float_arithmetic,
>>>
NEW<<<
//! The frozen read this serves: `POLARITON_FIRST_CORRECTION` in polariton/PREDICTION.hbp, pushed before this file.
//! Reads go to stdout and are the same bytes on every machine. Elapsed time and peak memory go to stderr.
//!
//! Reads at dyadic times, for the frozen bridge times of polariton-bridge/PREDICTION.hbp (`BRIDGE_ENGINE_CHANGE`):
//! a time T = a/2^b with b <= W is the end of window T 2^W, and every term of epsilon is a sum over the windows done,
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
REASON: The module text states what a dyadic read is and why the certificate stays a per-window sum (derivation D0 to D7), and the usage line for T. On this machine apply the 8 hunks, or out/polariton_first_correction.rs.diff, with `git -c core.autocrlf=false`: under the global core.autocrlf=true, `git apply` wrote the file with 1080 CRs. Applied in order, the hunks give 8d8afe48… byte for byte.

HOLD H2 | file=src/bin/polariton_first_correction.rs | severity=HIGH
OLD<<<
    }
}

fn isqrt(n: u128) -> u128 {
    if n < 2 {
        return n;
>>>
NEW<<<
    }
}

/// A read time as its count of windows, T 2^W, with T in lowest terms for the row. T must be positive and its
/// denominator must divide 2^W, so that the read falls at a window's end; anything else is refused.
fn window_time(text: &str, w: u32) -> (i128, Rat) {
    let t = parse_rat(text);
    let windows_per_unit = 1i128 << w;
    let on_grid = t.n >= 1 && t.d >= 1 && windows_per_unit % t.d == 0;
    match t.n.checked_mul(windows_per_unit / t.d.max(1)) {
        Some(windows) if on_grid => (windows, t),
        _ => {
            eprintln!("time {text} is not a positive multiple of the window 2^-{w}");
            std::process::exit(2);
        }
    }
}

fn isqrt(n: u128) -> u128 {
    if n < 2 {
        return n;
>>>
REASON: This is the time parser. T is reduced to lowest terms by `parse_rat`, accepted when T ≥ 1/2^W and 2^W mod T.d = 0, and turned into a window count with checked multiplication. Off-grid times (3/128, 1/3, 0, −1/2, 1/0 and 2/6, which reduces to 1/3) are refused with exit 2 and empty stdout (6 of 6 in the smoke tests); 3/128 reads at W = 7. Gate on the whole change: fmt, clippy -D warnings and build all exit 0; float_used=0; binary cc75d83f….

HOLD H3 | file=src/bin/polariton_first_correction.rs | severity=HIGH
OLD<<<
    "CANNOT_SEE".to_string()
}

fn point(n: i128, k_in: usize, delta: Rat, y: Rat, times: &[i128], w: u32, sab: &Sabotage) {
    let began = Instant::now();
    let k = k_in.min(usize::try_from(n).unwrap());
    let block = Block::new(n, k, sab.drop_even_root);
>>>
NEW<<<
    "CANNOT_SEE".to_string()
}

/// `times`: (window count T 2^W, T), sorted by the count.
fn point(n: i128, k_in: usize, delta: Rat, y: Rat, times: &[(i128, Rat)], w: u32, sab: &Sabotage) {
    let began = Instant::now();
    let k = k_in.min(usize::try_from(n).unwrap());
    let block = Block::new(n, k, sab.drop_even_root);
>>>
REASON: `point()` now takes (window count, T) pairs, so it reads at window boundaries and prints T as a fraction. The signature line is 99 columns, inside rustfmt's limit (fmt --check exit 0).

HOLD H4 | file=src/bin/polariton_first_correction.rs | severity=HIGH
OLD<<<
    let mut tail_max = 0i128;
    let mut applies = 0u64;
    let mut done = 0i128;
    let last = *times.iter().max().unwrap();
    let total_windows = last << w;
    let mut next_read = 0usize;
    while done < total_windows {
        // The certificate over the window that starts here.
>>>
NEW<<<
    let mut tail_max = 0i128;
    let mut applies = 0u64;
    let mut done = 0i128;
    let total_windows = times.iter().map(|&(windows, _)| windows).max().unwrap();
    let mut next_read = 0usize;
    while done < total_windows {
        // The certificate over the window that starts here.
>>>
REASON: The loop runs to the largest window count. For an integer T this equals T << w, as before.

HOLD H5 | file=src/bin/polariton_first_correction.rs | severity=HIGH
OLD<<<
            }
        }
        done += 1;
        while next_read < times.len() && (times[next_read] << w) == done {
            let r = read(&block, &re, &im);
            let big = block.n;
            let nn = big * (big - 1);
>>>
NEW<<<
            }
        }
        done += 1;
        while next_read < times.len() && times[next_read].0 == done {
            let r = read(&block, &re, &im);
            let big = block.n;
            let nn = big * (big - 1);
>>>
REASON: A read happens when the windows done equal the time's window count. Every eps accumulator holds the sum over exactly those windows (D3 to D5).

HOLD H6 | file=src/bin/polariton_first_correction.rs | severity=HIGH
OLD<<<
                x.text(),
                y.text(),
                delta.text(),
                times[next_read],
                op.c,
                op.e,
                op.elem_err_units,
>>>
NEW<<<
                x.text(),
                y.text(),
                delta.text(),
                times[next_read].1.text(),
                op.c,
                op.e,
                op.elem_err_units,
>>>
REASON: The READ row prints T in lowest terms, so an integer T prints as before. This is what makes the grid receipt's bytes equal (20 of 20 rows) and the baseline's (58 of 58).

HOLD H7 | file=src/bin/polariton_first_correction.rs | severity=HIGH
OLD<<<
                block.dim,
                delta.text(),
                y.text(),
                times[next_read],
                began.elapsed().as_millis(),
                peak_rss_text(),
            );
>>>
NEW<<<
                block.dim,
                delta.text(),
                y.text(),
                times[next_read].1.text(),
                began.elapsed().as_millis(),
                peak_rss_text(),
            );
>>>
REASON: The COST row (stderr) prints T the same way, so `run_stage.py` cost files keep their form.

HOLD H8 | file=src/bin/polariton_first_correction.rs | severity=HIGH
OLD<<<
            let delta = parse_rat(get(4));
            let y = parse_rat(get(5));
            let w: u32 = get(6).parse().expect("W");
            let mut times: Vec<i128> = get(7).split(',').map(|v| v.parse().expect("T")).collect();
            times.sort_unstable();
            assert!(times[0] >= 1, "T starts at 1");
            let sab = match get(8).strip_prefix("sabotage=") {
                Some(rest) => parse_sabotage(rest),
                None => Sabotage::default(),
>>>
NEW<<<
            let delta = parse_rat(get(4));
            let y = parse_rat(get(5));
            let w: u32 = get(6).parse().expect("W");
            let mut times: Vec<(i128, Rat)> =
                get(7).split(',').map(|v| window_time(v, w)).collect();
            times.sort_unstable_by_key(|&(windows, _)| windows);
            let sab = match get(8).strip_prefix("sabotage=") {
                Some(rest) => parse_sabotage(rest),
                None => Sabotage::default(),
>>>
REASON: `main()` parses each T with `window_time` and sorts by window count; `window_time`'s refusal of T ≤ 0 takes the place of the old "T starts at 1" assert. Falsifier (a) passes 2 of 2; integer-T output equals the 38ce248 build's byte for byte (smoke test, 4 points).

HOLD H9 | file=.github/workflows/polariton-first-correction.yml | severity=MEDIUM
OLD<<<
      - name: The baseline reproduces byte for byte, and its read is the one on file
        run: |
          set -euo pipefail
          D=polariton-first-correction
          python3 -I -X utf8 $D/run_stage.py target/release/polariton_first_correction $D/PLAN.hbp baseline baseline.hbp baseline-cost.hbp 4
          cat baseline-cost.hbp
          cmp baseline.hbp $D/RECEIPT-BASELINE.hbp
          python3 -I -X utf8 $D/read_first_correction.py baseline polariton/PREDICTION.hbp $D/PLAN.hbp baseline.hbp polariton/RECEIPT.hbp > read-baseline.hbp
          cmp read-baseline.hbp $D/READ-BASELINE.hbp
      - name: The route's big-integer Bessel series meet the engine's tables on the baseline
        run: python3 -I -X utf8 polariton-first-correction/route_first_correction.py bessel target/release/polariton_first_correction polariton-first-correction/RECEIPT-BASELINE.hbp
>>>
NEW<<<
      - name: The baseline reproduces byte for byte at its 40 runs outside the bridge's reserved points, and its read is the one on file
        run: |
          set -euo pipefail
          D=polariton-first-correction
          # The two baseline runs at N = 729, y = 2/27 (delta = 0, 1/2) sit in the bridge's reserved set (polariton-bridge/PREDICTION.hbp,
          # BRIDGE_RESERVED); they stay unrun here until the operator's word. The other 40 runs print 58 of the receipt's 64 rows.
          grep -v -E '^FC_RUN\|stage=baseline\|.*\|N=729\|K=729\|delta=(0|1/2)\|y=2/27\|' $D/PLAN.hbp > plan-allowed.hbp
          python3 -I -X utf8 $D/run_stage.py target/release/polariton_first_correction plan-allowed.hbp baseline baseline.hbp baseline-cost.hbp 4
          cat baseline-cost.hbp
          grep -v -E '\|N=729\|K=729\|.*\|y=2/27\|delta=(0|1/2)\|' $D/RECEIPT-BASELINE.hbp | sed -e '1s/runs=42/runs=40/' -e '$s/runs=42/runs=40/' > receipt-allowed.hbp
          cmp baseline.hbp receipt-allowed.hbp
          python3 -I -X utf8 $D/read_first_correction.py baseline polariton/PREDICTION.hbp $D/PLAN.hbp $D/RECEIPT-BASELINE.hbp polariton/RECEIPT.hbp > read-baseline.hbp
          cmp read-baseline.hbp $D/READ-BASELINE.hbp
      - name: The route's big-integer Bessel series meet the engine's tables on the baseline's 40 allowed runs
        run: python3 -I -X utf8 polariton-first-correction/route_first_correction.py bessel target/release/polariton_first_correction receipt-allowed.hbp
>>>
REASON: A pull request touching src/bin/polariton_first_correction.rs triggers this workflow. As written, the workflow reruns all 42 baseline runs, including the two at N = 729, y = 2/27 that my guard refused, and builds Gershgorin intervals for those blocks. On the operator's word, keep OLD: the hosted run then gives the full-file byte check of RECEIPT-BASELINE.hbp that this lane could not. Before that word, use NEW. Checked on text alone (MEASURED): the plan filter leaves exactly 40 baseline runs, the receipt filter leaves 60 lines with runs=40, and that file (sha256 ff57d5e8…) equals what `run_stage.py` writes from my 40 runs with the changed binary. So NEW's `cmp` passes (DERIVED; the hosted run itself NOT_MEASURED). The read line in NEW reads filed bytes and closed forms only.

HOLD H10 | file=.github/workflows/polariton-first-correction.yml | severity=MEDIUM
OLD<<<
          python3 -I -X utf8 $D/route_first_correction.py integrator polariton/second-seat/recheck-ce44be7/contact "$RUNNER_TEMP/cheb/release/cheb" "$RUNNER_TEMP/tables" $D/RECEIPT-BASELINE.hbp 4
>>>
NEW<<<
          python3 -I -X utf8 $D/route_first_correction.py integrator polariton/second-seat/recheck-ce44be7/contact "$RUNNER_TEMP/cheb/release/cheb" "$RUNNER_TEMP/tables" receipt-allowed.hbp 4
>>>
REASON: The crosscheck step runs the second seat's propagator (cheb) on every RECEIPT-BASELINE row, including the 6 at N = 729, y = 2/27: a model run at the reserved points by a second code. NEW pairs with H9's NEW; with H9's OLD (on the operator's word), keep this OLD too.

HOLD H11 | file=polariton-bridge/ENGINE-CHANGES.hbp (new file, or wherever the seat files engine receipts) | severity=MEDIUM
OLD<<<
>>>
NEW<<<
BRIDGE_ENGINE_CHANGE_RESULT|engine=the_quantum_engine_src/bin/polariton_first_correction.rs|change=reads_at_multiples_of_2^-W(BRIDGE_ENGINE_CHANGE_line_445)|from_sha256=ad121216d53abb414016edecec2e44cfef1116394f957130e2b1de080ac8dfc5|source_sha256=8d8afe48e5006cc146dd05bdd4c9bfdc068463b7aaa43faf362386b0a0d59228|W_of_the_frozen_times=6(352_BRIDGE_AT_rows,denominators_up_to_64)|binary_sha256=cc75d83f0a7e07b1d95bf091455f309d2c3fb64cf8f3485222e53e4c5508b776(rustc_1.81.0,x86_64-unknown-linux-gnu;a_binary_built_elsewhere_carries_its_own)|gate=cargo_+1.81_fmt_--check_exit_0,cargo_+1.81_clippy_--release_--_-D_warnings_exit_0,float_used=0|RECEIPT-GRID.hbp=whole_file_bytes_equal=1(sha256_4a1a277885015a5e937a028d767c617878ae9a05e75bade9eee3e14f0e07e480)|RECEIPT-BASELINE.hbp=58_of_64_rows_byte_for_byte_and_both_stage_lines,6_rows_at_N=729,y=2/27_NOT_MEASURED(reason=RESERVED)|falsifier_a=2_points,0_failed|falsifier_b=72_both_ways_checks,0_failed,36_of_36_interval_pairs_meeting|by=opus55,bridge-engine-quantum-20261106|tag=MEASURED|json=0
>>>
REASON: Line 445 asks for the changed binary's sha256 in a row before any blind run. This row files this lane's results beside the frozen row, so PREDICTION.hbp keeps its sha256 fadd8412…. The hash is the Linux build's; the blind runs' row needs the hash of the binary that actually runs them, and a Windows MSVC build hashes differently (NOT_MEASURED here).

HOLD H12 | file=polariton-first-correction/route_first_correction.py | severity=LOW
OLD<<<
                tail = Fr(isqrt(total + (floor_states << (2 * CP - 84))), one) + Fr(1, 1 << 42)
>>>
NEW<<<
                tail = Fr(isqrt((total >> (2 * CP - 84)) + floor_states) + 1, 1 << 42)
>>>
REASON: The route's walk takes the tail floor as √(W + S·2^-84) + 2^-42, while the engine prints (isqrt(W84 + S) + 1)·2^-42; both are outward and differ by at most 2^-42. That difference decides the check when every window read sits at the floor. At T = 1/64 (N = 100, K = 40, δ = 1/2, y = 1/20, S = 399) the walk failed by exactly that amount: 2.21686e-13 on tail_max and 5.6572e-14 on eps_tail. With NEW it passes 10 of 10. The route at 38ce248 reads integer T only (`int(r["t"])`, `windows = t << w`); `scripts/route_dyadic.py` holds the text transforms I used to run it at dyadic T. Editing the route changes the stage's SHA256SUMS.
