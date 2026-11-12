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

## Builder stage 2 — complete frozen row/obligation coverage, still READ-DISABLED (November 12, 2026)

This stage extends the accepted preflight without opening **any** reserved-point values or changing the original 873-row prediction, F/G amendments, jets, PR #15's sealed hashes, or the operator's E4R counts. It is an **executable synthetic reader contract**, not a completed real-data reader or a freeze authorizing blind reads.

- [`gpt6_clause_reader.py`](gpt6_clause_reader.py) enumerates **all 352 unique frozen `BRIDGE_AT` rows**, verifies exactly **28 points**, and preserves every clause from `applies` and `read_and_report`. It emits a complete in-memory contract for **4,001 clause slots** and **7,040 comparison slots** (`352 × 4 classical maps × 5 observables`), plus **239 supplemental predictions**: 24 trajectory, 16 trajectory scaling, 60 quantum-ensemble, 60 paired, 16 ensemble scaling, 29 additional ensemble, 24 diagnostics and 10 matched pairs. It does not silently turn `NOT_MEASURED` into `MET`. Every value-bearing verdict goes through the original FC02 exact rational rule, with all five named nonnegative errors, identity/provenance gates and E_PAIR's two precision gates. All observed-looking synthetic verdicts are generated entirely in memory.
- [`gpt6_ensemble_moments.py`](gpt6_ensemble_moments.py) independently assembles **common-prefix, integer-fixed-point** sums/squares, exact covariance of Re Z and X, nonnegative 3SE variances, mandatory round-bound batches, and `V2` as a **ratio of means**, never an average of per-sample ratios. For each VNC batch, `xnc` ordering is mandatory; V1/V0 require `xw`. A control-variate read requires independently proven expectations of its linear control: the code refuses to set them to zero by assumption. The source must be separately authenticated by its file hashes before this interface can consume it. `3SE` is a sampling estimate, not a deterministic uncertainty guarantee; positive C1 lower-bound failure leaves V2 undefined.
- [`gpt6_source_contracts.py`](gpt6_source_contracts.py) implements pure in-memory authentication gates for **quantum planned full-space**, the **trajectory bound pair**, and the source-native **jetread** stream including `JR_OBS`, `JR_SIGN`, `JR_PAIR`, `JR_CONS` and `JR_GATES`. `K=N` alone is **not** authorization for the planned `N=6561, δ=-3/5` shell/fallback route; that path stays **HOLD**. Jet `JET_NOT_RESOLVED` remains unresolved and cannot be converted to a success.
- Hosted preflight now tests the full 352-row contract, 20 distinct applicable/reporting clause families, **100 synthetic verdicts** (MET, MISS, NOT_RESOLVED, UNDEFINED, NOT_MEASURED), **141 clause-level planted faults**, ensemble covariance/ratio cases, quantum/trajectory/jet source sabotage, and failure of `--read` on every component. The indexed no-float/no-true-division scan covers every reader Python file.

**Contract SHA-256 (stage 2, synthetic, not a read):** `f45531773193df1fbb7c28cb1974307132974ce53c1dc55536778bac42d61695`; this hash identifies the frozen-row/slot inventory from the existing prediction and contains no actual output values.

**Still required to call this a complete reader:** independently authenticate every one of the 347 ensemble launch files and eight full-space output seals against the launch receipts, obtain independently proved **per-point control-variate expectations** and validate the covariance/rounding treatment for each observable, implement every trajectory/control/clock/9-versus-81/nonshell-clause-specific calculation (not merely catalogue them), reconcile all jet source gates and run hashes, and produce substantive synthetic sabotage results on every full clause before the **independent local reviewer** accepts the exact final head. The current files intentionally expose no loader for the reserved outputs. **Do not merge, unblind, or change draft status on the strength of this stage.**

## Mandatory remaining steps — HOLD, before freeze

1. **Raw data adapter:** independently parse `POLARITON_FIRST_CORRECTION_READ` with certified `eps_poly`, `eps_round`, `eps_tail` and `K=N` fallbacks, `TRAJ_BOUND/TRAJ_OBS_BOUND` with trajectory output values, all `TWB/TWB_ROUND/TWB_PAIR/TWB_PAIR_ROUND/TWB_NL` rows and the already sealed jet `JR_OBS/JR_PAIR/JR_GATES` rows. The adapter must use only the published source-format definitions, not any blind output.
2. **Ensemble assembly:** all 347 launches, exact batch source hash and sample prefix, source-recomputed means, control-variate estimators and **covariance of paired sums** (not unpaired error propagation). For V2, calculate from ensemble means (never average individual ratios). Use 3SE with a clear treatment of the nonlinear `abs` and ratio. Apply F counts and G memo conditions.
3. **Error budget:** keep `3SE`, step-halving `e_int`, per-sample fixed-point `e_round`, quantum certified `e_q`, and block truncation `e_trunc` separate on each row. Do not silently replace a frozen control-variate reading by a plain estimator. `C_MODE0` is a rigorous bound expected to be NOT_RESOLVED from `t=1/2`; never force MET from design expectations.
4. **Complete clause table:** cover all 352 `BRIDGE_AT` rows and the frozen trajectory, clock, pair, 9-versus-81 diagnostic, controls and zero-field branches; include `UNDEFINED` and `NOT_MEASURED` reasons, and preserve every failure. A synthetic error injection must force MET/MISS/NOT_RESOLVED correctly for *each* applicable clause, including deliberate missing rows and duplicate hashes.
5. **Freeze and review before read:** write a second commit/receipt sealing the complete reader source SHA and synthetic CI traces; have independent local seat review at that exact head; only then run once on already hashed blind outputs and seal `READ.hbp`. PR #15 stays draft through its final scientific review.

## Safety properties

The builder has **not** opened the values of runs 406–413, the 347 ensemble outputs or reserved-point jets; only frozen published prediction text, source schemas, and historical public read-method reports were consulted. The PR targets PR #15's branch, not `main`. This check-in does **not** represent that the blind bridge has passed or failed its predictions.

**Review verdict for this commit: PRE-READ CORE ONLY; the final reader is NOT FROZEN.**
