# A route that shares no code with the engine, for what the certificate rests on. Integers and fractions only.
#
# usage: route_first_correction.py bessel ENGINE RECEIPT [RECEIPT ...]   the engine's coefficient tables and series tail against exact big-integer series
#        route_first_correction.py rows ENGINE                           the engine's Hamiltonian against one built here in the full three-mode Fock space
#        route_first_correction.py integrator CHEBDRV_DIR CHEB_EXE TABLES RECEIPT THREADS   the second seat's separate propagator on the receipt's blocks
#        route_first_correction.py certificate ENGINE                    the certificate walked here on small blocks, against the engine's rows there
import re
import subprocess
import sys
from fractions import Fraction as Fr
from math import isqrt

sys.dont_write_bytecode = True
FAILED = []


def say(text):
    sys.stdout.write(text + "|json=0\n")
    sys.stdout.flush()


def check(name, ok, detail=""):
    if not ok:
        FAILED.append(name)
    say("FC_ROUTE|name=%s|result=%s%s" % (name, "PASS" if ok else "FAIL", ("|" + detail) if detail else ""))


def finish(mode):
    say("FC_ROUTE_DONE|mode=%s|failed=%d|names=%s" % (mode, len(FAILED), ",".join(FAILED) or "none"))
    if FAILED:
        sys.exit(1)


def fields(line):
    out = {}
    for part in line.strip().split("|")[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            out[key] = value
    return out


def receipt_rows(paths):
    rows = []
    for path in paths:
        for line in open(path, encoding="utf-8", newline=""):
            if line.startswith("POLARITON_FIRST_CORRECTION_READ|"):
                rows.append(fields(line))
    return rows


# ---- Bessel, from the defining series, in exact fractions.


def exact_bessel_scaled(z, k_top, bits=62):
    """2^bits J_k(z), floored, for k in 0..k_top, from the alternating series summed exactly until its terms fall under 2^-(bits + 40)."""
    half = z / 2
    half_sq = half * half
    out = []
    factorial_k = 1
    power_k = Fr(1)
    limit = Fr(1, 1 << (bits + 40))
    for k in range(k_top + 1):
        if k:
            factorial_k *= k
            power_k *= half
        term = power_k / factorial_k
        total = Fr(0)
        m = 0
        while True:
            total += term
            m += 1
            term = -term * half_sq / (m * (m + k))
            # Past the peak the terms fall in size and alternate, so the remainder is below the next term.
            if abs(term) < limit and m > int(half) + 1:
                break
        out.append((total * (1 << bits)).__floor__())
    return out


def majorant(m0, z):
    """Sum over m >= m0 of 2 (z/2)^m/m!, exact until the ratio falls under 1/2, with the geometric rest added outward."""
    half = z / 2
    term = Fr(1)
    for m in range(1, m0 + 1):
        term = term * half / m
    total = Fr(0)
    m = m0
    while True:
        total += 2 * term
        ratio = half / (m + 1)
        if ratio <= Fr(1, 2) and term < Fr(1, 1 << 90):
            total += 2 * 2 * term * ratio
            return total
        term = term * ratio
        m += 1


def route_bessel(engine, paths):
    rows = receipt_rows(paths)
    seen = {}
    for r in rows:
        w = int(r["window"].split("^-")[1])
        seen.setdefault((int(r["E"]), w), r)
    say("FC_ROUTE_START|mode=bessel|rows=%d|distinct_E_and_window=%d" % (len(rows), len(seen)))
    worst = 0
    for (big_e, w), r in sorted(seen.items()):
        z = Fr(big_e, 1 << w)
        text = subprocess.run([engine, "bessel", "%d/%d" % (big_e, 1 << w)], capture_output=True, text=True, check=True).stdout
        table = [int(fields(line)["J_s62"]) for line in text.splitlines() if line.startswith("BESSEL|")]
        degree = int(r["degree"])
        # Past the table's end its absent entries read as 0, up to two past the series' degree.
        exact = exact_bessel_scaled(z, max(len(table) - 1, degree + 2))
        off = max(abs((table[i] if i < len(table) else 0) - exact[i]) for i in range(len(exact)))
        worst = max(worst, off)
        # The certificate takes 4 units per coefficient.
        check("bessel_table_E=%d_W=%d" % (big_e, w), off <= 4, "z=%d/%d|table_length=%d|worst_units=%d|limit_units=4" % (big_e, 1 << w, len(table), off))
    say("FC_ROUTE_BESSEL|tables=%d|worst_units_of_2^-62=%d" % (len(seen), worst))
    route_certificate_parts(rows)
    finish("bessel")


def even_up(n, k, y, q, m):
    """Upward elements of H from the even state (q, m), p = q - m, as (target, mul, under, den) of mul sqrt(under)/den, from the operators' definitions."""
    p, n0 = q - m, n - q
    out = []
    if q + 2 <= k and n0 >= 2:
        out.append(((q + 2, m + 1), 1, (p + 1) * (m + 1) * n0 * (n0 - 1), n))
    if q + 1 <= k and n0 >= 1:
        out.append(((q + 1, m), abs(y.numerator), (p + 1) * n0 * (2 if p == m else 1), y.denominator))
        if p > m:
            out.append(((q + 1, m + 1), abs(y.numerator), (m + 1) * n0 * (2 if p == m + 1 else 1), y.denominator))
    return out


def block_gershgorin(n, k, delta, y, scale):
    """Gershgorin's interval of this block at this scale, outward."""
    index, size = {}, 0
    for q in range(k + 1):
        for m in range(q // 2 + 1):
            index[(q, m)] = size
            size += 1
    sums = [0] * size
    for q in range(k + 1):
        for m in range(q // 2 + 1):
            for target, mul, under, den in even_up(n, k, y, q, m):
                v = ((isqrt(under * scale * scale) + 1) * mul) // den + 1
                sums[index[(q, m)]] += v
                sums[index[target]] += v
    lo, hi = None, None
    for q in range(k + 1):
        for m in range(q // 2 + 1):
            d = ((delta - 1) * q + Fr((n - q) * q + (q - m) * m, n)) * scale
            s = sums[index[(q, m)]]
            lo = d.__floor__() - s if lo is None else min(lo, d.__floor__() - s)
            hi = d.__ceil__() + s if hi is None else max(hi, d.__ceil__() + s)
    return lo, hi


def block_schur(n, k, y):
    """The Schur test on the block's outgoing elements from shells K - 1 and K, at 2^20, outward, and the largest column's squared 2-norm, a lower bound on norm(B)^2."""
    col_max, column_two, row = 0, Fr(0), {}
    for q in (k - 1, k):
        for m in range(q // 2 + 1):
            col, two = 0, Fr(0)
            for target, mul, under, den in even_up(n, k + 2, y, q, m):
                if target[0] <= k:
                    continue
                v = ((isqrt(under << 40) + 1) * mul) // den + 1
                col += v
                two += Fr(mul * mul * under, den * den)
                row[target] = row.get(target, 0) + v
            col_max, column_two = max(col_max, col), max(column_two, two)
    return isqrt(col_max * max(row.values())) + 1, column_two


def route_certificate_parts(rows):
    """What the certificate rests on, row by row, from the operators' definitions: the series' tail, the reach, norm(B) and the spectral interval on the row's own block."""
    scale = 1 << 30
    blocks = {}
    tail_bad = reach_bad = norm_bad = interval_bad = 0
    for r in rows:
        n, k, t = int(r["N"]), int(r["K"]), int(r["t"])
        delta, y = Fr(r["delta"]), Fr(r["y"])
        w = int(r["window"].split("^-")[1])
        degree, big_e, c = int(r["degree"]), int(r["E"]), int(r["c"])
        windows = t << w
        if majorant(degree, Fr(big_e, 1 << w)) * windows > Fr(int(r["eps_poly_e18"]), 10 ** 18) + Fr(4, 10 ** 18):
            tail_bad += 1
        if int(r["reach"]) != 2 * degree + 1:
            reach_bad += 1
        key = (n, k, delta, y)
        if key not in blocks:
            blocks[key] = block_gershgorin(n, k, delta, y, scale)
        lo, hi = blocks[key]
        if max(c * scale - lo, hi - c * scale) > big_e * scale:
            interval_bad += 1
        printed = int(r["norm_B_s20"])
        if k < n:
            schur, column_two = block_schur(n, k, y)
            if abs(printed - schur) > 2 + schur // (1 << 18) or Fr(printed, 1 << 20) ** 2 < column_two:
                norm_bad += 1
        elif printed != 0:
            norm_bad += 1
    check("series_tail_covered_on_every_row", tail_bad == 0, "rows=%d|off=%d" % (len(rows), tail_bad))
    check("reach_is_2_degree_plus_1_on_every_row", reach_bad == 0, "rows=%d|off=%d" % (len(rows), reach_bad))
    check("norm_B_from_the_operators_on_every_row", norm_bad == 0, "rows=%d|off=%d" % (len(rows), norm_bad))
    check("spectral_interval_on_every_row's_block", interval_bad == 0, "rows=%d|blocks=%d|off=%d" % (len(rows), len(blocks), interval_bad))


# ---- The Hamiltonian, built in the full Fock space with its own formulas.

P = 400


def root_fixed(m):
    return isqrt(m << (2 * P))


def fock_h(n, x, u, y):
    """H on |n+, n-> with n0 = N - n+ - n-, in the operators' own definitions, as {(ket, bra): (coefficient Fraction, integer under the root)}."""
    basis = [(a, b) for a in range(n + 1) for b in range(n + 1 - a)]
    h = {}

    def add(bra, ket, coefficient, under):
        h.setdefault((bra, ket), []).append((coefficient, under))

    for a, b in basis:
        n0 = n - a - b
        add((a, b), (a, b), x * (a + b) + (u / n) * (n0 * (a + b) + a * b), 1)
        # P^dag = a+^dag a-^dag a0 a0 and P, each with coefficient 1/N.
        if n0 >= 2:
            add((a + 1, b + 1), (a, b), Fr(1, n), (a + 1) * (b + 1) * n0 * (n0 - 1))
        if a >= 1 and b >= 1:
            add((a - 1, b - 1), (a, b), Fr(1, n), a * b * (n0 + 1) * (n0 + 2))
        # -y [a0^dag (a+ + a-) + h.c.]
        if n0 >= 1:
            add((a + 1, b), (a, b), -y, (a + 1) * n0)
            add((a, b + 1), (a, b), -y, (b + 1) * n0)
        if a >= 1:
            add((a - 1, b), (a, b), -y, a * (n0 + 1))
        if b >= 1:
            add((a, b - 1), (a, b), -y, b * (n0 + 1))
    return basis, h


def even_vector(p, m):
    """The even state (q, m), p = q - m >= m, as {fock: fixed-point amplitude}."""
    if p == m:
        return {(p, m): 1 << P}
    amp = isqrt((1 << (2 * P)) // 2)
    return {(p, m): amp, (m, p): amp}


def odd_vector(p, m):
    amp = isqrt((1 << (2 * P)) // 2)
    return {(p, m): amp, (m, p): -amp}


def apply_h(h_rows, vector):
    """H on a fixed-point vector, with H's entries in fixed point too."""
    out = {}
    for ket, amp in vector.items():
        for bra, parts in h_rows.get(ket, ()):
            for coefficient, under in parts:
                element = (coefficient.numerator * root_fixed(under)) // coefficient.denominator
                out[bra] = out.get(bra, 0) + ((element * amp) >> P)
    return out


def dot(a, b):
    total = 0
    for key, value in a.items():
        if key in b:
            total += (value * b[key]) >> P
    return total


def route_rows(engine):
    cases = [
        (3, 3, "1/2", "1/3"),
        (8, 8, "3/4", "1/3"),
        (8, 5, "-3/4", "1/5"),
        (9, 4, "1/2", "-1/7"),
        (12, 12, "0", "1/9"),
        (30, 12, "-1/2", "1/81"),
        (40, 9, "3/4", "1/324"),
    ]
    say("FC_ROUTE_START|mode=rows|cases=%d" % len(cases))
    tolerance = 1 << (P - 340)
    for n, k_in, delta_text, y_text in cases:
        k = min(k_in, n)
        text = subprocess.run([engine, "rows", str(n), str(k), delta_text, y_text], capture_output=True, text=True, check=True).stdout.splitlines()
        head = fields(text[0])
        c, big_e, err_units = int(head["c"]), int(head["E"]), int(head["elem_err_units"])
        delta, y = Fr(delta_text), Fr(y_text)
        x = delta - 1
        basis, h = fock_h(n, x, Fr(1), y)
        by_ket = {}
        for (bra, ket), parts in h.items():
            by_ket.setdefault(ket, []).append((bra, parts))
        states = [fields(line) for line in text[1:] if line.startswith("H_STATE|")]
        labels = [(int(s["q"]), int(s["m"])) for s in states]
        expected = [(q, m) for q in range(k + 1) for m in range(q // 2 + 1)]
        check("states_are_the_even_block_N=%d_K=%d" % (n, k), labels == expected and int(head["even_states"]) == len(expected))
        vectors = {label: even_vector(label[0] - label[1], label[1]) for label in labels}
        images = {label: apply_h(by_ket, vectors[label]) for label in labels}
        gersh = 0
        bad = {"diag": 0, "pair": 0, "a": 0, "b": 0, "extra": 0, "scaled": 0, "odd": 0}
        scale = 1 << 62
        for s in states:
            q, m = int(s["q"]), int(s["m"])
            ket = (q, m)
            image = images[ket]
            diag_num, diag_den = s["diag"].split("/")
            diag = Fr(int(diag_num), int(diag_den))
            mine = dot(vectors[ket], image)
            if abs(mine - (diag.numerator << P) // diag.denominator) > tolerance:
                bad["diag"] += 1
            if abs(diag - c - Fr(int(s["d"]), scale) * big_e) > Fr(err_units * big_e, scale):
                bad["scaled"] += 1
            listed = {}
            for name, target, sign in (("pair", (q + 2, m + 1), 1), ("a", (q + 1, m), -1 if y > 0 else 1), ("b", (q + 1, m + 1), -1 if y > 0 else 1)):
                mul, under, den = (int(v) for v in s[name].split(","))
                value = sign * Fr(mul, den)
                listed[target] = (value, under)
                if target in vectors or mul:
                    theirs = (value.numerator * root_fixed(under)) // value.denominator if mul else 0
                    ours = dot(vectors[target], image) if target in vectors else theirs
                    if abs(theirs - ours) > tolerance:
                        bad[name] += 1
                    scaled = int(s[name + "_s"])
                    if abs(Fr(theirs, 1 << P) - Fr(scaled, scale) * big_e) > Fr((err_units + 1) * big_e, scale):
                        bad["scaled"] += 1
            # Nothing else couples upward, and the row's Gershgorin sum is covered by E.
            row = abs(diag - c)
            for label in labels:
                element = dot(vectors[label], image)
                if label == ket:
                    continue
                row += Fr(abs(element), 1 << P)
                up = label[0] > q
                if up and label not in listed and abs(element) > tolerance:
                    bad["extra"] += 1
                if abs(label[0] - q) > 2 and abs(element) > tolerance:
                    bad["extra"] += 1
            gersh = max(gersh, row)
            # The exchange-odd part of the same q never couples to the even block.
            for label in labels:
                p2, m2 = label[0] - label[1], label[1]
                if p2 > m2 and abs(dot(odd_vector(p2, m2), image)) > tolerance:
                    bad["odd"] += 1
        ok = all(v == 0 for v in bad.values())
        check("hamiltonian_N=%d_K=%d_delta=%s_y=%s" % (n, k, delta, y), ok, "|".join("%s_off=%d" % kv for kv in sorted(bad.items())))
        check("spectral_interval_N=%d_K=%d" % (n, k), gersh <= big_e, "gershgorin_e6=%d|E=%d|c=%d" % ((gersh * 10 ** 6).__floor__(), big_e, c))
    finish("rows")


# ---- The certificate recomputed from its own words on small blocks.

CP = 180
CERT_CASES = [(100, 40, "1/2", "1/20", 6, 2), (100, 40, "-1/2", "1/20", 6, 2), (100, 48, "0", "1/10", 6, 1), (40, 40, "1/2", "1/20", 6, 1)]


def cert_block(n, k, x, y):
    """PHP and the outgoing part of H on |a, b> with a + b <= k, by the operators' definitions, at 2^CP."""
    basis = [(a, q - a) for q in range(k + 1) for a in range(q + 1)]
    index = {s: i for i, s in enumerate(basis)}
    rows, leaks, diag = [[] for _ in basis], [[] for _ in basis], []
    for i, (a, b) in enumerate(basis):
        n0 = n - a - b
        d = x * (a + b) + Fr(n0 * (a + b) + a * b, n)
        diag.append((d.numerator << CP) // d.denominator)
        moves = []
        if n0 >= 2:
            moves.append(((a + 1, b + 1), Fr(1, n), (a + 1) * (b + 1) * n0 * (n0 - 1)))
        if a >= 1 and b >= 1:
            moves.append(((a - 1, b - 1), Fr(1, n), a * b * (n0 + 1) * (n0 + 2)))
        if n0 >= 1:
            moves.append(((a + 1, b), -y, (a + 1) * n0))
            moves.append(((a, b + 1), -y, (b + 1) * n0))
        if a >= 1:
            moves.append(((a - 1, b), -y, a * (n0 + 1)))
        if b >= 1:
            moves.append(((a, b - 1), -y, b * (n0 + 1)))
        for bra, coefficient, under in moves:
            element = (coefficient.numerator * isqrt(under << (2 * CP))) // coefficient.denominator
            if bra in index:
                rows[i].append((index[bra], element))
            else:
                leaks[i].append((bra, element))
    return basis, index, rows, leaks, diag


def cert_apply(rows, diag, v):
    out = [0] * len(v)
    for i, value in enumerate(v):
        if value:
            out[i] += (diag[i] * value) >> CP
            for t, element in rows[i]:
                out[t] += (element * value) >> CP
    return out


def cert_window(rows, diag, re, im, w):
    """exp(-i H 2^-w), its Taylor series, until the terms fall under 2^-(CP - 8)."""
    tr, ti, sr, si, j = re[:], im[:], re[:], im[:], 0
    while True:
        j += 1
        hr, hi = cert_apply(rows, diag, tr), cert_apply(rows, diag, ti)
        tr = [(value >> w) // j for value in hi]
        ti = [(-value >> w) // j for value in hr]
        sr = [a + b for a, b in zip(sr, tr)]
        si = [a + b for a, b in zip(si, ti)]
        if max(max(abs(v) for v in tr), max(abs(v) for v in ti)) < 256:
            return sr, si


def cert_compare(name, mine, theirs, relative, absolute):
    off = abs(Fr(theirs) - Fr(mine))
    limit = Fr(relative) * abs(Fr(mine)) + Fr(absolute)
    say("FC_ROUTE_CERT|name=%s|off_e24=%d|limit_e24=%d|result=%s" % (name, (off * 10 ** 24).__floor__(), (limit * 10 ** 24).__floor__(), "PASS" if off <= limit else "FAIL"))
    return off <= limit


def route_certificate(engine):
    """The engine's row at a small block against the same certificate walked here: the state in the Fock space window by window, the tail, the leak, norm(B), the rounding account, epsilon, the reads and their errors."""
    say("FC_ROUTE_START|mode=certificate|cases=%d" % len(CERT_CASES))
    e18 = 10 ** 18
    one = 1 << CP
    for n, k, delta_text, y_text, w, t in CERT_CASES:
        text = subprocess.run([engine, "point", str(n), str(k), delta_text, y_text, str(w), str(t)], capture_output=True, text=True, check=True).stdout
        r = fields([line for line in text.splitlines() if line.startswith("POLARITON_FIRST_CORRECTION_READ|")][0])
        delta, y = Fr(delta_text), Fr(y_text)
        big_e, degree, err_units, reach = int(r["E"]), int(r["degree"]), int(r["elem_err_units"]), int(r["reach"])
        z = Fr(big_e, 1 << w)
        windows = t << w
        mine_degree = 1
        while majorant(mine_degree, z) > Fr(8, 1 << 62):
            mine_degree += 1
        table = exact_bessel_scaled(z, degree + 1)
        weight = sum(((1 if j == 0 else 2) * abs(table[j]) >> 40) * (j * (j + 1) // 2 + 1) + 1 for j in range(degree + 1))
        dim = sum(q // 2 + 1 for q in range(k + 1))
        root = isqrt(dim) + 1
        per_window = Fr(((weight >> 22) + 1) * root * 4 + root * 4 + ((big_e >> w) + 1) * 8 * err_units + (degree + 1) * 16, 1 << 62)
        rho = Fr(int(r["eps_poly_e18"]), e18) / windows
        norm_b = Fr(block_schur(n, k, y)[0], 1 << 20) if k < n else Fr(0)
        basis, index, rows, leaks, diag = cert_block(n, k, delta - 1, y)
        re, im = [0] * len(basis), [0] * len(basis)
        re[0] = one
        first_shell = k + 1 - reach
        floor_states = sum(q // 2 + 1 for q in range(max(first_shell, 0), k + 1))
        eps_tail = tail_max = leak_max = leak_sum = Fr(0)
        for window in range(windows):
            if reach > k:
                tail = Fr(1)
            else:
                total = sum(re[i] * re[i] + im[i] * im[i] for i, s in enumerate(basis) if s[0] + s[1] >= first_shell)
                tail = Fr(isqrt((total >> (2 * CP - 84)) + floor_states) + 1, 1 << 42)
            tail_max = max(tail_max, tail)
            rr, ri = {}, {}
            for i, items in enumerate(leaks):
                for bra, element in items:
                    rr[bra] = rr.get(bra, 0) + ((element * re[i]) >> CP)
                    ri[bra] = ri.get(bra, 0) + ((element * im[i]) >> CP)
            lk = Fr(isqrt(sum(v * v for v in rr.values()) + sum(v * v for v in ri.values())), one)
            leak_max = max(leak_max, lk)
            leak_sum += lk / (1 << w)
            eps_tail += norm_b * (tail + rho + window * (per_window + rho)) / (1 << w)
            re, im = cert_window(rows, diag, re, im, w)
        sums = dict(q=0, pm=0, n0q=0, xd=0, xu=0, xl=0, sa=0, sb=0, p=0, a=0, b=0)
        for i, (a, b) in enumerate(basis):
            weight_i = re[i] * re[i] + im[i] * im[i]
            q, n0 = a + b, n - a - b
            sums["q"] += q * weight_i
            sums["pm"] += a * b * weight_i
            sums["n0q"] += n0 * q * weight_i
            sums["xd"] += (n0 * q) ** 2 * weight_i
            sums["xu"] += (a + 1) * (b + 1) * n0 * max(n0 - 1, 0) * weight_i
            sums["xl"] += a * b * (n0 + 1) * (n0 + 2) * weight_i
            sums["sa"] += (a + 1) * n0 * weight_i
            sums["sb"] += a * (n0 + 1) * weight_i
            for name, target, under, ok in (("p", (a + 1, b + 1), (a + 1) * (b + 1) * n0 * (n0 - 1), n0 >= 2), ("a", (a + 1, b), (a + 1) * n0, n0 >= 1), ("a", (a, b + 1), (b + 1) * n0, n0 >= 1), ("b", (a - 1, b + 1), a * (b + 1), a >= 1)):
                if ok and target in index:
                    other = index[target]
                    sums[name] += isqrt(under << (2 * CP)) * ((re[i] * re[other] + im[i] * im[other]) >> CP)
        scale = one * one
        c1 = 2 * (Fr(sums["n0q"], scale) + 2 * Fr(sums["p"], scale)) / (n * (n - 1))
        a_read, b_read = Fr(sums["a"], scale), Fr(sums["b"], scale)
        a1 = 2 * abs(a_read) / n
        read_x = Fr((1 << 38) + (dim * n * n >> 10) + 1, 1 << 60)
        read_s = Fr((1 << 39) + (dim * n >> 10) + 1, 1 << 60)
        eps = sum(Fr(int(r[name + "_e18"]), e18) for name in ("eps_tail", "eps_poly", "eps_round"))
        x_up = Fr(isqrt(sums["xd"]) + isqrt(sums["xu"]) + isqrt(sums["xl"]), one)
        s_up = 2 * Fr(isqrt(sums["sa"]) + isqrt(sums["sb"]), one)
        c1_err = 2 * (eps * (2 * x_up + ((n + 1) * (n + 1) + n) * eps) + read_x) / (n * (n - 1))
        a1_err = (eps * (2 * s_up + 2 * (n + 1) * eps) + read_s) / n
        unit = Fr(4, e18)
        tol = Fr(1, 10 ** 6)
        results = [
            cert_compare("degree", mine_degree, degree, 0, 1),
            cert_compare("reach", 2 * degree + 1, reach, 0, 0),
            cert_compare("norm_B", norm_b, Fr(int(r["norm_B_s20"]), 1 << 20), Fr(1, 1 << 16), 0),
            cert_compare("eps_poly", majorant(degree, z) * windows + Fr(windows, 1 << 62), Fr(int(r["eps_poly_e18"]), e18), 0, Fr(windows, 1 << 62) + unit),
            cert_compare("eps_round", per_window * windows, Fr(int(r["eps_round_e18"]), e18), tol, unit),
            cert_compare("eps_tail", eps_tail, Fr(int(r["eps_tail_e18"]), e18), tol, unit),
            cert_compare("tail_max", tail_max, Fr(int(r["tail_max_e18"]), e18), tol, unit),
            cert_compare("leak_max", leak_max, Fr(int(r["leak_max_e18"]), e18), tol, Fr(1, 1 << 40)),
            cert_compare("leak_sum", leak_sum, Fr(int(r["leak_sum_e18"]), e18), tol, Fr(1, 1 << 40)),
            cert_compare("eps", eps, Fr(int(r["eps_e18"]), e18), 0, 2 * unit),
            cert_compare("C1", c1, Fr(int(r["C1_e18"]), e18), 0, 4 * read_x / (n * (n - 1))),
            cert_compare("A1", a1, Fr(int(r["A1_e18"]), e18), 0, 2 * read_s / n),
            cert_compare("V2", a1 * a1 / (2 * c1), Fr(int(r["V2_e18"]), e18), Fr(1, 10 ** 5), unit),
            cert_compare("f", Fr(sums["q"], scale) / n, Fr(int(r["f_e18"]), e18), 0, Fr(1, 10 ** 12)),
            cert_compare("C2", 2 * Fr(sums["pm"], scale) / (n * (n - 1)), Fr(int(r["C2_e18"]), e18), 0, Fr(1, 10 ** 12)),
            cert_compare("A", a_read, Fr(int(r["A_e18"]), e18), 0, 2 * read_s),
            cert_compare("B", b_read, Fr(int(r["B_e18"]), e18), 0, Fr(1, 1 << 20)),
            cert_compare("C1_err", c1_err, Fr(int(r["C1_err_e18"]), e18), Fr(1, 100), unit),
            cert_compare("A1_err", a1_err, Fr(int(r["A1_err_e18"]), e18), Fr(1, 100), unit),
        ]
        check("certificate_recomputed_N=%d_K=%d_delta=%s_y=%s_t=%d" % (n, k, delta, y, t), all(results), "names=%d" % len(results))
    finish("certificate")


# ---- The second seat's propagator, on the same blocks.


def route_integrator(drv_dir, cheb_exe, tables, receipt, threads):
    sys.path.insert(0, drv_dir)
    import chebdrv

    chebdrv.EXE = cheb_exe
    chebdrv.TABLES = tables
    rows = receipt_rows([receipt])
    say("FC_ROUTE_START|mode=integrator|rows=%d" % len(rows))
    # The engine's read-out carries its square roots at 2^-24, and read_x, read_s in its point() account for them on C1 and A1. The propagator reads at 2^-62.
    # Measured at 2d77636 on the baseline's rows: C1 off 15507 and A1 off 6118833 at worst in 10^-18, and at N = 6561, K = 1200: C1 off 5, A1 off 53459.
    # f and C2 read populations, so they meet at the states' own rounding: measured at most 88 in 10^-18 on the same rows.
    states_limit = 10 ** 3  # 10^-15, in units of 10^-18
    for r in rows:
        n, k, t = int(r["N"]), int(r["K"]), int(r["t"])
        delta, y = Fr(r["delta"]), Fr(r["y"])
        got = chebdrv.run_chain(n, k, 1, delta, y, [Fr(t)], threads=int(threads), moments=0)
        them = chebdrv.parse_row(got[0])
        dim = int(r["even_states"])
        c_limit = 10 ** 18 * 2 * ((1 << 38) + (dim * n * n >> 10) + 1) // ((1 << 60) * n * (n - 1)) + states_limit
        a_limit = 10 ** 18 * ((1 << 39) + (dim * n >> 10) + 1) // ((1 << 60) * n) + states_limit
        c_off = abs(int(them["C1_e18"]) - int(r["C1_e18"]))
        a_off = abs(int(them["A1_e18"]) - int(r["A1_e18"]))
        d_off = abs(int(them["D2_e18"]) - int(r["D2_e18"]))
        f_off = abs(int(them["f_e18"]) - int(r["f_e18"]))
        c2_off = abs(int(them["C2_e18"]) - int(r["C2_e18"]))
        sign_off = abs(Fr(int(r["A_e18"]), n) - int(them["A_e18"])) + abs(Fr(int(r["B_e18"]), n) - int(them["B_e18"]))
        v2_inside = int(r["V2_hi_e18"]) < 0 or int(r["V2_lo_e18"]) - 2 <= int(them["V2_e18"]) <= int(r["V2_hi_e18"]) + 2
        ok = c_off <= c_limit and a_off <= a_limit and d_off <= a_limit and f_off <= states_limit and c2_off <= states_limit and sign_off <= a_limit and v2_inside
        check("second_seat_propagator_N=%d_K=%d_delta=%s_y=%s_t=%d" % (n, k, delta, y, t), ok, "C1_off_e18=%d|C1_limit_e18=%d|A1_off_e18=%d|A1_limit_e18=%d|D2_off_e18=%d|f_off_e18=%d|C2_off_e18=%d|A_and_B_over_N_off_e18=%d|V2_inside_interval=%d" % (c_off, c_limit, a_off, a_limit, d_off, f_off, c2_off, sign_off.__ceil__(), v2_inside))
    finish("integrator")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "bessel":
        route_bessel(sys.argv[2], sys.argv[3:])
    elif mode == "rows":
        route_rows(sys.argv[2])
    elif mode == "integrator":
        route_integrator(*sys.argv[2:7])
    elif mode == "certificate":
        route_certificate(sys.argv[2])
    else:
        sys.stderr.write("usage: route_first_correction.py bessel|rows|integrator ...\n")
        sys.exit(2)


main()
