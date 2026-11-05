#!/usr/bin/env python3
# t5_eval.py -- evaluates the first-correction time functions at given (delta, s, t), exact in the coefficients, fixed point in the exponentials.
import sys, time
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import t5_firstcorr as F
from law import exp_fp, cos_sin_fp, sqrt_fp, fp, mul, fr, ONE as FP_ONE, dec, law

_cache = {}
def results(delta, u=Fr(1)):
    key = (Fr(delta), Fr(u))
    if key not in _cache:
        F.W.g2 = 1 - key[0]*key[0]
        dyn = F.Dyn(F.Ctx(key[0], key[1]))
        _cache[key] = dyn.results()
    return _cache[key]

def evaluate(f, delta, s, t):
    """returns (re, im) Fractions of a time function at numeric (s, t)."""
    delta = Fr(delta); s = Fr(s); t = Fr(t)
    g2 = 1 - delta*delta
    tot_re = Fr(0); tot_im = Fr(0)
    if g2 > 0:
        g = sqrt_fp(g2)
        gf = fr(g)
        z = mul(g, fp(t))
        expo = {}
        for key in f:
            k = key[3]
            if k not in expo:
                expo[k] = fr(exp_fp(z*k)) if k != 0 else Fr(1)
        for (sp, ti, tj, k, k2), w in f.items():
            base = s**sp * t**ti * expo[k]
            tot_re += base*(w.a + w.b*gf)
            tot_im += base*(w.c + w.d*gf)
        return tot_re, tot_im
    if g2 == 0:
        for (sp, ti, tj, k, k2), w in f.items():
            base = s**sp * t**ti
            tot_re += base*w.a
            tot_im += base*w.c
        return tot_re, tot_im
    om = sqrt_fp(-g2)
    of = fr(om)
    z = mul(om, fp(t))
    for (sp, ti, tj, k, k2), w in f.items():
        c, sn = cos_sin_fp(z*k) if k != 0 else (FP_ONE, 0)
        cf, sf = fr(c), fr(sn)
        base = s**sp * t**ti
        # coefficient (a + b i om) + i (c + d i om) = (a - d om) + i (b om + c)
        cr = w.a - w.d*of
        ci = w.b*of + w.c
        tot_re += base*(cr*cf - ci*sf)
        tot_im += base*(cr*sf + ci*cf)
    return tot_re, tot_im

def first_order(delta, y, N, t, u=Fr(1)):
    """law + first correction for A1, C1, V2, D2, f at (N, delta, y, t), s = y sqrt(N) entering as s^2 and s exact where even powers."""
    N = Fr(N); y = Fr(y)
    res = results(delta, u)
    # s appears with fixed parity in each object, so divide out with y: <A> = N y (w0 + w1/N), w's polynomial in s^2
    # evaluate with s -> symbolic: use s^2 = y^2 N exact by evaluating at s = 1 pieces per power
    def ev_even(f):
        # sum over sp of (y^2 N)^(sp/2) * coefficient(s=1), sp even
        tot = Fr(0)
        for sp in set(k[0] for k in f):
            sub = {k: v for k, v in f.items() if k[0] == sp}
            r, _ = evaluate(sub, delta, Fr(1), t)
            assert sp % 2 == 0
            tot += r*(y*y*N)**(sp//2)
        return tot
    def ev_odd_over_s(f):
        tot = Fr(0)
        for sp in set(k[0] for k in f):
            sub = {k: v for k, v in f.items() if k[0] == sp}
            r, _ = evaluate(sub, delta, Fr(1), t)
            assert sp % 2 == 1
            tot += r*(y*y*N)**((sp-1)//2)
        return tot
    w0 = ev_odd_over_s(res['z0'])
    w1 = ev_odd_over_s(res['z1'])
    A1_0 = 2*abs(y)*abs(w0)
    A1_1 = 2*abs(y)*abs(w0 + w1/N)
    C0 = ev_even(res['C1_0'])
    C1v = ev_even(res['C1_1'])
    C1_0 = C0/N
    C1_1 = C0/N + C1v/(N*N)
    n0 = ev_even(res['n_0'])
    n1 = ev_even(res['n_1'])
    B0 = ev_even(res['B_0'])
    B1 = ev_even(res['B_1'])
    return dict(w0=w0, w1=w1, A1_law=A1_0, A1_first=A1_1, C0=C0, C1v=C1v, C1_law=C1_0, C1_first=C1_1,
                n0=n0, n1=n1, f_first=(n0 + n1/N)/N, D2_law=2*abs(B0)/N, D2_first=2*abs(B0 + B1/N)/N,
                V2_first=(A1_1*A1_1)/(2*C1_1) if C1_1 != 0 else None,
                V2_lin=None if C0 == 0 or w0 == 0 else (A1_0*A1_0/(2*C1_0))*(1 + (2*w1/w0 - C1v/C0)/N))

def readme_J1(delta, u, t):
    delta = Fr(delta); u = Fr(u); t = Fr(t)
    g2 = 1 - delta*delta
    if g2 == 0:
        sign = 1 if delta == 1 else -1
        return -(t**2 + (3 - sign*u)*t**4 + Fr(2, 5)*(4 - sign*3*u)*t**6)
    g = sqrt_fp(g2)
    z = mul(g, fp(t))
    ep = exp_fp(z); em = exp_fp(-z)
    sh = fr((ep-em) >> 1)
    ch = fr((ep+em) >> 1)
    sh2 = 2*sh*ch   # sinh 2z
    gf = fr(g)
    gamt = gf*t
    return (-(4 - 3*delta*u)*sh2*sh2/4 + Fr(3, 2)*gamt*(1 + 3*delta**2 - delta*u*(2 + delta**2))*sh2 + delta*(3*u*(1 + delta**2) - delta*(7 + delta**2))*sh*sh)/g2**3

def readme_w1_delta0(t):
    t = Fr(t)
    def ch(k):
        z = fp(k*t)
        return fr((exp_fp(z) + exp_fp(-z)) >> 1)
    def sh(k):
        z = fp(k*t)
        return fr((exp_fp(z) - exp_fp(-z)) >> 1)
    return -t*sh(1) + Fr(65, 12)*ch(1) - Fr(11, 3)*ch(2) + Fr(5, 4)*ch(3) - 3

if __name__ == '__main__':
    # check 1: J1 against the README form at several (delta, u), s = 0 part of n_1 / 2
    bad = 0
    print('CHECK_J1|machine n_1(s^0)/2 against the README J1 form, at (delta,u,t):')
    for (d, u) in ((Fr(0), Fr(1)), (Fr(1, 2), Fr(1)), (Fr(-1, 2), Fr(1)), (Fr(3, 4), Fr(1)), (Fr(-3, 4), Fr(1)), (Fr(1, 2), Fr(1, 2)), (Fr(0), Fr(1, 2)), (Fr(1), Fr(1)), (Fr(-1), Fr(1)), (Fr(1), Fr(1, 2)), (Fr(-1), Fr(1, 2))):
        res = results(d, u)
        sub = {k: v for k, v in res['n_1'].items() if k[0] == 0}
        for t in (Fr(1, 2), Fr(1), Fr(3)):
            r, im = evaluate(sub, d, 0 + Fr(1), t)
            j1 = r/2
            ref = readme_J1(d, u, t)
            off = abs(j1 - ref)
            ok = off < Fr(1, 10**40)
            bad += 0 if ok else 1
            print('  delta=%s u=%s t=%s machine=%s README=%s off_lt_1e-40=%s' % (d, u, t, dec(j1, 12), dec(ref, 12), ok))
    print('CHECK_J1|bad=%d|json=0' % bad)
    # check 2: w1 at delta = 0, s^1 part of z1
    res = results(Fr(0))
    sub = {k: v for k, v in res['z1'].items() if k[0] == 1}
    bad = 0
    for t in (Fr(1, 2), Fr(1), Fr(2), Fr(3)):
        r, im = evaluate(sub, 0, 1, t)
        ref = readme_w1_delta0(t)
        ok = abs(r-ref) < Fr(1, 10**40)
        bad += 0 if ok else 1
        print('  w1 t=%s machine=%s README=%s ok=%s' % (t, dec(r, 12), dec(ref, 12), ok))
    print('CHECK_W1|bad=%d|json=0' % bad)
    # check 3: energy conservation exact at each delta
    for d, u in ((Fr(0), Fr(1)), (Fr(1, 2), Fr(1)), (Fr(-1, 2), Fr(1)), (Fr(3, 4), Fr(1)), (Fr(-3, 4), Fr(1)), (Fr(1), Fr(1)), (Fr(-1), Fr(1)), (Fr(5, 4), Fr(1)), (Fr(-5, 4), Fr(1)), (Fr(1, 2), Fr(1, 3))):
        res = results(d, u)
        print('CHECK_ENERGY|delta=%s|u=%s|nonzero_terms=%d|json=0' % (d, u, len(res['energy_first_order'])))
