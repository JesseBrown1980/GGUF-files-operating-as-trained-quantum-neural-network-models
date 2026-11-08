#!/usr/bin/env python3
"""Cloud C independently checks completeness and integer identity of twens reuse.

Run:
  python3 strict_reuse.py --stair STAIR NO_REUSE_COUNT_A NO_REUSE_COUNT_B ...
  python3 strict_reuse.py --union NO_REUSE_FULL PART_A PART_B ...

This verifier is independent of cloud-seat-reuse-gate's ens_merge_check.py.
No float arithmetic, JSON, external dependencies, or changes to inputs.
"""
import sys

KINDS = frozenset(("TWB", "TWB_ROUND", "TWB_PAIR", "TWB_PAIR_ROUND", "TWENS", "TWPAIR"))
META = frozenset(("N", "delta", "u", "y", "seed", "dtden", "step", "variant", "init",
                  "seeds", "kappa", "phase", "h", "ctrl", "pair", "units", "float_used", "json"))
JOB = ("N", "delta", "u", "y", "seed", "seed_string", "dtden", "steps", "mask",
       "q", "sums", "rounding", "cli")


def fail(reason):
    print("CLOUD_C_FAIL|reason=%s|json=0" % reason)
    raise SystemExit(1)


def fields(line):
    bits = line.rstrip("\n").split("|")
    result = {}
    for bit in bits[1:]:
        if not bit or "=" not in bit:
            fail("malformed_field")
        key, value = bit.split("=", 1)
        if not key or key in result:
            fail("duplicate_or_blank_field:%s" % key)
        result[key] = value
    return bits[0], result


def read(path):
    head, rows, nl = None, {}, []
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            kind, d = fields(line)
            if kind == "TWB_HEAD":
                if head is not None:
                    fail("duplicate_head")
                head = d
            elif kind == "TWB_NL":
                nl.append(line.rstrip("\n"))
            elif kind in KINDS:
                if "step" not in d or ("variant" not in d and "pair" not in d):
                    fail("incomplete_row_key:%s" % kind)
                key = (kind, d["step"], d.get("variant", d.get("pair")))
                if key in rows:
                    fail("duplicate_row:%s" % (key,))
                rows[key] = d
    if head is None or not rows or "start" not in head or "count" not in head:
        fail("missing_head_or_rows")
    return head, rows, nl


def same_job(a, b):
    for key in JOB:
        if a.get(key) != b.get(key):
            fail("job_field_differs:%s" % key)


def rows_identical(a, b):
    if set(a) != set(b):
        fail("row_set_differs:missing=%d:extra=%d" %
             (len(set(b) - set(a)), len(set(a) - set(b))))
    checked = 0
    for key in sorted(b):
        if set(a[key]) != set(b[key]):
            fail("field_set_differs:%s" % (key,))
        for name in sorted(b[key]):
            if a[key][name] != b[key][name]:
                fail("row_differs:%s:%s" % (name, (key,)))
            checked += 1
    return checked


def stair(paths):
    if len(paths) < 3:
        fail("stair_needs_two_references")
    head, actual, nl = read(paths[0])
    refs, reference_keys = {}, None
    for path in paths[1:]:
        h, rows, ref_nl = read(path)
        same_job(head, h)
        if h["start"] != head["start"]:
            fail("stair_start_differs")
        count = int(h["count"])
        if count in refs:
            fail("duplicate_reference_count")
        refs[count] = rows
        if reference_keys is None:
            reference_keys = set(rows)
        elif set(rows) != reference_keys:
            fail("reference_row_set_differs")
        if ref_nl != nl:
            fail("nl_rows_differ")
        for key, row in rows.items():
            n = row.get("n", row.get("samples"))
            if n is not None and int(n) != count:
                fail("reference_count_differs:%s" % (key,))
    if set(actual) != reference_keys:
        fail("row_set_differs:missing=%d:extra=%d" %
             (len(reference_keys - set(actual)), len(set(actual) - reference_keys)))
    used, checks = set(), 0
    for key, row in actual.items():
        n = row.get("n", row.get("samples"))
        if n is None or int(n) not in refs:
            fail("stair_no_reference_for_count:%s" % (key,))
        n = int(n)
        used.add(n)
        checks += rows_identical({key: row}, {key: refs[n][key]})
    print("CLOUD_C_PASS|mode=stair|rows=%d|counts=%s|fields=%d|json=0" %
          (len(actual), ",".join(str(n) for n in sorted(used)), checks))


def union(paths):
    if len(paths) < 3:
        fail("union_needs_parts")
    head, reference, nl = read(paths[0])
    parts = [read(path) for path in paths[1:]]
    ranges = sorted((int(h["start"]), int(h["count"])) for h, _, _ in parts)
    pos = int(head["start"])
    for start, count in ranges:
        if start != pos or count <= 0:
            fail("index_ranges_not_disjoint_or_not_covering")
        pos += count
    if pos != int(head["start"]) + int(head["count"]):
        fail("index_ranges_not_disjoint_or_not_covering")
    for h, rows, part_nl in parts:
        same_job(head, h)
        if part_nl != nl:
            fail("nl_rows_differ")
        if set(rows) != set(reference):
            fail("row_set_differs")
    compared = 0
    for key in sorted(reference):
        ref = reference[key]
        values = [rows[key] for _, rows, _ in parts]
        if any(set(v) != set(ref) for v in values):
            fail("field_set_differs:%s" % (key,))
        for name in sorted(ref):
            vals = [v[name] for v in values]
            if name in META or name in ("start", "count"):
                if name in META and any(v != ref[name] for v in vals):
                    fail("row_metadata_differs:%s" % name)
                continue
            if name == "eps_max":
                if max(int(v) for v in vals) != int(ref[name]):
                    fail("eps_max_differs:%s" % (key,))
            elif sum(int(v) for v in vals) != int(ref[name]):
                fail("sum_differs:%s:%s" % (name, (key,)))
            compared += 1
    print("CLOUD_C_PASS|mode=union|rows=%d|integer_fields=%d|parts=%d|json=0" %
          (len(reference), compared, len(parts)))


def main():
    if len(sys.argv) < 5:
        fail("usage")
    if sys.argv[1] == "--stair":
        stair(sys.argv[2:])
    elif sys.argv[1] == "--union":
        union(sys.argv[2:])
    else:
        fail("unknown_mode")


if __name__ == "__main__":
    main()
