#!/usr/bin/env python3
# t4_split.py -- the README's 35 rows (N>=243, predicted f>1/10, conversion rows of the receipt): how much is forced by the ceiling.
# Reads each row in V^2/law, in the complement (1-V^2)/(1-law), and in the uncompressed Y_read = V^2/(1-V^2) against Y.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import chebdrv as D
from law import law, dec

REC = 'C:/tmp/qnn-polariton-wt/polariton/RECEIPT.hbp'

def rows():
    out = []
    with open(REC, encoding='utf8', newline='') as fh:
        for ln in fh:
            ln = ln.rstrip('\r\n')
            if ln.startswith('POLARITON_QUENCH_CONVERSION|'):
                out.append(D.parse_row(ln))
    return out

def main():
    all_rows = rows()
    sel = []
    for d in all_rows:
        N = int(d['N']); delta = Fr(d['delta']); y = Fr(d['y']); t = Fr(d['t'])
        L = law(N, delta, y, t)
        if N >= 243 and L['f'] > Fr(1, 10):
            A = Fr(int(d['A_ppb']), 10**9); C1 = Fr(int(d['C1_ppb']), 10**9)
            A1 = 2*abs(A)/N
            V2 = A1*A1/(2*C1)
            f_read = Fr(int(d['f_ppb']), 10**9)
            sel.append(dict(N=N, delta=delta, s=d['s'], t=t, L=L, V2=V2, A1=A1, C1=C1, f_read=f_read))
    print('rows N>=243, predicted f>1/10:', len(sel))
    print(' min/max V2/law: %s %s' % (dec(min(r['V2']/r['L']['V2'] for r in sel), 4), dec(max(r['V2']/r['L']['V2'] for r in sel), 4)))
    print(' min A1/law %s, min C1/law %s' % (dec(min(r['A1']/r['L']['A1'] for r in sel), 4), dec(min(r['C1']/r['L']['C1'] for r in sel), 4)))
    print()
    print('N delta s t Y law V2 V2/law ceiling=1/law (1-V2)/(1-law) Y_read/Y f_pred f_read A1/law C1/law')
    for r in sorted(sel, key=lambda r: r['L']['V2']):
        L = r['L']
        yr = r['V2']/(1-r['V2']) if r['V2'] != 1 else None
        print('%d %s %s %s %s %s %s %s %s %s %s %s %s %s %s' % (
            r['N'], r['delta'], r['s'], r['t'], dec(L['Y'], 3), dec(L['V2'], 4), dec(r['V2'], 4), dec(r['V2']/L['V2'], 4), dec(1/L['V2'], 3),
            dec((1-r['V2'])/(1-L['V2']), 3), (dec(yr/L['Y'], 3) if yr is not None else 'None'), dec(L['f'], 3), dec(r['f_read'], 3), dec(r['A1']/L['A1'], 3), dec(r['C1']/L['C1'], 3)))
    small = [r for r in sel if r['L']['V2'] <= Fr(1, 2)]
    large = [r for r in sel if r['L']['V2'] > Fr(1, 2)]
    def summ(name, rs):
        if not rs:
            print(name, 'none'); return
        yrs = [(r['V2']/(1-r['V2']))/r['L']['Y'] for r in rs if r['V2'] < 1]
        print('%s rows=%d V2/law=%s..%s Y_read/Y=%s..%s (1-V2)/(1-law)=%s..%s f_read=%s..%s C1/law=%s..%s A1/law=%s..%s' % (
            name, len(rs), dec(min(r['V2']/r['L']['V2'] for r in rs), 4), dec(max(r['V2']/r['L']['V2'] for r in rs), 4),
            dec(min(yrs), 3), dec(max(yrs), 3),
            dec(min((1-r['V2'])/(1-r['L']['V2']) for r in rs), 3), dec(max((1-r['V2'])/(1-r['L']['V2']) for r in rs), 3),
            dec(min(r['f_read'] for r in rs), 3), dec(max(r['f_read'] for r in rs), 3),
            dec(min(r['C1']/r['L']['C1'] for r in rs), 3), dec(max(r['C1']/r['L']['C1'] for r in rs), 3),
            dec(min(r['A1']/r['L']['A1'] for r in rs), 3), dec(max(r['A1']/r['L']['A1'] for r in rs), 3)))
    print()
    summ('LAW<=1/2 (Y<=1)', small)
    summ('LAW>1/2  (Y>1) ', large)
    deep_small = [r for r in small if r['f_read'] > Fr(1, 5)]
    summ('LAW<=1/2 and f_read>1/5', deep_small)
    return 0

if __name__ == '__main__':
    sys.exit(main())
