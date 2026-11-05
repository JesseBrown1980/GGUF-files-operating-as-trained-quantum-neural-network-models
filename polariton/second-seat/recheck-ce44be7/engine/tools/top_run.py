# The top mutants: the whole sector stage to 3^16, merged into the filed receipt, with the real reader and the real sector_compare and top_compare.
# usage: top_run.py [ids...]
import os
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-engine-20261105/tools")
from mutants_def import TOP

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
BIN = W + "/target/release/"
OUT = W + "/out/top/"
READER = W + "/clean/polariton/read_prediction.py"
ROUTE = W + "/clean/polariton/second_route.py"
RECEIPT = open(W + "/clean/polariton/RECEIPT.hbp", encoding="utf8").read().splitlines()
os.makedirs(OUT, exist_ok=True)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def py(script, *args):
    p = subprocess.run(["python3", "-I", "-X", "utf8", script, *args], capture_output=True, text=True, encoding="utf8", env=env)
    return p.returncode, p.stdout.replace("\r", ""), p.stderr[-200:]


def fields(line):
    return dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f)


def key(line):
    f = fields(line)
    return (f["N"], f["u"], f["x"], f["P"])


def read_rows(text):
    out = {}
    for l in text.splitlines():
        if l.startswith("POLARITON_READ|"):
            f = fields(l)
            out[f["row"]] = (f["result"], f.get("read"), f.get("predicted"))
    return out


filed_read = read_rows(open(W + "/clean/polariton/READ.hbp", encoding="utf8").read())
ids = sys.argv[1:]
todo = [("X00_base", "x_base")] + [(m, "x_" + m.lower().replace("^", "")) for m, _ in TOP]
for mid, exe in todo:
    if ids and not any(mid.startswith(i) for i in ids):
        continue
    d = OUT + mid + "/"
    os.makedirs(d, exist_ok=True)
    if os.path.exists(d + "verdict.hbp"):
        print(open(d + "verdict.hbp", encoding="utf8").read().strip(), flush=True)
        continue
    t = time.time()
    p = subprocess.run([BIN + exe + ".exe", "sector"], capture_output=True, text=True)
    rows = [l for l in p.stdout.splitlines() if l.startswith("POLARITON_SECTOR|")]
    open(d + "sector.rows", "w", encoding="utf8", newline="\n").write("\n".join(rows) + "\n")
    new = {key(l): l for l in rows}
    merged = [new.get(key(l), l) if l.startswith("POLARITON_SECTOR|") else l for l in RECEIPT]
    rec = d + "receipt.hbp"
    open(rec, "w", encoding="utf8", newline="\n").write("\n".join(merged) + "\n")
    moved = sum(1 for a, b in zip(merged, RECEIPT) if a != b)
    rc, out, err = py(READER, rec)
    r = read_rows(out)
    miss = [k for k, v in r.items() if v[0] == "MISS" and filed_read.get(k, ("MET",))[0] == "MET"]
    met = [k for k, v in r.items() if v[0] == "MET" and filed_read.get(k, ("MET",))[0] == "MISS"]
    rc1, out1, err1 = py(ROUTE, "sector_compare", rec, "243")
    m1 = re.search(r"\|rows=(\d+)\|bad=(\d+)", out1)
    off = [int(x) for x in re.findall(r"off_units_of_2\^-60=(\d+)", out1)]
    rc2, out2, err2 = py(ROUTE, "top_compare", rec, "59049")
    m2 = re.search(r"\|rows=(\d+)\|bad=(\d+)", out2)
    top = [l for l in out2.splitlines() if l.startswith("SECOND_ROUTE_TOP|")]
    ja = [int(re.findall(r"off_ppm=(\d+)", l)[0]) for l in top]
    ga = [int(re.findall(r"off_ppm=(\d+)", l)[1]) for l in top]
    v = "TOP_MUTANT|id=%s|stage_rc=%d|sector_rows=%d|rows_moved=%d|reader_rc=%d|new_miss=%d|miss_to_met=%d|new_miss_names=%s|sector_route=rows=%s:bad=%s|largest_units=%d|top_route=rows=%s:bad=%s|top_rc=%d|largest_jbar_ppm=%d|largest_gap_ppm=%d|secs=%d|json=0\n" % (
        mid, p.returncode, len(rows), moved, rc, len(miss), len(met), ",".join(miss[:8]) or "none", m1.group(1) if m1 else "?", m1.group(2) if m1 else "?", max(off) if off else -1, m2.group(1) if m2 else "?", m2.group(2) if m2 else "?", rc2, max(ja) if ja else -1, max(ga) if ga else -1, time.time() - t)
    open(d + "verdict.hbp", "w", encoding="utf8", newline="\n").write(v)
    os.remove(rec)
    print(v.strip(), flush=True)
print("TOP_DONE", flush=True)
