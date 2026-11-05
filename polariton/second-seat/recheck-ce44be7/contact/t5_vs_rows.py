#!/usr/bin/env python3
# t5_vs_rows.py -- reads the first correction against the receipt's conversion rows (the receipt's own integers),
# and against my grid rows. Exact rationals, no float.
import sys, glob
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import chebdrv as D
import t5_eval as E
from law import law, dec

REC = 'C:/tmp/qnn-polariton-wt/polariton/RECEIPT.hbp'

def receipt_rows():
    rows = []
    with open(REC, encoding='utf8', newline='') as fh:
        for ln in fh:
            ln = ln.rstrip('\r\n')
            if ln.startswith('POLARITON_QUENCH_CONVERSION|'):
                rows.append(D.parse_row(ln))
    return rows

def main():
    rows = receipt_rows()
    print('rows', len(rows))
    print('MISSES: C1 frozen at 5 percent, predicted f<=1/20, N>=243')
    bigger = []
    for d in rows:
        N = int(d['N']); delta = Fr(d['delta']); y = Fr(d['y']); t = Fr(d['t'])
        L = law(N, delta, y, t)
        C1 = Fr(int(d['C1_ppb']), 10**9); A = Fr(int(d['A_ppb']), 10**9); B = Fr(int(d['B_ppb']), 10**9)
        A1 = 2*abs(A)/N; D2 = 2*abs(B)/N
        fo = E.first_order(delta, y, N, t)
        V2 = A1*A1/(2*C1)
        rec = dict(N=N, delta=delta, y=y, t=t, s=d['s'], f_pred=L['f'], f_read=Fr(int(d['f_ppb']), 10**9),
                   C1=C1, C1_law=L['C1'], C1_first=fo['C1_first'], A1=A1, A1_law=L['A1'], A1_first=fo['A1_first'],
                   V2=V2, V2_law=L['V2'], V2_first=fo['V2_first'], V2_lin=fo['V2_lin'], D2=D2, D2_law=L['D2'], D2_first=fo['D2_first'])
        bigger.append(rec)
        if N >= 243 and L['f'] <= Fr(1, 20) and abs(C1/L['C1'] - 1) > Fr(1, 20):
            print('  MISS N=%d delta=%s y=%s t=%s f_pred=%s C1_read=%s law=%s read/law=%s first=%s read/first=%s' % (
                N, delta, y, t, dec(L['f'], 4), dec(C1, 6), dec(L['C1'], 6), dec(C1/L['C1'], 4), dec(fo['C1_first'], 6), dec(C1/fo['C1_first'], 4)))
    print()
    print('TABLE: every conversion row: read/law and read/(law+first correction) for A1, C1, V2, D2')
    print('N delta s t f_pred  A1/law A1/first  C1/law C1/first  V2/law V2/first V2/lin  D2/law D2/first')
    for r in bigger:
        print('%d %s %s %s %s  %s %s  %s %s  %s %s %s  %s %s' % (
            r['N'], r['delta'], r['s'], r['t'], dec(r['f_pred'], 3),
            dec(r['A1']/r['A1_law'], 4), dec(r['A1']/r['A1_first'], 4),
            dec(r['C1']/r['C1_law'], 4), dec(r['C1']/r['C1_first'], 4),
            dec(r['V2']/r['V2_law'], 4), dec(r['V2']/r['V2_first'], 4), dec(r['V2']/r['V2_lin'], 4),
            dec(r['D2']/r['D2_law'], 4), dec(r['D2']/r['D2_first'], 4)))
    # summary at f_pred <= 1/20
    for (lim, name) in ((Fr(1, 20), 'f_pred<=1/20'), (Fr(1, 10), 'f_pred<=1/10')):
        sel = [r for r in bigger if r['f_pred'] <= lim and r['N'] >= 243]
        def span(key, ref):
            vals = [abs(r[key]/r[ref]-1) for r in sel]
            return dec(max(vals), 4)
        print('SUMMARY %s N>=243 rows=%d worst |read/law-1|: A1=%s C1=%s V2=%s D2=%s ; worst |read/first-1|: A1=%s C1=%s V2=%s D2=%s' % (
            name, len(sel), span('A1', 'A1_law'), span('C1', 'C1_law'), span('V2', 'V2_law'), span('D2', 'D2_law'),
            span('A1', 'A1_first'), span('C1', 'C1_first'), span('V2', 'V2_first'), span('D2', 'D2_first')))
    return 0

if __name__ == '__main__':
    sys.exit(main())
