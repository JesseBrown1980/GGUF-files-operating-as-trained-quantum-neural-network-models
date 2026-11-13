# November 13, 2026 — QNN cross-repository file-type transfer (research result, draft)

**Status:** Hosted exact replay **PASS**; scientific acceptance **IN REVIEW**. This report was written **after** the cross-repository results and does not change the frozen selection or predictions.

- [Original prospective freeze](CROSSREPO-PREDICTION.hbp), committed as `b36eef810efceba2b65f59d9aec689c7f9ba9adb` **before evaluator code**.
- [Frozen 36-file manifest](CROSSREPO-HOLDOUT.tsv), committed as `e01cb29074b43c5042464d5cd2f54619d3bcb99e`.
- [Hosted full gate](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/actions/runs/43460524759), after the no-warning lint and source checks; an earlier passing gate was [43460069576](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/actions/runs/43460069576).
- Original #28 benchmark and its 72-file training/validation/held-out split **unchanged**.

## Fixed task

Classify unseen 256-byte and 1,024-byte file prefixes as Rust, Python, Markdown or HBP. Train the models exclusively on the **original QNN repository** (24 source files for fitting, 12 for calibration). Predict on **36 other repository files**, six of each class from the finite S₃ Yang–Mills repository and three of each class from the 4D Yang–Mills repository. All source repositories, Git commits, exact Git blob SHAs, paths and byte lengths are fixed in the manifest. The same 8 classifier arms and synthetic 6,561-head checkpoint from #28 are retained; no model is fitted on the external 36 labels.

These two held-out repositories have the **same owner and related mathematical domains**. This is an improvement over a single-repo split, but it is **not** a claim of independent third-party transfer.

## Observed correct classifications (36 external files)

| Arm | 256-byte correct | 1,024-byte correct | Serialized model bytes |
|---|---:|---:|---:|
| Majority | 9 | 9 | 5 |
| Three-family Naive Bayes | 17 | 18 | 56 |
| Byte-unigram Naive Bayes | **19** | **28** | **4,104** |
| Byte-centroid | 18 | 24 | 4,104 |
| Byte-bigram Naive Bayes | 17 | 26 | 16,972 |
| Real-file-trained parent GGUF | 18 | 20 | 10,176 |
| Real-file-trained parent/leaf GGUF | 18 | 20 | 10,304 |
| Original synthetically trained 6,561-head GGUF with QNN validation-label map | 17 | 17 | 49,169 |

The first 256-byte comparison is close (unigram 19 vs parent router 18); at 1,024 bytes the byte-unigram model is eight correct predictions ahead (28 vs 20). Under the **pre-declared comparison** at both prefixes, verdict: `NAIVE_BAYES_STRONGER_ON_THIS_CORPUS`.

### Per-repository results at 1,024 bytes

| Arm | Finite S₃ (24 files) | 4D Yang–Mills (12 files) |
|---|---:|---:|
| Byte unigram | 17 | 11 |
| Byte bigram | 14 | 12 |
| Parent GGUF | 13 | 7 |
| Full-tree GGUF | 13 | 7 |
| Synthetic GGUF transferred | 12 | 5 |

### Context-matched and paired checks

The GGUF router uses recent decoded bytes for parent selection. As a control, all Bayesian models were additionally measured using **only the latest 256 bytes** from each prefix; this was predeclared in the cross-repository prediction.

| Context-matched control | At 256-byte prefix | Latest 256 at 1,024-byte prefix |
|---|---:|---:|
| Three-family Naive Bayes | 17 | 18 |
| Byte-unigram Naive Bayes | 19 | **26** |
| Byte-bigram Naive Bayes | 17 | **27** |
| GGUF parent route | 18 | 20 |

The two classifiers' correct sets differ: at 256 bytes, the unigram alone gets **2**, GGUF alone **1**, and both **17**. At 1,024 bytes, unigram alone gets **9**, GGUF alone **1**, both **19**. Neither arm sees any external test labels during fitting or model selection.

## Verification and boundaries

The GitHub gate uses Rust 1.81, strict Clippy, pinned source commits, byte-verified Git blobs and manifest-source equality. It independently loads **saved** baseline tables, GGUF parent/tree models and the original hash-pinned synthetic checkpoint, and recomputes every external prediction. It records 16 result rows, 64 class confusion rows, 576 individual predictions and 6 equal-context rows, with model checksums and a retained artifact. It does not certify out-of-domain language understanding or quantum performance.

Model bytes are serialized file sizes, **excluding temporary scoring caches**, cold-load time and any model training expenditure. Timings are ten hot inference passes, excluding file I/O. There are only 36 held-out files, selected deterministically rather than randomly, with possible shared formatting conventions and near-duplicates between related repositories. No statistical universal superiority claim is warranted.

## Practical next gate — stronger QNN learning rather than more addresses

The **full leaf tree offers no classification accuracy advantage** over its parent-only router in either benchmark. Address capacity (6,561 leaves) is therefore not the present limiting metric.

A useful separately frozen next model should supply a genuinely supervised **class-conditional readout**, using class evidence from the specialist network rather than equating the chosen parent route with a class label. Record actual class training labels, parameter count and serialized bytes; use frozen untouched development files for parameter fitting; benchmark against byte-unigram and bigram baselines at **equal effective context**. Include a shuffled learned-head assignment, a parent-only arm and a no-graft generalist as controls.

**Avoid reusing these already-read 36 external files as a new blind validation set.** A future changed model needs a further independently frozen unseen holdout, with all underperforming outcomes retained. The two 2026-11-13 benchmarks are evidence, not optimization targets for post-hoc tuning.
