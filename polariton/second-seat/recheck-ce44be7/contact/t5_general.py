#!/usr/bin/env python3
# t5_general.py -- reconstructs the first-correction coefficients as exact rational functions of delta at u = 1 (or given u).
# Each result is Sum t^ti s^sp [ A_k(delta) cosh(k gamma t) + B_k(delta) gamma sinh(k gamma t) ], with A_k, B_k rational in delta.
# Reconstruction: exact rational interpolation through many rational delta, then a check at held-out delta.
import sys, time, json
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import t5_firstcorr as F

def coeff_table(res_f):
    """time function -> {(sp, ti, k>=0): (A, B)}; asserts the symmetry a_-k = a_k, b_-k = -b_k and no imaginary part."""
    out = {}
    for (sp, ti, tj, k, k2), w in res_f.items():
        assert tj == 0 and k2 == 0
        assert w.c == 0 and w.d == 0, 'imaginary part'
        key = (sp, ti, abs(k))
        a, b = out.get(key, (Fr(0), Fr(0)))
        # coefficient (w.a + w.b gamma) e^(k gamma t):  e^(+k) + e^(-k) -> cosh parts
        if k == 0:
            out[key] = (a + w.a, b + w.b)
        else:
            # a e^{kgt} + a e^{-kgt} = 2 a cosh ; b g e^{kgt} - b g e^{-kgt} = 2 b g sinh. Each sign contributes half.
            sign = 1 if k > 0 else -1
            out[key] = (a + w.a, b + sign*w.b)
    return out

# polynomials over Q: lists low -> high
def padd(a, b):
    n = max(len(a), len(b))
    return ptrim([(a[i] if i < len(a) else 0) + (b[i] if i < len(b) else 0) for i in range(n)])
def psub(a, b):
    n = max(len(a), len(b))
    return ptrim([(a[i] if i < len(a) else 0) - (b[i] if i < len(b) else 0) for i in range(n)])
def pmul(a, b):
    if not a or not b: return []
    out = [Fr(0)]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i+j] += x*y
    return ptrim(out)
def ptrim(a):
    a = list(a)
    while a and a[-1] == 0:
        a.pop()
    return a
def pdivmod(a, b):
    a = list(a); q = [Fr(0)]*max(len(a)-len(b)+1, 0)
    while ptrim(a) and len(ptrim(a)) >= len(b):
        a = ptrim(a)
        c = a[-1]/b[-1]
        d = len(a)-len(b)
        q[d] = c
        for i, y in enumerate(b):
            a[i+d] -= c*y
        a = ptrim(a)
    return ptrim(q), ptrim(a)
def peval(a, x):
    s = Fr(0)
    for c in reversed(a):
        s = s*x + c
    return s

def interp(xs, ys):
    # Newton -> monomial
    n = len(xs)
    coef = list(ys)
    for j in range(1, n):
        for i in range(n-1, j-1, -1):
            coef[i] = (coef[i]-coef[i-1])/(xs[i]-xs[i-j])
    poly = [coef[-1]]
    for i in range(n-2, -1, -1):
        poly = padd(pmul(poly, [-xs[i], Fr(1)]), [coef[i]])
    return ptrim(poly)

def rational_reconstruct(xs, ys):
    """Cauchy interpolation by the extended Euclid algorithm; returns (num, den) with the smallest total degree that fits."""
    if all(y == 0 for y in ys):
        return [], [Fr(1)]
    M = [Fr(1)]
    for x in xs:
        M = pmul(M, [-x, Fr(1)])
    f = interp(xs, ys)
    r0, r1 = M, f
    t0, t1 = [], [Fr(1)]
    best = None
    while r1:
        deg_tot = (len(r1)-1) + (len(t1)-1)
        if best is None or deg_tot < best[0]:
            best = (deg_tot, r1, t1)
        q, r = pdivmod(r0, r1)
        r0, r1 = r1, r
        t0, t1 = t1, psub(t0, pmul(q, t1))
    _, num, den = best
    lead = den[-1]
    return [c/lead for c in num], [c/lead for c in den]

def factor_pm(den, numr):
    """pull factors (1+d) and (1-d) out of den and cancel with num; returns (num, den_rest, a, b): num/((1+d)^a (1-d)^b den_rest)"""
    a = 0; b = 0
    den = list(den); num = list(numr)
    while len(den) > 1 and peval(den, Fr(-1)) == 0:
        den, rem = pdivmod(den, [Fr(1), Fr(1)])
        a += 1
    while len(den) > 1 and peval(den, Fr(1)) == 0:
        den, rem = pdivmod(den, [Fr(-1), Fr(1)])   # divides by (d - 1)
        b += 1
    if b % 2 == 1:                                 # report the factor as (1 - d)^b
        num = [-c for c in num]
    return num, den, a, b

def pstr(p, var='d'):
    if not p:
        return '0'
    parts = []
    for i, c in enumerate(p):
        if c == 0:
            continue
        mono = '' if i == 0 else (var if i == 1 else '%s^%d' % (var, i))
        parts.append(('%s%s%s' % (c if c.denominator != 1 or i == 0 or abs(c) != 1 else ('-' if c < 0 else ''), '*' if (mono and (c.denominator != 1 or abs(c) != 1)) else '', mono)))
    return ' + '.join(parts).replace('+ -', '- ')

def cleaned(num, den):
    num, den, a, b = factor_pm(den, num)
    # common integer factor
    return num, den, a, b

def fstr(num, den):
    n, d, a, b = cleaned(num, den)
    if not n:
        return '0'
    s = '(' + pstr(n) + ')'
    denom = []
    if a: denom.append('(1+d)^%d' % a)
    if b: denom.append('(1-d)^%d' % b)
    if len(d) > 1 or (d and d[0] != 1):
        denom.append('(' + pstr(d) + ')')
    if denom:
        s += ' / [' + ' '.join(denom) + ']'
    return s

def main():
    u = Fr(sys.argv[1]) if len(sys.argv) > 1 else Fr(1)
    npts = int(sys.argv[2]) if len(sys.argv) > 2 else 34
    held = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    # delta points: avoid +-1, spread on rationals
    pts = []
    k = 1
    cand = []
    for q in (3, 5, 7, 11, 13, 17, 19, 23):
        for p in range(-q+1, q):
            f = Fr(p, q)
            if f not in cand and abs(f) < 1:
                cand.append(f)
    cand = sorted(cand, key=lambda f: (f.denominator, abs(f), f))
    pts = cand[:npts+held]
    t0 = time.time()
    tables = {}
    names = ['z1', 'C1_1', 'n_1', 'B_1']
    for d in pts:
        F.W.g2 = 1 - d*d
        dyn = F.Dyn(F.Ctx(d, u))
        res = dyn.results()
        assert not res['energy_first_order']
        tables[d] = {nm: coeff_table(res[nm]) for nm in names}
    print('built', len(pts), 'points in', int(time.time()-t0), 's', flush=True)
    fit = pts[:npts]; chk = pts[npts:]
    out = {}
    for nm in names:
        keys = set()
        for d in pts:
            keys |= set(tables[d][nm].keys())
        print('QUANTITY', nm)
        for key in sorted(keys):
            ys_a = [tables[d][nm].get(key, (Fr(0), Fr(0)))[0] for d in fit]
            ys_b = [tables[d][nm].get(key, (Fr(0), Fr(0)))[1] for d in fit]
            na, da = rational_reconstruct(fit, ys_a)
            nb, db = rational_reconstruct(fit, ys_b)
            bad = 0
            for d in chk:
                va, vb = tables[d][nm].get(key, (Fr(0), Fr(0)))
                if peval(na, d) != va*peval(da, d): bad += 1
                if peval(nb, d) != vb*peval(db, d): bad += 1
            out[(nm,)+key] = (na, da, nb, db)
            print('  s^%d t^%d k=%d  held_out_bad=%d' % (key[0], key[1], key[2], bad))
            print('     cosh(k g t) coef A = %s' % fstr(na, da))
            print('     g sinh(k g t) coef B = %s' % fstr(nb, db))
    print('done', int(time.time()-t0), 's')
    return 0

if __name__ == '__main__':
    sys.exit(main())
