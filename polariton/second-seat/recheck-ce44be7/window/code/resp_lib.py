# The exact y -> 0 response of the P = 0 branch, on the chains P = 0, 1, 2, at K fractional bits in Python integers.
# ground chain P=0: psi0, E0. psi1 = (H1 - E0)^-1 U psi0, psi2 = (H2 - E0)^-1 U psi1, with U = a+^dag a0 + a0^dag a- raising P by one.
# <A>/y = 2 <psi1|U|psi0>, <B>/y^2 = 2 sum sqrt((j+2)(j+1)) psi2(j) psi0(j+1) + sum (j+1) psi1(j)^2.
# Own code. No float.
from fractions import Fraction as F
from math import isqrt


class Chains:
    def __init__(self, N, u, x, K=400):
        self.N, self.u, self.x, self.K = N, F(u), F(x), K
        self.one = 1 << K
        self.ch = {}

    def q(self, r):
        r = F(r)
        return (r.numerator << self.K) // r.denominator

    def chain(self, P):
        if P in self.ch:
            return self.ch[P]
        N, u, x, K = self.N, self.u, self.x, self.K
        top = (N - P) // 2
        un, ud, xn, xd = u.numerator, u.denominator, x.numerator, x.denominator
        den = ud * xd * N
        d, o = [], []
        for j in range(top + 1):
            n0 = N - 2 * j - P
            s = 2 * j + P
            d.append(((xn * s * ud * N + un * (n0 * s + (j + P) * j) * xd) << K) // den)
            if j < top:
                # sqrt((j+P+1)(j+1) n0 (n0-1))/N at 2^K
                o.append(isqrt(((j + P + 1) * (j + 1) * n0 * (n0 - 1)) << (2 * K)) // N)
        self.ch[P] = (d, o)
        return d, o

    def factor(self, P, sigma):
        d, o = self.chain(P)
        K = self.K
        n = len(d)
        piv = [0] * n
        l = [0] * (n - 1)
        piv[0] = d[0] - sigma
        neg = 1 if piv[0] < 0 else 0
        for i in range(1, n):
            l[i - 1] = (o[i - 1] << K) // piv[i - 1]
            piv[i] = d[i] - sigma - ((l[i - 1] * o[i - 1]) >> K)
            if piv[i] < 0:
                neg += 1
        return piv, l, neg

    def solve(self, piv, l, b):
        K = self.K
        n = len(piv)
        x = list(b)
        for i in range(1, n):
            x[i] -= (l[i - 1] * x[i - 1]) >> K
        for i in range(n):
            x[i] = (x[i] << K) // piv[i]
        for i in range(n - 2, -1, -1):
            x[i] -= (l[i] * x[i + 1]) >> K
        return x

    def norm(self, v):
        K = self.K
        r = isqrt(sum(a * a for a in v))
        return [(a << K) // r for a in v]

    def rayleigh(self, P, v):
        d, o = self.chain(P)
        K = self.K
        t = 0
        for i in range(len(d)):
            t += (((d[i] * v[i]) >> K) * v[i]) >> K
        for i in range(len(o)):
            t += 2 * ((((o[i] * v[i]) >> K) * v[i + 1]) >> K)
        return t

    def ground(self, P):
        d, o = self.chain(P)
        K = self.K
        n = len(d)
        # Bisection on pivots to about 2^-60, then Rayleigh quotient iteration from below.
        lo = min(d) - 2 * max(o + [0]) - self.one
        hi = min(d) + self.one
        while hi - lo > (1 << (K - 64)):
            mid = (lo + hi) >> 1
            if self.factor(P, mid)[2] >= 1:
                hi = mid
            else:
                lo = mid
        sigma = lo - (1 << (K - 62))
        v = self.norm([(((-1) ** i) * self.one) for i in range(n)])
        theta = sigma
        for r in range(12):
            piv, l, neg = self.factor(P, sigma)
            w = self.norm(self.solve(piv, l, v))
            th = self.rayleigh(P, w)
            v = w
            if abs(th - theta) < (1 << (K // 3)) and r > 2:
                theta = th
                break
            theta = th
            sigma = th - (1 << (K // 2))
        # One more step at a tight shift, so the vector matches the level to about 2^-(K/2).
        piv, l, neg = self.factor(P, theta - (1 << (K // 2)))
        v = self.norm(self.solve(piv, l, v))
        theta = self.rayleigh(P, v)
        return theta, v

    def raise_U(self, P, v):
        """U = a+^dag a0 + a0^dag a- from chain P into chain P + 1."""
        N, K = self.N, self.K
        size = (N - P - 1) // 2 + 1
        out = [0] * size
        for j, c in enumerate(v):
            n0 = N - 2 * j - P
            if n0 >= 1 and j < size:
                out[j] += (c * isqrt(((j + P + 1) * n0) << (2 * K))) >> K
            if j >= 1 and j - 1 < size:
                out[j - 1] += (c * isqrt((j * (n0 + 1)) << (2 * K))) >> K
        return out

    def dot(self, a, b):
        return sum(p * q for p, q in zip(a, b)) >> self.K

    def response(self):
        K = self.K
        e0, p0 = self.ground(0)
        e1, q1 = self.ground(1)
        e2, q2 = self.ground(2)
        u0 = self.raise_U(0, p0)
        piv, l, neg1 = self.factor(1, e0)
        psi1 = self.solve(piv, l, u0)
        s1 = self.dot(u0, psi1)
        u1 = self.raise_U(1, psi1)
        piv, l, neg2 = self.factor(2, e0)
        psi2 = self.solve(piv, l, u1)
        t = 0
        for j, c in enumerate(psi2):
            if j + 1 < len(p0):
                t += (((c * p0[j + 1]) >> K) * isqrt(((j + 2) * (j + 1)) << (2 * K))) >> K
        s = 0
        for j, c in enumerate(psi1):
            s += ((c * c) >> K) * (j + 1)
        b2 = 2 * t + s
        # Ground-chain moments, for the 1/N theory.
        return dict(e0=e0, e1=e1, e2=e2, s1=s1, b2=b2, t=t, s=s, neg1=neg1, neg2=neg2)


def constants(u, x):
    u, x = F(u), F(x)
    delta = u + x
    rho = (1 - delta) / (4 - 3 * u)
    rho0 = 1 - 2 * rho
    c0 = (rho0 / rho - u) / 4
    return delta, rho, rho0, c0


def rotor_chi_d(N, u, x):
    delta, rho, rho0, c0 = constants(u, x)
    return rho * F(u) * N * N / (16 * c0 * c0)


def rotor_chi_a(u, x):
    delta, rho, rho0, c0 = constants(u, x)
    return 2 * (1 + F(u) / (8 * c0))


def dec(v, digits=9):
    f = F(v)
    sign = "-" if f < 0 else ""
    f = abs(f)
    scaled = (f.numerator * 10 ** digits) // f.denominator
    return "%s%d.%0*d" % (sign, scaled // 10 ** digits, digits, scaled % 10 ** digits)
