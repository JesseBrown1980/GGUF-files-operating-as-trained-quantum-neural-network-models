# Survivors against the held reader and route: the mutant's stages over the filed receipt, as in mutate_run.py, read by holdcopy/ in place of clean/.
# usage: held_on_mutant.py ID ...   (reruns each mutant's group)
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-engine-20261105/tools")
from mutants_def import M
from mutants_more import M2

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
BIN = W + "/target/release/"
OUT = W + "/out/held/"
os.makedirs(OUT, exist_ok=True)
BASE = W + "/out/mut/base/"
RECEIPT = open(W + "/clean/polariton/RECEIPT.hbp", encoding="utf8").read().splitlines()
HELD_READER = W + "/holdcopy/polariton/read_prediction.py"
HELD_ROUTE = W + "/holdcopy/polariton/second_route.py"
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
GROUPS = {"S": ["rotor", "sector"], "SL": ["rotor", "sector", "pin", "window"], "F": ["taylor", "control", "reversal", "wavevector", "quench_pin", "quench", "pin", "window", "conversion"], "L": ["pin", "window"], "W": ["window"], "C": ["taylor", "conversion"], "Q": ["control", "wavevector", "quench_pin", "quench"], "V": ["reversal"]}
ALL = ["taylor", "control", "reversal", "wavevector", "rotor", "quench_pin", "quench", "pin", "sector", "window", "conversion"]
ID_FIELDS = ("N", "u", "x", "y", "s", "delta", "t", "P", "full")
base = {s: open(BASE + s + ".rows", encoding="utf8").read().splitlines() for s in ALL}


def fields(line):
    return dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f)


def key(line):
    f = fields(line)
    return (line.split("|", 1)[0],) + tuple(f.get(k, "") for k in ID_FIELDS)


def hybrid(stage_rows):
    filed_keys = {key(l) for l in RECEIPT}
    replaced, deleted, extra = {}, set(), []
    for stage in ALL:
        rows = stage_rows.get(stage, base[stage])
        base_keys = {key(l) for l in base[stage]}
        new = {key(l): l for l in rows}
        for k in base_keys:
            if k in new:
                replaced[k] = new[k]
                if k not in filed_keys:
                    extra.append(new[k])
            else:
                deleted.add(k)
        for k, l in new.items():
            if k not in base_keys:
                extra.append(l)
    out = []
    for l in RECEIPT:
        if l.startswith("POLARITON_DONE"):
            continue
        k = key(l)
        if k in deleted:
            continue
        out.append(replaced.get(k, l))
    out += extra
    out.append(RECEIPT[-1])
    return out


def read(path):
    p = subprocess.run(["python3", "-I", "-X", "utf8", HELD_READER, path], capture_output=True, text=True, encoding="utf8", env=env)
    rows = {}
    for l in p.stdout.replace("\r", "").splitlines():
        if l.startswith("POLARITON_READ|"):
            f = fields(l)
            rows[f["row"]] = f["result"]
    return p.returncode, rows, p.stderr.strip()[-160:]


basepath = OUT + "base.hbp"
open(basepath, "w", encoding="utf8", newline="\n").write("\n".join(hybrid({})) + "\n")
rc, baseread, err = read(basepath)
print("HELD_BASE|rc=%d|rows=%d|miss=%d|json=0" % (rc, len(baseread), sum(v == "MISS" for v in baseread.values())), flush=True)
table = {m[0]: m for m in M + M2}
for mid in sys.argv[1:]:
    _, grp, _ = table[mid]
    exe = BIN + "m_%s.exe" % mid.lower().replace("^", "")
    stage_rows, panic = {}, []
    for s in GROUPS[grp]:
        p = subprocess.run([exe, s], capture_output=True, text=True, timeout=1200)
        if p.returncode != 0:
            panic.append(s)
            continue
        stage_rows[s] = [l for l in p.stdout.splitlines() if not l.startswith("POLARITON_DONE")]
    path = OUT + mid + ".hbp"
    rows = hybrid(stage_rows)
    open(path, "w", encoding="utf8", newline="\n").write("\n".join(rows) + "\n")
    rc, r, err = read(path)
    new = [k for k, v in r.items() if v == "MISS" and baseread.get(k, "MET") == "MET"]
    fams = sorted(set(re.sub(r"(_N=.*|_u=.*|_delta=.*|_t=.*|_s=.*)$", "", k) for k in new))
    route = {}
    changed = {
        "full": ("full_compare", path, "3"),
        "convert": ("convert_compare", path),
    }
    for name, args in changed.items():
        tag = "POLARITON_TAYLOR_CONVERT|" if name == "convert" else ("POLARITON_PIN|", "POLARITON_PIN_WINDOW|")
        here = [l for l in rows if l.startswith(tag) and (name == "convert" or int(fields(l)["N"]) <= 3)]
        there = [l for s in ALL for l in base[s] if l.startswith(tag) and (name == "convert" or int(fields(l)["N"]) <= 3)]
        if sorted(here) == sorted(there):
            route[name] = "same_rows"
            continue
        q = subprocess.run(["python3", "-I", "-X", "utf8", HELD_ROUTE, *args], capture_output=True, text=True, encoding="utf8", env=env)
        m = re.search(r"\|rows=(\d+)\|bad=(\d+)", q.stdout)
        route[name] = "rows=%s:bad=%s" % (m.group(1), m.group(2)) if m else "crash:rc=%d" % q.returncode
    print("HELD_READ|id=%s|panic=%s|rc=%d|new_miss=%d|families=%s|held_route=%s|err=%s|json=0" % (mid, ",".join(panic) or "none", rc, len(new), ",".join(fams) or "none", ",".join("%s:%s" % kv for kv in route.items()), err if rc else ""), flush=True)
    os.remove(path)
os.remove(basepath)
print("HELD_DONE", flush=True)
