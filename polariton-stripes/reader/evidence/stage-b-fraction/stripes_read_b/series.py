"""Closed forms of the linear law and the exact small-y series, bracketed in rationals.

C = cosh(gamma t) and S = sinh(gamma t)/gamma are series in gamma^2 t^2 = (1 - delta^2) t^2 with rational terms; each is
bracketed by its partial sum and a geometric bound on the tail. Every closed form here is a polynomial or ratio of
polynomials in C and S, evaluated in outward-rounded intervals. The y-series is the port of closed_forms.py series():
exact Taylor coefficients in t, 90 terms (rule EB), with a majorant bound on the truncation."""

from fractions import Fraction

from . import frozen as frozen_mod
from .exact import Decimal, Iv, div, fr, ipow, isqrt_iv, parse_rat

BITS = 256


def _tail_ok(term, ratio, bits):
    return ratio < Fraction(1, 2) and term < fr(1, ipow(2, bits + 8))


def cosh_C(delta, t, bits=BITS):
    """C = cosh(gamma t), gamma^2 = 1 - delta^2: [partial sum, partial sum + tail bound]."""
    x = (1 - fr(delta) * fr(delta)) * fr(t) * fr(t)
    if x < 0:
        raise ValueError("gamma^2 t^2 < 0")
    s, term, k = Fraction(0), Fraction(1), 0
    while True:
        s += term
        k += 1
        term = div(term * x, (2 * k - 1) * (2 * k))
        ratio = div(x, (2 * k + 1) * (2 * k + 2))
        if _tail_ok(term, ratio, bits):
            return Iv(s, s + div(term, 1 - ratio)).r(bits + 32)


def sinh_S(delta, t, bits=BITS):
    """S = sinh(gamma t)/gamma = t sum (gamma^2 t^2)^k/(2k+1)!."""
    t = fr(t)
    x = (1 - fr(delta) * fr(delta)) * t * t
    s, term, k = Fraction(0), t, 0
    while True:
        s += term
        k += 1
        term = div(term * x, (2 * k) * (2 * k + 1))
        ratio = div(x, (2 * k + 2) * (2 * k + 3))
        if _tail_ok(term, ratio, bits):
            return Iv(s, s + div(term, 1 - ratio)).r(bits + 32)


def sinh_iv(delta, t, bits=BITS):
    """sinh(gamma t) = gamma S, with gamma bracketed by an integer square root."""
    return sinh_S(delta, t, bits) * isqrt_iv(1 - fr(delta) * fr(delta), bits)


class Law:
    """The linear (Bogoliubov) law at (delta, t) for sigma = N y^2 = s^2 (LINEAR, closed_forms.law)."""

    def __init__(self, delta, sigma, t, bits=BITS):
        d = fr(delta)
        self.delta, self.sigma, self.t = d, fr(sigma), fr(t)
        g2 = 1 - d * d
        C = cosh_C(d, t, bits)
        S = sinh_S(d, t, bits)
        self.C, self.S = C, S
        gr = (C - 1) * div(d - 1, g2)
        gi = S
        self.g2 = gi.sq() + gr.sq()
        S2 = S.sq()
        self.u2 = C.sq() + S2 * (d * d)
        self.v2 = S2
        self.nf = (self.u2 + self.v2) * Fraction(1, 2)
        self.m2 = S2.sq() * (d * d) + C.sq() * S2
        re_g2_conj_m = (gr.sq() - gi.sq()) * S2 * (-d) - gr * gi * C * S * 2
        sg = self.sigma
        self.s2 = self.g2 * sg
        self.var = self.nf.sq() + self.m2 + self.s2 * self.nf * 2 + re_g2_conj_m * (2 * sg)
        self.EB = self.s2
        self.EB2 = self.var + self.s2.sq()
        self.var0 = self.nf.sq() + self.m2

    def nstar(self):
        """n*_lin = Var/|s|^4; None (infinite) at s = 0."""
        if self.sigma == 0:
            return None
        return self.var * self.s2.sq().inv()

    def rho(self):
        """rho = |E B|^2 / E|B|^2 = 1/(1 + n*)."""
        return self.s2.sq() * self.EB2.inv()

    def Z(self, n):
        """E[Z_n] = 1 + (n - 1) rho (rule E12 identity)."""
        return self.rho() * (n - 1) + 1

    def f_lin(self, n_modes):
        """Linear-law f = (2|v|^2 + 2|s|^2)/N."""
        return (self.v2 * 2 + self.s2 * 2) * fr(1, n_modes)


def g2_abs(delta, t, bits=BITS):
    return Law(delta, 0, t, bits).g2


def d2_law(delta, y, t, bits=BITS):
    """D2_law = 2 y^2 |g|^2."""
    return g2_abs(delta, t, bits) * (2 * fr(y) * fr(y))


def D_classical(delta, t, y=0, bits=BITS):
    """D(t) = D2/(2 y^2 t^2) - 1 of the classical trajectory to y^4 (Q04): (b2 + y^2 b4)/t^2 - 1;
    |g|^2/t^2 - 1 at y=0."""
    t = fr(t)
    if fr(y) == 0:
        return g2_abs(delta, t, bits) * fr(1, t * t) - 1
    b2, b4 = b2b4_iv(delta, t)
    return (b2 + b4 * (fr(y) * fr(y))) * fr(1, t * t) - 1


def d2_coefficient(delta):
    """The t^2 coefficient of D(t) = |g|^2/t^2 - 1, exactly: (1 - delta^2)/3 + (1 - delta)^2/4."""
    d = fr(delta)
    return div(1 - d * d, 3) + div((1 - d) * (1 - d), 4)


def kappa_q(delta, t, n, bits=BITS):
    """kappa_q = w10/(N w0) (LINEAR; final_numbers.py kq), c(k) = cosh(k gamma t), gs(1) = gamma t sinh(gamma t)."""
    d = fr(delta)
    t = fr(t)
    C = cosh_C(d, t, bits)
    S = sinh_S(d, t, bits)
    g2 = 1 - d * d
    c1 = C
    c2 = C.sq() * 2 - 1
    c3 = C * C.sq() * 4 - C * 3
    gs1 = S * (g2 * t)
    D3 = (1 + d) * (1 + d) * (1 + d) * (1 - d) * (1 - d)
    w0 = (C - 1) * div(-2, 1 + d)
    w10 = (c1 * (fr(65, 12) - fr(85, 6) * d + 12 * d * d - 4 * d * d * d)
           + c3 * (fr(5, 4) - div(d, 2))
           + c2 * ((d - fr(11, 3)) * (1 - d))
           + (4 * d - 3) * (1 - d) * (1 - d)
           + gs1 * (2 * d * d * d - 4 * d * d - 1)) * div(1, D3)
    return w10 * (w0 * n).inv()


# ---------------------------------------------------------------------------------------------------------------------
# The exact y-series (YSERIES): a = y a1 + y^3 a3, psi0 = 1 + y^2 z2; b2 = |a1|^2, b4 = 2 Re(conj a1 a3).


def series(delta, u, K):
    """Taylor coefficients (exact rationals) of a1 = p + iq, z2 = r + iw, a3 = P + iQ: a port of closed_forms.series."""
    d = fr(delta)
    u = fr(u)
    z = Fraction(0)
    p = [z] * (K + 1)
    q = [z] * (K + 1)
    r = [z] * (K + 1)
    w = [z] * (K + 1)
    P = [z] * (K + 1)
    Q = [z] * (K + 1)

    def conv(a, b, k):
        return sum(a[i] * b[k - i] for i in range(k + 1))

    for k in range(K):
        p[k + 1] = div((d - 1) * q[k], k + 1)
        q[k + 1] = div((1 if k == 0 else 0) - (d + 1) * p[k], k + 1)
    for k in range(K):
        pp, qq, pq = conv(p, p, k), conv(q, q, k), conv(p, q, k)
        X = 2 * u * (pp + qq) + 2 * (pp - qq) - 2 * p[k]
        Y = 4 * pq - 2 * q[k]
        r[k + 1] = div(Y, k + 1)
        w[k + 1] = div(-X, k + 1)
    amp = [2 * r[k] + conv(p, p, k) + conv(q, q, k) for k in range(K + 1)]
    for k in range(K):
        Fr = u * conv(amp, p, k) + 2 * (conv(r, p, k) + conv(w, q, k)) - r[k]
        Fi = u * conv(amp, q, k) + 2 * (conv(w, p, k) - conv(r, q, k)) - w[k]
        P[k + 1] = div((d - 1) * Q[k] + Fi, k + 1)
        Q[k + 1] = div(-(d + 1) * P[k] - Fr, k + 1)
    return p, q, r, w, P, Q


def ev(c, t):
    t = fr(t)
    s = Fraction(0)
    tk = Fraction(1)
    for ck in c:
        s += ck * tk
        tk *= t
    return s


_SERIES_CACHE = {}


def _series_cached(delta, u, K):
    key = (fr(delta), fr(u), K)
    if key not in _SERIES_CACHE:
        _SERIES_CACHE[key] = series(delta, u, K)
    return _SERIES_CACHE[key]


def b2b4(delta, t, K=90, u=1):
    """b2 = |a1|^2 and b4 = 2 Re(conj a1 a3) of the K-term series, exact rationals (rule EB: K = 90)."""
    p, q, r, w, P, Q = _series_cached(delta, u, K)
    pv, qv, Pv, Qv = ev(p, t), ev(q, t), ev(P, t), ev(Q, t)
    return pv * pv + qv * qv, 2 * (pv * Pv + qv * Qv)


def series_remainder(delta, t, K=90, u=1):
    """Bounds (T1, T3) on |p - p_K|, |q - q_K| and |P - P_K|, |Q - Q_K| at t >= 0, from the majorants
    |p_k|, |q_k| <= A mu^k/k!, |r_k|, |w_k| <= R (2mu)^k/k!, |P_k|, |Q_k| <= Pi (3mu)^k/k!, mu = 1 + |delta|."""
    d, u, t = fr(delta), fr(u), fr(t)
    mu = 1 + abs(d)
    A = div(1, mu)
    X = (4 * abs(u) + 4) * A * A + 2 * A
    Y = 4 * A * A + 2 * A
    R = div(max(X, Y), 2 * mu)
    Am = 2 * R + 2 * A * A
    Phi = abs(u) * Am * A + 4 * R * A + R
    Pi = div(Phi, 2 * mu)

    def tail(c, m):
        x = m * t
        if x >= K + 2:
            raise ValueError("series_remainder: K too small for t")
        term = c
        for k in range(1, K + 2):
            term = div(term * x, k)
        return div(term, 1 - div(x, K + 2))

    return tail(A, mu), tail(Pi, 3 * mu)


def b2b4_iv(delta, t, K=90, u=1):
    """Intervals holding the exact b2 and b4 (the K-term values widened by the majorant remainder)."""
    p, q, r, w, P, Q = _series_cached(delta, u, K)
    pv, qv, Pv, Qv = ev(p, t), ev(q, t), ev(P, t), ev(Q, t)
    T1, T3 = series_remainder(delta, t, K, u)
    ip = Iv(pv - T1, pv + T1)
    iq = Iv(qv - T1, qv + T1)
    iP = Iv(Pv - T3, Pv + T3)
    iQ = Iv(Qv - T3, Qv + T3)
    return ip.sq() + iq.sq(), (ip * iP + iq * iQ) * 2


def lowest_terms(delta, K=12, u=1):
    """The lowest-order t coefficients of b2(t) and b4(t) as exact polynomials (YSERIES: b4/b2 = -(2/3) t^2)."""
    p, q, r, w, P, Q = series(delta, u, K)

    def mul(a, b):
        out = [Fraction(0)] * (K + 1)
        for i in range(K + 1):
            for j in range(K + 1 - i):
                out[i + j] += a[i] * b[j]
        return out

    b2 = [x + y for x, y in zip(mul(p, p), mul(q, q), strict=True)]
    b4 = [2 * (x + y) for x, y in zip(mul(p, P), mul(q, Q), strict=True)]

    def first(c):
        return next((k, c[k]) for k in range(K + 1) if c[k] != 0)

    return first(b2), first(b4)


def r_two_term(delta, t, y, K=90):
    """R(y) - 1/4 by the two-term series: R(y) = D2(y/2)/D2(y) = (1/4)(b2 + b4 y^2/4)/(b2 + b4 y^2)."""
    b2, b4 = b2b4(delta, t, K)
    y = fr(y)
    return div(fr(1, 4) * (b2 + div(b4 * y * y, 4)), b2 + b4 * y * y) - fr(1, 4)


# ---------------------------------------------------------------------------------------------------------------------
# The frozen decimals these brackets must hold to their stated digits.

M14 = fr(-1, 4)
P12 = fr(1, 2)


def _law(delta, n, y, t):
    return Law(delta, n * fr(y) * fr(y), t)


def _iv(x):
    return x if isinstance(x, Iv) else Iv(x)


def _checks():
    c = []

    def add(kind, rid, snippet, text, fn, label):
        c.append((kind, rid, snippet, text, fn, label))

    # YSERIES and Q05: b4/b2 at delta = -1/4.
    for tt, text in ((fr(1, 2), "-0.234401"), (fr(1), "-1.904686"), (fr(2), "-37.768005")):
        add("STRIPES_DERIVATION", "YSERIES", "-0.234401,_-1.904686,_-37.768005_at_t=1/2,_1,_2_(delta=-1/4)", text,
            lambda tt=tt: _b4_over_b2(M14, tt), "b4/b2 delta=-1/4 t=%s" % tt)
        add("STRIPES_PREDICT", "Q05", "b4/b2=-0.234401,_-1.904686,_-37.768005_at_t=1/2,_1,_2", text,
            lambda tt=tt: _b4_over_b2(M14, tt), "Q05 b4/b2 t=%s" % tt)
    add("STRIPES_DERIVATION", "YSERIES", "(1/3,1/9,1):_0.0177464_against_NL_0.0177507", "0.0177464",
        lambda: _series_B_over_N(fr(1, 3), fr(1, 9), 1), "YSERIES excluded check y^2 b2 + y^4 b4")
    add("STRIPES_DERIVATION", "YSERIES", "0.0177464_against_NL_0.0177507", "0.0177507",
        lambda: Iv(fr(19517145882, ipow(2, 40))), "YSERIES NL value 19517145882/2^40")
    add("STRIPES_DERIVATION", "QSEL", "0.0070508_against_0.0069444_at_t=1/4", "0.0069444",
        lambda: Iv(9 * fr(1, 81) * fr(1, 16)), "QSEL N y^2 t^2 at N=9 y=1/9 t=1/4")
    # Q03: the two-term-series range and the Richardson limit.
    add("STRIPES_PREDICT", "Q03", "R-1/4_from_3.77e-6_to_6.09e-4", "3.77e-6",
        lambda: Iv(r_two_term(M14, fr(1, 2), fr(1, 108))), "Q03 min R-1/4 (t=1/2, 1/108->1/216)")
    add("STRIPES_PREDICT", "Q03", "R-1/4_from_3.77e-6_to_6.09e-4", "6.09e-4",
        lambda: Iv(r_two_term(M14, fr(2), fr(1, 108))), "Q03 max R-1/4 (t=2, 1/108->1/216)")
    add("STRIPES_PREDICT", "Q03", "L-1/4=-8.0e-6", "-8.0e-6",
        lambda: Iv(div(4 * r_two_term(M14, 2, fr(1, 108)) - r_two_term(M14, 2, fr(1, 54)), 3)),
        "Q03 L-1/4 two-term")
    # Q04: classical D ratios and D(1/8), and d2 = 45/64.
    y27 = fr(1, 27)
    add("STRIPES_PREDICT", "Q04", "(classical_0.24837,_0.24357)", "0.24837",
        lambda: D_classical(M14, fr(1, 8), y27) * D_classical(M14, fr(1, 4), y27).inv(), "Q04 D(1/8)/D(1/4) y=1/27")
    add("STRIPES_PREDICT", "Q04", "(classical_0.24837,_0.24357)", "0.24357",
        lambda: D_classical(M14, fr(1, 4), y27) * D_classical(M14, fr(1, 2), y27).inv(), "Q04 D(1/4)/D(1/2) y=1/27")
    add("STRIPES_PREDICT", "Q04", "(classical_0.010996)", "0.010996",
        lambda: D_classical(M14, fr(1, 8), y27), "Q04 D(1/8) y=1/27")
    add("STRIPES_PREDICT", "Q04", "trajectory_d2=45/64", "45/64", lambda: Iv(d2_coefficient(M14)), "Q04 d2 exact")
    # Q05: R - 1/4, two-term series.
    for (tt, y, text) in ((fr(1, 2), fr(1, 27), "+6.031e-5"), (fr(1), fr(1, 27), "+4.912e-4"),
                          (fr(1), fr(1, 54), "+1.2255e-4"), (fr(2), fr(1, 54), "+2.4604e-3"),
                          (fr(2), fr(1, 108), "+6.091e-4")):
        add("STRIPES_PREDICT", "Q05", "R-1/4=+6.031e-5,_+4.912e-4,_+1.2255e-4,_+2.4604e-3,_+6.091e-4", text,
            lambda tt=tt, y=y: Iv(r_two_term(M14, tt, y)), "Q05 R-1/4 t=%s y=%s" % (tt, y))
    # Q06: D2_law, kappa_q, y^2 b4/b2 at N=729.
    d2 = (("2.02700e-4", "1/2", "1/54"), ("5.06750e-5", "1/2", "1/108"), ("1.241720e-3", "1", "1/54"),
          ("3.104301e-4", "1", "1/108"), ("1.629505e-2", "2", "1/54"), ("4.073763e-3", "2", "1/108"))
    for text, tt, y in d2:
        add("STRIPES_PREDICT", "Q06", "D2_law=2.02700e-4,_5.06750e-5;_1.241720e-3,_3.104301e-4;_1.629505e-2,"
            "_4.073763e-3", text, lambda tt=tt, y=y: d2_law(M14, fr(y), fr(tt)), "Q06 D2_law t=%s y=%s" % (tt, y))
    for text, tt in (("-0.000648", "1/2"), ("-0.003599", "1"), ("-0.040379", "2")):
        add("STRIPES_PREDICT", "Q06", "kappa_q=-0.000648,_-0.003599,_-0.040379", text,
            lambda tt=tt: kappa_q(M14, fr(tt), 729), "Q06 kappa_q t=%s" % tt)
    yb = (("-0.000080", "1/2", "1/54"), ("-0.000020", "1/2", "1/108"), ("-0.000653", "1", "1/54"),
          ("-0.000163", "1", "1/108"), ("-0.012952", "2", "1/54"), ("-0.003238", "2", "1/108"))
    for text, tt, y in yb:
        add("STRIPES_PREDICT", "Q06", "y^2_b4/b2=-0.000080,_-0.000020;_-0.000653,_-0.000163;_-0.012952,_-0.003238",
            text, lambda tt=tt, y=y: _b4_over_b2(M14, fr(tt)) * (fr(y) * fr(y)), "Q06 y^2 b4/b2 t=%s y=%s" % (tt, y))
    # Q07, E18, E19: n*_lin and EB2_lin at N=729.
    q7 = "n*_lin=17.760,_199.67;_5.566,_46.527,_574.30;_infinite,_17.723,_182.18"
    q7e = "EB2_lin=1.6385,_1.0955;_21.522,_9.7361,_7.3657;_327.18,_660.50,_403.89"
    for text, tt, y in (("17.760", "1/2", "1/27"), ("199.67", "1/2", "1/54"), ("5.566", "1", "1/27"),
                        ("46.527", "1", "1/54"), ("574.30", "1", "1/108"), ("17.723", "2", "1/54"),
                        ("182.18", "2", "1/108")):
        add("STRIPES_PREDICT", "Q07", q7, text, lambda tt=tt, y=y: _law(M14, 729, y, tt).nstar(),
            "Q07 n*_lin t=%s y=%s" % (tt, y))
    for text, tt, y in (("1.6385", "1/2", "1/27"), ("1.0955", "1/2", "1/54"), ("21.522", "1", "1/27"),
                        ("9.7361", "1", "1/54"), ("7.3657", "1", "1/108"), ("327.18", "2", "0"),
                        ("660.50", "2", "1/54"), ("403.89", "2", "1/108")):
        add("STRIPES_PREDICT", "Q07", q7e, text, lambda tt=tt, y=y: _law(M14, 729, y, tt).EB2,
            "Q07 EB2_lin t=%s y=%s" % (tt, y))
    for text, tt, y in (("327.18", "2", "0"), ("21.522", "1", "1/27"), ("9.7361", "1", "1/54"),
                        ("660.50", "2", "1/54"), ("403.89", "2", "1/108")):
        add("STRIPES_PREDICT", "E18", "law_values_327.18,_21.522,_9.7361,_660.50,_403.89_beside", text,
            lambda tt=tt, y=y: _law(M14, 729, y, tt).EB2, "E18 EB2_lin t=%s y=%s" % (tt, y))
    for text, tt in (("199.67", "1/2"), ("46.527", "1")):
        add("STRIPES_PREDICT", "E19", "share_n*_lin=199.67_(t=1/2),_46.527_(t=1)", text,
            lambda tt=tt: _law(M14, 81, fr(1, 18), tt).nstar(), "E19 n*_lin (81,1/18) t=%s" % tt)
    add("STRIPES_PREDICT", "E19", "R3_at_t=1_against_574.30", "574.30",
        lambda: _law(M14, 729, fr(1, 108), 1).nstar(), "E19 n*_lin (729,1/108) t=1")
    # E14: the crossover ratios.
    add("STRIPES_PREDICT", "E14", "closed_form_574.30/46.527=12.343", "12.343",
        lambda: _law(M14, 729, fr(1, 108), 1).nstar() * _law(M14, 729, fr(1, 54), 1).nstar().inv(), "E14 ratio t=1")
    add("STRIPES_PREDICT", "E14", "t=2:_closed_form_10.280", "10.280",
        lambda: _law(M14, 729, fr(1, 108), 2).nstar() * _law(M14, 729, fr(1, 54), 2).nstar().inv(), "E14 ratio t=2")
    # E13: rho at t=2 (t=1), n* at t=2, the Z_n bands.
    e13 = (("P02", 1296, fr(1, 576), "9.2917e-6", "4.5447e-6", "107622"),
           ("P03", 1296, fr(1, 288), "1.4500e-4", "7.1578e-5", "6895.6"),
           ("P04", 1296, fr(1, 144), "2.1085e-3", "1.0770e-3", "473.28"),
           ("P05", 1296, fr(1, 72), "2.4298e-2", "1.3781e-2", "40.156"),
           ("P06", 1296, fr(1, 36), "0.16250", "0.11271", "5.1537"))
    for pid, n, y, r2, r1, ns in e13:
        snip = "%s_%s_(%s)" % (pid, r2, r1)
        add("STRIPES_PREDICT", "E13", snip, r2, lambda n=n, y=y: _law(P12, n, y, 2).rho(), "E13 %s rho t=2" % pid)
        add("STRIPES_PREDICT", "E13", snip, r1, lambda n=n, y=y: _law(P12, n, y, 1).rho(), "E13 %s rho t=1" % pid)
        add("STRIPES_PREDICT", "E13", "n*_t=2:_107622,_6895.6,_473.28,_40.156,_5.1537,_17.723", ns,
            lambda n=n, y=y: _law(P12, n, y, 2).nstar(), "E13 %s n* t=2" % pid)
    add("STRIPES_PREDICT", "E13", "P08_5.3411e-2_(2.1041e-2)", "5.3411e-2",
        lambda: _law(M14, 729, fr(1, 54), 2).rho(), "E13 P08 rho t=2")
    add("STRIPES_PREDICT", "E13", "P08_5.3411e-2_(2.1041e-2)", "2.1041e-2",
        lambda: _law(M14, 729, fr(1, 54), 1).rho(), "E13 P08 rho t=1")
    # The Z_n band values are 1 + (n - 1) rho at the row's own frozen rho decimal (rule DECIMAL).
    zb = (("P02_MET_to_n=4096_(1.038)", "1.038", "9.2917e-6", 4096),
          ("P03_MET_to_1024_(1.148)", "1.148", "1.4500e-4", 1024),
          ("NOT_MET_at_4096_(1.594)", "1.594", "1.4500e-4", 4096),
          ("P04_MET_to_64_(1.133)", "1.133", "2.1085e-3", 64),
          ("NOT_MET_from_256_(1.538,_3.157,_9.634)", "1.538", "2.1085e-3", 256),
          ("NOT_MET_from_256_(1.538,_3.157,_9.634)", "3.157", "2.1085e-3", 1024),
          ("NOT_MET_from_256_(1.538,_3.157,_9.634)", "9.634", "2.1085e-3", 4096),
          ("(P05_1.365,_2.531,_7.196,_25.86)", "1.365", "2.4298e-2", 16),
          ("(P05_1.365,_2.531,_7.196,_25.86)", "2.531", "2.4298e-2", 64),
          ("(P05_1.365,_2.531,_7.196,_25.86)", "7.196", "2.4298e-2", 256),
          ("(P05_1.365,_2.531,_7.196,_25.86)", "25.86", "2.4298e-2", 1024),
          ("P06_NOT_MET_from_4_(1.4875)", "1.4875", "0.16250", 4),
          ("MET_at_n=4_(1.0631)", "1.0631", "2.1041e-2", 4),
          ("(1.3156,_2.3256,_6.3655,_22.525_to_n=1024)", "1.3156", "2.1041e-2", 16),
          ("(1.3156,_2.3256,_6.3655,_22.525_to_n=1024)", "2.3256", "2.1041e-2", 64),
          ("(1.3156,_2.3256,_6.3655,_22.525_to_n=1024)", "6.3655", "2.1041e-2", 256),
          ("(1.3156,_2.3256,_6.3655,_22.525_to_n=1024)", "22.525", "2.1041e-2", 1024))
    for snip, text, rho, nb in zb:
        add("STRIPES_PREDICT", "E13", snip, text, lambda rho=rho, nb=nb: Iv(1 + (nb - 1) * Decimal(rho).value),
            "E13 Z_%d at frozen rho %s" % (nb, rho))
    # E17: linear-law f and Z_64 at N=121, delta=1/2, s=1.
    for text, tt in (("0.043", 1), ("0.357", 2), ("2.21", 3)):
        add("STRIPES_PREDICT", "E17", "linear-law_f=0.043,_0.357,_2.21_at_t=1,_2,_3", text,
            lambda tt=tt: _law(P12, 121, fr(1, 11), tt).f_lin(121), "E17 f_lin t=%s" % tt)
    add("STRIPES_PREDICT", "E17", "(Z_64=8.10_at_t=1)", "8.10", lambda: _law(P12, 121, fr(1, 11), 1).Z(64),
        "E17 Z_64 t=1")
    return c


def _b4_over_b2(delta, t):
    b2, b4 = b2b4_iv(delta, t)
    return b4 * b2.inv()


def _series_B_over_N(delta, y, t):
    b2, b4 = b2b4_iv(delta, t)
    y = fr(y)
    return b2 * (y * y) + b4 * (y * y * y * y)


# Frozen decimals no exact bracket rounds to (a last-digit slip at design time), reported, never corrected.
KNOWN_SLIPS = {"E13 Z_16 at frozen rho 2.4298e-2": "1 + 15 rho = 1.36447 from rho 2.4298e-2 (exact rho 2.42979e-2)"}

CONTAINS = "contains"
OUTSIDE = "outside"
STRADDLES = "straddles"


def check_decimal(bracket, text):
    """Whether the bracket of the exact quantity lies inside [d - h, d + h], h half a unit of d's last stated digit
    (an exact rational n/d must equal the bracket)."""
    if "/" in text:
        v = parse_rat(text)
        lo = hi = v
    else:
        lo, hi = Decimal(text).stated_band()
    b = _iv(bracket)
    if lo <= b.lo and b.hi <= hi:
        return CONTAINS
    if b.hi < lo or b.lo > hi:
        return OUTSIDE
    return STRADDLES


def check_frozen(fz=None):
    """[(label, kind, id, decimal, bracket, status)] for every frozen decimal this module brackets; each decimal must
    stand in its snippet and each snippet in its frozen row."""
    fz = fz or frozen_mod.load()
    out = []
    for kind, rid, snippet, text, fn, label in _checks():
        fz.require(kind, rid, snippet)
        if text not in snippet:
            raise ValueError("decimal %s not in its snippet" % text)
        b = _iv(fn())
        out.append((label, kind, rid, text, b, check_decimal(b, text)))
    return out
