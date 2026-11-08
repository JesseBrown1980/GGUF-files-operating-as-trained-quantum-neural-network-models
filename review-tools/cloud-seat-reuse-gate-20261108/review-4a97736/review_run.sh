#!/usr/bin/env bash
# The cloud seat's independent reuse review of twens 0.4.0 (memo=1) at PR #15 head 4a97736, on the reuse path itself
# (K4 at >= 2^22 samples, K2 at >= 2^10), against twens 0.3.0. Allowed points only. Integers only. json=0.
set -uo pipefail
R=$(cd "$(dirname "$0")" && pwd); B=$R/bin; O=$R/run; C=$R/gate/review-tools/cloud-seat-reuse-gate-20261108/ens_merge_check.py
rm -rf "$O"; mkdir -p "$O"; cd "$O"
row() { echo "$*" | tee -a "$O/REVIEW.hbp"; }
for f in "$B"/*; do [ -L "$f" ] || [ "${f##*-}" = memo ] || row "BIN|name=$(basename "$f")|sha256=$(sha256sum "$f" | cut -d' ' -f1)|json=0"; done
for p in "N=81 delta=1/2 y=1/18" "N=81 delta=1/2 y=1/27" "N=729 delta=-1/4 y=1/27"; do row "GUARD|$p|$("$B/twens04" guard $p | tr '\n' ' ')|json=0"; done
body() { tail -n +2 "$1" | sha256sum | cut -d' ' -f1; }
same_body() { # name ref memo: rows after TWB_HEAD byte-equal
  if [ "$(body "$2")" = "$(body "$3")" ]; then row "BODY_EQUAL|$1|sha256=$(body "$2")|json=0"; else row "BODY_DIFF|$1|json=0"; fi; }
# 1. the hosted workflow's four batches, here: plain = memo byte for byte, rows pinned, TWB_MEMO rows as filed
K="N=81 delta=1/2 u=1 y=1/27 dtden=64 threads=2"
C2="ctrl=1099511627776:0:0;1099511628776:3000:-5000"
C3="ctrl=1099511627776:0:0;1099511628776:3000:-5000;1099511636776:7000:-9000"
ci() { b=$1; pin=$2; shift 2
  "$B/twens04" "$@" > "plain-$b.hbp" 2> "plain-$b.err"; "$B/twens04" "$@" memo=1 > "memo-$b.hbp" 2> "memo-$b.err"
  "$B/twens03" "$@" > "v03-$b.hbp" 2> "v03-$b.err"
  row "CI_BATCH|batch=$b|plain_eq_memo=$(cmp -s plain-$b.hbp memo-$b.hbp && echo 1 || echo 0)|pin_ok=$([ "$(body memo-$b.hbp)" = "$pin" ] && echo 1 || echo 0)|v03_body_eq=$([ "$(body v03-$b.hbp)" = "$pin" ] && echo 1 || echo 0)|plain_err_bytes=$(wc -c < plain-$b.err)|memo_err=$(cut -c1-60 memo-$b.err)|json=0"; }
ci A b9ded2c9471319f419e6a3d69cacd1346a64fe8d5f66626d90616ee80d98f5fb run $K seed_string=count-memo-rr-batchA start=7 count=4194311 steps=0,4 "$C2" mask=VNC,V1,LOCK
ci B 43b6f63dc2d0a077e5c2ecfaf745f7ed74bf178d25e969d7f03abe6e6e0ba687 run $K seed_string=count-memo-rr-batchB start=0 count=4194304 steps=0,4 "$C2" mask=VNC,V1,V0,FLIP,LOCK
ci C 236a53f92c386ac3deff499f0eb20bb557834e21587a532e0f4972dfe36ea6f4 run $K seed_string=count-memo-rr-batchC start=0 count=20000 steps=0,8,16 "$C3" mask=VNC,V1,V0,RN,FLIP,LOCK,MODE0,NL
ci D 549a15d6aded94f80760b5f583c98459616942d1886ac62bd388f2925f2deef6 twens 81 1/2 1 1/27 20000 20261108 64 3 32,64 '1204211555720:283548732622:0;1538251237657:621098771141:0'
# 2. new batches, chosen here: other point, other seed, other steps, every K4 variant, odd start, thread counts
E1="N=81 delta=1/2 u=1 y=1/18 seed=20261105 dtden=64 steps=0,4,8 $C3 mask=VNC,V1,RN,FLIP,LOCK"
"$B/twens03" run $E1 threads=4 start=5 count=8388619 > e1-v03.hbp
"$B/twens04" run $E1 threads=4 start=5 count=8388619 memo=1 > e1-memo.hbp 2> e1-memo.err
"$B/twens04" run $E1 threads=3 start=5 count=4194310 memo=1 > e1-memo-h1.hbp 2> e1-memo-h1.err
"$B/twens04" run $E1 threads=1 start=4194315 count=4194309 memo=1 > e1-memo-h2.hbp 2> e1-memo-h2.err
same_body E1_whole_v03_vs_memo e1-v03.hbp e1-memo.hbp
row "E1_MEMO|$(cut -d'|' -f2- e1-memo.err)"
row "E1_UNION|$(python3 -I "$C" e1-v03.hbp e1-memo-h1.hbp e1-memo-h2.hbp | tr '\n' ' ')|json=0"
E2="N=729 delta=-1/4 u=1 y=1/27 seed=7 dtden=128 steps=0,2 $C2 mask=VNC,V1,V0,RN,FLIP,LOCK,MODE0,NL"
"$B/twens03" run $E2 threads=4 start=1000 count=4194305 > e2-v03.hbp
"$B/twens04" run $E2 threads=4 start=1000 count=4194305 memo=1 > e2-memo4.hbp 2> e2-memo4.err
"$B/twens04" run $E2 threads=1 start=1000 count=4194305 memo=1 > e2-memo1.hbp 2> e2-memo1.err
same_body E2_v03_vs_memo_t4 e2-v03.hbp e2-memo4.hbp
same_body E2_v03_vs_memo_t1 e2-v03.hbp e2-memo1.hbp
row "E2_MEMO|$(cut -d'|' -f2- e2-memo4.err)"
E3="N=81 delta=1/2 u=1 y=1/18 seed=99 dtden=64 steps=0,4,8 $C3 mask=V1,LOCK,FLIP"
"$B/twens03" run $E3 threads=4 start=0 count=1500 > e3-v03.hbp
"$B/twens04" run $E3 threads=4 start=0 count=1500 memo=1 > e3-memo.hbp 2> e3-memo.err
same_body E3_k2_only_v03_vs_memo e3-v03.hbp e3-memo.hbp
row "E3_MEMO|$(cut -d'|' -f2- e3-memo.err)"
# 3. planted faults in the reused counts, weights and keys: each must be refused by a named check
mut() { name=$1; ref=$2; shift 2
  "$B/mut-$name" "$@" memo=1 > "mut-$name.hbp" 2> "mut-$name.err"; rc=$?
  chk=$(python3 -I "$C" "$ref" "mut-$name.hbp" 2>&1 | tr '\n' ' ')
  row "FAULT|name=$name|engine_rc=$rc|engine_fault=$(grep -o 'reason=[a-z_]*' "mut-$name.err" | head -1)|comparator=$chk|json=0"; }
FA="N=81 delta=1/2 u=1 y=1/18 seed=20261105 dtden=64 steps=0,4,8 $C3 mask=VNC,V1,RN,FLIP,LOCK threads=4 start=5 count=8388619"
mut N1_k4_reused_weight_plus1 e1-v03.hbp run $FA
mut N5_k4_count_dropped e1-v03.hbp run $FA
mut N6_k4_key_c3_sign e1-v03.hbp run $FA
FB="N=81 delta=1/2 u=1 y=1/18 seed=99 dtden=64 steps=0,4,8 $C3 mask=V1,LOCK,FLIP threads=4 start=0 count=1500"
mut N2_k2_reused_weight_plus1 e3-v03.hbp run $FB
mut N7_k2_count_dropped e1-v03.hbp run $FA
row "CORRECT_ENGINE|comparator=$(python3 -I "$C" e1-v03.hbp e1-memo.hbp | tr '\n' ' ')|json=0"
row "REVIEW_DONE|json=0"
