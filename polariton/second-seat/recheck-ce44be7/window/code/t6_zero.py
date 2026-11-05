# Item 6 and item 3. Every y = 0 window row against exact chain levels over all P. The frozen f(q) table against my own Mathieu reader. The 18 points the README cites, over ALL P at N = 243. The N = 3 and N = 2 closed forms in exact arithmetic.
import sys
from fractions import Fraction as F
from math import isqrt
sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from sec_lib import argmin_P, chain, ground_level, K, fx, dec
from t4_reduced import mathieu_f

WT = "C:/tmp/qnn-polariton-wt/polariton/"
rows = []
for line in open(WT + "RECEIPT.hbp", encoding="utf-8").read().splitlines():
    if line.startswith("POLARITON_PIN_WINDOW|"):
        rows.append(dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f))
bad = 0
for r in rows:
    if r["s"] != "0":
        continue
    N, u, x = int(r["N"]), F(r["u"]), F(r["x"])
    who, best, e0 = argmin_P(N, u, x, stop_bits=100)
    e = F(best, 1 << K)
    read = F(int(r["energy_ppb"]), 10 ** 9)
    p2 = F(who * who, N * N)
    read_p2 = F(int(r["P2_over_N2_ppm"]), 10 ** 6)
    ok = abs(e - read) < F(2, 10 ** 9) and abs(p2 - read_p2) <= F(1, 10 ** 6)
    bad += not ok
    print("ZERO_ROW|N=%d|u=%s|x=%s|lowest_P=%d|E_exact=%s|E_read=%s|P2/N2=%s|read=%s|ok=%d|json=0" % (N, u, x, who, dec(e, 9), dec(read, 9), dec(p2, 6), dec(read_p2, 6), ok))
print("ZERO_ROW_DONE|bad=%d|json=0" % bad)

print("# frozen f(q) in POLARITON_WINDOW_INSIDE against mathieu_f")
INSIDE = {("1/4", "-1/4"): (31223, 123327, 417999, 744149, 874846, 937483), ("1/4", "0"): (7199, 28779, 113886, 394162, 732112, 869614), ("3/4", "0"): (5190, 20753, 82548, 304289, 675100, 846304), ("3/4", "1/8"): (740, 2962, 11850, 47314, 183943, 539654), ("1/2", "1/4"): (1111, 4444, 17772, 70798, 266308, 642446)}
SIX = (F(1, 2), F(1), F(2), F(4), F(8), F(16))
offmax = F(0)
for (us, xs), table in INSIDE.items():
    u, x = F(us), F(xs)
    delta = u + x
    rho = (1 - delta) / (4 - 3 * u)
    c0 = ((1 - 2 * rho) / rho - u) / 4
    for s, fp in zip(SIX, table):
        q = s * s * u / (16 * c0 * c0)
        f = mathieu_f(q)
        off = abs(f * 10 ** 6 - fp)
        offmax = max(offmax, off)
        print("F_OF_Q|u=%s|x=%s|s=%s|q=%s|f_ppm_mine=%s|frozen=%d|off_ppm=%s|json=0" % (us, xs, s, q, dec(f * 10 ** 6, 3), fp, dec(off, 3)))
print("F_OF_Q_DONE|largest_off_ppm=%s|json=0" % dec(offmax, 3))
for us, xs, s, want in (("1", "-1/4", F(4), "0.437"), ("1/2", "-1/4", F(4), "0.511")):
    u, x = F(us), F(xs)
    delta = u + x
    rho = (1 - delta) / (4 - 3 * u)
    c0 = ((1 - 2 * rho) / rho - u) / 4
    q = s * s * u / (16 * c0 * c0)
    f = mathieu_f(q)
    print("ROTOR_THERE|u=%s|x=%s|s=%s|q=%s|f=%s|2rho_f=%s|readme=%s|A1/y_rotor=%s|json=0" % (us, xs, s, q, dec(f, 6), dec(2 * rho * f, 4), want, dec(2 * (1 + (u / (8 * c0)) * (1 + f)), 4)))

print("# the 18 points of the README, over all P at N = 243")
PTS = [("1/2", "0"), ("1/2", "1/4"), ("1/2", "-1/8"), ("1/2", "-1/4"), ("1/2", "-3/8"), ("1/2", "-1/2"), ("1/2", "-5/8"), ("1/4", "-1/4"), ("1/4", "-3/8"), ("1/4", "-1/2"), ("3/4", "0"), ("3/4", "-1/8"), ("3/4", "-1/4"), ("1", "-1/8"), ("1", "-1/4"), ("1", "-3/8"), ("0", "-1/2"), ("0", "-3/4")]
for us, xs in PTS:
    u, x = F(us), F(xs)
    who, best, e0 = argmin_P(243, u, x, stop_bits=100)
    root = u * (4 - 3 * u)
    w = ((4 - 3 * u) - F(isqrt(root.numerator * 10 ** 24 // root.denominator), 10 ** 12)) / 2
    edge = 1 - w - u
    print("ALL_P_243|u=%s|x=%s|lowest_P=%d|x_edge=%s|side=%s|json=0" % (us, xs, who, dec(edge, 4), "below" if x < edge else "above"))

print("# N = 3 by exact arithmetic: E satisfies (E + 1/3)^2 = 73/144 on P = 1, exactly, and <B> from the exact weights")
u, x = F(1, 4), F(-1, 4)
d1 = x + u * F(2, 3)
d2 = 3 * x + u * F(2, 3)
o2 = F(2 * 1 * 2 * 1, 9)
mean = (d1 + d2) / 2
half = (d1 - d2) / 2
disc = half * half + o2
print("N3|d1=%s|d2=%s|o^2=%s|mean=%s|half_diff=%s|disc=%s|disc*144=%s|json=0" % (d1, d2, o2, mean, half, disc, disc * 144))
# weights (1 -+ half/sqrt(disc))/2, with half/sqrt(disc) = 3/sqrt(73); <B>_even = (1/2)(c1^2 + 2 c2^2) = (3/4)(1 + (1/3)(half/sqrt disc)).
print("N3_B|<B>_even=(1/2)(w1+2w2)=(3/4)+(1/4)(3/sqrt73)=(3/4)(1+1/sqrt73)|half/sqrt(disc)^2=%s|=9/73:%s|json=0" % (half * half / disc, half * half / disc == F(9, 73)))
root73 = F(isqrt(73 * 10 ** 80), 10 ** 40)
print("N3_VALUES|E=%s|B=%s|P0_level=%s|json=0" % (dec(mean - root73 / 12, 12), dec(F(3, 4) * (1 + 1 / root73), 12), dec(F(-1, 8) - F(isqrt((F(1, 64) + F(2, 3)).numerator * 10 ** 80 // (F(1, 64) + F(2, 3)).denominator), 10 ** 40), 12)))
