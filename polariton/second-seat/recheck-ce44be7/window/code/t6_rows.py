# Item 6. Every one of the 196 POLARITON_PIN_WINDOW rows read by tools that share no code with the engine: my even block at N = 3, 9, 81; the exact plane-wave series below the edge at N = 243, 729; the reduced chain basis inside the window at N = 243, 729.
# Compares E, <A>, <B>, and the charge share on the below rows. Prints each row's offsets and a summary.
import sys
from fractions import Fraction as F
from math import isqrt
sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from ed_lib import Block
from pw_lib import Series, evaluate
from resp_lib import constants, dec
import t4_reduced as tr

WT = "C:/tmp/qnn-polariton-wt/polariton/RECEIPT.hbp"
rows = []
for line in open(WT, encoding="utf-8").read().splitlines():
    if line.startswith("POLARITON_PIN_WINDOW|"):
        rows.append(dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f))
stats = {}


def note(N, kind, de, da, db):
    t = stats.setdefault((N, kind), [0, F(0), F(0), F(0)])
    t[0] += 1
    t[1] = max(t[1], abs(de))
    t[2] = max(t[2], abs(da))
    t[3] = max(t[3], abs(db))


BELOW = {("1", "-1/4"), ("1", "-1/8"), ("1/2", "-1/4"), ("3/4", "-1/8")}
# Small N by the even block.
for r in rows:
    N = int(r["N"])
    if N > 81:
        continue
    u, x, y = F(r["u"]), F(r["x"]), F(r["y"])
    b = Block(N, u, x, y, parity=1, K=160)
    theta, v, res = b.ground(bits=44)
    a_v, b_v, p2, pairs, npnm = b.read(v)
    e, a_q, b_q = F(theta, b.one), F(a_v, b.one), F(b_v, b.one)
    de = e - F(int(r["energy_ppb"]), 10 ** 9)
    da = a_q - F(int(r["A_ppb"]), 10 ** 9)
    db = b_q - F(int(r["B_ppb"]), 10 ** 9)
    note(N, "even_block", de, da, db)
    print("ROW|N=%d|u=%s|x=%s|s=%s|tool=even_block|E_off=%s|A_off=%s|B_off=%s|P2/N2_off=%s|json=0" % (N, u, x, r["s"], dec(de, 10), dec(da, 10), dec(db, 10), dec(F(p2, b.one) / (N * N) - F(int(r["P2_over_N2_ppm"]), 10 ** 6), 7)))
    sys.stdout.flush()
# Large N below the edge by the exact series.
for r in rows:
    N = int(r["N"])
    if N <= 81 or (r["u"], r["x"]) not in BELOW:
        continue
    u, x, y = F(r["u"]), F(r["x"]), F(r["y"])
    ser = Series(N, u, x, 14)
    e = evaluate(ser.E, y)
    a_q = evaluate(ser.A(), y)
    b_q = evaluate(ser.B(), y)
    p2 = evaluate(ser.charge2(), y)
    de = e - F(int(r["energy_ppb"]), 10 ** 9)
    da = a_q - F(int(r["A_ppb"]), 10 ** 9)
    db = b_q - F(int(r["B_ppb"]), 10 ** 9)
    note(N, "series", de, da, db)
    print("ROW|N=%d|u=%s|x=%s|s=%s|tool=series|E_off=%s|A_off=%s|B_off=%s|P2/N2_off=%s|json=0" % (N, u, x, r["s"], dec(de, 10), dec(da, 10), dec(db, 10), dec(p2 / (N * N) - F(int(r["P2_over_N2_ppm"]), 10 ** 6), 7)))
    sys.stdout.flush()
# Large N inside the window by the reduced chain basis.
K, ONE = tr.K, tr.ONE
done = {}
for r in rows:
    N = int(r["N"])
    if N <= 81 or (r["u"], r["x"]) in BELOW:
        continue
    key = (N, r["u"], r["x"])
    u, x, y = F(r["u"]), F(r["x"]), F(r["y"])
    if key not in done:
        delta, rho, rho0, c0 = constants(u, x)
        g = isqrt(((rho0 / rho).numerator << 80) // (rho0 / rho).denominator)
        lam = 16 * F(g, 1 << 40) / (2 * c0)
        top = min(int(2 * lam) + 24, N)
        L = 12 if N <= 243 else 8
        done[key] = (top, L) + tr.build(N, u, x, top, L)
    top, L, c, lv, Um, Bm, B1 = done[key]
    theta, a_val, b_val, tail, v = tr.solve_reduced(N, lv, Um, Bm, B1, y, top, L)
    de = F(theta, ONE) - F(int(r["energy_ppb"]), 10 ** 9)
    da = F(a_val, ONE) - F(int(r["A_ppb"]), 10 ** 9)
    db = F(b_val, ONE) - F(int(r["B_ppb"]), 10 ** 9)
    note(N, "reduced", de, da, db)
    print("ROW|N=%d|u=%s|x=%s|s=%s|tool=reduced|Pmax=%d|L=%d|E_off=%s|A_off=%s|B_off=%s|json=0" % (N, u, x, r["s"], top, L, dec(de, 10), dec(da, 10), dec(db, 10)))
    sys.stdout.flush()
for (N, kind), t in sorted(stats.items()):
    print("ROWS_SUMMARY|N=%d|tool=%s|rows=%d|largest_E_off=%s|largest_A_off=%s|largest_B_off=%s|json=0" % (N, kind, t[0], dec(t[1], 10), dec(t[2], 10), dec(t[3], 10)))
print("ROWS_DONE|rows=%d|json=0" % sum(t[0] for t in stats.values()))
