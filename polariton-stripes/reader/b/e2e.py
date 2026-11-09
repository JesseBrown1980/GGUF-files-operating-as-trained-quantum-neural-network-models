"""End-to-end test of stage B on a synthetic campaign, with no engine:

    python3 -I e2e.py [--work DIR] [--keep]

1. tests/campaign.py writes every input of a run: P01-P14 (8000 call files and the P08, P13 side files), R1-R4
   (64 batches each), the 15 QE commands of QR1-QR5 and the guard lines.
2. `stripes_read_b read` writes READ-STRIPE-PHASE.hbp; it must hold one VERDICT row per STRIPES_PREDICT row, in the
   frozen order, and pass `audit`; `verify` must rebuild it line for line.
3. A second campaign loses calls, batches, records and QE rows under rule STOP, each with the evidence the run script
   files: P03 call 500 and P08 call 10 lost (every try down to one record exited 4), P05 call 7 rerun without its last
   record, R2 batch 5 lost the same way, the QE command at (729, 1/108) killed after its t=1 row (rc=137) and the 6561
   sector command panicked after its t=2 row (rc=101, the panic text on stderr). Its READ file must have the same
   rows, the same scored and read-and-report reads (the SCORING table), and NOT_MEASURED reads where data was lost.

Prints one E2E row; exit 0 when every check holds."""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "tests"))

import campaign  # noqa: E402
from stripes_read_b import common as c  # noqa: E402
from stripes_read_b import frozen  # noqa: E402
from stripes_read_b import qe as qe_mod  # noqa: E402
from stripes_read_b.hbp import fields_dict, parse_row, read_lines  # noqa: E402

MAIN = os.path.join(HERE, "stripes_read_b", "__main__.py")


def stage_b(*args):
    p = subprocess.run([sys.executable, "-I", MAIN] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=False)
    return p.returncode, p.stdout.decode("ascii", "replace").strip()


def inputs(root):
    return ["--agg", os.path.join(root, "agg"), "--runs", os.path.join(root, "run"), "--qe",
            os.path.join(root, "QE.hbp"), "--cost", os.path.join(root, "QE-COST.hbp"), "--qe-rc",
            os.path.join(root, "QE-RC.hbp"), "--guard", os.path.join(root, "GUARD.hbp")]


def replace_file(path, data):
    """Write a new file at path (the campaign copies share inodes with the original; never write in place)."""
    if os.path.exists(path):
        os.remove(path)
    with open(path, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode("ascii"))


def link_copy(src, dst):
    shutil.copytree(src, dst, copy_function=os.link)


PANIC = ("thread 'main' panicked at src/bin/polariton_first_correction.rs:1967:57:\nre\n"
         "note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\n")


def stop_call(d, pid, call, stem):
    """A try of a dump call whose engine exited 4, filed as <stem>.hbp and <stem>.eng.err."""
    text, err = campaign.engine_stop_call(pid, call)
    replace_file(os.path.join(d, stem + ".hbp"), text)
    replace_file(os.path.join(d, stem + ".eng.err"), err)


def stop_batch(d, stem):
    """A try of a run batch that exited 4: nothing on stdout, the TWB_FAULT row on stderr, rc=4."""
    replace_file(os.path.join(d, stem + ".hbp"), "")
    replace_file(os.path.join(d, stem + ".err"), campaign.ENGINE_FAULT)
    replace_file(os.path.join(d, stem + ".rc"), "rc=4\n")


def lose(root):
    """The rule STOP campaign: data lost in every way the run plan allows, each loss with its evidence. Returns
    (QE rows absent from QE.hbp, QE commands with rc != 0)."""
    campaign.LOCK_Q = campaign.e.lock_q(frozen.load())
    for pid, call in (("P03", 500), ("P08", 10)):  # 4 records: tries with 4, 3 and 2 records, then the last with 1
        d = os.path.join(root, "agg", pid)
        for k in (1, 2, 3):
            stop_call(d, pid, call, "%d.attempt%d" % (call, k))
        stop_call(d, pid, call, str(call))
    os.remove(os.path.join(root, "agg", "P08", "10.side"))
    d = os.path.join(root, "agg", "P05")
    stop_call(d, "P05", 7, "7.attempt1")
    text, _ = campaign.call_block(c.DUMP_POINTS["P05"], 7, [64, 128, 192], "agg/P05/7.side")
    replace_file(os.path.join(d, "7.hbp"), text + "rc=0 rc_reader=0\n")
    for pid in ("P03", "P05", "P08"):
        d = os.path.join(root, "agg", pid)
        os.remove(os.path.join(d, "SHA256SUMS"))
        c.write_sha256sums(d)
    d = os.path.join(root, "run")
    for stem in ("R2.5.attempt1", "R2.5.attempt2", "R2.5"):  # 3 records: tries with 3, 2 and 1
        stop_batch(d, stem)
    reads = read_lines(os.path.join(root, "QE.hbp"))
    costs = read_lines(os.path.join(root, "QE-COST.hbp"))
    killed = [k for k, r in enumerate(reads) if "|N=729|" in r and "|y=1/108|" in r and "|t=2|" in r]
    panicked = [k for k, r in enumerate(reads) if "|N=6561|" in r and "|t=4|" in r]
    keep = [k for k in range(len(reads)) if k not in killed + panicked]
    replace_file(os.path.join(root, "QE.hbp"), "".join(reads[k] + "\n" for k in keep))
    replace_file(os.path.join(root, "QE-COST.hbp"), "".join(costs[k] + "\n" + (PANIC if k + 1 == panicked[0] else "")
                                                              for k in keep))
    rcs = {qe_mod.argv_text(cm): rc for cm, rc in zip(qe_mod.PLAN, [0] * len(qe_mod.PLAN), strict=True)}
    for cm in qe_mod.PLAN:
        if (cm.mode, cm.N, cm.y) == ("sector", 6561, "0"):
            rcs[qe_mod.argv_text(cm)] = 101
        if (cm.mode, cm.N, cm.y) == ("point", 729, "1/108"):
            rcs[qe_mod.argv_text(cm)] = 137
    replace_file(os.path.join(root, "QE-RC.hbp"), campaign.qe_rc_text(rcs))
    return len(reads) - len(keep), sum(1 for v in rcs.values() if v)


def verdict_rows(path):
    return [fields_dict(parse_row(ln)[1]) for ln in read_lines(path) if ln.startswith("STRIPES_VERDICT|")]


def campaign_scoring(path):
    """The sorted read:scored:why lines of a READ file (its SCORING table before hashing)."""
    if not os.path.exists(path):
        return []
    rows = [fields_dict(parse_row(ln)[1]) for ln in read_lines(path) if ln.startswith("STRIPES_READ|")]
    return sorted("%s:%s:%s:%s" % (r["row"], r["read"], r["scored"], r["why"]) for r in rows)


def main(argv):
    work, keep = None, False
    i = 1
    while i < len(argv):
        if argv[i] == "--work" and i + 1 < len(argv):
            work = argv[i + 1]
            i += 2
        elif argv[i] == "--keep":
            keep = True
            i += 1
        else:
            sys.stderr.write(__doc__)
            return 2
    own = work is None
    work = work or tempfile.mkdtemp(prefix="stripes-e2e-")
    fails = []
    try:
        base = os.path.join(work, "campaign")
        if not os.path.isdir(base):
            os.makedirs(base)
            campaign.make_campaign(base)
        out = os.path.join(work, "READ-STRIPE-PHASE.hbp")
        rc, text = stage_b("read", *inputs(base), "--out", out)
        if rc != 0:
            fails.append("read:" + text[:200])
        order = [d["id"] for k, d, _ in frozen.load().rows if k == "STRIPES_PREDICT"]
        vs = verdict_rows(out) if rc == 0 else []
        if [v["row"] for v in vs] != order:
            fails.append("verdict_rows")
        rc_a, text_a = stage_b("audit", "--read", out)
        if rc_a != 0:
            fails.append("audit:" + text_a[:200])
        rc_v, text_v = stage_b("verify", "--read", out, *inputs(base))
        if rc_v != 0:
            fails.append("verify:" + text_v[:200])
        lost = os.path.join(work, "campaign-stop")
        if os.path.isdir(lost):
            shutil.rmtree(lost)
        link_copy(base, lost)
        nq, nfail = lose(lost)
        out2 = os.path.join(work, "READ-STRIPE-PHASE-stop.hbp")
        rc2, text2 = stage_b("read", *inputs(lost), "--out", out2)
        if rc2 != 0:
            fails.append("read_stop:" + text2[:200])
        vs2 = verdict_rows(out2) if rc2 == 0 else []
        if [v["row"] for v in vs2] != order:
            fails.append("verdict_rows_stop")
        nm = sum(int(v["not_measured"]) for v in vs2)
        if nm == 0:
            fails.append("no_NOT_MEASURED_after_losses")
        rc_a2, text_a2 = stage_b("audit", "--read", out2)
        if rc_a2 != 0:
            fails.append("audit_stop:" + text_a2[:200])
        tally = {}
        for v in vs:
            tally[v["verdict"]] = tally.get(v["verdict"], 0) + 1
        notes = {}
        if rc2 == 0:
            for ln in read_lines(out2):
                if ln.startswith("STRIPES_READ_NOTE|"):
                    d = fields_dict(parse_row(ln)[1])
                    notes[d["label"]] = d["text"]
        want_notes = {"point_P03": "lost=500", "point_P05": "not_measured=256,attempts=1",
                      "point_P08": "lost=10", "run_R2": "lost=5", "qe_rc": "rc=101"}
        for label, part in want_notes.items():
            if part not in notes.get(label, ""):
                fails.append("note_" + label)
        rc_v2, text_v2 = stage_b("verify", "--read", out2, *inputs(lost))
        if rc_v2 != 0:
            fails.append("verify_stop:" + text_v2[:200])
        if rc2 == 0 and [r for r in campaign_scoring(out) if r] != [r for r in campaign_scoring(out2) if r]:
            fails.append("scoring_table_stop")
        print("E2E|predict_rows=%d|verdict_rows=%d|verdicts=%s|audit=%s|verify=%s|stop_campaign_verdict_rows=%d|"
              "stop_campaign_not_measured_scored=%d|qe_rows_absent=%d|qe_commands_rc_nonzero=%d|engine_runs=0|"
              "result=%s|json=0" % (
                  len(order), len(vs), ",".join("%s:%d" % kv for kv in sorted(tally.items())),
                  "pass" if rc_a == 0 else "fail", "equal" if rc_v == 0 else "differ", len(vs2), nm, nq, nfail,
                  "pass" if not fails else "fail:" + ";".join(f.replace("|", "/") for f in fails)))
    finally:
        if own and not keep:
            shutil.rmtree(work)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
