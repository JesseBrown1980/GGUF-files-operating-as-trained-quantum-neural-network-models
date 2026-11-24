# V7 hybrid contraction crossover, 2026-11-24
Prior PR #37 hosted runs 45391627819 and 45391627684 both PASS. This follow-up is exploratory, not preregistered.

Local exact integer scan: 48 fixtures, 2–5 crossings, cycle/bipartite/clique/seeded irregular graphs, seeds 0–2. 420 signed subsets (single/pair and full triple) tested against optimal direct dense bucket elimination. No signed subset won. Direct planner exhaustive; signed planner best of three greedy policies. 27 numerical tests on nine original V7 parameter receipts, two small 2-crossing and one 3-crossing fixture each, verified all 27 signed sums and rejected all 27 omitted first terms. Amplitude slices divided by common exact gcd equally across arms. 18 direct independent brute checks and nine alternative greedy direct orders (not necessarily different orders). Source receipt replay is not a new SHA-pinned native model run.

Extension: cliques of 6–16 crossings, three seeds, every single rewrite, 363 candidates, four wins in the original dense cost convention (two at 8, one at 9, one at 12). Each pair of logical labels has a matrix factor attached to SHA-selected occurrences (hash ASCII port/{seed}/{a}/{b}, low bit of first and second bytes); each label has one unary factor. Direct equality elimination identifies x=v and y=u, giving complete graph on n=2k labels. Dense bucket charge (factor_count-1)*N + N-N/d. By symmetry every direct order has the same dense count: (n-1)9^n+8*9^(n-1)+sum_{m=1}^{n-1}(m*9^m+8*9^(m-1)). Signed terms R,C,E,F cover 8-state core and full ninth-state corrections; charge two correction multiplications, three additions and final division. Fixed orders independently replayed with set-based scopes.

| crossings | direct dense | signed dense | direct pairwise | signed pairwise |
|---|---:|---:|---:|---:|
|8|33093782435275847|31455975317196245|4169297072582423|7201230320827301|
|9|3018309306675591698|2952974840278011998|337712935715922842|583245315174785245|
|12|2142476807017872569611211|2089517522273703294058625|179474499007617206747195|309957037312525913845303|

Stronger control: for every bucket multiply the pair with smallest union size, charge its actual union domain, repeat then sum. Same fixed variable orders for both cost conventions. All three apparent crossover examples lose against this better direct route. This does not prove no other signed order can win. No large numeric contraction, wall-time advantage, STEER inference, or Fischer playback claimed. Planning, tensor construction, memory, Big integer limb work and receipts remain additional. The native test replays these three structural certificates; hosted acceptance pending. Main and prior drafts unchanged.

Local scan source SHA256 8c77864d25587cd2cc7f23be4080c242cc1ca2b45003ea88d1cab5ff24ae3e02; output 7a069ac0401492b63ee045211f1ef0f79bdc73d01a92119b2b4d1dd961f733fa. Next: optimize factor product trees and variable orders jointly, exploit actual QNN factor structure, evaluate only a signed path with an end-to-end advantage against equally optimized direct baseline.
