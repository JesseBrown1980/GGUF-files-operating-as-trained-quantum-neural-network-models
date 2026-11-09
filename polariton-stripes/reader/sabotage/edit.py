"""edit.py: the planted faults of the sabotage suite (run.sh). Each command writes an edited copy of a stream, a
campaign call file or a READ file; nothing is edited in place and no engine runs.

  stream --in F --out F --op OP              OP: twb_br, round_rb_br, version_030, xatom_minus0, xatom_flip
  block  --campaign D --point P --call I --op OP [--rehash] [--sums]
                                             OP: xatom_bi_nz, swap_sec, version_030
  drop   --campaign D --point P --call I [--sums]
  read   --in F --out F --op OP              OP: promote, promote_why, falsify
  stop   --campaign D --op OP                rule STOP without its evidence (SHA256SUMS rewritten each time):
                                             dump_no_attempt, dump_block_as_attempt, dump_garbage_attempt,
                                             dump_garbage_attempt_short, dump_stop_without_fault, run_empty_no_attempt,
                                             run_truncated_no_attempt, run_crash
  qe     --campaign D --op OP                OP: panic_rc101, panic_rc0, altered_B, rc_row_missing
"""

import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "b"))

from stripes_read_b import common as c  # noqa: E402
from stripes_read_b import frozen  # noqa: E402


def read_text(path):
    with open(path, "rb") as f:
        return f.read().decode("ascii")


def replace_file(path, text):
    """A new file at path: campaign copies share inodes with their original, so a file is never written in place."""
    if os.path.exists(path):
        os.remove(path)
    with open(path, "wb") as f:
        f.write(text.encode("ascii"))


def field(line, key):
    for p in line.split("|")[1:]:
        if p.startswith(key + "="):
            return p[len(key) + 1:]
    raise KeyError(key)


def set_field(line, key, val):
    parts = line.split("|")
    for k, p in enumerate(parts):
        if k and p.startswith(key + "="):
            parts[k] = key + "=" + val
            return "|".join(parts)
    raise KeyError(key)


def edit_first(lines, pred, fn):
    for k, ln in enumerate(lines):
        if pred(ln):
            lines[k] = fn(ln)
            return lines
    raise SystemExit("edit.py: no row to edit")


# ---------------------------------------------------------------------------------------------------------------------
# Dump streams (stage A).


def exchange_atoms(lines):
    """{idx: (non-LOCK exchange atom, LOCK exchange atom)} from the TWB_DUMP_SAMPLE draws c_i = g_i / 2^35."""
    out = {}
    for ln in lines:
        if ln.startswith("TWB_DUMP_SAMPLE|"):
            g = [int(x) >> 35 for x in field(ln, "g").split(":")]
            out[field(ln, "idx")] = (g[0] == g[2] and g[1] == g[3], g[1] == 0)
    return out


def cmd_stream(a):
    lines = read_text(a["--in"]).split("\n")[:-1]
    op = a["--op"]
    if op == "twb_br":
        edit_first(lines, lambda ln: ln.startswith("TWB|"),
                   lambda ln: set_field(ln, "br", str(int(field(ln, "br")) + 1)))
    elif op == "round_rb_br":
        edit_first(lines, lambda ln: ln.startswith("TWB_ROUND|"),
                   lambda ln: set_field(ln, "rb_br", str(int(field(ln, "rb_br")) + 1)))
    elif op == "version_030":
        edit_first(lines, lambda ln: ln.startswith("TWB_HEAD|"), lambda ln: set_field(ln, "version", "0.3.0"))
    elif op in ("xatom_minus0", "xatom_flip"):
        ex = exchange_atoms(lines)

        def pick(ln):
            if not ln.startswith("TWB_DUMP_OBS|"):
                return False
            nl, lk = ex[field(ln, "idx")]
            atom = lk if field(ln, "variant") == "LOCK" else nl
            bi = int(field(ln, "bi"))
            return atom and ((bi == 0) if op == "xatom_minus0" else (bi != 0))

        edit_first(lines, pick, lambda ln: set_field(ln, "bi", "-0" if op == "xatom_minus0" else
                                                    str(-int(field(ln, "bi")))))
    else:
        raise SystemExit("edit.py: stream op " + op)
    with open(a["--out"], "wb") as f:
        f.write("".join(x + "\n" for x in lines).encode("ascii"))


# ---------------------------------------------------------------------------------------------------------------------
# Call files of a campaign (stage B).


def rehash(lines):
    """A new AGG_END for the rows before it: what a forger of the block would write."""
    body = lines[:-1]
    h = hashlib.sha256("".join(x + "\n" for x in body).encode("ascii")).hexdigest()
    return body + [set_field(set_field(lines[-1], "agg_lines", str(len(body))), "agg_sha256", h)]


def cmd_block(a):
    d = os.path.join(a["--campaign"], "agg", a["--point"])
    path = os.path.join(d, a["--call"] + ".hbp")
    lines = read_text(path).split("\n")[:-1]
    trailer, block = lines[-1], lines[:-1]
    op = a["--op"]
    if op == "xatom_bi_nz":
        def pick(ln):
            return ln.startswith("AGG_VR|") and "|step=64|variant=VNC|" in ln and int(field(ln, "xatoms")) > 0

        edit_first(block, pick, lambda ln: set_field(ln, "xatom_bi_nz", str(int(field(ln, "xatom_bi_nz")) + 1)))
    elif op == "swap_sec":
        def pick(ln):
            return ln.startswith("AGG_VR|") and len(set(field(ln, "sec").split(":"))) > 1

        def swap(ln):
            s = field(ln, "sec").split(":")
            j = next(k for k in range(1, 16) if s[k] != s[0])
            s[0], s[j] = s[j], s[0]
            return set_field(ln, "sec", ":".join(s))

        edit_first(block, pick, swap)
    elif op == "version_030":
        edit_first(block, lambda ln: ln.startswith("AGG_TWB_HEAD|"), lambda ln: set_field(ln, "version", "0.3.0"))
    else:
        raise SystemExit("edit.py: block op " + op)
    if "--rehash" in a:
        block = rehash(block)
    replace_file(path, "".join(x + "\n" for x in block + [trailer]))
    if "--sums" in a:
        os.remove(os.path.join(d, "SHA256SUMS"))
        c.write_sha256sums(d)


def cmd_drop(a):
    """Every file of the call: its block, its stderr files and its side file."""
    d = os.path.join(a["--campaign"], "agg", a["--point"])
    os.remove(os.path.join(d, a["--call"] + ".hbp"))
    for ext in (".side", ".err", ".eng.err"):
        p = os.path.join(d, a["--call"] + ext)
        if os.path.exists(p):
            os.remove(p)
    if "--sums" in a:
        os.remove(os.path.join(d, "SHA256SUMS"))
        c.write_sha256sums(d)


# ---------------------------------------------------------------------------------------------------------------------
# READ files (stage B output).


def end_row(lines):
    body = [x for x in lines if not x.startswith("STRIPES_READ_END|")]
    h = hashlib.sha256("".join(x + "\n" for x in body).encode("ascii")).hexdigest()
    return body + ["STRIPES_READ_END|rows=%d|sha256=%s|json=0" % (len(body), h)]


def cmd_read(a):
    lines = read_text(a["--in"]).split("\n")[:-1]
    op = a["--op"]
    target = "STRIPES_READ|row=E17|read=pi_t1|"
    vrow = "STRIPES_VERDICT|row=E17|"
    if op in ("promote", "promote_why"):
        def promote(ln):
            ln = set_field(set_field(ln, "scored", "1"), "verdict", c.MET)
            return set_field(ln, "why", "unexposed") if op == "promote_why" else ln

        edit_first(lines, lambda ln: ln.startswith(target), promote)

        def counts(ln):
            for k in ("scored", "met"):
                ln = set_field(ln, k, str(int(field(ln, k)) + 1))
            ln = set_field(ln, "report", str(int(field(ln, "report")) - 1))
            return set_field(ln, "verdict", c.MET)

        edit_first(lines, lambda ln: ln.startswith(vrow), counts)
    elif op == "falsify":
        fals = frozen.load().predict("E17")["falsifier"]
        edit_first(lines, lambda ln: ln.startswith(vrow),
                   lambda ln: set_field(set_field(ln, "falsifier", "pi_t1:" + fals), "verdict", c.NOT_MET))
    else:
        raise SystemExit("edit.py: read op " + op)
    replace_file(a["--out"], "".join(x + "\n" for x in end_row(lines)))


# ---------------------------------------------------------------------------------------------------------------------
# Rule STOP without its evidence (the review's probes A, B and C, and the run batches).

FAULT = "TWB_FAULT|reason=rounding_bound_hL_above_1/2|json=0\n"


def _stage_b_tests():
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "b", "tests"))
    import campaign  # noqa: E402

    campaign.LOCK_Q = campaign.e.lock_q(frozen.load())
    return campaign


def _resum(d):
    os.remove(os.path.join(d, "SHA256SUMS"))
    c.write_sha256sums(d)


def cmd_stop(a):
    root, op = a["--campaign"], a["--op"]
    if op.startswith("dump_"):
        camp = _stage_b_tests()
        d = os.path.join(root, "agg", "P05")
        short, _ = camp.call_block(c.DUMP_POINTS["P05"], 7, [64, 128, 192], "agg/P05/7.side")
        short += "rc=0 rc_reader=0\n"
        stop_text, _ = camp.engine_stop_call("P05", 7)
        if op == "dump_no_attempt":  # probe A: a record dropped with no exit 4 filed
            replace_file(os.path.join(d, "7.hbp"), short)
        elif op == "dump_block_as_attempt":  # probe B: the complete block filed as the attempt, a shorter rerun kept
            os.rename(os.path.join(d, "7.hbp"), os.path.join(d, "7.attempt1.hbp"))
            replace_file(os.path.join(d, "7.attempt1.eng.err"), FAULT)
            replace_file(os.path.join(d, "7.hbp"), short)
        elif op in ("dump_garbage_attempt", "dump_garbage_attempt_short"):  # probe C: an attempt that is not a row
            replace_file(os.path.join(d, "7.attempt1.hbp"), "anything\n")
            replace_file(os.path.join(d, "7.attempt1.eng.err"), FAULT)
            if op.endswith("_short"):
                replace_file(os.path.join(d, "7.hbp"), short)
        elif op == "dump_stop_without_fault":  # every try filed, but the engine's stderr of the last one is empty
            for k in (1, 2, 3):
                replace_file(os.path.join(d, "7.attempt%d.hbp" % k), stop_text)
                replace_file(os.path.join(d, "7.attempt%d.eng.err" % k), FAULT)
            replace_file(os.path.join(d, "7.hbp"), stop_text)
            replace_file(os.path.join(d, "7.eng.err"), "")
        else:
            raise SystemExit("edit.py: stop op " + op)
        _resum(d)
        return
    d = os.path.join(root, "run")
    if op == "run_empty_no_attempt":
        replace_file(os.path.join(d, "R2.5.hbp"), "")
        replace_file(os.path.join(d, "R2.5.err"), FAULT)
        replace_file(os.path.join(d, "R2.5.rc"), "rc=4\n")
    elif op == "run_truncated_no_attempt":
        lines = read_text(os.path.join(d, "R2.5.hbp")).split("\n")[:-1]
        head = set_field(lines[0], "steps", "32,64")
        done = set_field(lines[-1], "records", "2")
        replace_file(os.path.join(d, "R2.5.hbp"), "".join(x + "\n" for x in [head] + lines[1:7] + [done]))
    elif op == "run_crash":
        replace_file(os.path.join(d, "R2.5.hbp"), "")
        replace_file(os.path.join(d, "R2.5.err"), "")
        replace_file(os.path.join(d, "R2.5.rc"), "rc=137\n")
    else:
        raise SystemExit("edit.py: stop op " + op)


# ---------------------------------------------------------------------------------------------------------------------
# QE receipts.

PANIC = ("thread 'main' panicked at src/bin/polariton_first_correction.rs:1967:57:\nre\n"
         "note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\n")


def cmd_qe(a):
    root, op = a["--campaign"], a["--op"]
    qe_p, cost_p, rc_p = (os.path.join(root, x) for x in ("QE.hbp", "QE-COST.hbp", "QE-RC.hbp"))
    reads = read_text(qe_p).split("\n")[:-1]
    costs = read_text(cost_p).split("\n")[:-1]
    rcs = read_text(rc_p).split("\n")[:-1]
    if op in ("panic_rc101", "panic_rc0"):  # the 6561 sector command panics after its t=2 row
        k = [i for i, r in enumerate(reads) if "|N=6561|" in r and "|t=4|" in r][0]
        replace_file(qe_p, "".join(x + "\n" for i, x in enumerate(reads) if i != k))
        replace_file(cost_p, "".join(x + "\n" + (PANIC if i + 1 == k else "") for i, x in enumerate(costs) if i != k))
        if op == "panic_rc101":
            j = [i for i, r in enumerate(rcs) if "|argv=sector_6561_" in r][0]
            rcs[j] = set_field(rcs[j], "rc", "101")
            replace_file(rc_p, "".join(x + "\n" for x in rcs))
    elif op == "altered_B":  # B at (81, -1/54, t=2) moved by 10^-5: the parity of Q02 breaks
        k = [i for i, r in enumerate(reads) if "|N=81|" in r and "|y=-1/54|" in r and "|t=2|" in r][0]
        reads[k] = set_field(reads[k], "B_e18", str(int(field(reads[k], "B_e18")) + 10000000000000))
        replace_file(qe_p, "".join(x + "\n" for x in reads))
    elif op == "rc_row_missing":
        replace_file(rc_p, "".join(x + "\n" for x in rcs[:-1]))
    else:
        raise SystemExit("edit.py: qe op " + op)


COMMANDS = {
    "stream": (cmd_stream, ("--in", "--out", "--op"), ()),
    "block": (cmd_block, ("--campaign", "--point", "--call", "--op"), ("--rehash", "--sums")),
    "drop": (cmd_drop, ("--campaign", "--point", "--call"), ("--sums",)),
    "read": (cmd_read, ("--in", "--out", "--op"), ()),
    "stop": (cmd_stop, ("--campaign", "--op"), ()),
    "qe": (cmd_qe, ("--campaign", "--op"), ()),
}


def main(argv):
    if len(argv) < 2 or argv[1] not in COMMANDS:
        sys.stderr.write(__doc__)
        return 2
    fn, keys, flags = COMMANDS[argv[1]]
    a, i = {}, 2
    while i < len(argv):
        if argv[i] in flags:
            a[argv[i]] = True
            i += 1
        elif argv[i] in keys and i + 1 < len(argv):
            a[argv[i]] = argv[i + 1]
            i += 2
        else:
            sys.stderr.write(__doc__)
            return 2
    if any(k not in a for k in keys):
        sys.stderr.write(__doc__)
        return 2
    fn(a)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
