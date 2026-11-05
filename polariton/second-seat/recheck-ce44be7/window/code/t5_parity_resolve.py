# Item 5. The points of t5_parity_scan that sat within 2^-40: resolve the direction at higher precision, for N <= 12.
import sys
from fractions import Fraction as F
sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from ed_lib import Block, dec


def tight(blk, start=None):
    K = blk.K
    theta, v, res = blk.ground(bits=40)
    for _ in range(6):
        sigma = theta - (1 << (K // 2))
        neg, lrows, d = blk.factor(sigma)
        w = blk.norm(blk.solve(lrows, d, v))
        th = blk.rayleigh(w)
        done = abs(th - theta) < (1 << 60)
        v, theta = w, th
        if done:
            break
    return theta


tally = {}
K = 1000
worst = None
for line in open("C:/tmp/opus55/polariton-recheck-window-20261105/out/t5_parity_scan.hbp", encoding="utf-8").read().splitlines():
    if not line.startswith("PARITY_SCAN_HIT|"):
        continue
    d = dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f)
    N = int(d["N"])
    if N > 12:
        continue
    u, x, y = F(d["u"]), F(d["x"]), F(d["y"])
    be = Block(N, u, x, y, parity=1, K=K)
    bo = Block(N, u, x, y, parity=-1, K=K)
    te = tight(be)
    to = tight(bo)
    gap = to - te
    res = "even" if gap > (1 << 200) else ("odd" if gap < -(1 << 200) else "unresolved")
    t = tally.setdefault(N, {"even": 0, "odd": 0, "unresolved": 0})
    t[res] += 1
    if res != "even":
        print("RESOLVE_NOT_EVEN|N=%d|u=%s|x=%s|y=%s|result=%s|gap_log2=%d|json=0" % (N, u, x, y, res, gap.bit_length() - K))
    sys.stdout.flush()
for N in sorted(tally):
    print("RESOLVE|N=%d|even_below=%d|odd_below=%d|unresolved_at_2^-800=%d|json=0" % (N, tally[N]["even"], tally[N]["odd"], tally[N]["unresolved"]))
