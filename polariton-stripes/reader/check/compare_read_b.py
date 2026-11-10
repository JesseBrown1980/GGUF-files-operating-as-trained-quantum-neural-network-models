#!/usr/bin/env python3
"""compare_read_b.py: the READ files of the live stage B (integer pairs, reader/b) and of the stage B kept as evidence
(fractions.Fraction, reader/evidence/stage-b-fraction), on the same fabricated campaigns (review M5). No engine, no
row-point data: the campaigns are tests/campaign.py's small fabricated integers.

    python3 -I compare_read_b.py [--campaigns DIR] [--work DIR] [--keep]

1. Checks the evidence folder's tree pin (float_evidence.py), so the version compared is the one listed.
2. The campaigns: tests/campaign.py's clean campaign and e2e.py's STOP campaign (e2e.lose: calls, batches, records
   and QE rows lost under rule STOP). With --campaigns, DIR/campaign and DIR/campaign-stop as `e2e.py --keep --work
   DIR` leaves them; otherwise both are written into the work folder.
3. The live stage B reads each campaign as it is. The evidence, laid out at its old depth beside a copy of the frozen
   file (as compare_b.py lays it out), reads a copy in its own receipt grammar: ` steps=S` dropped from the trailer of
   every call file and attempt and from every run .rc file, and the sha256 of each rewritten call file put in its
   point's SHA256SUMS. The copy is hard links to the campaign, and a rewritten file is a new file.
4. Compares the two READ files row by row. The STRIPES_READ rows must name the same (row, read) keys in the same
   order, and the STRIPES_VERDICT rows the same rows; each row that differs must fall in one declared case:
     E16_bounds          an E16 read whose lo, hi and detail alone differ (the conservative SE_pair);
     band_infinite_end   a read whose band alone differs, and only in the bracket of an infinite end ((0,inf) for
                         (0,inf]);
     R2_lost_batch       on the STOP campaign, a read of E04, E18 or E19 at R2 that the live stage B leaves
                         NOT_MEASURED stating the lost batch (rule STOP for runs), with that row's VERDICT;
     qe_rc_reason        on the STOP campaign, a read whose detail alone differs, lost:qe_rc_<rc> for missing_QE_row;
     call_loss_blocks    on the STOP campaign, an E12 or E13 read with a size below 1024 complete blocks after a lost
                         call (the owner's ruling, PR #18 comment 6753596286): that size NOT_MEASURED with reason
                         call_loss_insufficient_blocks and the audit fields where the evidence prints K<k>_NOT_MEASURED;
                         the read NOT_MEASURED where the evidence reads NOT_RESOLVED, or MISS or NOT_RESOLVED in both
                         from a measured size (a Z_n read; REPORT for NOT_RESOLVED or MISS where the read is
                         read-and-report); a band NOT_MEASURED in both, the evidence's detail
                         lost:fewer_than_1024_blocks; with that row's VERDICT.
   The head, the inputs and the notes are compared apart, against their own declared lists (NOTE_CASES, INPUT_CASES).
5. Prints one COMPARE_READ_B row per campaign, one COMPARE_READ_B_META row per campaign for the head, inputs and
   notes, a COMPARE_READ_B_UNEXPLAINED row per row outside every case (at most 20), and COMPARE_READ_B_DONE; exit 0
   when every difference is declared."""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
READER = os.path.dirname(HERE)
STRIPES = os.path.dirname(READER)
LIVE = os.path.join(READER, "b")
EVIDENCE = os.path.join(READER, "evidence", "stage-b-fraction")
FROZEN = os.path.join(STRIPES, "PREDICTION-STRIPE-PHASE.hbp")
sys.dont_write_bytecode = True
sys.path.insert(0, LIVE)
sys.path.insert(0, os.path.join(LIVE, "tests"))

import campaign  # noqa: E402
import e2e  # noqa: E402
from stripes_read_b import common as c  # noqa: E402
from stripes_read_b.hbp import fields_dict, file_sha256, parse_row, read_lines  # noqa: E402

CALL_TRAILER = re.compile(r"(rc=(?:0|[1-9][0-9]*) rc_reader=(?:0|[1-9][0-9]*)) steps=[0-9,]+\Z")
RUN_RC = re.compile(r"(rc=(?:0|[1-9][0-9]*)) steps=[0-9,]+\Z")
SUMS_LINE = re.compile(r"([0-9a-f]{64})  (\S+)\Z")
R2_ROWS = ("E04", "E18", "E19")
CALL_LOSS = "call_loss_insufficient_blocks"
AUDIT_KEY = re.compile(r"(nominal_blocks_n|complete_blocks_n)[0-9]+\Z|(reason|missing_indices|schedule)\Z")
QE_RC_DETAIL = re.compile(r"(?<=lost:)qe_rc_[1-9][0-9]*")

# The head, input and note rows that may differ, each with its reason; any other difference is outside the list.
HEAD_CASES = {"reader_version": "0.1.0 for the evidence, 0.2.0 live"}
# label: the fields that may differ. The evidence reads a copy whose call files lost ` steps=`, so the sha256 of each
# point's SHA256SUMS moves (its bytes do not).
INPUT_CASES = {"AGG_P%02d" % k: ("sha256",) for k in range(1, 15)}
NOTE_CASES = {
    "reader_b": "the version, the arithmetic and the tree pin of each stage B",
    "reader_a": "the live note also names stage A's source, the git tree of reader/a (review M4)",
    "runs": "the run listing's sha256: the evidence reads .rc files without ` steps=`",
    "run_R1": "the live run notes count the batches checked (checked=)",
    "run_R2": "checked=, and on the STOP campaign rule STOP for runs: R2 keeps no record (read=0, steps=none)",
    "run_R3": "checked=",
    "run_R4": "checked=",
    "reading_E10_falsifier": "a reading the later fixes added (the low end of the ambiguity bracket)",
    "reading_E12_E13_n": "reworded by the later fixes (a size left with fewer than 1024 measured blocks)",
    "reading_E16": "the conservative SE_pair of the later fixes",
    "reading_STOP_tries": "the steps of every try and rule STOP for runs, added by the later fixes",
    "frozen_R1_s": "live only: R1's frozen s=1/2 against the s=1 stage B computes (review N6)",
    "closed_STOP_runs": "live only: the GATE ruling the frozen text closes, with its frozen line (PR #18 comment)",
    "closed_E16_bracket": "live only: the GATE ruling the frozen text closes, with its frozen lines (PR #18 comment)",
    "closed_E02_counts": "live only: the GATE ruling the frozen text closes, with its frozen lines (PR #18 comment)",
    "ruled_E12_E13": "live only: the owner's E12/E13 ruling (PR #18 comment 6753596286) the live stage B applies",
}


def run(argv):
    p = subprocess.run([sys.executable, "-I"] + argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
                       cwd="/")
    return p.returncode, p.stdout.decode("ascii", "replace").strip(), p.stderr.decode("ascii", "replace")


def inputs(root):
    return e2e.inputs(root)


def last_line_rewritten(path, pattern):
    """The file at path with the steps of its last line dropped, written as a new file; its new sha256."""
    with open(path, "rb") as f:
        data = f.read()
    lines = data.decode("ascii").split("\n")
    if len(lines) < 2 or lines[-1] != "":
        raise SystemExit("COMPARE_READ_B_DONE|result=receipt_without_a_last_line|path=%s|json=0" % path)
    m = pattern.match(lines[-2])
    if not m:
        raise SystemExit("COMPARE_READ_B_DONE|result=receipt_trailer_not_live|path=%s|json=0" % path)
    lines[-2] = m.group(1)
    e2e.replace_file(path, "\n".join(lines))
    return file_sha256(path)


def adapt(src, dst):
    """A copy of the campaign src at dst in the evidence's receipt grammar (the trailers of 5aad307)."""
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    e2e.link_copy(src, dst)
    agg = os.path.join(dst, "agg")
    for pid in sorted(os.listdir(agg)):
        d = os.path.join(agg, pid)
        moved = {nm: last_line_rewritten(os.path.join(d, nm), CALL_TRAILER)
                 for nm in sorted(os.listdir(d)) if nm.endswith(".hbp")}
        sums = []
        for ln in read_lines(os.path.join(d, "SHA256SUMS")):
            m = SUMS_LINE.match(ln)
            if not m:
                raise SystemExit("COMPARE_READ_B_DONE|result=sums_line|point=%s|json=0" % pid)
            sums.append("%s  %s\n" % (moved.pop(m.group(2), m.group(1)), m.group(2)))
        if moved:
            raise SystemExit("COMPARE_READ_B_DONE|result=call_file_not_in_sums|point=%s|json=0" % pid)
        e2e.replace_file(os.path.join(d, "SHA256SUMS"), "".join(sums))
    rd = os.path.join(dst, "run")
    for nm in sorted(os.listdir(rd)):
        if nm.endswith(".rc"):
            last_line_rewritten(os.path.join(rd, nm), RUN_RC)


def read_file(path):
    """(head, [(label, row)] of inputs, [(label, text)] of notes, [READ rows], [VERDICT rows]) of a READ file."""
    head, ins, notes, reads, verdicts = None, [], [], [], []
    for ln in read_lines(path):
        kind, fields = parse_row(ln)
        d = fields_dict(fields)
        if kind == "STRIPES_READ_HEAD":
            head = d
        elif kind == "STRIPES_READ_INPUT":
            ins.append((d["label"], d))
        elif kind == "STRIPES_READ_NOTE":
            notes.append((d["label"], d["text"]))
        elif kind == "STRIPES_READ":
            reads.append(d)
        elif kind == "STRIPES_VERDICT":
            verdicts.append(d)
    return head, ins, notes, reads, verdicts


def differing(a, b):
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))


def band_case(live, frac):
    """The live band prints an infinite end open, the evidence closed: ( or ) at -inf or inf."""
    x, y = live["band"], frac["band"]
    if "inf" not in x or len(x) != len(y) or x[1:-1] != y[1:-1]:
        return False
    ends_ok = all(p == q or (p, q) in (("(", "["), (")", "]")) for p, q in ((x[0], y[0]), (x[-1], y[-1])))
    open_at_inf = (x[0] == y[0] or x.startswith("(-inf,")) and (x[-1] == y[-1] or x.endswith(",inf)"))
    return ends_ok and open_at_inf


def r2_lost(live, stop):
    return (stop and live["row"] in R2_ROWS and e2e.R2_AT.search(live["at"]) is not None
            and live["verdict"] == c.NOT_MEASURED and "batch_lost" in live["detail"])


def call_loss(live, frac, stop):
    """The live read states a call loss below 1024 blocks; the evidence read the same sizes, that one unmeasured."""
    if not stop or live["row"] not in ("E12", "E13"):
        return False
    det = [x.split(":", 1) for x in live["detail"].split(",")]
    d = dict(det)
    if d.get("reason") != CALL_LOSS:
        return False
    if live["read"].startswith("band_"):
        return frac["verdict"] == c.NOT_MEASURED and frac["detail"] == "lost:fewer_than_1024_blocks"
    want = []
    for k, v in det:
        if AUDIT_KEY.match(k):
            continue
        if v == "NOT_MEASURED_" + CALL_LOSS:
            v = "K%s_NOT_MEASURED" % d["complete_blocks_" + k]
        want.append("%s:%s" % (k, v))
    # a measured MISS or NOT_RESOLVED is kept in both; else the live NOT_MEASURED where the evidence NOT_RESOLVED
    verdicts = (live["verdict"], frac["verdict"])
    # (a read-and-report read prints REPORT for a measured outcome, NOT_MEASURED for none)
    rr = live["scored"] == "0"
    kept = ((c.REPORT, c.REPORT),) if rr else ((c.MISS, c.MISS), (c.NOT_RESOLVED, c.NOT_RESOLVED))
    lost = (c.NOT_MEASURED, c.REPORT if rr else c.NOT_RESOLVED)
    return frac["detail"] == ",".join(want) and (verdicts in kept and set(differing(live, frac)) == {"detail"}
                                                 or verdicts == lost
                                                 and set(differing(live, frac)) == {"verdict", "detail"})


def read_case(live, frac, stop):
    """The declared case of a differing READ row, or None."""
    diff = differing(live, frac)
    if live["row"] == "E16" and set(diff) <= {"lo", "hi", "detail"}:
        return "E16_bounds"
    if diff == ["band"] and band_case(live, frac):
        return "band_infinite_end"
    if r2_lost(live, stop):
        return "R2_lost_batch"
    if call_loss(live, frac, stop):
        return "call_loss_blocks"
    if stop and diff == ["detail"] and QE_RC_DETAIL.sub("missing_QE_row", live["detail"]) == frac["detail"] \
            and QE_RC_DETAIL.search(live["detail"]):
        return "qe_rc_reason"
    return None


def compare_meta(live, frac):
    """The head, inputs and notes, each against its own list: (differing labels, labels outside the lists)."""
    found, bad = {}, []
    for key in differing(live[0], frac[0]):
        (found.setdefault("head", []) if key in HEAD_CASES else bad).append("head:" + key)
    for name, a, b in (("input", live[1], frac[1]), ("note", live[2], frac[2])):
        da, db = dict(a), dict(b)
        if len(da) != len(a) or len(db) != len(b) or [k for k, _ in a if k in db] != [k for k, _ in b if k in da]:
            bad.append(name + ":order")
        for label in sorted(set(da) | set(db)):
            x, y = da.get(label), db.get(label)
            if x == y:
                continue
            if name == "input":
                ok = x is not None and y is not None and set(differing(x, y)) <= set(INPUT_CASES.get(label, ()))
            else:
                ok = label in NOTE_CASES
            (found.setdefault(name, []) if ok else bad).append("%s:%s%s" % (
                name, label, "" if x is not None and y is not None else ":only_" + ("live" if y is None else
                                                                                   "evidence")))
    return found, bad


def compare(name, live_path, frac_path, stop, quiet=False):
    """The faults of a pair of READ files: every row outside the declared cases (printed unless quiet)."""
    live, frac = read_file(live_path), read_file(frac_path)
    counts = {"E16_bounds": 0, "band_infinite_end": 0, "R2_lost_batch": 0, "qe_rc_reason": 0, "call_loss_blocks": 0}
    bad, r2_rows = [], set()
    lr, fr_ = live[3], frac[3]
    if [(r["row"], r["read"]) for r in lr] != [(r["row"], r["read"]) for r in fr_]:
        bad.append(("STRIPES_READ", "keys", "the (row, read) keys differ"))
    equal = 0
    for a, b in zip(lr, fr_, strict=False):
        if a == b:
            equal += 1
            continue
        case = read_case(a, b, stop) if (a["row"], a["read"]) == (b["row"], b["read"]) else None
        if case is None:
            bad.append(("STRIPES_READ", "%s:%s" % (a["row"], a["read"]), ",".join(differing(a, b))))
            continue
        counts[case] += 1
        if case in ("R2_lost_batch", "call_loss_blocks"):
            r2_rows.add(a["row"])
    lv, fv = live[4], frac[4]
    if [v["row"] for v in lv] != [v["row"] for v in fv]:
        bad.append(("STRIPES_VERDICT", "rows", "the VERDICT rows differ"))
    v_equal, v_r2 = 0, 0
    for a, b in zip(lv, fv, strict=False):
        if a == b:
            v_equal += 1
        elif a["row"] in r2_rows and set(differing(a, b)) <= {"met", "miss", "not_resolved", "not_measured",
                                                                "falsifier", "verdict"}:
            v_r2 += 1
        else:
            bad.append(("STRIPES_VERDICT", a["row"], ",".join(differing(a, b))))
    found, meta_bad = compare_meta(live, frac)
    bad += [("META", x, "outside_the_declared_list") for x in meta_bad]
    if quiet:
        return bad
    print("COMPARE_READ_B|campaign=%s|live_sha256=%s|evidence_sha256=%s|read_rows=%d:%d|read_equal=%d|%s|"
          "read_unexplained=%d|verdict_rows=%d:%d|verdict_equal=%d|verdict_declared_loss=%d|verdict_unexplained=%d|"
          "result=%s|json=0" % (
              name, file_sha256(live_path)[:16], file_sha256(frac_path)[:16], len(lr), len(fr_), equal,
              "|".join("%s=%d" % kv for kv in counts.items()), sum(1 for x in bad if x[0] == "STRIPES_READ"),
              len(lv), len(fv), v_equal, v_r2, sum(1 for x in bad if x[0] == "STRIPES_VERDICT"),
              "within_allowlist" if not bad else "outside_allowlist"))
    print("COMPARE_READ_B_META|campaign=%s|head=%s|inputs=%s|notes=%s|unexplained=%s|json=0" % (
        name, ",".join(found.get("head", [])) or "equal", len(found.get("input", [])),
        ",".join(x.split(":", 1)[1] for x in found.get("note", [])) or "equal",
        ",".join(meta_bad) or "none"))
    for kind, key, what in bad[:20]:
        print("COMPARE_READ_B_UNEXPLAINED|campaign=%s|kind=%s|key=%s|fields=%s|json=0" % (name, kind, key, what))
    return bad


def planted(path, out, pick, field, value):
    """A copy of the READ file at path with one field of the first row pick(kind, fields) accepts set to
    value(fields); the copy is parsed, not audited."""
    lines, done = [], False
    for ln in read_lines(path):
        kind, fields = parse_row(ln)
        d = fields_dict(fields)
        if not done and pick(kind, d):
            ln = ln.replace("|%s=%s|" % (field, d[field]), "|%s=%s|" % (field, value(d)), 1)
            done = True
        lines.append(ln)
    if not done:
        raise SystemExit("COMPARE_READ_B_DONE|result=self_test_found_no_row_to_plant|json=0")
    e2e.replace_file(out, "".join(ln + "\n" for ln in lines))
    return out


def is_read(rid):
    return lambda k, d: k == "STRIPES_READ" and d["row"] == rid


def is_row(kind, key, value):
    return lambda k, d: k == kind and d[key] == value


# Differences outside every declared case, planted in a copy of a READ file: (name, campaign, file planted (the
# evidence's, or both), the row, the field, its new value). compare must find each one.
PLANTS = (
    ("verdict_of_a_Q02_read", "clean", "evidence", is_read("Q02"), "verdict", lambda d: c.NOT_RESOLVED),
    ("value_of_an_E05_read", "clean", "evidence", is_read("E05"), "value", lambda d: "12345"),
    ("verdict_of_an_E16_read", "clean", "evidence", is_read("E16"), "verdict", lambda d: c.NOT_RESOLVED),
    ("band_at_a_finite_end", "clean", "evidence",
     lambda k, d: k == "STRIPES_READ" and d["band"][:1] == "[" and "inf" not in d["band"] and d["row"] != "E16",
     "band", lambda d: "(" + d["band"][1:]),
    ("qe_rc_reason_without_a_QE_exit", "clean", "both", is_read("Q01"), "detail", None),
    ("verdict_row_E07", "clean", "evidence", is_row("STRIPES_VERDICT", "row", "E07"), "verdict", lambda d: c.NONE),
    ("note_point_P01", "clean", "evidence", is_row("STRIPES_READ_NOTE", "label", "point_P01"), "text",
     lambda d: "calls=1024"),
    ("input_QE", "clean", "evidence", is_row("STRIPES_READ_INPUT", "label", "QE"), "sha256", lambda d: "0" * 64),
    ("an_E04_read_off_R2", "stop", "evidence", lambda k, d: is_read("E04")(k, d) and "R2" not in d["at"], "verdict",
     lambda d: c.MISS),
    ("verdict_row_Q01", "stop", "evidence", is_row("STRIPES_VERDICT", "row", "Q01"), "verdict", lambda d: c.NONE),
    ("a_call_loss_read_MET_in_the_evidence", "stop", "evidence",
     lambda k, d: k == "STRIPES_READ" and d["row"] == "E12" and d["read"] == "iid_P03_VNC_t1", "verdict",
     lambda d: c.MET),
)


def self_test(work, pairs):
    """[(plant, found)] for every PLANTS row."""
    out = []
    for name, which, where, pick, field, value in PLANTS:
        live_path, frac_path = pairs[which]
        frac_value = value
        if where == "both":
            # the live file names a QE exit and the evidence missing_QE_row, on a campaign with no QE exit
            live_path = planted(live_path, os.path.join(work, "plant-%s-live.hbp" % name), pick, field,
                                lambda d: "lost:qe_rc_101")
            frac_value = lambda d: "lost:missing_QE_row"  # noqa: E731
        p = planted(frac_path, os.path.join(work, "plant-%s.hbp" % name), pick, field, frac_value)
        out.append((name, bool(compare(which, live_path, p, which == "stop", quiet=True))))
    return out


def main(argv):
    work, given, keep = None, None, False
    i = 1
    while i < len(argv):
        if argv[i] in ("--work", "--campaigns") and i + 1 < len(argv):
            if argv[i] == "--work":
                work = argv[i + 1]
            else:
                given = argv[i + 1]
            i += 2
        elif argv[i] == "--keep":
            keep, i = True, i + 1
        else:
            sys.stderr.write(__doc__)
            return 2
    rc, so, _ = run([os.path.join(HERE, "float_evidence.py")])
    if rc != 0:
        print(so)
        print("COMPARE_READ_B_DONE|result=evidence_pin_moved|json=0")
        return 1
    own = work is None
    work = work or tempfile.mkdtemp(prefix="stripes-compare-read-b-")
    ok = True
    try:
        frac = os.path.join(work, "polariton-stripes", "reader", "b")
        if os.path.isdir(os.path.join(work, "polariton-stripes")):
            shutil.rmtree(os.path.join(work, "polariton-stripes"))
        shutil.copytree(EVIDENCE, frac, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(FROZEN, os.path.join(work, "polariton-stripes", os.path.basename(FROZEN)))
        if given:
            clean, stop = os.path.join(given, "campaign"), os.path.join(given, "campaign-stop")
        else:
            clean, stop = os.path.join(work, "campaign"), os.path.join(work, "campaign-stop")
            for d in (clean, stop):
                if os.path.isdir(d):
                    shutil.rmtree(d)
            os.makedirs(clean)
            campaign.make_campaign(clean)
            e2e.link_copy(clean, stop)
            e2e.lose(stop)
        for d in (clean, stop):
            if not os.path.isdir(os.path.join(d, "agg")):
                print("COMPARE_READ_B_DONE|result=no_campaign|path=%s|json=0" % d)
                return 1
        jobs = []
        for name, src in (("clean", clean), ("stop", stop)):
            adapted = os.path.join(work, "evidence-" + name)
            adapt(src, adapted)
            for label, main_py, root in (("live", os.path.join(LIVE, "stripes_read_b", "__main__.py"), src),
                                         ("evidence", os.path.join(frac, "stripes_read_b", "__main__.py"), adapted)):
                out = os.path.join(work, "READ-%s-%s.hbp" % (label, name))
                if os.path.exists(out):
                    os.remove(out)
                argv = [sys.executable, "-I", main_py, "read"] + inputs(root) + ["--out", out]
                p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd="/")
                jobs.append((name, label, out, p))
        outs = {}
        for name, label, out, p in jobs:
            so, se = p.communicate()
            if p.returncode != 0:
                ok = False
                print("COMPARE_READ_B|campaign=%s|reader=%s|rc=%d|stdout=%s|json=0" % (
                    name, label, p.returncode, so.decode("ascii", "replace").strip()[:200].replace("|", "/")))
                sys.stderr.write(se.decode("ascii", "replace")[-2000:])
            outs[(name, label)] = out
        if ok:
            for name in ("clean", "stop"):
                ok = not compare(name, outs[(name, "live")], outs[(name, "evidence")], name == "stop") and ok
            tests = self_test(work, {n: (outs[(n, "live")], outs[(n, "evidence")]) for n in ("clean", "stop")})
            missed = [n for n, found in tests if not found]
            print("COMPARE_READ_B_SELF_TEST|plants=%d|found=%d|missed=%s|json=0" % (
                len(tests), len(tests) - len(missed), ",".join(missed) or "none"))
            ok = ok and not missed
    finally:
        if own and not keep:
            shutil.rmtree(work)
    print("COMPARE_READ_B_DONE|campaigns=2|engine_runs=0|row_points=0|result=%s|json=0" % (
        "within_allowlist" if ok else "outside_allowlist"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
