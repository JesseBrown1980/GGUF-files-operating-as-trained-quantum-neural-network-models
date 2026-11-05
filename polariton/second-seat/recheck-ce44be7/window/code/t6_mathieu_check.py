# Why does second_route.mathieu(1) read 417999 ppm and my vector read 417996.36? A third reading: the slope of an exact level, by Sturm counts on my own reduced tridiagonal at 2^-200, and the route's own function at neighbours of q = 1.
import sys, importlib.util
sys.dont_write_bytecode = True
from fractions import Fraction as F
from math import isqrt
spec = importlib.util.spec_from_file_location("second_route", "C:/tmp/qnn-polariton-wt/polariton/second_route.py")
route = importlib.util.module_from_spec(spec)
spec.loader.exec_module(route)
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from t4_reduced import mathieu_f
from resp_lib import dec

K = 240
ONE = 1 << K
ROOT2 = isqrt(2 << (2 * K))


def level(q, M=60):
    qi = (F(q).numerator << K) // F(q).denominator
    d = [(4 * k * k) << K for k in range(M)]
    o2 = [(2 * qi * qi) >> K] + [(qi * qi) >> K] * (M - 2)

    def count(lam):
        p = d[0] - lam
        c = 1 if p < 0 else 0
        for i in range(1, M):
            if p == 0:
                p = -1
            p = d[i] - lam - (o2[i - 1] << K) // p
            if p < 0:
                c += 1
        return c

    lo, hi = -(4 * ONE + 4 * abs(qi)), ONE
    while hi - lo > (1 << (K - 190)):
        mid = (lo + hi) >> 1
        if count(mid) >= 1:
            hi = mid
        else:
            lo = mid
    return F(lo + hi, 2 * ONE)


for q in (F(1), F(1) + F(1, 100000), F(1) - F(1, 100000), F(9, 10), F(11, 10), F(5, 4), F(3, 4), F(1, 2), F(2), F(1, 16), F(1, 4), F(4), F(16), F(64), F(9, 625), F(4, 675)):
    vals = {}
    for b in (F(1, 1 << 16), F(1, 1 << 24)):
        vals[b] = (level(q - b) - level(q + b)) / (4 * b)
    print("MATHIEU_CHECK|q=%s|slope_b=2^-16=%s|slope_b=2^-24=%s|my_vector=%s|route_mathieu=%s|json=0" % (q, dec(vals[F(1, 1 << 16)] * 10 ** 6, 4), dec(vals[F(1, 1 << 24)] * 10 ** 6, 4), dec(mathieu_f(q) * 10 ** 6, 4), dec(route.mathieu(q) * 10 ** 6, 4)))
    sys.stdout.flush()
print("# route's level at q - 2^-16, q + 2^-16 near q = 1, from tridiagonal_level with both widths")
for value in (F(1) - F(1, 1 << 16), F(1) + F(1, 1 << 16)):
    m = 40
    diag = [F(4 * k * k) for k in range(-m, m + 1)]
    o2 = [value * value] * (2 * m)
    lo, hi = route.tridiagonal_level(diag, o2, 0, F(1, 1 << 48))
    print("ROUTE_LEVEL|value=%s|lo=%s|hi=%s|mine=%s|json=0" % (value, dec(lo, 18), dec(hi, 18), dec(level(value), 18)))
