# Step 3: the reader's exit behaviour on damaged receipts, with the reader byte-identical to this head. Writes HBP rows.
import os
import re
import subprocess
import sys

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
READER = W + "/clean/polariton/read_prediction.py"
REC = open(W + "/clean/polariton/RECEIPT.hbp", encoding="utf8").read().splitlines()
TMP = W + "/out/reader_tests/"
os.makedirs(TMP, exist_ok=True)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
BASE = {}


def parse(text):
    out = {}
    for l in text.splitlines():
        if l.startswith("POLARITON_READ|"):
            f = dict(x.split("=", 1) for x in l.split("|")[1:] if "=" in x)
            out.setdefault(f["row"], []).append(f["result"])
    return out


def run(name, lines):
    path = TMP + name + ".hbp"
    open(path, "w", encoding="utf8", newline="\n").write("\n".join(lines) + "\n")
    p = subprocess.run(["python3", "-I", "-X", "utf8", READER, path], capture_output=True, text=True, encoding="utf8", env=env)
    os.remove(path)
    out = p.stdout.replace("\r", "")
    last = [l for l in out.splitlines() if l.startswith("POLARITON_READ_DONE")]
    rows = parse(out)
    return p.returncode, (last[0] if last else "no_done_line"), rows, p.stderr.strip().splitlines()[-1][:150] if p.stderr.strip() else ""


def report(name, lines, note=""):
    rc, last, rows, err = run(name, lines)
    gone = [k for k in BASE if k not in rows]
    new_miss = [k for k, v in rows.items() if "MISS" in v and "MISS" not in BASE.get(k, ["MET"])]
    met_now = [k for k, v in rows.items() if "MISS" not in v and "MISS" in BASE.get(k, ["MET"])]
    dup = [k for k, v in rows.items() if len(v) > 1]
    print("READER_TEST|case=%s|rc=%d|done=%s|rows_read=%d|reads_gone=%d|new_miss=%d|new_miss_names=%s|miss_gone_with_no_new_miss_row=%d|dup_names=%d|stderr=%s|note=%s|json=0" % (name, rc, last.replace("POLARITON_READ_DONE|", "").replace("|json=0", ""), len(rows), len(gone), len(new_miss), ",".join(new_miss[:6]), len([k for k in gone if "MISS" in BASE[k]]) + len(met_now), len(dup), err, note), flush=True)
    return rows


rc, last, BASE, err = run("whole", REC)
print("READER_TEST|case=whole|rc=%d|done=%s|rows=%d|json=0" % (rc, last, len(BASE)))
tags = {}
for l in REC:
    tags.setdefault(l.split("|")[0], []).append(l)
print("TAGS|%s|json=0" % "|".join("%s=%d" % (k, len(v)) for k, v in tags.items()))

# Every tag removed, one at a time.
for t in tags:
    if t == "POLARITON_DONE":
        continue
    report("tag_removed_" + t, [l for l in REC if not l.startswith(t + "|")])
# The eight the 8dfa11a lane removed, together.
eight = ("POLARITON_REVERSAL", "POLARITON_CONTROL_NO_BOSE", "POLARITON_SYMMETRY", "POLARITON_WAVEVECTOR", "POLARITON_QUENCH_BAND", "POLARITON_SECTOR_EQUALS_FULL", "POLARITON_QUENCH_OTHER_U", "POLARITON_TAYLOR_POINT")
report("eight_tags_removed", [l for l in REC if not l.startswith(tuple(t + "|" for t in eight))])
# Only the tags the reader's counts do not name.
report("taylor_and_other_u_removed", [l for l in REC if not l.startswith(("POLARITON_TAYLOR_POINT|", "POLARITON_TAYLOR_CONVERT|", "POLARITON_QUENCH_OTHER_U|"))])


def pick(tag, want):
    return [l for l in REC if l.startswith(tag + "|") and all(("|%s=%s|" % kv) in l for kv in want.items())]


# A single row deleted, on each read path.
for name, tag, want in (
    ("del_conversion_missed_row", "POLARITON_QUENCH_CONVERSION", {"N": "729", "delta": "0", "y": "1/108", "t": "2"}),
    ("del_quench_missed_row", "POLARITON_QUENCH", {"N": "6561", "delta": "-1", "t": "8"}),
    ("del_quench_pin_row", "POLARITON_QUENCH_PIN", {"N": "729", "delta": "0", "y": "1/1024", "t": "3"}),
    ("del_window_row", "POLARITON_PIN_WINDOW", {"N": "729", "u": "3/4", "x": "0", "s": "4"}),
    ("del_pin_row", "POLARITON_PIN", {"N": "729", "u": "1/2", "x": "0", "s": "4"}),
    ("del_sector_row", "POLARITON_SECTOR", {"N": "43046721", "u": "1/2", "x": "1/2"}),
    ("del_rotor_row", "POLARITON_SECTOR", {"N": "531441", "u": "1/2", "x": "0", "P": "3"}),
    ("del_band_row", "POLARITON_QUENCH_BAND", {"N": "6561", "delta": "1"}),
    ("del_reversal_row", "POLARITON_REVERSAL", {"N": "243", "full": "1"}),
):
    p = pick(tag, want)
    assert len(p) == 1, (name, len(p))
    rows = report(name, [l for l in REC if l != p[0]], note="count_expected_one_less")
    # The same deletion with another row of that tag written twice, so the per-tag count stays.
    other = [l for l in tags[tag] if l != p[0]][0]
    i = REC.index(p[0])
    swap = REC[:i] + [other] + REC[i + 1:]
    report(name + "_with_a_duplicate", swap, note="tag_count_kept")

# A row with its tag kept and its value field removed, and a row with a non-integer value.
p = pick("POLARITON_QUENCH", {"N": "6561", "delta": "0", "t": "1"})[0]
report("field_removed_energy", [l if l != p else re.sub(r"\|energy_off_1e-9=[^|]*", "", l) for l in REC])
# A receipt where one met row turns to a miss: the reader's exit code, which the workflow's set -e reads.
p = pick("POLARITON_PIN_WINDOW", {"N": "729", "u": "3/4", "x": "0", "s": "4"})[0]
report("value_pushed_to_a_miss", [l if l != p else re.sub(r"\|B_ppb=-?\d+", "|B_ppb=1", l) for l in REC])
# An empty receipt, and one with only the done row.
report("only_done_row", [REC[-1]])
