# Item 1. Even against odd at N = 81 on the plane-wave side, with the level bracketed from the exact series, and K sized to the splitting.
# A row reads E_odd - E_even from Rayleigh quotients at K bits; the vector is iterated until the quotient has settled to about 2^-(K-60).
import sys
from fractions import Fraction as F
sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from ed_lib import Block, dec
from pw_lib import Series, evaluate


def expo(q):
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


def settle(blk, guess_q):
    """Inverse iteration from a shift just below the series level, then Rayleigh quotient steps."""
    K = blk.K
    g = (guess_q.numerator << K) // guess_q.denominator
    sigma = g - (1 << (K - 26))
    neg, lrows, d = blk.factor(sigma)
    if neg != 0:
        sigma = g - (1 << (K - 12))
        neg, lrows, d = blk.factor(sigma)
    assert neg == 0
    v = [(((i * 2654435761 + 12345) % 1000003) - 500001) << (K - 20) for i in range(blk.size)]
    v = blk.norm(v)
    theta = sigma
    for r in range(14):
        w = blk.norm(blk.solve(lrows, d, v))
        th = blk.rayleigh(w)
        settled = abs(th - theta) < (1 << 80)
        v, theta = w, th
        if settled and r >= 2:
            break
        sigma = th - (1 << (K // 2))
        neg, lrows, d = blk.factor(sigma)
        if neg != 0:
            sigma = th - (1 << (K // 3))
            neg, lrows, d = blk.factor(sigma)
    return theta, v, neg


POINTS = [("1", "-1/4"), ("1/2", "-1/4"), ("3/4", "-1/8"), ("1", "-1/8")]
N = 81
for us, xs in POINTS:
    u, x = F(us), F(xs)
    ser = Series(N, u, x, 16)
    for s, K in ((F(16), 700), (F(8), 900), (F(4), 1200)):
        y = s / N
        guess = evaluate(ser.E, y)
        be = Block(N, u, x, y, parity=1, K=K)
        bo = Block(N, u, x, y, parity=-1, K=K)
        te, ve, n1 = settle(be, guess)
        to, vo, n2 = settle(bo, guess)
        gap = F(to - te, be.one)
        re = be.read(ve)
        ro = bo.read(vo)
        print("PARITY_BELOW|N=%d|u=%s|x=%s|s=%s|K=%d|E_even=%s|E_odd-E_even=%s|lower=%s|B_even=%s|B_odd-B_even=%s|A_odd-A_even=%s|neg_at_last_shift=%d,%d|json=0" % (
            N, us, xs, s, K, dec(F(te, be.one), 9), expo(gap), "even" if gap > 0 else ("odd" if gap < 0 else "tie"), dec(F(re[1], be.one), 9), expo(F(ro[1] - re[1], be.one)), expo(F(ro[0] - re[0], be.one)), n1, n2))
        sys.stdout.flush()
