# GPT-6 polariton bridge reader — PRE-READ BUILD, NOT ACCEPTED FOR BLIND OUTPUTS

2026-11-09. Builder: GPT-6 independent cloud seat. Independent reviewer: local Opus 5.5 seat. **Scope:** QNN PR #15, issue #9; DO NOT READ ANY RESERVED-POINT OUTPUT until the final reader source and tests are frozen and reviewed. This branch starts at PR #15 head `4a97736d0e5a7f4b479308d49039aecc57bdb281`; it does not modify the prediction or any run receipt.

## Freeze inputs

- `polariton-bridge/PREDICTION.hbp`, 873 HBP rows, sha256 `fadd84122e820cc03e9a4d6d5dd47fe7118ab4b16e1d4db93a601fb44c90b892` (the first freeze in PR #15).
- `AMENDMENT-2026-11-06-F-SAMPLING.hbp` changes the E4R `M_VNC` sample counts on the listed `BRIDGE_AMENDED_AT` lines **only**, never predicted values, bands or tolerances.
- `AMENDMENT-2026-11-06-G-MEMO.hbp` changes the memo engine and batch provenance **without** changing the sampled sums. `CORRECTIONS.hbp` preserves the frozen rows and identifies postfreeze reading details.
- 28 distinct `BRIDGE_POINT` points, 352 `BRIDGE_AT` records, 60 quantum comparisons, 60 pair predictions, 29 extra, 16 scaling, 24 trajectory, 24 diagnostics (may reference shared points). No arbitrary reduction of scope is permitted.

**Frozen source authentication (stage-one review correction):** every source is checked against a full published SHA-256 rather than merely checking a field: PREDICTION `fadd8412…`, F sampling `60c403d3…`, G memo `9ca167ef…`, CORRECTIONS `9bfdd27d…`, and HOLDS-APPLIED `b9cf4641…` (full constants in `gpt6_read_core.py`). The HOLDS file's Git blob `954e8ee3…` and the `SHA256SUMS` entries provide additional independent checks. The original file bytes are unchanged.

## What is implemented

`gpt6_read_core.py` **does not accept or open measurement files**. Its only CLI modes are `--preflight` (verify frozen HBP, exact precedence, changed count rows and G memo source) and `--selftest` (synthetic positive and planted-fault checks). It contains the exact frozen three-way rule and a reduced-integer rational arithmetic implementation:

```text
MET             iff |d| + e <= tol
MISS            iff |d| - e > tol
NOT_RESOLVED    otherwise
UNDEFINED       when mathematically undefined
NOT_MEASURED    only with an explicit missing-source reason in the final reader
e = 3*SE + e_int + e_round + e_q + e_trunc
```

Every term must be nonnegative, named, and independently justified. This stage implements exact 3-SE with fixed-point signed-integer sums and squared sums, mandatory **shared sample prefix** for `E_PAIR`, and a rational conversion of the paired `TWB_PAIR` sum: `P = 2N^3/(N-1) * mean(d)/2^40`. It will **refuse** separate V1 and VNC sums as a substitute for the paired source.

**Independent stage-one review changes:** The core now requires present and non-null identity fields, canonical ASCII number tokens (no underscores or mixed signs), exactly five named error components (`3SE`, `e_int`, `e_round`, `e_q`, `e_trunc`), a matching `TWB_PAIR_ROUND` source per batch, and both frozen E_PAIR precision conditions: `3SE <= |P|/100` and `3.29SE <= |P|/100` before any MET. The paired difference's normalization is proved by [twens source: `obs` and `PAIRS`](../engines/ensemble/src/main.rs): `xw = X_W/N²` and `xnc = X_NC/N²` at 2⁴⁰, while `ps.d` is the sample-wise `V1xw-VNCxnc`; therefore `P = 2N³/(N−1) · mean(d)/2⁴⁰`, exactly as the reader computes. The hosted test exercises 26 core sabotage cases and 9 raw-schema sabotage cases, and a separate Python AST gate checks tracked file modes from the Git index and forbids true division, float constants, and unsafe numeric imports.

**Quantum route remains an explicit blocker:** the `HOLDS-APPLIED.hbp` `requirements_H1` concerns diagnostic sampling, not the later shell `K_shell+411` / point-mode / fallback conditions mentioned in the independent review. Those labels must be reconciled with the actual pinned quantum-route plan before the full reader accepts any shell result. In particular, `K=N` printed by an engine is not, by itself, proof that a **fallback** was authorized. The final adapter must prove from sealed launch and owner authorization whether a run was planned full space or an allowed fallback. Until then, quantum-route acceptance is **HOLD**.

The self-test deliberately catches corrupted headers, altered sampling, wrong pairing, missing/overlapping batches, a negative sampled variance, altered seeds, undefined values and tolerance boundaries. Hosted CI must run before acceptance. It is NOT a complete reader.

## Mandatory remaining steps — HOLD, before freeze

1. **Raw data adapter:** independently parse `POLARITON_FIRST_CORRECTION_READ` with certified `eps_poly`, `eps_round`, `eps_tail` and `K=N` fallbacks, `TRAJ_BOUND/TRAJ_OBS_BOUND` with trajectory output values, all `TWB/TWB_ROUND/TWB_PAIR/TWB_PAIR_ROUND/TWB_NL` rows and the already sealed jet `JR_OBS/JR_PAIR/JR_GATES` rows. The adapter must use only the published source-format definitions, not any blind output.
2. **Ensemble assembly:** all 347 launches, exact batch source hash and sample prefix, source-recomputed means, control-variate estimators and **covariance of paired sums** (not unpaired error propagation). For V2, calculate from ensemble means (never average individual ratios). Use 3SE with a clear treatment of the nonlinear `abs` and ratio. Apply F counts and G memo conditions.
3. **Error budget:** keep `3SE`, step-halving `e_int`, per-sample fixed-point `e_round`, quantum certified `e_q`, and block truncation `e_trunc` separate on each row. Do not silently replace a frozen control-variate reading by a plain estimator. `C_MODE0` is a rigorous bound expected to be NOT_RESOLVED from `t=1/2`; never force MET from design expectations.
4. **Complete clause table:** cover all 352 `BRIDGE_AT` rows and the frozen trajectory, clock, pair, 9-versus-81 diagnostic, controls and zero-field branches; include `UNDEFINED` and `NOT_MEASURED` reasons, and preserve every failure. A synthetic error injection must force MET/MISS/NOT_RESOLVED correctly for *each* applicable clause, including deliberate missing rows and duplicate hashes.
5. **Freeze and review before read:** write a second commit/receipt sealing the complete reader source SHA and synthetic CI traces; have independent local seat review at that exact head; only then run once on already hashed blind outputs and seal `READ.hbp`. PR #15 stays draft through its final scientific review.

## Safety properties

The builder has **not** opened the values of runs 406–413, the 347 ensemble outputs or reserved-point jets; only frozen published prediction text, source schemas, and historical public read-method reports were consulted. The PR targets PR #15's branch, not `main`. This check-in does **not** represent that the blind bridge has passed or failed its predictions.

**Review verdict for this commit: PRE-READ CORE ONLY; the final reader is NOT FROZEN.**
