# Item 1. Even against odd block on the plane-wave side: E, <A>, <B>. K large enough to see an exponentially small splitting.
import sys
from fractions import Fraction as F
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from ed_lib import Block, dec

POINTS = [("1", "-1/4"), ("1", "-1/8"), ("1/2", "-1/4"), ("3/4", "-1/8")]
SIX = ["1/2", "1", "2", "4", "8", "16"]


def tight(blk):
    """Lowest level and vector, tightening with a Rayleigh step until the level is good to about 2^-(K-40)."""
    theta, v, res = blk.ground(bits=48)
    K = blk.K
    for _ in range(5):
        sigma = theta - (1 << (K // 2))
        neg, lrows, d = blk.factor(sigma)
        w = blk.norm(blk.solve(lrows, d, v))
        th = blk.rayleigh(w)
        done = abs(th - theta) < (1 << 40)
        v, theta = w, th
        if done:
            break
    return theta, v


def expo(q):
    """Decimal exponent of a nonzero rational, by integers."""
    q = abs(F(q))
    if q == 0:
        return "zero"
    e = 0
    while q >= 10:
        q /= 10
        e += 1
    while q < 1:
        q *= 10
        e -= 1
    return "%se%d" % (dec(q, 3), e)


for N, K, ss in ((3, 400, SIX), (9, 400, SIX), (27, 800, SIX), (81, 1800, ["2", "4", "8", "16"])):
    for us, xs in POINTS:
        for s in ss:
            u, x, y = F(us), F(xs), F(s) / N
            be = Block(N, u, x, y, parity=1, K=K)
            bo = Block(N, u, x, y, parity=-1, K=K)
            te, ve = tight(be)
            to, vo = tight(bo)
            re = be.read(ve)
            ro = bo.read(vo)
            one = be.one
            gap = F(to - te, one)
            print("PARITY_BELOW|N=%d|u=%s|x=%s|s=%s|E_even=%s|E_odd-E_even=%s|lower=%s|B_even=%s|B_odd-B_even=%s|A_even=%s|A_odd-A_even=%s|P2/N2_even=%s|json=0" % (
                N, us, xs, s, dec(F(te, one), 9), expo(gap), "even" if gap > 0 else ("odd" if gap < 0 else "tie"), dec(F(re[1], one), 9), expo(F(ro[1] - re[1], one)), dec(F(re[0], one), 9), expo(F(ro[0] - re[0], one)), dec(F(re[2], one) / (N * N), 6)))
            sys.stdout.flush()
