# Item 3. The three edges by mean field, in exact arithmetic where it is rational and integer roots where it is not, and the exact P = 0 / P = N crossing against them.
import sys
from fractions import Fraction as F
from math import isqrt
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from sec_lib import chain, ground_level, K, fx, dec, argmin_P

SCALE = 10 ** 40


def rt(q):
    q = F(q)
    return F(isqrt(q.numerator * SCALE * SCALE // q.denominator), SCALE)


def x_edge(u):
    u = F(u)
    w = ((4 - 3 * u) - rt(u * (4 - 3 * u))) / 2
    return 1 - w - u, w


def e_pair(u, x):
    delta = u + x
    return -(1 - delta) ** 2 / (4 - 3 * u)


def mf_min(u, x, G=720):
    """min over (s, m) of x s + u[(1-s)s + (s^2-m^2)/4] - (1-s) sqrt(s^2-m^2), theta = pi, on an integer grid in s, m by the closed inner minimum and by the grid."""
    best = None
    for i in range(0, G + 1):
        s = F(i, G)
        for j in range(0, i + 1):
            m = F(j, G)
            r = rt(s * s - m * m)
            e = x * s + u * ((1 - s) * s + (s * s - m * m) / 4) - (1 - s) * r
            if best is None or e < best[0]:
                best = (e, s, m)
    return best


print("# edges at y = 0: delta(rho0 = 0), delta(c0 = 0), x(plane wave equal), and the same from direct evaluation")
for us, want in (("0", "-1"), ("1/4", "-0.4243"), ("1/3", "-1/3"), ("1/2", "-0.1910"), ("3/4", "-0.0522"), ("1", "0"), ("9/8", "0"), ("5/4", "0")):
    u = F(us)
    d_rho = -1 + 3 * u / 2
    d_c0 = (4 * u - 2) / (2 + u)
    if u <= 1:
        xe, w = x_edge(u)
        # Direct check: e_pair - x changes sign across x_edge.
        below = e_pair(u, xe + F(1, 10 ** 6)) - (xe + F(1, 10 ** 6))
        above = e_pair(u, xe - F(1, 10 ** 6)) - (xe - F(1, 10 ** 6))
        print("EDGE|u=%s|delta_rho0=%s|delta_c0=%s|x_edge=%s|readme=%s|u-x_at_edge=%s|e_pair-e_pw_just_above_edge=%s|just_below=%s|x_rho0=%s|x_c0=%s|json=0" % (us, d_rho, d_c0, dec(xe, 6), want, dec(u - xe, 6), dec(below, 9), dec(above, 9), d_rho - u, d_c0 - u))
    else:
        print("EDGE|u=%s|delta_rho0=%s|delta_c0=%s|x_edge=formula_root_is_negative_for_u>1|json=0" % (us, d_rho, d_c0))

print("# mean-field grid against min(pair, plane wave, vacuum), u in 0..5/4, x in -2..1: the largest shortfall of the three-branch minimum below the grid minimum, and any grid minimum with 0 < m < s or m < 1 at s = 1")
worst = F(0)
interior = 0
points = 0
for iu in range(0, 11):
    u = F(iu, 8)
    for ix in range(-16, 9):
        x = F(ix, 8)
        delta = u + x
        three = [F(0), x]
        if delta < 1 and 4 - 3 * u > 0:
            rho = (1 - delta) / (4 - 3 * u)
            if 2 * rho <= 1:
                three.append(e_pair(u, x))
        # the balanced state with rho0 = 0
        three.append(x + u / 4)
        low = min(three)
        e, s, m = mf_min(u, x, 240)
        points += 1
        if e < low - F(1, 10 ** 30):
            gap = low - e
            worst = max(worst, gap)
            print("MF_BELOW_THREE|u=%s|x=%s|grid_e=%s|three=%s|s=%s|m=%s|json=0" % (u, x, dec(e, 9), dec(low, 9), s, m))
        if m != 0 and not (s == 1 and m == 1):
            interior += 1
            print("MF_INTERIOR|u=%s|x=%s|grid_e=%s|three=%s|s=%s|m=%s|json=0" % (u, x, dec(e, 9), dec(low, 9), s, m))
print("MF_GRID_DONE|points=%d|interior_minima=%d|largest_grid_min_below_three_branches=%s|json=0" % (points, interior, dec(worst, 12)))

print("# exact crossing of P = 0 and P = N, by bisection in x with exact chain levels")
for us in ("1/4", "1/3", "1/2", "3/4", "1"):
    u = F(us)
    xe, w = x_edge(u)
    for N in (9, 10, 27, 81, 243, 729, 2187, 6561, 19683):
        lo, hi = xe - F(3, N) - F(1, 50), xe + F(3, N) + F(1, 50)

        def diff(x):
            d, o2 = chain(N, u, x, 0)
            e = ground_level(d, o2, stop=1 << (K - 90))
            return F(e, 1 << K) - x * N

        for _ in range(60):
            mid = (lo + hi) / 2
            mid = F(mid.numerator * (1 << 80) // mid.denominator, 1 << 80)
            if diff(mid) < 0:
                hi = mid
            else:
                lo = mid
        xc = (lo + hi) / 2
        d, o2 = chain(N, u, xe, 0)
        e1 = F(ground_level(d, o2, stop=1 << (K - 90)), 1 << K) - N * (x_edge(u)[0])
        delta = u + xe
        s_star = 2 * (1 - delta) / (4 - 3 * u)
        print("CROSS|u=%s|N=%d|x_cross=%s|x_edge=%s|N(x_cross-x_edge)=%s|E_P0-Nx_at_edge=%s|predicted_N(x_cross-x_edge)=%s|json=0" % (us, N, dec(xc, 9), dec(xe, 9), dec(N * (xc - xe), 5), dec(e1, 6), dec(e1 / (1 - s_star), 5) if s_star != 1 else "-"))
        sys.stdout.flush()
