"""End-to-end test of stage B on a synthetic campaign, with no engine:

    python3 -I e2e.py [--work DIR] [--keep]

1. tests/campaign.py writes every input of a run: P01-P14 (8000 call files and the P08, P13 side files), R1-R4
   (64 batches each), the 15 QE commands of QR1-QR5 and the guard lines.
2. `stripes_read_b read` writes READ-STRIPE-PHASE.hbp; it must hold one VERDICT row per STRIPES_PREDICT row, in the
   frozen order, and pass `audit`; `verify` must rebuild it line for line.
3. A second campaign loses calls, batches, records and QE rows under rule STOP (an engine stop at P03 and P08, a rerun
   of P05 call 7 without its last record, an empty R2 batch, two QE rows missing). Its READ file must have the same
   rows, the same scored and read-and-report reads (the SCORING table), and NOT_MEASURED reads where data was lost.

Prints one E2E row; exit 0 when every check holds."""

import hashlib
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
from stripes_read_b.hbp import fields_dict, parse_row, read_lines  # noqa: E402

MAIN = os.path.join(HERE, "stripes_read_b", "__main__.py")


def stage_b(*args):
    p = subprocess.run([sys.executable, "-I", MAIN] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=False)
    return p.returncode, p.stdout.decode("ascii", "replace").strip()


def inputs(root):
    return ["--agg", os.path.join(root, "agg"), "--runs", os.path.join(root, "run"), "--qe",
            os.path.join(root, "QE.hbp"), "--cost", os.path.join(root, "QE-COST.hbp"), "--guard",
            os.path.join(root, "GUARD.hbp")]


def replace_file(path, data):
    """Write a new file at path (the campaign copies share inodes with the original; never write in place)."""
    if os.path.exists(path):
        os.remove(path)
    with open(path, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode("ascii"))


def link_copy(src, dst):
    shutil.copytree(src, dst, copy_function=os.link)


def engine_stop(pid, call):
    """What the run script files for a call whose engine stopped: stage A's empty_stream STOP and both exit codes."""
    e = hashlib.sha256(b"").hexdigest()
    return ("STOP|reader=stripes-read-a|reader_version=0.1.0|point=%s|call=%d|reason=empty_stream|line=0|detail=none"
            "|stdin_bytes=0|stdin_lines=0|stdin_sha256=%s|json=0\nrc=4 rc_reader=3\n" % (pid, call, e))


def lose(root):
    """The rule STOP campaign: data lost in every way the run plan allows."""
    campaign.LOCK_Q = campaign.e.lock_q(frozen.load())
    replace_file(os.path.join(root, "agg", "P03", "500.hbp"), engine_stop("P03", 500))
    replace_file(os.path.join(root, "agg", "P08", "10.hbp"), engine_stop("P08", 10))
    os.remove(os.path.join(root, "agg", "P08", "10.side"))
    replace_file(os.path.join(root, "agg", "P05", "7.attempt1.hbp"), engine_stop("P05", 7))
    text, _ = campaign.call_block(c.DUMP_POINTS["P05"], 7, [64, 128, 192], "agg/P05/7.side")
    replace_file(os.path.join(root, "agg", "P05", "7.hbp"), text + "rc=0 rc_reader=0\n")
    for pid in ("P03", "P05", "P08"):
        d = os.path.join(root, "agg", pid)
        os.remove(os.path.join(d, "SHA256SUMS"))
        c.write_sha256sums(d)
    replace_file(os.path.join(root, "run", "R2.5.hbp"), "")
    reads = read_lines(os.path.join(root, "QE.hbp"))
    costs = read_lines(os.path.join(root, "QE-COST.hbp"))
    keep = [k for k, r in enumerate(reads) if not (("|N=729|" in r and "|y=1/108|" in r and "|t=2|" in r)
                                                  or ("|N=6561|" in r and "|t=4|" in r))]
    replace_file(os.path.join(root, "QE.hbp"), "".join(reads[k] + "\n" for k in keep))
    replace_file(os.path.join(root, "QE-COST.hbp"), "".join(costs[k] + "\n" for k in keep))
    return len(reads) - len(keep)


def verdict_rows(path):
    return [fields_dict(parse_row(ln)[1]) for ln in read_lines(path) if ln.startswith("STRIPES_VERDICT|")]


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
        nq = lose(lost)
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
        print("E2E|predict_rows=%d|verdict_rows=%d|verdicts=%s|audit=%s|verify=%s|stop_campaign_verdict_rows=%d|"
              "stop_campaign_not_measured_scored=%d|qe_rows_dropped=%d|engine_runs=0|result=%s|json=0" % (
                  len(order), len(vs), ",".join("%s:%d" % kv for kv in sorted(tally.items())),
                  "pass" if rc_a == 0 else "fail", "equal" if rc_v == 0 else "differ", len(vs2), nm, nq,
                  "pass" if not fails else "fail:" + ";".join(f.replace("|", "/") for f in fails)))
    finally:
        if own and not keep:
            shutil.rmtree(work)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
