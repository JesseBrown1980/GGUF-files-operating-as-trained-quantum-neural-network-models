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


def sector(n, u, x, p="0"):
    for r in R.get("POLARITON_SECTOR", []):
        if int(r["N"]) == n and F(r["u"]) == F(u) and F(r["x"]) == F(x) and int(r["P"]) == int(p):
            return r
    return None


BIG = [3 ** p for p in range(9, 14)]
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
    for n in BIG:
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
        for n in BIG:
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
    if n < 6561 or int(r["jbar_over_N_ppm"]) > 10000:
        continue
    tag = "N=%d_delta=%s_t=%s" % (n, r["delta"], r["t"])
    report("quench_jbar_" + tag, abs(int(r["ratio_ppm"]) - 10 ** 6) <= 20000, r["ratio_ppm"], "1000000")
    delta = F(r["delta"])
    if int(r["jbar_ppb"]) > 0 and F(int(r["jbar_ppb"]), 10 ** 9) > F(1, 100):
        report("quench_phase_" + tag, abs(F(int(r["re_P_over_N_jbar_ppm"]), 10 ** 6) + delta) <= F(2, 100) * max(abs(delta), F(1, 50)), r["re_P_over_N_jbar_ppm"], str(-delta))
        if delta != 1:
            report("quench_C1_" + tag, within(F(int(r["C1_ppm"])), F(int(r["predicted_C1_ppm"])), F(5, 100)) if int(r["predicted_C1_ppm"]) else True, r["C1_ppm"], r["predicted_C1_ppm"])
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

# The quench with pinning.
qp = R.get("POLARITON_QUENCH_PIN", [])
for r in qp:
    y = F(r["y"])
    delta = F(r["delta"])
    if y == 0:
        continue
    tag = "N=%s_delta=%s_y=%s_t=%s" % (r["N"], delta, y, r["t"])
    if delta in (0, F(1, 2)):
        report("quench_pin_A1_" + tag, within(F(int(r["A1_ppm"])), F(int(r["predicted_A1_ppm"])), F(5, 100)), r["A1_ppm"], r["predicted_A1_ppm"])
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
for r in R.get("POLARITON_SECTOR_EQUALS_FULL", []):
    report("sector_equals_full_N=%s" % r["N"], r["off_line_nonzero"] == "0" and r["on_line_different"] == "0", r["off_line_nonzero"] + "," + r["on_line_different"], "0,0")
for r in R.get("POLARITON_REVERSAL", []):
    report("reversal_N=%s_full=%s" % (r["N"], r["full"]), r["every_byte_returned"] == "1" and r["state_moved"] == "1", r["every_byte_returned"], "1")
for r in R.get("POLARITON_WAVEVECTOR", []):
    u = F(r["u"])
    report("wavevector_u=%s" % u, abs(F(r["argmax_x"]) + u) <= F(1, 16), r["argmax_x"], str(-u))
for r in R.get("POLARITON_CONTROL_NO_BOSE", []):
    report("control_no_bose_must_miss_t=%s" % r["t"], abs(int(r["ratio_ppm"]) - 10 ** 6) > 20000, r["ratio_ppm"], "off_1000000_by_more_than_20000")

print("POLARITON_READ_DONE|met=%d|miss=%d|json=0" % (met, miss))
