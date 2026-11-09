#!/usr/bin/env bash
# The sabotage suite of the stripe-phase reader: seven planted faults, each of which the reader must catch. Every case
# prints CAUGHT or MISSED; the suite exits 0 only when all seven are CAUGHT. No engine runs here: the streams are
# synthetic (the stage A emulator) and the campaign is fabricated (reader/b/tests/campaign.py).
#
#   CARGO_TARGET_DIR=<outside the repo> reader/sabotage/run.sh
#
# Optional: STRIPES_SABOTAGE_WORK (work folder, kept), STRIPES_CAMPAIGN (an existing campaign folder),
# STRIPES_EXCL_DIR (real dumps at the excluded points, X1.0.txt; adds one more stage A check).
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

(cd "$READER/a" && cargo build --release --offline --locked -q) || { echo "stage A build failed" >&2; exit 2; }
rm -rf "$WORK/streams"
(cd "$READER/a" && STRIPES_EMIT_DIR="$WORK/streams" cargo test --release --offline --locked -q --test synthetic \
  emit_streams_for_the_independent_check -- --ignored >/dev/null) || { echo "stream emitter failed" >&2; exit 2; }
CAMPAIGN=${STRIPES_CAMPAIGN:-$WORK/campaign}
[ -d "$CAMPAIGN/agg" ] || $PY -I "$READER/b/tests/campaign.py" --out "$CAMPAIGN" >/dev/null || exit 2
inputs() { echo --agg "$1/agg" --runs "$1/run" --qe "$1/QE.hbp" --cost "$1/QE-COST.hbp" --guard "$1/GUARD.hbp"; }
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
ra "$S/table_P13_0_r2.txt" --point P13 --call 0 --side "$WORK/good.side" > "$WORK/p13.agg" || ok=1
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
C=$(copy c2b); $EDIT block --campaign "$C" --point P01 --call 0 --op swap_sec --rehash && stop sha256sums $PY -I "$B" read $(inputs "$C") --out "$WORK/r2b.hbp" || r=1
report $r swapped_sector_counts "stage B refuses the block when SHA256SUMS is rewritten (agg_sha256) and when AGG_END is forged (sha256sums)"

# 3. A dropped call.
r=0
C=$(copy c3a); $EDIT drop --campaign "$C" --point P01 --call 17 && stop sha256sums $PY -I "$B" read $(inputs "$C") --out "$WORK/r3a.hbp" || r=1
C=$(copy c3b); $EDIT drop --campaign "$C" --point P01 --call 17 --sums && stop seed_dropped_call $PY -I "$B" read $(inputs "$C") --out "$WORK/r3b.hbp" || r=1
report $r dropped_call "SHA256SUMS lists the call (sha256sums); with the list rewritten, rule SEED finds call 17 missing (seed_dropped_call)"

# 4. An altered TWB sum.
r=0
$EDIT stream --in "$S/good_y40.txt" --out "$WORK/s4a.txt" --op twb_br && stop summary_mismatch ra "$WORK/s4a.txt" "${TSYN[@]}" || r=1
$EDIT stream --in "$S/table_P13_0_r2.txt" --out "$WORK/s4b.txt" --op round_rb_br && stop summary_mismatch ra "$WORK/s4b.txt" --point P13 --call 0 --side "$WORK/s4b.side" || r=1
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
report $r report_read_promoted "a module scoring E15's RP13 cross-read is refused (scoring_table); in a READ file, E17 pi_t1 scored with why=X08 fails audit (scored_read), and with why=unexposed (scoring_table)"

# 7. A falsifier evaluated on a read-and-report read.
r=0
stop falsifier $PY -I "$HERE/patch.py" falsify_report $(inputs "$CAMPAIGN") --out "$WORK/r7a.hbp" || r=1
$EDIT read --in "$CLEAN" --out "$WORK/r7b.hbp" --op falsify && stop falsifier $PY -I "$B" audit --read "$WORK/r7b.hbp" || r=1
report $r falsifier_on_report_read "a module naming E17's read-and-report pi_t1 as a falsifier is refused (falsifier); so is a READ file whose E17 VERDICT does (falsifier)"

for d in c1c c1d c2a c2b c3a c3b c5; do rm -rf "${WORK:?}/$d"; done
echo "SABOTAGE|cases=7|caught=$((7 - MISSED))|missed=$MISSED|engine_runs=0|json=0"
[ "$MISSED" = 0 ]
