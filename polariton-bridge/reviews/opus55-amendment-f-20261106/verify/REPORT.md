**Verdict: PASS_WITH_HOLDS.** My own code recomputes every count, staircase and cost total in the amendment exactly. The holds below are about how the numbers are reported and about text. None of them changes a count.

**Method.** I wrote `vcore.py` from scratch. It holds closed forms for f, D2, A1, C1 and V2 (Gaussian quadratic-form variances) and evaluates them in certified exact-rational intervals, so every ceiling and every comparison is proven. It also has its own staircase and cost sums. It imports nothing from the generator, from `ix_core.py` or from the amendment lane. A separate comparison script checks my closed forms against `ix_core` on 150 values; they agree to about 1e-120 (MEASURED). Nothing was written to the worktree or to any earlier lane folder. No git writes, no model runs, float_used=0.

**Findings, by task item**
1. **Changed rows (DERIVED closed form; MEASURED by comparison).**
   - On the 70 first-order rows with y≠0, 4×M3_f is above the frozen M_VNC on 33 rows and at or below it on 37.
   - The 33 changed rows are the 33 the amendment lists: none missing, none extra, 0 field mismatches.
   - Fields checked on each: N, δ, y, s, t, M_VNC_frozen, M_VNC_amended, M3_f, 4xM3_f, frozen_requirement and set_by.
   - Each of the 33 is set by its own row's 4×M3_f; none is set by a later row.
   - The largest is L673: 5475421080 → 6330267356.
   - The frozen requirement rule is met on 83 of 83 first-order rows.
2. **Staircases (MEASURED).**
   - Rebuilt from the frozen counts, the frozen staircases equal the plan text (line 426) on 168 of 168 point-variant pairs.
   - The VNC staircase moves on 14 points, the 14 the amendment lists, with 0 mismatches in steps or exact work.
   - Nesting violations: 0. Every variant's count falls with t, M_V1 ≤ M_VNC, M_ins ≤ M_VNC, and each row's count is the step that covers its time, so each row reads on one prefix.
3. **Unchanged counts (MEASURED).**
   - M_VNC equals the frozen rows on 319 of 352.
   - M_V1, M_V0, M_FLIP, M_LOCK, M_MODE0 and M_eint are carried unchanged from the frozen rows (2112 counts), and M_ins=57182 on 352 of 352.
   - The V1, V0, FLIP, LOCK and MODE0 staircases equal the plan text on 28 points; the VNC staircase equals it on the other 14.
   - The BRIDGE_AT rows hold 11502 fields; 11502 − 33 = 11469. That the other fields do not depend on M_VNC is CONJECTURE: I did not rerun the generator's row writers.
   - The 16 diagnostic lines (354–356, 359–363, 366–368, 371–375) plus line 426 equal the amendment's list of 17.
4. **Expected reads at the amended counts (DERIVED; the 1.04 allowance is CONJECTURE).**
   - f at y≠0: bound inside τ on 70/70 and with an excursion on 70/70 (frozen 64 and 37). Expected NOT_RESOLVED: 0 rows (frozen 6).
   - D2 at y≠0: bound inside τ on 38/70 and with an excursion on 15/70 (frozen 35 and 15). Expected NOT_RESOLVED: 32 rows (frozen 35).
   - Other clauses: cv excursion 223/223, plain bound 137/223 and plain excursion 52/223 (frozen 123 and 47), E_VNC_ZERO f 13/13, floor 83/83.
   - The D_9_81 729-to-6561 rows have M_eff ≥ 1e9 on 80/80 at both the frozen and the amended counts (minimum 2.454e9; maximum 8.160e14 frozen, 4.432e15 amended).
   - E_PAIR, C_JFLIP, C_LOCK and the control verdicts read at counts equal to the frozen ones, so their reads equal the frozen reads (DERIVED).
5. **Cost (DERIVED, exact).** The amendment's cost row matches mine on all 9 fields.

| Part | Frozen | Amended |
|---|---|---|
| VNC | 22021873831/8 | 57591496603/16 |
| Primary | 73957089571/16 | 5469052407 |
| e_int (12 × 2^16 × Σt_max, Σt_max = 1159/8) | 113934336 | equal |
| Controls | 5025984959/16 | equal |
| **Total** | **40403011953/8 (5.0504e9)** | **94353772847/16 (5.8971e9)** |

   - Increment: 13547748941/16 (8.467e8).
   - Ratio: 94353772847/80806023906 = 1.1677 on the frozen plan, and 1.1696 on the E4R check's base. Both are within the authorized 1.17.
   - Hours (CONJECTURE, scaled from measured rates): 98.29 to 122.9 thread-hours; 15.96 h wall at 102631 vst/s against 13.67 h frozen, 2.292 h more.
6. **PREDICTION.hbp (MEASURED).** The worktree file, `git show 38ce248` and `git show HEAD` (2ab8143) all give sha256 fadd84122e820cc03e9a4d6d5dd47fe7118ab4b16e1d4db93a601fb44c90b892: 873 lines, 470395 bytes, no CR.
7. **README and amendment file (MEASURED).**
   - The amendment file is sha256 d69f9447…9192, 56 rows, LF only, no spaces.
   - Every README number matches mine: 33, 14, 319, 11469/11502, 16, 70/70, 38/15/32, 137 (52), 123 (47), 5.897e9, 5.469e9, 1.139e8, 3.141e8, 8.467e8, 1.168, 98.3 to 123, 16.0 h, 2.3 h.
   - The amendment lane's SHA256SUMS checks OK on all 11 files, and its gen/ copies match bridge-freeze-e4r-20261105.
   - Text-rule wording is in H3 and H4.

**Files** (all in C:/tmp/opus55/bridge-amend-f-verify-20261106/)
- vcore.py 5852f7e06f8a541da6ca0ed28612426237d206ed2ffb1069d5fae0be28cebd4c
- verify.py 2eb18f7e2b67eba1ce41122bc1f951e49d484901ead31a399a7cda6aa9b11c13
- meff.py 40dab1490c573d72bc16f86e0aa632da37e5218c6e022084809bfd8fdc6560a9
- xcheck_ixcore.py 54c68a93870ee938f14e21e6f2e3b08516cacd3e5d8f80a4e310db42ab2719db
- out/VERIFY.hbp c4f851a88f0452ac3c53f8fa2ccff644ba865001096a65a44e1c7c61a8f1b986 (has .sha256 sidecar)
- out/meff.hbp c1a313f9f28ef6915e0078ec0355666e48293c15e94e9bf13c13aead6e0733f7 (has .sha256 sidecar)
- out/xcheck_ixcore.hbp 71e1849c047c7e6135ded6af819cccdc32b2bb108eb760da389ec42cbb6280bf (has .sha256 sidecar)
- in/PREDICTION.hbp (copy) fadd84122e820cc03e9a4d6d5dd47fe7118ab4b16e1d4db93a601fb44c90b892
- in/AMENDMENT.hbp (copy) d69f944764cae0830ffc8d94eb922778d4f289b79470fa38333846a95be89192
- in/README-AMENDMENT.md (copy) ca941e2e30409117bf12968e0a64d7ffaf9bfeafe7114a897bf909b56efef35b
- SHA256SUMS (folder, one-space format)

HOLD H1 | file=reply to the operator / PR #15 text | severity=MEDIUM
OLD<<<
Compute units 5.050B → 5.840B; Estimated wall time 13.7 h → 15.8 h; Additional compute Approximately 2.1 h
>>>
NEW<<<
Compute units 5.0504e9 → 5.8971e9 vst (x1.1677, inside the authorized 1.17); estimated wall time 13.67 h → 15.96 h at 102631 vst/s; additional 8.467e8 vst, about 2.29 h (CONJECTURE, scaled from measured rates)
>>>
REASON: I recomputed this independently and endorse the amendment lane's H1. The relayed table's 5.840e9 and 15.8 h are the E4R check's option-f figures (IX_SIZE_FD 5.8401e9, 15.81 h). That check's base leaves out H4's control e_int. Exactly 56967168 vst separates the two totals, which is that term (3×2×2^16×1159/8), and it is already in the frozen 5.0504e9. The approved increment is 13547748941/16 on both bases. The table is the operator's authorization text, so the seat should send him the frozen-plan figures before the blind run. Then the 15.96 h projection is the one checked against the run.

HOLD H2 | file=C:/tmp/opus55/bridge-amend-f-20261106/AMENDMENT-2026-11-06-F-SAMPLING.hbp (new row after BRIDGE_AMENDED_TEXT) | severity=LOW
OLD<<<
BRIDGE_AMENDED_TEXT|lines_outside_BRIDGE_AT_that_print_a_moved_count=17|...
>>>
NEW<<<
(add) BRIDGE_AMENDED_SUMMARY_TEXT|lines_that_print_a_frozen-plan_figure=6|line_181:E_VNC(f,D2_bound_inside_tau_64,35;excursion_37,15;NOT_RESOLVED_6_f,35_D2)->70,38;70,15;0_f,32_D2|line_425:BRIDGE_SAMPLING_cost_estimate=5.050e9->5.897e9|line_426:BRIDGE_SAMPLE_PLAN_cost_at_these_counts=5.050e9->5.897e9|line_427:BRIDGE_CHECK(plain_bound_123,47;E_VNC_f_and_D2_64,35,37,15)->137,52;70,38,70,15|line_836:cost_5.050e9->5.897e9|line_872:BRIDGE_OPEN_O20(5.840e9,1.170x,97.3_to_122_thread-hours)->decided_2026-11-06,APPROVED,5.897e9_on_the_frozen_plan|reading=for_the_blind_run_these_figures_read_at_this_file's_amended_counts;PREDICTION.hbp_keeps_its_frozen_text|tag=MEASURED_by_comparison|json=0
>>>
REASON: The 17 listed lines are the ones that print a moved count. Six more frozen lines print figures that follow from the counts, which the amendment now replaces: lines 181, 425, 426 (its cost_at_these_counts field), 427, 836 and 872 (MEASURED by grep, values checked against VERIFY.hbp). The figures appear in the amendment's READ and COST rows, but no row maps them to these lines. One row tells the final reviewer and the driver which frozen statements read at the amended counts, and it records that the operator's decision settles O20.

HOLD H3 | file=AMENDMENT-2026-11-06-F-SAMPLING.hbp (BRIDGE_AMENDMENT row) and README-AMENDMENT.md (first paragraph) | severity=NOTE
OLD<<<
D2=the_original_rule:read_plain_at_the_row's_M_VNC,no_D2_sizing   /   at 1.17 times the E4R cost, with no further compute increase.
>>>
NEW<<<
D2=the_original_rule:read_plain_at_the_row's_M_VNC,D2_at_the_original_sampling_level   /   at 1.17 times the E4R cost, the full increase the operator authorized.
>>>
REASON: The operator's text rule asks for statements of what a thing is. These two phrases say what is not done. The positive forms carry the same scope: D2 stays at the original sampling level, and 1.17x is the authorized ceiling. The operator's own quote, "no further compute increase authorized", can stay as a quote in the decision field.

HOLD H4 | file=README-AMENDMENT.md (first paragraph) | severity=NOTE
OLD<<<
at 1.17 times the E4R cost
>>>
NEW<<<
at 1.168 times the E4R cost (94353772847/80806023906; the operator authorized 1.17)
>>>
REASON: The opening paragraph gives the authorized figure 1.17. The cost bullet gives the computed 1.1677, which rounds to 1.168. Putting both in the first sentence makes the paragraph match the cost bullet and shows that the amended plan fits within what was authorized (DERIVED, exact).

HOLD H5 | file=the blind-run driver and pin workflow (bridge branch 4eaad01, 2ab8143) | severity=MEDIUM
OLD<<<
the run takes M_VNC and the VNC steps from PREDICTION.hbp
>>>
NEW<<<
the run takes M_VNC and the VNC steps from AMENDMENT-2026-11-06-F-SAMPLING.hbp on its 33 rows / 14 points and from PREDICTION.hbp elsewhere; confirmed in the driver and the pin workflow before the hosted checks
>>>
REASON: I endorse the amendment lane's H4. I did not read the driver or the workflow at 2ab8143 either (CANNOT_SEE). The 14 amended VNC staircases verified here take effect only if the run reads them. The operator's order also requires the final hosted checks to pass before any blind measurement starts.
