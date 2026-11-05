#!/usr/bin/env python3
# law.py -- the contact quench law, evaluated in big-integer fixed point (no float). Written from my own derivation (F1).
from fractions import Fraction as Fr
from math import isqrt

P = 320
ONE = 1 << P

def fp(x):
    x = Fr(x)
    return (x.numerator << P)//x.denominator

def mul(a, b): return (a*b) >> P

def exp_fp(z):
    # z fixed point. halve to keep the series short.
    k = 0
    zz = z
    while abs(zz) > (ONE >> 4):
        zz >>= 1 if zz >= 0 else 0
        if zz < 0:
            zz = -((-zz) >> 1)
        k += 1
    term = ONE; s = ONE; n = 1
    while True:
        term = mul(term, zz)//n
        if term == 0: break
        s += term
        n += 1
        if n > 400: break
    for _ in range(k):
        s = mul(s, s)
    return s

def cos_sin_fp(z):
    # reduce by halving, then double-angle
    k = 0
    zz = z
    while abs(zz) > (ONE >> 5):
        zz = zz >> 1 if zz >= 0 else -((-zz) >> 1)
        k += 1
    z2 = mul(zz, zz)
    c = ONE; s = zz
    tc = ONE; ts = zz
    n = 1
    while True:
        tc = -mul(tc, z2)//((2*n-1)*(2*n))
        ts = -mul(ts, z2)//((2*n)*(2*n+1))
        if tc == 0 and ts == 0: break
        c += tc; s += ts
        n += 1
        if n > 200: break
    for _ in range(k):
        c, s = mul(c, c) - mul(s, s), 2*mul(s, c)
    return c, s

def sqrt_fp(x):
    # x Fraction >= 0
    x = Fr(x)
    return isqrt((x.numerator << (2*P))//x.denominator)

def fr(v):
    return Fr(v, ONE)

def parts(delta, t):
    """Returns G = (cosh gt - 1)/(1+delta), S1 = sinh^2(gt)/(1+delta), J0 = sinh^2/gamma^2, T1 = tanh^2(gt/2)/(1+delta)
    as Fractions, all continued to the edges and outside the band."""
    delta = Fr(delta); t = Fr(t)
    g2 = 1 - delta*delta
    if g2 > 0:
        g = sqrt_fp(g2)
        z = mul(g, fp(t))
        ep = exp_fp(z); em = exp_fp(-z)
        ch = (ep + em) >> 1
        sh = (ep - em) >> 1
        chm1 = ch - ONE
        S = mul(sh, sh)
        G = fr(chm1)/(1 + delta)
        S1 = fr(S)/(1 + delta)
        J0 = fr(S)/g2
        # tanh^2(z/2) = (ch-1)/(ch+1)
        T1 = (fr(chm1)/fr(ch + ONE))/(1 + delta)
        return G, S1, J0, T1
    if g2 == 0:
        if delta == -1:
            # (ch-1)/(1+d) -> (1-d) t^2/2 = t^2; sinh^2/(1+d) -> (1-d) t^2 = 2 t^2; tanh^2/(1+d) -> (1-d) t^2/4 = t^2/2
            return t*t, 2*t*t, t*t, t*t/2
        else:
            return Fr(0), Fr(0), t*t, Fr(0)
    w2 = -g2
    w = sqrt_fp(w2)
    z = mul(w, fp(t))
    c, s = cos_sin_fp(z)
    G = fr(c - ONE)/(1 + delta)
    S1 = -fr(mul(s, s))/(1 + delta)
    J0 = fr(mul(s, s))/w2
    # tanh^2(i z/2) = -tan^2(z/2) = -(1-c)/(1+c)
    T1 = (-(fr(ONE - c)/fr(ONE + c)))/(1 + delta) if c != -ONE else None
    return G, S1, J0, T1

def law(N, delta, y, t):
    N = Fr(N); y = Fr(y)
    G, S1, J0, T1 = parts(delta, t)
    A1 = 4*abs(y)*abs(G)
    C1 = 4*S1/N + A1*A1/2
    Y = 2*N*y*y*T1 if T1 is not None else None
    V2 = (Y/(1 + Y)) if (Y is not None and 1 + Y != 0) else None
    D2 = 2*y*y*(G*G + J0)
    ncoh = 2*N*y*y*(G*G + J0)
    f = (2*J0 + ncoh)/N
    Astar = -4*y*G*N/2  # <A> predicted, with sign: <A> = -2 N y G, A1 = 2|<A>|/N
    return dict(A1=A1, C1=C1, Y=Y, V2=V2, D2=D2, f=f, J0=J0, ncoh=ncoh, A=-2*N*y*G)

def dec(x, digits=12):
    # exact rational to decimal text with integer arithmetic; no float
    if x is None:
        return 'None'
    x = Fr(x)
    neg = x < 0
    x = abs(x)
    scaled = (x.numerator*10**digits + x.denominator//2)//x.denominator
    ip = scaled//10**digits
    fp_ = scaled % 10**digits
    return ('-' if neg else '') + str(ip) + '.' + str(fp_).zfill(digits)

if __name__ == '__main__':
    # checks at known points
    print('cosh1-1 ~ 0.543080634815', dec(parts(0, 1)[0]))
    print('N=729 delta=0 y=1/27 t=1 V2', dec(law(729, 0, Fr(1, 27), 1)['V2']), ' README 0.29928')
    print('N=729 delta=1/2 y=4/27 t=3 V2', dec(law(729, Fr(1, 2), Fr(4, 27), 3)['V2']), ' README 0.94059')
    print('delta=-1 limit vs -0.999999 at t=2 y=1/27 N=729: V2', dec(law(729, -1, Fr(1, 27), 2)['V2']), dec(law(729, Fr(-999999, 1000000), Fr(1, 27), 2)['V2']))
    print('delta=-1 limit vs -0.999999 at t=2: A1', dec(law(729, -1, Fr(1, 27), 2)['A1']), dec(law(729, Fr(-999999, 1000000), Fr(1, 27), 2)['A1']))
    print('delta=-1 limit vs -0.999999 at t=2: C1', dec(law(729, -1, Fr(1, 27), 2)['C1']), dec(law(729, Fr(-999999, 1000000), Fr(1, 27), 2)['C1']))
    print('delta=+1 limit vs 0.999999 at t=2: V2', dec(law(729, 1, Fr(1, 27), 2)['V2']), dec(law(729, Fr(999999, 1000000), Fr(1, 27), 2)['V2']))
    print('delta=+1.000001 vs +0.999999 at t=2: V2', dec(law(729, Fr(1000001, 1000000), Fr(1, 27), 2)['V2']), dec(law(729, Fr(999999, 1000000), Fr(1, 27), 2)['V2']))
    print('D2 continuity delta=1:', dec(law(729, 1, Fr(1, 27), 2)['D2']), dec(law(729, Fr(999999, 1000000), Fr(1, 27), 2)['D2']))
    print('outside delta=5/4 y=1/27 t=2: V2,Y,C1', dec(law(729, Fr(5, 4), Fr(1, 27), 2)['V2']), dec(law(729, Fr(5, 4), Fr(1, 27), 2)['Y']), dec(law(729, Fr(5, 4), Fr(1, 27), 2)['C1']))
