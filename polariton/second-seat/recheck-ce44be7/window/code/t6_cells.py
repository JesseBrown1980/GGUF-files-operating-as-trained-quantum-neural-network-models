# Item 6. Each printed cell of the two window tables against the receipt rows, cell by cell, from the README text itself.
import re
from fractions import Fraction as F
WT = "C:/tmp/qnn-polariton-wt/polariton/"
rows = []
for line in open(WT + "RECEIPT.hbp", encoding="utf-8").read().splitlines():
    if line.startswith("POLARITON_PIN_WINDOW|"):
        rows.append(dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f))


def win(N, u, x, s):
    for r in rows:
        if int(r["N"]) == N and F(r["u"]) == F(u) and F(r["x"]) == F(x) and F(r["s"]) == F(s):
            return r


def rounded(q, d):
    q = F(q)
    return (q * 10 ** d * 2 + 1).__floor__() // 2 if q >= 0 else None


def same(text, q):
    """The printed decimal equals q rounded to its digits, or truncated to its digits."""
    digits = len(text.split(".")[1]) if "." in text else 0
    p = F(text)
    scale = 10 ** digits
    return p * scale == rounded(q, digits) or p * scale == (q * scale).__floor__()


readme = open(WT + "README.md", encoding="utf-8").read().splitlines()
INSIDE = {("1/4", "-1/4"): (31223, 123327, 417999, 744149, 874846, 937483), ("1/4", "0"): (7199, 28779, 113886, 394162, 732112, 869614), ("3/4", "0"): (5190, 20753, 82548, 304289, 675100, 846304), ("3/4", "1/8"): (740, 2962, 11850, 47314, 183943, 539654), ("1/2", "1/4"): (1111, 4444, 17772, 70798, 266308, 642446)}
six = ("1/2", "1", "2", "4", "8", "16")
bad = total = 0
minus = lambda t: t.replace("\u2212", "-")
for line in readme:
    m = re.match(r"^\| \(([^,]+), ([^)]+)\) \| (\d+) \| (.*)\|$", line)
    if not m:
        continue
    us, xs, N = m.group(1), minus(m.group(2)), int(m.group(3))
    cells = [c.strip() for c in m.group(4).split("|")]
    if len(cells) == 8 + 1 - 0 and (us, xs) in INSIDE:
        u, x = F(us), F(xs)
        delta = u + x
        rho = (1 - delta) / (4 - 3 * u)
        c0 = ((1 - 2 * rho) / rho - u) / 4
        f = {s: F(v, 10 ** 6) for s, v in zip(six, INSIDE[(us, xs)])}
        expect = [2 * rho]
        for s in ("1", "4", "16"):
            r = win(N, us, xs, s)
            expect += [F(int(r["D2_ppm"]), 10 ** 6), 2 * rho * f[s]]
        r = win(N, us, xs, "4")
        expect += [F(abs(int(r["A_ppb"])) * 2, N * 10 ** 9) / (F(4) / N), 2 * (1 + (u / (8 * c0)) * (1 + f["4"]))]
        for c, e in zip(cells, expect):
            total += 1
            ok = same(c, e)
            bad += not ok
            if not ok:
                print("CELL_OFF|table=inside|u=%s|x=%s|N=%d|printed=%s|from_rows=%s|json=0" % (us, xs, N, c, float(e)))
    elif len(cells) == 7:
        u, x = F(us), F(xs)
        r16, r4 = win(N, us, xs, "16"), win(N, us, xs, "4")
        y16, y4 = F(16) / N, F(4) / N
        expect = [F(int(r16["P2_over_N2_ppm"]), 10 ** 6), F(abs(int(r4["A_ppb"])) * 2, N * 10 ** 9) / y4, 2 / (u - x), F(abs(int(r16["B_ppb"])) * 2, N * 10 ** 9) / (y16 * y16), 2 * abs(u - x - 1) / (u * (u - x) ** 2)]
        for c, e in zip(cells[:5], expect):
            total += 1
            ok = same(c, e)
            bad += not ok
            if not ok:
                print("CELL_OFF|table=below|u=%s|x=%s|N=%d|printed=%s|from_rows=%s|json=0" % (us, xs, N, c, float(e)))
        total += 1
        sign = "+" if int(r16["B_ppb"]) > 0 else "\u2212"
        ok = cells[5] == sign
        bad += not ok
        if not ok:
            print("CELL_OFF|table=below|u=%s|x=%s|N=%d|sign=%s|json=0" % (us, xs, N, cells[5]))
print("CELLS_DONE|cells=%d|off=%d|json=0" % (total, bad))
