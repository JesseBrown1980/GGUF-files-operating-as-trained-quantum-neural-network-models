#!/usr/bin/env python3
"""Independent exact-rational comparison gate for Google's official qsim 64 amplitudes.

The QNN output is integer pairs scaled by 2^60; Google's reference is its
own floating-point output parsed as exact decimal rationals. The comparator
itself uses only arbitrary-precision Python integers. No JSON or NumPy.
"""
import hashlib
import sys
from pathlib import Path

SCALE = 1 << 60
DEN = 1_000_000
UPSTREAM_COMMIT = "50cac4b3fa331450b70387735479a00e223b8d25"


def fail(reason):
    print("QSIM_REFERENCE_FAIL|reason=" + reason + "|json=0", file=sys.stderr)
    raise SystemExit(1)


def decimal_rational(text):
    text = text.strip().lower()
    exponent = 0
    if "e" in text:
        text, power = text.split("e")
        exponent = int(power)
    sign = -1 if text.startswith("-") else 1
    text = text.lstrip("+-")
    whole, dot, fraction = text.partition(".")
    if not whole and not fraction:
        fail("empty_decimal")
    if not (whole + fraction).isdigit():
        fail("invalid_decimal")
    numerator = int(whole + fraction) * sign
    exponent -= len(fraction)
    if exponent >= 0:
        return (numerator * 10 ** exponent, 1)
    return (numerator, 10 ** (-exponent))


def parse_ours(path):
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.startswith("FULL_Q24_AMPLITUDE|"):
            continue
        fields = dict(field.split("=", 1) for field in line.split("|")[1:])
        if set(fields) != {"index", "re_at_2^60", "im_at_2^60", "json"}:
            fail("bad_qnn_fields")
        if fields["json"] != "0":
            fail("json_control")
        out.append((int(fields["index"]), int(fields["re_at_2^60"]), int(fields["im_at_2^60"])))
    if len(out) != 64:
        fail("qnn_count_" + str(len(out)))
    if len({x[0] for x in out}) != 64:
        fail("duplicate_qnn_index")
    return out


def parse_qsim(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 2:
            fail("invalid_qsim_output_line")
        rows.append((decimal_rational(fields[0]), decimal_rational(fields[1])))
    if len(rows) != 64:
        fail("qsim_count_" + str(len(rows)))
    return rows


def bitstrings(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if len(lines) != 64:
        fail("source_bitstring_count")
    if any(len(x) != 24 or any(d not in "01" for d in x) for x in lines):
        fail("source_bitstring_shape")
    indices = [sum((d == "1") << i for i, d in enumerate(x)) for x in lines]
    if len(set(indices)) != 64:
        fail("duplicate_bitstring")
    return indices


def check(which, ours, qsim, expected_indices, require_match):
    wrong = 0
    worst_num, worst_den = 0, 1
    worst_index = -1
    for (index, re, im), (qre, qim), expected_index in zip(ours, qsim, expected_indices):
        if index != expected_index:
            fail("qsim_bitstring_order_mismatch")
        for mine, (ref_num, ref_den) in [(re, qre), (im, qim)]:
            delta_num = abs(mine * ref_den - ref_num * SCALE)
            delta_den = ref_den * SCALE
            if delta_num * worst_den > worst_num * delta_den:
                worst_num, worst_den, worst_index = delta_num, delta_den, index
            wrong += int(delta_num * DEN > delta_den)
    print(
        "QSIM_REFERENCE|case=%s|reference_commit=%s|bitstrings=64|parts=128|parts_above_1e-6=%d|"
        "max_difference_pico=%d|worst_index=%d|comparison_integer_rational=1|json=0"
        % (which, UPSTREAM_COMMIT, wrong, worst_num * 1_000_000_000_000 // worst_den, worst_index)
    )
    if (wrong == 0) != require_match:
        fail(which + "_unexpected_mismatch_count")
    return wrong


def main():
    if len(sys.argv) != 6:
        fail("usage: script BITSTRINGS QNN QSIM MUTANT_QNN OUT")
    bitfile, oursfile, qsimfile, mutantfile, recordfile = sys.argv[1:]
    expected = bitstrings(bitfile)
    ref = parse_qsim(qsimfile)
    ours = parse_ours(oursfile)
    mutant = parse_ours(mutantfile)
    from contextlib import redirect_stdout
    with Path(recordfile).open("w", encoding="utf-8") as f:
        with redirect_stdout(f):
            check("original", ours, ref, expected, True)
            check("mutated_y2_sign", mutant, ref, expected, False)
            print("QSIM_REFERENCE_DONE|original=PASS|mutant=REJECTED|source_commit=%s|json=0" % UPSTREAM_COMMIT)
    print(Path(recordfile).read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
