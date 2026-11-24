# Connected signed QNN audit (2026-11-24)
Source: nine original V7 checkpoints; prior exact local crossing gate PR #36, hosted runs 45292742334 and 45292742380 passed. This is a post-hoc follow-up, not a preregistered prediction.

Two crossing factors on ports (x,y,u,v) joined by four 9x9 matrices, selected from actual V7 amplitude environment slices 0,1,40,80. Three wirings: 0123,0213,0132 (the first two have equivalent equality-reduced topology). Direct baseline substitutes x=v,y=u and minimizes dense bucket elimination arithmetic exactly over all variable orders. Independent referee enumerates 9^4 assignments. Each crossing becomes R+C+2E+2F divided by 2, E fixes x=v=8 and y=u unrestricted, F fixes y=u=8 and x=v<8. R and C split via an eight-valued XOR bond with the original ordered octonion signs. All 16 terms evaluated and summed; exact numerator must equal four times direct. Dropping the RR term is a negative control.

Independent Python integer replay of published trained parameters (per-matrix common gcd removed uniformly) gave 27/27 exact agreements and 27/27 RR-drop rejections. Native Rust test independently loads hash-pinned checkpoints without gcd normalization, and redoes the complete comparison. Native acceptance pending.

| Wiring | Direct | Signed optimized | Signed fixed forward | Signed fixed backward |
|---|---:|---:|---:|---:|
| 0123 | 323 | 441913 | 499641 | 2213785 |
| 0213 | 323 | 441913 | 499641 | 2213785 |
| 0132 | 2915 | 549462 | 596471 | 2229399 |
| All 27 | 32049 | 12899592 | 14361777 | 59912721 |

Dense cost convention: for a bucket of k factors on union size N and eliminated dimension d, charge (k-1)N products and N-N/d additions, final scalar products, correction weights and 15 summations; final division by four charged separately. This is a shape-based arithmetic model, not wall time or a count of individual Big limb operations. Peak bucket domain: direct 81/81/729 versus signed 32768 in each optimized wiring. Planner visits 16 states per direct topology and 4624 across signed terms (memoized per term); planning transitions, tensor construction, address work, source replay, receipts and referee arithmetic additional. Python cache shared topology plans between models; native planner repeats them. The fixed order comparisons are modeled costs, not timings or native Bobby Fischer playback. The guide is exact structural optimization, not the trained STEER text router.

Independent audit SHA-256: 5f9da4ad3aad367bdd544fa79bf30f4dfcf742280d8cfb4092258eba5a2aaba9; local output SHA-256: 03b5ebeef25efe88809403aeb09a912f18dfad2c5a9c94491a5496425508def9. The original parameter replay script SHA-256: b44836d4adcd2cb9709fd602c5e1865c49e03e26cc8b941be1301415c72f028e. Native test emits its own raw-amplitude observable SHA-256s.

Result: signed order selection reduces modeled cost 78.5% versus backward and 10.2% versus forward; direct substitution remains about 402.5 times cheaper. No overall speedup. Next target is an actual structured network with high-width non-equality factors, direct preprocessing and optimized variable elimination as baseline, and a hybrid guide that selects the signed rewrite only when its entire cost is lower. Preserve main and prior accepted head.