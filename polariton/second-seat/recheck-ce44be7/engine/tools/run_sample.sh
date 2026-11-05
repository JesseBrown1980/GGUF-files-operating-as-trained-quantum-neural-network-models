#!/bin/bash
# The stage sample from my own clean build, then the reader and the whole exact route on the receipt at this head. Everything lands in out/.
export MSYS_NO_PATHCONV=1
export PYTHONDONTWRITEBYTECODE=1
W=C:/tmp/opus55/polariton-recheck-engine-20261105
B=$W/target/release/polariton_three_mode.exe
O=$W/out/fresh
mkdir -p "$O"
for stage in taylor control reversal wavevector rotor; do
  t0=$(date +%s)
  "$B" "$stage" > "$O/$stage.out" 2> "$O/$stage.err"
  echo "STAGE|$stage|rc=$?|seconds=$(( $(date +%s)-t0 ))|rows=$(wc -l < "$O/$stage.out")"
done
R=$W/clean/polariton
python3 -I -X utf8 "$R/read_prediction.py" "$R/RECEIPT.hbp" > "$O/read.hbp" 2> "$O/read.err"; echo "READER|rc=$?"
t0=$(date +%s)
: > "$O/route.hbp"
for args in "hand" "taylor_compare $R/RECEIPT.hbp" "convert_compare $R/RECEIPT.hbp" "sector_compare $R/RECEIPT.hbp 243" "full_compare $R/RECEIPT.hbp 9" "top_compare $R/RECEIPT.hbp 59049" "mathieu 1/50 2/25 8/25 32/25 128/25 512/25"; do
  t1=$(date +%s)
  python3 -I -X utf8 "$R/second_route.py" $args >> "$O/route.hbp" 2>> "$O/route.err"
  echo "ROUTE|${args%% *}|rc=$?|seconds=$(( $(date +%s)-t1 ))"
done
echo "ROUTE_ALL|seconds=$(( $(date +%s)-t0 ))"
echo SAMPLE_DONE
