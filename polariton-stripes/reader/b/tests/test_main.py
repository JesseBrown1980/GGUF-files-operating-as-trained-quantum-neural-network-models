"""The READ-file audit of stripes_read_b/__main__.py on a small hand-built READ file: one read per PREDICT row."""

import contextlib
import io
import os
import re
import subprocess
import sys
import unittest

import stripes_read_b.__main__ as sb
from stripes_read_b import VERSION, qint
from stripes_read_b import common as c
from stripes_read_b import frozen
from stripes_read_b.hbp import sha256_hex

FZ = frozen.load()
ORDER = [d["id"] for k, d, _ in FZ.rows if k == "STRIPES_PREDICT"]


def read_row(rid, read="r1", scored=True, why="symmetry", verdict=c.MET):
    return ("STRIPES_READ|row=%s|read=%s|at=x|kind=exact|scored=%d|why=%s|value=none|lo=none|hi=none|band=none|"
            "frozen=none|verdict=%s|detail=none|json=0" % (rid, read, 1 if scored else 0, why, verdict))


def verdict_row(rid, reads=2, scored=1, met=1, miss=0, falsifier="none", verdict=c.MET):
    p = FZ.predict(rid)
    return ("STRIPES_VERDICT|row=%s|name=%s|tag=%s|reads=%d|scored=%d|report=%d|met=%d|miss=%d|not_resolved=0|"
            "not_measured=0|falsifier=%s|verdict=%s|json=0" % (rid, p["name"], p["tag"], reads, scored,
                                                               reads - scored, met, miss, falsifier, verdict))


def build(reads=None, verdicts=None):
    head = ("STRIPES_READ_HEAD|reader=stripes-read-b|reader_version=%s|frozen=polariton-stripes/"
            "PREDICTION-STRIPE-PHASE.hbp|frozen_sha256=%s|rows=%s|json=0" % (VERSION, FZ.sha256, ",".join(ORDER)))
    reads = reads or {rid: [read_row(rid), read_row(rid, "r2", False, "X08", c.REPORT)] for rid in ORDER}
    verdicts = verdicts or {rid: verdict_row(rid) for rid in ORDER}
    body = [head] + [x for rid in ORDER for x in reads[rid]] + [verdicts[rid] for rid in ORDER]
    h = sha256_hex("".join(x + "\n" for x in body).encode("ascii"))
    return body + ["STRIPES_READ_END|rows=%d|sha256=%s|json=0" % (len(body), h)]


def reason(lines, table=False):
    try:
        sb.audit_lines(lines, FZ, table=table)
    except c.StageBStop as e:
        return e.reason
    return None


class Audit(unittest.TestCase):
    def test_clean_file(self):
        self.assertIsNone(reason(build()))

    def test_scoring_table_of_the_reader(self):
        lines = build()
        self.assertEqual(reason(lines, table=None), "scoring_table")  # SCORING is the real rows' table
        got = sb.audit_lines(lines, FZ, table=False)
        self.assertIsNone(reason(lines, table=got))
        tbl = dict(got)
        tbl["E15"] = (2, 2, tbl["E15"][2])
        self.assertEqual(reason(lines, table=tbl), "scoring_table")

    def test_end_hash(self):
        lines = build()
        lines[1] = lines[1].replace("|value=none|", "|value=1|")
        self.assertEqual(reason(lines), "read_file_sha256")

    def test_promoted_read(self):
        reads = {rid: [read_row(rid), read_row(rid, "r2", False, "X08", c.REPORT)] for rid in ORDER}
        reads["E17"][1] = read_row("E17", "r2", True, "X08", c.MET)
        v = {rid: verdict_row(rid) for rid in ORDER}
        v["E17"] = verdict_row("E17", scored=2, met=2)
        self.assertEqual(reason(build(reads, v)), "scored_read")

    def test_falsifier_on_report_read(self):
        v = {rid: verdict_row(rid) for rid in ORDER}
        v["E17"] = verdict_row("E17", falsifier="r2:" + FZ.predict("E17")["falsifier"], verdict=c.NOT_MET)
        self.assertEqual(reason(build(verdicts=v)), "falsifier")
        v["E17"] = verdict_row("E17", falsifier="r1:not_the_frozen_text", verdict=c.NOT_MET)
        self.assertEqual(reason(build(verdicts=v)), "falsifier")
        v["E17"] = verdict_row("E17", falsifier="r1:" + FZ.predict("E17")["falsifier"], verdict=c.NOT_MET)
        self.assertIsNone(reason(build(verdicts=v)))

    def test_counts_and_verdict_rule(self):
        v = {rid: verdict_row(rid) for rid in ORDER}
        v["Q03"] = verdict_row("Q03", met=0)
        self.assertEqual(reason(build(verdicts=v)), "verdict_counts")
        v["Q03"] = verdict_row("Q03", verdict=c.NOT_RESOLVED)
        self.assertEqual(reason(build(verdicts=v)), "verdict_rule")
        reads = {rid: [read_row(rid), read_row(rid, "r2", False, "X08", c.REPORT)] for rid in ORDER}
        reads["Q03"][0] = read_row("Q03", verdict=c.MISS)
        v["Q03"] = verdict_row("Q03", met=0, miss=1, verdict=c.NOT_MET)
        self.assertIsNone(reason(build(reads, v)))

    def test_one_verdict_per_predict_row(self):
        lines = build()
        drop = [k for k, ln in enumerate(lines) if ln.startswith("STRIPES_VERDICT|row=E09|")][0]
        body = lines[:drop] + lines[drop + 1:-1]
        h = sha256_hex("".join(x + "\n" for x in body).encode("ascii"))
        self.assertEqual(reason(body + ["STRIPES_READ_END|rows=%d|sha256=%s|json=0" % (len(body), h)]),
                         "verdict_rows")

    def test_row_verdict_rule(self):
        met, miss = {"verdict": c.MET}, {"verdict": c.MISS}
        nm, nr = {"verdict": c.NOT_MEASURED}, {"verdict": c.NOT_RESOLVED}
        self.assertEqual(sb._row_verdict([met, met], False), c.MET)
        self.assertEqual(sb._row_verdict([met, miss], False), c.NOT_MET)
        self.assertEqual(sb._row_verdict([met], True), c.NOT_MET)
        self.assertEqual(sb._row_verdict([], False), c.NONE)
        self.assertEqual(sb._row_verdict([nm, nm], False), c.NOT_MEASURED)
        self.assertEqual(sb._row_verdict([met, nr], False), c.NOT_RESOLVED)
        self.assertEqual(sb._row_verdict([met, nm], False), c.NOT_RESOLVED)

    def test_rules_agree_with_common(self):
        for outs, fals in (((c.MET, c.MET), False), ((c.MET, c.MISS), False), ((c.NOT_MEASURED,), False),
                           ((c.MET, c.NOT_RESOLVED), False), ((c.MET,), True)):
            rs = [c.Read("T", "r%d" % k, "x", "exact", c.scored(), o) for k, o in enumerate(outs)]
            self.assertEqual(sb._row_verdict([{"verdict": r.verdict} for r in rs], fals), c.row_verdict(rs, fals))


FLOAT_EVIDENCE = os.path.join(os.path.dirname(sb.B_DIR), "check", "float_evidence.py")


class Provenance(unittest.TestCase):
    """The READ file names the stage B that wrote it (quantum review 2, M3), and stray floats end in a STOP row."""

    def test_version(self):
        self.assertEqual((VERSION, c.READER_VERSION), ("0.2.0", "0.2.0"))

    def test_tree_pin(self):
        path, pin = sb.stage_b_tree()
        self.assertEqual(path, "polariton-stripes/reader/b")
        self.assertTrue(re.fullmatch("[0-9a-f]{64}", pin))
        # the rule of check/float_evidence.py, which lists the files git would track: the same pin
        if not os.path.exists(os.path.join(sb.REPO, ".git")):
            self.skipTest("no git checkout around this stage B")
        p = subprocess.run([sys.executable, "-I", FLOAT_EVIDENCE, "--repo", sb.REPO, "--pins", path + "/"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual((p.returncode, p.stdout.decode("ascii")), (0, "%s/ | tree=%s | \n" % (path, pin)))

    def _main(self, fn):
        sb.COMMANDS["probe_exit"] = fn
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                rc = sb.main(["stripes_read_b", "probe_exit"])
        finally:
            del sb.COMMANDS["probe_exit"]
        return rc, out.getvalue()

    def test_stray_float_is_a_stop_row(self):
        rc, text = self._main(lambda argv: qint.make(1, 3) * qint.make(1, 2) + True)  # a bool is not an int here
        self.assertEqual(rc, 3)
        self.assertRegex(text, r"^STOP\|reader=stripes-read-b\|reader_version=%s\|reason=qint\|detail=QintError:" %
                         re.escape(VERSION))
        rc, text = self._main(lambda argv: qint.div(1, 0))
        self.assertEqual(rc, 3)
        self.assertIn("|reason=qint|detail=ZeroDivisionError:", text)


if __name__ == "__main__":
    unittest.main()
