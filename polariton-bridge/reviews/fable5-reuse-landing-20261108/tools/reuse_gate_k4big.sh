#!/usr/bin/env bash
# K4 path engaged: 2^22 samples at the allowed point N=81, delta=1/2, y=1/18, mask V1; 30-minute stop per run. json=0.
set -uo pipefail
R=/mnt/c/tmp/opus55/reuse-gate-run-20261108; G=/mnt/c/tmp/opus55/cloud-reuse-gate-20261108/repo/review-tools/cloud-seat-reuse-gate-20261108
row() { echo "$*" | tee -a "$R/GATE-RUN-K4BIG.hbp"; }
C3='1099511627776:0:0'
J="N=81 delta=1/2 u=1 y=1/18 seed=20261105 dtden=64 steps=0,32,64 ctrl=$C3;$C3;$C3 mask=V1"
mkdir -p "$R/k4big"
for e in twens03 twens04-memo mut-F3_dropped_count-memo; do
  t0=$(date +%s%N)
  timeout 1800 "$R/bin/$e" run $J start=0 count=4194304 threads=4 > "$R/k4big/$e.hbp" 2> "$R/k4big/$e.err"; rc=$?
  ms=$(( ($(date +%s%N) - t0) / 1000000 ))
  row "K4BIG_RUN|engine=$e|rc=$rc|wall_ms=$ms|json=0"
  grep -h '^TWB_MEMO' "$R/k4big/$e.err" | cut -c1-330 | sed 's/^/K4BIG_MEMO_ROW|/' | tee -a "$R/GATE-RUN-K4BIG.hbp"
  [ "$rc" = 0 ] || exit 1
done
for e in twens04-memo mut-F3_dropped_count-memo; do
  out=$(python3 -I "$G/ens_merge_check.py" "$R/k4big/twens03.hbp" "$R/k4big/$e.hbp" 2>&1); rc=$?
  row "MERGE|case=k4big_union_ref03_part_$e|rc=$rc|$(echo "$out" | tr '\n' ' ' | cut -c1-300)"
done
(cd "$R/k4big" && sha256sum * > SHA256SUMS)
row "K4BIG_DONE|sha256sums=$(sha256sum "$R/k4big/SHA256SUMS" | cut -d' ' -f1)|json=0"
