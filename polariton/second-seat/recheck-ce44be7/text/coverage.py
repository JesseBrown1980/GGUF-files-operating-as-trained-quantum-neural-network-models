# Which numeric tokens of the texts never appear in any of my check outputs. Those need a manual line in the ledger.
import re, glob
ME = "C:/tmp/opus55/polariton-recheck-text-20261105/"
inv = open(ME + "out/inventory.txt", encoding="utf-8").read().split("\n")
outs = ""
for p in glob.glob(ME + "out/*.txt") + glob.glob(ME + "out/*.hbp"):
    if p.endswith("inventory.txt") or p.endswith("coverage.txt") or p.endswith("scan_neg.txt"):
        continue
    outs += open(p, encoding="utf-8", errors="replace").read() + "\n"
SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")
norm_out = outs.replace(",", "").replace("−", "-")
res = []
i = 0
while i < len(inv) - 1:
    head, sent = inv[i], inv[i + 1]
    i += 2
    if " | " not in head:
        continue
    loc, toks = head.split(" | ", 1)
    for t in toks.split(" ; "):
        t0 = t
        t = t.replace(",", "").replace("−", "-").strip()
        core = re.match(r"[-+]?\d+(?:\.\d+)?", t)
        if not core:
            continue
        c = core.group(0).lstrip("+-")
        significant = ("." in c) or len(c) >= 4
        if not significant:
            continue
        if c in norm_out:
            continue
        # try without trailing zero, and with the digits as ppm or ppb integers
        digits = c.replace(".", "").lstrip("0")
        if digits and digits in norm_out.replace(".", ""):
            status = "digits_only"
        else:
            status = "UNMATCHED"
        res.append((loc, t0, status, sent.strip()[:150]))
with open(ME + "out/coverage.txt", "w", encoding="utf-8", newline="\n") as f:
    for r in res:
        f.write(" | ".join(r) + "\n")
print(len(res))
for r in res:
    print(" | ".join(r))
