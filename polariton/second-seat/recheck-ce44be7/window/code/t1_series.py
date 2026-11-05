# Item 1, part 1. The plane-wave perturbation series with exact rationals against the closed forms, exact in N.
import sys
from fractions import Fraction as F
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from pw_lib import Series, closed_A1, closed_B2, closed_E2, dec

POINTS = [("1", "-1/4"), ("1", "-1/8"), ("1/2", "-1/4"), ("3/4", "-1/8")]
for N, order in ((9, 8), (27, 10), (81, 10), (243, 8), (729, 8)):
    for us, xs in POINTS:
        u, x = F(us), F(xs)
        s = Series(N, u, x, order)
        a = s.A()
        b = s.B()
        c2 = s.charge2()
        ok = a[1] == closed_A1(N, u, x) and b[2] == closed_B2(N, u, x) and s.E[2] == closed_E2(N, u, x)
        odd_zero = all(s.E[k] == 0 for k in range(1, order + 1, 2)) and all(a[k] == 0 for k in range(0, order + 1, 2)) and all(b[k] == 0 for k in range(1, order + 1, 2))
        print("PW_SERIES|N=%d|u=%s|x=%s|order=%d|A1=<A>/y=%s|closed_A1=%s|B2=<B>/y^2=%s|closed_B2=%s|E2=%s|matches_closed=%d|parity_of_orders_ok=%d|D2/y2_leading=%s|A1/y_leading=%s|form_D2/y2=%s|form_A1/y=%s|json=0" % (
            N, us, xs, order, dec(a[1], 12), dec(closed_A1(N, u, x), 12), dec(b[2], 12), dec(closed_B2(N, u, x), 12), dec(s.E[2], 12), ok, odd_zero,
            dec(2 * abs(b[2]) / N, 9), dec(2 * abs(a[1]) / N, 9), dec(2 * abs(u - x - 1) / (u * (u - x) ** 2), 9), dec(2 / (u - x), 9)))
        print("PW_SERIES_HIGHER|N=%d|u=%s|x=%s|A3/N=%s|A5/N=%s|B4/N=%s|B6/N=%s|P2_y2/N2=%s|json=0" % (N, us, xs, dec(a[3] / N, 9), dec(a[5] / N, 9), dec(b[4] / N, 9), dec(b[6] / N, 9), dec(c2[2] / (N * N), 9)))
        sys.stdout.flush()
