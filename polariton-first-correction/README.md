# The first correction of the polariton test

The frozen read is `POLARITON_FIRST_CORRECTION`, line 48 of [the prediction](../polariton/PREDICTION.hbp), pushed at `5792654` before this folder existed. It freezes C₁, A₁ and V² within 1/1000 of law plus first correction at N = 6561, t = 2, on 8 points no lane has run and 2 the second seat touched, reported apart.

**Status: the engine, the reader, the route and [the plan](PLAN.hbp) are pushed, the baseline on seen rows is filed ([receipt](RECEIPT-BASELINE.hbp), [read](READ-BASELINE.hbp), [local cost](COST-LOCAL-BASELINE.hbp)), and [the second seat's source and certificate review](reviews/opus55-source-2d77636/) at `2d77636` is applied. All three of its lanes found the engine fit to read the grid. They found the reader and the route unfit, and [each hold has a row of disposition](reviews/opus55-source-2d77636/HOLDS-APPLIED.hbp). The frozen grid runs next.**

- [`polariton_first_correction.rs`](../src/bin/polariton_first_correction.rs): the integer Chebyshev integrator on a block near |N, 0, 0⟩, with its certificate.
- [`read_first_correction.py`](read_first_correction.py): evaluates the law and first correction from the row's own text, and reads the receipts against it.
- [`route_first_correction.py`](route_first_correction.py): shares no code with the engine. It builds the Hamiltonian in the full Fock space, sums the Bessel series exactly, and drives the second seat's separate propagator, which has its own basis, one long series against the engine's windows, and its own rounding, and shares with the engine the floor square root, the width Q = 62, the operator text of H and the read-out definitions.
- [`run_stage.py`](run_stage.py): runs a stage of the plan, with rows in plan order, so the receipt is the same bytes at any parallelism.
