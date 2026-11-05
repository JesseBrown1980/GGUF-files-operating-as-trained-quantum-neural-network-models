# Item 2. The below-edge forms on the plane-wave side, read by the exact rational series from one plane wave (checked against exact diagonalization at N = 81, 243 in t1_compare and t2_forms).
# Part 1: the zero of u - x - 1 and large |x|: ratio to the form at s = 1, 4, 16, N = 81, 243, 729, 2187.
# Part 2: how close to the zero the 5% tolerance survives, by bisection in W = u - x - 1, at each N and s.
# Part 3: the zero of <B> against -(1 - 2u)/N - 2(1 - u) y^2.
import sys
from fractions import Fraction as F
sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from pw_lib import Series, closed_A1, closed_B2, evaluate, dec

ORDER = 12


def read(N, u, x, s, order=ORDER):
    ser = Series(N, u, x, min(order, 2 * N - 1))
    y = s / N
    a = evaluate(ser.A(), y)
    b = evaluate(ser.B(), y)
    p2 = evaluate(ser.charge2(), y) / (N * N)
    last_b = abs(ser.B()[min(order, 2 * N - 1)]) * y ** min(order, 2 * N - 1)
    return 2 * abs(a) / N / y, 2 * abs(b) / N / (y * y), b, p2, last_b


print("# part 1")
for u, Ws in ((F(1, 4), [F(1), F(1, 4), F(1, 8), F(1, 16), F(1, 32), F(1, 64), F(0), F(-1, 64), F(-1, 32), F(-1, 16), F(-1, 8), F(-1, 4)]),
              (F(1, 2), [F(1), F(1, 4), F(1, 8), F(1, 16), F(1, 32), F(1, 64), F(0), F(-1, 64), F(-1, 32), F(-1, 16), F(-1, 8), F(-1, 4)]),
              (F(3, 4), [F(1), F(1, 4), F(1, 8), F(1, 16), F(1, 32), F(1, 64), F(0), F(-1, 64), F(-1, 32), F(-1, 16), F(-1, 8)]),
              (F(1), [F(1), F(1, 4), F(1, 8), F(1, 16), F(1, 32), F(1, 64)])):
    for W in Ws:
        x = u - 1 - W
        w = u - x
        for N in (81, 243, 729, 2187):
            for s in (F(1), F(4), F(16)):
                a1y, d2y, b, p2, last = read(N, u, x, s)
                form_a = 2 / w
                form_d = 2 * abs(W) / (u * w * w)
                ex = 2 * abs(closed_B2(N, u, x)) / N
                print("ZERO_LINE|u=%s|x=%s|W=%s|N=%d|s=%s|P2/N2=%s|A1/y_over_form=%s|D2/y2=%s|form=%s|exact_N_y2=%s|D2_over_form=%s|B=%s|last_term=%s|json=0" % (
                    u, x, W, N, s, dec(p2, 5), dec(a1y / form_a, 5), dec(d2y, 5), dec(form_d, 5), dec(ex, 5), dec(d2y / form_d, 4) if form_d else "-", dec(b, 8), dec(last, 10)))
    sys.stdout.flush()
for u in (F(1, 16), F(1, 4), F(1, 2), F(1), F(2)):
    for x in (F(-1), F(-2), F(-5), F(-10), F(-50), F(-100)):
        w = u - x
        W = w - 1
        for N in (81, 243, 729, 2187):
            for s in (F(1), F(4), F(16)):
                a1y, d2y, b, p2, last = read(N, u, x, s)
                print("LARGE_X|u=%s|x=%s|N=%d|s=%s|P2/N2=%s|A1/y=%s|form=%s|ratio=%s|D2/y2=%s|form=%s|ratio=%s|sign_ok=%d|last_term=%s|N*u*(u-x)=%s|json=0" % (
                    u, x, N, s, dec(p2, 5), dec(a1y, 5), dec(2 / w, 5), dec(a1y * w / 2, 5), dec(d2y, 6), dec(2 * abs(W) / (u * w * w), 6), dec(d2y * u * w * w / (2 * abs(W)), 4), (b > 0) == (W > 0), dec(last, 10), dec(N * u * w, 3)))
    sys.stdout.flush()
print("# part 2: the smallest |W| at which |D2/y^2 over form - 1| <= 5%, on each side")
for u in (F(1, 4), F(1, 2), F(3, 4)):
    for N in (243, 729, 2187):
        for s in (F(1, 2), F(4), F(16)):
            for side in (1, -1):
                # Walk in from a far W that passes, bisect on a dyadic grid.
                hi = F(1, 4)
                lo = F(0)
                edge_ok = None
                x_hi = u - 1 - side * hi
                good_far = True
                for _ in range(14):
                    mid = (lo + hi) / 2
                    W = side * mid
                    x = u - 1 - W
                    w = u - x
                    a1y, d2y, b, p2, last = read(N, u, x, s, 8)
                    form_d = 2 * abs(W) / (u * w * w)
                    ok = abs(d2y / form_d - 1) <= F(5, 100)
                    if ok:
                        hi = mid
                    else:
                        lo = mid
                print("TOLERANCE_5PCT|u=%s|N=%d|s=%s|side=%s|smallest_abs_W_about=%s|1_over_N_estimate=|(1-2u)/N|*20=%s|json=0" % (u, N, s, "+" if side > 0 else "-", dec(hi, 5), dec(abs(1 - 2 * u) * 20 / N, 5)))
                sys.stdout.flush()
print("# part 3: the zero of <B> in W at fixed N, s, by bisection on the sign, against -(1-2u)/N - 2(1-u) y^2")
for u in (F(1, 4), F(1, 2), F(3, 4)):
    for N in (243, 729, 2187):
        for s in (F(1, 2), F(4), F(16)):
            lo, hi = F(-1, 4), F(1, 4)
            for _ in range(40):
                mid = (lo + hi) / 2
                x = u - 1 - mid
                ser = Series(N, u, x, 8)
                y = s / N
                if evaluate(ser.B(), y) > 0:
                    hi = mid
                else:
                    lo = mid
            y = s / N
            print("B_ZERO|u=%s|N=%d|s=%s|W_zero=%s|predicted=%s|json=0" % (u, N, s, dec(hi, 7), dec(-(1 - 2 * u) / N - 2 * (1 - u) * y * y, 7)))
            sys.stdout.flush()
