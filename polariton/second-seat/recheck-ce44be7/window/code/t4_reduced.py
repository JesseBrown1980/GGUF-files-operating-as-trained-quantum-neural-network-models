# Item 4, at finite s. A reduced even basis of the lowest L chain levels of each charge P <= Pmax, read at fixed yN = s against 2 rho f(q) as N grows, to N beyond the engine's reach.
# Integers at K bits. Own code. Checks itself against the receipt's rows at N = 243, 729.
import sys
from fractions import Fraction as F
from math import isqrt
sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from resp_lib import Chains, constants, dec

K = 200
ONE = 1 << K


def mathieu_f(q, M=120):
    """f(q) = -<cos 2 alpha> in the ground state of -d^2/dalpha^2 + 2 q cos 2 alpha on even P, tridiagonal in P = 2k, k >= 0, with sqrt2 on the first link."""
    q = F(q)
    root2 = isqrt(2 << (2 * K))
    qi = (q.numerator << K) // q.denominator
    d = [(4 * k * k) << K for k in range(M)]
    o = [(qi * root2) >> K] + [qi] * (M - 2)
    # Lowest level by bisection, vector by inverse iteration.
    lo, hi = -(2 * qi + ONE), ONE

    def count(lam):
        # A zero pivot counts as negative. An earlier version of this reader did not count it, the same fault the engine's first run had, and read f(1) 2.6 ppm low.
        p = d[0] - lam
        if p == 0:
            p = -1
        c = 1 if p < 0 else 0
        for i in range(1, M):
            p = d[i] - lam - ((o[i - 1] * o[i - 1]) >> K << K) // p
            if p == 0:
                p = -1
            if p < 0:
                c += 1
        return c

    while hi - lo > (1 << (K - 100)):
        mid = (lo + hi) >> 1
        if count(mid) >= 1:
            hi = mid
        else:
            lo = mid
    sigma = lo - (1 << (K - 96))
    piv = [0] * M
    l = [0] * (M - 1)
    piv[0] = d[0] - sigma
    for i in range(1, M):
        l[i - 1] = (o[i - 1] << K) // piv[i - 1]
        piv[i] = d[i] - sigma - ((l[i - 1] * o[i - 1]) >> K)
    v = [ONE] * M
    for _ in range(6):
        x = list(v)
        for i in range(1, M):
            x[i] -= (l[i - 1] * x[i - 1]) >> K
        for i in range(M):
            x[i] = (x[i] << K) // piv[i]
        for i in range(M - 2, -1, -1):
            x[i] -= (l[i] * x[i + 1]) >> K
        r = isqrt(sum(a * a for a in x))
        v = [(a << K) // r for a in x]
    # <cos 2 alpha> = sum over the links of the amplitude product, with sqrt2 on the first.
    t = (((v[0] * v[1]) >> K) * root2) >> K
    for i in range(1, M - 1):
        t += (v[i] * v[i + 1]) >> K
    return F(-t, ONE) * -1 if False else F(abs(t), ONE)


class Levels(Chains):
    def levels(self, P, L, omega_guess):
        d, o = self.chain(P)
        n = len(d)
        L = min(L, n)
        out = []
        last = None
        for k in range(L):
            if k == 0:
                theta, v = self.ground_fast(P)
            else:
                theta, v = self.next_level(P, out, last, omega_guess)
            out.append((theta, v))
            last = theta
        return out

    def ground_fast(self, P):
        d, o = self.chain(P)
        K_ = self.K
        lo = min(d) - 2 * max(o + [0]) - self.one
        hi = min(d) + self.one
        while hi - lo > (1 << (K_ - 48)):
            mid = (lo + hi) >> 1
            if self.factor(P, mid)[2] >= 1:
                hi = mid
            else:
                lo = mid
        sigma = lo - (1 << (K_ - 46))
        n = len(d)
        v = self.norm([((-1) ** i) * self.one for i in range(n)])
        return self.rqi(P, v, sigma, [])

    def rqi(self, P, v, sigma, previous):
        K_ = self.K
        theta = sigma
        for r in range(10):
            piv, l, neg = self.factor(P, sigma)
            w = self.solve(piv, l, v)
            w = self.orth(w, previous)
            w = self.norm(w)
            th = self.rayleigh(P, w)
            v = w
            good = abs(th - theta) < (1 << (K_ // 2))
            theta = th
            if good and r >= 2:
                break
            sigma = th - (1 << (K_ - 120))
        return theta, v

    def orth(self, w, previous):
        K_ = self.K
        for _, p in previous:
            c = sum(a * b for a, b in zip(w, p)) >> K_
            w = [a - ((c * b) >> K_) for a, b in zip(w, p)]
        return w

    def next_level(self, P, previous, last, omega_guess):
        d, o = self.chain(P)
        K_ = self.K
        index = len(previous)
        # Bracket the level by the pivot count, starting from the last level plus a guess of the spacing.
        lo = last + (1 << (K_ - 30))
        step = omega_guess
        hi = lo + step
        while self.factor(P, hi)[2] <= index:
            hi += step
        while hi - lo > (1 << (K_ - 30)):
            mid = (lo + hi) >> 1
            if self.factor(P, mid)[2] > index:
                hi = mid
            else:
                lo = mid
        n = len(d)
        # Start from the last vector times (j - <j>), a ladder step. A periodic pattern has an exponentially small overlap with these levels once the width in j passes about 30, and at N = 6561 it sent the iteration to a far level.
        prev = previous[-1][1]
        mean = sum(((a * a) >> K_) * j for j, a in enumerate(prev)) >> K_
        v = [(a * (j - mean)) for j, a in enumerate(prev)]
        return self.rqi(P, self.norm(self.orth(v, previous)), lo, previous)


def build(N, u, x, Pmax, L):
    c = Levels(N, u, x, K)
    delta, rho, rho0, c0 = constants(u, x)
    a = 4 - 3 * F(u)
    w2 = 4 * a * rho * rho0
    omega_guess = (isqrt((w2.numerator << (2 * K)) // w2.denominator)) // 1
    lv = {}
    for P in range(0, Pmax + 1):
        lv[P] = c.levels(P, L, omega_guess)
    # <P+1,k'|U|P,k> and the B elements.
    Um = {}
    for P in range(0, Pmax):
        table = {}
        for k, (_, v) in enumerate(lv[P]):
            up = c.raise_U(P, v)
            for k2, (_, w) in enumerate(lv[P + 1]):
                table[(k2, k)] = c.dot(up, w)
        Um[P] = table
    Bm = {}
    for P in range(0, Pmax - 1):
        # B from chain P + 2, index j, to chain P, index j + 1, with sqrt((j+P+2)(j+1)).
        table = {}
        for k2, (_, w) in enumerate(lv[P + 2]):
            image = [0] * len(lv[P][0][1])
            for j, a in enumerate(w):
                if j + 1 < len(image):
                    image[j + 1] += (a * isqrt(((j + P + 2) * (j + 1)) << (2 * K))) >> K
            for k, (_, v) in enumerate(lv[P]):
                table[(k, k2)] = c.dot(image, v)
        Bm[P] = table
    # B from chain +1, index j, to chain -1, index j, with (j+1).
    B1 = {}
    for k2, (_, w) in enumerate(lv[1]):
        image = [a * (j + 1) for j, a in enumerate(w)]
        for k, (_, v) in enumerate(lv[1]):
            B1[(k, k2)] = c.dot(image, v)
    return c, lv, Um, Bm, B1


def solve_reduced(N, lv, Um, Bm, B1, y, Pmax, L):
    """Lowest level of the reduced even matrix, by Rayleigh quotient iteration from a pivot-counted bracket."""
    index = {}
    states = []
    for P in range(0, Pmax + 1):
        for k in range(len(lv[P])):
            index[(P, k)] = len(states)
            states.append((P, k))
    size = len(states)
    yq = (F(y).numerator << K) // F(y).denominator
    root2 = isqrt(2 << (2 * K))
    diag = [lv[P][k][0] for (P, k) in states]
    upper = [{} for _ in range(size)]
    for P in range(0, Pmax):
        for (k2, k), m in Um[P].items():
            v = -((yq * m) >> K)
            if P == 0:
                v = (v * root2) >> K
            a, b = index[(P, k)], index[(P + 1, k2)]
            upper[a][b] = v

    def factor(lam):
        d = [v - lam for v in diag]
        rows = [dict(r) for r in upper]
        neg = 0
        lrows = [None] * size
        for k in range(size):
            piv = d[k] if d[k] != 0 else 1
            d[k] = piv
            if piv < 0:
                neg += 1
            row = rows[k]
            lrow = sorted((j, (v << K) // piv) for j, v in row.items() if v != 0)
            for i, (j, l) in enumerate(lrow):
                d[j] -= (l * row[j]) >> K
                rj = rows[j]
                for j2, l2 in lrow[i + 1:]:
                    rj[j2] = rj.get(j2, 0) - ((l * row[j2]) >> K)
            lrows[k] = lrow
            rows[k] = None
        return neg, lrows, d

    def apply_solve(lrows, d, b):
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

    def rayleigh(v):
        t = 0
        for i in range(size):
            t += (((diag[i] * v[i]) >> K) * v[i]) >> K
            for j, e in upper[i].items():
                t += 2 * (((e * v[i]) >> K) * v[j] >> K)
        return t

    def norm(v):
        r = isqrt(sum(a * a for a in v))
        return [(a << K) // r for a in v]

    lo = min(diag) - (((abs(yq) * (6 * N + 8))) ) - ONE
    hi = lv[0][0][0] + ONE
    while hi - lo > (1 << (K - 44)):
        mid = (lo + hi) >> 1
        if factor(mid)[0] >= 1:
            hi = mid
        else:
            lo = mid
    sigma = lo - (1 << (K - 42))
    v = norm([ONE if st[1] == 0 else ONE >> 8 for st in states])
    theta = sigma
    for r in range(10):
        neg, lrows, d = factor(sigma)
        w = norm(apply_solve(lrows, d, v))
        th = rayleigh(w)
        v = w
        good = abs(th - theta) < (1 << (K // 2))
        theta = th
        if good and r >= 2:
            break
        sigma = th - (1 << (K - 110))
    # Read <A> and <B> on the even state.
    a_val = 0
    for P in range(0, Pmax):
        for (k2, k), m in Um[P].items():
            t = (((v[index[(P, k)]] * v[index[(P + 1, k2)]]) >> K) * m) >> K
            if P == 0:
                t = (t * root2) >> K
            a_val += t
    b_val = 0
    for P in range(0, Pmax - 1):
        for (k, k2), m in Bm[P].items():
            t = (((v[index[(P, k)]] * v[index[(P + 2, k2)]]) >> K) * m) >> K
            if P == 0:
                t = (t * root2) >> K
            b_val += t
    for (k, k2), m in B1.items():
        t = (((v[index[(1, k)]] * v[index[(1, k2)]]) >> K) * m) >> K
        b_val += t >> 1
    return theta, a_val, b_val, sum((((c * c) >> K) for c in v[-len(lv[Pmax]):])), v


def receipt_row(N, us, xs, s):
    for line in open("C:/tmp/qnn-polariton-wt/polariton/RECEIPT.hbp", encoding="utf-8").read().splitlines():
        if line.startswith("POLARITON_PIN_WINDOW|") and ("|N=%d|" % N) in line and ("|u=%s|" % us) in line and ("|x=%s|" % xs) in line and ("|s=%s|" % s) in line:
            return dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f)
    return None


if __name__ == "__main__":
    POINTS = [("1/4", "-1/4"), ("1/4", "0"), ("3/4", "0"), ("3/4", "1/8"), ("1/2", "1/4")]
    NS = [int(a) for a in sys.argv[1].split(",")]
    SS = [F(a) for a in sys.argv[2].split(",")]
    only = sys.argv[3].split(";") if len(sys.argv) > 3 else None
    for us, xs in POINTS:
        if only and ("%s,%s" % (us, xs)) not in only:
            continue
        u, x = F(us), F(xs)
        delta, rho, rho0, c0 = constants(u, x)
        g = isqrt(((rho0 / rho).numerator << 80) // (rho0 / rho).denominator)
        lam = max(SS) * F(g, 1 << 40) / (2 * c0)
        Pmax = int(2 * lam) + 24
        for N in NS:
            L = 10 if N <= 243 else (8 if N <= 729 else 6)
            P_top = min(Pmax, N)
            c, lv, Um, Bm, B1 = build(N, u, x, P_top, L)
            for s in SS:
                y = s / N
                theta, a_val, b_val, tail, v = solve_reduced(N, lv, Um, Bm, B1, y, P_top, L)
                q = s * s * u / (16 * c0 * c0)
                f = mathieu_f(q)
                d2 = 2 * abs(F(b_val, ONE)) / N
                a1y = 2 * abs(F(a_val, ONE)) / N / y
                ratio = d2 / (2 * rho * f)
                want_a = 2 * (1 + (u / (8 * c0)) * (1 + f))
                ra = a1y / want_a
                rr = receipt_row(N, us, xs, str(s)) if N in (81, 243, 729) else None
                check = ""
                if rr is not None:
                    check = "|receipt_E_off=%s|receipt_A_off=%s|receipt_B_off=%s" % (dec(F(theta, ONE) - F(int(rr["energy_ppb"]), 10 ** 9), 9), dec(F(a_val, ONE) - F(int(rr["A_ppb"]), 10 ** 9), 9), dec(F(b_val, ONE) - F(int(rr["B_ppb"]), 10 ** 9), 9))
                print("REDUCED|u=%s|x=%s|N=%d|s=%s|Pmax=%d|L=%d|q=%s|f=%s|D2=%s|D2_ratio=%s|N(D2_ratio-1)=%s|A1/y=%s|A1_ratio=%s|N(A1_ratio-1)=%s|B_sign=%s|top_block_weight=%s%s|json=0" % (
                    us, xs, N, s, P_top, L, dec(q, 6), dec(f, 8), dec(d2, 8), dec(ratio, 6), dec(N * (ratio - 1), 4), dec(a1y, 6), dec(ra, 6), dec(N * (ra - 1), 4), "-" if b_val < 0 else "+", dec(F(tail, ONE), 12), check))
                sys.stdout.flush()
