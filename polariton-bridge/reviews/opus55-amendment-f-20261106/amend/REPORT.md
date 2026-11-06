Amendment written. The copied generator, run unchanged, reproduces PREDICTION.hbp byte for byte. The amended plan raises M_VNC on 33 rows, the same 33 the E4R check found, and adds 8.467e8 vst, which equals that check's increment. Nothing was written to C:/tmp/qnn-bridge-wt or any earlier lane folder, no model was run, no git writes, float_used=0.

**What I did**
- **Reproduction (MEASURED):** copied the generator to `gen/` and confirmed every file is byte-identical to bridge-freeze-e4r-20261105 (build_prediction.py c0e271d4, e4r.py 61ef91bc, check_f_d2.py 09ca64b7, core.py e422bcee). `repro.py` runs it as a module with no source change and two runtime pins:
  - NOTES points to the copy, so no earlier folder is written.
  - `git_head` returns the recorded base `bde1035`, because the worktree has moved on to `2ab8143`.
  - Result: `identical=1`, 470395 bytes, sha256 fadd8412…b892, 873 lines (`out/repro_run.txt`).
- **Amendment mode (DERIVED):** `e4r_amend.point_plan_amended` is e4r.point_plan with one change. On each first-order row with y≠0, the VNC requirement becomes max(frozen requirement, 4×M3_f). M3_f = ceil(9·var(n)/(E[n]−1)²·1.04²/τ²), from `check_f_d2.moments`.
  - With no extension it equals e4r.point_plan and the generator's own plan on 28 of 28 points (falsifier).
  - The frozen totals are reproduced exactly: 40403011953/8.
- **Shadow comparison (MEASURED):** the generator's own row writers were rerun in memory with the amended counts and compared field by field with every frozen line. A control rerun with the frozen counts matched 873 of 873 lines. Two module-level text counters (ABS_CONVERTED, SPACE_CONVERTED) had to be reset first: a second run in one process extends them and line 846 (FC14) drifts.

**Counts and checks**
- **Rows moved:** M_VNC on 33 rows across 14 points' VNC staircases. Each row is set by its own 4×M3_f. Largest: L673, N81 δ−3/5 y2/27 t1/16, 5475421080 → 6330267356.
- **Counts that stay:**
  - M_VNC equals the frozen rows on 319 of 352.
  - M_V1, M_V0, M_FLIP, M_LOCK, M_MODE0, M_eint equal on 352 rows (2112 counts); M_ins=57182 on all rows.
  - V1, V0, FLIP, LOCK, MODE0 staircases equal on 28 of 28 points.
  - Of 11502 fields in the 352 BRIDGE_AT rows, 11469 equal the frozen rows; the 33 others are the moved M_VNC values.
- **Moved counts printed outside BRIDGE_AT:** 16 BRIDGE_DIAGNOSTIC precision fields (lines 354–356, 359–363, 366–368, 371–375) and the BRIDGE_SAMPLE_PLAN steps of the 14 points (line 426).
- **f at y≠0:** bound inside τ on 70 of 70, with a 3-SE excursion on 70 of 70 (frozen 64 and 37). NOT_RESOLVED expected on 0 rows (frozen 6).
- **D2 at y≠0 (original rule):** bound inside τ on 38 of 70, with an excursion on 15 (frozen 35 and 15). NOT_RESOLVED expected on 32 rows (frozen 35).
- **Other sized checks:** E_VNC with the control variate 223/223, plain floor 83/83, E_VNC_ZERO f 13/13, E_PAIR 83/83, D_9_81 V1 14/14, C_JFLIP 156/156, C_LOCK 57/57, control verdicts 352/352 — all equal to the frozen figures. The plain bound of A1, C1, V2 now fits 137/223, 52 with an excursion (frozen 123 and 47).
- **Cost, in vst:**

| Part | Frozen | Amended |
|---|---|---|
| Primary | 73957089571/16 (4.622e9) | 5469052407 (5.469e9) |
| e_int | 113934336 (1.139e8) | equal |
| Controls | 5025984959/16 (3.141e8) | equal |
| VNC alone | 2.75273e9 | 3.59947e9 |
| **Total** | 40403011953/8 (5.0504e9) | 94353772847/16 (5.8971e9) |

  - Increment: 13547748941/16 (8.467e8); ratio 1.168.
  - Thread-hours: 98.29 to 122.9 (frozen 84.17 to 105.2).
  - At 102631 vst/s: 15.96 h (frozen 13.67 h), 2.292 h more (CONJECTURE, scaled from measured rates).
- **Cross-check with the E4R check's own forms (MEASURED):**
  - `rows_raised` 33 = 33, and the same rows.
  - 4×M3_f equals its `ix_core.LO.relf2` values on 70 of 70.
  - Its `stair_work` reproduces both VNC works exactly.
  - Its increment 5.8401e9 − 4.9934e9 = 8.467e8 equals mine.
  - The two totals differ only by base: its 5.8401e9 sits on a base without H4's control e_int (5.6967e7), so both sides are right.

**Files** (all in C:/tmp/opus55/bridge-amend-f-20261106/)
- AMENDMENT-2026-11-06-F-SAMPLING.hbp (56 rows, 18645 B, LF, no spaces): d69f944764cae0830ffc8d94eb922778d4f289b79470fa38333846a95be89192; sidecar AMENDMENT-2026-11-06-F-SAMPLING.hbp.sha256
- README-AMENDMENT.md: ca941e2e30409117bf12968e0a64d7ffaf9bfeafe7114a897bf909b56efef35b
- The SHA256SUMS line for the stage: `d69f944764cae0830ffc8d94eb922778d4f289b79470fa38333846a95be89192 AMENDMENT-2026-11-06-F-SAMPLING.hbp`
- amend.py: f8063000e111d62f3b59af1fb45f8c20910268f388cf69134636899f4e8fe4ac
- amend_compute.py: 10f2e6a5235d88a8b37c0e5c1806afc0a4df976db8d6be9753392e353ee02872
- e4r_amend.py: 522429292a5167ff8079be173a548287f1a49f4afc62b85e698ad70609d88700
- repro.py: 82164022a1370f96bdfe5f1023d7128654ca0b58ef5e0fa73ff463cb6d704b49
- out/repro_run.txt: 8bdeae65dc8e2f8becf40c3776160d56b808e502baf70635f8173101569e62ff
- SHA256SUMS (folder, one-space format); gen/ (byte-identical copies of the generator, plus issue9-comment-ids.hbp and issue9-meta.hbp)

HOLD H1 | file=reply to the operator / PR #15 text | severity=MEDIUM
OLD<<<
Compute units 5.050B → 5.840B; Estimated wall time 13.7 h → 15.8 h; Additional compute Approximately 2.1 h
>>>
NEW<<<
Compute units 5.0504e9 → 5.8971e9 vst (x1.168); estimated wall time 13.67 h → 15.96 h at 102631 vst/s; additional 8.467e8 vst, about 2.29 h (CONJECTURE, scaled from measured rates)
>>>
REASON: The relayed table took the E4R check's 5.840e9, which sits on a base without H4's control e_int (5.697e7 vst). That term is already in the frozen plan (5.0504e9). The f increment is the same 8.467e8 on both bases (MEASURED, exact), and the ratio is 1.168 on the frozen plan or 1.170 on the check's base, so both are inside the authorized 1.17x. No compute is added beyond the approved increment. The seat should report the figures for the plan as frozen, so the 15.96 h projection is the one checked against the run.

HOLD H2 | file=C:/tmp/qnn-bridge-wt/polariton-bridge/README.md (Sampling, f/D2 bullet and Cost bullet) | severity=LOW
OLD<<<
- Cost: 5.050 x 10^9 variant-sample time units, 84.2 to 105 thread-hours at the ensemble lane's measured rate, about
  13.7 hours at the machine's measured floor of 102631 per second, two 3-thread processes together (CONJECTURE, scaled from
  measured rates; a dedicated 8-thread rate OPEN).
>>>
NEW<<<
- Cost: 5.050 x 10^9 variant-sample time units, 84.2 to 105 thread-hours at the ensemble lane's measured rate, about
  13.7 hours at the machine's measured floor of 102631 per second, two 3-thread processes together (CONJECTURE, scaled from
  measured rates; a dedicated 8-thread rate OPEN). The sampling amendment of November 6, 2026 (below) sets 5.897 x 10^9.
>>>
REASON: The README's Sampling section describes the frozen plan: 64/35 fits, 6/35 NOT_RESOLVED, and 5.050e9. With README-AMENDMENT.md's section inserted after it, one pointer sentence on the cost bullet (and the same on the f/D2 bullet if the seat wants it) tells a reader which counts the blind run uses. PREDICTION.hbp stays byte for byte. The amendment file and its SHA256SUMS line go into polariton-bridge/ through the seat's normal commit.

HOLD H3 | file=AMENDMENT-2026-11-06-F-SAMPLING.hbp (BRIDGE_AMENDED_READ clause=E_VNC_D2_at_y!=0) | severity=NOTE
OLD<<<
D2 bound inside tau 35 of 70 (frozen)
>>>
NEW<<<
D2 bound inside tau 38 of 70 at the amended counts, 15 of 70 with an excursion, 32 NOT_RESOLVED expected; D2 rule unchanged
>>>
REASON: D2 is read plain on the same VNC samples, so the higher f counts happen to put 3 more D2 rows' bounds inside τ. That is a by-product; no D2 sizing was done. As the operator said, D2 precision stays at the original sampling level. The seat should keep all 32 expected NOT_RESOLVED D2 rows visible and should not describe D2 as sized.

HOLD H4 | file=the blind-run driver (engine commits 4eaad01, 2ab8143 on the bridge branch) | severity=MEDIUM
OLD<<<
the run takes M_VNC and the VNC steps from PREDICTION.hbp (BRIDGE_AT, BRIDGE_SAMPLE_PLAN)
>>>
NEW<<<
the run takes M_VNC and the VNC steps from AMENDMENT-2026-11-06-F-SAMPLING.hbp on the 33 rows / 14 points it lists, and from PREDICTION.hbp everywhere else; the 16 BRIDGE_DIAGNOSTIC precision fields read at the amended counts
>>>
REASON: The frozen file still prints the old counts on 33 BRIDGE_AT rows, 16 diagnostic lines and the plan's 14 VNC staircases. Any driver or pin workflow that reads counts only from PREDICTION.hbp runs the frozen counts, and the amendment does not take effect. I have not read those engine commits or the workflow at 2ab8143 (CANNOT_SEE). Before the hosted checks and the baseline-first blind order, the seat should confirm the driver reads the amendment and that the pin workflow accepts a new file beside the pinned one.

HOLD H5 | file=C:/tmp/opus55/bridge-amend-f-20261106/repro.py | severity=NOTE
OLD<<<
the generator, run unchanged, reproduces PREDICTION.hbp
>>>
NEW<<<
the generator, run unchanged as a module with two runtime pins (NOTES = the copy; git_head = bde1035, the base the file records, while the worktree is at 2ab8143), reproduces PREDICTION.hbp byte for byte
>>>
REASON: build() asserts HEAD == bde1035 and writes its preview into NOTES. Running the script directly would fail on the moved worktree and would write into the read-only freeze folder. The pins change no source byte, and the sha256 values the file prints are the same. A later reproducer, such as the independent final review, needs the same two pins, and also needs ABS_CONVERTED and SPACE_CONVERTED reset if the generator runs twice in one process.
