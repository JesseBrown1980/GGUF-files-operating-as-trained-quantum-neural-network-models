# Prints the mutant verdicts so far as a table. usage: show.py [file]
import glob
import os
import sys

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
rows = []
for d in sorted(glob.glob(W + "/out/mut/*/verdict.hbp")):
    l = open(d, encoding="utf8").read().strip()
    rows.append(dict(x.split("=", 1) for x in l.split("|")[1:] if "=" in x))
out = []
for f in rows:
    by = []
    if f["reader"] != "ran":
        by.append("reader_crash")
    if int(f["value_miss"]):
        by.append("reader_value(%s)" % f["value_miss"])
    if int(f["absent_miss"]):
        by.append("reader_absent(%s)" % f["absent_miss"])
    if f["route_value"] != "none":
        by.append("route(%s)" % f["route_value"])
    if f["route_other"] != "none":
        by.append("route_rows(%s)" % f["route_other"])
    if f["panic"] != "none":
        by.append("panic(%s)" % f["panic"])
    out.append("%-34s %-3s %-44s tomet=%-3s bnd=%s moved=%-3s lost=%-3s gain=%-3s %5ss %s" % (f["id"][:34], f["group"], ",".join(by) or "SURVIVED", f["miss_to_met"], f["boundary_miss"], f["fields_moved"], f["rows_lost"], f["rows_gained"], f["secs"], f["families"][:90]))
print("\n".join(out))
print("VERDICTS|%d" % len(rows))
