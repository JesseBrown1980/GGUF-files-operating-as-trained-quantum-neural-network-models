"""Exact arithmetic for stage B on checked integer pairs (qint.Q): helpers, outward-rounded intervals, exact signs of
sums of square roots, decimal text in and out. No float, no fractions, no math, no true division: every rational is a
qint.Q and every operation goes through qint's checked functions."""

import re

from . import qint
from .qint import Q, ZERO, ONE, HALF  # noqa: F401  (re-exported for the row modules)

_INT = re.compile(r"-?(0|[1-9][0-9]*)\Z")
_DEC = re.compile(r"([+-]?)([0-9]+)(?:\.([0-9]+))?(?:e([+-]?[0-9]+))?\Z")
_RAT = re.compile(r"(-?(?:0|[1-9][0-9]*))(?:/([1-9][0-9]*))?\Z")


class ExactError(Exception):
    """A value that is not what the grammar or the arithmetic allows."""


def fr(n, d=1):
    """The rational n/d of ints or Qs, or of the canonical rational text parse_rat reads."""
    if type(n) is str:
        n = parse_rat(n)
    if type(d) is str:
        d = parse_rat(d)
    return div(n, d)


def div(a, b):
    """a/b exactly; b must be nonzero."""
    return qint.div(a, b)


def ipow(x, k):
    """x**k for an int k >= 0: an int for an int x, a Q for a Q."""
    if type(k) is not int or k < 0:
        raise ExactError("ipow takes an integer exponent >= 0")
    return qint.ipow(x, k)


def canon_int(text):
    """A canonical decimal integer (no '+', no leading zeros, no '-0')."""
    if not _INT.match(text) or text == "-0":
        raise ExactError("not a canonical integer: " + text)
    return int(text)


def parse_rat(text):
    """A rational in the engines' text: an integer or n/d in lowest terms with d > 1."""
    m = _RAT.match(text)
    if not m or text == "-0":
        raise ExactError("not a rational: " + text)
    n = int(m.group(1))
    if m.group(2) is None:
        return qint.make(n)
    d = int(m.group(2))
    if d == 1 or qint.gcd(n, d) != 1 or n == 0:
        raise ExactError("rational not in lowest terms: " + text)
    return qint.make(n, d)


def rat_text(x):
    """The engines' text of a rational."""
    return qint.text(fr(x))


class Decimal:
    """A frozen decimal: the exact rational it spells (rule DECIMAL) and the place of its last digit."""

    __slots__ = ("text", "value", "last")

    def __init__(self, text):
        m = _DEC.match(text)
        if not m:
            raise ExactError("not a decimal: " + text)
        sign, whole, frac, exp = m.groups()
        frac = frac or ""
        e = int(exp) if exp else 0
        digits = int(whole + frac)
        last = e - len(frac)
        v = qint.make(digits) * _p10(last)
        self.text = text
        self.value = -v if sign == "-" else v
        self.last = last

    def half_unit(self):
        """Half a unit of the last stated digit."""
        if self.last >= 0:
            return qint.make(ipow(10, self.last), 2)
        return fr(1, 2 * ipow(10, -self.last))

    def stated_band(self):
        return (self.value - self.half_unit(), self.value + self.half_unit())


def dec(text):
    """The exact rational of a frozen decimal."""
    return Decimal(text).value


def _floor(x):
    return qint.floor(x)


def _ceil(x):
    return qint.ceil(x)


def fmt(x, sig=10, mode="near"):
    """x as a decimal with sig significant digits, rounded to nearest (ties away from zero), down or up.

    Exact integer arithmetic; scientific notation outside [1e-3, 1e7)."""
    x = qint.q(x)
    if x == 0:
        return "0"
    neg = x < 0
    a = -x if neg else x
    # exponent e with 10^e <= a < 10^(e+1)
    e = len(str(_floor(a))) - 1 if a >= 1 else -len(str(_ceil(fr(1, a)))) + 1
    while a >= _p10(e + 1):
        e += 1
    while a < _p10(e):
        e -= 1
    scale = _p10(sig - 1 - e)
    v = a * scale
    if mode == "near":
        n = _floor(v + HALF)
    else:
        down = (mode == "down") != neg
        n = _floor(v) if down else _ceil(v)
    if n >= ipow(10, sig):
        n //= 10
        e += 1
    digits = str(n)
    if -3 <= e < 7:
        if e >= 0:
            ip = digits[: e + 1].ljust(e + 1, "0")
            fp = digits[e + 1 :]
        else:
            ip = "0"
            fp = "0" * (-e - 1) + digits
        fp = fp.rstrip("0")
        s = ip + ("." + fp if fp else "")
    else:
        mant = digits[0] + ("." + digits[1:].rstrip("0") if digits[1:].rstrip("0") else "")
        s = mant + "e" + str(e)
    return ("-" if neg else "") + s


def _p10(k):
    return qint.make(ipow(10, k)) if k >= 0 else fr(1, ipow(10, -k))


# ---------------------------------------------------------------------------------------------------------------------
# Intervals with outward rounding.

ROUND_BITS = 320


def round_down(x, bits=ROUND_BITS):
    x = qint.q(x)
    if x.d == 1 or x.d.bit_length() <= bits:
        return x
    return qint.make(_floor(x * ipow(2, bits)), ipow(2, bits))


def round_up(x, bits=ROUND_BITS):
    x = qint.q(x)
    if x.d == 1 or x.d.bit_length() <= bits:
        return x
    return qint.make(_ceil(x * ipow(2, bits)), ipow(2, bits))


class Iv:
    """A closed interval [lo, hi] of rationals; every operation encloses the exact result."""

    __slots__ = ("lo", "hi")
    _exact_operand = True

    def __init__(self, lo, hi=None):
        lo = qint.q(lo)
        hi = lo if hi is None else qint.q(hi)
        if lo > hi:
            raise ExactError("empty interval")
        self.lo = lo
        self.hi = hi

    @staticmethod
    def of(x):
        return x if isinstance(x, Iv) else Iv(x)

    def r(self, bits=ROUND_BITS):
        return Iv(round_down(self.lo, bits), round_up(self.hi, bits))

    def __add__(self, o):
        o = Iv.of(o)
        return Iv(self.lo + o.lo, self.hi + o.hi).r()

    __radd__ = __add__

    def __neg__(self):
        return Iv(-self.hi, -self.lo)

    def __sub__(self, o):
        return self + (-Iv.of(o))

    def __rsub__(self, o):
        return Iv.of(o) - self

    def __mul__(self, o):
        o = Iv.of(o)
        p = (self.lo * o.lo, self.lo * o.hi, self.hi * o.lo, self.hi * o.hi)
        return Iv(min(p), max(p)).r()

    __rmul__ = __mul__

    def sq(self):
        if self.lo >= 0:
            return Iv(self.lo * self.lo, self.hi * self.hi).r()
        if self.hi <= 0:
            return Iv(self.hi * self.hi, self.lo * self.lo).r()
        return Iv(0, max(self.lo * self.lo, self.hi * self.hi)).r()

    def inv(self):
        if self.lo <= 0 <= self.hi:
            raise ExactError("interval division by an interval that holds 0")
        return Iv(div(1, self.hi), div(1, self.lo)).r()

    def mid(self):
        return (self.lo + self.hi) * HALF

    def width(self):
        return self.hi - self.lo

    def contains(self, x):
        return self.lo <= x <= self.hi

    def pos(self):
        return self.lo > 0

    def neg(self):
        return self.hi < 0

    def __repr__(self):
        return "Iv[%s, %s]" % (fmt(self.lo, 16, "down"), fmt(self.hi, 16, "up"))


class Ext:
    """A closed interval [lo, hi] of the extended line, None standing for -inf (lo) or +inf (hi): what a ratio is when
    its denominator's interval reaches 0. Every operation encloses the exact result."""

    __slots__ = ("lo", "hi")
    _exact_operand = True

    def __init__(self, lo, hi):
        self.lo = None if lo is None else qint.q(lo)
        self.hi = None if hi is None else qint.q(hi)
        if self.lo is not None and self.hi is not None and self.lo > self.hi:
            raise ExactError("empty interval")

    @staticmethod
    def of(x):
        if isinstance(x, Ext):
            return x
        x = Iv.of(x)
        return Ext(x.lo, x.hi)

    def bounded(self):
        return self.lo is not None and self.hi is not None

    def iv(self):
        if not self.bounded():
            raise ExactError("unbounded interval")
        return Iv(self.lo, self.hi)

    def __add__(self, o):
        o = Ext.of(o)
        lo = None if self.lo is None or o.lo is None else round_down(self.lo + o.lo)
        hi = None if self.hi is None or o.hi is None else round_up(self.hi + o.hi)
        return Ext(lo, hi)

    __radd__ = __add__

    def __neg__(self):
        return Ext(None if self.hi is None else -self.hi, None if self.lo is None else -self.lo)

    def __sub__(self, o):
        return self + (-Ext.of(o))

    def scale(self, k):
        """k * self for a rational k."""
        k = qint.q(k)
        if k == 0:
            return Ext(0, 0)
        a = None if self.lo is None else self.lo * k
        b = None if self.hi is None else self.hi * k
        if k < 0:
            a, b = b, a
        return Ext(None if a is None else round_down(a), None if b is None else round_up(b))

    def times_pos(self, iv):
        """self * [p, q] for an interval with 0 < p <= q."""
        iv = Iv.of(iv)
        if iv.lo <= 0:
            raise ExactError("times_pos takes a positive interval")
        lo = None if self.lo is None else round_down(self.lo * (iv.lo if self.lo >= 0 else iv.hi))
        hi = None if self.hi is None else round_up(self.hi * (iv.hi if self.hi >= 0 else iv.lo))
        return Ext(lo, hi)

    def __repr__(self):
        a = "-inf" if self.lo is None else fmt(self.lo, 16, "down")
        b = "+inf" if self.hi is None else fmt(self.hi, 16, "up")
        return "Ext[%s, %s]" % (a, b)


def quotient(a, b):
    """{x/y : x in a, y in b, y != 0} for two intervals, enclosed in one or two Ext pieces: one bounded piece when b
    keeps away from 0; a half-line, or a half-line on each side, when b reaches 0; the whole line when both reach 0."""
    a, b = Iv.of(a), Iv.of(b)
    if b.lo > 0 or b.hi < 0:
        return [Ext.of(a * b.inv())]
    if a.lo <= 0 <= a.hi:
        return [Ext(None, None)]
    out = []
    if a.lo > 0:
        if b.lo < 0:
            out.append(Ext(None, round_up(div(a.lo, b.lo))))
        if b.hi > 0:
            out.append(Ext(round_down(div(a.lo, b.hi)), None))
    else:
        if b.lo < 0:
            out.append(Ext(round_down(div(a.hi, b.lo)), None))
        if b.hi > 0:
            out.append(Ext(None, round_up(div(a.hi, b.hi))))
    if not out:
        raise ExactError("division by the interval [0, 0]")
    return out


def iv_abs(a):
    a = Iv.of(a)
    if a.lo >= 0:
        return a
    if a.hi <= 0:
        return -a
    return Iv(0, max(-a.lo, a.hi))


def isqrt_iv(x, bits=ROUND_BITS):
    """An interval holding sqrt(x) for a rational x >= 0, to about 2^-bits."""
    x = qint.q(x)
    if x < 0:
        raise ExactError("sqrt of a negative")
    p, d = x.n, x.d
    s = qint.isqrt(p * d * ipow(4, bits))
    lo = qint.make(s, d * ipow(2, bits))
    hi = qint.make(s + 1, d * ipow(2, bits))
    if s * s == p * d * ipow(4, bits):
        hi = lo
    return Iv(lo, hi)


def sqrt_iv(a, bits=ROUND_BITS):
    a = Iv.of(a)
    if a.lo < 0:
        raise ExactError("sqrt of an interval below 0")
    return Iv(isqrt_iv(a.lo, bits).lo, isqrt_iv(a.hi, bits).hi)


# ---------------------------------------------------------------------------------------------------------------------
# Exact signs of a + sum_i b_i sqrt(x_i) (rule DECIMAL: comparisons squared and cross-multiplied).


class Rad:
    """a + sum b_i sqrt(x_i), rationals a, b_i and x_i >= 0; exact sign and comparisons."""

    __slots__ = ("a", "terms")
    _exact_operand = True

    def __init__(self, a=0, terms=()):
        self.a = qint.q(a)
        merged = {}
        for b, x in terms:
            b, x = qint.q(b), qint.q(x)
            if x < 0:
                raise ExactError("sqrt of a negative")
            if b == 0 or x == 0:
                continue
            merged[x] = merged.get(x, ZERO) + b
        self.terms = tuple((b, x) for x, b in sorted(merged.items()) if b != 0)

    @staticmethod
    def of(v):
        if isinstance(v, Rad):
            return v
        return Rad(v)

    @staticmethod
    def sqrt(x, coef=1):
        """coef * sqrt(x)."""
        return Rad(0, ((coef, x),))

    def __add__(self, o):
        o = Rad.of(o)
        return Rad(self.a + o.a, self.terms + o.terms)

    __radd__ = __add__

    def __neg__(self):
        return Rad(-self.a, tuple((-b, x) for b, x in self.terms))

    def __sub__(self, o):
        return self + (-Rad.of(o))

    def __rsub__(self, o):
        return Rad.of(o) - self

    def scale(self, c):
        c = qint.q(c)
        return Rad(self.a * c, tuple((b * c, x) for b, x in self.terms))

    def iv(self, bits=ROUND_BITS):
        s = Iv(self.a)
        for b, x in self.terms:
            s = s + isqrt_iv(x, bits) * b
        return s

    def sign(self):
        if not self.terms:
            return _sgn(self.a)
        if len(self.terms) == 1:
            return _sign1(self.a, *self.terms[0])
        if len(self.terms) == 2:
            (b1, x1), (b2, x2) = self.terms
            return _sign2(self.a, b1, x1, b2, x2)
        bits = 256
        while bits <= 16384:
            v = self.iv(bits)
            if v.lo > 0:
                return 1
            if v.hi < 0:
                return -1
            bits *= 2
        raise ExactError("sign of a sum of three or more roots not resolved")

    def abs(self):
        return -self if self.sign() < 0 else self

    def __le__(self, o):
        return (self - o).sign() <= 0

    def __lt__(self, o):
        return (self - o).sign() < 0

    def __ge__(self, o):
        return (self - o).sign() >= 0

    def __gt__(self, o):
        return (self - o).sign() > 0

    def text(self, sig=10):
        v = self.iv()
        if v.lo == v.hi:
            return fmt(v.lo, sig)
        return fmt(v.mid(), sig)


def _sgn(x):
    return qint.sign(x)


def _sign1(a, b, x):
    """sign(a + b sqrt(x)), x >= 0."""
    sa, sb = _sgn(a), _sgn(b) if x > 0 else 0
    if sb == 0:
        return sa
    if sa == 0 or sa == sb:
        return sb
    # opposite signs: compare a^2 with b^2 x
    d = a * a - b * b * x
    return sa * _sgn(d)


def _sign2(a, b1, x1, b2, x2):
    """sign(P + b2 sqrt(x2)), P = a + b1 sqrt(x1)."""
    sp = _sign1(a, b1, x1)
    sq = _sgn(b2) if x2 > 0 else 0
    if sq == 0:
        return sp
    if sp == 0 or sp == sq:
        return sq
    # |P| vs |b2| sqrt(x2): P^2 - b2^2 x2 = (a^2 + b1^2 x1 - b2^2 x2) + 2 a b1 sqrt(x1)
    d = _sign1(a * a + b1 * b1 * x1 - b2 * b2 * x2, 2 * a * b1, x1)
    return sp * d
