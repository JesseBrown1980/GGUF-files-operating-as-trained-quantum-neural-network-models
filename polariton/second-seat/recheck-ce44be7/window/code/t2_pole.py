# Item 2. What happens on the plane-wave branch at u - x -> 0: the block of the top R charge sectors, P >= N - R, holds the branch and its first excitations. Dense solve at K bits with partial pivoting; the level followed is the one with the largest weight on |0, N, 0>.
# Against 2/D1 and the two-level form A1/y = 2/sqrt(D1^2 + 4 N y^2), D1 = u(N-1)/N - x, and against the ground state's lowest sector at the same (u, x).
import sys
from fractions import Fraction as F
from math import isqrt
sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from sec_lib import argmin_P, K as KS, fx
from pw_lib import dec

K = 256
ONE = 1 << K


def block(N, u, x, y, R):
    states = []
    for r in range(0, R + 1):
        for m in range(0, r // 2 + 1):
            p = N - r + m
            if p >= 0 and p + m <= N:
                states.append((p, m))
    index = {s: i for i, s in enumerate(states)}
    M = [[0] * len(states) for _ in states]
    q = lambda v: (F(v).numerator << K) // F(v).denominator
    for (p, m), i in index.items():
        n0 = N - p - m
        M[i][i] += q(x * (p + m) + u * F(n0 * (p + m) + p * m, N))
        if n0 >= 2 and (p + 1, m + 1) in index:
            v = isqrt((p + 1) * (m + 1) * n0 * (n0 - 1) << (2 * K)) // N
            j = index[(p + 1, m + 1)]
            M[i][j] += v
            M[j][i] += v
        if n0 >= 1:
            for t, w in (((p + 1, m), (p + 1) * n0), ((p, m + 1), (m + 1) * n0)):
                if t in index:
                    v = -(isqrt(w << (2 * K)) * F(y).numerator) // F(y).denominator
                    j = index[t]
                    M[i][j] += v
                    M[j][i] += v
    return states, index, M


def solve_dense(M, b, sigma):
    n = len(M)
    A = [[M[i][j] - (sigma if i == j else 0) for j in range(n)] + [b[i]] for i in range(n)]
    for i in range(n):
        piv = max(range(i, n), key=lambda r: abs(A[r][i]))
        A[i], A[piv] = A[piv], A[i]
        for r in range(i + 1, n):
            if A[r][i]:
                f = (A[r][i] << K) // A[i][i]
                A[r] = [a - ((f * c) >> K) for a, c in zip(A[r], A[i])]
    x = [0] * n
    for i in range(n - 1, -1, -1):
        t = A[i][n] - sum((A[i][j] * x[j]) >> K for j in range(i + 1, n))
        x[i] = (t << K) // A[i][i]
    return x


def norm(v):
    r = isqrt(sum(a * a for a in v))
    return [(a << K) // r for a in v]


def rayleigh(M, v):
    w = [sum((a * b) >> K for a, b in zip(row, v)) for row in M]
    return sum((a * b) >> K for a, b in zip(v, w))


def branch(N, u, x, y, R):
    states, index, M = block(N, u, x, y, R)
    n = len(states)
    ref = index[(N, 0)]
    D1 = u * F(N - 1, N) - x
    root = F(isqrt(int((D1 * D1 / 4 + N * y * y) * 10 ** 40)), 10 ** 20)
    # The branch is the lower member of the two-level pair for D1 > 0, the upper for D1 < 0; try both shifts, keep the larger weight on the reference.
    best = None
    for shift in (D1 / 2 - root, D1 / 2 + root):
        sig = x * N + shift
        sig_i = (sig.numerator << K) // sig.denominator + (1 << (K - 30))
        v = [ONE if i == ref else ONE >> 6 for i in range(n)]
        for _ in range(6):
            v = norm(solve_dense(M, v, sig_i))
            sig_i = rayleigh(M, v) + (1 << (K - 120))
        w = abs(v[ref])
        if best is None or w > best[0]:
            best = (w, v, sig_i)
    w, v, th = best
    # <A>
    a_val = 0
    for (p, m), i in index.items():
        n0 = N - p - m
        if p >= 1 and (p - 1, m) in index:
            a_val += (((v[i] * v[index[(p - 1, m)]]) >> K) * isqrt((p * (n0 + 1)) << (2 * K))) >> K
        if n0 >= 1 and (p, m + 1) in index:
            a_val += (((v[i] * v[index[(p, m + 1)]]) >> K) * isqrt(((m + 1) * n0) << (2 * K))) >> K
    return F(th, ONE), F(a_val, ONE), F(w * w >> K, ONE)


for N in (81, 243):
    for u in (F(1, 2), F(1)):
        D0 = F(u) * F(N - 1, N)
        for s in (F(1), F(4)):
            y = s / N
            for k in (F(-4), F(-1), F(-1, 4), F(0), F(1, 4), F(1), F(4), F(16)):
                # D1 = k/sqrt(N) up to a rational step: x = u(N-1)/N - D1.
                rootN = F(isqrt(N * 10 ** 12), 10 ** 6)
                D1 = k / rootN
                x = D0 - D1
                th, a_val, w = branch(N, u, x, y, 12)
                a1y = 2 * abs(a_val) / N / y
                two = 2 / F(isqrt(int((D1 * D1 + 4 * N * y * y) * 10 ** 40)), 10 ** 20)
                who, best, e0 = argmin_P(N, u, F(x.numerator * (1 << 40) // x.denominator, 1 << 40), stop_bits=80)
                print("POLE|N=%d|u=%s|s=%s|D1*sqrtN=%s|x=%s|branch_weight_on_plane_wave=%s|A1/y=%s|two_level=%s|2/D1=%s|E_branch=%s|E_lowest=%s|lowest_P=%d|json=0" % (
                    N, u, s, k, dec(x, 5), dec(w, 4), dec(a1y, 4), dec(two, 4), dec(2 / D1, 4) if D1 != 0 else "pole", dec(th, 5), fx(best, 5), who))
                sys.stdout.flush()
