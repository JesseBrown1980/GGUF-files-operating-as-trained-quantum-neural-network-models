# Item 3. A denser search for any 1 < P < N as the lowest sector. Every N <= 24, on a grid of step 1/64 in u and x, and on the exact crossing of the end branches.
import sys
from fractions import Fraction as F
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from sec_lib import argmin_P, K, fx, chain, ground_level

US = [F(k, 64) for k in range(0, 97)]
XS = [F(k, 64) for k in range(-192, 33)]
total = 0
hits = {}
for N in range(2, 25):
    for u in US:
        for x in XS:
            who, best, e0 = argmin_P(N, u, x, stop_bits=70)
            total += 1
            hits.setdefault((N, who if who in (0, 1, N) else "other"), 0)
            hits[(N, who if who in (0, 1, N) else "other")] += 1
            if who not in (0, 1, N):
                print("OTHER_P|N=%d|u=%s|x=%s|P=%d|E=%s|json=0" % (N, u, x, who, fx(best, 9)))
    print("DENSE|N=%d|P0=%d|P1=%d|PN=%d|other=%d|json=0" % (N, hits.get((N, 0), 0), hits.get((N, 1), 0), hits.get((N, N), 0), hits.get((N, "other"), 0)))
    sys.stdout.flush()


def level(N, u, x, P):
    d, o2 = chain(N, u, x, P)
    return ground_level(d, o2, stop=1 << (K - 100))


# On the crossing in u of the low branch and the plane wave, at fixed x: every other P.
print("# at the exact crossing in u of min(P=0, P=1) with P = N, at fixed x: the lowest other P above it")
for N in (5, 6, 7, 8, 9, 10, 11, 12, 15, 16, 21, 22, 27, 28, 40, 41, 81, 82, 121, 122):
    for x in (F(-1, 8), F(-1, 4), F(-3, 8), F(-1, 2), F(-3, 4), F(-1), F(-5, 4), F(-2), F(-3), F(-5)):
        # bracket in u
        lo, hi = F(0), F(3, 2)
        def low_minus_plane(u):
            return min(level(N, u, x, 0), level(N, u, x, 1)) - (x * N).numerator * (1 << K) // (x * N).denominator
        if low_minus_plane(lo) >= 0 or low_minus_plane(hi) <= 0:
            print("CROSS_U|N=%d|x=%s|no_crossing_in_0..3/2|json=0" % (N, x))
            continue
        for _ in range(70):
            mid = (lo + hi) / 2
            if low_minus_plane(mid) < 0:
                lo = mid
            else:
                hi = mid
        u = (lo + hi) / 2
        ref = level(N, u, x, N)
        best = None
        for P in range(2, N):
            e = level(N, u, x, P)
            if best is None or e < best[0]:
                best = (e, P)
        margin = best[0] - ref if best else 0
        print("CROSS_U|N=%d|x=%s|u_cross=%s|N*u*(u-x)=%s|lowest_other_P=%s|its_margin_above=%s|json=0" % (N, x, fx(u.numerator * (1 << K) // u.denominator, 6), fx(((N * u * (u - x)).numerator << K) // (N * u * (u - x)).denominator, 4), best[1] if best else "-", fx(margin, 6)))
    sys.stdout.flush()
