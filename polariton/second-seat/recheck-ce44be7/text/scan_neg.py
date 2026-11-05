# Sentences in the three texts that state what a result is not, or what stays out.
import re, sys
WT = "C:/tmp/qnn-polariton-wt/"
OUT = "C:/tmp/opus55/polariton-recheck-text-20261105/out/"
readme = open(WT + "polariton/README.md", encoding="utf-8").read().split("\n")
root = open(WT + "README.md", encoding="utf-8").read().split("\n")
s = next(i for i, l in enumerate(root) if l.startswith("## Three-mode polariton test"))
e = next(i for i, l in enumerate(root) if l.startswith("## Versions at a glance"))
body = open(OUT + "pr8_body.md", encoding="utf-8").read().split("\n")
PAT = re.compile(r"\b(not|no|none|never|neither|nor|without|cannot|can't|isn't|aren't|doesn't|don't|won't|un[a-z]+|absent|lacks?|fails?|failed|miss(?:es|ed)?|outside|only|nothing|zero|free of|rather than|instead of|stay(?:s)? out|left out|leaves?|wrong|below|beyond|past)\b", re.I)
SKIP = {"under", "until", "unit", "units", "unique", "uniform", "unitary", "united"}
with open(OUT + "scan_neg.txt", "w", encoding="utf-8", newline="\n") as f:
    for name, lines, base in (("polariton/README.md", readme, 1), ("README.md", root[s:e], s + 1), ("PR body", body, 1)):
        for i, line in enumerate(lines, base):
            for sent in re.split(r"(?<=[.;:])\s+", line):
                hits = [m.group(0) for m in PAT.finditer(sent) if m.group(0).lower() not in SKIP]
                if hits:
                    f.write("%s:%d %s\n   %s\n" % (name, i, hits, sent.strip()))
print(open(OUT + "scan_neg.txt", encoding="utf-8").read())
