# The held reader and the filed reader on receipts edited the way a mutant would print them. The edit acts on the whole filed receipt, so this read is the full size and needs no rerun.
import os
import re
import subprocess

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
FILED = W + "/clean/polariton/read_prediction.py"
HELD = W + "/holdcopy/polariton/read_prediction.py"
REC = open(W + "/clean/polariton/RECEIPT.hbp", encoding="utf8").read().splitlines()
TMP = W + "/out/hold_tests/"
os.makedirs(TMP, exist_ok=True)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def run(reader, path):
    p = subprocess.run(["python3", "-I", "-X", "utf8", reader, path], capture_output=True, text=True, encoding="utf8", env=env)
    rows = {}
    for l in p.stdout.replace("\r", "").splitlines():
        if l.startswith("POLARITON_READ|"):
            f = dict(x.split("=", 1) for x in l.split("|")[1:] if "=" in x)
            rows.setdefault(f["row"], []).append(f["result"])
    return p.returncode, rows, p.stderr.strip()[-120:]


base = {}
path = TMP + "whole.hbp"
open(path, "w", encoding="utf8", newline="\n").write("\n".join(REC) + "\n")
for name, reader in (("filed", FILED), ("held", HELD)):
    rc, rows, err = run(reader, path)
    base[name] = rows
    print("HOLD_TEST|case=whole|reader=%s|rc=%d|met=%d|miss=%d|json=0" % (name, rc, sum("MISS" not in v for v in rows.values()), sum("MISS" in v for v in rows.values())))


def case(label, lines):
    path = TMP + label + ".hbp"
    open(path, "w", encoding="utf8", newline="\n").write("\n".join(lines) + "\n")
    for name, reader in (("filed", FILED), ("held", HELD)):
        rc, rows, err = run(reader, path)
        new = [k for k, v in rows.items() if "MISS" in v and "MISS" not in base[name].get(k, ["MET"])]
        gone = [k for k in base[name] if k not in rows]
        fams = sorted(set(re.sub(r"(_N=.*|_u=.*|_delta=.*|_t=.*|_s=.*)$", "", k) for k in new))
        print("HOLD_TEST|case=%s|reader=%s|rc=%d|new_miss=%d|families=%s|reads_gone=%d|err=%s|json=0" % (label, name, rc, len(new), ",".join(fams) or "none", len(gone), err if rc else ""), flush=True)
    os.remove(path)


def edit(tags, pattern, repl):
    return [re.sub(pattern, repl, l) if l.startswith(tags) else l for l in REC]


QR = ("POLARITON_QUENCH|", "POLARITON_QUENCH_PIN|", "POLARITON_QUENCH_OTHER_U|", "POLARITON_CONTROL_NO_BOSE|")
CC = ("POLARITON_QUENCH_CONVERSION|", "POLARITON_TAYLOR_CONVERT|")
ZERO = r"\|energy_off_1e-9=-?\d+"
case("R19_energy_zero_on_quench_rows", edit(QR, ZERO, "|energy_off_1e-9=0"))
case("C12_energy_zero_on_conversion_rows", edit(CC, ZERO, "|energy_off_1e-9=0"))
# Half the printed offset on the conversion rows, and a tenth on the quench rows: a read that is wrong and not zero.
halve = lambda m: "|energy_off_1e-9=%d" % (int(m.group(0).split("=")[1]) // 2)
tenth = lambda m: "|energy_off_1e-9=%d" % (int(m.group(0).split("=")[1]) // 10)
case("energy_half_on_conversion_rows", edit(CC, ZERO, halve))
case("energy_tenth_on_quench_rows", edit(QR, ZERO, tenth))
# The swap of F3e, on a held reader.
tags = {}
for l in REC:
    tags.setdefault(l.split("|")[0], []).append(l)


def pick(tag, want):
    return [l for l in REC if l.startswith(tag + "|") and all(("|%s=%s|" % kv) in l for kv in want.items())][0]


for name, tag, want in (
    ("swap_conversion_missed_row", "POLARITON_QUENCH_CONVERSION", {"N": "729", "delta": "0", "y": "1/108", "t": "2"}),
    ("swap_quench_missed_row", "POLARITON_QUENCH", {"N": "6561", "delta": "-1", "t": "8"}),
    ("swap_top_critical_row", "POLARITON_SECTOR", {"N": "43046721", "u": "1/2", "x": "1/2"}),
    ("swap_band_row", "POLARITON_QUENCH_BAND", {"N": "6561", "delta": "1"}),
    ("swap_reversal_row", "POLARITON_REVERSAL", {"N": "243", "full": "1"}),
):
    p = pick(tag, want)
    other = [l for l in tags[tag] if l != p][0]
    i = REC.index(p)
    case(name, REC[:i] + [other] + REC[i + 1:])
# A row whose name is changed and whose count stands: the grid moved, label and value together.
def relabel(tag, want, a, b):
    p = pick(tag, want)
    return [l.replace(a, b) if l == p else l for l in REC]
case("relabel_conversion_y", relabel("POLARITON_QUENCH_CONVERSION", {"N": "729", "delta": "0", "y": "1/108", "t": "2"}, "|y=1/108|", "|y=1/109|"))
# The gate on the engine's own column: jbar_over_N_ppm printed times N, as mutant Q03 prints it.
def times_n(line):
    n = int(re.search(r"\|N=(\d+)\|", line).group(1))
    return re.sub(r"\|jbar_over_N_ppm=(\d+)", lambda m: "|jbar_over_N_ppm=%d" % (int(m.group(1)) * n), line)
case("Q03_gate_column_times_N", [times_n(l) if l.startswith("POLARITON_QUENCH|") else l for l in REC])
os.remove(TMP + "whole.hbp")
