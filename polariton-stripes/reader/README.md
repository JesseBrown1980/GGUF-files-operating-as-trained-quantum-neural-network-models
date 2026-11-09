# polariton-stripes/reader: the integer reader of the stripe-phase prediction

This folder reads the runs of `PREDICTION-STRIPE-PHASE.hbp` (frozen at 1977d45, sha256 `3398b073...`) and writes `READ-STRIPE-PHASE.hbp`. It uses integers and exact rationals only (rule DECIMAL). Nothing here runs an engine. The tests use synthetic streams, a fabricated campaign, and real dumps and QE rows at the excluded points only (N = 27, delta = 1/4, y = 1/40 and y = 0; QE at N = 9, delta = 1/3).

- `a/`: stage A, `stripes-read-a` 0.1.0, Rust 1.81, no dependencies, its own `[workspace]`. It reads one twens 0.4.0 dump stream and writes one aggregate block.
- `AGG-FORMAT.md`: the full grammar of the aggregate block, the side file and the STOP row. Stage B reads only what it defines.
- `b/`: stage B, `stripes-read-b` 0.1.0, Python 3 (int and `fractions.Fraction` only, run with `python3 -I`). It reads the aggregates, the run receipts and the QE receipts and applies every STRIPES_PREDICT row.
- `check/`: the independent check of stage A (`check_a.py`, `compare.py`) and `no_float.sh`.
- `sabotage/run.sh`: seven planted faults; the reader must catch each one.
- `.github/workflows/polariton-stripes.yml` (at the repo root): runs all of it on every push and pull request that touches `polariton-stripes/`.

## Stage A: one dump stream in, one aggregate block out

```
stripes-read-a --point ID --call I [--side PATH] < dump
```

`ID` is P01-P14, or the excluded test points X1 and X0. Stage A:

- checks the head: version 0.4.0, the source and binary sha256, reserved=0, guard=active, float_used=0 on every row that prints it, and the seed against the seed string;
- checks the exact row sequence, key order and canonical integers, and, at a table point, the frozen command of that call (N, delta, y, seed string, start = 4096 I, count = 4096, mask, steps a prefix of the point's, ctrl 0:0:0);
- rebuilds every start, control seed and start bound from the draws, and recomputes every field of TWB, TWB_ROUND, TWENS, TWPAIR, TWB_PAIR and TWB_PAIR_ROUND from the per-sample rows;
- applies rules SECTOR and ATOMS, and prints per record and variant the 16 certified sector counts with A, the sign counts (atoms apart), the moment sums, the block sums for n = 4..4096, the comparison tables against VNC, the LOCK lattice test, the verbatim TWB_NL rows, sha256 of stdin, the TWB_HEAD line and the block's own sha256 (AGG_END);
- with `--side`, writes the per-index side file that row E04 pairs across P08 and P13. It is required at P08 and P13 for calls below 64.

Any difference is one STOP row (stdout and stderr) and exit 3; the reader still reads the rest of stdin. Exit 0 is a block. Exit 101 is a panic (overflow checks are on in release).

Build and test, always with the target folder outside the repo:

```
cd polariton-stripes/reader/a
export CARGO_TARGET_DIR=/abs/path/outside/the/repo/ra
cargo +1.81.0 fmt -- --check
cargo +1.81.0 clippy --locked --offline --release --all-targets -- -D warnings
cargo +1.81.0 test --locked --offline --release
STRIPES_EXCL_DIR=<folder with X1.0.txt X1.1.txt X0.0.txt X0.1.txt> cargo +1.81.0 test --locked --offline --release --test excluded_dumps -- --ignored
```

The 29 default tests need no engine. The three ignored tests read real dumps at the excluded points. The test emulator reproduces those dumps byte for byte, and the aggregates equal oracles written apart from the crate. This seat's build of stage A has sha256 `c8c3f0d12bcc5a21c703d0170b30637e8138b89004219b8d6562c43c36db7cf2`; a second build into another target folder gave the same hash.

## Stage B: the aggregates, the runs and the QE rows in, READ-STRIPE-PHASE.hbp out

```
python3 -I polariton-stripes/reader/b/stripes_read_b/__main__.py read \
  --agg receipts/agg --runs receipts/run --qe receipts/QE.hbp --cost receipts/QE-COST.hbp \
  --guard receipts/GUARD.hbp --out polariton-stripes/READ-STRIPE-PHASE.hbp
```

`read` does, in order:

1. Checks the frozen file's sha256, the point tables against the STRIPES_POINT rows, rule EXPOSED against X08 and the 15 QE commands against QR1-QR5.
2. Requires a `TWB_GUARD ... verdict=allowed` line for every (N, delta, y) used (rule GUARD).
3. Loads P01-P14 under rules SEED and STOP:
   - each point's SHA256SUMS against its call files;
   - every call file's trailer (`rc=E rc_reader=R`), AGG_END hash, `nl_sha256`, grammar and identities;
   - one block per call, the side files' sha256;
   - an engine stop (rc=4) loses that call's indices (NOT_MEASURED);
   - a point keeps only the records every call reached.
4. Loads R1-R4 (64 batches each, with their TWB_MEMO stderr) and the QE rows.
5. Applies Q01-Q07 (`rows_q.py`), E01-E08 (`rows_e_sym.py`) and E09-E19 (`rows_e_mom.py`) by rules READ3, H8, B16, SIGNFLIP, SE, STOP, SEED and EXPOSED.
6. Writes the file: a head, the inputs with their sha256, notes (calls read and lost per point, batches per run, missing QE rows, and the readings below), one STRIPES_READ row per read, one STRIPES_VERDICT row per STRIPES_PREDICT row in frozen order, and an end row with the file's sha256.

The other commands:

- `audit --read F` checks a READ file alone:
  - its hash, and one VERDICT per PREDICT row;
  - every VERDICT count and verdict recomputed from its READ rows by READ3;
  - falsifiers name scored reads only, with the frozen falsifier text;
  - each row's split into scored and read-and-report reads equals the reader's SCORING table.
  `read` runs the same audit before it writes.
- `verify --read F <inputs>` rebuilds the file from the inputs and compares it line for line.
- `scoring --read F` prints the SCORING table, to review a change of a row module.

The split into scored and read-and-report reads follows from the frozen text and rule EXPOSED alone, never from data; a campaign with lost calls, batches, records and QE rows gives the same table. So a read promoted to scored, or demoted, changes the table and stops the read.

Readings where the frozen text allows two (also written as STRIPES_READ_NOTE rows):

- E06, "0 mismatches ... with abs(B)>=2^-20": MET only if there is no mismatch where either B is big, MISS if there is one where both are, else NOT_RESOLVED.
- E16: the prediction names abs(Pi_V - Pi_VNC); the method's recipe (D+ - D-)/(2M) is half of it. MET only if both pass, MISS if the recipe fails, else NOT_RESOLVED.
- E15, "a scored cross-read other than predicted": a falsifier when certified (the read is MISS). A cross-read left NOT_RESOLVED leaves the row NOT_RESOLVED.
- E02 atom counts: the integer intervals are keyed by sample count and variant class. [0,51] is also read on the first-2^18 control set of each point, and a count is read only on its full nominal set.
- E04 ratios: MET inside [1/4 - 1/100 - 4SE, 1/4 + 1/100 + 4SE], MISS outside (the frozen band and falsifier).
- Pi_hat counts every sample, the atoms by their own sign states; H8 and B16 leave the atoms out.

Tests:

```
python3 -I polariton-stripes/reader/b/run_tests.py     # 219 unit tests, about 20 s
python3 -I polariton-stripes/reader/b/e2e.py           # the end-to-end test, about 2 min, about 0.3 GB of temporary files
```

`e2e.py` writes a synthetic campaign with `b/tests/campaign.py`:

- every point P01-P14 (8000 call files and the P08 and P13 side files);
- R1-R4 (64 batches each);
- QR1-QR5 (the 15 QE commands);
- the guard lines.

The values are small fabricated integers, not engine values. `read` must give one VERDICT row per STRIPES_PREDICT row, and `audit` and `verify` must pass. A second campaign then loses data in every way rule STOP allows:

- engine stops at P03 and P08;
- a rerun of P05 call 7 without its last record;
- an empty R2 batch;
- two missing QE rows.

It must give the same rows and the same SCORING table, with NOT_MEASURED reads where data was lost.

The part-1 commands of `b/run_b.py` (`tables`, `series`, `q`, `point`, `run`) check the tables, the frozen decimals and single inputs.

## The independent check of stage A

`check/check_a.py` is a second stage A written from the frozen rules and AGG-FORMAT.md in Python (int and Fraction only). `check/compare.py` reads each stream with both readers. A block must be equal byte for byte, and its side file too. A STOP must agree in every field but `detail`, with the reason the case expects.

```
cd polariton-stripes/reader/a
STRIPES_EMIT_DIR=/abs/streams cargo +1.81.0 test --locked --offline --release --test synthetic emit_streams_for_the_independent_check -- --ignored
python3 -I ../check/compare.py --ra $CARGO_TARGET_DIR/release/stripes-read-a --streams /abs/streams [--excl <dir of X1.i.txt, X0.i.txt>]
```

The emitter writes 67 synthetic cases:

- 14 blocks: designed streams at y = 1/40 and y = 0, the LOCK lattice, a VNC-only stream, and table-point streams at P13 (with side files, one with a dropped record), P14, P01, P07, P08, X1 and X0;
- 53 STOPs: every STOP path of the stream and the arguments, and the planted exchange-atom faults.

On this seat all 67 were equal, and so were the 4 real excluded dumps (71 of 71). CI runs the synthetic cases only.

## The sabotage suite

```
CARGO_TARGET_DIR=/abs/path/outside/the/repo/ra polariton-stripes/reader/sabotage/run.sh
```

It builds stage A, emits the synthetic streams, writes (or reuses, `STRIPES_CAMPAIGN`) the campaign, and checks first that the clean inputs read. Then it plants seven faults (`sabotage/edit.py` edits copies; `sabotage/patch.py` plants a fault in stage B's code). Each case prints CAUGHT or MISSED:

1. The sign of bi flipped on one exchange atom:
   - bi=-0 on a LOCK atom is a STOP `bad_integer`;
   - a flipped nonzero bi is a STOP `summary_mismatch`;
   - an edited block fails `agg_sha256`;
   - a forged, consistent block turns E02 NOT_MET, with its `xbi` read in the falsifier.
2. Two sector counts swapped: the block fails `agg_sha256` (with SHA256SUMS rewritten) or `sha256sums` (with AGG_END forged).
3. A dropped call: SHA256SUMS still lists it (`sha256sums`); with the list rewritten, rule SEED finds the call missing (`seed_dropped_call`).
4. An altered TWB or TWB_ROUND sum: a STOP `summary_mismatch`. With `STRIPES_EXCL_DIR` the suite also tries this on a real excluded dump.
5. A wrong TWB_HEAD version: a STOP `head_version` in stage A, and in stage B for a forged block.
6. A read-and-report read promoted to scored:
   - in a row module, stage B stops (`scoring_table`);
   - in a READ file, `audit` stops (`scored_read`, or `scoring_table` when its `why` is changed too).
7. A falsifier evaluated on a read-and-report read: stage B stops (`falsifier`), in a row module and in a READ file.

A forger who rewrites a block, its AGG_END and the point's SHA256SUMS together is not visible in the aggregates. The defense is to commit the aggregates and their sums with the run (run plan step 8), with the stream hashes stage A prints.

## No float

```
polariton-stripes/reader/check/no_float.sh
```

- The Rust of stage A, with comments and strings removed, is grepped for f32 and f64, float literals and float methods.
- Every .py under `reader/` is scanned as tokens for float and complex literals, float(), round, pow, math other than isqrt and gcd, numpy and the like.
- Then the AST check of `b/tests/test_nofloat.py` runs on every .py, which also bans true division outside `exact.div` and `**`.
- A self-test first plants one fault of each kind.

## The run, with this seat's binaries

The binaries are built under this seat's scratch folder, never inside the repo:

```
OUT=/tmp/claude-0/-home-user/b2fb539a-cb4d-5f0b-a22f-ca1a7fcb500d/scratchpad/stripes-build
T=$OUT/tw/release/twens                          # twens 0.4.0, sha256 33e62fbe0837aeddc916a57d67848338cbc258aa1dfb85a01cfba53fb8a4e03f
QE=$OUT/qe/release/polariton_first_correction    # sha256 6bf8ebf2309700cb5be4cce25d82e5c4ee70fbc49521d4d7686cfc1649aa0a21 (equal to the lane build)
RA=$OUT/ra/release/stripes-read-a                # stage A, sha256 c8c3f0d12bcc5a21c703d0170b30637e8138b89004219b8d6562c43c36db7cf2
SB="python3 -I $PWD/polariton-stripes/reader/b/stripes_read_b/__main__.py"
```

Never use `polariton-bridge/engines/ensemble/target/release/twens`, a stale 0.3.0 build. Rebuild with `(cd polariton-bridge/engines/ensemble && cargo build --release --locked --offline --target-dir $OUT/tw)` and `CARGO_TARGET_DIR=$OUT/qe cargo build --release --locked --bin polariton_first_correction`, and check both sha256 before use. Commit the reader with its sha256 before step 3 (run plan step 2).

All commands below run in `polariton-stripes/receipts/`:

```
mkdir -p polariton-stripes/receipts/run && cd polariton-stripes/receipts
g() { "$T" guard N=$1 delta=$2 y=$3 | tee -a GUARD.hbp | grep -q 'verdict=allowed'; }
```

Run `g` before every twens and QE command (rule GUARD), and stop on any refusal. Never pass `lift_reserved_guard`.

Quantum (run plan step 4): 15 commands, stdout to QE.hbp, stderr (the COST rows) to QE-COST.hbp. `q MODE N K delta y W times` guards (N, delta, y) first:

```
q() { g $2 $4 $5 && "$QE" "$@" >> QE.hbp 2>> QE-COST.hbp; }
for N in 81 729 6561; do q sector $N $N -1/4 0 6 1/2,1,2,4 || exit 1; done
for N in 81 729; do q point $N $N -1/4 0 6 1/2,1,2,4 || exit 1; done
for Y in 1/27 1/54 1/108 1/216; do q point 729 729 -1/4 $Y 6 1/8,1/4,1/2,1,2 || exit 1; done
q point 729 729 -1/4 -1/54 6 1/2,1,2 || exit 1
for Y in 1/27 1/108 1/216; do q point 81 81 -1/4 $Y 6 1/8,1/4,1/2,1 || exit 1; done
q point 81 81 -1/4 1/54 6 1/8,1/4,1/2,1,2,4 || exit 1
q point 81 81 -1/4 -1/54 6 1/2,1,2,4 || exit 1
```

Ensemble runs R1-R4 (run plan step 5), one at a time with threads=4:

```
run_pt() { id=$1 N=$2 d=$3 y=$4 C=$5 S=$6 K=$7; g $N $d $y || return 1
  for j in $(seq 0 63); do
    "$T" run N=$N delta=$d u=1 y=$y seed_string=stripes-ens-v1:N$N:d$d:y$y start=$((j*C/64)) count=$((C/64)) dtden=64 threads=4 steps=$S "ctrl=$K" mask=VNC memo=1 > run/$id.$j.hbp 2> run/$id.$j.err
  done; }
run_pt R1 729 -1/4 1/27  4194304  32,64,128 '0:0:0;0:0:0;0:0:0'
run_pt R2 729 -1/4 1/54  4194304  32,64,128 '0:0:0;0:0:0;0:0:0'
run_pt R3 729 -1/4 1/108 16777216 32,64,128 '0:0:0;0:0:0;0:0:0'
run_pt R4 81  -1/4 1/18  4194304  32,64     '0:0:0;0:0:0'
```

Dumps (run plan step 6). `points.txt` (id N delta y vnc_count all_variant_calls steps ctrl):

```
P01 1296 1/2 0 4194304 64 64,128,192,256 0:0:0;0:0:0;0:0:0;0:0:0
P02 1296 1/2 1/576 4194304 64 64,128,192,256 0:0:0;0:0:0;0:0:0;0:0:0
P03 1296 1/2 1/288 4194304 64 64,128,192,256 0:0:0;0:0:0;0:0:0;0:0:0
P04 1296 1/2 1/144 4194304 64 64,128,192,256 0:0:0;0:0:0;0:0:0;0:0:0
P05 1296 1/2 1/72 1048576 64 64,128,192,256 0:0:0;0:0:0;0:0:0;0:0:0
P06 1296 1/2 1/36 1048576 64 64,128,192,256 0:0:0;0:0:0;0:0:0;0:0:0
P07 729 -1/4 0 1048576 64 128,192,256 0:0:0;0:0:0;0:0:0
P08 729 -1/4 1/54 1048576 64 64,128,192,256 0:0:0;0:0:0;0:0:0;0:0:0
P09 121 1/2 0 1048576 64 64,128,192,256 0:0:0;0:0:0;0:0:0;0:0:0
P10 121 1/2 1/11 1048576 64 64,128,192,256 0:0:0;0:0:0;0:0:0;0:0:0
P11 1296 1/2 1/648 4194304 64 64,128,192,256 0:0:0;0:0:0;0:0:0;0:0:0
P12 324 1/2 1/162 4194304 64 64,128,192,256 0:0:0;0:0:0;0:0:0;0:0:0
P13 729 -1/4 -1/54 262144 64 64,128 0:0:0;0:0:0
P14 729 -1/4 1/108 1048576 0 64,128 0:0:0;0:0:0
```

Two fixes to the plan's `one()`:

- it passes `--side` at P08 and P13 for calls below 64;
- it records both exit codes in one trailer line, the engine's and the reader's.

The reader's stderr goes to `<call>.err`:

```
one() { id=$1 N=$2 d=$3 y=$4 i=$5 A=$6 S=$7 K=$8
  mask=VNC; [ "$i" -lt "$A" ] && mask=VNC,V1,V0,RN,FLIP,LOCK,MODE0,NL
  side=(); case $id in P08|P13) [ "$i" -lt 64 ] && side=(--side "agg/$id/$i.side");; esac
  "$T" dump N=$N delta=$d u=1 y=$y seed_string=stripes-ens-v1:N$N:d$d:y$y start=$((4096*i)) count=4096 dtden=64 threads=1 steps=$S "ctrl=$K" mask=$mask | "$RA" --point $id --call $i "${side[@]}" > agg/$id/$i.hbp 2> agg/$id/$i.err
  st=("${PIPESTATUS[@]}"); echo "rc=${st[0]} rc_reader=${st[1]}" >> agg/$id/$i.hbp; }
export -f one; export T RA
while read id N d y M A S K; do g $N $d $y || exit 1; mkdir -p agg/$id
  for i in $(seq 0 $((M/4096-1))); do echo "$id $N $d $y $i $A $S $K"; done
done < points.txt | xargs -P 4 -L 1 bash -c 'one "$@"' _
```

This wiring was tried with a stand-in for the engine that printed synthetic streams (no engine ran): P13 calls 0 and 5 gave blocks with side files and `rc=0 rc_reader=0`, and an empty stream with exit 4 gave stage A's `empty_stream` STOP and `rc=4 rc_reader=3`. Stage B accepts that STOP as an engine stop.

Rule STOP (run plan step 7):

- A call ending `rc=4 rc_reader=3` (the engine printed nothing) is renamed `<call>.attempt<k>.hbp` and rerun with the same keys, its last record and its ctrl entry dropped, until it completes. Stage B keeps the attempts in SHA256SUMS, keeps only the records every call reached, and marks the rest NOT_MEASURED.
- Any other trailer, or a reader STOP on a complete stream (`rc=0 rc_reader=3`), is a fault to report, not to rerun. Stage B refuses it.

Then file the sums and read:

```
for d in agg/P*/; do (cd "$d" && sha256sum [0-9]*.hbp > SHA256SUMS); done
$SB read --agg agg --runs run --qe QE.hbp --cost QE-COST.hbp --guard GUARD.hbp --out ../READ-STRIPE-PHASE.hbp
$SB audit --read ../READ-STRIPE-PHASE.hbp
$SB verify --read ../READ-STRIPE-PHASE.hbp --agg agg --runs run --qe QE.hbp --cost QE-COST.hbp --guard GUARD.hbp
```

Storage, an open decision:

- The aggregates are about 0.2 GB: about 120 KB for an all-variant call with 4 records, about 15 KB for a VNC-only call.
- The side files of P08 and P13 are 122 MB (950,336 bytes per call).
- No raw dump text is ever stored.
