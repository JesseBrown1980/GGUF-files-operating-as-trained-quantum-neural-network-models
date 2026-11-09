# polariton-stripes: the stripe phase and the averaged contrast

This folder holds one frozen, prediction-first study of the three-mode polariton model:

- `PREDICTION-STRIPE-PHASE.hbp`: 26 predictions (`STRIPES_PREDICT` rows) with their points, read rules, derivations, exposure and smoke-test records. It was written before any engine ran at a row point.
- `README.md`: this file.
- `design/`: the synthesis draft before the final critic and the second review (`draft-PREDICTION.hbp`), the two scripts that turned it into the frozen file (`apply_fixes.py`, `apply_fixes2.py`; replaying them on the draft reproduces `PREDICTION-STRIPE-PHASE.hbp` byte for byte), and `MANIFEST.sha256`, the hashes of every design-lane, judge and review scratch file named in `STRIPES_SMOKE`.
- `SHA256SUMS`: hashes of every file above.

## What it tests

In the model of `polariton/PREDICTION.hbp` (lines 3 and 4), the cos(2kx) stripe term of the density has amplitude `B = a-^dag a+`, and arg B sets where the stripes sit. The study looks at that phase in two settings:

- **The exact quantum frame map** (`polariton_first_correction`, delta = -1/4, N = 81, 729 and 6561). The rows cover the selection rules for `<B>`: it is exactly 0 at y = 0, even in y, needs at least two h insertions, and is even in t. They also cover the y^4 saturation, the displaced-Bogoliubov law for D2 with the sign and size of its first quantum correction, and the symmetric-order crossover `n*_Q = Q_W/<B>^2 - 1`.
- **The classical Wigner ensembles of twens 0.4.0.** Each sample is read as one "shot" and arg(B_W) as that shot's stripe phase. The rows cover:
  - the exact Klein symmetry of the y = 0 phase histogram, which makes its quadrants uniform;
  - the exchange balance at every y;
  - the zero mean at y = 0 and the evenness in y;
  - how the 16-sector histogram and the pinning moment `Pi = P(Re B > 0) - 1/2` flatten as y goes to 0;
  - the contrast of the average of n samples: a 1/sqrt(n) decay at y = 0, and a plateau beyond `n* = Var(B)/|E B|^2` when pinned;
  - the controls (FLIP, LOCK, MODE0, V1, V0, RN, NL);
  - the bridge `E|B_W|^2 = Q_W` to the quantum side.

8 rows are DERIVED from symmetry or algebra and 18 are CONJECTURE. A read of a frozen value at an exposed point is read-and-report: its frozen value stays in the file, but it gets no verdict (rule `EXPOSED`, see below). E17 has only such reads. Every other CONJECTURE row keeps scored reads and can read NOT_MET. One DERIVED row (E07) predicts a non-uniform histogram on purpose. At y = 0 the LOCK variant's stripe phase is tied, sample by sample, to its starting lattice point (arg B = arg c^2). Its histogram therefore follows the binomial lattice and fails the uniformity test.

## Why

Muszynski et al. (Science Advances 2026, arXiv:2407.02406v2) measured the stripe phase of a room-temperature polariton supersolid shot by shot. Over 500 shots it was uniform at high density and pinned by disorder at about 4x lower density. They also measured the contrast of the average of n shots: it falls as 1/sqrt(n) when the phases are random and levels off when they are pinned. The bridge model has direct counterparts: arg B per ensemble sample, and |mean of B over n samples|. Its h term (y) is an explicit pinning field, and at y = 0 the Hamiltonian commutes with n+ - n-, so symmetry alone makes the zero-field phase random.

## How it is read

The engines are used exactly as they stand at 4a97736: twens 0.4.0 rebuilt from source, and polariton_first_correction. The reader works in integers and exact rationals only. Histogram sectors come from integer sign and comparison tests, never from a floating-point atan2. Symmetry tests use certified bounds (Hoeffding, Bernstein, and a sign-flip bound); the other reads use 3 SE or 4 SE rules, as each row states. Each read is MET, MISS, NOT_RESOLVED or NOT_MEASURED (rule READ3). A falsifier counts only scored reads.

The runs are 15 quantum commands, 4 twens `run` points and 14 twens `dump` points (8000 calls, about 87 GB of text). The dump output is streamed into the reader and never stored. A `twens guard` check runs before every command, including the quantum ones, because the quantum engine has no guard of its own.

## Separation from PR #15

This study is separate from the frozen blind prediction `polariton-bridge/PREDICTION.hbp`:

- No row of it is reused or changed.
- Nothing under `polariton-bridge/blind/` is read, run or written.
- No engine is changed.
- Its reserved points are never run: delta = +-3/5 at every N, and y = 2/27 at N = 81, 729 and 6561, together with their neighbourhoods.

All points here use delta = 1/2 or -1/4. Some points whose values had already been filed in the repo were moved to an unexposed N at the same (delta, s = y sqrt N). The move protects the samples and the finite-N values. It does not protect the leading-order values: those depend only on (delta, s, t), and receipts at another N with the same (delta, s, t) already show them. So every read scored against a frozen value at such a triple is read-and-report (rule `EXPOSED`, row `X08`). That covers delta = 1/2 at s = 1/8 to 1 at every t, and delta = -1/4 at s = 1 (t = 1/2, 3/2, 2) and at s = 1/2 and 1/4 (t = 2). The same rule covers the second moments Q_W and E|B_W|^2 at y = 0, delta = -1/4, t = 2, which the s = 1/4 receipts reach to O(s^2). Three kinds of read are scored at every point: symmetry and identity reads; comparisons of two variants on the same samples that have no frozen value; and values fixed by the start lattice alone. Before the freeze, two reads moved to unexposed times: E13's plateau band (added at P08, t = 1) and E14's crossover ratio (moved to t = 1). The exposures, moves and demotions are listed in `STRIPES_EXPOSURE` and `STRIPES_REPAIR`.

## What it does not claim

- **It is not a model of the experiment.** The model is a closed three-mode system with no pump, no loss and no disorder. The pinning comes from an explicit field y.
- **A Wigner sample is not a single-shot image.** arg B_W, Pi, rho and Q_W are symmetric-order quantities, and n* is a symmetric-order crossover, not the paper's shot count. A real image would also carry atom shot noise.
- **"Uniform" means uniform at the stated thresholds.** The samples number 2^18 to 2^22, against the paper's 500 shots.
- **The density analog (E11) is not the same physical system at 4x density.** It holds h/J fixed while delta and t are kept in units of JN.
- **The CONJECTURE values rest on the linear (Bogoliubov) law.** Its first corrections were not computed, so the tolerances are judgments.
- **It says nothing about the frozen PR #15 prediction or its blind run, and nothing about supersolidity.**
