# Item 5. Even against odd on the inside points of the window, where the second seat's parity test at 8dfa11a had no rows. Same reduced basis as t4_reduced, odd block: no P = 0, no sqrt 2.
import sys
from fractions import Fraction as F
from math import isqrt
sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from t4_reduced import build, solve_reduced, K, ONE
from resp_lib import constants, dec


def reduced_level(N, lv, Um, y, Pmax, parity):
    low = 0 if parity == 1 else 1
    index = {}
    states = []
    for P in range(low, Pmax + 1):
        for k in range(len(lv[P])):
            index[(P, k)] = len(states)
            states.append((P, k))
    size = len(states)
    yq = (F(y).numerator << K) // F(y).denominator
    root2 = isqrt(2 << (2 * K))
    diag = [lv[P][k][0] for (P, k) in states]
    upper = [{} for _ in range(size)]
    for P in range(low, Pmax):
        for (k2, k), m in Um[P].items():
            v = -((yq * m) >> K)
            if P == 0:
                v = (v * root2) >> K
            upper[index[(P, k)]][index[(P + 1, k2)]] = v

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
        return neg

    lo = min(diag) - abs(yq) * (6 * N + 8) - ONE
    hi = min(diag) + ONE
    while hi - lo > (1 << (K - 90)):
        mid = (lo + hi) >> 1
        if factor(mid) >= 1:
            hi = mid
        else:
            lo = mid
    return (lo + hi) >> 1


POINTS = [("1/4", "-1/4"), ("1/4", "0"), ("3/4", "0"), ("3/4", "1/8"), ("1/2", "1/4")]
for us, xs in POINTS:
    u, x = F(us), F(xs)
    delta, rho, rho0, c0 = constants(u, x)
    g = isqrt(((rho0 / rho).numerator << 80) // (rho0 / rho).denominator)
    lam = 16 * F(g, 1 << 40) / (2 * c0)
    Pmax = int(2 * lam) + 24
    for N in (81, 243, 729):
        L = 10 if N <= 243 else 8
        top = min(Pmax, N)
        c, lv, Um, Bm, B1 = build(N, u, x, top, L)
        for s in (F(1, 2), F(1), F(2), F(4), F(8), F(16)):
            y = s / N
            ee = reduced_level(N, lv, Um, y, top, 1)
            eo = reduced_level(N, lv, Um, y, top, -1)
            print("INSIDE_PARITY|N=%d|u=%s|x=%s|s=%s|E_even=%s|E_odd-E_even=%s|lower=%s|json=0" % (N, us, xs, s, dec(F(ee, ONE), 9), dec(F(eo - ee, ONE), 12), "even" if eo > ee else "odd"))
            sys.stdout.flush()
