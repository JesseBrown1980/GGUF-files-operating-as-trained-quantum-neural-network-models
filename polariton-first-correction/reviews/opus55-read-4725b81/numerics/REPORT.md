Nothing in the filed read is refuted (refuted=false). Every number it rests on held up under every check I ran. The only faults are two low-severity wording and sourcing points in the stage README.

**Head checked:** `git -C C:/tmp/qnn-fc-read-wt rev-parse HEAD` = 4725b8124d1ef19d2e22844534e3abf39543fb30. The worktree is clean; I edited, committed, pushed and commented nothing. No model run touched delta = ±3/5. Every engine run used a copy of the filed binary, sha256 d9718bbe…, which I found at C:/tmp/qnn-fc-target/release. I kept to two of my processes at a time.

**What I ran and what it shows:**

1. **K beyond the plan (task 1).** K = 2000 and 2400 at two blind points, (1/2, 1/4) and (-1/4, 1). Across K = 1200 to 2400, C1, A1 and V² move by at most 124 × 10⁻¹⁸. Each value lies inside K = 1600's and K = 1200's certified intervals, and theirs inside it, at 12 of 12 both ways. Eps grows with K (2.37 × 10⁻⁷ and 2.98 × 10⁻⁷ at K = 2400), as the earlier review predicted from a rounding floor in the certificate. Runs took 420 to 439 s (K = 2000, 121 MB peak) and 669 to 733 s (K = 2400, 173 MB). MEASURED.

2. **The window (task 2).** W = 5 and 7 at K = 1200 move the reads by at most 47 × 10⁻¹⁸ from the filed W = 6 rows, inside every interval both ways. Eps falls with smaller windows. The logged leak (sampled at window starts) changes with the window size because the leak rises steeply near t = 2 and each grid's last sample falls at a different time. The certificate uses neither leak log. Runs took 98 to 163 s, 46 MB. MEASURED.

3. **The second seat's propagator (task 3).** At K = 2000 it meets the engine within 123 × 10⁻¹⁸ on C1, 8.9 × 10⁻¹³ on A1, and 1 × 10⁻¹⁸ on f; V² lies inside the engine's interval. Run locally on all 20 grid rows, it gives the same largest offsets as the hosted run: C1 122, A1 885,924, f 2, C2 1 (in 10⁻¹⁸). Runs took 12 to 56 s, 75 to 200 MB. MEASURED.

4. **A third route sharing no code (task 4).** I wrote `fockprop`: Rust 1.81, clippy `-D warnings` exits 0, no float type words. It uses the full Fock basis with no exchange symmetry, Taylor steps instead of Chebyshev, 2⁻⁵⁶ arithmetic with round-to-nearest, and an exact big-integer read-out in Python.
   - It meets a 2⁻²⁰⁰ reference at N ≤ 12 within 1.1 × 10⁻¹⁶.
   - At K = 1200 it agrees with cheb to 1.6 × 10⁻¹⁵ on C1, 6.2 × 10⁻¹⁵ on A1 and 3.2 × 10⁻¹⁵ on V², inside every engine interval.
   - Its exact leak at t = 2 at (-1/4, 1), 1.77 × 10⁻⁷, lies on the same steep rise as the engine's three logged leak values. Stepped back to t = 127/64, its tail weight gives 4.25 × 10⁻⁹ against the engine's 4.21 × 10⁻⁹.
   - What it cannot do: it has no certificate of its own, it ran 2 of the 10 points, and it shares the operator text of H and the observable definitions with both codes.
   - Runs took 226 to 547 s, up to 83 MB.

5. **The remainder at the other six points (task 5, exploration beside the frozen read).** C1 over first minus 1 falls by 78.09 to 80.90 from N = 729 to N = 6561 (lower bounds 77.69 to 80.80). That is near the 81 a 1/N² remainder gives and far from the 9 of 1/N. My own scripts reproduce the reader's four frozen ratios digit for digit: 77.650, 78.056, 77.787, 78.315. The N = 729 rows at delta = ±1/4 are confirmed by cheb and by `fockprop` to within 2 × 10⁻¹⁵. Runs took 28 to 37 s, 20 MB. MEASURED.

6. **Law plus first correction.** My own parser of the row's text reproduces all 50 values the read prints, with 0 off. MEASURED (closed forms only, no model run).

7. **The owning gate.** Hosted run 42091397290 at 4725b81 completed with success. It reproduced the grid receipt and the read byte for byte and met the second seat's propagator on 20 of 20 rows. MEASURED.

**Holds:**
- **H1 (low).** The README says "The remainder falls with N as 1/N²." The measured content is a ratio between two N values (77.65 to 78.31 in lower bounds), so the hold restates it as a factor near 81.
- **H2 (low).** No file at this head carries the README's separate-code figures. The hold names hosted run 42091397290, which prints them.

**What I could not check:**
- K and W stability at the other eight points. Running K = 2000 and W = 5, 7 there would settle it, at about 7 and 3 minutes per run.
- The forms themselves. I evaluated them but did not derive them. A third square N, such as 2025 at y = s/45, would separate a 1/N² remainder from a 1/N³ one.
- A rigorous bound from separate code. Only the engine's certificate bounds the block error.
- The fabric, which I did not ask. Recall answered live with count = 0 for the row name, which is an index gap, not absence.

All files are in C:/tmp/opus55/fc-read-attack-numerics-20261105/:
- FINDINGS.txt
- HOLDS.txt
- out/engine_vs_filed.hbp
- out/routes_vs_engine.hbp
- out/remainder_lane.hbp
- out/cheb_vs_filed_grid.txt
- out/growth_lane.hbp
- out/hosted_grid_integrator.hbp
- fockprop/src/main.rs
- scripts/
