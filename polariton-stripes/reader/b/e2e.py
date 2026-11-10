"""End-to-end test of stage B on a synthetic campaign, with no engine:

    python3 -I e2e.py [--work DIR] [--keep]

1. tests/campaign.py writes every input of a run: P01-P14 (8000 call files, each trailer with its steps, and the
   P08, P13 side files, each one's sums equal to its block's AGG_SUM and AGG_ATOMS), R1-R4 (64 batches each, each .rc
   with its steps), the 15 QE commands of QR1-QR5 and the guard lines.
2. `stripes_read_b read` writes READ-STRIPE-PHASE.hbp; it must hold one VERDICT row per STRIPES_PREDICT row, in the
   frozen order, and pass `audit`; `verify` must rebuild it line for line.
3. A second campaign loses calls, batches, records and QE rows under rule STOP, each with the evidence the run script
   files, every try with the steps it ran: P03 call 500 and P08 call 10 lost (every try down to one record exited 4),
   P05 call 7 rerun without its last record, R2 batch 5 lost the same way, the QE command at (729, 1/108) killed
   after its t=1 row (rc=137) and the 6561 sector command panicked after its t=2 row (rc=101, the panic text on
   stderr). Its READ file must have the same rows, the same scored and read-and-report reads (the SCORING table), and
   NOT_MEASURED reads where data was lost. Rule STOP keeps only the records all 64 batches of a run point reached, and
   the lost batch reached none: every read of R2 (E04, E18, E19) must be NOT_MEASURED and state the loss. By the
   owner's E12/E13 ruling (PR #18 comment 6753596286), every read with a size of its nominal grid below 1024 complete
   blocks after a lost call (P03 and P08) must be NOT_MEASURED with its audit fields, and the clean campaign has none.

Stage B computes on checked integer pairs (stripes_read_b/qint.py). Prints one E2E row; exit 0 when every check
holds."""

import os
import re
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


def stop_call(d, pid, call, stem, steps):
    """A try of a dump call whose engine exited 4 while running `steps`, filed as <stem>.hbp and <stem>.eng.err."""
    text, err = campaign.engine_stop_call(pid, call, steps)
    replace_file(os.path.join(d, stem + ".hbp"), text)
    replace_file(os.path.join(d, stem + ".eng.err"), err)


def stop_batch(d, stem, steps):
    """A try of a run batch that exited 4 while running `steps`: nothing on stdout, the TWB_FAULT row on stderr,
    rc=4 and the steps in the .rc file."""
    replace_file(os.path.join(d, stem + ".hbp"), "")
    replace_file(os.path.join(d, stem + ".err"), campaign.ENGINE_FAULT)
    replace_file(os.path.join(d, stem + ".rc"), "rc=4 steps=%s\n" % ",".join(map(str, steps)))


def lose(root):
    """The rule STOP campaign: data lost in every way the run plan allows, each loss with its evidence. Returns
    (QE rows absent from QE.hbp, QE commands with rc != 0)."""
    campaign.LOCK_Q = campaign.e.lock_q(frozen.load())
    s4 = list(c.DUMP_POINTS["P03"].steps)
    for pid, call in (("P03", 500), ("P08", 10)):  # 4 records: tries with 4, 3 and 2 records, then the last with 1
        d = os.path.join(root, "agg", pid)
        for k in (1, 2, 3):
            stop_call(d, pid, call, "%d.attempt%d" % (call, k), s4[: 5 - k])
        stop_call(d, pid, call, str(call), s4[:1])
    os.remove(os.path.join(root, "agg", "P08", "10.side"))
    d = os.path.join(root, "agg", "P05")
    stop_call(d, "P05", 7, "7.attempt1", s4)
    text, _ = campaign.call_block(c.DUMP_POINTS["P05"], 7, s4[:3], "agg/P05/7.side")
    replace_file(os.path.join(d, "7.hbp"), text + campaign.trailer(0, 0, s4[:3]))
    for pid in ("P03", "P05", "P08"):
        d = os.path.join(root, "agg", pid)
        os.remove(os.path.join(d, "SHA256SUMS"))
        c.write_sha256sums(d)
    d = os.path.join(root, "run")
    s3 = list(c.RUN_POINTS["R2"].steps)
    for stem, steps in (("R2.5.attempt1", s3), ("R2.5.attempt2", s3[:2]), ("R2.5", s3[:1])):  # tries with 3, 2, 1
        stop_batch(d, stem, steps)
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


R2_AT = re.compile(r"(^|[^A-Z0-9])R2([^0-9]|$)")


def run_reads(path, rid="R2"):
    """The READ rows of a READ file whose `at` names the run point rid (E04, E18, E19)."""
    pat = R2_AT if rid == "R2" else re.compile(r"(^|[^A-Z0-9])%s([^0-9]|$)" % rid)
    rows = [fields_dict(parse_row(ln)[1]) for ln in read_lines(path) if ln.startswith("STRIPES_READ|")]
    return [r for r in rows if pat.search(r["at"])]


# Reads the STOP campaign's lost calls leave below 1024 complete blocks (P03 call 500: 1023 of 1024 at n=4096; P08
# call 10: 1020 of 1024 at n=1024 for VNC, 1008 of 1024 at n=256 for the controls), each with a part of its detail.
CALL_LOSS_WANT = {
    ("E12", "iid_P03_VNC_t1"): "nominal_blocks_n4096:1024,complete_blocks_n4096:1023,reason:call_loss_insufficient"
                               "_blocks,missing_indices:2048000-2052095,schedule:calls_0-1023_x4096_indices_0-4194303",
    ("E12", "iid_P08_VNC_t1"): "nominal_blocks_n1024:1024,complete_blocks_n1024:1020",
    ("E12", "iid_P08_LOCK_t2"): "nominal_blocks_n256:1024,complete_blocks_n256:1008,reason:call_loss_insufficient"
                                "_blocks,missing_indices:40960-45055,schedule:calls_0-63_x4096_indices_0-262143",
    ("E13", "tol_P03_t2"): "n4096:NOT_MEASURED_call_loss_insufficient_blocks",
    ("E13", "band_P03_t2_n4096"): "complete_blocks_n4096:1023",
    ("E13", "band_P08_t1_n1024"): "complete_blocks_n1024:1020",
}


def call_loss_reads(path):
    rows = [fields_dict(parse_row(ln)[1]) for ln in read_lines(path) if ln.startswith("STRIPES_READ|")]
    return [r for r in rows if "reason:call_loss_insufficient_blocks" in r["detail"]]


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
                      "point_P08": "lost=10", "run_R2": "read=0,lost=5,steps=none,not_measured=32:64:128",
                      "qe_rc": "rc=101"}
        for label, part in want_notes.items():
            if part not in notes.get(label, ""):
                fails.append("note_" + label)
        # rule STOP for runs: the records all 64 batches reached; R2's lost batch reached none
        r2 = run_reads(out2) if rc2 == 0 else []
        r2_clean = run_reads(out) if rc == 0 else []
        if len(r2) != 11 or len(r2_clean) != 11:
            fails.append("R2_reads_%d_%d" % (len(r2), len(r2_clean)))
        for r in r2:
            if r["verdict"] != c.NOT_MEASURED or "batch_lost" not in r["detail"]:
                fails.append("R2_read_" + r["read"])
        if any(r["verdict"] == c.NOT_MEASURED for r in r2_clean):
            fails.append("R2_read_lost_in_the_clean_campaign")
        # the owner's E12/E13 ruling (PR #18 comment 6753596286): a size of the nominal grid below 1024 complete
        # blocks after a lost call is NOT_MEASURED, never MET, MISS or NOT_RESOLVED, with its audit fields
        cl = call_loss_reads(out2) if rc2 == 0 else []
        for r in cl:
            d = dict(x.split(":", 1) for x in r["detail"].split(","))
            measured = [v.rsplit("_", 1)[-1] for k, v in d.items() if re.fullmatch("n[0-9]+", k) and "+-" in v]
            want = c.MISS if "MISS" in measured else c.NOT_RESOLVED if "RESOLVED" in measured else c.NOT_MEASURED
            if r["verdict"] != want or not {"missing_indices", "schedule"} <= set(d) \
                    or not any(k.startswith("nominal_blocks_n") for k in d):
                fails.append("call_loss_read_" + r["read"])
        got = {(r["row"], r["read"]): r["detail"] for r in cl}
        for key, part in CALL_LOSS_WANT.items():
            if part not in got.get(key, ""):
                fails.append("call_loss_%s_%s" % key)
        if rc == 0 and call_loss_reads(out):
            fails.append("call_loss_in_the_clean_campaign")
        rc_v2, text_v2 = stage_b("verify", "--read", out2, *inputs(lost))
        if rc_v2 != 0:
            fails.append("verify_stop:" + text_v2[:200])
        if rc2 == 0 and [r for r in campaign_scoring(out) if r] != [r for r in campaign_scoring(out2) if r]:
            fails.append("scoring_table_stop")
        print("E2E|predict_rows=%d|verdict_rows=%d|verdicts=%s|audit=%s|verify=%s|stop_campaign_verdict_rows=%d|"
              "stop_campaign_not_measured_scored=%d|stop_campaign_R2_reads_not_measured=%d|"
              "stop_campaign_call_loss_reads=%d|qe_rows_absent=%d|qe_commands_rc_nonzero=%d|engine_runs=0|"
              "result=%s|json=0" % (
                  len(order), len(vs), ",".join("%s:%d" % kv for kv in sorted(tally.items())),
                  "pass" if rc_a == 0 else "fail", "equal" if rc_v == 0 else "differ", len(vs2), nm,
                  sum(1 for r in r2 if r["verdict"] == c.NOT_MEASURED), len(cl), nq, nfail,
                  "pass" if not fails else "fail:" + ";".join(f.replace("|", "/") for f in fails)))
    finally:
        if own and not keep:
            shutil.rmtree(work)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
