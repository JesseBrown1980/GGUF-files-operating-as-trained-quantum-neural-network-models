# Item 5. Is the odd block ever below the even block at y != 0? Exact negative-pivot counts at K bits, for N <= 12 on a wide grid, N = 13..27 on a thinner one.
import sys
from fractions import Fraction as F
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from ed_lib import Block, dec

K = 140


def compare(N, u, x, y):
    be = Block(N, u, x, y, parity=1, K=K)
    bo = Block(N, u, x, y, parity=-1, K=K)
    lo, hi = be.lowest(bits=44)
    tol = 1 << (K - 40)
    # odd below even by more than 2^-40?
    if bo.count_below(lo - tol) >= 1:
        return -1, lo
    # odd above even by more than 2^-40?
    if bo.count_below(hi + tol) == 0:
        return 1, lo
    return 0, lo


US = [F(k, 8) for k in range(0, 13)]
XS = [F(k, 8) for k in range(-16, 9)]
YS = [F(1, 64), F(1, 16), F(1, 8), F(1, 4), F(1, 2), F(1), F(2)]
for N in list(range(2, 13)) + [15, 21, 27]:
    if N <= 12:
        us, xs, ys = US, XS, YS
    else:
        us, xs, ys = US[::2], XS[::2], YS[::2]
    tally = {1: 0, 0: 0, -1: 0}
    for u in us:
        for x in xs:
            for y in ys:
                r, lo = compare(N, u, x, y)
                tally[r] += 1
                if r <= 0:
                    print("PARITY_SCAN_HIT|N=%d|u=%s|x=%s|y=%s|result=%s|E_even=%s|json=0" % (N, u, x, y, "odd_below" if r < 0 else "within_2^-40", dec(F(lo, 1 << K), 9)))
    print("PARITY_SCAN|N=%d|points=%d|even_below=%d|within_2^-40=%d|odd_below=%d|json=0" % (N, sum(tally.values()), tally[1], tally[0], tally[-1]))
    sys.stdout.flush()
