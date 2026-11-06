#!/usr/bin/env python3
# s2_validate.py -- numerical runs of the single classical trajectory at ALLOWED points only, against the exact series.
# usage: s2_validate.py DELTA KMAX TMAX   (y list fixed below; reserved points refused by traj_int.guard)
import sys
from fractions import Fraction as Fr
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from exact import QGField, QIField, Series, ep_eval_qg, ep_eval, gamma_iv, iv_exp, Iv, sci
from traj_int import Traj, guard
from math import isqrt

OUTD = ''  # the output lands in the working folder the gate runner gives
YS = [Fr(1, 27), Fr(4, 27), Fr(1, 81), Fr(4, 81), Fr(1, 243)]
NREF = 729

def sqrt_iv(q, bits=200):
    q = Fr(q)
    lo = Fr(isqrt((q.numerator << (2 * bits)) // q.denominator), 1 << bits)
    return Iv(lo, lo + Fr(1, 1 << bits))

def fmax_orbit(delta, y, u=Fr(1)):
    """largest root in (0,1) of g(f) = f(1+delta) - (1+3u/4) f^2 + 4|y| sqrt(f(1-f)/2), by bisection in rationals"""
    delta = Fr(delta); y = abs(Fr(y))
    def g_sign(f):
        a = f * (1 + delta) - (1 + 3 * u / 4) * f * f
        # compare a + 4 y sqrt(f(1-f)/2) with 0 exactly: b = 4y sqrt(h), h = f(1-f)/2
        h = f * (1 - f) / 2
        if a >= 0:
            return 1
        # sign of b + a with a < 0: b^2 vs a^2
        return 1 if 16 * y * y * h > a * a else (-1 if 16 * y * y * h < a * a else 0)
    lo, hi = Fr(1, 10 ** 9), Fr(1)
    if g_sign(hi) >= 0:
        return Fr(1)
    for _ in range(80):
        mid = (lo + hi) / 2
        if g_sign(mid) > 0:
            lo = mid
        else:
            hi = mid
    return lo

def main():
    delta = Fr(sys.argv[1]); kmax = int(sys.argv[2]); tmax = Fr(sys.argv[3])
    for y in YS:
        guard(delta, y)
    g2 = 1 - delta * delta
    rows = []
    rows.append('S2|script=s2_validate.py|delta=%s|series_orders=1..%d|integrator=traj_int.py_Taylor28_h=1/32_fixed_point_2^-256|N_for_C1=%d|float_used=0|json=0' % (delta, 2 * kmax + 1, NREF))
    F = QGField(delta)
    S = Series(F).build(2 * kmax + 1)
    nb = S.norm_check(2 * kmax); eb = S.energy_check(2 * kmax)
    rows.append('S2_SERIES_CONSERVE|delta=%s|orders=2..%d|norm_bad=%s|energy_bad=%s|json=0' % (delta, 2 * kmax, nb or 'none', eb or 'none'))
    W = S.A_coeffs(kmax)
    Fc = S.f_coeffs(kmax)
    G = gamma_iv(g2)
    times = [Fr(k, 4) for k in range(2, int(tmax * 4) + 1)]
    for y in YS:
        tr = Traj(delta, y)
        prev_f = None; rising = True; fpk = None; tret = None; sign_change = None; A_prev = None
        fm = fmax_orbit(delta, y)
        rq = sqrt_iv(fm) / sqrt_iv(Fr(2))
        Tlb = None
        # T >= 2 ln(1 + sqrt(fmax/2)/|y|): report as exp(Tlb/2) = 1 + sqrt(fmax/2)/|y|
        ratio = Iv(1) + rq / abs(y)
        for t in times:
            tr.advance_to(t)
            o = tr.obs(NREF)
            # V2 identity on the integrated trajectory: A2 / X must be 1
            idv = o['A2'] / o['X'] if o['X'] != 0 else None
            # series partial sums for <A>/(N y) and f
            Ev = None
            parts = []
            acc = Iv(0)
            for k in range(0, kmax + 1):
                re, _ = ep_eval_qg(W[k], t, g2, G)
                acc = acc + re * (y ** (2 * k))
                parts.append(acc)
            facc = Iv(0); fparts = []
            for k in range(1, kmax + 1):
                re, _ = ep_eval_qg(Fc[k], t, g2, G)
                facc = facc + re * (y ** (2 * k))
                fparts.append(facc)
            Aint = o['A_re'] / y
            rel = [((p.mid() - Aint) / Aint) for p in parts]
            frel = [((p.mid() - o['f']) / o['f']) if o['f'] != 0 else None for p in fparts]
            rows.append('S2_ROW|delta=%s|y=%s|t=%s|f_int=%s|A_over_Ny_int=%s|A_im_int=%s|V2_identity_A2_over_X_minus_1=%s|norm_minus_1=%s|energy=%s|sym=%s|A_rel_err_series_orders=%s|f_rel_err_series_orders=%s|json=0' % (
                delta, y, t, sci(o['f'], 8), sci(Aint, 12), sci(o['A_im'], 3), sci(idv - 1, 3) if idv is not None else 'undef',
                sci(o['norm'] - 1, 3), sci(o['E'], 3), sci(o['sym'], 2),
                ','.join(sci(r, 3) for r in rel), ','.join(sci(r, 3) if r is not None else 'undef' for r in frel)))
            # return detection
            if prev_f is not None:
                if rising and o['f'] < prev_f:
                    rising = False; fpk = (t, prev_f)
                elif (not rising) and o['f'] > prev_f and tret is None:
                    tret = (t, prev_f)
            if A_prev is not None and sign_change is None and (A_prev < 0) != (o['A_re'] < 0):
                sign_change = t
            prev_f = o['f']; A_prev = o['A_re']
        rows.append('S2_RETURN|delta=%s|y=%s|fmax_orbit_algebraic=%s|f_peak_grid=%s@t=%s|first_f_min_after_peak_grid=%s@t~%s|A_sign_change_grid=%s|T_lower_bound=2ln(1+sqrt(fmax/2)/|y|)=2ln(%s)|json=0' % (
            delta, y, sci(fm, 8), sci(fpk[1], 8) if fpk else 'none', fpk[0] if fpk else '-',
            sci(tret[1], 4) if tret else 'none', tret[0] if tret else '-', sign_change if sign_change else 'none_on_grid', sci(ratio.mid(), 8)))
    name = OUTD + 's2_validate_d%s.txt' % str(delta).replace('/', 'o').replace('-', 'm')
    with open(name, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(rows) + '\n')
    print('\n'.join(r for r in rows if not r.startswith('S2_ROW')))
    print('rows', len(rows), 'written', name)

if __name__ == '__main__':
    main()
