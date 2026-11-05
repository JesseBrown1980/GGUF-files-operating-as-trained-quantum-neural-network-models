# Even or odd block of the three-mode model under n+ <-> n-, in the normalized parity basis, at K fractional bits in Python integers.
# Banded LDL^t with no pivoting, negative-pivot count (Sylvester), inverse iteration, read-out of <A>, <B>, <P^2>.
# Own code: shares nothing with the engine or second_route.py. No float anywhere in the model arithmetic.
from fractions import Fraction as F
from math import isqrt


class Block:
    def __init__(self, N, u, x, y, parity=1, K=256, kappa=F(0)):
        self.N, self.u, self.x, self.y = N, F(u), F(x), F(y)
        self.parity, self.K = parity, K
        self.kappa = F(kappa)
        self.one = 1 << K
        self.states = []
        # Order by charge P >= 0, then by n-, so the band is about N/2.
        low = 0 if parity == 1 else 1
        for charge in range(low, N + 1):
            for m in range(0, (N - charge) // 2 + 1):
                self.states.append((m + charge, m))
        self.index = {s: i for i, s in enumerate(self.states)}
        self.size = len(self.states)
        self.diag = [0] * self.size
        self.edges = []  # (i, j, value at 2^K), i < j or kept once
        self._build()
        self.band = max([abs(i - j) for i, j, _ in self.edges] + [0])

    def q(self, r):
        r = F(r)
        return (r.numerator << self.K) // r.denominator

    def root(self, n, scale=F(1), extra2=False):
        """scale * sqrt(n [*2]) at 2^K, from an integer sqrt at 2^K."""
        scale = F(scale)
        rad = n * (2 if extra2 else 1)
        rt = isqrt(rad << (2 * self.K))
        return (rt * scale.numerator) // scale.denominator

    def _build(self):
        N, u, x, y, parity = self.N, self.u, self.x, self.y, self.parity
        index = self.index
        for s, i in index.items():
            p, m = s
            n0 = N - p - m
            self.diag[i] = self.q(x * (p + m) + u * F(n0 * (p + m) + p * m, N))
            # The pair term keeps P, and keeps the kind of orbit.
            if n0 >= 2:
                t = (p + 1, m + 1)
                self.edges.append((i, index[t], self.root((p + 1) * (m + 1) * n0 * (n0 - 1), F(1, N))))
            if y != 0 and n0 >= 1:
                # up in p: (p+1, m)
                t = (p + 1, m)
                value = self.root((p + 1) * n0, -y, extra2=(p == m))
                if t in index and s in index:
                    if not (parity == -1 and p == m):
                        self.edges.append((i, index[t], value))
                # up in m: (p, m+1)
                t = (p, m + 1)
                if p > m + 1:
                    self.edges.append((i, index[t], self.root((m + 1) * n0, -y)))
                elif p == m + 1 and parity == 1:
                    self.edges.append((i, index[t], self.root((m + 1) * n0, -y, extra2=True)))
                # p == m: the mirror of the hop above, already counted through the factor of sqrt 2. p == m + 1, odd: (p,p) is absent.
            if self.kappa != 0:
                # kappa (B + B^dag), B = a-^dag a+: (p, m) -> (p-1, m+1), element sqrt(p (m+1)).
                if p >= 1:
                    tp, tm = p - 1, m + 1
                    v = self.kappa
                    if tp > tm:
                        self.edges.append((i, index[(tp, tm)], self.root(p * (m + 1), v)))
                    elif tp == tm:
                        if parity == 1:
                            self.edges.append((i, index[(tp, tm)], self.root(p * (m + 1), v, extra2=True)))
                    else:
                        # (tp, tm) is the mirror of (tm, tp): even keeps the sign, odd flips it. p == tm, m == tp - 1 gives the self-loop.
                        mirror = (tm, tp)
                        sign = parity
                        if mirror == s:
                            self.diag[i] += sign * self.root(p * (m + 1), v)
                        else:
                            self.edges.append((i, index[mirror], sign * self.root(p * (m + 1), v)))
        # Merge duplicates and keep upper triangle.
        merged = {}
        for i, j, v in self.edges:
            a, b = (i, j) if i < j else (j, i)
            merged[(a, b)] = merged.get((a, b), 0) + v
        self.edges = [(a, b, v) for (a, b), v in merged.items() if v != 0]

    def factor(self, lam):
        """L D L^t of H - lam at 2^K. Returns negative count, plus the factors. lam is an integer at 2^K."""
        K, size, band = self.K, self.size, self.band
        d = [v - lam for v in self.diag]
        # Upper rows in band storage.
        rows = [{} for _ in range(size)]
        for i, j, v in self.edges:
            rows[i][j] = v
        neg = 0
        lrows = [None] * size
        for k in range(size):
            piv = d[k]
            if piv == 0:
                piv = 1
                d[k] = 1
            if piv < 0:
                neg += 1
            row = rows[k]
            items = sorted(row.items())
            lrow = []
            for j, v in items:
                if v == 0:
                    continue
                l = (v << K) // piv
                lrow.append((j, l))
            for idx, (j, l) in enumerate(lrow):
                v = row[j]
                # Schur complement on j and on later columns of row j.
                d[j] -= (l * v) >> K
                rj = rows[j]
                for j2, l2 in lrow[idx + 1:]:
                    # entry (j, j2) -= l * row[j2]
                    rj[j2] = rj.get(j2, 0) - ((l * row[j2]) >> K)
            lrows[k] = lrow
            rows[k] = None
        return neg, lrows, d

    def solve(self, lrows, d, b):
        K, size = self.K, self.size
        x = list(b)
        for k in range(size):
            xk = x[k]
            if xk:
                for j, l in lrows[k]:
                    x[j] -= (l * xk) >> K
        for k in range(size):
            x[k] = (x[k] << K) // d[k]
        for k in range(size - 1, -1, -1):
            t = x[k]
            for j, l in lrows[k]:
                t -= (l * x[j]) >> K
            x[k] = t
        return x

    def count_below(self, lam):
        return self.factor(lam)[0]

    def lowest(self, lo=None, hi=None, bits=None):
        """Bisection on the negative count, lowest level of the block, integer at 2^K. Stops at 2^-bits."""
        K = self.K
        bits = bits if bits is not None else K // 2
        bound = max(abs(v) for v in self.diag) + (6 * self.N + 8) * self.one
        lo = -bound if lo is None else lo
        hi = bound if hi is None else hi
        while hi - lo > (1 << max(K - bits, 0)):
            mid = (lo + hi) >> 1
            if self.count_below(mid) >= 1:
                hi = mid
            else:
                lo = mid
        return lo, hi

    def ground(self, lo=None, hi=None, bits=None, rounds=8):
        """Lowest level by coarse bisection then inverse iteration; returns (theta, vector at 2^K, residual)."""
        K = self.K
        lo, hi = self.lowest(lo, hi, bits if bits is not None else 60)
        sigma = lo - (1 << (K - 62))
        neg, lrows, d = self.factor(sigma)
        if neg != 0:
            sigma = lo - (1 << (K - 40))
            neg, lrows, d = self.factor(sigma)
        v = [(((i * 2654435761 + 12345) % 1000003) - 500001) << (K - 20) for i in range(self.size)]
        v = self.norm(v)
        theta = sigma
        for r in range(rounds):
            w = self.solve(lrows, d, v)
            w = self.norm(w)
            theta_new = self.rayleigh(w)
            done = abs(theta_new - theta) < (1 << 40) and r > 1
            v, theta = w, theta_new
            if done:
                break
        return theta, v, self.residual(v, theta)

    def apply(self, v):
        K = self.K
        out = [(a * b) >> K for a, b in zip(self.diag, v)]
        for i, j, e in self.edges:
            out[i] += (e * v[j]) >> K
            out[j] += (e * v[i]) >> K
        return out

    def rayleigh(self, v):
        K = self.K
        w = self.apply(v)
        return sum(a * b for a, b in zip(v, w)) >> K

    def residual(self, v, theta):
        K = self.K
        w = self.apply(v)
        r = 0
        for a, b in zip(w, v):
            e = a - ((theta * b) >> K)
            r = max(r, abs(e))
        return r

    def norm(self, v):
        K = self.K
        s = sum(a * a for a in v)
        r = isqrt(s)
        return [(a << K) // r for a in v]

    def expand(self, v):
        """The state on the Fock basis, as a dict (p, m) -> amplitude at 2^K."""
        K = self.K
        rt = isqrt(self.one * self.one // 2)
        out = {}
        for (p, m), c in zip(self.states, v):
            if p == m:
                out[(p, m)] = c
            else:
                a = (c * rt) >> K
                out[(p, m)] = a
                out[(m, p)] = self.parity * a
        return out

    def read(self, v):
        """<A>, <B>, <P^2>, <n+ + n->, <n+ n-> on the expanded state, as integers at 2^K."""
        K, N = self.K, self.N
        psi = self.expand(v)
        a_val, b_val, p2, pairs, npnm = 0, 0, 0, 0, 0
        for (p, m), c in psi.items():
            n0 = N - p - m
            w = (c * c) >> K
            p2 += w * (p - m) * (p - m)
            pairs += w * (p + m)
            npnm += w * p * m
            if p >= 1:
                t = psi.get((p - 1, m))
                if t is not None:
                    a_val += (((c * t) >> K) * isqrt(p * (n0 + 1) << (2 * K))) >> K
                t = psi.get((p - 1, m + 1))
                if t is not None:
                    b_val += (((c * t) >> K) * isqrt(p * (m + 1) << (2 * K))) >> K
            if n0 >= 1:
                t = psi.get((p, m + 1))
                if t is not None:
                    a_val += (((c * t) >> K) * isqrt(n0 * (m + 1) << (2 * K))) >> K
        return a_val, b_val, p2, pairs, npnm

    def frac(self, v):
        return F(v, self.one)


def dec(q, digits=9):
    q = F(q)
    sign = "-" if q < 0 else ""
    q = abs(q)
    scaled = (q.numerator * 10 ** digits) // q.denominator
    return "%s%d.%0*d" % (sign, scaled // 10 ** digits, digits, scaled % 10 ** digits)
