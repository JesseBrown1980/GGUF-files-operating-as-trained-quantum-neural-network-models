# cf.py -- closed forms for the ensemble lane, exact rationals only (float_used=0).
# Reads the frozen row POLARITON_FIRST_CORRECTION (line 48 of polariton/PREDICTION.hbp) as DATA and walks its
# arithmetic with a whitelist walker of this file's own (no code from the repo is imported or executed).
# Adds the ensemble's first-order residuals DERIVED in FINDINGS.txt:
#   V1  (ring |c0|^2 = N + 1/2, independent vacuum noise on +-, 3-mode Weyl symbols):  dw1 = 0,  dC1v = 2[2 d sinh^2(g t) + g t sinh(2 g t)]/(1+d)^2
#   V3  (sharp total number N + 3/2, 3-mode Weyl X):                                    dw1 = 0,  dC1v = -1
#   VNC (sharp total number N + 3/2, number-conserving X form):                         dw1 = 0,  dC1v = 0
#   ring at N + 1/2 + kappa, radial variance v (independent):  + kappa * d/de [law(e)] + (v/(2N)) d2/de2 [law(e)]
#   V0  (coherent stand-in, random phase): v = N + 1/4, kappa = 0
# where law(e) is the leading order with JN -> (1+e): pair 1+e, delta -> delta+e (u = 1), s -> s sqrt(1+e), A ~ sqrt(N_tot), X ~ N_tot.
import ast
from fractions import Fraction as Fr

TERMS = 160
FACT = [1]
for _i in range(1, 2 * TERMS + 4):
    FACT.append(FACT[-1] * _i)


def read_row48(path):
    with open(path, 'rb') as fh:
        lines = fh.read().decode('utf-8').replace('\r', '').split('\n')
    row = lines[47]
    assert row.startswith('POLARITON_FIRST_CORRECTION|'), 'line 48 is the frozen row'
    text = {}
    for part in row.split('|')[1:]:
        if '=' in part:
            k, v = part.split('=', 1)
            text[k] = v
    return row, text


def walk(node, env):
    if isinstance(node, ast.BinOp):
        a = walk(node.left, env)
        b = walk(node.right, env)
        if isinstance(node.op, ast.Add):
            return a + b
        if isinstance(node.op, ast.Sub):
            return a - b
        if isinstance(node.op, ast.Mult):
            return a * b
        if isinstance(node.op, ast.Div):
            return a / b
        if isinstance(node.op, ast.Pow):
            assert b.denominator == 1
            return a ** int(b)
        raise ValueError('op')
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -walk(node.operand, env)
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return Fr(node.value)
    if isinstance(node, ast.Name):
        return env[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'abs' and len(node.args) == 1:
        return abs(walk(node.args[0], env))
    raise ValueError('form node %r' % (node,))


def ev(text, env):
    src = text.replace('sinh1^2', 'SINH_SQ').replace('s^2', 's2').replace('s^4', 's4').replace('^', '**')
    return walk(ast.parse(src, mode='eval').body, env)


def cosh_k(k, g2):
    """cosh(k gamma t) with g2 = (gamma t)^2 rational; positive terms, TERMS long."""
    x = Fr(k * k) * g2
    tot, p = Fr(0), Fr(1)
    for m in range(TERMS):
        tot += p / FACT[2 * m]
        p *= x
    return tot


def gsinh_k(k, g2):
    """gamma t sinh(k gamma t) as a series in g2."""
    x = Fr(k * k) * g2
    tot, p = Fr(0), g2 * k
    for m in range(TERMS):
        tot += p / FACT[2 * m + 1]
        p *= x
    return tot


def sinh_over_g(gamma2, t):
    """sinh(gamma t)/gamma = t * sum (gamma^2 t^2)^m/(2m+1)!, with gamma2 = gamma^2 rational."""
    t = Fr(t)
    x = Fr(gamma2) * t * t
    tot, p = Fr(0), Fr(1)
    for m in range(TERMS):
        tot += p / FACT[2 * m + 1]
        p *= x
    return t * tot


class Row48:
    def __init__(self, path):
        self.row, self.text = read_row48(path)

    def values(self, N, delta, y, t):
        d = Fr(delta)
        t = Fr(t)
        g2 = (1 - d * d) * t * t
        env = {'N': Fr(N), 'd': d, 'y': Fr(y), 's2': Fr(N) * Fr(y) * Fr(y)}
        env['s4'] = env['s2'] * env['s2']
        for k in (1, 2, 3, 4):
            env['c_%d' % k] = cosh_k(k, g2)
            env['gs_%d' % k] = gsinh_k(k, g2)
        env['SINH_SQ'] = (env['c_2'] - 1) / 2
        for nm, p in (('D3', 3), ('D4', 4), ('D5', 5)):
            env[nm] = (1 + d) ** p * (1 - d) ** 2
        for nm in ('w0', 'C0', 'w10', 'w11', 'C10', 'C11', 'C12'):
            env[nm] = ev(self.text[nm], env)
        out = {}
        for nm in ('A1_first', 'C1_first', 'A1_law', 'C1_law'):
            out[nm] = ev(self.text[nm], env)
        out['V2_first'] = out['A1_first'] ** 2 / (2 * out['C1_first']) if out['C1_first'] != 0 else None
        out['V2_law'] = out['A1_law'] ** 2 / (2 * out['C1_law']) if out['C1_law'] != 0 else None
        for nm in ('w0', 'C0', 'w10', 'w11', 'C10', 'C11', 'C12', 'c_1', 'c_2', 'gs_1', 'gs_2', 'SINH_SQ', 's2'):
            out[nm] = env[nm]
        j0 = env['SINH_SQ'] / (1 - d * d) if d * d != 1 else t * t
        nc = env['s2'] * ((env['c_1'] - 1) ** 2 / (1 + d) ** 2 + j0)
        out['f_pred'] = 2 * (j0 + nc) / Fr(N)
        out['C1v'] = env['C10'] + env['s2'] * env['C11'] + env['s4'] * env['C12']
        out['w1'] = env['w10'] + env['s2'] * env['w11']
        # the law's Y and V2
        out['Y'] = (2 * env['s2'] / (1 + d)) * ((env['c_1'] - 1) ** 2 / (env['SINH_SQ'])) if env['SINH_SQ'] != 0 else Fr(0)
        return out


def dC1v_V1(delta, t):
    """DERIVED: the V1 ensemble's shift of C1's 1/N^2 coefficient, s-independent."""
    d = Fr(delta)
    t = Fr(t)
    g2 = (1 - d * d) * t * t
    sh2 = (cosh_k(2, g2) - 1) / 2
    return 2 * (2 * d * sh2 + gsinh_k(2, g2)) / (1 + d) ** 2


# ---- truncated power series in e (degree 2), rational coefficients
class PS:
    __slots__ = ('c',)

    def __init__(self, c0, c1=0, c2=0):
        self.c = [Fr(c0), Fr(c1), Fr(c2)]

    def __add__(self, o):
        o = o if isinstance(o, PS) else PS(o)
        return PS(*[a + b for a, b in zip(self.c, o.c)])

    __radd__ = __add__

    def __sub__(self, o):
        o = o if isinstance(o, PS) else PS(o)
        return PS(*[a - b for a, b in zip(self.c, o.c)])

    def __mul__(self, o):
        o = o if isinstance(o, PS) else PS(o)
        a, b = self.c, o.c
        return PS(a[0] * b[0], a[0] * b[1] + a[1] * b[0], a[0] * b[2] + a[1] * b[1] + a[2] * b[0])

    __rmul__ = __mul__

    def inv(self):
        a0, a1, a2 = self.c
        i0 = 1 / a0
        return PS(i0, -a1 * i0 * i0, (a1 * a1 * i0 - a2) * i0 * i0)

    def __truediv__(self, o):
        o = o if isinstance(o, PS) else PS(o)
        return self * o.inv()


def cosh_ps(k, g2ps):
    x = g2ps * (k * k)
    tot = PS(0)
    p = PS(1)
    for m in range(TERMS):
        tot = tot + p * Fr(1, FACT[2 * m])
        p = p * x
    return tot


def law_eps(delta, s2, t):
    """leading order as a series in e: w(e) = <A>/(N y), X(e) = <X>/N (u = 1)."""
    d = Fr(delta)
    t = Fr(t)
    D = PS(1 + d, 2)
    g2ps = PS((1 - d) * (1 + d) * t * t, 2 * (1 - d) * t * t)
    ch = cosh_ps(1, g2ps)
    sh2 = (cosh_ps(2, g2ps) - 1) * Fr(1, 2)
    one_e = PS(1, 1)
    w = Fr(-2) * one_e * (ch - 1) / D
    X = one_e * one_e * (Fr(4) * Fr(s2) * (ch - 1) * (ch - 1) / (D * D) + Fr(2) * sh2 / D)
    return w, X


def ensemble_first(variant, delta, s2, t):
    """(dw1, dC1v): the variant's first-order shifts against the quantum first correction."""
    if variant == 'VNC':
        return Fr(0), Fr(0)
    if variant == 'V3':
        return Fr(0), Fr(-1)
    v1 = dC1v_V1(delta, t)
    if variant in ('V1', 'V2'):
        return Fr(0), v1
    w, X = law_eps(delta, s2, t)
    if variant == 'V0':          # v_r/N -> 1, kappa = 0: (1/2) d2/de2 = coefficient c[2]
        return w.c[2], v1 + 2 * X.c[2]
    if variant == 'RING_N':      # kappa = -1/2
        return -w.c[1] / 2, v1 - X.c[1]
    raise ValueError(variant)


def dec(x, n=6):
    if x is None:
        return 'None'
    x = Fr(x)
    sgn = '-' if x < 0 else ''
    x = abs(x)
    q = (x * 10 ** n + Fr(1, 2)).__floor__()
    ip, fp = divmod(q, 10 ** n)
    return '%s%d.%0*d' % (sgn, ip, n, fp)


def sci(x, n=4):
    """decimal scientific print of a rational, integer arithmetic only."""
    if x is None:
        return 'None'
    x = Fr(x)
    if x == 0:
        return '0'
    sgn = '-' if x < 0 else ''
    x = abs(x)
    e = 0
    while x >= 10:
        x /= 10
        e += 1
    while x < 1:
        x *= 10
        e -= 1
    q = (x * 10 ** (n - 1) + Fr(1, 2)).__floor__()
    if q >= 10 ** n:
        q //= 10
        e += 1
    s = str(q)
    return '%s%s.%se%d' % (sgn, s[0], s[1:], e)
