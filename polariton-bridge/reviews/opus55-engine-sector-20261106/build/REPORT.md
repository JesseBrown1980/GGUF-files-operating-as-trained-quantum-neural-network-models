I built the Q = 0 sector mode into the quantum engine and it passes every gate I ran locally. Hosted CI and the second-seat review are still open. Every launch went through a reserved-point guard in code, and 0 reserved points were run. At most 2 of this lane's heavy processes ran at once; the longest single run was about 6 minutes. No push, no GitHub writes, float_used=0, LF endings throughout.

**What I did**
- Wrote the predictions first: `PREDICTION-Q0.hbp`, sha256 d30dd9dc555a9779e14153c51542c028f78fe09cbc95456a9f4f9a195966bb6c, 19:48Z.
- Built `sector` on the LF archive of e4fc6ba as a third layout inside `point`, so point, stream and sector share one READ-row printer. I wrote it from the LF source rather than from the Use lane's copy.
- Sector state: one state per even shell, (2j, j), for j = 0..K/2.
- Taken from the whole block, shell by shell, with no array of the block's size: c, E, the elements' rounding bound, norm(B), the tail norm's 1 per state, and the read's terms for the states at amplitude 0.
- It works at any K ≤ N, not only K = N. It refuses y ≠ 0 with exit 2 and no row.

**Results (all MEASURED unless tagged)**
- **R01 toolchain:** fmt `--check` 0, clippy `--release -D warnings` 0, the workflow's clippy form 0, build 0, no f32/f64 tokens.
  - New binary: 6bf8ebf2309700cb5be4cce25d82e5c4ee70fbc49521d4d7686cfc1649aa0a21.
  - ed75eca8 rebuilt here gave d892971d…, the filed binary, so the build does not depend on the path.
- **R02 point and stream unchanged:**
  - RECEIPT-DYADIC: point whole file equal, stream equal but array_bytes, off-grid time refused.
  - RECEIPT-BASELINE: 58 of 58 allowed rows byte-equal in point; stream equal but array_bytes, also at tile=depth=8 and 3.
  - RECEIPT-GRID: 20 of 20 rows, point whole file equal; stream equal but array_bytes.
  - CONTROLS.hbp: 4 of 4 sabotages fail as named.
  - At the sector points, the new point stdout equals the filed engine's.
- **R03 sector against point:** 17 of 17 READ rows at 10 allowed y = 0 points (N = 81, 243, 729, 2187, 6561; K = N, K < N, odd K = 63 and 127; includes N = 6561 at K = 6561 and K = 2039). Every field is equal but array_bytes, and all 8 checks pass.
  - With array_bytes set to even_states × 120, the sector output hashes to the Use lane's point stdout on 4 of 4: 0e41d2fe…, 24b630d0…, 610ac218…, and af455347… (the frozen y = 0 time list to 207/32 at N = 6561, delta = 1/2).
- **R04 array_bytes:** (min(K,N)/2 + 1) × 104 on every row; 341,224 at N = K = 6561.
- **R05 refusals:** y = 1/27, −1/27 and 1/108 give exit 2 with 0 stdout bytes. Exit 2 with 0 bytes also for: a point sabotage in sector mode, a sector sabotage in point or stream, an unknown argument, an off-grid time.
- **R06–R09 controls** (`CONTROLS-SECTOR.hbp`):
  - Real sector: 0 checks failed.
  - `drop_off_sector_couplings` fails the operator, observable, certificate and byte-equality checks. It is caught on 2 of 3 rows: at N = 81 full space, c goes −7 → 3 and E 35 → 25. At N = 729, K = 128 the row is unchanged. The control stage therefore needs a K = N point, and it has one.
  - `wrong_basis_order` fails observable, certificate and byte equality on 3 of 3 rows.
  - `run_at_nonzero_y` fails the same three checks on 3 of 3 rows; the sector reads A1 = 0 where point reads 0.0378 at N = 81, t = 1.
  - All three fail sets match the predictions.
- **R10 cost:** sector at N = K = 6561, delta = 1/2, frozen y = 0 list (414 windows): 13,501 ms at a 2,544 kB peak. Point at the same size: 41.2 s for one window and 89.6 to 104.3 s for two, at a 1,264,036 kB peak.
- **R11 independent replay:** a fresh tree at a second path with a fresh target gives the same binary sha256. Fmt, clippy and build pass; the bridge pin, both SHA256SUMS checks, the review sums and the 0-CR check pass. A separately written second driver matched 17 of 17 rows. The outputs are byte-equal to the first run.
- **R12 workflow step:** run locally it exits 0 (run_stage parallelism set to 2 here instead of 4). Hosted CI: CANNOT_SEE.
- **Verdict: PASS_WITH_HOLDS**, 12 of 12 predictions met.

**Lane files**
- Folder: C:/tmp/opus55/q0-sector-20261106/
- Index, records and seal: INDEX.hbi (158 artifacts, bytes, sha256 and a 16-hex SH each) 2ebfb63a…; SHA256SUMS 96fae977…; SEAL.hbp 570e1548…, seal value 6f7b32d5476f3f79141eff7937c7261e07958d2364a1d48ba832e51ec423a00b; seal verify PASS.
- RESULTS-Q0.hbp b4e5e4d42f0be6ee3bfe0e2aee31151b6498d3ed43a9683bd485fa52a955141f
- Scripts: run_jobs.py, guarded_stage.py, guard_check.py, replay_driver.py, seal.py, gate_*.sh.

**Proposed repo changes** (under proposed/, sha256)
- src/bin/polariton_first_correction.rs c3b9498b65bdfdffaab642dbd856e10909eae13fc340d7a81399a82460bb370a (diff engine-sector.diff a7201bed16abfa38f8f2b5d6562e5b988202fa0e586d80848bc5a7f693f5678f: 373 lines added, 10 changed)
- polariton-first-correction/check_sector.py 1cd3cb2e1a0f64afe577ae7ae25027e300ca7c9b34d21bee8bb8cac00a28382f
- polariton-first-correction/PLAN-SECTOR.hbp 1b3ac8ae590b5bd2b1f659384599310b908e9db033a4bd669bfe3622d3c5ff29
- polariton-first-correction/CONTROLS-SECTOR.hbp 979b7b4302ac5bcc3bf6c7a2c45ee35f8f18eb7077e09ca65373d566a1c3fb1d
- polariton-first-correction/RECEIPT-SECTOR.hbp 4c9060601598c317929c345ef75f7d97cc3a7b37840fac470055c8c607e8d2a7
- polariton-first-correction/RECEIPT-SECTOR-CONTROL.hbp f08cc80f217fd7e48c271a280fe3fffd0b41e3f249b0e91436a5a545f0b879c3
- polariton-first-correction/RECEIPT-SECTOR-CONTROL-Y.hbp f87947b98e0788cf3934256c8c10e335b4f28743f8cc82b06b80ef831a6abd76
- polariton-first-correction/SHA256SUMS 6d17c78f2c66edd7105d373a87f2f68650486cc2ac87b797c6a36eb60cc08b4b
- .github/workflows/polariton-first-correction.yml 1cc2090411ac791f7ce295d685485af1b15d3d97d8a3ea24ef865565f0c43852 (the added step alone: workflow-step-sector.yml 67b3a365533ed7902a9fc8f28b5ce8c960c0859f400ab583481702386a3fcb70)
- polariton-bridge/CORRECTIONS.hbp e9a126f637f6264834fb20fd4899ca70b2884a9c371975edd6825a14b9604ade
- polariton-bridge/ENGINE-CHANGES.hbp ec0ed55f62c2fa29b80b6ef163328a3f7555c994fdda7dfc1ae9eb549997ef09
- polariton-bridge/README.md 83bf080cf28d225c451577da6b5e3e356dddac74c081d343137764a844948e20
- polariton-bridge/SHA256SUMS d90a4d855f5abf7912d12acbc8037138d01ce2bce1706dbe96386d190696b779
- PLAN-BLIND-CHANGE.hbp 958784387c8572b3682316f4b1454d175e26f7f9afe7e42b6a215063c7ebdc1b

**For you to decide**

HOLD H1 | file=src/bin/polariton_first_correction.rs | severity=high
OLD<<<sha256 ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6>>>
NEW<<<sha256 c3b9498b65bdfdffaab642dbd856e10909eae13fc340d7a81399a82460bb370a (proposed/engine-sector.diff)>>>
REASON: decision (3), the sector mode; gate R01 to R12.

HOLD H2 | file=polariton-first-correction/{check_sector.py,PLAN-SECTOR.hbp,CONTROLS-SECTOR.hbp,RECEIPT-SECTOR.hbp,RECEIPT-SECTOR-CONTROL.hbp,RECEIPT-SECTOR-CONTROL-Y.hbp} | severity=medium
OLD<<<(absent)>>>
NEW<<<the six files, sha256 as listed above>>>
REASON: the checker, the plan, the filed point rows from the d892971d binary, and the controls' expected fail sets.

HOLD H3 | file=polariton-first-correction/SHA256SUMS | severity=medium
OLD<<<ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6 ../src/bin/polariton_first_correction.rs>>>
NEW<<<c3b9498b65bdfdffaab642dbd856e10909eae13fc340d7a81399a82460bb370a ../src/bin/polariton_first_correction.rs, plus six appended lines for the H2 files>>>
REASON: the workflow checks this file with `sha256sum --strict -c`.

HOLD H4 | file=.github/workflows/polariton-first-correction.yml | severity=medium
OLD<<<the file ends at the streaming step (sha256 86a79f9215ebe93263783f3d9ccd04e3b5d89ab0c8763ba44fcb85d39cfdd5fa)>>>
NEW<<<the step "The Q = 0 sector mode at y = 0 meets point mode in every field but array_bytes, each sabotage fails the checks CONTROLS-SECTOR.hbp names, and y != 0 is refused" appended (proposed/workflow-step-sector.yml)>>>
REASON: it compares point rows with the filed receipts, reads the sector rows with check_sector.py, runs each sabotage through run_stage and compares its FC_SECTOR_DONE line with CONTROLS-SECTOR.hbp, and checks that y = ±1/27 gives exit 2 with no row. It parses as YAML (14 steps).

HOLD H5 | file=polariton-bridge/CORRECTIONS.hbp | severity=high
OLD<<<|engines=ensemble(twens_0.3.0,src/main.rs_723b3674),trajectory(traj_int.py_c08a0c75)|>>>
NEW<<<|engines=ensemble(twens_0.3.0,src/main.rs_723b3674),trajectory(traj_int.py_c08a0c75),quantum(src/bin/polariton_first_correction.rs_c3b9498b)|>>>
OLD<<<BRIDGE_CORRECTIONS_END|rows=28|frozen_texts_verified=28_of_28(each_once_on_its_line)|json=0>>>
NEW<<<
BRIDGE_CORRECTION|id=quantum-sector-1|frozen_line=466|frozen_text=quantum=full_exchange_even_space_K=N|reads_as=quantum=full_exchange_even_space_K=N,run_on_its_Q=n+-n-=0_sector_by_the_quantum_engine's_sector_mode(at_y=0_H_keeps_Q,and_the_start_|N,0,0>_has_Q=0,so_the_full-space_state_holds_its_amplitude_on_the_3281_sector_states_(q,m)=(2j,j)_of_the_10768242_and_exactly_0_on_the_rest;launch_sector~6561~6561~3/5~0~6~1/2,1,2,141/32,77/16,163/32,11/2,185/32,99/16,207/32;its_READ_rows_carry_every_field_point_prints_at_K=N,with_array_bytes_its_own_layout's_341224_and_point's_1292189040_beside_it_in_the_COST_row;ENGINE-CHANGES.hbp,the_sector_layout's_row)|kind=ENGINE_LAYOUT|values_moved=0(the_quantum_rows_of_this_point_are_the_full_exchange-even_space's;the_352_BRIDGE_AT_rows'_closed_forms,counts_and_times_stand)|from=q0-sector-20261106|tag=MEASURED_at_allowed_points(17_of_17_READ_rows_at_10_points,N=81_to_6561;the_point_stdout_of_the_frozen_y=0_time_list_at_N=6561,delta=1/2);NAMED_at_this_point(blind,the_seat_runs_it_through_the_driver)|json=0
BRIDGE_CORRECTION|id=quantum-sector-2|frozen_line=480|frozen_text=quantum=energy_shell_block_K=2039_under_BRIDGE_QUANTUM_GATE_BLOCK,fallback_K=N|reads_as=quantum=energy_shell_block_K=2039_under_BRIDGE_QUANTUM_GATE_BLOCK,fallback_K=N(the_K_shell_runs_at_K=2039_and_K=2450_are_PLAN-BLIND_orders_29_and_30,point_mode;the_fallback_K=N,when_BRIDGE_QUANTUM_GATE_BLOCK_sends_this_point_there,runs_on_the_full_space's_Q=0_sector_by_the_quantum_engine's_sector_mode,launch_sector~6561~6561~-3/5~0~6~1/2,1,2,227/64,271/64,77/16,315/64,11/2,359/64,99/16,its_READ_rows_carrying_every_field_point_prints_at_K=N_with_array_bytes_its_own_layout's;at_a_block_K<N_the_sector_mode_prints_every_field_point_prints_at_that_K,array_bytes_its_own(N=6561,K=2039,delta=-1/2,y=0,t=1/64,1/8))|kind=ENGINE_LAYOUT|values_moved=0(the_route_of_this_point,its_gate_and_its_fallback_stand;the_352_BRIDGE_AT_rows'_closed_forms,counts_and_times_stand)|from=q0-sector-20261106|tag=MEASURED_at_allowed_points;NAMED_at_this_point|json=0
BRIDGE_CORRECTIONS_END|rows=30|frozen_texts_verified=30_of_30(each_once_on_its_line)|json=0
>>>
REASON: correction rows beside lines 466 and 480; the frozen file keeps sha256 fadd8412…; each frozen_text occurs once on its line, 30 of 30.

HOLD H6 | file=polariton-bridge/ENGINE-CHANGES.hbp | severity=high
OLD<<<(16 rows, ending at the trajectory final-stage BRIDGE_ENGINE_REVIEW)>>>
NEW<<<row 17 appended:
BRIDGE_ENGINE_CHANGE_RESULT|engine=the_quantum_engine_src/bin/polariton_first_correction.rs|change=the_Q=0_sector_layout_as_mode_sector(BRIDGE_ENGINE_CHANGE_line_451,a_memory-layout_change;the_operator's_decision_(3)_of_2026-11-06):at_y=0_H_keeps_Q=n+-n-_and_|N,0,0>_has_Q=0,so_the_run_keeps_the_K/2+1_states_(2j,j),each_row_summed_from_the_products_step_adds_there;c,E,the_elements'_rounding_bound,norm(B),the_tail's_1_per_state_and_the_read's_terms_of_the_states_at_amplitude_0_from_the_whole_block,shell_by_shell;y!=0_refused(exit_2,no_row)|from_sha256=ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6(the_streaming_engine)|source_sha256=c3b9498b65bdfdffaab642dbd856e10909eae13fc340d7a81399a82460bb370a|diff=373_lines_added,10_lines_changed(point's_layout_switch_at_the_operator,the_state_length,tail,leak,step_and_read,and_the_usage_message;the_streaming_code_as_filed)|binary_sha256=6bf8ebf2309700cb5be4cce25d82e5c4ee70fbc49521d4d7686cfc1649aa0a21(rustc_1.81.0,x86_64-unknown-linux-gnu;the_same_at_a_second_path_and_target;ed75eca8_built_here_gave_the_filed_d892971d)|gate=cargo_+1.81_fmt_--all_--_--check_exit_0,cargo_+1.81_clippy_--release_--_-D_warnings_exit_0,the_workflow's_clippy_form_exit_0,float_used=0(no_f32_or_f64_token)|RECEIPT-GRID.hbp=point_whole_file_bytes_equal(20_rows);stream_every_field_but_array_bytes|RECEIPT-BASELINE.hbp=58_of_64_rows_byte_for_byte_in_point,every_field_but_array_bytes_in_stream_and_at_tile=depth=8_and_3,6_rows_at_N=729,y=2/27_NOT_MEASURED(reason=RESERVED)|RECEIPT-DYADIC.hbp=point_whole_file_equal,stream_but_array_bytes,the_off-grid_time_refused|CONTROLS.hbp=4_of_4_sabotages_fail_as_named,the_real_run_passes|sector=17_of_17_READ_rows_at_10_allowed_y=0_points(N=81,243,729,2187,6561;K=N_and_K<N,odd_K=63,127_and_even;polariton-first-correction/RECEIPT-SECTOR.hbp)_every_field_but_array_bytes_equal_to_point;with_array_bytes_set_to_even_states*120,4_of_4_point_stdout_sha256_met(N=81,729_t=1,2,3;N=6561_t=1/64,1/16;N=6561_the_frozen_y=0_time_list_to_207/32;delta=1/2)|array_bytes=(min(K,N)/2+1)*104,341224_at_N=K=6561_beside_1292189040_in_the_COST_row|controls=CONTROLS-SECTOR.hbp:the_real_mode_0_checks_failed;drop_off_sector_couplings_4_failed(operator,observable,certificate,byte),caught_at_the_K=N_rows(c=-7->3,E=35->25_at_N=81)_and_equal_at_N=729,K=128;wrong_basis_order_3_failed(observable,certificate,byte)_on_3_of_3_rows;run_at_nonzero_y_3_failed_on_3_of_3_rows(A1=0_beside_point's)|refusals=y=1/27,-1/27,1/108_exit_2_with_0_bytes;a_point_sabotage_in_sector,a_sector_sabotage_in_point_and_in_stream,an_unknown_argument,an_off-grid_time_exit_2_with_0_bytes|cost=N=K=6561,delta=1/2,y=0,the_frozen_y=0_list_to_207/32(414_windows):13501_ms,peak_rss_2544_kB;point_N=K=6561,y=0:41184_to_41273_ms_for_one_window,89612_to_104303_ms_for_two,peak_rss_1264036_kB(two_runs_at_a_time)|replay=a_fresh_tree(e4fc6ba_plus_the_proposed_files)_at_a_second_path_and_target:the_same_binary_sha256,the_workflow_step_exit_0,a_second_driver_17_of_17_rows|review=OPEN(BRIDGE_ORDER_step_4,a_second-seat_review)|hosted_ci=OPEN(the_seat_pushes)|by=opus55,q0-sector-20261106|tag=MEASURED|json=0
>>>
REASON: the line-451 result row; review and hosted CI are left OPEN for you to fill.

HOLD H7 | file=polariton-bridge/README.md | severity=low
OLD<<<…at a peak of 1.04 GB against 1.29 GB per run. The hours above are at `point`'s rate.>>>
NEW<<<the same text, then the sector-layout paragraph (scripts/rows/readme-sector.txt)>>>
REASON: documents the mode beside the stream paragraph.

HOLD H8 | file=polariton-bridge/SHA256SUMS | severity=medium
OLD<<<2e1aba3b… README.md / b5fc5d6a… ENGINE-CHANGES.hbp / a4d6e101… CORRECTIONS.hbp>>>
NEW<<<83bf080c… README.md / ec0ed55f… ENGINE-CHANGES.hbp / e9a126f6… CORRECTIONS.hbp>>>
REASON: the bridge workflow checks these sums.

HOLD H9 | file=C:/tmp/opus55/bridge-blind-driver-20261106/PLAN-BLIND.hbp | severity=high
OLD<<<line 1: |quantum=d892971d6c0023534a2cbfac2631a7d983eeeab6853ffb6524b589e74795f270(source_ed75eca85a15bf592d4147db7ad196cc1ee3f4f11c491db7c356f68d02ea7ee6)|
line 411 (order 410): |binary_sha256=d892971d…|kind=full_K6561|…|argv=stream~6561~6561~3/5~0~6~1/2,1,2,141/32,77/16,163/32,11/2,185/32,99/16,207/32|>>>
NEW<<<line 1: |quantum=d892971d…(source_ed75eca8…),quantum_sector=6bf8ebf2309700cb5be4cce25d82e5c4ee70fbc49521d4d7686cfc1649aa0a21(source_c3b9498b65bdfdffaab642dbd856e10909eae13fc340d7a81399a82460bb370a,order_410)|
line 411: |binary_sha256=6bf8ebf2…|kind=full_K6561_sector_Q0|…|argv=sector~6561~6561~3/5~0~6~1/2,1,2,141/32,77/16,163/32,11/2,185/32,99/16,207/32|>>>
REASON: order 410 is the only y = 0 launch still unrun. Orders 6, 11, 15, 20, 29 and 30 are done according to the 28/28 checkpoint in your brief; I read only the plan file, so I cannot see that myself. Plan sha256 goes from a2f40acc… to bbd62f9b…, and PLAN-BLIND.hbp.sha256 needs re-sealing. Whether run_blind.py takes a binary per launch row is CANNOT_SEE; please check before running.

HOLD H10 | file=PLAN-BLIND.hbp | severity=medium (decision)
OLD<<<no fallback launch for line 480>>>
NEW<<<only if BRIDGE_QUANTUM_GATE_BLOCK fails at orders 29 and 30: a new launch Q-N6561_delta-3/5_y0-full with argv=sector~6561~6561~-3/5~0~6~1/2,1,2,227/64,271/64,77/16,315/64,11/2,359/64,99/16 and the new binary>>>
REASON: the frozen fallback K = N then costs seconds. This lane cannot see whether the gate passed.

HOLD H11 | file=(process) | severity=high
OLD<<<review and hosted CI open>>>
NEW<<<a second-seat review of c3b9498b (BRIDGE_ORDER step 4), then your push and the "First correction of the polariton test" job confirmed with gh pr checks, before order 410 runs>>>
REASON: decision (3) requires both.

HOLD H12 | file=polariton-bridge/CORRECTIONS.hbp (optional) | severity=low
OLD<<<line 439: runs=5_full_space>>>
NEW<<<an optional correction row: 4 full-space runs plus one sector run of seconds; optionally, sector beside-runs of the six done y = 0 quantum points through the driver>>>
REASON: budget text only; the beside-runs are at reserved points, so they are yours to order.