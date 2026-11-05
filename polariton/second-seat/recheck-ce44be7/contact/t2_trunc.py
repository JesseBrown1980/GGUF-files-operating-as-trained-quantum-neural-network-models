#!/usr/bin/env python3
# t2_trunc.py -- N = 2187 rows the receipt does not hold, on a truncated Fock block whose edge weight is read on every row. Same integer route.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import chebdrv as D
import t5_eval as E
from law import law, dec

ROOT = 'C:/tmp/opus55/polariton-recheck-contact-20261105/out/'
N = 2187
root = 47
lines = []
for (delta, ts, nmax) in ((Fr(-1), [Fr(1), Fr(2), Fr(3)], 500), (Fr(1), [Fr(1), Fr(2), Fr(3)], 500), (Fr(-3, 4), [Fr(1), Fr(2)], 500), (Fr(-1, 2), [Fr(1), Fr(2)], 600), (Fr(3, 4), [Fr(1), Fr(2)], 500)):
    for s in (Fr(1, 4), Fr(1)):
        y = s/root
        rows = D.run_chain(N, nmax, 1, delta, y, ts, threads=2, moments=0)
        for row in rows:
            d = D.parse_row(row)
            t = Fr(d['t'])
            L = law(N, delta, y, t)
            fo = E.first_order(delta, y, N, t)
            V2 = Fr(int(d['V2_e18']), 10**18); A1 = Fr(int(d['A1_e18']), 10**18); C1 = Fr(int(d['C1_e18']), 10**18); f = Fr(int(d['f_e18']), 10**18)
            if L['V2']:
                line = 'TRUNC|N=%d|nmax=%d|delta=%s|s=%s|y2N=%s|t=%s|edge_weight_e18=%s|f=%s|V2=%s|law=%s|V2/law=%s|N(V2/law-1)=%s|A1/law=%s|C1/law=%s|A1/first=%s|C1/first=%s|json=0' % (
                    N, nmax, delta, s, dec(y*y*N, 4), t, d['boundary_e18'], dec(f, 5), dec(V2, 6), dec(L['V2'], 6), dec(V2/L['V2'], 4), dec((V2/L['V2']-1)*N, 2), dec(A1/L['A1'], 4), dec(C1/L['C1'], 4), dec(A1/fo['A1_first'], 4), dec(C1/fo['C1_first'], 4))
            else:
                line = 'TRUNC|N=%d|nmax=%d|delta=%s|s=%s|y2N=%s|t=%s|edge_weight_e18=%s|f=%s|V2=%s|A1=%s|C1=%s|A1/first=%s|C1/first=%s|json=0' % (
                    N, nmax, delta, s, dec(y*y*N, 4), t, d['boundary_e18'], dec(f, 5), dec(V2, 7), dec(A1, 8), dec(C1, 9), dec(A1/fo['A1_first'], 4), dec(C1/fo['C1_first'], 4))
            print(line, flush=True)
            lines.append(line)
open(ROOT + 'TRUNC-N2187.hbp', 'w', newline=chr(10)).write(chr(10).join(lines) + chr(10))
