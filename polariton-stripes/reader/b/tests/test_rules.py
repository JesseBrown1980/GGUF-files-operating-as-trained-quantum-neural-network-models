"""Rules H8, B16, SIGNFLIP, READ3, SE and EXPOSED on exact hand-computed cases."""

import unittest

from stripes_read_b import common as c
from stripes_read_b import frozen
from stripes_read_b.exact import ExactError, Rad, fmt, fr


class H8(unittest.TestCase):
    def test_equal_counts_unflagged(self):
        self.assertEqual(c.h8(100, 100, 0), c.UNFLAGGED)

    def test_boundary_is_unflagged(self):
        # (|90 - 10| + 0)^2 = 6400 = 64 * 100
        self.assertEqual(c.h8(90, 10, 0), c.UNFLAGGED)

    def test_just_over_flags(self):
        # 81^2 = 6561 > 64 * 101 = 6464
        self.assertEqual(c.h8(91, 10, 0), c.FLAG)

    def test_ambiguous_unresolved(self):
        # (81 + 2)^2 = 6889 > 6464, and (81 - 2)^2 = 6241 <= 64 * 103 = 6592
        self.assertEqual(c.h8(91, 10, 2), c.UNRESOLVED)

    def test_difference_within_ambiguous(self):
        self.assertEqual(c.h8(50, 0, 60), c.UNRESOLVED)

    def test_large_imbalance(self):
        self.assertEqual(c.h8(1000, 0, 0), c.FLAG)

    def test_pairs(self):
        sec = list(range(16))
        p = dict((k, (a, b)) for k, a, b in c.h8_pairs(sec))
        self.assertEqual(p["pi3"], (3, 11))
        self.assertEqual(p["mir3"], (3, 12))
        self.assertEqual(len(p), 16)


class B16(unittest.TestCase):
    def test_threshold_D(self):
        # 3 D^2 > 1440 * 16000 + 512 D first at D = 2858: 24504492 > 24503296, 24487347 <= 24502784 at 2857
        self.assertEqual(c.b16_threshold_D(16000), 2858)

    def test_uniform(self):
        v, per = c.b16([1000] * 16, 0, 16000)
        self.assertEqual(v, "uniform")
        self.assertEqual(set(per), {c.UNFLAGGED})

    def test_one_sector_flags(self):
        # O_0 = 1179: D = 16 * 1179 - 16000 = 2864 >= 2858; O_15 = 821: D = 2864 too; 1178 gives 2848
        sec = [1179] + [1000] * 14 + [821]
        v, per = c.b16(sec, 0, 16000)
        self.assertEqual(v, "not_uniform")
        self.assertEqual(per[0], c.FLAG)
        self.assertEqual(per[15], c.FLAG)
        self.assertEqual(per[1], c.UNFLAGGED)

    def test_ambiguous_bracketed(self):
        sec = [1178] + [1000] * 14 + [821]
        v, per = c.b16(sec, 1, 16000)
        self.assertEqual(v, "unresolved")
        self.assertEqual(per[0], c.UNRESOLVED)
        self.assertEqual(per[15], c.UNRESOLVED)
        self.assertEqual(per[3], c.UNFLAGGED)

    def test_identity_enforced(self):
        with self.assertRaises(c.StageBStop):
            c.b16([1000] * 16, 1, 16000)

    def test_frozen_thresholds(self):
        # rule B16: about 6.70e-4 at 2^22, 1.34e-3 at 2^20; E07: 2.75e-3 at M' about 251109
        for mp, text in ((1 << 22, "6.7e-4"), (1 << 20, "0.00134"), (251109, "0.00275")):
            self.assertEqual(fmt(fr(c.b16_threshold_D(mp), 16 * mp), 3), text)


class SignFlip(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(c.signflip(100, 100), c.FLAG)  # 100 > 5 * 10
        self.assertEqual(c.signflip(-50, 100), c.UNFLAGGED)  # 50 > 50 fails
        self.assertEqual(c.signflip(51, 100), c.FLAG)

    def test_two_roots_exact(self):
        # 5 (sqrt 50 + sqrt 8) = 35 sqrt 2 = 49.497...
        self.assertEqual(c.signflip(60, 50, 10, 8), c.FLAG)  # 50 > 49.497
        self.assertEqual(c.signflip(59, 50, 10, 8), c.UNFLAGGED)  # 49 < 49.497

    def test_bound_eats_sum(self):
        self.assertEqual(c.signflip(100, 0, 100, 0), c.UNFLAGGED)


class Radicals(unittest.TestCase):
    def test_sign1(self):
        self.assertEqual((Rad(7) - Rad.sqrt(50)).sign(), -1)  # 49 < 50
        self.assertEqual((Rad(8) - Rad.sqrt(64)).sign(), 0)
        self.assertEqual((Rad(-3) + Rad.sqrt(8)).sign(), -1)  # 9 > 8

    def test_sign2(self):
        # sqrt 2 + sqrt 3 = 3.1462...; 22/7 = 3.1428
        self.assertEqual((Rad.sqrt(2) + Rad.sqrt(3) - fr(22, 7)).sign(), 1)
        self.assertEqual((Rad.sqrt(8) - Rad.sqrt(2, 2)).sign(), 0)
        self.assertEqual((Rad(1) + Rad.sqrt(8) - Rad.sqrt(2, 2)).sign(), 1)

    def test_three_roots(self):
        self.assertEqual((Rad.sqrt(2) + Rad.sqrt(3) + Rad.sqrt(5) - fr(538, 100)).sign(), 1)  # 5.3823
        # three independent radicands whose sum the refinement cannot resolve still refuse: the bound is 16384 bits
        tiny = Rad.sqrt(2) + Rad.sqrt(3) + Rad.sqrt(5)
        near = tiny.iv(20000)
        with self.assertRaises(ExactError):
            (tiny - near.lo).sign()

    def test_square_ratio_radicands_merge(self):
        # review N14: sqrt 8 = 2 sqrt 2 and sqrt 18 = 3 sqrt 2, so sqrt 2 + sqrt 8 - sqrt 18 is exactly 0 (it refused
        # before, as a tie of three radicands that refinement cannot decide)
        r = Rad(0, ((1, 2), (1, 8), (-1, 18)))
        self.assertEqual((r.a, r.terms), (0, ()))
        self.assertEqual(r.sign(), 0)
        # rational radicands: sqrt(1/2) = (1/2) sqrt 2, sqrt(9/8) = (3/4) sqrt 2; one term on the least radicand
        r = Rad(1, ((1, fr(1, 2)), (1, 2), (-4, fr(9, 8))))
        # 1 + sqrt(1/2) + 2 sqrt(1/2) - 6 sqrt(1/2) = 1 - 3 sqrt(1/2), and 9/2 > 1
        self.assertEqual(r.terms, ((-3, fr(1, 2)),))
        self.assertEqual(r.sign(), -1)
        # the order of the terms does not change the result
        self.assertEqual(Rad(1, ((-4, fr(9, 8)), (1, 2), (1, fr(1, 2)))).terms, r.terms)
        # radicands whose ratio is not a square stay apart; equal radicands add as before
        self.assertEqual(len(Rad(0, ((1, 2), (1, 3), (1, 6))).terms), 3)
        self.assertEqual(Rad(0, ((1, 3), (2, 3))).terms, ((3, 3),))
        self.assertEqual(Rad(0, ((1, 12), (1, 27))).terms, ((fr(5, 2), 12),))  # sqrt 27 = (3/2) sqrt 12
        # sqrt 2 + sqrt 8 + sqrt 3 - (1/3) sqrt 27 = 3 sqrt 2: the sqrt 3 class cancels
        self.assertEqual((Rad.sqrt(2) + Rad.sqrt(8) + Rad.sqrt(3) - Rad.sqrt(27, fr(1, 3))).terms,
                         ((3, 2),))


class Read3(unittest.TestCase):
    band = c.Band(fr(99, 400), fr(101, 400))

    def test_interval(self):
        self.assertEqual(c.read3_interval(fr(248, 1000), fr(2499, 10000), self.band), c.MET)
        self.assertEqual(c.read3_interval(fr(2, 10), fr(24, 100), self.band), c.MISS)
        self.assertEqual(c.read3_interval(fr(24, 100), fr(25, 100), self.band), c.NOT_RESOLVED)
        self.assertEqual(c.read3_interval(fr(99, 400), fr(1, 4), self.band), c.MET)
        self.assertEqual(c.read3_interval(fr(101, 400), fr(1, 2), self.band), c.NOT_RESOLVED)

    def test_open_band(self):
        b = c.Band(0, fr(1, 20), lo_open=True, hi_open=True)
        self.assertEqual(c.read3_interval(0, fr(1, 100), b), c.NOT_RESOLVED)
        self.assertEqual(c.read3_interval(fr(-1, 100), 0, b), c.MISS)
        self.assertEqual(c.read3_interval(fr(1, 1000), fr(1, 100), b), c.MET)
        self.assertEqual(c.read3_interval(fr(1, 20), fr(1, 10), b), c.MISS)

    def test_sampled(self):
        p, tol = fr(1, 4), fr(1, 10)
        self.assertEqual(c.read3_sampled(fr(3, 10), p, tol, fr(4, 100)), c.MET)
        self.assertEqual(c.read3_sampled(fr(3, 10), p, tol, fr(5, 100)), c.MET)  # 0.05 + 0.05 = tol
        self.assertEqual(c.read3_sampled(fr(3, 10), p, tol, fr(6, 100)), c.NOT_RESOLVED)
        self.assertEqual(c.read3_sampled(fr(1, 2), p, tol, fr(6, 100)), c.MISS)
        self.assertEqual(c.read3_sampled(fr(41, 100), p, tol, fr(6, 100)), c.NOT_RESOLVED)  # 0.16 - 0.06 = tol

    def test_sampled_with_roots(self):
        # E10 style: Pi_hat = 0.1 against 0.09 with e = 3 SE + A/M, tol = 0.009 + 3/sqrt(M), M = 10^6
        m = 1000000
        x = fr(1, 10)
        se2 = c.se2_pi(x, m)
        e = c.se(se2, 3) + fr(1000, m)
        tol = fr(9, 1000) + Rad.sqrt(fr(1, m), 3)
        # |x - p| + e = 0.01 + 3 * 0.000497 + 0.001 = 0.01249 > tol = 0.012; |x - p| - e = 0.00751 < tol
        self.assertEqual(c.read3_sampled(x, fr(9, 100), tol, e), c.NOT_RESOLVED)
        self.assertEqual(c.read3_sampled(x, fr(95, 1000), tol, e), c.MET)
        self.assertEqual(c.read3_sampled(x, fr(7, 100), tol, e), c.MISS)

    def test_outcomes(self):
        self.assertEqual(c.predicted_flag_read(c.FLAG, c.FLAG), c.MET)
        self.assertEqual(c.predicted_flag_read(c.UNFLAGGED, c.FLAG), c.MISS)
        self.assertEqual(c.predicted_flag_read(c.UNRESOLVED, c.UNFLAGGED), c.NOT_RESOLVED)


def _r(rid, outcome, sc=True):
    return c.Read("T", rid, "here", "exact", c.Scoring(sc, "x"), outcome)


class RowVerdict(unittest.TestCase):
    def test_cases(self):
        rv = c.row_verdict
        self.assertEqual(rv([_r("a", c.MET), _r("b", c.MET)]), c.MET)
        self.assertEqual(rv([_r("a", c.MET), _r("b", c.MISS)]), c.NOT_MET)
        self.assertEqual(rv([_r("a", c.MET), _r("b", c.NOT_RESOLVED)]), c.NOT_RESOLVED)
        self.assertEqual(rv([_r("a", c.MET), _r("b", c.NOT_MEASURED)]), c.NOT_RESOLVED)
        self.assertEqual(rv([_r("a", c.NOT_MEASURED), _r("b", c.NOT_MEASURED)]), c.NOT_MEASURED)
        self.assertEqual(rv([_r("a", c.MET), _r("b", c.MISS, sc=False)]), c.MET)
        self.assertEqual(rv([_r("a", c.MISS, sc=False)]), c.NONE)
        self.assertEqual(rv([_r("a", c.MET)], falsifier=True), c.NOT_MET)

    def test_report_has_no_verdict(self):
        self.assertEqual(_r("a", c.MISS, sc=False).verdict, c.REPORT)
        self.assertEqual(_r("a", c.NOT_MEASURED, sc=False).verdict, c.NOT_MEASURED)

    def test_falsifier_only_on_scored(self):
        with self.assertRaises(c.StageBStop):
            c.Verdict("T", "n", "DERIVED", [_r("a", c.MET), _r("b", c.MET, sc=False)], falsifier_reads=("b",))
        v = c.Verdict("T", "n", "DERIVED", [_r("a", c.MET)], falsifier_reads=("a",), falsifier_text="flag")
        self.assertEqual(v.verdict, c.NOT_MET)


class SE(unittest.TestCase):
    def test_binomial_pi(self):
        p = c.pi_hat(60, 40, 100)
        self.assertEqual(p, fr(1, 10))
        self.assertEqual(c.se2_pi(p, 100), fr(3, 1250))
        self.assertEqual(c.se2_binomial(25, 100), fr(3, 1600))

    def test_mean(self):
        self.assertEqual(c.mean_se2([1, 2, 3, 4]), (fr(5, 2), fr(5, 12)))
        self.assertEqual(c.batch_means([10, 20, 30, 40], [10, 10, 10, 10]), (fr(5, 2), fr(5, 12)))
        with self.assertRaises(c.StageBStop):
            c.batch_means([1, 2], [1, 2])

    def test_ratio(self):
        self.assertEqual(c.ratio_paired([2, 4], [1, 2]), (2, 0))
        self.assertEqual(c.ratio_paired([2, 5], [1, 2]), (fr(7, 3), fr(4, 81)))
        self.assertEqual(c.ratio_indep(1, fr(1, 100), 2, fr(1, 100)), (fr(1, 2), fr(1, 320)))

    def test_jackknife_of_mean(self):
        def mean(xs):
            return fr(sum(xs), len(xs))

        self.assertEqual(c.jackknife(mean, [1, 2, 3, 4]), (fr(5, 2), fr(5, 12)))


class Exposed(unittest.TestCase):
    def test_frozen_text(self):
        self.assertTrue(c.check_exposure_text(frozen.load()))

    def test_triples(self):
        q = fr
        self.assertTrue(c.exposed(q(-1, 4), 1, q(1, 2)))
        self.assertFalse(c.exposed(q(-1, 4), 1, 1))
        self.assertTrue(c.exposed(q(-1, 4), q(1, 2), 2))
        self.assertFalse(c.exposed(q(-1, 4), q(1, 2), 1))
        self.assertFalse(c.exposed(q(-1, 4), q(1, 8), 2))
        self.assertTrue(c.exposed(q(-1, 4), q(1, 4), 2))
        self.assertTrue(c.exposed(q(1, 2), q(1, 8), 3))
        self.assertFalse(c.exposed(q(1, 2), q(1, 16), 1))
        self.assertFalse(c.exposed(q(1, 2), q(1, 18), 2))
        self.assertTrue(c.exposed_s0(q(-1, 4), 2))
        self.assertFalse(c.exposed_s0(q(-1, 4), 1))

    def test_value_scoring_agrees_with_text(self):
        fz = frozen.load()
        s = c.value_scoring(fz, "Q06", (fr(-1, 4), fr(1, 2), 2), "both_t=2_reads_with_their_sign")
        self.assertFalse(s.scored)
        self.assertTrue(c.value_scoring(fz, "Q06", (fr(-1, 4), fr(1, 2), 1), None).scored)
        with self.assertRaises(c.StageBStop):
            c.value_scoring(fz, "Q06", (fr(-1, 4), fr(1, 2), 1), "both_t=2_reads_with_their_sign")
        with self.assertRaises(c.StageBStop):
            c.value_scoring(fz, "Q06", (fr(-1, 4), fr(1, 2), 2), None)


class Tables(unittest.TestCase):
    def test_against_frozen(self):
        self.assertTrue(c.check_tables())

    def test_mismatch_caught(self):
        p = c.DUMP_POINTS["P08"]
        saved = p.steps
        p.steps = (64, 128)
        try:
            with self.assertRaises(c.StageBStop):
                c.check_tables()
        finally:
            p.steps = saved

    def test_seed_and_h(self):
        # the head of the excluded X1 dumps: seed=2827389175355266397, h=105800555712
        self.assertEqual(c.seed_u64("stripes-ens-v1:N27:d1/4:y1/40"), 2827389175355266397)
        self.assertEqual(c.engine_h(27), 105800555712)
        self.assertEqual(c.DUMP_POINTS["P08"].s(), fr(1, 2))
        self.assertEqual(c.DUMP_POINTS["P02"].s(), fr(1, 16))
        self.assertEqual(sum(p.calls for p in c.DUMP_POINTS.values()), 8000)


if __name__ == "__main__":
    unittest.main()
