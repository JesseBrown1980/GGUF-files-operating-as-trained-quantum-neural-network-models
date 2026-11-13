I've finished round 2 of the trajectory integrator. The line-446 byte gate passes 3 of 3 on two interpreters. The review's 172 tests and 451 new ones pass, also under python -O. The audit passes at all 15 filed points. All 49 planted faults are caught. Every model run was at an allowed point.

## What changed
The engine is `traj_int.py` (sha256 c08a0c75…, 484 lines). It starts from the review's proposed file 18f2a85b… (hash checked) and changes it by +166/−19 lines. The integration code itself (taylor_step, horner, obs, _bound_step, _residual) is unchanged text.

- **Guard (H6).** It now reads each argument twice: as the exact rational, and as the 2^-256 image the run uses (delta, x = delta − 1, and y).
  - Each is checked against the allowed lists, the reserved values and a band around each reserved value: |delta ∓ 3/5| < 1/20 and ||y| − 2/27| < 1/81.
  - `guard_checks()` names every check that refuses, so each layer is tested on its own.
  - The three inputs you listed are refused (MEASURED). 2/27 + 2^-300 hits Y_LIST, Y_BAND and Y_IMAGE, and its image equals the image of 2/27. The float 2/27 is refused by the type check, and as a Fraction it hits the same three. The string 0.0740740740740741 hits the same three.
  - Under the flag, delta = ±3/5 opens only when the exact value and its image both match. y = ±2/27 opens only there.
  - u must be exactly 1, and the run's own images x, y, u are checked against the ones the guard compared.
- **The bands.** The review's report proposes no band; its tool (reserved_rv.py) uses 2^-128. The engine uses the ensemble engine's widths, which contain 2^-128 and also catch the float and the string by band. That choice is H6 below.
- **Audit as a gate tool (H7).** `check_audit.py` is the review's audit_rv.py with three additions: ROW_T counts half steps, OBS_ROUND checks the rounding of obs() at every state, and OBS_LO checks the new observable bounds. Each run ends with one half-step read.
- **Every step-grid, flag and argument check is now an explicit raise (H8–H10).** advance_to also refuses a time behind the run, and _exp_up and K are checked too. bound=1 is refused, and the bound rows refuse a run without the bound.
- **Half-step read labels (H11).** Both bound rows print `steps=j|half_step=1|h=1/32`.
- **No clock values in receipts (H13, H14).** 327 receipts scanned, 0 with a wall-time field (MEASURED). Wall times go to `*.timing.log` and stdout. The local CI run's gate receipt is byte-identical to the earlier one (ee6f80e4…).
- **C1 and D2 bounds (F13).** `obs_bound_row(N)` prints bounds for A1, C1, f, D2, D2², and the V2 identity, each as an exact-solution part plus a rounding part.
  - Exact-solution parts (DERIVED): the review's forms, |ΔX| ≤ (R²+1)(R+1)e and |Δ(conj(z−)z+)| ≤ (R+1)e, so D2 gets 2(R+1)e.
  - Rounding parts (DERIVED): X ≤ (2+2√2)R²q + 3q + 6q², A2 ≤ 4R²q + q + 8q², D2² ≤ 4√2R²q + 4q + 8q².
  - T_V2_ID depends only on the rounding of obs(), because |A(Z)|² = X(Z) exactly at the integer state. Its bound is (A2_round + X_round)/X.

## Gate results (all MEASURED)
1. **Line-446 byte gate: 3 of 3, twice.**
   - WSL Ubuntu 24.04, Python 3.12.3: 295 s for the three in parallel. Windows Python 3.13.14: 324 s.
   - Outputs e889958b…, bd4a3b90…, 8a5caf2e… (63,198 / 63,514 / 63,014 bytes, 0 CR).
2. **Tests.** The review's own file (only its paths changed) passes 172 of 172. `test_engine.py` passes those 172 plus 451 new ones, with and without python -O. Reruns reproduce the receipts byte for byte.
3. **Audit at the 15 filed points: 15 of 15.** Each point is 320 steps plus one half step, and every check has 0 failures.
   - Largest state bound is 1.25e-41 at (−1/2, 4/27), where C1 ≤ 9.95e-41, D2 ≤ 4.97e-41 and the V2 identity ≤ 7.95e-76.
   - Measured rounding as a share of its derived bound: f just under 1, X up to 0.83, A 0.79, D2² 0.77.
4. **Mutants: 49 of 49 caught.** That is the review's 16 (M13, M14 and M16 re-planted on the new text) plus 33 of mine on the guard, the explicit checks, the labels and the observable bounds.
   - The six faults round 1's checks missed:
     - M06 is caught by audit ROW_LO.
     - M07–M09 by audit LOCAL_LO and the pinned read_at test.
     - M10 by LOCAL_LO and GLOBAL_LO.
     - M16 by ROW_T and the label tests.
   - O01–O08 (the observable-bound faults) are caught by OBS_LO only.
   - The first pass caught 48. S03 was missed because the probe never read off the half-step grid on a fresh run; I added that case, and the earlier pass is kept in out/mut_pass1. A rerun after a comment-only text patch matched the second pass byte for byte, 49 of 49.
5. **float_used=0, static and dynamic.**
   - Static: 0 float tokens.
   - Rewrite: 279 true divisions with 0 int/int, and 814 powers.
   - Trace: 88,256,984 values classified, 0 float.
6. **C1/D2 falsifier.** At 3 points × 7 reads, against a finer reference run (order 36, h = 1/64, 2^-320), 0 differences exceed the bounds. The tightest bound/difference ratios are A 2.10, f 12.1, C1/X 12.6, D2 7.36.
7. **CI job, run locally: 9 of 9 steps exit 0.**
   - WSL, Python 3.12.3, the checkout replaced by the archived tree with the proposed files laid over it.
   - Quiet machine: tests 8 s, float scan 60 s, audit 20 s, gate 318 s, about 6.8 min.
   - While other lanes' cargo and twens builds were running: about 18.8 min.
   - Under 30 min on a hosted runner is a CONJECTURE until it runs there.
8. **Rust 1.81 clippy/fmt** have nothing to run on: the engine is Python and its folder has 0 .rs files.
9. **Reserved points.**
   - 526 reserved-point checks across my runs, 0 hits, and 0 model runs at a reserved value.
   - In 6 test sections a planted fault reached a tripwire, and the tripwired fx raised before computing anything. For M13 that was at (3/5, 0); for G14, G16 and S06 it was at (1/2, 1/27).
10. **Read-only.**
    - The worktree is clean at 2ab8143 at start and end.
    - The review folder matches its 773-file manifest, the build lane its 71-file snapshot, and the round-1 reports their checksums.
    - Git was used for rev-parse, status and archive only.

**CORRECTIONS.** None of the 15 round-1 trajectory holds names PREDICTION.hbp as its file. H1 changes how line 428 reads (it says h=1/32), so it becomes row trajectory-1 (ENGINE_DETAIL). Its frozen text occurs once, at byte 297 of line 428. It moves no values: 298 of 352 BRIDGE_AT rows hold traj_V2 = (N−1)/N exactly and the 54 at y=0 hold UNDEFINED_0/0. 120 BRIDGE_AT times sit off the 1/32 grid, and all 20 blind points have at least one.

**ENGINE-CHANGES.** Three rows: the lane's H2, the review's H15, and this round's result.

## Files (folder C:/tmp/opus55/bridge-engine-trajectory2-20261106/)
- BRIDGE-ENGINE-TRAJECTORY2.hbp b3af77267a593aa2fedb442f81716a4609a0beab28a5845007316b813f64b820 (146 rows)
- its sidecar 06a8ef5bc24fd428988b5ff199e004405ef2fabb229e4eb6c507b21d064ba736
- MANIFEST.sha256 4704aa651d2a481fc964f33930f69661852978b9cc9927443f9261e5eb670637 (all 1,826 files, check exit 0)
- src/traj_int.py c08a0c75bf7d089875d2e6017b731bac767fb93fff849464f9af9d9849afb504
- out/gate446_wsl/gate446.hbp ee6f80e42ff0f1858f0aee9ce2a1432a65334e90a5d887d12f26de35e61f1e29
- out/gate446_win/gate446.hbp e60b5d99109d31fa780f3e2d52d9868f11db950a1d978f9730c7b85c27a8919b
- out/test_review172_src.hbp f6cc0b023dcc47adfe0de6c145e563258c6bf59e29093facc601dcf0a9916ff5
- out/test_engine_src.hbp 6988a86bda40c452d5cd9939ca8386586cd0e5c1509af06c7f81265b7ae85999
- out/test_engine_src_O.hbp 99a8074d27e24cf87e897f31a3f623a688bcfb8dcbbbbdce4866359106c76077
- out/audit15.hbp b4969055a0e85edc155a0bdb9ead6cebcf6dedb9a634705dfcf1152c0359ab41
- out/mutants2.hbp 4cdb56fa06616bcd34833140c0354f06bf5eca9b45afb49913454bab8c4f5397
- out/mut_table2.hbp 81baf9ec188d7af3ac2c942f2c8afdfa2c30dcf6fd91f043a55a915ec4d85619
- out/mut_table2_pass1.hbp 48eab8898a437d3efba3172221da672b7698cfa4319817cad43bfa3f5fb3b977
- out/float_scan_src.hbp 9bc69862ef41bf713e2706bc2ddc916d4f8465a78ecd255fad7232bf43e7de88
- out/obs_falsifier_d1o2_y4o27.hbp 9081cbfe63cef33478a2eab48f6288c66f60d2986dbdc6600740906b7ba17502
- out/obs_falsifier_dm1o2_y4o27.hbp efd6805d897d5c3a14a3fc2b4f8ab17231069a7b0f5b640f6184847a0dea852e
- out/obs_falsifier_d3o4_y1o27.hbp 361a2186065c0c0ec94fd915bfe98abcbbd6a8717c5818eb78e2b90a820bb96b
- out/corrections_check.hbp 8a98ac7245604d47821c93266389c9be809b61ae9f5a97b26fa83817f1d25330
- out/CORRECTIONS-trajectory.hbp 5d7395450f0955f3169c39debdb055713e380c616a65e838d9ac5e0f42acae75
- out/CORRECTIONS-trajectory-candidate.hbp 497bc8e9b3017129f5b57fd756dab0c237aaaa2e332938e599e198e7975da4f8
- out/ENGINE-CHANGES-trajectory-rows.hbp 08f70fda8245251938f3f5484e07bbd502b26e45609f7b809d29b2a86d60dfa2
- out/ci_local.hbp a4bf1b9e58048f3c11727923e0d5a6bed683fa841b77d46158f5b023c2962a1a
- out/ci_local.timing.log 7288c9bb4d9f8c0c0a923f873803ee843ecf179c4198372c29d4b9c08b7b60e7 (the times)

## Proposed repo files (under proposed_repo/)
- polariton-bridge/engines/trajectory/
  - traj_int.py c08a0c75bf7d089875d2e6017b731bac767fb93fff849464f9af9d9849afb504
  - exact.py cb4c69367764a0f0ce4d2ee56adfb1d1089fbeaf4fa6abc6b80a01a754236a19
  - s2_validate.py 3d7dd17558ff9477769757a3ccd19eadac666d61c0b718bb34901c28692aad0c
  - gate446.py 4b7c38406be5af413b73436d95d3e34a33d87cebc50659241dad897b21823c55
  - test_engine.py 56c05c4df3b9b84af18d5e20aab5315e6fa22c3fb22cdd85b6dd1ffe58c81645
  - check_audit.py 0c56a6312aa2b8537de4b18969e7e7fdfb89a75da5adda8d007b76fa689bc2c9
  - float_scan.py 8884ca692acb12611f026d72cf6c362fbec883c7174bd3fbb969dbec5bb1c4b3
  - reserved.py 45a8a25c9422c4eb0387b9bbaf451da332c5aaf9d2e64fa5db637450b13bf9ae
  - README.md 1f64e1bce2d32e4b61d94c309c5744dcacb9e9cfe3b9117731fa0b3cc6a0dcd1
  - SHA256SUMS c6da0dd86e41d9eb0379ae4960c07700e947e8e6d752e44cc47d72625407ed1f
- polariton-bridge/ENGINE-CHANGES.hbp 92b1ce0d01756870bc46aca45751b69a9948757df99ec6878a48efd05deb2acd
- polariton-bridge/CORRECTIONS.hbp 69b4bf45de875f5e7e9490f7b4bb326a0d33b09a34760e2b50bdd7c2df16c4fe
- polariton-bridge/SHA256SUMS f5c9c10cee7a7b7721e8752132e2af5ae24cc239304de406fc977a23d704c3a6
- .github/workflows/polariton-bridge.yml f38502f413779fe0430548b791c9a33990194a660515a1be2c26ee9bb50b41c0

## Holds

HOLD H1 | file=polariton-bridge/engines/trajectory/ (new folder) | severity=HIGH
OLD<<<
(folder absent)
>>>
NEW<<<
The ten files of C:/tmp/opus55/bridge-engine-trajectory2-20261106/proposed_repo/polariton-bridge/engines/trajectory/, byte for byte, at the sha256 values of the list above (SHA256SUMS c6da0dd8…).
>>>
REASON: 120 of the 352 BRIDGE_AT times sit at odd multiples of 1/64, and all 20 blind (delta, y) have one. `read_at` is the engine's route to those times, with the half step bounded and labelled. The folder holds the engine with round-1 holds H6–H14 applied and the F13 bounds, plus its gate, tests, audit and float scan. The gate passes 3 of 3 on two interpreters, the tests pass 172 + 451 with and without -O, the audit passes 15 of 15, and 49 of 49 mutants are caught. s2_validate.py differs from the design lane's 69c19c27… in lines 6 and 11 only, and exact.py is a byte copy.

HOLD H2 | file=.github/workflows/polariton-bridge.yml | severity=MEDIUM
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
  trajectory:
    name: The trajectory engine, its guard and step tests, float scan, the audit at one point and the line-446 byte gate
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    steps:
      - name: Checkout, on a pull request its merge with the base
        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      - name: The engine folder at its sums, and the interpreter
        run: |
          set -euo pipefail
          (cd polariton-bridge/engines/trajectory && sha256sum --strict -c --quiet SHA256SUMS)
          python3 --version
      - name: The tools' reserved-point check, predicate only
        run: python3 -I -B -X utf8 polariton-bridge/engines/trajectory/reserved.py
      - name: The guard and step tests (the review's 172 and the round-2 tests), with and without python -O
        run: |
          set -euo pipefail
          mkdir -p "$RUNNER_TEMP/trajectory"
          cd polariton-bridge/engines/trajectory
          python3 -I -B -X utf8 test_engine.py traj_int.py "$RUNNER_TEMP/trajectory" engine
          python3 -O -I -B -X utf8 test_engine.py traj_int.py "$RUNNER_TEMP/trajectory" engine_O
      - name: float_used=0 by the static scan and the two dynamic scans
        run: python3 -I -B -X utf8 polariton-bridge/engines/trajectory/float_scan.py polariton-bridge/engines/trajectory/traj_int.py "$RUNNER_TEMP/trajectory" engine
      - name: The audit of the printed bounds at delta = 1/2, y = 1/27, 320 steps and a half-step read
        run: python3 -I -B -X utf8 polariton-bridge/engines/trajectory/check_audit.py polariton-bridge/engines/trajectory/traj_int.py 1/2 1/27 320 d1o2_y1o27 "$RUNNER_TEMP/trajectory"
      - name: The line-446 byte gate, three runs against the sha256 values line 446 names
        run: python3 -I -B -X utf8 polariton-bridge/engines/trajectory/gate446.py "$RUNNER_TEMP/trajectory/gate446"
>>>
REASON: I ran every step locally on WSL Ubuntu 24.04 with Python 3.12.3, the hosted runner's interpreter: 9 of 9 steps exit 0. It took about 6.8 min on a quiet machine and about 18.8 min while other lanes ran. The frozen job stays as it is. The job uses only the pinned checkout action and the runner's own python3.

HOLD H3 | file=polariton-bridge/ENGINE-CHANGES.hbp | severity=MEDIUM
OLD<<<
(the file's four rows, sha256 5565de09fa595c059a260081a9c4ced4234f056faebee2bf69d50f8aa905287a, ending at line 4)
>>>
NEW<<<
(the four rows unchanged, then the three rows of out/ENGINE-CHANGES-trajectory-rows.hbp, sha256 08f70fda…: BRIDGE_ENGINE_CHANGE_RESULT for round 1 (source ea5d4ba8…), BRIDGE_ENGINE_REVIEW for round 1 (verdict PASS_WITH_HOLDS, receipt 18d633f5…), and BRIDGE_ENGINE_CHANGE_RESULT for round 2 (source c08a0c75…, receipt=BRIDGE-ENGINE-TRAJECTORY2.hbp_sha256=b3af77267a593aa2fedb442f81716a4609a0beab28a5845007316b813f64b820))
>>>
REASON: You decided that the build lane's H2 and the review's H15 go into ENGINE-CHANGES.hbp, in the form its quantum rows use. Every figure in the rows is read from a receipt whose sha256 the generator (tools/engine_changes.py) checks.

HOLD H4 | file=polariton-bridge/CORRECTIONS.hbp (new) | severity=LOW
OLD<<<
(file absent)
>>>
NEW<<<
BRIDGE_CORRECTIONS|beside=PREDICTION.hbp|PREDICTION.hbp_sha256=fadd84122e820cc03e9a4d6d5dd47fe7118ab4b16e1d4db93a601fb44c90b892|frozen_in=38ce24869f2c08cd4ffd346703c426f2276813e8|what=readings_of_frozen_lines_from_the_round-1_holds,each_frozen_text_a_byte_for_byte_substring_of_its_frozen_line,the_frozen_file_unchanged|json=0
BRIDGE_CORRECTION|id=trajectory-1|frozen_line=428|frozen_text=integration_trajectory=the_integer_Taylor_integrator's_printed_bound(order_28,h=1/32,2^-256_fixed_point)|reads_as=integration_trajectory=the_integer_Taylor_integrator's_printed_bound(order_28,h=1/32,2^-256_fixed_point;at_the_120_BRIDGE_AT_times_off_the_1/32_grid(odd_multiples_of_1/64)_the_read_takes_one_half_step_of_1/64_from_the_grid_point_below,its_bound_rows_printing_h=1/32,steps=j,half_step=1)|kind=ENGINE_DETAIL|values_moved=0(the_frozen_trajectory_values_are_closed_forms:traj_V2=(N-1)/N_exactly_in_298_of_352_BRIDGE_AT_rows_and_UNDEFINED_0/0_in_the_54_at_y=0,line_49_this_file=closed_forms_and_exact_series_only;the_integrator_reads_at_the_blind_points_come_after_the_operator's_word)|from=trajectory-build:H1(amended_by_trajectory-review:H8-H11)|tag=MEASURED|json=0
>>>
REASON: None of the 15 round-1 trajectory holds names PREDICTION.hbp as its file. H1's half-step read is the one change to how a frozen line reads (line 428, h=1/32). The frozen text occurs once, at byte 297. The header row is my proposal, and you merge the other engines' rows.

HOLD H5 | file=polariton-bridge/SHA256SUMS | severity=LOW
OLD<<<
5565de09fa595c059a260081a9c4ced4234f056faebee2bf69d50f8aa905287a ENGINE-CHANGES.hbp
>>>
NEW<<<
92b1ce0d01756870bc46aca45751b69a9948757df99ec6878a48efd05deb2acd ENGINE-CHANGES.hbp
69b4bf45de875f5e7e9490f7b4bb326a0d33b09a34760e2b50bdd7c2df16c4fe CORRECTIONS.hbp
>>>
REASON: The frozen job's stage_sums step reads this file, and it exits 0 locally with these lines. Rows from the other engines give both files new sha256 values again.

HOLD H6 | file=polariton-bridge/engines/trajectory/traj_int.py | severity=NOTE
OLD<<<
BAND_DELTA = Fr(1, 20)
BAND_Y = Fr(1, 81)
>>>
NEW<<<
BAND_DELTA = Fr(1, 1 << 128)
BAND_Y = Fr(1, 1 << 128)
>>>
REASON: Your text says "the bands the review proposes". The review's report proposes none; its tool refuses within 2^-128. The applied widths are the ensemble engine's, and they contain 2^-128 and also the float 2/27 (4.11e-18 from 2/27) and the decimal string (2.59e-17 from it). With 2^-128 the type check and the y list still refuse those two, as mutants G06 and G07 show. Taking NEW changes test_engine.py's expected check lists, gives the engine a new sha256, and reruns the gate.

HOLD H7 | file=polariton-bridge/CORRECTIONS.hbp | severity=NOTE
OLD<<<
(no row for line 446)
>>>
NEW<<<
BRIDGE_CORRECTION|id=trajectory-2|frozen_line=446|frozen_text=change=its_reserved-point_guard_lifted_after_this_file_is_pushed|reads_as=change=its_reserved-point_guard_kept_and_opened_after_this_file_is_pushed_by_the_literal_keyword_allow_reserved=True,at_delta=+-3/5_exactly_and_the_listed_y(the_blind_points);every_other_reserved_value_and_its_bands_refused_with_or_without_it|kind=LABEL|values_moved=0(a_reading_of_the_change_text;the_values_of_line_446_are_its_three_gate_sha256,which_reproduce_3_of_3)|from=trajectory2:H7(a_round-2_reading_for_the_seat)|tag=MEASURED|json=0
>>>
REASON: Line 446 says the guard is lifted, but the engine keeps it and opens it per call by the literal flag. This is my reading, from this round, not from a round-1 hold. The frozen text occurs once, at byte 87 of line 446. It's your call whether it belongs in CORRECTIONS.hbp.

HOLD H8 | file=the trajectory blind-run driver (round 1's H3, written after BRIDGE_ORDER step 4) | severity=NOTE
OLD<<<
            o = r.obs(N)                              # A1, C1, V2, f, D2 in the quantum read's normalisation
        print(r.bound_row())                          # BRIDGE_ERRORS integration_trajectory beside the read
>>>
NEW<<<
            o = r.obs(N)                              # A1, C1, V2, f, D2 in the quantum read's normalisation
            print(r.obs_bound_row(N))                 # A1, C1, f, D2 and the V2 identity bounds at this N
        print(r.bound_row())                          # BRIDGE_ERRORS integration_trajectory beside the read
>>>
REASON: C_NOISELESS reads the trajectory's A1, C1, f and D2 within the integration bounds, and T_V2_ID's run clause reads |V2·N/(N−1) − 1|. obs_bound_row(N) prints each bound at the read's own time and N. At y = 0 it prints V2_identity_err_le=undefined_X=0.

HOLD H9 | file=polariton-bridge/README.md | severity=NOTE
OLD<<<
- `design/controls/` FINDINGS.txt (sha256 `9755bb3a46f35eba28500750ebf2163d6c9d5de6c4b4c608b9fbd0b05b133b66`, 287 lines) and PROPOSED-ROWS.hbp (sha256 `9091896d690d0ccd8ac779137c5eec522665bc79ee930a6f704bf78c3a9430b5`, 33 rows), copied byte for byte from `C:/tmp/opus55/bridge-design-controls-20261105/`.
>>>
NEW<<<
- `design/controls/` FINDINGS.txt (sha256 `9755bb3a46f35eba28500750ebf2163d6c9d5de6c4b4c608b9fbd0b05b133b66`, 287 lines) and PROPOSED-ROWS.hbp (sha256 `9091896d690d0ccd8ac779137c5eec522665bc79ee930a6f704bf78c3a9430b5`, 33 rows), copied byte for byte from `C:/tmp/opus55/bridge-design-controls-20261105/`.
- [`CORRECTIONS.hbp`](CORRECTIONS.hbp): readings of frozen lines from the round-1 holds, each frozen_text a byte-for-byte substring of its frozen line; PREDICTION.hbp keeps its bytes.
- [`engines/trajectory/`](engines/trajectory/): the trajectory integrator (traj_int.py, sha256 `c08a0c75bf7d089875d2e6017b731bac767fb93fff849464f9af9d9849afb504`), its line-446 gate, tests, audit and float scan, with its README.md and SHA256SUMS; the workflow's `trajectory` job runs them.
>>>
REASON: The README's tables are your map. Changing the README gives README.md a new sha256 in SHA256SUMS (H5).
