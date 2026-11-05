**Head checked:** `git -C C:/tmp/qnn-fc-read-wt rev-parse HEAD` printed 4725b8124d1ef19d2e22844534e3abf39543fb30, before and after my work. The worktree has no changes (`git status` is empty). Nothing ran at δ = ±3/5.

**Verdict:** the read is not refuted. My own code reproduces every number in READ-GRID.hbp from the receipts and the row. What I did refute is narrow: four small README gaps, and one line of the task text.

## What I ran (all in C:/tmp/opus55/fc-read-attack-reread-20261105/)
1. **My own evaluator** (`my_forms.py`, `eval_points.py` → `MY-FORMS.hbp`). It has its own parser and works in exact rational intervals with bounded series tails. It shares no code with read_first_correction.py, and I never opened forms_mine.py. It evaluates the row's text, F5's text, and line 39's law and predicted f.
2. **My own read** (`my_read.py` → `MY-READ.hbp`), compared field by field by `compare_read.py` → `COMPARE-READ.hbp`. Alongside it I computed stricter readings and `baseline_relative.py`.
3. **History:** git, plus read-only `gh` queries for run times and the hosted log. Three searches for runs at blind points (`scan_blind.py`, `check_synthetic.py`, `search_digits.py`), the last with a positive control.
4. **Reproduction:**
   - The reader rerun under Windows and under WSL, into `run5r/`.
   - The 7f72d2c tree exported with `git archive` into `src-7f72d2c/` and built with `cargo +1.81.0` into my own target folder.
   - `run_stage.py` on one K = 1200 row (δ = −1/4, y = 1/81, the point with the largest offsets), into `run5/`.
   - `pe_diff.py` comparing my binary with the filed one.

## What survives
**Item 1, MEASURED: the row's forms match F5.**
- The five correction numerators (w10, w11, C10, C11, C12) equal F5's as exact polynomials: 0 differing terms.
- w0, C0, A1_first, C1_first and both law forms agree at 40 of 40 random rational points, with every symbol independent.
- Line 39's law agrees with line 48's law.

**Item 1, values.** At all 10 points:

| (δ, s) | C1_first | A1_first | V²_first | C1_law | A1_law |
|---|---:|---:|---:|---:|---:|
| (1/2, 1/4) | 3143643672389569 | 15689651883244526 | 39152843304006152 | 3170341466640254 | 15757839013793647 |
| (−1/4, 1) | 22854974630007745 | 165766392955692521 | 601149147579074662 | 23347106124027265 | 167196351223932286 |

- These are 10⁻¹⁸ units; the other eight points are in FINDINGS F1b.
- Predicted f runs from 0.0032676 to 0.0109902.
- Tail bound: at most 102 terms; every tail is below 2⁻⁶³⁹ and every enclosure is narrower than 2⁻⁶³².
- F5's text gives the same values; all 168 compared values overlap.

**Item 2, MEASURED: every filed read row reproduces.**
- 117 filed rows, 1,221 fields, **0 differ**. That covers every FC_READ, FC_CONTROL and FC_CERT row, the lower-K rows, the set rows and the ten C₁ lower-bound checks.
- All four remainder ratios match (77.650 / 78.056 / 77.787 / 78.315).
- The engine prints every value rounded down, for both signs (engine line 727), so the read's widening of each interval by 2 units of 10⁻¹⁸ is safe (DERIVED).
- Stricter readings change no verdict:
  - tight intervals: 30 of 30 still inside; the worst edge is 494,394 ppb, at (−1/4, 1) on C₁;
  - the law-alone control on whole intervals: 20 of 20 still outside;
  - signs with half the read's error on ⟨A⟩: 10 of 10.
- All 50 cells of the stage README's table, and every summary number in it, match my values.

**Item 4, MEASURED: the prediction came first.**
- Line 48 entered at 5792654. GitHub's own merge commit 4693097 has 5792654 as a parent at 15:02:41 UTC. Line 48 is byte-identical at head; its sha256 with the newline equals the plan's `row_sha256`.
- The 20 grid rows are byte-identical from f303c35 to head.
- The hosted run at 7f72d2c (42084476668) passed at 18:39:53Z, before the 18:41 start.
- A README commit that GitHub merged at 18:31:19 UTC says "No grid point has run".
- No observable at a blind point turned up before the grid. Three independent searches:
  - **By fields:** the only matches in the repo are the 16 plan rows.
  - **By markers:** 2,586 engine-format rows in the review lanes are all marked synthetic, with 0 unmarked. In the local worktrees, the only unmarked ones are the grid receipt itself, written at 19:02:49Z.
  - **By digits:** none of the receipt's 183 long values appears in 8,913 files. The positive control does hit.
- The independent review lane did run the engine's `rows` and `bessel` modes at all 20 grid runs, 15:57 to 16:09Z. Those modes print only the Hamiltonian block's c, E, norm(B) and Bessel tables. The filed review discloses this (its F5 and F7).

**Item 5, MEASURED: byte for byte.**
- **Reader:** WSL output is identical to READ-GRID.hbp (sha256 ae2522617c75…). Windows output is identical once its 162 CRs are removed; Windows writes CRLF and git stores LF. The author's first copy (READ-GRID-FIRST.hbp) is byte-identical, with 0 CRs.
- **Hosted:** run 42091397290 at 4725b81 passed at 19:42:47Z. It re-ran all 20 grid rows and compared both the receipt and the read.
- **Engine:** my 7f72d2c build reproduced the δ = −1/4, y = 1/81, K = 1200 row byte for byte (sha256 a1dd0090…, 129 s).
- **Binary:** mine is d1cbdc72…, the filed one is d9718bbe…. Both are 286,720 bytes and 23 bytes differ. All 23 sit in link timestamps and the debug GUID; 0 differ in code or data. So the filed binary runs 7f72d2c's code.

## What is refuted
- **Task text:** 4725b81 does not add "only" the grid, the read and README text. Through merge 64e198c it also brings a renamed step in `.github/workflows/polariton.yml` (from adaf3e7) and the root README's scope line (from 77addcf). The engine, plan, reader and baseline are unchanged (MEASURED).
- **Item 3, readings looser than the row's words** (MEASURED; no verdict changes):
  - "Expanding L converges" is read as the two certified intervals overlapping. That test fails only if a certificate is wrong. The values themselves agree within 3 (C₁) and 29 (A₁) units of 10⁻¹⁸. Epsilon still rises with K at 8 of 10 points, as the README says.
  - "Below the gap" compares e6561 with the gap measured in N = 729 units. In N = 6561 units it still passes, by at least 106×.
  - e729 prints as 0 ppb; the actual bound is 26 to 55 parts per trillion. Only the print is rounded down, not the decision.
  - "Within 10⁻⁵ relative" (in READ-BASELINE) has 8 C₂ values over 10⁻⁵. Each is within one 10⁻⁹ print step of the old receipt.
- **Item 3, read elsewhere:**
  - The engine-side clauses (outward norms, leaking shells, parity, no charge sector) are left to the review and the hosted steps.
  - Integer-only, Rust 1.81 and clippy are read by the hosted runs; `float_used=0` on 20 of 20 rows; no f32/f64 in the engine source.
- **Item 3, stricter than the words:** signs carry certified errors, and a MET requires the whole certified interval inside.
- **My own guess was wrong:** I first put the binary hash difference down to embedded source paths. It is the link metadata.

## Holds (all on polariton-first-correction/README.md, all low)
- **H1:** the "Separate code" paragraph's two route files exist only in C:/tmp/qnn-fc-out/grid. The hosted run prints identical rows, but its log expires. Cite both hashes and the hosted run; file the two files.
- **H2:** state the N = 729 numerical error (2.6 to 5.5 × 10⁻¹¹), which the read prints as `e729_ppb=0`. The row's clause covers both N.
- **H3:** the largest C₁ half width is 1.4 × 10⁻⁸ at K = 1600 but 1.5 × 10⁻⁸ at K = 1200; the sentence names both K.
- **H4:** beside "8 points no lane has run", state the review's `rows`/`bessel` runs at all 20 grid runs (15:57 to 16:09Z).

## Could not check (CANNOT_SEE)
- That the read "was run once": no log of attempts exists.
- F5's derivation, and how rigorous the engine's certificate is: both taken from their own lanes.
- Runs outside the folders I searched, on other disks, other machines or deleted outputs; and GitHub push events.
- Commit times are self-reported; mtimes are local filesystem times.

Files are in C:/tmp/opus55/fc-read-attack-reread-20261105/:
- FINDINGS.txt
- HOLDS.txt
