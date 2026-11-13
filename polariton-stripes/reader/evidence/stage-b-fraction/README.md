# Stage B on fractions.Fraction, kept as evidence

This folder holds stage B of the stripe reader as it was reviewed, at commit 5aad307 of branch `cloud-seat-stripe-reader-20261109`. It computes on `fractions.Fraction`. It is kept verbatim. It is not live code.

## What is here

- `stripes_read_b/`, `tests/`, `e2e.py`, `run_b.py` and `run_tests.py`: all 96 files of `polariton-stripes/reader/b/` at 5aad307, byte for byte (each checked against its blob in `git ls-tree -r 5aad307`).
- This README, the only file added.

## Why it is kept

On 2026-11-09 the owner ruled that stage B moves from `fractions.Fraction` to checked integer pairs before any run at a row point. The reason: one stray float slips through Fraction without an error. `Fraction(1, 3) * 0.5` returns a float, and `Fraction(0.1)` turns a float into a ratio without a word.

The live stage B in `polariton-stripes/reader/b/` now computes on `stripes_read_b/qint.py`: reduced (numerator, denominator) pairs, both parts checked to be `int` after every operation, compared by cross-multiplication.

The operator's rule of 2026-11-03 keeps replaced float-capable code as evidence, listed with its tree pin. This folder has one row in `polariton-stripes/FLOAT-EVIDENCE.txt`. A new file, a mode change or an edited byte here moves the pin, and `reader/check/no_float.sh` fails.

## How it is used

- Only `reader/check/compare_b.py` runs it. That script copies this folder into a scratch tree at its old depth, `<tmp>/polariton-stripes/reader/b/`, beside a copy of the frozen file. It runs this version and the live one on the same control inputs and requires byte-identical output.
- The control inputs are no row-point data: the frozen decimals and the closed forms at the excluded (delta, y, t), the QE rows at N = 9, delta = 1/3, the stage A blocks and run sums at N = 27, delta = 1/4, and the real side files of X1 and X0.
- At the conversion step, before any other change, both versions also read the same fabricated e2e campaigns and wrote byte-identical READ files.
- It is never run at a row point. No live module imports it.
- It does not run in place: `frozen.py` looks for the frozen file three folders up, which from here is `polariton-stripes/reader/`.

Do not edit anything in this folder. A change needs a new row in `FLOAT-EVIDENCE.txt`, with its reason.
