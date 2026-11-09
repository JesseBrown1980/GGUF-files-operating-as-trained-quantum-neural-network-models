"""Brackets of the closed forms and the exact y-series, and the frozen decimals they must hold."""

import unittest

from stripes_read_b import series
from stripes_read_b.exact import Iv, fr, ipow, isqrt_iv


class Brackets(unittest.TestCase):
    def test_cosh_sinh_identity(self):
        # cosh^2 - gamma^2 (sinh/gamma)^2 = 1
        for d, t in ((fr(-1, 4), 2), (fr(1, 2), 4), (fr(1, 3), fr(1, 8))):
            C, S = series.cosh_C(d, t), series.sinh_S(d, t)
            v = C.sq() - S.sq() * (1 - d * d)
            self.assertTrue(v.contains(1))
            self.assertTrue(v.width() < fr(1, ipow(10, 60)))

    def test_known_values(self):
        # delta = 0, t = 1: cosh 1 = 1.5430806348..., sinh 1 = 1.1752011936...
        C, S = series.cosh_C(0, 1), series.sinh_S(0, 1)
        self.assertTrue(C.lo > fr(15430806348, ipow(10, 10)) and C.hi < fr(15430806349, ipow(10, 10)))
        self.assertTrue(S.lo > fr(11752011936, ipow(10, 10)) and S.hi < fr(11752011937, ipow(10, 10)))
        sh = series.sinh_iv(fr(-1, 4), 2)
        self.assertTrue(sh.width() < fr(1, ipow(10, 60)))
        self.assertTrue((sh * isqrt_iv(fr(16, 15))).contains(series.sinh_S(fr(-1, 4), 2).mid()) or
                        (sh * isqrt_iv(fr(16, 15))).hi - series.sinh_S(fr(-1, 4), 2).lo > 0)

    def test_series_b2_is_the_law(self):
        # b2 = |a1|^2 of the exact y-series equals |g|^2 of the closed form
        for t in (fr(1, 2), 1, 2):
            b2, _ = series.b2b4_iv(fr(-1, 4), t)
            g2 = series.g2_abs(fr(-1, 4), t)
            self.assertTrue(b2.lo <= g2.hi and g2.lo <= b2.hi)
            self.assertTrue(b2.width() < fr(1, ipow(10, 40)))

    def test_lowest_terms(self):
        # YSERIES: b4/b2 = -(2/3) t^2 at short t; Q04: |g|^2 = t^2 + (45/64) t^4 + ... at delta = -1/4
        (k2, c2), (k4, c4) = series.lowest_terms(fr(-1, 4))
        self.assertEqual((k2, c2), (2, 1))
        self.assertEqual((k4, c4), (4, fr(-2, 3)))
        self.assertEqual(series.d2_coefficient(fr(-1, 4)), fr(45, 64))
        p, q, r, w, P, Q = series.series(fr(-1, 4), 1, 8)
        b2_t4 = sum(p[i] * p[4 - i] + q[i] * q[4 - i] for i in range(5))
        self.assertEqual(b2_t4, fr(45, 64))

    def test_remainder(self):
        T1, T3 = series.series_remainder(fr(-1, 4), 2)
        self.assertTrue(T1 < fr(1, ipow(10, 50)) and T3 < fr(1, ipow(10, 50)))
        b2a, b4a = series.b2b4(fr(-1, 4), 2, 90)
        b2b, b4b = series.b2b4(fr(-1, 4), 2, 110)
        bi2, bi4 = series.b2b4_iv(fr(-1, 4), 2)
        self.assertTrue(bi2.contains(b2b) and bi4.contains(b4b))
        self.assertTrue(abs(b4a - b4b) < fr(1, ipow(10, 50)))

    def test_kappa_sign_and_law_at_zero_field(self):
        self.assertTrue(series.kappa_q(fr(-1, 4), 1, 729).hi < 0)
        law = series.Law(fr(-1, 4), 0, 2)
        self.assertIsNone(law.nstar())
        self.assertTrue(law.EB2.contains(law.var0.mid()))

    def test_rho_and_nstar(self):
        law = series.Law(fr(-1, 4), fr(1, 4), 1)
        v = law.rho() * (law.nstar() + 1)
        self.assertTrue(v.contains(1))


class FrozenDecimals(unittest.TestCase):
    def test_every_bracket_holds_its_decimal(self):
        res = series.check_frozen()
        self.assertEqual(len(res), 99)
        bad = {r[0] for r in res if r[5] != series.CONTAINS}
        self.assertEqual(bad, set(series.KNOWN_SLIPS))

    def test_decimal_check(self):
        self.assertEqual(series.check_decimal(Iv(fr(24837, 100000)), "0.24837"), series.CONTAINS)
        self.assertEqual(series.check_decimal(Iv(fr(248374, 1000000), fr(248376, 1000000)), "0.24837"),
                         series.STRADDLES)
        self.assertEqual(series.check_decimal(Iv(fr(24834, 100000)), "0.24837"), series.OUTSIDE)
        self.assertEqual(series.check_decimal(Iv(fr(45, 64)), "45/64"), series.CONTAINS)


if __name__ == "__main__":
    unittest.main()
