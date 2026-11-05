# Own exact reads of statements in the text that carry algebra. Exact rationals, own code.
#  1. Operator identity for V^2.
#  2. J1 against the exact Taylor coefficients of pairs, extracted in 1/N, at (delta,u) the second seat did not use.
#  3. w1 at delta = 0, u = 1 against the exact Taylor coefficients of <A> at first order in y.
#  4. The 4 conversion rows: exact series at 10^-15.
#  5. N = 2 hand row, N = 3 doublet.
import sys
from math import factorial, comb
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
out = open(ME + 'out/own_exact.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True); out.write(s + '\n'); out.flush()

# ---- 1. Operator identity on all Fock pairs for N = 2..14
# In the normalized basis |n0,p,m>:
#   A = a0^dag a+ + a-^dag a0.  A^dag A vs n0(p+m) + n0 + p + P + P^dag.  Elements squared are integers, all elements are >= 0 here.
def a(n, k):
    return n  # placeholder for readability
bad = 0
tot = 0
def apply_A(st):
    """A|n0,p,m> as {state: element^2}, each element non-negative."""
    n0, p, m = st
    out_ = {}
    if p >= 1:
        out_[(n0 + 1, p - 1, m)] = (n0 + 1) * p
    if n0 >= 1:
        t = (n0 - 1, p, m + 1)
        out_[t] = out_.get(t, 0) + n0 * (m + 1)
    return out_
from fractions import Fraction
def isqrt_exact(v):
    r = isqrt(v)
    return r if r * r == v else None
# Use exact field Q(sqrt) by comparing squared elements on single-path terms and adding via a small symbolic dict.
class Surd:
    """Sum of c*sqrt(k) with integer k, reduced by exact comparison."""
    def __init__(self, terms=None):
        self.t = {}
        for k, c in (terms or {}).items():
            self.add(k, c)
    def add(self, k, c):
        if k == 0 or c == 0:
            return
        s = 1
        # square-free part
        d = 2
        kk = k
        while d * d <= kk:
            while kk % (d * d) == 0:
                kk //= d * d
                s *= d
            d += 1
        self.t[kk] = self.t.get(kk, 0) + c * s
    def clean(self):
        return {k: v for k, v in self.t.items() if v != 0}
def elements_AdagA(st):
    """(A^dag A)|st> = sum over intermediate states."""
    res = {}
    for mid, el2 in apply_A(st).items():
        # A^dag = a+^dag a0 + a0^dag a-
        n0, p, m = mid
        if n0 >= 1:
            t = (n0 - 1, p + 1, m)
            res.setdefault(t, Surd()).add(el2 * n0 * (p + 1), 1)
        if m >= 1:
            t = (n0 + 1, p, m - 1)
            res.setdefault(t, Surd()).add(el2 * (n0 + 1) * m, 1)
    return res
def elements_rhs(st):
    n0, p, m = st
    res = {}
    res.setdefault(st, Surd()).add(1, n0 * (p + m) + n0 + p)
    if n0 >= 2:
        t = (n0 - 2, p + 1, m + 1)
        res.setdefault(t, Surd()).add(n0 * (n0 - 1) * (p + 1) * (m + 1), 1)
    if p >= 1 and m >= 1:
        t = (n0 + 2, p - 1, m - 1)
        res.setdefault(t, Surd()).add((n0 + 1) * (n0 + 2) * p * m, 1)
    return res
for n in range(2, 15):
    for p in range(n + 1):
        for m in range(n + 1 - p):
            st = (n - p - m, p, m)
            l, r_ = elements_AdagA(st), elements_rhs(st)
            for t in set(l) | set(r_):
                tot += 1
                if l.get(t, Surd()).clean() != r_.get(t, Surd()).clean():
                    bad += 1
P('IDENTITY|A^dag A = n0(n+ + n-) + n0 + n+ + P + P^dag|elements checked', tot, '|mismatches', bad, '|N=2..14')
P('  so C1 = 2[<n0(n+ + n-)> + 2Re<P>]/(N(N-1)) = 2[<A^dag A> - <n0 + n+>]/(N(N-1)), and V^2 = A1^2/2C1 = ((N-1)/N)|<A>|^2/(<A^dag A> - <n0 + n+>).')

# ---- 2. Pairs as a Taylor series in t on the P = 0 chain, exact, then the coefficient of 1/N.
def chain_pairs_series(n, x, u, order):
    """Coefficients of t^k of <n+> from |N,0,0>, k <= order. Basis |j>' = P^j |N,0,0>-like with rational action."""
    x, u = F(x), F(u)
    top = n // 2
    dg = [x * 2 * j + u * F((n - 2 * j) * 2 * j + j * j, n) for j in range(top + 1)]
    # P|j>' = |j+1>'   with weight; J = 1/N. P^dag|j>' = c_j |j-1>' with c_j = j^2 (n-2j+2)(n-2j+1)
    c = [F(0)] + [F(j * j * (n - 2 * j + 2) * (n - 2 * j + 1)) for j in range(1, top + 1)]
    w = [F(1)]
    for j in range(1, top + 1):
        w.append(w[-1] * c[j])
    pn = F(1, n)
    vecs = []
    v = [F(0)] * (top + 1)
    v[0] = F(1)
    vecs.append(v)
    for k in range(order):
        nv = [F(0)] * (top + 1)
        for j, val in enumerate(v):
            if val == 0:
                continue
            nv[j] += dg[j] * val
            if j < top:
                nv[j + 1] += pn * val
            if j > 0:
                nv[j - 1] += pn * c[j] * val
        v = nv
        vecs.append(v)
    # a_j(t) = sum_k (-i t)^k/k! v_k[j]. |a_j|^2 coefficient of t^m = sum_{k+l=m} (i)^k (-i)^l /(k! l!) v_k v_l, only even |k-l| survive with real value (-1)^((k-l)/2)...
    res = []
    for m in range(order + 1):
        total = F(0)
        for k in range(m + 1):
            l = m - k
            # (-i)^l (i)^k = i^(k-l)... i^k * (-i)^l = i^(k + 3l) ; real part when k+3l even
            e = (k + 3 * l) % 4
            if e % 2:
                continue
            sign = 1 if e == 0 else -1
            s = F(0)
            for j in range(top + 1):
                if vecs[k][j] and vecs[l][j]:
                    s += j * w[j] * vecs[k][j] * vecs[l][j]
            total += sign * s / (factorial(k) * factorial(l))
        res.append(total)
    return res

def interp_in_eps(values):
    """values: list of (eps, y). Newton form; returns polynomial coefficients c0, c1, ... by exact solve."""
    pts = list(values)
    size = len(pts)
    mat = [[e ** i for i in range(size)] + [y] for e, y in pts]
    for i in range(size):
        piv = next(r for r in range(i, size) if mat[r][i] != 0)
        mat[i], mat[piv] = mat[piv], mat[i]
        mat[i] = [q / mat[i][i] for q in mat[i]]
        for r in range(size):
            if r != i and mat[r][i] != 0:
                fac = mat[r][i]
                mat[r] = [a_ - fac * b_ for a_, b_ in zip(mat[r], mat[i])]
    return [mat[i][size] for i in range(size)]

def closed_series(delta, u, order):
    """Series in t of J0 and J1 from the text's closed forms, exact, through t^order."""
    d, u = F(delta), F(u)
    g2 = 1 - d * d
    J0 = [F(0)] * (order + 1)
    J1 = [F(0)] * (order + 1)
    if g2 == 0:
        s = 1 if d > 0 else -1
        J0[2] = F(1)
        J1[2] = F(-1)
        J1[4] = -(3 - s * u)
        J1[6] = -F(2, 5) * (4 - s * 3 * u)
        return J0, J1
    # z^2 = g2 t^2
    # sinh^2 z = sum_{k>=1} 2^(2k-1) z^(2k)/(2k)!
    def sinh2(a2, k):
        """coefficient of t^(2k) in sinh^2(sqrt(a2) t)."""
        return F(2 ** (2 * k - 1), factorial(2 * k)) * a2 ** k if k >= 1 else F(0)
    # z sinh 2z = sum_{k>=0} 2^(2k+1) z^(2k+2)/(2k+1)!
    def zsinh2z(a2, k):
        """coefficient of t^(2k) in z sinh 2z, k >= 1."""
        return F(2 ** (2 * k - 1), factorial(2 * k - 1)) * a2 ** k if k >= 1 else F(0)
    for k in range(1, order // 2 + 1):
        J0[2 * k] = sinh2(g2, k) / g2
    for k in range(1, order // 2 + 4):
        term = (-(4 - 3 * d * u) * sinh2(4 * g2, k) / 4 + F(3, 2) * (1 + 3 * d * d - d * u * (2 + d * d)) * zsinh2z(g2, k) + d * (3 * u * (1 + d * d) - d * (7 + d * d)) * sinh2(g2, k))
        # divide by g2^3: the t^(2k) coefficient of the form is term / g2^3
        if 2 * k <= order:
            J1[2 * k] = term / g2 ** 3
    return J0, J1

ORDER = 16
NS = list(range(30, 50))
P('J1 check through t^%d, N in %s' % (ORDER, NS))
for delta, u in (('1/3', '1'), ('-1/5', '1/2'), ('2/3', '3/4'), ('0', '1/4'), ('3/2', '1'), ('1', '1'), ('-1', '1'), ('1', '1/2'), ('-1', '1/4')):
    d, uu = F(delta), F(u)
    x = d - uu
    series_by_n = {n: chain_pairs_series(n, x, uu, ORDER) for n in NS}
    J0, J1 = closed_series(d, uu, ORDER)
    mis0, mis1, deg_ok = 0, 0, True
    for m in range(0, ORDER + 1):
        c = interp_in_eps([(F(1, n), series_by_n[n][m]) for n in NS])
        if c[0] != J0[m]:
            mis0 += 1
        if c[1] != J1[m]:
            mis1 += 1
        if any(v != 0 for v in c[m + 1:]):
            deg_ok = False
    P(' delta', delta, 'u', u, 'J0 mismatches', mis0, 'J1 mismatches', mis1, 'polynomial in 1/N of bounded degree', deg_ok)

# ---- 3. w1 at delta = 0, u = 1, and the same machinery at delta = 1/2 for reference.
def a_linear_series(n, x, u, order):
    """Coefficient of t^k of <A>/y at first order in y, from |N,0,0>, in the basis |n0,p,m>' = a0^dag^n0 a+^dag^p a-^dag^m |vac>."""
    x, u = F(x), F(u)
    pn = F(1, n)
    states = [(p, m) for p in range(n + 1) for m in range(n + 1 - p)]
    idx = {s: i for i, s in enumerate(states)}
    def weight(p, m):
        return F(factorial(n - p - m) * factorial(p) * factorial(m))
    def H0(v):
        o = [F(0)] * len(states)
        for i, val in enumerate(v):
            if not val:
                continue
            p, m = states[i]
            n0 = n - p - m
            o[i] += (x * (p + m) + u * pn * (n0 * (p + m) + p * m)) * val
            if n0 >= 2:
                o[idx[(p + 1, m + 1)]] += pn * n0 * (n0 - 1) * val
            if p >= 1 and m >= 1:
                o[idx[(p - 1, m - 1)]] += pn * p * m * val
        return o
    def V(v):
        # H = H0 + y V, V = -(A + A^dag)
        o = [F(0)] * len(states)
        for i, val in enumerate(v):
            if not val:
                continue
            p, m = states[i]
            n0 = n - p - m
            if p >= 1:
                o[idx[(p - 1, m)]] += -p * val          # a0^dag a+
            if n0 >= 1:
                o[idx[(p, m + 1)]] += -n0 * val         # a-^dag a0
                o[idx[(p + 1, m)]] += -n0 * val         # a+^dag a0
            if m >= 1:
                o[idx[(p, m - 1)]] += -m * val          # a0^dag a-
        return o
    def Aop(v):
        o = [F(0)] * len(states)
        for i, val in enumerate(v):
            if not val:
                continue
            p, m = states[i]
            n0 = n - p - m
            if p >= 1:
                o[idx[(p - 1, m)]] += p * val
            if n0 >= 1:
                o[idx[(p, m + 1)]] += n0 * val
        return o
    W = [weight(*s) for s in states]
    norm = W[idx[(0, 0)]]
    a_ = [[F(0)] * len(states)]
    a_[0][idx[(0, 0)]] = F(1)
    b_ = [[F(0)] * len(states)]
    for k in range(order):
        na = H0(a_[-1])
        nb = [p_ + q_ for p_, q_ in zip(H0(b_[-1]), V(a_[-1]))]
        a_.append(na)
        b_.append(nb)
    Aa = [Aop(v) for v in a_]
    Ab = [Aop(v) for v in b_]
    def dot(u_, v_):
        return sum(w_ * p_ * q_ for w_, p_, q_ in zip(W, u_, v_) if p_ and q_)
    res = []
    for m_ in range(order + 1):
        total = F(0)
        for k in range(m_ + 1):
            l = m_ - k
            e = (k + 3 * l) % 4   # bra carries (+i)^k, ket (-i)^l
            if e % 2:
                continue
            sign = 1 if e == 0 else -1
            s = dot(a_[k], Ab[l]) + dot(b_[k], Aa[l])
            total += sign * s / (factorial(k) * factorial(l))
        res.append(total / norm)
    return res

def w_series(order):
    """Series in t of w0 and w1 from the text at delta = 0, u = 1."""
    w0 = [F(0)] * (order + 1)
    w1 = [F(0)] * (order + 1)
    for k in range(0, order // 2 + 1):
        ck = F(1, factorial(2 * k))
        c2k = F(2 ** (2 * k), factorial(2 * k))
        c3k = F(3 ** (2 * k), factorial(2 * k))
        if k >= 1:
            w0[2 * k] = -2 * ck
        w1[2 * k] = F(65, 12) * ck - F(11, 3) * c2k + F(5, 4) * c3k - (3 if k == 0 else 0)
        if k >= 1:
            # -t sinh t: sum_{j>=0} -t^(2j+2)/(2j+1)!
            w1[2 * k] += -F(1, factorial(2 * k - 1))
    return w0, w1

ORDER3 = 12
NS3 = list(range(14, 29))
ser = {n: a_linear_series(n, F(-1), F(1), ORDER3) for n in NS3}
w0, w1 = w_series(ORDER3)
mis0, mis1 = 0, 0
for m_ in range(ORDER3 + 1):
    c = interp_in_eps([(F(1, n), ser[n][m_] / n) for n in NS3])
    if c[0] != w0[m_]:
        mis0 += 1
    if c[1] != w1[m_]:
        mis1 += 1
P('w0, w1 at delta=0,u=1 through t^%d, N in %s: w0 mismatches' % (ORDER3, NS3), mis0, 'w1 mismatches', mis1)
P('  <A>/(N y) t^2 coefficient at N=20:', ser[20][2] / 20, ' t^4:', ser[20][4] / 20)
out.close()
