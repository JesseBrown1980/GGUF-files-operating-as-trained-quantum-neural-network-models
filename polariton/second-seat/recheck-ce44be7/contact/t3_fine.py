#!/usr/bin/env python3
# t3_fine.py -- fine scans outside the band at N=729 (and 243): where the pole of V^2 falls (delta>1), and how the period pulls (delta<-1).
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import chebdrv as D
import t5_eval as E
from law import law, dec, parts

ROOT = 'C:/tmp/opus55/polariton-recheck-contact-20261105/out/'

def g(d, k):
    return Fr(int(d[k]), 10**18)

def scan(N, delta, s, root, t0, t1, den, lines):
    y = s/root
    ts = [Fr(k, den) for k in range(int(t0*den), int(t1*den)+1)]
    rows = D.run_chain(N, N, 1, delta, y, ts, threads=1, moments=0)
    prev = None
    res = []
    for row in rows:
        d = D.parse_row(row)
        t = Fr(d['t'])
        L = law(N, delta, y, t)
        fo = E.first_order(delta, y, N, t)
        rec = dict(t=t, V2=g(d, 'V2_e18'), C1=g(d, 'C1_e18'), A=g(d, 'A_e18'), A1=g(d, 'A1_e18'), f=g(d, 'f_e18'), L=L, fo=fo)
        res.append(rec)
        lines.append('FINE|N=%d|delta=%s|s=%s|y=%s|t=%s|Y=%s|V2_law=%s|V2_read=%s|C1_law=%s|C1_first=%s|C1_read=%s|A1_law=%s|A1_first=%s|A1_read=%s|A_sign=%s|f=%s|json=0' % (
            N, delta, s, y, t, dec(L['Y'], 5) if L['Y'] is not None else 'None', dec(L['V2'], 5) if L['V2'] is not None else 'None', dec(rec['V2'], 5), dec(L['C1'], 9), dec(fo['C1_first'], 9), dec(rec['C1'], 9),
            dec(L['A1'], 7), dec(fo['A1_first'], 7), dec(rec['A1'], 7), '+' if rec['A'] > 0 else '-', dec(rec['f'], 5)))
    return res

def zero_cross(res, key):
    out = []
    for a, b in zip(res, res[1:]):
        if (a[key] < 0) != (b[key] < 0):
            # linear interpolation in exact rationals
            tz = a['t'] + (b['t']-a['t'])*(-a[key])/(b[key]-a[key])
            out.append(tz)
    return out

def law_cross(res):
    out = []
    for a, b in zip(res, res[1:]):
        if (a['L']['C1'] < 0) != (b['L']['C1'] < 0):
            tz = a['t'] + (b['t']-a['t'])*(-a['L']['C1'])/(b['L']['C1']-a['L']['C1'])
            out.append(tz)
    return out

def first_cross(res):
    out = []
    for a, b in zip(res, res[1:]):
        if (a['fo']['C1_first'] < 0) != (b['fo']['C1_first'] < 0):
            tz = a['t'] + (b['t']-a['t'])*(-a['fo']['C1_first'])/(b['fo']['C1_first']-a['fo']['C1_first'])
            out.append(tz)
    return out

def amin(res):
    # first local minimum of A1 after its first maximum
    i = 1
    while i < len(res)-1 and not (res[i]['A1'] >= res[i-1]['A1'] and res[i]['A1'] >= res[i+1]['A1']):
        i += 1
    imax = i
    while i < len(res)-1 and not (res[i]['A1'] <= res[i-1]['A1'] and res[i]['A1'] <= res[i+1]['A1']):
        i += 1
    return res[imax], res[i]

def main():
    lines = []
    print('POLE delta>1: where C1 crosses 0 (V^2 pole), read, law and law+first correction', flush=True)
    for (N, root) in ((729, 27),):
        for delta, s_, t0, t1 in ((Fr(5, 4), Fr(1, 2), Fr(5, 2), Fr(7, 2)), (Fr(5, 4), Fr(1), Fr(3, 2), Fr(5, 2)), (Fr(2), Fr(1), Fr(1, 2), Fr(3, 2)), (Fr(2), Fr(2), Fr(5, 2), Fr(7, 2))):
            res = scan(N, delta, s_, root, t0, t1, 16, lines)
            print('N=%d delta=%s s=%s C1=0 at read %s law %s first %s' % (N, delta, s_, ' '.join(dec(x, 3) for x in zero_cross(res, 'C1')), ' '.join(dec(x, 3) for x in law_cross(res)), ' '.join(dec(x, 3) for x in first_cross(res))), flush=True)
    print(flush=True)
    print('PERIOD delta<-1: first maximum and first minimum of A1 against the law (pi/w, 2 pi/w), N=729', flush=True)
    pi = Fr(314159265358979323846, 10**20)
    from law import sqrt_fp, fr
    for delta in (Fr(-5, 4), Fr(-2)):
        w2 = delta*delta - 1
        w = fr(sqrt_fp(w2))
        for s_ in (Fr(1, 4), Fr(1), Fr(4)):
            tmax = Fr(9) if delta == Fr(-5, 4) else Fr(5)
            res = scan(729, delta, s_, 27, Fr(1, 4), tmax, 8, lines)
            hi, lo = amin(res)
            print('N=729 delta=%s s=%s t(max A1)=%s law %s; t(min A1)=%s law %s; A1 at min=%s; f at max=%s; V2 at min=%s' % (delta, s_, dec(hi['t'], 3), dec(pi/w, 3), dec(lo['t'], 3), dec(2*pi/w, 3), dec(lo['A1'], 5), dec(hi['f'], 4), dec(lo['V2'], 4)), flush=True)
    open(ROOT + 'FINE-outside.hbp', 'w', newline=chr(10)).write(chr(10).join(lines) + chr(10))
    print('rows', len(lines), flush=True)
    return 0

if __name__ == '__main__':
    sys.exit(main())
