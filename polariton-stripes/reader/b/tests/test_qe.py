"""QE rows from a real run at the excluded point N=9, delta=1/3 (guarded; tests/data/qe9), and rule EB."""

import os
import unittest

from stripes_read_b import common as c
from stripes_read_b import qe, rows_q
from stripes_read_b.exact import fmt, fr, ipow

from .util import QE9, TempDir, read, write

TEST_PLAN = [
    qe.Command("sector", 9, "1/3", "0", ("1/4", "1/2"), "T"),
    qe.Command("point", 9, "1/3", "0", ("1/4", "1/2"), "T"),
    qe.Command("point", 9, "1/3", "1/9", ("1/4", "1/2"), "T"),
    qe.Command("point", 9, "1/3", "-1/9", ("1/4", "1/2"), "T"),
    qe.Command("point", 9, "1/3", "1/18", ("1/4", "1/2"), "T"),
]


def reads():
    return qe.parse_qe(os.path.join(QE9, "QE.hbp"), TEST_PLAN, os.path.join(QE9, "QE-COST.hbp"))


class Parse(unittest.TestCase):
    def test_all_rows(self):
        r = reads()
        self.assertEqual(len(r), 10)
        self.assertEqual(qe.missing(r, TEST_PLAN), [])
        self.assertEqual(r[("sector", 9, "1/3", "0", "1/4")].layout, "sector")

    def test_smoke_value_reproduced(self):
        # the lane smoke (SM2) printed B_e18=7050781371498383 here; QSEL quotes it as 0.0070508
        x = reads()[("point", 9, "1/3", "1/9", "1/4")]
        self.assertEqual(x.v["B_e18"], 7050781371498383)
        self.assertEqual(fmt(x.B(), 5), "0.0070508")

    def test_rule_eb(self):
        x = reads()[("point", 9, "1/3", "1/9", "1/4")]
        self.assertEqual(x.v["eps_e18"], 922)
        eps = fr(923, ipow(10, 18))
        self.assertEqual(x.e_B(), 5 * (2 * eps + eps * eps) + fr(1, ipow(2, 21)))
        self.assertEqual(x.A_err(), fr(9, 2) * fr(52983428254, ipow(10, 18)))
        lo = fr(1677355164077467, ipow(10, 18)) - fr(2, 72) * fr(81, 4) * (2 * eps + eps * eps)
        self.assertEqual(x.C2_iv().lo, lo)
        self.assertTrue(x.QW_iv().lo > fr(1, 4))

    def test_plan_matches_frozen(self):
        self.assertTrue(qe.check_plan())
        self.assertEqual(len(qe.plan_triples()), 13)

    def test_guard_file(self):
        self.assertTrue(c.check_guard_file(os.path.join(QE9, "GUARD.hbp"),
                                           sorted({(cm.N, cm.delta, cm.y) for cm in TEST_PLAN})))
        with self.assertRaises(c.StageBStop):
            c.check_guard_file(os.path.join(QE9, "GUARD.hbp"), [(9, "1/3", "1/27")])


class Faults(unittest.TestCase):
    def _parse(self, text, cost=False):
        with TempDir() as d:
            p = os.path.join(d, "QE.hbp")
            write(p, text)
            return qe.parse_qe(p, TEST_PLAN, os.path.join(QE9, "QE-COST.hbp") if cost else None)

    def test_production_plan_refuses_other_points(self):
        with self.assertRaises(c.StageBStop) as e:
            qe.parse_qe(os.path.join(QE9, "QE.hbp"))
        self.assertEqual(e.exception.reason, "qe_unplanned_row")

    def test_repeated_row(self):
        t = read(os.path.join(QE9, "QE.hbp"))
        first = t.split("\n")[0]
        with self.assertRaises(c.StageBStop) as e:
            self._parse(t + first + "\n")
        self.assertEqual(e.exception.reason, "qe_repeated_row")

    def test_sabotage_tag(self):
        t = read(os.path.join(QE9, "QE.hbp"))
        t2 = t.replace("POLARITON_FIRST_CORRECTION_READ|N=9", "POLARITON_FIRST_CORRECTION_READ|sabotage=x|N=9", 1)
        with self.assertRaises(c.StageBStop):
            self._parse(t2)

    def test_float_used(self):
        t = read(os.path.join(QE9, "QE.hbp"))
        with self.assertRaises(c.StageBStop):
            self._parse(t.replace("|float_used=0|", "|float_used=1|", 1))

    def test_missing_row_is_not_measured(self):
        t = read(os.path.join(QE9, "QE.hbp"))
        r = self._parse("\n".join(t.split("\n")[1:]))
        self.assertEqual(len(qe.missing(r, TEST_PLAN)), 1)

    def test_cost_rows_must_match(self):
        t = read(os.path.join(QE9, "QE.hbp"))
        with self.assertRaises(c.StageBStop) as e:
            self._parse("\n".join(t.split("\n")[1:]), cost=True)
        self.assertEqual(e.exception.reason, "qe_cost")


class Helpers(unittest.TestCase):
    """The Q-row reads on the real N=9 rows."""

    def test_q01_zero_and_same(self):
        r = reads()
        for t in ("1/4", "1/2"):
            s, p = r[("sector", 9, "1/3", "0", t)], r[("point", 9, "1/3", "0", t)]
            self.assertEqual(rows_q.q01_zero(s)[0], c.MET)
            self.assertEqual(rows_q.q01_zero(p)[0], c.MET)
            self.assertEqual(rows_q.q01_same(s, p)[0], c.MET)
        self.assertEqual(rows_q.q01_zero(r[("point", 9, "1/3", "1/9", "1/4")])[0], c.MISS)

    def test_q01_mismatch_caught(self):
        r = reads()
        s, p = r[("sector", 9, "1/3", "0", "1/4")], r[("point", 9, "1/3", "0", "1/4")]
        p.d = dict(p.d, C2_e18=str(int(p.d["C2_e18"]) + 1))
        out, det = rows_q.q01_same(s, p)
        self.assertEqual(out, c.MISS)
        self.assertEqual(dict(det)["differ"], "C2_e18")

    def test_q02_parity(self):
        r = reads()
        for t in ("1/4", "1/2"):
            out, _ = rows_q.q02_parity(r[("point", 9, "1/3", "1/9", t)], r[("point", 9, "1/3", "-1/9", t)])
            self.assertEqual(out, c.MET)
        a, b = r[("point", 9, "1/3", "1/9", "1/4")], r[("point", 9, "1/3", "-1/9", "1/4")]
        b.v = dict(b.v, B_e18=b.v["B_e18"] + ipow(10, 12))
        self.assertEqual(rows_q.q02_parity(a, b)[0], c.MISS)

    def test_q03_ratio(self):
        r = reads()
        for t in ("1/4", "1/2"):
            iv = rows_q.q03_ratio(r[("point", 9, "1/3", "1/18", t)], r[("point", 9, "1/3", "1/9", t)])
            self.assertTrue(fr(24, 100) < iv.lo < iv.hi < fr(26, 100))
            self.assertTrue(iv.width() < fr(1, 1000))

    def test_q07_moments(self):
        x = reads()[("point", 9, "1/3", "1/9", "1/2")]
        ns = rows_q.q07_nstar(x)
        nn = rows_q.q07_nstar_normal(x)
        self.assertTrue(nn.hi < ns.lo)  # the normal order is lower by 1/(4<B>^2)
        self.assertIsNone(rows_q.q07_nstar(reads()[("point", 9, "1/3", "0", "1/2")]))


if __name__ == "__main__":
    unittest.main()
