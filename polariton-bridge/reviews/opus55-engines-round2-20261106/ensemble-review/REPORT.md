VERDICT: PASS_WITH_HOLDS. Before any blind run, four HIGH holds need the seat: H1 and H5 (engine), H8 (ENGINE-CHANGES) and H9 (CORRECTIONS).

What changed: I wrote only inside `C:/tmp/opus55/bridge-engine-review2-ensemble-20261106/`. The worktree is still clean at 2ab8143. No earlier lane folder or the worktree has a file written after 06:00 (round1-reports holds only the seat's 06:01 files). Every number below is MEASURED unless tagged otherwise.

## 1. Rebuild, gate, float scan (MEASURED)
- **Windows, Rust 1.81.0, my target directory:**
  - fmt: exit 0, empty log.
  - clippy, both forms: exit 0, 0 warnings.
  - Tests: 14/14 pass.
  - Binary: ae6d33e2…, the same as the lane's, built at a different path (so /Brepro gives a path-independent build).
- **Linux, Ubuntu WSL, rustc 1.81.0:**
  - fmt, clippy (both forms) and the tests give the same results.
  - Binary: 9ad6f7d6…, also equal to the CI-stage build, a third path.
- **My own lexer scan** (`tools/r2_floatscan.py`):
  - Self-test finds 1/1 type, 6/6 literals and 1/1 float method.
  - main.rs (85,042 B) and sha256.rs: 0 types, 0 literals, 0 float methods, so float_used=0.
- **Binary scan:** 0 x86 float arithmetic, convert or compare instructions in either binary. The only xmm instructions are register zeroing (`xorps reg,reg`: 115 on Linux, 57 on Windows) and data moves.
- **Lane folder:** 1,132 of the 1,133 LANE-RECEIPT-E2 rows match their files. The one mismatch is the receipt's own sidecar, which a row inside the receipt cannot list (H16).

## 2. Reproduction: 13 of 33 receipts, byte for byte (MEASURED)
- **The 11 slowest raw files**, run with the Linux binary (the lane ran Windows), all bytes-equal:
  - raw_y0_N2187_d1o2 and _d0, raw_y0_N729_d0, raw_y0_N2187_dm1o2
  - raw_y0_N729_d1o2 and _dm1o2, raw_reseed_y0_N2187_d0
  - raw_y_N243_d1o2_s1o2, raw_y_N729_d1o2_s1, raw_y_N243_dm1o2_s1o2, raw_diag_y0_N729_d0_dt128
- **The two controls files:** TEST-RUNS.hbp (331dc0a6…) and T1B (8aee3a7f…), both bytes-equal.
- In every case the receipt hash matched, the TWRUN line was equal, and stdout had 0 CR bytes. My own decimal recomputation of the control triples equals the printed ones.

## 3. Line-by-line read since round 1 (DERIVED unless tagged)
- **The diffs:** 34df919c→a740b653 is exactly the review's R2, R3, R5 and R7. a740b653→e5682f1d is 1,093 diff lines, all read.
- **Every bound formula checked against BRIDGE_TRAJ_MAP's H:** step_bound (the M and S row sums, μ, L, Lip, the R_n chain, ρ), obs_bounds, field_bounds, sharp_err, seed_err, the MODE0 term and Pb. All match.
- **Region margin:** 2ε + 32 covers the exact stage points, which lie within 1.66ε + 15.4 of the computed ones given hL ≤ ½ and hρ ≤ 8. The comment does not state this; H4 adds it.
- **Rounding direction:** every bound step rounds up.
- **Overflow:** the u64 products in step_bound can't overflow before a fault fires at u = 1, and the u128 sums stay within about 2^121 at plan counts.
- **Index arithmetic:** the stride and record indexing are correct.
- **LOCK and FLIP start from VNC's state:** confirmed, with no code change in this round.
- **My integer model (MEASURED), at 7 points as built (P6 stopped, exit 4) and 8 with the fix:** draws, starts, observables, controls, all 34 TWB fields (the 8 exact squares included), pairs and NL agree bit for bit, 0 mismatches across 184 draws, 5,320 observables, 6,664 fields and 924 pairs. The `run` rows on 3 threads equal the `dump` rows on 1.
- **Bound against my exact 2^-160 reference (MEASURED):** 0 violations, covering 3,864 start, 5,320 state, 47,880 observable, 6,664 field, 924 pair and 28 NL comparisons.
- **The lane's results, reproduced with my own code (MEASURED):**
  - BOUND-GROWTH and BOUND-GROWTH-ACTUAL to the printed digits.
  - E2_START_A: C1 = 7.401313e-2, 2.470321e-2, 8.233748e-3; z against 2/N = −0.62, 0.50, 0.82; against the ring −44.37, −19.00, −11.93.
  - Fresh seeds: N=81 gives z 0.24 against 2/N and −19.26 against the ring.
- **DERIVED:** E[X_NC] = N−1 for Gaussian seeds, and N−1+1/2048 for the engine's binomial seeds.
- **Correction to the lane's H9 text:** at t=493/64 the actual/bound ratio runs from 1.1e-7 to 9.7e-6, not "1e-7 to 1e-6".
- **NEW, HIGH:**
  - **MODE0 stops the batch at late times.** At N=6561, δ=1/2, y=1/243 (8 samples), MODE0 stops with TWB_FAULT `rounding_bound_hL_above_1/2` (exit 4) at t=29/4; the plan runs MODE0 to 493/64 at its δ=3/5 partner. With 96 samples to t=7, both N=6561 and N=729 stop with exit 4.
  - **C_MODE0's predicted MET is unreachable.** e_round over the 1e-7 tolerance is 4.7 to 9.4e5 on the worst of A1, C1, f, D2 across 13 records. The MODE0−VNC differences themselves are 5e-11 to 2.4e-8.
- **Proposed fix FIXF (holds H1–H7):** main.rs becomes 723b3674…, Linux binary 75530df9…, Windows /Brepro binary ac7ff8f4… (identical at two paths). It passes fmt, clippy and 14/14 tests.
  - No stops at 4 analog points out to their frozen last times.
  - VNC's bound at N=6561, t=493/64 drops from 3.3e-3 to 3.9e-5.
  - The bound still holds at all 8 points: 0 violations against the exact reference with MODE0 rotated by the integer vector.
  - My bound model R2_BND recomputes every printed bound with 0 mismatches.
  - Value rows are unchanged: the P1 dump and run, raw_y0_N81_dm1o2 and T1B are bytes-equal.
  - C_MODE0's e_round over tolerance is still 1.08 to 2.0e5, so H9 still applies.

## 4. Mutation: 27 faults in the new parts (MEASURED; `out/mut/MUTATION-MATRIX.hbp`)
- **Frozen-gate receipt and CI T1B:** caught 0 of 29 binaries (27 mutants plus BASE and FIXF).
- **Caught by the integer model, the soundness check, unit tests or CI provenance:** N01, N05–N14, N17, N19, N06c, N07c, N13c, N14c.
- **Caught only by my formula-level model R2_BND:** N04, N15, N16, N20, N02c, N03c, N18c. Clippy also catches N02 and N03, but only through an unused-name lint; their lint-clean forms are N02c and N03c. H10 adds R2_BND to the gate text.

## 5. CORRECTIONS (MEASURED)
- All 26 frozen_text values occur exactly once on their stated line, byte for byte.
- The values_moved counts recount exactly on the 352 BRIDGE_AT rows: jflip 82/13/60/196/1, lock 57/39/256, mode0 MET 352, noiseless 352, all M fields present on 352.
- ensemble-26 departs from R6's NEW (they share only the first 21 of 311 characters); see H9.
- The lane's candidate ensemble-27 also checks: its frozen text occurs once, on line 423.

## 6. Reserved set (MEASURED)
- **The lane:** 5,893 launches plus the model rows of 1,242 text files contain 0 reserved points.
  - 800 band launches, all with zero samples: 790 were refused.
  - The other 10 came from mutant M09 (band dropped). Two of those ran mask=NL and integrated 32 steps at δ=−31/50 (N=6561) and δ=−16/25 (N=2187), y=0. Both points are outside the reserved set; H11 closes this gap.
  - lift_reserved_guard=1 appears 32 times, always at (81, 1/2, 1/18) with 0 samples.
- **Mine:** 885 launch rows, 0 reserved. Band points were only ever started with zero samples, and those carrying NL were refused by the engine.
- **CI job, run verbatim on the staged repo (968 files):** the frozen job passes 3/3 steps and the ensemble job 6/6. The guard step with steps=0 (H11) also passes.

## Files
All in `C:/tmp/opus55/bridge-engine-review2-ensemble-20261106/`:

| File | sha256 |
|---|---|
| out/REVIEW2-ENSEMBLE.hbp (1,591 rows, 733 files listed; sidecar written) | 8b8e99cc96f3886938c6264f1033bf2e730ea6455cf736cd819b7e6fd3abdc0b |
| out/HOLDS-REVIEW2.txt | 4650b8b885aaf28e753fdf84d3de87463c20bbdd496e0c529744cd59765bb42d |
| out/HOLDS-CHECK.hbp (16/16 OLD texts verified; H1–H7 applied give 723b3674) | 8c1617dc673241dc9b428fc0d9c0f937f5cd40d7c6f557281e9ff0adfadd52dd |
| out/mut/MUTATION-MATRIX.hbp | b46f189ab0b450fa6c5844f27bf4f224c6e5ddf7c402fad445561e7cecc8b9ef |
| out/hold/MODE0-RANGES.hbp | 66bd0dddacb7722a593d3a118b68e5a5501e6ce017c00a390d25d613774ef931 |
| out/hold/HOLD-SUM.hbp | d1976c265ceb6d474b4b7c639f8f790c6eab63ce4ee44f2ae0676b7b403a16c6 |
| tools/r2_ref.py | 504151b7cc53f1eaf0e3bc2df878baeb203a33a3b979c98d5006f4a6429d395a |
| tools/r2_hold.py | 14edd4c421f21c03b9059e2a33a40cae82e45ef8ffdca6db21892fe8e41a9f38 |
| tools/r2_bnd.py | 50af2797a5bac8dc89637c7a79108d03926a3508b610e261cedf785435998c05 |
| tools/r2_guard.py | dcfd46afa1960c2b64de8b671bae4b84a8867624c452be136bbe5953a852defc |
| tools/r2_floatscan.py | 95ba3868d4904339b667a163d31b5e367b535e7c31f5d9a9861533c9bbe46aa7 |
| tools/r2_repro.py | 994d8ad951f7a9d8ec6950054d0a5641399ec94e4b3539a75660855c5f07f288 |
| tools/r2_repro_ctl.py | cd190881b5cb52638bf79a216e408fe7fd2fb4770a97f3485d607c3c6ad47b53 |
| tools/r2_mutants.py | 2665e31cf95b133f75a46468f03d6229039b6b32f53d1ed17ff973102ca28c7f |
| tools/r2_mut_run.py | 572b95baf83000a2ed87552ae3ecd193a6caf6d88e6905558aa4b72aeb92dfb9 |
| tools/r2_fixf.py | 6282b659ca141d62d5d36000648f6213a014c4f8417db12b513e8c4813da4486 |
| mut/FIXF/twens/src/main.rs (the proposed source) | 723b36745af6c926849ff7a6da74d8c82007dfc4071761795bb639fcd8d4a609 |

The lane's proposed repo files check out (MEASURED):
- README equals the worktree's with H6–H8 applied (2eaded4a).
- ENGINE-CHANGES equals the worktree's plus the 5 rows (3235389a).
- SHA256SUMS equals H5's NEW, and all 12 lines are true.
- The engine files equal the gated crate.
- The workflow keeps the frozen job's bytes as a prefix (676ef273).
- All 14 files have 0 CR bytes.

## HOLDS

HOLD H1 | file=C:/tmp/opus55/bridge-engine-ensemble2-20261106/proposed/polariton-bridge/engines/ensemble/src/main.rs | severity=HIGH
OLD<<<
    let vnc0 = out.init[VNC];
    let mut ib6 = out.ib[VNC];
    for (j, e) in ib6.iter_mut().enumerate() {
        *e += cu(cmod(vnc0[2 * j], vnc0[2 * j + 1]), out.eta + 2) + 3;
    }
    out.ib[MODE0] = ib6;
>>>
NEW<<<
    // MODE0's reference: the exact VNC start rotated by the integer vector (c30, s30)/2^40 itself, whose norm is below
    // 1 + 2^-29 (r >= 2^29); C_MODE0 reads "a unit vector exact to at least 2^-29". Its start error is VNC's times that
    // norm, plus the 3 ulps of the rotation's floors (modulus below sqrt(5)).
    let mut ib6 = out.ib[VNC];
    for e in ib6.iter_mut() {
        *e = cu(*e, ONEU + (1 << 11)) + 3;
    }
    out.ib[MODE0] = ib6;
>>>
REASON: As built, MODE0's start bound carries the norm excess of its 30-bit unit vector, about 1.4e3 ulps against VNC's 3 to 10, and the step recursion carries that to order 1. At N=6561, δ=1/2, y=1/243 (8 samples) the engine stops with TWB_FAULT hL_above_1/2 (exit 4) at t=29/4, with ε = 0.584 at 463/64. The plan runs MODE0 to 493/64 there. Runs with 96 samples to t=7 at N=6561 and N=729 also stop, and a stop loses every variant in the batch. The frozen C_MODE0 clause reads "a unit vector exact to at least 2^-29", so the reference can be the drawn integer vector, whose norm is below 1 + 2^-29. With H1–H7 applied (723b3674…): fmt, clippy and 14/14 tests pass; Linux binary 75530df9…; Windows /Brepro ac7ff8f4… at two paths. There are 0 stops at the 4 analog points, the bound holds at 8 points against the matching reference, R2_BND finds 0 mismatches, and the value rows are bytes-equal. If adopted, the lane regenerates the sums, CORRECTIONS ensemble-8 and ensemble-18 to 20, and ENGINE-CHANGES rows 1, 2 and 5, then reruns the 33-file gate.

HOLD H2 | file=(same) | severity=LOW
OLD<<<
// of the starts, the exact unit vector of MODE0, the exact parameters delta, u, y, the exact RK4 map at the same dtden,
>>>
NEW<<<
// of the starts, MODE0's integer unit vector as drawn, the exact parameters delta, u, y, the exact RK4 map at the same dtden,
>>>
REASON: The reference statement in H1's terms. This comment is part of the source that was measured as 723b3674.

HOLD H3 | file=(same) | severity=LOW
OLD<<<
//  min)); the V1 ring by < 2; MODE0's rotation by the integer unit vector (c, s) = trunc((a, b) 2^40 / r), r = isqrt(a^2+b^2),
//  is off from the exact unit vector by at most D/(2 r^2) + 2 ulps relative, D = a^2 + b^2 - r^2, plus 3 ulps of its floors.
>>>
NEW<<<
//  min)); the V1 ring by < 2; MODE0's reference is VNC's exact start rotated by the integer vector (c, s) = trunc((a, b)
//  2^40 / r) itself, r = isqrt(a^2+b^2) >= 2^29, so |(c, s)| < 1 + 2^-29: VNC's start error times that, plus 3 ulps of floors.
>>>
REASON: The derivation of H1's start term. Part of the measured source.

HOLD H4 | file=(same) | severity=LOW
OLD<<<
//  (row-sum bounds over the region the step's stage points can reach, R_j = max over the stage inputs of |re| + |im|,
//  plus 2 eps + 32). RK4's step map has DPhi = I + h Abar + R2, Abar the weighted mean of Df at the stage points,
>>>
NEW<<<
//  (row-sum bounds over the region the step's stage points can reach, R_j = max over the stage inputs of max + min/2 of
//  |re|, |im| (at least the modulus), plus 2 eps + 32: with hL <= 1/2 and h rho <= 8 the exact stage points of any state
//  within eps lie within 1.66 eps + 16 of the computed ones). RK4's step map has DPhi = I + h Abar + R2, Abar the weighted
//  mean of Df at the stage points,
>>>
REASON: H5's radius, plus the justification of the margin. With hL ≤ ½ and hρ ≤ 8, the stage deviations are 1.25ε+7, 1.3125ε+8.75 and 1.65625ε+15.375 (DERIVED). Part of the measured source.

HOLD H5 | file=(same) | severity=HIGH
OLD<<<
/// |re| + |im| at 2^40 (at least the modulus), cheap.
#[inline]
fn amag(re: i64, im: i64) -> u64 {
    re.unsigned_abs() + im.unsigned_abs()
}
>>>
NEW<<<
/// max(|re|, |im|) + min(|re|, |im|)/2 at 2^40, rounded up: at least the modulus ((a + b/2)^2 >= a^2 + b^2 for a >= b),
/// at most 1.118 times it, so the region is the same at every phase of the sample (cheap; no square root).
#[inline]
fn amag(re: i64, im: i64) -> u64 {
    let (a, b) = (re.unsigned_abs(), im.unsigned_abs());
    a.max(b) + a.min(b).div_ceil(2)
}
>>>
REASON: |re|+|im| reaches √2 times the modulus, and the dynamics rotate each mode's phase, so μ and L (both ∝ r²) come out up to 2× too large, and the bound's exponential growth inflates with them. Measured with H1–H7:
- N=6561, δ=1/2, y=1/243, t=493/64: VNC ε = 4.31e7 ulps (as built 3.58e9), MODE0 9.94e7 (as built it stops), NL 1.15e7.
- N=729, t=405/64: VNC 5.95e6 (as built 2.00e8), MODE0 1.28e7 (as built 4.75e10).
- VNC's relative e_round at N=81, t=317/64 drops by about 20×.

HOLD H6 | file=(same) | severity=LOW
OLD<<<
/// inputs' magnitudes (|re| + |im| per mode, at 2^40).
>>>
NEW<<<
/// inputs' magnitudes (amag per mode, at 2^40).
>>>
REASON: The comment in H5's terms. Part of the measured source.

HOLD H7 | file=(same) | severity=LOW
OLD<<<
/// rk4 with the per-mode magnitudes (|re| + |im|, at 2^40) of its four stage inputs, maximised, for the rounding bound.
>>>
NEW<<<
/// rk4 with the per-mode magnitudes (amag, at 2^40) of its four stage inputs, maximised, for the rounding bound.
>>>
REASON: The comment in H5's terms. With H1–H7 applied, main.rs is 723b3674…, which is what was measured.

HOLD H8 | file=C:/tmp/opus55/bridge-engine-ensemble2-20261106/proposed/polariton-bridge/ENGINE-CHANGES.hbp | severity=HIGH
OLD<<<
growth_on_the_noiseless_path_N=6561=state_bound_2.4e-9_to_2.8e-9_at_t=2,2.1e-4_to_1.8e-3_at_t=493/64;the_measured_error_there_1e2_to_4e3_ulps(out/BOUND-GROWTH.hbp,out/BOUND-GROWTH-ACTUAL.hbp)|cost=
>>>
NEW<<<
growth_on_the_noiseless_path_N=6561=state_bound_2.4e-9_to_2.8e-9_at_t=2,2.1e-4_to_1.8e-3_at_t=493/64;the_measured_error_there_1e2_to_4e3_ulps(out/BOUND-GROWTH.hbp,out/BOUND-GROWTH-ACTUAL.hbp;reproduced_by_the_second_seat's_review_2)|late_times_with_samples=MODE0_stops_with_TWB_FAULT_rounding_bound_hL_above_1/2(exit_4,the_whole_batch)_at_t=29/4_at_N=6561,delta=1/2,y=1/243(8_samples;the_plan_runs_MODE0_to_493/64_at_its_delta=3/5_partner)_and_before_t=7_at_N=729,delta=1/2,y=1/81(96_samples);VNC's_state_bound_3.3e-3_at_N=6561,delta=1/2,y=1/243,t=493/64|C_MODE0=its_e_round(TWB_PAIR_ROUND_rb_d_over_n)_above_its_10^-7_tolerance_at_every_measured_record:4.7_to_9.4e5_times_on_the_worst_of_A1,C1,f,D2(13_records,t=1/2_to_99/16,N=81_and_6561;f_alone_1.02_to_1.4e5),the_measured_MODE0-VNC_differences_5e-11_to_2.4e-8_relative|cost=
>>>
REASON: These are results of this engine at allowed points (MEASURED; out/hold/FAULT-TIME.hbp and MODE0-READ.hbp). If H1–H7 are taken, the row carries 723b3674's numbers instead: no stops, and a C_MODE0 ratio of 1.08 to 2.0e5.

HOLD H9 | file=C:/tmp/opus55/bridge-engine-ensemble2-20261106/proposed/polariton-bridge/CORRECTIONS.hbp | severity=HIGH
OLD<<<
and_the_read_stage_decides_those_verdicts_with_the_operator(the_review's_F4:2.33e-6_on_Re_Z_at_N=2187,delta=0,y=0,t=3_where_VNC's_mean_is_-1.28e-5;its_R6_names_the_paired-difference_reading)
>>>
NEW<<<
and_the_read_stage_decides_those_verdicts_with_the_operator(the_review's_F4:2.33e-6_on_Re_Z_at_N=2187,delta=0,y=0,t=3_where_VNC's_mean_is_-1.28e-5;its_R6_names_the_paired-difference_reading);C_MODE0's_e(BRIDGE_READ_RULE)_carries_e_round=the_engine's_printed_bound_of_the_paired_difference(TWB_PAIR_ROUND_rb_d_over_n),so_a_row_whose_e_round_exceeds_10^-7_of_the_observable_reads_NOT_RESOLVED(measured_at_allowed_analogs_of_the_frozen_points,the_worst_of_A1,C1,f,D2_per_record:4.7_to_9.4e5_times_10^-7_with_twens_0.3.0_e5682f1d(13_records),1.08_to_2.0e5_times_with_the_second_seat's_engine_holds_H1_to_H7(14_records;there_f,C1,D2_fall_below_10^-7_on_some_records_at_N=81,t<=1);the_MODE0-VNC_differences_themselves_5e-11_to_6.4e-8_relative)
>>>
REASON: The read rule's e includes e_round, so the predicted MET (mode0=MET on 352 of 352 rows) can only read NOT_RESOLVED from t=½ onward, even though the measured differences are below the tolerance. values_moved=0. The seat chooses one of:
- (a) this row as written;
- (b) an engine change where e_round = |O_40 − O_fine| plus the fine run's bound, from a second run at a finer fixed point (its cost is a CONJECTURE until built);
- (c) R6's paired-difference reading at y=0. ensemble-26 departs from R6's NEW (21 of 311 characters in common).

HOLD H10 | file=C:/tmp/opus55/bridge-engine-ensemble2-20261106/proposed/polariton-bridge/CORRECTIONS.hbp | severity=MEDIUM
OLD<<<
the_printed_rounding_bound_against_a_finer_run_of_the_same_samples,0_violations,and_halved_failing;
>>>
NEW<<<
the_printed_rounding_bound_against_a_finer_run_of_the_same_samples,0_violations,and_halved_failing;an_independent_recomputation_of_every_printed_bound(TWB_DUMP_IB,TWB_DUMP_RB,TWB_ROUND,TWB_PAIR_ROUND,TWB_NL)_from_the_derivation,exact_equality;
>>>
REASON: Replace all 3 occurrences (ensemble-23, 24, 25). Seven mutants (N02c, N03c, N04, N15, N16, N18c, N20) pass every check except a formula-level recomputation: fmt, clippy, the tests, the CI job, the receipt, the model and the soundness check all miss them. R2_BND, like the lane's R_BND, catches all of them.

HOLD H11 | file=C:/tmp/opus55/bridge-engine-ensemble2-20261106/proposed/.github/workflows/polariton-bridge.yml | severity=LOW
OLD<<<
          K="u=1 seed=1 start=0 count=0 dtden=64 threads=1 steps=32 ctrl=1099511627776:0:0"
>>>
NEW<<<
          K="u=1 seed=1 start=0 count=0 dtden=64 threads=1 steps=0 ctrl=1099511627776:0:0"
>>>
REASON: mask=NL integrates one trajectory whatever the count, so a guard that fails to refuse runs 32 steps inside the band. M09 did exactly that at δ=−31/50 and δ=−16/25, both outside the reserved set. With steps=0, a broken guard reaches only the t=0 record. The step with steps=0 passes (exit 0).

HOLD H12 | file=C:/tmp/opus55/bridge-engine-ensemble2-20261106/proposed/polariton-bridge/ENGINE-CHANGES.hbp | severity=NOTE
OLD<<<
for_the_same_file_without_the_bound|tag=MEASURED|json=0
>>>
NEW<<<
for_the_same_file_without_the_bound|by=opus55,bridge-engine-ensemble2-20261106|tag=MEASURED|json=0
>>>
REASON: Row 2. The quantum rows and row 1 carry by=; rows 2 to 5 do not.

HOLD H13 | file=(same) | severity=NOTE
OLD<<<
|tools=tools/e2_nl.py|tag=MEASURED|json=0
>>>
NEW<<<
|tools=tools/e2_nl.py|by=opus55,bridge-engine-ensemble2-20261106|tag=MEASURED|json=0
>>>
REASON: As H12, row 3.

HOLD H14 | file=(same) | severity=NOTE
OLD<<<
|tools=tools/e2_start.py|tag=MEASURED|json=0
>>>
NEW<<<
|tools=tools/e2_start.py|by=opus55,bridge-engine-ensemble2-20261106|tag=MEASURED|json=0
>>>
REASON: As H12, row 4.

HOLD H15 | file=(same) | severity=NOTE
OLD<<<
(no_flag)|tag=MEASURED|json=0
>>>
NEW<<<
(no_flag)|by=opus55,bridge-engine-ensemble2-20261106|tag=MEASURED|json=0
>>>
REASON: As H12, row 5.

HOLD H16 | file=C:/tmp/opus55/bridge-engine-ensemble2-20261106/out/LANE-RECEIPT-E2.hbp | severity=NOTE
OLD<<<
E2_FILE|path=out/LANE-RECEIPT-E2.hbp.sha256|bytes=86|sha256=865cab9aced36d59ede79f1bfe3c98bfc2af4e6611a7ee814b7c088b39444a1b|cr=0|json=0
>>>
NEW<<<
(the row removed)
>>>
REASON: A row inside the receipt cannot list the sidecar, which holds the receipt's own hash. On disk the sidecar is bf6e3655…; the other 1,132 rows match.

On the lane's holds:
- H1, H2, H6–H8: agreed, with H8 and H9 above added.
- H3 and H5: agreed, with H11 added. If H1–H7 are taken, the main.rs line in H5 changes.
- H4: agreed, subject to H1–H7.
- H9 (the ensemble-27 candidate): its frozen text is verified on line 423. Recommended, alongside H1–H7.
