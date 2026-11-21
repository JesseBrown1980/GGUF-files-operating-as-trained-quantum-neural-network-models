# The blind jets across two machines, November 8, 2026

[`../jets-20261108/`](../jets-20261108/) seals the seat's 124 local files whole, wall-clock timings included, which makes it the tamper seal for those files. The cross-machine identity is read through normalizations that leave the timing out ([the second machine's report](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/pull/15#issuecomment-6722516374), [GPT-6's acceptance rule](https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/pull/15#issuecomment-6722576380)):

- **Step 1.** All 124 files verified whole against the sealed `INDEX.hbi` first: 124 of 124.
- **Rule J** (jets, the `JET_TIME` row removed): 40 of 40 equal to the second machine's, list sha256 `33bb3993…` on both.
- **Rule R** (reads, the embedded `jet_sha256` and `eint_jet_sha256` fields removed): 83 of 83 equal, list sha256 `e92b18e3…` on both.
- **Rule J without `JET_HEAD`** (the CI's rule): `c54244b78db59be2…` on both.
- **Rule J2** (only the four `*_ms` fields removed, so the deterministic counters stay in the hash): filed here for the second machine to recompute. The counters in [`JET-COUNTERS.list`](JET-COUNTERS.list) agree with the plan on all 40 jets.

Two machines produced the same 40 jets and 83 reads before the ensemble Monte Carlo ran, and no value was opened. Rows and hashes: [`ADDENDUM.hbp`](ADDENDUM.hbp).
