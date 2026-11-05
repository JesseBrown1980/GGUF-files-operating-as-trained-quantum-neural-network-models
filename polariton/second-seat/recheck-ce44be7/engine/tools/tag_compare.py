# Step 1: the third-run receipt against this head's, tag by tag: which stages the holds moved and by how much. And the route's rows at this head.
import re

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
ID_FIELDS = ("N", "u", "x", "y", "s", "delta", "t", "P", "full")


def load(path):
    out = {}
    for l in open(path, encoding="utf8").read().splitlines():
        tag = l.split("|", 1)[0]
        f = dict(x.split("=", 1) for x in l.split("|")[1:] if "=" in x)
        out.setdefault(tag, {})[tuple(f.get(k, "") for k in ID_FIELDS)] = (l, f)
    return out


a = load(W + "/clean/polariton/third-run/RECEIPT.hbp")
b = load(W + "/clean/polariton/RECEIPT.hbp")
for tag in sorted(set(a) | set(b)):
    ra, rb = a.get(tag, {}), b.get(tag, {})
    same = sum(1 for k in ra if k in rb and ra[k][0] == rb[k][0])
    moved = [k for k in ra if k in rb and ra[k][0] != rb[k][0]]
    gone = [k for k in ra if k not in rb]
    new = [k for k in rb if k not in ra]
    print("TAG|%s|third=%d|head=%d|byte_same=%d|moved=%d|gone=%d|new=%d|json=0" % (tag, len(ra), len(rb), same, len(moved), len(gone), len(new)))
    sizes = {}
    for k in moved:
        fa, fb = ra[k][1], rb[k][1]
        for name in fa:
            if name in ID_FIELDS or name not in fb or fa[name] == fb[name] or name == "json":
                continue
            try:
                x, y = int(fa[name]), int(fb[name])
            except ValueError:
                sizes.setdefault(name, ("text", fa[name], fb[name], k))
                continue
            d = abs(y - x)
            if name not in sizes or sizes[name][0] == "text" or d > sizes[name][0]:
                sizes[name] = (d, x, y, k)
    for name, v in sorted(sizes.items()):
        print("TAG_MOVE|%s|field=%s|largest=%s|from=%s|to=%s|at=N=%s,u=%s,x=%s,y=%s,s=%s,P=%s|json=0" % (tag, name, v[0], v[1], v[2], v[3][0], v[3][1], v[3][2], v[3][3], v[3][4], v[3][7]))

# H2: the finite-difference step on the critical rows, and the hold's m on each.
crit = []
for k, (l, f) in b["POLARITON_SECTOR"].items():
    if "fd_step" in f and (f["u"], f["x"]) in (("1/2", "1/2"), ("0", "1"), ("1", "0")):
        n = int(f["N"])
        power, v = 0, n
        while v > 1:
            v //= 3
            power += 1
        want = 20 + power // 2
        got = int(f["fd_step"].split("-")[1])
        crit.append(got == want)
print("H2_FD_STEP|critical_rows=%d|equal_to_20_plus_power_over_2=%d|json=0" % (len(crit), sum(crit)))
other = [f for k, (l, f) in b["POLARITON_SECTOR"].items() if "fd_step" in f and (f["u"], f["x"]) not in (("1/2", "1/2"), ("0", "1"), ("1", "0"))]
print("H2_FD_STEP_OTHER|rows=%d|at_2^-20=%d|json=0" % (len(other), sum(f["fd_step"] == "2^-20" for f in other)))
