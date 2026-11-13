# November 13, 2026 — GPT-6 direct GGUF weight-space surgery (CPU, exploratory)

**Status:** Exact hosted experiment **PASS**; proposed scientific acceptance **IN REVIEW**. This report was written after the results. [Draft PR #31](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/pull/31) is stacked on draft #30, which is stacked on draft #28. The original 72-file and 36-file source manifests and the synthetic 6,561-head GGUF remain unchanged.

## Why edit the weights?

The operator's target is weight-space programming: direct model surgery by an LLM, without a gradient update or fitting loop for the edited weights, following [*Sparks of Weight-Space Programming*](https://rikiyat.github.io/blog/weight-space-programming/) (Takehi, Teoh, Zhang, Khattab; November 2, 2026). This experiment edits the **actual compact signed integer correction vectors in a GGUF v3 shared-graft model**, then cold-reloads the rewritten model and compares outputs. It is a software model-composition experiment, not a hardware quantum device or 6,561 independently trained circuits.

**Training-only inspection:** Hosted run [43462529010](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/actions/runs/43462529010) printed four parent vectors and all 24 leaf vectors using only 24 QNN training and 12 QNN validation blobs; no test input was read at inspection time. Parent weights for Rust and Python were identical, so the old parent-class readout cannot discriminate those two by its class-conditional scoring.

## Explicit GPT-6 edit — frozen before evaluating the edited model

The old and new vectors have exactly three signed integer coordinates, representing multiplicative adjustments to whitespace, alphabetic and other-byte frequency families. The patch was frozen in [WEIGHT-SURGERY-EDIT-FREEZE-20261113.hbp](WEIGHT-SURGERY-EDIT-FREEZE-20261113.hbp), commit `acceb54be7a10c4a6a8b3ed0b7531e6b19a87cb3`, before implementing the evaluation code.

| Parent | Original learned weights | GPT-6-authored weights | Edited integer coordinates |
|---|---|---|---:|
| Rust | `[1, 0, -1]` | `[0, 1, -1]` | 2 |
| Python | `[1, 0, -1]` | `[2, -1, -1]` | 2 |
| Markdown | `[0, 0, -2]` | unchanged | 0 |
| HBP | `[-2, 2, 1]` | unchanged | 0 |

The shared backbone, all **24** leaf corrections, model byte format, parent-address mapping and model fitting remain fixed. The edited four integer parameters encode a *hypothesis*: Rust favors letters relative to whitespace, and Python favors whitespace relatively more, based on the observed training/validation families. This is not a learned optimum.

## The actual cold-reloaded GGUF artifacts

| Model | Serialized bytes | SHA-256 |
|---|---:|---|
| Unedited | 10,304 | `2dd411497261539d267c4cff8d67182896bfb3e65cf525592921d019e2adca99` |
| **GPT-6 direct edit** | 10,304 | `8f75199ccc8ef25ec70f2c750cdfa7d78f6fb81131ae4a5211b1366fc7492563` |
| Shuffled edited parent assignments (negative control) | 10,304 | `c19f12e436f4d3eb3d57ee7e8285767fa06f4a78c93c7249d5ffeabc692e59fd` |
| Parent edit ablation to zero | 10,304 | `eec38e97dd2d102bf43e8b0d3fb2fad413c9f63e65ecb23e7507481ab290e6f4` |

The binary writes these GGUF files to the workflow artifact and reopens each one to check that the model's parent vectors, leaf corrections, backbone and all individual classifications agree with the in-memory originals. Tampering with GGUF magic is rejected. The synthetic 6,561-head checkpoint is still pinned to SHA-256 `606c4d8478b8dbd72dfda0dad6c6ef1895c081a7cd5d5bb6c363525f57b941b2`.

## Measured classifications — each out of 36 existing known test files

| Classifier | Original QNN 256 B | Original QNN 1,024 B | Other repositories 256 B | Other repositories 1,024 B |
|---|---:|---:|---:|---:|
| Majority | 9 | 9 | 9 | 9 |
| Byte-unigram Naive Bayes | 21 | **34** | 19 | **28** |
| Byte-bigram Naive Bayes | **22** | 32 | 17 | 26 |
| **Original real-trained GGUF** | 18 | 23 | 18 | 20 |
| **GPT-6 manual GGUF edit** | **20** | 20 | 16 | 17 |
| Shuffled weight edit | 17 | 16 | 16 | 19 |
| Rust/Python parent weights ablated to zero | 17 | 19 | 17 | 19 |
| Original synthetic 6,561-head GGUF transfer | 13 | 20 | 17 | 17 |

**Primary observation:** Manual direct weight editing changed the actual GGUF and its classifications while preserving the model byte size. Relative to unedited, the edit yielded **+2, −3, −2 and −3** correct classifications across the four corpus/prefix combinations. On the 1,024-byte cross-repository corpus, both shuffled and ablated controls outperformed the manual edit (19 vs 17). The hand-authored correction **does not generalize** across these existing tests.

This result does not contradict Takehi et al.: their reported improvement repaired a different, more structured failure mode in a much larger model, with analysis and sometimes test feedback. Our three-family parent score cannot represent most Rust-versus-Python syntax distinctions, and the current four-class readout ignores leaf-level correction scores.

## Verification and limitations

The exact Rust 1.81 CI checked no floating-point arithmetic, no GPU, no gradient optimizer, source and freeze provenance, cold round trips and 32 evaluated method/corpus/prefix rows, 1,152 individual predictions, and 128 confusion-matrix rows. [Hosted exact replay 43463383625](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/actions/runs/43463383625) passed, including actual saved GGUF artifacts; a second hosted pull-request replay also passed [43463397317](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/actions/runs/43463397317).

**Both evaluation sets had already been seen in previous projects**, and the selected edit was frozen before these new predictions but after earlier benchmark summaries were known. So this is **exploratory weight-space programming evidence**, not an independent blind trial, and cannot establish statistically reliable gains. The experiment obeys its one-patch-only constraint: no post hoc retuning, no second patch to rescue negative results.

## Next hypothesis: edit the weights that the class readout actually uses

The 24 leaf codices *are learned and distinct* but currently do not affect the parent-class decision. A new experiment could implement a **frozen class-conditional readout from all leaf likelihoods**, then let an LLM directly edit a small number of those leaf correction weights rather than adding many empty addresses. Compare parent-only, leaf-readout unedited, leaf-readout LLM-edited, shuffled, ablated and ordinary unigram/bigram baselines. Enforce a byte-cost and CPU-cost budget, exact GGUF cold replay and unchanged training data.

A **new, independently frozen and previously unevaluated corpus** is necessary before describing that next intervention as blind evidence. Until then, keep results and failures in full.
