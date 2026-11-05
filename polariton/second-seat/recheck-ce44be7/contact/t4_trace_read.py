#!/usr/bin/env python3
# t4_trace_read.py -- reads exact traces: V^2, law, f, <A^2>/<A^dag A>, and the first depletion peak. Exact rationals, no float.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import chebdrv as D
from law import law, dec, parts

ROOT = 'C:/tmp/opus55/polariton-recheck-contact-20261105/out/'

def load(N):
    rows = {}
    for ln in open(ROOT + 'TRACE-N%d.hbp' % N):
        ln = ln.strip()
        if not ln.startswith('ROW|'):
            continue
        d = D.parse_row(ln)
        key = (Fr(d['delta']), Fr(d['y']))
        rows.setdefault(key, []).append(d)
    for k in rows:
        rows[k].sort(key=lambda d: Fr(d['t']))
    return rows

def g(d, k):
    return Fr(int(d[k]), 10**18)

def Rician(Y):
    """(pi/4) Y exp(-Y) [I0(Y/2) + I1(Y/2)]^2 with exact-rational series at fixed precision; no float. Y >= 0."""
    Y = Fr(Y)
    SC = 10**40
    x = Y/2
    def trunc(v):
        return Fr((v.numerator*SC)//v.denominator, SC)
    I0 = Fr(0); I1 = Fr(0)
    term0 = Fr(1); term1 = x/2
    for k in range(0, 200):
        I0 += term0
        I1 += term1
        term0 = trunc(term0*(x/2)**2/((k+1)*(k+1)))
        term1 = trunc(term1*(x/2)**2/((k+1)*(k+2)))
        if term0 == 0 and term1 == 0:
            break
    # exp(-Y)
    e = Fr(1); t = Fr(1)
    for k in range(1, 400):
        t = trunc(t*(-Y)/k)
        e += t
        if t == 0:
            break
    pi = Fr(314159265358979323846264338327950288419716939937510, 10**50)
    return pi/4*Y*e*(I0+I1)**2

def first_peak(ds):
    # first local maximum of the read f, on the trace grid
    for i in range(1, len(ds)-1):
        if g(ds[i], 'f_e18') >= g(ds[i-1], 'f_e18') and g(ds[i], 'f_e18') >= g(ds[i+1], 'f_e18'):
            return i
    return None

def main():
    N = int(sys.argv[1])
    rows = load(N)
    print('N=%d chains=%d' % (N, len(rows)))
    for key in sorted(rows):
        delta, y = key
        ds = rows[key]
        ip = first_peak(ds)
        print()
        print('delta=%s y=%s y2N=%s first_f_peak_t=%s f_peak=%s' % (delta, y, dec(y*y*N, 4), ds[ip]['t'] if ip is not None else None, dec(g(ds[ip], 'f_e18'), 4) if ip is not None else None))
        print(' t f_read Y law V2_read V2/law Rician(Y) A2/AdA D2 A1/lawA1 C1/lawC1')
        for i, d in enumerate(ds):
            t = Fr(d['t'])
            L = law(N, delta, y, t)
            V2 = g(d, 'V2_e18')
            am2 = g(d, 'Am2_re_e18')
            nrm1 = g(d, 'Am1_nrm_e18')
            rat = V2/L['V2'] if L['V2'] not in (None, 0) else None
            ri = Rician(L['Y']) if (L['Y'] is not None and L['Y'] >= 0) else None
            mark = '*' if i == ip else ' '
            a1r = g(d, 'A1_e18')/L['A1'] if L['A1'] != 0 else None
            c1r = g(d, 'C1_e18')/L['C1'] if L['C1'] != 0 else None
            print('%s%s %s %s %s %s %s %s %s %s %s %s' % (
                mark, dec(t, 2), dec(g(d, 'f_e18'), 4), dec(L['Y'], 4), dec(L['V2'], 4), dec(V2, 4), dec(rat, 3) if rat is not None else 'None',
                dec(ri, 4) if ri is not None else 'None', dec(am2/nrm1, 4) if nrm1 != 0 else 'None', dec(g(d, 'D2_e18'), 4),
                dec(a1r, 3) if a1r is not None else 'None', dec(c1r, 3) if c1r is not None else 'None'))
    return 0

if __name__ == '__main__':
    sys.exit(main())
