# Runs mutants at ce44be7 against the real reader and the exact route.
# The read: the whole filed receipt, with the rows of the lite stages replaced by the mutant's rows. So the reader is byte-identical to the one filed, rows outside lite keep their filed values,
# a kill is a real kill (every row it read is a row the real run would print), and a survivor may still die at a size lite did not rerun.
# usage: mutate_run.py BUDGET_SECONDS PARALLEL [ids or id prefixes...]
import concurrent.futures as cf
import os
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-engine-20261105/tools")
from mutants_def import M
from mutants_more import M2

M = M + M2

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
BIN = W + "/target/release/"
OUT = W + "/out/mut/"
READER = W + "/clean/polariton/read_prediction.py"
ROUTE = W + "/clean/polariton/second_route.py"
RECEIPT = open(W + "/clean/polariton/RECEIPT.hbp", encoding="utf8").read().splitlines()
READ_FILED = open(W + "/clean/polariton/READ.hbp", encoding="utf8").read()
os.makedirs(OUT, exist_ok=True)
F_STAGES = ["taylor", "control", "reversal", "wavevector", "quench_pin", "quench", "pin", "window", "conversion"]
GROUPS = {
    "S": ["rotor", "sector"],
    "SL": ["rotor", "sector", "pin", "window"],
    "F": F_STAGES,
    "L": ["pin", "window"],
    "W": ["window"],
    "C": ["taylor", "conversion"],
    "Q": ["control", "wavevector", "quench_pin", "quench"],
    "V": ["reversal"],
    "B": ["taylor", "control", "reversal", "wavevector", "rotor", "quench_pin", "quench", "pin", "sector", "window", "conversion"],
}
ALL = GROUPS["B"]
FBATCHES = [["taylor", "control", "quench_pin", "reversal"], ["quench"], ["pin"], ["window"], ["wavevector", "conversion"]]
# Rows whose read mixes a lite row with a filed row, so a move there can be an artefact of this hybrid: counted apart.
BOUNDARY = {"critical_jbar_ratio_u=1/2_N=1594323_to_4782969", "critical_gap_ratio_u=1/2_N=1594323_to_4782969", "susceptibility_ratio_N=243_to_729"}
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
ID_FIELDS = ("N", "u", "x", "y", "s", "delta", "t", "P", "full")
VALUE_SKIP = set(ID_FIELDS) | {"json", "dt", "fd_step", "cycles", "steps", "grid_step", "predicted_x", "stages"}


def fields(line):
    return dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f)


def key(line):
    tag = line.split("|", 1)[0]
    f = fields(line)
    return (tag,) + tuple(f.get(k, "") for k in ID_FIELDS)


def py(script, *args, timeout=1500):
    try:
        p = subprocess.run(["python3", "-I", "-X", "utf8", script, *args], capture_output=True, text=True, encoding="utf8", timeout=timeout, env=env)
        return p.returncode, p.stdout.replace("\r", ""), p.stderr[-300:]
    except subprocess.TimeoutExpired:
        return 99, "", "timeout"


def run_stage(exe, stage, timeout=900):
    try:
        p = subprocess.run([exe, stage], capture_output=True, text=True, timeout=timeout)
        rows = [l for l in p.stdout.splitlines() if not l.startswith("POLARITON_DONE")]
        return p.returncode, rows, p.stderr[-300:]
    except subprocess.TimeoutExpired:
        return 99, [], "timeout"


def read_rows(text):
    out = {}
    for l in text.splitlines():
        if l.startswith("POLARITON_READ|"):
            f = fields(l)
            out[f["row"]] = (f["result"], f.get("read"), f.get("predicted"))
    return out


def base_rows():
    d = OUT + "base/"
    os.makedirs(d, exist_ok=True)
    res = {}
    for s in ALL:
        fp = d + s + ".rows"
        if not os.path.exists(fp):
            t = time.time()
            rc, rows, err = run_stage(BIN + "m_base.exe", s)
            assert rc == 0, (s, err)
            open(fp, "w", encoding="utf8", newline="\n").write("\n".join(rows) + "\n")
            print("BASE_STAGE|%s|rows=%d|secs=%d" % (s, len(rows), time.time() - t), flush=True)
        res[s] = open(fp, encoding="utf8").read().splitlines()
    return res


def hybrid(base, stage_rows):
    filed_keys = {key(l) for l in RECEIPT}
    replaced, deleted, extra = {}, set(), []
    for stage in ALL:
        rows = stage_rows.get(stage, base[stage])
        base_keys = {key(l) for l in base[stage]}
        new = {}
        for l in rows:
            new[key(l)] = l
        for k in base_keys:
            if k in new:
                replaced[k] = new[k]
                # Lite-only rows, N = 81 quench_pin and N = 27 reversal, have no filed partner: they go in beside the filed rows.
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


def lanes(rows):
    """The exact route's lanes on these rows, each with the slice of rows that decides it, for a cache by bytes."""
    keep = {
        "taylor": [l for l in rows if l.startswith("POLARITON_TAYLOR_POINT|")],
        "convert": [l for l in rows if l.startswith("POLARITON_TAYLOR_CONVERT|")],
        "sector": [l for l in rows if l.startswith("POLARITON_SECTOR|") and int(fields(l)["N"]) <= 243],
        "full": [l for l in rows if l.startswith(("POLARITON_PIN|", "POLARITON_PIN_WINDOW|")) and int(fields(l)["N"]) <= 3],
    }
    return keep


ROUTE_ARGS = {"taylor": ("taylor_compare", None), "convert": ("convert_compare", None), "sector": ("sector_compare", None, "243"), "full": ("full_compare", None, "3")}
route_cache = {}


def route(name, slice_rows, path):
    k = (name, "\n".join(slice_rows))
    if k in route_cache:
        return route_cache[k]
    args = [a if a is not None else path for a in ROUTE_ARGS[name]]
    rc, out, err = py(ROUTE, *args)
    m = re.search(r"\|rows=(\d+)\|bad=(\d+)", out)
    if rc in (0, 1) and m:
        res = "rows=%s:bad=%s" % (m.group(1), m.group(2))
    else:
        res = "crash:rc=%d" % rc
    route_cache[k] = res
    return res


def moved(base, stage_rows):
    """The largest move of every value field, by tag, against the base, for rows with a partner; and rows lost or gained."""
    sizes = {}
    lost, gained = 0, 0
    for stage, rows in stage_rows.items():
        b = {key(l): l for l in base[stage]}
        n = {key(l): l for l in rows}
        lost += sum(k not in n for k in b)
        gained += sum(k not in b for k in n)
        for k, l in n.items():
            if k not in b or b[k] == l:
                continue
            fa, fb = fields(b[k]), fields(l)
            for name, va in fa.items():
                if name in VALUE_SKIP or name not in fb or fb[name] == va:
                    continue
                try:
                    x, y = int(va), int(fb[name])
                except ValueError:
                    sizes.setdefault((k[0], name), [None, None, "text:%s->%s" % (va, fb[name])])
                    continue
                d = abs(y - x)
                rel = d * 10 ** 6 // max(abs(x), 1)
                cur = sizes.get((k[0], name))
                if cur is None or cur[0] is None or d > cur[0]:
                    sizes[(k[0], name)] = [d, rel, "N=%s,%s->%s" % (k[1], va, fb[name])]
    return sizes, lost, gained


def run(mid, grp, base, baseread, baseroutes):
    d = OUT + mid + "/"
    os.makedirs(d, exist_ok=True)
    vf = d + "verdict.hbp"
    if os.path.exists(vf):
        return open(vf, encoding="utf8").read()
    t = time.time()
    exe = BIN + "m_%s.exe" % mid.lower().replace("^", "")
    stage_rows, panic = {}, []
    rec = d + "receipt.hbp"
    # Group F was killed whole at 8dfa11a, so its stages run in batches, cheapest first, and stop at the first batch where the reader reads a value miss. Every other group runs whole.
    batches = FBATCHES if grp == "F" else [GROUPS[grp]]
    for batch in batches:
        for s in batch:
            rc, rows, err = run_stage(exe, s)
            if rc != 0:
                panic.append("%s:%s" % (s, "timeout" if rc == 99 else "rc=%d" % rc))
                open(d + s + ".err", "w", encoding="utf8", newline="\n").write(err)
                continue
            stage_rows[s] = rows
        rows = hybrid(base, stage_rows)
        open(rec, "w", encoding="utf8", newline="\n").write("\n".join(rows) + "\n")
        rc, out, err = py(READER, rec)
        r = read_rows(out) if rc == 0 else None
        if r is None or any(v[0] == "MISS" and baseread.get(k, ("MET",))[0] == "MET" and k not in BOUNDARY and v[1] != "no_row" and not k.startswith("rows_") and k != "hand_rows" for k, v in r.items()):
            break
    open(d + "read.hbp", "w", encoding="utf8", newline="\n").write(out)
    if r is None:
        reader = "reader_crash"
        value, absent, boundary, tomet, lost, note = [], [], [], [], [], err.strip().splitlines()[-1][:120] if err.strip() else ""
    else:
        new = [k for k, v in r.items() if v[0] == "MISS" and baseread.get(k, ("MET",))[0] == "MET"]
        boundary = [k for k in new if k in BOUNDARY]
        new = [k for k in new if k not in BOUNDARY]
        absent = [k for k in new if r[k][1] == "no_row" or k.startswith("rows_") or k == "hand_rows"]
        value = [k for k in new if k not in absent]
        tomet = [k for k, v in r.items() if v[0] == "MET" and baseread.get(k, ("MET",))[0] == "MISS"]
        lost = [k for k in baseread if k not in r]
        reader, note = "ran", ""
    fam = sorted(set(re.sub(r"(_N=.*|_u=.*|_delta=.*|_t=.*|_s=.*)$", "", k) for k in value))
    fam_absent = sorted(set(re.sub(r"(_N=.*|_u=.*|_delta=.*|_t=.*|_s=.*)$", "", k) for k in absent))
    keep = lanes(rows)
    routes = {}
    for name in ("taylor", "convert", "sector", "full"):
        routes[name] = route(name, keep[name], rec)
    route_value = [k for k, v in routes.items() if v != baseroutes[k] and ":bad=0" not in v]
    route_other = [k for k, v in routes.items() if v != baseroutes[k] and k not in route_value]
    sizes, row_lost, row_gained = moved(base, stage_rows)
    with open(d + "size.hbp", "w", encoding="utf8", newline="\n") as h:
        for (tag, name), v in sorted(sizes.items()):
            h.write("MOVE|id=%s|tag=%s|field=%s|largest=%s|rel_ppm=%s|where=%s|json=0\n" % (mid, tag, name, v[0], v[1], v[2]))
    killed_value = r is None or bool(value)
    killed = killed_value or bool(absent) or bool(route_value) or bool(panic)
    v = "MUTANT|id=%s|group=%s|killed=%d|reader=%s|value_miss=%d|absent_miss=%d|boundary_miss=%d|miss_to_met=%d|read_rows_lost=%d|route_value=%s|route_other=%s|panic=%s|rows_lost=%d|rows_gained=%d|fields_moved=%d|families=%s|families_absent=%s|routes=%s|secs=%d|stages_run=%s|note=%s|json=0\n" % (
        mid, grp, killed, reader, len(value), len(absent), len(boundary), len(tomet), len(lost), ",".join(route_value) or "none", ",".join(route_other) or "none", ",".join(panic) or "none", row_lost, row_gained, len(sizes), ",".join(fam) or "none", ",".join(fam_absent) or "none", ",".join("%s:%s" % kv for kv in routes.items()), time.time() - t, "+".join(stage_rows), note)
    open(vf, "w", encoding="utf8", newline="\n").write(v)
    os.remove(rec)
    return v


def main():
    budget = int(sys.argv[1])
    par = int(sys.argv[2])
    ids = sys.argv[3:]
    t0 = time.time()
    base = base_rows()
    # Every base row that has a filed partner must be byte-equal to it.
    filed = {key(l): l for l in RECEIPT}
    in_receipt, not_equal, no_partner = 0, [], []
    for s in ALL:
        for l in base[s]:
            k = key(l)
            if k not in filed:
                no_partner.append(l.split("|")[0] + "|" + fields(l).get("N", ""))
            elif filed[k] == l:
                in_receipt += 1
            else:
                not_equal.append(l[:120])
    print("BASE_ROWS|byte_equal_to_receipt=%d|different=%d|no_filed_partner=%d|first_different=%s|json=0" % (in_receipt, len(not_equal), len(no_partner), not_equal[:2]), flush=True)
    assert not not_equal
    rows = hybrid(base, {s: base[s] for s in ALL})
    rec = OUT + "base/receipt.hbp"
    open(rec, "w", encoding="utf8", newline="\n").write("\n".join(rows) + "\n")
    brf = OUT + "base/read.hbp"
    if not os.path.exists(brf):
        rc, o, e = py(READER, rec)
        assert rc == 0, e
        open(brf, "w", encoding="utf8", newline="\n").write(o)
    baseread = read_rows(open(brf, encoding="utf8").read())
    filedread = read_rows(READ_FILED)
    different = [k for k in filedread if baseread.get(k) != filedread[k]]
    extra = [k for k in baseread if k not in filedread]
    print("BASE_READ|rows=%d|met=%d|miss=%d|filed_rows=%d|filed_rows_read_otherwise=%s|extra_rows=%d|extra_rows_missed=%d|json=0" % (len(baseread), sum(v[0] == "MET" for v in baseread.values()), sum(v[0] == "MISS" for v in baseread.values()), len(filedread), ",".join(different), len(extra), sum(baseread[k][0] == "MISS" for k in extra)), flush=True)
    keep = lanes(rows)
    baseroutes = {name: route(name, keep[name], rec) for name in ("taylor", "convert", "sector", "full")}
    print("BASE_ROUTES|%s|secs=%d|json=0" % (",".join("%s:%s" % kv for kv in baseroutes.items()), time.time() - t0), flush=True)
    order = {"V": 0, "Q": 1, "C": 2, "S": 3, "SL": 4, "F": 5, "W": 6, "L": 7}
    todo = sorted([m for m in M if (not ids or any(m[0] == i or m[0].startswith(i) for i in ids)) and not os.path.exists(OUT + m[0] + "/verdict.hbp")], key=lambda m: order[m[1]])
    print("TODO|%d" % len(todo), flush=True)
    with cf.ThreadPoolExecutor(par) as ex:
        fut = {}
        while todo or fut:
            while todo and len(fut) < par and time.time() - t0 < budget:
                m = todo.pop(0)
                fut[ex.submit(run, m[0], m[1], base, baseread, baseroutes)] = m[0]
            if not fut:
                break
            done, _ = cf.wait(list(fut), return_when=cf.FIRST_COMPLETED)
            for f in done:
                try:
                    print(f.result().strip(), flush=True)
                except Exception as e:
                    print("ERROR", fut[f], repr(e)[:300], flush=True)
                fut.pop(f)
    print("REMAIN|%d" % len(todo), flush=True)


main()
