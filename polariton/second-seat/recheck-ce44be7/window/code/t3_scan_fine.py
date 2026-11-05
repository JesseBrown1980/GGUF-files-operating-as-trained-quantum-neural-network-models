# Item 3. A fine scan in u near u ~ 1/(N|x|), where the plane wave and the balanced state nearly tie on n0 ~ 0, for any P strictly between the ends.
import sys
from fractions import Fraction as F
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from sec_lib import argmin_P, fx

for N in (9, 10, 27, 28, 81, 82, 243, 244, 729):
    for x in (F(-1, 2), F(-3, 4), F(-1), F(-5, 4), F(-2), F(-3), F(-5), F(-10)):
        # u up to 3/(N|x|) and up to 1/8 at least for |x| small, in 120 steps. Every step asks all P.
        top = max(F(3, N * max(abs(x), F(1, 2))), F(1, 8) if N <= 27 else F(3, N))
        steps = 120 if N <= 243 else 40
        last = None
        spans = []
        for k in range(0, steps + 1):
            u = top * k / steps
            who, best, e0 = argmin_P(N, u, x, stop_bits=80)
            if who != last:
                spans.append((u, who))
                last = who
        print("FINE|N=%d|x=%s|u_top=%s|steps=%d|changes=%s|json=0" % (N, x, top, steps, ";".join("u>=%s:P=%d" % (fx(F(a).numerator * (1 << 160) // F(a).denominator, 6), b) for a, b in spans)))
        sys.stdout.flush()
