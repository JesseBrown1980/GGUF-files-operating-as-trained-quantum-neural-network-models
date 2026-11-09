"""qint: reduced pairs, checks after every operation, refusal of every operand that is not an int or a Q, comparison by
cross-multiplication, and the integer gcd and isqrt. The values come from an integer LCG (no random module)."""

import unittest

from stripes_read_b import qint
from stripes_read_b.exact import Iv, Rad, fr
from stripes_read_b.qint import Q, QintError


def lcg(seed, count, bits):
    x, out = seed, []
    for _ in range(count):
        x = (x * 6364136223846793005 + 1442695040888963407) % (1 << 64)
        v = x >> (64 - bits) if bits <= 64 else (x << (bits - 64)) | (x >> 3)
        out.append(v - (1 << (bits - 1)))
    return out


def euclid(a, b):
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def reduced(x):
    return type(x) is Q and type(x.n) is int and type(x.d) is int and x.d > 0 and euclid(x.n, x.d) == 1


class Pairs(unittest.TestCase):
    def test_make_reduces_and_signs(self):
        x = qint.make(6, -4)
        self.assertEqual((x.n, x.d), (-3, 2))
        self.assertEqual((qint.make(0, -7).n, qint.make(0, -7).d), (0, 1))
        self.assertEqual(str(qint.make(-1, 4)), "-1/4")
        self.assertEqual(str(qint.make(8, 4)), "2")
        with self.assertRaises(ZeroDivisionError):
            qint.make(1, 0)

    def test_operations_against_cross_multiplication(self):
        ns = lcg(7, 400, 90)
        ds = [abs(v) + 1 for v in lcg(11, 400, 70)]
        for k in range(0, 398, 2):
            a, b = qint.make(ns[k], ds[k]), qint.make(ns[k + 1], ds[k + 1])
            an, ad, bn, bd = ns[k], ds[k], ns[k + 1], ds[k + 1]
            for got, n, d in ((a + b, an * bd + bn * ad, ad * bd), (a - b, an * bd - bn * ad, ad * bd),
                              (a * b, an * bn, ad * bd), (qint.div(a, b), an * bd, ad * bn), (-a, -an, ad)):
                self.assertTrue(reduced(got), got)
                self.assertEqual(got.n * d, n * got.d)
            self.assertEqual(qint.cmp(a, b), (an * bd > bn * ad) - (an * bd < bn * ad))
            self.assertEqual(a < b, an * bd < bn * ad)
            self.assertEqual(qint.floor(a), an // ad)
            self.assertEqual(qint.ceil(a), -((-an) // ad))

    def test_ints_mix_and_stay_exact(self):
        x = qint.make(1, 3)
        self.assertEqual(2 * x, qint.make(2, 3))
        self.assertEqual(1 - x, qint.make(2, 3))
        self.assertEqual(sum([x, x, x]), 1)
        self.assertEqual(hash(qint.make(5)), hash(5))
        self.assertEqual({qint.make(1, 2): "h"}[fr(2, 4)], "h")
        self.assertTrue(reduced(qint.ipow(qint.make(-2, 3), 5)))
        self.assertEqual(qint.ipow(qint.make(-2, 3), 5), qint.make(-32, 243))
        self.assertEqual(qint.ipow(3, 4), 81)

    def test_refused_operands(self):
        x = qint.make(1, 3)
        for bad in ("1/3", None, True, [1], (1, 3), b"1"):
            with self.assertRaises(TypeError):
                x * bad
            with self.assertRaises(TypeError):
                bad * x
            with self.assertRaises(TypeError):
                x == bad
            with self.assertRaises(TypeError):
                x < bad
            with self.assertRaises(TypeError):
                qint.q(bad)
        with self.assertRaises(QintError):
            qint.make(True, 3)
        with self.assertRaises(QintError):
            qint.make(1, False)
        with self.assertRaises(QintError):
            qint.isqrt(True)
        with self.assertRaises(QintError):
            qint.gcd(1, None)

    def test_no_other_numeric_doors(self):
        for name in ("__truediv__", "__rtruediv__", "__floordiv__", "__mod__", "__pow__", "__float__", "__int__",
                     "__index__", "__round__", "__complex__", "__trunc__", "__floor__", "__ceil__"):
            self.assertFalse(hasattr(Q, name), name)
        x = qint.make(1, 3)
        with self.assertRaises(AttributeError):
            x.n = 2
        with self.assertRaises(QintError):
            Q(1, 3)
        with self.assertRaises(TypeError):
            int(x)
        with self.assertRaises(TypeError):
            "%d" % x

    def test_exact_classes_answer_for_themselves(self):
        x = qint.make(1, 2)
        self.assertTrue(x < Rad.sqrt(1))
        iv = x * Iv(1, 3)
        self.assertEqual((iv.lo, iv.hi), (qint.make(1, 2), qint.make(3, 2)))
        r = qint.make(7, 2) - Rad(1)
        self.assertEqual((r.a, r.terms), (qint.make(5, 2), ()))

    def test_gcd_and_isqrt(self):
        for a, b in zip(lcg(3, 300, 200), lcg(5, 300, 150), strict=True):
            self.assertEqual(qint.gcd(a, b), euclid(a, b))
            self.assertEqual(qint.gcd(a, 1 << 77), euclid(a, 1 << 77))
        self.assertEqual(qint.gcd(0, 0), 0)
        for n in [0, 1, 2, 3, 4, 15, 16, 17] + [abs(v) for v in lcg(9, 200, 3000)]:
            r = qint.isqrt(n)
            self.assertTrue(r * r <= n < (r + 1) * (r + 1), n)
        with self.assertRaises(ValueError):
            qint.isqrt(-1)


if __name__ == "__main__":
    unittest.main()
