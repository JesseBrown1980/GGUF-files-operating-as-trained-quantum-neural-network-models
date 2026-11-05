# Fixed-P chains of the three-mode model. n+ = j + P, n- = j, n0 = N - 2j - P, tridiagonal in j.
# Pivot counts in Python integers at K fractional bits, or in exact rationals. Own code; shares nothing with the engine or the route.
from fractions import Fraction as F
from math import isqrt

K = 160
ONE = 1 << K


def q(r, bits=K):
    r = F(r)
    return (r.numerator << bits) // r.denominator


def chain(N, u, x, P, bits=K):
    """Diagonal and squared off-diagonal at 2^bits, in units JN = 1."""
    u, x = F(u), F(x)
    top = (N - P) // 2
    d, o2 = [], []
    un, ud, xn, xd = u.numerator, u.denominator, x.numerator, x.denominator
    den = ud * xd * N
    for j in range(top + 1):
        n0 = N - 2 * j - P
        s = 2 * j + P
        num = xn * s * ud * N + un * (n0 * s + (j + P) * j) * xd
        d.append((num << bits) // den)
        if j < top:
            o2.append((((j + P + 1) * (j + 1) * n0 * (n0 - 1)) << bits) // (N * N))
    return d, o2


def count_below(d, o2, lam, bits=K):
    c = 0
    p = d[0] - lam
    if p == 0:
        p = -1
    if p < 0:
        c += 1
    for k in range(1, len(d)):
        p = d[k] - lam - (o2[k - 1] << bits) // p
        if p == 0:
            p = -1
        if p < 0:
            c += 1
    return c


def has_below(d, o2, lam, bits=K):
    """True when at least one level lies below lam, stopping at the first negative pivot."""
    p = d[0] - lam
    if p <= 0:
        return True
    for k in range(1, len(d)):
        p = d[k] - lam - (o2[k - 1] << bits) // p
        if p <= 0:
            return True
    return False


def ground_level(d, o2, lo=None, hi=None, stop=None, bits=K):
    stop = (1 << (bits - 70)) if stop is None else stop
    if hi is None:
        hi = min(d) + 1
    if lo is None:
        r = max([isqrt(v << bits) for v in o2] + [0])
        lo = min(d) - 2 * r - 2
    while hi - lo > stop:
        mid = (lo + hi) >> 1
        if has_below(d, o2, mid, bits):
            hi = mid
        else:
            lo = mid
    return (lo + hi) >> 1


def argmin_P(N, u, x, stop_bits=70, bits=K):
    """Lowest level over all P >= 0, with every P asked once at the running best, and refined when it lies below."""
    stop = 1 << (bits - stop_bits)
    d, o2 = chain(N, u, x, 0, bits)
    best = ground_level(d, o2, stop=stop, bits=bits)
    e0 = best
    who = 0
    # The plane wave first: its level is its diagonal, and it spares a refinement at each P on the plane-wave side.
    d, o2 = chain(N, u, x, N, bits)
    if d[0] < best - stop:
        best = d[0]
        who = N
    for P in range(1, N):
        d, o2 = chain(N, u, x, P, bits)
        if has_below(d, o2, best - stop, bits):
            best = ground_level(d, o2, hi=best, stop=stop, bits=bits)
            who = P
    return who, best, e0


def rat_chain(N, u, x, P):
    u, x = F(u), F(x)
    top = (N - P) // 2
    d, o2 = [], []
    for j in range(top + 1):
        n0 = N - 2 * j - P
        s = 2 * j + P
        d.append(x * s + u * F(n0 * s + (j + P) * j, N))
        if j < top:
            o2.append(F((j + P + 1) * (j + 1) * n0 * (n0 - 1), N * N))
    return d, o2


def rat_has_below(d, o2, lam):
    p = d[0] - lam
    if p <= 0:
        return True
    for k in range(1, len(d)):
        p = d[k] - lam - o2[k - 1] / p
        if p <= 0:
            return True
    return False


def dec(v, digits=9):
    f = F(v)
    sign = "-" if f < 0 else ""
    f = abs(f)
    scaled = (f.numerator * 10 ** digits) // f.denominator
    return "%s%d.%0*d" % (sign, scaled // 10 ** digits, digits, scaled % 10 ** digits)


def fx(v, digits=9, bits=K):
    return dec(F(v, 1 << bits), digits)
