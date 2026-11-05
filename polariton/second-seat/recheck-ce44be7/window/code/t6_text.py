# Item 6. Each table cell and sentence of the window section and the N = 2, 3 section, read from RECEIPT.hbp, PREDICTION.hbp, READ.hbp, SECOND-ROUTE.hbp, at this head.
import sys
from fractions import Fraction as F
from math import isqrt
WT = "C:/tmp/qnn-polariton-wt/polariton/"


def rows(path, tag):
    out = []
    for line in open(path, encoding="utf-8").read().splitlines():
        if line.startswith(tag + "|"):
            out.append(dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f))
    return out


W = rows(WT + "RECEIPT.hbp", "POLARITON_PIN_WINDOW")
PIN = rows(WT + "RECEIPT.hbp", "POLARITON_PIN")


def win(N, u, x, s):
    for r in W:
        if int(r["N"]) == N and F(r["u"]) == F(u) and F(r["x"]) == F(x) and F(r["s"]) == F(s):
            return r
    return None


def d(q, digits=6):
    q = F(q)
    sign = "-" if q < 0 else ""
    q = abs(q)
    v = (q.numerator * 10 ** digits * 2 + q.denominator) // (2 * q.denominator)
    return "%s%d.%0*d" % (sign, v // 10 ** digits, digits, v % 10 ** digits)


print("WINDOW_ROWS|count=%d|by_N=%s|json=0" % (len(W), {n: sum(1 for r in W if int(r['N']) == n) for n in (3, 9, 81, 243, 729)}))
INSIDE = {("1/4", "-1/4"): (31223, 123327, 417999, 744149, 874846, 937483), ("1/4", "0"): (7199, 28779, 113886, 394162, 732112, 869614), ("3/4", "0"): (5190, 20753, 82548, 304289, 675100, 846304), ("3/4", "1/8"): (740, 2962, 11850, 47314, 183943, 539654), ("1/2", "1/4"): (1111, 4444, 17772, 70798, 266308, 642446)}
SIX = ("1/2", "1", "2", "4", "8", "16")
print("# inside table, as the README prints it: (u,x), N, 2rho, D2 at s=1, rotor, D2 at s=4, rotor, D2 at s=16, rotor, A1/y at s=4, rotor")
for (us, xs), N in ((("1/4", "-1/4"), 729), (("1/4", "0"), 243), (("3/4", "0"), 729), (("3/4", "1/8"), 243), (("1/2", "1/4"), 243)):
    u, x = F(us), F(xs)
    delta = u + x
    rho = (1 - delta) / (4 - 3 * u)
    c0 = ((1 - 2 * rho) / rho - u) / 4
    f = {s: F(v, 10 ** 6) for s, v in zip(SIX, INSIDE[(us, xs)])}
    cells = []
    for s in ("1", "4", "16"):
        r = win(N, us, xs, s)
        d2 = F(abs(int(r["B_ppb"])) * 2, N * 10 ** 9)
        cells.append("%s %s" % (d(d2), d(2 * rho * f[s])))
    r = win(N, us, xs, "4")
    a1y = F(abs(int(r["A_ppb"])) * 2, N * 10 ** 9) / (F(4) / N)
    print("INSIDE|u=%s|x=%s|N=%d|2rho=%s|%s|A1/y=%s %s|c0=%s|json=0" % (us, xs, N, d(2 * rho, 4), "|".join(cells), d(a1y, 4), d(2 * (1 + (u / (8 * c0)) * (1 + f["4"])), 4), c0))

print("# ratios the README prints: D2 ratio at s=1")
for us, xs, s in (("3/4", "0", "1"), ("1/4", "-1/4", "1")):
    u, x = F(us), F(xs)
    delta = u + x
    rho = (1 - delta) / (4 - 3 * u)
    f = {a: F(v, 10 ** 6) for a, v in zip(SIX, INSIDE[(us, xs)])}
    for N in (243, 729):
        r = win(N, us, xs, s)
        d2 = F(abs(int(r["B_ppb"])) * 2, N * 10 ** 9)
        print("RATIO|u=%s|x=%s|s=%s|N=%d|D2/rotor=%s|json=0" % (us, xs, s, N, d(d2 / (2 * rho * f[s]), 4)))
print("# all inside rows at N = 243, 729: the D2 ratio and A1 ratio, lowest and highest")
for (us, xs), table in INSIDE.items():
    u, x = F(us), F(xs)
    delta = u + x
    rho = (1 - delta) / (4 - 3 * u)
    c0 = ((1 - 2 * rho) / rho - u) / 4
    for N in (81, 243, 729):
        out = []
        for s, fp in zip(SIX, table):
            r = win(N, us, xs, s)
            if r is None:
                continue
            f = F(fp, 10 ** 6)
            d2 = F(abs(int(r["B_ppb"])) * 2, N * 10 ** 9)
            y = F(s) / N
            a1y = F(abs(int(r["A_ppb"])) * 2, N * 10 ** 9) / y
            out.append((s, d2 / (2 * rho * f), a1y / (2 * (1 + (u / (8 * c0)) * (1 + f))), int(r["B_ppb"]) < 0))
        if out:
            print("INSIDE_RATIOS|u=%s|x=%s|N=%d|%s|json=0" % (us, xs, N, ";".join("s=%s:D2=%s,A1=%s,B_neg=%d" % (s, d(a, 4), d(b, 5), c) for s, a, b, c in out)))

print("# below table, as the README prints it")
for (us, xs), N in ((("1", "-1/4"), 729), (("1", "-1/8"), 243), (("1/2", "-1/4"), 729), (("3/4", "-1/8"), 243)):
    u, x = F(us), F(xs)
    r16 = win(N, us, xs, "16")
    r4 = win(N, us, xs, "4")
    a1y = F(abs(int(r4["A_ppb"])) * 2, N * 10 ** 9) / (F(4) / N)
    d2y = F(abs(int(r16["B_ppb"])) * 2, N * 10 ** 9) / (F(16) / N) ** 2
    print("BELOW|u=%s|x=%s|N=%d|P2/N2_s16=%s|A1/y_s4=%s|form=%s|D2/y2_s16=%s|form=%s|sign_B_s16=%s|json=0" % (us, xs, N, d(F(int(r16["P2_over_N2_ppm"]), 10 ** 6), 4), d(a1y, 4), d(2 / (u - x), 4), d(d2y, 4), d(2 * abs(u - x - 1) / (u * (u - x) ** 2), 4), "+" if int(r16["B_ppb"]) > 0 else "-"))

print("# all below rows at N = 243, 729: sign of B and D2/y^2 at every s, including s < 4, which the reader does not read for sign")
for us, xs in (("1", "-1/4"), ("1", "-1/8"), ("1/2", "-1/4"), ("3/4", "-1/8")):
    u, x = F(us), F(xs)
    want = 2 * abs(u - x - 1) / (u * (u - x) ** 2)
    sign = 1 if u - x - 1 > 0 else -1
    for N in (81, 243, 729):
        out = []
        for s in ("0",) + SIX:
            r = win(N, us, xs, s)
            if r is None:
                continue
            if s == "0":
                out.append("s=0:E=%s,A=%s,B=%s,P2=%s" % (r["energy_ppb"], r["A_ppb"], r["B_ppb"], r["P2_over_N2_ppm"]))
                continue
            y = F(s) / N
            d2y = F(abs(int(r["B_ppb"])) * 2, N * 10 ** 9) / (y * y)
            a1y = F(abs(int(r["A_ppb"])) * 2, N * 10 ** 9) / y
            out.append("s=%s:D2/y2=%s(%s),A1/y=%s,signB_ok=%d,P2=%s" % (s, d(d2y, 4), d(d2y / want, 3), d(a1y, 4), int(r["B_ppb"]) * sign > 0, r["P2_over_N2_ppm"]))
        if out:
            print("BELOW_ALL|u=%s|x=%s|N=%d|%s|json=0" % (us, xs, N, ";".join(out)))

print("# paragraph after the below table")
r = win(243, "1", "-1/4", "4")
print("PARA|u=1,x=-1/4,N=243,s=4|D2=%s|A1/y=%s|P2_over_N2_ppm=%s|json=0" % (d(F(abs(int(r["B_ppb"])) * 2, 243 * 10 ** 9), 6), d(F(abs(int(r["A_ppb"])) * 2, 243 * 10 ** 9) / (F(4) / 243), 3), r["P2_over_N2_ppm"]))
r = win(243, "1/2", "-1/4", "4")
print("PARA|u=1/2,x=-1/4,N=243,s=4|D2=%s|json=0" % d(F(abs(int(r["B_ppb"])) * 2, 243 * 10 ** 9), 6))
r = win(729, "1/2", "-1/4", "4")
print("PARA|u=1/2,x=-1/4,N=729,s=4|D2=%s|json=0" % d(F(abs(int(r["B_ppb"])) * 2, 729 * 10 ** 9), 6))
for us, xs in (("1", "-1/4"), ("1/2", "-1/4")):
    u, x = F(us), F(xs)
    delta = u + x
    rho = (1 - delta) / (4 - 3 * u)
    c0 = ((1 - 2 * rho) / rho - u) / 4
    q = 16 * u / (16 * c0 * c0)
    print("ROTOR_AT|u=%s|x=%s|rho=%s|c0=%s|q_at_s4=%s|2rho=%s|rotor_A1/y_needs_f|json=0" % (us, xs, rho, c0, q, 2 * rho))

print("# the zero-field rows")
for r in W:
    if r["s"] == "0":
        print("ZERO|N=%s|u=%s|x=%s|E=%s|A=%s|B=%s|C2=%s|f=%s|P2=%s|residual=%s|json=0" % (r["N"], r["u"], r["x"], r["energy_ppb"], r["A_ppb"], r["B_ppb"], r["C2_ppm"], r["f_ppm"], r["P2_over_N2_ppm"], r["residual_1e-12"]))
