"""twens run sums at the excluded points (tests/data/run: 8 batches of 512 at N=27, delta=1/4, y=1/40 and y=0)."""

import os
import shutil
import unittest

from stripes_read_b import common as c
from stripes_read_b import runs

from .util import AGG, ENGINE_FAULT, RUN, X0, X1, XR0, XR1, TempDir, point_dir, read, with_trailer, write


def copy_run(d, ids=("XR1",)):
    for nm in os.listdir(RUN):
        if any(nm.startswith(i + ".") for i in ids):
            shutil.copy(os.path.join(RUN, nm), os.path.join(d, nm))


def try_steps(stem):
    """The steps rule STOP gives a try of an XR1 batch (3 records): attempt k ran the first 4 - k, the last try of a
    lost batch ran one."""
    k = int(stem.split(".attempt")[1]) if ".attempt" in stem else 3
    return ",".join(("32", "64", "128")[: 4 - k])


def engine_stop(d, stem, steps=None):
    """A try of a batch whose engine exited 4: nothing on stdout, a TWB_FAULT row on stderr, rc=4 and its steps."""
    write(os.path.join(d, stem + ".hbp"), "")
    write(os.path.join(d, stem + ".err"), ENGINE_FAULT)
    write(os.path.join(d, stem + ".rc"), "rc=4 steps=%s\n" % (try_steps(stem) if steps is None else steps))


def truncate(d, j, records):
    """Batch j of XR1 rerun with its first `records` records (the head, the TWENS/TWB/TWB_ROUND triples, TWB_DONE)."""
    p = os.path.join(d, "XR1.%d.hbp" % j)
    lines = read(p).split("\n")[:-1]
    steps = ",".join(("32", "64", "128")[:records])
    head = lines[0].replace("|steps=32,64,128|", "|steps=%s|" % steps)
    done = lines[-1].replace("|records=3|", "|records=%d|" % records)
    write(p, "\n".join([head] + lines[1:1 + 3 * records] + [done]) + "\n")
    write(os.path.join(d, "XR1.%d.rc" % j), "rc=0 steps=%s\n" % steps)


def run_reason(d):
    try:
        runs.load_run(d, XR1)
    except c.StageBStop as e:
        return e.reason
    return None


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
        # XR1 has 3 records: a lost batch was tried with 3 and 2 records (attempts 1, 2) and with 1 (the batch files)
        with TempDir() as d:
            copy_run(d)
            for stem in ("XR1.5", "XR1.5.attempt1", "XR1.5.attempt2"):
                engine_stop(d, stem)
            r = runs.load_run(d, XR1)
        self.assertEqual(r.lost, [(5, "engine_stop_rc4")])
        self.assertEqual(r.attempts, 2)
        self.assertEqual(len(r.batches), 7)  # the other batches are still checked
        # rule STOP: the point keeps only the records all 8 batches reached; the lost batch reached none
        self.assertEqual(r.steps, ())
        self.assertEqual(r.not_measured, (32, 64, 128))
        with self.assertRaises(c.StageBStop) as e:
            r.pooled(32)
        self.assertEqual(e.exception.reason, "not_measured_record")

    def test_rerun_with_last_record_dropped(self):
        with TempDir() as d:
            copy_run(d)
            truncate(d, 3, 2)
            engine_stop(d, "XR1.3.attempt1")
            r = runs.load_run(d, XR1)
        self.assertEqual(r.steps, (32, 64))
        self.assertEqual(r.not_measured, (128,))
        self.assertEqual(r.attempts, 1)

    def test_empty_batch_without_its_attempts(self):
        with TempDir() as d:
            copy_run(d)
            engine_stop(d, "XR1.5")
            self.assertEqual(run_reason(d), "stop_attempt_count")
            engine_stop(d, "XR1.5.attempt1")
            self.assertEqual(run_reason(d), "stop_attempt_count")  # the one-record try is missing
            write(os.path.join(d, "XR1.5.rc"), "rc=0 steps=32,64,128\n")
            self.assertEqual(run_reason(d), "run_rows")  # an empty stdout with rc=0

    def test_truncated_batch_without_its_attempt(self):
        with TempDir() as d:
            copy_run(d)
            truncate(d, 3, 2)
            self.assertEqual(run_reason(d), "stop_attempt_count")
            engine_stop(d, "XR1.0.attempt1")
            engine_stop(d, "XR1.3.attempt1")
            self.assertEqual(run_reason(d), "stop_attempt_count")  # attempts on the complete batch 0

    def test_attempt_evidence(self):
        with TempDir() as d:
            copy_run(d)
            truncate(d, 3, 2)
            engine_stop(d, "XR1.3.attempt1")
            write(os.path.join(d, "XR1.3.attempt1.err"), "")
            self.assertEqual(run_reason(d), "stop_engine_stderr")  # exit 4 without its TWB_FAULT row
            write(os.path.join(d, "XR1.3.attempt1.err"), ENGINE_FAULT + ENGINE_FAULT)
            self.assertIsNone(run_reason(d))  # one row per stopped thread (threads=4)
            write(os.path.join(d, "XR1.3.attempt1.rc"), "rc=137 steps=32,64,128\n")
            self.assertEqual(run_reason(d), "stop_attempt_file")
            write(os.path.join(d, "XR1.3.attempt1.rc"), "rc=4 steps=32,64,128\n")
            write(os.path.join(d, "XR1.3.attempt1.hbp"), read(os.path.join(RUN, "XR1.3.hbp")))
            self.assertEqual(run_reason(d), "stop_attempt_file")  # a complete batch filed as an attempt
            os.unlink(os.path.join(d, "XR1.3.attempt1.rc"))
            self.assertEqual(run_reason(d), "stop_attempt_file")

    def test_exit_codes(self):
        with TempDir() as d:
            copy_run(d)
            os.unlink(os.path.join(d, "XR1.2.rc"))
            self.assertEqual(run_reason(d), "run_rc")
            write(os.path.join(d, "XR1.2.rc"), "rc=137 steps=32,64,128\n")
            self.assertEqual(run_reason(d), "run_rc")  # a crash or a kill is not an engine stop
            write(os.path.join(d, "XR1.2.rc"), "rc=00 steps=32,64,128\n")
            self.assertEqual(run_reason(d), "run_rc")
            write(os.path.join(d, "XR1.2.rc"), "rc=0\n")
            self.assertEqual(run_reason(d), "run_rc")  # no steps
            write(os.path.join(d, "XR1.2.rc"), "rc=0 steps=32,64,128\n")
            write(os.path.join(d, "XR1.2.bak"), "")
            self.assertEqual(run_reason(d), "run_extra_file")

    def test_steps_of_each_try(self):
        with TempDir() as d:
            copy_run(d)
            truncate(d, 3, 2)
            engine_stop(d, "XR1.3.attempt1", steps="32,64")
            self.assertEqual(run_reason(d), "stop_attempt_steps")  # attempt 1 ran all 3 records
            engine_stop(d, "XR1.3.attempt1")
            self.assertIsNone(run_reason(d))
            write(os.path.join(d, "XR1.3.rc"), "rc=0 steps=32,64,128\n")
            self.assertEqual(run_reason(d), "stop_trailer_steps")  # the batch printed 2 records
        with TempDir() as d:
            copy_run(d)
            for stem in ("XR1.5.attempt1", "XR1.5.attempt2"):
                engine_stop(d, stem)
            engine_stop(d, "XR1.5", steps="32,64")
            self.assertEqual(run_reason(d), "stop_attempt_steps")  # the last try runs one record
            engine_stop(d, "XR1.5")
            self.assertIsNone(run_reason(d))

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
