# Writes the second set's bins into attack3/, from the lite base the first set was built from, so nothing already built moves.
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-engine-20261105/tools")
from mutants_more import M2

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
base = open(W + "/attack/src/bin/m_base.rs", encoding="utf8", newline="").read()


def rep(s, a, b, count=1):
    assert s.count(a) == count, (a, s.count(a))
    return s.replace(a, b)


os.makedirs(W + "/attack3/src/bin", exist_ok=True)
open(W + "/attack3/Cargo.toml", "w", encoding="utf8", newline="\n").write('[package]\nname = "attack3"\nversion = "0.1.0"\nedition = "2021"\n[dependencies]\n[profile.release]\nopt-level = 3\noverflow-checks = true\n')
for mid, grp, subs in M2:
    s = base
    for a, b in subs:
        s = rep(s, a, b)
    open(W + "/attack3/src/bin/m_%s.rs" % mid.lower().replace("^", ""), "w", encoding="utf8", newline="\n").write(s)
print("BINS|count=%d|json=0" % len(M2))
