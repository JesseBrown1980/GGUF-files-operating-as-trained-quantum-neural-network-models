#!/usr/bin/env python3
"""check_a.py: an independent stage A for the stripe-phase reader, written from the frozen rules SECTOR and ATOMS and
reader/AGG-FORMAT.md, in Python with int only. It reads one twens 0.4.0 dump on stdin and writes the aggregate block of
AGG-FORMAT.md section 3 on stdout, or one STOP row. A stream with more than one fault STOPs at the first in the order of
AGG-FORMAT.md section 8 (every row read, then the rebuilds from the draws, then the sums record by record).

    python3 -I check_a.py --point ID --call I [--side PATH] < dump
"""

import hashlib
import re
import sys

READER = "stripes-read-a"
READER_VERSION = "0.1.0"
BIN_SHA = "33e62fbe0837aeddc916a57d67848338cbc258aa1dfb85a01cfba53fb8a4e03f"
SRC_SHA = (
    "main.rs:1d768fa9aba719d0439625f08ea2711cc0d28a5e751b25a81667b4b3d5fcacbb,"
    "sha256.rs:7447d1e84a95fe1ab84882938a0344119d017c347809e0f7e929c2e8c27d4621"
)
Q = 40
ONE = 1 << Q
I64_MIN, I64_MAX = -(1 << 63), (1 << 63) - 1
U64_MAX = (1 << 64) - 1
U128_MAX = (1 << 128) - 1
I128_MIN, I128_MAX = -(1 << 127), (1 << 127) - 1

VN = ["VNC", "V1", "V0", "RN", "FLIP", "LOCK", "MODE0"]
VNC, V1, V0, RN, FLIP, LOCK, MODE0 = range(7)
VINIT = ["sharp", "ring_half", "coherent", "ring", "sharp", "sharp", "sharp"]
VSEEDS = ["vac", "vac", "vac", "vac", "vac", "lock", "vac"]
VKAPPA = ["1", "1", "1", "1", "-1", "1", "1"]
VPHASE = ["fixed", "fixed", "fixed", "fixed", "fixed", "fixed", "rot30"]
LEGACY = [(V1, "V1"), (VNC, "VN"), (V0, "V0"), (RN, "RN")]
OZR, OZI, OXW, OXNC, OF, OBR, OBI = range(7)
PAIRS = [
    (V1, OXW, VNC, OXNC, "V1xw-VNCxnc"),
    (V1, OZR, VNC, OZR, "V1zr-VNCzr"),
    (V0, OXW, V1, OXW, "V0xw-V1xw"),
    (V0, OZR, V1, OZR, "V0zr-V1zr"),
    (V1, OXW, VNC, OXW, "V1xw-VNCxw"),
    (MODE0, OZR, VNC, OZR, "MODE0zr-VNCzr"),
    (MODE0, OZI, VNC, OZI, "MODE0zi-VNCzi"),
    (MODE0, OXNC, VNC, OXNC, "MODE0xnc-VNCxnc"),
    (MODE0, OF, VNC, OF, "MODE0f-VNCf"),
    (MODE0, OBR, VNC, OBR, "MODE0br-VNCbr"),
    (MODE0, OBI, VNC, OBI, "MODE0bi-VNCbi"),
]
TWB_F = (
    "zr zi dzr dzi xw dxw xnc dxnc f qdzr qdxw qdxnc qzr qxw qxnc qdzi f2 br bi br2 bi2 brbi zrxw zrxnc dzrdxw "
    "dzrdxnc zr2 zi2 dzr2 dzi2 xw2 dxw2 xnc2 dxnc2"
).split()
BLOCKS = [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
SUMS_TEXT = "plain_at_2^40,q_sum_of_floor(v*v/2^40),products_exact_at_2^80"
ROUNDING_TEXT = "per-sample_bound_summed_in_TWB_ROUND_and_TWB_PAIR_ROUND"
UNITS_TEXT = "ulps_of_each_field(sums_2^-40,squares_and_products_2^-80)"
NL_INIT = "c0=sqrt(N),c+-=0"
NL_READS = (
    "trajectory_frame:A1=2abs(Z),C1=2N*abs(Z)^2/(N-1),f=fcl,D2=2abs(B);"
    "ensemble_frames:C1_NC=2N*xnc/(N-1),C1_W=2N*xw/(N-1),f_W=f=fcl-1/N"
)

K_HEAD = (
    "engine version cli binary_sha256 source_sha256 N delta u y seed seed_string start count samples dtden threads "
    "steps mask reserved guard q sums rounding float_used json"
).split()
K_SAMPLE = "idx g rot json".split()
K_INIT = "idx variant s uv json".split()
K_IB = "idx variant e0 ep em seeds eta json".split()
K_OBS = "idx variant step zr zi xw xnc f br bi zcr zci xc json".split()
K_RB = "idx variant step eps b_zr b_zi b_xw b_xnc b_f b_br b_bi b_z2 b_fcl json".split()
K_TWENS = (
    "N delta u y samples seed dtden step variant n h ctrl zr zi dzr dzi xw dxw xnc dxnc f qdzr qdxw qdxnc qzr qxw "
    "qxnc qdzi float_used json"
).split()
K_TWPAIR = (
    "N delta y samples step n v1xw_vnxnc q0 v1zr_vnzr q1 v0xw_v1xw q2 v0zr_v1zr q3 v1xw_vnxw q4 float_used json"
).split()
K_TWB = (
    "N delta u y seed start count dtden step variant init seeds kappa phase n h ctrl".split()
    + TWB_F
    + ["float_used", "json"]
)
K_ROUND = (
    "N delta y seed start count dtden step variant n".split()
    + ["rb_" + f for f in TWB_F]
    + ["eps_max", "units", "float_used", "json"]
)
K_PAIR = "N delta y seed start count dtden step pair n d qd d2 float_used json".split()
K_PROUND = "N delta y seed start count dtden step pair n rb_d rb_qd rb_d2 float_used json".split()
K_NL = (
    "N delta u y dtden step init kappa zr zi z2 xw xnc f fcl br bi rb_zr rb_zi rb_z2 rb_xw rb_xnc rb_f rb_fcl "
    "rb_br rb_bi eps reads at float_used json"
).split()
K_DONE = "n records mask float_used json".split()
# the value fields of each summary row, in key order
TWPAIR_F = "v1xw_vnxnc q0 v1zr_vnzr q1 v0xw_v1xw q2 v0zr_v1zr q3 v1xw_vnxw q4".split()
ROUND_F = ["rb_" + f for f in TWB_F] + ["eps_max"]
PAIR_F = ["d", "qd", "d2"]
PROUND_F = ["rb_d", "rb_qd", "rb_d2"]

# id: (N, delta, y, calls, all, steps, side)
TABLE = {
    "P01": (1296, "1/2", "0", 1024, 64, [64, 128, 192, 256], False),
    "P02": (1296, "1/2", "1/576", 1024, 64, [64, 128, 192, 256], False),
    "P03": (1296, "1/2", "1/288", 1024, 64, [64, 128, 192, 256], False),
    "P04": (1296, "1/2", "1/144", 1024, 64, [64, 128, 192, 256], False),
    "P05": (1296, "1/2", "1/72", 256, 64, [64, 128, 192, 256], False),
    "P06": (1296, "1/2", "1/36", 256, 64, [64, 128, 192, 256], False),
    "P07": (729, "-1/4", "0", 256, 64, [128, 192, 256], False),
    "P08": (729, "-1/4", "1/54", 256, 64, [64, 128, 192, 256], True),
    "P09": (121, "1/2", "0", 256, 64, [64, 128, 192, 256], False),
    "P10": (121, "1/2", "1/11", 256, 64, [64, 128, 192, 256], False),
    "P11": (1296, "1/2", "1/648", 1024, 64, [64, 128, 192, 256], False),
    "P12": (324, "1/2", "1/162", 1024, 64, [64, 128, 192, 256], False),
    "P13": (729, "-1/4", "-1/54", 64, 64, [64, 128], True),
    "P14": (729, "-1/4", "1/108", 256, 0, [64, 128], False),
    "X1": (27, "1/4", "1/40", 8, 8, [64, 128], False),
    "X0": (27, "1/4", "0", 8, 8, [64, 128], False),
}
FULL_MASK = "VNC,V1,V0,RN,FLIP,LOCK,MODE0,NL"

INT_RE = re.compile(r"-?(0|[1-9][0-9]*)\Z")
RAT_RE = re.compile(r"-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?\Z")
TEST_RE = re.compile(r"T[A-Za-z0-9_-]+\Z")
PRINTABLE = bytes(range(32, 127)) + b"\n"


class Stop(Exception):
    def __init__(self, reason, line, **detail):
        super().__init__(reason)
        self.reason = reason
        self.line = line
        self.detail = detail


def m(a, b):
    return (a * b) >> Q


def isqrt(n):
    if n < 2:
        return n
    x = 1 << ((n.bit_length() + 1) // 2)
    while True:
        y = (x + n // x) >> 1
        if y >= x:
            return x
        x = y


# The draws of twens 0.4.0 (Rng, splitmix, ens_draw in polariton-bridge/engines/ensemble/src/main.rs), from the engine
# source, in Python ints (review N8): at a table point g, rot and eta are rebuilt from (seed, idx).
U64 = (1 << 64) - 1
FNV = 0x1000000001B3  # the engine const FNV = 0x1000_0000_01B3
ROT_LIMIT = 1 << 41


def _splitmix(z):
    z = (z + 0x9E3779B97F4A7C15) & U64
    v = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & U64
    v = ((v ^ (v >> 27)) * 0x94D049BB133111EB) & U64
    return z, v ^ (v >> 31)


def _rotl(x, k):
    return ((x << k) | (x >> (64 - k))) & U64


class Xoshiro:
    def __init__(self, seed):
        z, self.s = seed & U64, []
        for _ in range(4):
            z, v = _splitmix(z)
            self.s.append(v)

    def next(self):
        s = self.s
        result = (_rotl((s[1] * 5) & U64, 7) * 9) & U64
        t = (s[1] << 17) & U64
        s[2] ^= s[0]
        s[3] ^= s[1]
        s[1] ^= s[2]
        s[0] ^= s[3]
        s[2] ^= t
        s[3] = _rotl(s[3], 45)
        return result


def engine_draws(seed, idx, mode0):
    """(g0..g5, [rot_c, rot_s], eta) of sample idx: six Gaussians (popcount of 4096 bits - 2048) 2^35, then MODE0's
    unit30x when MODE0 is on, else (2^40, 0) and 0."""
    r = Xoshiro(seed + idx * FNV)
    g = []
    for _ in range(6):
        c = 0
        for _ in range(64):
            c += bin(r.next()).count("1")
        g.append((c - 2048) << 35)
    if not mode0:
        return g, [ONE, 0], 0
    while True:
        a = (r.next() >> 33) - (1 << 30)
        b = (r.next() >> 33) - (1 << 30)
        r2 = a * a + b * b
        if not (1 << 58) <= r2 <= (1 << 60):
            continue
        rt = isqrt(r2)
        d, rr = r2 - rt * rt, rt * rt
        eta = ceil_div(d << Q, 2 * rr)
        # the engine's i128 division truncates toward zero
        cs = [(abs(x) << Q) // rt * (1 if x >= 0 else -1) for x in (a, b)]
        return g, cs, eta


def cu(a, b):
    return (a * b + (ONE - 1)) >> Q


def ceil_div(a, b):
    return -((-a) // b)


def sigma(x, y):
    """Rule SECTOR: the sector 0..15 of (x, y), half-open edges at k*pi/8; None at (0, 0)."""
    if y >= 0 and x > 0:
        qd, a, b = 0, x, y
    elif x <= 0 and y > 0:
        qd, a, b = 1, y, -x
    elif y <= 0 and x < 0:
        qd, a, b = 2, -x, -y
    elif x >= 0 and y < 0:
        qd, a, b = 3, -y, x
    else:
        return None
    s = a + b
    if s * s < 2 * a * a:
        sub = 0
    elif b < a:
        sub = 1
    elif s * s > 2 * b * b:
        sub = 2
    else:
        sub = 3
    return 4 * qd + sub


def certified(br, bi, bbr, bbi):
    """The certified sector of the box (br +- bbr, bi +- bbi), or None when ambiguous."""
    lim = 1 << 63
    if bbr >= lim or bbi >= lim:
        return None
    sec = None
    for sx in (1, -1):
        for sy in (1, -1):
            x = br + sx * bbr
            yv = bi + sy * bbi
            if abs(x) >= lim or abs(yv) >= lim:
                return None
            if x == 0 or yv == 0 or abs(x) == abs(yv):
                return None
            s = sigma(x, yv)
            if sec is None:
                sec = s
            elif s != sec:
                return None
    return sec


def sign_state(v, b):
    if abs(v) > b:
        return 0 if v > 0 else 1
    return 2


def flags_of(c):
    c0, c1, c2, c3 = c[0], c[1], c[2], c[3]
    nl_klein = (c0, c1) in ((c2, c3), (-c3, c2), (-c2, -c3), (c3, -c2))
    nl_exch = c0 == c2 and c1 == c3
    lk_klein = c0 * c1 * (c0 * c0 - c1 * c1) == 0
    lk_exch = c1 == 0
    return nl_klein, nl_exch, lk_klein, lk_exch


def seed_err(g):
    return 1 + ceil_div(abs(g), ONE)


def sharp(nsum, n, line):
    arg = ONE + (3 * ONE) // (2 * n) - nsum
    if arg <= 0:
        raise Stop("start_rebuild", line, what="sharp_argument_not_positive", arg=arg)
    return isqrt(arg * ONE)


def sharp_err(comps, errs, n, line):
    dn = 4
    nsum = 0
    for cv, ce in zip(comps, errs):
        dn += cu(2 * abs(cv), ce) + cu(ce, ce)
        nsum += m(cv, cv)
    darg = dn + 1
    arg = ONE + (3 * ONE) // (2 * n) - nsum
    lo = max(max(arg, 0) - darg, 0)
    if lo == 0:
        raise Stop("start_rebuild", line, what="sharp_bound_low_end_not_positive")
    slo = isqrt(lo << Q)
    return 1 + ceil_div(darg << Q, 2 * slo)


def uv_of(rp, ip, rm, im):
    return [rp + rm, ip - im, rp - rm, ip + im]


def rot(s, c, sn):
    out = []
    for k in (0, 2, 4):
        re_, im_ = s[k], s[k + 1]
        out += [m(re_, c) - m(im_, sn), m(re_, sn) + m(im_, c)]
    return out


def build(g, rotv, on, n, h, psi_v1, line):
    """Every variant's start, control seeds, start bounds (e0, ep, em) and seed bound, from the draws."""
    rp, ip, rm, im = m(g[0], h), m(g[1], h), m(g[2], h), m(g[3], h)
    nsum = m(rp, rp) + m(ip, ip) + m(rm, rm) + m(im, im)
    need_vn = on[VNC] or on[FLIP] or on[MODE0]
    psi_vn = sharp(nsum, n, line) if need_vn else 0
    vac = uv_of(rp, ip, rm, im)
    init = [None] * 7
    init[VNC] = [psi_vn, 0, rp, ip, rm, im]
    init[V1] = [psi_v1, 0, rp, ip, rm, im]
    init[V0] = [ONE + m(g[4], h), m(g[5], h), rp, ip, rm, im]
    init[RN] = [ONE, 0, rp, ip, rm, im]
    init[FLIP] = list(init[VNC])
    lp, lip, lm, lim = rp, ip, rp, -ip
    psi_l = sharp(m(lp, lp) + m(lip, lip) + m(lm, lm) + m(lim, lim), n, line) if on[LOCK] else 0
    init[LOCK] = [psi_l, 0, lp, lip, lm, lim]
    init[MODE0] = rot(init[VNC], rotv[0], rotv[1])
    uv = [list(vac) for _ in range(7)]
    uv[LOCK] = uv_of(lp, lip, lm, lim)
    ec = [seed_err(g[0]), seed_err(g[1]), seed_err(g[2]), seed_err(g[3])]
    ep, em = ec[0] + ec[1], ec[2] + ec[3]
    e_vn = sharp_err([rp, ip, rm, im], ec, n, line) if need_vn else 0
    ib = [None] * 7
    ib[VNC] = [e_vn, ep, em]
    ib[V1] = [2, ep, em]
    ib[V0] = [seed_err(g[4]) + seed_err(g[5]), ep, em]
    ib[RN] = [0, ep, em]
    ib[FLIP] = list(ib[VNC])
    e_l = sharp_err([lp, lip, lm, lim], [ec[0], ec[1], ec[0], ec[1]], n, line) if on[LOCK] else 0
    ib[LOCK] = [e_l, ep, ep]
    ib[MODE0] = [cu(e, ONE + (1 << 11)) + 3 for e in ib[VNC]]
    sb = [ep + em] * 7
    sb[LOCK] = 2 * ep
    return init, uv, ib, sb


def lin(ctrl, uv, n):
    cc, rs, mz = ctrl
    u_re, u_im, v_re, v_im = uv
    zc_re = mz + m(cc, u_re) - m(rs, v_im)
    zc_im = m(cc, u_im) + m(rs, v_re)
    xc = m(zc_re, zc_re) + m(zc_im, zc_im) - ONE // n
    return zc_re, zc_im, xc


def field_bounds(ob, ctrl, du, vals, zc):
    cc, rs, _ = ctrl
    bzc = 2 + cu(abs(cc), du) + cu(abs(rs), du)
    zcr, zci = abs(zc[0]), abs(zc[1])
    bxc = 3 + cu(2 * zcr, bzc) + cu(2 * zci, bzc) + 2 * cu(bzc, bzc)
    zr, zi, dzr, dzi, xw, dxw, xnc, dxnc, f, br, bi = [abs(v) for v in vals]
    bzr, bzi, bxw, bxnc, bf, bbr, bbi = ob
    bdzr, bdzi, bdxw, bdxnc = bzr + bzc, bzi + bzc, bxw + bxc, bxnc + bxc

    def qb(a, b):
        return cu(2 * a, b) + cu(b, b) + 1

    def sq(a, b):
        return 2 * a * b + b * b

    def pr(a, ba, c, bc):
        return a * bc + c * ba + ba * bc

    return [
        bzr, bzi, bdzr, bdzi, bxw, bdxw, bxnc, bdxnc, bf,
        qb(dzr, bdzr), qb(dxw, bdxw), qb(dxnc, bdxnc), qb(zr, bzr), qb(xw, bxw), qb(xnc, bxnc), qb(dzi, bdzi),
        sq(f, bf), bbr, bbi, sq(br, bbr), sq(bi, bbi), pr(br, bbr, bi, bbi), pr(zr, bzr, xw, bxw),
        pr(zr, bzr, xnc, bxnc), pr(dzr, bdzr, dxw, bdxw), pr(dzr, bdzr, dxnc, bdxnc),
        sq(zr, bzr), sq(zi, bzi), sq(dzr, bdzr), sq(dzi, bdzi), sq(xw, bxw), sq(dxw, bdxw), sq(xnc, bxnc),
        sq(dxnc, bdxnc),
    ]


class Stream:
    def __init__(self, lines):
        self.lines = lines
        self.i = 0

    def row(self, kind, keys):
        ln = self.i + 1
        if self.i >= len(self.lines):
            raise Stop("truncated", ln - 1, expected=kind)
        t = self.lines[self.i]
        parts = t.split("|")
        if parts[0] != kind:
            raise Stop("row_kind", ln, expected=kind, got=parts[0][:40])
        vals = []
        for j, k in enumerate(keys, 1):
            if j >= len(parts):
                raise Stop("row_short", ln, kind=kind, missing=k)
            p = parts[j]
            e = p.find("=")
            if e < 0:
                raise Stop("row_field_without_value", ln, kind=kind, token=p[:40])
            if p[:e] != k:
                raise Stop("row_key", ln, kind=kind, expected=k, got=p[:e][:40])
            vals.append(p[e + 1:])
        if len(parts) > len(keys) + 1:
            raise Stop("row_long", ln, kind=kind)
        self.i += 1
        d = dict(zip(keys, vals))
        if "float_used" in d and d["float_used"] != "0":
            raise Stop("head_float_used" if kind == "TWB_HEAD" else "float_used", ln, kind=kind, text=d["float_used"])
        if d["json"] != "0":
            raise Stop("field_value", ln, kind=kind, field="json", text=d["json"])
        return d, ln, t


def pint(text, field, line, lo=I128_MIN, hi=I128_MAX):
    if not INT_RE.match(text) or text == "-0":
        raise Stop("bad_integer", line, field=field, text=text[:40])
    v = int(text)
    if v < lo or v > hi:
        raise Stop("bad_integer", line, field=field, text=text[:40])
    return v


def pvec(text, field, line, k, lo=I64_MIN, hi=I64_MAX):
    parts = text.split(":")
    if len(parts) != k:
        raise Stop("bad_list", line, field=field, text=text[:40])
    return [pint(p, field, line, lo, hi) for p in parts]


def want(d, field, expect, line):
    if d[field] != expect:
        raise Stop("field_value", line, field=field, stream=d[field][:60], expected=expect[:60])


def sha_hex(b):
    return hashlib.sha256(b).hexdigest()


def detail_text(detail):
    s = ",".join(f"{k}={v}" for k, v in detail.items())
    return "".join(ch if 32 <= ord(ch) < 127 and ch != "|" else "_" for ch in s)


def read_block(point, call, side_path, data):
    """The aggregate rows of one call (without AGG_END), or a Stop."""
    if not data:
        raise Stop("empty_stream", 0)
    bad = data.translate(None, PRINTABLE)
    if bad:
        pos = data.index(bad[:1])
        raise Stop("non_printable_byte", data.count(b"\n", 0, pos) + 1, byte=bad[0])
    if data[-1] != 10:
        nlines = data.count(b"\n") + 1
        raise Stop("unterminated_last_line", nlines, bytes=len(data) - (data.rfind(b"\n") + 1))
    lines = data[:-1].decode("ascii").split("\n")
    st = Stream(lines)
    if lines[0].split("|")[0] != "TWB_HEAD":
        raise Stop("first_row_not_TWB_HEAD", 1)
    hd, hl, head_text = st.row("TWB_HEAD", K_HEAD)
    if hd["engine"] != "twens":
        raise Stop("field_value", hl, field="engine", stream=hd["engine"])
    if hd["version"] != "0.4.0":
        raise Stop("head_version", hl, stream=hd["version"], expected="0.4.0")
    want(hd, "cli", "dump", hl)
    if hd["binary_sha256"] != BIN_SHA:
        raise Stop("head_binary_sha256", hl, stream=hd["binary_sha256"][:64])
    if hd["source_sha256"] != SRC_SHA:
        raise Stop("head_source_sha256", hl, stream=hd["source_sha256"][:80])
    if hd["reserved"] != "0":
        raise Stop("head_reserved", hl, stream=hd["reserved"])
    if hd["guard"] != "active":
        raise Stop("head_guard", hl, stream=hd["guard"])
    want(hd, "q", "40", hl)
    want(hd, "sums", SUMS_TEXT, hl)
    want(hd, "rounding", ROUNDING_TEXT, hl)
    n = pint(hd["N"], "N", hl, I64_MIN, I64_MAX)
    if n < 2:
        raise Stop("head_N", hl, stream=n)
    for f in ("delta", "u", "y"):
        if not RAT_RE.match(hd[f]) or hd[f].startswith("-0"):
            raise Stop("bad_rational", hl, field=f, text=hd[f][:40])
    y_zero = 1 if hd["y"].split("/")[0] == "0" else 0  # RAT_RE holds: zero exactly when the numerator is 0
    seed = pint(hd["seed"], "seed", hl, 0, U64_MAX)
    seed_string = hd["seed_string"]
    # The engine prints seed_string=none when it was given seed= instead: no string binds that seed (section 6).
    if seed_string == "none" or seed != int.from_bytes(hashlib.sha256(seed_string.encode()).digest()[:8], "big"):
        raise Stop("head_seed", hl, seed=seed, seed_string=seed_string)
    start = pint(hd["start"], "start", hl, 0, U64_MAX)
    count = pint(hd["count"], "count", hl, 0, U64_MAX)
    if count == 0 or count > 4096 or hd["samples"] != hd["count"]:
        raise Stop("head_count", hl, count=hd["count"], samples=hd["samples"])
    dtden = pint(hd["dtden"], "dtden", hl, I64_MIN, I64_MAX)
    if dtden < 1:
        raise Stop("head_dtden", hl, stream=dtden)
    want(hd, "threads", "1", hl)
    steps_t = hd["steps"].split(",")
    steps = [pint(s, "steps", hl, 0, U64_MAX) for s in steps_t]
    if any(steps[k] >= steps[k + 1] for k in range(len(steps) - 1)):
        raise Stop("head_steps_not_increasing", hl, steps=hd["steps"])
    nrec = len(steps)
    mask_t = hd["mask"].split(",")
    canon = VN + ["NL"]
    if any(x not in canon for x in mask_t) or [canon.index(x) for x in mask_t] != sorted(
        set(canon.index(x) for x in mask_t)
    ):
        raise Stop("head_mask", hl, mask=hd["mask"])
    if "VNC" not in mask_t:
        raise Stop("no_VNC", hl, mask=hd["mask"])
    on = [VN[v] in mask_t for v in range(7)]
    nl = "NL" in mask_t
    pres = [v for v in range(7) if on[v]]
    nv = len(pres)
    table = "none"
    if point in TABLE:
        table = "checked"
        tn, tdelta, ty, calls, nall, tsteps, _ = TABLE[point]
        if call >= calls:
            raise Stop("table_call_out_of_range", hl, call=call, calls=calls)
        tmask = FULL_MASK if call < nall else "VNC"
        exp = {
            "N": str(tn), "delta": tdelta, "u": "1", "y": ty,
            "seed_string": f"stripes-ens-v1:N{tn}:d{tdelta}:y{ty}",
            "start": str(4096 * call), "count": "4096", "dtden": "64", "mask": tmask,
        }
        for k, v in exp.items():
            if hd[k] != v:
                raise Stop("table_mismatch", hl, field=k, stream=hd[k][:60], table=v)
        if steps != tsteps[:nrec]:
            raise Stop("table_mismatch", hl, field="steps", stream=hd["steps"])
    h = isqrt((ONE * ONE) // (4 * n))
    psi_v1 = isqrt((((2 * n + 1) * ONE) // (2 * n)) * ONE)
    M = count
    # per-sample storage
    obs = [[[None] * M for _ in range(nrec)] for _ in range(7)]  # obs[v][r][i] = (7 obs, zc3)
    rbs = [[[None] * M for _ in range(nrec)] for _ in range(7)]  # rbs[v][r][i] = (eps, 7 bounds)
    uvs = [[None] * M for _ in range(7)]
    sbs = [[0] * M for _ in range(7)]
    draws = []  # per sample (g, rot, rot text, [(s, uv, e0:ep:em, seeds, eta) per variant]), checked once all is read
    for i in range(M):
        idx = start + i
        sd, sl, _ = st.row("TWB_DUMP_SAMPLE", K_SAMPLE)
        if sd["idx"] != str(idx):
            raise Stop("sample_index", sl, expected=idx, stream=sd["idx"][:30])
        g = pvec(sd["g"], "g", sl, 6)
        rotv = pvec(sd["rot"], "rot", sl, 2)
        per_v = []
        for v in pres:
            d, ln, _ = st.row("TWB_DUMP_INIT", K_INIT)
            if d["idx"] != str(idx):
                raise Stop("sample_index", ln, expected=idx, stream=d["idx"][:30])
            want(d, "variant", VN[v], ln)
            s = pvec(d["s"], "s", ln, 6)
            u4 = pvec(d["uv"], "uv", ln, 4)
            d, ln, _ = st.row("TWB_DUMP_IB", K_IB)
            if d["idx"] != str(idx):
                raise Stop("sample_index", ln, expected=idx, stream=d["idx"][:30])
            want(d, "variant", VN[v], ln)
            e3 = [pint(d[k], k, ln, 0, U128_MAX) for k in ("e0", "ep", "em")]
            sbv = pint(d["seeds"], "seeds", ln, 0, U128_MAX)
            et = pint(d["eta"], "eta", ln, 0, U128_MAX)
            per_v.append((s, u4, e3, sbv, et))
            uvs[v][i] = u4
            sbs[v][i] = sbv
            for r in range(nrec):
                d, ln, _ = st.row("TWB_DUMP_OBS", K_OBS)
                if d["idx"] != str(idx):
                    raise Stop("sample_index", ln, expected=idx, stream=d["idx"][:30])
                want(d, "variant", VN[v], ln)
                want(d, "step", str(steps[r]), ln)
                o = [pint(d[k], k, ln, I64_MIN, I64_MAX) for k in ("zr", "zi", "xw", "xnc", "f", "br", "bi")]
                zc = [pint(d[k], k, ln, I64_MIN, I64_MAX) for k in ("zcr", "zci", "xc")]
                obs[v][r][i] = (o, zc, ln)
                d, ln, _ = st.row("TWB_DUMP_RB", K_RB)
                if d["idx"] != str(idx):
                    raise Stop("sample_index", ln, expected=idx, stream=d["idx"][:30])
                want(d, "variant", VN[v], ln)
                want(d, "step", str(steps[r]), ln)
                b = [pint(d[k], k, ln, 0, U128_MAX) for k in ("eps", "b_zr", "b_zi", "b_xw", "b_xnc", "b_f", "b_br",
                                                              "b_bi", "b_z2", "b_fcl")]
                rbs[v][r][i] = (b[0], b[1:8])
        draws.append((g, rotv, sd["rot"], per_v))
    # summary rows: each value is parsed as its row is read; the sums are compared once the whole stream is read
    ctrls = [None] * nrec
    nl_rows = [None] * nrec
    summ = {}  # (kind, record, variant or pair) -> [values]

    def set_ctrl(r, text, ln):
        cv = pvec(text, "ctrl", ln, 3)
        if ctrls[r] is None:
            ctrls[r] = (cv, text)
        elif ctrls[r][1] != text:
            raise Stop("ctrl_differs_within_record", ln, step=steps[r])

    h_seen = []

    def set_h(text, ln):
        hv = pint(text, "h", ln, I64_MIN, I64_MAX)
        if not h_seen:
            h_seen.append(hv)
        elif hv != h_seen[0]:
            raise Stop("h_differs", ln, stream=text[:30])

    def common(d, ln, keys):
        for k in keys:
            if k in ("N", "delta", "u", "y", "seed", "start", "count", "dtden", "samples", "seed_string"):
                want(d, k, hd[k] if k != "samples" else hd["count"], ln)

    def values(d, ln, names, unsigned):
        lo, hi = (0, U128_MAX) if unsigned else (I128_MIN, I128_MAX)
        return [pint(d[x], x, ln, lo, hi) for x in names]

    for r in range(nrec):
        for v, name in LEGACY:
            if not on[v]:
                continue
            d, ln, _ = st.row("TWENS", K_TWENS)
            common(d, ln, K_TWENS)
            want(d, "step", str(steps[r]), ln)
            want(d, "variant", name, ln)
            want(d, "n", str(M), ln)
            set_h(d["h"], ln)
            set_ctrl(r, d["ctrl"], ln)
            summ[("TWENS", r, v)] = values(d, ln, TWB_F[:16], False)
        if on[V1] and on[VNC] and on[V0]:
            d, ln, _ = st.row("TWPAIR", K_TWPAIR)
            common(d, ln, K_TWPAIR)
            want(d, "step", str(steps[r]), ln)
            want(d, "n", str(M), ln)
            summ[("TWPAIR", r, None)] = values(d, ln, TWPAIR_F, False)
        for v in pres:
            d, ln, _ = st.row("TWB", K_TWB)
            common(d, ln, K_TWB)
            want(d, "step", str(steps[r]), ln)
            want(d, "variant", VN[v], ln)
            want(d, "init", VINIT[v], ln)
            want(d, "seeds", VSEEDS[v], ln)
            want(d, "kappa", VKAPPA[v], ln)
            want(d, "phase", VPHASE[v], ln)
            want(d, "n", str(M), ln)
            set_h(d["h"], ln)
            set_ctrl(r, d["ctrl"], ln)
            summ[("TWB", r, v)] = values(d, ln, TWB_F, False)
            d, ln, _ = st.row("TWB_ROUND", K_ROUND)
            common(d, ln, K_ROUND)
            want(d, "step", str(steps[r]), ln)
            want(d, "variant", VN[v], ln)
            want(d, "n", str(M), ln)
            summ[("TWB_ROUND", r, v)] = values(d, ln, ROUND_F, True)
            want(d, "units", UNITS_TEXT, ln)
        for k, (va, _, vb, _, name) in enumerate(PAIRS):
            if not (on[va] and on[vb]):
                continue
            for kind, keys, names in (("TWB_PAIR", K_PAIR, PAIR_F), ("TWB_PAIR_ROUND", K_PROUND, PROUND_F)):
                d, ln, _ = st.row(kind, keys)
                common(d, ln, keys)
                want(d, "step", str(steps[r]), ln)
                want(d, "pair", name, ln)
                want(d, "n", str(M), ln)
                summ[(kind, r, k)] = values(d, ln, names, kind == "TWB_PAIR_ROUND")
        if nl:
            d, ln, t = st.row("TWB_NL", K_NL)
            for k in ("N", "delta", "u", "y", "dtden"):
                want(d, k, hd[k], ln)
            want(d, "step", str(steps[r]), ln)
            want(d, "init", NL_INIT, ln)
            want(d, "kappa", "1", ln)
            want(d, "reads", NL_READS, ln)
            want(d, "at", "2^40", ln)
            for k in ("zr", "zi", "z2", "xw", "xnc", "f", "fcl", "br", "bi"):
                pint(d[k], k, ln, I64_MIN, I64_MAX)
            for k in ("rb_zr", "rb_zi", "rb_z2", "rb_xw", "rb_xnc", "rb_f", "rb_fcl", "rb_br", "rb_bi", "eps"):
                pint(d[k], k, ln, 0, U128_MAX)
            nl_rows[r] = t
        if ctrls[r] is None:
            raise Stop("record_without_ctrl", st.i, step=steps[r])
        if table == "checked" and ctrls[r][0] != [0, 0, 0]:
            raise Stop("table_mismatch", st.i, field="ctrl", step=steps[r], stream=ctrls[r][1][:40])
    d, ln, _ = st.row("TWB_DONE", K_DONE)
    want(d, "n", str(M), ln)
    want(d, "records", str(nrec), ln)
    want(d, "mask", hd["mask"], ln)
    if st.i != len(lines):
        raise Stop("rows_after_TWB_DONE", st.i + 1)

    # every row is read: h, then each sample's draws, starts, control seeds and start bounds
    if h_seen and h_seen[0] != h:
        raise Stop("h_mismatch", 0, stream=h_seen[0], reader=h)
    flags = []
    lat = []
    starts = 0
    for i, (g, rotv, rot_text, per_v) in enumerate(draws):
        c = []
        for gi in g:
            if gi % (1 << 35) != 0 or abs(gi >> 35) > 2048:
                raise Stop("draw_not_a_coin_count", 0, idx=start + i, g=gi)
            c.append(gi >> 35)
        flags.append(flags_of(c))
        lat.append((c[0] * c[0] - c[1] * c[1], 2 * c[0] * c[1]))
        if any(abs(x) > ROT_LIMIT for x in rotv):
            raise Stop("rot_out_of_range", 0, idx=start + i, rot=rot_text)
        if not on[MODE0] and rotv != [ONE, 0]:
            raise Stop("rot_without_MODE0", 0, idx=start + i, rot=rot_text)
        if table == "checked":
            eg, erot, eeta = engine_draws(seed, start + i, on[MODE0])
            field = "g" if eg != g else "rot" if erot != rotv else "eta" if eeta != per_v[0][4] else None
            if field:
                raise Stop("draw_mismatch", 0, idx=start + i, field=field)
        init, uv, ib, sb = build(g, rotv, on, n, h, psi_v1, 0)
        eta = None
        for v, (s, u4, e3, sbv, et) in zip(pres, per_v, strict=True):
            if s != init[v]:
                raise Stop("start_mismatch", 0, variant=VN[v], stream=":".join(map(str, s)),
                           reader=":".join(map(str, init[v])))
            if u4 != uv[v]:
                raise Stop("control_seed_mismatch", 0, variant=VN[v], stream=":".join(map(str, u4)))
            if e3 != ib[v] or sbv != sb[v]:
                raise Stop("start_bound_mismatch", 0, variant=VN[v])
            if eta is None:
                eta = et
            elif et != eta:
                raise Stop("eta_mismatch", 0, variant=VN[v])
            if not on[MODE0] and et != 0:
                raise Stop("eta_mismatch", 0, variant=VN[v], why="MODE0_off")
            starts += 1

    # record by record: per variant the linear controls and the TWB, TWB_ROUND and TWENS sums, then per pair the
    # TWB_PAIR and TWB_PAIR_ROUND sums, then TWPAIR
    lin_n = 0
    rows_n = 0
    fields_n = 0
    sums = {}

    def cmp(kind, r, label, names, stream_vals, reader_vals):
        nonlocal rows_n, fields_n
        rows_n += 1
        for nm, x, rv in zip(names, stream_vals, reader_vals, strict=True):
            if x != rv:
                raise Stop("summary_mismatch", 0, row=kind, step=steps[r], of=label, field=nm, stream=x, reader=rv)
            fields_n += 1

    legacy = dict(LEGACY)
    for r in range(nrec):
        cv = ctrls[r][0]
        for v in pres:
            S = [0] * 34
            RB = [0] * 34
            epsmax = 0
            for i in range(M):
                o, zc, ln = obs[v][r][i]
                if list(lin(cv, uvs[v][i], n)) != zc:
                    raise Stop("linear_control_mismatch", 0, variant=VN[v], step=steps[r])
                lin_n += 1
                zr, zi, xw, xnc, f, br, bi = o
                dzr, dzi, dxw, dxnc = zr - zc[0], zi - zc[1], xw - zc[2], xnc - zc[2]
                vals = [zr, zi, dzr, dzi, xw, dxw, xnc, dxnc, f]
                qv = [(x * x) >> Q for x in (dzr, dxw, dxnc, zr, xw, xnc, dzi)]
                xv = [f * f, br, bi, br * br, bi * bi, br * bi, zr * xw, zr * xnc, dzr * dxw, dzr * dxnc]
                ev = [x * x for x in (zr, zi, dzr, dzi, xw, dxw, xnc, dxnc)]
                row = vals + qv + xv + ev
                for k in range(34):
                    S[k] += row[k]
                eps, ob = rbs[v][r][i]
                fb = field_bounds(ob, cv, sbs[v][i], vals + [br, bi], zc)
                for k in range(34):
                    RB[k] += fb[k]
                if eps > epsmax:
                    epsmax = eps
            sums[("TWB", r, v)] = S
            sums[("TWB_ROUND", r, v)] = RB + [epsmax]
            cmp("TWB", r, VN[v], TWB_F, summ[("TWB", r, v)], S)
            cmp("TWB_ROUND", r, VN[v], ROUND_F, summ[("TWB_ROUND", r, v)], RB + [epsmax])
            if v in legacy:
                cmp("TWENS", r, legacy[v], TWB_F[:16], summ[("TWENS", r, v)], S[:16])
        pair_sums = {}
        for k, (va, oa, vb, ob_, name) in enumerate(PAIRS):
            if not (on[va] and on[vb]):
                continue
            pd = pq = pd2 = 0
            r0 = r1 = r2 = 0
            for i in range(M):
                dd = obs[va][r][i][0][oa] - obs[vb][r][i][0][ob_]
                pd += dd
                pq += (dd * dd) >> Q
                pd2 += dd * dd
                bd = rbs[va][r][i][1][oa] + rbs[vb][r][i][1][ob_]
                ad = abs(dd)
                r0 += bd
                r1 += cu(2 * ad, bd) + cu(bd, bd) + 1
                r2 += 2 * ad * bd + bd * bd
            pair_sums[k] = [pd, pq, pd2]
            cmp("TWB_PAIR", r, name, PAIR_F, summ[("TWB_PAIR", r, k)], [pd, pq, pd2])
            cmp("TWB_PAIR_ROUND", r, name, PROUND_F, summ[("TWB_PAIR_ROUND", r, k)], [r0, r1, r2])
        if ("TWPAIR", r, None) in summ:
            rv = []
            for k in range(5):
                rv += pair_sums[k][:2]
            cmp("TWPAIR", r, "legacy", TWPAIR_F, summ[("TWPAIR", r, None)], rv)

    # the aggregate rows
    pc = f"point={point}|call={call}"
    out = []
    out.append(
        f"AGG_HEAD|reader={READER}|reader_version={READER_VERSION}|{pc}|table={table}|stdin_bytes={len(data)}"
        f"|stdin_lines={len(lines)}|stdin_sha256={sha_hex(data)}|json=0"
    )
    out.append("AGG_TWB_HEAD|" + head_text)
    nl_sha = sha_hex("".join(t + "\n" for t in nl_rows).encode()) if nl else "none"
    out.append(
        f"AGG_CALL|{pc}|N={hd['N']}|delta={hd['delta']}|u={hd['u']}|y={hd['y']}|y_zero={y_zero}|seed={seed}"
        f"|seed_string={seed_string}|start={start}|count={count}|dtden={dtden}|h={h}|steps={hd['steps']}"
        f"|records={nrec}|mask={hd['mask']}|variants={','.join(VN[v] for v in pres)}|nl={int(nl)}"
        f"|ctrl={';'.join(t for _, t in ctrls)}|nl_sha256={nl_sha}|json=0"
    )
    cnt = [sum(1 for fl in flags if fl[k]) for k in range(4)]
    out.append(f"AGG_ATOMS|{pc}|M={M}|nl_klein={cnt[0]}|nl_exch={cnt[1]}|lk_klein={cnt[2]}|lk_exch={cnt[3]}|json=0")

    def atom(v, i):
        fl = flags[i]
        if y_zero:
            return fl[2] if v == LOCK else fl[0]
        return fl[3] if v == LOCK else fl[1]

    def xatom(v, i):
        return flags[i][3] if v == LOCK else flags[i][1]

    lock_atoms = 0
    lat_edge = 0
    latc = [0] * 16
    lat_sec = [None] * M
    for i in range(M):
        x, yv = lat[i]
        lat_sec[i] = sigma(x, yv)
        if atom(LOCK, i):
            lock_atoms += 1
        elif x == 0 or yv == 0 or abs(x) == abs(yv):
            lat_edge += 1
        else:
            latc[lat_sec[i]] += 1
    out.append(f"AGG_LAT|{pc}|lock_atoms={lock_atoms}|lat_edge={lat_edge}|lat={':'.join(map(str, latc))}|json=0")

    # per sample, per record, per variant: certified sector, sign states, big
    side_recs = [r for r in range(nrec) if steps[r] in (64, 128)]
    for r in range(nrec):
        cert = {}
        sbr = {}
        sbi = {}
        big = {}
        for v in pres:
            ce, s1, s2, bg = [None] * M, [0] * M, [0] * M, [False] * M
            for i in range(M):
                o = obs[v][r][i][0]
                bb = rbs[v][r][i][1]
                br, bi, bbr, bbi = o[5], o[6], bb[5], bb[6]
                ce[i] = certified(br, bi, bbr, bbi)
                s1[i] = sign_state(br, bbr)
                s2[i] = sign_state(bi, bbi)
                bg[i] = br * br + bi * bi >= ONE
            cert[v], sbr[v], sbi[v], big[v] = ce, s1, s2, bg
        for v in pres:
            at = [atom(v, i) for i in range(M)]
            na = M - sum(at)
            xat = [xatom(v, i) for i in range(M)]
            xnz = sum(1 for i in range(M) if xat[i] and obs[v][r][i][0][6] != 0)
            nabi0 = sum(1 for i in range(M) if not at[i] and obs[v][r][i][0][6] == 0)
            sec = [0] * 16
            amb = 0
            sgn = [[0] * 3 for _ in range(4)]  # br na, bi na, br atom, bi atom
            for i in range(M):
                if at[i]:
                    sgn[2][sbr[v][i]] += 1
                    sgn[3][sbi[v][i]] += 1
                else:
                    if cert[v][i] is None:
                        amb += 1
                    else:
                        sec[cert[v][i]] += 1
                    sgn[0][sbr[v][i]] += 1
                    sgn[1][sbi[v][i]] += 1
            natoms = M - na
            if not (sum(sec) + amb == na and sum(sgn[0]) == na and sum(sgn[1]) == na
                    and sum(sgn[2]) == natoms and sum(sgn[3]) == natoms):
                raise Stop("aggregate_identity", 0, what="vr_counts", step=steps[r], variant=VN[v])
            out.append(
                f"AGG_VR|{pc}|step={steps[r]}|variant={VN[v]}|M={M}|atoms={natoms}|xatoms={sum(xat)}"
                f"|xatom_bi_nz={xnz}|mp={na}|na_bi0={nabi0}|sec={':'.join(map(str, sec))}|amb={amb}"
                f"|br_pos={sgn[0][0]}|br_neg={sgn[0][1]}|br_amb={sgn[0][2]}"
                f"|bi_pos={sgn[1][0]}|bi_neg={sgn[1][1]}|bi_amb={sgn[1][2]}"
                f"|at_br_pos={sgn[2][0]}|at_br_neg={sgn[2][1]}|at_br_amb={sgn[2][2]}"
                f"|at_bi_pos={sgn[3][0]}|at_bi_neg={sgn[3][1]}|at_bi_amb={sgn[3][2]}|json=0"
            )
            for setname in ("all", "atom"):
                acc = [0] * 10
                for i in range(M):
                    if setname == "atom" and not at[i]:
                        continue
                    o = obs[v][r][i][0]
                    bb = rbs[v][r][i][1]
                    br, bi, bbr, bbi = o[5], o[6], bb[5], bb[6]
                    for k, x in enumerate((1, br, bi, br * br, bi * bi, br * bi, bbr, bbi, bbr * bbr, bbi * bbi)):
                        acc[k] += x
                if setname == "all":
                    tw = sums[("TWB", r, v)]
                    trb = sums[("TWB_ROUND", r, v)]
                    if acc[1:6] != tw[17:22] or acc[6] != trb[17] or acc[7] != trb[18]:
                        raise Stop("aggregate_identity", 0, what="sum_all_vs_TWB", step=steps[r], variant=VN[v])
                    w_all = acc[3] + acc[4]
                out.append(
                    f"AGG_SUM|{pc}|step={steps[r]}|variant={VN[v]}|set={setname}|m={acc[0]}|br={acc[1]}"
                    f"|bi={acc[2]}|br2={acc[3]}|bi2={acc[4]}|brbi={acc[5]}|bbr={acc[6]}|bbi={acc[7]}"
                    f"|bbr2={acc[8]}|bbi2={acc[9]}|json=0"
                )
            for bn in BLOCKS:
                K = M // bn
                s2 = s4 = w = w2 = sw = 0
                for b in range(K):
                    xr = xi = wb = 0
                    for i in range(b * bn, (b + 1) * bn):
                        o = obs[v][r][i][0]
                        xr += o[5]
                        xi += o[6]
                        wb += o[5] * o[5] + o[6] * o[6]
                    a2 = xr * xr + xi * xi
                    s2 += a2
                    s4 += a2 * a2
                    w += wb
                    w2 += wb * wb
                    sw += a2 * wb
                if K * bn == M and w != w_all:
                    raise Stop("aggregate_identity", 0, what="blk_w", step=steps[r], variant=VN[v], n=bn)
                out.append(
                    f"AGG_BLK|{pc}|step={steps[r]}|variant={VN[v]}|n={bn}|K={K}|s2={s2}|s4={s4}|w={w}|w2={w2}"
                    f"|sw={sw}|json=0"
                )
            if v != VNC:
                tbr = [0] * 9
                tbi = [0] * 9
                common_n = cert2 = mis = c2bb = mbb = c2ba = mba = 0
                for i in range(M):
                    if at[i] or atom(VNC, i):
                        continue
                    common_n += 1
                    tbr[3 * sbr[v][i] + sbr[VNC][i]] += 1
                    tbi[3 * sbi[v][i] + sbi[VNC][i]] += 1
                    a, b = cert[v][i], cert[VNC][i]
                    if a is not None and b is not None:
                        cert2 += 1
                        mis += a != b
                        if big[v][i] and big[VNC][i]:
                            c2bb += 1
                            mbb += a != b
                        if big[v][i] or big[VNC][i]:
                            c2ba += 1
                            mba += a != b
                out.append(
                    f"AGG_CMP|{pc}|step={steps[r]}|variant={VN[v]}|ref=VNC|common={common_n}"
                    f"|br={':'.join(map(str, tbr))}|bi={':'.join(map(str, tbi))}|cert2={cert2}|mis={mis}"
                    f"|cert2_big_both={c2bb}|mis_big_both={mbb}|cert2_big_any={c2ba}|mis_big_any={mba}|json=0"
                )
            if v == LOCK:
                lc = lm_ = 0
                for i in range(M):
                    if at[i] or cert[v][i] is None:
                        continue
                    lc += 1
                    lm_ += cert[v][i] != lat_sec[i]
                out.append(f"AGG_LOCK|{pc}|step={steps[r]}|cert={lc}|mis={lm_}|json=0")
        if nl:
            out.append("AGG_NL|" + nl_rows[r])
    if side_path is not None:
        vmask = sum(1 << v for v in pres)
        hdr = b"STRPSIDE" + (1).to_bytes(4, "little") + nv.to_bytes(4, "little") + vmask.to_bytes(4, "little")
        hdr += len(side_recs).to_bytes(4, "little")
        for k in range(2):
            hdr += (steps[side_recs[k]] if k < len(side_recs) else 0).to_bytes(4, "little")
        hdr += start.to_bytes(8, "little") + M.to_bytes(8, "little") + bytes(16)
        body = [hdr]
        for i in range(M):
            fl = flags[i]
            body.append((fl[0] | fl[1] << 1 | fl[2] << 2 | fl[3] << 3).to_bytes(8, "little"))
            for v in pres:
                for r in side_recs:
                    bbr = rbs[v][r][i][1][5]
                    if bbr > U64_MAX:
                        raise Stop("side_bound_above_u64", 0, variant=VN[v], step=steps[r])
                    body.append(obs[v][r][i][0][5].to_bytes(8, "little", signed=True) + bbr.to_bytes(8, "little"))
        blob = b"".join(body)
        try:
            with open(side_path, "wb") as fh:
                fh.write(blob)
        except OSError as e:
            raise Stop("side_write", 0, error=type(e).__name__)
        stp = ",".join(str(steps[r]) for r in side_recs) or "none"
        out.append(
            f"AGG_SIDE|{pc}|path={side_path}|bytes={len(blob)}|sha256={sha_hex(blob)}|indices={M}"
            f"|variants={','.join(VN[v] for v in pres)}|steps={stp}|json=0"
        )
    out.append(
        f"AGG_CHECK|{pc}|samples={M}|starts={starts}|lin={lin_n}|rows={rows_n}|fields={fields_n}"
        f"|result=all_equal|json=0"
    )
    return out


def main(argv):
    data = sys.stdin.buffer.read()
    point = call_t = "-"
    side = None
    try:
        args = argv[1:]
        seen = {}
        k = 0
        while k < len(args):
            a = args[k]
            if a not in ("--point", "--call", "--side") or a in seen or k + 1 >= len(args):
                raise Stop("usage", 0, arg=a[:40])
            seen[a] = args[k + 1]
            k += 2
        if "--point" not in seen or "--call" not in seen:
            raise Stop("usage", 0, missing="point_or_call")
        if not INT_RE.match(seen["--call"]) or seen["--call"].startswith("-") or int(seen["--call"]) > U64_MAX:
            raise Stop("usage", 0, call=seen["--call"][:40])
        point, call_t = seen["--point"], seen["--call"]
        call = int(call_t)
        side = seen.get("--side")
        if point not in TABLE and not TEST_RE.match(point):
            raise Stop("unknown_point", 0, point=point[:40])
        if point in ("P08", "P13") and call < 64 and side is None:
            raise Stop("side_file_required", 0)
        rows = read_block(point, call, side, data)
    except Stop as s:
        nlines = data.count(b"\n") + (1 if data and data[-1] != 10 else 0)
        row = (
            f"STOP|reader={READER}|reader_version={READER_VERSION}|point={point}|call={call_t}|reason={s.reason}"
            f"|line={s.line}|detail={detail_text(s.detail)}|stdin_bytes={len(data)}|stdin_lines={nlines}"
            f"|stdin_sha256={sha_hex(data)}|json=0"
        )
        sys.stdout.write(row + "\n")
        sys.stderr.write(row + "\n")
        return 3
    body = "".join(t + "\n" for t in rows)
    end = f"AGG_END|point={point}|call={call_t}|agg_lines={len(rows)}|agg_sha256={sha_hex(body.encode())}|json=0"
    sys.stdout.write(body + end + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
