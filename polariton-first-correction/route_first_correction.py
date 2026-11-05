# A route that shares no code with the engine, for what the certificate rests on. Integers and fractions only.
#
# usage: route_first_correction.py bessel ENGINE RECEIPT [RECEIPT ...]   the engine's coefficient tables and series tail against exact big-integer series
#        route_first_correction.py rows ENGINE                           the engine's Hamiltonian against one built here in the full three-mode Fock space
#        route_first_correction.py integrator CHEBDRV_DIR CHEB_EXE TABLES RECEIPT THREADS   the second seat's separate propagator on the receipt's blocks
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
        exact = exact_bessel_scaled(z, len(table) - 1)
        off = max(abs(a - b) for a, b in zip(table, exact))
        worst = max(worst, off)
        # The certificate takes 4 units per coefficient.
        check("bessel_table_E=%d_W=%d" % (big_e, w), off <= 4, "z=%d/%d|table_length=%d|worst_units=%d|limit_units=4" % (big_e, 1 << w, len(table), off))
        # What the table drops, past its last entry, stays under the unit, so the series at this degree is the certified one.
        rho = majorant(degree, z)
        windows = (int(r["t"])) << w
        printed_poly = Fr(int(r["eps_poly_e18"]), 10 ** 18)
        check("series_tail_covered_E=%d_W=%d" % (big_e, w), rho * windows <= printed_poly + Fr(1, 10 ** 18) + Fr(windows, 1 << 60), "rho_times_windows_e24=%d|printed_eps_poly_e18=%d" % ((rho * windows * 10 ** 24).__floor__(), int(r["eps_poly_e18"])))
    say("FC_ROUTE_BESSEL|tables=%d|worst_units_of_2^-62=%d" % (len(seen), worst))
    finish("bessel")


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
        (8, 8, "1/4", "1/3"),
        (8, 5, "-1/4", "1/5"),
        (9, 4, "1/2", "-1/7"),
        (12, 12, "0", "1/9"),
        (30, 12, "-1/4", "1/81"),
        (40, 9, "1/4", "1/324"),
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


# ---- The second seat's propagator, on the same blocks.


def route_integrator(drv_dir, cheb_exe, tables, receipt, threads):
    sys.path.insert(0, drv_dir)
    import chebdrv

    chebdrv.EXE = cheb_exe
    chebdrv.TABLES = tables
    rows = receipt_rows([receipt])
    say("FC_ROUTE_START|mode=integrator|rows=%d" % len(rows))
    limit = 10 ** 4  # 10^-14, in units of 10^-18
    for r in rows:
        n, k, t = int(r["N"]), int(r["K"]), int(r["t"])
        delta, y = Fr(r["delta"]), Fr(r["y"])
        got = chebdrv.run_chain(n, k, 1, delta, y, [Fr(t)], threads=int(threads), moments=0)
        them = chebdrv.parse_row(got[0])
        c_off = abs(int(them["C1_e18"]) - int(r["C1_e18"]))
        a_off = abs(int(them["A1_e18"]) - int(r["A1_e18"]))
        check("second_seat_propagator_N=%d_K=%d_delta=%s_y=%s_t=%d" % (n, k, delta, y, t), c_off <= limit and a_off <= limit, "C1_off_e18=%d|A1_off_e18=%d|limit_e18=%d" % (c_off, a_off, limit))
    finish("integrator")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "bessel":
        route_bessel(sys.argv[2], sys.argv[3:])
    elif mode == "rows":
        route_rows(sys.argv[2])
    elif mode == "integrator":
        route_integrator(*sys.argv[2:7])
    else:
        sys.stderr.write("usage: route_first_correction.py bessel|rows|integrator ...\n")
        sys.exit(2)


main()
