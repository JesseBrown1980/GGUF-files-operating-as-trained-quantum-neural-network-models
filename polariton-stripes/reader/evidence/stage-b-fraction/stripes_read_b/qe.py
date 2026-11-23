"""The quantum engine's rows: POLARITON_FIRST_CORRECTION_READ, parsed against the command plan, and the certified
errors of rule EB."""

import re
from fractions import Fraction

from . import frozen as frozen_mod
from .common import StageBStop, square_root
from .exact import ExactError, Iv, canon_int, div, fr, ipow, parse_rat, rat_text
from .hbp import RowError, fields_dict, parse_row, read_lines

READ_KIND = "POLARITON_FIRST_CORRECTION_READ"
COST_KIND = "POLARITON_FIRST_CORRECTION_COST"
READ_KEYS = ("N", "K", "even_states", "array_bytes", "u", "x", "y", "delta", "t", "window", "c", "E", "degree", "reach",
             "applies", "elem_err_units", "jbar_e18", "f_e18", "A_e18", "B_e18", "C1_e18", "C2_e18", "A1_e18",
             "D2_e18", "V2_e18", "energy_e18", "norm_off_e18", "eps_tail_e18", "eps_poly_e18", "eps_round_e18",
             "eps_e18", "C1_err_e18", "A1_err_e18", "V2_lo_e18", "V2_hi_e18", "norm_B_s20", "tail_max_e18",
             "leak_max_e18", "leak_sum_e18", "float_used")
INT_KEYS = READ_KEYS[10:39]
COST_KEYS = ("N", "K", "even_states", "array_bytes", "delta", "y", "t", "ms", "peak_rss_kB")
SECTOR_BYTES_PER_STATE = 104
POINT_BYTES_PER_STATE = 120
E18 = ipow(10, 18)
W = 6


class Command:
    """One QE command of the plan: mode (point or sector), N = K, delta, y, the read times, and its frozen point."""

    __slots__ = ("mode", "N", "delta", "y", "times", "point")

    def __init__(self, mode, n, delta, y, times, point):
        self.mode = mode
        self.N = n
        self.delta = delta
        self.y = y
        self.times = tuple(times)
        self.point = point

    def keys(self):
        return [(self.mode, self.N, self.delta, self.y, t) for t in self.times]

    def argv(self):
        return [self.mode, str(self.N), str(self.N), self.delta, self.y, str(W), ",".join(self.times)]


def _plan():
    p = []
    for n in (81, 729, 6561):
        p.append(Command("sector", n, "-1/4", "0", ("1/2", "1", "2", "4"), "QR1"))
    for n in (81, 729):
        p.append(Command("point", n, "-1/4", "0", ("1/2", "1", "2", "4"), "QR2"))
    for y in ("1/27", "1/54", "1/108", "1/216"):
        p.append(Command("point", 729, "-1/4", y, ("1/8", "1/4", "1/2", "1", "2"), "QR3"))
    p.append(Command("point", 729, "-1/4", "-1/54", ("1/2", "1", "2"), "QR4"))
    for y in ("1/27", "1/108", "1/216"):
        p.append(Command("point", 81, "-1/4", y, ("1/8", "1/4", "1/2", "1"), "QR5"))
    p.append(Command("point", 81, "-1/4", "1/54", ("1/8", "1/4", "1/2", "1", "2", "4"), "QR5"))
    p.append(Command("point", 81, "-1/4", "-1/54", ("1/2", "1", "2", "4"), "QR5"))
    return p


PLAN = _plan()
# The frozen command text of each QE point (STRIPES_POINT QR1-QR5), checked verbatim before the plan is used.
FROZEN_COMMANDS = {
    "QR1": "sector_N_N_-1/4_0_6_1/2,1,2,4_for_N=81,_729,_6561",
    "QR2": "point_N_N_-1/4_0_6_1/2,1,2,4_for_N=81,_729",
    "QR3": "point_729_729_-1/4_Y_6_1/8,1/4,1/2,1,2_for_Y=1/27,_1/54,_1/108,_1/216",
    "QR4": "point_729_729_-1/4_-1/54_6_1/2,1,2",
    "QR5": "point_81_81_-1/4_Y_6_1/8,1/4,1/2,1_for_Y=1/27,_1/108,_1/216;_point_81_81_-1/4_1/54_6_1/8,1/4,1/2,1,2,4;"
           "_point_81_81_-1/4_-1/54_6_1/2,1,2,4",
}


def check_plan(fz=None):
    fz = fz or frozen_mod.load()
    for pid, text in FROZEN_COMMANDS.items():
        if fz.row("STRIPES_POINT", pid)["commands"] != text:
            raise StageBStop("qe_plan", pid + " command text differs from the frozen row")
    if len(PLAN) != 15:
        raise StageBStop("qe_plan", "15 commands")
    return True


def plan_triples(plan=PLAN):
    """The (N, delta, y) the commands use."""
    return sorted({(c.N, c.delta, c.y) for c in plan})


def plan_guards(plan=PLAN):
    """One (N, delta, y) per command: each QE command is guarded before it runs (rule GUARD)."""
    return [(c.N, c.delta, c.y) for c in plan]


RC_KIND = "QE_RC"
BINARY_KIND = "QE_BINARY"
LANE_BINARY_SHA256 = "6bf8ebf2309700cb5be4cce25d82e5c4ee70fbc49521d4d7686cfc1649aa0a21"
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def argv_text(cmd):
    """The wrapper's text of a command's arguments: joined by '_'."""
    return "_".join(cmd.argv())


def parse_rc(path, plan=PLAN):
    """QE-RC.hbp, the wrapper's receipt: QE_BINARY|sha256= (sha256sum of the QE binary), then one QE_RC|argv=|rc= row
    per command, after it ran, in plan order. Returns (binary sha256, [rc per command])."""
    lines = read_lines(path)
    if len(lines) != 1 + len(plan):
        raise StageBStop("qe_rc", "%d rows, the plan has %d commands and the binary row" % (len(lines), len(plan)))
    try:
        b = fields_dict(parse_row(lines[0], BINARY_KIND, ("sha256",))[1])
        if not _HEX64.match(b["sha256"]):
            raise StageBStop("qe_rc", "binary sha256")
        rcs = []
        for cmd, ln in zip(plan, lines[1:], strict=True):
            d = fields_dict(parse_row(ln, RC_KIND, ("argv", "rc"))[1])
            if d["argv"] != argv_text(cmd):
                raise StageBStop("qe_rc", "row %s, the plan's command %s" % (d["argv"][:60], argv_text(cmd)))
            rcs.append(canon_int(d["rc"]))
    except (RowError, ExactError) as e:
        raise StageBStop("qe_rc", str(e)) from e
    return b["sha256"], rcs


class QeReads(dict):
    """{key: QeRead} of the commands read, and what rule STOP left out: `failed` the (argv, rc) of each command that
    exited nonzero, `stderr_lines` the stderr lines that are not COST rows, `binary` the QE binary's sha256."""

    def __init__(self):
        dict.__init__(self)
        self.failed = []
        self.stderr_lines = 0
        self.binary = None


def _cost_key(fields):
    try:
        return (fields.get("layout", "point"), canon_int(fields["N"]), rat_text(parse_rat(fields["delta"])),
                rat_text(parse_rat(fields["y"])), rat_text(parse_rat(fields["t"])))
    except (ExactError, KeyError) as e:
        raise StageBStop("qe_cost", "COST row keys: %s" % e) from e


class QeRead:
    """One READ row with its exact values and the certified intervals of rule EB."""

    def __init__(self, line, layout, d):
        self.line = line
        self.layout = layout
        self.d = d
        self.N = canon_int(d["N"])
        self.delta = parse_rat(d["delta"])
        self.y = parse_rat(d["y"])
        self.t = parse_rat(d["t"])
        self.v = {k: canon_int(d[k]) for k in INT_KEYS}

    def key(self):
        return (self.layout, self.N, rat_text(self.delta), rat_text(self.y), rat_text(self.t))

    def e18(self, name):
        return fr(self.v[name + "_e18"], E18)

    def eps(self):
        """eps = (eps_e18 + 1) 10^-18 (rule EB)."""
        return fr(self.v["eps_e18"] + 1, E18)

    def _blk(self, norm):
        e = self.eps()
        return norm * (2 * e + e * e)

    def B(self):
        return self.e18("B")

    def e_B(self):
        """e_B = ((N + 1)/2)(2 eps + eps^2) + 2^-21."""
        return self._blk(fr(self.N + 1, 2)) + fr(1, ipow(2, 21))

    def B_iv(self):
        return Iv(self.B() - self.e_B(), self.B() + self.e_B())

    def absB_iv(self):
        b, e = abs(self.B()), self.e_B()
        return Iv(max(b - e, Fraction(0)), b + e)

    def A(self):
        return self.e18("A")

    def A_err(self):
        """(N/2) A1_err: the bound on A of the engine's A1 = 2|A|/N."""
        return fr(self.N, 2) * self.e18("A1_err")

    def _floored(self, name, norm_err):
        """A field printed by floor twice (at 2^60, then at 10^-18): [p, p + 2] 10^-18, widened by the norm term."""
        p = self.v[name + "_e18"]
        return Iv(fr(p, E18) - norm_err, fr(p + 2, E18) + norm_err)

    def C2_iv(self):
        """C2 = 2<n+ n->/(N(N-1)); norm(n+ n-) <= N^2/4."""
        n = self.N
        return self._floored("C2", div(2, n * (n - 1)) * self._blk(fr(n * n, 4)))

    def f_iv(self):
        """f = <n+ + n->/N; norm(n+ + n-) <= N."""
        return self._floored("f", div(1, self.N) * self._blk(Fraction(self.N)))

    def QW_iv(self):
        """Q_W = N(N-1) C2/2 + N f/2 + 1/4 (derivation QW)."""
        n = self.N
        return self.C2_iv() * fr(n * (n - 1), 2) + self.f_iv() * fr(n, 2) + fr(1, 4)

    def D2_iv(self):
        """D2 = 2|<B>|/N from B_e18 with e_B."""
        return self.absB_iv() * fr(2, self.N)


def _layout(d):
    n_states = canon_int(d["even_states"])
    k = canon_int(d["K"])
    ab = canon_int(d["array_bytes"])
    if ab == n_states * POINT_BYTES_PER_STATE:
        return "point"
    if ab == (k // 2 + 1) * SECTOR_BYTES_PER_STATE:
        return "sector"
    raise StageBStop("qe_row", "array_bytes fits neither layout")


def parse_qe(path, plan=PLAN, cost_path=None, rc_path=None):
    """{key: QeRead} of a concatenated QE stdout file; key = (layout, N, delta, y, t) in the engine's text.

    Every row must be an unsabotaged READ row of a planned command at the frozen keys (K = N, u = 1, x = delta - 1,
    window 2^-6, float_used = 0), each key at most once. Rule STOP: missing rows are left out, and so is every row of
    a command whose rc in rc_path (QE-RC.hbp) is not 0; their reads are NOT_MEASURED. With cost_path, the COST rows
    of the commands that exited 0 must match their READ rows one for one, in order; the COST rows of a command that
    exited nonzero, and stderr text that is not a COST row, are kept out of the match. Such text with every command
    at rc=0 is a StageBStop."""
    want = {}
    for c in plan:
        for k in c.keys():
            want[k] = c
    res = QeReads()
    failed = set()
    if rc_path is not None:
        res.binary, rcs = parse_rc(rc_path, plan)
        for cmd, rc in zip(plan, rcs, strict=True):
            if rc != 0:
                failed.add(id(cmd))
                res.failed.append((argv_text(cmd), rc))
    out = {}
    order = []
    for ln in read_lines(path):
        try:
            _, f = parse_row(ln, READ_KIND, READ_KEYS)
        except RowError as e:
            raise StageBStop("qe_row", str(e)) from e
        d = fields_dict(f)
        try:
            lay = _layout(d)
            r = QeRead(ln, lay, d)
        except ExactError as e:
            raise StageBStop("qe_row", str(e)) from e
        k = r.key()
        if k not in want:
            raise StageBStop("qe_unplanned_row", "%s" % (k,))
        if k in out:
            raise StageBStop("qe_repeated_row", "%s" % (k,))
        delta = r.delta
        fixed = {"K": str(r.N), "u": "1", "x": rat_text(delta - 1), "window": "2^-%d" % W, "float_used": "0"}
        for kk, vv in fixed.items():
            if d[kk] != vv:
                raise StageBStop("qe_row", "%s: %s=%s" % (k, kk, d[kk]))
        square_root(r.N)
        out[k] = r
        order.append(k)
    if cost_path is not None:
        costs = []
        for ln in read_lines(cost_path):
            if not ln.startswith(COST_KIND + "|"):
                res.stderr_lines += 1
                continue
            try:
                fields = fields_dict(parse_row(ln, COST_KIND)[1])
            except RowError as e:
                raise StageBStop("qe_cost", str(e)) from e
            key = _cost_key(fields)
            if key not in want:
                raise StageBStop("qe_cost", "COST row of no planned command: %s" % (key,))
            if id(want[key]) in failed:
                continue
            costs.append(tuple(fields.get(x) for x in ("N", "K", "even_states", "array_bytes", "delta", "y", "t"))
                         + (key[0],))
        if res.stderr_lines and not failed:
            raise StageBStop("qe_stderr", "%d stderr lines that are not COST rows, and every command exited 0" % (
                res.stderr_lines))
        reads = [tuple(out[k].d[x] for x in ("N", "K", "even_states", "array_bytes", "delta", "y", "t"))
                 + (out[k].layout,) for k in order if id(want[k]) not in failed]
        if costs != reads:
            raise StageBStop("qe_cost", "COST rows do not match the READ rows")
    for k in order:
        if id(want[k]) not in failed:
            res[k] = out[k]
    return res


def get(reads, layout, n, delta, y, t):
    """The read at a key, or None (NOT_MEASURED)."""
    return reads.get((layout, n, delta, y, t))


def missing(reads, plan=PLAN):
    return [k for c in plan for k in c.keys() if k not in reads]
