#!/usr/bin/env python3
# t5_firstcorr.py -- exact first correction in 1/N at fixed s = y sqrt(N), any rational delta and u.
# Number-conserving expansion on (n+, n-): H = H2 + H1/N + O(1/N^2). Heisenberg operators to first order:
#    z = a + c^dag, w = a - c^dag:   z' = i(1-delta) w + zeta/N,  w' = -i(1+delta) z + 2 i s + xi/N
#    zeta = i[H1, z], xi = i[H1, w], evaluated on the zeroth-order (Gaussian) operators.
# Everything reduces to equal-time Gaussian moments at tau and elementary integrals over tau in [0, t].
# Ring: Q(gamma)[i] with gamma^2 = 1 - delta^2 as a formal symbol; time functions are sums of
#    s^sp t^ti tau^tj e^(k1 gamma t) e^(k2 gamma tau).
# No float. Exact rationals only.
from fractions import Fraction as Fr
from math import comb, factorial
import sys

class Ctx:
    def __init__(self, delta, u):
        self.delta = Fr(delta)
        self.u = Fr(u)
        self.g2 = 1 - self.delta*self.delta

class W:
    """(a + b gamma) + i (c + d gamma)"""
    __slots__ = ('a', 'b', 'c', 'd')
    g2 = Fr(1)
    def __init__(self, a=0, b=0, c=0, d=0):
        self.a = Fr(a); self.b = Fr(b); self.c = Fr(c); self.d = Fr(d)
    def __add__(s, o):
        return W(s.a+o.a, s.b+o.b, s.c+o.c, s.d+o.d)
    def __sub__(s, o):
        return W(s.a-o.a, s.b-o.b, s.c-o.c, s.d-o.d)
    def __neg__(s):
        return W(-s.a, -s.b, -s.c, -s.d)
    def __mul__(s, o):
        g = W.g2
        # real parts
        ra = s.a*o.a + s.b*o.b*g
        rb = s.a*o.b + s.b*o.a
        ia = s.c*o.a + s.d*o.b*g
        ib = s.c*o.b + s.d*o.a
        ja = s.a*o.c + s.b*o.d*g
        jb = s.a*o.d + s.b*o.c
        ka = s.c*o.c + s.d*o.d*g
        kb = s.c*o.d + s.d*o.c
        return W(ra - ka, rb - kb, ia + ja, ib + jb)
    def conj(s):
        return W(s.a, s.b, -s.c, -s.d)
    def is_zero(s):
        return s.a == 0 and s.b == 0 and s.c == 0 and s.d == 0
    def __repr__(s):
        return 'W(%s,%s,%s,%s)' % (s.a, s.b, s.c, s.d)

ONE = W(1)
I = W(0, 0, 1, 0)

def wr(x):
    return W(Fr(x))

# ---- normal-ordered operator polynomials: key (sp, i, j, k, l) = s^sp a^dag^i c^dag^j a^k c^l
def nadd(A, B, sign=1):
    out = dict(A)
    for key, v in B.items():
        if key in out:
            nv = out[key] + v if sign == 1 else out[key] - v
        else:
            nv = v if sign == 1 else -v
        if nv.is_zero():
            out.pop(key, None)
        else:
            out[key] = nv
    return out

def nscal(A, w):
    out = {}
    for key, v in A.items():
        nv = v*w
        if not nv.is_zero():
            out[key] = nv
    return out

def contract(k, m):
    # a^k (a^dag)^m = Sum_r r! C(k,r) C(m,r) (a^dag)^(m-r) a^(k-r)
    return [(factorial(r)*comb(k, r)*comb(m, r), m-r, k-r) for r in range(0, min(k, m)+1)]

def nmul(A, B):
    out = {}
    for (s1, i1, j1, k1, l1), v1 in A.items():
        for (s2, i2, j2, k2, l2), v2 in B.items():
            v = v1*v2
            for (ca, m_a, k_a) in contract(k1, i2):
                for (cc, m_c, k_c) in contract(l1, j2):
                    key = (s1+s2, i1+m_a, j1+m_c, k_a+k2, k_c+l2)
                    nv = v*wr(ca*cc)
                    if key in out:
                        out[key] = out[key] + nv
                    else:
                        out[key] = nv
    return {k: v for k, v in out.items() if not v.is_zero()}

def nconst(x):
    return {(0, 0, 0, 0, 0): (x if isinstance(x, W) else wr(x))}

Ad = {(0, 1, 0, 0, 0): ONE}
Cd = {(0, 0, 1, 0, 0): ONE}
Aa = {(0, 0, 0, 1, 0): ONE}
Cc = {(0, 0, 0, 0, 1): ONE}
S_ = {(1, 0, 0, 0, 0): ONE}

def comm(A, B):
    return nadd(nmul(A, B), nmul(B, A), -1)

def hermitian_conj(A):
    out = {}
    for (s, i, j, k, l), v in A.items():
        out[(s, k, l, i, j)] = v.conj()
    return out

# ---- Gaussian expectation of a monomial as a polynomial in (alpha, alphabar, J, M, Mbar); memoised.
_memo = {}
def wick(i, j, k, l):
    key = (i, j, k, l)
    if key in _memo:
        return _memo[key]
    res = {}
    def add(sym_idx, mult, sub):
        for ex, c in sub.items():
            e = list(ex)
            e[sym_idx] += 1
            e = tuple(e)
            res[e] = res.get(e, 0) + mult*c
    # symbols: 0 alpha, 1 alphabar, 2 J, 3 M, 4 Mbar
    if i > 0:
        add(1, 1, wick(i-1, j, k, l))
        if k > 0:
            add(2, k, wick(i-1, j, k-1, l))
        if j > 0:
            add(4, j, wick(i-1, j-1, k, l))
    elif j > 0:
        add(1, 1, wick(0, j-1, k, l))
        if l > 0:
            add(2, l, wick(0, j-1, k, l-1))
    elif k > 0:
        add(0, 1, wick(0, 0, k-1, l))
        if l > 0:
            add(3, l, wick(0, 0, k-1, l-1))
    elif l > 0:
        add(0, 1, wick(0, 0, 0, l-1))
    else:
        res[(0, 0, 0, 0, 0)] = 1
    _memo[key] = res
    return res

# ---- time functions: key (sp, ti, tj, k1, k2)
def tadd(A, B, sign=1):
    out = dict(A)
    for key, v in B.items():
        if key in out:
            nv = out[key] + v if sign == 1 else out[key] - v
        else:
            nv = v if sign == 1 else -v
        if nv.is_zero():
            out.pop(key, None)
        else:
            out[key] = nv
    return out

def tmul(A, B):
    out = {}
    for (a0, a1, a2, a3, a4), v1 in A.items():
        for (b0, b1, b2, b3, b4), v2 in B.items():
            key = (a0+b0, a1+b1, a2+b2, a3+b3, a4+b4)
            v = v1*v2
            if key in out:
                out[key] = out[key] + v
            else:
                out[key] = v
    return {k: v for k, v in out.items() if not v.is_zero()}

def tscal(A, w):
    return {k: v*w for k, v in A.items() if not (v*w).is_zero()}

def tconst(w):
    return {(0, 0, 0, 0, 0): (w if isinstance(w, W) else wr(w))}

def tconj(A):
    return {k: v.conj() for k, v in A.items()}

class Dyn:
    def __init__(self, ctx):
        self.ctx = ctx
        W.g2 = ctx.g2
        self.edge = (ctx.g2 == 0)
        d = ctx.delta
        # single-time functions keyed by var in ('tau','t','t-tau')
        self.C = {v: self._C(v) for v in ('tau', 't', 't-tau')}
        self.S = {v: self._S(v) for v in ('tau', 't', 't-tau')}
        self.G = {v: self._G(v) for v in ('tau', 't')}
        s = {(1, 0, 0, 0, 0): ONE}
        G = self.G['tau']; St = self.S['tau']
        # alpha = -s G + i s S
        self.alpha = tadd(tmul(s, tscal(G, wr(-1))), tmul(s, tscal(St, I)))
        self.alphabar = tconj(self.alpha)
        self.J = tmul(St, St)
        # M = <da dc> = -i S (C - i delta S) = -i S C - delta S^2
        Ct = self.C['tau']
        self.M = tadd(tscal(tmul(St, Ct), W(0, 0, -1, 0)), tscal(tmul(St, St), wr(-d)))
        self.Mbar = tconj(self.M)
        self.sym = [self.alpha, self.alphabar, self.J, self.M, self.Mbar]
        self._pow = {}
        # means at t and at tau of z, w
        self.zbar_tau = tadd(self.alpha, self.alphabar)
        self.wbar_tau = tadd(self.alpha, self.alphabar, -1)
        G_t = self.G['t']; S_t = self.S['t']
        self.zbar_t = tmul(s, tscal(G_t, wr(-2)))
        self.wbar_t = tmul(s, tscal(S_t, W(0, 0, 2, 0)))
        self.build_ops()

    def _exp(self, var, sign):
        if var == 'tau':
            return (0, 0, 0, 0, sign)
        if var == 't':
            return (0, 0, 0, sign, 0)
        return (0, 0, 0, sign, -sign)

    def _C(self, var):
        if self.edge:
            return tconst(ONE)
        half = wr(Fr(1, 2))
        return {self._exp(var, 1): half, self._exp(var, -1): half}

    def _S(self, var):
        if self.edge:
            if var == 'tau':
                return {(0, 0, 1, 0, 0): ONE}
            if var == 't':
                return {(0, 1, 0, 0, 0): ONE}
            return {(0, 1, 0, 0, 0): ONE, (0, 0, 1, 0, 0): wr(-1)}
        # 1/(2 gamma) = gamma/(2 g2)
        co = W(0, Fr(1)/(2*self.ctx.g2))
        return {self._exp(var, 1): co, self._exp(var, -1): -co}

    def _G(self, var):
        d = self.ctx.delta
        if self.edge:
            if d == -1:
                if var == 'tau':
                    return {(0, 0, 2, 0, 0): ONE}
                return {(0, 2, 0, 0, 0): ONE}
            return {}
        Cv = self.C[var]
        return tscal(tadd(Cv, tconst(ONE), -1), wr(Fr(1)/(1+d)))

    def spow(self, idx, e):
        key = (idx, e)
        if key not in self._pow:
            if e == 0:
                self._pow[key] = tconst(ONE)
            else:
                self._pow[key] = tmul(self.spow(idx, e-1), self.sym[idx])
        return self._pow[key]

    def expect(self, nop):
        """Gaussian expectation at tau of a normal-ordered polynomial -> time function of tau."""
        out = {}
        for (sp, i, j, k, l), v in nop.items():
            poly = wick(i, j, k, l)
            for ex, c in poly.items():
                term = {(sp, 0, 0, 0, 0): v*wr(c)}
                for idx, e in enumerate(ex):
                    if e:
                        term = tmul(term, self.spow(idx, e))
                out = tadd(out, term)
        return out

    def build_ops(self):
        ctx = self.ctx
        d, u = ctx.delta, ctx.u
        np_ = nmul(Ad, Aa); nm = nmul(Cd, Cc); n = nadd(np_, nm)
        self.n = n
        half = nconst(Fr(1, 2))
        pairup = nmul(Ad, nmul(Cd, nadd(n, half)))          # a^dag c^dag (n + 1/2)
        pairdn = nmul(nadd(n, half), nmul(Aa, Cc))          # (n + 1/2) a c
        diag = nadd(nadd(nmul(np_, np_), nmul(nm, nm)), nmul(np_, nm))
        nm1 = nadd(n, nconst(1), -1)
        fld = nadd(nadd(nadd(nmul(Aa, nm1), nmul(Ad, n)), nmul(Cc, nm1)), nmul(Cd, n))
        H1 = nadd(nadd(nscal(diag, wr(-u)), nscal(nadd(pairup, pairdn), wr(-1))), nscal(nmul(S_, fld), wr(Fr(1, 2))))
        self.H1 = H1
        self.H2 = nadd(nadd(nscal(n, wr(d)), nadd(nmul(Ad, Cd), nmul(Aa, Cc))), nscal(nmul(S_, nadd(nadd(Aa, Ad), nadd(Cc, Cd))), wr(-1)))
        self.z = nadd(Aa, Cd); self.w = nadd(Aa, Cd, -1)
        self.zd = nadd(Ad, Cc); self.wd = nadd(Ad, Cc, -1)
        self.zeta = nscal(comm(H1, self.z), I)
        self.xi = nscal(comm(H1, self.w), I)
        # check the zeroth-order equations of motion
        eq1 = nscal(comm(self.H2, self.z), I)
        tgt1 = nscal(self.w, W(0, 0, 1-d, 0))
        assert not nadd(eq1, tgt1, -1), 'eom z'
        eq2 = nscal(comm(self.H2, self.w), I)
        tgt2 = nadd(nscal(self.z, W(0, 0, -(1+d), 0)), nscal(S_, W(0, 0, 2, 0)))
        assert not nadd(eq2, tgt2, -1), 'eom w'
        # sources' expectations
        self.e_zeta = self.expect(self.zeta)
        self.e_xi = self.expect(self.xi)
        # <B src> for B in z, w, zd, wd; src in zeta, xi
        self.e_B_src = {}
        self.e_src_B = {}
        for bname, bop, bmean in (('z', self.z, self.zbar_tau), ('w', self.w, self.wbar_tau),
                                  ('zd', self.zd, self.zbar_tau), ('wd', self.wd, tscal(self.wbar_tau, wr(-1)))):
            for sname, sop, smean in (('zeta', self.zeta, self.e_zeta), ('xi', self.xi, self.e_xi)):
                full = self.expect(nmul(bop, sop))
                self.e_B_src[(bname, sname)] = tadd(full, tmul(bmean, smean), -1)
                full2 = self.expect(nmul(sop, bop))
                self.e_src_B[(sname, bname)] = tadd(full2, tmul(bmean, smean), -1)
        self.ctm = self.C['t-tau']; self.stm = self.S['t-tau']

    def coef_x(self, X):
        """X^(0)(t) = Xbar(t) + Sum cX_B dB(tau): returns (Xbar(t), {B: coef})"""
        d = self.ctx.delta
        C, S = self.ctm, self.stm
        if X == 'z':
            return self.zbar_t, {'z': C, 'w': tscal(S, W(0, 0, 1-d, 0))}
        if X == 'w':
            return self.wbar_t, {'w': C, 'z': tscal(S, W(0, 0, -(1+d), 0))}
        if X == 'zd':
            return self.zbar_t, {'zd': C, 'wd': tscal(S, W(0, 0, -(1-d), 0))}
        if X == 'wd':
            return tscal(self.wbar_t, wr(-1)), {'wd': C, 'zd': tscal(S, W(0, 0, 1+d, 0))}
        raise ValueError(X)

    def coef_y(self, Y):
        d = self.ctx.delta
        C, S = self.ctm, self.stm
        if Y == 'z':
            return {'zeta': C, 'xi': tscal(S, W(0, 0, 1-d, 0))}
        if Y == 'w':
            return {'xi': C, 'zeta': tscal(S, W(0, 0, -(1+d), 0))}
        raise ValueError(Y)

    def integrate(self, f):
        """integral over tau from 0 to t of a time function; result has tj = 0, k2 = 0."""
        out = {}
        g2 = self.ctx.g2
        for (sp, ti, tj, k1, k2), v in f.items():
            # integral of tau^j e^(k gamma tau) dtau from 0 to t
            terms = self._int_tau(tj, k2)
            for (mult, a, ek) in terms:
                key = (sp, ti+a, 0, k1+ek, 0)
                nv = v*mult
                if key in out:
                    out[key] = out[key] + nv
                else:
                    out[key] = nv
        return {k: v for k, v in out.items() if not v.is_zero()}

    def _int_tau(self, j, k):
        # returns list of (W coefficient, power of t, exponent k) for int_0^t tau^j e^(k gamma tau) dtau
        if k == 0:
            return [(wr(Fr(1, j+1)), j+1, 0)]
        kgi = W(0, Fr(1)/(k*self.ctx.g2))   # 1/(k gamma) = gamma/(k g2)
        # int = t^j e^(kgt)/(kg) - (j/(kg)) int tau^(j-1) e^(kg tau); at j=0 subtract lower limit 1/(kg)
        if j == 0:
            return [(kgi, 0, k), (-kgi, 0, 0)]
        res = [(kgi, j, k)]
        for (w, a, e) in self._int_tau(j-1, k):
            res.append((w*kgi*wr(-j), a, e))
        return res

    def G_pair(self, X, Y):
        """<X^(0)(t) Y1(t)>"""
        Xbar, cx = self.coef_x(X)
        cy = self.coef_y(Y)
        means = {'zeta': self.e_zeta, 'xi': self.e_xi}
        total = {}
        for sname, cs in cy.items():
            inner = tmul(Xbar, means[sname])
            for B, cB in cx.items():
                inner = tadd(inner, tmul(cB, self.e_B_src[(B, sname)]))
            total = tadd(total, tmul(cs, inner))
        return self.integrate(total)

    def G_pair_rev(self, Y, X):
        """<Y1(t) X^(0)(t)>"""
        Xbar, cx = self.coef_x(X)
        cy = self.coef_y(Y)
        means = {'zeta': self.e_zeta, 'xi': self.e_xi}
        total = {}
        for sname, cs in cy.items():
            inner = tmul(Xbar, means[sname])
            for B, cB in cx.items():
                inner = tadd(inner, tmul(cB, self.e_src_B[(sname, B)]))
            total = tadd(total, tmul(cs, inner))
        return self.integrate(total)

    def mean_first(self, Y):
        """<Y1(t)>"""
        cy = self.coef_y(Y)
        means = {'zeta': self.e_zeta, 'xi': self.e_xi}
        total = {}
        for sname, cs in cy.items():
            total = tadd(total, tmul(cs, means[sname]))
        return self.integrate(total)

    def at_t(self, f):
        """replace tau by t in a function of tau only"""
        out = {}
        for (sp, ti, tj, k1, k2), v in f.items():
            key = (sp, ti+tj, 0, k1+k2, 0)
            out[key] = out[key] + v if key in out else v
        return {k: v for k, v in out.items() if not v.is_zero()}

    def results(self):
        res = {}
        # <A>/sqrt(N) = zbar + (1/N)( <z1> - (1/2)<a(n-1) + c^dag n>_0 )
        nm1 = nadd(self.n, nconst(1), -1)
        a1op = nscal(nadd(nmul(Aa, nm1), nmul(Cd, self.n)), wr(Fr(-1, 2)))
        res['z0'] = self.zbar_t
        res['z1'] = tadd(self.mean_first('z'), self.at_t(self.expect(a1op)))
        # <z^dag z>_1, <w^dag w>_1
        Gzz = self.G_pair('zd', 'z')
        Gww = self.G_pair('wd', 'w')
        zz1 = tadd(Gzz, tconj(Gzz))
        ww1 = tadd(Gww, tconj(Gww))
        res['zz1'] = zz1; res['ww1'] = ww1
        # zeroth-order O2 = z^dag z - 1, X1 = -n^2 - a^dag c^dag (n+1/2) - (n+1/2) a c
        one = nconst(1)
        zdz = nmul(self.zd, self.z)
        O2 = nadd(zdz, one, -1)
        res['O2_0'] = self.at_t(self.expect(O2))
        half = nconst(Fr(1, 2))
        X1 = nadd(nscal(nmul(self.n, self.n), wr(-1)),
                  nscal(nadd(nmul(Ad, nmul(Cd, nadd(self.n, half))), nmul(nadd(self.n, half), nmul(Aa, Cc))), wr(-1)))
        res['X1_0'] = self.at_t(self.expect(X1))
        # C1 = (2/N) O2_0 + (2/N^2) [O2_0 + zz1 + X1_0]
        res['C1_0'] = tscal(res['O2_0'], wr(2))
        res['C1_1'] = tscal(tadd(tadd(res['O2_0'], zz1), res['X1_0']), wr(2))
        # n = (z^dag z + w^dag w)/2 - 1: <n>_1 = (zz1 + ww1)/2
        res['n_0'] = self.at_t(self.expect(self.n))
        res['n_1'] = tscal(tadd(zz1, ww1), wr(Fr(1, 2)))
        # pair sum a^dag c^dag + a c = (z^dag z - w^dag w)/2
        pair1 = tscal(tadd(zz1, ww1, -1), wr(Fr(1, 2)))
        # energy check: <H2>_1 + <H1>_0 = 0
        z1only = self.mean_first('z')
        field1 = tadd(z1only, tconj(z1only))   # <a + a^dag + c + c^dag>_1 = 2 Re <z1>
        s = {(1, 0, 0, 0, 0): ONE}
        e1 = tadd(tadd(tscal(res['n_1'], wr(self.ctx.delta)), pair1), tscal(tmul(s, field1), wr(-1)))
        e1 = tadd(e1, self.at_t(self.expect(self.H1)))
        res['energy_first_order'] = e1
        # D2: <B> = <c^dag a> = (z z - w w)/4 at the operator level: c^dag a = (z-w)(z+w)/4 = (z z - w w)/4 since [z,w] = 0
        # <z z>_1 = <z0 z1> + <z1 z0>, both orders read explicitly
        res['zz_op1'] = tadd(self.G_pair('z', 'z'), self.G_pair_rev('z', 'z'))
        res['ww_op1'] = tadd(self.G_pair('w', 'w'), self.G_pair_rev('w', 'w'))
        res['B_0'] = self.at_t(self.expect(nmul(Cd, Aa)))
        res['B_1'] = tscal(tadd(res['zz_op1'], res['ww_op1'], -1), wr(Fr(1, 4)))
        return res


def fmt_w(w):
    parts = []
    if w.a != 0: parts.append(str(w.a))
    if w.b != 0: parts.append('(%s)g' % w.b)
    if w.c != 0: parts.append('i(%s)' % w.c)
    if w.d != 0: parts.append('i(%s)g' % w.d)
    return '+'.join(parts) if parts else '0'

def show(name, f):
    print(name + ':')
    for key in sorted(f):
        print('   s^%d t^%d e^(%d g t): %s' % (key[0], key[1], key[3], fmt_w(f[key])))

if __name__ == '__main__':
    delta = Fr(sys.argv[1]) if len(sys.argv) > 1 else Fr(0)
    u = Fr(sys.argv[2]) if len(sys.argv) > 2 else Fr(1)
    W.g2 = 1 - delta*delta
    dyn = Dyn(Ctx(delta, u))
    res = dyn.results()
    print('delta', delta, 'u', u, 'g2', W.g2)
    print('energy_first_order_terms_nonzero', len(res['energy_first_order']))
    for nm in ('z0', 'z1', 'O2_0', 'C1_1', 'n_1', 'B_1'):
        show(nm, res[nm])
