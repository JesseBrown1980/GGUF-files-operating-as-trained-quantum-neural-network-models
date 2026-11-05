#!/usr/bin/env python3
# t4_tw.py -- drives the integer truncated Wigner sampler; reads V^2, the phase coherence and the amplitude moments per time.
# usage: t4_tw.py N delta y samples threads tref_t [dtden] ; t list = 1/4 .. tmax
import sys, subprocess
from fractions import Fraction as Fr
from math import isqrt
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import chebdrv as D
from law import law, dec

EXE = 'C:/tmp/opus55/polariton-recheck-contact-20261105/tw/target/release/tw.exe'

def run_tw(N, delta, y, samples, threads, tref, dtden=64, tmax=Fr(12), seed=20261105, tstep=Fr(1, 4), u=Fr(1)):
    ts = []
    k = tstep
    while k <= tmax:
        ts.append(k)
        k += tstep
    steps = [int(t*dtden) for t in ts]
    idx = min(range(len(ts)), key=lambda i: abs(ts[i]-tref))
    cmd = [EXE, str(N), D.ratstr(delta), D.ratstr(u), D.ratstr(y), str(samples), str(seed), str(dtden), str(idx), str(threads), ','.join(str(s) for s in steps)]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    rows = [D.parse_row(ln.strip()) for ln in r.stdout.splitlines() if ln.startswith('TW|')]
    out = []
    for t, d in zip(ts, rows):
        def g(k):
            return Fr(int(d[k]), 10**12)
        zr, zi = g('mean_zr_e12'), g('mean_zi_e12')
        r2 = g('mean_r2_e12')
        a0, ap, am = g('mean_a0_e12'), g('mean_ap_e12'), g('mean_am_e12')
        # X/N^2 = <|Z|^2> - (<|psi0|^2> + <|psi+|^2>)/N + 1/(2N^2)
        Xn2 = r2 - (a0 + (ap + am)/2)/N + Fr(1, 2*N*N)
        C1 = 2*Xn2*Fr(N, N-1)
        A1 = 2*(zr*zr + zi*zi)
        # A1 here holds A1^2/2: |<A>|^2/N^2 * 2
        V2 = (A1/ (2*C1))*2 if C1 != 0 else None   # A1^2/(2 C1), where A1^2 = 4 |Z|^2
        f = ap + am - Fr(1, N)
        R1 = g('mean_cos_e12')
        R1s = g('mean_sin_e12')
        out.append(dict(t=t, f=f, C1=C1, A1sq=4*(zr*zr + zi*zi), V2=V2, zr=zr, zi=zi, r2=r2, r1=g('mean_r1_e12'),
                        r4=g('mean_r4_e12'), cos=R1, sin=R1s, cos2=g('mean_cos2_e12'), sin2=g('mean_sin2_e12'),
                        z2r=g('mean_z2r_e12'), corr=g('corr_ref_e12'), ch2=g('mean_ch2_e12'), rcos2=g('mean_rcos2_e12'), tref=ts[idx],
                        rz=Fr(int(d['mean_rz_e16']), 10**16), zz=Fr(int(d['mean_zz_e16']), 10**16), coss=g('mean_coss_e12')))
    return out

def main():
    N = int(sys.argv[1]); delta = Fr(sys.argv[2]); y = Fr(sys.argv[3]); samples = int(sys.argv[4]); threads = int(sys.argv[5]); tref = Fr(sys.argv[6])
    dtden = int(sys.argv[7]) if len(sys.argv) > 7 else 64
    tmax = Fr(sys.argv[8]) if len(sys.argv) > 8 else Fr(12)
    rows = run_tw(N, delta, y, samples, threads, tref, dtden=dtden, tmax=tmax)
    print('N=%d delta=%s y=%s samples=%d y2N=%s tref=%s' % (N, delta, y, samples, dec(y*y*N, 5), rows[0]['tref']))
    print('t f_TW C1_TW A1_TW V2_TW R1^2=|<e^itheta>|^2 cos2theta <r>^2/<r2> corr(theta,theta_ref) law_V2 law_Y')
    for r in rows:
        L = law(N, delta, y, r['t'])
        R12 = r['cos']*r['cos'] + r['sin']*r['sin']
        a1 = isqrt(int(r['A1sq']*10**24))
        print('%s %s %s %s %s %s %s %s %s %s %s' % (
            dec(r['t'], 2), dec(r['f'], 4), dec(r['C1'], 5), dec(Fr(a1, 10**12), 5), dec(r['V2'], 4) if r['V2'] is not None else 'None', dec(R12, 4), dec(r['cos2'], 4),
            dec(r['r1']*r['r1']/r['r2'], 4), dec(r['corr'], 4), dec(L['V2'], 4), dec(L['Y'], 4)))
    return 0

if __name__ == '__main__':
    sys.exit(main())
