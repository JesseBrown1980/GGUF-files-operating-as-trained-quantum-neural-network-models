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
        self.assertEqual(len(qe.plan_guards()), 15)
        self.assertEqual(qe.argv_text(qe.PLAN[0]), "sector_81_81_-1/4_0_6_1/2,1,2,4")

    def test_guard_file(self):
        g = os.path.join(QE9, "GUARD.hbp")
        self.assertTrue(c.check_guard_file(g, qe.plan_guards(TEST_PLAN)))  # one line per command, 2 at y=0
        with self.assertRaises(c.StageBStop):
            c.check_guard_file(g, [(9, "1/3", "1/27")])
        with self.assertRaises(c.StageBStop) as e:
            c.check_guard_file(g, qe.plan_guards(TEST_PLAN) + [(9, "1/3", "0")])  # 3 commands at y=0, 2 lines
        self.assertEqual(e.exception.reason, "guard")
        refused = "TWB_GUARD|N=9|delta=1/3|y=1/27|verdict=refused|reason=reserved|computed=0|json=0\n"
        with TempDir() as d:
            p = os.path.join(d, "GUARD.hbp")
            write(p, read(g) + refused)
            self.assertTrue(c.check_guard_file(p, qe.plan_guards(TEST_PLAN)))  # a refusal outside the plan
            with self.assertRaises(c.StageBStop):
                c.check_guard_file(p, qe.plan_guards(TEST_PLAN) + [(9, "1/3", "1/27")])


def rc_text(plan, rcs=None, binary=qe.LANE_BINARY_SHA256):
    """QE-RC.hbp as the wrapper files it: the binary's sha256, then one QE_RC row per command after it ran."""
    rcs = rcs or [0] * len(plan)
    return "QE_BINARY|sha256=%s|json=0\n" % binary + "".join(
        "QE_RC|argv=%s|rc=%d|json=0\n" % (qe.argv_text(cm), rc) for cm, rc in zip(plan, rcs, strict=True))


PANIC = ("thread 'main' panicked at src/bin/polariton_first_correction.rs:1967:57:\nre\n"
         "note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\n")


class Stop(unittest.TestCase):
    """Rule STOP for QE: a QE exit or a missing READ row leaves its reads NOT_MEASURED."""

    def _parse(self, qe_text=None, cost_text=None, rc=None):
        with TempDir() as d:
            paths = {}
            for name, text in (("QE.hbp", qe_text), ("QE-COST.hbp", cost_text), ("QE-RC.hbp", rc)):
                paths[name] = os.path.join(d, name)
                write(paths[name], read(os.path.join(QE9, name)) if text is None and name != "QE-RC.hbp" else
                      (text if text is not None else rc_text(TEST_PLAN)))
            return qe.parse_qe(paths["QE.hbp"], TEST_PLAN, paths["QE-COST.hbp"], paths["QE-RC.hbp"])

    def test_every_command_exited_0(self):
        r = self._parse()
        self.assertEqual(len(r), 10)
        self.assertEqual((r.failed, r.stderr_lines, r.binary), ([], 0, qe.LANE_BINARY_SHA256))

    def test_panic_with_rc_101(self):
        # point 9 9 1/3 1/9 printed its t=1/4 rows, then panicked: rc=101 and the panic text on stderr
        reads = read(os.path.join(QE9, "QE.hbp")).split("\n")[:-1]
        costs = read(os.path.join(QE9, "QE-COST.hbp")).split("\n")[:-1]
        cut = [k for k, ln in enumerate(reads) if "|y=1/9|" in ln and "|t=1/2|" in ln][0]
        qe_text = "".join(x + "\n" for k, x in enumerate(reads) if k != cut)
        cost_text = "".join(x + "\n" for x in costs[:cut]) + PANIC + "".join(x + "\n" for x in costs[cut + 1:])
        r = self._parse(qe_text, cost_text, rc_text(TEST_PLAN, [0, 0, 101, 0, 0]))
        self.assertEqual(r.failed, [("point_9_9_1/3_1/9_6_1/4,1/2", 101)])
        self.assertEqual(r.stderr_lines, 3)
        self.assertEqual(len(r), 8)  # both reads of the command left out, the t=1/4 row it printed included
        self.assertIsNone(qe.get(r, "point", 9, "1/3", "1/9", "1/4"))
        self.assertEqual(sorted(qe.missing(r, TEST_PLAN)), [("point", 9, "1/3", "1/9", "1/2"),
                                                            ("point", 9, "1/3", "1/9", "1/4")])
        self.assertEqual(qe.lost_why(r, [("point", 9, "1/3", "1/9", "1/2")]), "qe_rc_101")
        self.assertEqual(qe.lost_why({}, [("point", 9, "1/3", "1/9", "1/2")]), "missing_QE_row")
        # a READ row printed without its COST row by the command that exited is left out of the match too
        cost_text2 = "".join(x + "\n" for k, x in enumerate(costs) if k not in (cut - 1, cut)) + PANIC
        self.assertEqual(len(self._parse(qe_text, cost_text2, rc_text(TEST_PLAN, [0, 0, 101, 0, 0]))), 8)

    def test_stderr_text_with_every_rc_0(self):
        cost = read(os.path.join(QE9, "QE-COST.hbp")) + PANIC
        with self.assertRaises(c.StageBStop) as e:
            self._parse(cost_text=cost)
        self.assertEqual(e.exception.reason, "qe_stderr")
        with TempDir() as d:
            p = os.path.join(d, "QE-COST.hbp")
            write(p, cost)
            with self.assertRaises(c.StageBStop) as e:
                qe.parse_qe(os.path.join(QE9, "QE.hbp"), TEST_PLAN, p)
        self.assertEqual(e.exception.reason, "qe_stderr")

    def test_cost_rows_still_match_for_the_commands_that_exited_0(self):
        costs = read(os.path.join(QE9, "QE-COST.hbp")).split("\n")[:-1]
        cost_text = "".join(x + "\n" for k, x in enumerate(costs) if k != 0)  # sector t=1/4 COST row lost
        with self.assertRaises(c.StageBStop) as e:
            self._parse(cost_text=cost_text, rc=rc_text(TEST_PLAN, [0, 0, 101, 0, 0]))
        self.assertEqual(e.exception.reason, "qe_cost")

    def test_rc_rows_follow_the_plan(self):
        for bad in (rc_text(TEST_PLAN[:-1]), rc_text(TEST_PLAN[::-1]), rc_text(TEST_PLAN, binary="x" * 64),
                    rc_text(TEST_PLAN).replace("|rc=0|", "|rc=00|", 1)):
            with self.assertRaises(c.StageBStop) as e:
                self._parse(rc=bad)
            self.assertEqual(e.exception.reason, "qe_rc")


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
            self.assertTrue(iv.bounded())
            self.assertTrue(fr(24, 100) < iv.lo < iv.hi < fr(26, 100))
            self.assertTrue(iv.hi - iv.lo < fr(1, 1000))

    def test_q07_moments(self):
        x = reads()[("point", 9, "1/3", "1/9", "1/2")]
        ns = rows_q.q07_nstar(x)
        nn = rows_q.q07_nstar_normal(x)
        self.assertTrue(nn.hi < ns.lo)  # the normal order is lower by 1/(4<B>^2)
        # B_e18 = 0 at y = 0: n*_Q is the half-line [Q_W.lo/e_B^2 - 1, +inf)
        z = reads()[("point", 9, "1/3", "0", "1/2")]
        ns0 = rows_q.q07_nstar(z)
        b = z.absB_iv()
        self.assertEqual((z.v["B_e18"], b.lo, ns0.hi), (0, 0, None))
        self.assertTrue(ns0.lo > ipow(10, 9))
        self.assertTrue((ns0.lo + 1) * b.hi * b.hi <= z.QW_iv().lo)


if __name__ == "__main__":
    unittest.main()
