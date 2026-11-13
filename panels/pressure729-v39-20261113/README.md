# Pressure boxes on 729 Asolaria-trained tables (V39, local seat, November 13, 2026)

**What this is.** The local counterpart of GPT-6's hosted 81-node pressure/box experiment: the same
question on other material and at a larger scale. 729 order-2 codex tables trained on a 2.69 GB
stream of Asolaria material are edited directly (no training loop, after *Sparks of Weight-Space
Programming*, Takehi, Teoh, Zhang, Khattab, 2026-11-02) and measured by how small 4,478,976 bytes
of held-out text code. The spec and its eight predictions were sealed before the run.

**Status: superseded as the record by the integer run in [STEER-QNN-and-NN](https://github.com/JesseBrown1980/STEER-QNN-and-NN), which reproduces every number below exactly (all 62 arms and 10 layer rows identical) and adds the STEER layer rule. This folder keeps the first measurement and the sealed specs: `SPEC-PRESSURE729-V39.hbp` (before the first run) and `SPEC-PRESSURE729-V40-INTEGER-STEER.hbp` (commit `0c28863`, before the integer run; the Rust program was committed on this branch as `fc9d6a8` before its run and now lives in the new repository).**

## Setup

- **Outer network:** 27 box tables. **Inner network:** 729 tables, 27 per box. A two-level switch
  picks the box, then the inner table, by cheapest cost over the previous 64 bytes.
- **Weight of an entry:** how often it was seen. **Density:** the share of inner entries kept.
- **Pressure rules** (same total kept at each density): EQUAL (each table keeps its own share),
  SEALED (weight flows between the 27 tables of a box), OPEN (walls open), and two controls,
  RANDOM and INVERSE (the lightest entries kept).
- **Fallback** for a removed entry: FLAT (probability 1/2) or PARENT (the box table).

## Weight concentration

| Heaviest share of entries | 1/2 | 1/16 | 1/64 | 1/256 |
|---|---|---|---|---|
| Share of total weight | 99.5% | 90.2% | 65.0% | 34.2% |

Median weight 5; 75,696,165 inner entries.

## Coded size against the full inner network (1,083,359 bytes), PARENT fallback

| Density | EQUAL | SEALED | OPEN | RANDOM |
|---|---|---|---|---|
| 1/2 | 0.0% | −0.1% | −0.1% | +9.4% |
| 1/4 | +0.6% | +0.1% | −0.1% | +13.6% |
| 1/8 | +2.7% | +1.5% | +0.2% | +15.5% |
| 1/16 | +5.1% | +3.8% | +1.4% | +16.2% |
| 1/64 | +11.0% | +9.7% | +7.1% | +16.4% |
| 1/256 | +14.3% | +13.4% | +12.4% | +16.0% |

With FLAT fallback the same cuts cost far more (for example +18% to +57% at 1/16). All 62 arms are
in `RESULT-PRESSURE729-V39.hbp`.

## Layers at different densities (the operator's hourglass)

NORMAL = everything, PRESSURIZED = 1/4, NEUTRON STAR = 1/16, BLACK HOLE = 1/256, each sealed in its
box. A layer replaces the incoming prediction where it still has an entry and lets it through
where the entry was removed; each layer has its own switch.

| Layer | Density | Bytes after the layer | Own inner table found |
|---|---|---|---|
| 1 | NORMAL | 1,083,359 | 37.6% |
| 2 | PRESSURIZED | 1,084,984 | 36.7% |
| 3 | NEUTRON STAR | 1,092,592 | 31.9% |
| 4 | BLACK HOLE | 1,105,462 | 13.4% |
| 5 | NEUTRON STAR | 1,094,042 | 32.0% |
| 6 | NORMAL | 1,084,235 | 37.3% |

Starting from the black hole outward: 1,228,711 → 1,125,600 → 1,085,638 → 1,084,460.

## Predictions (sealed first)

Five of eight met in full. Missed: the cut to 1/16 was predicted to cost more than 10% and cost
0.8% over the plain baseline; OPEN was marginally above SEALED at density 1/2; INVERSE was not the
largest rule at 1/64 and 1/256 with PARENT fallback. See `JUDGE-PRESSURE729-V39.hbp`.

## Nearest published work found in a first search (not a priority audit)

- Pruning count-based language models with backoff to a lower-order model: Stolcke,
  *Entropy-based Pruning of Backoff Language Models* (2000), https://arxiv.org/abs/cs/0006025.
  The PARENT fallback and count-guided cuts here are of that family.
- One global threshold against per-layer budgets in magnitude pruning: Lee et al.,
  *Layer-adaptive Sparsity for the Magnitude-based Pruning* (LAMP), https://arxiv.org/abs/2010.07611;
  Zhou et al., *Effective Sparsification of Neural Networks with Global Sparsity Constraint*,
  https://arxiv.org/abs/2105.01571. EQUAL / SEALED / OPEN here are of that family.
- For a stack of the same network at alternating densities with pass-through of removed entries,
  that search returned hourglass architectures with dense layers only.

## Scope

- Pressure, flow and walls are analogies on a table network; no fluid solver runs.
- In the hourglass the last NORMAL layer can answer almost every context itself, so by this
  pass-through rule the stack is close to transparent by construction.
- The baseline through the real range coder is 1,091,311 bytes against 1,090,464 by the cost table.
- **Lane.** This first run used a local Node program whose cost table was built with floating logarithms. The integer Rust program in the new repository computes the same table exactly and reproduces these rows.
- The stream and the tables (2.7 GB and 0.6 GB) stay on the local machine.
