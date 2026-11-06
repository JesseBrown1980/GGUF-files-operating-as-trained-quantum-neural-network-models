# Independent replay of a historical 104-minute polariton job

Date: 2026-11-06. No repository writes or frozen-run changes.

## Historical source

- Repository: https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models
- Hosted job: https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/actions/runs/42071602272 (completed in ~104.6 minutes on 2026-11-05).
- Filed baseline observations: `polariton/RECEIPT.hbp` (`POLARITON_QUENCH`, N=6561, y=0).
- Filed local per-case baseline times: `polariton/TIMING-LOCAL-20261104.hbp`.
- Original model source: `src/bin/polariton_three_mode.rs`, `Space::sector`, `build`, `read`, `advance`.

## Scope and mathematical method

This is a reproduction of **42 readings from the historical hour-plus job**, not the entire multi-stage job. It covers seven deltas (-2, -1, -1/2, 0, 1/2, 1, 2) at t=(1,2,3,4,6,8), each with three observables (pair population, C1, C2). The remaining stages of the original job were **not reproduced**.

At y=0, Q=n_+ - n_- commutes with H. The initial |N,0,0> has Q=0, so all dynamics stay in the sector with basis |j,j,N-2j>, for j=0..floor(N/2). At N=6561 this sector contains 3,281 states. The total symmetric three-mode Fock space has 21,533,203 states; its exchange-even sector has 10,768,242, which is the comparison dimension cited in the earlier Use report.

Instead of reproducing each fixed-point integer time step, the independent code rebuilds the *same real-valued Hamiltonian formula*, diagonalizes the resulting symmetric tridiagonal sector matrix with SciPy, and evaluates exp(-it H)|0> for the six read times. It then computes the three observables from the resulting amplitudes.

The reconstruction is analytic but **the numerical implementation uses double precision**. Its results cannot be expected to be byte-identical to the original Rust integer-shear integrator, and this test is not an exact-arithmetic certificate for the complete state.

## Measurements

| Item | Result |
|---|---:|
| Independent N=6561 detunings | 7 |
| Times per detuning | 6 |
| Independent readings | 42 |
| Independent observable comparisons | 126 |
| Max relative pair-population discrepancy | 1.202e-8 |
| Max absolute C1 discrepancy | 0.98491 ppm |
| Max absolute C2 discrepancy | 0.99168 ppm |
| First spectral measurement (7 detunings, one process) | 9.74 s |
| Reproducible standalone replay on same session, warm code/data | 6.115 s |
| Historical local Rust time for those seven detunings | 135.196 s |
| Relative time, different machines/environments | 22.1x (6.115 s run); ~13.9x (first 9.74 s run) |

The original hosted job spent 363.51 seconds on the whole quench stage, but that stage includes many other N and detunings. Thus 363.51 seconds must **not** be used as the denominator for the 42 readings tested here. The 135.196-second historical local comparison is the exact seven-condition subset, albeit on a different machine.

Acceptance criteria: relative jbar discrepancy <2e-8 at every row, |difference| <1 ppm for C1 and C2 at every row, total norm discrepancy <1e-12. All 126 comparisons PASS. See the CSV for every archived and independently recomputed value.

## Conclusions and limits

- **Supported:** The existing conservation-law sector and a direct spectral jump recover the historical zero-field N=6561 outputs without simulating the many small time steps. The independent implementation reproduces late-time as well as early-time results.
- **Not supported by this test:** A claim that an arbitrary 4D Yang-Mills transfer operator, nonlinear ensemble, or full non-zero-field polariton engine can be accelerated to seconds. No general-purpose NTT shortcut was used here: the sector Hamiltonian is tridiagonal, not a translation-invariant ring convolution.
- **Next acceptance step for production substitution:** For the declared blind-run points, verify the exact Q conservation law in the final engine, byte-identical full-versus-sector output at approved small and representative points, sabotages for broken Q symmetry and forbidden y != 0, and hosted CI on the final head. Preserve frozen predictions and add a documented correction. D1 is approved subject to those gates.

## Reproduction

`python3 polariton_6561_independent_replay.py`

Requires Python with numpy, scipy and threadpoolctl. Emits 42 comparison rows in `polariton_6561_independent_replay.csv` and prints the measured time. The CSV digest and independent local audit metadata are archived beside this report.
