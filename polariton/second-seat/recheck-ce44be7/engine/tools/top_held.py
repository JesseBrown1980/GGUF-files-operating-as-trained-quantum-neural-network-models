# H16: the held route's top lane on X02's and X07's sector rows, and on the filed rows.
import os
import re
import subprocess

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
RECEIPT = open(W + "/clean/polariton/RECEIPT.hbp", encoding="utf8").read().splitlines()
ROUTE = W + "/holdcopy/polariton/second_route.py"
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def key(l):
    f = dict(x.split("=", 1) for x in l.split("|")[1:] if "=" in x)
    return (f["N"], f["u"], f["x"], f["P"])


for mid in ("filed", "X02_old_fd_step", "X07_o2_floor_2^70"):
    if mid == "filed":
        merged = RECEIPT
    else:
        new = {key(l): l for l in open(W + "/out/top/" + mid + "/sector.rows", encoding="utf8").read().splitlines() if l}
        merged = [new.get(key(l), l) if l.startswith("POLARITON_SECTOR|") else l for l in RECEIPT]
    path = W + "/out/top_held_tmp.hbp"
    open(path, "w", encoding="utf8", newline="\n").write("\n".join(merged) + "\n")
    p = subprocess.run(["python3", "-I", "-X", "utf8", ROUTE, "top_compare", path, "59049"], capture_output=True, text=True, encoding="utf8", env=env)
    done = [l for l in p.stdout.replace("\r", "").splitlines() if l.startswith("SECOND_ROUTE_TOP_DONE")]
    print("TOP_HELD|id=%s|rc=%d|%s|json=0" % (mid, p.returncode, done[0] if done else p.stderr[-120:]), flush=True)
    os.remove(path)
