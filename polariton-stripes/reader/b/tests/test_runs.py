"""twens run sums at the excluded points (tests/data/run: 8 batches of 512 at N=27, delta=1/4, y=1/40 and y=0)."""

import os
import shutil
import unittest

from stripes_read_b import common as c
from stripes_read_b import runs

from .util import AGG, RUN, X0, X1, XR0, XR1, TempDir, point_dir, read, with_trailer, write


def copy_run(d, ids=("XR1",)):
    for nm in os.listdir(RUN):
        if any(nm.startswith(i + ".") for i in ids):
            shutil.copy(os.path.join(RUN, nm), os.path.join(d, nm))


class Load(unittest.TestCase):
    def test_load(self):
        r = runs.load_run(RUN, XR1)
        self.assertEqual(r.steps, (32, 64, 128))
        self.assertEqual(len(r.batches), 8)
        self.assertEqual(r.M(), 4096)
        self.assertEqual(r.pooled(64)["n"], 4096)
        m, se2 = r.mean_br(128)
        self.assertTrue(se2 > 0)
        self.assertEqual(r.nstar(32), (None, None))  # |Bbar|^2_u <= 0 with 4096 samples at s = 0.13

    def test_run_equals_dump(self):
        # indices 0..4095 of the run (memo=1, threads=4) are call 0 of the X1 and X0 dumps (threads=1, no memo)
        for rid, spec, pspec, agg, steps in (("XR1", XR1, X1, "X1", (64, 128)), ("XR0", XR0, X0, "X0", (64,))):
            r = runs.load_run(RUN, spec)
            with TempDir() as d:
                point_dir(d, {"0.hbp": with_trailer(read(os.path.join(AGG, agg + ".0.agg"))),
                              "1.hbp": with_trailer(read(os.path.join(AGG, agg + ".1.agg")))})
                pt = c.load_point(d, pspec)
            for step in steps:
                a = pt.calls[0].sums[(step, "VNC", "all")]
                p = r.pooled(step)
                for k in ("br", "bi", "br2", "bi2", "brbi"):
                    self.assertEqual(a[k], p[k], (rid, step, k))
                self.assertEqual((a["bbr"], a["bbi"]), (p["rb_br"], p["rb_bi"]))


class Faults(unittest.TestCase):
    def test_dropped_batch(self):
        with TempDir() as d:
            copy_run(d)
            os.unlink(os.path.join(d, "XR1.5.hbp"))
            with self.assertRaises(c.StageBStop) as e:
                runs.load_run(d, XR1)
        self.assertEqual(e.exception.reason, "run_dropped_batch")

    def test_engine_stop_batch_is_lost(self):
        with TempDir() as d:
            copy_run(d)
            write(os.path.join(d, "XR1.5.hbp"), "")
            r = runs.load_run(d, XR1)
        self.assertEqual(r.lost, [(5, "engine_stop_empty")])
        self.assertEqual(r.M(), 3584)

    def test_rerun_with_last_record_dropped(self):
        with TempDir() as d:
            copy_run(d)
            p = os.path.join(d, "XR1.3.hbp")
            lines = read(p).split("\n")[:-1]
            head = lines[0].replace("|steps=32,64,128|", "|steps=32,64|")
            done = lines[-1].replace("|records=3|", "|records=2|")
            write(p, "\n".join([head] + lines[1:7] + [done]) + "\n")
            r = runs.load_run(d, XR1)
        self.assertEqual(r.steps, (32, 64))
        self.assertEqual(r.not_measured, (128,))

    def test_wrong_version(self):
        with TempDir() as d:
            copy_run(d)
            p = os.path.join(d, "XR1.0.hbp")
            write(p, read(p).replace("|version=0.4.0|", "|version=0.3.0|", 1))
            with self.assertRaises(c.StageBStop) as e:
                runs.load_run(d, XR1)
        self.assertEqual(e.exception.reason, "run_field")

    def test_altered_sum(self):
        with TempDir() as d:
            copy_run(d)
            p = os.path.join(d, "XR1.2.hbp")
            t = read(p)
            ln = [x for x in t.split("\n") if x.startswith("TWB|")][0]
            zr = [x for x in ln.split("|") if x.startswith("zr=")][0]
            write(p, t.replace(ln, ln.replace("|" + zr + "|", "|zr=%d|" % (int(zr[3:]) + 1))))
            with self.assertRaises(c.StageBStop) as e:
                runs.load_run(d, XR1)
        self.assertEqual(e.exception.reason, "run_legacy")

    def test_stderr(self):
        with TempDir() as d:
            copy_run(d)
            p = os.path.join(d, "XR1.1.err")
            write(p, read(p) + "TWB_FAULT|reason=x|json=0\n")
            with self.assertRaises(c.StageBStop) as e:
                runs.load_run(d, XR1)
        self.assertEqual(e.exception.reason, "run_stderr")

    def test_wrong_start(self):
        with TempDir() as d:
            copy_run(d)
            shutil.copy(os.path.join(d, "XR1.1.hbp"), os.path.join(d, "XR1.2.hbp"))
            with self.assertRaises(c.StageBStop):
                runs.load_run(d, XR1)

    def test_table(self):
        self.assertEqual(c.RUN_POINTS["R3"].per_batch, 262144)
        self.assertEqual(c.RUN_POINTS["R2"].seed_string, c.DUMP_POINTS["P08"].seed_string)
        self.assertEqual(c.RUN_POINTS["R3"].seed_string, c.DUMP_POINTS["P14"].seed_string)


if __name__ == "__main__":
    unittest.main()
