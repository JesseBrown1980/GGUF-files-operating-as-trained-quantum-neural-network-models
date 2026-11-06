**Verdict: PASS_WITH_HOLDS.** I checked the round-2 trajectory engine (`traj_int.py`, c08a0c75…) and its stage files independently:

- **Gate:** the line-446 byte gate reproduces 3 of 3, on two interpreters with two different drivers.
- **float_used=0:** confirmed by my own scan.
- **Receipts:** 14 of the 19 receipts the lane lists reproduce byte for byte, including the slowest ones.
- **CORRECTIONS:** the rows match their frozen lines byte for byte.
- **Reserved points:** every run, the lane's and mine, was at an allowed point.

The main hold: I planted 12 faults in the round-2 code, and 9 of them pass every check the lane filed. H1 and H2 add checks that catch all 12; the engine still passes them (MEASURED). The other holds fix text, row content and checksum lines.

## What changed
- Everything I wrote is in `C:/tmp/opus55/bridge-engine-review2-trajectory-20261106/`:
  - `lane/`: a byte copy of the build folder (1,827 files, same file listing).
  - `repo_arch/`: `git archive` of 2ab8143.
  - `ci_tree/`: that archive plus the lane's 17 proposed files.
  - `ci_tree_prop/`: the archive plus my proposed files.
  - `rerun/`: the lane's tools, each with its one path line pointed at `rerun/`.
  - `mutv/`: my 12 planted faults.
  - `prop/` and `proposed_repo2/`: my proposed repo files.
  - `tools/`, `out/`, `snap/`: my scripts, receipts and before/after snapshots.
- I wrote nothing outside that folder (MEASURED, gate 9 below).

## Gate results (all MEASURED)
1. **Line-446 byte gate: 3 of 3, twice.**
   - The proposed job's `gate446.py` on WSL Python 3.12.3: 405 s with other lanes running, 298 s in the final run.
   - My own driver `gate_rv.py` on Windows Python 3.13.14: 404 s.
   - Outputs: e889958b… (63,198 bytes), bd4a3b90… (63,514), 8a5caf2e… (63,014), 0 CR bytes. They equal the hashes on line 446 and the design lane's files.
   - My first `gate_rv` attempt used a relative engine path; all 3 launches failed to open the file and 0 model steps ran. That attempt is kept in `out/gate_rv_win_attempt1_relative_path`.
2. **Proposed workflow: 9 of 9 steps exit 0.**
   - Run by my own runner, which parses the YAML (PyYAML 6.0.1), runs each `run:` as `bash -e`, and gives each job a fresh RUNNER_TEMP. The checkout step is replaced by the archive tree.
   - Its 5 receipts are byte-equal to the lane's: tests 488f1825, tests under -O ecf26eda, float scan 03564831, audit 14ef6cce, gate ee6f80e4.
   - Wall time with other lanes running: tests 15 s, float scan 106 s, audit 25 s, gate 405 s (about 9.2 min).
   - On the tree with my proposed files: 9 of 9 exit 0, tests 8 s, float 57 s, audit 19 s, gate 298 s (6.4 min). The tests are 172 + 454, with and without -O.
   - With row 8 added to ENGINE-CHANGES: the frozen job's 3 steps and the engine-sums step exit 0.
3. **float_used=0 (`float_rv.py`).**
   - Static: `traj_int.py`, `exact.py` and `s2_validate.py` have 0 float or complex constants, 0 uses of the names float/complex, 0 non-integer math, 0 negative literal powers.
   - Dynamic: every binary and unary operator in `traj_int.py` rewritten into a checked call; 19,178,118 operations ran, with 0 float or complex operands or results and 0 int/int true divisions. No float was returned or held as an attribute.
   - `test_engine.py` and `reserved.py` contain floats on purpose, as inputs that must be refused; none of them is on the engine's computation path.
4. **Receipts reproduced byte for byte: 14 of 19.**
   - `gate446_wsl`, `audit15` (and its 15 per-point receipts), `mut_table2` (and all 49 mutant receipts), `mutants2`, the three observable-bound falsifiers, `test_engine_src`, `test_engine_src_O`, `test_review172_src`, `float_scan_src`, `corrections_check`, `CORRECTIONS-trajectory`, `CORRECTIONS-trajectory-candidate`.
   - Also the 5 CI receipts that `ci_local.hbp` summarises.
   - The golden pins in the tests (STATES64, OBS64, READ364) recompute from the round-1 files.
   - The other five: I checked `gate446_win` with my own driver on the same interpreter, and the `ENGINE-CHANGES-trajectory-rows` figures by hand; `mut_table2_pass1`, `ci_local.hbp` and the assembled `BRIDGE-ENGINE-TRAJECTORY2.hbp` I left aside.
5. **Rust 1.81 clippy/fmt:** nothing to run. The engine folder has 0 `.rs` files; the build folder's 64 `.rs` files are all in its `repo/` archive copy.
6. **Mutation (12 faults, V01–V12).** The behavioural checks run were the tests (plain and -O), the round-1 review's 172 tests, and the audit at (1/2, 1/27) for 64 steps.

   | Fault | What it breaks | Lane's checks | My proposed checks (H1, H2) |
   |---|---|---|---|
   | V01 | R pinned at 1 | pass | audit R_COVER fails 23 times |
   | V02 | printed state bound halved in TRAJ_OBS_BOUND | pass | audit OBS_LO fails 2 |
   | V03 | printed state bound halved in TRAJ_BOUND | pass | audit ROW_LO fails 2 |
   | V04 | D2 square root rounded upward | pass | audit OBS_EXACT fails 2 |
   | V05 | half-step copy is a plain Traj (audit shows half_steps=0 and still reports PASS) | pass | HALF_AUDITED fails 1; test `half_step_copy_keeps_the_class` |
   | V06 | D2 rounding term = 0 where D2sq = 0 | pass | test `zero_field_D2_round_branch` |
   | V07 | image band loses its one unit | caught by the two band-edge tests | same |
   | V08 | reserved_open always printed as 0 | pass | test `reserved_open_printed_as_held` |
   | V09 | X rounding term uses 4R²q | caught by audit OBS_LO | OBS_LO and OBS_EXACT |
   | V10 | the 8q² term of the \|A\|² rounding dropped | pass | audit OBS_EXACT fails 2 |
   | V11 | y-image check without abs | caught by 34 tests | same |
   | V12 | R taken from the step's start state | pass | audit R_COVER fails 20 |

   - On the real engine the proposed audit passes 15 of 15 allowed points (320 steps each, all new counters 0), and the proposed tests pass 454 of 454.
   - The engine-sums step catches every fault only because the file's hash changes (DERIVED).
7. **CORRECTIONS.**
   - trajectory-1: the frozen text (104 bytes) sits at line 428, byte 297, and occurs once in the file.
   - trajectory-2 (the lane's H7 candidate): the frozen text (64 bytes) sits at line 446, byte 87, once.
   - Both rows follow the seat's field order. The header's `frozen_in=38ce248` matches: `git cat-file` of 38ce248 gives fadd8412…, PREDICTION.hbp's one commit.
   - values_moved=0 holds. Of the 352 BRIDGE_AT rows:
     - traj_V2 = (N−1)/N in 287;
     - (N−1)/N_where_A!=0 in 11;
     - UNDEFINED_0/0 in the 54 at y=0.
   - 120 of the times are odd multiples of 1/64 and none is finer. Each of the 20 (delta, y) points has at least one such time.
   - The 24 BRIDGE_TRAJ_PRED rows hold (N−1)/N and series values, all at multiples of 1/8.
8. **Reserved set, checked against my own predicate.**
   - Lane: 526 pre-run checks in 178 files, 0 hits. 2,021 run rows in 92 files, all at delta −1/2, 1/2, 3/4 and |y| 1/243, 1/81, 1/27, 4/81, 4/27, 0 hits.
   - Lane: 18 rows are `reserved.py`'s self-test, 12 of them at reserved values on purpose; that test is predicate-only and loads no engine.
   - Lane: in 6 test sections a planted fault reached the tripwire, which raised before any step: M13 ×2 at (3/5, 0), G14 and G16 in the u tests, S06 ×2.
   - Mine: 1,507 pre-run checks in 307 files and 2,833 run rows in 149 files, 0 hits. Every run was checked in code before it started.
9. **Read-only.** The build folder (listing 98c2aca5…) and the round-1 build, review and report folders hash the same before and after. The worktree is at 2ab8143 with 0 porcelain lines at start and end. Git was used for `rev-parse`, `status --no-optional-locks`, `log`, `cat-file` and `archive` only.

## Findings
- **The C1 and D2 bound derivations hold (DERIVED, my own derivation).**
  - Exact-solution parts: Cauchy–Schwarz, with |A| ≤ |z|²/√2, |B| ≤ |z|²/2, and |z| = 1 for the exact flow (norm conservation re-derived).
  - Rounding parts: X ≤ (1+√2)qf + (2+2√2)q·n0 + 3q + 4q², which sits under the engine's 5R²q + 3q + 6q². The A2, D2², f and A terms equal mine.
  - Every bound rounds upward. Python integers are unbounded, so there is no overflow. The index arithmetic in `read_at`, `time()`, `advance_to` and ROW_T is correct.
- **R matters in practice (MEASURED):** |Z|² − 1 reaches 7.75e-52 within 64 steps at (1/2, 4/27), so R > 1 enters every observable bound.
- **gate446.py's refusal paths work (MEASURED):** with PREDICTION.hbp, `s2_validate.py` or `exact.py` one byte off, it refuses 3 of 3 times and launches 0 runs. The CI job never exercises these paths.
- **A1 route (MEASURED):** reading A1 as sqrt(A1sq) differs from 2|A| by up to 6.22e4 times the 6q rounding part at (1/2, 1/243, t = 1/32). That is 5.07e-4 of the printed A1 bound, so the exact-solution part still covers it.
- **Minor audit inconsistency (MEASURED):** ROW_LO takes √2 from below in its A/N need, while OBS_LO takes it from above. Folded into H1.
- **Lane's quiet-machine timing (CANNOT_SEE):** the lane folder's only CI log is the loaded run (19 / 168 / 45 / 893 s). My quiet final run measured 8 / 57 / 19 / 298 s, close to the lane's quoted figures.
- **Other lane claims confirmed (MEASURED):**
  - 327 receipts, 0 with clock fields.
  - The bands 1/20 and 1/81 are the ensemble engine's (`e2_common.py` lines 62–64).
  - `exact.py` is a byte copy; `s2_validate.py` differs in lines 6 and 11 only.
  - `test_review172.py` is the round-1 review's file with only paths, the engine argument, the reserved import, the probe and the exit code changed.
  - The round-1 build folder's 71 files match their snapshot (c5ce4cc7…).
- **My own slips (MEASURED), each fixed and kept on file:**
  - a stray `python3 -` (the Windows stub waiting on stdin), stopped with nothing run;
  - the relative-path gate attempt noted in gate 1;
  - `float_rv` first refused an augmented assignment to a subscript (it fails safe), then handled it;
  - the run scanner first counted `reserved.py`'s self-test rows as runs, then counted them apart;
  - the CI dry run first printed MEASURED_PASS, then DRY_PRECHECK_ONLY.

## Files I made (folder C:/tmp/opus55/bridge-engine-review2-trajectory-20261106/)
- REVIEW2-TRAJECTORY.hbp 2f45c3877090c2eb15c7e8b3f97cae0af249cba5f9890ecb12ccc55c3c4c377e (267 rows, LF)
- REVIEW2-TRAJECTORY.hbp.sha256 b9f3187c7e5754a6e83fef80d7cbf048d7ffb9dd4d741f48ca2ec2046a75ad9b
- MANIFEST.sha256 bfd71c5ebd7c9bbf2210a368b58b115b96145083a455d7bec5e19480bcf34ba9 (all 5,790 files; check exit 0)
- out/ci_rv/ci_rv.hbp 3896715d…35e
- out/ci_rv_prop/ci_rv.hbp 152ff95b…663
- out/ci_rv_final_stage/ci_rv.hbp e21c9f33…64a
- out/gate_rv_win/gate_rv.hbp 79952d13…62e
- out/float_rv.hbp d34f7fb0…909
- out/corr_check_rv.hbp a5678116…d84
- out/lane_runs_rv.hbp 67b4fd8c…62e
- out/my_runs_rv.hbp aede39f9…17d
- out/cmp_ci.hbp b1cf54b4…494
- out/cmp_repro.hbp eec052fd…dcd
- out/cmp_mut.hbp b1bea8de…56f
- out/cmp_corrections.hbp a674d782…307
- out/prop_runs/runprop_rv.hbp dccd1ef8…683
- out/prop_audit15/prop_audit15.hbp 1ac101d7…bb3
- mutv/mutants_rv.hbp df7884cd…aed
- out/check_extra_engine.hbp f4747736…a14
- out/a1_route_rv.hbp 41ba1d59…1db
- out/gate_neg_rv.hbp 057bdd6a…efee
- out/ENGINE-CHANGES-review2-row.hbp f661ae65…573
- out/H1_check_audit.diff 89893448…920
- out/H2_test_engine.diff ba5b67a8…355
- The 24 scripts in tools/ and every other file are listed with full hashes in MANIFEST.sha256.

## Proposed repo files (C:/tmp/opus55/bridge-engine-review2-trajectory-20261106/proposed_repo2/)
- polariton-bridge/engines/trajectory/check_audit.py a10db050273449e6edf58927d670008c9cd0c4ffb12bb7651f5c661c26837ff4
- polariton-bridge/engines/trajectory/test_engine.py 2f047aa499ef068d65c9ae58f1a698b6eae12153de9edfddf8be06d8427f95db
- polariton-bridge/engines/trajectory/SHA256SUMS 68deffce7c62b51eef346540c5ebb7038044c7336bb00c225363279adaf702c3
- The engine folder's other 7 files are the lane's, byte for byte:
  - traj_int.py c08a0c75…
  - exact.py cb4c6936…
  - s2_validate.py 3d7dd175…
  - gate446.py 4b7c3840…
  - float_scan.py 8884ca69…
  - reserved.py 45a8a25c…
  - README.md 1f64e1bc…
- polariton-bridge/CORRECTIONS.hbp 22107ce8e1a35ed61bb60a08328c63300b2f64891f7f30a8fb4778d61c574834
- polariton-bridge/ENGINE-CHANGES.hbp 26007dba5c32d0c1600cd04bbde5f051904f6b56e6f1caeec39f852c6c11568f (8 rows)
- polariton-bridge/SHA256SUMS e7cc388bb325619b514a17a05530f883ec89721bdaf89439c1f5899588676cdc
- .github/workflows/polariton-bridge.yml f38502f413779fe0430548b791c9a33990194a660515a1be2c26ee9bb50b41c0 (the lane's, unchanged)

**My position on the lane's holds:**
- H1, H2, H3, H4, H8: agree, with my H1/H2/H3, H6, H5 and H7 respectively.
- H5 and H9: agree; together they need my H4.
- H6: keep the applied bands (my H8).
- H7: its text is accurate (frozen text at line 446, byte 87); whether to file it is the seat's call.

## HOLDS

HOLD H1 | file=polariton-bridge/engines/trajectory/check_audit.py | severity=MEDIUM
OLD<<<
(the lane's file, sha256 0c56a6312aa2b8537de4b18969e7e7fdfb89a75da5adda8d007b76fa689bc2c9; its lines 164, 202, 273-274, 289, 294, as in the diff below)
>>>
NEW<<<
(sha256 a10db050273449e6edf58927d670008c9cd0c4ffb12bb7651f5c661c26837ff4 = proposed_repo2/polariton-bridge/engines/trajectory/check_audit.py; diff -U0 against OLD:)
@@ -22,0 +23,5 @@
+#   R_COVER  : the engine's R = bR >= max(1, |Z|_2) exactly at every audited step (R enters every observable bound)
+#   OBS_EXACT: the exact rationals of _obs_terms, the values the rows round up, >= the needs of OBS_LO, and
+#              D2_round^2 D2sq >= D2sq_round^2 (the direction of the square root), D2_round^2 >= D2sq_round where D2sq = 0
+#   HALF_AUDITED: the half step of the read is one of the audited steps (the copy keeps the run's class)
+#   ROW_LO and OBS_LO also read the printed state_err_2norm_le >= e and R_now_le >= R of both rows.
@@ -164 +169,2 @@
-    fails = {'LOCAL_LO': 0, 'LOCAL_HI': 0, 'GLOBAL_LO': 0, 'ROW_LO': 0, 'ROW_T': 0, 'OBS_ROUND': 0, 'OBS_LO': 0}
+    fails = {'LOCAL_LO': 0, 'LOCAL_HI': 0, 'GLOBAL_LO': 0, 'ROW_LO': 0, 'ROW_T': 0, 'OBS_ROUND': 0, 'OBS_LO': 0,
+             'R_COVER': 0, 'OBS_EXACT': 0, 'HALF_AUDITED': 0}
@@ -202 +208 @@
-             'A1_err_le': 2 * (e * (R + 1) + need['A'])}
+             'A1_err_le': 2 * (e * (R + 1) + need['A']), 'state_err_2norm_le': e, 'R_now_le': R}
@@ -211,0 +218,9 @@
+        t_ex, _ = tr._obs_terms(NN)
+        if o['D2sq'] > 0:
+            d2_dir = t_ex['D2_round'] ** 2 * o['D2sq'] >= t_ex['D2sq_round'] ** 2
+        else:
+            d2_dir = t_ex['D2_round'] ** 2 >= t_ex['D2sq_round'] > 0
+        ex_ok = (d2_dir and t_ex['A2_round'] >= need['A2'] and t_ex['X_round'] >= need['X'] and t_ex['D2sq_round'] >= need['D2sq']
+                 and t_ex['X_exact'] >= X_ex and t_ex['D2sq_exact'] >= n['D2sq_exact_part_le'] and t_ex['D2_exact'] >= n['D2_exact_part_le']
+                 and t_ex['f_err'] >= n['f_err_le'] and t_ex['A_err'] >= n['A_over_N_err_le'])
+        fails['OBS_EXACT'] += 0 if ex_ok else 1
@@ -259,0 +275,2 @@
+            z2 = Fr(sum(v * v for v in (self.z0[0], self.z0[1], self.zp[0], self.zp[1], self.zm[0], self.zm[1])), 1 << (2 * P))
+            fails['R_COVER'] += 0 if (self.bR >= 1 and self.bR * self.bR >= z2) else 1
@@ -273,2 +290,3 @@
-        A_need = e * (Rn + 1) + SQ2_LO * 2 * qu
-        ok_row = parse_sci(f['f_err_le']) >= f_need and parse_sci(f['A_over_N_err_le']) >= A_need
+        A_need = e * (Rn + 1) + SQ2_HI * 2 * qu
+        ok_row = (parse_sci(f['f_err_le']) >= f_need and parse_sci(f['A_over_N_err_le']) >= A_need and parse_sci(f['R_now_le']) >= Rn
+                  and ((f['state_err_2norm_le'] == '0' and e == 0) or (f['state_err_2norm_le'] != '0' and parse_sci(f['state_err_2norm_le']) >= e)))
@@ -285,0 +304 @@
+    fails['HALF_AUDITED'] += 0 if stats['half_steps'] == 1 else 1
@@ -289 +308,2 @@
-                'LOCAL_HI_fail=%d|GLOBAL_LO_fail=%d|ROW_LO_fail=%d|ROW_T_fail=%d|OBS_ROUND_fail=%d|OBS_LO_fail=%d|row_t=%s|'
+                'LOCAL_HI_fail=%d|GLOBAL_LO_fail=%d|ROW_LO_fail=%d|ROW_T_fail=%d|OBS_ROUND_fail=%d|OBS_LO_fail=%d|R_COVER_fail=%d|'
+                'OBS_EXACT_fail=%d|HALF_AUDITED_fail=%d|row_t=%s|'
@@ -294 +314 @@
-                    fails['OBS_ROUND'], fails['OBS_LO'], fm['t'], checked[1][1]['t'],
+                    fails['OBS_ROUND'], fails['OBS_LO'], fails['R_COVER'], fails['OBS_EXACT'], fails['HALF_AUDITED'], fm['t'], checked[1][1]['t'],
>>>
REASON: Seven of my faults pass every filed behavioural check, and this audit change targets them. V01 and V12 pin R or take it from the step's start state. V02 and V03 halve the printed state bound, which is the number BRIDGE_ERRORS integration_trajectory names. V05 makes the half-step copy a plain Traj; the audit then never audits the half step (half_steps=0) and still reports PASS. V04 and V10 are rounding-direction faults of size 2^-768 and 8q². With NEW the audit fails on V01 (R_COVER 23), V02 (OBS_LO 2), V03 (ROW_LO 2), V04 (OBS_EXACT 2), V05 (HALF_AUDITED 1), V09 (OBS_LO 2, OBS_EXACT 2), V10 (OBS_EXACT 2) and V12 (R_COVER 20). It passes on the engine at all 15 allowed points over 320 steps each, and in the CI step. The comment-only edit since those runs leaves the same AST (MEASURED). The AUDIT row gains three fields, so the audit receipts get new sha256 values.

HOLD H2 | file=polariton-bridge/engines/trajectory/test_engine.py | severity=LOW
OLD<<<
#     both bound rows, the rounding parts of the observable bounds at the integer state, the V2 identity, y = 0.
    record('NEW_OBS', 'zero_field_fixed_point', (z.z0, z.zp, z.zm) == ((N.ONE, 0), (0, 0), (0, 0)) and z.berr == 0
           and rz['V2_identity_err_le'] == 'undefined_X=0' and rz['state_err_2norm_le'] == '0',
           'state_err=%s|V2_identity=%s' % (rz['state_err_2norm_le'], rz['V2_identity_err_le']))
>>>
NEW<<<
#     both bound rows, the rounding parts of the observable bounds at the integer state, the V2 identity, y = 0,
#     the D2 rounding branch at y = 0, reserved_open as each row prints it, and the class of the half-step copy.
    record('NEW_OBS', 'zero_field_fixed_point', (z.z0, z.zp, z.zm) == ((N.ONE, 0), (0, 0), (0, 0)) and z.berr == 0
           and rz['V2_identity_err_le'] == 'undefined_X=0' and rz['state_err_2norm_le'] == '0',
           'state_err=%s|V2_identity=%s' % (rz['state_err_2norm_le'], rz['V2_identity_err_le']))
    tz, oz = z._obs_terms(729)
    record('NEW_OBS', 'zero_field_D2_round_branch', oz['D2sq'] == 0 and tz['D2_round'] > 0 and tz['D2_round'] ** 2 >= tz['D2sq_round'],
           'D2sq=%s|D2_round=%s' % (oz['D2sq'], N._sci_up(tz['D2_round'])))
    lab = fields(z.bound_row())['reserved_open'] + fields(z.obs_bound_row(729))['reserved_open']
    z.reserved_open = True
    lab += fields(z.bound_row())['reserved_open'] + fields(z.obs_bound_row(729))['reserved_open']
    z.reserved_open = False
    record('NEW_LABEL', 'reserved_open_printed_as_held', lab == '0011', 'printed=%s' % lab)

    class Sub(N.Traj):
        pass
    sb = Sub(Fr(1, 2), Fr(0), bound=True)
    record('NEW_STEPS', 'half_step_copy_keeps_the_class', type(sb.read_at(Fr(1, 64))) is Sub, 'class=%s' % type(sb.read_at(Fr(1, 64))).__name__)
>>>
REASON: V06 (the D2 rounding term set to 0 where D2sq = 0) and V08 (reserved_open always printed 0) pass every filed check. The y = 0 branch is reached only at zero-field points, and reserved_open = 1 only at the blind points, so an allowed-point test like these is the only way to see them before the blind runs. The reserved_open test only formats rows of an allowed-point object. MEASURED: the new tests fail on V06, V08 and V05 respectively, and 454 of 454 new tests pass on the engine with and without -O. The file is 2f047aa4….

HOLD H3 | file=polariton-bridge/engines/trajectory/SHA256SUMS | severity=LOW
OLD<<<
0c56a6312aa2b8537de4b18969e7e7fdfb89a75da5adda8d007b76fa689bc2c9  check_audit.py
56c05c4df3b9b84af18d5e20aab5315e6fa22c3fb22cdd85b6dd1ffe58c81645  test_engine.py
>>>
NEW<<<
a10db050273449e6edf58927d670008c9cd0c4ffb12bb7651f5c661c26837ff4  check_audit.py
2f047aa499ef068d65c9ae58f1a698b6eae12153de9edfddf8be06d8427f95db  test_engine.py
>>>
REASON: With H1 and H2 in place, SHA256SUMS becomes 68deffce… (it replaces the lane's c6da0dd8…). The engine-sums step exits 0 with it, and so do all 9 workflow steps on that tree (MEASURED).

HOLD H4 | file=polariton-bridge/SHA256SUMS | severity=LOW
OLD<<<
33fc48048de5319a5e2292120b5e4e40e6f0a3762a8137b27d18b3059db2f5e9 README.md
>>>
NEW<<<
49d0932604018f935cb9a56f6735b8419560f09b0288b64d6e56de06d5f2f36e README.md
>>>
REASON: The lane's H9 turns README.md into 49d09326…, but the lane's H5 keeps its old checksum line. I applied H9 to a scratch copy: with H5's lines the frozen job's stage_sums step exits 1 (README.md FAILED), and with this line it exits 0 (MEASURED, out/h9_check). With my H5 and H6, the file's other two lines are 22107ce8… CORRECTIONS.hbp and 26007dba… ENGINE-CHANGES.hbp. That file is proposed_repo2/polariton-bridge/SHA256SUMS (e7cc388b…), which keeps the README line at 33fc4804… until H9 lands.

HOLD H5 | file=polariton-bridge/CORRECTIONS.hbp | severity=LOW
OLD<<<
traj_V2=(N-1)/N_exactly_in_298_of_352_BRIDGE_AT_rows_and_UNDEFINED_0/0_in_the_54_at_y=0,
>>>
NEW<<<
traj_V2=(N-1)/N_in_287_of_352_BRIDGE_AT_rows,(N-1)/N_where_A!=0_in_11_and_UNDEFINED_0/0_in_the_54_at_y=0;the_24_BRIDGE_TRAJ_PRED_rows_hold_V2_traj=(N-1)/N_and_series_values_at_multiples_of_1/8,
>>>
REASON: My own parse of the frozen file (MEASURED) finds 287 rows with (N−1)/N and 11 with (N−1)/N_where_A!=0, at t = 55/16 to 99/16. The lane's counter (corrections.py line 47) strips "_where_A!=0" before comparing, so its 298 includes those 11. The value-dependent BRIDGE_TRAJ_PRED rows all sit at multiples of 1/8. values_moved=0 stands. The new file is 22107ce8…, and its frozen_text still sits at line 428, byte 297.

HOLD H6 | file=polariton-bridge/ENGINE-CHANGES.hbp | severity=NOTE
OLD<<<
|holds=H6_to_H15_of_bridge-engine-review-trajectory-20261106|tag=MEASURED|json=0
>>>
NEW<<<
|reserved_runs_started=0(this_review_183_reserved-check_rows,0_hits;the_lane's_1259_model_rows_in_26_files_at_15_allowed_points)|holds=H6_to_H15_of_bridge-engine-review-trajectory-20261106|tag=MEASURED|json=0
(row 7 as the lane proposes it, then row 8:)
BRIDGE_ENGINE_REVIEW|engine=the_trajectory_integrator(polariton-bridge/engines/trajectory/traj_int.py)|changes=round_2(source_c08a0c75)|by=opus55,bridge-engine-review2-trajectory-20261106(BRIDGE_ORDER_step_4)|verdict=PASS_WITH_HOLDS|gate=byte_for_byte_3_of_3_by_the_review's_own_driver(Windows_Python_3.13.14)_and_3_of_3_by_the_proposed_job_run_locally(WSL_Linux_Python_3.12.3),float_used=0(static_and_every_operator_rewritten:19178118_operations)|ci=the_proposed_workflow_9_of_9_steps_exit_0(failed=0),its_5_receipts_byte_equal_to_the_lane's|reproduced=14_of_the_lane's_19_receipts_byte_for_byte,the_slowest_among_them(the_gate,audit15,the_49_mutant_receipts_and_their_table)|mutants=12_planted_in_the_round-2_parts,3_caught_by_the_filed_checks,12_by_the_checks_of_holds_H1_and_H2|reserved_runs_started=0(this_review_1507_reserved-check_rows,0_hits;the_lane's_526_rows_and_2021_run_rows_at_15_allowed_points)|receipt=REVIEW2-TRAJECTORY.hbp_sha256=2f45c3877090c2eb15c7e8b3f97cae0af249cba5f9890ecb12ccc55c3c4c377e|holds=H1_to_H9_of_bridge-engine-review2-trajectory-20261106|tag=MEASURED|json=0
>>>
REASON: The quantum engine's review row carries reserved_runs_started; the trajectory review rows should carry it too. The round-1 counts come from the round-1 review's report. Rows 1–4 stay byte-equal to 2ab8143's file, and rows 5 and 7 equal the lane's. The file becomes 26007dba…, and the frozen job's three steps exit 0 with it (MEASURED).

HOLD H7 | file=the trajectory blind-run driver (the lane's H8 text) | severity=NOTE
OLD<<<
            o = r.obs(N)                              # A1, C1, V2, f, D2 in the quantum read's normalisation
            print(r.obs_bound_row(N))                 # A1, C1, f, D2 and the V2 identity bounds at this N
>>>
NEW<<<
            o = r.obs(N)                              # A1, C1, V2, f, D2 in the quantum read's normalisation
            # A1 = 2|A| from o['A_re'], o['A_im'] (the route A1_err covers); D2 = sqrt(o['D2sq']); V2 = o['A1sq'] / (2 o['C1'])
            print(r.obs_bound_row(N))                 # A1, C1, f, D2 and the V2 identity bounds at this N
>>>
REASON: A1_err's rounding part (6q) covers A1 computed as 2|A| from A_re and A_im. If the driver reads A1 as sqrt(A1sq) instead, the floor in A2 adds up to 2q/|A|. That is 6.22e4 × 6q at (1/2, 1/243, t = 1/32), which equals 5.07e-4 of the printed A1_err (MEASURED). There the exact-solution part covers it, at every allowed point read.

HOLD H8 | file=polariton-bridge/engines/trajectory/traj_int.py | severity=NOTE
OLD<<<
BAND_DELTA = Fr(1, 1 << 128)
BAND_Y = Fr(1, 1 << 128)
>>>
NEW<<<
BAND_DELTA = Fr(1, 20)
BAND_Y = Fr(1, 81)
>>>
REASON: OLD is the lane's H6 NEW; NEW keeps the band text that is in the file now. Those bands are the ensemble engine's widths (`e2_common.py` lines 62–64), and every listed value lies outside them; the nearest are delta = 1/2 at 1/10 and |y| = 4/81 at 2/81. They refuse the float 2/27 and the decimal string by band as well as by the list and type checks. The gate, the tests and the audit all pass with them (MEASURED).

HOLD H9 | file=polariton-bridge/reviews/opus55-engine-trajectory-20261106/ (new folder) | severity=NOTE
OLD<<<
(the stage's reviews/ holds opus55-engine-quantum-20261106/ alone)
>>>
NEW<<<
build1/BRIDGE-ENGINE-TRAJECTORY.hbp c9bb6ec03116f491b73327e9eadbb74565d5a860a8ca93f12eed8c2609b8a656
build1/REPORT.md d5f99d8a6f618d54afcd4ac4f651e4af9ea580760e94c8f18c9e7337197f9d3b (round1-reports/trajectory-build.md)
review1/REVIEW-TRAJECTORY.hbp 18d633f5f7dea88f81743a799ee49fae7beb269901b052db049ceb8700fdc749
review1/REPORT.md 14fcc75f85ddb6861b4f83fffc7d4804f430a8d79f529351f985b51bc77c224b (round1-reports/trajectory-review.md)
build2/BRIDGE-ENGINE-TRAJECTORY2.hbp b3af77267a593aa2fedb442f81716a4609a0beab28a5845007316b813f64b820
build2/REPORT.md (the round-2 build report the seat holds)
review2/REVIEW2-TRAJECTORY.hbp 2f45c3877090c2eb15c7e8b3f97cae0af249cba5f9890ecb12ccc55c3c4c377e
review2/REPORT.md (this report)
README.md and HOLDS-APPLIED.hbp by the seat, and SHA256SUMS over the folder
>>>
REASON: The ENGINE-CHANGES rows cite these receipts by sha256. The quantum engine's lanes file theirs under reviews/ with a SHA256SUMS that the frozen job checks. The five receipt and report files listed with hashes are all LF (0 CR bytes, MEASURED).
