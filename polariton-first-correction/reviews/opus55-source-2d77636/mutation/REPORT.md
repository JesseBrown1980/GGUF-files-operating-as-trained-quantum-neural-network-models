**Head checked:** `2d776369fbf7448c6adcf3ecce4bcaa2ae792c20`, before and after, and it matches the PR head (draft, open). The worktree is clean. The grid was not run.

**Verdict in one line:** I find no fault in the engine, but as filed the checks catch dynamics faults and miss certificate faults. Hold the grid until H1, H2–H4, H15 and H16 land.

**Two slips**
- My first `cheb` build wrote `Cargo.lock` into the worktree for 21 s. I removed it.
- The limit was 2 runs at a time. Python scripts ran beside the two engine workers, including `run/distance.py`, a 3-minute model run at N=60. So 3 or 4 of my processes ran at those moments.

No process of mine is left running.

## What I ran

| Run | Scope | Result file |
|---|---|---|
| Mutants | 153, built with Rust 1.81. Each went through route rows, the control stage with the reader's control mode, chosen rows at N=81, 243, 729 (K≤729), and route bessel. | `run/TABLE.txt` |
| Anchors | 39 survivors whose bounds moved, read at N=6561, K=800 or 1000. The other anchor rows came from the filed receipt, since the reads are unchanged. | `out/*/RESULT2.hbp` |
| Reader, synthetic | 87 scenarios plus 19 reader mutants, values from the closed forms, no model run. | `synth/` |
| Forms | Typed by hand from F5 and compared with `Forms.values` in exact rationals. | `forms/FORMS-COMPARE.hbp` |
| Second seat | `cheb` on all 62 filed rows, my 17 chosen rows and 6 new rows at delta=-1/2, -3/4, 3/4. | `run/cross-baseline.out`, `run/patched-integrator-*.out` |
| Certificate walk | Recomputed from its own words in big integers at N=100 and N=40. | `run/route_cert_real.out`, `run/CERT.hbp` |
| State distance | ‖ψ_full − ψ_block‖ computed directly at N=60. | `run/DISTANCE.hbp` |
| K=1600 | The seen point only: N=6561, delta=0, y=1/81. | `run/final_real.out` |

## What survives

All tagged MEASURED unless marked.

- **Row's forms:** my typing equals `Forms.values` within 10^-60 at the 10 grid points and 35 seen points. Predicted f is 0.00327 to 0.01099. The law alone is off by at least 4327 ppm on A1 and 8421 ppm on C1 at every point.
- **Dynamics checks:** every mutant of H, the even basis, the diagonal, the recurrence and the matrix-free product dies by name or by panic. So do the signs at delta≥0 and all phase mutants except exact time reversal, which no read can tell apart.
- **Real engine against `cheb`:**
  - At N=6561, K=1200, C1 is off by 5e-18 and A1 by 5.3e-14.
  - f and C2 agree within 88e-18.
  - Differences on C1, A1 and V2 sit inside the engine's read-out account.
  - The negative-delta rows agree too.
- **Certificate arithmetic:** the walk passes 19 of 19 names on all 4 cases. The limits are 1e-6 on `eps_tail`, the tail and the leak, and 1% on `C1_err` and `A1_err`.
- **State-level falsifier:** at N=60 the true distance sits under `leak_sum` by 1.27x to 2.29x, and under `eps_tail` on all 4 points.
- **K=1600 at the seen point:** 214 s, no panic, V² half width 1.9 ppm.
- **Reader, when fed well-formed receipts:**
  - MET and MISS are right at 1/1000 ± 10^-9 on C1, A1 and V² (24 of 24).
  - A wide certificate reads MISS, matching the row's words.
  - Blind and touched are apart and counted right.
  - The nondiscriminating mark is right.
  - The 30x read uses intervals, as GPT-6's item 7 asks.
  - The signs read with their errors.
- **Controls:** the four filed sabotages match `CONTROLS.hbp` byte for byte.
- **Certificate logic (DERIVED):** I found no fault reading Duhamel, the reach, the recurrence rounding or the observable forms. Another lane owns this review.

## What is refuted

1. **"The checks catch a wrong engine."** 68 of 153 mutants pass every filed check before the grid. The killed ones: 83 by name or panic, 2 at the anchors.
   - **Bound too small, reads unchanged (47, named in F4):**
     - W01: `eps_tail` is one window, `C1_err` x0.0112.
     - B02: norm(B) cut by 8.
     - B07: no pair elements, x0.010.
     - L02: top two shells only, x0.0475.
     - X02: `C1_err` cut by 16.
     - X12: A1 read-out dropped, x0.000235.
     - T06: `eps_poly` printed 0.
     - A04: `eps_round` cut by 100.
   - **Reads past their own bound, passing everything (6):**
     - S06: x wrong at delta<0, C1 off 0.38 at N=81. No check reads an evolved row at delta<0.
     - R04: C1 scaled by 1+2^-20, 61700x its error.
     - R06: A1, 261x.
     - R08: V² scaled by 1+2^-20, with no separate read of V² to catch it.
     - R17: hidden drift, 5790x.
     - W12: real damping, 1.4x.
   - **Within bound, or in a value nothing reads (15):** P04, K03, K05, K06, K08, T01, T02, W10, W13, T04, X17, B09, R11, R15, R16.
   - With the holds, 57 of the 68 die by name. The 11 left are P04, K03, K05, K06, W05, W06, W10, W13, A09, R15, R16. Each moves reads by at most 3097e-18 and eps by at most 1.3%.

2. **The route's integrator limit.** As filed it reads FAIL on the real engine at N=6561, K=1200: `A1_off_e18=53459` against limit 10000, exit 1 (`run/route_integrator_seen.out`). The workflow runs this step only after the grid is read, so at this seen row it would turn red on a healthy engine. Whether it does at the grid's own points is CANNOT_SEE.

3. **"The reader enforces the row."** Head reads 73 of 87 scenarios as the row asks.
   - Every K=1600 row missing reads exit 0, blind 8/8, touched 2/2, with 0 `expanding_L` rows.
   - A duplicate row overwrites silently, and an extra row goes unread.
   - x wrong, V² off its definition by 2703 ppm, a printed-narrow V² interval, eps under its parts, and `eps_tail`=0 at K=1200 all read as met.
   - `numerical_over_margin_ppm` mixes units: it prints 1571 where 500000 is right.

4. **Nothing reads the reader's grid mode before the grid.** The workflow skips that step until the grid receipt exists. My battery kills 19 of 19 reader mutants, and two of those needed scenarios I added after a first pass (recorded beside). Filing the battery adds a new file, so it carries no OLD text to hold. It is an open item for the operator.

5. **Checks that hold whatever the engine does (MEASURED by census):**
   - `no_sabotage_named_in_control` reads PASS on all sabotages.
   - `extra_off` and `odd_off` read the route's own H: 0 of 153 nonzero, including wrong targets in `step()`.
   - `states_are_the_even_block` and `full_space_has_no_leak` never fail.
   - `anchor_K=1200_interval_holds_K=1200` compares a row with itself.
   - The f row reads the closed form only.
   - `series_tail_covered` has a slack the size of the tail. T06 passes all 11 tables with `eps_poly` printed 0.
   - `bessel_table` stops at the table's end, so K08 and K09 pass it.

   Weak rather than decorative:
   - `every_certificate_holds` has at least 3465x of room on the baseline.
   - The norm check has 1138x of room.
   - The anchors pin V²'s half width to a window: 11.8x under, 3.66x over.

   F7 names each one and its sharper form.

## Every hold

All 30 OLD texts occur once at head. None touches the engine, and `RECEIPT-BASELINE.hbp` stays.

| Hold | Severity | Change |
|---|---|---|
| H1 | high | Route integrator limits from the read-out account; reads every observable `cheb` prints. |
| H2, H3 | high | Calls of the new coverage check, grid and baseline. |
| H4 | high | `plan_coverage` and `printed_fields_checks` in the reader. |
| H5 | medium | `no_sabotage` that can fail on a control; calls the printed-field checks. |
| H6 | low | Unit fix in `numerical_over_margin_ppm`. |
| H7 | low | Drop the K=1200 anchor self-comparison. |
| H8 | low | Run internal checks on the baseline file in grid mode. |
| H9 | low | `run_stage` `removesuffix`; `rstrip` eats trailing zeros off peak memory on Linux. |
| H10, H11 | low | Route rows cases off delta=±1/4; elements only today, no state evolved. |
| H12 | medium | Bessel table compared past its end. |
| H13 | medium | Series tail read on every row, without the slack. |
| H14 | medium | norm(B) and the spectral interval on each receipt row's own block. |
| H15 | medium | Crosscheck rows at delta=-1/2, -3/4, 3/4 in the plan. |
| H16 | high | Workflow runs the second seat and the certificate walk before the grid. |
| H17, H18, H19 | medium, medium, low | Route `certificate` mode, its main branch, its usage line. |
| H20 | low | No baseline run on any grid point, touched included. |
| H21 | low | Mark read f beside predicted f. |
| H22, H23 | low | Workflow paths cover the pinned inputs. |
| H24 | medium | Second seat on the verdict K as well, not only K=1200. |
| H25, H26 | low | New expected rows in `CONTROLS.hbp`. |
| H27 | low | New pins in `SHA256SUMS`, valid if every hold lands; otherwise recompute. |
| H28, H29, H30 | low | New rows in `READ-BASELINE.hbp`. |

With all holds applied in `patched/` (`run/VERIFY-FINAL.hbp`):
- The baseline read is byte-identical to the patched file.
- The sabotages match the patched `CONTROLS.hbp` 4 of 4.
- The synthetic battery reads 87 of 87 as the row asks.
- All 62 filed rows and the 6 crosscheck rows pass the second seat.

The hosted run of this set is NAMED until pushed; it owns "green".

## Is the engine fit to read the grid?

**Yes as an engine.** This lane measured no engine fault, on evidence that shares no code with it: `cheb` on all rows, the certificate walk, the state distance, and 0 engine holds. The tail floor at K=1200 and K=1600 gives V² half widths of about 5 ppm and 1.9 ppm of V², far inside 1/1000. That is measured only at the seen point.

**The checks around it are not yet fit.** I would hold the grid for these:
- **H1:** otherwise the last hosted step reads red on a healthy engine, measured at the seen row.
- **H2–H4:** otherwise a lost K reads as met.
- **H15 and H16:** otherwise no negative-delta evolution meets separate code before the grid reads.

These are minutes of work and the grid is unrun. H17 is what puts the certificate's size under separate arithmetic. Without it, a certificate wrong by a factor of 2 to 8 reaches the frozen read unseen.

## What I could not check

- **CANNOT_SEE (off limits):** the grid rows themselves, their K=1600 behaviour, and whether A1 off exceeds 10^-14 there.
- **CANNOT_SEE (filed rows case list):** I did not run the list at delta=±1/4 here. The hosted job at this head passes it.
- **CANNOT_SEE (hosted):** the bytes of anything in `HOLDS.txt`. All my runs are local Windows MSVC.
- **Not done:**
  - rederiving F5, which I typed but did not derive;
  - the certificate's logic beyond F9 and the N=60 distances;
  - mutants of `cheb` and of `run_stage.py`;
  - N=6561 at any delta but 0.
- **Coverage limit:** my mutant rows sit at K≤729, so a fault only at large K is seen only through the K=800 anchor and the rows-based checks.

## Files

All in `C:/tmp/opus55/fc-review-mutation-20261105/`:
- `FINDINGS.txt` holds the full 153-row table in F4b, each finding with what ran and what could still be wrong, the row's text phrase by phrase in F6, and GPT-6's checklist item by item in F12.
- `HOLDS.txt`
- `run/TABLE.txt`
- `synth/SYNTH-READ-head.hbp`
