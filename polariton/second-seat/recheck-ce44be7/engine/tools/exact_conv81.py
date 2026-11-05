# The conversion rows at N = 81 against the exact unitary, with my own code: Taylor series of exp(-iHt) in normalised-basis integers at 2^320, separate from second_route.py and from the engine.
# So the production step of the leapfrog with y on, 2^-13 at N = 81, meets an exact answer; the filed route reads N = 9, 27 at 2^-16 only.
# usage: exact_conv81.py [N] [row filter by y text]
import sys
from fractions import Fraction as F
from math import isqrt

BITS = 320
ONE = 1 << BITS
W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 81
ONLY = sys.argv[2:]
REC = open(W + "/clean/polariton/RECEIPT.hbp", encoding="utf8").read().splitlines()
rows = []
for l in REC:
    if l.startswith("POLARITON_QUENCH_CONVERSION|"):
        f = dict(x.split("=", 1) for x in l.split("|")[1:] if "=" in x)
        if int(f["N"]) == N and (not ONLY or f["y"] in ONLY):
            rows.append(f)

states = [(p, m) for p in range(N + 1) for m in range(N + 1 - p)]
index = {s: i for i, s in enumerate(states)}
size = len(states)
ROOT = {}


def root(v):
    """sqrt(v) at 2^BITS, as an integer, from an integer v."""
    if v not in ROOT:
        ROOT[v] = isqrt(v << (2 * BITS))
    return ROOT[v]


def fix(q):
    q = F(q)
    return (q.numerator << BITS) // q.denominator


def operator(x, u, y):
    """H as a list of (i, j, value at 2^BITS), every entry listed, in the normalised Fock basis."""
    out = [[] for _ in range(size)]
    xq, uq = fix(x), fix(u)
    yq = fix(y)
    for (p, m), i in index.items():
        n0 = N - p - m
        diag = xq * (p + m) + (uq * (n0 * (p + m) + p * m)) // N
        out[i].append((i, diag))
        if n0 >= 2:
            j = index[(p + 1, m + 1)]
            v = root((p + 1) * (m + 1) * n0 * (n0 - 1)) // N
            out[i].append((j, v))
            out[j].append((i, v))
        if n0 >= 1:
            j = index[(p + 1, m)]
            v = -((yq * root((p + 1) * n0)) >> BITS)
            out[i].append((j, v))
            out[j].append((i, v))
            j = index[(p, m + 1)]
            v = -((yq * root((m + 1) * n0)) >> BITS)
            out[i].append((j, v))
            out[j].append((i, v))
    return out


def apply(op, vec):
    res = [0] * size
    for i, row in enumerate(op):
        s = 0
        for j, v in row:
            if vec[j]:
                s += v * vec[j]
        res[i] = s >> BITS
    return res


def state(op, t):
    # psi(t) = sum (-i t H)^k / k! |N,0,0>, with re and im kept apart. The terms stop when they vanish at 2^BITS.
    vec = [0] * size
    vec[index[(0, 0)]] = ONE
    re, im = list(vec), [0] * size
    k = 0
    while True:
        k += 1
        vec = apply(op, vec)
        vec = [(v * t) // k for v in vec]
        if not any(vec) or (k > 40 and max(abs(v) for v in vec) < 2):
            break
        phase = k % 4
        for i, v in enumerate(vec):
            if v:
                if phase == 0:
                    re[i] += v
                elif phase == 1:
                    im[i] -= v
                elif phase == 2:
                    re[i] -= v
                else:
                    im[i] += v
    return re, im, k


def read(re, im):
    def inner(a, b):
        return (re[a] * re[b] + im[a] * im[b]) >> BITS

    norm = pairs = a_val = b_val = n0_pairs = np_nm = re_p = 0
    for (p, m), i in index.items():
        n0 = N - p - m
        w = inner(i, i)
        norm += w
        pairs += w * (p + m)
        n0_pairs += w * n0 * (p + m)
        np_nm += w * p * m
        if n0 >= 2:
            t = index[(p + 1, m + 1)]
            re_p += (inner(t, i) * root((p + 1) * (m + 1) * n0 * (n0 - 1))) >> BITS
        if n0 >= 1:
            t = index[(p + 1, m)]
            a_val += (inner(t, i) * root((p + 1) * n0)) >> BITS
            t = index[(p, m + 1)]
            a_val += (inner(t, i) * root((m + 1) * n0)) >> BITS
        if p >= 1:
            t = index[(p - 1, m + 1)]
            b_val += (inner(t, i) * root(p * (m + 1))) >> BITS
    c1 = F(2 * (n0_pairs + 2 * re_p), N * (N - 1) * ONE)
    c2 = F(2 * np_nm, N * (N - 1) * ONE)
    return F(norm, ONE), F(pairs, 2 * ONE), F(a_val, ONE), F(b_val, ONE), c1, c2


chains = {}
for r in rows:
    chains.setdefault((r["delta"], r["y"], r["x"], r["u"]), []).append(r)
worst = {}
for (delta, ytext, xtext, utext), chain in chains.items():
    op = operator(F(xtext), F(utext), F(ytext))
    for r in chain:
        t = int(r["t"])
        re, im, k = state(op, t)
        norm, jbar, a, b, c1, c2 = read(re, im)
        vals = {"jbar_ppb": jbar, "A_ppb": a, "B_ppb": b, "C1_ppb": c1, "C2_ppb": c2}
        cells = []
        for name, v in vals.items():
            off = abs(F(int(r[name]), 10 ** 9) - v)
            rel = off / max(abs(v), F(1, 10 ** 12))
            cells.append("%s_off_1e-9=%d:rel_ppm=%d" % (name.split("_")[0], off * 10 ** 9, rel * 10 ** 6))
            cur = worst.get(name)
            if cur is None or off > cur[0]:
                worst[name] = (off, rel, "delta=%s,y=%s,t=%d" % (delta, ytext, t))
        # V^2 = A1^2/(2 C1) from each, the README's read.
        a1x, a1r = 2 * abs(a) / N, 2 * abs(F(int(r["A_ppb"]), 10 ** 9)) / N
        v2x, v2r = a1x * a1x / (2 * c1), a1r * a1r / (2 * F(int(r["C1_ppb"]), 10 ** 9))
        d2x, d2r = 2 * abs(b) / N, 2 * abs(F(int(r["B_ppb"]), 10 ** 9)) / N
        print("EXACT_CONV|N=%d|delta=%s|y=%s|t=%d|dt=%s|terms=%d|norm_off_1e-15=%d|%s|V2_exact_ppm=%d|V2_read_ppm=%d|D2_exact_ppm=%d|D2_read_ppm=%d|json=0" % (N, delta, ytext, t, r["dt"], k, abs(norm - 1) * 10 ** 15, "|".join(cells), v2x * 10 ** 6, v2r * 10 ** 6, d2x * 10 ** 6, d2r * 10 ** 6), flush=True)
print("EXACT_CONV_WORST|N=%d|%s|json=0" % (N, "|".join("%s:off_1e-9=%d:rel_ppm=%d:at=%s" % (k, v[0] * 10 ** 9, v[1] * 10 ** 6, v[2]) for k, v in worst.items())))
