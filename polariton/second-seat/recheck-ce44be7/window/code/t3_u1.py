# Item 3. u = 1 across all x, by exact levels over all P: who is lowest, and the pair fraction on P = 0, from the slope of the chain level in x.
# Then the c0 = 0 edge and the rho0 = 0 edge read on exact chains, for several u.
import sys
from fractions import Fraction as F
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from sec_lib import argmin_P, chain, ground_level, K, fx, dec


def level(N, u, x, P):
    d, o2 = chain(N, u, x, P)
    return F(ground_level(d, o2, stop=1 << (K - 110)), 1 << K)


def pair_fraction(N, u, x):
    """<n+ + n->/N on the P = 0 chain, from the exact level's slope in x."""
    h = F(1, 1 << 30)
    return (level(N, u, x + h, 0) - level(N, u, x - h, 0)) / (2 * h) / N


print("# u = 1: lowest P over x, for N = 27, 81, 243, 729, 2187")
XS = [F(k, 8) for k in range(-24, 17)] + [F(-1, 16), F(-1, 32), F(-1, 64), F(-1, 128), F(-1, 256), F(-1, 512), F(-1, 1024), F(-1, 2048), F(1, 16), F(1, 32), F(1, 64), F(1, 1024)]
XS = sorted(set(XS))
for N in (27, 81, 243, 729, 2187):
    last = None
    spans = []
    for x in XS:
        who, best, e0 = argmin_P(N, F(1), x, stop_bits=90)
        if who != last:
            spans.append("x>=%s:P=%d" % (x, who))
            last = who
    print("U1_LOWEST|N=%d|%s|json=0" % (N, ";".join(spans)))
    sys.stdout.flush()
print("# u = 1: at x > 0 the P = 0 chain against the plane wave, and its pair fraction, against the mean-field ordered form 2 rho = 2(1 - delta)/(4 - 3u) = -2x, which is negative there")
for N in (243, 729, 2187, 6561):
    for x in (F(-1, 2), F(-1, 4), F(-1, 8), F(-1, 32), F(-1, N), F(-1, 3 * N), F(1, 1024), F(1, 8), F(1, 2), F(1), F(2)):
        e = level(N, F(1), x, 0)
        f = pair_fraction(N, F(1), x)
        print("U1_P0|N=%d|x=%s|E_P0/N=%s|plane_wave_E/N=x=%s|E_P0-Nx=%s|f=%s|f*N=%s|json=0" % (N, x, dec(e / N, 9), dec(x, 9), dec(e - N * x, 6), dec(f, 9), dec(f * N, 4)))
    sys.stdout.flush()

print("# the c0 = 0 edge: x where E(P=1) = E(P=0) on the exact chains, against x_c0 = (4u-2)/(2+u) - u; N(x_exact - x_c0) reads the 1/N shift")
for us in ("1/4", "1/2", "3/4", "1"):
    u = F(us)
    x_c0 = (4 * u - 2) / (2 + u) - u
    for N in (243, 729, 2187, 6561, 19683):
        lo, hi = x_c0 - F(40, N), x_c0 + F(40, N)
        s_lo = level(N, u, lo, 1) - level(N, u, lo, 0)
        s_hi = level(N, u, hi, 1) - level(N, u, hi, 0)
        if (s_lo > 0) == (s_hi > 0):
            print("C0_EDGE|u=%s|N=%d|no_sign_change_in_bracket|s_lo=%s|s_hi=%s|json=0" % (us, N, dec(s_lo * N, 6), dec(s_hi * N, 6)))
            continue
        for _ in range(40):
            mid = (lo + hi) / 2
            mid = F(mid.numerator * (1 << 60) // mid.denominator, 1 << 60)
            s = level(N, u, mid, 1) - level(N, u, mid, 0)
            if (s > 0) == (s_hi > 0):
                hi = mid
            else:
                lo = mid
        xc = (lo + hi) / 2
        print("C0_EDGE|u=%s|N=%d|x_exact=%s|x_c0=%s|N(x_exact-x_c0)=%s|json=0" % (us, N, dec(xc, 8), dec(x_c0, 8), dec(N * (xc - x_c0), 4)))
    sys.stdout.flush()

print("# the rho0 = 0 edge: <n0>/N = 1 - f on the P = 0 chain, across x_rho0 = -1 + u/2, against 1 - 2(1-delta)/(4-3u)")
for us in ("1/4", "1/2", "3/4", "1"):
    u = F(us)
    x_rho = -1 + u / 2
    for N in (243, 729, 2187):
        out = []
        for dx in (F(1, 4), F(1, 8), F(1, 16), F(0), F(-1, 16), F(-1, 8), F(-1, 4)):
            x = x_rho + dx
            f = pair_fraction(N, u, x)
            delta = u + x
            mf = max(1 - 2 * (1 - delta) / (4 - 3 * u), F(0))
            out.append("dx=%s:n0/N=%s,mf=%s" % (dx, dec(1 - f, 6), dec(mf, 6)))
        print("RHO0_EDGE|u=%s|N=%d|x_rho0=%s|%s|json=0" % (us, N, x_rho, ";".join(out)))
    sys.stdout.flush()
