#!/usr/bin/env python3
# t5_vs_grid.py -- reads the first correction against my own grid rows: band (delta = -1, -3/4, -1/2, 0, 1/2, 3/4, 1) and outside.
# Exact rationals. For delta = +1, where the law's A1 and C1 are 0, the first correction is the leading term.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import t2_read as R
import t5_eval as E
from law import dec

def safe(a, b):
    return a/b if b not in (0, None) else None

def main():
    for grid in ('band', 'outside'):
        rows = R.merged(grid)
        print('GRID', grid, 'rows', len(rows))
        recs = []
        for r in rows:
            fo = E.first_order(r['delta'], r['y'], r['N'], r['t'])
            r['fo'] = fo
            recs.append(r)
        for delta in sorted(set(r['delta'] for r in recs)):
            for N in sorted(set(r['N'] for r in recs)):
                sel = [r for r in recs if r['delta'] == delta and r['N'] == N and r['L']['f'] <= Fr(1, 20) and r['fo']['f_first'] <= Fr(1, 20)]
                if not sel:
                    continue
                # only rows where a nonzero law or first-correction value exists
                a = [abs(safe(r['A1'], r['fo']['A1_first'])-1) for r in sel if r['fo']['A1_first']]
                c = [abs(safe(r['C1'], r['fo']['C1_first'])-1) for r in sel if r['fo']['C1_first']]
                d = [abs(safe(r['D2'], r['fo']['D2_first'])-1) for r in sel if r['fo']['D2_first']]
                v = [abs(safe(r['V2'], r['fo']['V2_lin'])-1) for r in sel if r['fo']['V2_lin']]
                al = [abs(safe(r['A1'], r['L']['A1'])-1) for r in sel if r['L']['A1']]
                cl = [abs(safe(r['C1'], r['L']['C1'])-1) for r in sel if r['L']['C1']]
                dl = [abs(safe(r['D2'], r['L']['D2'])-1) for r in sel if r['L']['D2']]
                vl = [abs(safe(r['V2'], r['L']['V2'])-1) for r in sel if r['L']['V2']]
                m = lambda x: dec(max(x), 4) if x else 'n/a'
                print('delta=%s N=%d rows=%d  worst |read/law-1|: A1=%s C1=%s V2=%s D2=%s ;  worst |read/(law+first)-1|: A1=%s C1=%s V2lin=%s D2=%s' % (
                    delta, N, len(sel), m(al), m(cl), m(vl), m(dl), m(a), m(c), m(v), m(d)))
        if grid == 'band':
            print('EDGE_PLUS: delta=+1, read/first at each s,t,N (first correction is the leading term there)')
            for r in sorted([r for r in recs if r['delta'] == 1 and r.get('s') in (Fr(1, 4), Fr(1), Fr(4))], key=lambda r: (r['s'], r['t'], r['N'])):
                fo = r['fo']
                print('  N=%d s=%s t=%s A1_read=%s A1_first=%s C1_read=%s C1_first=%s V2_read=%s V2_first=%s f=%s' % (
                    r['N'], r['s'], r['t'], dec(r['A1'], 8), dec(fo['A1_first'], 8), dec(r['C1'], 9), dec(fo['C1_first'], 9), dec(r['V2'], 6), dec(fo['V2_first'], 6) if fo['V2_first'] is not None else 'None', dec(r['f'], 4)))
    return 0

if __name__ == '__main__':
    sys.exit(main())
