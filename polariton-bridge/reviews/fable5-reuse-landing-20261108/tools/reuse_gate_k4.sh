#!/usr/bin/env bash
# K4-path control: the same allowed point (N=81, delta=1/2, y=1/18), mask V1,V0, so the 4-ball reuse path runs. json=0.
set -uo pipefail
R=/mnt/c/tmp/opus55/reuse-gate-run-20261108; G=/mnt/c/tmp/opus55/cloud-reuse-gate-20261108/repo/review-tools/cloud-seat-reuse-gate-20261108
row() { echo "$*" | tee -a "$R/GATE-RUN-K4.hbp"; }
C3='1099511627776:0:0'
J="N=81 delta=1/2 u=1 y=1/18 seed=20261105 dtden=64 steps=0,32,64 ctrl=$C3;$C3;$C3 mask=V1,V0"
mkdir -p "$R/k4"
"$R/bin/twens03" run $J start=0 count=20000 threads=4 > "$R/k4/ref03.hbp" 2> "$R/k4/ref03.err"
for e in twens04-memo mut-F3_dropped_count-memo mut-F1_key_merges_two_starts-memo; do
  "$R/bin/$e" run $J start=0 count=7000 threads=3 > "$R/k4/$e-p1.hbp" 2> "$R/k4/$e-p1.err"; r1=$?
  "$R/bin/$e" run $J start=7000 count=13000 threads=2 > "$R/k4/$e-p2.hbp" 2> "$R/k4/$e-p2.err"; r2=$?
  row "K4_RUN|engine=$e|rc=$r1,$r2|json=0"
  grep -h '^TWB_MEMO' "$R/k4/$e-p1.err" "$R/k4/$e-p2.err" | cut -c1-330 | sed 's/^/K4_MEMO_ROW|/' | tee -a "$R/GATE-RUN-K4.hbp"
  out=$(python3 -I "$G/ens_merge_check.py" "$R/k4/ref03.hbp" "$R/k4/$e-p1.hbp" "$R/k4/$e-p2.hbp" 2>&1); rc=$?
  row "MERGE|case=k4_union_ref03_parts_$e|rc=$rc|$(echo "$out" | tr '\n' ' ' | cut -c1-300)"
done
(cd "$R/k4" && sha256sum * > SHA256SUMS)
row "K4_DONE|sha256sums=$(sha256sum "$R/k4/SHA256SUMS" | cut -d' ' -f1)|json=0"
