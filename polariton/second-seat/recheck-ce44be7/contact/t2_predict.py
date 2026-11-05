#!/usr/bin/env python3
# t2_predict.py -- writes what the law predicts on the task 2 and task 3 grids, BEFORE any of these rows is read.
import sys, hashlib
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
from law import law, dec

ROOT = 'C:/tmp/opus55/polariton-recheck-contact-20261105/out/'

SS = [Fr(1, 4), Fr(3, 8), Fr(1, 2), Fr(3, 4), Fr(1), Fr(3, 2), Fr(2), Fr(3), Fr(4)]
SS5 = [Fr(1, 4), Fr(1, 2), Fr(1), Fr(2), Fr(4)]
TT = [Fr(1, 2), Fr(1), Fr(2), Fr(3)]
DEN = {81: 9, 243: 16, 729: 27, 2187: 47}
BAND = [Fr(-1), Fr(-3, 4), Fr(-1, 2), Fr(0), Fr(1, 2), Fr(3, 4), Fr(1)]
# outside the band: rational w where possible. 5/4 -> w=3/4, 5/3 -> w=4/3, 13/5 -> w=12/5, 2 -> w=sqrt3
OUTSIDE = [Fr(5, 4), Fr(5, 3), Fr(2), Fr(-5, 4), Fr(-5, 3), Fr(-2)]
TT_OUT = [Fr(1, 2), Fr(1), Fr(2), Fr(3), Fr(4), Fr(6)]

def grid_band():
    for N in (81, 243, 729):
        for d in BAND:
            for s in SS:
                yield N, d, s/DEN[N], s, TT
    for d in BAND:
        for s in SS5:
            yield 2187, d, s/DEN[2187], s, TT

def grid_outside():
    for N in (81, 243, 729, 2187):
        for d in OUTSIDE:
            for s in SS5:
                yield N, d, s/DEN[N], s, TT_OUT

def fmt(N, d, y, s, t, tag):
    L = law(N, d, y, t)
    return 'LAW|grid=%s|N=%d|delta=%s|y=%s|s=%s|t=%s|Y=%s|V2=%s|A1=%s|C1=%s|D2=%s|f=%s|J0=%s|y2N=%s|float_used=0|json=0' % (
        tag, N, d, y, s, t, dec(L['Y'], 10), dec(L['V2'], 10), dec(L['A1'], 12), dec(L['C1'], 12), dec(L['D2'], 12), dec(L['f'], 8), dec(L['J0'], 8), dec(y*y*N, 8))

def main():
    lines = []
    for N, d, y, s, TS in grid_band():
        for t in TS:
            lines.append(fmt(N, d, y, s, t, 'band'))
    for N, d, y, s, TS in grid_outside():
        for t in TS:
            lines.append(fmt(N, d, y, s, t, 'outside'))
    path = ROOT + 'LAW-PREDICTIONS.hbp'
    data = ('\n'.join(lines) + '\n').encode()
    open(path, 'wb').write(data)
    print('rows', len(lines), 'sha256', hashlib.sha256(data).hexdigest())
    return 0

if __name__ == '__main__':
    sys.exit(main())
