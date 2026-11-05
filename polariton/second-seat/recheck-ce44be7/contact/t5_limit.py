#!/usr/bin/env python3
# t5_limit.py -- the first correction as the actual limit: N^2 (C1 - C0/N) and N (<A>/(N y) - w0) at N = 3^8, 3^10, 3^12 from the integer route on a truncated Fock block,
# with the weight on the block's edge read on each row, against the closed forms. Remainders should fall as 1/N.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import chebdrv as D
import t5_eval as E
from law import dec

ROOT = 'C:/tmp/opus55/polariton-recheck-contact-20261105/out/'

def main():
    rows = [(Fr(0), Fr(1), Fr(1), 300), (Fr(0), Fr(1), Fr(2), 900), (Fr(0), Fr(1, 2), Fr(2), 800), (Fr(1, 2), Fr(2), Fr(1), 300), (Fr(-1, 2), Fr(1, 2), Fr(2), 500),
            (Fr(3, 4), Fr(1), Fr(2), 500), (Fr(-3, 4), Fr(1), Fr(2), 400), (Fr(1), Fr(1), Fr(2), 300), (Fr(-1), Fr(1), Fr(2), 300), (Fr(5, 4), Fr(1), Fr(2), 200), (Fr(-5, 4), Fr(1), Fr(2), 200), (Fr(2), Fr(1), Fr(2), 200)]
    NR = [(6561, 81), (59049, 243), (531441, 729)]
    out = []
    for (delta, s, t, nmax) in rows:
        for (N, root) in NR:
            y = s/root
            r = D.run_chain(N, nmax, 1, delta, y, [t], threads=2, moments=0)[0]
            d = D.parse_row(r)
            fo = E.first_order(delta, y, N, t)
            C1 = Fr(int(d['C1_e18']), 10**18)
            A = Fr(int(d['A_e18']), 10**18)   # <A>/N
            bd = int(d['boundary_e18'])
            c_read = (C1 - fo['C0']/N)*N*N
            w_read = (A/y - fo['w0'])*N
            line = 'LIMIT|delta=%s|s=%s|t=%s|N=%d|nmax=%d|boundary_e18=%d|N2(C1-C0/N)=%s|C1v=%s|ratio=%s|N(A/Ny-w0)=%s|w1=%s|ratio=%s|json=0' % (
                delta, s, t, N, nmax, bd, dec(c_read, 4), dec(fo['C1v'], 4), dec(c_read/fo['C1v'], 5) if fo['C1v'] else 'None', dec(w_read, 4), dec(fo['w1'], 4), dec(w_read/fo['w1'], 5) if fo['w1'] else 'None')
            print(line, flush=True)
            out.append(line)
    open(ROOT + 'LIMIT.hbp', 'w', newline='\n').write('\n'.join(out) + '\n')
    return 0

if __name__ == '__main__':
    sys.exit(main())
