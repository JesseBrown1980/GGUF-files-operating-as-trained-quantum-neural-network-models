# QNN × One Button — 81 balanced-ternary nodes + central Ω (November 13, 2026)

**Experimental status:** exact CPU implementation **PASS** at [hosted run 43465408682](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/actions/runs/43465408682); this is a **structure and relocation experiment**, not a trained file-classifier accuracy measurement. The branch is kept as **draft PR #32** pending broader repository CI and review.

## Why this architecture?

The [one-button visual source](https://github.com/JesseBrown1980/the-one-button/blob/main/index.html) draws 81 mutually interacting bodies, 27 each in red, green and blue, and a central Ω. The site uses fixed-point integer state for its moving bodies, but initial sine/cosine placement and the final browser canvas boundary also use floating-point JavaScript. This QNN bridge avoids those floats completely.

The existing full synthetic GGUF contains 81 **populated parent correction addresses**, each containing a signed three-coordinate integer weight vector, and 6,561 populated leaf corrections. These weights are **not address coordinates**: they determine a specialist's byte-family correction. The four real-file-trained parent codices in the earlier classification experiment are a distinct model with only 4 populated parents/24 populated leaves. The new structural test uses the full synthetic model, pinned to SHA-256 `606c4d8478b8dbd72dfda0dad6c6ef1895c081a7cd5d5bb6c363525f57b941b2`.

## Exact 81 = 3 × 27 = 3⁴ mapping

Every parent address i in 0..80 maps into 4 balanced trits:

- `color = (i % 3) - 1` in `{-1,0,+1}` (red/green/blue)
- the other three trits are the base-3 digits of `i / 3`, each shifted down by 1, giving 27 unique spatial coordinates per color.

The central Ω is an **aggregator, not an 82nd trained neural head**.

Each node receives an initial state `s_i = sign(delta_i[0]*x_i + delta_i[1]*y_i + delta_i[2]*z_i)`. Thus we actually consume the trained GGUF correction vector from address i. The explicit symmetric, ternary edge matrix T has `T_ij = -1` for same-color neighbors, `+1` for different-color neighbors, and 0 otherwise; neighbors are within Hamming distance 1 in the three spatial trits, never self. The topology is local, whereas the original One Button browser animation calculates all-pair forces.

Three synchronous steps use strictly integer arithmetic:

```
s_i(t+1) = sign(4*s_i(initial) + 2*s_i(t) + sum_j T_ij*s_j(t))
```

All states, coefficients and signals are integers; outputs are balanced trits. The center reports exact R/G/B sums and their total and sign.

## Prediction-first controls

The protocol was frozen first: [ONEBUTTON-TERNARY81-FREEZE-20261113.hbp](ONEBUTTON-TERNARY81-FREEZE-20261113.hbp), final pre-code commit `556c576fc6d4c832035dcb2c04a74edea3ba3fd0`. The exact swap addresses **0 and 80** were fixed in advance; the swapped count was unpredicted.

**Control A — coordinate change:** the entire model and connection matrix are relabelled with the bijection `p(i) = (5i+1) mod 81`, the three-step update is run, and coordinates are relabelled back. All **81/81** trit states match the base run, byte-for-byte. Merely renaming the location of data does not change the function if its topology moves with it.

**Control B — logical surgery:** swap the trained parent weight vectors at addresses 0 and 80, leaving their spatial positions, connectivity and all 6,561 leaf corrections unchanged. The modified GGUF is serialized and cold-reloaded. **10/81 final balanced-ternary states change**. This is a genuine function change caused by a positional reassignment.

| Property | Base | Weight swap |
|---|---:|---:|
| Undirected attractive links | 567 | 567 |
| Undirected repulsive links | 243 | 243 |
| Red channel total | −18 | −15 |
| Green channel total | −14 | −9 |
| Blue channel total | 0 | 0 |
| Central total | **−32** | **−24** |
| Central balanced-trit sign | −1 | −1 |
| Final state SHA-256 | `8681b95a96fc…` | `f3a361fdbf3…` |

The hosted gate builds the unchanged checkpoint from source, verifies its byte-level SHA-256, runs Rust 1.81 strict Clippy/tests, creates both GGUFs, independently reloads the modified model, checks the original backbone/leaf array unchanged, validates matrix symmetry and trit ranges, and archives all model/state hashes.

## What this establishes

1. A stable balanced-ternary, **integer-only** 81-node matrix arrangement can be built using real weights already inside the synthetic GGUF.
2. A consistent renaming of address, input and connectivity preserves the integer result exactly.
3. Moving weights while preserving spatial connections changes the computed state, with 10 changed nodes in this frozen test.

**What it has not measured:** accuracy, cold classifier inference, language understanding, learning superiority, an 81-model neural ensemble, or quantum-hardware performance. The current source GGUF is a **synthetically trained shared-backbone correction model**, not 81 independently trained QNN circuits.

## Next concrete scientific test

A separate prediction-first experiment would connect the new 81-node state to **actual class logits** or a causal byte predictor, with a central class-readout trained only on a frozen training partition. Compare unchanged router, same model with neutral/no-edge topology, integer ternary coupling, shuffled address assignments and weight erasure. Keep total GGUF model storage plus topology side-information, cold decode, CPU inference time and equal-context accuracy. The already-read #28/#30 test files can be reported only as exploratory diagnostics; any new generalization claim needs a new blind holdout.
