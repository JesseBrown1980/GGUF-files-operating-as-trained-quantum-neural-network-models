#!/usr/bin/env bash
# The sabotage suite of the stripe-phase reader: twelve planted faults, each of which the reader must catch, and one
# documented fault it cannot see (case 13). Every case prints CAUGHT or MISSED (case 13 NOT_VISIBLE or MISSED); the
# suite exits 0 only when all twelve are CAUGHT and case 13 reads as documented. No engine runs here: the streams are
# synthetic (the stage A emulator) and the campaign is fabricated (reader/b/tests/campaign.py).
#
#   CARGO_TARGET_DIR=<outside the repo> reader/sabotage/run.sh
#
# Optional: STRIPES_SABOTAGE_WORK (work folder, kept), STRIPES_CAMPAIGN (an existing campaign folder),
# STRIPES_EXCL_DIR (real dumps at the excluded points, X1.0.txt; adds one more stage A check, 4c; a folder that
# reader/check/excl_unpack.py --out writes from reader/b/tests/data/excl serves).
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
READER=$(dirname "$HERE")
PY=${PYTHON:-python3}
: "${CARGO_TARGET_DIR:?set CARGO_TARGET_DIR to a folder outside the repo}"
export CARGO_TARGET_DIR
case "$CARGO_TARGET_DIR" in "$READER"*) echo "CARGO_TARGET_DIR must be outside the repo" >&2; exit 2;; esac
if [ -n "${STRIPES_SABOTAGE_WORK:-}" ]; then WORK=$STRIPES_SABOTAGE_WORK; mkdir -p "$WORK"; KEEP=1
else WORK=$(mktemp -d); KEEP=0; fi
cleanup() { [ "$KEEP" = 1 ] || rm -rf "$WORK"; }
trap cleanup EXIT
RA=$CARGO_TARGET_DIR/release/stripes-read-a
B=$READER/b/stripes_read_b/__main__.py
EDIT="$PY -I $HERE/edit.py"
MISSED=0

# Rust 1.81.0 as CI pins it (review N20), and the build of reader/README.md: the checkout path remapped to stage-a, so
# the binary's sha256 does not depend on where the checkout is (review M4) and a shared CARGO_TARGET_DIR keeps it.
export RUSTFLAGS="--remap-path-prefix=$(cd "$READER/a" && pwd)=stage-a"
(cd "$READER/a" && cargo +1.81.0 build --release --offline --locked -q) || { echo "stage A build failed" >&2; exit 2; }
rm -rf "$WORK/streams"
(cd "$READER/a" && STRIPES_EMIT_DIR="$WORK/streams" cargo +1.81.0 test --release --offline --locked -q --test synthetic \
  emit_streams_for_the_independent_check -- --ignored >/dev/null) || { echo "stream emitter failed" >&2; exit 2; }
CAMPAIGN=${STRIPES_CAMPAIGN:-$WORK/campaign}
[ -d "$CAMPAIGN/agg" ] || $PY -I "$READER/b/tests/campaign.py" --out "$CAMPAIGN" >/dev/null || exit 2
inputs() { echo --agg "$1/agg" --runs "$1/run" --qe "$1/QE.hbp" --cost "$1/QE-COST.hbp" --qe-rc "$1/QE-RC.hbp" --guard "$1/GUARD.hbp"; }
copy() { rm -rf "$WORK/$1"; cp -al "$CAMPAIGN" "$WORK/$1"; echo "$WORK/$1"; }

# stop WANT CMD...: CMD exits 3 with one STOP row whose reason is WANT.
stop() {
  local want=$1 out rc; shift
  out=$("$@" 2>/dev/null); rc=$?
  if [ "$rc" -eq 3 ] && grep -q "^STOP|.*|reason=$want|" <<<"$out"; then return 0; fi
  echo "    expected STOP $want, got rc=$rc: ${out:0:240}" >&2
  return 1
}
ra() { local f=$1; shift; "$RA" "$@" < "$f"; }
verdict_of() { grep "^STRIPES_VERDICT|row=$2|" "$1"; }
report() { if [ "$1" = 0 ]; then echo "CAUGHT $2: $3"; else echo "MISSED $2: $3"; MISSED=$((MISSED + 1)); fi; }

S=$WORK/streams
TSYN=(--point Tsyn --call 0)
# Baseline: the unsabotaged inputs are read, so every catch below is the fault's.
ok=0
ra "$S/good_y40.txt" "${TSYN[@]}" > "$WORK/good.agg" || ok=1
ra "$S/table_X0_5_r2.txt" --point X0 --call 5 --side "$WORK/good.side" > "$WORK/x0.agg" || ok=1
CLEAN=$WORK/READ-clean.hbp
$PY -I "$B" read $(inputs "$CAMPAIGN") --out "$CLEAN" > /dev/null || ok=1
$PY -I "$B" audit --read "$CLEAN" > /dev/null || ok=1
grep -q "^STRIPES_VERDICT|row=E02|.*|verdict=MET|" "$CLEAN" || ok=1
if [ "$ok" != 0 ]; then echo "BASELINE_FAILED: the clean inputs do not read" >&2; exit 2; fi
echo "BASELINE ok: synthetic streams read (exit 0), clean campaign READ file passes audit, E02 MET"

# 1. The sign of bi flipped on one exchange atom.
r=0
$EDIT stream --in "$S/good_y40.txt" --out "$WORK/s1a.txt" --op xatom_minus0 && stop bad_integer ra "$WORK/s1a.txt" "${TSYN[@]}" || r=1
$EDIT stream --in "$S/good_y40.txt" --out "$WORK/s1b.txt" --op xatom_flip && stop summary_mismatch ra "$WORK/s1b.txt" "${TSYN[@]}" || r=1
C=$(copy c1d); $EDIT block --campaign "$C" --point P02 --call 0 --op xatom_bi_nz --sums && stop agg_sha256 $PY -I "$B" read $(inputs "$C") --out "$WORK/r1d.hbp" || r=1
C=$(copy c1c); $EDIT block --campaign "$C" --point P02 --call 0 --op xatom_bi_nz --rehash --sums
if $PY -I "$B" read $(inputs "$C") --out "$WORK/r1c.hbp" > /dev/null; then
  verdict_of "$WORK/r1c.hbp" E02 | grep -q "|falsifier=[^|]*xbi_P02_t1_VNC[^|]*|verdict=NOT_MET|" || r=1
else r=1; fi
report $r bi_flip_on_exchange_atom "stage A STOPs on bi=-0 (bad_integer) and on a flipped nonzero bi (summary_mismatch); an edited block fails agg_sha256 (SHA256SUMS rewritten); a forged consistent block turns E02 NOT_MET (falsifier xbi_P02_t1_VNC)"

# 2. Two sector counts swapped.
r=0
C=$(copy c2a); $EDIT block --campaign "$C" --point P01 --call 0 --op swap_sec --sums && stop agg_sha256 $PY -I "$B" read $(inputs "$C") --out "$WORK/r2a.hbp" || r=1
rm -f "$WORK/r2b.hbp" "$WORK/r2c.hbp"
C=$(copy c2b); $EDIT block --campaign "$C" --point P01 --call 0 --op swap_sec --rehash && stop sha256sums $PY -I "$B" read $(inputs "$C") --out "$WORK/r2b.hbp" || r=1
# review M3: no flag skips SHA256SUMS. verify of the clean READ file on case 2b's inputs stops at the same check, and
# the flag that skipped it (--no-sums, removed) is a usage STOP for read and verify; no READ file is written
stop sha256sums $PY -I "$B" verify --read "$CLEAN" $(inputs "$C") || r=1
stop usage $PY -I "$B" read $(inputs "$C") --out "$WORK/r2c.hbp" --no-sums || r=1
stop usage $PY -I "$B" verify --read "$CLEAN" $(inputs "$C") --no-sums || r=1
[ ! -e "$WORK/r2b.hbp" ] && [ ! -e "$WORK/r2c.hbp" ] || r=1
report $r swapped_sector_counts "stage B refuses the block when SHA256SUMS is rewritten (agg_sha256) and when AGG_END is forged (sha256sums), in read and in verify; --no-sums is a usage STOP for both, and no READ file is written"

# 3. A dropped call.
r=0
C=$(copy c3a); $EDIT drop --campaign "$C" --point P01 --call 17 && stop sha256sums $PY -I "$B" read $(inputs "$C") --out "$WORK/r3a.hbp" || r=1
C=$(copy c3b); $EDIT drop --campaign "$C" --point P01 --call 17 --sums && stop seed_dropped_call $PY -I "$B" read $(inputs "$C") --out "$WORK/r3b.hbp" || r=1
report $r dropped_call "SHA256SUMS lists the call (sha256sums); with the list rewritten, rule SEED finds call 17 missing (seed_dropped_call)"

# 4. An altered TWB sum.
r=0
$EDIT stream --in "$S/good_y40.txt" --out "$WORK/s4a.txt" --op twb_br && stop summary_mismatch ra "$WORK/s4a.txt" "${TSYN[@]}" || r=1
$EDIT stream --in "$S/table_X0_5_r2.txt" --out "$WORK/s4b.txt" --op round_rb_br && stop summary_mismatch ra "$WORK/s4b.txt" --point X0 --call 5 --side "$WORK/s4b.side" || r=1
if [ -n "${STRIPES_EXCL_DIR:-}" ] && [ -f "$STRIPES_EXCL_DIR/X1.0.txt" ]; then
  $EDIT stream --in "$STRIPES_EXCL_DIR/X1.0.txt" --out "$WORK/s4c.txt" --op twb_br && stop summary_mismatch ra "$WORK/s4c.txt" --point X1 --call 0 --side "$WORK/s4c.side" || r=1
  rm -f "$WORK/s4c.txt"
fi
report $r altered_TWB_sum "stage A recomputes every TWB and TWB_ROUND field from the per-sample rows (summary_mismatch)"

# 5. A wrong TWB_HEAD version.
r=0
$EDIT stream --in "$S/good_y40.txt" --out "$WORK/s5a.txt" --op version_030 && stop head_version ra "$WORK/s5a.txt" "${TSYN[@]}" || r=1
C=$(copy c5); $EDIT block --campaign "$C" --point P01 --call 3 --op version_030 --rehash --sums && stop head_version $PY -I "$B" read $(inputs "$C") --out "$WORK/r5.hbp" || r=1
report $r wrong_TWB_HEAD_version "stage A STOPs on version=0.3.0 (head_version); stage B checks AGG_TWB_HEAD of a forged block too (head_version)"

# 6. A read-and-report read promoted to scored.
r=0
stop scoring_table $PY -I "$HERE/patch.py" promote $(inputs "$CAMPAIGN") --out "$WORK/r6a.hbp" || r=1
$EDIT read --in "$CLEAN" --out "$WORK/r6b.hbp" --op promote && stop scored_read $PY -I "$B" audit --read "$WORK/r6b.hbp" || r=1
$EDIT read --in "$CLEAN" --out "$WORK/r6c.hbp" --op promote_why && stop scoring_table $PY -I "$B" audit --read "$WORK/r6c.hbp" || r=1
# 6d (review N19): the other way, a scored read demoted: E04's first MET signflip read filed as read-and-report
# (scored=0, why=X08, verdict=REPORT), its VERDICT counts made to agree; only the SCORING table sees it
$EDIT read --in "$CLEAN" --out "$WORK/r6d.hbp" --op demote && stop scoring_table $PY -I "$B" audit --read "$WORK/r6d.hbp" || r=1
report $r report_read_promoted "a module scoring E15's RP13 cross-read is refused (scoring_table); in a READ file, E17 pi_t1 scored with why=X08 fails audit (scored_read), and with why=unexposed (scoring_table); a scored E04 read demoted to read-and-report, its VERDICT agreeing, fails audit (scoring_table)"

# 7. A falsifier evaluated on a read-and-report read.
r=0
stop falsifier $PY -I "$HERE/patch.py" falsify_report $(inputs "$CAMPAIGN") --out "$WORK/r7a.hbp" || r=1
$EDIT read --in "$CLEAN" --out "$WORK/r7b.hbp" --op falsify && stop falsifier $PY -I "$B" audit --read "$WORK/r7b.hbp" || r=1
report $r falsifier_on_report_read "a module naming E17's read-and-report pi_t1 as a falsifier is refused (falsifier); so is a READ file whose E17 VERDICT does (falsifier)"

# 8. Rule STOP without its evidence: a record or a batch dropped with no exit 4 filed, data already seen filed as an
# attempt, an attempt that is not a row, an exit 4 without its TWB_FAULT row, a crash taken for an engine stop, and a
# try filed with steps other than rule STOP gives it (the trailer and the .rc file name the steps of each try).
r=0
for op_want in dump_no_attempt:stop_attempt_count dump_block_as_attempt:stop_attempt_file \
               dump_garbage_attempt:stop_attempt_count dump_garbage_attempt_short:stop_attempt_file \
               dump_stop_without_fault:stop_engine_stderr dump_attempt_wrong_steps:stop_attempt_steps \
               dump_lost_last_try_steps:stop_attempt_steps run_empty_no_attempt:stop_attempt_count \
               run_truncated_no_attempt:stop_attempt_count run_crash:run_rc \
               run_attempt_wrong_steps:stop_attempt_steps; do
  op=${op_want%%:*}; want=${op_want#*:}
  C=$(copy c8); $EDIT stop --campaign "$C" --op "$op" && stop "$want" $PY -I "$B" read $(inputs "$C") --out "$WORK/r8.hbp" || { echo "    case 8 $op" >&2; r=1; }
done
report $r stop_without_evidence "probes A (P05 call 7 cut to 3 records, no attempt: stop_attempt_count), B (the complete block filed as attempt1: stop_attempt_file) and C (an attempt holding 'anything': stop_attempt_count beside the complete block, stop_attempt_file beside a rerun); an exit 4 with an empty engine stderr (stop_engine_stderr); an attempt filed with the rerun's steps, and a lost call whose last try ran 2 records (stop_attempt_steps); an R2 batch empty or cut with no attempts (stop_attempt_count); rc=137 (run_rc); an R2 attempt filed with the rerun's steps (stop_attempt_steps)"

# 9. QE: a panic with rc=101 leaves that command's reads NOT_MEASURED and the read goes on; the same panic text filed
# with rc=0 stops (qe_stderr); an altered B turns Q02 NOT_MET; QE-RC.hbp short of a command stops (qe_rc).
r=0
C=$(copy c9a); $EDIT qe --campaign "$C" --op panic_rc101
if $PY -I "$B" read $(inputs "$C") --out "$WORK/r9a.hbp" > /dev/null; then
  for k in 09 10 11 12; do grep -q "^STRIPES_READ|row=Q01|read=zero$k|.*|verdict=NOT_MEASURED|" "$WORK/r9a.hbp" || r=1; done
  grep -q "^STRIPES_READ|row=Q01|read=zero08|.*|verdict=MET|" "$WORK/r9a.hbp" || r=1
  grep -q "^STRIPES_READ_NOTE|label=qe_rc|text=[^|]*sector_6561_[^|]*rc=101" "$WORK/r9a.hbp" || r=1
  $PY -I "$B" audit --read "$WORK/r9a.hbp" > /dev/null || r=1
else r=1; fi
C=$(copy c9b); $EDIT qe --campaign "$C" --op panic_rc0 && stop qe_stderr $PY -I "$B" read $(inputs "$C") --out "$WORK/r9b.hbp" || r=1
C=$(copy c9c); $EDIT qe --campaign "$C" --op altered_B
if $PY -I "$B" read $(inputs "$C") --out "$WORK/r9c.hbp" > /dev/null; then
  verdict_of "$WORK/r9c.hbp" Q02 | grep -q "|falsifier=par3:[^|]*|verdict=NOT_MET|" || r=1
else r=1; fi
C=$(copy c9d); $EDIT qe --campaign "$C" --op rc_row_missing && stop qe_rc $PY -I "$B" read $(inputs "$C") --out "$WORK/r9d.hbp" || r=1
report $r qe_exit_and_altered_B "a 6561 sector panic with rc=101 leaves its 4 reads NOT_MEASURED (zero09-zero12) and the READ file passes audit; the panic text with rc=0 is a STOP qe_stderr; B at (81, -1/54, t=2) moved by 1e-5 turns Q02 NOT_MET (falsifier par3); QE-RC.hbp short of a row is a STOP qe_rc"

# 10. Stray floats (the owner's ruling of 2026-11-09). At run time every float, bool or true division that meets a
# checked integer pair raises TypeError, where fractions.Fraction lets the owner's two examples through. In the source,
# a float planted in a copy of the live stage B is found by the scan of b/tests/test_nofloat.py, file by file.
r=0
$EDIT floats --work "$WORK/f10" || r=1
out=$($PY -I "$WORK/f10/qint_floats.py" "$READER/b" 2>&1)
{ [ "$(grep -c '^REFUSED|' <<<"$out")" = 27 ] && ! grep -q '^PASSED_THROUGH|' <<<"$out"; } || { echo "    $out" >&2; r=1; }
out=$($PY -I "$WORK/f10/fraction_floats.py" 2>&1)
[ "$(grep -c '^PASSED_THROUGH|' <<<"$out")" = 2 ] || { echo "    $out" >&2; r=1; }
out=$($PY -I - "$READER/b" "$WORK/f10/b" <<'PYEOF'
import os, sys
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
from tests.test_nofloat import violations
root = sys.argv[2]
for d in (root, os.path.join(root, "stripes_read_b"), os.path.join(root, "tests")):
    for nm in sorted(os.listdir(d)):
        if nm.endswith(".py") and violations(os.path.join(d, nm)):
            print("FOUND|file=%s|json=0" % os.path.relpath(os.path.join(d, nm), root))
PYEOF
)
want=$(printf 'FOUND|file=%s|json=0\n' e2e.py stripes_read_b/common.py stripes_read_b/exact.py stripes_read_b/qint.py stripes_read_b/rows_q.py stripes_read_b/series.py)
[ "$out" = "$want" ] || { echo "    scan found: $out" >&2; r=1; }
rm -rf "$WORK/f10"
report $r stray_float "27 stray floats, bools, true divisions, Fractions, Decimals and complexes against qint pairs, Iv, Rad and fmt each raise TypeError (Fraction(1,3)*0.5 and Fraction(0.1) pass through fractions.Fraction); 6 planted source faults (true division, a float literal, import fractions, import math, float(), round()) are each found by the source scan"

# 11. A side file forged with every hash made to agree (ensemble review M4): one br of P08 call 0 moved by 1, its
# AGG_SIDE bytes and sha256, the block's AGG_END and the point's SHA256SUMS rewritten. The side file's sums no longer
# equal the block's AGG_SUM, so stage B stops (side_sums).
r=0
C=$(copy c11); $EDIT side --campaign "$C" && stop side_sums $PY -I "$B" read $(inputs "$C") --out "$WORK/r11.hbp" || r=1
report $r side_file_forged "a P08 side file edited with its row, AGG_END and SHA256SUMS forged: its sums differ from the block's AGG_SUM (side_sums)"

# 12. A moved frozen file (review N1, M8). edit.py copies reader/a and reader/b into a git repository of their own,
# beside a copy of the frozen file and its README with one of them moved. The repo's frozen files are only read. The
# unmoved copy passes audit and gets past the frozen check in read; each moved copy stops there (frozen_sha256).
r=0
F12=$WORK/f12
rm -f "$WORK/r12a.hbp" "$WORK/r12d.hbp"
M=$($EDIT frozen --work "$F12" --op none) && $PY -I "$M" audit --read "$CLEAN" > /dev/null || r=1
# the unmoved copy's read passes its tree checks and the frozen check and reaches rule GUARD: a guard file not there
stop FileNotFoundError $PY -I "$M" read --agg "$CAMPAIGN/agg" --runs "$CAMPAIGN/run" --qe "$CAMPAIGN/QE.hbp" \
  --cost "$CAMPAIGN/QE-COST.hbp" --qe-rc "$CAMPAIGN/QE-RC.hbp" --guard "$F12/no_such_guard.hbp" --out "$WORK/r12a.hbp" || r=1
M=$($EDIT frozen --work "$F12" --op byte) && stop frozen_sha256 $PY -I "$M" read $(inputs "$CAMPAIGN") --out "$WORK/r12a.hbp" || r=1
M=$($EDIT frozen --work "$F12" --op byte) && stop frozen_sha256 $PY -I "$M" audit --read "$CLEAN" || r=1
M=$($EDIT frozen --work "$F12" --op crlf) && stop frozen_sha256 $PY -I "$M" audit --read "$CLEAN" || r=1
M=$($EDIT frozen --work "$F12" --op readme) && stop frozen_sha256 $PY -I "$M" verify --read "$CLEAN" $(inputs "$CAMPAIGN") || r=1
M=$($EDIT frozen --work "$F12" --op no_readme) && stop frozen_sha256 $PY -I "$M" read $(inputs "$CAMPAIGN") --out "$WORK/r12d.hbp" || r=1
[ ! -e "$WORK/r12a.hbp" ] && [ ! -e "$WORK/r12d.hbp" ] || r=1
rm -rf "$F12"
report $r frozen_file_moved "a copy of stage B beside the frozen file with one digit moved stops in read and audit (frozen_sha256), with CRLF line ends in audit, with one byte of the frozen README moved in verify, and with no README in read; no READ file is written; the unmoved copy passes audit, and its read gets past the frozen check"

# 13. Not visible, by design (review N17): case 2's sector swap with the block, its AGG_END and the point's SHA256SUMS
# all forged. Nothing in the aggregates can see it: the READ file passes audit with the same 26 VERDICT rows, and
# the only STRIPES_READ rows that move are E07's at P01 (the lattice read's detail and lk_x2_P01_t1_LOCK's reported
# value). This case is not counted as CAUGHT: it prints NOT_VISIBLE when exactly that holds, else MISSED (the limit
# moved, so the README's statement of it must change). The defense is the run plan's: commit the aggregates and their
# sums with the run, beside the stream hashes stage A prints (reader/README.md, the sabotage suite).
r=0
C=$(copy c13); $EDIT block --campaign "$C" --point P01 --call 0 --op swap_sec --rehash --sums || r=1
if [ "$r" = 0 ] && $PY -I "$B" read $(inputs "$C") --out "$WORK/r13.hbp" > /dev/null && $PY -I "$B" audit --read "$WORK/r13.hbp" > /dev/null; then
  cmp -s <(grep '^STRIPES_VERDICT|' "$CLEAN") <(grep '^STRIPES_VERDICT|' "$WORK/r13.hbp") || r=1
  moved=$(diff <(grep '^STRIPES_READ|' "$CLEAN") <(grep '^STRIPES_READ|' "$WORK/r13.hbp") | grep '^>' | cut -d'|' -f2,3 | sort -u | tr '\n' ' ')
  [ "$moved" = "row=E07|read=lk_lat_P01_t1_LOCK row=E07|read=lk_x2_P01_t1_LOCK " ] || { echo "    rows moved: $moved" >&2; r=1; }
else r=1; fi
if [ "$r" = 0 ]; then
  echo "NOT_VISIBLE swapped_sector_counts_fully_forged: case 2's swap with the block, AGG_END and SHA256SUMS forged reads with the same 26 VERDICT rows and passes audit; only E07 at P01 moves (lk_lat_P01_t1_LOCK detail, lk_x2_P01_t1_LOCK value); the defense is the committed aggregates and sums"
else
  echo "MISSED swapped_sector_counts_fully_forged: the documented not-visible case no longer reads as documented"; MISSED=$((MISSED + 1))
fi

for d in c1c c1d c2a c2b c3a c3b c5 c8 c9a c9b c9c c9d c11 c13; do rm -rf "${WORK:?}/$d"; done
echo "SABOTAGE|cases=12|caught=$((12 - MISSED))|missed=$MISSED|not_visible_documented=1|engine_runs=0|json=0"
[ "$MISSED" = 0 ]
