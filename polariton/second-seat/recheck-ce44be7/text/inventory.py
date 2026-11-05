# Lists every number in the three texts with the sentence around it.
# Reads: polariton/README.md, the root README section, the PR body. Writes out/inventory.txt.
# Tokens: integers, decimals, fractions, powers, unicode super/subscripts, with their sentence.
import re, sys, json
WT = "C:/tmp/qnn-polariton-wt/"
OUT = "C:/tmp/opus55/polariton-recheck-text-20261105/out/"

def sentences(line):
    # split on '. ' keeping decimals together, on '; ' and on table bars
    parts = re.split(r"(?<=[.;:!?])\s+(?=[A-Z*\[`(⟨|−\-0-9])", line)
    return [p for p in parts if p.strip()]

TOKEN = re.compile(
    r"(?<![\w.])"
    r"(?:[−\-+]?\d[\d,]*(?:\.\d+)?(?:\s?×\s?10[⁰¹²³⁴⁵⁶⁷⁸⁹⁻−\-]+)?(?:/\d+)?(?:[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+)?(?:\s?(?:ppm|ppb|%|μW|μm⁻¹|fs|MHz|ps|min(?:utes)?|units|rows?|states|bits))?)"
)

def tokens(s):
    # skip URLs and git hashes in backticks
    t = re.sub(r"https?://\S+", " ", s)
    t = re.sub(r"`[0-9a-f]{7,40}`", " ", t)
    t = re.sub(r"\]\([^)]*\)", "] ", t)
    return [m.group(0).strip() for m in TOKEN.finditer(t)]

def run(name, text, base_line=1):
    out = []
    for i, line in enumerate(text.splitlines(), base_line):
        if not line.strip():
            continue
        for sent in sentences(line):
            toks = tokens(sent)
            if toks:
                out.append((name, i, toks, sent.strip()))
    return out

readme = open(WT + "polariton/README.md", encoding="utf-8", newline="").read()
root = open(WT + "README.md", encoding="utf-8", newline="").read().split("\n")
# the root section: line 30 to the line before '## Versions at a glance'
start = next(i for i, l in enumerate(root) if l.startswith("## Three-mode polariton test"))
end = next(i for i, l in enumerate(root) if l.startswith("## Versions at a glance"))
rootsec = "\n".join(root[start:end])
body = open(OUT + "pr8_body.md", encoding="utf-8", newline="").read()

all_rows = run("polariton/README.md", readme) + run("README.md", rootsec, start + 1) + run("PR#8 body", body)
n = 0
with open(OUT + "inventory.txt", "w", encoding="utf-8", newline="\n") as f:
    for name, line, toks, sent in all_rows:
        f.write("%s:%d | %s\n    SENT: %s\n" % (name, line, " ; ".join(toks), sent))
        n += len(toks)
print("sentences=%d tokens=%d" % (len(all_rows), n))
for k in ("polariton/README.md", "README.md", "PR#8 body"):
    print(k, sum(len(t) for nm, _, t, _ in all_rows if nm == k))
