#!/bin/bash
# The instrumented copy: bits lost at every left shift and narrowing cast, on the stages where the sizes are largest, and the step test at N = 729.
export MSYS_NO_PATHCONV=1
W=C:/tmp/opus55/polariton-recheck-engine-20261105
B=$W/target/release/inst.exe
O=$W/out/inst
mkdir -p "$O"
for stage in rotor sector reversal i_window729 i_conv729 i_step729; do
  t0=$(date +%s)
  "$B" "$stage" > "$O/$stage.out" 2> "$O/$stage.err"
  echo "INST|$stage|rc=$?|seconds=$(( $(date +%s)-t0 ))|rows=$(wc -l < "$O/$stage.out")|lost=$(grep '^WRAP' "$O/$stage.out" | grep -v 'events=0' | tr -d '\r' | tr '\n' ';')"
done
echo INST_DONE
