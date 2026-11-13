# Full 6,561-head shared GGUF table

This is the follow-up to the [81×81 shared-backbone model](README.md) and [PR #25](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/pull/25). This version **actually populates all 81 parent correction heads and all 6,561 leaf correction heads**, not merely allocating empty addresses.

The model remains a shared conditional-byte predictor, not 6,561 fully independent byte function tables and not 6,561 independent LLMs or simulated quantum processors. Each leaf has **three fitted signed integer correction weights**; every parent also has three. A single 256×256 backbone holds the common byte-transition counts and is serialized once.

## Verified synthetic 6,561-head measurement — November 13, 2026

The [complete hosted run](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/actions/runs/43359606249) succeeded on **synthetic fixture V2**. The deterministic generator creates different parent-level distributions so the hierarchical router must change both parents and leaves. The original fixture V1 had filled all slots but never changed parents; that deficiency is retained explicitly in [POSTCHECK.hbp](FULL6561-POSTCHECK.hbp), rather than obscured by the corrected fixture.

All 81 parents and all 6,561 leaf slots were fitted and populated; 5,988 of the leaf correction triples were nonzero. Shared count model trained from 6,718,464 synthetic bytes, with an additional 3,359,232 validation bytes and 3,359,232 test bytes. Every configuration used the same synthetic held-out bytes, source SHA-256 `bdb209e56732eb6ec7ae98d31ae0995d9a4847b640f28a4814fa6a1a536b9e2f`.

| Case | GGUF bytes | Arithmetic stream bytes | Total cold transfer | Parent switches | All switches |
|---|---:|---:|---:|---:|---:|
| One shared base | 15,904 | 2,058,446 | 2,074,350 | 0 | 0 |
| 81 trained parents only | 16,256 | 1,972,807 | **1,989,063** | 2,496 | 2,496 |
| All 6,561 trained leaves | 49,088 | 1,971,762 | 2,020,850 | 2,496 | 3,849 |
| All heads, zero corrections | 49,088 | 2,058,446 | 2,107,534 | 0 | 0 |
| All heads, shuffled leaf corrections | 49,088 | 1,971,151 | 2,020,239 | 2,496 | 3,225 |

**The full tree worked and replayed exactly**, including all 13,122 routing decisions and byte-identical recovery in separate processes. On this fixture, the full tree improved the encoded stream by only **1,045 bytes** compared with the parent-only model, but paid **32,832 extra GGUF bytes**, so its cold total was **31,787 bytes worse**. Shuffled leaf heads were also **611 total bytes better** than the intended leaf assignments. This does *not* demonstrate that correct leaf-specific surgery or extra nodes improves predictive quality. The parent-only arm was the best of the five.

The full tree's GGUF contains just **49,088 bytes** for a shared count table, 81 trained parent correction triples, and all 6,561 trained leaf correction triples. This is not a lossless encoding of 6,561 unrelated full dense function tables. Fit time on the hosted synthetic fixture was 101 ms (the timing excludes synthetic corpus generation, model encoding/decoding, and Actions setup); the full tree's encode and decode were 362 ms and 499 ms respectively in that measurement. Treat timings as one host observation, not universal performance.

[Full numerical HBP receipt](FULL6561-MEASURED.hbp). **The operator's original 6,561 local artifact files were not available and have not been fitted by this hosted run.**

## Run a complete 6,561-head synthetic proof

```sh
cargo +1.81.0 run --release --locked --bin shared_6561 -- \
  --fixture-6561 build/full-6561

cargo +1.81.0 run --release --locked --bin shared_6561 -- \
  --decode-check \
  build/full-6561/full_tree.gguf \
  build/full-6561/full_tree.stream \
  build/full-6561/target.raw
```

The synthetic generator independently produces **6,561 distinct training streams**, 6,561 validation streams, and 6,561 separate 512-byte test tails. The concatenated held-out target has **3,359,232 bytes**, the same *length* as the operator's proposed real-file target but **not the same content**. This is not a substitute for training on the operator's D: corpus; it proves that 6,561 populated slots can fit, serialize, route, encode and decode exactly.

The run measures five arms on identical bytes:
- one shared backbone with no corrections;
- 81 parent correction heads, no leaves;
- **the full 81 × 81 parent/leaf tree, all 6,561 leaves fitted**;
- complete tree with all weight corrections zeroed;
- complete tree with leaf corrections reassigned among leaves within each parent.

All five emit complete GGUF model and byte-coded streams. Every stream and all 13,122 expected routing decisions are reconstructed by a separate process using the GGUF file and stream only; file identity is not passed to the decoder. The output reports **GGUF model bytes + stream bytes** as cold transfer, and SHA-256s for model, stream, decoded bytes and route sequence.

## Run against the actual 6,561 source artifacts

Prepare a UTF-8 text list with exactly 6,561 rows and no header, in order `0` through `6560`. Each row is:

```text
0<TAB>D:/absolute/path/to/artifact-0000.md
1<TAB>D:/absolute/path/to/artifact-0001.py
...
6560<TAB>D:/absolute/path/to/artifact-6560.hbp
```

Replace the literal `<TAB>` with an actual tab character. Source paths must exist and be unique even after resolving symlinks. All files must have at least 1,025 bytes of readable data; the previously reported smallest local artifact (13,937 bytes) qualifies.

```sh
cargo +1.81.0 run --release --locked --bin shared_6561 -- \
  --fit-source-list source-list.tsv build/real-6561
```

**Partition rule:** for files longer than 128 KiB, the first **130,560 bytes** train the common predictor, the next **512 bytes** fit correction weights, and bytes **131,072–131,583** form the 512-byte test tail. Short files use their last 512 bytes as test, the prior 512 as validation, and earlier bytes as training. This preserves the operator's held-out tail position when the original training boundary was 128 KiB and prevents consulting the held-out bytes during correction fitting. It is a slightly smaller training prefix because validation must be separate.

The command reads only up to 128 KiB + 512 bytes of each source into memory, verifies that all 6,561 rows and distinct paths are present, fits each head, then writes:

| File | Description |
|---|---|
| `full_tree.gguf` | Complete shared GGUF backbone plus 81 × 81 fitted weight corrections |
| `full_tree.stream` | Actual arithmetic-coded output with causal hierarchical routing |
| `parents.gguf`, `parents.stream` | Parent-only comparison |
| `base.gguf`, `base.stream` | Shared static generalist comparison |
| `zero_deltas.*`, `shuffled_deltas.*` | Negative controls |
| `target.raw` | Exact concatenation of 6,561 independent 512-byte test tails; **local private data** |

**Privacy:** the real-corpus outputs may contain original artifact content. Keep the `build/real-6561` directory local, do not commit `target.raw` or model files to GitHub without deliberate source review. The hosted CI downloads only the **synthetic** fixture outputs.

## Acceptance and limits

The source list is required for legitimate claims that **all 6,561 local artifact files have trained correction heads**. The model can fill 6,561 slots on a synthetic fixture without those original files, but must mark that status clearly. A 6,561-address model with only 27 trained addresses is not a full run.

This build's specialist leaves each carry 3 parameters, so it cannot encode 6,561 arbitrary full independent conditional-probability tables. Its capacity is intentionally constrained. New independent validation is required before claiming it preserves the operator's 6,561-table prediction quality; a larger number of populated heads by itself does not demonstrate compression or generalization.
