# The mutation table and its counts, from the verdict files. Survivors carry the size of what they move, from size.hbp.
import glob
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-engine-20261105/tools")
from mutants_def import M
from mutants_more import M2

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
OLD = {"S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S11", "S12", "S13", "S14", "S15", "S16", "S17", "S18", "S19", "S20", "F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08", "F09", "F10", "F11", "T01", "T02", "T03", "T04", "T05", "R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09", "R10", "R11", "R12", "R13", "R14", "R15", "R16", "R17", "R18", "R19", "R20", "L01", "L02", "L03", "L04"}
order = [m[0] for m in M] + [m[0] for m in M2]
rows = {}
for mid in order:
    p = W + "/out/mut/" + mid + "/verdict.hbp"
    if os.path.exists(p):
        l = open(p, encoding="utf8").read().strip()
        rows[mid] = dict(x.split("=", 1) for x in l.split("|")[1:] if "=" in x)


def kind(f):
    k = []
    if f["reader"] != "ran":
        k.append("reader_crash")
    if int(f["value_miss"]):
        k.append("reader_value")
    if int(f["absent_miss"]):
        k.append("reader_absent")
    if f["route_value"] != "none":
        k.append("route_value")
    if f["panic"] != "none":
        k.append("panic")
    return k


def sizes(mid):
    p = W + "/out/mut/" + mid + "/size.hbp"
    out = []
    if os.path.exists(p):
        for l in open(p, encoding="utf8").read().splitlines():
            f = dict(x.split("=", 1) for x in l.split("|")[1:] if "=" in x)
            if f["field"] in ("residual_1e-12",):
                continue
            out.append((f["tag"].replace("POLARITON_", ""), f["field"], f["largest"], f["rel_ppm"], f["where"]))
    return out


out = []
for mid, f in rows.items():
    k = kind(f)
    detail = []
    if int(f["value_miss"]):
        detail.append("reader_value=%s" % f["value_miss"])
    if int(f["absent_miss"]):
        detail.append("reader_absent=%s" % f["absent_miss"])
    if f["reader"] != "ran":
        detail.append("reader_crash")
    if f["route_value"] != "none":
        detail.append("route=" + f["route_value"])
    if f["route_other"] != "none":
        detail.append("route_prints_other_rows_exit_0=" + f["route_other"])
    if f["panic"] != "none":
        detail.append("panic=" + f["panic"])
    if int(f["miss_to_met"]):
        detail.append("miss_to_met=%s" % f["miss_to_met"])
    if int(f["read_rows_lost"]):
        detail.append("reads_lost=%s" % f["read_rows_lost"])
    if int(f["boundary_miss"]):
        detail.append("boundary=%s" % f["boundary_miss"])
    out.append("%-34s %-3s %s %s %s" % (mid[:34], f["group"], "SURVIVED" if not k else "killed", " ".join(detail), ("families=" + f["families"]) if f["families"] != "none" else ""))
print("MUTANT TABLE. reader_value = new misses on a value; reader_absent = new misses because a row is gone or a tag count moved; route = a lane read bad rows; route_prints_other_rows_exit_0 = the lane still exits 0 on a different row count, which only the workflow's cmp of the filed route rows sees, so it does not count as a kill here; panic = a stage exited nonzero or timed out.")
print("\n".join(out))


def rate(ids, label):
    ids = [i for i in ids if i in rows]
    killed = [i for i in ids if kind(rows[i])]
    by_value = [i for i in killed if "reader_value" in kind(rows[i]) or "reader_crash" in kind(rows[i])]
    route_only = [i for i in killed if i not in by_value and "route_value" in kind(rows[i])]
    panic_only = [i for i in killed if i not in by_value and i not in route_only and "panic" in kind(rows[i])]
    absent_only = [i for i in killed if i not in by_value and i not in route_only and i not in panic_only]
    print("RATE|%s|run=%d|killed=%d|reader_on_value=%d|route_on_value_alone=%d|panic_alone=%d|absent_rows_alone=%d|survived=%d|json=0" % (label, len(ids), len(killed), len(by_value), len(route_only), len(panic_only), len(absent_only), len(ids) - len(killed)))


rate([i for i in rows if i[:3] in OLD], "earlier_59")
rate([i for i in rows if i[:3] not in OLD], "new")
rate(list(rows), "all")
print("SURVIVORS, with the largest move of each field against the base rows:")
for mid, f in rows.items():
    if not kind(f):
        s = sizes(mid)
        s.sort(key=lambda r: -int(r[3]) if r[3] not in ("None",) else 0)
        print("%s|rows_lost=%s|rows_gained=%s|%s" % (mid, f["rows_lost"], f["rows_gained"], ";".join("%s.%s:%s(%sppm,%s)" % r for r in s[:4]) or "no_field_moved_in_rows_with_a_partner"))
missing = [m for m in order if m not in rows]
print("NOT_RUN|%d|%s" % (len(missing), ",".join(missing)))
