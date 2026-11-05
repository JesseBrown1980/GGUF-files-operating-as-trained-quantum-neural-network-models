#!/usr/bin/env python3
# t3_read.py -- reads the outside-band grid against the continued law. Exact rationals, no float.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import t2_read as R
from law import law, dec

def ratio(a, b):
    return a/b if b not in (0, None) else None

def main():
    rows = R.merged('outside')
    print('rows', len(rows))
    print('TABLE_A: delta<-1: V2 read and law, ratio; all rows at N=729 with f_pred<=1/5, per delta; then worst ratio by N')
    for delta in sorted(set(r['delta'] for r in rows)):
        for N in sorted(set(r['N'] for r in rows)):
            sel = [r for r in rows if r['delta'] == delta and r['N'] == N]
            for (lo, hi, name) in ((Fr(0), Fr(1, 20), 'f<=1/20'), (Fr(1, 20), Fr(1, 5), '1/20<f<=1/5'), (Fr(1, 5), Fr(10**6), 'f>1/5')):
                s2 = [r for r in sel if lo < r['L']['f'] <= hi]
                if not s2:
                    continue
                # exclude rows where law V2 is zero or undefined
                vr = [ratio(r['V2'], r['L']['V2']) for r in s2 if r['L']['V2'] not in (None, 0)]
                ar = [ratio(r['A1'], r['L']['A1']) for r in s2 if r['L']['A1'] != 0]
                cr = [ratio(r['C1'], r['L']['C1']) for r in s2 if r['L']['C1'] != 0]
                dr = [ratio(r['D2'], r['L']['D2']) for r in s2 if r['L']['D2'] != 0]
                print('delta=%s N=%d %s rows=%d V2/law=%s A1/law=%s C1/law=%s D2/law=%s' % (delta, N, name, len(s2), R.rng(vr), R.rng(ar), R.rng(cr), R.rng(dr)))
    print()
    print('TABLE_B: delta>1 at N=729 and N=243: Y, law V2, read V2, law C1, read C1 per row, f')
    for delta in (Fr(5, 4), Fr(5, 3), Fr(2)):
        for N in (243, 729):
            for r in sorted([r for r in rows if r['delta'] == delta and r['N'] == N], key=lambda r: (r['s'] if 's' in r else 0, r['t'])):
                L = r['L']
                print('delta=%s N=%d s=%s t=%s Y=%s V2_law=%s V2_read=%s C1_law=%s C1_read=%s A1_law=%s A1_read=%s f_read=%s sign_A=%s' % (
                    delta, N, r.get('s'), r['t'], dec(L['Y'], 4), dec(L['V2'], 4), dec(r['V2'], 4), dec(L['C1'], 7), dec(r['C1'], 7), dec(L['A1'], 5), dec(r['A1'], 5), dec(r['f'], 5), '-' if r['A'] < 0 else '+'))
    print()
    print('TABLE_C: sign tests delta>1. Law: C1<0 and V2<0 for |Y|<1; V2>1 for |Y|>1.')
    for delta in (Fr(5, 4), Fr(5, 3), Fr(2)):
        for N in (81, 243, 729, 2187):
            sel = [r for r in rows if r['delta'] == delta and r['N'] == N and r['L']['V2'] is not None]
            if not sel:
                continue
            inner = [r for r in sel if abs(r['L']['Y']) < 1 and r['L']['Y'] != 0]
            outer = [r for r in sel if abs(r['L']['Y']) > 1]
            neg_ok = sum(1 for r in inner if r['C1'] < 0 and r['V2'] < 0)
            big_ok = sum(1 for r in outer if r['C1'] > 0 and r['V2'] > 1)
            print('delta=%s N=%d |Y|<1 rows=%d C1<0&V2<0 met=%d ; |Y|>1 rows=%d C1>0&V2>1 met=%d' % (delta, N, len(inner), neg_ok, len(outer), big_ok))
    print()
    print('TABLE_D: rows off the sign prediction at N=729, 243')
    for delta in (Fr(5, 4), Fr(5, 3), Fr(2)):
        for N in (243, 729, 2187):
            sel = [r for r in rows if r['delta'] == delta and r['N'] == N and r['L']['V2'] is not None]
            for r in sel:
                Y = r['L']['Y']
                if Y == 0:
                    continue
                ok = (r['C1'] < 0 and r['V2'] < 0) if abs(Y) < 1 else (r['C1'] > 0 and r['V2'] > 1)
                if not ok:
                    print('  OFF delta=%s N=%d s=%s t=%s Y=%s V2_law=%s V2_read=%s C1_law=%s C1_read=%s f_read=%s' % (delta, N, r.get('s'), r['t'], dec(Y, 4), dec(r['L']['V2'], 4), dec(r['V2'], 4), dec(r['L']['C1'], 7), dec(r['C1'], 7), dec(r['f'], 5)))
    print()
    print('TABLE_E: delta<-1 per row at N=729: Y, V2 law, read, ratio')
    for delta in (Fr(-5, 4), Fr(-5, 3), Fr(-2)):
        for r in sorted([r for r in rows if r['delta'] == delta and r['N'] == 729], key=lambda r: (r.get('s'), r['t'])):
            L = r['L']
            print('delta=%s N=729 s=%s t=%s Y=%s V2_law=%s V2_read=%s ratio=%s A1/law=%s C1/law=%s f_read=%s' % (
                delta, r.get('s'), r['t'], dec(L['Y'], 4), dec(L['V2'], 5), dec(r['V2'], 5), dec(ratio(r['V2'], L['V2']), 4) if L['V2'] else 'None', dec(ratio(r['A1'], L['A1']), 4), dec(ratio(r['C1'], L['C1']), 4), dec(r['f'], 5)))
    return 0

if __name__ == '__main__':
    sys.exit(main())
