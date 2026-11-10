# polariton-stripes/reader: the integer reader of the stripe-phase prediction

This folder reads the runs of `PREDICTION-STRIPE-PHASE.hbp` (frozen at 1977d45, sha256 `3398b073...`) and writes `READ-STRIPE-PHASE.hbp`. It uses integers and exact rationals only (rule DECIMAL). Stage B computes on ints and checked integer pairs only (the owner's ruling of 2026-11-09). Nothing here runs an engine. The tests use synthetic streams, a fabricated campaign, and real dumps and QE rows at the excluded points only (N = 27, delta = 1/4, y = 1/40 and y = 0; QE at N = 9, delta = 1/3).

- `a/`: stage A, `stripes-read-a` 0.1.0, Rust 1.81, no dependencies, its own `[workspace]`. It reads one twens 0.4.0 dump stream and writes one aggregate block.
- `AGG-FORMAT.md`: the full grammar of the aggregate block, the side file and the STOP row. Stage B reads only what it defines.
- `b/`: stage B, `stripes-read-b` 0.2.0, Python 3, ints and checked integer pairs (`stripes_read_b/qint.py`) only, run with `python3 -I`. It reads the aggregates, the run receipts and the QE receipts and applies every STRIPES_PREDICT row.
- `evidence/stage-b-fraction/`: stage B as reviewed at 5aad307 (`stripes-read-b` 0.1.0), on `fractions.Fraction`, kept verbatim as evidence: all 96 files of `b/` at 5aad307, byte for byte, and its README. It is listed with its tree pin in `polariton-stripes/FLOAT-EVIDENCE.txt` and is never run at a row point.
- `check/`: the independent check of stage A (`check_a.py`, `compare.py`), `no_float.sh` with `float_evidence.py`, and the comparison of the two stage B versions (`compare_b.py`, `probe_b.py`, `compare_read_b.py`).
- `sabotage/run.sh`: twelve planted faults, which the reader must catch each one of, and one documented fault it cannot see (case 13).
- `.github/workflows/polariton-stripes.yml` (at the repo root): runs all of it on every push and pull request that touches `polariton-stripes/`.

## Stage A: one dump stream in, one aggregate block out

```
stripes-read-a --point ID --call I [--side PATH] < dump
```

`ID` is P01-P14, or the excluded test points X1 and X0. Stage A:

- checks the head: version 0.4.0, the source and binary sha256, reserved=0, guard=active, float_used=0 on every row that prints it, the seed against the seed string (a `seed_string=none` is refused), and N, dtden and the canonical text of delta, u and y;
- checks the exact row sequence, key order and canonical integers, and, at a table point, the frozen command of that call (N, delta, y, seed string, start = 4096 I, count = 4096, mask, steps a prefix of the point's, ctrl 0:0:0);
- at a table point (P01-P14, X1, X0), rebuilds each sample's draws g, rot and eta from (seed, idx) with a port of the engine's generator (`src/rng.rs`, review N8; STOP `draw_mismatch`); refuses a rot component above 2^41 before any product takes it (`rot_out_of_range`, review N9);
- rebuilds every start, control seed and start bound from the draws, and recomputes every field of TWB, TWB_ROUND, TWENS, TWPAIR, TWB_PAIR and TWB_PAIR_ROUND from the per-sample rows;
- applies rules SECTOR and ATOMS, and prints per record and variant the 16 certified sector counts with A, the sign counts (atoms apart), the moment sums, the block sums for n = 4..4096, the comparison tables against VNC, the LOCK lattice test, the verbatim TWB_NL rows, sha256 of stdin, the TWB_HEAD line and the block's own sha256 (AGG_END);
- with `--side`, writes the per-index side file that row E04 pairs across P08 and P13. It is required at P08 and P13 for calls below 64.

Any difference is one STOP row (stdout and stderr) and exit 3; the reader still reads the rest of stdin. Exit 0 is a block. Exit 101 is a panic (overflow checks are on in release).

Build and test, always with the target folder outside the repo, and with the checkout path remapped to `stage-a` for every cargo call that shares the target folder:

```
cd polariton-stripes/reader/a
export CARGO_TARGET_DIR=/abs/path/outside/the/repo/ra
export RUSTFLAGS="--remap-path-prefix=$PWD=stage-a"
cargo +1.81.0 fmt -- --check
cargo +1.81.0 clippy --locked --offline --release --all-targets -- -D warnings
cargo +1.81.0 test --locked --offline --release
cargo +1.81.0 build --locked --offline --release
sha256sum "$CARGO_TARGET_DIR/release/stripes-read-a"   # af85e03d44bc056c9f7cb729a8c6c2a3f0263d5b7ac1eb96e8a748f0736b34ef
python3 -I ../check/excl_unpack.py --out /abs/excl   # the real excluded dumps of b/tests/data/excl, unpacked and checked
STRIPES_EXCL_DIR=/abs/excl cargo +1.81.0 test --locked --offline --release --test excluded_dumps -- --ignored
```

The 34 default tests (22 unit, 12 synthetic) need no engine. Three of the unit tests check the generator port: splitmix64 and xoshiro256** against their published reference vectors, and the form of the draws. The three ignored tests read real dumps at the excluded points (see "The real excluded-point data" below). The test emulator reproduces those dumps byte for byte, and the aggregates equal oracles written apart from the crate.

The stage A pin is the build of git tree `dcab5aeff0c87a52669b099a8f1f2ab605b00183` of `reader/a` (`git rev-parse <commit>:polariton-stripes/reader/a`) with rustc 1.81.0 (`eeb90cda1`) and the remap above: sha256 `af85e03d44bc056c9f7cb729a8c6c2a3f0263d5b7ac1eb96e8a748f0736b34ef`. Without the remap the binary holds the absolute source paths of its panic locations, so its sha256 moves with the checkout path (review M4). This seat built that tree with the remap at two source paths (the checkout `/home/user/qnn/polariton-stripes/reader/a` and a copy under its scratch folder, `.../qnn18fix2/q1/x/a`), each into its own target folder, and got the same sha256 twice. CI asserts the pin and the tree (`STAGE_A_SHA256`, `STAGE_A_TREE`), and stage B names the tree in the `reader_a` note of every READ file (see "The run, with this seat's binaries").

The second fix pass moved the pin: the draw rebuild at table points (review N8: `src/rng.rs`, `check.rs`, `lib.rs`) and the rot bound (review N9: `check.rs`, `eng.rs`) changed the source, so tree `590b2528bee1ee52e0e0b47d23540f0ac44dd998` and its sha256 `7fe3c18f59a75bd4b06ba080027045a4d066ca1677c173ec1139c2f2dcd80ed3` (the first fix pass, built with the remap at three paths) are replaced. The aggregate rows did not change: on the four real dumps at X1 and X0 `af85e03d` writes the four side files byte for byte and each block byte for byte apart from `AGG_SIDE path=` and the AGG_END hash over it (the same comparison as for `7fe3c18f`, see "The real excluded-point data").

Earlier stage A hashes, both builds without the remap at this seat's checkout path `/home/user/qnn/polariton-stripes/reader/a`: `c8c3f0d12bcc5a21c703d0170b30637e8138b89004219b8d6562c43c36db7cf2` is git tree `a64e2af9` (commits b810786 to 73fb7ee), built into target folders under this seat's scratch folder (`.../scratchpad/stripes-build/ra` and others) and rebuilt the same here; `742eea62f2107cbf5c9d888da78a88c28d155daf6c4e4d354e874bd2a25b8400` (`b/tests/data/agg/COMMANDS.txt`) was the binary at `.../scratchpad/stripes-build/ra/release/stripes-read-a` at 10:22 on 2026-11-09, recorded in `.../stripes-build/excl/READER.txt`, from a `reader/a` that no commit holds (`lib.rs` and `stream.rs` were edited at 11:48, before b810786, and a rebuild of `a64e2af9` at that path gives `c8c3f0d1`, not `742eea62`). Neither can be rebuilt at another path (tree `a64e2af9` with the remap gives `ce98e0c8b1a44f30d4ecb7f4ea9db67686fde1f738af91b81129fa90dbcf11ec` at any path; this fix pass changed `row.rs` and `stream.rs`, so the pin moved to `7fe3c18f`). `7fe3c18f`, and now `af85e03d`, replace both: on the four real dumps at X1 and X0 each writes the four `X*.agg` fixtures and their side files byte for byte (the `--side` path aside), and `compare.py --excl` gives 4 of 4 equal.

## Stage B: the aggregates, the runs and the QE rows in, READ-STRIPE-PHASE.hbp out

```
python3 -I polariton-stripes/reader/b/stripes_read_b/__main__.py read \
  --agg receipts/agg --runs receipts/run --qe receipts/QE.hbp --cost receipts/QE-COST.hbp \
  --qe-rc receipts/QE-RC.hbp --guard receipts/GUARD.hbp --out polariton-stripes/READ-STRIPE-PHASE.hbp
```

`read` does, in order:

1. Takes stage B's own tree pin, the `reader_b` note: each file's mode from git's index (`git ls-files -s`), its bytes from the working tree. It writes nothing (a STOP row) when a file under `b/` is not in the index (`stage_b_tree`) or a working-tree mode differs from the index's (`stage_b_modes`). So stage B and the gates run from a POSIX checkout (Linux, or WSL on ext4), not from `/mnt/c` or another checkout with `core.filemode=false`, and a new file is staged with `git add` before a read. Then checks the frozen file's sha256 and the frozen README's (STOP `frozen_sha256`; the rows are parsed from the bytes that were hashed), the point tables against the STRIPES_POINT rows, rule EXPOSED against X08 and the 15 QE commands against QR1-QR5.
2. Rule GUARD: a `TWB_GUARD ... verdict=allowed` line before each QE command and before each dump or run point, so at least as many lines at each (N, delta, y) as guarded commands there (33 in all), and no refusal at a plan triple.
3. Loads P01-P14 under rules SEED and STOP:
   - each point's SHA256SUMS against its receipts (every `.hbp`, `.err` and `.eng.err`); `read` and `verify` take no flag, and nothing skips this check;
   - every call file's trailer (`rc=E rc_reader=R steps=S`, S the steps that try ran with), AGG_END hash, `nl_sha256`, grammar and identities;
   - one block per call, and every side file's size and sha256;
   - every side file against its own block (ensemble review M4): start and count, variants and records, the four atom-flag counts against AGG_ATOMS, and per record and variant m, Sum br, Sum br^2, Sum b_br and Sum b_br^2 over all samples and over the variant's atom set against AGG_SUM;
   - the engine's stderr per call: empty beside a block, the TWB_FAULT row of an exit 4 beside an engine stop;
   - an engine stop (rc=4, stage A empty_stream, a TWB_FAULT row) loses that call's indices (NOT_MEASURED);
   - the earlier tries of a call, `<call>.attempt1..k`, each an engine stop of that point and call with its TWB_FAULT row, k = (records of the point) - (records of the block), or (records of the point) - 1 when no try completed; a complete block has none;
   - the steps of every try: attempt j ran the first R - j + 1 records of the point's R; the last try of a lost call ran one; a block's trailer names the block's own steps;
   - a point keeps only the records every call reached.
4. Loads R1-R4: 64 batches each, with their TWB_MEMO stderr and their exit code and steps (`<id>.<j>.rc`, one line `rc=E steps=S`). A batch that exited 4 has an empty stdout and a TWB_FAULT row on stderr, and its tries are kept as for the dump calls (`<id>.<j>.attempt<k>.hbp`, `.err`, `.rc`), with their steps checked the same way. Any other exit is a STOP. A run point keeps only the records all 64 batches reached (rule STOP). A batch whose one-record try exits 4 too reached no record, so its point keeps none: every read of that point is NOT_MEASURED and states the loss. Its other batches and every try are still checked.
5. Loads the QE rows. QE-RC.hbp holds the QE binary's sha256 and one row per command, in plan order, with its exit code. A command that exited nonzero has every read of its rows NOT_MEASURED, and its stderr is kept out of the COST match.
6. Applies Q01-Q07 (`rows_q.py`), E01-E08 (`rows_e_sym.py`) and E09-E19 (`rows_e_mom.py`) by rules READ3, H8, B16, SIGNFLIP, SE, STOP, SEED and EXPOSED.
7. Writes the file: a head, the inputs with their sha256, notes (stage B's version and tree pin, calls read and lost and attempts per point, batches checked and read per run, missing QE rows, the QE exit codes and binary, and the readings below), one STRIPES_READ row per read, one STRIPES_VERDICT row per STRIPES_PREDICT row in frozen order, and an end row with the file's sha256.

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
- E16, the conservative reading: D+ = t1 and D- = t3 are the certified discordant cells on the common non-atom samples. Every ambiguous cell (t2, t5, t6, t7, t8) and every sample outside the common non-atom set (the atoms) counts as possibly discordant. So D+ + D- <= D_max, and SE_pair = sqrt(D_max)/(2M) is an upper bound of the frozen sqrt(D+ + D-)/(2M) at every placement. The ambiguous samples also widen the bracket of the difference. The prediction names abs(Pi_V - Pi_VNC); the method's recipe (D+ - D-)/(2M) is half of it. MET if the prediction passes at every placement (then the recipe passes too), MISS if the recipe fails at every placement (then the prediction fails too), else NOT_RESOLVED. Each read files D_max beside D+ and D-.
- E15, "a scored cross-read other than predicted": a falsifier when certified (the read is MISS). A cross-read left NOT_RESOLVED leaves the row NOT_RESOLVED, since READ3 counts falsifiers on outcomes and NOT_RESOLVED is not certified.
- E02 atom counts: the integer intervals are keyed by sample count and variant class. [0,51] is also read on the first-2^18 control set of each point, and a count is read only on its full nominal set.
- E04 ratios: MET inside [1/4 - 1/100 - 4SE, 1/4 + 1/100 + 4SE], MISS outside (the frozen band and falsifier).
- Pi_hat counts every sample, the atoms by their own sign states; H8 and B16 leave the atoms out.
- E01: the Klein atom masses have no band, so they are read and reported.
- E12 and the E13 tolerance reads: n = 4..4096 is every power of 2 from 4 to 4096 with at least 1024 blocks in the nominal sample count. After a lost call, a size left with fewer than 1024 measured blocks is NOT_MEASURED, so that read is NOT_RESOLVED at best (one lost call is enough: K = 1023 at n = 4096 on 2^22). The frozen text also allows limiting n to the sizes the measured data have; the owner picks. The E13 bands take the frozen n = 4^k.
- E10, the falsifier "P02 not resolved above 0 at 3 SE": the low end of the ambiguity bracket, (O+ - O- - A)/(2M), minus 3 SE, is at or below 0. The band read keeps the frozen e = 3SE + A/M.
- E18: E_VNC[abs(B_W)^2] = 0 is a ratio of 0, so MISS. E19: n* is not estimable when abs(Bbar)^2_u <= 0, so NOT_RESOLVED.
- Q03, Q04, Q05, Q07: a ratio whose denominator's interval reaches 0 is the half-line [lo, +inf), or both half-lines when the denominator crosses 0. It is MISS when every piece is disjoint from the band (rule READ3), else NOT_RESOLVED.
- Q06: c comes from the signed B interval (D2_q = 2B_e18/N), so it is bounded at every B. B_e18 <= 0 is MISS (the falsifier), else READ3 decides on c.
- Rule STOP for QE: a command filed with rc != 0 leaves every read of its rows NOT_MEASURED, rows it printed before the exit included. Its stderr is kept out of the COST match. Stderr text other than COST rows while every command exited 0 is a STOP.
- Rule STOP for the dumps and runs: a call or batch that exits 4 (nothing on stdout, a TWB_FAULT row on stderr) is kept as an attempt and rerun with its last record dropped. A block with r of R records needs attempts 1..R-r, and a lost call or batch needs 1..R-1. Attempt j filed the first R - j + 1 records as its steps, and the last try of a lost call or batch filed one. Any other exit is a STOP.
- Rule STOP, a lost call and a lost batch: the dump clause says a call that never completes has its 4096 indices NOT_MEASURED, and the other calls are read. The run clause has no such sentence: a point keeps only the records all 64 batches reached. A lost batch reached none, so every read of its run point is NOT_MEASURED (E04, E18, E19), each stating the loss. This is the literal reading; no ruling for the dump analogy is filed.
- Rule GUARD: the guard is a function of (N, delta, y) alone. One allowed line is filed before each QE command and before each dump or run point, whose calls and batches follow it. A refusal counts only at a plan triple.

Three of the owner rulings that the receipt's GATE row listed as open are closed by the frozen text (the local seat's PR #18 comment 6749660971; line numbers of `PREDICTION-STRIPE-PHASE.hbp` at 1977d45, checked by this seat and by the unit test `FrozenCitations`). Each has its own STRIPES_READ_NOTE that cites its frozen lines:

- `closed_STOP_runs`, STOP for runs, the literal reading: frozen line 37 (rule STOP) gives a dump call that never completes its own sentence ("if none completes, its 4096 indices are NOT_MEASURED") and the run clause none ("the point keeps only the records all 64 batches reached"). A lost batch reached none, so every read of its run point is NOT_MEASURED and states the loss.
- `closed_E16_bracket`, E16, the bracket reading above: frozen line 30 (rule SECTOR) brackets an ambiguous cell "in every test"; frozen line 114 (E16) holds the statement abs(Pi_V - Pi_VNC) and the recipe (D+ - D-)/(2M).
- `closed_E02_counts`, E02, counts keyed by sample count and variant class: frozen line 4 (STRIPES_POINTS_COMMON: calls i < 64 carry every variant and NL, "so the controls and NL cover the first 2^18 indices") and frozen line 100 (E02). The comment cited line 5 for STRIPES_POINTS_COMMON; it is line 4 (line 5 is STRIPES_POINT P01).

E12 and E13, the set of block sizes n (the step, and the range after a lost call; the reading `reading_E12_E13_n` above): ruled by the owner (PR #18 comment 6753596286, 2026-11-09T22:50Z), applied in the next pass; this pass leaves the reader as it is (receipt, rows 12 and 13). Every other reading of this list is a seat choice made before any data; the owner confirms each before the run (receipt, row 13).

And one note on a frozen value the reader does not use: `frozen_R1_s`. STRIPES_POINT R1 (frozen line 19) files s = 1/2, while y sqrt(N) = (1/27) sqrt(729) = 1. Stage B computes s = y sqrt(N) itself from N and y (`rows_e_mom.triple`, `DumpPoint.s`), so rule EXPOSED reads abs(s) = 1 at R1 and no read takes the filed value (review N6; the unit test `test_r1_s_is_computed`). The frozen bytes stay as they are.

Tests:

```
python3 -I polariton-stripes/reader/b/run_tests.py     # 304 unit tests, none skipped, about 40 s
python3 -I polariton-stripes/reader/b/e2e.py           # the end-to-end test, about 3.5 min, about 0.3 GB of temporary files
```

`e2e.py` writes a synthetic campaign with `b/tests/campaign.py`:

- every point P01-P14 (8000 call files with their engine stderr, and the P08 and P13 side files, each built so its sums equal its block's AGG_SUM and AGG_ATOMS; P13 takes P08's sums, so the paired E04 differences are 0);
- R1-R4 (64 batches each, with stderr and exit code);
- QR1-QR5 (the 15 QE commands) and QE-RC.hbp;
- one guard line per guarded command.

The values are small fabricated integers, not engine values. `read` must give one VERDICT row per STRIPES_PREDICT row, and `audit` and `verify` must pass. A second campaign then loses data in every way rule STOP allows, each loss with its evidence:

- P03 call 500 and P08 call 10 lost: every try, down to one record, exited 4 (three attempts each and the last try, each trailer with its steps);
- P05 call 7 rerun without its last record (one attempt);
- R2 batch 5 lost the same way (two attempts and the last try), so every R2 read is NOT_MEASURED (11 reads of E04, E18 and E19, each stating the loss);
- the QE command at (729, 1/108) killed after its t=1 row (rc=137), and the 6561 sector command panicked after its t=2 row (rc=101, the panic text on stderr).

It must give the same rows and the same SCORING table, with NOT_MEASURED reads where data was lost, the losses in its notes, and `verify` equal.

The part-1 commands of `b/run_b.py` (`tables`, `series`, `q`, `point`, `sides`, `run`) check the tables, the frozen decimals and single inputs. `sides` checks every side file of a point against its block (M4).

## Integer pairs

The owner ruled on 2026-11-09 that stage B moves from `fractions.Fraction` to integer pairs before any run at a row point. One stray float slips through Fraction without an error: `Fraction(1, 3) * 0.5` returns a float, and `Fraction(0.1)` turns a float into a ratio.

`b/stripes_read_b/qint.py`:

- A value is a `Q`, the reduced pair (n, d): d > 0, gcd(n, d) = 1.
- `make(n, d)`, `add`, `sub`, `mul`, `div`, `neg`, `absq`, `cmp`, `sign`, `floor`, `ceil`, `ipow`, and `gcd` and `isqrt` in integers (no `math`).
- Every result passes `_pair`, which checks `type(x) is int` for both parts (a bool is refused) and d > 0. `_pair` does not reduce: its docstring gives the argument that every caller passes a pair reduced by construction (review N13).
- An operand must be a `Q` or an int. A float, complex, bool, Fraction, Decimal or str raises `TypeError`. Comparison is by cross-multiplication.
- `Q`'s operators are these same functions. `/`, `//`, `%`, `divmod`, `float()` and `int()` on a `Q`, from either side, raise `QintError`; `Q` has no power or `round` (`TypeError`).
- `exact.py` keeps its API (`fr`, `div`, `Iv`, `Ext`, `Rad`, `fmt`, ...) and the same algorithms, now on `Q`.
- A `QintError` (a stray float, bool or other type), an exact division by zero, or any other `ValueError` or `ArithmeticError` ends `read`, `audit` and `verify` with one STOP row, reason `qint`, and exit 3, and no READ file is written.

The source scan `b/tests/test_nofloat.py` refuses, in every .py of `b/`:

- the imports fractions, decimal, math, numpy, statistics, cmath, random, json, pickle, marshal, importlib, ctypes, scipy, mpmath, sympy, operator, array, time, datetime, tomllib and builtins;
- the names float, round, complex, pow, eval, exec, compile, `__import__`, format and `__builtins__`;
- float and complex literals, true division anywhere, and `**`;
- the attributes `__truediv__`, `__rtruediv__`, `__itruediv__`, `truediv`, `itruediv`, `__float__`, `__complex__`, `__round__`, `fromhex`, `as_integer_ratio`, `pow`, `__pow__`, `__rpow__`, `__ipow__`, `float`, `cast`, `literal_eval`, `float_info`, `timestamp`, `st_mtime`, `st_atime`, `st_ctime`, `getmtime` and `modules`;
- `getattr`, unless it is called with a str constant as the name and that name is none of the attributes or names above;
- a format spec in an f-string; in any string, a percent format of type e, f, g or % (with a mapping key, a `*` width or a `*` precision too) and a brace format spec of type e, f, g or % (as `str.format` and `format()` read it);
- a struct call whose format is not a literal or holds a float code (e, f, d), called through `struct`, an alias of it, or a name imported from it; and `from struct import *`.

It plants one fault of each kind first: 83 plants, one for every listed module, name and attribute (a test checks that none is left without one), and a clean control with integer struct codes, a constant `getattr`, `%s`, `%d` and braces that are not a float spec. The checker and the sabotage suite get the loose form of the same scan (`no_float.sh`). The scan reads the source; it is not a proof that no float can arise. The other half is at run time: `qint` refuses every operand that is not an int or a `Q`.

CRT and rational reconstruction are not used. The largest pair measured: 1,389 bits in a whole read of the synthetic campaign, 1,753 bits in the frozen-decimal checks, 16,387 bits in the unit tests of the first fix pass (the 16,384-bit refinement of `Rad.sign` on sqrt 2 + sqrt 8 - sqrt 18). Since the second pass `Rad` merges terms whose radicands differ by a rational square factor (review N14: the isqrt test on n_i d_j n_j d_i, one term on the least radicand), so that tie is exactly 0 with no refinement; the 16,384-bit bound stays for sums of three or more independent roots, and a unit test still reaches it. Not re-measured in this pass. Python ints carry these directly. A read takes about 40 s.

The two versions against each other, on control data only (no row point, no engine):

```
python3 -I polariton-stripes/reader/check/compare_b.py [--excl <dir of X1.i.side, X0.i.side>, such as polariton-stripes/reader/b/tests/data/excl>]
```

It checks the evidence pin, lays the evidence out at its old depth beside a copy of the frozen file, and runs `run_b.py tables`, `run_b.py series`, `probe_b.py` and `probe_b.py --lens` with each version. The probe prints, at 30 significant digits, the closed forms at the excluded (delta, y, t), the QE rows at N = 9, delta = 1/3 and the Q helpers on them, the pooled blocks at N = 27, delta = 1/4 with every estimator and 412 READ rows built on them, the run sums of XR0 and XR1, and with `--excl` the paired sums of the real side files. The lens runs the row builders of Q01-Q07, E09-E15 and E17-E19: on fabricated QE receipts and runs R1-R4 that the live `tests/campaign.py --only qe,runs` writes once (small integers, no engine value), and on the X1 and X0 blocks. It prints each read by its fields, so text-only changes do not reach it. E16 is left out, since its conservative SE_pair changed its output on purpose; E01-E08 need the table's own points. On this seat all four outputs were byte-identical (probe 1,122 lines with `--excl`, lens 784 lines).

At the conversion step alone, before the open items below changed any output, both versions also wrote byte-identical files on the e2e campaigns: the 16,914 campaign files, the READ file (sha256 `c625ee46...`) and the STOP campaign's READ file (`9e7be937...`). Those two hashes came from an uncommitted working tree: no commit holds the conversion without the later fixes (5aad307 is the Fraction version, c036d7a has both), so git history cannot reproduce them. The open items then changed the trailer grammar, the side files and E16. What is repeatable on the current tree is the probe, the lens and `check/compare_read_b.py` below.

The later fixes change the live output on purpose, and the evidence keeps the old one. `check/compare_read_b.py` (review M5, run in CI after `e2e.py`) has each version `read` the clean campaign and the STOP campaign. The evidence reads a copy in its own receipt grammar: ` steps=` dropped from every call-file trailer and run `.rc` file, and the point's SHA256SUMS given the new sha256 of each rewritten call file. It requires every STRIPES_READ and STRIPES_VERDICT row that differs to fall in one of the declared cases below, compares the head, the inputs and the notes against their own declared lists, and then checks itself on ten planted undeclared differences, each of which it must find:

```
python3 -I polariton-stripes/reader/check/compare_read_b.py [--campaigns <the --work folder of e2e.py --keep>]
```

Each difference is one of these:

- E16, 24 reads: the bounds and the detail of the conservative SE_pair (no verdict changed on the campaign).
- The band of an infinite end prints open, `(0,inf)` and `(-inf,inf)`: 20 reads of E15, E19 and Q07 (text only).
- A read lost to a QE exit names it, `lost:qe_rc_101` or `lost:qe_rc_137` (STOP campaign, 27 reads; text only).
- Rule STOP for runs: R2's lost batch leaves every R2 read NOT_MEASURED (STOP campaign, 11 reads). E04 turns from NOT_MET to NOT_RESOLVED and E19 from MET to NOT_RESOLVED; E18 stays NOT_MET on its R1 read.
- The head and notes: version 0.2.0, the `reader_b` tree pin, the run notes (`checked=`), the reading notes, the four notes of the second fix pass (`frozen_R1_s`, `closed_STOP_runs`, `closed_E16_bracket`, `closed_E02_counts`, live only), and the receipts' new trailer grammar (the AGG input hashes and the run listing).

Every other row was byte-identical: 2,634 of 2,678 READ rows and all 26 VERDICT rows on the clean campaign, 2,600 READ rows and 23 VERDICT rows on the STOP campaign (`compare_read_b.py` on this seat; the evidence's READ files `96507472...` and `164f3bbd...`). The E10 falsifier and the E19 bounds changed nothing there: the campaign has A = 0 at P02, where both forms of the falsifier agree, and n* - 4SE stays above 0 at every E19 read.

## The independent check of stage A

`check/check_a.py` is a second stage A written from the frozen rules and AGG-FORMAT.md in Python (int only). `check/compare.py` reads each stream with both readers. A block must be equal byte for byte, and its side file too. A STOP must agree in every field but `detail`, with the reason the case expects. Before any case, `compare.py` checks `check_a.py`'s own port of the engine generator on the published splitmix64 and xoshiro256** reference vectors, the ones stage A's `rng.rs` unit tests use (`COMPARE_PREFLIGHT`, review 5831368495 note N8; CI requires `result=equal`); the rest of that port is pinned by the cross-check.

```
cd polariton-stripes/reader/a
STRIPES_EMIT_DIR=/abs/streams cargo +1.81.0 test --locked --offline --release --test synthetic emit_streams_for_the_independent_check -- --ignored
python3 -I ../check/compare.py --ra $CARGO_TARGET_DIR/release/stripes-read-a --streams /abs/streams [--excl <dir of X1.i.txt, X0.i.txt>]
```

The emitter writes 99 synthetic cases:

- 14 blocks: designed streams at y = 1/40 and y = 0, the LOCK lattice, a VNC-only stream, a planted consistent exchange atom, table-point streams at the excluded points X1 and X0 only (`table_X1_2_r2`, `table_X0_5_r2` with its side file, `table_X1_0_r1` and `table_X0_7_r1` with one record, `table_X1_6_r2` with a side file), and three of the probes below (`probe15_block`, `probe17_block`, `probe18_block`);
- 85 STOPs: 51 faulty streams (`stopNN_REASON`) and 10 faulty argument lists (`argsNN_REASON`), the planted exchange-atom faults, 16 of the probes (`probeNN_REASON`) and 6 draw cases (`drawNN_REASON`, reviews N8 and N9): g0 of one sample moved by 2^35 at X1, rot moved by 1 and eta moved by 1 at X0 (each stream rendered from the moved draw, so its starts and sums agree with it and only the rebuild from (seed, idx) sees it: `draw_mismatch`), a rot component of 2^41 + 1 and of -(2^41 + 1) at Tsyn (`rot_out_of_range`), and one of exactly 2^41, which passes the bound and fails the start rebuild (`start_mismatch`). `compare.py` requires the reason a case is named for, and a block for `probeNN_block`.

Since stage A rebuilds a table point's draws from its seed (review N8), the table-point streams carry the engine's draws from (seed, idx): those of X1's and X0's seeds, computed by the port in the test emulator. No test computes the draws of a row point's seed, so the table-point streams at P13, P14, P01, P07 and P08 of the first fix pass (LCG draws, which stage A would now refuse) were replaced by the X1 and X0 streams above; no emitted stream carries a row-point id or seed. Two argument cases (`args05`, `args06`) name P08 and P13 and stop `side_file_required` at the argument check, before any row is read. The head checks of every point of the table stay in `table_checks_at_every_point`.

Between them they give 50 of the 59 reasons of the AGG-FORMAT STOP table. The 9 that no case gives: `read_error` (stdin from a file does not fail); `record_without_ctrl` and the four `missing_TWB*` (no stream that passes the row sequence check lacks those rows); `aggregate_identity` (a reader fault); `block_sum_overflow` and `side_bound_above_u64` (values the engine cannot reach; a stream that reaches them first overflows a 128-bit sum, a panic in stage A, while `check_a.py` has unbounded ints, so the two readers would differ there). The agreement claim is for the emitted cases and the real excluded dumps only.

The probes (review M7, at Tsyn and X1 only): 16 gave a different outcome, reason or line in the two readers of 73fb7ee (stage A `c8c3f0d1` and that `check_a.py`: 80 of these 96 cases equal, the 16 differ), and 3 are controls on which they already agreed. Non-canonical rationals on every row, `y = -0`, `+1/40`, `01/40`, `1/040`, `delta = +1/4` and `u = +1`, were a block in stage A (an i128 parse) and `bad_rational` in `check_a.py`; `y = -0` at X1 was `table_mismatch` against `bad_rational`; a `y` with a 43-digit denominator was `bad_rational` in stage A (i128) and a block in `check_a.py`. `seed_string=none` with seed = sha256("none") on every row was `head_seed` in stage A and a block in `check_a.py`. `dtden = 0` and `N = 1` were `head_dtden` and `head_N` against `bad_integer`; `dtden = 32` at X1 was `table_mismatch` against `head_dtden`; a token without `=` other than the key was `row_field_without_value` against `row_key`; a first row `TWB_HEAD` alone was `row_short` against `first_row_not_TWB_HEAD`; a start fault followed by a TWB_DONE fault was `field_value` against `start_mismatch`; ctrl `1:0:0` at X1 was `table_mismatch` in both, at the record's last line against line 0. The controls: the token `xw` alone, `y = 0/7` and `y = -1/40`. Now stage A reads a rational as text by RAT_RE (no width limit), both refuse `seed_string=none`, `check_a.py` takes stage A's reasons for N, dtden and a token without `=`, and both follow the check order of AGG-FORMAT.md section 8, so all 96 were equal on the first fix pass.

On this seat, with stage A `af85e03d`, all 99 were equal, and so were the 4 real excluded dumps (103 of 103). CI runs the synthetic cases only and requires 99 of 99. On the 4 real dumps (16,384 samples, MODE0 on) the draws g, rot and eta of every sample rebuild from (seed, idx) in both readers; a real dump with one sample's eta moved by 1 on all its variants is a STOP `draw_mismatch` at X1 and a block at a test id, so the rebuild is what sees it. The real dumps also caught a slip in this pass: `check_a.py` first carried the multiplier 0x100000001B3 (the BRIDGE_SAMPLING text, hold H1) for the engine's 0x1000_0000_01B3 and stopped `draw_mismatch` at idx 1 of every real dump.

## The real excluded-point data

`b/tests/data/excl/` holds the real dumps that the cloud seat made at the excluded points before the freeze review, with its scratch build of twens 0.4.0 (sha256 `33e62fbe...`), each command after a `twens guard`: X1 (N = 27, delta = 1/4, u = 1, y = 1/40) and X0 (y = 0), calls 0 and 1. No row point is there. `PROVENANCE.txt` in the folder says where each file came from. The folder holds:

- `COMMANDS.txt`, `READER.txt` and `GUARD.hbp`, byte for byte as the cloud seat wrote them; the absolute scratch paths in them are the historical record;
- the four blocks `X*.agg` (byte-identical to `agg/X*.agg`) and their side files `X*.side`;
- the four dumps as xz -9 copies, `X*.txt.xz` (4.2 to 4.3 MB each, 26.7 to 26.8 MB unpacked);
- `SHA256SUMS`: the 13 lines of the source folder's own list unchanged, then every other file. `X1s4.0.txt` (call 0 of X1 with steps 64 to 256, 47 MB) is listed by its sha256 only: its xz copy is 8.5 MB, over this copy's 8 MB limit, and nothing reads it.

`run_tests.py` reads the blocks and side files there (`RealSideFiles`, no longer skipped, and a check of the folder against its `SHA256SUMS`). For the rest, `check/excl_unpack.py` unpacks the dumps into a folder outside the repo, after checking every file present and every unpacked dump against `SHA256SUMS`. Then, from `polariton-stripes/reader`:

```
python3 -I check/excl_unpack.py --out /abs/excl
(cd a && STRIPES_EXCL_DIR=/abs/excl cargo +1.81.0 test --locked --offline --release --test excluded_dumps -- --ignored)
python3 -I check/compare.py --ra $CARGO_TARGET_DIR/release/stripes-read-a --excl /abs/excl
python3 -I check/compare_b.py --excl b/tests/data/excl
STRIPES_EXCL_DIR=/abs/excl CARGO_TARGET_DIR=/abs/path/outside/the/repo/ra sabotage/run.sh
```

These are the items the review could not see. On this seat, with stage A `7fe3c18f` (first fix pass; the second, with `af85e03d`, is in the receipt, row 14), they gave:

- the three ignored stage A tests: 3 passed. The third writes `SABOTAGE.txt` into the folder, and it was byte-identical to the one in the cloud seat's dump folder;
- `compare.py --excl`: 4 of 4 blocks equal;
- `compare_b.py --excl`: 4 of 4 equal, the probe 1,122 lines;
- sabotage case 4c: CAUGHT, inside the full suite run. Run by hand, it is a STOP `summary_mismatch` at TWB step 64, VNC, br: stream -42498031717, reader -42498031718, the line S2 of the cloud seat's `SABOTAGE.txt`;
- the producer of the X1 and X0 blocks, `stripes-read-a --point X1 --call 0 --side PATH < X1.0.txt` and so on: it writes each side file byte for byte, and each block byte for byte apart from `AGG_SIDE path=`, which holds the `--side` argument as given, and the AGG_END hash over it. The fixtures were written with `--side /tmp/claude-0/-home-user/b2fb539a-cb4d-5f0b-a22f-ca1a7fcb500d/scratchpad/stripes-build/excl/X1.0.side` (and so on). On this seat, with `--side` in a scratch folder, the side files were byte-identical, and the blocks became byte-identical once that path was put in `path=` and AGG_END recomputed. To get them byte for byte directly, give `--side` that same path (create the folder first); this seat did not, since the folder holds the cloud seat's originals.

## The sabotage suite

```
CARGO_TARGET_DIR=/abs/path/outside/the/repo/ra polariton-stripes/reader/sabotage/run.sh
```

It builds stage A, emits the synthetic streams, writes (or reuses, `STRIPES_CAMPAIGN`) the campaign, and checks first that the clean inputs read. Then it plants twelve faults (`sabotage/edit.py` edits copies; `sabotage/patch.py` plants a fault in stage B's code) and one it cannot see (case 13). Cases 1 to 12 print CAUGHT or MISSED; case 13 prints NOT_VISIBLE or MISSED. CI requires 12 CAUGHT, one NOT_VISIBLE and no MISSED. The baseline and case 4 read the emitter's synthetic X0 table stream (call 5, with its side file); no stream with a row-point id is read (review N8, see "The independent check of stage A").

1. The sign of bi flipped on one exchange atom:
   - bi=-0 on a LOCK atom is a STOP `bad_integer`;
   - a flipped nonzero bi is a STOP `summary_mismatch`;
   - an edited block fails `agg_sha256`;
   - a forged, consistent block turns E02 NOT_MET, with its `xbi` read in the falsifier.
2. Two sector counts swapped: the block fails `agg_sha256` (with SHA256SUMS rewritten) or `sha256sums` (with AGG_END forged). With AGG_END forged, `verify` of the clean READ file stops at `sha256sums` too, and `--no-sums` (review M3, removed) is a STOP `usage` for `read` and `verify`; no READ file is written.
3. A dropped call: SHA256SUMS still lists it (`sha256sums`); with the list rewritten, rule SEED finds the call missing (`seed_dropped_call`).
4. An altered TWB or TWB_ROUND sum: a STOP `summary_mismatch`. With `STRIPES_EXCL_DIR` the suite also tries this on a real excluded dump (4c; a folder `check/excl_unpack.py --out` wrote serves).
5. A wrong TWB_HEAD version: a STOP `head_version` in stage A, and in stage B for a forged block.
6. A read-and-report read promoted to scored:
   - in a row module, stage B stops (`scoring_table`);
   - in a READ file, `audit` stops (`scored_read`, or `scoring_table` when its `why` is changed too);
   - 6d, the other way (review N19): a scored E04 read filed as read-and-report (`scored=0`, `why=X08`, `verdict=REPORT`), its VERDICT counts made to agree. Every other check of `audit` passes; the SCORING table stops it (`scoring_table`, E04 (17, 15) against (17, 16)).
7. A falsifier evaluated on a read-and-report read: stage B stops (`falsifier`), in a row module and in a READ file.
8. Rule STOP without its evidence (the review's probes A, B and C, and the runs). Each is a STOP:
   - P05 call 7 cut to 3 records with no attempt (`stop_attempt_count`);
   - the complete block filed as `7.attempt1.hbp` beside a 3-record rerun (`stop_attempt_file`);
   - an attempt holding `anything`, beside the complete block (`stop_attempt_count`) and beside a rerun (`stop_attempt_file`);
   - a lost call whose last try has an empty engine stderr (`stop_engine_stderr`);
   - an R2 batch empty with rc=4, or cut to 2 records, with no attempts (`stop_attempt_count`);
   - an R2 batch with rc=137 (`run_rc`);
   - an attempt filed with the rerun's steps, at P05 call 7 and at R2 batch 5, and a lost call whose last try ran 2 records (`stop_attempt_steps`).
9. QE:
   - a panic after the t=2 row of the 6561 sector command, filed with rc=101: the read goes on, the command's 4 reads are NOT_MEASURED, and the READ file passes audit;
   - the same panic text filed with rc=0: a STOP `qe_stderr`;
   - B at (81, -1/54, t=2) moved by 1e-5: Q02 NOT_MET, with falsifier `par3`;
   - QE-RC.hbp short of a row: a STOP `qe_rc`.
10. Stray floats: 27 floats, bools, true divisions, Fractions, Decimals and complexes (review N18: from either side of a `Q`, into `make`, `fr`, `Iv`, `Rad` and `fmt`) against `qint` pairs, `Iv`, `Rad` and `fmt` each raise `TypeError` (the same `Fraction(1, 3) * 0.5` and `Fraction(0.1)` pass through `fractions.Fraction`); six faults planted in a copy of the live stage B source (true division, a float literal, `import fractions`, `import math`, `float()`, `round()`) are each found by the source scan.
11. A side file forged with every hash made to agree: one br of P08 call 0 moved by 1, its AGG_SIDE bytes and sha256, the block's AGG_END and SHA256SUMS rewritten. Its sums differ from the block's AGG_SUM: a STOP `side_sums`.
12. A moved frozen file (review N1, M8): `edit.py frozen` copies `reader/a` and `reader/b` into a git repository of their own, beside copies of the frozen file and its README with one of them moved (the repo's frozen files are only read). One digit of the frozen file moved stops `read` and `audit`, CRLF line ends stop `audit`, one byte of the README moved stops `verify`, and no README stops `read`: each a STOP `frozen_sha256`, with no READ file written. The unmoved copy passes `audit`, and its `read` gets past the frozen check (to a missing guard file, `FileNotFoundError`).

13. Not visible, by design (review N17, fabricated data only): case 2's sector swap at P01 call 0 of the fabricated campaign, with the block, its AGG_END and the point's SHA256SUMS all forged (`edit.py block --op swap_sec --rehash --sums`). `read` writes a READ file that passes `audit`, with the same 26 VERDICT rows (the same tally: MET 17, NONE 1, NOT_MET 5, NOT_RESOLVED 3) as the clean campaign. The only STRIPES_READ rows that move are two of E07 at P01: `lk_x2_P01_t1_LOCK`, a read-and-report value, 987.204892966 to 978.98470948, and the detail of `lk_lat_P01_t1_LOCK`. The case prints NOT_VISIBLE when exactly that holds; any other outcome is MISSED, since then this statement of the limit is out of date.

So a forger who rewrites a block, its AGG_END and the point's SHA256SUMS together is not visible in the aggregates, unless the block names a side file whose sums then disagree (case 11). The defense is to commit the aggregates and their sums with the run (run plan step 8), with the stream hashes stage A prints.

## No float

```
polariton-stripes/reader/check/no_float.sh
```

- Every folder row of `polariton-stripes/FLOAT-EVIDENCE.txt` is checked against its tree pin (`check/float_evidence.py`), and those folders are left out of the scans below.
- The Rust of stage A, with comments and strings removed, is grepped for f32 and f64, float literals and float methods.
- Every other .py under `reader/` is scanned as tokens for float and complex literals, float(), round, pow, math other than isqrt and gcd, numpy and the like, `builtins`, `__builtins__` and `tomllib`, and, after a `.`, the float doors (`pow`, `__pow__`, `float`, `__truediv__`, `cast`, `literal_eval`, `float_info`, `timestamp`, `st_mtime`, `getmtime`, `modules` and their kin).
- Then the AST check of `b/tests/test_nofloat.py` runs on every such .py: strict on `b/` (the rules above under "Integer pairs"), loose on `check/` and `sabotage/` (math.isqrt, math.gcd and fractions allowed there, and the modules of the strict list; no `/`, no `**`, and the attribute, `getattr`, format and struct rules hold).
- A self-test first plants one fault of each kind, the float doors of review M6 among them (`operator.pow`, `(2).__pow__`, `builtins.float`, `sys.float_info`, `time.time()`, `format()`, a computed `getattr` name, `from struct import unpack` with `<d`, `'{:.3f}'` and `'%(a).3f'`), and a moved pin.

## The run, with this seat's binaries

The binaries are built under this seat's scratch folder, never inside the repo:

```
OUT=/tmp/claude-0/-home-user/b2fb539a-cb4d-5f0b-a22f-ca1a7fcb500d/scratchpad/stripes-build
T=$OUT/tw/release/twens                          # twens 0.4.0, sha256 33e62fbe0837aeddc916a57d67848338cbc258aa1dfb85a01cfba53fb8a4e03f
QE=$OUT/qe/release/polariton_first_correction    # sha256 6bf8ebf2309700cb5be4cce25d82e5c4ee70fbc49521d4d7686cfc1649aa0a21 (equal to the lane build)
RA=$OUT/ra-remap/release/stripes-read-a          # stage A, sha256 af85e03d44bc056c9f7cb729a8c6c2a3f0263d5b7ac1eb96e8a748f0736b34ef (git tree dcab5aef of reader/a)
SB="python3 -I $PWD/polariton-stripes/reader/b/stripes_read_b/__main__.py"
```

Never use `polariton-bridge/engines/ensemble/target/release/twens`, a stale 0.3.0 build. Rebuild with `(cd polariton-bridge/engines/ensemble && cargo build --release --locked --offline --target-dir $OUT/tw)` and `CARGO_TARGET_DIR=$OUT/qe cargo build --release --locked --bin polariton_first_correction`, and check both sha256 before use. Build stage A from the committed reader with the path remapped, `(cd polariton-stripes/reader/a && RUSTFLAGS="--remap-path-prefix=$PWD=stage-a" CARGO_TARGET_DIR=$OUT/ra-remap cargo +1.81.0 build --locked --offline --release)`, and check that `sha256sum $RA` gives `af85e03d...` and `git rev-parse HEAD:polariton-stripes/reader/a` gives `dcab5aef...` (the pins of the stage A section). `$OUT/ra` keeps the earlier `c8c3f0d1` build. Commit the reader with its sha256 before step 3 (run plan step 2). In a sparse checkout whose cone leaves out `polariton-stripes/` (this seat's cone is `.github polariton-bridge review-tools src`), stage it with `git add --sparse polariton-stripes .github/workflows/polariton-stripes.yml`: the 103 new files (`FLOAT-EVIDENCE.txt`, `qint.py`, `test_qint.py`, `compare_b.py`, `float_evidence.py`, `probe_b.py` and the 97 evidence files) and every changed one, the 16 `.rc` fixtures among them. Then run `no_float.sh`, `run_tests.py`, `compare_b.py`, `e2e.py --keep` and `compare_read_b.py` on a fresh POSIX checkout of the commit (Linux, or WSL on ext4, not `/mnt/c`). The `reader_b` note of a READ file holds stage B's tree pin; `float_evidence.py --pins polariton-stripes/reader/b/` on the commit prints the same pin. Both take each mode from git's index (`git ls-files -s`), so any checkout of the commit gives that pin, and stage B writes no READ file from a working tree whose modes differ from the index or that holds a file the index does not. The `reader_a` note names stage A's source, the git tree of `reader/a` taken from the index (`git_tree_polariton-stripes/reader/a/_dcab5aef...` on the commit); stage B writes no READ file when a file under `reader/a` differs from the index or is not in it (STOP `stage_a_tree`), so stage those edits first too.

All commands below run in `polariton-stripes/receipts/`:

```
mkdir -p polariton-stripes/receipts/run && cd polariton-stripes/receipts
REL_MERGE=...   # the release row: the merge commit of PR #18,
REL_RA=...      # the stage A sha256 and
REL_RB=...      # stage B's tree pin, as the owner files them for the release
rel() { local top b; top=$(git rev-parse --show-toplevel) || return 1
  b=$(python3 -I "$top/polariton-stripes/reader/check/float_evidence.py" --repo "$top" --pins polariton-stripes/reader/b/ | sed -n 's/^polariton-stripes\/reader\/b\/ | tree=\([0-9a-f]\{64\}\) | $/\1/p')
  [ -n "${REL_MERGE:-}" ] && [ -n "${REL_RA:-}" ] && [ -n "${REL_RB:-}" ] \
  && git cat-file -e "$REL_MERGE^2" 2> /dev/null && git merge-base --is-ancestor "$REL_MERGE" HEAD \
  && git diff --quiet "$REL_MERGE" -- "$top/polariton-stripes/reader" "$top/polariton-stripes/PREDICTION-STRIPE-PHASE.hbp" \
  && [ -z "$(git status --porcelain --untracked-files=all -- "$top/polariton-stripes/reader")" ] \
  && [ "$(sha256sum "$RA" | cut -d' ' -f1)" = "$REL_RA" ] && [ "$b" = "$REL_RB" ] \
  || { echo "RELEASE_REFUSED|N=$1|delta=$2|y=$3|json=0" >&2; return 1; }; }
g() { rel "$@" && "$T" guard N=$1 delta=$2 y=$3 | tee -a GUARD.hbp | grep -q 'verdict=allowed'; }
```

Run `g` before every QE command and before every dump or run point (rule GUARD), and stop on any refusal. Never pass `lift_reserved_guard`.

The release-row check (review N4). Every triple `g` guards in this plan is a row point (P01-P14, R1-R4, QR1-QR5), and `g` refuses each one, before the engine's own guard runs, unless the release row is given and holds: `REL_MERGE` is a merge commit (it has a second parent) and an ancestor of HEAD; `reader/` and the frozen file in the working tree equal that commit's, and `reader/` holds no file git does not track (`git diff` against a commit cannot see an untracked file; review 5831368495, the second pass's notes on `rel`); `$RA` has the sha256 `REL_RA`; and stage B's tree pin (`float_evidence.py --pins`, the pin of the `reader_b` note) is `REL_RB`. A refusal prints `RELEASE_REFUSED` on stderr and writes nothing to GUARD.hbp. So the pre-merge ban on row-point runs, which until now was procedural only (receipt row 10, PR body line 1), is also in the wrapper. The readers themselves do not change: stage A and stage B still read a row point when given one, and this check lives in the run plan only. This seat tried `rel` with a stand-in `T` at the excluded triple (27, 1/4, 1/40) only, in a scratch git repository: no marker, a commit that is not a merge, a merge that is not an ancestor of HEAD, a reader file changed after the merge, a wrong `REL_RA` and a wrong `REL_RB` each refused, and the full marker passed to the stand-in guard (receipt, row 14). The untracked-file clause was added after that trial and tried on its own in a scratch git repository: a new untracked file under `reader/` refused, an ignored `__pycache__/` passed, from the top and from a subfolder. The stand-in wiring run below predates `rel`.

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

Ensemble runs R1-R4 (run plan step 5), one at a time with threads=4. Each batch files its stdout, its stderr, and its exit code with the steps of the try (`rc=E steps=S`). A batch that exits 4 is kept as an attempt and rerun with its last record and that record's ctrl entry dropped, until it completes or its one-record try exits 4 too (rule STOP):

```
run_pt() { local id=$1 N=$2 d=$3 y=$4 C=$5 S=$6 K=$7 j s k a x e; g $N $d $y || return 1
  for j in $(seq 0 63); do s=$S k=$K a=0
    while :; do
      "$T" run N=$N delta=$d u=1 y=$y seed_string=stripes-ens-v1:N$N:d$d:y$y start=$((j*C/64)) count=$((C/64)) dtden=64 threads=4 steps=$s "ctrl=$k" mask=VNC memo=1 > run/$id.$j.hbp 2> run/$id.$j.err; e=$?
      echo "rc=$e steps=$s" > run/$id.$j.rc
      [ "$e" = 4 ] && [ "${s#*,}" != "$s" ] || break
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
- it records both exit codes and the steps the try ran with in one trailer line, `rc=E rc_reader=R steps=S`;
- it files the engine's stderr as `<call>.eng.err` (the TWB_FAULT row of an exit 4) and stage A's as `<call>.err`.

```
one() { local id=$1 N=$2 d=$3 y=$4 i=$5 A=$6 S=$7 K=$8 mask=VNC side=() st
  [ "$i" -lt "$A" ] && mask=VNC,V1,V0,RN,FLIP,LOCK,MODE0,NL
  case $id in P08|P13) [ "$i" -lt 64 ] && side=(--side "agg/$id/$i.side");; esac
  { "$T" dump N=$N delta=$d u=1 y=$y seed_string=stripes-ens-v1:N$N:d$d:y$y start=$((4096*i)) count=4096 dtden=64 threads=1 steps=$S "ctrl=$K" mask=$mask 2> agg/$id/$i.eng.err < /dev/null; } | "$RA" --point $id --call $i "${side[@]}" > agg/$id/$i.hbp 2> agg/$id/$i.err
  st=("${PIPESTATUS[@]}"); echo "rc=${st[0]} rc_reader=${st[1]} steps=$S" >> agg/$id/$i.hbp; }
export -f one; export T RA
while read id N d y M A S K; do g $N $d $y || exit 1; mkdir -p agg/$id
  for i in $(seq 0 $((M/4096-1))); do echo "$id $N $d $y $i $A $S $K"; done
done < points.txt | xargs -P 4 -L 1 bash -c 'one "$@"' _
```

Rule STOP (run plan step 7). A call ending `rc=4 rc_reader=3 steps=S` (the engine printed nothing and filed a TWB_FAULT row) keeps its three files as `<call>.attempt<k>.hbp`, `.err` and `.eng.err`, k = 1, 2, ..., and is rerun with the same keys, its last record and its ctrl entry dropped, until it completes or its one-record try exits 4 too:

```
redo() { local id=$1 N=$2 d=$3 y=$4 i=$5 A=$6 S=$7 K=$8 k=0 x
  while [ "$(tail -n 1 agg/$id/$i.hbp)" = "rc=4 rc_reader=3 steps=$S" ] && [ "${S#*,}" != "$S" ]; do
    k=$((k + 1)); for x in hbp err eng.err; do mv agg/$id/$i.$x agg/$id/$i.attempt$k.$x; done
    S=${S%,*} K=${K%;*}; one $id $N $d $y $i $A $S $K
  done; }
while read id N d y M A S K; do g $N $d $y || exit 1
  for i in $(seq 0 $((M/4096-1))); do
    [ "$(tail -n 1 agg/$id/$i.hbp)" = "rc=4 rc_reader=3 steps=$S" ] && redo $id $N $d $y $i $A $S $K
  done
done < points.txt
```

Stage B checks every attempt against this procedure, keeps only the records every call reached, and marks the rest NOT_MEASURED. Any other trailer, or a reader STOP on a complete stream (`rc=0 rc_reader=3`), is a fault to report, not to rerun, and stage B refuses it. So does an attempt that is not an engine stop of its call, a count of attempts the procedure does not give, a try filed with steps the procedure does not give, or an exit 4 without its TWB_FAULT row.

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
- Runs: R2 batch 5 exited 4 with 3 records and completed with 2 (one attempt); batch 9 exited 4 at every try (two attempts and the last try). Stage B 0.1.0 read R2 as 63 batches, records 32 and 64, three attempts. Stage B 0.2.0, given the same receipts, checks the 63 batches and the three attempts, and keeps no record of R2 (rule STOP: batch 9 reached none), so every R2 read is NOT_MEASURED.
- Dumps, P13 with 8 calls: call 0 completed with its side file; call 5 exited 4 with 2 records and completed with 1 (one attempt); the other six exited 4 at both tries (one attempt each). Stage B's per-call STOP check passed every call, and the README's `sha256sum` line gave a SHA256SUMS stage B accepts.
- The guard file held 21 lines: 15 QE commands, 4 run points, and the dump point twice (before its calls and before its reruns).

Storage, an open decision:

- The aggregates are about 0.2 GB: about 120 KB for an all-variant call with 4 records, about 15 KB for a VNC-only call.
- The side files of P08 and P13 are 122 MB (950,336 bytes per call).
- No raw dump text is ever stored.
