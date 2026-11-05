# Item 1, part 2. Even-block exact diagonalization (K fractional bits, no float) against the plane-wave series and the closed forms, at N = 9, 27, 81.
import sys
from fractions import Fraction as F
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from pw_lib import Series, closed_A1, closed_B2, evaluate, dec
from ed_lib import Block

POINTS = [("1", "-1/4"), ("1", "-1/8"), ("1/2", "-1/4"), ("3/4", "-1/8")]
SIX = ["1/2", "1", "2", "4", "8", "16"]
ORDERS = {9: 16, 27: 20, 81: 20}
for N in (9, 27, 81):
    for us, xs in POINTS:
        u, x = F(us), F(xs)
        ser = Series(N, u, x, ORDERS[N])
        sa, sb, sp = ser.A(), ser.B(), ser.charge2()
        form_a = 2 / (u - x)
        form_d = 2 * abs(u - x - 1) / (u * (u - x) ** 2)
        for ss in SIX:
            y = F(ss) / N
            blk = Block(N, u, x, y, parity=1, K=200)
            guess = (x * N).numerator << 200 >> 0
            guess = ((x * N + evaluate(ser.E, y)).numerator << 200) // (x * N + evaluate(ser.E, y)).denominator if False else None
            theta, v, res = blk.ground()
            a, b, p2, pairs, npnm = blk.read(v)
            a_q, b_q, p2_q = F(a, blk.one), F(b, blk.one), F(p2, blk.one)
            e_q = F(theta, blk.one)
            ser_e = evaluate(ser.E, y)
            ser_a = evaluate(sa, y)
            ser_b = evaluate(sb, y)
            ser_p2 = evaluate(sp, y)
            lead_b = closed_B2(N, u, x) * y * y
            print("T1_ED|N=%d|u=%s|x=%s|s=%s|E_even=%s|E_series=%s|A_even=%s|A_series=%s|B_even=%s|B_series=%s|B_second_order=%s|P2/N2_even=%s|P2/N2_series=%s|A1/y=%s|form=%s|D2/y2=%s|finiteN_second_order=%s|form=%s|sign_B=%s|residual_log2=%d|json=0" % (
                N, us, xs, ss, dec(e_q, 12), dec(ser_e, 12), dec(a_q, 10), dec(ser_a, 10), dec(b_q, 10), dec(ser_b, 10), dec(lead_b, 10),
                dec(p2_q / (N * N), 8), dec(ser_p2 / (N * N), 8), dec(2 * abs(a_q) / N / y, 7), dec(form_a, 7), dec(2 * abs(b_q) / N / (y * y), 7), dec(2 * abs(lead_b) / N / (y * y), 7), dec(form_d, 7),
                "+" if b > 0 else "-", (res.bit_length() - 200)))
            sys.stdout.flush()
