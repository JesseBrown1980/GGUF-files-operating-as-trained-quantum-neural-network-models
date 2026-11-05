**The engine is fit to read the grid. The reader is not, until H1 goes in.** Every inequality the printed bound rests on survives. The fault is one clause in the reader, which would turn a rounding floor in eps into frozen MISS rows.

**Head checked:** `2d776369fbf7448c6adcf3ecce4bcaa2ae792c20`. The worktree is clean. The hosted job on PR #11 passes at this head (`gh pr checks 11`).

**One slip of mine:** building cheb with `--manifest-path` wrote a `Cargo.lock` into `polariton/second-seat/recheck-ce44be7/contact/cheb/` at 13:27:49. I deleted that one file about a minute later, and `git status --short` is empty.

## What I ran
All runs stayed on allowed points: no stage grid and no off-limits point.

| Run | Scale | Script |
|---|---|---|
| Exact reference on the full Fock space, Python integers at 2^-240, sharing no code | 42,258 reads at N ≤ 40 | `truth_lib.py`, `sweep.py` |
| State-level deviation, read directly | every read above | `sweep.py` |
| Each inequality on its own, with exact block states | 1,152 rows at N ≤ 40 | `decompose.py` |
| Test of the test, with broken copies of the bound | 272 and 780 reads per copy | `copy2/`, `sweep.py` |
| Majorant and Bessel tables against exact series | E = 2..2999 at W = 6, plus other W | `check_series.py` |
| Integer scales against their limits, by closed forms | the grid's ranges | `overflow_ranges.py` |
| Largest K of the plan at the allowed point | N=6561, delta=0, y=1/81, K=1600, t=1,2 | engine and copy |
| State deviation against the full-space state | N=729 | `state_large.py` |
| Actual rounding, from W=6 against W=8 | N=40, 200, 729 | `rounding_actual.py` |
| Route's integrator check on seen rows | N=729 and N=6561 | `route_first_correction.py` |

The sweeps covered:
- delta = 0, ±1/2, ±3/4
- y from 0 to 100, including negative y
- every K at small N
- W = 0..14
- t up to 16

## What survives (DERIVED by hand and MEASURED)
1. **Duhamel:** the code accumulates the right quantity, with the right P, the block's own H, the even basis and JN = 1. The integral over the true deviation runs from 1.042 to 104.
2. **Boundary:** B acts on shells K-1 and K only, and every outgoing element is in `b_norm` with its even factors, including p = m and the top of the block. Printed norm(B) over the true norm:
   - 1.00 to 1.38 at N ≤ 40
   - 1.04 to 1.07 at grid-sized K
3. **Window:** the split at K-R, degree ≥ m0 with reach = 2 degree + 1, rho over all tau, and the offset carried before the rounding update are all correct.
   - The real reach never goes outside the bound. Reach 2 goes outside on 173 of 780 reads.
   - Inside the K > reach region, the smallest margin is 6.08.
4. **Series:** the phases of parts 0 and 1, the scale, the truncation and the early break are correct.
   - The majorant is never below exact where it is uncapped.
   - The worst Bessel table entry is off by 0.504 units, against the 4 units the bound takes.
   - rho ≤ 8 units holds up to z = 219. The grid's z is at most 34.8.
5. **Rounding:** the U_k accounting, sqrt(dim) per floor, E h times the element error, and the final floors are all on one scale, with a factor of 2 to spare.
   - The Bessel errors are covered.
   - The spectrum margin is at least 4.4e-4 against 3e-18, so rounding cannot push it outside [-1, 1].
6. **Overflow:** no overflow check can stop a run on the grid's ranges. K=1600 ran to the end in 367 s.
7. **Observables:** X, S, A = S/2 and B are correct. x_up and s_up are true upper bounds, and x_norm and s_norm are valid. The V² division and its sentinel are correct. The reader's bound on `<B>` is true.
8. **Reader's norm and energy bounds:** both are true statements.
   - A FAIL is a real alarm.
   - A PASS only means the read sits inside an account some 500 to 1,400 times wider than the rounding, and neither check tests the Hamiltonian.
9. **Truth at small N:** 0 of 42,258 reads fall outside any printed bound, and all 5,402 valid V² intervals hold the true value.

**Smallest margins found:**

| Quantity | Bound over true | Where |
|---|---|---|
| State | 1.021 | N=2, delta=3/4, y=1/100000, W=0, K=1, t=1 |
| C1 | 5.43 | N=4, delta=-1/2, y=1/100000, W=0, K=1, t=1 |
| A1, `<A>` | 15.41 | N=24, delta=-1/2, y=1/10, W=0, K=0, t=1 |
| `<B>` | 18.90 | N=3, delta=-1/2, y=10, W=0, K=3, t=5 |
| Norm | 66.75 | N=3, delta=1/2, y=1/1000000, W=2, K=2, t=1 |
| Energy | 4.358 | N=20, delta=0, y=0, W=2, K=18, t=2 |

The state margin of 1.021 matches my derived value, 1.0212. The bound is tight there and it holds.

**No missing term makes the bound false.** Four small unwritten terms sit far inside the slack, and F5 names them.

## Where the bound is loose (MEASURED)

| Layer | Factor |
|---|---|
| eps over true state deviation, N=729, K=128 to 384 | 21 to 203 |
| Same, at the floor, K=512 | 3.5e6 |
| Rounding account over actual | about 500 to 1,400 |
| C1_err over true offset, N=729 | 2.6e4 to 1.5e10 |

The causes:
- **The floor:** described in the next section.
- **The split:** it uses the norm on all shells above K-R, where the actual leak reads only K-1 and K. That costs a factor of 5 to 25.
- **Cauchy-Schwarz in the observable:** the deviation meets the state only at the boundary, which gives the large C1 factors.

None of this threatens the 1/1000 limit. V²'s half-width over V² is 1.9e-6 at K=1600.

## What is refuted
**`low.eps >= r.eps` in the reader's `expanding_L` is refuted.** eps at K_low can sit below eps at K_high with the observables identical.

`tail_norm` adds a floor of sqrt(S)·2^-42, and the offset term adds norm(B)·eta. So eps ≥ t·norm(B)·(sqrt(S)·2^-42 + eta/2), which rises with K. The law matches three measured rows within 0.03%. The bound stays true; only the clause is wrong.

Two measured pairs where the clause prints MISS:

| Point | eps at lower K | eps at higher K | Observables |
|---|---|---|---|
| N=6561, delta=0, y=1/81, t=1 | K=1200: 3.393e-8 | K=1600: 5.495e-8 | same C1_e18 |
| N=2187, delta=1/2, y=1/94, t=2 | K=1000: 2.710e-8 | K=1090: 2.861e-8 | same C1_e18, A1 within 1e-17 |

- **Estimate for the grid (CONJECTURE):** 8 or 9 of the 10 points print a frozen MISS on `expanding_L`, at least 6 of them blind. It comes from N=2187 runs only, and the count itself was not run.
- **Synthetic demonstration:** I built a receipt from the row's closed forms with eps at the measured floors; no model ran. It reads `all_rows_met=0|with_a_miss=8` on the blind set, and `8|0` with H1.
- **Falsifier:** the `eps_low` and `eps_high` columns on the grid's rows. If K=1200 is at or above K=1600 on all ten, the clause would have been harmless, and H1 still loses nothing.

**The route's 10^-14 limit on A1 is also refuted.** It FAILS on the seen rows:
- N=6561, K=1200: `A1_off_e18=53459`
- N=729, K=512: 1169874 and 797478

The state is right: A1 recomputed from the engine's dumped state with exact roots agrees with the second seat within 5e-18. The offset is `root24` in the read-out, inside A1_err. This step runs in CI only once the grid is filed, so it would go red after the read.

## Holds
All six OLD texts match the head byte for byte, once each. They are in `HOLDS.txt`.

- **H1, high:** `read_first_correction.py`: drop `and low.eps >= r.eps`. `READ-BASELINE.hbp` still reproduces byte for byte.
- **H2, medium:** `route_first_correction.py`: A1 limit becomes 10^-14 + 2^-23/N, printed. It PASSES on the three seen rows.
- **H3, low:** `polariton_first_correction.rs`: guard the V² division at C1 = 0 (2,082 stops at K=0, and at K=1 with y=0).
- **H4, low:** `polariton_first_correction.rs`: assert T ≥ 1, since t=0 prints nothing, exits 0 and blocks later t.
- **H5, low:** `polariton_first_correction.rs`: correct the sum-rule comment to the tolerance actually asserted.
- **H6, low:** `run_stage.py`: `rstrip` becomes `removesuffix`, since a Linux peak memory ending in 0 loses its zeros in the cost file.

H3, H4 and H5 pass fmt and clippy, and three filed rows reproduce byte for byte with them in. `SHA256SUMS` needs regenerating after any hold, and any engine hold moves the engine pin the grid runs at.

**Order:** H1 is required before the grid. H2 belongs before it too, so that no tolerance changes after a read. H3 to H6 are optional.

## What I could not check
- **CANNOT_SEE, grid points:** eps, tail and every read there are off limits. That is why the MISS count is an estimate; the mechanism is measured.
- **CANNOT_SEE, exact reference above N = 40:** N=729 rests on the engine against itself across K and W. N=6561 rests on K against K and the second seat's propagator on one row.
- **CANNOT_SEE, rho and offset terms:** no run distinguishes them, because the tail floor exceeds both. They rest on the derivation.
- **CANNOT_SEE, others:** the Gershgorin looseness of E at grid sizes, the Bessel check at W=0 above E=200 (my check's precision), and the V² margin, which I read only as inside or outside.
- **Not reviewed line by line:** the row's closed forms in `Forms` and the expected sabotage rows.
- **Not asked:** fabric, recall and the backend office.
- **One line, no hold:** `polariton-first-correction/README.md` says the baseline comes next, but it is already filed at this head.

Everything is in `C:/tmp/opus55/fc-review-certificate-20261105/`:
- `FINDINGS.txt`
- `HOLDS.txt`
- `results/` (the synthetic files are marked `SYNTHETIC-*` and are not reads)
