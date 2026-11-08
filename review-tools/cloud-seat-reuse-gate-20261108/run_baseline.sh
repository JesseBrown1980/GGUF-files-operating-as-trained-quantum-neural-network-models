#!/usr/bin/env bash
# The no-reuse identity on twens as it stands: disjoint sample-index ranges, added, equal one run over their union.
# usage: run_baseline.sh PATH_TO_TWENS OUT_DIR
set -euo pipefail
T=$1; O=$2; H=$(cd "$(dirname "$0")" && pwd); mkdir -p "$O"
C='1099511627776:0:0'
J1="N=81 delta=1/2 u=1 y=1/18 seed=20261105 dtden=64 steps=0,32,64 ctrl=$C;$C;$C mask=VNC,V1,V0,FLIP,LOCK,MODE0,NL"
"$T" run $J1 start=0 count=96 threads=1 > "$O/a_ref.hbp"
"$T" run $J1 start=0 count=96 threads=4 > "$O/a_ref_t4.hbp"
"$T" run $J1 start=0 count=40 threads=2 > "$O/a_p1.hbp"
"$T" run $J1 start=40 count=56 threads=3 > "$O/a_p2.hbp"
cmp <(grep -v '^TWB_HEAD|' "$O/a_ref.hbp") <(grep -v '^TWB_HEAD|' "$O/a_ref_t4.hbp") && echo "BASE|thread_invariant=1|json=0"
python3 -I "$H/ens_merge_check.py" "$O/a_ref.hbp" "$O/a_p1.hbp" "$O/a_p2.hbp"
J2="N=729 delta=-1/4 u=1 y=1/27 seed=7 dtden=128 steps=0,16,48,64 ctrl=$C;$C;$C;$C mask=VNC,V1,V0,RN,FLIP,LOCK,MODE0,NL"
"$T" run $J2 start=1000 count=50 threads=3 > "$O/b_ref.hbp"
"$T" run $J2 start=1000 count=7 threads=1 > "$O/b_q1.hbp"
"$T" run $J2 start=1007 count=30 threads=2 > "$O/b_q2.hbp"
"$T" run $J2 start=1037 count=13 threads=4 > "$O/b_q3.hbp"
python3 -I "$H/ens_merge_check.py" "$O/b_ref.hbp" "$O/b_q3.hbp" "$O/b_q1.hbp" "$O/b_q2.hbp"
# the comparator's own controls: each must fail by its name
python3 -I - "$O" <<'PY'
import re, sys
o = sys.argv[1]
L = open(o + '/a_p2.hbp').read().split('\n')
i = next(k for k, l in enumerate(L) if l.startswith('TWB|') and '|variant=V1|' in l)
for name, key in (('bad_n', 'n'), ('bad_sum', 'xnc')):
    pat = r'\|%s=(-?\d+)\|' % key
    M = L[:]
    M[i] = re.sub(pat, lambda m: '|%s=%d|' % (key, int(m.group(1)) + 1), L[i], count=1)
    open('%s/a_%s.hbp' % (o, name), 'w').write('\n'.join(M))
PY
ctl() { if python3 -I "$H/ens_merge_check.py" "$O/a_ref.hbp" "$@" > "$O/ctl.out"; then echo "CONTROL_ACCEPTED_WRONGLY|$*"; exit 1; fi; echo "CONTROL|$(cat "$O/ctl.out")"; }
ctl "$O/a_p1.hbp" "$O/a_bad_n.hbp"
ctl "$O/a_p1.hbp" "$O/a_bad_sum.hbp"
ctl "$O/a_p1.hbp" "$O/a_p1.hbp"
ctl "$O/a_p1.hbp"
python3 -I - "$O" <<'PY'
import sys
o = sys.argv[1]
L = open(o + '/a_p2.hbp').read().split('\n')
i = next(k for k, l in enumerate(L) if l.startswith('TWB|') and '|variant=V1|' in l)
L[i] = L[i].replace('|xnc=', '|xnc_gone=', 1)
open(o + '/a_bad_field.hbp', 'w').write('\n'.join(L))
PY
ctl "$O/a_p1.hbp" "$O/a_bad_field.hbp"
# the staircase mode on a synthetic staircase: step 0 at count 96, steps 32 and 64 at count 40, both from start 0
{ grep '^TWB_HEAD|' "$O/a_ref.hbp"
  grep -E '^(TWB|TWB_ROUND|TWB_PAIR|TWB_PAIR_ROUND|TWENS|TWPAIR)\|' "$O/a_ref.hbp" | grep '|step=0|'
  grep -E '^(TWB|TWB_ROUND|TWB_PAIR|TWB_PAIR_ROUND|TWENS|TWPAIR)\|' "$O/a_p1.hbp" | grep -v '|step=0|'; } > "$O/a_stair.hbp"
python3 -I "$H/ens_merge_check.py" --stair "$O/a_stair.hbp" "$O/a_ref.hbp" "$O/a_p1.hbp"
sed '0,/|step=32|variant=V0|/{s/\(|step=32|variant=V0|.*|f=\)\(-\?[0-9]\+\)/\1999/}' "$O/a_stair.hbp" > "$O/a_stair_bad.hbp"
if python3 -I "$H/ens_merge_check.py" --stair "$O/a_stair_bad.hbp" "$O/a_ref.hbp" "$O/a_p1.hbp" > "$O/ctl.out"; then echo "CONTROL_ACCEPTED_WRONGLY|stair"; exit 1; fi
echo "CONTROL|$(cat "$O/ctl.out")"
# completeness controls (added 2026-11-08 after Cloud C's report on PR #15): a staircase missing one real row, a
# reference count no row uses, and a union part missing its noiseless rows; each must fail by its name
sctl() { if python3 -I "$H/ens_merge_check.py" "$@" > "$O/ctl.out"; then echo "CONTROL_ACCEPTED_WRONGLY|$*"; exit 1; fi; echo "CONTROL|$(cat "$O/ctl.out")"; }
grep -v '^TWB|.*|step=64|variant=LOCK|' "$O/a_stair.hbp" > "$O/a_stair_drop.hbp"
[ "$(wc -l < "$O/a_stair_drop.hbp")" = "$(( $(wc -l < "$O/a_stair.hbp") - 1 ))" ]
sctl --stair "$O/a_stair_drop.hbp" "$O/a_ref.hbp" "$O/a_p1.hbp"
"$T" run $J1 start=0 count=50 threads=1 > "$O/a_c50.hbp"
sctl --stair "$O/a_stair.hbp" "$O/a_ref.hbp" "$O/a_p1.hbp" "$O/a_c50.hbp"
grep -v '^TWB_NL|' "$O/a_p2.hbp" > "$O/a_p2_nonl.hbp"
sctl "$O/a_ref.hbp" "$O/a_p1.hbp" "$O/a_p2_nonl.hbp"
echo "BASE_DONE|json=0"
