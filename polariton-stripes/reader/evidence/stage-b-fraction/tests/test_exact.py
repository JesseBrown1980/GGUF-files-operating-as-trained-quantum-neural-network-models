"""Exact arithmetic: canonical integers, rationals, frozen decimals, decimal output, intervals."""

import unittest

from stripes_read_b.exact import (
    Decimal,
    ExactError,
    Iv,
    canon_int,
    dec,
    fmt,
    fr,
    ipow,
    isqrt_iv,
    parse_rat,
    rat_text,
)


class Text(unittest.TestCase):
    def test_canon_int(self):
        self.assertEqual(canon_int("-12"), -12)
        self.assertEqual(canon_int("0"), 0)
        for bad in ("-0", "+1", "01", "", "1.0", "1e3"):
            with self.assertRaises(ExactError):
                canon_int(bad)

    def test_rat(self):
        self.assertEqual(parse_rat("-1/54"), fr(-1, 54))
        self.assertEqual(rat_text(fr(-5, 4)), "-5/4")
        self.assertEqual(rat_text(fr(3)), "3")
        for bad in ("2/4", "1/1", "0/3", "1/-2", "-0"):
            with self.assertRaises(ExactError):
                parse_rat(bad)

    def test_decimal(self):
        self.assertEqual(dec("6.031e-5"), fr(6031, ipow(10, 8)))
        self.assertEqual(dec("+2.4604e-3"), fr(24604, ipow(10, 7)))
        self.assertEqual(dec("-0.000648"), fr(-648, ipow(10, 6)))
        self.assertEqual(dec("107622"), 107622)
        d = Decimal("17.760")
        self.assertEqual(d.stated_band(), (fr(177595, 10000), fr(177605, 10000)))
        self.assertEqual(Decimal("107622").half_unit(), fr(1, 2))

    def test_fmt(self):
        self.assertEqual(fmt(fr(1, 3), 4), "0.3333")
        self.assertEqual(fmt(fr(2, 3), 4), "0.6667")
        self.assertEqual(fmt(fr(2, 3), 4, "down"), "0.6666")
        self.assertEqual(fmt(fr(-2, 3), 4, "down"), "-0.6667")
        self.assertEqual(fmt(fr(-2, 3), 4, "up"), "-0.6666")
        self.assertEqual(fmt(fr(6031, ipow(10, 8)), 4), "6.031e-5")
        self.assertEqual(fmt(fr(9999, 10000), 3), "1")
        self.assertEqual(fmt(123456789, 4), "1.235e8")
        self.assertEqual(fmt(0, 4), "0")
        self.assertEqual(fmt(fr(1, 1000), 3), "0.001")


class Intervals(unittest.TestCase):
    def test_ops(self):
        a, b = Iv(1, 2), Iv(-3, 4)
        self.assertEqual(((a * b).lo, (a * b).hi), (-6, 8))
        self.assertEqual(((a - b).lo, (a - b).hi), (-3, 5))
        self.assertEqual((b.sq().lo, b.sq().hi), (0, 16))
        self.assertEqual(((a * Iv(2, 4).inv()).lo, (a * Iv(2, 4).inv()).hi), (fr(1, 4), 1))
        with self.assertRaises(ExactError):
            b.inv()

    def test_rounding_is_outward(self):
        v = fr(1, ipow(3, 40))
        x = Iv(v).r(16)
        self.assertTrue(x.lo < v < x.hi)
        self.assertTrue(x.hi - x.lo <= fr(1, 1 << 16))
        self.assertEqual(Iv(fr(1, 3)).r(16).lo, fr(1, 3))  # small denominators stay exact

    def test_sqrt(self):
        r = isqrt_iv(2, 64)
        self.assertTrue(r.lo * r.lo <= 2 <= r.hi * r.hi)
        self.assertEqual(isqrt_iv(fr(9, 4)).lo, fr(3, 2))


if __name__ == "__main__":
    unittest.main()
