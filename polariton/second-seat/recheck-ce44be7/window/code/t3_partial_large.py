# Item 3. Does P = +-1, or any 0 < P < N, win above the plane-wave edge at larger N? All P at each point, on x steps of 1/128 across the edge region, at fixed u.
import sys
from fractions import Fraction as F
from math import isqrt
sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from sec_lib import argmin_P, K, fx
SC = 10**24
def edge(u):
    r = u*(4-3*u)
    w = ((4-3*u) - F(isqrt(r.numerator*SC*SC//r.denominator), SC))/2
    return 1-w-u
for N in (27, 28, 45, 81, 82, 121, 243, 244, 729):
    for u in (F(1,64), F(1,32), F(1,16), F(1,8), F(3,16), F(1,4), F(3,8), F(1,2), F(3,4), F(1)):
        xe = edge(u)
        base = F((xe*128).numerator//(xe*128).denominator, 128)
        spans = []
        last = None
        for k in range(-12, 37):
            x = base + F(k, 128)
            who, best, e0 = argmin_P(N, u, x, stop_bits=80)
            if who != last:
                spans.append("x>=%s:P=%d" % (x, who))
                last = who
        print("LARGE_PARTIAL|N=%d|u=%s|x_edge=%s|%s|json=0" % (N, u, fx((xe.numerator<<K)//xe.denominator, 5), ";".join(spans)))
        sys.stdout.flush()
