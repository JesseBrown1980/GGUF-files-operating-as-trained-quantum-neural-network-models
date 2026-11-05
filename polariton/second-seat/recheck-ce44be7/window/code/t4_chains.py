# Item 4. D2/y^2 and A1/y at y -> 0 over the rotor, against N, with Richardson in 1/N on N = 2^k. Exact chains at K bits.
import sys, time
from fractions import Fraction as F
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from resp_lib import Chains, rotor_chi_d, rotor_chi_a, constants, dec

POINTS = [("1/4", "-1/4"), ("1/4", "0"), ("3/4", "0"), ("3/4", "1/8"), ("1/2", "1/4"), ("1/2", "0")]
K = 600
for us, xs in POINTS:
    u, x = F(us), F(xs)
    delta, rho, rho0, c0 = constants(u, x)
    print("POINT|u=%s|x=%s|delta=%s|rho=%s|rho0=%s|c0=%s|rotor_chiD/N^2=%s|rotor_chiA=%s|json=0" % (us, xs, delta, rho, rho0, c0, rotor_chi_d(1, u, x), rotor_chi_a(u, x)))
    for N in (81, 243, 729, 2187, 6561, 19683):
        c = Chains(N, u, x, K)
        r = c.response()
        one = c.one
        chid = 2 * F(r["b2"], one) / N
        ratio = -chid / rotor_chi_d(N, u, x)
        chia = 4 * F(r["s1"], one) / N
        ra = chia / rotor_chi_a(u, x)
        print("CHAIN3|u=%s|x=%s|N=%d|D2_ratio=%s|N(D2_ratio-1)=%s|A1_ratio=%s|N(A1_ratio-1)=%s|sign_B=%s|neg1=%d|neg2=%d|json=0" % (us, xs, N, dec(ratio, 12), dec(N * (ratio - 1), 8), dec(ra, 12), dec(N * (ra - 1), 8), "-" if chid < 0 else "+", r["neg1"], r["neg2"]))
        sys.stdout.flush()
    seq, seqa = [], []
    powers = list(range(7, 16))
    for k in powers:
        N = 1 << k
        c = Chains(N, u, x, K)
        r = c.response()
        one = c.one
        chid = 2 * F(r["b2"], one) / N
        ratio = -chid / rotor_chi_d(N, u, x)
        chia = 4 * F(r["s1"], one) / N
        ra = chia / rotor_chi_a(u, x)
        seq.append(N * (ratio - 1))
        seqa.append(N * (ra - 1))
    tab = list(seq)
    taba = list(seqa)
    level = 1
    lines = []
    while len(tab) > 1:
        tab = [((1 << level) * tab[i + 1] - tab[i]) / ((1 << level) - 1) for i in range(len(tab) - 1)]
        taba = [((1 << level) * taba[i + 1] - taba[i]) / ((1 << level) - 1) for i in range(len(taba) - 1)]
        lines.append((level, tab[-1], taba[-1]))
        level += 1
    for lv, v, va in lines:
        print("RICHARDSON|u=%s|x=%s|level=%d|K_D2=%s|K_A1=%s|json=0" % (us, xs, lv, dec(v, 24), dec(va, 24)))
    sys.stdout.flush()
