# Reads the polariton receipt against polariton/PREDICTION.hbp, row by row, with the frozen tolerances written out here as they stand there.
# Integers and exact rationals only. It prints MET or MISS for each reading, and a miss stays a miss.
#   read_prediction.py RECEIPT
# json=0.
import sys
from fractions import Fraction as F
from math import isqrt


def rows(path):
    out = {}
    for line in open(path, encoding="utf-8").read().splitlines():
        if "|" not in line:
            continue
        tag, rest = line.split("|", 1)
        out.setdefault(tag, []).append(dict(f.split("=", 1) for f in rest.split("|") if "=" in f))
    return out


R = rows(sys.argv[1])
met, miss = 0, 0


def report(name, ok, read, want):
    global met, miss
    if ok:
        met += 1
    else:
        miss += 1
    print("POLARITON_READ|row=%s|result=%s|read=%s|predicted=%s|json=0" % (name, "MET" if ok else "MISS", read, want))


def within(value, target, tolerance):
    return abs(F(value) - F(target)) <= abs(F(target)) * F(tolerance)


def root(q, digits=6):
    """sqrt of a rational, in units of 10^-digits."""
    q = F(q) * 10 ** (2 * digits)
    return F(isqrt(q.numerator // q.denominator), 10 ** digits)


def sinh_cosh(square):
    """sinh(z)/z and cosh(z) for z^2 = square, a rational of either sign, at 2^200, in integers."""
    one = 1 << 200
    v = (F(square).numerator << 200) // F(square).denominator
    a, b, chz, shc = one, one, one, one
    for k in range(1, 400):
        a = (a * v >> 200) // ((2 * k - 1) * (2 * k))
        b = (b * v >> 200) // ((2 * k) * (2 * k + 1))
        chz += a
        shc += b
    return F(shc, one), F(chz, one)


def closed_jbar(delta, t):
    """sinh^2(gamma t)/gamma^2 with gamma^2 = 1 - delta^2: t^2 at the band edge and sin^2(omega t)/omega^2 outside, from the one series."""
    return sinh_cosh((1 - delta * delta) * t * t)[0] ** 2 * t * t


def closed_a1(delta, t, y):
    """4|y|(cosh(gamma t) - 1)/(1 + delta)."""
    return 4 * abs(y) * (sinh_cosh((1 - delta * delta) * t * t)[1] - 1) / (1 + delta)


def sector(n, u, x, p="0"):
    for r in R.get("POLARITON_SECTOR", []):
        if int(r["N"]) == n and F(r["u"]) == F(u) and F(r["x"]) == F(x) and int(r["P"]) == int(p):
            return r
    return None


BIG = [3 ** p for p in range(9, 14)]
TOP = [3 ** 14, 3 ** 15, 23887872, 3 ** 16]  # The frozen rows say N >= 19683, and the stage runs these for u = 1/2, x = 0 and x = 3/2.
ORDERED = [("0", "0"), ("0", "1/2"), ("0", "-1/2"), ("1/2", "0"), ("1/2", "1/4"), ("1", "-1/4"), ("1", "-1/8")]
for u, x in ORDERED:
    du, dx = F(u), F(x)
    delta = dx + du
    rho = (1 - delta) / (4 - 3 * du)
    rho0 = 1 - 2 * rho
    e = -(1 - delta) ** 2 / (4 - 3 * du)
    f = 2 * rho
    gap = root(4 * (4 - 3 * du) * rho * rho0)
    c2 = 2 * rho * rho
    c0 = (rho0 / rho - du) / 4
    for n in BIG + (TOP if (u, x) == ("1/2", "0") else []):
        r = sector(n, u, x)
        if r is None:
            report("sector_ordered_N=%d_u=%s_x=%s" % (n, u, x), False, "no_row", "row")
            continue
        tag = "N=%d_u=%s_x=%s" % (n, u, x)
        report("e_" + tag, within(F(int(r["e_ppb"]), 10 ** 9), e, F(2, 1000)), r["e_ppb"], str(e))
        report("f_" + tag, within(F(int(r["f_ppb"]), 10 ** 9), f, F(1, 100)), r["f_ppb"], str(f))
        report("gap_" + tag, within(F(int(r["gap_ppb"]), 10 ** 9), gap, F(2, 100)), r["gap_ppb"], str(gap.numerator * 10 ** 6 // gap.denominator) + "e-6")
        report("C2_" + tag, within(F(int(r["C2_ppm"]), 10 ** 6), c2, F(2, 100)), r["C2_ppm"], str(c2))
        report("C1N_" + tag, abs(int(r["C1_times_N_ppm"])) <= 8 * 10 ** 6, r["C1_times_N_ppm"], "abs_at_most_8e6")
        if n <= 3 ** 12:
            for p in (1, 2, 3):
                s = sector(n, u, x, str(p))
                if s is not None:
                    report("rotor_P=%d_%s" % (p, tag), within(F(int(s["N2_times_e_above_P0_ppm"]), 10 ** 6), c0 * p * p, F(3, 100)), s["N2_times_e_above_P0_ppm"], str(c0 * p * p))

for delta, jbar, gap in ((F(2), F(7735, 100000), F(346410, 100000)), (F(3, 2), F(17082, 100000), F(223607, 100000))):
    for u in ("0", "1/2", "1"):
        x = delta - F(u)
        for n in BIG + (TOP if (delta, u) == (F(2), "1/2") else []):
            r = sector(n, u, str(x))
            if r is None:
                report("sector_disordered_N=%d_u=%s_x=%s" % (n, u, x), False, "no_row", "row")
                continue
            tag = "N=%d_u=%s_x=%s" % (n, u, x)
            report("jbar_" + tag, within(F(int(r["jbar_ppb"]), 10 ** 9), jbar, F(2, 100)), r["jbar_ppb"], str(jbar.numerator * 100000 // jbar.denominator) + "e-5")
            report("gap_" + tag, within(F(int(r["gap_ppb"]), 10 ** 9), gap, F(2, 100)), r["gap_ppb"], str(gap.numerator * 100000 // gap.denominator) + "e-5")

for u, x in (("0", "1"), ("1/2", "1/2"), ("1", "0")):
    powers = [n for n in (3 ** p for p in range(1, 17)) if sector(n, u, x) is not None]
    top = powers[-4:]
    for a, b in zip(top, top[1:]):
        ra, rb = sector(a, u, x), sector(b, u, x)
        j = F(int(rb["jbar_ppb"]), int(ra["jbar_ppb"]))
        g = F(int(rb["gap_ppb"]), int(ra["gap_ppb"]))
        report("critical_jbar_ratio_u=%s_N=%d_to_%d" % (u, a, b), within(j, F(144225, 100000), F(5, 100)), (j * 10 ** 5).numerator // (j * 10 ** 5).denominator, "144225_e-5")
        report("critical_gap_ratio_u=%s_N=%d_to_%d" % (u, a, b), within(g, F(69336, 100000), F(5, 100)), (g * 10 ** 5).numerator // (g * 10 ** 5).denominator, "69336_e-5")

# The plane wave.
for u, x, want_below in (("1", "-1/4", True), ("1/2", "0", False)):
    n = 19683
    e0 = sector(n, u, x)
    top = sector(n, u, x, str(n))
    if e0 and top:
        below = int(top["e_at_2^60"]) < int(e0["e_at_2^60"])
        report("plane_wave_u=%s_x=%s" % (u, x), below == want_below, top["e_ppb"], "below_e0=%d" % int(want_below))
n = 19683
series = [sector(n, "1/2", "0", str(p)) for p in (0, n // 9, n // 3, 2 * n // 3, n)]
if all(series):
    values = [int(s["e_at_2^60"]) for s in series]
    report("e_rises_with_P_u=1/2_x=0", values == sorted(values), ",".join(s["e_ppb"] for s in series), "rising")


def pin(n, u, x, s):
    for r in R.get("POLARITON_PIN", []):
        if int(r["N"]) == n and F(r["u"]) == F(u) and F(r["x"]) == F(x) and r["s"] != "hand" and F(r["s"]) == F(s):
            return r
    return None


FQ = {"1/2": 9999, "1": 39944, "2": 156537, "4": 490857, "8": 776331, "16": 889412}
for n in (243, 729):
    zero = pin(n, "1/2", "0", "0")
    report("zero_field_A_N=%d" % n, abs(int(zero["A_ppb"])) <= 1000, zero["A_ppb"], "abs_at_most_1000_ppb")
    report("zero_field_B_N=%d" % n, abs(int(zero["B_ppb"])) <= 1000, zero["B_ppb"], "abs_at_most_1000_ppb")
    report("zero_field_C2_N=%d" % n, within(F(int(zero["C2_ppm"]), 10 ** 6), F(2, 25), F(5, 100)), zero["C2_ppm"], "80000")
    c2 = F(int(zero["C2_ppm"]), 10 ** 6)
    for s, f in FQ.items():
        r = pin(n, "1/2", "0", s)
        y = F(s) / n
        f = F(f, 10 ** 6)
        d2 = F(int(r["D2_ppm"]), 10 ** 6)
        a1 = F(int(r["A1_ppm"]), 10 ** 6)
        report("pin_D2_N=%d_s=%s" % (n, s), within(d2 / F(2, 5), f, F(1, 10)), r["D2_ppm"], str((f * F(2, 5) * 10 ** 6).numerator // (f * F(2, 5) * 10 ** 6).denominator))
        report("pin_A1_N=%d_s=%s" % (n, s), within(a1 / y, 2 * (1 + (1 + f) / 10), F(5, 100)), (a1 / y * 10 ** 6).numerator // (a1 / y * 10 ** 6).denominator, str((2 * (1 + (1 + f) / 10) * 10 ** 6).numerator // (2 * (1 + (1 + f) / 10) * 10 ** 6).denominator))
        report("pin_B_negative_N=%d_s=%s" % (n, s), int(r["B_ppb"]) < 0, r["B_ppb"], "negative")
        report("pin_A_positive_N=%d_s=%s" % (n, s), int(r["A_ppb"]) > 0, r["A_ppb"], "positive")
        if F(s) >= 4:
            conversion = root(2 * c2)
            report("conversion_N=%d_s=%s" % (n, s), within(d2, f * conversion, F(1, 10)), r["D2_ppm"], str((f * conversion * 10 ** 6).numerator // (f * conversion * 10 ** 6).denominator))
    for s in ("1/2", "1", "2", "4"):
        r = pin(n, "0", "0", s)
        d2 = F(int(r["D2_ppm"]), 10 ** 6)
        report("no_leading_order_D2_N=%d_s=%s" % (n, s), d2 / F(1, 2) <= F(1, 10), r["D2_ppm"], "at_most_50000")
        y = F(s) / n
        a1 = F(int(r["A1_ppm"]), 10 ** 6)
        report("no_leading_order_A1_N=%d_s=%s" % (n, s), within(a1 / y, 2, F(5, 100)), (a1 / y * 10 ** 6).numerator // (a1 / y * 10 ** 6).denominator, "2000000")
    for s in ("1/2", "1", "2", "4", "8", "16"):
        r = pin(n, "1/2", "3/2", s)
        y = F(s) / n
        a1 = F(int(r["A1_ppm"]), 10 ** 6)
        report("disordered_A1_N=%d_s=%s" % (n, s), within(a1 / y, F(4, 3), F(5, 100)), (a1 / y * 10 ** 6).numerator // (a1 / y * 10 ** 6).denominator, "1333333")
        if F(s) >= 8:
            d2 = F(int(r["D2_ppm"]), 10 ** 6)
            report("disordered_D2_N=%d_s=%s" % (n, s), within(d2 / (y * y), F(2, 9), F(1, 10)), (d2 / (y * y) * 10 ** 6).numerator // (d2 / (y * y) * 10 ** 6).denominator, "222222")

chi = {}
for n in (81, 243, 729):
    r = pin(n, "1/2", "0", "1/2")
    y = F(1, 2 * n)
    chi[n] = F(int(r["B_ppb"]), 10 ** 9) * 2 / n / (y * y)
for a, b in ((81, 243), (243, 729)):
    ratio = chi[b] / chi[a]
    report("susceptibility_ratio_N=%d_to_%d" % (a, b), within(ratio, 9, F(15, 100)), (ratio * 10 ** 6).numerator // (ratio * 10 ** 6).denominator, "9000000")
report("susceptibility_scale_N=729", within(abs(chi[729]) / (729 * 729), F(2, 125), F(15, 100)), (abs(chi[729]) / (729 * 729) * 10 ** 6).numerator // (abs(chi[729]) / (729 * 729) * 10 ** 6).denominator, "16000")

sym = R.get("POLARITON_SYMMETRY", [])
if len(sym) == 2:
    a, b = sym
    report("symmetry_A_flips", abs(int(a["A_ppb"]) + int(b["A_ppb"])) <= 1000, a["A_ppb"] + "," + b["A_ppb"], "opposite")
    report("symmetry_B_same", abs(int(a["B_ppb"]) - int(b["B_ppb"])) <= 1000, a["B_ppb"] + "," + b["B_ppb"], "equal")
    report("symmetry_E_same", abs(int(a["energy_ppb"]) - int(b["energy_ppb"])) <= 1, a["energy_ppb"] + "," + b["energy_ppb"], "equal_within_1e-9")

# The quench.
for r in R.get("POLARITON_QUENCH", []):
    n = int(r["N"])
    if n < 6561 or F(int(r["jbar_ppb"]), 10 ** 9) / n > F(1, 100):
        continue
    tag = "N=%d_delta=%s_t=%s" % (n, r["delta"], r["t"])
    delta = F(r["delta"])
    report("quench_jbar_" + tag, within(F(int(r["jbar_ppb"]), 10 ** 9), closed_jbar(delta, int(r["t"])), F(2, 100)), r["ratio_ppm"], "1000000")
    if int(r["jbar_ppb"]) > 0 and F(int(r["jbar_ppb"]), 10 ** 9) > F(1, 100):
        report("quench_phase_" + tag, abs(F(int(r["re_P_over_N_jbar_ppm"]), 10 ** 6) + delta) <= F(2, 100) * max(abs(delta), F(1, 50)), r["re_P_over_N_jbar_ppm"], str(-delta))
        if delta != 1:
            report("quench_C1_" + tag, within(F(int(r["C1_ppm"]), 10 ** 6), 4 * (1 - delta) * F(int(r["jbar_ppb"]), 10 ** 9) / n, F(5, 100)), r["C1_ppm"], r["predicted_C1_ppm"])
for r in R.get("POLARITON_QUENCH", []):
    report("energy_N=%s_delta=%s_t=%s" % (r["N"], r["delta"], r["t"]), abs(int(r["energy_off_1e-9"])) <= 10 ** 5, r["energy_off_1e-9"], "abs_at_most_100000e-9")
for r in R.get("POLARITON_QUENCH_BAND", []):
    if int(r["N"]) != 6561:
        continue
    delta = F(r["delta"])
    value = int(r["largest_f_ppm"])
    if abs(delta) < 1:
        report("band_inside_delta=%s" % delta, value >= 50000, value, "at_least_50000")
    elif abs(delta) == 1:
        report("band_edge_delta=%s" % delta, value <= 30000, value, "at_most_30000")
    else:
        report("band_outside_delta=%s" % delta, value <= 1000, value, "at_most_1000")

# The band column against the rows it comes from, since the table above it quotes the column.
band_off = max((abs(int(r["largest_f_ppm"]) - max((2 * int(s["jbar_ppb"]) // (1000 * int(r["N"])) for s in R.get("POLARITON_QUENCH", []) if s["N"] == r["N"] and s["delta"] == r["delta"]), default=0)) for r in R.get("POLARITON_QUENCH_BAND", [])), default=0)
report("band_column_is_the_rows", band_off <= 2, band_off, "at_most_2_ppm")

# The quench with pinning.
qp = R.get("POLARITON_QUENCH_PIN", [])
for r in qp:
    y = F(r["y"])
    delta = F(r["delta"])
    if y == 0:
        continue
    tag = "N=%s_delta=%s_y=%s_t=%s" % (r["N"], delta, y, r["t"])
    if delta in (0, F(1, 2)):
        report("quench_pin_A1_" + tag, within(F(int(r["A1_ppm"]), 10 ** 6), closed_a1(delta, int(r["t"]), y), F(5, 100)), r["A1_ppm"], r["predicted_A1_ppm"])
    else:
        same = [s for s in qp if s["N"] == r["N"] and F(s["delta"]) == 0 and s["t"] == r["t"] and F(s["y"]) == y][0]
        report("quench_pin_at_edge_" + tag, F(int(r["A1_ppm"])) <= F(5, 100) * int(same["A1_ppm"]), r["A1_ppm"], "at_most_5_percent_of_" + same["A1_ppm"])
for r in qp:
    y = F(r["y"])
    if y > 0:
        other = [s for s in qp if s["N"] == r["N"] and s["delta"] == r["delta"] and s["t"] == r["t"] and F(s["y"]) == -y][0]
        report("quench_pin_sign_N=%s_delta=%s_t=%s" % (r["N"], r["delta"], r["t"]), int(r["A_ppb"]) * int(other["A_ppb"]) < 0 or (int(r["A_ppb"]) == 0 and int(other["A_ppb"]) == 0), r["A_ppb"] + "," + other["A_ppb"], "opposite")
    if y == 0:
        report("quench_pin_zero_A_N=%s_delta=%s_t=%s" % (r["N"], r["delta"], r["t"]), int(r["A_ppb"]) == 0, r["A_ppb"], "0")
pin_energy = max((abs(int(r["energy_off_1e-9"])) for r in qp), default=0)
report("quench_pin_energy", pin_energy <= 10 ** 5, pin_energy, "abs_at_most_100000e-9")
for r in R.get("POLARITON_SECTOR_EQUALS_FULL", []):
    report("sector_equals_full_N=%s" % r["N"], r["off_line_nonzero"] == "0" and r["on_line_different"] == "0", r["off_line_nonzero"] + "," + r["on_line_different"], "0,0")
for r in R.get("POLARITON_REVERSAL", []):
    report("reversal_N=%s_full=%s" % (r["N"], r["full"]), r["every_byte_returned"] == "1" and r["state_moved"] == "1", r["every_byte_returned"], "1")
for r in R.get("POLARITON_WAVEVECTOR", []):
    u = F(r["u"])
    report("wavevector_u=%s" % u, abs(F(r["argmax_x"]) + u) <= F(1, 16), r["argmax_x"], str(-u))
for r in R.get("POLARITON_CONTROL_NO_BOSE", []):
    report("control_no_bose_must_miss_t=%s" % r["t"], not within(F(int(r["jbar_ppb"]), 10 ** 9), closed_jbar(F(r["delta"]), int(r["t"])), F(2, 100)), r["ratio_ppm"], "off_1000000_by_more_than_20000")
    # The energy read's own control: these rows evolve with the Bose factor removed while the row reads the true H, so the printed offset leaves the 10^-4 of the quench rows.
    report("control_no_bose_energy_moves_t=%s" % r["t"], abs(int(r["energy_off_1e-9"])) > 10 ** 5, r["energy_off_1e-9"], "abs_above_100000e-9")

# POLARITON_WINDOW_INSIDE and POLARITON_WINDOW_BELOW, added at 89a026a.
def window(n, u, x, s):
    for r in R.get("POLARITON_PIN_WINDOW", []):
        if int(r["N"]) == n and F(r["u"]) == F(u) and F(r["x"]) == F(x) and F(r["s"]) == F(s):
            return r
    return None


def micro(q):
    return (q * 10 ** 6).numerator // (q * 10 ** 6).denominator


SIX = ("1/2", "1", "2", "4", "8", "16")
INSIDE = {("1/4", "-1/4"): (31223, 123327, 417999, 744149, 874846, 937483), ("1/4", "0"): (7199, 28779, 113886, 394162, 732112, 869614), ("3/4", "0"): (5190, 20753, 82548, 304289, 675100, 846304), ("3/4", "1/8"): (740, 2962, 11850, 47314, 183943, 539654), ("1/2", "1/4"): (1111, 4444, 17772, 70798, 266308, 642446)}
for (u, x), table in INSIDE.items():
    du, dx = F(u), F(x)
    delta = du + dx
    rho = (1 - delta) / (4 - 3 * du)
    c0 = ((1 - 2 * rho) / rho - du) / 4
    for n, limit_d, limit_a in ((243, F(20, 100), F(2, 100)), (729, F(10, 100), F(1, 100))):
        if n == 729 and (u, x) not in (("1/4", "-1/4"), ("3/4", "0")):
            continue
        for s, f_ppm in zip(SIX, table):
            r = window(n, u, x, s)
            tag = "N=%d_u=%s_x=%s_s=%s" % (n, u, x, s)
            if r is None:
                report("window_inside_" + tag, False, "no_row", "row")
                continue
            y = F(s) / n
            f = F(f_ppm, 10 ** 6)
            want_d = 2 * rho * f
            want_a = 2 * (1 + (du / (8 * c0)) * (1 + f))
            d2 = F(abs(int(r["B_ppb"])) * 2, n * 10 ** 9)
            a1y = F(abs(int(r["A_ppb"])) * 2, n * 10 ** 9) / y
            report("window_inside_D2_" + tag, within(d2, want_d, limit_d), micro(d2), micro(want_d))
            report("window_inside_A1_" + tag, within(a1y, want_a, limit_a), micro(a1y), micro(want_a))
            report("window_inside_B_negative_" + tag, int(r["B_ppb"]) < 0, r["B_ppb"], "negative")
for u, x in (("1", "-1/4"), ("1", "-1/8"), ("1/2", "-1/4"), ("3/4", "-1/8")):
    du, dx = F(u), F(x)
    want_a = 2 / (du - dx)
    want_d = 2 * abs(du - dx - 1) / (du * (du - dx) ** 2)
    sign = 1 if du - dx - 1 > 0 else -1
    for n in (243, 729):
        if n == 729 and (u, x) not in (("1", "-1/4"), ("1/2", "-1/4")):
            continue
        z = window(n, u, x, "0")
        tag = "N=%d_u=%s_x=%s" % (n, u, x)
        report("window_below_E_at_zero_" + tag, z is not None and abs(F(int(z["energy_ppb"]), 10 ** 9) - dx * n) <= F(1, 10 ** 6), z["energy_ppb"] if z else "no_row", str(dx * n))
        for s in ("0",) + SIX:
            r = window(n, u, x, s)
            label = tag + "_s=" + s
            if r is None:
                report("window_below_" + label, False, "no_row", "row")
                continue
            report("window_below_P2_" + label, int(r["P2_over_N2_ppm"]) >= 980000, r["P2_over_N2_ppm"], "at_least_980000")
            if s == "0":
                continue
            y = F(s) / n
            a1y = F(abs(int(r["A_ppb"])) * 2, n * 10 ** 9) / y
            report("window_below_A1_" + label, within(a1y, want_a, F(1, 100)), micro(a1y), micro(want_a))
            report("window_below_B_sign_" + label, int(r["B_ppb"]) * sign > 0, r["B_ppb"], "sign_%d" % sign)
            if F(s) >= 4:
                d2y = F(abs(int(r["B_ppb"])) * 2, n * 10 ** 9) / (y * y)
                report("window_below_D2_" + label, within(d2y, want_d, F(5, 100)), micro(d2y), micro(want_d))

# POLARITON_QUENCH_CONVERSION, added at 89a026a.
for r in R.get("POLARITON_QUENCH_CONVERSION", []):
    n, t = int(r["N"]), int(r["t"])
    y, delta = F(r["y"]), F(r["delta"])
    square = (1 - delta * delta) * t * t
    shc, chz = sinh_cosh(square)
    j0 = shc * shc * t * t
    sinh2 = shc * shc * square
    a1_want = 4 * abs(y) * (chz - 1) / (1 + delta)
    c1_want = 4 * sinh2 / ((1 + delta) * n) + a1_want * a1_want / 2
    big_y = (2 * n * y * y / (1 + delta)) * (chz - 1) ** 2 / sinh2
    v2_want = big_y / (1 + big_y)
    coh = 2 * n * y * y * ((chz - 1) ** 2 / (1 + delta) ** 2 + j0)
    d2_want = coh / n
    f_want = (2 * j0 + coh) / n
    a1 = F(abs(int(r["A_ppb"])) * 2, n * 10 ** 9)
    c1 = F(int(r["C1_ppb"]), 10 ** 9)
    d2 = F(abs(int(r["B_ppb"])) * 2, n * 10 ** 9)
    v2 = a1 * a1 / (2 * c1)
    tag = "N=%d_delta=%s_y=%s_t=%d" % (n, delta, y, t)
    report("conversion_energy_" + tag, abs(int(r["energy_off_1e-9"])) <= 10 ** 5, r["energy_off_1e-9"], "abs_at_most_100000e-9")
    # At u = 1 the energy is 2x jbar + ((N - 1)/2)(C1 + C2) - 2y<A>, from the row's other fields. Each field is floored at 10^-9, which sets the bound.
    rebuilt = 2 * F(r["x"]) * F(int(r["jbar_ppb"]), 10 ** 9) + F(n - 1, 2) * (c1 + F(int(r["C2_ppb"]), 10 ** 9)) - 2 * y * F(int(r["A_ppb"]), 10 ** 9)
    report("conversion_energy_rebuilt_" + tag, abs(rebuilt - F(int(r["energy_off_1e-9"]), 10 ** 9)) <= (2 * abs(F(r["x"])) + n + 1 + 2 * abs(y)) / 10 ** 9, r["energy_off_1e-9"], micro(rebuilt * 1000))
    report("conversion_A_negative_" + tag, int(r["A_ppb"]) < 0, r["A_ppb"], "negative")
    report("conversion_B_positive_" + tag, int(r["B_ppb"]) > 0, r["B_ppb"], "positive")
    if n >= 243 and f_want <= F(1, 10):
        report("conversion_V2_" + tag, within(v2, v2_want, F(5, 100)), micro(v2), micro(v2_want))
    if n >= 243 and f_want <= F(1, 20):
        report("conversion_A1_" + tag, within(a1, a1_want, F(5, 100)), micro(a1), micro(a1_want))
        report("conversion_C1_" + tag, within(c1, c1_want, F(5, 100)), micro(c1), micro(c1_want))
        report("conversion_D2_" + tag, within(d2, d2_want, F(10, 100)), micro(d2), micro(d2_want))

# The frozen grid of POLARITON_QUENCH_CONVERSION, since the loop above reads whatever rows are there.
grid = {(n, d, s / root, t) for n, root in ((81, 9), (243, 16), (729, 27)) for d in (F(0), F(1, 2)) for s in (F(1, 4), F(1, 2), F(1), F(2), F(4)) for t in (1, 2, 3)} | {(2187, F(0), s / 47, t) for s in (F(1, 2), F(1)) for t in (1, 2)}
have = {(int(r["N"]), F(r["delta"]), F(r["y"]), int(r["t"])) for r in R.get("POLARITON_QUENCH_CONVERSION", [])}
report("conversion_grid_as_frozen", have == grid, len(have & grid), str(len(grid)))

# POLARITON_HAND, on the engine's own rows at N = 2. The levels -2 and 4 are in units of H with JN = 4, so E = -1/2 here.
hand = {r["y"]: r for r in R.get("POLARITON_PIN", []) if r["s"] == "hand"}
report("hand_rows", len(hand) == 4, len(hand), "4")
if "0" in hand:
    z = hand["0"]
    report("hand_E", abs(int(z["energy_ppb"]) + 500000000) <= 10, z["energy_ppb"], "-1/2")
    report("hand_A", abs(int(z["A_ppb"])) <= 10, z["A_ppb"], "0")
    report("hand_B", abs(int(z["B_ppb"])) <= 10, z["B_ppb"], "0")
    report("hand_C1", abs(F(int(z["C1_ppm"]), 10 ** 6) + F(4, 3)) <= F(2, 10 ** 6), z["C1_ppm"], "-4/3")
    report("hand_C2", abs(F(int(z["C2_ppm"]), 10 ** 6) - F(1, 3)) <= F(2, 10 ** 6), z["C2_ppm"], "1/3")
    report("hand_f", abs(F(int(z["f_ppm"]), 10 ** 6) - F(1, 3)) <= F(2, 10 ** 6), z["f_ppm"], "1/3")
if "1/1024" in hand:
    # y = h/4, so h = 1/256 and <A> = (2/9) h at this size.
    slope = F(int(hand["1/1024"]["A_ppb"]), 10 ** 9) * 256
    report("hand_dA_dh", within(slope, F(2, 9), F(1, 1000)), hand["1/1024"]["A_ppb"], "2/9_per_h")
if "1/64" in hand and "-1/64" in hand:
    report("hand_sign_A_follows_h", int(hand["1/64"]["A_ppb"]) > 0 > int(hand["-1/64"]["A_ppb"]), hand["1/64"]["A_ppb"] + "," + hand["-1/64"]["A_ppb"], "opposite")

# Every Lanczos row reached its tolerance, 2^-30 = 931e-12.
for tag in ("POLARITON_PIN", "POLARITON_PIN_WINDOW", "POLARITON_SYMMETRY"):
    top = max((int(r["residual_1e-12"]) for r in R.get(tag, [])), default=0)
    report("lanczos_converged_" + tag, top <= 931, top, "at_most_931")

# A row the prediction names and the receipt lacks is a miss.
for tag, count in (("POLARITON_TAYLOR_POINT", 6), ("POLARITON_TAYLOR_CONVERT", 4), ("POLARITON_REVERSAL", 5), ("POLARITON_CONTROL_NO_BOSE", 4), ("POLARITON_SYMMETRY", 2), ("POLARITON_WAVEVECTOR", 3), ("POLARITON_QUENCH", 240), ("POLARITON_QUENCH_BAND", 40), ("POLARITON_QUENCH_PIN", 54), ("POLARITON_SECTOR_EQUALS_FULL", 2), ("POLARITON_SECTOR", 438), ("POLARITON_PIN", 172), ("POLARITON_PIN_WINDOW", 196), ("POLARITON_QUENCH_CONVERSION", 94)):
    # Counted by what names a row, so a row replaced by a copy of another counts as missing.
    distinct = {tuple(r.get(k) for k in ("N", "u", "x", "y", "s", "delta", "t", "P", "full")) for r in R.get(tag, [])}
    report("rows_" + tag, len(R.get(tag, [])) == count and len(distinct) == count, len(distinct), str(count))

print("POLARITON_READ_DONE|met=%d|miss=%d|json=0" % (met, miss))
