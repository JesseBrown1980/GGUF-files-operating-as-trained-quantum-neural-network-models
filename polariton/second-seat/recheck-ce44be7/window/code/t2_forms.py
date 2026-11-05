# Item 2. The below-edge forms at (u, x) the receipt does not hold. Even-block exact levels from the second seat's own block Cholesky (no engine code, Q48 integers) at N = 81, 243,
# exact rational plane-wave series at N = 243, 729, 2187, and the forms: A1/y = 2/(u-x), D2/y^2 = 2|u-x-1|/(u(u-x)^2), with their exact-in-N second order.
import sys, subprocess, re
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction as F
sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from pw_lib import Series, closed_A1, closed_B2, evaluate, dec

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
# Near the zero of u - x - 1, inside the plane-wave side.
for u, Ws in ((F(1, 4), [F(1), F(1, 2), F(1, 4), F(1, 8), F(1, 16), F(1, 32), F(1, 64), F(0), F(-1, 64), F(-1, 32), F(-1, 16), F(-1, 8), F(-1, 4)]),
              (F(1, 2), [F(1), F(1, 2), F(1, 4), F(1, 8), F(1, 16), F(1, 32), F(1, 64), F(0), F(-1, 64), F(-1, 32), F(-1, 16), F(-1, 8), F(-1, 4)]),
              (F(3, 4), [F(1), F(1, 2), F(1, 4), F(1, 8), F(1, 16), F(1, 32), F(1, 64), F(0), F(-1, 64), F(-1, 32), F(-1, 16), F(-1, 8)]),
              (F(1), [F(1), F(1, 2), F(1, 4), F(1, 8), F(1, 16), F(1, 32), F(1, 64)])):
    for W in Ws:
        GROUPS.append(("zero_line", u, u - 1 - W))
# Just inside the plane-wave side of the edge: for each x, u just above the edge value, and for each u, x just below the edge value.
for u, x in ((F(5, 8), F(-1, 8)), (F(7, 16), F(-1, 4)), (F(13, 64), F(-1, 2)), (F(1, 2), F(-1, 5)), (F(1, 4), F(-7, 16)), (F(3, 4), F(-1, 16)), (F(1), F(-1, 64)), (F(1), F(-1, 32)), (F(1, 3), F(-3, 8)), (F(9, 8), F(-1, 64))):
    GROUPS.append(("near_edge", u, x))
# Large |x|.
for u in (F(1, 16), F(1, 4), F(1, 2), F(1), F(2)):
    for x in (F(-1), F(-2), F(-5), F(-10), F(-50), F(-100)):
        GROUPS.append(("large_x", u, x))
# Small u.
for u in (F(1, 512), F(1, 256), F(1, 128), F(1, 64), F(1, 32), F(1, 16), F(1, 8)):
    for x in (F(-3, 4), F(-1), F(-2), F(-5)):
        GROUPS.append(("small_u", u, x))
# Near the pole of the plane-wave branch, u - x -> 0, where the plane wave lies above the ground state.
for u, x in ((F(1, 2), F(1, 2)), (F(1, 2), F(15, 32)), (F(1, 2), F(1, 4)), (F(1), F(1)), (F(1), F(31, 32)), (F(1, 4), F(1, 4)), (F(5, 4), F(5, 4)), (F(5, 4), F(1, 8))):
    GROUPS.append(("pole", u, x))

SS = (F(1), F(4), F(16))


def work(item):
    group, u, x, N, s = item
    y = s / N
    r = full(N, u, x, y)
    return item, r


jobs = []
for group, u, x in GROUPS:
    for N in (81, 243):
        for s in SS:
            jobs.append((group, u, x, N, s))

workers = int(sys.argv[1]) if len(sys.argv) > 1 else 2
series_cache = {}
with ThreadPoolExecutor(workers) as pool:
    for item, r in pool.map(work, jobs):
        group, u, x, N, s = item
        y = s / N
        w = u - x
        W = w - 1
        if w <= 0:
            form_a, form_d = "pole", "pole"
            exact_a, exact_d = "-", "-"
        else:
            form_a = 2 / w
            form_d = 2 * abs(W) / (u * w * w)
            exact_a = 2 * closed_A1(N, u, x) / N if u * F(N - 1, N) - x > 0 else "-"
            exact_d = 2 * abs(closed_B2(N, u, x)) / N if u * F(N - 1, N) - x > 0 else "-"
        if r is None:
            print("FORMS|%s|N=%d|u=%s|x=%s|W=%s|s=%s|CANNOT_SEE=solver_returned_nothing|json=0" % (group, N, u, x, W, s))
            continue
        a1y = F(r["A1"]) / y
        d2y = F(r["D2"]) / (y * y)
        p2 = F(r["J2"]) / (N * N)
        b = F(r["B"])
        ok_p2 = p2 >= F(98, 100)
        ra = a1y / form_a if form_a != "pole" else None
        rd = d2y / form_d if (form_d != "pole" and form_d != 0) else None
        sign_ok = (b > 0) == (W > 0) if W != 0 else None
        print("FORMS|%s|N=%d|u=%s|x=%s|W=%s|s=%s|P2/N2=%s|A1/y=%s|form=%s|finiteN=%s|ratio=%s|D2/y2=%s|form=%s|finiteN=%s|ratio=%s|B=%s|sign_ok=%s|within_1pct_5pct_98pct=%s|residual=%s|json=0" % (
            group, N, u, x, W, s, dec(p2, 5), dec(a1y, 5), dec(form_a, 5) if form_a != "pole" else "pole", dec(exact_a, 5) if exact_a != "-" else "-", dec(ra, 4) if ra is not None else "-",
            dec(d2y, 5), dec(form_d, 5) if form_d != "pole" else "pole", dec(exact_d, 5) if exact_d != "-" else "-", dec(rd, 4) if rd is not None else "-", dec(b, 8), sign_ok,
            (ok_p2 and ra is not None and abs(ra - 1) <= F(1, 100) and rd is not None and abs(rd - 1) <= F(5, 100)), r.get("residual", "?")))
        sys.stdout.flush()
