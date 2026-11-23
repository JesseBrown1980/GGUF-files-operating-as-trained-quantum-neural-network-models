#!/usr/bin/env bash
# The cloud seat's reuse acceptance gate, run on twens 0.4.0 (memo=1) against 0.3.0, before any push. Allowed points only. json=0.
set -uo pipefail
R=/mnt/c/tmp/opus55/reuse-gate-run-20261108
G=/mnt/c/tmp/opus55/cloud-reuse-gate-20261108/repo/review-tools/cloud-seat-reuse-gate-20261108
M=/mnt/c/tmp/opus55/review-memo-20261108/bin
D=/mnt/c/tmp/opus55/bridge-blind-driver-20261106
rm -rf "$R"; mkdir -p "$R/bin"
row() { echo "$*" | tee -a "$R/GATE-RUN.hbp"; }
cp "$M/twens-b03" "$R/bin/twens03"; cp "$M/twens-e04" "$R/bin/twens04"
for m in F1_key_merges_two_starts F3_dropped_count; do cp "$M/mut/twens-$m" "$R/bin/mut-$m"; done
chmod +x "$R"/bin/*
for f in "$R"/bin/*; do row "BIN|name=$(basename "$f")|sha256=$(sha256sum "$f" | cut -d' ' -f1)|json=0"; done
for w in twens04 mut-F1_key_merges_two_starts mut-F3_dropped_count; do
  printf '#!/usr/bin/env bash\nexec %s "$@" memo=1\n' "$R/bin/$w" > "$R/bin/$w-memo"; chmod +x "$R/bin/$w-memo"
done
(cd "$G" && sha256sum -c SHA256SUMS > "$R/tools-check.out" 2>&1) && row "TOOLS|sha256sums=OK|json=0" || { row "TOOLS|sha256sums=FAIL|json=0"; exit 1; }
# reserved-point check of every point used, in the driver's code and in the engine's own guard
python3 -I -B - "$D" <<'PY' | tee -a "$R/GATE-RUN.hbp"
import sys
sys.path.insert(0, sys.argv[1])
import bridge_plan as bp
assert bp.reserved_selftest()
for (N, d, y) in ((81, '1/2', '1/18'), (729, '-1/4', '1/27')):
    ex, band = bp.reserved(N, d, y)
    print('POINT|N=%d|delta=%s|y=%s|exact=%d|band=%d|json=0' % (N, d, y, ex, band))
    if ex or band:
        raise SystemExit('POINT_REFUSED|json=0')
PY
[ "${PIPESTATUS[0]}" = 0 ] || exit 1
"$R/bin/twens04" guard N=81 delta=1/2 y=1/18 | sed 's/^/GUARD|/' | tee -a "$R/GATE-RUN.hbp"
"$R/bin/twens04" guard N=729 delta=-1/4 y=1/27 | sed 's/^/GUARD|/' | tee -a "$R/GATE-RUN.hbp"
# 1. the gate's own script on three engines: 0.3.0 (its baseline), 0.4.0 plain, 0.4.0 memo=1
for e in twens03 twens04 twens04-memo; do
  bash "$G/run_baseline.sh" "$R/bin/$e" "$R/$e" > "$R/$e.stdout" 2> "$R/$e.stderr"; rc=$?
  row "BASELINE|engine=$e|rc=$rc|done=$(grep -c '^BASE_DONE' "$R/$e.stdout")|equal=$(grep -c 'result=EQUAL' "$R/$e.stdout")|controls_failed_by_name=$(grep -c '^CONTROL|' "$R/$e.stdout")|wrongly_accepted=$(grep -c 'CONTROL_ACCEPTED_WRONGLY' "$R/$e.stdout")|stdout_sha256=$(sha256sum "$R/$e.stdout" | cut -d' ' -f1)|json=0"
done
cmp -s "$R/twens03.stdout" "$G/BASELINE.out" && row "BASELINE_VS_FILED|engine=twens03|equal=1|json=0" || row "BASELINE_VS_FILED|engine=twens03|equal=0|json=0"
for e in twens04 twens04-memo; do
  cmp -s "$R/twens03.stdout" "$R/$e.stdout" && row "STDOUT_VS_03|engine=$e|equal=1|json=0" || row "STDOUT_VS_03|engine=$e|equal=0|json=0"
done
# 2. cross-engine: every run file of 0.4.0 memo=1 equals 0.3.0's after the head row
for f in a_ref a_ref_t4 a_p1 a_p2 b_ref b_q1 b_q2 b_q3; do
  if cmp -s <(grep -v '^TWB_HEAD|' "$R/twens03/$f.hbp") <(grep -v '^TWB_HEAD|' "$R/twens04-memo/$f.hbp"); then eq=1; else eq=0; fi
  row "CROSS|file=$f|memo_vs_03_after_head=$eq|rows=$(grep -vc '^TWB_HEAD|' "$R/twens03/$f.hbp")|json=0"
done
# 3. the comparator across engines: reuse parts against the no-reuse union, and the reverse; stair on reuse against no-reuse
X=python3; C="$G/ens_merge_check.py"
cm() { local tag=$1; shift; out=$($X -I "$C" "$@" 2>&1); rc=$?; row "MERGE|case=$tag|rc=$rc|$(echo "$out" | tr '\n' ' ' | tr -s ' ' | cut -c1-400)"; }
cm union_ref03_parts_memo "$R/twens03/a_ref.hbp" "$R/twens04-memo/a_p1.hbp" "$R/twens04-memo/a_p2.hbp"
cm union_refmemo_parts03 "$R/twens04-memo/a_ref.hbp" "$R/twens03/a_p1.hbp" "$R/twens03/a_p2.hbp"
cm union_ref03_parts_memo_b "$R/twens03/b_ref.hbp" "$R/twens04-memo/b_q3.hbp" "$R/twens04-memo/b_q1.hbp" "$R/twens04-memo/b_q2.hbp"
cm stair_memo_vs_03 --stair "$R/twens04-memo/a_stair.hbp" "$R/twens03/a_ref.hbp" "$R/twens03/a_p1.hbp"
# 4. a batch with heavy reuse (LOCK and VNC, 20,000 samples) at the same allowed point, then the change's own planted faults
C3='1099511627776:0:0'
J="N=81 delta=1/2 u=1 y=1/18 seed=20261105 dtden=64 steps=0,32,64 ctrl=$C3;$C3;$C3 mask=VNC,LOCK"
mkdir -p "$R/heavy"
"$R/bin/twens03" run $J start=0 count=20000 threads=4 > "$R/heavy/ref03.hbp" 2> "$R/heavy/ref03.err"
for e in twens04-memo mut-F1_key_merges_two_starts-memo mut-F3_dropped_count-memo; do
  "$R/bin/$e" run $J start=0 count=7000 threads=3 > "$R/heavy/$e-p1.hbp" 2> "$R/heavy/$e-p1.err"; r1=$?
  "$R/bin/$e" run $J start=7000 count=13000 threads=2 > "$R/heavy/$e-p2.hbp" 2> "$R/heavy/$e-p2.err"; r2=$?
  row "HEAVY_RUN|engine=$e|rc=$r1,$r2|memo_rows=$(cat "$R/heavy/$e-p1.err" "$R/heavy/$e-p2.err" | grep -c '^TWB_MEMO')|json=0"
  grep -h '^TWB_MEMO' "$R/heavy/$e-p1.err" "$R/heavy/$e-p2.err" | head -4 | cut -c1-300 | sed 's/^/HEAVY_MEMO_ROW|/' | tee -a "$R/GATE-RUN.hbp"
  cm "heavy_union_ref03_parts_$e" "$R/heavy/ref03.hbp" "$R/heavy/$e-p1.hbp" "$R/heavy/$e-p2.hbp"
done
cd "$R" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
row "GATE_RUN_DONE|sha256sums=$(sha256sum "$R/SHA256SUMS" | cut -d' ' -f1)|json=0"
