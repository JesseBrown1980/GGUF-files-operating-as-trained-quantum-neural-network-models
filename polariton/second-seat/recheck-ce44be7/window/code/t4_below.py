# Item 4/6. The y -> 0 response of the P = 0 branch at the below-edge points of the README, against the rotor and the closed-form 1/N coefficient.
import sys
from fractions import Fraction as F
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from resp_lib import Chains, rotor_chi_d, rotor_chi_a, constants, dec
from t4_theory import theory

K = 500
for us, xs in (("1", "-1/4"), ("1", "-1/8"), ("1/2", "-1/4"), ("3/4", "-1/8"), ("1/4", "-1/2")):
    u, x = F(us), F(xs)
    delta, rho, rho0, c0 = constants(u, x)
    t = theory(u, x)
    print("BELOW_POINT|u=%s|x=%s|rho=%s|c0=%s|K_D2_theory=%s|K_A1_theory=%s|json=0" % (us, xs, rho, c0, dec(t["k_d2"], 8), dec(t["k_a1"], 8)))
    for N in (243, 729, 2187, 6561, 19683):
        c = Chains(N, u, x, K)
        r = c.response()
        one = c.one
        chid = 2 * F(r["b2"], one) / N
        ratio = -chid / rotor_chi_d(N, u, x)
        chia = 4 * F(r["s1"], one) / N
        ra = chia / rotor_chi_a(u, x)
        print("BELOW_CHAIN|u=%s|x=%s|N=%d|D2_ratio=%s|N(ratio-1)=%s|A1_ratio=%s|N(A1_ratio-1)=%s|sign_B=%s|neg1=%d|neg2=%d|json=0" % (us, xs, N, dec(ratio, 9), dec(N * (ratio - 1), 5), dec(ra, 9), dec(N * (ra - 1), 5), "-" if chid < 0 else "+", r["neg1"], r["neg2"]))
        sys.stdout.flush()
