**Verdict: PASS_WITH_HOLDS.** The sector engine c3b9498b matches point mode on every printed field except array_bytes, at every allowed point I ran, and its internal integers match too. The holds are text and pin fixes, one optional CI step, and the open hosted CI. Reserved points run: 0, and every launch went through `scripts/guard.py` first. At most 2 heavy processes ran at once; the longest single run was 79 s. No push, no GitHub writes, float_used=0, 0 CR bytes.

**What I did**
- I wrote my predictions before any code or run:
  - PREDICTION-REVIEW.hbp 16eb985c… (21:50Z)
  - PREDICTION-REVIEW-ADDED.hbp 6f2e7b0d… (22:02Z, before the faults)
  - PREDICTION-REVIEW-ADDED2.hbp 75afaf54… (22:18Z, before the harness)
- I rebuilt both engines from an LF archive of e4fc6ba and reran the lane's workflow step.
- I ran my own points, planted 16 faults, and wrote an instrumented harness that compares internal integers.
- I recomputed the lane's chain and seal, and checked the proposed text against the frozen file.

**Results (all MEASURED unless tagged)**
- **V01 Rebuild** (third path, third target):
  - fmt, clippy `--release -D warnings`, the workflow's clippy form and build all exit 0; no f32/f64 tokens.
  - The new binary is 6bf8ebf2…, the same as the lane's; ed75eca8 rebuilt gives d892971d.
- **V02 The diff:**
  - `patch` of engine-sector.diff on the LF base gives c3b9498b: 373 lines added, 10 changed.
  - New point stdout is byte-equal to d892971d's at 63 of 63 points.
  - RECEIPT-DYADIC reproduces as a whole file, and the off-grid time gives exit 2 with 0 bytes.
  - Stream equals point in every field but array_bytes at 2 of 2 points.
- **V03 Workflow step, run locally at parallelism 2:** exit 0, 209 s, peak 1,263,764 kB.
  - It reproduces the lane's outputs byte for byte: sector.hbp e133c14e, sector-point.hbp 4c906060 (equal to RECEIPT-SECTOR), real-sector.hbp d09cd050.
  - All 3 sabotage fail sets match CONTROLS-SECTOR. c goes −7→3 and E 35→25 at N=81; A1 reads 0 where point reads 37757806429640237e-18.
- **V04 My own points:** 63 points, 121 READ rows, check_sector passes 63/63.
  - 58 are seeded small points: N=2..500, including K=0, K=1, K>N, and y written as 0/7 and −0.
  - 5 are large: N=2187/K=2187, 729/727, and 6561 at K=1001, 4000 and 6560.
  - array_bytes = (min(K,N)/2+1)×104 on all 63; a second run of the 63 sector outputs is byte-equal.
  - All 4 Use-lane hashes reproduce. **Three of them (0e41d2fe, 24b630d0, 610ac218) are point stdout. af455347 is the stdout of the Use lane's separately written sector program (B3, "sector_mode_alone").** Point at that time list was never run; the Use lane projected it at 4.28 h.
  - Sector at the frozen y=0 time list (N=6561, delta=1/2) took 15,812 ms at 2,544 kB.
- **V05 Planted faults** (15 in the engine, 1 in the checker), in `faults/ALL-GATES.hbp`:

| Fault | Workflow step | Caught by | My 63 points |
|---|---|---|---|
| F01 tail key j for 2j | caught | certificate (9/17 rows) | 30/63 |
| F02 leak reads re[mi−1] | caught | certificate | 46/63 |
| F03 read key j(j+1) | caught | observable | 61/63 |
| F04a tail count of Q≠0 states dropped | caught | certificate | 45/63 |
| F04b tail count off by one | **passed** | — | 2/63 |
| F05 read terms on shell K dropped | **passed** | — | 1/63 |
| F06 read weight wraps through u64/i64 | caught | certificate | 45/63 |
| F07 step product wraps in i64 | caught | observable + certificate | 61/63 |
| F08 leak gives a Q=1 state a sector amplitude | caught | certificate | 47/63 |
| F09 refusal only for y>0 | caught | y=−1/27 check | 0/63 |
| F10 refusal after the rows | caught | no-row check | 0/63 |
| F11 valid K<N refused | caught | run_stage exits 1 | 54/63 |
| F12 Gershgorin ring key | **passed** | — | 4/63 |
| F13 rounding bound from sector only | **passed** | — | 0/63 (no change seen) |
| F14 checker without its certificate group | caught | sabotage fail sets | — |
| F16 start placed at j=1 | caught | observable + certificate | 63/63 |

  - The workflow step catches 12 of 16.
  - My predictions missed on F05 (I predicted the step would catch it). F01 was caught on 9 of 17 rows, not every row.
- **V10 Instrumented harness** (my test copy only):
  - It compares, inside the program, every Gershgorin sum, c, E, the rounding bound, d and pair, read's 9 fields and 5 raw sums, the tail and leak totals, and step's rows.
  - Real code: 74 points, 20,826 checks, 0 fails. That includes N=K=6561, where all 10,768,242 sums are equal.
  - It catches the faults the step passes, out of 58 points: F05 57, F12 56, F04b 56 of 56 when the reach starts at 1. It catches F06 on 0 (my random vectors never put half the weight on one state; the step catches F06). F13 shows no change at any point I ran; the filed code takes the bound from every state (DERIVED from reading the code).
- **V06 The lane's chain**, recomputed by my own script:
  - 158 of 158 index rows and 158 of 158 SHA256SUMS lines equal, 0 unindexed files, 0 files newer than the seal.
  - The seal 6f7b32d5… recomputes exactly: PASS.
- **V07 Text against the frozen file:**
  - PREDICTION.hbp is fadd8412… (873 lines, 0 CR) and no proposed file changes it.
  - The texts on lines 466 and 480 each occur once on their line; 30 of 30 correction texts occur once on their lines.
  - The diffs are exactly the rows the lane named.
  - **Three places call af455347 a point stdout** (R1 below).
- **V08 Sums and plan change:**
  - Both proposed SHA256SUMS files pass `sha256sum --strict -c`.
  - The plan change applied to a copy turns a2f40acc into bbd62f9b, changing lines 1 and 411. The time lists match orders 410 and 29/30.
  - **The new plan head still pins CORRECTIONS a4d6e101 and ENGINE-CHANGES b5fc5d6a**, the e4fc6ba versions that H5 and H6 replace.

**My files** (C:/tmp/opus55/review-sector-20261106/)
- Records and seal:
  - RESULTS-REVIEW.hbp 5a1610d37a47b537d0a5fb44ae4e237e5ac4018c7f55358b0c90fa68daf011d1
  - INDEX.hbi b281d7f33e4b8adb86bc5aba18a192026653945abb99c55d06e7c382144ad6e5 (4,588 artifacts)
  - SHA256SUMS 37b044b90664ba65dfe51d3441acefae6a0c74bb1958b02d40763fafb4fdc489
  - SEAL.hbp e09ed171137ef05cdfbbdb27910d9767f0eeaf41df135f08a579fd6aafdb0316, seal value befc6a3c61f8a1fd49715f73b85143b2cdcf6240f92e0cd34bf9f55eb301ff1e (verify PASS)
- Result rows:
  - faults/ALL-GATES.hbp ed3eab0f…
  - harness/FAULTS-HARNESS.hbp 2450712c…
  - harness/REAL.hbp 7953ea81…
  - out/CHAIN-BUILD-LANE.hbp b9ef763a…
  - out/CORRECTIONS-CHECK.hbp ff2fe927…
  - out/plan/PLAN-CHECK.hbp 165fe850…
  - out/use-ref/USE-REF.hbp 57681b0c…
- Scripts: guard.py b08d13c7…, instrument.py c37b11d2…, fault_gate.py b12fce05…, faults.py 5e750f18…, verify_chain.py 82214532…, check_corrections.py 8b57f184…, fix_text.py 80490250…, seal.py 67ec8c41…

**For you to decide**

I support the lane's H1–H4, H10 and H12 as written. H5–H9 should go in with my R1 and R2 changes. H11 stays open.

HOLD R1a | file=polariton-bridge/CORRECTIONS.hbp (row quantum-sector-1) | severity=medium
OLD<<<tag=MEASURED_at_allowed_points(17_of_17_READ_rows_at_10_points,N=81_to_6561;the_point_stdout_of_the_frozen_y=0_time_list_at_N=6561,delta=1/2);>>>
NEW<<<tag=MEASURED_at_allowed_points(17_of_17_READ_rows_at_10_points,N=81_to_6561;the_point_stdout_at_N=81,729_t=1,2,3_and_N=6561_t=1/64,1/16;at_the_frozen_y=0_time_list,N=6561,delta=1/2,the_stdout_af455347_of_the_Use_lane's_separately_written_sector_implementation,byte_for_byte);>>>
REASON: af455347 is mle-use-20261106 B3, which ran sector only. The file goes from e9a126f6 to 9bfdd27d9b418cb71835a870e527f8e4c83f412aab8bd148c56539af597e9e99 (proposed-fix/polariton-bridge/CORRECTIONS.hbp); 30 of 30 texts are still once on their lines.

HOLD R1b | file=polariton-bridge/ENGINE-CHANGES.hbp (row 17) | severity=medium
OLD<<<with_array_bytes_set_to_even_states*120,4_of_4_point_stdout_sha256_met(N=81,729_t=1,2,3;N=6561_t=1/64,1/16;N=6561_the_frozen_y=0_time_list_to_207/32;delta=1/2)>>>
NEW<<<with_array_bytes_set_to_even_states*120,3_of_3_point_stdout_sha256_met(N=81,729_t=1,2,3;N=6561_t=1/64,1/16;delta=1/2),and_at_the_frozen_y=0_time_list_to_207/32(N=6561,delta=1/2)_the_stdout_sha256_af455347_of_the_Use_lane's_separately_written_sector_implementation(mle-use-20261106_B3;point_at_that_length_projected_at_4.28_h_there)>>>
REASON: the same fact. The file becomes c3a5e90f7f2b4e2fa53981a1ef51e6868a8b49cca38967109115a8411bcf7633.

HOLD R1c | file=polariton-bridge/README.md (lines 268–269) | severity=low
OLD<<<(`polariton-first-correction/RECEIPT-SECTOR.hbp`), and the point output of the frozen y = 0 time list to t = 207/32 at
N = 6561, delta = 1/2, byte for byte, MEASURED. That run took 13.5 s>>>
NEW<<<(`polariton-first-correction/RECEIPT-SECTOR.hbp`), and, at the frozen y = 0 time list to t = 207/32 (N = 6561,
delta = 1/2), the output of a separately written sector implementation (the Use lane's), byte for byte, MEASURED;
`point` at that length is projected at about 4.3 h on this machine. The sector run took 13.5 s>>>
REASON: the same fact. The file becomes 1537fe421177159c138fb00ea64f7fce773d9af11763f3c786aab81059881883.

HOLD R1d | file=polariton-bridge/SHA256SUMS | severity=medium
OLD<<<d90a4d855f5abf7912d12acbc8037138d01ce2bce1706dbe96386d190696b779 (the lane's H8 NEW)>>>
NEW<<<b5f248eb69c9c5a4cc08cb9151fa0a7e614742d9c4a72a4ef207a2d9844e1132 (proposed-fix/polariton-bridge/SHA256SUMS)>>>
REASON: it follows R1a–c. On the fixed tree the frozen pin, the bridge sums, the review sums and the 0-CR check all pass.

HOLD R2 | file=PLAN-BLIND.hbp head (the H9 change) | severity=medium
OLD<<<CORRECTIONS_sha256=a4d6e10180e6ce39b3afbc2881ad620ecaee5d790d7add5b9d21d760dc93ca22|ENGINE-CHANGES_sha256=b5fc5d6ab581bc9f23e80dad68b8be1e8cddd41e9ef877f168886d8b191b8bc1|>>>
NEW<<<CORRECTIONS_sha256=9bfdd27d9b418cb71835a870e527f8e4c83f412aab8bd148c56539af597e9e99|ENGINE-CHANGES_sha256=c3a5e90f7f2b4e2fa53981a1ef51e6868a8b49cca38967109115a8411bcf7633|>>>
REASON: the plan head would otherwise pin files that H5 and H6 replace. My change file is proposed-fix/PLAN-BLIND-CHANGE.hbp ed9b4dd48ecd9d3724afcd91a40ea73dbdfdd298013cfb62e697362081f0a6ed, and the plan after it is a14d9c8779da5f79392fa4c0df91d7d716a54dd9843c9ec42a239a7b50240295 instead of bbd62f9b. If you decline R1, use e9a126f6/ec0ed55f instead. Whether run_blind.py reads these pins is CANNOT_SEE (I read only the plan file). PLAN-BLIND.hbp.sha256 needs re-sealing either way.

HOLD R3 | file=polariton-first-correction/sector_harness.py + workflow step (optional) | severity=medium (decision)
OLD<<<(absent)>>>
NEW<<<proposed-harness/polariton-first-correction/sector_harness.py ff5938d8976c3e1725f7917fa71c83e62630142b91640151bc2740e2cb9b49f3; step proposed-harness/workflow-step-harness.yml 21950efedb2e233af07620a6803eb0850677ed6b9356b15d3df485bf494a1a34; with it, polariton-first-correction/SHA256SUMS fc4f311326ac298e37b12815b632102fe2496ab307a90daf2dbf027fd0137bd4 (instead of 6d17c78f) and .github/workflows/polariton-first-correction.yml 954b19b7f08773fe98987f1ce994db6f33f7846ffeb42342f5b55bafaefed559 (15 steps)>>>
REASON: the lane's step passes F04b, F05 and F12, faults whose effect on the printed fields is too small to show at its points. The harness catches them at 56–58 of 58 points, passes 10 of 10 on the real code, and took 90 s and 1.1 GB here. The engine itself does not change. It needs its own second-seat check.

HOLD R4 | file=(process) | severity=high
OLD<<<review OPEN, hosted CI OPEN>>>
NEW<<<record this review (PASS_WITH_HOLDS for c3b9498b, binary 6bf8ebf2) in ENGINE-CHANGES row 17's review field; then your push and the "First correction of the polariton test" and polariton-bridge jobs confirmed with gh pr checks, before order 410 runs>>>
REASON: decision (3). Hosted CI is CANNOT_SEE from this lane.

Low, lane-internal only, no repo change:
- The lane's seal.py comment names RECORDS.hbp; its records are PREDICTION-Q0.hbp and RESULTS-Q0.hbp.
- PREDICTION-Q0 names scripts/guard.py; the lane's guards are run_jobs.py, guarded_stage.py, guard_check.py and replay_driver.py.
- The SEAL row has a "||" inside a field, so a reader that splits on "|" needs a pattern to find the seal value.