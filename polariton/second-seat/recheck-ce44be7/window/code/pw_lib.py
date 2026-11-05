# One plane wave |n0=0, n+=N, n-=0> as the reference. Rayleigh-Schrodinger series in y with exact rationals,
# in the monomial basis a0^dag^n0 a+^dag^p a-^dag^m |vac>, where every operator acts rationally.
# H = x(n+ + n-) + (u/N)[n0(n+ + n-) + n+ n-] + (1/N)(P + P^dag) - y[a0^dag(a+ + a-) + h.c.], P = a+^dag a-^dag a0 a0.
# Written from the Hamiltonian in polariton/README.md; shares no code with the engine or second_route.py.
from fractions import Fraction as F
from math import factorial


def diag(N, u, x, p, m):
    n0 = N - p - m
    return x * (p + m) + u * F(n0 * (p + m) + p * m, N)


def apply_pair(N, vec):
    """(P + P^dag)/N in the monomial basis."""
    out = {}
    for (p, m), c in vec.items():
        n0 = N - p - m
        if n0 >= 2:
            k = (p + 1, m + 1)
            out[k] = out.get(k, F(0)) + c * F(n0 * (n0 - 1), N)
        if p >= 1 and m >= 1:
            k = (p - 1, m - 1)
            out[k] = out.get(k, F(0)) + c * F(p * m, N)
    return out


def apply_v(N, vec):
    """V = -[a0^dag a+ + a0^dag a- + a+^dag a0 + a-^dag a0], the coefficient of y."""
    out = {}
    for (p, m), c in vec.items():
        n0 = N - p - m
        if p >= 1:
            k = (p - 1, m)
            out[k] = out.get(k, F(0)) - c * p
        if m >= 1:
            k = (p, m - 1)
            out[k] = out.get(k, F(0)) - c * m
        if n0 >= 1:
            k = (p + 1, m)
            out[k] = out.get(k, F(0)) - c * n0
            k = (p, m + 1)
            out[k] = out.get(k, F(0)) - c * n0
    return out


def apply_A(N, vec):
    """A = a0^dag a+ + a-^dag a0 acting to the right."""
    out = {}
    for (p, m), c in vec.items():
        n0 = N - p - m
        if p >= 1:
            k = (p - 1, m)
            out[k] = out.get(k, F(0)) + c * p
        if n0 >= 1:
            k = (p, m + 1)
            out[k] = out.get(k, F(0)) + c * n0
    return out


def apply_B(N, vec):
    """B = a-^dag a+."""
    out = {}
    for (p, m), c in vec.items():
        if p >= 1:
            k = (p - 1, m + 1)
            out[k] = out.get(k, F(0)) + c * p
    return out


def solve_dense(M, b):
    n = len(M)
    A = [list(r) + [v] for r, v in zip(M, b)]
    for i in range(n):
        piv = next((r for r in range(i, n) if A[r][i] != 0), None)
        if piv is None:
            raise ZeroDivisionError("singular block")
        A[i], A[piv] = A[piv], A[i]
        for r in range(n):
            if r != i and A[r][i] != 0:
                f = A[r][i] / A[i][i]
                A[r] = [a - f * c for a, c in zip(A[r], A[i])]
    return [A[i][n] / A[i][i] for i in range(n)]


class Series:
    """psi = sum y^k psi[k], E = sum y^k E[k], from the reference |0, N, 0>, intermediate normalization."""

    def __init__(self, N, u, x, order):
        if order >= 2 * N:
            raise ValueError("order must stay below 2N, where the mirror plane wave enters")
        self.N, self.u, self.x, self.order = N, F(u), F(x), order
        self.ref = (N, 0)
        self.E0 = diag(N, self.u, self.x, N, 0)
        self.E = [self.E0]
        self.psi = [{self.ref: F(1)}]
        for k in range(1, order + 1):
            rhs = {}
            v = apply_v(N, self.psi[k - 1])
            for s, c in v.items():
                rhs[s] = rhs.get(s, F(0)) - c
            ek = v.get(self.ref, F(0))
            self.E.append(ek)
            for j in range(1, k + 1):
                if self.E[j] != 0:
                    for s, c in self.psi[k - j].items():
                        rhs[s] = rhs.get(s, F(0)) + self.E[j] * c
            rhs.pop(self.ref, None)
            self.psi.append(self._solve(rhs))

    def _solve(self, rhs):
        # Sector by sector in P = p - m. H0 in the monomial basis is not symmetric, and it is rational.
        N, u, x = self.N, self.u, self.x
        sectors = {}
        for s, c in rhs.items():
            if c != 0:
                sectors.setdefault(s[0] - s[1], []).append(s)
        out = {}
        for charge, _ in sectors.items():
            r = N - charge
            states = []
            for m in range(0, N + 1):
                p = m + charge
                if p < 0 or m < 0 or p + m > N:
                    continue
                states.append((p, m))
            index = {s: i for i, s in enumerate(states)}
            size = len(states)
            M = [[F(0)] * size for _ in range(size)]
            for s, i in index.items():
                M[i][i] += diag(N, u, x, s[0], s[1]) - self.E0
                for t, c in apply_pair(N, {s: F(1)}).items():
                    M[index[t]][i] += c
            b = [rhs.get(s, F(0)) for s in states]
            sol = solve_dense(M, b)
            for s, c in zip(states, sol):
                if c != 0:
                    out[s] = c
        return out

    def weight(self, s):
        p, m = s
        return F(factorial(self.N - p - m) * factorial(p) * factorial(m), factorial(self.N))

    def inner(self, a, b):
        total = F(0)
        for s, c in a.items():
            if s in b:
                total += self.weight(s) * c * b[s]
        return total

    def expect(self, op):
        """<psi|O|psi>/<psi|psi> as a list of coefficients of y^k, k <= order. op(vec) is the operator on a vector."""
        size = self.order + 1
        images = [op(self.psi[k]) for k in range(size)]
        num = [F(0)] * size
        den = [F(0)] * size
        for i in range(size):
            for j in range(size - i):
                num[i + j] += self.inner(self.psi[i], images[j])
                den[i + j] += self.inner(self.psi[i], self.psi[j])
        out = [F(0)] * size
        for k in range(size):
            t = num[k]
            for j in range(1, k + 1):
                t -= den[j] * out[k - j]
            out[k] = t / den[0]
        return out

    def A(self):
        return self.expect(lambda v: apply_A(self.N, v))

    def B(self):
        return self.expect(lambda v: apply_B(self.N, v))

    def charge2(self):
        return self.expect(lambda v: {s: c * (s[0] - s[1]) ** 2 for s, c in v.items()})


def closed_A1(N, u, x):
    """<A>/y at first order, exact in N: N/D1, D1 = u(N-1)/N - x."""
    return F(N) / (F(u) * F(N - 1, N) - F(x))


def closed_B2(N, u, x):
    """<B>/y^2 at second order, exact in N and exact in the pair term:
    N [a - 2(N-1)/N] / (D1 (a b - kappa^2)), a = 2(u(N-2)/N - x), b = u(N-1)/N, D1 = b - x, kappa^2 = 2(N-1)/N^2."""
    u, x = F(u), F(x)
    a = 2 * (u * F(N - 2, N) - x)
    b = u * F(N - 1, N)
    d1 = b - x
    k2 = F(2 * (N - 1), N * N)
    return N * (a - 2 * F(N - 1, N)) / (d1 * (a * b - k2))


def closed_E2(N, u, x):
    return -F(N) / (F(u) * F(N - 1, N) - F(x))


def evaluate(coeffs, y):
    total = F(0)
    power = F(1)
    for c in coeffs:
        total += c * power
        power *= y
    return total


def dec(q, digits=9):
    q = F(q)
    sign = "-" if q < 0 else ""
    q = abs(q)
    scaled = (q.numerator * 10 ** digits) // q.denominator
    return "%s%d.%0*d" % (sign, scaled // 10 ** digits, digits, scaled % 10 ** digits)
