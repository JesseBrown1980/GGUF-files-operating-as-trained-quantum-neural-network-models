# polariton-stripes/reader: the integer reader of the stripe-phase prediction

This folder reads the runs of `PREDICTION-STRIPE-PHASE.hbp` (frozen at 1977d45, sha256 `3398b073...`) and writes `READ-STRIPE-PHASE.hbp`. It uses integers and exact rationals only (rule DECIMAL). Nothing here runs an engine. The tests use synthetic streams, a fabricated campaign, and real dumps and QE rows at the excluded points only (N = 27, delta = 1/4, y = 1/40 and y = 0; QE at N = 9, delta = 1/3).

- `a/`: stage A, `stripes-read-a` 0.1.0, Rust 1.81, no dependencies, its own `[workspace]`. It reads one twens 0.4.0 dump stream and writes one aggregate block.
- `AGG-FORMAT.md`: the full grammar of the aggregate block, the side file and the STOP row. Stage B reads only what it defines.
- `b/`: stage B, `stripes-read-b` 0.1.0, Python 3 (int and `fractions.Fraction` only, run with `python3 -I`). It reads the aggregates, the run receipts and the QE receipts and applies every STRIPES_PREDICT row.
- `check/`: the independent check of stage A (`check_a.py`, `compare.py`) and `no_float.sh`.
- `sabotage/run.sh`: nine planted faults; the reader must catch each one.
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
  --qe-rc receipts/QE-RC.hbp --guard receipts/GUARD.hbp --out polariton-stripes/READ-STRIPE-PHASE.hbp
```

`read` does, in order:

1. Checks the frozen file's sha256, the point tables against the STRIPES_POINT rows, rule EXPOSED against X08 and the 15 QE commands against QR1-QR5.
2. Rule GUARD: a `TWB_GUARD ... verdict=allowed` line before each QE command and before each dump or run point, so at least as many lines at each (N, delta, y) as guarded commands there (33 in all), and no refusal at a plan triple.
3. Loads P01-P14 under rules SEED and STOP:
   - each point's SHA256SUMS against its receipts (every `.hbp`, `.err` and `.eng.err`);
   - every call file's trailer (`rc=E rc_reader=R`), AGG_END hash, `nl_sha256`, grammar and identities;
   - one block per call, and every side file's size and sha256;
   - the engine's stderr per call: empty beside a block, the TWB_FAULT row of an exit 4 beside an engine stop;
   - an engine stop (rc=4, stage A empty_stream, a TWB_FAULT row) loses that call's indices (NOT_MEASURED);
   - the earlier tries of a call, `<call>.attempt1..k`, each an engine stop of that point and call with its TWB_FAULT row, k = (records of the point) - (records of the block), or (records of the point) - 1 when no try completed; a complete block has none;
   - a point keeps only the records every call reached.
4. Loads R1-R4: 64 batches each, with their TWB_MEMO stderr and their exit code (`<id>.<j>.rc`). A batch that exited 4 has an empty stdout and a TWB_FAULT row on stderr, and its tries are kept as for the dump calls (`<id>.<j>.attempt<k>.hbp`, `.err`, `.rc`). Any other exit is a STOP.
5. Loads the QE rows. QE-RC.hbp holds the QE binary's sha256 and one row per command, in plan order, with its exit code. A command that exited nonzero has every read of its rows NOT_MEASURED, and its stderr is kept out of the COST match.
6. Applies Q01-Q07 (`rows_q.py`), E01-E08 (`rows_e_sym.py`) and E09-E19 (`rows_e_mom.py`) by rules READ3, H8, B16, SIGNFLIP, SE, STOP, SEED and EXPOSED.
7. Writes the file: a head, the inputs with their sha256, notes (calls read and lost and attempts per point, batches per run, missing QE rows, the QE exit codes and binary, and the readings below), one STRIPES_READ row per read, one STRIPES_VERDICT row per STRIPES_PREDICT row in frozen order, and an end row with the file's sha256.

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

Readings where the frozen text allows two, or says nothing (also written as STRIPES_READ_NOTE rows):

- E06, "0 mismatches ... with abs(B)>=2^-20": MET only if there is no mismatch where either B is big, MISS if there is one where both are, else NOT_RESOLVED.
- E16: D+ = t1 and D- = t3, the certified discordant cells on the common non-atom samples, and SE_pair = sqrt(D+ + D-)/(2M) as frozen. The ambiguous cells and the atoms enter the bracket of the difference only. The prediction names abs(Pi_V - Pi_VNC); the method's recipe (D+ - D-)/(2M) is half of it. MET if the prediction passes at every placement (then the recipe passes too), MISS if the recipe fails at every placement (then the prediction fails too), else NOT_RESOLVED.
- E15, "a scored cross-read other than predicted": a falsifier when certified (the read is MISS). A cross-read left NOT_RESOLVED leaves the row NOT_RESOLVED, since READ3 counts falsifiers on outcomes and NOT_RESOLVED is not certified.
- E02 atom counts: the integer intervals are keyed by sample count and variant class. [0,51] is also read on the first-2^18 control set of each point, and a count is read only on its full nominal set.
- E04 ratios: MET inside [1/4 - 1/100 - 4SE, 1/4 + 1/100 + 4SE], MISS outside (the frozen band and falsifier).
- Pi_hat counts every sample, the atoms by their own sign states; H8 and B16 leave the atoms out.
- E01: the Klein atom masses have no band, so they are read and reported.
- E12 and the E13 tolerance reads: n = 4..4096 is every power of 2 from 4 to 4096 with at least 1024 blocks. The E13 bands take the frozen n = 4^k.
- E18: E_VNC[abs(B_W)^2] = 0 is a ratio of 0, so MISS. E19: n* is not estimable when abs(Bbar)^2_u <= 0, so NOT_RESOLVED.
- Q03, Q04, Q05, Q07: a ratio whose denominator's interval reaches 0 is the half-line [lo, +inf), or both half-lines when the denominator crosses 0. It is MISS when every piece is disjoint from the band (rule READ3), else NOT_RESOLVED.
- Q06: c comes from the signed B interval (D2_q = 2B_e18/N), so it is bounded at every B. B_e18 <= 0 is MISS (the falsifier), else READ3 decides on c.
- Rule STOP for QE: a command filed with rc != 0 leaves every read of its rows NOT_MEASURED, rows it printed before the exit included. Its stderr is kept out of the COST match. Stderr text other than COST rows while every command exited 0 is a STOP.
- Rule STOP for the dumps and runs: a call or batch that exits 4 (nothing on stdout, a TWB_FAULT row on stderr) is kept as an attempt and rerun with its last record dropped. A block with r of R records needs attempts 1..R-r, and a lost call or batch needs 1..R-1. Any other exit is a STOP.
- Rule GUARD: the guard is a function of (N, delta, y) alone. One allowed line is filed before each QE command and before each dump or run point, whose calls and batches follow it. A refusal counts only at a plan triple.

Tests:

```
python3 -I polariton-stripes/reader/b/run_tests.py     # 260 unit tests, about 20 s
python3 -I polariton-stripes/reader/b/e2e.py           # the end-to-end test, about 3 min, about 0.3 GB of temporary files
```

`e2e.py` writes a synthetic campaign with `b/tests/campaign.py`:

- every point P01-P14 (8000 call files with their engine stderr, and the P08 and P13 side files);
- R1-R4 (64 batches each, with stderr and exit code);
- QR1-QR5 (the 15 QE commands) and QE-RC.hbp;
- one guard line per guarded command.

The values are small fabricated integers, not engine values. `read` must give one VERDICT row per STRIPES_PREDICT row, and `audit` and `verify` must pass. A second campaign then loses data in every way rule STOP allows, each loss with its evidence:

- P03 call 500 and P08 call 10 lost: every try, down to one record, exited 4 (three attempts each and the last try);
- P05 call 7 rerun without its last record (one attempt);
- R2 batch 5 lost the same way (two attempts and the last try);
- the QE command at (729, 1/108) killed after its t=1 row (rc=137), and the 6561 sector command panicked after its t=2 row (rc=101, the panic text on stderr).

It must give the same rows and the same SCORING table, with NOT_MEASURED reads where data was lost, the losses in its notes, and `verify` equal.

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

It builds stage A, emits the synthetic streams, writes (or reuses, `STRIPES_CAMPAIGN`) the campaign, and checks first that the clean inputs read. Then it plants nine faults (`sabotage/edit.py` edits copies; `sabotage/patch.py` plants a fault in stage B's code). Each case prints CAUGHT or MISSED:

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
8. Rule STOP without its evidence (the review's probes A, B and C, and the runs). Each is a STOP:
   - P05 call 7 cut to 3 records with no attempt (`stop_attempt_count`);
   - the complete block filed as `7.attempt1.hbp` beside a 3-record rerun (`stop_attempt_file`);
   - an attempt holding `anything`, beside the complete block (`stop_attempt_count`) and beside a rerun (`stop_attempt_file`);
   - a lost call whose last try has an empty engine stderr (`stop_engine_stderr`);
   - an R2 batch empty with rc=4, or cut to 2 records, with no attempts (`stop_attempt_count`);
   - an R2 batch with rc=137 (`run_rc`).
9. QE:
   - a panic after the t=2 row of the 6561 sector command, filed with rc=101: the read goes on, the command's 4 reads are NOT_MEASURED, and the READ file passes audit;
   - the same panic text filed with rc=0: a STOP `qe_stderr`;
   - B at (81, -1/54, t=2) moved by 1e-5: Q02 NOT_MET, with falsifier `par3`;
   - QE-RC.hbp short of a row: a STOP `qe_rc`.

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

Run `g` before every QE command and before every dump or run point (rule GUARD), and stop on any refusal. Never pass `lift_reserved_guard`.

Quantum (run plan step 4): 15 commands, stdout to QE.hbp, stderr (the COST rows, and any panic or usage text) to QE-COST.hbp. The wrapper files the QE binary's sha256 first, then one QE_RC row with each command's exit code after it ran. `q MODE N K delta y W times` guards (N, delta, y) first. It exits only on a guard refusal; a QE exit is filed and the next command runs:

```
echo "QE_BINARY|sha256=$(sha256sum "$QE" | cut -d' ' -f1)|json=0" > QE-RC.hbp
q() { local rc=0; g $2 $4 $5 || exit 1; "$QE" "$@" >> QE.hbp 2>> QE-COST.hbp || rc=$?
  echo "QE_RC|argv=$(IFS=_; echo "$*")|rc=$rc|json=0" >> QE-RC.hbp; }
for N in 81 729 6561; do q sector $N $N -1/4 0 6 1/2,1,2,4; done
for N in 81 729; do q point $N $N -1/4 0 6 1/2,1,2,4; done
for Y in 1/27 1/54 1/108 1/216; do q point 729 729 -1/4 $Y 6 1/8,1/4,1/2,1,2; done
q point 729 729 -1/4 -1/54 6 1/2,1,2
for Y in 1/27 1/108 1/216; do q point 81 81 -1/4 $Y 6 1/8,1/4,1/2,1; done
q point 81 81 -1/4 1/54 6 1/8,1/4,1/2,1,2,4
q point 81 81 -1/4 -1/54 6 1/2,1,2,4
```

Ensemble runs R1-R4 (run plan step 5), one at a time with threads=4. Each batch files its stdout, its stderr and its exit code. A batch that exits 4 is kept as an attempt and rerun with its last record and that record's ctrl entry dropped, until it completes or its one-record try exits 4 too (rule STOP):

```
run_pt() { local id=$1 N=$2 d=$3 y=$4 C=$5 S=$6 K=$7 j s k a x; g $N $d $y || return 1
  for j in $(seq 0 63); do s=$S k=$K a=0
    while :; do
      "$T" run N=$N delta=$d u=1 y=$y seed_string=stripes-ens-v1:N$N:d$d:y$y start=$((j*C/64)) count=$((C/64)) dtden=64 threads=4 steps=$s "ctrl=$k" mask=VNC memo=1 > run/$id.$j.hbp 2> run/$id.$j.err
      echo "rc=$?" > run/$id.$j.rc
      [ "$(cat run/$id.$j.rc)" = rc=4 ] && [ "${s#*,}" != "$s" ] || break
      a=$((a + 1)); for x in hbp err rc; do mv run/$id.$j.$x run/$id.$j.attempt$a.$x; done
      s=${s%,*} k=${k%;*}
    done
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

Three fixes to the plan's `one()`:

- it passes `--side` at P08 and P13 for calls below 64;
- it records both exit codes in one trailer line, the engine's and the reader's;
- it files the engine's stderr as `<call>.eng.err` (the TWB_FAULT row of an exit 4) and stage A's as `<call>.err`.

```
one() { local id=$1 N=$2 d=$3 y=$4 i=$5 A=$6 S=$7 K=$8 mask=VNC side=() st
  [ "$i" -lt "$A" ] && mask=VNC,V1,V0,RN,FLIP,LOCK,MODE0,NL
  case $id in P08|P13) [ "$i" -lt 64 ] && side=(--side "agg/$id/$i.side");; esac
  { "$T" dump N=$N delta=$d u=1 y=$y seed_string=stripes-ens-v1:N$N:d$d:y$y start=$((4096*i)) count=4096 dtden=64 threads=1 steps=$S "ctrl=$K" mask=$mask 2> agg/$id/$i.eng.err < /dev/null; } | "$RA" --point $id --call $i "${side[@]}" > agg/$id/$i.hbp 2> agg/$id/$i.err
  st=("${PIPESTATUS[@]}"); echo "rc=${st[0]} rc_reader=${st[1]}" >> agg/$id/$i.hbp; }
export -f one; export T RA
while read id N d y M A S K; do g $N $d $y || exit 1; mkdir -p agg/$id
  for i in $(seq 0 $((M/4096-1))); do echo "$id $N $d $y $i $A $S $K"; done
done < points.txt | xargs -P 4 -L 1 bash -c 'one "$@"' _
```

Rule STOP (run plan step 7). A call ending `rc=4 rc_reader=3` (the engine printed nothing and filed a TWB_FAULT row) keeps its three files as `<call>.attempt<k>.hbp`, `.err` and `.eng.err`, k = 1, 2, ..., and is rerun with the same keys, its last record and its ctrl entry dropped, until it completes or its one-record try exits 4 too:

```
redo() { local id=$1 N=$2 d=$3 y=$4 i=$5 A=$6 S=$7 K=$8 k=0 x
  while [ "$(tail -n 1 agg/$id/$i.hbp)" = "rc=4 rc_reader=3" ] && [ "${S#*,}" != "$S" ]; do
    k=$((k + 1)); for x in hbp err eng.err; do mv agg/$id/$i.$x agg/$id/$i.attempt$k.$x; done
    S=${S%,*} K=${K%;*}; one $id $N $d $y $i $A $S $K
  done; }
while read id N d y M A S K; do g $N $d $y || exit 1
  for i in $(seq 0 $((M/4096-1))); do
    [ "$(tail -n 1 agg/$id/$i.hbp)" = "rc=4 rc_reader=3" ] && redo $id $N $d $y $i $A $S $K
  done
done < points.txt
```

Stage B checks every attempt against this procedure, keeps only the records every call reached, and marks the rest NOT_MEASURED. Any other trailer, or a reader STOP on a complete stream (`rc=0 rc_reader=3`), is a fault to report, not to rerun, and stage B refuses it. So does an attempt that is not an engine stop of its call, a count of attempts the procedure does not give, or an exit 4 without its TWB_FAULT row.

The wiring of `one()`, `redo()`, `run_pt()` and `q()` was tried with stand-ins for the engines that print synthetic streams or exit 4 (no engine ran): see "The wiring, tried with stand-ins" below.

Then file the sums and read:

```
for d in agg/P*/; do (cd "$d" && sha256sum [0-9]*.hbp [0-9]*.err > SHA256SUMS); done
$SB read --agg agg --runs run --qe QE.hbp --cost QE-COST.hbp --qe-rc QE-RC.hbp --guard GUARD.hbp --out ../READ-STRIPE-PHASE.hbp
$SB audit --read ../READ-STRIPE-PHASE.hbp
$SB verify --read ../READ-STRIPE-PHASE.hbp --agg agg --runs run --qe QE.hbp --cost QE-COST.hbp --qe-rc QE-RC.hbp --guard GUARD.hbp
```

The wiring, tried with stand-ins. The blocks above that define `g`, `q`, `run_pt`, `one` and `redo` were run verbatim, with a stand-in for twens and one for QE that print synthetic streams and fabricated campaign rows or exit as the engines do (no engine ran), and with this seat's stage A:

- QE: all 15 commands ran; the 6561 sector command printed 3 rows and exited 101 with a panic text. QE-RC.hbp filed 15 rows; stage B read 61 rows, left that command's 4 keys out and counted 2 stderr lines that are not COST rows.
- Runs: R2 batch 5 exited 4 with 3 records and completed with 2 (one attempt); batch 9 exited 4 at every try (two attempts and the last try). Stage B read R2 as 63 batches, records 32 and 64, three attempts.
- Dumps, P13 with 8 calls: call 0 completed with its side file; call 5 exited 4 with 2 records and completed with 1 (one attempt); the other six exited 4 at both tries (one attempt each). Stage B's per-call STOP check passed every call, and the README's `sha256sum` line gave a SHA256SUMS stage B accepts.
- The guard file held 21 lines: 15 QE commands, 4 run points, and the dump point twice (before its calls and before its reruns).

Storage, an open decision:

- The aggregates are about 0.2 GB: about 120 KB for an all-variant call with 4 records, about 15 KB for a VNC-only call.
- The side files of P08 and P13 are 122 MB (950,336 bytes per call).
- No raw dump text is ever stored.
