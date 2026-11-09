# Stage A output: the aggregate grammar

`stripes-read-a` (crate `reader/a/`, version 0.1.0) reads one twens 0.4.0 dump stream on stdin and writes one block of rows on stdout. This file is the whole contract for stage B. Stage B reads the aggregate rows and the side files only. It never reads dump text.

## 1. Command and exit codes

```
stripes-read-a --point ID --call I [--side PATH] < dump
```

- `ID` is a point of the table in section 9 (`P01`-`P14`, or the excluded test points `X1`, `X0`), or a test id: `T` followed by letters, digits, `-` or `_`. A test id has no table check (`table=none`). Stage B accepts only `P01`-`P14`.
- `I` is the call index, a canonical decimal integer below 2^64 (anything else is a STOP `usage`). At a table point the call reads samples `[4096 I, 4096 I + 4096)`.
- `--side PATH` writes the side file (section 7). It is required at P08 and P13 for calls `I < 64`; without it the call STOPs (`side_file_required`). It is allowed for any other call.
- Each key may appear once. Any other argument is a STOP (`usage`).

| exit | stdout |
|---|---|
| 0 | the aggregate block (section 3), ending with `AGG_END` |
| 3 | one `STOP` row (section 8); the same row on stderr |
| 101 | one `STOP` row with `reason=panic` (arithmetic overflow or another panic; the release build has overflow checks on) |
| 5 | nothing usable: stdout could not be written |

The run script appends one line after the reader's output, `rc=<e> rc_reader=<r>`: the engine's exit code and the reader's own (`PIPESTATUS[0]` and `PIPESTATUS[1]`, taken from one expansion right after the pipeline). That line is not part of the block and is not covered by `agg_sha256`. Stage B requires it on every call file: a block is read only with `rc=0 rc_reader=0`; a STOP row is accepted only as an engine stop (`rc=4`, reason `empty_stream`, `rc_reader=3`, rule STOP); anything else stops stage B.

## 2. Row syntax

- Every row is `KIND|key=value|...|json=0` followed by one `\n`. Keys appear in exactly the order given below. Values never contain `|`.
- Integers are canonical decimals: an optional `-`, no `+`, no leading zeros, no `-0`.
- Fixed-length vectors are joined by `:`. Lists of steps, variants and masks are joined by `,`. The ctrl list is joined by `;`.
- Units: `br`, `bi`, `b_br`, `b_bi` are integers at 2^40 (B = br/2^40 + i bi/2^40, the engine's `B_W/N`). Squares and products of them are exact at 2^80. Fourth powers are exact at 2^160. Bounds are in ulps of 2^-40.
- `point=ID|call=I` (written `PC` below) follows the kind in every row except `AGG_TWB_HEAD` and `AGG_NL`.

## 3. Row order of one block

```
AGG_HEAD
AGG_TWB_HEAD
AGG_CALL
AGG_ATOMS
AGG_LAT
for each record r (in the order of `steps`):
    for each sampled variant v present (order VNC, V1, V0, RN, FLIP, LOCK, MODE0):
        AGG_VR
        AGG_SUM  set=all
        AGG_SUM  set=atom
        AGG_BLK  n=4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096 (11 rows)
        AGG_CMP  (only when v is not VNC)
        AGG_LOCK (only when v is LOCK)
    AGG_NL      (only when NL is in the mask)
AGG_SIDE        (only with --side)
AGG_CHECK
AGG_END
```

A call with every variant, NL and 4 records has 431 rows (432 with `--side`). A VNC-only call with 4 records has 63.

## 4. Definitions used by the rows

Per sample, from the stream:

- `c_i = g_i / 2^35`, i = 0..5, from `TWB_DUMP_SAMPLE g=`. Each `g_i` is a multiple of 2^35 with `|c_i| <= 2048`, or the call STOPs.
- `y_zero` is 1 when the head's `y` is the rational 0, else 0.
- Atom flags (rule ATOMS), from `c0..c3`:
  - `nl_klein`: `(c0, c1) = R^k (c2, c3)` for some k = 0..3, `R(a, b) = (-b, a)`;
  - `nl_exch`: `c0 = c2` and `c1 = c3`;
  - `lk_klein`: `c0 c1 (c0^2 - c1^2) = 0`;
  - `lk_exch`: `c1 = 0`.
- The atom set of a variant (left out of every sector and sign count): at `y_zero=1`, `nl_klein` for the six non-LOCK variants and `lk_klein` for LOCK; at `y_zero=0`, `nl_exch` and `lk_exch`.
- The exchange-atom set of a variant, at every y: `nl_exch` for non-LOCK, `lk_exch` for LOCK.
- `sigma(X, Y)` in 0..15 (rule SECTOR): quadrant 0 if Y>=0, X>0; 1 if X<=0, Y>0; 2 if Y<=0, X<0; 3 if X>=0, Y<0; rotated to (a, b) with a>0, b>=0 (q1: (Y, -X); q2: (-X, -Y); q3: (-Y, X)); sub 0 if (a+b)^2 < 2a^2, 1 if b < a, 2 if (a+b)^2 > 2b^2, else 3; sigma = 4q + sub. Undefined at (0, 0).
- Certified sector of B = (br, bi) with bounds (b_br, b_bi) from `TWB_DUMP_RB`: the four corners (br +- b_br, bi +- b_bi) have the same sigma and none lies on an axis (X = 0 or Y = 0) or a diagonal (|X| = |Y|). Otherwise the sample is ambiguous. A box with a corner at |X| or |Y| >= 2^63, or a bound >= 2^63, is ambiguous.
- Sign state of br: `pos` if |br| > b_br and br > 0; `neg` if |br| > b_br and br < 0; `amb` otherwise. Likewise bi with b_bi.
- `big`: br^2 + bi^2 >= 2^40, that is |B| >= 2^-20.
- Lattice sector of a sample: `sigma(c0^2 - c1^2, 2 c0 c1)`, the sector of LOCK's start c^2.

## 5. The rows

### AGG_HEAD

`AGG_HEAD|reader=stripes-read-a|reader_version=0.1.0|PC|table=T|stdin_bytes=B|stdin_lines=L|stdin_sha256=H|json=0`

- `table`: `checked` for a table point, `none` for a test id.
- `stdin_bytes`, `stdin_lines`, `stdin_sha256`: the size, line count and SHA-256 (in-crate, FIPS 180-4) of the whole input, byte for byte. This is sha256 of the engine's stdout.

### AGG_TWB_HEAD

`AGG_TWB_HEAD|` followed by the stream's first row verbatim (it begins `TWB_HEAD|engine=twens|version=0.4.0|...`). Everything after the first `|` is the engine's row.

### AGG_CALL

`AGG_CALL|PC|N=|delta=|u=|y=|y_zero=|seed=|seed_string=|start=|count=|dtden=|h=|steps=|records=|mask=|variants=|nl=|ctrl=|nl_sha256=|json=0`

- `N`, `delta`, `u`, `y`, `seed`, `seed_string`, `start`, `count`, `dtden`, `mask`: as in the head row (`delta`, `u`, `y` are the head's rational text).
- `h`: floor(2^40 / (2 sqrt N)), as the engine computes it, equal to the `h` of every TWENS and TWB row.
- `steps`: the records, comma-separated; `records`: their number.
- `variants`: the sampled variants present, comma-separated, in the fixed order; VNC is always first (a stream without VNC STOPs).
- `nl`: 1 if NL is in the mask.
- `ctrl`: one `C:RS:mz` per record, `;`-separated. At a table point every entry is `0:0:0`.
- `nl_sha256`: SHA-256 of the call's `TWB_NL` rows, each with its `\n`, in record order; `none` when `nl=0`. The NL rows carry no call-specific field, so every call of a point with the same steps has the same `nl_sha256` (row E05).

### AGG_ATOMS

`AGG_ATOMS|PC|M=|nl_klein=|nl_exch=|lk_klein=|lk_exch=|json=0`

`M` is the number of samples in the call. The four counts are the numbers of samples with each flag (section 4). They do not depend on the variant or the record.

### AGG_LAT

`AGG_LAT|PC|lock_atoms=|lat_edge=|lat=L0:...:L15|json=0`

- `lock_atoms`: samples in LOCK's atom set (lk_klein at y=0, lk_exch at y!=0).
- `lat`: among the other samples, the count with lattice sector k, k = 0..15, when the lattice point is off the axes and diagonals.
- `lat_edge`: the other samples whose lattice point is on an axis or diagonal (0 at y=0, since those are atoms there).
- `lock_atoms + lat_edge + sum(lat) = M`. The row is printed whether or not LOCK is in the mask; it depends only on the draws.
- The lattice sector of an edge point (an axis or diagonal, which happens only at y != 0) is still `sigma(c0^2 - c1^2, 2 c0 c1)` by the half-open rule of section 4; AGG_LOCK uses it for those samples too. It is read and reported only.

### AGG_VR (one per record and variant)

`AGG_VR|PC|step=|variant=|M=|atoms=|xatoms=|xatom_bi_nz=|mp=|na_bi0=|sec=O0:...:O15|amb=|br_pos=|br_neg=|br_amb=|bi_pos=|bi_neg=|bi_amb=|at_br_pos=|at_br_neg=|at_br_amb=|at_bi_pos=|at_bi_neg=|at_bi_amb=|json=0`

- `atoms`: samples in the variant's atom set; `mp = M - atoms` (M-prime of rule B16).
- `xatoms`: samples in the variant's exchange-atom set; `xatom_bi_nz`: those of them with `bi != 0` (the E02 falsifier "an atom with bi != 0"; 0 when exchange holds bit-exactly).
- `na_bi0`: non-atom samples with `bi = 0` exactly (E02, read and report).
- `sec`: O_k, the non-atom samples whose certified sector is k; `amb`: the non-atom samples with no certified sector (A of rules SECTOR, H8, B16).
- `br_pos`, `br_neg`, `br_amb`: the non-atom samples by sign state of br; `bi_*` likewise.
- `at_br_*`, `at_bi_*`: the same sign states over the atoms.
- Identities, checked by the reader (a failure is the STOP `aggregate_identity`): `sum(sec) + amb = mp`; `br_pos + br_neg + br_amb = mp`; the same for bi; `at_br_pos + at_br_neg + at_br_amb = atoms`; the same for bi.
- Use: H8 pi pairs (k, k+8) and mirror pairs (k, 15-k) from `sec` with A = `amb`; the sign tests from `br_pos`/`br_neg` with A = `br_amb` (bi likewise); B16 from `sec`, `amb`, `mp`; Pi_hat from `br_pos`, `br_neg`, `br_amb` (the atoms' signs are in `at_br_*` if a read includes atoms).

### AGG_SUM (two per record and variant)

`AGG_SUM|PC|step=|variant=|set=S|m=|br=|bi=|br2=|bi2=|brbi=|bbr=|bbi=|bbr2=|bbi2=|json=0`

- `set=all` sums over all M samples; `set=atom` over the variant's atom set (`m = atoms`). The non-atom sums are `all - atom`.
- `br = Sum br`, `bi = Sum bi` (at 2^40); `br2 = Sum br^2`, `bi2 = Sum bi^2`, `brbi = Sum br bi` (exact, at 2^80); `bbr = Sum b_br`, `bbi = Sum b_bi` (ulps); `bbr2 = Sum b_br^2`, `bbi2 = Sum b_bi^2` (ulps squared). All signed or unsigned 128-bit integers.
- For `set=all`, `br`, `bi`, `br2`, `bi2`, `brbi`, `bbr`, `bbi` equal the stream's TWB `br`, `bi`, `br2`, `bi2`, `brbi` and TWB_ROUND `rb_br`, `rb_bi`; the reader checks this (STOP `aggregate_identity`), and `w = br2 + bi2` for every AGG_BLK with K n = M.
- Use: SIGNFLIP (rows E02-E04) with `Sum b_i`, `Sum b_i^2`, RB = `bbr` or `bbi`, `Sum rb_i^2` = `bbr2` or `bbi2`; rho_u, n*_hat, E18's `N^2 (br2 + bi2) / (M 2^80)`.

### AGG_BLK (eleven per record and variant)

`AGG_BLK|PC|step=|variant=|n=|K=|s2=|s4=|w=|w2=|sw=|json=0`

The call's samples, in index order, are cut into K = floor(M / n) consecutive blocks of n (each block inside the call; at M = 4096 no sample is left over). For block b, `S_b = (Sum br, Sum bi)` over its samples and `W_b = Sum (br^2 + bi^2)`. Over all samples, atoms included:

- `s2 = Sum_b |S_b|^2` (at 2^80);
- `s4 = Sum_b |S_b|^4` (at 2^160; up to 256 bits);
- `w = Sum_b W_b` (at 2^80; equals `br2 + bi2` of `set=all` when K n = M);
- `w2 = Sum_b W_b^2` (at 2^160);
- `sw = Sum_b |S_b|^2 W_b` (at 2^160).

Widths: `s2` and `w` are unsigned 128-bit; `s4`, `w2` and `sw` are unsigned 256-bit, so stage B must parse all three as integers wider than 128 bits. The reader STOPs with `block_sum_overflow` (detail `abs_S_b_squared`) when a block's |S_b|^2 reaches 2^127, and with `block_sum_overflow` (detail `u256`) when a 256-bit sum would wrap; a 128-bit sum that would wrap is a panic (exit 101, overflow checks on). The engine cannot reach these: its own fault at hL > 1/2 keeps mode amplitudes below about 4, so |br| < 2^44 and |S_b|^2 < 2^113.

Use (rows E12-E14, E17): pooled over the calls of a point, `Z_n = Sum s2 / Sum w`; the z_b of the frozen rule, `z_b = K_tot |S_b|^2 / Sum |B|^2`, has mean Z_n and sample variance from `Sum s2` and `Sum s4`; `w2` and `sw` allow a delta-method SE for the ratio instead; `K2(n) = Sum s2 / (n M_tot)` at 2^80.

### AGG_CMP (per record, for each variant other than VNC)

`AGG_CMP|PC|step=|variant=|ref=VNC|common=|br=t0:...:t8|bi=t0:...:t8|cert2=|mis=|cert2_big_both=|mis_big_both=|cert2_big_any=|mis_big_any=|json=0`

Over the samples that are non-atoms for both the variant and VNC (`common` of them; for the six non-LOCK variants the atom sets are the same, for LOCK they differ):

- `br`: a 3x3 table of sign states, row = the variant's state, column = VNC's, order pos, neg, amb, flattened row by row: `t = [pos/pos, pos/neg, pos/amb, neg/pos, neg/neg, neg/amb, amb/pos, amb/neg, amb/amb]`. `bi` likewise.
- `cert2`: samples with a certified sector in both; `mis`: those whose two sectors differ.
- `cert2_big_both`, `mis_big_both`: the same, restricted to samples where both B are `big`; `cert2_big_any`, `mis_big_any`: where at least one is `big`.
- Use: E06 (MODE0) reads `mis_big_both` (or `mis_big_any`) for the sector claim and `t1 + t3` of `br` for the certified sign disagreements; E16 (V1, V0, RN) and E15 (FLIP, LOCK) read the discordant cells, D+ = `t1` (variant pos, VNC neg) and D- = `t3` (variant neg, VNC pos), with the `amb` cells bracketing.

### AGG_LOCK (per record, when LOCK is present)

`AGG_LOCK|PC|step=|cert=|mis=|json=0`

`cert`: LOCK non-atom samples with a certified sector; `mis`: those whose certified sector differs from their lattice sector (E07 (i)), the lattice sector of an edge point taken by the half-open rule (section 5, AGG_LAT). Printed at every y; it is a prediction only at y = 0, where every edge point is an atom.

### AGG_NL (per record, when NL is in the mask)

`AGG_NL|` followed by the stream's `TWB_NL` row of that record verbatim. Its `br`, `bi` (at 2^40) and bounds are E05's data. The reader checks the row's grammar and constant fields, not its values.

### AGG_SIDE (with --side)

`AGG_SIDE|PC|path=|bytes=|sha256=|indices=|variants=|steps=|json=0`

The side file's path as given, its size, its SHA-256, the number of indices (= M), the variants it holds, and the records it holds (`64,128`, a prefix of that, or `none`).

### AGG_CHECK

`AGG_CHECK|PC|samples=|starts=|lin=|rows=|fields=|result=all_equal|json=0`

What section 6 compared: samples, (sample, variant) starts rebuilt, (sample, variant, record) linear controls, summary rows and summary fields. `result` is always `all_equal`; any difference is a STOP instead of a block.

### AGG_END

`AGG_END|PC|agg_lines=|agg_sha256=|json=0`

`agg_lines` is the number of rows before this one; `agg_sha256` is the SHA-256 of those rows, each with its `\n`. Stage B must recompute it and refuse a block whose hash differs (an edited count, such as two swapped sector counts, fails here).

## 6. What stage A has checked when it prints a block

- The rows are exactly those `twens dump` prints, in its order: `TWB_HEAD`; per sample `TWB_DUMP_SAMPLE`, then per variant `TWB_DUMP_INIT`, `TWB_DUMP_IB` and per record `TWB_DUMP_OBS`, `TWB_DUMP_RB`; per record the legacy `TWENS` rows (V1, VN, V0, RN), `TWPAIR`, per variant `TWB` and `TWB_ROUND`, the `TWB_PAIR` and `TWB_PAIR_ROUND` rows of the pairs whose variants are on, and `TWB_NL`; then `TWB_DONE`, and nothing after it. Every row has its exact key sequence. A missing, extra, reordered or unterminated row is a STOP; so is a stream with no `TWB_DONE`.
- `TWB_HEAD`: engine=twens, version=0.4.0, cli=dump, binary_sha256=33e62fbe0837aeddc916a57d67848338cbc258aa1dfb85a01cfba53fb8a4e03f, source_sha256 main.rs:1d768fa9..., sha256.rs:7447d1e8... (in full), reserved=0, guard=active, float_used=0, q=40, threads=1, samples=count, count <= 4096, seed = the first 8 bytes of sha256(seed_string), steps strictly increasing, mask in canonical order with VNC. `float_used=0` on every row that prints it.
- Every metadata field of every summary row equals the head's; `n` = count; the variant's init, seeds, kappa and phase names are the engine's; `h` as in AGG_CALL; one ctrl per record across its rows.
- Per sample: each g_i is a multiple of 2^35 with |c_i| <= 2048; every variant's start (`TWB_DUMP_INIT s`), control seeds (`uv`) and start bounds (`TWB_DUMP_IB e0, ep, em, seeds`) equal the engine's construction from the draws, operation for operation; `eta` is the same for all variants of a sample, and `rot = 2^40:0`, `eta = 0` when MODE0 is off. Per record, `zcr`, `zci`, `xc` equal the linear control from ctrl and `uv`.
- Every field of every TWENS, TWPAIR, TWB (34 fields), TWB_ROUND (34 fields and eps_max), TWB_PAIR and TWB_PAIR_ROUND row equals the reader's own sum over the per-sample rows.
- At a table point: N, delta, u=1, y, seed_string, start = 4096 call, count = 4096, dtden = 64, the mask of the call (section 9), steps a nonempty prefix of the point's steps (rule STOP drops last records), ctrl 0:0:0 on every record, and call < calls of the point.

Stage A does not check across calls. Stage B checks: each point's SHA256SUMS against its receipts (every `.hbp`, `.err` and `.eng.err`), `agg_sha256`, each call's `nl_sha256` against its own AGG_NL rows, the AGG_CMP nesting (`mis_big_both <= mis_big_any <= mis <= cert2 <= common`, `cert2_big_both <= cert2_big_any <= cert2`), one block per call 0..calls-1 at each point (a dropped or repeated call), the side files' size and `sha256`, and rule STOP's record truncation against the attempts filed (section 10). Whether `nl_sha256` is equal across the calls of a point with the same steps is row E05's read, not a STOP.

## 7. Side file

Little-endian binary. One file per call, written only with `--side`.

Header, 64 bytes:

| offset | type | value |
|---|---|---|
| 0 | 8 bytes | `STRPSIDE` |
| 8 | u32 | format version, 1 |
| 12 | u32 | number of variants present, nv |
| 16 | u32 | variant mask: bit k set when variant k is present (k: VNC 0, V1 1, V0 2, RN 3, FLIP 4, LOCK 5, MODE0 6) |
| 20 | u32 | number of side records, nrec (0, 1 or 2) |
| 24 | u32 | step of side record 0 (64), 0 if nrec < 1 |
| 28 | u32 | step of side record 1 (128), 0 if nrec < 2 |
| 32 | u64 | start index |
| 40 | u64 | count M |
| 48 | 16 bytes | zero |

The side records are the stream's records whose step is 64 or 128, in stream order. Then, for each sample in index order (index = start + position), `8 + 16 nv nrec` bytes:

- u64 flags: bit 0 nl_klein, bit 1 nl_exch, bit 2 lk_klein, bit 3 lk_exch (section 4); the other bits zero;
- for each present variant in the fixed order, for each side record: i64 `br`, then u64 `b_br` (a bound above 2^64 - 1 is a STOP).

At P08 and P13 (all seven variants, steps 64 and 128) a call's file is 950,336 bytes; 64 calls make about 61 MB per point. E04 pairs index i of P08 with index i of P13 (both seeds, indices below 2^18).

## 8. STOP row

`STOP|reader=stripes-read-a|reader_version=0.1.0|point=|call=|reason=|line=|detail=|stdin_bytes=|stdin_lines=|stdin_sha256=|json=0`

- `point`, `call`: as given (`-` when the arguments did not parse).
- `line`: the input line where the fault was found; 0 when it was found after the whole stream was read (the summary and start checks).
- `detail`: key=value pairs joined by `,` (printable, `|` replaced by `_`).
- After a STOP the reader still reads the rest of stdin, so `stdin_*` cover the whole input and the engine is not cut off.
- A panic row is `STOP|reader=stripes-read-a|reader_version=0.1.0|reason=panic|detail=|json=0` (exit 101).

Reasons:

| reason | cause |
|---|---|
| `usage` | bad or missing arguments |
| `unknown_point` | an id that is neither in the table nor a test id |
| `side_file_required` | P08 or P13 with call < 64 and no `--side` |
| `read_error` | stdin could not be read |
| `empty_stream` | no input (the engine prints nothing when it stops, rule STOP) |
| `unterminated_last_line` | the input ends inside a line |
| `non_printable_byte` | a byte outside printable ASCII (including `\r`) |
| `first_row_not_TWB_HEAD` | the first row is not the head |
| `head_version`, `head_binary_sha256`, `head_source_sha256`, `head_reserved`, `head_guard`, `head_float_used`, `head_seed`, `head_count`, `head_dtden`, `head_N`, `head_mask`, `head_steps_not_increasing` | a head field outside section 6 (`head_count`: count = 0, count > 4096, samples != count, or start + count beyond 2^64; `head_mask`: an unknown name, or names out of order or repeated) |
| `table_mismatch`, `table_call_out_of_range` | the head or ctrl is not the table's for this point and call |
| `truncated` | the stream ends before an expected row (no `TWB_DONE`, or rows missing) |
| `rows_after_TWB_DONE` | content after the last row |
| `row_kind`, `row_key`, `row_short`, `row_long`, `row_field_without_value` | a row of the wrong kind or key sequence |
| `bad_integer`, `bad_list`, `bad_rational` | a value that is not canonical |
| `field_value` | a metadata or constant field differs from the head or the engine's text |
| `float_used` | a row prints `float_used` other than 0 |
| `sample_index` | a sample row out of index order |
| `ctrl_differs_within_record`, `h_differs`, `h_mismatch`, `record_without_ctrl` | ctrl or h inconsistent |
| `draw_not_a_coin_count` | a g_i not a multiple of 2^35, or |c_i| > 2048 |
| `rot_without_MODE0`, `eta_mismatch` | MODE0's draw fields inconsistent |
| `start_rebuild` | the engine would have stopped at this sample (a non-positive square-root argument) |
| `start_mismatch`, `control_seed_mismatch`, `start_bound_mismatch` | a start, `uv` or start bound differs from the construction from the draws |
| `linear_control_mismatch` | `zcr`, `zci` or `xc` differs from the linear control |
| `summary_mismatch` | a summary field differs from the reader's sum (`detail` names row, step, variant or pair, field, both values) |
| `missing_TWB`, `missing_TWB_ROUND`, `missing_TWENS`, `missing_TWB_PAIR` | an expected summary row absent |
| `aggregate_identity` | an AGG_VR identity of section 5 failed (a reader fault) |
| `block_sum_overflow`, `side_bound_above_u64` | a value beyond the reader's integer widths |
| `side_write` | the side file could not be written (a partial file is removed) |
| `no_VNC` | the head's mask has no VNC |

## 9. Point table

The id fixes the stream of each call (STRIPES_POINT and STRIPES_POINTS_COMMON of the frozen file). `seed_string = stripes-ens-v1:N<N>:d<delta>:y<y>`, u = 1, dtden = 64, count = 4096, start = 4096 call, ctrl 0:0:0 per record. Calls below `all` use mask `VNC,V1,V0,RN,FLIP,LOCK,MODE0,NL`, the later calls `VNC`.

| id | N | delta | y | calls | all | steps | side |
|---|---|---|---|---|---|---|---|
| P01 | 1296 | 1/2 | 0 | 1024 | 64 | 64,128,192,256 | |
| P02 | 1296 | 1/2 | 1/576 | 1024 | 64 | 64,128,192,256 | |
| P03 | 1296 | 1/2 | 1/288 | 1024 | 64 | 64,128,192,256 | |
| P04 | 1296 | 1/2 | 1/144 | 1024 | 64 | 64,128,192,256 | |
| P05 | 1296 | 1/2 | 1/72 | 256 | 64 | 64,128,192,256 | |
| P06 | 1296 | 1/2 | 1/36 | 256 | 64 | 64,128,192,256 | |
| P07 | 729 | -1/4 | 0 | 256 | 64 | 128,192,256 | |
| P08 | 729 | -1/4 | 1/54 | 256 | 64 | 64,128,192,256 | calls < 64 |
| P09 | 121 | 1/2 | 0 | 256 | 64 | 64,128,192,256 | |
| P10 | 121 | 1/2 | 1/11 | 256 | 64 | 64,128,192,256 | |
| P11 | 1296 | 1/2 | 1/648 | 1024 | 64 | 64,128,192,256 | |
| P12 | 324 | 1/2 | 1/162 | 1024 | 64 | 64,128,192,256 | |
| P13 | 729 | -1/4 | -1/54 | 64 | 64 | 64,128 | calls < 64 |
| P14 | 729 | -1/4 | 1/108 | 256 | 0 | 64,128 | |
| X1 | 27 | 1/4 | 1/40 | 8 | 8 | 64,128 | (excluded test point) |
| X0 | 27 | 1/4 | 0 | 8 | 8 | 64,128 | (excluded test point) |

The P points total 8000 calls.

## 10. Notes for stage B

- Everything is an integer. Form every mean, ratio and test in exact rationals; compare squares by cross-multiplying, as rule DECIMAL says.
- Pooling a point: add the AGG_VR counts, the AGG_SUM sums and the AGG_BLK sums over its calls, record by record and variant by variant. The controls cover the calls below `all` only (the first 2^18 indices).
- The files of call `i` in a point folder: `i.hbp` (this block, or a STOP row, then the trailer `rc=E rc_reader=R`), `i.err` (stage A's stderr: empty beside a block, the STOP row beside a STOP), `i.eng.err` (the engine's stderr: empty after a completed dump, one TWB_FAULT row after an exit 4) and `i.side`.
- Rule STOP: a call whose engine exited 4 has `rc=4 rc_reader=3` and stage A's `empty_stream` STOP. Its files are kept as `i.attempt<k>.hbp`, `.err` and `.eng.err`, k = 1, 2, ..., and it is rerun with its last record and that record's ctrl entry dropped, until it completes or its one-record try exits 4 too. A block with r of the point's R records has attempts 1..R-r; a call that never completed has attempts 1..R-1 and a STOP in `i.hbp`; a complete block has none. Each attempt must be an engine stop of its point and call with its TWB_FAULT row.
- Keep only the records every call of the point reached; the later records of the other calls are discarded unread and marked NOT_MEASURED.
- A STOP block means the call is not read. Decide nothing from values.
