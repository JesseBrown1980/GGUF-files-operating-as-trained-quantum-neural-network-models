# The N = 729 conversion rows at their production step 2^-12 against the same rows at 2^-14, from the instrumented copy, which adds no change to a value. Error of the production step = (4/3)(rows at 12 - rows at 14) if it goes as h^2.
from fractions import Fraction as F

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
filed = {}
for l in open(W + "/clean/polariton/RECEIPT.hbp", encoding="utf8").read().splitlines():
    if l.startswith("POLARITON_QUENCH_CONVERSION|"):
        f = dict(x.split("=", 1) for x in l.split("|")[1:] if "=" in x)
        filed[(f["N"], f["delta"], f["y"], f["t"])] = f
fine = []
for l in open(W + "/out/inst/i_step729.out", encoding="utf8", errors="replace").read().splitlines():
    if l.startswith("POLARITON_QUENCH_CONVERSION|"):
        fine.append(dict(x.split("=", 1) for x in l.split("|")[1:] if "=" in x))
wrap = [l for l in open(W + "/out/inst/i_step729.out", encoding="utf8", errors="replace").read().splitlines() if l.startswith("WRAP") and "events=0" not in l]
print("STEP_FILE|rows=%d|sites_with_bits_lost=%d|json=0" % (len(fine), len(wrap)))
for f in fine:
    a = filed[(f["N"], f["delta"], f["y"], f["t"])]
    cells = []
    for name in ("jbar_ppb", "A_ppb", "B_ppb", "C1_ppb", "C2_ppb", "energy_off_1e-9"):
        cells.append("%s:%d" % (name.split("_")[0], int(a[name]) - int(f[name])))
    n = int(f["N"])

    def v2d2(r):
        a1 = F(abs(int(r["A_ppb"])) * 2, n * 10 ** 9)
        c1 = F(int(r["C1_ppb"]), 10 ** 9)
        return a1 * a1 / (2 * c1), F(abs(int(r["B_ppb"])) * 2, n * 10 ** 9)

    v0, d0 = v2d2(a)
    v1, d1 = v2d2(f)
    print("STEP|N=%s|delta=%s|y=%s|t=%s|dt_filed=%s|dt_here=%s|filed_minus_fine_1e-9=%s|V2_filed_ppm=%d|V2_fine_ppm=%d|D2_filed_ppm=%d|D2_fine_ppm=%d|energy_filed=%s|energy_fine=%s|json=0" % (f["N"], f["delta"], f["y"], f["t"], a["dt"], f["dt"], ",".join(cells), v0 * 10 ** 6, v1 * 10 ** 6, d0 * 10 ** 6, d1 * 10 ** 6, a["energy_off_1e-9"], f["energy_off_1e-9"]))
