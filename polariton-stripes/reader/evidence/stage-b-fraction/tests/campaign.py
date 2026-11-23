"""A synthetic campaign: every input stage B reads, fabricated in the formats of a real run, with no engine.

    python3 -I campaign.py --out DIR

writes DIR/agg/P01..P14/<call>.hbp (stage A blocks of AGG-FORMAT.md with the run script's trailer line, one file per
call of the point table) and <call>.eng.err (the engine's stderr, empty), the side files of P08 and P13, a SHA256SUMS
per point, DIR/run/R1..R4.<j>.hbp, .err and .rc (the 64 batches of each run point), DIR/QE.hbp, DIR/QE-COST.hbp and
DIR/QE-RC.hbp (the 15 QE commands, QR1-QR5, and the wrapper's receipt) and DIR/GUARD.hbp (one line per guarded
command).

The values are small fabricated integers, internally consistent where stage B checks them: each call's AGG_END hash
and nl_sha256, the AGG_VR, AGG_SUM, AGG_BLK and AGG_CMP identities, the point table, the seeds and the stream
hashes. Counts and sums are set from the frozen Pi, rho and B16 values and from the linear law, so most reads have
data to decide on. None of it is an engine value."""

import hashlib
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(HERE))

from stripes_read_b import common as c  # noqa: E402
from stripes_read_b import frozen  # noqa: E402
from stripes_read_b import qe as qe_mod  # noqa: E402
from stripes_read_b import rows_e_mom as m  # noqa: E402
from stripes_read_b import rows_e_sym as e  # noqa: E402
from stripes_read_b import runs as runs_mod  # noqa: E402
from stripes_read_b import series  # noqa: E402
from stripes_read_b.exact import dec, fr, ipow, parse_rat, rat_text  # noqa: E402

M = c.COUNT
Q = 1 << 60
VNC = "VNC"
LK_EXCH = 51
LK_KLEIN = 172


def floor_fr(x):
    x = fr(x)
    return x.numerator // x.denominator


def ceil_fr(x):
    x = fr(x)
    return -((-x.numerator) // x.denominator)


def row(kind, pairs):
    return "|".join([kind] + ["%s=%s" % (k, v) for k, v in pairs] + ["json=0"])


def sha(text):
    return hashlib.sha256(text.encode("ascii")).hexdigest()


# ---------------------------------------------------------------------------------------------------------------------
# The model: per (point, record, variant) the Pi, rho, sector deviation and discordance of the reads.

_LAW = {}


def law(spec_delta, sigma, t):
    key = (spec_delta, sigma, t)
    if key not in _LAW:
        _LAW[key] = series.Law(parse_rat(spec_delta), sigma, t)
    return _LAW[key]


def law_rho(spec, step):
    y = parse_rat(spec.y)
    if y == 0:
        return fr(0)
    r = law(spec.delta, spec.N * y * y, c.t_of_step(step)).rho().mid()
    return fr(floor_fr(r * 1000000000), 1000000000)


def model(pid, step, v, par):
    spec = c.DUMP_POINTS[pid]
    t = step // 64
    t12 = min(t, 2)
    alt = 1 if par == 0 else -1
    p = {"pi": fr(0), "rho": fr(0), "dev": fr(0), "disc": fr(3, 10) if v in ("FLIP", "LOCK") else fr(1, 100),
         "scale": 1 + fr(alt, 1000), "s2ps": Q + alt * (Q >> 10)}
    if v == "MODE0":
        p["disc"] = fr(0)
    if parse_rat(spec.y) != 0:
        p["rho"] = law_rho(spec, step)
        p["pi"] = fr(1, 100)
    if pid in m.E10_PI:
        p["pi"] = dec(m.E10_PI[pid][t12 - 1])
    if pid in m.E11_PI:
        p["pi"] = dec(m.E11_PI[pid][t12 - 1])
    if pid == "P10":
        p["pi"] = dec("0.233911") if t == 1 else fr(26, 100)
        p["dev"] = fr(1, 100)
    if (pid, v) in m.E15_PI:
        p["pi"] = dec(m.E15_PI[(pid, v)][t12 - 1])
    if v == VNC and pid in m.E13_RHO and t <= 2:
        p["rho"] = dec(m.E13_RHO[pid][t - 1])
    if v in (VNC, "MODE0") and pid in ("P03", "P04", "P05", "P06", "P08"):
        p["dev"] = fr(3, 1000)
    return p


def atoms_of(spec, third):
    """AGG_ATOMS counts of a call: one non-LOCK exchange atom in every third call, a fixed LOCK count."""
    nx = 1 if third else 0
    return {"nl_klein": nx, "nl_exch": nx, "lk_klein": LK_KLEIN, "lk_exch": LK_EXCH}


def variant_atoms(spec, v, at):
    y0 = parse_rat(spec.y) == 0
    if v == "LOCK":
        return (at["lk_klein"] if y0 else at["lk_exch"]), at["lk_exch"]
    return (at["nl_klein"] if y0 else at["nl_exch"]), at["nl_exch"]


def vr_block(pi, dev, atoms, xatoms, lock_q=None):
    mp = M - atoms
    apos, aneg = (atoms + 1) // 2, atoms // 2
    d = floor_fr(2 * pi * M) - (apos - aneg)
    pos = (mp + d) // 2
    neg = mp - pos
    if lock_q is not None:
        sec = [floor_fr(mp * q) for q in lock_q]
    else:
        base = mp // 16
        sec = [base] * 16
        k = floor_fr(dev * mp)
        for j, sg in ((0, 1), (15, 1), (7, -1), (8, -1)):  # a first harmonic, symmetric under the mirror k -> 15-k
            sec[j] += sg * k
    amb = mp - sum(sec)
    return {"M": M, "atoms": atoms, "xatoms": xatoms, "xatom_bi_nz": 0, "mp": mp, "na_bi0": 0, "sec": sec, "amb": amb,
            "br_pos": pos, "br_neg": neg, "br_amb": 0, "bi_pos": mp // 2, "bi_neg": mp - mp // 2, "bi_amb": 0,
            "at_br_pos": apos, "at_br_neg": aneg, "at_br_amb": 0, "at_bi_pos": 0, "at_bi_neg": 0, "at_bi_amb": atoms}


def sum_all(rho, scale, s2ps):
    s2 = M * s2ps
    br = 0 if rho == 0 else floor_fr(math.isqrt(s2 + floor_fr(rho * (M - 1) * s2)) * fr(scale))
    return {"m": M, "br": br, "bi": 0, "br2": s2, "bi2": 0, "brbi": 0, "bbr": 4 * M, "bbi": 0, "bbr2": 16 * M,
            "bbi2": 0}


def sum_atom(atoms, s2ps):
    return {"m": atoms, "br": atoms * math.isqrt(s2ps), "bi": 0, "br2": atoms * s2ps, "bi2": 0, "brbi": 0,
            "bbr": 4 * atoms, "bbi": 0, "bbr2": 16 * atoms, "bbi2": 0}


def blk(s2tot, rho, n):
    k = M // n
    z = 1 + (n - 1) * rho
    s2 = floor_fr(z * s2tot)
    var = (1 - rho) * (1 - rho) + 2 * n * rho * (1 - rho)
    s4 = ceil_fr((s2 * s2 + var * s2tot * s2tot * (k - 1) * fr(1, k)) * fr(1, k))
    w2 = s2tot * s2tot // k
    return {"K": k, "s2": s2, "s4": s4, "w": s2tot, "w2": w2, "sw": floor_fr(z * w2)}


def cmp_block(vv, ref, disc, common):
    delta = vv["br_pos"] - ref["br_pos"]
    d = max(floor_fr(disc * common), abs(delta))
    if (d - delta) % 2:
        d += 1
    t1, t3 = (d + delta) // 2, (d - delta) // 2
    pos = min(vv["br_pos"], common)
    t0, t4 = pos - t1, common - pos - t3
    if min(t0, t4) < 0:
        raise ValueError("campaign: negative AGG_CMP cell")
    return {"common": common, "br": [t0, t1, 0, t3, t4, 0, 0, 0, 0], "bi": [common] + [0] * 8, "cert2": common,
            "mis": 0, "cert2_big_both": common, "mis_big_both": 0, "cert2_big_any": common, "mis_big_any": 0}


def nl_row(spec, step):
    y = parse_rat(spec.y)
    br = 0 if y == 0 else floor_fr(law(spec.delta, spec.N * y * y, c.t_of_step(step)).EB.mid() * (1 << 40))
    pairs = [("N", spec.N), ("delta", spec.delta), ("u", 1), ("y", spec.y), ("dtden", c.DTDEN), ("step", step),
             ("init", "c0=sqrt(N),c+-=0"), ("kappa", 1)]
    pairs += [(k, 0) for k in ("zr", "zi", "z2", "xw", "xnc", "f", "fcl")]
    pairs += [("br", br), ("bi", 0)]
    pairs += [(k, 3) for k in ("rb_zr", "rb_zi", "rb_z2", "rb_xw", "rb_xnc", "rb_f", "rb_fcl", "rb_br", "rb_bi")]
    pairs += [("eps", 5), ("reads", c.TWB_NL_READS), ("at", "2^40"), ("float_used", 0)]
    return row("TWB_NL", pairs)


# ---------------------------------------------------------------------------------------------------------------------
# One call's block.


def twb_head(spec, call, steps):
    pairs = [("engine", "twens"), ("version", c.TWENS_VERSION), ("cli", "dump"),
             ("binary_sha256", c.TWENS_BINARY_SHA256), ("source_sha256", c.TWENS_SOURCE_SHA256), ("N", spec.N),
             ("delta", spec.delta), ("u", 1), ("y", spec.y), ("seed", c.seed_u64(spec.seed_string)),
             ("seed_string", spec.seed_string), ("start", M * call), ("count", M), ("samples", M),
             ("dtden", c.DTDEN), ("threads", 1), ("steps", ",".join(map(str, steps))), ("mask", spec.mask(call)),
             ("reserved", 0), ("guard", "active"), ("q", 40), ("sums", c.TWB_HEAD_SUMS),
             ("rounding", c.TWB_HEAD_ROUNDING), ("float_used", 0)]
    return row("TWB_HEAD", pairs)


def side_bytes(spec, call, variants, steps, at):
    srec = [s for s in steps if s in (64, 128)]
    vmask = sum(1 << c.VARIANTS.index(v) for v in variants)
    head = b"STRPSIDE" + struct.pack("<6I", 1, len(variants), vmask, len(srec), *((srec + [0, 0])[:2]))
    head += struct.pack("<2Q", M * call, M) + bytes(16)
    body = []
    nvals = len(variants) * len(srec)
    for k in range(M):
        flags = (3 if k < at["nl_exch"] else 0) | (4 if k < at["lk_klein"] else 0) | (8 if k < at["lk_exch"] else 0)
        br = ((k * 7919) % 2001 - 1000) << 20
        body.append(struct.pack("<Q" + "qQ" * nvals, flags, *([br, 16] * nvals)))
    return head + b"".join(body)


def call_block(spec, call, steps, side_name=None, side_data=None):
    """The stage A block of one call as text (with AGG_END), and the side file bytes when the call writes one."""
    all_v = call < spec.all
    variants = c.VARIANTS if all_v else (VNC,)
    par = call % 2
    third = call % 3 == 0
    at = atoms_of(spec, third)
    pc = [("point", spec.id), ("call", call)]
    y0 = parse_rat(spec.y) == 0
    nl = [nl_row(spec, s) for s in steps] if all_v else []
    rows = [None, "AGG_TWB_HEAD|" + twb_head(spec, call, steps)]
    rows.append(row("AGG_CALL", pc + [
        ("N", spec.N), ("delta", spec.delta), ("u", 1), ("y", spec.y), ("y_zero", 1 if y0 else 0),
        ("seed", c.seed_u64(spec.seed_string)), ("seed_string", spec.seed_string), ("start", M * call), ("count", M),
        ("dtden", c.DTDEN), ("h", c.engine_h(spec.N)), ("steps", ",".join(map(str, steps))), ("records", len(steps)),
        ("mask", spec.mask(call)), ("variants", ",".join(variants)), ("nl", 1 if all_v else 0),
        ("ctrl", ";".join(["0:0:0"] * len(steps))),
        ("nl_sha256", sha("".join(x + "\n" for x in nl)) if all_v else "none")]))
    rows.append(row("AGG_ATOMS", pc + [("M", M)] + [(k, at[k]) for k in ("nl_klein", "nl_exch", "lk_klein",
                                                                          "lk_exch")]))
    lock_atoms = at["lk_klein"] if y0 else at["lk_exch"]
    edge = 0 if y0 else at["lk_klein"] - at["lk_exch"]
    rest = M - lock_atoms - edge
    lat = [rest // 16] * 16
    lat[0] += rest - sum(lat)
    rows.append(row("AGG_LAT", pc + [("lock_atoms", lock_atoms), ("lat_edge", edge),
                                     ("lat", ":".join(map(str, lat)))]))
    lq = LOCK_Q if y0 else None
    for step in steps:
        ref = None
        ref_atoms = None
        for v in variants:
            p = model(spec.id, step, v, par)
            atoms, xatoms = variant_atoms(spec, v, at)
            vr = vr_block(p["pi"], p["dev"], atoms, xatoms, lq if v == "LOCK" else None)
            sp = [("step", step), ("variant", v)]
            rows.append(row("AGG_VR", pc + sp + [(k, ":".join(map(str, vr[k])) if k == "sec" else vr[k])
                                                 for k in c.AGG_KEYS["AGG_VR"][4:]]))
            sa = sum_all(p["rho"], p["scale"], p["s2ps"])
            st = sum_atom(atoms, p["s2ps"])
            for name, s in (("all", sa), ("atom", st)):
                rows.append(row("AGG_SUM", pc + sp + [("set", name)] + [(k, s[k]) for k in c.AGG_KEYS["AGG_SUM"][5:]]))
            for n in c.BLOCK_SIZES:
                b = blk(sa["br2"], p["rho"], n)
                rows.append(row("AGG_BLK", pc + sp + [("n", n)] + [(k, b[k]) for k in ("K", "s2", "s4", "w", "w2",
                                                                                         "sw")]))
            if v == VNC:
                ref, ref_atoms = vr, atoms
            else:
                common = M - max(atoms, ref_atoms)
                cm = cmp_block(vr, ref, p["disc"], common)
                rows.append(row("AGG_CMP", pc + sp + [("ref", VNC), ("common", cm["common"]),
                                                      ("br", ":".join(map(str, cm["br"]))),
                                                      ("bi", ":".join(map(str, cm["bi"])))]
                                + [(k, cm[k]) for k in ("cert2", "mis", "cert2_big_both", "mis_big_both",
                                                        "cert2_big_any", "mis_big_any")]))
            if v == "LOCK":
                rows.append(row("AGG_LOCK", pc + [("step", step), ("cert", vr["mp"] - vr["amb"]), ("mis", 0)]))
        if all_v:
            rows.append("AGG_NL|" + nl[steps.index(step)])
    side = None
    if spec.side and all_v:
        side = side_bytes(spec, call, variants, steps, at)
        srec = [s for s in steps if s in (64, 128)]
        rows.append(row("AGG_SIDE", pc + [("path", side_name), ("bytes", len(side)),
                                          ("sha256", hashlib.sha256(side).hexdigest()), ("indices", M),
                                          ("variants", ",".join(variants)),
                                          ("steps", ",".join(map(str, srec)) or "none")]))
    nv = len(variants)
    rows.append(row("AGG_CHECK", pc + [("samples", M), ("starts", M * nv), ("lin", M * nv * len(steps)),
                                       ("rows", 20 * len(steps)), ("fields", 600 * len(steps)),
                                       ("result", "all_equal")]))
    h = sha("campaign:%s:%d" % (spec.id, call))
    rows[0] = row("AGG_HEAD", [("reader", c.READER_A), ("reader_version", c.READER_A_VERSION)] + pc + [
        ("table", "checked"), ("stdin_bytes", 1000000 + call), ("stdin_lines", 10000 + call), ("stdin_sha256", h)])
    body = "".join(x + "\n" for x in rows)
    end = row("AGG_END", pc + [("agg_lines", len(rows)), ("agg_sha256", sha(body))])
    return body + end + "\n", side


def write(path, data):
    with open(path, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode("ascii"))


def make_point(root, pid, steps=None):
    spec = c.DUMP_POINTS[pid]
    d = os.path.join(root, "agg", pid)
    os.makedirs(d, exist_ok=True)
    steps = list(spec.steps if steps is None else steps)
    cache = {}
    for call in range(spec.calls):
        side_name = "agg/%s/%d.side" % (pid, call)
        all_v = call < spec.all
        key = (all_v, call % 2, call % 3 == 0)
        if all_v or key not in cache:
            text, side = call_block(spec, call, steps, side_name)
            if not all_v:
                cache[key] = (text, call)
        else:
            text0, call0 = cache[key]
            text, side = rebase(text0, spec, call0, call), None
        write(os.path.join(d, "%d.hbp" % call), text + "rc=0 rc_reader=0\n")
        write(os.path.join(d, "%d.eng.err" % call), "")
        if side is not None:
            write(os.path.join(d, "%d.side" % call), side)
    c.write_sha256sums(d)


ENGINE_FAULT = "TWB_FAULT|reason=rounding_bound_hL_above_1/2|json=0\n"


def engine_stop_call(pid, call):
    """What the run script files for a dump call whose engine stopped: stage A's empty_stream STOP and both exit
    codes (<call>.hbp), and the engine's TWB_FAULT row (<call>.eng.err)."""
    e = hashlib.sha256(b"").hexdigest()
    return ("STOP|reader=stripes-read-a|reader_version=0.1.0|point=%s|call=%d|reason=empty_stream|line=0|detail=none"
            "|stdin_bytes=0|stdin_lines=0|stdin_sha256=%s|json=0\nrc=4 rc_reader=3\n" % (pid, call, e)), ENGINE_FAULT


def rebase(text, spec, call0, call):
    """A VNC-only block of call0 moved to call: its call, start and stream fields, then a new AGG_END."""
    lines = text.split("\n")[:-1]
    out = []
    a, b = "|point=%s|call=%d|" % (spec.id, call0), "|point=%s|call=%d|" % (spec.id, call)
    for ln in lines[:-1]:
        ln = ln.replace(a, b)
        if ln.startswith("AGG_HEAD|"):
            ln = row("AGG_HEAD", [("reader", c.READER_A), ("reader_version", c.READER_A_VERSION),
                                  ("point", spec.id), ("call", call), ("table", "checked"),
                                  ("stdin_bytes", 1000000 + call), ("stdin_lines", 10000 + call),
                                  ("stdin_sha256", sha("campaign:%s:%d" % (spec.id, call)))])
        elif ln.startswith("AGG_TWB_HEAD|"):
            steps = [int(x) for x in ln.split("|steps=")[1].split("|")[0].split(",")]
            ln = "AGG_TWB_HEAD|" + twb_head(spec, call, steps)
        elif ln.startswith("AGG_CALL|"):
            ln = ln.replace("|start=%d|" % (M * call0), "|start=%d|" % (M * call))
        out.append(ln)
    body = "".join(x + "\n" for x in out)
    return body + row("AGG_END", [("point", spec.id), ("call", call), ("agg_lines", len(out)),
                                  ("agg_sha256", sha(body))]) + "\n"


# ---------------------------------------------------------------------------------------------------------------------
# Runs R1-R4.


def make_run(root, rid):
    spec = c.RUN_POINTS[rid]
    d = os.path.join(root, "run")
    os.makedirs(d, exist_ok=True)
    n = spec.per_batch
    seed = c.seed_u64(spec.seed_string)
    hv = c.engine_h(spec.N)
    y = parse_rat(spec.y)
    for j in range(spec.batches):
        alt = 1 if j % 2 == 0 else -1
        lines = [row("TWB_HEAD", [
            ("engine", "twens"), ("version", c.TWENS_VERSION), ("cli", "run"), ("binary_sha256", c.TWENS_BINARY_SHA256),
            ("source_sha256", c.TWENS_SOURCE_SHA256), ("N", spec.N), ("delta", spec.delta), ("u", 1), ("y", spec.y),
            ("seed", seed), ("seed_string", spec.seed_string), ("start", j * n), ("count", n), ("samples", n),
            ("dtden", c.DTDEN), ("threads", 4), ("steps", ",".join(map(str, spec.steps))), ("mask", VNC),
            ("reserved", 0), ("guard", "active"), ("q", 40), ("sums", c.TWB_HEAD_SUMS),
            ("rounding", c.TWB_HEAD_ROUNDING), ("float_used", 0)])]
        for step in spec.steps:
            lw = law(spec.delta, spec.N * y * y, c.t_of_step(step))
            ns = lw.nstar().mid()
            mu = math.isqrt(floor_fr(fr(Q, 1 + ns)))
            vals = dict.fromkeys(runs_mod.S_NAMES + runs_mod.Q_NAMES + runs_mod.X_NAMES + runs_mod.E_NAMES, 0)
            vals["br"] = floor_fr(n * mu * (1 + fr(alt, 100)))
            vals["br2"] = n * (Q + alt * (Q >> 10))
            meta = [("N", spec.N), ("delta", spec.delta), ("u", 1), ("y", spec.y)]
            lines.append(row("TWENS", meta + [("samples", n), ("seed", seed), ("dtden", c.DTDEN), ("step", step),
                                              ("variant", "VN"), ("n", n), ("h", hv), ("ctrl", "0:0:0")]
                             + [(k, vals[k]) for k in runs_mod.S_NAMES + runs_mod.Q_NAMES] + [("float_used", 0)]))
            lines.append(row("TWB", meta + [("seed", seed), ("start", j * n), ("count", n), ("dtden", c.DTDEN),
                                            ("step", step), ("variant", VNC), ("init", "sharp"), ("seeds", "vac"),
                                            ("kappa", 1), ("phase", "fixed"), ("n", n), ("h", hv), ("ctrl", "0:0:0")]
                             + [(k, vals[k]) for k in runs_mod.S_NAMES + runs_mod.Q_NAMES + runs_mod.X_NAMES
                                + runs_mod.E_NAMES] + [("float_used", 0)]))
            rb = dict.fromkeys(runs_mod.RB_NAMES, 0)
            rb["br"] = 4 * n
            lines.append(row("TWB_ROUND", [("N", spec.N), ("delta", spec.delta), ("y", spec.y), ("seed", seed),
                                           ("start", j * n), ("count", n), ("dtden", c.DTDEN), ("step", step),
                                           ("variant", VNC), ("n", n)]
                             + [("rb_" + k, rb[k]) for k in runs_mod.RB_NAMES]
                             + [("eps_max", 7), ("units", runs_mod.ROUND_UNITS), ("float_used", 0)]))
        lines.append(row("TWB_DONE", [("n", n), ("records", len(spec.steps)), ("mask", VNC), ("float_used", 0)]))
        write(os.path.join(d, "%s.%d.hbp" % (rid, j)), "".join(x + "\n" for x in lines))
        memo = [("count", n), ("per_sample", VNC)] + [(k, 0) for k in runs_mod.MEMO_KEYS[2:]]
        write(os.path.join(d, "%s.%d.err" % (rid, j)), row("TWB_MEMO", memo) + "\n")
        write(os.path.join(d, "%s.%d.rc" % (rid, j)), "rc=0\n")


# ---------------------------------------------------------------------------------------------------------------------
# QE commands QR1-QR5 and the guard lines.


def qe_rows(cmd, t):
    n = cmd.N
    y, tt = parse_rat(cmd.y), parse_rat(t)
    lw = law(cmd.delta, n * y * y, tt)
    b = 0 if y == 0 else floor_fr(lw.EB.mid() * ipow(10, 18))
    qw = lw.EB2.mid()
    c2 = max(1, floor_fr(2 * (qw - fr(1, 4)) * fr(1, n * (n - 1)) * ipow(10, 18)))
    even = (n // 2 + 1) * (n + 1)
    ab = even * qe_mod.POINT_BYTES_PER_STATE if cmd.mode == "point" else (n // 2 + 1) * qe_mod.SECTOR_BYTES_PER_STATE
    v = dict.fromkeys(qe_mod.INT_KEYS, 0)
    v.update({"c": 1, "E": 2, "degree": 40, "reach": 12, "applies": 300, "elem_err_units": 9, "B_e18": b,
              "D2_e18": floor_fr(fr(2 * b, n)), "C2_e18": c2, "eps_e18": 1000, "norm_B_s20": n << 19})
    pairs = [("N", n), ("K", n), ("even_states", even), ("array_bytes", ab), ("u", 1),
             ("x", rat_text(parse_rat(cmd.delta) - 1)), ("y", cmd.y), ("delta", cmd.delta), ("t", t),
             ("window", "2^-%d" % qe_mod.W)] + [(k, v[k]) for k in qe_mod.INT_KEYS] + [("float_used", 0)]
    read = row(qe_mod.READ_KIND, pairs)
    cost = [("N", n), ("K", n), ("even_states", even), ("array_bytes", ab), ("delta", cmd.delta), ("y", cmd.y),
            ("t", t), ("ms", 5), ("peak_rss_kB", 4096)]
    if cmd.mode == "sector":
        cost.append(("layout", "sector"))
    return read, row(qe_mod.COST_KIND, cost)


def make_qe(root):
    reads, costs = [], []
    for cmd in qe_mod.PLAN:
        for t in cmd.times:
            r, k = qe_rows(cmd, t)
            reads.append(r)
            costs.append(k)
    write(os.path.join(root, "QE.hbp"), "".join(x + "\n" for x in reads))
    write(os.path.join(root, "QE-COST.hbp"), "".join(x + "\n" for x in costs))
    write(os.path.join(root, "QE-RC.hbp"), qe_rc_text())


def qe_rc_text(rcs=None):
    """QE-RC.hbp as the wrapper files it: the QE binary's sha256, then each command's rc after it ran."""
    rcs = rcs or {}
    return row(qe_mod.BINARY_KIND, [("sha256", qe_mod.LANE_BINARY_SHA256)]) + "\n" + "".join(
        row(qe_mod.RC_KIND, [("argv", qe_mod.argv_text(cmd)), ("rc", rcs.get(qe_mod.argv_text(cmd), 0))]) + "\n"
        for cmd in qe_mod.PLAN)


def guard_triples():
    """One line per guarded command, in run order: each QE command, then each run point, then each dump point."""
    t = list(qe_mod.plan_guards())
    t += [(p.N, p.delta, p.y) for p in c.RUN_POINTS.values()]
    t += [(p.N, p.delta, p.y) for p in c.DUMP_POINTS.values()]
    return t


def make_guard(root):
    lines = [row("TWB_GUARD", [("N", n), ("delta", d), ("y", y), ("verdict", "allowed"), ("reason", "none"),
                               ("computed", 0)]) for n, d, y in guard_triples()]
    write(os.path.join(root, "GUARD.hbp"), "".join(x + "\n" for x in lines))


LOCK_Q = None


def make_campaign(root):
    global LOCK_Q
    LOCK_Q = e.lock_q(frozen.load())
    for pid in c.DUMP_POINTS:
        make_point(root, pid)
    for rid in c.RUN_POINTS:
        make_run(root, rid)
    make_qe(root)
    make_guard(root)
    return root


def main(argv):
    if len(argv) != 3 or argv[1] != "--out":
        sys.stderr.write(__doc__)
        return 2
    out = argv[2]
    if os.path.exists(out) and os.listdir(out):
        sys.stderr.write("campaign: %s is not empty\n" % out)
        return 2
    os.makedirs(out, exist_ok=True)
    make_campaign(out)
    n = sum(len(fs) for _, _, fs in os.walk(out))
    print(row("CAMPAIGN", [("out", out), ("files", n), ("dump_points", len(c.DUMP_POINTS)),
                           ("run_points", len(c.RUN_POINTS)), ("qe_commands", len(qe_mod.PLAN)), ("engine_runs", 0)]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
