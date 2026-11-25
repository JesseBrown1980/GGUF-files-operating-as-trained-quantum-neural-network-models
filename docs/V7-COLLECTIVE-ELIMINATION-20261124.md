# V7 collective elimination, 2026-11-24

External lead: [P = NP agent swarm](https://pequalnp.com/), strategy orchestrator update retrieved 2026-11-24. The report describes a Boolean circuit family in which removing a whole class sharing a helper avoids size growth that occurs when removing fewer gates. It explicitly labels this observation computed, not checked. [Public Lean repository](https://github.com/brilliant-hq/pequalnp-proofs). We import the research question, not a formal Boolean theorem. Related source: [Asolaria Radiated Slice](https://github.com/JesseBrown1980/Asolaria/blob/main/docs/THE-RADIATED-SLICE.md). Previous radiated factorization PR #39 hosted runs 45408258782 and 45408258822 passed.

## Exact V7 theorem

Let P be the invertible linear ternary address map induced by the forward SUM ring on F_3^8; U_P maps |x> to |Px>. The initial state after first-layer rotations and disjoint SUM gates is the product of four pair factors on (0,4),(2,6),(1,3),(5,7). The active dressing layer is U_P^-1 (product of local rotations) U_P. Conjugate each nonidentity local rotation R on coordinate q separately; adjacent U_P U_P^-1 cancel exactly. For an output address x, y=(Px)_q, and an integer numerator matrix M for R, the transformed amplitude is

    psi_new(x) = sum_{t=0}^2 M[y,t] psi_old(x + (t-y) P^-1 e_q).

Address arithmetic is modulo 3. The numerator matrix is the same rational rotation numerator as the native engine; denominator scales multiply exactly. This operator acts only on the union of the support of row q of P and column q of P^-1. Outside that support the address is unchanged and coefficients are independent of outside coordinates. Identity rotations are skipped, including their scale, per native semantics.

Start with the four pair supports, union every pair of blocks touched by a nonidentity conjugated gate, transitively. By induction all initial factors are internal to components and all subsequent gates act within one final component. Thus the final numerator state is exactly a product of component tensors. Evaluate each independently in original coordinates using the displayed formula. The common SUM ring is eliminated as a materialized helper; its address action is preserved. This is a sufficient factorization; connectivity alone does not certify minimal rank.

## Independent exact integer replay

Source: nine published rotation receipts from results-v7/V7.hbp; Python arbitrary precision integer replay, compared against the separate expanded forward simulation, with an entry-perturbation negative control per model. Both ring inverse compositions checked on all eight basis vectors. Native Rust acceptance will instead parse and SHA-256-check the original GGUFs.

| model | component sizes | entries | dressing coefficient products |
|---|---|---:|---:|
|9 identity|6,2|738|2430|
|9 warm|2,2,2,2|36|0|
|9 star|8|6561|174960|
|27 identity|6,2|738|2430|
|27 warm|2,2,2,2|36|0|
|27 star|8|6561|174960|
|81 identity|2,2,2,2|36|0|
|81 warm|2,2,2,2|36|0|
|81 star|8|6561|174960|

All 59,049 amplitudes matched; 9/9 deliberately corrupted component controls rejected. 21,303 component entries versus 59,049 expanded entries (63.9% fewer), six models with reduced representation. For each of the two active identity checkpoints the isolated pair is (5,7); the other six coordinates form a single component. The dressing products are 2,430 instead of 21,870 for full-state rotations (same five coefficient products per three entries; 9-fold reduction). These counts exclude pair factor formation, address arithmetic, allocations, planning, additions, big-integer limb costs, denominator handling and acceptance expansion. No timing or advantage over an equally optimized conventional tensor network established. Three star models have one component and use the full 6,561 entries; no reduction by this sufficient test. The identical 81 identity/warm rotation receipts produce the same state and are separate checkpoint cases, not statistically independent evidence.

Local replay script SHA-256 89612049ffa09664746d4b43d004c522460292bacc87498d83ff5839f7008798; output SHA-256 55ecccd9a5fd53c99856b1115383ff1bdf8cc00db6042ee17617951a54b6c9f1. Dependencies signed audit b44836d4adcd2cb9709fd602c5e1865c49e03e26cc8b941be1301415c72f028e and radiated audit 6ca48fe63b1847fe366b3061dbc5aed7b19e74d9b4d7867124b1ea7c793cfc86. Native test and hosted workflow in this PR; status pending. No P vs NP conclusion. Next: conditional separators and exact low-rank factorization for the star models, joint contraction tree/order optimization against optimized direct reference, and separate observable-level acceptance. No change to main.
