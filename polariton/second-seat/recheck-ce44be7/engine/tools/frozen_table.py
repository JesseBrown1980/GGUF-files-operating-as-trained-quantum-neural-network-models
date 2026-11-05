# Step 3: the typed f(q) tables in the reader against the frozen rows, and each frozen value from my own Mathieu read, which uses the ground vector and no slope, in integers at 2^400.
import ast
import re
from fractions import Fraction as F
from math import isqrt

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
pred = open(W + "/clean/polariton/PREDICTION.hbp", encoding="utf8").read().splitlines()
src = open(W + "/clean/polariton/read_prediction.py", encoding="utf8").read()


def row(tag):
    return [l for l in pred if l.startswith(tag + "|")][0]


# The tables as frozen.
inside = row("POLARITON_WINDOW_INSIDE")
m = re.search(r"f_ppm_from_the_exact_mathieu_route=([^|]*)\|", inside).group(1)
frozen = {}
for part in m.split(";"):
    point, values = part.split(":")
    u, x = point.strip("()").split(",")
    frozen[(u, x)] = tuple(int(v) for v in values.split(","))
pin = row("POLARITON_PIN_ORDERED")
fq_frozen = tuple(int(v) for v in re.search(r"f\(q\)=([0-9,]*)_ppm", pin).group(1).split(","))
# The tables as typed, read out of the reader's source by the ast, with nothing run.
tree = ast.parse(src)
typed_inside, typed_fq = None, None
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        if node.targets[0].id == "INSIDE":
            typed_inside = ast.literal_eval(node.value)
        if node.targets[0].id == "FQ":
            typed_fq = ast.literal_eval(node.value)
print("TABLE_INSIDE|points_frozen=%d|points_typed=%d|equal=%d|json=0" % (len(frozen), len(typed_inside), int(frozen == typed_inside)))
print("TABLE_FQ|frozen=%s|typed=%s|equal=%d|keys=%s|json=0" % (fq_frozen, tuple(typed_fq.values()), int(fq_frozen == tuple(typed_fq.values())), ",".join(typed_fq)))

BITS = 400
ONE = 1 << BITS


def count(diag, off2, lam):
    q = diag[0] - lam or -1
    total = int(q < 0)
    for k in range(1, len(diag)):
        q = (diag[k] - lam - (off2 << BITS) // q) or -1
        total += q < 0
    return total


def f_of_q(q):
    """|<cos 2 alpha>| in the ground state of -d^2/dalpha^2 + 2q cos 2alpha on even P, from its vector: (4k^2 - lam) c_k + q (c_{k-1} + c_{k+1}) = 0."""
    m = 60
    qi = (q.numerator << BITS) // q.denominator
    off2 = (qi * qi) >> BITS
    diag = [(4 * k * k) << BITS for k in range(-m, m + 1)]
    lo, hi = -(4 * (qi + ONE)), ONE * 4
    while hi - lo > 1 << (BITS - 300):
        mid = (lo + hi) >> 1
        if count(diag, off2, mid) >= 1:
            hi = mid
        else:
            lo = mid
    lam = (lo + hi) >> 1
    # Ratio r_k = c_k / c_{k-1} by backward recursion from k = m + 1, where it is 0.
    r = 0
    ratios = {}
    for k in range(m, 0, -1):
        den = ((4 * k * k) << BITS) - lam + ((qi * r) >> BITS)
        r = -((qi << BITS) // den)
        ratios[k] = r
    c = {0: ONE}
    for k in range(1, m + 1):
        c[k] = (c[k - 1] * ratios[k]) >> BITS
    norm = c[0] * c[0] + 2 * sum(c[k] * c[k] for k in range(1, m + 1))
    cross = 2 * sum(c[k] * c[k + 1] for k in range(0, m))
    return abs(F(cross, norm))


worst = 0
for (u, x), table in frozen.items():
    du, dx = F(u), F(x)
    delta = du + dx
    rho = (1 - delta) / (4 - 3 * du)
    c0 = ((1 - 2 * rho) / rho - du) / 4
    for s, want in zip((F(1, 2), F(1), F(2), F(4), F(8), F(16)), table):
        qq = s * s * du / (16 * c0 * c0)
        f = f_of_q(qq)
        got = int(f * 10 ** 6)
        worst = max(worst, abs(got - want))
        print("MATHIEU_MINE|u=%s|x=%s|s=%s|q=%s|f_ppm=%d|frozen=%d|json=0" % (u, x, s, qq, got, want))
for s, want in zip((F(1, 2), F(1), F(2), F(4), F(8), F(16)), fq_frozen):
    qq = F(4, 50) * s * s
    f = f_of_q(qq)
    got = int(f * 10 ** 6)
    worst = max(worst, abs(got - want))
    print("MATHIEU_MINE|u=1/2|x=0|s=%s|q=%s|f_ppm=%d|frozen=%d|json=0" % (s, qq, got, want))
print("MATHIEU_MINE_DONE|largest_off_ppm=%d|json=0" % worst)
