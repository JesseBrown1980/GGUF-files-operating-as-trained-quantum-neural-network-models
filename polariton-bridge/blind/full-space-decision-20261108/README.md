# The full-space decision of November 8, 2026

This folder files the owner's decision on the quantum shell-block gate (`BRIDGE_QUANTUM_GATE_BLOCK`, `PREDICTION.hbp` line 438), with the gate record it rests on. The blind run's local driver wrote both on November 8, 2026. Neither file holds a value the bridge reader scores: the gate rows carry `tail_max` and the C1 and A1 differences between shell sizes as fractions of their widths.

- [`GATE-BLOCK.hbp`](GATE-BLOCK.hbp), sha256 `7aa65299…`: the gate over the five N = 6561, δ = −3/5 points. Verdict FAIL at 3 of 5 (`tail_max_e18` above 10⁸ at y = 2/243, 4/243 and 2/27), `fallback_K=N_needed=1`.
- [`DECISION-FALLBACK-20261108.hbp`](DECISION-FALLBACK-20261108.hbp), sha256 `7cd173f3…`: `by=OP-JESSE`. The choice is to run those 3 points at K = N, and it **releases the owner's H2 hold of 2026-11-06 for these three points**. Their rows are read from the K = N runs (stream mode, H4). The two points that passed the gate (y = 0 and y = 1/243) are read from their shell blocks.

Authorizations for the eight full-space launches (orders 406–413 of plan `3eca4df9`):
- orders 406–410 (N = 6561, δ = +3/5): the owner approved the full space for these points on 2026-11-05;
- orders 411–413 (N = 6561, δ = −3/5): this decision.

Every output sha256 matches its launch row and its sidecar. The outputs stay sealed until the reader is frozen and reviewed.
