"""Stage A blocks at the excluded points X1 (y=1/40) and X0 (y=0): parsing, pooling, rules SEED and STOP, and the
planted faults stage B must refuse."""

import os
import shutil
import unittest

from stripes_read_b import common as c
from stripes_read_b.hbp import fields_dict, parse_row, sha256_hex

from .util import AGG, ENGINE_FAULT, EXCL, X0, X1, TempDir, point_dir, read, rehash, with_trailer, write


def x1_files(call1="X1.1.agg"):
    return {"0.hbp": with_trailer(read(os.path.join(AGG, "X1.0.agg"))),
            "1.hbp": with_trailer(read(os.path.join(AGG, call1)))}


def engine_stop(steps="64,128"):
    """What the run script files for a try of X1 call 1 whose engine stopped: stage A's empty_stream STOP, rc=4
    rc_reader=3 and the steps the try ran with (point_dir adds the engine's TWB_FAULT row as 1.eng.err or
    1.attempt<k>.eng.err). X1 has 2 records: attempt 1 ran 64,128; the last try of a lost call ran 64."""
    return with_trailer(read(os.path.join(AGG, "X1.1.empty.agg")), rc=4, rc_reader=3, steps=steps)


def stop_reason(files, **kw):
    with TempDir() as d:
        point_dir(d, files, **kw)
        try:
            c.load_point(d, X1)
        except c.StageBStop as e:
            return e.reason
    return None


class Parse(unittest.TestCase):
    def test_block_fields(self):
        with TempDir() as d:
            point_dir(d, x1_files())
            pt = c.load_point(d, X1)
        self.assertEqual(pt.steps, (64, 128))
        self.assertEqual(pt.not_measured, ())
        b = pt.calls[0]
        self.assertEqual(b.variants, c.VARIANTS)
        self.assertTrue(b.nl)
        self.assertEqual(b.atoms, {"M": 4096, "nl_klein": 2, "nl_exch": 1, "lk_klein": 165, "lk_exch": 47})
        self.assertEqual(b.vr[(64, "VNC")]["sec"][:3], [257, 239, 247])
        self.assertEqual(b.vr[(64, "LOCK")]["atoms"], 47)
        self.assertEqual(b.lock[64], {"cert": 4049, "mis": 1854})
        self.assertEqual(b.cmp[(64, "MODE0")]["br"], [2054, 0, 0, 0, 2041, 0, 0, 0, 0])
        self.assertEqual(len(b.blk), 2 * 7 * 11)
        self.assertEqual(b.side["indices"], 4096)

    def test_pooling_adds_calls(self):
        with TempDir() as d:
            point_dir(d, x1_files())
            pt = c.load_point(d, X1)
        b0, b1 = pt.calls[0], pt.calls[1]
        for step in (64, 128):
            for v in c.VARIANTS:
                p = pt.vr(step, v)
                pair = zip(b0.vr[(step, v)]["sec"], b1.vr[(step, v)]["sec"], strict=True)
                self.assertEqual(p["sec"], [x + y for x, y in pair])
                self.assertEqual(p["mp"], b0.vr[(step, v)]["mp"] + b1.vr[(step, v)]["mp"])
                s = pt.sums(step, v)
                self.assertEqual(s["br2"], b0.sums[(step, v, "all")]["br2"] + b1.sums[(step, v, "all")]["br2"])
                na = pt.sums(step, v, "nonatom")
                self.assertEqual(na["m"], p["mp"])
                k = pt.blk(step, v, 4096)
                self.assertEqual(k["K"], 2)
                self.assertEqual(k["w"], s["br2"] + s["bi2"])
            self.assertEqual(len(pt.nl_rows(step)), 1)  # E05: one NL row across the calls
            self.assertEqual(sorted(list(pt.nl_rows(step).values())[0]), [0, 1])
        self.assertEqual(pt.M(), 8192)
        self.assertEqual(pt.M("ctrl", "LOCK"), 8192)
        lat = pt.lat()
        self.assertEqual(lat["lock_atoms"] + lat["lat_edge"] + sum(lat["lat"]), 8192)
        self.assertEqual(len(pt.per_call_sums(64, "VNC")), 2)

    def test_y0_atoms(self):
        files = {"0.hbp": with_trailer(read(os.path.join(AGG, "X0.0.agg"))),
                 "1.hbp": with_trailer(read(os.path.join(AGG, "X0.1.agg")))}
        with TempDir() as d:
            point_dir(d, files)
            pt = c.load_point(d, X0)
        b = pt.calls[0]
        self.assertEqual(b.call_row["y_zero"], "1")
        for v in c.VARIANTS:
            atoms = b.vr[(64, v)]["atoms"]
            self.assertEqual(atoms, b.atoms["lk_klein"] if v == "LOCK" else b.atoms["nl_klein"])
            self.assertEqual(b.vr[(64, v)]["xatom_bi_nz"], 0)  # exchange holds bit-exactly
        nl = list(pt.nl_rows(64))[0]
        d = fields_dict(parse_row(nl, "TWB_NL")[1])
        self.assertEqual((d["br"], d["bi"]), ("0", "0"))  # E05 at y=0: the fixed point


class Seed(unittest.TestCase):
    def test_dropped_call(self):
        with TempDir() as d:
            point_dir(d, {"0.hbp": x1_files()["0.hbp"]})
            with self.assertRaises(c.StageBStop) as e:
                c.load_point(d, X1)
        self.assertEqual(e.exception.reason, "seed_dropped_call")

    def test_extra_call(self):
        f = x1_files()
        f["2.hbp"] = f["1.hbp"]
        with TempDir() as d:
            point_dir(d, f)
            with self.assertRaises(c.StageBStop) as e:
                c.load_point(d, X1)
        self.assertEqual(e.exception.reason, "seed_extra_call")

    def test_stray_file(self):
        f = x1_files()
        f["1.hbp.bak"] = f["1.hbp"]
        with TempDir() as d:
            point_dir(d, f)
            with self.assertRaises(c.StageBStop) as e:
                c.load_point(d, X1)
        self.assertEqual(e.exception.reason, "seed_extra_file")

    def test_call_filed_under_another_index(self):
        f = x1_files()
        f["1.hbp"] = f["0.hbp"]
        with TempDir() as d:
            point_dir(d, f)
            with self.assertRaises(c.StageBStop) as e:
                c.load_point(d, X1)
        self.assertEqual(e.exception.reason, "block_pc")

    def test_wrong_point(self):
        files = {"0.hbp": with_trailer(read(os.path.join(AGG, "X0.0.agg"))), "1.hbp": x1_files()["1.hbp"]}
        with TempDir() as d:
            point_dir(d, files)
            with self.assertRaises(c.StageBStop) as e:
                c.load_point(d, X1)
        self.assertEqual(e.exception.reason, "block_pc")

    def test_sums_file(self):
        with TempDir() as d:
            point_dir(d, x1_files())
            c.write_sha256sums(d)
            self.assertEqual(c.load_point(d, X1, require_sums=True).steps, (64, 128))
            write(os.path.join(d, "1.hbp"), x1_files()["1.hbp"].replace("rc=0 rc_reader=0", "rc=0  rc_reader=0"))
            with self.assertRaises(c.StageBStop) as e:
                c.load_point(d, X1, require_sums=True)
        self.assertEqual(e.exception.reason, "sha256sums")


class Stop(unittest.TestCase):
    def test_truncated_record(self):
        f = x1_files("X1.1.steps64.agg")
        f["1.attempt1.hbp"] = engine_stop()
        with TempDir() as d:
            point_dir(d, f)
            pt = c.load_point(d, X1)
            self.assertEqual(pt.steps, (64,))
            self.assertEqual(pt.not_measured, (128,))
            self.assertFalse(pt.measured(128))
            self.assertEqual(pt.attempts, ["1.attempt1.hbp"])
            with self.assertRaises(c.StageBStop) as e:
                pt.vr(128, "VNC")
        self.assertEqual(e.exception.reason, "not_measured_record")

    def test_engine_stop_loses_the_call(self):
        # X1 has 2 records: a lost call was tried with 2 records (attempt 1) and with 1 (the call file)
        f = x1_files()
        f["1.hbp"] = engine_stop("64")
        f["1.attempt1.hbp"] = engine_stop()
        with TempDir() as d:
            point_dir(d, f)
            pt = c.load_point(d, X1)
        self.assertEqual(pt.lost, [(1, "engine_stop_rc4")])
        self.assertEqual(pt.attempts, ["1.attempt1.hbp"])
        self.assertEqual(pt.M(), 4096)
        self.assertEqual(pt.lost_indices(), [(4096, 8192)])
        self.assertEqual(pt.steps, (64, 128))

    def test_probe_a_truncated_call_without_its_attempt(self):
        # a record dropped with no evidence of an exit 4 (review probe A)
        self.assertEqual(stop_reason(x1_files("X1.1.steps64.agg")), "stop_attempt_count")

    def test_probe_b_complete_block_filed_as_an_attempt(self):
        # the complete block renamed to an attempt and a shorter rerun kept: data seen would be discarded (probe B)
        f = x1_files("X1.1.steps64.agg")
        f["1.attempt1.hbp"] = with_trailer(read(os.path.join(AGG, "X1.1.agg")))
        f["1.attempt1.eng.err"] = ENGINE_FAULT
        self.assertEqual(stop_reason(f), "stop_attempt_file")

    def test_probe_c_attempt_that_is_not_a_row(self):
        f = x1_files("X1.1.steps64.agg")
        f["1.attempt1.hbp"] = "anything\n"
        f["1.attempt1.eng.err"] = ENGINE_FAULT
        self.assertEqual(stop_reason(f), "stop_attempt_file")

    def test_attempts_on_a_complete_call(self):
        f = x1_files()
        f["1.attempt1.hbp"] = engine_stop()
        self.assertEqual(stop_reason(f), "stop_attempt_count")

    def test_lost_call_needs_every_try(self):
        f = x1_files()
        f["1.hbp"] = engine_stop("64")
        self.assertEqual(stop_reason(f), "stop_attempt_count")  # no one-record try
        f["1.attempt2.hbp"] = engine_stop()
        self.assertEqual(stop_reason(f), "stop_attempt_count")  # attempts numbered from 1
        f["1.attempt1.hbp"] = engine_stop()
        self.assertEqual(stop_reason(f), "stop_attempt_count")  # one try too many

    def test_attempt_of_another_call(self):
        f = x1_files("X1.1.steps64.agg")
        f["1.attempt1.hbp"] = engine_stop().replace("|call=1|", "|call=0|")
        self.assertEqual(stop_reason(f), "stop_attempt_file")

    def test_attempt_with_another_exit(self):
        f = x1_files("X1.1.steps64.agg")
        f["1.attempt1.hbp"] = with_trailer(read(os.path.join(AGG, "X1.1.empty.agg")), rc=2, rc_reader=3,
                                           steps="64,128")
        f["1.attempt1.eng.err"] = ENGINE_FAULT
        self.assertEqual(stop_reason(f), "stop_attempt_file")

    def test_engine_stderr(self):
        # an exit 4 must file its TWB_FAULT row; a completed call files an empty engine stderr
        f = x1_files("X1.1.steps64.agg")
        f["1.attempt1.hbp"] = engine_stop()
        f["1.attempt1.eng.err"] = ""
        self.assertEqual(stop_reason(f), "stop_engine_stderr")
        f["1.attempt1.eng.err"] = "TWB_FAULT|reason=memo_count_check|count=1|ps=0|k4=0+0|k2=0+0|json=0\n"
        self.assertEqual(stop_reason(f), "stop_engine_stderr")  # an exit-6 fault, not an exit 4
        f["1.attempt1.eng.err"] = "TWB_FAULT|reason=sharp_mode0_argument_not_positive|arg=-5|json=0\n"
        self.assertIsNone(stop_reason(f))
        f["1.eng.err"] = ENGINE_FAULT
        self.assertEqual(stop_reason(f), "stop_engine_stderr")
        del f["1.eng.err"]
        with TempDir() as d:
            point_dir(d, f, engine_err=False)
            for k in ("0.eng.err", "1.attempt1.eng.err"):
                write(os.path.join(d, k), "")
            with self.assertRaises(c.StageBStop) as e:
                c.load_point(d, X1)
        self.assertEqual(e.exception.reason, "stop_engine_stderr")  # 1.eng.err not filed

    def test_stage_a_stderr(self):
        f = x1_files()
        f["0.err"] = ""
        self.assertIsNone(stop_reason(f))
        f["0.err"] = "x\n"
        self.assertEqual(stop_reason(f), "reader_stderr")
        f = x1_files("X1.1.steps64.agg")
        f["1.attempt1.hbp"] = engine_stop()
        f["1.attempt1.err"] = read(os.path.join(AGG, "X1.1.empty.agg"))
        self.assertIsNone(stop_reason(f))

    def test_orphan_stderr_file(self):
        f = x1_files()
        f["1.attempt1.eng.err"] = ENGINE_FAULT
        self.assertEqual(stop_reason(f), "seed_extra_file")

    def test_sums_list_every_receipt(self):
        f = x1_files("X1.1.steps64.agg")
        f["1.attempt1.hbp"] = engine_stop()
        with TempDir() as d:
            point_dir(d, f)
            c.write_sha256sums(d)
            listed = sorted(ln.split("  ")[1] for ln in read(os.path.join(d, "SHA256SUMS")).split("\n")[:-1])
            self.assertEqual(listed, ["0.eng.err", "0.hbp", "1.attempt1.eng.err", "1.attempt1.hbp", "1.eng.err",
                                      "1.hbp"])
            self.assertEqual(c.load_point(d, X1, require_sums=True).steps, (64,))
            write(os.path.join(d, "1.attempt1.eng.err"), "TWB_FAULT|reason=rounding_bound_hL_above_1/2|json=0\n"
                  "TWB_FAULT|reason=rounding_bound_hL_above_1/2|json=0\n")
            with self.assertRaises(c.StageBStop) as e:
                c.load_point(d, X1, require_sums=True)
        self.assertEqual(e.exception.reason, "sha256sums")

    def test_reader_stop_on_a_complete_stream_is_fatal(self):
        f = x1_files()
        f["1.hbp"] = with_trailer(read(os.path.join(AGG, "X1.1.empty.agg")), rc=0, rc_reader=3, steps="64,128")
        with TempDir() as d:
            point_dir(d, f)
            with self.assertRaises(c.StageBStop) as e:
                c.load_point(d, X1)
        self.assertEqual(e.exception.reason, "reader_stop")

    def test_other_engine_exit_is_fatal(self):
        f = x1_files()
        f["1.hbp"] = with_trailer(read(os.path.join(AGG, "X1.1.empty.agg")), rc=2, rc_reader=3, steps="64,128")
        with TempDir() as d:
            point_dir(d, f)
            with self.assertRaises(c.StageBStop):
                c.load_point(d, X1)

    def test_trailer_required(self):
        f = x1_files()
        f["1.hbp"] = read(os.path.join(AGG, "X1.1.agg")) + "rc=0 steps=64,128\n"
        with TempDir() as d:
            point_dir(d, f)
            with self.assertRaises(c.StageBStop) as e:
                c.load_point(d, X1)
            self.assertEqual(e.exception.reason, "call_file_trailer")
            self.assertEqual(c.load_point(d, X1, require_reader_rc=False).steps, (64, 128))
            write(os.path.join(d, "1.hbp"), read(os.path.join(AGG, "X1.1.agg")) + "rc=0 rc_reader=0\n")
            with self.assertRaises(c.StageBStop) as e:
                c.load_point(d, X1)
            self.assertEqual(e.exception.reason, "call_file_trailer")  # no steps
            write(os.path.join(d, "1.hbp"), read(os.path.join(AGG, "X1.1.agg")))
            with self.assertRaises(c.StageBStop):
                c.load_point(d, X1, require_reader_rc=False)


class AttemptSteps(unittest.TestCase):
    """The trailer files the steps of each try; rule STOP fixes them: attempt k ran the first R - k + 1 records, the
    last try of a lost call ran one, and a block's trailer names the block's own steps."""

    def test_attempt_ran_the_wrong_records(self):
        f = x1_files("X1.1.steps64.agg")
        f["1.attempt1.hbp"] = engine_stop("64")
        self.assertEqual(stop_reason(f), "stop_attempt_steps")

    def test_last_try_of_a_lost_call(self):
        f = x1_files()
        f["1.hbp"] = engine_stop("64,128")
        f["1.attempt1.hbp"] = engine_stop()
        self.assertEqual(stop_reason(f), "stop_attempt_steps")
        f["1.hbp"] = engine_stop("128")
        self.assertEqual(stop_reason(f), "stop_attempt_steps")

    def test_block_trailer_names_its_steps(self):
        f = x1_files("X1.1.steps64.agg")
        f["1.attempt1.hbp"] = engine_stop()
        f["1.hbp"] = with_trailer(read(os.path.join(AGG, "X1.1.steps64.agg")), steps="64,128")
        self.assertEqual(stop_reason(f), "stop_trailer_steps")

    def test_bad_steps_text(self):
        f = x1_files()
        f["1.hbp"] = with_trailer(read(os.path.join(AGG, "X1.1.agg")), steps="064,128")
        self.assertEqual(stop_reason(f), "call_file_trailer")


def tside_block(name):
    """The real stage A block of a Tside fixture (count 64 at the excluded point N=27, delta=1/4) as the fields
    check_side_sums reads: call 0, its steps, variants, AGG_ATOMS, AGG_SUM rows and y_zero."""
    b = c.CallBlock()
    b.point, b.call = name, 0
    for ln in read(os.path.join(AGG, name + ".agg")).split("\n")[:-1]:
        kind = ln.split("|", 1)[0]
        if kind in ("AGG_TWB_HEAD", "AGG_NL"):
            continue
        d = fields_dict(parse_row(ln)[1])
        if kind == "AGG_CALL":
            b.call_row = d
            b.steps = tuple(int(x) for x in d["steps"].split(","))
            b.variants = tuple(d["variants"].split(","))
        elif kind == "AGG_ATOMS":
            b.atoms = {k: int(d[k]) for k in ("M", "nl_klein", "nl_exch", "lk_klein", "lk_exch")}
        elif kind == "AGG_SUM":
            b.sums[(int(d["step"]), d["variant"], d["set"])] = {k: int(d[k]) for k in c.AGG_KEYS["AGG_SUM"][5:]}
    return b


class SideSums(unittest.TestCase):
    """Ensemble review M4: a side file must agree with its block's AGG_SUM and AGG_ATOMS (real stage A output)."""

    def test_real_side_files_agree(self):
        for name in ("Tside.0", "Tside0.0"):
            b = tside_block(name)
            self.assertTrue(c.check_side_sums(c.SideFile(os.path.join(AGG, name + ".side")), b))
            flags, sums = c.side_sums(c.SideFile(os.path.join(AGG, name + ".side")), b.call_row["y_zero"] == "1")
            self.assertEqual(sums[(64, "LOCK", "atom")]["m"], b.atoms["lk_exch" if name == "Tside.0" else "lk_klein"])

    def _planted(self, edit_side=None, edit_block=None):
        b = tside_block("Tside.0")
        with TempDir() as d:
            p = os.path.join(d, "Tside.0.side")
            shutil.copy(os.path.join(AGG, "Tside.0.side"), p)
            if edit_side:
                with open(p, "r+b") as f:
                    data = bytearray(f.read())
                    edit_side(data)
                    f.seek(0)
                    f.write(bytes(data))
            if edit_block:
                edit_block(b)
            try:
                c.check_side_sums(c.SideFile(p), b)
            except c.StageBStop as e:
                return e.reason, e.detail
        return None, None

    def test_planted_faults(self):
        rec = 8 + 16 * 7 * 2

        def br_plus_one(data):  # sample 5, VNC at step 64: its br
            off = 64 + rec * 5 + 8
            data[off] = (data[off] + 1) % 256

        def bound_plus_one(data):  # sample 9, MODE0 at step 128: its b_br
            off = 64 + rec * 9 + 8 + 16 * 13 + 8
            data[off] = (data[off] + 1) % 256

        def flag_moved(data):  # an LOCK exchange-atom flag on a sample that is not one
            off = 64 + rec * 40
            data[off] ^= 8

        for edit, part in ((br_plus_one, "VNC set=all: side br="), (bound_plus_one, "MODE0 set=all: side bbr="),
                           (flag_moved, "atom flags")):
            reason, detail = self._planted(edit_side=edit)
            self.assertEqual(reason, "side_sums")
            self.assertIn(part, detail)

        def sum_edited(b):
            b.sums[(128, "V1", "atom")]["bbr2"] += 1

        self.assertEqual(self._planted(edit_block=sum_edited)[0], "side_sums")

        def call_moved(b):
            b.call = 1

        self.assertEqual(self._planted(edit_block=call_moved), ("side_sums", "Tside.0 call 1: side start 0 count 64"))

    def test_open_side_checks_the_block(self):
        b = tside_block("Tside.0")
        t = read(os.path.join(AGG, "Tside.0.agg"))
        ln = [x for x in t.split("\n") if x.startswith("AGG_SIDE|")][0]
        sd = fields_dict(parse_row(ln)[1])
        row = {"path": sd["path"], "sha256": sd["sha256"], "bytes": int(sd["bytes"]), "indices": 64,
               "variants": sd["variants"], "steps": sd["steps"], "dir": AGG, "block": b}
        self.assertEqual(c.open_side(row).count, 64)
        self.assertEqual(row["sums_checked"], sd["sha256"])
        b.sums[(64, "VNC", "all")]["br"] += 1
        del row["sums_checked"]
        with self.assertRaises(c.StageBStop) as e:
            c.open_side(row)
        self.assertEqual(e.exception.reason, "side_sums")


class RealSideFiles(unittest.TestCase):
    """M4 on the real side files of X1 and X0 (4096 samples, 7 variants, records 64 and 128), beside their blocks: from
    tests/data/excl, or from STRIPES_EXCL_DIR when it is set (a folder check/excl_unpack.py wrote)."""

    def test_the_folder_matches_its_sums(self):
        lines = read(os.path.join(EXCL, "SHA256SUMS")).split("\n")[:-1]
        listed = dict(reversed(ln.split("  ", 1)) for ln in lines)
        self.assertEqual(len(listed), len(lines))
        present = sorted(os.listdir(EXCL))
        self.assertEqual([nm for nm in present if nm != "SHA256SUMS" and nm not in listed], [])
        for nm in present:
            if nm != "SHA256SUMS":
                with open(os.path.join(EXCL, nm), "rb") as f:
                    self.assertEqual(sha256_hex(f.read()), listed[nm], nm)
        # what is listed and not here: the four dumps (here as xz) and X1s4.0.txt (sha256 only)
        self.assertEqual(sorted(nm for nm in listed if nm not in present),
                         ["X0.0.txt", "X0.1.txt", "X1.0.txt", "X1.1.txt", "X1s4.0.txt"])
        self.assertEqual([nm for nm in ("X1.0", "X1.1", "X0.0", "X0.1") if nm + ".txt.xz" not in present], [])
        for nm in ("X1.0", "X1.1", "X0.0", "X0.1"):  # the blocks are the agg fixtures, byte for byte
            self.assertEqual(read(os.path.join(EXCL, nm + ".agg")), read(os.path.join(AGG, nm + ".agg")), nm)

    def test_real_side_files_agree(self):
        excl = os.environ.get("STRIPES_EXCL_DIR") or EXCL
        for spec in (X1, X0):
            files = {"%d.hbp" % i: with_trailer(read(os.path.join(excl, "%s.%d.agg" % (spec.id, i)))) for i in (0, 1)}
            with TempDir() as d, TempDir() as sd:
                point_dir(d, files)
                for i in (0, 1):  # the side files beside the blocks, under the names the AGG_SIDE rows give
                    shutil.copy(os.path.join(excl, "%s.%d.side" % (spec.id, i)), sd)
                pt = c.load_point(d, spec, side_dir=sd)
                self.assertEqual(pt.verify_sides(), 2)
                b = pt.calls[1]
                b.sums[(128, "RN", "atom")]["br2"] += 1
                row = dict(b.side)
                del row["sums_checked"]
                with self.assertRaises(c.StageBStop) as e:
                    c.open_side(row)
                self.assertEqual(e.exception.reason, "side_sums")


class PlantedFaults(unittest.TestCase):
    """Edits to a block: stage B refuses each one."""

    def _refuse(self, text):
        f = x1_files()
        f["0.hbp"] = with_trailer(text)
        with TempDir() as d:
            point_dir(d, f)
            with self.assertRaises(c.StageBStop) as e:
                c.load_point(d, X1)
        return e.exception.reason

    def _vr_line(self, text, step="64", v="VNC"):
        for ln in text.split("\n"):
            if ln.startswith("AGG_VR|") and "|step=%s|variant=%s|" % (step, v) in ln:
                return ln
        raise AssertionError("no row")

    def test_two_sector_counts_swapped(self):
        t = read(os.path.join(AGG, "X1.0.agg"))
        ln = self._vr_line(t)
        sec = [p for p in ln.split("|") if p.startswith("sec=")][0]
        v = sec[4:].split(":")
        v[0], v[1] = v[1], v[0]
        t2 = t.replace(ln, ln.replace(sec, "sec=" + ":".join(v)))
        self.assertEqual(self._refuse(t2), "agg_sha256")

    def test_edited_count_with_forged_hash(self):
        t = read(os.path.join(AGG, "X1.0.agg"))
        ln = self._vr_line(t)
        t2 = rehash(t.replace(ln, ln.replace("|br_pos=2054|br_neg=2041|", "|br_pos=2055|br_neg=2041|")))
        self.assertEqual(self._refuse(t2), "aggregate_identity")

    def test_altered_square_sum_with_forged_hash(self):
        t = read(os.path.join(AGG, "X1.0.agg"))
        ln = [x for x in t.split("\n") if x.startswith("AGG_SUM|") and "|step=64|variant=VNC|set=all|" in x][0]
        br2 = [p for p in ln.split("|") if p.startswith("br2=")][0]
        t2 = rehash(t.replace(ln, ln.replace(br2, "br2=%d" % (int(br2[4:]) + 1))))
        self.assertEqual(self._refuse(t2), "aggregate_identity")

    def test_wrong_engine_version_with_forged_hash(self):
        t = read(os.path.join(AGG, "X1.0.agg"))
        t2 = rehash(t.replace("|engine=twens|version=0.4.0|", "|engine=twens|version=0.3.0|", 1))
        self.assertEqual(self._refuse(t2), "head_version")

    def test_wrong_binary_with_forged_hash(self):
        t = read(os.path.join(AGG, "X1.0.agg"))
        t2 = rehash(t.replace(c.TWENS_BINARY_SHA256, "75530df9" + c.TWENS_BINARY_SHA256[8:], 1))
        self.assertEqual(self._refuse(t2), "head_binary_sha256")

    def test_truncated_block(self):
        t = read(os.path.join(AGG, "X1.0.agg"))
        lines = t.split("\n")[:-1]
        self.assertEqual(self._refuse("\n".join(lines[:-1]) + "\n"), "block_end")

    def test_row_deleted_with_forged_hash(self):
        t = read(os.path.join(AGG, "X1.0.agg"))
        ln = [x for x in t.split("\n") if x.startswith("AGG_LOCK|")][0]
        t2 = t.replace(ln + "\n", "")
        t2 = t2.replace("agg_lines=219", "agg_lines=218")
        self.assertEqual(self._refuse(rehash(t2)), "block_rows")

    def test_first_moment_edit_needs_the_receipt(self):
        # Sum br has no redundant identity in the block: a forged AGG_END passes the block checks, and only the
        # point's SHA256SUMS receipt (written when the call files were made) refuses it.
        t = read(os.path.join(AGG, "X1.0.agg"))
        ln = [x for x in t.split("\n") if x.startswith("AGG_SUM|") and "|step=64|variant=VNC|set=all|" in x][0]
        br = [p for p in ln.split("|") if p.startswith("br=")][0]
        forged = rehash(t.replace(ln, ln.replace("|" + br + "|", "|br=%d|" % (int(br[3:]) + 1))))
        with TempDir() as d:
            point_dir(d, x1_files())
            c.write_sha256sums(d)
            write(os.path.join(d, "0.hbp"), with_trailer(forged))
            self.assertEqual(c.load_point(d, X1).steps, (64, 128))
            with self.assertRaises(c.StageBStop) as e:
                c.load_point(d, X1, require_sums=True)
        self.assertEqual(e.exception.reason, "sha256sums")

    def test_noncanonical_integer_with_forged_hash(self):
        t = read(os.path.join(AGG, "X1.0.agg"))
        t2 = rehash(t.replace("|M=4096|nl_klein=2|", "|M=04096|nl_klein=2|", 1))
        self.assertEqual(self._refuse(t2), "block_rows")


class Side(unittest.TestCase):
    def _side_row(self, name):
        t = read(os.path.join(AGG, name))
        ln = [x for x in t.split("\n") if x.startswith("AGG_SIDE|")][0]
        d = fields_dict(parse_row(ln, "AGG_SIDE", c.AGG_KEYS["AGG_SIDE"])[1])
        return {"path": d["path"], "sha256": d["sha256"], "bytes": int(d["bytes"]), "indices": int(d["indices"]),
                "variants": d["variants"], "steps": d["steps"], "dir": AGG}

    def test_side_header_and_samples(self):
        sf = c.open_side(self._side_row("Tside.0.agg"))
        self.assertEqual(sf.variants, c.VARIANTS)
        self.assertEqual(sf.steps, (64, 128))
        self.assertEqual((sf.start, sf.count), (0, 64))
        flags, vals = sf.sample(0)
        self.assertEqual(len(vals), 14)

    def test_side_sums_match_the_block(self):
        sf = c.open_side(self._side_row("Tside.0.agg"))
        t = read(os.path.join(AGG, "Tside.0.agg"))
        for ln in t.split("\n"):
            if ln.startswith("AGG_SUM|") and "|set=all|" in ln:
                d = fields_dict(parse_row(ln, "AGG_SUM", c.AGG_KEYS["AGG_SUM"])[1])
                key = (d["variant"], int(d["step"]))
                s = sum(sf.sample(i)[1][key][0] for i in range(sf.count))
                b = sum(sf.sample(i)[1][key][1] for i in range(sf.count))
                self.assertEqual((s, b), (int(d["br"]), int(d["bbr"])))

    def test_paired_sums(self):
        a = c.open_side(self._side_row("Tside.0.agg"))
        b = c.open_side(self._side_row("Tside0.0.agg"))
        acc = c.paired_side_sums(a, b)
        k = acc[("VNC", 64)]
        da = [a.sample(i)[1][("VNC", 64)] for i in range(64)]
        db = [b.sample(i)[1][("VNC", 64)] for i in range(64)]
        self.assertEqual(k["S"], sum(x[0] - y[0] for x, y in zip(da, db, strict=True)))
        self.assertEqual(k["RB"], sum(x[1] + y[1] for x, y in zip(da, db, strict=True)))
        self.assertEqual(k["m"], 64)

    def test_side_tamper(self):
        with TempDir() as d:
            row = self._side_row("Tside.0.agg")
            shutil.copy(os.path.join(AGG, "Tside.0.side"), os.path.join(d, "Tside.0.side"))
            with open(os.path.join(d, "Tside.0.side"), "r+b") as f:
                f.seek(100)
                x = f.read(1)
                f.seek(100)
                f.write(bytes([x[0] ^ 1]))
            row["dir"] = d
            row["path"] = os.path.join(d, "Tside.0.side")
            with self.assertRaises(c.StageBStop) as e:
                c.open_side(row)
        self.assertEqual(e.exception.reason, "side_file_sha256")


if __name__ == "__main__":
    unittest.main()
