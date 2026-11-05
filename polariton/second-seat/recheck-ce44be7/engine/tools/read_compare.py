# Step 3: third-run/READ.hbp against READ.hbp, row by row, and the head reader run on the third-run receipt so that the reader's own change and the data's change come apart.
import re
import subprocess
import sys

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
CLEAN = W + "/clean/polariton"
OUT = W + "/out"


def parse(text):
    rows = {}
    order = []
    for line in text.splitlines():
        if not line.startswith("POLARITON_READ|"):
            continue
        f = dict(x.split("=", 1) for x in line.split("|")[1:] if "=" in x)
        rows[f["row"]] = (f["result"], f.get("read", ""), f.get("predicted", ""))
        order.append(f["row"])
    return rows, order


def fam(name):
    return re.sub(r"(_N=.*|_u=.*|_delta=.*|_t=.*|_s=.*)$", "", name)


def tally(rows):
    out = {}
    for k, v in rows.items():
        d = out.setdefault(fam(k), [0, 0])
        d[0 if v[0] == "MET" else 1] += 1
    return out


def compare(label, old, new, handle):
    oldr, _ = old
    newr, _ = new
    only_old = [k for k in oldr if k not in newr]
    only_new = [k for k in newr if k not in oldr]
    both = [k for k in oldr if k in newr]
    verdict = [k for k in both if oldr[k][0] != newr[k][0]]
    read = [k for k in both if oldr[k][1] != newr[k][1]]
    pred = [k for k in both if oldr[k][2] != newr[k][2]]
    print("COMPARE|%s|old_rows=%d|new_rows=%d|only_old=%d|only_new=%d|verdict_changed=%d|read_changed=%d|predicted_changed=%d|new_rows_missed=%d|json=0" % (label, len(oldr), len(newr), len(only_old), len(only_new), len(verdict), len(read), len(pred), sum(newr[k][0] != "MET" for k in only_new)))
    for k in only_old:
        handle.write("ONLY_OLD|%s|row=%s|old=%s|json=0\n" % (label, k, oldr[k]))
    for k in only_new:
        handle.write("ONLY_NEW|%s|row=%s|new=%s,%s,%s|json=0\n" % (label, k, *newr[k]))
    for k in verdict:
        handle.write("VERDICT_CHANGED|%s|row=%s|old=%s,%s,%s|new=%s,%s,%s|json=0\n" % (label, k, *oldr[k], *newr[k]))
    for k in read:
        handle.write("READ_CHANGED|%s|row=%s|old=%s|new=%s|result_old=%s|result_new=%s|json=0\n" % (label, k, oldr[k][1], newr[k][1], oldr[k][0], newr[k][0]))
    for k in pred:
        handle.write("PREDICTED_CHANGED|%s|row=%s|old=%s|new=%s|json=0\n" % (label, k, oldr[k][2], newr[k][2]))
    fams = {}
    for k in read:
        fams[fam(k)] = fams.get(fam(k), 0) + 1
    print("READ_CHANGED_FAMILIES|%s|%s|json=0" % (label, "|".join("%s=%d" % kv for kv in sorted(fams.items()))))
    fams = {}
    for k in only_new:
        fams[fam(k)] = fams.get(fam(k), 0) + 1
    print("ONLY_NEW_FAMILIES|%s|%s|json=0" % (label, "|".join("%s=%d" % kv for kv in sorted(fams.items()))))
    print("ONLY_OLD_ROWS|%s|%s|json=0" % (label, ",".join(only_old)))
    print("VERDICT_CHANGED_ROWS|%s|%s|json=0" % (label, ",".join(verdict)))
    return verdict, read


third = open(CLEAN + "/third-run/READ.hbp", encoding="utf-8").read()
head = open(CLEAN + "/READ.hbp", encoding="utf-8").read()
env_args = ["python3", "-I", "-X", "utf8", CLEAN + "/read_prediction.py", CLEAN + "/third-run/RECEIPT.hbp"]
p = subprocess.run(env_args, capture_output=True, text=True, encoding="utf-8")
print("HEAD_READER_ON_THIRD_RECEIPT|rc=%d|last=%s|stderr=%s|json=0" % (p.returncode, p.stdout.strip().splitlines()[-1] if p.stdout.strip() else "", p.stderr[-200:].replace("\n", " ")))
open(OUT + "/head_reader_on_third_receipt.hbp", "w", encoding="utf-8", newline="\n").write(p.stdout)
a = parse(third)
b = parse(head)
c = parse(p.stdout)
print("DONE_ROWS|third=%s|head=%s|json=0" % (third.strip().splitlines()[-1], head.strip().splitlines()[-1]))
with open(OUT + "/read_diff.hbp", "w", encoding="utf-8", newline="\n") as h:
    compare("third_read_vs_head_read", a, b, h)
    compare("third_read_vs_head_reader_on_third_receipt", a, c, h)
    compare("head_reader_on_third_receipt_vs_head_read", c, b, h)
print("MISSES_THIRD|%s|json=0" % ",".join(k for k, v in a[0].items() if v[0] != "MET"))
print("MISSES_HEAD|%s|json=0" % ",".join(k for k, v in b[0].items() if v[0] != "MET"))
t = tally(b[0])
print("FAMILY_TALLY_HEAD|%s|json=0" % "|".join("%s=%d/%d" % (k, v[0], v[1]) for k, v in sorted(t.items())))
