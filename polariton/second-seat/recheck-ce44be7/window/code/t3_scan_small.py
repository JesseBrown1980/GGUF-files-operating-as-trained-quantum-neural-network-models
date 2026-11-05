# Item 3 and item 5. Lowest level over all P at every N <= 27, on a grid of (u, x), y = 0. Prints a row for each point with 0 < P < N, a census per N.
import sys
from fractions import Fraction as F
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from sec_lib import argmin_P, K, fx

US = [F(k, 16) for k in range(0, 25)]
XS = [F(k, 32) for k in range(-96, 49)]
for N in range(2, 28):
    census = {}
    partial = []
    for u in US:
        for x in XS:
            who, best, e0 = argmin_P(N, u, x)
            kind = "P0" if who == 0 else ("PN" if who == N else "partial")
            census[kind] = census.get(kind, 0) + 1
            if kind == "partial":
                partial.append((u, x, who))
                print("SMALL_PARTIAL|N=%d|u=%s|x=%s|P=%d|E=%s|E_P0=%s|json=0" % (N, u, x, who, fx(best, 9), fx(e0, 9)))
    ones = sum(1 for _, _, w in partial if w == 1)
    print("SMALL_CENSUS|N=%d|points=%d|P0=%d|PN=%d|partial=%d|partial_P=1=%d|partial_u_range=%s..%s|partial_x_range=%s..%s|json=0" % (
        N, len(US) * len(XS), census.get("P0", 0), census.get("PN", 0), census.get("partial", 0), ones,
        min([p[0] for p in partial], default="-"), max([p[0] for p in partial], default="-"), min([p[1] for p in partial], default="-"), max([p[1] for p in partial], default="-")))
    sys.stdout.flush()
