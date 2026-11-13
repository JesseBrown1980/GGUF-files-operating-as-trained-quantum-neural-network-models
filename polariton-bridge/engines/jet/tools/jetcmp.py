# jetcmp.py -- exact Gaussian averages of the jet (jetens jet output) against the filed Monte Carlo sums.
# Lane ensemble-skip-20261106 (opus55, a lane of the second seat for ACER-CLAUDE-FABLE5). Integers and exact rationals
# only (float_used=0); square roots by integer isqrt at a stated relative precision (10^-30).
#
# Jet: polynomials in (a, conj a, b, conj b, e) at 2^-q, weights 1,1,1,1,2. Averages:
#   gauss  : a = h(g0 + i g1), b = h(g2 + i g3), g iid N(0,1), h^2 = 1/(4N): E[a^i conj(a)^j] = delta_ij i! (1/(2N))^i.
#   engine : g = (Binomial(4096,1/2) - 2048)/32 exactly (its moments summed exactly), h = isqrt(2^80 // (4N)) / 2^40.
#   e      : V1 e = 1/(2N); VNC (and V3) e = 3/(2N) - |a|^2 - |b|^2; RN e = 0.  c = 3/(2N) and 1/(2N) carry weight 2.
# Order p: every term of total weight <= p, each explicit 1/N weight 2:
#   X_W/N^2  = Z2 - (n0 + ns/2)/N + 1/(2N^2);  X_NC/N^2 = ns - 1/N - ns2 + 2 ns/N - 1/(2N^2) + 2 Re Pr;  f = ns - 1/N.
#   C1 = 2N/(N-1) E[X/N^2];  A1 = 2|E Z|;  V2 = A1^2/(2 C1);  D2 = 2|E B|.
# Monte Carlo (the filed sums): TWB rows of bridge-engine-ensemble-20261106/out/full (the design lane's runs reproduced
#   byte for byte with the extra sums), cross-checked field by field against the design lane's TWENS rows.
#   Control-variate means as the ensemble lane's reader forms them (twread.py): mean(O - O_lin) + E[O_lin] for X and Z;
#   plain means for f and B. SE = sqrt(var/n); V2, A1, D2 by the delta method.
import sys
from fractions import Fraction as Fr
from math import comb, factorial, isqrt, lcm

SC = Fr(1, 1 << 40)
SC2 = Fr(1, 1 << 80)


# ------------------------------------------------------------------------------------------------ number formatting
def sqrt_fr(x, digits=30):
    """sqrt of a Fraction x >= 0, relative precision about 10^-digits (integer isqrt)."""
    x = Fr(x)
    if x <= 0:
        return Fr(0)
    # scale so that the integer square root has about `digits` decimal digits beyond the leading ones
    num, den = x.numerator, x.denominator
    k = 0
    while num * 10 ** (2 * k) < den * 10 ** (2 * digits):
        k += 1
    s = isqrt(num * 10 ** (2 * k) // den)
    return Fr(s, 10 ** k)


def sci(x, sig=6):
    x = Fr(x)
    if x == 0:
        return '0'
    neg = x < 0
    x = abs(x)
    e = 0
    num, den = x.numerator, x.denominator
    # find e with 10^e <= x < 10^(e+1)
    e = len(str(num)) - len(str(den))
    if Fr(10) ** e > x:
        e -= 1
    if Fr(10) ** (e + 1) <= x:
        e += 1
    m = x / Fr(10) ** (e - sig + 1)
    mi = (m.numerator * 2 + m.denominator) // (2 * m.denominator)
    if mi >= 10 ** sig:
        mi //= 10
        e += 1
    s = str(mi)
    out = s[0] + ('.' + s[1:] if len(s) > 1 else '') + 'e' + ('%+d' % e)
    return ('-' if neg else '') + out


def dec(x, nd=3):
    x = Fr(x)
    neg = x < 0
    v = abs(x) * 10 ** nd
    vi = (v.numerator * 2 + v.denominator) // (2 * v.denominator)
    s = str(vi).rjust(nd + 1, '0')
    out = s[:-nd] + '.' + s[-nd:] if nd > 0 else s
    return ('-' if neg and vi != 0 else '') + out


def fields(line):
    out = {}
    for part in line.rstrip('\n').split('|')[1:]:
        if '=' in part:
            k, v = part.split('=', 1)
            out[k] = v
    return out


# ------------------------------------------------------------------------------------------------ the jet file
def read_jet(path):
    head = None
    mons = None
    polys = {}
    timing = None
    with open(path, 'rb') as fh:
        for raw in fh:
            ln = raw.decode('ascii').rstrip('\n')
            if ln.startswith('JET_HEAD|'):
                head = fields(ln)
            elif ln.startswith('JET_BASIS|'):
                mons = [tuple(int(v) for v in s.split('.')) for s in fields(ln)['mons'].split(';')]
            elif ln.startswith('JET_POLY|'):
                f = fields(ln)
                polys[(int(f['step']), f['obs'])] = ([int(v) for v in f['re'].split(',')], [int(v) for v in f['im'].split(',')])
            elif ln.startswith('JET_TIME|'):
                timing = fields(ln)
    return head, mons, polys, timing


# ------------------------------------------------------------------------------------------------ the laws
_BIN = {}


def binom_moment(k):
    """E[g^k] for g = (B - 2048)/32, B ~ Binomial(4096, 1/2), exactly."""
    if k in _BIN:
        return _BIN[k]
    if k % 2 == 1:
        _BIN[k] = Fr(0)
        return _BIN[k]
    n = 4096
    s = 0
    for c in range(n + 1):
        s += comb(n, c) * (c - 2048) ** k
    v = Fr(s, (1 << n) * 32 ** k)
    _BIN[k] = v
    return v


_MCX = {}


def engine_M(i, j):
    """E[(g0 + i g1)^i (g0 - i g1)^j] for iid engine Gaussians: real (the law is symmetric under g1 -> -g1)."""
    key = (i, j)
    if key in _MCX:
        return _MCX[key]
    tot = Fr(0)
    for r in range(i + 1):
        for s in range(j + 1):
            k = (i - r) - (j - s)
            if k % 2:
                continue
            sign = 1 if k % 4 == 0 else -1
            tot += sign * comb(i, r) * comb(j, s) * binom_moment(r + s) * binom_moment((i - r) + (j - s))
    _MCX[key] = tot
    return tot


def A_table(N, law, dmax):
    """A[(i, j)] = E[a^i conj(a)^j] for i + j <= dmax."""
    A = {}
    if law == 'gauss':
        s2 = Fr(1, 2 * N)
        for i in range(dmax + 1):
            for j in range(dmax + 1 - i):
                A[(i, j)] = Fr(factorial(i)) * s2 ** i if i == j else Fr(0)
    else:
        H = Fr(isqrt((1 << 80) // (4 * N)), 1 << 40)
        for i in range(dmax + 1):
            for j in range(dmax + 1 - i):
                A[(i, j)] = H ** (i + j) * engine_M(i, j)
    return A


def E_table(mons, N, variant, law):
    """E of every monomial (i, j, k, l, m) of the jet basis under the variant's substitution for e."""
    pmax = max(i + j + k + l + 2 * mm for (i, j, k, l, mm) in mons)
    A = A_table(N, law, pmax)
    out = []
    for (i, j, k, l, mm) in mons:
        if variant == 'V1':
            v = Fr(1, 2 * N) ** mm * A[(i, j)] * A[(k, l)]
        elif variant == 'RN':
            v = A[(i, j)] * A[(k, l)] if mm == 0 else Fr(0)
        elif variant in ('VNC', 'V3'):
            c = Fr(3, 2 * N)
            v = Fr(0)
            for r in range(mm + 1):
                cr = comb(mm, r) * c ** (mm - r) * (-1) ** r
                for s in range(r + 1):
                    v += cr * comb(r, s) * A[(i + s, j + s)] * A[(k + r - s, l + r - s)]
        else:
            raise SystemExit('unknown variant ' + variant)
        out.append(v)
    return out


_EC = {}


def e_common(mons, N, variant, law):
    """E_table over one common denominator, cached per (basis size, N, variant, law)."""
    key = (len(mons), N, variant, law)
    if key not in _EC:
        E = E_table(mons, N, variant, law)
        D = 1
        for v in E:
            D = lcm(D, v.denominator)
        _EC[key] = (D, [v.numerator * (D // v.denominator) for v in E])
    return _EC[key]


def weight_sums(mons, coeffs, EC, q, pmax):
    """per-weight sums of coeffs * E as Fractions (coeffs integers at 2^-q); EC = (D, numerators)."""
    D, nums = EC
    acc = [0] * (pmax + 1)
    for idx, (i, j, k, l, mm) in enumerate(mons):
        c = coeffs[idx]
        if c == 0 or nums[idx] == 0:
            continue
        acc[i + j + k + l + 2 * mm] += c * nums[idx]
    return [Fr(a, D << q) for a in acc]


def cum(ws, p):
    return sum(ws[: p + 1], Fr(0)) if p >= 0 else Fr(0)


def jet_means(mons, polys, step, N, variant, law, q, pmax):
    """observables at every order p = 0..pmax: dict p -> {ZR, ZI, BR, BI, X, f, C1, A1sq, V2, D2sq}."""
    E = e_common(mons, N, variant, law)
    ws = {}
    for obs in ('Z', 'B', 'n0', 'ns', 'Pr', 'Z2', 'ns2'):
        re, im = polys[(step, obs)]
        ws[obs] = (weight_sums(mons, re, E, q, pmax), weight_sums(mons, im, E, q, pmax))
    invN = Fr(1, N)
    res = {}
    for p in range(pmax + 1):
        g = lambda o, part=0, pp=p: cum(ws[o][part], pp)
        ZR, ZI = g('Z'), g('Z', 1)
        BR, BI = g('B'), g('B', 1)
        if variant in ('V1', 'V3', 'RN'):
            X = g('Z2') - (g('n0', 0, p - 2) + g('ns', 0, p - 2) / 2) * invN + (invN * invN / 2 if p >= 4 else 0)
        else:
            X = (g('ns') - (invN if p >= 2 else 0) - g('ns2') + 2 * g('ns', 0, p - 2) * invN
                 - (invN * invN / 2 if p >= 4 else 0) + 2 * g('Pr'))
        f = g('ns') - (invN if p >= 2 else 0)
        C1 = Fr(2 * N, N - 1) * X
        A1sq = 4 * (ZR * ZR + ZI * ZI)
        res[p] = {'ZR': ZR, 'ZI': ZI, 'BR': BR, 'BI': BI, 'X': X, 'f': f, 'C1': C1, 'A1sq': A1sq,
                  'V2': (A1sq / (2 * C1)) if C1 != 0 else None, 'D2sq': 4 * (BR * BR + BI * BI)}
    return res


# ------------------------------------------------------------------------------------------------ the Monte Carlo
def read_mc(full_path, raw_path):
    """TWB rows of the .full file, checked against the TWENS rows of the design lane's raw file."""
    with open(full_path, 'rb') as fh:
        flines = fh.read().decode('ascii').split('\n')
    with open(raw_path, 'rb') as fh:
        rlines = fh.read().decode('ascii').split('\n')
    head = fields(flines[0])
    twb = {}
    for ln in flines:
        if ln.startswith('TWB|'):
            f = fields(ln)
            twb[(int(f['step']), f['variant'])] = f
    checked = 0
    mism = 0
    for ln in rlines:
        if ln.startswith('TWENS|'):
            f = fields(ln)
            v = {'VN': 'VNC'}.get(f['variant'], f['variant'])
            g = twb.get((int(f['step']), v))
            if g is None:
                continue
            for k in ('n', 'h', 'ctrl', 'zr', 'zi', 'dzr', 'dzi', 'xw', 'dxw', 'xnc', 'dxnc', 'f', 'qdzr', 'qdxw', 'qdxnc',
                      'qzr', 'qxw', 'qxnc', 'qdzi'):
                checked += 1
                if f[k] != g[k]:
                    mism += 1
    return head, twb, checked, mism


def mc_obs(f, N, variant):
    n = int(f['n'])
    mean = lambda k: Fr(int(f[k])) * SC / n
    varq = lambda k, mk: Fr(int(f[k])) * SC / n - mk * mk
    var2 = lambda k, mk: Fr(int(f[k])) * SC2 / n - mk * mk
    H = Fr(int(f['h'])) * SC
    C, RS, MZ = [Fr(int(v)) * SC for v in f['ctrl'].split(':')]
    inv_n = Fr((1 << 40) // N) * SC
    exc = MZ * MZ + 4 * H * H * (C * C + RS * RS) - inv_n
    dx = 'dxnc' if variant == 'VNC' else 'dxw'
    qdx = 'qdxnc' if variant == 'VNC' else 'qdxw'
    cov_key = 'dzrdxnc' if variant == 'VNC' else 'dzrdxw'
    m_dx = mean(dx)
    v_dx = varq(qdx, m_dx)
    X = m_dx + exc
    m_dzr = mean('dzr')
    v_dzr = varq('qdzr', m_dzr)
    m_dzi = mean('dzi')
    v_dzi = varq('qdzi', m_dzi)
    ZR = m_dzr + MZ
    ZI = m_dzi
    cov_zx = Fr(int(f[cov_key])) * SC2 / n - m_dzr * m_dx
    m_f = mean('f')
    v_f = var2('f2', m_f)
    BR, BI = mean('br'), mean('bi')
    v_br, v_bi = var2('br2', BR), var2('bi2', BI)
    cov_b = Fr(int(f['brbi'])) * SC2 / n - BR * BI
    k = Fr(2 * N, N - 1)
    o = {'n': n}
    o['C1'] = (k * X, k * sqrt_fr(v_dx / n))
    o['f'] = (m_f, sqrt_fr(v_f / n))
    o['ZR'] = (ZR, sqrt_fr(v_dzr / n))
    o['ZI'] = (ZI, sqrt_fr(v_dzi / n))
    o['BR'] = (BR, sqrt_fr(v_br / n))
    o['BI'] = (BI, sqrt_fr(v_bi / n))
    Z2 = ZR * ZR + ZI * ZI
    if Z2 > 0:
        A1 = 2 * sqrt_fr(Z2)
        vA = 4 * (ZR * ZR * v_dzr + ZI * ZI * v_dzi) / Z2 / n
        o['A1'] = (A1, sqrt_fr(vA))
        C1 = k * X
        V2 = 2 * Z2 / C1
        # relative variance of V2 = Z2/X up to constants: 4 var(ZR)/ZR^2 + var(X)/X^2 - 4 cov/(ZR X) (ZI negligible)
        rel = (4 * v_dzr / (ZR * ZR) + v_dx / (X * X) - 4 * cov_zx / (ZR * X)) / n if ZR != 0 else Fr(0)
        o['V2'] = (V2, V2 * sqrt_fr(rel) if rel > 0 else Fr(0))
    B2 = BR * BR + BI * BI
    if B2 > 0:
        D2 = 2 * sqrt_fr(B2)
        vD = 4 * (BR * BR * v_br + BI * BI * v_bi + 2 * BR * BI * cov_b) / B2 / n
        o['D2'] = (D2, sqrt_fr(vD) if vD > 0 else Fr(0))
    return o


def jet_obs(r):
    """the compared observables from one order's jet means."""
    o = {'C1': r['C1'], 'f': r['f'], 'ZR': r['ZR'], 'ZI': r['ZI'], 'BR': r['BR'], 'BI': r['BI']}
    if r['A1sq'] > 0:
        o['A1'] = sqrt_fr(r['A1sq'])
        if r['V2'] is not None:
            o['V2'] = r['V2']
    if r['D2sq'] > 0:
        o['D2'] = sqrt_fr(r['D2sq'])
    return o
