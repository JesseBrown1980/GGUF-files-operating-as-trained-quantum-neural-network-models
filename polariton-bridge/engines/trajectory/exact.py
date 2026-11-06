#!/usr/bin/env python3
# exact.py -- exact algebra for the single classical trajectory of the three-mode polariton model.
# No float anywhere. Fractions and Python integers only.
#
# Fields:
#   QIField(delta)  : delta rational with gamma = sqrt(1 - delta^2) RATIONAL (e.g. 3/5 -> 4/5, 0 -> 1); elements a + b i.
#   QGField(delta)  : delta rational, gamma formal with gamma^2 = 1 - delta^2; elements (p + q gamma) + i (r + s gamma).
#   SymField()      : delta a symbol; coefficients are polynomials in delta over (1+delta)^a (1-delta)^b; gamma formal.
# ExpPoly: finite sums  coef * t^j * exp(k gamma t),  key (j, k).
from fractions import Fraction as Fr

# ---------------------------------------------------------------- polynomials in delta (low -> high)
def pstrip(a):
    a = list(a)
    while a and a[-1] == 0:
        a.pop()
    return tuple(a)

def padd(a, b):
    n = max(len(a), len(b))
    return pstrip([(a[i] if i < len(a) else 0) + (b[i] if i < len(b) else 0) for i in range(n)])

def pneg(a):
    return tuple(-c for c in a)

def pmul(a, b):
    if not a or not b:
        return ()
    out = [Fr(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        if x == 0:
            continue
        for j, y in enumerate(b):
            out[i + j] += x * y
    return pstrip(out)

def pscale(a, c):
    c = Fr(c)
    return pstrip([x * c for x in a])

def peval(a, x):
    v = Fr(0)
    for c in reversed(a):
        v = v * x + c
    return v

def pdiv_root(a, r):
    # divide polynomial a by (d - r); exact division required
    n = len(a) - 1
    if n < 1:
        raise ValueError('degree')
    b = [Fr(0)] * n
    b[n - 1] = a[n]
    for k in range(n - 1, 0, -1):
        b[k - 1] = a[k] + r * b[k]
    rem = a[0] + r * b[0]
    if rem != 0:
        raise ValueError('not exact')
    return pstrip(b)

ONEP = (Fr(1),)
P1PD = (Fr(1), Fr(1))      # 1 + d
P1MD = (Fr(1), Fr(-1))     # 1 - d
PG2 = (Fr(1), Fr(0), Fr(-1))  # 1 - d^2

def ppow(a, n):
    r = ONEP
    for _ in range(n):
        r = pmul(r, a)
    return r

class RF:
    """num(d) / ((1+d)^a (1-d)^b)"""
    __slots__ = ('n', 'a', 'b')
    def __init__(self, n=(), a=0, b=0):
        n = pstrip(tuple(Fr(c) for c in n))
        if not n:
            self.n, self.a, self.b = (), 0, 0
            return
        while a > 0 and peval(n, Fr(-1)) == 0:
            n = pdiv_root(n, Fr(-1)); a -= 1
        while b > 0 and peval(n, Fr(1)) == 0:
            n = pneg(pdiv_root(n, Fr(1))); b -= 1
        self.n, self.a, self.b = n, a, b
    def iszero(self):
        return not self.n
    def __add__(self, o):
        A = max(self.a, o.a); B = max(self.b, o.b)
        n1 = pmul(pmul(self.n, ppow(P1PD, A - self.a)), ppow(P1MD, B - self.b))
        n2 = pmul(pmul(o.n, ppow(P1PD, A - o.a)), ppow(P1MD, B - o.b))
        return RF(padd(n1, n2), A, B)
    def __neg__(self):
        return RF(pneg(self.n), self.a, self.b)
    def __sub__(self, o):
        return self + (-o)
    def __mul__(self, o):
        if self.iszero() or o.iszero():
            return RF()
        return RF(pmul(self.n, o.n), self.a + o.a, self.b + o.b)
    def scale(self, c):
        return RF(pscale(self.n, c), self.a, self.b)
    def at(self, d):
        d = Fr(d)
        return peval(self.n, d) / ((1 + d) ** self.a * (1 - d) ** self.b)
    def __repr__(self):
        return 'RF(%s / (1+d)^%d (1-d)^%d)' % ([str(c) for c in self.n], self.a, self.b)

RF0 = RF()
RF1 = RF(ONEP)
RFG2 = RF(PG2)

# ---------------------------------------------------------------- fields
class QI:
    __slots__ = ('a', 'b')
    def __init__(self, a=0, b=0):
        self.a = a if isinstance(a, Fr) else Fr(a)
        self.b = b if isinstance(b, Fr) else Fr(b)
    def __add__(s, o): return QI(s.a + o.a, s.b + o.b)
    def __sub__(s, o): return QI(s.a - o.a, s.b - o.b)
    def __neg__(s): return QI(-s.a, -s.b)
    def __mul__(s, o): return QI(s.a * o.a - s.b * o.b, s.a * o.b + s.b * o.a)
    def conj(s): return QI(s.a, -s.b)
    def iszero(s): return s.a == 0 and s.b == 0
    def scale(s, c): return QI(s.a * c, s.b * c)
    def __repr__(s): return 'QI(%s,%s)' % (s.a, s.b)

class QIField:
    def __init__(self, delta, gamma):
        self.delta = Fr(delta); self.gamma = Fr(gamma)
        assert self.gamma > 0 and self.gamma * self.gamma == 1 - self.delta * self.delta
    def zero(self): return QI()
    def one(self): return QI(1)
    def I(self): return QI(0, 1)
    def const(self, c): return QI(Fr(c))
    def dconst(self, c0, c1):  # c0 + c1*delta
        return QI(Fr(c0) + Fr(c1) * self.delta)
    def mul_gamma(self, x): return x.scale(self.gamma)
    def div_gamma(self, x): return x.scale(1 / self.gamma)
    def div_1pd(self, x): return x.scale(1 / (1 + self.delta))
    def div_1md(self, x): return x.scale(1 / (1 - self.delta))
    def realpart(self, x): return QI(x.a)
    def imagpart(self, x): return QI(x.b)   # as a real element

class QG:
    """(p + q g) + i (r + s g) with g^2 = g2, components Fractions"""
    __slots__ = ('p', 'q', 'r', 's')
    g2 = Fr(1)
    def __init__(self, p=0, q=0, r=0, s=0):
        self.p = Fr(p); self.q = Fr(q); self.r = Fr(r); self.s = Fr(s)
    def __add__(a, o): return QG(a.p + o.p, a.q + o.q, a.r + o.r, a.s + o.s)
    def __sub__(a, o): return QG(a.p - o.p, a.q - o.q, a.r - o.r, a.s - o.s)
    def __neg__(a): return QG(-a.p, -a.q, -a.r, -a.s)
    def __mul__(a, o):
        g = QG.g2
        xr = a.p * o.p + a.q * o.q * g; xg = a.p * o.q + a.q * o.p          # X1 X2
        yr = a.r * o.r + a.s * o.s * g; yg = a.r * o.s + a.s * o.r          # Y1 Y2
        ur = a.p * o.r + a.q * o.s * g; ug = a.p * o.s + a.q * o.r          # X1 Y2
        vr = a.r * o.p + a.s * o.q * g; vg = a.r * o.q + a.s * o.p          # Y1 X2
        return QG(xr - yr, xg - yg, ur + vr, ug + vg)
    def conj(a): return QG(a.p, a.q, -a.r, -a.s)
    def iszero(a): return a.p == 0 and a.q == 0 and a.r == 0 and a.s == 0
    def scale(a, c): return QG(a.p * c, a.q * c, a.r * c, a.s * c)

class QGField:
    def __init__(self, delta):
        self.delta = Fr(delta); self.g2 = 1 - self.delta * self.delta
        assert self.g2 > 0
        QG.g2 = self.g2
    def zero(self): return QG()
    def one(self): return QG(1)
    def I(self): return QG(0, 0, 1, 0)
    def const(self, c): return QG(Fr(c))
    def dconst(self, c0, c1): return QG(Fr(c0) + Fr(c1) * self.delta)
    def mul_gamma(self, x): return QG(x.q * self.g2, x.p, x.s * self.g2, x.r)
    def div_gamma(self, x): return QG(x.q, x.p / self.g2, x.s, x.r / self.g2)
    def div_1pd(self, x): return x.scale(1 / (1 + self.delta))
    def div_1md(self, x): return x.scale(1 / (1 - self.delta))
    def realpart(self, x): return QG(x.p, x.q)
    def imagpart(self, x): return QG(x.r, x.s)

class SG:
    """(p + q g) + i (r + s g), components RF in delta, g^2 = 1 - d^2"""
    __slots__ = ('p', 'q', 'r', 's')
    def __init__(self, p=RF0, q=RF0, r=RF0, s=RF0):
        self.p, self.q, self.r, self.s = p, q, r, s
    def __add__(a, o): return SG(a.p + o.p, a.q + o.q, a.r + o.r, a.s + o.s)
    def __sub__(a, o): return SG(a.p - o.p, a.q - o.q, a.r - o.r, a.s - o.s)
    def __neg__(a): return SG(-a.p, -a.q, -a.r, -a.s)
    def __mul__(a, o):
        xr = a.p * o.p + a.q * o.q * RFG2; xg = a.p * o.q + a.q * o.p
        yr = a.r * o.r + a.s * o.s * RFG2; yg = a.r * o.s + a.s * o.r
        ur = a.p * o.r + a.q * o.s * RFG2; ug = a.p * o.s + a.q * o.r
        vr = a.r * o.p + a.s * o.q * RFG2; vg = a.r * o.q + a.s * o.p
        return SG(xr - yr, xg - yg, ur + vr, ug + vg)
    def conj(a): return SG(a.p, a.q, -a.r, -a.s)
    def iszero(a): return a.p.iszero() and a.q.iszero() and a.r.iszero() and a.s.iszero()
    def scale(a, c): return SG(a.p.scale(c), a.q.scale(c), a.r.scale(c), a.s.scale(c))
    def at(self, d):
        """specialise to rational delta: returns QG at that delta (g2 = 1-d^2)"""
        return QG(self.p.at(d), self.q.at(d), self.r.at(d), self.s.at(d))

class SymField:
    def __init__(self):
        self.delta = None
    def zero(self): return SG()
    def one(self): return SG(RF1)
    def I(self): return SG(RF0, RF0, RF1, RF0)
    def const(self, c): return SG(RF((Fr(c),)))
    def dconst(self, c0, c1): return SG(RF((Fr(c0), Fr(c1))))
    def mul_gamma(self, x): return SG(x.q * RFG2, x.p, x.s * RFG2, x.r)
    def div_gamma(self, x):
        return SG(x.q, RF(x.p.n, x.p.a + 1, x.p.b + 1), x.s, RF(x.r.n, x.r.a + 1, x.r.b + 1))
    def div_1pd(self, x):
        return SG(*[RF(c.n, c.a + 1, c.b) for c in (x.p, x.q, x.r, x.s)])
    def div_1md(self, x):
        return SG(*[RF(c.n, c.a, c.b + 1) for c in (x.p, x.q, x.r, x.s)])
    def realpart(self, x): return SG(x.p, x.q)
    def imagpart(self, x): return SG(x.r, x.s)

# ---------------------------------------------------------------- exponential polynomials
class EP:
    """dict (j, k) -> coef : coef t^j e^{k gamma t}"""
    def __init__(self, F, d=None):
        self.F = F
        self.d = {} if d is None else d
    def copy(self):
        return EP(self.F, dict(self.d))
    def _put(self, key, v):
        if key in self.d:
            nv = self.d[key] + v
            if nv.iszero():
                del self.d[key]
            else:
                self.d[key] = nv
        elif not v.iszero():
            self.d[key] = v
    def __add__(self, o):
        r = self.copy()
        for k, v in o.d.items():
            r._put(k, v)
        return r
    def __neg__(self):
        return EP(self.F, {k: -v for k, v in self.d.items()})
    def __sub__(self, o):
        return self + (-o)
    def __mul__(self, o):
        r = EP(self.F)
        for (j1, k1), v1 in self.d.items():
            for (j2, k2), v2 in o.d.items():
                r._put((j1 + j2, k1 + k2), v1 * v2)
        return r
    def cmul(self, c):
        """multiply by a field element"""
        r = EP(self.F)
        for k, v in self.d.items():
            r._put(k, v * c)
        return r
    def scale(self, q):
        q = Fr(q)
        r = EP(self.F)
        for k, v in self.d.items():
            r._put(k, v.scale(q))
        return r
    def conj(self):
        return EP(self.F, {k: v.conj() for k, v in self.d.items()})
    def mapc(self, fn):
        r = EP(self.F)
        for k, v in self.d.items():
            r._put(k, fn(v))
        return r
    def shift(self, dk):
        return EP(self.F, {(j, k + dk): v for (j, k), v in self.d.items()})
    def iszero(self):
        return not self.d
    def re(self):
        return (self + self.conj()).scale(Fr(1, 2))
    def im_real(self):
        # (S - conj S)/(2i) = -i (S - conj S)/2 , a real exponential polynomial
        return (self - self.conj()).cmul(self.F.I()).scale(Fr(-1, 2))
    def integrate0(self):
        """int_0^t f(tau) dtau"""
        F = self.F
        r = EP(F)
        for (j, k), c in self.d.items():
            if k == 0:
                r._put((j + 1, 0), c.scale(Fr(1, j + 1)))
                continue
            # antiderivative e^{a tau} sum_m (-1)^m j!/(j-m)! tau^{j-m} / a^{m+1}, a = k gamma
            ff = 1
            for m in range(0, j + 1):
                if m > 0:
                    ff *= (j - m + 1)
                coef = c.scale(Fr((-1) ** m * ff, k ** (m + 1)))
                for _ in range(m + 1):
                    coef = F.div_gamma(coef)
                r._put((j - m, k), coef)
                if m == j:
                    r._put((0, 0), -coef)
        return r

def ep_const(F, c):
    e = EP(F)
    e._put((0, 0), c)
    return e

def ep_cosh(F, k):   # cosh(k gamma t)
    e = EP(F)
    if k == 0:
        e._put((0, 0), F.one())
        return e
    e._put((0, k), F.const(Fr(1, 2))); e._put((0, -k), F.const(Fr(1, 2)))
    return e

def ep_sinh(F, k):
    e = EP(F)
    e._put((0, k), F.const(Fr(1, 2))); e._put((0, -k), F.const(Fr(-1, 2)))
    return e

def ep_gs(F, k):     # gamma t sinh(k gamma t)
    e = EP(F)
    e._put((1, k), F.mul_gamma(F.const(Fr(1, 2)))); e._put((1, -k), F.mul_gamma(F.const(Fr(-1, 2))))
    return e

def duhamel(S):
    """solve i w' = delta w + conj(w) + S, w(0) = 0 (exactly), S an EP."""
    F = S.F
    Sr = S.re()
    Si = S.im_real()
    omd_over_g = lambda e: e.mapc(lambda v: F.div_gamma(v * F.dconst(1, -1)))   # (1-d)/gamma * e
    opd_over_g = lambda e: e.mapc(lambda v: F.div_gamma(v * F.dconst(1, 1)))    # (1+d)/gamma * e
    I1 = (Si + omd_over_g(Sr)).shift(-1).integrate0()
    I2 = (Si - omd_over_g(Sr)).shift(+1).integrate0()
    I3 = (-opd_over_g(Si) - Sr).shift(-1).integrate0()
    I4 = (opd_over_g(Si) - Sr).shift(+1).integrate0()
    p = (I1.shift(+1) + I2.shift(-1)).scale(Fr(1, 2))
    q = (I3.shift(+1) + I4.shift(-1)).scale(Fr(1, 2))
    return p + q.cmul(F.I())

def deriv(e):
    """d/dt of an EP"""
    F = e.F
    r = EP(F)
    for (j, k), c in e.d.items():
        if j > 0:
            r._put((j - 1, k), c.scale(j))
        if k != 0:
            r._put((j, k), F.mul_gamma(c.scale(k)))
    return r

# ---------------------------------------------------------------- the classical series
class Series:
    """single trajectory  z0 = 1 + sum y^{2k} v_{2k},  z+ = z- = w = sum y^{2k+1} w_{2k+1}
    i w'  = x w + u(|z0|^2 + |w|^2) w + conj(w) z0^2 - y z0
    i z0' = 2u |w|^2 z0 + 2 conj(z0) w^2 - 2 y w
    (the normal-ordered c-number equations of the operator text, reduced by the exchange symmetry z+ = z-)"""
    def __init__(self, F, u=Fr(1)):
        self.F = F
        self.u = Fr(u)
        self.w = {}
        self.z = {0: ep_const(F, F.one())}
    def _mul(self, A, B, n):
        r = EP(self.F)
        for i, a in A.items():
            j = n - i
            if j in B:
                r = r + a * B[j]
        return r
    def _conj(self, A):
        return {k: v.conj() for k, v in A.items()}
    def order(self, n):
        F = self.F
        w, z = self.w, self.z
        wc, zc = self._conj(w), self._conj(z)
        if n % 2 == 1:
            # S_n = [x w + u(|z0|^2 + |w|^2) w + conj(w) z0^2 - y z0]_n  with w_n := 0, minus nothing else
            # x w_n + u w_n + conj(w_n) is the linear part (delta w_n + conj w_n), excluded by w_n := 0
            x = F.dconst(-self.u, 1)    # x = delta - u
            zz = {m: self._mul(z, zc, m) for m in range(0, n + 1, 2)}
            ww = {m: self._mul(w, wc, m) for m in range(2, n + 1, 2)}
            mod = {m: zz.get(m, EP(F)) + ww.get(m, EP(F)) for m in range(0, n + 1, 2)}
            S = EP(F)
            # u (|z0|^2 + |w|^2) w, order n, excluding mod_0 * w_n (w_n not yet in w)
            S = S + self._mul(mod, w, n).scale(self.u)
            # conj(w) z0^2
            z2 = {m: self._mul(z, z, m) for m in range(0, n + 1, 2)}
            S = S + self._mul(wc, z2, n)
            # - y z0 : order n -> -z_{n-1}
            if (n - 1) in z:
                S = S - z[n - 1]
            # x w at order n is x w_n, linear, excluded
            del x
            wn = duhamel(S)
            self.w[n] = wn
            return S, wn
        else:
            # R_n = [2u|w|^2 z0 + 2 conj(z0) w^2 - 2 y w]_n
            ww = {m: self._mul(w, wc, m) for m in range(2, n + 1, 2)}
            R = self._mul(ww, z, n).scale(2 * self.u)
            w2 = {m: self._mul(w, w, m) for m in range(2, n + 1, 2)}
            R = R + self._mul(zc, w2, n).scale(2)
            if (n - 1) in w:
                R = R - w[n - 1].scale(2)
            vn = R.integrate0().cmul(F.I()).scale(-1)    # v_n = -i int R_n
            self.z[n] = vn
            return R, vn
    def build(self, nmax):
        for n in range(1, nmax + 1):
            self.order(n)
        return self
    # observables, as series in y
    def A_coeffs(self, kmax):
        """<A>/(N y) = sum_k y^{2k} W_k(t),  W_k = 2 Re [conj(z0) w]_{2k+1}"""
        zc = self._conj(self.z)
        out = []
        for k in range(0, kmax + 1):
            n = 2 * k + 1
            out.append(self._mul(zc, self.w, n).re().scale(2))
        return out
    def f_coeffs(self, kmax):
        """f = (n+ + n-)/N = 2|w|^2 = sum_k y^{2k} F_k(t), k >= 1"""
        wc = self._conj(self.w)
        return [None] + [self._mul(self.w, wc, 2 * k).scale(2) for k in range(1, kmax + 1)]
    def norm_check(self, nmax):
        """|z0|^2 + 2|w|^2 - 1 at each even order: must vanish identically"""
        zc = self._conj(self.z); wc = self._conj(self.w)
        bad = []
        for n in range(2, nmax + 1, 2):
            e = self._mul(self.z, zc, n) + self._mul(self.w, wc, n).scale(2)
            if not e.iszero():
                bad.append(n)
        return bad
    def energy_check(self, nmax):
        """H/N = x f + u[|z0|^2 2|w|^2 + |w|^4] + 2 Re(conj(w)^2 z0^2) - 4 y Re(conj(z0) w) ; zero at t=0, conserved"""
        F = self.F
        x = F.dconst(-self.u, 1)
        zc = self._conj(self.z); wc = self._conj(self.w)
        ww = {m: self._mul(self.w, wc, m) for m in range(2, nmax + 1, 2)}
        zz = {m: self._mul(self.z, zc, m) for m in range(0, nmax + 1, 2)}
        bad = []
        for n in range(2, nmax + 1, 2):
            e = ww.get(n, EP(F)).cmul(x).scale(2)
            e = e + self._mul(zz, ww, n).scale(2 * self.u) + self._mul(ww, ww, n).scale(self.u)
            wc2 = {m: self._mul(wc, wc, m) for m in range(2, n + 1, 2)}
            z2 = {m: self._mul(self.z, self.z, m) for m in range(0, n + 1, 2)}
            e = e + self._mul(wc2, z2, n).re().scale(2)
            e = e - self._mul(zc, self.w, n - 1).re().scale(4)
            if not e.iszero():
                bad.append(n)
        return bad

# ---------------------------------------------------------------- rigorous intervals (Fractions), outward rounding
BITS = 320
DEN = 1 << BITS

def _down(x):
    x = Fr(x)
    return Fr((x.numerator * DEN) // x.denominator, DEN)

def _up(x):
    x = Fr(x)
    return Fr(-((-x.numerator * DEN) // x.denominator), DEN)

class Iv:
    __slots__ = ('lo', 'hi')
    def __init__(self, lo, hi=None):
        if hi is None:
            hi = lo
        self.lo = Fr(lo); self.hi = Fr(hi)
        assert self.lo <= self.hi
    def __add__(s, o):
        o = o if isinstance(o, Iv) else Iv(o)
        return Iv(_down(s.lo + o.lo), _up(s.hi + o.hi))
    __radd__ = __add__
    def __neg__(s):
        return Iv(-s.hi, -s.lo)
    def __sub__(s, o):
        o = o if isinstance(o, Iv) else Iv(o)
        return s + (-o)
    def __rsub__(s, o):
        return Iv(o) - s
    def __mul__(s, o):
        o = o if isinstance(o, Iv) else Iv(o)
        c = [s.lo * o.lo, s.lo * o.hi, s.hi * o.lo, s.hi * o.hi]
        return Iv(_down(min(c)), _up(max(c)))
    __rmul__ = __mul__
    def inv(s):
        if s.lo <= 0 <= s.hi:
            raise ZeroDivisionError('interval contains 0')
        return Iv(_down(1 / s.hi), _up(1 / s.lo))
    def __truediv__(s, o):
        o = o if isinstance(o, Iv) else Iv(o)
        return s * o.inv()
    def __rtruediv__(s, o):
        return Iv(o) * s.inv()
    def absv(s):
        if s.lo >= 0:
            return s
        if s.hi <= 0:
            return -s
        return Iv(0, max(-s.lo, s.hi))
    def mid(s):
        return (s.lo + s.hi) / 2
    def width(s):
        return s.hi - s.lo
    def sq(s):
        a = s.absv()
        return a * a

def iv_exp(r):
    """rigorous enclosure of e^r for rational r"""
    r = Fr(r)
    m = 0
    x = r
    while abs(x) > Fr(1, 64):
        x /= 2
        m += 1
    # Taylor to K terms, remainder <= 2 |x|^(K+1)/(K+1)!
    s = Fr(0); term = Fr(1); K = 0
    tol = Fr(1, 1 << (BITS + 40))
    while True:
        s += term
        K += 1
        term = term * x / K
        if abs(term) * 2 < tol:
            break
    rem = abs(term) * 2
    lo = _down(s - rem); hi = _up(s + rem)
    v = Iv(lo, hi)
    for _ in range(m):
        v = v * v
    return v

def dec(x, digits=12):
    x = Fr(x)
    neg = x < 0
    x = abs(x)
    sc = (x.numerator * 10 ** digits + x.denominator // 2) // x.denominator
    ip, fp = divmod(sc, 10 ** digits)
    return ('-' if neg else '') + str(ip) + '.' + str(fp).zfill(digits)

def sci(x, sig=10):
    """exact rational to scientific text, sig significant digits, integers only"""
    x = Fr(x)
    if x == 0:
        return '0'
    neg = x < 0
    x = abs(x)
    e = 0
    while x >= 10:
        x /= 10; e += 1
    while x < 1:
        x *= 10; e -= 1
    sc = (x.numerator * 10 ** (sig - 1) + x.denominator // 2) // x.denominator
    if sc >= 10 ** sig:
        sc //= 10; e += 1
    s = str(sc)
    return ('-' if neg else '') + s[0] + '.' + s[1:] + 'e' + ('%+d' % e)

def ivtxt(v, sig=10):
    return '%s(+-%s)' % (sci(v.mid(), sig), sci(v.width() / 2, 2) if v.width() > 0 else '0')

def ep_eval(e, t, gamma, Eiv=None):
    """evaluate an EP over QI (rational gamma) at rational t, as (re, im) intervals"""
    t = Fr(t); gamma = Fr(gamma)
    if Eiv is None:
        Eiv = iv_exp(gamma * t)
    Einv = Eiv.inv()
    pw = {}
    def epow(k):
        if k not in pw:
            if k == 0:
                pw[k] = Iv(1)
            elif k > 0:
                pw[k] = epow(k - 1) * Eiv
            else:
                pw[k] = epow(k + 1) * Einv
        return pw[k]
    re = Iv(0); im = Iv(0)
    for (j, k), c in e.d.items():
        base = epow(k) * (t ** j)
        if c.a != 0:
            re = re + base * c.a
        if c.b != 0:
            im = im + base * c.b
    return re, im

# ---------------------------------------------------------------- evaluation over Q(gamma) with gamma irrational
from math import isqrt as _isqrt

def gamma_iv(g2, bits=360):
    g2 = Fr(g2)
    lo = Fr(_isqrt((g2.numerator << (2 * bits)) // g2.denominator), 1 << bits)
    hi = lo + Fr(1, 1 << bits)
    assert lo * lo <= g2 <= hi * hi
    return Iv(lo, hi)

def iv_exp_iv(a):
    """e^[lo,hi] for a rational interval"""
    return Iv(iv_exp(a.lo).lo, iv_exp(a.hi).hi)

def ep_eval_qg(e, t, g2, G=None):
    """evaluate an EP over QG at rational t; returns (re, im) intervals"""
    t = Fr(t)
    if G is None:
        G = gamma_iv(g2)
    cache = {}
    def ek(k):
        if k not in cache:
            if k == 0:
                cache[k] = Iv(1)
            else:
                ex = G * (k * t)
                cache[k] = iv_exp_iv(ex)
        return cache[k]
    re = Iv(0); im = Iv(0)
    for (j, k), c in e.d.items():
        base = ek(k) * (t ** j)
        if c.p != 0 or c.q != 0:
            re = re + base * (G * c.q + c.p)
        if c.r != 0 or c.s != 0:
            im = im + base * (G * c.s + c.r)
    return re, im
