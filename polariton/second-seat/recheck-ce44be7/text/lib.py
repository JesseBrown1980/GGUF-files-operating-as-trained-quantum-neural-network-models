# Own loader and own closed forms. Shares no code with the claim's author.
# Row values stay integers and Fractions. Printing goes through helpers that format Fractions.
from fractions import Fraction as F
from math import isqrt
WT = "C:/tmp/qnn-polariton-wt/"
ME = "C:/tmp/opus55/polariton-recheck-text-20261105/"


def load(path):
    out = {}
    with open(path, encoding="utf-8", newline="") as fh:
        for line in fh.read().split("\n"):
            line = line.rstrip("\r")
            if "|" not in line:
                continue
            parts = line.split("|")
            d = {}
            for p in parts[1:]:
                if "=" in p:
                    k, v = p.split("=", 1)
                    d[k] = v
            d["_raw"] = line
            out.setdefault(parts[0], []).append(d)
    return out


R = load(WT + "polariton/RECEIPT.hbp")
S = load(WT + "polariton/SECOND-ROUTE.hbp")


def fq(a, b=1):
    return F(a) / F(b)


def eq(a, b):
    return F(a) == F(b)


def pin(n, u, x, s):
    hits = [r for r in R["POLARITON_PIN"] if r["s"] != "hand" and int(r["N"]) == n and eq(r["u"], u) and eq(r["x"], x) and eq(r["s"], s)]
    assert len(hits) <= 1, (n, u, x, s, len(hits))
    return hits[0] if hits else None


def win(n, u, x, s):
    hits = [r for r in R["POLARITON_PIN_WINDOW"] if int(r["N"]) == n and eq(r["u"], u) and eq(r["x"], x) and eq(r["s"], s)]
    assert len(hits) <= 1
    return hits[0] if hits else None


def sec(n, u, x, p=0):
    hits = [r for r in R["POLARITON_SECTOR"] if int(r["N"]) == n and eq(r["u"], u) and eq(r["x"], x) and int(r["P"]) == int(p)]
    assert len(hits) <= 1
    return hits[0] if hits else None


def conv(n, delta, s, t):
    hits = [r for r in R["POLARITON_QUENCH_CONVERSION"] if int(r["N"]) == n and eq(r["delta"], delta) and eq(r["s"], s) and int(r["t"]) == int(t)]
    assert len(hits) <= 1
    return hits[0] if hits else None


# Fixed point at 2^256: cosh(z) and sinh(z)/z for z^2 = square, an exact rational.
ONE = 1 << 256


def series(square):
    q = F(square)
    v = (q.numerator << 256) // q.denominator
    a, b = ONE, ONE
    ch, shc = ONE, ONE
    for k in range(1, 600):
        a = ((a * v) >> 256) // ((2 * k - 1) * (2 * k))
        b = ((b * v) >> 256) // ((2 * k) * (2 * k + 1))
        ch += a
        shc += b
        if a == 0 and b == 0:
            break
    return F(shc, ONE), F(ch, ONE)


class Law:
    """The closed law at (N, y, delta, t), from its definition in polariton/README.md line 50-53, written out here."""

    def __init__(self, n, y, delta, t):
        self.n, self.y, self.delta, self.t = n, F(y), F(delta), F(t)
        g2 = 1 - self.delta ** 2
        self.g2 = g2
        square = g2 * self.t ** 2
        shc, ch = series(square)
        self.cosh = ch
        self.sinh2 = shc ** 2 * square          # sinh^2(gamma t)
        self.j0 = shc ** 2 * self.t ** 2        # sinh^2(gamma t)/gamma^2
        d = self.delta
        y_ = self.y
        self.a1 = 4 * abs(y_) * (ch - 1) / (1 + d)
        self.c1 = 4 * self.sinh2 / ((1 + d) * n) + self.a1 ** 2 / 2
        self.Y = (2 * n * y_ ** 2 / (1 + d)) * (ch - 1) / (ch + 1)   # tanh^2(z/2) = (cosh z - 1)/(cosh z + 1)
        self.v2 = self.Y / (1 + self.Y)
        self.d2 = 2 * y_ ** 2 * ((ch - 1) ** 2 / (1 + d) ** 2 + self.j0)
        self.ncoh = 2 * n * y_ ** 2 * ((ch - 1) ** 2 / (1 + d) ** 2 + self.j0)
        self.f = (2 * self.j0 + self.ncoh) / n


def read_conv(r):
    n = int(r["N"])
    a1 = F(abs(int(r["A_ppb"])) * 2, n * 10 ** 9)
    d2 = F(abs(int(r["B_ppb"])) * 2, n * 10 ** 9)
    c1 = F(int(r["C1_ppb"]), 10 ** 9)
    v2 = a1 * a1 / (2 * c1)
    return a1, d2, c1, v2


def dec(q, places=6):
    """A Fraction to a decimal string, rounded half up, no float."""
    q = F(q)
    sign = "-" if q < 0 else ""
    q = abs(q)
    scaled = (q * 10 ** places + F(1, 2)).__floor__()
    s = str(scaled).rjust(places + 1, "0")
    return sign + (s[:-places] + "." + s[-places:] if places else s)


def root(q, bits=256):
    q = F(q)
    return F(isqrt((q.numerator << (2 * bits)) // q.denominator), 1 << bits)


# Mathieu expectation f(q) = <cos 2 alpha> on the ground state of H = -d^2/d alpha^2 + 2 q cos(2 alpha) sign chosen so it peaks, written here
# from the even cosine block: basis 1, cos 2 a, cos 4 a ... of ce_0, exact rational matrix, inverse iteration at 2^256 by Sturm bisection on the tridiagonal.
def mathieu_f(q, size=60):
    """Ground state of -d^2 + 2q cos 2a' in the pi-periodic even basis. Returns <cos 2a> for the well minimum: positive."""
    q = F(q)
    # basis: e0 = 1/sqrt(pi) (norm), en = cos(2 n a)*sqrt(2/pi)
    # H_nn = (2n)^2, H_{n,n+1} = -q (well at cos 2a = 1 with V = -2 q cos 2a), H_01 = -sqrt(2) q.
    # Exact: use the squared off-diagonal in Sturm, and read the eigenvector by the three term recurrence.
    diag = [F((2 * n) ** 2) for n in range(size)]
    off2 = [2 * q * q] + [q * q] * (size - 2)
    # Sturm count of levels below lam
    def below(lam):
        c = 0
        d = None
        for i in range(size):
            if i == 0:
                d = diag[0] - lam
            else:
                if d == 0:
                    d = F(1, 1 << 300)
                d = diag[i] - lam - off2[i - 1] / d
            # keep the denominators bounded
            d = F((d.numerator << 400) // d.denominator, 1 << 400)
            if d < 0:
                c += 1
        return c
    lo, hi = -2 * q - 4, F(4)
    for _ in range(300):
        mid = (lo + hi) / 2
        mid = F((mid.numerator << 320) // mid.denominator, 1 << 320)
        if below(mid) >= 1:
            hi = mid
        else:
            lo = mid
    lam = (lo + hi) / 2
    # recurrence from the top down for stability: v[n]/v[n+1] form (continued fraction)
    bits = 320
    ratio = [F(0)] * size   # ratio[n] = v[n]/v[n-1]
    r = F(0)
    for n in range(size - 1, 0, -1):
        # (diag[n]-lam) v[n] + o[n-1] v[n-1] + o[n] v[n+1] = 0  with o = -q (or -sqrt2 q on the first link)
        # v[n] = -(o[n-1] v[n-1]) / (diag[n]-lam + o[n] r_{n+1})
        den = diag[n] - lam
        if n < size - 1:
            den = den + (-q) * r
        o_prev = -q
        # keep the sqrt2 out: use w0 = v0*sqrt2 convention, so all links read -q and the n=0 row reads differently
        r = F(((-o_prev / den).numerator << bits) // (-o_prev / den).denominator, 1 << bits)
        ratio[n] = r
    # with w0 = v0*sqrt 2:  w = (w0, v1, v2, ...), v1 = ratio[1] * w0
    v = [F(1)]
    for n in range(1, size):
        v.append(v[-1] * ratio[n])
        v[-1] = F((v[-1].numerator << bits) // v[-1].denominator, 1 << bits) if v[-1] != 0 else F(0)
    # norm: v0^2 + sum vn^2 with v0 = w0/sqrt2 -> w0^2/2 + sum
    norm = v[0] * v[0] / 2 + sum(a * a for a in v[1:])
    # <cos 2a>: in the normalized cos basis, <e0|cos 2a|e1> = 1/sqrt2, <en|cos 2a|en+1> = 1/2
    # with v0 = w0/sqrt2: 2 * v0 * v1 * (1/sqrt2) = w0 v1 ; 2 * vn vn+1 * 1/2 = vn vn+1
    num = v[0] * v[1] + sum(v[n] * v[n + 1] for n in range(1, size - 1))
    return num / norm
