"""Checked integer pairs: the only rationals of stage B (the owner's ruling of 2026-11-09).

A value is a Q, the reduced pair (n, d) of two ints: d > 0 and gcd(n, d) = 1. Every function here builds its result
through _pair, which checks that both parts are of type int (type(x) is int, so a bool is refused) and that the
denominator is positive. An operand must be a Q or an int; anything else raises TypeError, so a stray float or a
fractions.Fraction cannot enter or leave. Comparison is by cross-multiplication.

Q's operators (+, -, *, unary -, abs, ==, <, <=, >, >=) are these same functions. Q has no true division, floor
division, modulo, divmod, float or int: /, //, %, divmod(), float() and int() on a Q, from either side, raise
QintError; power and round raise TypeError. Division is div(a, b). No float, no fractions, no math: gcd and isqrt are
written here in integers."""


class QintError(TypeError):
    """An operand or a result that is not a checked integer pair."""


def _int(x, what):
    if type(x) is not int:
        raise QintError("%s is %s, not int" % (what, type(x).__name__))
    return x


def gcd(a, b):
    """gcd(|a|, |b|) of two ints, by Euclid; gcd(0, 0) = 0."""
    a = _int(a, "gcd operand")
    b = _int(b, "gcd operand")
    if a < 0:
        a = -a
    if b < 0:
        b = -b
    if a == 1 or b == 1:
        return 1
    if a == 0:
        return b
    if b == 0:
        return a
    # a power of two: the gcd is the shared power of two (exact, and fast for the dyadic values of stage B)
    if b & (b - 1) == 0:
        return min(b, a & -a)
    if a & (a - 1) == 0:
        return min(a, b & -b)
    while b:
        a, b = b, a % b
    return a


def isqrt(n):
    """floor(sqrt(n)) of an int n >= 0, by Newton's method on integers; checked: r*r <= n < (r+1)*(r+1)."""
    n = _int(n, "isqrt operand")
    if n < 0:
        raise ValueError("isqrt of a negative int")
    if n < 2:
        return n
    x = 1 << ((n.bit_length() + 1) >> 1)
    while True:
        y = (x + n // x) >> 1
        if y >= x:
            break
        x = y
    if not (x * x <= n < (x + 1) * (x + 1)):
        raise ArithmeticError("isqrt check failed")
    return x


class Q:
    """The reduced integer pair (n, d), d > 0. Built only by _pair; immutable."""

    __slots__ = ("n", "d")

    def __init__(self, *args):
        raise QintError("build a Q with make(n, d) or q(x)")

    def __setattr__(self, name, value):
        raise AttributeError("Q is immutable")

    def __add__(self, o):
        o = _operand(o)
        return NotImplemented if o is NotImplemented else add(self, o)

    def __radd__(self, o):
        o = _operand(o)
        return NotImplemented if o is NotImplemented else add(o, self)

    def __sub__(self, o):
        o = _operand(o)
        return NotImplemented if o is NotImplemented else sub(self, o)

    def __rsub__(self, o):
        o = _operand(o)
        return NotImplemented if o is NotImplemented else sub(o, self)

    def __mul__(self, o):
        o = _operand(o)
        return NotImplemented if o is NotImplemented else mul(self, o)

    def __rmul__(self, o):
        o = _operand(o)
        return NotImplemented if o is NotImplemented else mul(o, self)

    def __neg__(self):
        return neg(self)

    def __pos__(self):
        return self

    def __abs__(self):
        return absq(self)

    def __eq__(self, o):
        return cmp(self, _comparand(o)) == 0

    def __ne__(self, o):
        return cmp(self, _comparand(o)) != 0

    def __lt__(self, o):
        o = _operand(o)
        return NotImplemented if o is NotImplemented else cmp(self, o) < 0

    def __le__(self, o):
        o = _operand(o)
        return NotImplemented if o is NotImplemented else cmp(self, o) <= 0

    def __gt__(self, o):
        o = _operand(o)
        return NotImplemented if o is NotImplemented else cmp(self, o) > 0

    def __ge__(self, o):
        o = _operand(o)
        return NotImplemented if o is NotImplemented else cmp(self, o) >= 0

    def __truediv__(self, o):
        raise QintError("Q / %s: use div(a, b)" % type(o).__name__)

    def __rtruediv__(self, o):
        raise QintError("%s / Q: use div(a, b)" % type(o).__name__)

    def __floordiv__(self, o):
        raise QintError("Q // %s: use floor(div(a, b))" % type(o).__name__)

    def __rfloordiv__(self, o):
        raise QintError("%s // Q: use floor(div(a, b))" % type(o).__name__)

    def __mod__(self, o):
        raise QintError("Q mod %s refused" % type(o).__name__)

    def __rmod__(self, o):
        raise QintError("%s mod Q refused" % type(o).__name__)

    def __divmod__(self, o):
        raise QintError("divmod(Q, %s) refused" % type(o).__name__)

    def __rdivmod__(self, o):
        raise QintError("divmod(%s, Q) refused" % type(o).__name__)

    def __float__(self):
        raise QintError("float(Q) refused")

    def __int__(self):
        raise QintError("int(Q) refused: use floor, ceil or num")

    def __hash__(self):
        # equal values hash equal: Q(n, 1) == n
        return hash(self.n) if self.d == 1 else hash((self.n, self.d))

    def __bool__(self):
        return self.n != 0

    def __str__(self):
        return text(self)

    def __repr__(self):
        return "Q(%d, %d)" % (self.n, self.d)


def _operand(o):
    """An int or a Q as a Q. NotImplemented for the package's own exact classes (Iv, Ext, Rad set _exact_operand and
    answer for themselves). TypeError for anything else: a float, a complex, a bool, a Fraction, a Decimal, a str."""
    t = type(o)
    if t is Q:
        return o
    if t is int:
        return _pair(o, 1)
    if getattr(t, "_exact_operand", False) is True:
        return NotImplemented
    raise QintError("operand of type %s refused" % t.__name__)


def _comparand(o):
    t = type(o)
    if t is Q:
        return o
    if t is int:
        return _pair(o, 1)
    raise QintError("== between a Q and a %s refused" % t.__name__)


def _pair(n, d):
    """The checked result of every operation: both parts int, d > 0. It does not reduce: every caller passes a pair that is
    reduced by construction (review N13), so gcd(n, d) = 1 holds for every Q there is:
    - _reduced divides by g = gcd(n, d) after the sign is moved to n, so gcd(n/g, d/g) = 1 and d/g > 0;
    - (o, 1) for an int o (_operand, _comparand, q) and the constants (0, 1), (1, 1), (1, 2): gcd(n, 1) = 1, gcd(1, 2) = 1;
    - neg and absq give (-n, d) or (n, d) of a Q: gcd(-n, d) = gcd(n, d) = 1;
    - ipow gives (n^k, d^k) of a Q: a prime p dividing both would divide n and d, so gcd(n^k, d^k) = 1 (and (1, 1) at k = 0).
    No other code builds a Q: Q's own constructor is refused, and add, sub, mul and div go through _reduced."""
    _int(n, "numerator")
    _int(d, "denominator")
    if d <= 0:
        raise QintError("denominator %d not positive" % d)
    x = object.__new__(Q)
    object.__setattr__(x, "n", n)
    object.__setattr__(x, "d", d)
    return x


def _reduced(n, d):
    """n/d reduced by gcd, with a positive denominator; d != 0."""
    _int(n, "numerator")
    _int(d, "denominator")
    if d == 0:
        raise ZeroDivisionError("exact division by zero")
    if d < 0:
        n, d = -n, -d
    if d != 1:
        g = gcd(n, d)
        if g != 1:
            n, d = n // g, d // g
    return _pair(n, d)


def make(n, d=1):
    """The pair n/d of two ints, reduced; d != 0."""
    return _reduced(_int(n, "make numerator"), _int(d, "make denominator"))


def q(x):
    """An int or a Q as a Q; any other type raises TypeError."""
    t = type(x)
    if t is Q:
        return x
    if t is int:
        return _pair(x, 1)
    raise QintError("value of type %s is not an int or a Q" % t.__name__)


ZERO = _pair(0, 1)
ONE = _pair(1, 1)
HALF = _pair(1, 2)


def add(a, b):
    a, b = q(a), q(b)
    if a.d == b.d:
        return _reduced(a.n + b.n, a.d)
    return _reduced(a.n * b.d + b.n * a.d, a.d * b.d)


def sub(a, b):
    a, b = q(a), q(b)
    if a.d == b.d:
        return _reduced(a.n - b.n, a.d)
    return _reduced(a.n * b.d - b.n * a.d, a.d * b.d)


def mul(a, b):
    a, b = q(a), q(b)
    return _reduced(a.n * b.n, a.d * b.d)


def div(a, b):
    """a/b exactly; b must be nonzero (ZeroDivisionError)."""
    a, b = q(a), q(b)
    if b.n == 0:
        raise ZeroDivisionError("exact division by zero")
    return _reduced(a.n * b.d, a.d * b.n)


def neg(a):
    a = q(a)
    return _pair(-a.n, a.d)


def absq(a):
    a = q(a)
    return a if a.n >= 0 else _pair(-a.n, a.d)


def cmp(a, b):
    """-1, 0 or 1 as a < b, a = b, a > b, by cross-multiplication (both denominators are positive)."""
    a, b = q(a), q(b)
    x = a.n * b.d
    y = b.n * a.d
    return (x > y) - (x < y)


def sign(a):
    a = q(a)
    return (a.n > 0) - (a.n < 0)


def floor(a):
    """The largest int <= a."""
    a = q(a)
    return _int(a.n // a.d, "floor")


def ceil(a):
    """The smallest int >= a."""
    a = q(a)
    return _int(-((-a.n) // a.d), "ceil")


def is_int(a):
    return q(a).d == 1


def num(a):
    return q(a).n


def den(a):
    return q(a).d


def ipow(x, k):
    """x**k for an int k >= 0, by squaring: an int for an int x, a Q for a Q."""
    k = _int(k, "exponent")
    if k < 0:
        raise ValueError("ipow takes an exponent >= 0")
    if type(x) is int:
        r, base = 1, x
        while k:
            if k & 1:
                r = r * base
            base = base * base
            k >>= 1
        return _int(r, "ipow")
    x = q(x)
    # gcd(n, d) = 1 gives gcd(n^k, d^k) = 1
    return _pair(ipow(x.n, k), ipow(x.d, k))


def text(a):
    """'n' or 'n/d', the text of fractions.Fraction's str."""
    a = q(a)
    return str(a.n) if a.d == 1 else "%d/%d" % (a.n, a.d)
