# ens_merge_check.py -- the cloud seat's acceptance comparator for count-weighted reuse in twens (integers only).
# usage: python3 -I ens_merge_check.py REFERENCE.hbp PART.hbp [PART.hbp ...]
#        python3 -I ens_merge_check.py --stair REUSE.hbp NOREUSE_1.hbp [NOREUSE_2.hbp ...]
#   --stair: REUSE is one run whose records may sum different sample counts (a count per record, from one start).
#   Every summed row of REUSE must equal, field for field, the same row of the no-reuse run with that row's count n
#   and the same start, and REUSE must carry exactly the references' row set; fails by name: stair_row_set_differs,
#   stair_reference_row_sets_differ, stair_reference_unused, stair_reference_count_repeated,
#   stair_no_reference_for_count, stair_start_differs, stair_row_differs:<field>.
#   Adds the per-record sums of the PART runs (disjoint sample-index ranges of one job) and compares them with
#   REFERENCE, one run over the union. Exit 0 and CMP_DONE|result=EQUAL only if every keyed row agrees exactly.
#   Fails by name: index_ranges_not_disjoint_or_not_covering, job_fields_differ, row_set_differs, count_differs,
#   field_set_differs, sum_differs:<field>, eps_max_exceeds_reference, nl_rows_differ.
import sys

META = {'N', 'delta', 'u', 'y', 'seed', 'dtden', 'step', 'variant', 'init', 'seeds', 'kappa', 'phase', 'h', 'ctrl',
        'pair', 'units', 'float_used', 'json'}
RANGE = {'start', 'count'}
SUMMED_KINDS = ('TWB', 'TWB_ROUND', 'TWB_PAIR', 'TWB_PAIR_ROUND', 'TWENS', 'TWPAIR')


def fields(line):
    parts = line.rstrip('\n').split('|')
    return parts[0], dict(p.split('=', 1) for p in parts[1:] if '=' in p)


def load(path):
    rows, head, nl = {}, None, []
    for line in open(path, encoding='utf-8'):
        kind, f = fields(line)
        if kind == 'TWB_HEAD':
            head = f
        elif kind == 'TWB_NL':
            nl.append(line.rstrip('\n'))
        elif kind in SUMMED_KINDS:
            key = (kind, f.get('step'), f.get('variant') or f.get('pair'))
            if key in rows:
                fail('duplicate_row:%s' % (key,))
            rows[key] = f
    if head is None:
        fail('no_TWB_HEAD:%s' % path)
    return head, rows, nl


def fail(name):
    print('CMP_FAIL|check=%s|json=0' % name)
    sys.exit(1)


def stair():
    reuse_head, reuse_rows, _ = load(sys.argv[2])
    refs = {}
    for p in sys.argv[3:]:
        h, rows, _ = load(p)
        if h['start'] != reuse_head['start']:
            fail('stair_start_differs:%s' % p)
        for k in ('N', 'delta', 'u', 'y', 'seed', 'seed_string', 'dtden', 'q', 'sums', 'rounding'):
            if h.get(k) != reuse_head.get(k):
                fail('job_fields_differ:%s' % k)
        for k in ('steps', 'mask'):
            if h.get(k) != reuse_head.get(k):
                fail('job_fields_differ:%s' % k)
        if int(h['count']) in refs:
            fail('stair_reference_count_repeated:%s' % h['count'])
        refs[int(h['count'])] = rows
    if not refs:
        fail('no_parts')
    # completeness: every reference run carries one row set, and REUSE carries exactly that set (none missing, none extra)
    row_sets = {frozenset(rows) for rows in refs.values()}
    if len(row_sets) != 1:
        fail('stair_reference_row_sets_differ')
    if set(reuse_rows) != set(next(iter(row_sets))):
        fail('stair_row_set_differs')
    compared, counts = 0, set()
    for key, row in reuse_rows.items():
        n = int(row.get('n', row.get('samples', -1)))
        if n not in refs:
            fail('stair_no_reference_for_count:%d:%s' % (n, (key,)))
        counts.add(n)
        ref = refs[n].get(key)
        if ref is None or set(ref) != set(row):
            fail('stair_row_or_field_set_differs:%s' % (key,))
        for fname, v in row.items():
            if fname in RANGE:
                continue
            if ref[fname] != v:
                fail('stair_row_differs:%s:%s' % (fname, (key,)))
            compared += 1
    if counts != set(refs):
        fail('stair_reference_unused:%s' % ','.join(str(c) for c in sorted(set(refs) - counts)))
    print('CMP_DONE|mode=stair|rows=%d|counts=%s|fields_compared=%d|result=EQUAL|json=0' % (
        len(reuse_rows), ','.join(str(c) for c in sorted(counts)), compared))


def main():
    if sys.argv[1] == '--stair':
        stair()
        return
    ref_head, ref_rows, ref_nl = load(sys.argv[1])
    parts = [load(p) for p in sys.argv[2:]]
    if not parts:
        fail('no_parts')
    ranges = sorted((int(h['start']), int(h['count'])) for h, _, _ in parts)
    pos = int(ref_head['start'])
    for s, c in ranges:
        if s != pos:
            fail('index_ranges_not_disjoint_or_not_covering')
        pos = s + c
    if pos != int(ref_head['start']) + int(ref_head['count']):
        fail('index_ranges_not_disjoint_or_not_covering')
    for h, _, _ in parts:
        for k in ('N', 'delta', 'u', 'y', 'seed', 'seed_string', 'dtden', 'steps', 'mask', 'q', 'sums', 'rounding'):
            if h.get(k) != ref_head.get(k):
                fail('job_fields_differ:%s' % k)
    for _, rows, _ in parts:
        if set(rows) != set(ref_rows):
            fail('row_set_differs')
    for _, _, nl in parts:
        if nl != ref_nl:
            fail('nl_rows_differ')
    for _, rows, _ in parts:
        for key, ref in ref_rows.items():
            if set(rows[key]) != set(ref):
                fail('field_set_differs:%s' % (key,))
    compared = 0
    for key, ref in ref_rows.items():
        for fname, rv in ref.items():
            if fname in META or fname in RANGE:
                if fname in META and any(p[1][key].get(fname) != rv for p in parts):
                    fail('job_fields_differ:%s:%s' % (key[0], fname))
                continue
            if fname == 'eps_max':
                if max(int(p[1][key][fname]) for p in parts) > int(rv):
                    fail('eps_max_exceeds_reference:%s' % (key,))
                continue
            got = sum(int(p[1][key][fname]) for p in parts)
            if got != int(rv):
                fail(('count_differs:%s' if fname == 'n' else 'sum_differs:%s:%s') % ((key,) if fname == 'n' else (fname, key)))
            compared += 1
    print('CMP_DONE|parts=%d|rows=%d|integer_fields_compared=%d|result=EQUAL|json=0' % (len(parts), len(ref_rows), compared))


main()
