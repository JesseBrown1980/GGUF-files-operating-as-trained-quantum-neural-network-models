"""Stage B common layer: the point tables, the stage A aggregate blocks (AGG-FORMAT.md), pooling per point under rules
SEED and STOP, the side files, the read rules READ3, SE, H8, B16, SIGNFLIP and EXPOSED, and the READ and VERDICT rows.

Every value is an int or a Fraction. Every ensemble and quantum module reads its data through this module."""

import hashlib
import math
import os
import re
import struct

from . import frozen as frozen_mod
from .exact import (
    ExactError,
    Rad,
    canon_int,
    div,
    fmt,
    fr,
    parse_rat,
    rat_text,
)
from .hbp import RowError, emit, fields_dict, file_sha256, parse_row, read_lines, sha256_hex

READER = "stripes-read-b"
READER_VERSION = "0.1.0"

TWENS_VERSION = "0.4.0"
TWENS_BINARY_SHA256 = "33e62fbe0837aeddc916a57d67848338cbc258aa1dfb85a01cfba53fb8a4e03f"
TWENS_SOURCE_SHA256 = (
    "main.rs:1d768fa9aba719d0439625f08ea2711cc0d28a5e751b25a81667b4b3d5fcacbb,"
    "sha256.rs:7447d1e84a95fe1ab84882938a0344119d017c347809e0f7e929c2e8c27d4621"
)
READER_A = "stripes-read-a"
READER_A_VERSION = "0.1.0"

VARIANTS = ("VNC", "V1", "V0", "RN", "FLIP", "LOCK", "MODE0")
MASK_ALL = "VNC,V1,V0,RN,FLIP,LOCK,MODE0,NL"
MASK_VNC = "VNC"
COUNT = 4096
DTDEN = 64
SEED_PREFIX = "stripes-ens-v1"
BLOCK_SIZES = (4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096)

# READ3 outcomes and the read-and-report mark.
MET = "MET"
MISS = "MISS"
NOT_RESOLVED = "NOT_RESOLVED"
NOT_MEASURED = "NOT_MEASURED"
REPORT = "REPORT"
# row outcomes
NOT_MET = "NOT_MET"
NONE = "NONE"
# test outcomes of H8, B16 and SIGNFLIP
FLAG = "flag"
UNFLAGGED = "unflagged"
UNRESOLVED = "unresolved"


class StageBStop(Exception):
    """A fault that leaves stage B with nothing to decide: no READ file is written."""

    def __init__(self, reason, detail=""):
        Exception.__init__(self, "%s: %s" % (reason, detail))
        self.reason = reason
        self.detail = detail


# ---------------------------------------------------------------------------------------------------------------------
# Point tables (AGG-FORMAT.md section 9, RUN-PLAN steps 5 and 6), checked against the frozen STRIPES_POINT rows.


class DumpPoint:
    __slots__ = ("id", "N", "delta", "y", "vnc", "all", "steps", "side")

    def __init__(self, pid, n, delta, y, vnc, all_calls, steps, side):
        self.id = pid
        self.N = n
        self.delta = delta
        self.y = y
        self.vnc = vnc
        self.all = all_calls
        self.steps = tuple(steps)
        self.side = side

    @property
    def calls(self):
        return self.vnc // COUNT

    @property
    def seed_string(self):
        return "%s:N%d:d%s:y%s" % (SEED_PREFIX, self.N, self.delta, self.y)

    def mask(self, call):
        return MASK_ALL if call < self.all else MASK_VNC

    def s(self):
        """s = y sqrt(N), exact: every N used is a square."""
        return parse_rat(self.y) * square_root(self.N)


class RunPoint:
    __slots__ = ("id", "N", "delta", "y", "count", "steps", "batches")

    def __init__(self, rid, n, delta, y, count, steps, batches=64):
        self.id = rid
        self.N = n
        self.delta = delta
        self.y = y
        self.count = count
        self.steps = tuple(steps)
        self.batches = batches

    @property
    def seed_string(self):
        return "%s:N%d:d%s:y%s" % (SEED_PREFIX, self.N, self.delta, self.y)

    @property
    def per_batch(self):
        return self.count // self.batches


S4 = (64, 128, 192, 256)
S3 = (128, 192, 256)
S2 = (64, 128)

DUMP_POINTS = {
    p.id: p
    for p in (
        DumpPoint("P01", 1296, "1/2", "0", 4194304, 64, S4, False),
        DumpPoint("P02", 1296, "1/2", "1/576", 4194304, 64, S4, False),
        DumpPoint("P03", 1296, "1/2", "1/288", 4194304, 64, S4, False),
        DumpPoint("P04", 1296, "1/2", "1/144", 4194304, 64, S4, False),
        DumpPoint("P05", 1296, "1/2", "1/72", 1048576, 64, S4, False),
        DumpPoint("P06", 1296, "1/2", "1/36", 1048576, 64, S4, False),
        DumpPoint("P07", 729, "-1/4", "0", 1048576, 64, S3, False),
        DumpPoint("P08", 729, "-1/4", "1/54", 1048576, 64, S4, True),
        DumpPoint("P09", 121, "1/2", "0", 1048576, 64, S4, False),
        DumpPoint("P10", 121, "1/2", "1/11", 1048576, 64, S4, False),
        DumpPoint("P11", 1296, "1/2", "1/648", 4194304, 64, S4, False),
        DumpPoint("P12", 324, "1/2", "1/162", 4194304, 64, S4, False),
        DumpPoint("P13", 729, "-1/4", "-1/54", 262144, 64, S2, True),
        DumpPoint("P14", 729, "-1/4", "1/108", 1048576, 0, S2, False),
    )
}

RUN_POINTS = {
    r.id: r
    for r in (
        RunPoint("R1", 729, "-1/4", "1/27", 4194304, (32, 64, 128)),
        RunPoint("R2", 729, "-1/4", "1/54", 4194304, (32, 64, 128)),
        RunPoint("R3", 729, "-1/4", "1/108", 16777216, (32, 64, 128)),
        RunPoint("R4", 81, "-1/4", "1/18", 4194304, (32, 64)),
    )
}


def square_root(n):
    r = math.isqrt(n)
    if r * r != n:
        raise ExactError("N=%d is not a square" % n)
    return r


def t_of_step(step, dtden=DTDEN):
    return fr(step, dtden)


def step_of_t(t, dtden=DTDEN):
    s = fr(t) * dtden
    if s.denominator != 1:
        raise ExactError("t=%s is not a record time" % rat_text(t))
    return s.numerator


def check_tables(fz=None):
    """Every point of the tables equals its frozen STRIPES_POINT row (N, delta, y, steps, seed_string, vnc)."""
    fz = fz or frozen_mod.load()
    for table in (DUMP_POINTS, RUN_POINTS):
        for pid, p in table.items():
            row = fz.row("STRIPES_POINT", pid)
            want_engine = "dump" if table is DUMP_POINTS else "run"
            if row["engine"] != want_engine:
                raise StageBStop("table", "%s engine %s" % (pid, row["engine"]))
            if int(row["N"]) != p.N or row["delta"] != p.delta or row["y"] != p.y:
                raise StageBStop("table", pid + " N, delta or y")
            if tuple(int(x) for x in row["steps"].split(",")) != p.steps:
                raise StageBStop("table", pid + " steps")
            if row["seed_string"] != p.seed_string:
                raise StageBStop("table", pid + " seed_string")
            m = re.match(r"2\^([0-9]+)", row["vnc"])
            total = p.vnc if table is DUMP_POINTS else p.count
            if not m or (1 << int(m.group(1))) != total:
                raise StageBStop("table", pid + " vnc count")
    text = [ln for k, _, ln in fz.rows if k == "STRIPES_POINTS_COMMON"][0]
    for phrase in ("count=4096", "dtden=64", "threads=1", "calls_i<64_mask=VNC,V1,V0,RN,FLIP,LOCK,MODE0,NL",
                   "later_calls_mask=VNC", "64_batches_start=j*count/64", "threads=4_mask=VNC_memo=1"):
        if phrase not in text:
            raise StageBStop("table", "STRIPES_POINTS_COMMON lacks " + phrase)
    if "all_256_calls_VNC_only" not in fz.row("STRIPES_POINT", "P14")["vnc"]:
        raise StageBStop("table", "P14 VNC only")
    return True


def seed_u64(seed_string):
    """twens seed: the first 8 bytes of sha256(seed_string), big-endian."""
    return int.from_bytes(hashlib.sha256(seed_string.encode("ascii")).digest()[:8], "big")


def engine_h(n):
    """floor(2^40 / (2 sqrt N)) as twens computes it: isqrt(2^80 div 4N)."""
    return math.isqrt((1 << 80) // (4 * n))


# ---------------------------------------------------------------------------------------------------------------------
# Stage A blocks.

AGG_KEYS = {
    "AGG_HEAD": ("reader", "reader_version", "point", "call", "table", "stdin_bytes", "stdin_lines", "stdin_sha256"),
    "AGG_CALL": ("point", "call", "N", "delta", "u", "y", "y_zero", "seed", "seed_string", "start", "count", "dtden",
                 "h", "steps", "records", "mask", "variants", "nl", "ctrl", "nl_sha256"),
    "AGG_ATOMS": ("point", "call", "M", "nl_klein", "nl_exch", "lk_klein", "lk_exch"),
    "AGG_LAT": ("point", "call", "lock_atoms", "lat_edge", "lat"),
    "AGG_VR": ("point", "call", "step", "variant", "M", "atoms", "xatoms", "xatom_bi_nz", "mp", "na_bi0", "sec", "amb",
               "br_pos", "br_neg", "br_amb", "bi_pos", "bi_neg", "bi_amb", "at_br_pos", "at_br_neg", "at_br_amb",
               "at_bi_pos", "at_bi_neg", "at_bi_amb"),
    "AGG_SUM": ("point", "call", "step", "variant", "set", "m", "br", "bi", "br2", "bi2", "brbi", "bbr", "bbi", "bbr2",
                "bbi2"),
    "AGG_BLK": ("point", "call", "step", "variant", "n", "K", "s2", "s4", "w", "w2", "sw"),
    "AGG_CMP": ("point", "call", "step", "variant", "ref", "common", "br", "bi", "cert2", "mis", "cert2_big_both",
                "mis_big_both", "cert2_big_any", "mis_big_any"),
    "AGG_LOCK": ("point", "call", "step", "cert", "mis"),
    "AGG_SIDE": ("point", "call", "path", "bytes", "sha256", "indices", "variants", "steps"),
    "AGG_CHECK": ("point", "call", "samples", "starts", "lin", "rows", "fields", "result"),
    "AGG_END": ("point", "call", "agg_lines", "agg_sha256"),
}
TWB_HEAD_KEYS = ("engine", "version", "cli", "binary_sha256", "source_sha256", "N", "delta", "u", "y", "seed",
                 "seed_string", "start", "count", "samples", "dtden", "threads", "steps", "mask", "reserved", "guard",
                 "q", "sums", "rounding", "float_used")
TWB_HEAD_SUMS = "plain_at_2^40,q_sum_of_floor(v*v/2^40),products_exact_at_2^80"
TWB_HEAD_ROUNDING = "per-sample_bound_summed_in_TWB_ROUND_and_TWB_PAIR_ROUND"
TWB_NL_KEYS = ("N", "delta", "u", "y", "dtden", "step", "init", "kappa", "zr", "zi", "z2", "xw", "xnc", "f", "fcl",
               "br", "bi", "rb_zr", "rb_zi", "rb_z2", "rb_xw", "rb_xnc", "rb_f", "rb_fcl", "rb_br", "rb_bi", "eps",
               "reads", "at", "float_used")
TWB_NL_READS = ("trajectory_frame:A1=2abs(Z),C1=2N*abs(Z)^2/(N-1),f=fcl,D2=2abs(B);ensemble_frames:C1_NC=2N*xnc/(N-1),"
                "C1_W=2N*xw/(N-1),f_W=f=fcl-1/N")
STOP_KEYS = ("reader", "reader_version", "point", "call", "reason", "line", "detail", "stdin_bytes", "stdin_lines",
             "stdin_sha256")
INT_TEXT = {"point", "call", "table", "stdin_sha256", "reader", "reader_version", "variant", "set", "sec", "ref", "br",
            "bi", "lat", "path", "sha256", "variants", "steps", "result", "agg_sha256"}
_TRAILER = re.compile(r"rc=(0|[1-9][0-9]*)(?: rc_reader=(0|[1-9][0-9]*))?\Z")


def _ints(d, keys):
    return {k: canon_int(d[k]) for k in keys}


def _int_list(text, n, sep=":"):
    parts = text.split(sep)
    if len(parts) != n:
        raise RowError("list of %d expected: %s" % (n, text[:40]))
    return [canon_int(x) for x in parts]


class CallBlock:
    """One call's stage A block, parsed and checked against the grammar, its hash and the point table."""

    def __init__(self):
        self.vr = {}
        self.sums = {}
        self.blk = {}
        self.cmp = {}
        self.lock = {}
        self.nl_rows = {}
        self.side = None


class CallFile:
    """What a call file holds: a block, or a stage A STOP row, and the rc trailer."""

    __slots__ = ("path", "sha256", "point", "call", "block", "stop", "rc", "rc_reader")


def read_call_file(path, spec, call, require_reader_rc=True, side_dir=None):
    """Parse one per-call file: the stage A output followed by the trailer `rc=E rc_reader=R`."""
    cf = CallFile()
    cf.path = path
    cf.sha256 = file_sha256(path)
    cf.point = spec.id
    cf.call = call
    cf.block = None
    cf.stop = None
    lines = read_lines(path)
    if not lines:
        raise StageBStop("call_file_empty", "%s call %d" % (spec.id, call))
    m = _TRAILER.match(lines[-1])
    if not m:
        raise StageBStop("call_file_trailer", "%s call %d: %s" % (spec.id, call, lines[-1][:60]))
    cf.rc = int(m.group(1))
    cf.rc_reader = int(m.group(2)) if m.group(2) is not None else None
    if require_reader_rc and cf.rc_reader is None:
        raise StageBStop("call_file_trailer", "%s call %d: no rc_reader" % (spec.id, call))
    body = lines[:-1]
    if len(body) == 1 and body[0].startswith("STOP|"):
        cf.stop = _parse_stop(body[0], spec, call)
        engine_stop = cf.rc == 4 and cf.stop["reason"] == "empty_stream" and cf.rc_reader in (None, 3)
        if not engine_stop:
            raise StageBStop("reader_stop", "%s call %d: rc=%d reason=%s" % (spec.id, call, cf.rc, cf.stop["reason"]))
        return cf
    if cf.rc != 0 or cf.rc_reader not in (None, 0):
        raise StageBStop("call_rc", "%s call %d rc=%d rc_reader=%s" % (spec.id, call, cf.rc, cf.rc_reader))
    cf.block = parse_block(body, spec, call, side_dir=side_dir)
    return cf


def _parse_stop(line, spec, call):
    try:
        _, f = parse_row(line, "STOP", STOP_KEYS)
    except RowError:
        _, f = parse_row(line, "STOP", ("reader", "reader_version", "reason", "detail"))
    d = fields_dict(f)
    if d["reader"] != READER_A or d["reader_version"] != READER_A_VERSION:
        raise StageBStop("reader_stop", "STOP row from another reader")
    if "point" in d and (d["point"] != spec.id or d["call"] != str(call)):
        raise StageBStop("reader_stop", "STOP row of another call: %s %s" % (d["point"], d["call"]))
    return d


def parse_block(lines, spec, call, side_dir=None):
    """A stage A block (AGG-FORMAT.md sections 3 and 5), with every check stage B owes it."""
    if not lines or not lines[-1].startswith("AGG_END|"):
        raise StageBStop("block_end", "%s call %d" % (spec.id, call))
    end = fields_dict(parse_row(lines[-1], "AGG_END", AGG_KEYS["AGG_END"])[1])
    body = lines[:-1]
    h = sha256_hex("".join(ln + "\n" for ln in body).encode("ascii"))
    if canon_int(end["agg_lines"]) != len(body) or end["agg_sha256"] != h:
        raise StageBStop("agg_sha256", "%s call %d" % (spec.id, call))
    pc = (spec.id, str(call))
    b = CallBlock()
    b.agg_sha256 = h
    b.point = spec.id
    b.call = call
    pos = [0]

    def take(kind):
        if pos[0] >= len(body):
            raise StageBStop("block_rows", "%s call %d: missing %s" % (spec.id, call, kind))
        ln = body[pos[0]]
        pos[0] += 1
        if kind in ("AGG_TWB_HEAD", "AGG_NL"):
            if not ln.startswith(kind + "|"):
                raise StageBStop("block_rows", "%s call %d: %s expected" % (spec.id, call, kind))
            return ln[len(kind) + 1 :]
        try:
            _, f = parse_row(ln, kind, AGG_KEYS[kind])
        except RowError as e:
            raise StageBStop("block_rows", "%s call %d: %s" % (spec.id, call, e)) from e
        d = fields_dict(f)
        if (d["point"], d["call"]) != pc:
            raise StageBStop("block_pc", "%s call %d: row of %s %s" % (spec.id, call, d["point"], d["call"]))
        return d

    try:
        head = take("AGG_HEAD")
        if (head["reader"], head["reader_version"], head["table"]) != (READER_A, READER_A_VERSION, "checked"):
            raise StageBStop("block_head", "%s call %d" % (spec.id, call))
        b.stdin = _ints(head, ("stdin_bytes", "stdin_lines"))
        b.stdin["sha256"] = head["stdin_sha256"]
        b.twb_head = take("AGG_TWB_HEAD")
        th = fields_dict(parse_row(b.twb_head, "TWB_HEAD", TWB_HEAD_KEYS)[1])
        c = take("AGG_CALL")
        _check_call(spec, call, th, c)
        b.steps = tuple(canon_int(x) for x in c["steps"].split(","))
        b.variants = tuple(c["variants"].split(","))
        b.nl = c["nl"] == "1"
        b.call_row = c
        a = take("AGG_ATOMS")
        b.atoms = _ints(a, ("M", "nl_klein", "nl_exch", "lk_klein", "lk_exch"))
        if b.atoms["M"] != COUNT:
            raise StageBStop("block_values", "%s call %d: M" % (spec.id, call))
        lat = take("AGG_LAT")
        b.lat = _ints(lat, ("lock_atoms", "lat_edge"))
        b.lat["lat"] = _int_list(lat["lat"], 16)
        if b.lat["lock_atoms"] + b.lat["lat_edge"] + sum(b.lat["lat"]) != COUNT:
            raise StageBStop("block_values", "%s call %d: AGG_LAT identity" % (spec.id, call))
        for step in b.steps:
            for v in b.variants:
                _take_variant(b, take, spec, call, step, v)
            if b.nl:
                nl = take("AGG_NL")
                nd = fields_dict(parse_row(nl, "TWB_NL", TWB_NL_KEYS)[1])
                _check_nl(spec, call, step, nd)
                b.nl_rows[step] = nl
        if b.nl:
            nh = sha256_hex("".join(b.nl_rows[s] + "\n" for s in b.steps).encode("ascii"))
            if nh != c["nl_sha256"]:
                raise StageBStop("nl_sha256", "%s call %d: AGG_CALL nl_sha256 differs from its AGG_NL rows" % (
                    spec.id, call))
        if spec.side and call < spec.all:
            sd = take("AGG_SIDE")
            b.side = _check_side_row(spec, call, sd, b, side_dir)
        elif pos[0] < len(body) and body[pos[0]].startswith("AGG_SIDE|"):
            b.side = _check_side_row(spec, call, take("AGG_SIDE"), b, side_dir)
        ck = take("AGG_CHECK")
        if ck["result"] != "all_equal" or canon_int(ck["samples"]) != COUNT:
            raise StageBStop("block_values", "%s call %d: AGG_CHECK" % (spec.id, call))
        if pos[0] != len(body):
            raise StageBStop("block_rows", "%s call %d: rows after AGG_CHECK" % (spec.id, call))
    except (RowError, ExactError) as e:
        raise StageBStop("block_rows", "%s call %d: %s" % (spec.id, call, e)) from e
    return b


def _check_call(spec, call, th, c):
    want = {
        "N": str(spec.N), "delta": spec.delta, "u": "1", "y": spec.y, "seed_string": spec.seed_string,
        "start": str(COUNT * call), "count": str(COUNT), "dtden": str(DTDEN), "mask": spec.mask(call),
    }
    for k, v in want.items():
        if c[k] != v or (k in th and th[k] != v):
            raise StageBStop("table_mismatch", "%s call %d: %s=%s" % (spec.id, call, k, c[k]))
    if not (0 <= call < spec.calls):
        raise StageBStop("table_call_out_of_range", "%s call %d" % (spec.id, call))
    head_want = {
        "engine": "twens", "version": TWENS_VERSION, "cli": "dump", "binary_sha256": TWENS_BINARY_SHA256,
        "source_sha256": TWENS_SOURCE_SHA256, "samples": str(COUNT), "threads": "1", "reserved": "0",
        "guard": "active", "q": "40", "sums": TWB_HEAD_SUMS, "rounding": TWB_HEAD_ROUNDING, "float_used": "0",
    }
    for k, v in head_want.items():
        if th[k] != v:
            raise StageBStop("head_" + k, "%s call %d: %s" % (spec.id, call, th[k][:70]))
    seed = seed_u64(spec.seed_string)
    if c["seed"] != str(seed) or th["seed"] != str(seed):
        raise StageBStop("table_mismatch", "%s call %d: seed" % (spec.id, call))
    steps = tuple(canon_int(x) for x in c["steps"].split(","))
    if not steps or spec.steps[: len(steps)] != steps or th["steps"] != c["steps"]:
        raise StageBStop("table_mismatch", "%s call %d: steps %s" % (spec.id, call, c["steps"]))
    if canon_int(c["records"]) != len(steps):
        raise StageBStop("table_mismatch", "%s call %d: records" % (spec.id, call))
    if c["ctrl"] != ";".join(["0:0:0"] * len(steps)):
        raise StageBStop("table_mismatch", "%s call %d: ctrl" % (spec.id, call))
    y_zero = "1" if parse_rat(spec.y) == 0 else "0"
    if c["y_zero"] != y_zero or canon_int(c["h"]) != engine_h(spec.N):
        raise StageBStop("table_mismatch", "%s call %d: y_zero or h" % (spec.id, call))
    nl = spec.mask(call).endswith(",NL")
    variants = ",".join(VARIANTS) if nl else "VNC"
    if c["variants"] != variants or c["nl"] != ("1" if nl else "0"):
        raise StageBStop("table_mismatch", "%s call %d: variants" % (spec.id, call))
    if (c["nl_sha256"] == "none") == nl:
        raise StageBStop("table_mismatch", "%s call %d: nl_sha256" % (spec.id, call))


def _take_variant(b, take, spec, call, step, v):
    vr = take("AGG_VR")
    if (vr["step"], vr["variant"]) != (str(step), v):
        raise StageBStop("block_rows", "%s call %d: AGG_VR order" % (spec.id, call))
    keys = AGG_KEYS["AGG_VR"][4:]
    d = {k: canon_int(vr[k]) for k in keys if k != "sec"}
    d["sec"] = _int_list(vr["sec"], 16)
    mp = d["mp"]
    ok = (
        d["M"] == COUNT and mp == d["M"] - d["atoms"] and sum(d["sec"]) + d["amb"] == mp
        and d["br_pos"] + d["br_neg"] + d["br_amb"] == mp and d["bi_pos"] + d["bi_neg"] + d["bi_amb"] == mp
        and d["at_br_pos"] + d["at_br_neg"] + d["at_br_amb"] == d["atoms"]
        and d["at_bi_pos"] + d["at_bi_neg"] + d["at_bi_amb"] == d["atoms"]
        and d["xatom_bi_nz"] <= d["xatoms"] and min(v for k, v in d.items() if k != "sec") >= 0
        and min(d["sec"]) >= 0
    )
    if not ok:
        raise StageBStop("aggregate_identity", "%s call %d step %d %s" % (spec.id, call, step, v))
    b.vr[(step, v)] = d
    for which in ("all", "atom"):
        s = take("AGG_SUM")
        if (s["step"], s["variant"], s["set"]) != (str(step), v, which):
            raise StageBStop("block_rows", "%s call %d: AGG_SUM order" % (spec.id, call))
        b.sums[(step, v, which)] = _ints(s, AGG_KEYS["AGG_SUM"][5:])
    if b.sums[(step, v, "all")]["m"] != COUNT or b.sums[(step, v, "atom")]["m"] != d["atoms"]:
        raise StageBStop("aggregate_identity", "%s call %d: AGG_SUM m" % (spec.id, call))
    sa = b.sums[(step, v, "all")]
    for n in BLOCK_SIZES:
        k = take("AGG_BLK")
        if (k["step"], k["variant"], k["n"]) != (str(step), v, str(n)):
            raise StageBStop("block_rows", "%s call %d: AGG_BLK order" % (spec.id, call))
        bd = _ints(k, ("K", "s2", "s4", "w", "w2", "sw"))
        if bd["K"] != COUNT // n or bd["w"] != sa["br2"] + sa["bi2"]:
            raise StageBStop("aggregate_identity", "%s call %d: AGG_BLK n=%d" % (spec.id, call, n))
        b.blk[(step, v, n)] = bd
    if v != "VNC":
        cm = take("AGG_CMP")
        if (cm["step"], cm["variant"], cm["ref"]) != (str(step), v, "VNC"):
            raise StageBStop("block_rows", "%s call %d: AGG_CMP order" % (spec.id, call))
        cd = _ints(cm, ("common", "cert2", "mis", "cert2_big_both", "mis_big_both", "cert2_big_any", "mis_big_any"))
        cd["br"] = _int_list(cm["br"], 9)
        cd["bi"] = _int_list(cm["bi"], 9)
        nested = (cd["mis_big_both"] <= cd["mis_big_any"] <= cd["mis"] <= cd["cert2"] <= cd["common"]
                  and cd["mis_big_both"] <= cd["cert2_big_both"] <= cd["cert2_big_any"] <= cd["cert2"]
                  and cd["mis_big_any"] <= cd["cert2_big_any"])
        if sum(cd["br"]) != cd["common"] or sum(cd["bi"]) != cd["common"] or not nested:
            raise StageBStop("aggregate_identity", "%s call %d: AGG_CMP" % (spec.id, call))
        b.cmp[(step, v)] = cd
    if v == "LOCK":
        lk = take("AGG_LOCK")
        if lk["step"] != str(step):
            raise StageBStop("block_rows", "%s call %d: AGG_LOCK order" % (spec.id, call))
        b.lock[step] = _ints(lk, ("cert", "mis"))


def _check_nl(spec, call, step, nd):
    want = {"N": str(spec.N), "delta": spec.delta, "u": "1", "y": spec.y, "dtden": str(DTDEN), "step": str(step),
            "init": "c0=sqrt(N),c+-=0", "kappa": "1", "reads": TWB_NL_READS, "at": "2^40", "float_used": "0"}
    for k, v in want.items():
        if nd[k] != v:
            raise StageBStop("nl_row", "%s call %d step %d: %s" % (spec.id, call, step, k))
    for k in TWB_NL_KEYS:
        if k not in want:
            canon_int(nd[k])


def _check_side_row(spec, call, sd, b, side_dir):
    d = {"path": sd["path"], "sha256": sd["sha256"], "bytes": canon_int(sd["bytes"]),
         "indices": canon_int(sd["indices"]), "variants": sd["variants"], "steps": sd["steps"],
         "dir": side_dir}
    if d["indices"] != COUNT or d["variants"] != ",".join(b.variants):
        raise StageBStop("side_row", "%s call %d" % (spec.id, call))
    want_steps = ",".join(str(s) for s in b.steps if s in (64, 128)) or "none"
    if d["steps"] != want_steps:
        raise StageBStop("side_row", "%s call %d: steps" % (spec.id, call))
    return d


def open_side(side_row):
    """The side file of an AGG_SIDE row, found beside the call files (or at its recorded path), checked against the
    row's size and sha256 before it is read."""
    cands = []
    if side_row.get("dir"):
        cands.append(os.path.join(side_row["dir"], os.path.basename(side_row["path"])))
    cands.append(side_row["path"])
    for p in cands:
        if os.path.exists(p):
            if os.path.getsize(p) != side_row["bytes"] or file_sha256(p) != side_row["sha256"]:
                raise StageBStop("side_file_sha256", p)
            return SideFile(p)
    raise StageBStop("side_file_missing", side_row["path"])


# ---------------------------------------------------------------------------------------------------------------------
# Pooling per point (rules SEED and STOP).


class Point:
    """The calls of one dump point, checked for completeness and pooled record by record.

    `scope` selects calls: "all" every read call, "ctrl" the calls below the point's `all` (the first 2^18 indices,
    where the controls and NL were sampled)."""

    def __init__(self, spec):
        self.spec = spec
        self.files = {}
        self.calls = {}
        self.lost = []
        self.attempts = []
        self.steps = ()
        self.not_measured = ()

    # --- selection
    def call_list(self, scope="all", variant="VNC"):
        out = []
        for i in sorted(self.calls):
            if scope == "ctrl" and i >= self.spec.all:
                continue
            if variant not in self.calls[i].variants:
                continue
            out.append(self.calls[i])
        return out

    def measured(self, step):
        return step in self.steps

    def M(self, scope="all", variant="VNC"):
        return COUNT * len(self.call_list(scope, variant))

    def lost_indices(self, scope="all"):
        return [(COUNT * i, COUNT * (i + 1)) for i, _ in self.lost if scope == "all" or i < self.spec.all]

    def _need(self, step):
        if step not in self.steps:
            raise StageBStop("not_measured_record", "%s step %d" % (self.spec.id, step))

    # --- pooled sums
    def vr(self, step, variant, scope="all"):
        self._need(step)
        acc = None
        for b in self.call_list(scope, variant):
            d = b.vr[(step, variant)]
            if acc is None:
                acc = {k: (list(v) if k == "sec" else v) for k, v in d.items()}
            else:
                for k, v in d.items():
                    if k == "sec":
                        acc["sec"] = [x + y for x, y in zip(acc["sec"], v, strict=True)]
                    else:
                        acc[k] += v
        return acc

    def sums(self, step, variant, which="all", scope="all"):
        """Pooled AGG_SUM: which is "all", "atom" or "nonatom" (all minus atom)."""
        self._need(step)
        if which == "nonatom":
            a = self.sums(step, variant, "all", scope)
            t = self.sums(step, variant, "atom", scope)
            return {k: a[k] - t[k] for k in a}
        acc = None
        for b in self.call_list(scope, variant):
            d = b.sums[(step, variant, which)]
            acc = dict(d) if acc is None else {k: acc[k] + d[k] for k in acc}
        return acc

    def per_call_sums(self, step, variant, which="all", scope="all"):
        self._need(step)
        out = []
        for b in self.call_list(scope, variant):
            if which == "nonatom":
                a, t = b.sums[(step, variant, "all")], b.sums[(step, variant, "atom")]
                out.append({k: a[k] - t[k] for k in a})
            else:
                out.append(dict(b.sums[(step, variant, which)]))
        return out

    def blk(self, step, variant, n, scope="all"):
        self._need(step)
        acc = None
        for b in self.call_list(scope, variant):
            d = b.blk[(step, variant, n)]
            acc = dict(d) if acc is None else {k: acc[k] + d[k] for k in acc}
        return acc

    def cmp(self, step, variant):
        self._need(step)
        acc = None
        for b in self.call_list("ctrl", variant):
            d = b.cmp[(step, variant)]
            if acc is None:
                acc = {k: (list(v) if isinstance(v, list) else v) for k, v in d.items()}
            else:
                for k, v in d.items():
                    acc[k] = [x + y for x, y in zip(acc[k], v, strict=True)] if isinstance(v, list) else acc[k] + v
        return acc

    def lock(self, step):
        self._need(step)
        cert = mis = 0
        for b in self.call_list("ctrl", "LOCK"):
            cert += b.lock[step]["cert"]
            mis += b.lock[step]["mis"]
        return {"cert": cert, "mis": mis}

    def atoms(self, scope="all"):
        acc = {"M": 0, "nl_klein": 0, "nl_exch": 0, "lk_klein": 0, "lk_exch": 0}
        for b in self.call_list(scope):
            for k in acc:
                acc[k] += b.atoms[k]
        return acc

    def lat(self, scope="all"):
        acc = {"lock_atoms": 0, "lat_edge": 0, "lat": [0] * 16}
        for b in self.call_list(scope):
            acc["lock_atoms"] += b.lat["lock_atoms"]
            acc["lat_edge"] += b.lat["lat_edge"]
            acc["lat"] = [x + y for x, y in zip(acc["lat"], b.lat["lat"], strict=True)]
        return acc

    def nl_rows(self, step):
        """{TWB_NL row text: [calls]} over the calls that sampled NL (E05: one key expected)."""
        self._need(step)
        out = {}
        for b in self.call_list("ctrl", "V1"):
            out.setdefault(b.nl_rows[step], []).append(b.call)
        return out

    def sides(self):
        """[(call, AGG_SIDE row)] of the calls that wrote a side file; open_side checks and opens one."""
        return [(b.call, b.side) for b in self.call_list("ctrl", "V1") if b.side is not None]

    def verify_sides(self):
        for _, row in self.sides():
            open_side(row)
        return len(self.sides())


def write_sha256sums(agg_dir):
    """SHA256SUMS of the call files of a point directory, in sha256sum's format (the run's receipt)."""
    names = sorted(n for n in os.listdir(agg_dir) if re.match(r"(0|[1-9][0-9]*)(\.attempt[0-9]+)?\.hbp\Z", n))
    text = "".join("%s  %s\n" % (file_sha256(os.path.join(agg_dir, n)), n) for n in names)
    with open(os.path.join(agg_dir, "SHA256SUMS"), "wb") as f:
        f.write(text.encode("ascii"))


def check_sha256sums(agg_dir, names):
    """Every call file is listed in agg_dir/SHA256SUMS with its sha256, and the list names nothing else."""
    path = os.path.join(agg_dir, "SHA256SUMS")
    if not os.path.exists(path):
        raise StageBStop("sha256sums", "no SHA256SUMS in " + agg_dir)
    listed = {}
    for ln in read_lines(path):
        m = re.match(r"([0-9a-f]{64})  (\S+)\Z", ln)
        if not m or m.group(2) in listed:
            raise StageBStop("sha256sums", "bad line: " + ln[:80])
        listed[m.group(2)] = m.group(1)
    if set(listed) != set(names):
        raise StageBStop("sha256sums", "listed files differ from the call files")
    for n in names:
        if file_sha256(os.path.join(agg_dir, n)) != listed[n]:
            raise StageBStop("sha256sums", "sha256 of " + n)


def load_point(agg_dir, spec, require_reader_rc=True, side_dir=None, require_sums=False):
    """Read agg_dir/<call>.hbp for every call 0..calls-1 of the point and pool them.

    Rule SEED: every call present, no other call file, one seed and disjoint starts (checked per block).
    Rule STOP: an engine stop (rc=4, stage A empty_stream) loses that call's indices (NOT_MEASURED); the point keeps
    the records every read call reached, the later records are NOT_MEASURED. Anything else is a StageBStop."""
    pt = Point(spec)
    names = sorted(os.listdir(agg_dir)) if os.path.isdir(agg_dir) else []
    pat = re.compile(r"(0|[1-9][0-9]*)\.hbp\Z")
    seen = {}
    for nm in names:
        m = pat.match(nm)
        if m:
            seen[int(m.group(1))] = os.path.join(agg_dir, nm)
        elif re.match(r"(0|[1-9][0-9]*)\.attempt[0-9]+\.hbp\Z", nm):
            pt.attempts.append(nm)
        elif not (nm == "SHA256SUMS" or re.match(r"(0|[1-9][0-9]*)\.(side|err)\Z", nm)):
            raise StageBStop("seed_extra_file", "%s: %s" % (spec.id, nm))
    if require_sums:
        check_sha256sums(agg_dir, [os.path.basename(p) for p in seen.values()] + pt.attempts)
    missing = [i for i in range(spec.calls) if i not in seen]
    extra = [i for i in seen if i >= spec.calls]
    if missing:
        raise StageBStop("seed_dropped_call", "%s: calls %s" % (spec.id, _ranges(missing)))
    if extra:
        raise StageBStop("seed_extra_call", "%s: calls %s" % (spec.id, _ranges(extra)))
    streams = {}
    for i in range(spec.calls):
        cf = read_call_file(seen[i], spec, i, require_reader_rc, side_dir or agg_dir)
        pt.files[i] = cf
        if cf.block is None:
            pt.lost.append((i, "engine_stop_rc4"))
            continue
        h = cf.block.stdin["sha256"]
        if h in streams:
            raise StageBStop("seed_repeated_stream", "%s: calls %d and %d" % (spec.id, streams[h], i))
        streams[h] = i
        pt.calls[i] = cf.block
    if not pt.calls:
        pt.steps = ()
        pt.not_measured = spec.steps
        return pt
    k = min(len(b.steps) for b in pt.calls.values())
    pt.steps = spec.steps[:k]
    pt.not_measured = spec.steps[k:]
    return pt


def _ranges(xs):
    xs = sorted(xs)
    if len(xs) <= 6:
        return ",".join(str(x) for x in xs)
    return "%d..%d(%d)" % (xs[0], xs[-1], len(xs))


# ---------------------------------------------------------------------------------------------------------------------
# Side files (AGG-FORMAT.md section 7).

SIDE_MAGIC = b"STRPSIDE"


class SideFile:
    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = f.read()
        d = self.data
        if len(d) < 64 or d[:8] != SIDE_MAGIC:
            raise StageBStop("side_header", path)
        ver, nv, vmask, nrec, s0, s1 = struct.unpack_from("<6I", d, 8)
        start, count = struct.unpack_from("<2Q", d, 32)
        if ver != 1 or d[48:64] != bytes(16) or nrec > 2:
            raise StageBStop("side_header", path)
        self.variants = tuple(v for k, v in enumerate(VARIANTS) if vmask >> k & 1)
        if len(self.variants) != nv or vmask >> 7:
            raise StageBStop("side_header", path + " variant mask")
        self.steps = tuple(s for s in (s0, s1)[:nrec])
        if (s0, s1) != ((64, 128)[:nrec] + (0, 0))[:2]:
            raise StageBStop("side_header", path + " steps")
        self.start, self.count = start, count
        self.rec = 8 + 16 * nv * nrec
        if len(d) != 64 + self.rec * count:
            raise StageBStop("side_size", path)

    def sample(self, k):
        """(flags, {(variant, step): (br, b_br)}) of the k-th sample (index start + k)."""
        off = 64 + self.rec * k
        (flags,) = struct.unpack_from("<Q", self.data, off)
        if flags >> 4:
            raise StageBStop("side_flags", "sample %d" % k)
        out = {}
        off += 8
        for v in self.variants:
            for s in self.steps:
                br, bb = struct.unpack_from("<qQ", self.data, off)
                out[(v, s)] = (br, bb)
                off += 16
        return flags, out


def paired_side_sums(side_a, side_b, step_set=(64, 128)):
    """E04: per (variant, step), over the common indices of two side files of different seeds, of d_i = br_a - br_b
    and rb_i = b_br_a + b_br_b: {S: sum d, Q: sum d^2, RB: sum rb, RQ: sum rb^2, m: count}."""
    if side_a.start != side_b.start or side_a.count != side_b.count:
        raise StageBStop("side_pair", "index ranges differ")
    keys = [(v, s) for v in side_a.variants if v in side_b.variants for s in side_a.steps if s in side_b.steps
            and s in step_set]
    acc = {k: {"S": 0, "Q": 0, "RB": 0, "RQ": 0, "m": 0} for k in keys}
    for i in range(side_a.count):
        _, a = side_a.sample(i)
        _, b = side_b.sample(i)
        for k in keys:
            d = a[k][0] - b[k][0]
            rb = a[k][1] + b[k][1]
            x = acc[k]
            x["S"] += d
            x["Q"] += d * d
            x["RB"] += rb
            x["RQ"] += rb * rb
            x["m"] += 1
    return acc


# ---------------------------------------------------------------------------------------------------------------------
# Rule H8, rule B16, rule SIGNFLIP.


def h8(oa, ob, amb):
    """Pair test on certified counts Oa, Ob with A ambiguous: FLAG, UNFLAGGED or UNRESOLVED."""
    d = abs(oa - ob)
    if (d + amb) * (d + amb) <= 64 * (oa + ob):
        return UNFLAGGED
    if d > amb and (d - amb) * (d - amb) > 64 * (oa + ob + amb):
        return FLAG
    return UNRESOLVED


def h8_pairs(sec):
    """The 8 pi pairs (k, k+8) and the 8 mirror pairs (k, 15-k) of a 16-sector count vector."""
    return [("pi%d" % k, sec[k], sec[k + 8]) for k in range(8)] + [("mir%d" % k, sec[k], sec[15 - k])
                                                                    for k in range(8)]


def _b16_flag(d, mp):
    return 3 * d * d > 1440 * mp + 512 * d


def b16_sector(ok, amb, mp):
    """Sector k of rule B16 with its ambiguous samples bracketed: FLAG, UNFLAGGED or UNRESOLVED."""
    lo, hi = ok, ok + amb
    dmax = max(abs(16 * lo - mp), abs(16 * hi - mp))
    cands = [lo, hi] + [c for c in (mp // 16, -((-mp) // 16)) if lo <= c <= hi]
    dmin = min(abs(16 * c - mp) for c in cands)
    if _b16_flag(dmin, mp):
        return FLAG
    if not _b16_flag(dmax, mp):
        return UNFLAGGED
    return UNRESOLVED


def b16(sec, amb, mp):
    """Rule B16 on M' non-atom samples: (verdict, per-sector outcomes); verdict "uniform" if no sector can flag,
    "not_uniform" if one flags for every placement of the ambiguous samples, else "unresolved"."""
    if sum(sec) + amb != mp:
        raise StageBStop("b16_identity", "sum(sec)+A != M'")
    per = [b16_sector(sec[k], amb, mp) for k in range(16)]
    if FLAG in per:
        return "not_uniform", per
    if all(p == UNFLAGGED for p in per):
        return "uniform", per
    return "unresolved", per


def b16_threshold_D(mp):
    """The smallest integer D_k that flags at M' (for reports and tests)."""
    d = (512 + math.isqrt(512 * 512 + 4 * 3 * 1440 * mp)) // 6
    while _b16_flag(d, mp):
        d -= 1
    while not _b16_flag(d, mp):
        d += 1
    return d


def signflip(s, q, rb=0, rq=0):
    """Zero-mean test: FLAG if |sum b| - RB > 5 (sqrt(sum b^2) + sqrt(sum rb^2)), else UNFLAGGED (exact)."""
    lhs = Rad(abs(s) - rb)
    rhs = Rad.sqrt(q, 5) + Rad.sqrt(rq, 5)
    return FLAG if lhs > rhs else UNFLAGGED


# ---------------------------------------------------------------------------------------------------------------------
# Rule SE: binomial, batch means, delta method, batch jackknife. All return exact SE^2; Rad.sqrt makes the SE.


def pi_hat(pos, neg, m):
    """Pi_hat = (O+ - O-)/(2M)."""
    return fr(pos - neg, 2 * m)


def se2_pi(pi, m):
    """Binomial SE^2 of Pi_hat: (1 - 4 Pi^2)/(4M)."""
    return div(1 - 4 * pi * pi, 4 * m)


def se2_binomial(k, m):
    """SE^2 of a proportion k/m: p(1-p)/m."""
    p = fr(k, m)
    return div(p * (1 - p), m)


def mean_se2(values):
    """Mean of K values and the SE^2 of the mean, sum (v - mean)^2 / (K (K - 1))."""
    k = len(values)
    if k < 2:
        raise StageBStop("se_batches", "fewer than 2 batches")
    vals = [fr(v) for v in values]
    m = div(sum(vals), k)
    return m, div(sum((v - m) * (v - m) for v in vals), k * (k - 1))


def batch_means(sums, counts):
    """Batch means of equal-size batches: (pooled mean, SE^2)."""
    if len(set(counts)) != 1 or len(sums) != len(counts):
        raise StageBStop("se_batches", "unequal batches")
    return mean_se2([fr(s, c) for s, c in zip(sums, counts, strict=True)])


def ratio_paired(xs, ys):
    """Delta method for R = sum x / sum y over K paired batch values: (R, SE^2), SE^2 = sum (x_j - R y_j)^2 /
    (K (K - 1) ybar^2)."""
    k = len(xs)
    if k < 2 or len(ys) != k:
        raise StageBStop("se_batches", "ratio batches")
    sx, sy = sum(fr(x) for x in xs), sum(fr(y) for y in ys)
    r = div(sx, sy)
    ybar = div(sy, k)
    return r, div(sum((fr(x) - r * fr(y)) * (fr(x) - r * fr(y)) for x, y in zip(xs, ys, strict=True)),
               k * (k - 1) * ybar * ybar)


def ratio_indep(mx, se2x, my, se2y):
    """Delta method for R = X/Y of independent estimates: (R, SE^2 = se2x/Y^2 + X^2 se2y / Y^4)."""
    r = div(mx, my)
    return r, div(se2x, my * my) + div(mx * mx * se2y, my * my * my * my)


def jackknife(stat, batches):
    """Batch jackknife: stat maps a list of batches to a Fraction; returns (stat(all), SE^2 = (K-1)/K sum
    (theta_j - mean)^2)."""
    k = len(batches)
    if k < 2:
        raise StageBStop("se_batches", "jackknife needs 2 batches")
    full = stat(batches)
    th = [stat(batches[:j] + batches[j + 1 :]) for j in range(k)]
    m = div(sum(th), k)
    return full, div((k - 1) * sum((t - m) * (t - m) for t in th), k)


def se(se2, times=1):
    """times * sqrt(se2) as an exact radical."""
    return Rad.sqrt(se2, times)


# ---------------------------------------------------------------------------------------------------------------------
# Rule READ3.


class Band:
    """A band [lo, hi] with optional open ends; None for an unbounded end."""

    __slots__ = ("lo", "hi", "lo_open", "hi_open")

    def __init__(self, lo, hi, lo_open=False, hi_open=False):
        self.lo = None if lo is None else Rad.of(lo)
        self.hi = None if hi is None else Rad.of(hi)
        self.lo_open = lo_open
        self.hi_open = hi_open

    def text(self):
        a = "-inf" if self.lo is None else self.lo.text(8)
        b = "inf" if self.hi is None else self.hi.text(8)
        return ("(" if self.lo_open else "[") + a + "," + b + (")" if self.hi_open else "]")

    def holds_interval(self, lo, hi):
        lo_ok = self.lo is None or ((lo > self.lo) if self.lo_open else (lo >= self.lo))
        hi_ok = self.hi is None or ((hi < self.hi) if self.hi_open else (hi <= self.hi))
        return lo_ok and hi_ok

    def disjoint(self, lo, hi):
        below = self.lo is not None and ((hi <= self.lo) if self.lo_open else (hi < self.lo))
        above = self.hi is not None and ((lo >= self.hi) if self.hi_open else (lo > self.hi))
        return below or above


def read3_interval(lo, hi, band):
    """Interval [lo, hi] against a band: MET inside, MISS disjoint, else NOT_RESOLVED. lo, hi may be Rad."""
    lo, hi = Rad.of(lo), Rad.of(hi)
    if lo > hi:
        raise StageBStop("read3", "empty interval")
    if band.holds_interval(lo, hi):
        return MET
    if band.disjoint(lo, hi):
        return MISS
    return NOT_RESOLVED


def read3_sampled(x, p, tol, e):
    """Sampled estimate x against p with tolerance tol and error e (any may be Rad): MET if |x-p| + e <= tol,
    MISS if |x-p| - e > tol, else NOT_RESOLVED."""
    d = (Rad.of(x) - Rad.of(p)).abs()
    e, tol = Rad.of(e), Rad.of(tol)
    if d + e <= tol:
        return MET
    if d - e > tol:
        return MISS
    return NOT_RESOLVED


def read3_exact(ok):
    return MET if ok else MISS


def read3_outcome(outcome, predicted, opposite):
    """A certified test outcome against its predicted outcome: MET if equal, MISS if the certified opposite."""
    if outcome == predicted:
        return MET
    if outcome == opposite:
        return MISS
    return NOT_RESOLVED


def predicted_flag_read(outcome, predicted_flag):
    """H8 or B16 sector style: predicted FLAG or UNFLAGGED."""
    opp = UNFLAGGED if predicted_flag == FLAG else FLAG
    return read3_outcome(outcome, predicted_flag, opp)


# ---------------------------------------------------------------------------------------------------------------------
# Rule EXPOSED (X08), from the frozen text.

X08_TRIPLES = ("delta=-1/4:_(s,t)=(1,1/2),_(1,3/2),_(1,2),_(1/2,2),_(1/4,2);"
               "_delta=1/2:_s_in_{1/8,1/4,1/2,1}_at_every_t")
_EXPOSED_M14 = {(fr(1), fr(1, 2)), (fr(1), fr(3, 2)), (fr(1), fr(2)), (fr(1, 2), fr(2)), (fr(1, 4), fr(2))}
_EXPOSED_P12_S = {fr(1, 8), fr(1, 4), fr(1, 2), fr(1)}
EXPOSED_S0_PHRASE = "(Q07_y=0_t=2_and_E18_(0,2))"


def check_exposure_text(fz=None):
    fz = fz or frozen_mod.load()
    if fz.row("STRIPES_EXPOSURE", "X08")["triples"] != X08_TRIPLES:
        raise StageBStop("exposed", "X08 triples differ from the reader's table")
    fz.require("STRIPES_RULE", "EXPOSED", EXPOSED_S0_PHRASE)
    return True


def exposed(delta, abs_s, t):
    """Rule EXPOSED for a value read at (delta, |s|, t), s != 0."""
    delta, abs_s, t = fr(delta), fr(abs_s), fr(t)
    if abs_s == 0:
        raise StageBStop("exposed", "s=0 takes exposed_s0")
    if delta == fr(-1, 4):
        return (abs_s, t) in _EXPOSED_M14
    if delta == fr(1, 2):
        return abs_s in _EXPOSED_P12_S
    return False


def exposed_s0(delta, t):
    """The s=0 criterion of rule EXPOSED: second moments at (delta, 0, t), filed C2 and f at |s|<=1/4."""
    delta, t = fr(delta), fr(t)
    if delta == fr(1, 2):
        return True
    return delta == fr(-1, 4) and t == 2


class Scoring:
    """Whether a read is scored, and why: `rr` is the frozen phrase that makes it read-and-report."""

    __slots__ = ("scored", "why")

    def __init__(self, scored, why):
        self.scored = scored
        self.why = why


def scored(why="scored"):
    return Scoring(True, why)


def report(fz, kind, rid, phrase, why):
    """Read-and-report, by a phrase that must stand verbatim in the frozen row."""
    fz.require(kind, rid, phrase)
    return Scoring(False, why)


def value_scoring(fz, rid, triple, phrase):
    """A read of a frozen value at triple (delta, |s|, t): read-and-report iff exposed; the phrase (or None) is the
    frozen text naming it, and its presence must agree with the rule."""
    ex = exposed_s0(triple[0], triple[2]) if fr(triple[1]) == 0 else exposed(*triple)
    if ex != (phrase is not None):
        raise StageBStop("exposed", "%s %s: rule and row text disagree" % (rid, triple))
    if phrase is None:
        return Scoring(True, "unexposed")
    fz.require("STRIPES_PREDICT", rid, phrase)
    return Scoring(False, "X08")


# ---------------------------------------------------------------------------------------------------------------------
# READ and VERDICT rows.


class Read:
    """One read of a PREDICT row. lo, hi, value: Fraction, Rad or None; verdict from READ3 (REPORT if not scored)."""

    __slots__ = ("row", "rid", "at", "kind", "scoring", "outcome", "value", "lo", "hi", "band", "frozen", "detail")

    def __init__(self, row, rid, at, kind, scoring, outcome, value=None, lo=None, hi=None, band="", frozen="none",
                 detail=()):
        if outcome not in (MET, MISS, NOT_RESOLVED, NOT_MEASURED):
            raise StageBStop("read", "outcome " + str(outcome))
        self.row = row
        self.rid = rid
        self.at = at
        self.kind = kind
        self.scoring = scoring
        self.outcome = outcome
        self.value = value
        self.lo = lo
        self.hi = hi
        self.band = band
        self.frozen = frozen
        self.detail = tuple(detail)

    @property
    def scored(self):
        return self.scoring.scored

    @property
    def verdict(self):
        if self.outcome == NOT_MEASURED:
            return NOT_MEASURED
        return self.outcome if self.scored else REPORT

    def row_text(self):
        pairs = [
            ("row", self.row), ("read", self.rid), ("at", self.at), ("kind", self.kind),
            ("scored", "1" if self.scored else "0"), ("why", self.scoring.why),
            ("value", _num_text(self.value, "near")), ("lo", _num_text(self.lo, "down")),
            ("hi", _num_text(self.hi, "up")),
            ("band", self.band.text() if isinstance(self.band, Band) else (self.band or "none")),
            ("frozen", self.frozen or "none"), ("verdict", self.verdict),
            ("detail", ",".join("%s:%s" % (k, v) for k, v in self.detail) or "none"),
        ]
        return emit("STRIPES_READ", pairs)


def _num_text(x, mode):
    if x is None:
        return "none"
    if isinstance(x, str):
        return x
    if isinstance(x, int):
        return str(x)
    if isinstance(x, Rad):
        v = x.iv()
        return fmt(v.lo if mode == "down" else v.hi if mode == "up" else v.mid(), 12, mode)
    return fmt(x, 12, mode)


class Verdict:
    __slots__ = ("row", "name", "tag", "reads", "falsifier", "verdict")

    def __init__(self, row, name, tag, reads, falsifier_reads=(), falsifier_text="none"):
        self.row = row
        self.name = name
        self.tag = tag
        self.reads = list(reads)
        ids = {r.rid for r in self.reads if r.scored}
        for f in falsifier_reads:
            if f not in ids:
                raise StageBStop("falsifier", "%s: falsifier on a read that is not scored: %s" % (row, f))
        self.falsifier = (",".join(falsifier_reads) + ":" + falsifier_text) if falsifier_reads else "none"
        self.verdict = row_verdict(self.reads, bool(falsifier_reads))

    def counts(self):
        sc = [r for r in self.reads if r.scored]
        c = {"reads": len(self.reads), "scored": len(sc), "report": len(self.reads) - len(sc)}
        for o in (MET, MISS, NOT_RESOLVED, NOT_MEASURED):
            c[o] = sum(1 for r in sc if r.outcome == o)
        return c

    def row_text(self):
        c = self.counts()
        return emit("STRIPES_VERDICT", [
            ("row", self.row), ("name", self.name), ("tag", self.tag), ("reads", str(c["reads"])),
            ("scored", str(c["scored"])), ("report", str(c["report"])), ("met", str(c[MET])),
            ("miss", str(c[MISS])), ("not_resolved", str(c[NOT_RESOLVED])), ("not_measured", str(c[NOT_MEASURED])),
            ("falsifier", self.falsifier), ("verdict", self.verdict),
        ])


def row_verdict(reads, falsifier=False):
    """Rule READ3 for a row, on its scored reads: NOT_MET if one is MISS or a falsifier occurs, MET if all are MET,
    NOT_MEASURED if all lack data, NONE if no read is scored, else NOT_RESOLVED."""
    sc = [r for r in reads if r.scored]
    if any(r.outcome == MISS for r in sc) or falsifier:
        return NOT_MET
    if not sc:
        return NONE
    if all(r.outcome == MET for r in sc):
        return MET
    if all(r.outcome == NOT_MEASURED for r in sc):
        return NOT_MEASURED
    return NOT_RESOLVED


class ReadFile:
    """READ-STRIPE-PHASE.hbp: a head, the inputs, the READ rows, the VERDICT rows and an end row with the hash."""

    def __init__(self, fz=None):
        self.fz = fz or frozen_mod.load()
        self.inputs = []
        self.verdicts = []
        self.notes = []

    def add_input(self, label, path):
        self.inputs.append((label, path, file_sha256(path), os.path.getsize(path)))

    def add(self, verdict):
        if verdict.row in {v.row for v in self.verdicts}:
            raise StageBStop("read_file", "row twice: " + verdict.row)
        self.verdicts.append(verdict)

    def lines(self):
        out = [emit("STRIPES_READ_HEAD", [
            ("reader", READER), ("reader_version", READER_VERSION),
            ("frozen", "polariton-stripes/" + frozen_mod.FROZEN_NAME), ("frozen_sha256", self.fz.sha256),
            ("rows", ",".join(v.row for v in self.verdicts)),
        ])]
        for label, path, h, n in self.inputs:
            out.append(emit("STRIPES_READ_INPUT", [("label", label), ("path", os.path.basename(path)),
                                                   ("bytes", str(n)), ("sha256", h)]))
        for label, text in self.notes:
            out.append(emit("STRIPES_READ_NOTE", [("label", label), ("text", text)]))
        for v in self.verdicts:
            for r in v.reads:
                out.append(r.row_text())
        for v in self.verdicts:
            out.append(v.row_text())
        h = sha256_hex("".join(ln + "\n" for ln in out).encode("ascii"))
        out.append(emit("STRIPES_READ_END", [("rows", str(len(out))), ("sha256", h)]))
        return out

    def write(self, path):
        data = "".join(ln + "\n" for ln in self.lines()).encode("ascii")
        with open(path, "wb") as f:
            f.write(data)
        return sha256_hex(data)


# ---------------------------------------------------------------------------------------------------------------------
# Rule GUARD: the filed guard lines.


def check_guard_file(path, triples):
    """Every (N, delta, y) has a TWB_GUARD verdict=allowed line, and no line refuses."""
    seen = set()
    for ln in read_lines(path):
        _, f = parse_row(ln, "TWB_GUARD", ("N", "delta", "y", "verdict", "reason", "computed"))
        d = fields_dict(f)
        if d["verdict"] != "allowed" or d["reason"] != "none" or d["computed"] != "0":
            raise StageBStop("guard", "refused: " + ln[:80])
        seen.add((int(d["N"]), d["delta"], d["y"]))
    missing = [t for t in triples if (t[0], t[1], t[2]) not in seen]
    if missing:
        raise StageBStop("guard", "no guard line for %s" % (missing[:3],))
    return True
