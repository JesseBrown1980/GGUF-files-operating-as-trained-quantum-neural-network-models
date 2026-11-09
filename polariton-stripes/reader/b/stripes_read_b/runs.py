"""The twens run sums of R1-R4: 64 batches per point, each a TWB_HEAD, per record TWENS, TWB and TWB_ROUND of VNC,
and TWB_DONE; stderr one TWB_MEMO row (memo=1). Rule STOP: an empty batch (exit 4 prints nothing) is lost and the
point keeps the records every read batch reached."""

import os
import re

from .common import (
    DTDEN,
    RUN_POINTS,
    TWB_HEAD_KEYS,
    TWB_HEAD_ROUNDING,
    TWB_HEAD_SUMS,
    TWENS_BINARY_SHA256,
    TWENS_SOURCE_SHA256,
    TWENS_VERSION,
    StageBStop,
    batch_means,
    engine_h,
    jackknife,
    seed_u64,
)
from .exact import ExactError, canon_int, div, fr
from .hbp import RowError, fields_dict, file_sha256, parse_row, read_lines

S_NAMES = ("zr", "zi", "dzr", "dzi", "xw", "dxw", "xnc", "dxnc", "f")
Q_NAMES = ("qdzr", "qdxw", "qdxnc", "qzr", "qxw", "qxnc", "qdzi")
X_NAMES = ("f2", "br", "bi", "br2", "bi2", "brbi", "zrxw", "zrxnc", "dzrdxw", "dzrdxnc")
E_NAMES = ("zr2", "zi2", "dzr2", "dzi2", "xw2", "dxw2", "xnc2", "dxnc2")
RB_NAMES = S_NAMES + Q_NAMES + X_NAMES + E_NAMES
TWENS_KEYS = ("N", "delta", "u", "y", "samples", "seed", "dtden", "step", "variant", "n", "h", "ctrl") + S_NAMES \
    + Q_NAMES + ("float_used",)
TWB_KEYS = ("N", "delta", "u", "y", "seed", "start", "count", "dtden", "step", "variant", "init", "seeds", "kappa",
            "phase", "n", "h", "ctrl") + S_NAMES + Q_NAMES + X_NAMES + E_NAMES + ("float_used",)
ROUND_KEYS = ("N", "delta", "y", "seed", "start", "count", "dtden", "step", "variant", "n") \
    + tuple("rb_" + x for x in RB_NAMES) + ("eps_max", "units", "float_used")
ROUND_UNITS = "ulps_of_each_field(sums_2^-40,squares_and_products_2^-80)"
DONE_KEYS = ("n", "records", "mask", "float_used")
MEMO_KEYS = ("count", "per_sample", "k4", "k4_core", "k4_in_core", "k4_distinct", "k4_outside", "k4_wraps", "k2",
             "k2_core", "k2_in_core", "k2_distinct", "k2_outside", "ps_samples", "integrations", "plain_integrations")
KEEP = ("n", "br", "bi", "br2", "bi2", "brbi")
KEEP_RB = ("br", "bi", "br2", "bi2", "brbi")


class Batch:
    """One run batch: per record step, {n, br, bi, br2, bi2, brbi, rb_br, rb_bi, rb_br2, rb_bi2, rb_brbi}."""

    def __init__(self, j, path):
        self.j = j
        self.path = path
        self.sha256 = file_sha256(path)
        self.steps = ()
        self.rec = {}
        self.memo = None


def _expect(fields_d, want, what):
    for k, v in want.items():
        if fields_d[k] != v:
            raise StageBStop("run_field", "%s: %s=%s, expected %s" % (what, k, fields_d[k][:60], v[:60]))


def parse_batch(path, err_path, spec, j):
    """One batch's stdout (and stderr), checked row by row; None for an empty stdout (an engine stop)."""
    lines = read_lines(path)
    if not lines:
        return None
    b = Batch(j, path)
    per = spec.per_batch
    seed = str(seed_u64(spec.seed_string))
    try:
        _, f = parse_row(lines[0], "TWB_HEAD", TWB_HEAD_KEYS)
        h = fields_dict(f)
        _expect(h, {"engine": "twens", "version": TWENS_VERSION, "cli": "run", "binary_sha256": TWENS_BINARY_SHA256,
                    "source_sha256": TWENS_SOURCE_SHA256, "N": str(spec.N), "delta": spec.delta, "u": "1",
                    "y": spec.y, "seed": seed, "seed_string": spec.seed_string, "start": str(j * per),
                    "count": str(per), "samples": str(per), "dtden": str(DTDEN), "threads": "4", "mask": "VNC",
                    "reserved": "0", "guard": "active", "q": "40", "sums": TWB_HEAD_SUMS,
                    "rounding": TWB_HEAD_ROUNDING, "float_used": "0"}, "%s batch %d TWB_HEAD" % (spec.id, j))
        steps = tuple(canon_int(x) for x in h["steps"].split(","))
        if not steps or spec.steps[: len(steps)] != steps:
            raise StageBStop("run_steps", "%s batch %d steps %s" % (spec.id, j, h["steps"]))
        if len(lines) != 2 + 3 * len(steps):
            raise StageBStop("run_rows", "%s batch %d: %d rows" % (spec.id, j, len(lines)))
        hv = str(engine_h(spec.N))
        for r, step in enumerate(steps):
            tw = fields_dict(parse_row(lines[1 + 3 * r], "TWENS", TWENS_KEYS)[1])
            tb = fields_dict(parse_row(lines[2 + 3 * r], "TWB", TWB_KEYS)[1])
            ro = fields_dict(parse_row(lines[3 + 3 * r], "TWB_ROUND", ROUND_KEYS)[1])
            meta = {"N": str(spec.N), "delta": spec.delta, "y": spec.y, "dtden": str(DTDEN), "step": str(step),
                    "n": str(per), "float_used": "0"}
            _expect(tw, dict(meta, u="1", samples=str(per), seed=seed, variant="VN", h=hv, ctrl="0:0:0"),
                    "%s batch %d TWENS" % (spec.id, j))
            _expect(tb, dict(meta, u="1", seed=seed, start=str(j * per), count=str(per), variant="VNC", init="sharp",
                             seeds="vac", kappa="1", phase="fixed", h=hv, ctrl="0:0:0"),
                    "%s batch %d TWB" % (spec.id, j))
            _expect(ro, dict(meta, seed=seed, start=str(j * per), count=str(per), variant="VNC", units=ROUND_UNITS),
                    "%s batch %d TWB_ROUND" % (spec.id, j))
            for k in S_NAMES + Q_NAMES:
                if tw[k] != tb[k]:
                    raise StageBStop("run_legacy", "%s batch %d step %d: TWENS %s differs from TWB" % (spec.id, j,
                                                                                                    step, k))
            for k in X_NAMES + E_NAMES + S_NAMES + Q_NAMES:
                canon_int(tb[k])
            for k in RB_NAMES:
                if canon_int(ro["rb_" + k]) < 0:
                    raise StageBStop("run_round", "negative bound")
            canon_int(ro["eps_max"])
            rec = {k: canon_int(tb[k]) for k in KEEP}
            for k in KEEP_RB:
                rec["rb_" + k] = canon_int(ro["rb_" + k])
            b.rec[step] = rec
        dn = fields_dict(parse_row(lines[-1], "TWB_DONE", DONE_KEYS)[1])
        _expect(dn, {"n": str(per), "records": str(len(steps)), "mask": "VNC", "float_used": "0"},
                "%s batch %d TWB_DONE" % (spec.id, j))
        b.steps = steps
        if err_path is not None:
            el = read_lines(err_path)
            if len(el) != 1:
                raise StageBStop("run_stderr", "%s batch %d: %d stderr rows" % (spec.id, j, len(el)))
            m = fields_dict(parse_row(el[0], "TWB_MEMO", MEMO_KEYS)[1])
            if m["count"] != str(per) or m["per_sample"] != "VNC":
                raise StageBStop("run_stderr", "%s batch %d TWB_MEMO" % (spec.id, j))
            b.memo = m
    except (RowError, ExactError, KeyError) as e:
        raise StageBStop("run_rows", "%s batch %d: %s" % (spec.id, j, e)) from e
    return b


class Run:
    """The read batches of one run point, pooled per record."""

    def __init__(self, spec):
        self.spec = spec
        self.batches = []
        self.lost = []
        self.steps = ()
        self.not_measured = ()

    def _need(self, step):
        if step not in self.steps:
            raise StageBStop("not_measured_record", "%s step %d" % (self.spec.id, step))

    def per_batch(self, step):
        self._need(step)
        return [b.rec[step] for b in self.batches]

    def pooled(self, step):
        rs = self.per_batch(step)
        return {k: sum(r[k] for r in rs) for k in rs[0]}

    def M(self):
        return self.spec.per_batch * len(self.batches)

    def mean_br(self, step):
        """E[br] estimate at 2^-40 units removed: (mean, batch-means SE^2) in units of B_W/N."""
        rs = self.per_batch(step)
        m, se2 = batch_means([r["br"] for r in rs], [r["n"] for r in rs])
        sc = fr(1, 1 << 40)
        return m * sc, se2 * sc * sc

    def moment2(self, step):
        """E[|B_W/N|^2] estimate: (mean, batch-means SE^2)."""
        rs = self.per_batch(step)
        m, se2 = batch_means([r["br2"] + r["bi2"] for r in rs], [r["n"] for r in rs])
        sc = fr(1, 1 << 80)
        return m * sc, se2 * sc * sc

    def nstar(self, step):
        """n* = (S2/M)/|Bbar|^2_u - 1 with |Bbar|^2_u = (|Sum B|^2 - Sum |B|^2)/(M(M-1)); batch jackknife SE^2.

        (None, None) when |Bbar|^2_u <= 0 for the whole set or any leave-one-out set: n* is then not estimable."""
        rs = self.per_batch(step)
        if nstar_of(rs) is None or any(nstar_of(rs[:j] + rs[j + 1 :]) is None for j in range(len(rs))):
            return None, None
        return jackknife(nstar_of, rs)


def nstar_of(rs):
    m = sum(r["n"] for r in rs)
    sb_r = sum(r["br"] for r in rs)
    sb_i = sum(r["bi"] for r in rs)
    s2 = sum(r["br2"] + r["bi2"] for r in rs)
    bbar2_u = div(sb_r * sb_r + sb_i * sb_i - s2, m * (m - 1))
    if bbar2_u <= 0:
        return None
    return div(div(s2, m), bbar2_u) - 1


def load_run(run_dir, spec, require_err=True):
    """Read run_dir/<id>.<j>.hbp (and .err) for j = 0..63."""
    run = Run(spec)
    pat = re.compile(re.escape(spec.id) + r"\.(0|[1-9][0-9]*)\.(hbp|err)\Z")
    present = {}
    for nm in sorted(os.listdir(run_dir)):
        m = pat.match(nm)
        if m:
            present.setdefault(int(m.group(1)), set()).add(m.group(2))
    extra = [j for j in present if j >= spec.batches]
    missing = [j for j in range(spec.batches) if j not in present or "hbp" not in present[j]]
    if extra:
        raise StageBStop("run_extra_batch", "%s: %s" % (spec.id, extra[:4]))
    if missing:
        raise StageBStop("run_dropped_batch", "%s: %s" % (spec.id, missing[:4]))
    for j in range(spec.batches):
        p = os.path.join(run_dir, "%s.%d.hbp" % (spec.id, j))
        e = os.path.join(run_dir, "%s.%d.err" % (spec.id, j))
        if require_err and not os.path.exists(e):
            raise StageBStop("run_stderr", "%s batch %d: no .err" % (spec.id, j))
        b = parse_batch(p, e if os.path.exists(e) else None, spec, j)
        if b is None:
            run.lost.append((j, "engine_stop_empty"))
        else:
            run.batches.append(b)
    if not run.batches:
        run.not_measured = spec.steps
        return run
    k = min(len(b.steps) for b in run.batches)
    run.steps = spec.steps[:k]
    run.not_measured = spec.steps[k:]
    return run


def load_runs(run_dir, ids=("R1", "R2", "R3", "R4"), table=RUN_POINTS):
    return {i: load_run(run_dir, table[i]) for i in ids}
