# A second arithmetic route to the three-mode polariton test, sharing no code with src/bin/polariton_three_mode.rs. Exact rationals only.
# Modes m = 0, +1, -1 with H = x(n+ + n-) + (u/N)[n0(n+ + n-) + n+ n-] + (1/N)(P + P^dag) - y[a0^dag(a+ + a-) + h.c.], P = a+^dag a-^dag a0 a0.
# Units are JN = 1, so x = Delta/(JN), u = U/J, y = h/(JN).
#   second_route.py hand
#   second_route.py mathieu Q_NUM/Q_DEN ...
#   second_route.py sector_compare RECEIPT N_MAX
#   second_route.py full_compare RECEIPT N_MAX
#   second_route.py taylor_compare RECEIPT
#   second_route.py convert_compare RECEIPT
#   second_route.py top_compare RECEIPT N_MIN
# Prints HBP rows, exits 1 on a failed check. json=0.
import sys
from fractions import Fraction as F
from math import factorial, isqrt

BITS = 64


def sector_entries(n, x, u, charge=0, kappa=F(0)):
    """Diagonal and squared off-diagonal of the fixed-P sector, n+ = j + P, n- = j, exactly."""
    top = (n - charge) // 2
    d, o2 = [], []
    for j in range(top + 1):
        n0 = n - 2 * j - charge
        plus, minus = j + charge, j
        d.append(x * (plus + minus) + u * F(n0 * (plus + minus) + plus * minus, n) + kappa * F(plus * minus, n))
        if j < top:
            o2.append(F((plus + 1) * (minus + 1) * n0 * (n0 - 1), n * n))
    return d, o2


def count_below(d, o2, lam):
    """Eigenvalues of the tridiagonal matrix below lam, from exact pivots."""
    count, q = 0, d[0] - lam
    if q < 0:
        count += 1
    for k in range(1, len(d)):
        if q == 0:
            q = F(1, 1 << 200)
        q = d[k] - lam - o2[k - 1] / q
        if q < 0:
            count += 1
    return count


def tridiagonal_level(d, o2, index, width=F(1, 1 << 58)):
    """A bracket of eigenvalue number `index`, counted from the lowest."""
    radius = max(abs(v) for v in d) + 2 * max([isqrt(int(v)) + 1 for v in o2] + [0]) + 1
    lo, hi = -F(radius), F(radius)
    while hi - lo > width:
        mid = (lo + hi) / 2
        if count_below(d, o2, mid) > index:
            hi = mid
        else:
            lo = mid
    return lo, hi


def basis(n):
    return [(p, m) for p in range(n + 1) for m in range(n + 1 - p)]


def congruent_matrix(n, x, u, y, lam, kappa_b=F(0), kappa_n=F(0), kappa_c=F(0)):
    """W(H - lam)W with W = diag(sqrt(n0! p! m!)), which is rational and has the inertia of H - lam."""
    states = basis(n)
    index = {s: i for i, s in enumerate(states)}
    size = len(states)
    rows = [{} for _ in range(size)]
    pn = F(1, n)

    def put(a, b, value):
        if value:
            rows[a][b] = rows[a].get(b, F(0)) + value
            if a != b:
                rows[b][a] = rows[b].get(a, F(0)) + value

    for (p, m), i in index.items():
        n0 = n - p - m
        norm = factorial(n0) * factorial(p) * factorial(m)
        put(i, i, norm * (x * (p + m) + u * pn * (n0 * (p + m) + p * m) + kappa_n * p * m + kappa_c * (p - m) * (p - m) - lam))
        if n0 >= 2:
            put(i, index[(p + 1, m + 1)], pn * norm * (p + 1) * (m + 1))
        if n0 >= 1:
            put(i, index[(p + 1, m)], -y * norm * (p + 1))
            put(i, index[(p, m + 1)], -y * norm * (m + 1))
        if p >= 1 and kappa_b:
            put(i, index[(p - 1, m + 1)], kappa_b * norm * (m + 1))
    return rows


def inertia_negative(rows):
    """Negative pivots of a symmetric sparse rational matrix, by exact elimination with no pivoting."""
    size = len(rows)
    rows = [dict(r) for r in rows]
    negative = 0
    for k in range(size):
        pivot = rows[k].get(k, F(0))
        if pivot == 0:
            raise ZeroDivisionError("zero pivot")
        if pivot < 0:
            negative += 1
        below = [i for i in rows[k] if i > k]
        for i in below:
            factor = rows[i][k] / pivot
            for j, value in rows[k].items():
                if j >= k + 1:
                    rows[i][j] = rows[i].get(j, F(0)) - factor * value
            del rows[i][k]
    return negative


def even_block(rows, n):
    """T^t S T with T = |p,m> + |m,p>: the rational matrix with the inertia of S on the states even under n+ <-> n-."""
    states = basis(n)
    reps = {s: i for i, s in enumerate(s for s in states if s[0] >= s[1])}
    of = [reps[(max(s), min(s))] for s in states]
    out = [{} for _ in reps]
    for i, row in enumerate(rows):
        for j, value in row.items():
            out[of[i]][of[j]] = out[of[i]].get(of[j], F(0)) + value
    return out


def full_ground(n, x, u, y, kappa_b=F(0), width=F(1, 1 << 44), kappa_n=F(0), even=False, kappa_c=F(0)):
    """The lowest level of the whole symmetric space, or of its parity-even block. The block's level is smooth in kappa_b where the whole space has an exact doublet."""
    lo, hi = F(-4 * n * n - 8), F(4 * n * n + 8)
    def below_count(lam):
        rows = congruent_matrix(n, x, u, y, lam, kappa_b, kappa_n, kappa_c)
        return inertia_negative(even_block(rows, n) if even else rows)
    while hi - lo > width:
        mid = (lo + hi) / 2 + F(1, 1 << 90)
        try:
            below = below_count(mid)
        except ZeroDivisionError:
            mid += F(1, 1 << 80)
            below = below_count(mid)
        if below >= 1:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def decimal(q, digits=9):
    q = F(q)
    sign = "-" if q < 0 else ""
    q = abs(q)
    scaled = (q * 10 ** digits).numerator // (q * 10 ** digits).denominator
    return "%s%d.%0*d" % (sign, scaled // 10 ** digits, digits, scaled % 10 ** digits)


def hand():
    """N = 2, J = 2, Delta = 1, U = 0: H_2 = [[0, sqrt2 J], [sqrt2 J, 2 Delta]], in the units of H."""
    ok = True
    n = 2
    x, u = F(1, 4), F(0)
    d, o2 = sector_entries(n, x, u)
    scale = 4  # JN
    low = tridiagonal_level(d, o2, 0)
    high = tridiagonal_level(d, o2, 1)
    e0, e1 = low[0] * scale, high[0] * scale
    ok &= abs(e0 + 2) < F(1, 1 << 50) and abs(e1 - 4) < F(1, 1 << 50)
    # The ground vector: c0^2 = 2/3, c1^2 = 1/3, opposite signs, from row one of (H + 2)c = 0.
    # (H - E)c = 0 on |2,0,0> and |0,1,1> with H_2 = [[0, o], [o, d]] and o^2 = 2J^2 gives c1/c0 = E/o, so everything below follows from E = -2 and J = 2.
    level_exact, j_value = F(-2), F(2)
    c0_sq = 1 / (1 + level_exact * level_exact / (2 * j_value * j_value))
    c1_sq = 1 - c0_sq
    c0c1_times_root2 = c0_sq * level_exact / j_value  # sqrt2 c0 c1 = sqrt2 c0^2 E/o = c0^2 E/J
    ok &= c0_sq == F(2, 3) and c1_sq == F(1, 3) and c0c1_times_root2 == -F(2, 3)
    wk = 2 * c0c1_times_root2  # <n0(n+ + n-)> + 2 Re<P>, and <P> = sqrt2 c0 c1
    w2k = c1_sq
    c1 = 2 * wk / (n * (n - 1))
    c2 = 2 * w2k / (n * (n - 1))
    g2_at_0 = 1 + c1 + c2
    g2_at_half = 1 - c1 + c2
    ok &= c1 == F(-4, 3) and c2 == F(1, 3) and g2_at_0 == 0 and g2_at_half == F(8, 3)
    print("HAND_N2|J=2|Delta=1|U=0|level_0=%s|level_1=%s|c0_squared=2/3|c1_squared=1/3|C1=%s|C2=%s|g2_at_0=%s|g2_at_half_period=%s|json=0" % (decimal(e0), decimal(e1), c1, c2, g2_at_0, g2_at_half))
    # The response of <A> to h, exact: from the second derivative of the 6-state ground energy in y, E(y) - E(0) = -(1/2) chi y^2.
    step = F(1, 1 << 12)
    e_0 = full_ground(2, x, u, F(0))
    e_p = full_ground(2, x, u, step)
    # In units of H, E = 4 Etilde, h = 4 y, 2<A> = -dE/dh, so d<A>/dh = -(1/2) d^2E/dh^2 = -(1/2)(4 d^2Etilde/dy^2)/16.
    curvature = 2 * (e_p - e_0) / (step * step)
    slope = -F(1, 2) * (4 * curvature) / 16
    ok &= abs(slope - F(2, 9)) < F(1, 1000)
    print("HAND_N2_PIN|d_A_d_h_exact_route=%s|by_hand=2/9|visibility_per_h=2/9|json=0" % decimal(slope))
    # N = 3, u = 1/4, x = -1/4, y = 0: P = 0 has levels -1/8 +- sqrt(1/64 + 2/3), P = +1 and P = -1 share -1/3 - sqrt(73)/12, the ground level.
    # On {|2,1,0>, |0,2,1>} the weights are (1 -+ 3/sqrt(73))/2, B|P=1> lands in P=-1 with element c1^2 + 2 c2^2, and the even member has <B> = (3/4)(1 + 1/sqrt(73)).
    x3, u3 = F(-1, 4), F(1, 4)
    root73 = F(isqrt(73 << 160), 1 << 80)
    level_p1 = -F(1, 3) - root73 / 12
    d1, o1 = sector_entries(3, x3, u3, 1)
    d0, o0 = sector_entries(3, x3, u3, 0)
    lo1, hi1 = tridiagonal_level(d1, o1, 0)
    lo0, _ = tridiagonal_level(d0, o0, 0)
    ok &= lo1 - F(1, 1 << 50) < level_p1 < hi1 + F(1, 1 << 50) and hi1 < lo0
    b_closed = F(3, 4) * (1 + 1 / root73)
    b_step = F(1, 1 << 14)
    b_even = (full_ground(3, x3, u3, F(0), b_step, even=True) - full_ground(3, x3, u3, F(0), -b_step, even=True)) / (4 * b_step)
    ok &= abs(b_even - b_closed) < F(1, 10 ** 5)
    ok &= abs(full_ground(3, x3, u3, F(0)) - level_p1) < F(1, 10 ** 6)
    print("HAND_N3_DOUBLET|u=1/4|x=-1/4|y=0|level_P=1_and_P=-1=%s|level_P=0=%s|B_even_block=%s|B_closed_form=%s|json=0" % (decimal(level_p1), decimal(lo0), decimal(b_even), decimal(b_closed)))
    return 0 if ok else 1


def mathieu(q):
    """f(q) = |<cos 2 alpha>| in the ground state of -d^2/dalpha^2 + 2q cos 2 alpha, on even P, from the slope of its lowest level."""
    m = 40
    diag = [F(4 * k * k) for k in range(-m, m + 1)]
    bracket = F(1, 1 << 16)
    def level(value):
        o2 = [value * value] * (2 * m)
        lo, hi = tridiagonal_level(diag, o2, 0, F(1, 1 << 48))
        return (lo + hi) / 2
    upper = level(q - bracket)
    lower = level(q + bracket)
    return (upper - lower) / (4 * bracket)


def compare_sector(path, n_max):
    bad = 0
    count = 0
    for line in open(path, encoding="utf-8").read().splitlines():
        if not line.startswith("POLARITON_SECTOR|"):
            continue
        row = dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f)
        n = int(row["N"])
        if n > n_max:
            continue
        x = F(row["x"])
        u = F(row["u"])
        charge = int(row["P"])
        d, o2 = sector_entries(n, x, u, charge)
        lo, hi = tridiagonal_level(d, o2, 0, F(1, 1 << 58))
        exact = (lo + hi) / (2 * n)
        read = F(int(row["e_at_2^60"]), 1 << 60)
        off = abs(exact - read) * (1 << 60)
        good = off <= 4096
        bad += not good
        count += 1
        print("SECOND_ROUTE_SECTOR|N=%d|u=%s|x=%s|P=%d|exact_e=%s|rust_e=%s|off_units_of_2^-60=%d|json=0" % (n, u, x, charge, decimal(exact, 15), decimal(read, 15), off))
    print("SECOND_ROUTE_SECTOR_DONE|rows=%d|bad=%d|json=0" % (count, bad))
    return 1 if bad or not count else 0


def compare_full(path, n_max):
    bad = 0
    count = 0
    step = F(1, 1 << 14)
    for line in open(path, encoding="utf-8").read().splitlines():
        if not line.startswith(("POLARITON_PIN|", "POLARITON_PIN_WINDOW|")):
            continue
        row = dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f)
        n = int(row["N"])
        if n > n_max:
            continue
        if n > 3 and row["s"] != "4" and not line.startswith("POLARITON_PIN_WINDOW|"):  # Nine polaritons cost minutes a row, so one pinned row per point of the pin stage, and all the window rows, as POLARITON_CONVERSION_ROUTE says.
            continue
        x, u, y = F(row["x"]), F(row["u"]), F(row["y"])
        e = full_ground(n, x, u, y)
        read_e = F(int(row["energy_ppb"]), 10 ** 9)
        # 2<A> = -dE/dy and 2<B> = dE/dkappa, both from exact levels. The engine's state is parity-even, and <B> is read on that block: at an exact P = +-1 doublet the lowest level of the whole space has a cusp in kappa.
        a = -(full_ground(n, x, u, y + step) - full_ground(n, x, u, y - step)) / (4 * step)
        b = (full_ground(n, x, u, y, step, even=True) - full_ground(n, x, u, y, -step, even=True)) / (4 * step)
        read_a, read_b = F(int(row["A_ppb"]), 10 ** 9), F(int(row["B_ppb"]), 10 ** 9)
        good = abs(e - read_e) < F(1, 10 ** 6) and abs(a - read_a) < F(1, 10 ** 5) and abs(b - read_b) < F(1, 10 ** 5)
        if n <= 3:
            # C2 = 2<n+ n->/(N(N-1)) from the level's slope in kappa_n, for N = 2 and 3.
            c2 = (full_ground(n, x, u, y, kappa_n=step) - full_ground(n, x, u, y, kappa_n=-step)) / (2 * step) * 2 / (n * (n - 1))
            read_c2 = F(int(row["C2_ppm"]), 10 ** 6)
            good = good and abs(c2 - read_c2) < F(1, 10 ** 5)
            print("SECOND_ROUTE_FULL_C2|N=%d|u=%s|x=%s|y=%s|exact_C2=%s|rust_C2=%s|json=0" % (n, u, x, y, decimal(c2), decimal(read_c2)))
            if "P2_over_N2_ppm" in row:
                # <(n+ - n-)^2>/N^2 from the level's slope in kappa_c. The operator is even under the exchange, so an exact doublet moves as one. It moves the level by up to N^2 kappa_c, so the step is finer than for C2.
                fine = F(1, 1 << 18)
                p2 = (full_ground(n, x, u, y, F(0), F(1, 1 << 52), kappa_c=fine) - full_ground(n, x, u, y, F(0), F(1, 1 << 52), kappa_c=-fine)) / (2 * fine) / (n * n)
                read_p2 = F(int(row["P2_over_N2_ppm"]), 10 ** 6)
                good = good and abs(p2 - read_p2) < F(1, 10 ** 5)
                print("SECOND_ROUTE_FULL_P2|N=%d|u=%s|x=%s|y=%s|exact_P2=%s|rust_P2=%s|json=0" % (n, u, x, y, decimal(p2), decimal(read_p2)))
        bad += not good
        count += 1
        print("SECOND_ROUTE_FULL|N=%d|u=%s|x=%s|y=%s|exact_E=%s|rust_E=%s|exact_A=%s|rust_A=%s|exact_B=%s|rust_B=%s|json=0" % (n, u, x, y, decimal(e), decimal(read_e), decimal(a), decimal(read_a), decimal(b), decimal(read_b)))
    print("SECOND_ROUTE_FULL_DONE|rows=%d|bad=%d|json=0" % (count, bad))
    return 1 if bad or not count else 0


def compare_top(path, n_min):
    """The P = 0 rows at N >= n_min with delta >= 1, whose ground state sits at low j, against exact o^2 and d on a block of 6000 states, at 2^320 in integers."""
    bits, one = 320, 1 << 320
    def entries(n, u, x, j_top, step=F(0)):
        return [(((x + step) * F(2 * j, n) + u * F((n - 2 * j) * 2 * j + j * j, n * n)).numerator << bits) // ((x + step) * F(2 * j, n) + u * F((n - 2 * j) * 2 * j + j * j, n * n)).denominator for j in range(j_top + 1)]
    def count(d, o, lam):
        q = d[0] - lam or -1
        total = int(q < 0)
        for k in range(1, len(d)):
            q = (d[k] - lam - (o[k - 1] << bits) // q) or -1
            total += q < 0
        return total
    def level(d, o, index, guess, width):
        lo, hi = guess - width, guess + width
        while count(d, o, lo) > index:
            lo -= width
            width *= 4
        while count(d, o, hi) <= index:
            hi += width
            width *= 4
        while hi - lo > 1 << (bits - 170):
            mid = (lo + hi) >> 1
            if count(d, o, mid) > index:
                hi = mid
            else:
                lo = mid
        return (lo + hi) >> 1
    bad, total = 0, 0
    for line in open(path, encoding="utf-8").read().splitlines():
        if not line.startswith("POLARITON_SECTOR|"):
            continue
        row = dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f)
        n, u, x = int(row["N"]), F(row["u"]), F(row["x"])
        if n < n_min or row["P"] != "0" or u + x < 1:
            continue
        j_top = 6000
        o = [(((j + 1) * (j + 1) * (n - 2 * j) * (n - 2 * j - 1)) << bits) // n ** 4 for j in range(j_top)]
        d = entries(n, u, x, j_top)
        guess = (int(row["e_at_2^60"]) << (bits - 60))
        e0 = level(d, o, 0, guess, one >> 60)
        gap_read = F(int(row["gap_ppb"]), 10 ** 9)
        e1 = level(d, o, 1, e0 + (gap_read.numerator << bits) // (gap_read.denominator * n), one >> 40)
        step = F(1, 1 << 70)
        up = level(entries(n, u, x, j_top, step), o, 0, e0, one >> 60)
        down = level(entries(n, u, x, j_top, -step), o, 0, e0, one >> 60)
        jbar = F(up - down, one) / (2 * step) * n / 2
        gap = F(e1 - e0, one) * n
        read_jbar = F(int(row["jbar_ppb"]), 10 ** 9)
        off_jbar, off_gap = abs(read_jbar / jbar - 1) * 10 ** 6, abs(gap_read / gap - 1) * 10 ** 6
        good = off_jbar <= 50 and off_gap <= 10
        bad += not good
        total += 1
        print("SECOND_ROUTE_TOP|N=%d|u=%s|x=%s|exact_jbar=%s|rust_jbar=%s|off_ppm=%d|exact_gap=%s|rust_gap=%s|off_ppm=%d|json=0" % (n, u, x, decimal(jbar), decimal(read_jbar), off_jbar, decimal(gap), decimal(gap_read), off_gap))
    print("SECOND_ROUTE_TOP_DONE|rows=%d|bad=%d|json=0" % (total, bad))
    return 1 if bad or not total else 0


def taylor(n, x, u, y, t, terms):
    """psi(t) from |N,0,0>, as exact power series in the unnormalized Fock basis, where a and a^dag act rationally."""
    states = basis(n)
    index = {s: i for i, s in enumerate(states)}
    size = len(states)
    links = [[] for _ in range(size)]
    pn = F(1, n)
    for (p, m), i in index.items():
        n0 = n - p - m
        links[i].append((i, x * (p + m) + u * pn * (n0 * (p + m) + p * m)))
        if n0 >= 2:
            links[index[(p + 1, m + 1)]].append((i, pn * n0 * (n0 - 1)))  # a+^dag a-^dag a0 a0 on |n0,p,m>' gives n0(n0-1)|n0-2,p+1,m+1>'
        if p >= 1 and m >= 1:
            links[index[(p - 1, m - 1)]].append((i, pn * p * m))  # a0^dag a0^dag a+ a- gives p m |n0+2,p-1,m-1>'
        if y:
            if n0 >= 1:
                links[index[(p + 1, m)]].append((i, -y * n0))
                links[index[(p, m + 1)]].append((i, -y * n0))
            if p >= 1:
                links[index[(p - 1, m)]].append((i, -y * p))
            if m >= 1:
                links[index[(p, m - 1)]].append((i, -y * m))
    vector = [F(0)] * size
    vector[index[(0, 0)]] = F(1)
    re, im = list(vector), [F(0)] * size
    coefficient = F(1)
    for k in range(1, terms + 1):
        fresh = [F(0)] * size
        for i, row in enumerate(links):
            total = F(0)
            for j, value in row:
                if vector[j]:
                    total += value * vector[j]
            fresh[i] = total
        vector = fresh
        coefficient = coefficient * t / k
        phase = k % 4  # (-i)^k
        for i, value in enumerate(vector):
            if value:
                if phase == 0:
                    re[i] += coefficient * value
                elif phase == 1:
                    im[i] -= coefficient * value
                elif phase == 2:
                    re[i] -= coefficient * value
                else:
                    im[i] += coefficient * value
    weight = {}
    for (p, m) in states:
        n0 = n - p - m
        weight[(p, m)] = F(factorial(n0) * factorial(p) * factorial(m), factorial(n))
    norm, pairs, a_value = F(0), F(0), F(0)
    for (p, m), i in index.items():
        n0 = n - p - m
        size_sq = (re[i] * re[i] + im[i] * im[i]) * weight[(p, m)]
        norm += size_sq
        pairs += size_sq * (p + m)
        # <a0^dag a+> and <a-^dag a0>, with |n>' overlaps of the unnormalized basis.
        if p >= 1:
            target = index[(p - 1, m)]
            overlap = weight[(p - 1, m)] * p  # a0^dag a+ |n0,p,m>' = p |n0+1,p-1,m>'
            a_value += overlap * (re[target] * re[i] + im[target] * im[i])
        if n0 >= 1:
            target = index[(p, m + 1)]
            overlap = weight[(p, m + 1)] * n0  # a-^dag a0 |n0,p,m>' = n0 |n0-1,p,m+1>'
            a_value += overlap * (re[target] * re[i] + im[target] * im[i])
    return norm, pairs / 2, a_value


def convert_point(n, x, u, y, t, terms):
    """pairs, <A>, <B>, C1 and C2 of psi(t) from |N,0,0>, from the exact power series."""
    states = basis(n)
    index = {s: i for i, s in enumerate(states)}
    size = len(states)
    links = [[] for _ in range(size)]
    pn = F(1, n)
    for (p, m), i in index.items():
        n0 = n - p - m
        links[i].append((i, x * (p + m) + u * pn * (n0 * (p + m) + p * m)))
        if n0 >= 2:
            links[index[(p + 1, m + 1)]].append((i, pn * n0 * (n0 - 1)))
        if p >= 1 and m >= 1:
            links[index[(p - 1, m - 1)]].append((i, pn * p * m))
        if n0 >= 1:
            links[index[(p + 1, m)]].append((i, -y * n0))
            links[index[(p, m + 1)]].append((i, -y * n0))
        if p >= 1:
            links[index[(p - 1, m)]].append((i, -y * p))
        if m >= 1:
            links[index[(p, m - 1)]].append((i, -y * m))
    vector = [F(0)] * size
    vector[index[(0, 0)]] = F(1)
    re, im = list(vector), [F(0)] * size
    coefficient = F(1)
    for k in range(1, terms + 1):
        vector = [sum((value * vector[j] for j, value in row if vector[j]), F(0)) for row in links]
        coefficient = coefficient * t / k
        phase = k % 4  # (-i)^k
        for i, value in enumerate(vector):
            if value:
                if phase == 0:
                    re[i] += coefficient * value
                elif phase == 1:
                    im[i] -= coefficient * value
                elif phase == 2:
                    re[i] -= coefficient * value
                else:
                    im[i] += coefficient * value
    weight = {(p, m): F(factorial(n - p - m) * factorial(p) * factorial(m), factorial(n)) for (p, m) in states}

    def inner(target, i):
        return re[target] * re[i] + im[target] * im[i]

    norm, pairs, a_value, b_value, n0_pairs, np_nm, re_p = F(0), F(0), F(0), F(0), F(0), F(0), F(0)
    for (p, m), i in index.items():
        n0 = n - p - m
        size_sq = (re[i] * re[i] + im[i] * im[i]) * weight[(p, m)]
        norm += size_sq
        pairs += size_sq * (p + m)
        n0_pairs += size_sq * n0 * (p + m)
        np_nm += size_sq * p * m
        if p >= 1:
            a_value += weight[(p - 1, m)] * p * inner(index[(p - 1, m)], i)  # a0^dag a+ gives p |n0+1,p-1,m>'
            b_value += weight[(p - 1, m + 1)] * p * inner(index[(p - 1, m + 1)], i)  # a-^dag a+ gives p |n0,p-1,m+1>'
        if n0 >= 1:
            a_value += weight[(p, m + 1)] * n0 * inner(index[(p, m + 1)], i)  # a-^dag a0 gives n0 |n0-1,p,m+1>'
        if n0 >= 2:
            re_p += weight[(p + 1, m + 1)] * n0 * (n0 - 1) * inner(index[(p + 1, m + 1)], i)  # P gives n0(n0-1) |n0-2,p+1,m+1>'
    c1 = 2 * (n0_pairs + 2 * re_p) / (n * (n - 1))
    c2 = 2 * np_nm / (n * (n - 1))
    return norm, pairs / 2, a_value, b_value, c1, c2


def compare_convert(path):
    bad = 0
    count = 0
    limit = F(1, 10 ** 6)
    for line in open(path, encoding="utf-8").read().splitlines():
        if not line.startswith("POLARITON_TAYLOR_CONVERT|"):
            continue
        row = dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f)
        n = int(row["N"])
        x, u, y, t = F(row["x"]), F(row["u"]), F(row["y"]), F(row["t"])
        norm, pair, a_value, b_value, c1, c2 = convert_point(n, x, u, y, t, 8 * n + 120)
        read = [F(int(row[name]), 10 ** 9) for name in ("jbar_ppb", "A_ppb", "B_ppb", "C1_ppb", "C2_ppb", "f_ppb")]
        exact = [pair, a_value, b_value, c1, c2, 2 * pair / n]
        off = max(abs(p - q) for p, q in zip(read, exact))
        good = abs(norm - 1) < F(1, 10 ** 12) and off < limit
        bad += not good
        count += 1
        print("SECOND_ROUTE_CONVERT|N=%d|x=%s|y=%s|t=%s|exact_jbar=%s|exact_A=%s|exact_B=%s|exact_C1=%s|exact_C2=%s|largest_off_1e-9=%d|json=0" % (n, x, y, t, decimal(pair), decimal(a_value), decimal(b_value), decimal(c1), decimal(c2), off * 10 ** 9))
    print("SECOND_ROUTE_CONVERT_DONE|rows=%d|bad=%d|json=0" % (count, bad))
    return 1 if bad or not count else 0


def compare_taylor(path):
    bad = 0
    count = 0
    for line in open(path, encoding="utf-8").read().splitlines():
        if not line.startswith("POLARITON_TAYLOR_POINT|"):
            continue
        row = dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f)
        n = int(row["N"])
        x, u, y, t = F(row["x"]), F(row["u"]), F(row["y"]), F(row["t"])
        norm, pair, a_value = taylor(n, x, u, y, t, 8 * n + 120)
        off_norm = abs(norm - 1)
        read_pair, read_a = F(int(row["jbar_ppb"]), 10 ** 9), F(int(row["A_ppb"]), 10 ** 9)
        good = off_norm < F(1, 10 ** 12) and abs(pair - read_pair) < F(1, 1000) and abs(a_value - read_a) < F(1, 1000)
        bad += not good
        count += 1
        print("SECOND_ROUTE_TAYLOR|N=%d|u=%s|x=%s|y=%s|t=%s|exact_jbar=%s|rust_jbar=%s|exact_A=%s|rust_A=%s|series_norm_off_1e-12=%d|json=0" % (n, u, x, y, t, decimal(pair), decimal(read_pair), decimal(a_value), decimal(read_a), off_norm * 10 ** 12))
    print("SECOND_ROUTE_TAYLOR_DONE|rows=%d|bad=%d|json=0" % (count, bad))
    return 1 if bad or not count else 0


def main():
    what = sys.argv[1]
    if what == "hand":
        return hand()
    if what == "mathieu":
        for text in sys.argv[2:]:
            print("MATHIEU|q=%s|f_ppm=%d|json=0" % (text, mathieu(F(text)) * 10 ** 6))
        return 0
    if what == "sector_compare":
        return compare_sector(sys.argv[2], int(sys.argv[3]))
    if what == "full_compare":
        return compare_full(sys.argv[2], int(sys.argv[3]))
    if what == "taylor_compare":
        return compare_taylor(sys.argv[2])
    if what == "convert_compare":
        return compare_convert(sys.argv[2])
    if what == "top_compare":
        return compare_top(sys.argv[2], int(sys.argv[3]))
    return 2


if __name__ == "__main__":
    sys.exit(main())
