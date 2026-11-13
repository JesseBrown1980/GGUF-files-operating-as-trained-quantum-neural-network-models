"""Row E13's tolerance read at its edges, through z_read with kind "tol": abs(Z_n - (1 + (n-1) rho)) + 3SE against
1/4 + (n-1) rho/5. Each case is a block aggregate built by hand to give an exact Z_n and an exact SE; the expected
verdict is worked here from the frozen formula in integers over one denominator, apart from the reader's arithmetic.

Two faults these cases turn: the coefficient 1/5 read as 1/4, and the 3SE term left out."""

import unittest

from stripes_read_b import common as c
from stripes_read_b import rows_e_mom as m
from stripes_read_b.exact import Rad, fr

N = 16  # block size
RHO = (1, 100)  # frozen rho of the case, as a pair
K = 1025  # blocks, above the 1024 minimum
D = 2000  # one denominator for every quantity below


def blk(z_num, se_num):
    """A block aggregate with Z_n = z_num/D and SE = se_num/D exactly: w = K D, s2 = K z_num, and s4 from
    SE^2 = (K s4 - s2^2) / (w^2 (K - 1))."""
    w = K * D
    s2 = K * z_num
    top = se_num * se_num * K * K * (K - 1) + s2 * s2
    assert top % K == 0
    return {"K": K, "s2": s2, "s4": top // K, "w": w}


def frozen_verdict(z_num, se_num, coef_den=5, se_times=3):
    """MET, MISS or NOT_RESOLVED from the frozen row in integers over D * RHO[1] * coef_den."""
    s = D * RHO[1] * coef_den
    z = z_num * RHO[1] * coef_den
    p = s + (N - 1) * RHO[0] * D * coef_den
    tol = s // 4 + (N - 1) * RHO[0] * D
    e = se_times * se_num * RHO[1] * coef_den
    assert s % 4 == 0
    d = z - p if z >= p else p - z
    if d + e <= tol:
        return c.MET
    if d - e > tol:
        return c.MISS
    return c.NOT_RESOLVED


# p = 1 + 15/100 = 2300/2000; tolerance 1/4 + 15/500 = 560/2000; with 1/4 in place of 1/5 it would be 575/2000.
P = 2300
CASES = (
    # name, Z_n * D, SE * D, verdict
    ("met_inside", P + 400, 20, "MET"),  # 400 + 60 = 460
    ("met_edge_above", P + 500, 20, "MET"),  # 500 + 60 = 560, the tolerance exactly
    ("met_edge_below", P - 500, 20, "MET"),
    ("one_past_the_edge", P + 501, 20, "NOT_RESOLVED"),  # 561
    ("between_fifth_and_quarter", P + 510, 20, "NOT_RESOLVED"),  # 570: past 560, inside 575
    ("between_fifth_and_quarter_below", P - 510, 20, "NOT_RESOLVED"),
    ("inside_without_3se", P + 540, 20, "NOT_RESOLVED"),  # 540 alone is inside 560; 540 + 60 is past it
    ("outside_within_3se", P + 580, 20, "NOT_RESOLVED"),  # 580 alone is past 560; 580 - 60 is inside it
    ("miss_edge", P + 620, 20, "NOT_RESOLVED"),  # 620 - 60 = 560: MISS needs more than the tolerance
    ("miss_one_past", P + 621, 20, "MISS"),
    ("miss_between", P + 630, 20, "MISS"),  # 630 - 60 = 570: past 560, inside 575
    ("miss_below", P - 630, 20, "MISS"),
    ("miss_far", P + 1200, 20, "MISS"),
)


class E13ToleranceEdges(unittest.TestCase):
    def setUp(self):
        self.saved = (m.sums_of, m.rho_u, m.nominal_of, m.blk_of, m.short_of, m.loss, m.nstar_of)
        self.block = None
        m.sums_of = lambda pt, step, v, scope: {}
        m.rho_u = lambda s: fr(0)
        m.nominal_of = lambda pt, scope: 1 << 22
        m.blk_of = lambda pt, step, v, n, scope: self.block
        m.short_of = lambda pt, scope, nominal, n, k: False
        m.loss = lambda pt, scope="all": ()
        m.nstar_of = lambda rs: None

    def tearDown(self):
        m.sums_of, m.rho_u, m.nominal_of, m.blk_of, m.short_of, m.loss, m.nstar_of = self.saved

    def read(self, z_num, se_num):
        self.block = blk(z_num, se_num)
        return m.z_read("E13", "tol_edge", "at", c.scored("edge"), None, 64, "VNC", "all", (N,), "tol",
                        fr(RHO[0], RHO[1]))

    def test_the_block_gives_the_stated_z_and_se(self):
        z = m.Zn(blk(P + 510, 20))
        self.assertEqual(z.Z, fr(P + 510, D))
        e, want = z.e3(), Rad.of(fr(60, D))
        self.assertTrue(e <= want and want <= e)
        self.assertTrue(Rad.of(0) < e)

    def test_edges(self):
        for name, z_num, se_num, want in CASES:
            with self.subTest(name):
                r = self.read(z_num, se_num)
                self.assertEqual(r.outcome, {"MET": c.MET, "MISS": c.MISS, "NOT_RESOLVED": c.NOT_RESOLVED}[want])
                self.assertEqual(r.outcome, frozen_verdict(z_num, se_num))
                self.assertEqual(r.band, "abs(Z_n-1-(n-1)rho)+3SE<=1/4+(n-1)rho/5")

    def test_the_cases_tell_the_frozen_formula_from_both_faults(self):
        frozen = [frozen_verdict(z, s) for _, z, s, _ in CASES]
        quarter = [frozen_verdict(z, s, coef_den=4) for _, z, s, _ in CASES]
        no_se = [frozen_verdict(z, s, se_times=0) for _, z, s, _ in CASES]
        self.assertGreaterEqual(sum(a != b for a, b in zip(frozen, quarter)), 4)
        self.assertGreaterEqual(sum(a != b for a, b in zip(frozen, no_se)), 4)
        self.assertEqual({c.MET, c.MISS, c.NOT_RESOLVED}, set(frozen))

    def test_zero_se_reads_met_or_miss_only(self):
        self.assertEqual(self.read(P + 560, 0).outcome, c.MET)
        self.assertEqual(self.read(P + 561, 0).outcome, c.MISS)


if __name__ == "__main__":
    unittest.main()
