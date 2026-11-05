# Item 4. The 1/N coefficient of D2/y^2 and of A1/y over the rotor, in closed form, derived from the Weyl symbol of the chains (derivation in FINDINGS.txt),
# against the Richardson limits of the exact chains. Integers at 2^K for the one irrational, omega = sqrt(4 a r z).
import sys
from fractions import Fraction as F
from math import isqrt
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from resp_lib import dec

SC = 10 ** 60


def rt(q):
    q = F(q)
    return F(isqrt(q.numerator * SC * SC // q.denominator), SC)


def theory(u, x):
    u, x = F(u), F(x)
    delta = u + x
    a = 4 - 3 * u
    r = (1 - delta) / a
    z = 1 - 2 * r
    c0 = (z / r - u) / 4
    w = rt(4 * a * r * z)
    t1 = -1 / (2 * a) - (1 - 4 * r) / (2 * w)
    c1 = (1 / (8 * r * r)) * ((1 / a - 1 + 3 * r) + (3 - 8 * r) / w - w / 4)
    k_d2 = (t1 + F(1, 2)) / r - 2 * c1 / c0 + (1 / r - u - 1 / u) / w
    rotor_a = 2 + u / (4 * c0)
    a_next = -u * c1 / (4 * c0 * c0) + (z / (r * r) - 1 / (4 * r * r) + z * a / (4 * r)) / (4 * c0 * w) + (a / 4 - c0 - 1 / (2 * r)) / w
    k_a1 = a_next / rotor_a
    return dict(r=r, z=z, a=a, c0=c0, w=w, t1=t1, c1=c1, k_d2=k_d2, k_a1=k_a1)


if __name__ == "__main__":
    limits = {}
    for line in open("C:/tmp/opus55/polariton-recheck-window-20261105/out/t4_chains.hbp", encoding="utf-8").read().splitlines():
        if line.startswith("RICHARDSON|"):
            row = dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f)
            limits[(row["u"], row["x"])] = (F(row["K_D2"]), F(row["K_A1"]), int(row["level"]))
    for (us, xs), (kd, ka, lv) in limits.items():
        t = theory(us, xs)
        print("THEORY_1_OVER_N|u=%s|x=%s|rho=%s|c0=%s|omega=%s|K_D2_chain=%s|K_D2_theory=%s|off=%s|K_A1_chain=%s|K_A1_theory=%s|off=%s|levels=%d|json=0" % (
            us, xs, t["r"], t["c0"], dec(t["w"], 12), dec(kd, 20), dec(t["k_d2"], 20), dec(kd - t["k_d2"], 20), dec(ka, 20), dec(t["k_a1"], 20), dec(ka - t["k_a1"], 20), lv))
