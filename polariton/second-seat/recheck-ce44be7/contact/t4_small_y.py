#!/usr/bin/env python3
# t4_small_y.py -- exact V^2/Y at very small y, N = 243 and 729: no sampling, the integer Chebyshev route.
# With y -> 0, <A> is linear in y and C1 stays at its y=0 value, so V^2/Y is the exact small-Y limit at finite N.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import chebdrv as D
from law import law, dec

ROOT = 'C:/tmp/opus55/polariton-recheck-contact-20261105/out/'

def main():
    out = []
    for N, y in ((243, Fr(1, 1024)), (729, Fr(1, 1728))):
        for delta in (Fr(0), Fr(1, 2), Fr(-1, 2)):
            TT = [Fr(k, 4) for k in range(1, 33)]
            rows = D.run_chain(N, N, 1, delta, y, TT, threads=1, moments=0)
            for row in rows:
                d = D.parse_row(row)
                t = Fr(d['t'])
                L = law(N, delta, y, t)
                V2 = Fr(int(d['V2_e18']), 10**18)
                C1 = Fr(int(d['C1_e18']), 10**18)
                A1 = Fr(int(d['A1_e18']), 10**18)
                f = Fr(int(d['f_e18']), 10**18)
                line = 'SMALLY|N=%d|delta=%s|y=%s|t=%s|f=%s|V2_over_Y=%s|A1_over_law=%s|C1_over_law=%s|V2_e18=%s|Y=%s|json=0' % (
                    N, delta, y, t, dec(f, 5), dec(V2/L['Y'], 4), dec(A1/L['A1'], 4), dec(C1/L['C1'], 4), d['V2_e18'], dec(L['Y'], 10))
                out.append(line)
    open(ROOT + 'SMALLY.hbp', 'w', newline='\n').write('\n'.join(out) + '\n')
    print(len(out))
    return 0

if __name__ == '__main__':
    sys.exit(main())
