# Item 5. second_route.even_block against a direct even-basis count, on matrices of my choice.
# Direct count: H acts rationally on monomial even vectors v = |p,m>' + |m,p>' (or |p,p>'), giving a non-symmetric rational M similar to H on the even block by a diagonal scaling,
# so the leading minors of M - lam are those of H_even - lam. Negative pivots by exact elimination, with no use of T^t S T.
# A second count with no pivots: the exact characteristic polynomial of M by Faddeev-LeVerrier, and Descartes on p(lam - t), since all roots are real.
# The odd block the same way, and even + odd against the route's whole-space count.
import sys, random
sys.dont_write_bytecode = True  # -I ignores PYTHONDONTWRITEBYTECODE, and the worktree stays read-only
from fractions import Fraction as F
sys.path.insert(0, "C:/tmp/qnn-polariton-wt/polariton")
import importlib.util
spec = importlib.util.spec_from_file_location("second_route", "C:/tmp/qnn-polariton-wt/polariton/second_route.py")
route = importlib.util.module_from_spec(spec)
spec.loader.exec_module(route)


def act(n, x, u, y, kb, kn, s):
    """H on the monomial |p,m>' as a dict, for H = x(p+m) + (u/n)(n0(p+m)+pm) + kn pm + (P + P^dag)/n - y(...) + kb(B + B^dag)."""
    p, m = s
    n0 = n - p - m
    out = {}

    def add(k, v):
        if v:
            out[k] = out.get(k, F(0)) + v

    add((p, m), x * (p + m) + u * F(n0 * (p + m) + p * m, n) + kn * p * m)
    if n0 >= 2:
        add((p + 1, m + 1), F(n0 * (n0 - 1), n))
    if p >= 1 and m >= 1:
        add((p - 1, m - 1), F(p * m, n))
    if p >= 1:
        add((p - 1, m), -y * p)
        add((p - 1, m + 1), kb * p)
    if m >= 1:
        add((p, m - 1), -y * m)
        add((p + 1, m - 1), kb * m)
    if n0 >= 1:
        add((p + 1, m), -y * n0)
        add((p, m + 1), -y * n0)
    return out


def direct_matrix(n, x, u, y, kb, kn, parity):
    reps = [(p, m) for p in range(n + 1) for m in range(n + 1 - p) if (p >= m if parity == 1 else p > m)]
    index = {s: i for i, s in enumerate(reps)}
    size = len(reps)
    M = [[F(0)] * size for _ in range(size)]
    for s, j in index.items():
        p, m = s
        image = dict(act(n, x, u, y, kb, kn, s))
        if p != m:
            for k, v in act(n, x, u, y, kb, kn, (m, p)).items():
                image[k] = image.get(k, F(0)) + parity * v
        # Read off the coefficient of each v_a, from its representative with p >= m. For the odd block a state (m,p) carries the opposite sign, and the image is odd by symmetry.
        for (a, b), v in image.items():
            if a > b or (a == b and parity == 1):
                M[index[(a, b)]][j] = M[index[(a, b)]][j] + v
    return M


def pivots_negative(M, lam):
    size = len(M)
    A = [list(r) for r in M]
    for i in range(size):
        A[i][i] -= lam
    neg = 0
    for k in range(size):
        piv = A[k][k]
        if piv == 0:
            raise ZeroDivisionError
        if piv < 0:
            neg += 1
        for i in range(k + 1, size):
            if A[i][k] != 0:
                f = A[i][k] / piv
                for j in range(k, size):
                    A[i][j] -= f * A[k][j]
    return neg


def charpoly(M):
    """Coefficients c[0..n] of det(t - M) = sum c[k] t^k, by Faddeev-LeVerrier, exact."""
    n = len(M)
    B = [[F(i == j) for j in range(n)] for i in range(n)]
    c = [F(0)] * (n + 1)
    c[n] = F(1)
    for k in range(1, n + 1):
        AB = [[sum(M[i][l] * B[l][j] for l in range(n)) for j in range(n)] for i in range(n)]
        tr = sum(AB[i][i] for i in range(n))
        c[n - k] = -tr / k
        B = [[AB[i][j] + (c[n - k] if i == j else F(0)) for j in range(n)] for i in range(n)]
    return c


def roots_below(c, lam):
    """Roots of a real-rooted polynomial below lam: p(lam - t) has only real roots, and its positive roots are the roots below lam. Descartes is exact for real-rooted polynomials."""
    n = len(c) - 1
    # Taylor shift to lam, then flip t -> -t.
    a = list(c)
    for i in range(n):
        for j in range(n - 1, i - 1, -1):
            a[j] += lam * a[j + 1]
    shifted = [a[k] * ((-1) ** k) for k in range(n + 1)]
    signs = [1 if v > 0 else -1 for v in shifted if v != 0]
    return sum(1 for p, q in zip(signs, signs[1:]) if p != q)


rng = random.Random(20261105)
checks = 0
bad = 0
zero_hits = 0


def compare(n, x, u, y, kb, kn, lam, label):
    global checks, bad, zero_hits
    rows = route.congruent_matrix(n, x, u, y, lam, kb, kn)
    try:
        route_even = route.inertia_negative(route.even_block(rows, n))
        route_whole = route.inertia_negative(rows)
    except ZeroDivisionError:
        zero_hits += 1
        route_even = route_whole = None
    Me = direct_matrix(n, x, u, y, kb, kn, 1)
    Mo = direct_matrix(n, x, u, y, kb, kn, -1)
    pe = roots_below(charpoly(Me), lam) if n <= 5 else None
    po = roots_below(charpoly(Mo), lam) if n <= 5 and Mo else (0 if not Mo else None)
    try:
        de = pivots_negative(Me, lam)
        do = pivots_negative(Mo, lam) if Mo else 0
    except ZeroDivisionError:
        zero_hits += 1
        de = do = None
    ok = True
    if route_even is not None and de is not None:
        ok &= route_even == de and route_whole == de + do
    if pe is not None and de is not None:
        ok &= pe == de and po == do
    checks += 1
    bad += not ok
    if not ok or checks % 40 == 0:
        print("EVEN_BLOCK|%s|N=%d|u=%s|x=%s|y=%s|kb=%s|kn=%s|lam=%s|route_even=%s|direct_even=%s|charpoly_even=%s|route_whole=%s|direct_odd=%s|charpoly_odd=%s|ok=%d|json=0" % (label, n, u, x, y, kb, kn, lam, route_even, de, pe, route_whole, do, po, ok))
        sys.stdout.flush()


# Named points: the doublet, the plane-wave doublet, the hand point.
for n, u, x in ((3, F(1, 4), F(-1, 4)), (3, F(1), F(-1, 4)), (2, F(0), F(1, 4)), (5, F(1, 4), F(-1, 2)), (4, F(1, 2), F(-1, 4))):
    for y in (F(0), F(1, 6), F(1, 3)):
        for kb in (F(0), F(1, 1 << 14), F(-1, 1 << 14), F(1, 7)):
            for k in range(-24, 25):
                compare(n, x, u, y, kb, F(0), F(k, 8) + F(1, 1 << 70), "named")
# Random rational points.
for trial in range(240):
    n = rng.choice((2, 3, 4, 5, 6, 7, 9))
    u = F(rng.randint(0, 24), 16)
    x = F(rng.randint(-48, 24), 16)
    y = F(rng.randint(-16, 16), rng.choice((8, 16, 81)))
    kb = F(rng.randint(-8, 8), rng.choice((16, 64, 1 << 14)))
    kn = F(rng.randint(-4, 4), rng.choice((16, 1 << 14)))
    lam = F(rng.randint(-200, 200), 16) * n / 3 + F(1, 1 << 70)
    compare(n, x, u, y, kb, kn, lam, "random")
print("EVEN_BLOCK_DONE|checks=%d|bad=%d|zero_pivot_hits=%d|json=0" % (checks, bad, zero_hits))
