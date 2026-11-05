#!/usr/bin/env python3
# t4_cs.py -- tests the explanation of "V^2 holds past its parts" by trajectories, in integers.
# Classical-field picture: z(t) = rho(t; zeta) e^(i theta), seed zeta = unstable-mode amplitude at t=0, complex Gaussian with mean m, variance v.
# For small Y = m^2/v, with theta = arg zeta frozen:
#     V^2/Y = <rho |zeta|>^2 / (v <rho^2>)  [a Cauchy-Schwarz cosine^2 in the y=0 ensemble]; equals 1 when rho is proportional to |zeta|, pi/4 when rho is constant.
# Reads, at each t, at y=0 (transfer) and at small y (direct): V^2, V^2/Y, the cosine^2, phase coherence R1^2, cos(theta - arg zeta).
# usage: t4_cs.py N delta s_num/s_den samples threads tmax
import sys
from fractions import Fraction as Fr
from math import isqrt
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import t4_tw as W
from law import law, dec
import t4_trace_read as TR

def rational_sqrt_den(N):
    # y = s/root with root integer nearest sqrt(N); y^2 N reported exactly
    r = isqrt(N)
    return r if r*r == N else r+1

def main():
    N = int(sys.argv[1]); delta = Fr(sys.argv[2]); s = Fr(sys.argv[3]); samples = int(sys.argv[4]); threads = int(sys.argv[5]); tmax = Fr(sys.argv[6])
    y = s/rational_sqrt_den(N)
    rows = W.run_tw(N, delta, y, samples, threads, Fr(2), dtden=64, tmax=tmax, tstep=Fr(1, 4))
    rows0 = W.run_tw(N, delta, Fr(0), max(samples//4, 100000), threads, Fr(2), dtden=64, tmax=tmax, tstep=Fr(1, 4), seed=20261106)
    print('N=%d delta=%s s=%s y=%s y2N=%s samples=%d' % (N, delta, s, y, dec(y*y*N, 6), samples))
    print('t f_TW Y law V2_TW V2/law V2/Y cos2_transfer R1^2 Rician(Y) cos(th-arg_zeta) A1/lawA1 C1/lawC1 | y=0: <r>^2/<r2>')
    for r, r0 in zip(rows, rows0):
        L = law(N, delta, y, r['t'])
        cs = (r0['rz']*r0['rz'])/(r0['zz']*r0['r2']) if r0['zz'] != 0 else None
        R12 = r['cos']*r['cos'] + r['sin']*r['sin']
        ri = TR.Rician(L['Y']) if L['Y'] >= 0 else None
        a1 = isqrt(int(r['A1sq']*10**24))
        A1 = Fr(a1, 10**12)
        print('%s %s %s %s %s %s %s %s %s %s %s %s %s | %s' % (
            dec(r['t'], 2), dec(r['f'], 4), dec(L['Y'], 4), dec(L['V2'], 4), dec(r['V2'], 4), dec(r['V2']/L['V2'], 3), dec(r['V2']/L['Y'], 3),
            dec(cs, 3) if cs is not None else 'None', dec(R12, 4), dec(ri, 4) if ri is not None else 'None', dec(r['coss'], 3),
            dec(A1/L['A1'], 3) if L['A1'] else 'None', dec(r['C1']/L['C1'], 3) if L['C1'] else 'None', dec(r0['r1']*r0['r1']/r0['r2'], 3)))
    return 0

if __name__ == '__main__':
    sys.exit(main())
