# Reads of the filed receipt that the reader does not make: signs past the f gate, the below-edge sign at low s, and the energy rebuilt from a row's other fields.
from fractions import Fraction as F

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
REC = open(W + "/clean/polariton/RECEIPT.hbp", encoding="utf8").read().splitlines()


def rows(tag):
    out = []
    for l in REC:
        if l.startswith(tag + "|"):
            out.append(dict(f.split("=", 1) for f in l.split("|")[1:] if "=" in f))
    return out


def sinh_cosh(square):
    one = 1 << 200
    v = (F(square).numerator << 200) // F(square).denominator
    a, b, chz, shc = one, one, one, one
    for k in range(1, 400):
        a = (a * v >> 200) // ((2 * k - 1) * (2 * k))
        b = (b * v >> 200) // ((2 * k) * (2 * k + 1))
        chz += a
        shc += b
    return F(shc, one), F(chz, one)


# ---- Conversion signs on all 94 rows, and the gate each row falls in.
conv = rows("POLARITON_QUENCH_CONVERSION")
tally = {}
exceptions = []
for r in conv:
    n, t = int(r["N"]), int(r["t"])
    y, delta = F(r["y"]), F(r["delta"])
    square = (1 - delta * delta) * t * t
    shc, chz = sinh_cosh(square)
    j0 = shc * shc * t * t
    coh = 2 * n * y * y * ((chz - 1) ** 2 / (1 + delta) ** 2 + j0)
    f_want = (2 * j0 + coh) / n
    gate = "read" if n >= 243 and f_want <= F(1, 10) else ("N81" if n < 243 else "f_above_1/10")
    a, b = int(r["A_ppb"]), int(r["B_ppb"])
    d = tally.setdefault(gate, [0, 0, 0])
    d[0] += 1
    d[1] += a < 0
    d[2] += b > 0
    if not (a < 0 and b > 0):
        exceptions.append("N=%d,delta=%s,y=%s,t=%d,A_ppb=%d,B_ppb=%d,f_want=%.3s" % (n, delta, y, t, a, b, str(float(f_want))) if False else "N=%d,delta=%s,y=%s,t=%d,A_ppb=%d,B_ppb=%d,f_want_ppm=%d" % (n, delta, y, t, a, b, f_want * 10 ** 6))
for g, v in tally.items():
    print("CONVERSION_SIGNS|gate=%s|rows=%d|A_negative=%d|B_positive=%d|json=0" % (g, v[0], v[1], v[2]))
print("CONVERSION_SIGN_EXCEPTIONS|count=%d|rows=%s|json=0" % (len(exceptions), ";".join(exceptions)))

# ---- Below-edge sign of <B> at every s.
win = rows("POLARITON_PIN_WINDOW")
below = [("1", "-1/4"), ("1", "-1/8"), ("1/2", "-1/4"), ("3/4", "-1/8")]
for u, x in below:
    du, dx = F(u), F(x)
    sign = 1 if du - dx - 1 > 0 else -1
    for n in (81, 243, 729):
        got = [r for r in win if r["u"] == u and r["x"] == x and int(r["N"]) == n]
        if not got:
            continue
        cells = []
        for r in got:
            b = int(r["B_ppb"])
            cells.append("s=%s:B=%d:ok=%d" % (r["s"], b, int(b * sign > 0)))
        print("BELOW_SIGN|u=%s|x=%s|N=%d|want_sign=%d|%s|json=0" % (u, x, n, sign, ",".join(cells)))

# ---- Inside: <B> sign, <A> sign (<A> sign_follows_y is frozen at the central point only).
ins = [("1/4", "-1/4"), ("1/4", "0"), ("3/4", "0"), ("3/4", "1/8"), ("1/2", "1/4")]
bad = 0
for u, x in ins:
    for r in win:
        if r["u"] == u and r["x"] == x and r["s"] != "0" and int(r["N"]) >= 243:
            bad += not (int(r["A_ppb"]) > 0 and int(r["B_ppb"]) < 0)
print("INSIDE_SIGNS|rows_with_A_not_positive_or_B_not_negative=%d|json=0" % bad)

# ---- P2 read on every window row.
for u, x in ins + below:
    for n in (3, 9, 81, 243, 729):
        got = [r for r in win if r["u"] == u and r["x"] == x and int(r["N"]) == n]
        if got:
            print("P2_ROW|u=%s|x=%s|N=%d|%s|json=0" % (u, x, n, ",".join("s=%s:%s" % (r["s"], r["P2_over_N2_ppm"]) for r in got)))

# ---- The energy rebuilt from the row's other fields, at u = 1: E = 2x jbar + ((N-1)/2)(C1 + C2) - 2y<A>.
for tag in ("POLARITON_QUENCH_CONVERSION", "POLARITON_TAYLOR_CONVERT"):
    largest_diff, over, largest_e = F(0), 0, 0
    lines = []
    can_see = 0
    for r in rows(tag):
        n = int(r["N"])
        x, u, y = F(r["x"]), F(r["u"]), F(r["y"])
        jbar, a = F(int(r["jbar_ppb"]), 10 ** 9), F(int(r["A_ppb"]), 10 ** 9)
        c1, c2 = F(int(r["C1_ppb"]), 10 ** 9), F(int(r["C2_ppb"]), 10 ** 9)
        if u == 1:
            rebuilt = 2 * x * jbar + F(n - 1, 2) * (c1 + c2) - 2 * y * a
        else:
            # u != 1: wk and np_nm enter with different weights, and Re<P> has no ppb field. Rows at u = 1/2 stay out.
            continue
        printed = F(int(r["energy_off_1e-9"]), 10 ** 9)
        bound = (2 * abs(x) + (n - 1) + 2 * abs(y) + 2) * F(1, 10 ** 9)
        diff = abs(rebuilt - printed)
        largest_diff = max(largest_diff, diff / bound)
        over += diff > bound
        largest_e = max(largest_e, abs(int(r["energy_off_1e-9"])))
        can_see += abs(printed) > 2 * bound
        lines.append("N=%d,delta=%s,y=%s,t=%s,printed=%d,rebuilt_1e-9=%d,bound_1e-9=%d" % (n, r["delta"], r["y"], r["t"], int(r["energy_off_1e-9"]), rebuilt * 10 ** 9, bound * 10 ** 9))
    print("ENERGY_REBUILT|tag=%s|rows=%d|over_bound=%d|largest_diff_over_bound_ppm=%d|largest_printed_1e-9=%d|rows_where_printed_exceeds_twice_the_bound=%d|json=0" % (tag, len(lines), over, largest_diff * 10 ** 6, largest_e, can_see))
    for l in lines[:12]:
        print("ENERGY_REBUILT_ROW|tag=%s|%s|json=0" % (tag, l))
    print("ENERGY_ROWS_LARGEST|tag=%s|%s|json=0" % (tag, ";".join(sorted(lines, key=lambda s: -abs(int(s.split("printed=")[1].split(",")[0])))[:8])))

# ---- The printed energy_off at each tag, by N.
for tag in ("POLARITON_QUENCH", "POLARITON_QUENCH_PIN", "POLARITON_QUENCH_OTHER_U", "POLARITON_CONTROL_NO_BOSE", "POLARITON_TAYLOR_CONVERT", "POLARITON_QUENCH_CONVERSION"):
    by = {}
    for r in rows(tag):
        by.setdefault(int(r["N"]), []).append(int(r["energy_off_1e-9"]))
    print("ENERGY_PRINTED|tag=%s|%s|json=0" % (tag, "|".join("N=%d:rows=%d:largest_abs=%d:zero_rows=%d" % (n, len(v), max(abs(e) for e in v), sum(e == 0 for e in v)) for n, v in sorted(by.items()))))
