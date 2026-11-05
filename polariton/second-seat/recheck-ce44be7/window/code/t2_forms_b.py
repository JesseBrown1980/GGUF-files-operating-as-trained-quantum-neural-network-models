# Item 2, the groups the series cannot read: near the edge, small u, and the pole, with the even-block solver at N = 81 and 243.
import sys, subprocess
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction as F
sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from pw_lib import closed_A1, closed_B2, dec

EXE = "C:/tmp/opus55/polariton-derivations-20261104/fullspace/target/release/fullspace.exe"


def full(N, u, x, y):
    u, x, y = F(u), F(x), F(y)
    args = [EXE] + [str(v) for v in (N, u.numerator, u.denominator, x.numerator, x.denominator, y.numerator, y.denominator)]
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=500).stdout
    except subprocess.TimeoutExpired:
        return None
    if not out.startswith("FULL|"):
        return None
    return dict(p.split("=", 1) for p in out.strip().split("|") if "=" in p)


GROUPS = []
for u, x in ((F(5, 8), F(-1, 8)), (F(7, 16), F(-1, 4)), (F(13, 64), F(-1, 2)), (F(1, 2), F(-1, 5)), (F(1, 4), F(-7, 16)), (F(3, 4), F(-1, 16)), (F(1), F(-1, 64)), (F(1), F(-1, 32)), (F(1, 3), F(-3, 8))):
    GROUPS.append(("near_edge", u, x))
for u in (F(1, 512), F(1, 128), F(1, 64), F(1, 16)):
    for x in (F(-1), F(-2), F(-5)):
        GROUPS.append(("small_u", u, x))
for u, x in ((F(1, 2), F(1, 2)), (F(1, 2), F(1, 4)), (F(1), F(1)), (F(5, 4), F(1, 8))):
    GROUPS.append(("pole", u, x))
jobs = []
for group, u, x in GROUPS:
    for N in (81, 243):
        for s in (F(4), F(16)):
            jobs.append((group, u, x, N, s))


def work(item):
    group, u, x, N, s = item
    return item, full(N, u, x, s / N)


with ThreadPoolExecutor(2) as pool:
    for item, r in pool.map(work, jobs):
        group, u, x, N, s = item
        y = s / N
        w = u - x
        W = w - 1
        if r is None:
            print("FORMS_B|%s|N=%d|u=%s|x=%s|s=%s|CANNOT_SEE=solver_returned_nothing|json=0" % (group, N, u, x, s))
            continue
        a1y = F(r["A1"]) / y
        d2y = F(r["D2"]) / (y * y)
        p2 = F(r["J2"]) / (N * N)
        b = F(r["B"])
        fa = dec(2 / w, 5) if w > 0 else "pole"
        fd = dec(2 * abs(W) / (u * w * w), 5) if w > 0 else "pole"
        ea = dec(2 * closed_A1(N, u, x) / N, 5) if w > u / N else "-"
        ed = dec(2 * abs(closed_B2(N, u, x)) / N, 5) if w > u / N else "-"
        print("FORMS_B|%s|N=%d|u=%s|x=%s|W=%s|s=%s|N*u*(u-x)=%s|P2/N2=%s|A1/y=%s|form=%s|finiteN=%s|D2/y2=%s|form=%s|finiteN=%s|B=%s|residual=%s|json=0" % (group, N, u, x, W, s, dec(N * u * w, 3), dec(p2, 5), dec(a1y, 5), fa, ea, dec(d2y, 5), fd, ed, dec(b, 8), r.get("residual", "?")))
        sys.stdout.flush()
