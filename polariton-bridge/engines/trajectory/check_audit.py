#!/usr/bin/env python3
# check_audit.py -- the audit of the printed bounds, step by step, with code of its own (the round-1 review's audit_rv.py,
# sha256 d6e2b1d3..., widened to the half-step read and to the observable bounds of obs_bound_row).
# At every step of a run the step's coefficients C_0..C_K (the engine's own lists), the engine's bound before and after
# the step, and its local term (the growth of bsum) are captured. From the coefficients and the exact rational
# x = delta - u, u, y only, this script recomputes:
#   rho = F(p) - p'   (its own convolution, exact Fractions; F = -i dH/dconj(z) with H written out below),
#   Ir  = sum_n |rho_n| h^(n+1)/(n+1),  R_p = sum_n |C_n| h^n,  hor = |Z_new - p(h)|,
#   mu  = sqrt(2) R^2 (the log-norm bound |S|_F <= sqrt(2) R^2 at u = 1, derived a second way, below),
# each as a LOWER and an UPPER rational bound (isqrt both ways at 2^-400; e^q between its series truncated at q^12 and
# the same plus 2 q^13/13!). Checks:
#   LOCAL_LO : engine local >= hor_lo + e^(mu_p,lo h) Ir_lo        (the engine computed at least what its method states)
#   LOCAL_HI : engine local <= (hor_hi + e^(mu_p,hi h) Ir_hi)(1 + 2^-40)   (and not more than that, up to its rounding)
#   GLOBAL_LO: engine e_(j+1) >= e^(mu_g,lo h) e_j + engine local,  mu_g = sqrt(2) max(1, |Z_j|^2)
#   ROW_LO   : the printed f_err and A_over_N_err >= e(R+1) + 2 and e(R+1) + 2 sqrt(2) units of 2^-P
#   ROW_T    : each row's t = (2 steps + half_step) h / 2, steps and half_step as taken, h = 1/hden
#   OBS_ROUND: at every step and at the half-step read, the rounding of obs() at the integer state Z (exact rationals of
#              X, |A|^2, 4|B|^2, f, A at Z, with X(Z) = |A(Z)|^2 checked) within this script's own derived bounds:
#              f 2q, A 2 sqrt2 q, |A|^2 4R^2 q + q + 8q^2, X (2 + 2 sqrt2) R^2 q + 3q + 6q^2, D2sq 4 sqrt2 R^2 q + 4q + 8q^2
#   OBS_LO   : the printed TRAJ_OBS_BOUND terms >= this script's needs: X_exact e(R+1)(R^2+1), D2 exact 2e(R+1), D2sq exact
#              2e(R+1)(R^2+1), C1 2N/(N-1)(X_exact + X_round), D2 = D2 exact + D2sq_round / sqrt(D2sq), V2 identity
#              (A2_round + X_round) / X, each rounding part as in OBS_ROUND (sqrt 2 taken from above)
#   R_COVER  : the engine's R = bR >= max(1, |Z|_2) exactly at every audited step (R enters every observable bound)
#   OBS_EXACT: the exact rationals of _obs_terms, the values the rows round up, >= the needs of OBS_LO, and
#              D2_round^2 D2sq >= D2sq_round^2 (the direction of the square root), D2_round^2 >= D2sq_round where D2sq = 0
#   HALF_AUDITED: the half step of the read is one of the audited steps (the copy keeps the run's class)
#   ROW_LO and OBS_LO also read the printed state_err_2norm_le >= e and R_now_le >= R of both rows.
# Second derivation of mu at u = 1, a = |z0|^2, s = |z+|^2 + |z-|^2, a + s <= R^2:
#   |S|_F^2 <= s^2 + 2as + 2(s/2 + a)^2 = 2(a+s)^2 - s^2/2 <= 2 R^4.
# The run: NSTEPS main steps, then a half-step read one 1/(2 hden) later (its half step audited as a step of h/2).
# usage: check_audit.py ENGINE DELTA Y NSTEPS [LABEL [OUTDIR [N]]]   Allowed points only (reserved.clear first).
import hashlib, importlib.util, os, sys
from fractions import Fraction as Fr
from math import isqrt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reserved import clear

B = 400
SQ2_LO = Fr(isqrt(2 << (2 * B)), 1 << B)
SQ2_HI = SQ2_LO + Fr(1, 1 << B)


def sqrt_lo(q):
    q = Fr(q)
    return Fr(isqrt((q.numerator << (2 * B)) // q.denominator), 1 << B)


def sqrt_hi(q):
    q = Fr(q)
    n = -((-q.numerator << (2 * B)) // q.denominator)
    r = isqrt(n)
    return Fr(r if r * r == n else r + 1, 1 << B)


def exp_lo(q):
    s = Fr(0); t = Fr(1)
    for k in range(13):
        s += t; t = t * q / (k + 1)
    return s


def exp_hi(q):
    if not 0 <= q <= 1:
        raise AssertionError('exp_hi takes 0 <= q <= 1')
    s = Fr(0); t = Fr(1)
    for k in range(13):
        s += t; t = t * q / (k + 1)
    return s + 2 * t


def conv(a, b):
    """product of two complex polynomials, coefficient lists of (re, im) integer pairs"""
    out = [[0, 0] for _ in range(len(a) + len(b) - 1)]
    for i, (ar, ai) in enumerate(a):
        for j, (br, bi) in enumerate(b):
            o = out[i + j]
            o[0] += ar * br - ai * bi
            o[1] += ar * bi + ai * br
    return [tuple(o) for o in out]


def conj(a):
    return [(r, -i) for r, i in a]


def add(a, b):
    n = max(len(a), len(b))
    a = a + [(0, 0)] * (n - len(a)); b = b + [(0, 0)] * (n - len(b))
    return [(p[0] + q[0], p[1] + q[1]) for p, q in zip(a, b)]


def rho_sq(c0, cp, cm, x, u, y, P):
    """|rho_n|^2 for n = 0..3K as exact Fractions; inputs are the integer coefficients at scale 2^P"""
    K = len(c0) - 1
    S = 1 << (2 * P)
    n0 = conv(c0, conj(c0)); npl = conv(cp, conj(cp)); nmi = conv(cm, conj(cm))
    sq0 = conv(c0, c0); ppm = conv(cp, cm)
    cub_p = conv(add(n0, nmi), cp); cub_m = conv(add(n0, npl), cm); cub_0 = conv(add(npl, nmi), c0)
    pr_p = conv(sq0, conj(cm)); pr_m = conv(sq0, conj(cp)); pr_0 = conv(ppm, conj(c0))
    out = []
    for n in range(3 * K + 1):
        tot = Fr(0)
        for comp in ('p', 'm', '0'):
            if comp == 'p':
                g = (u * cub_p[n][0] + pr_p[n][0], u * cub_p[n][1] + pr_p[n][1])
                lin = (x * cp[n][0] - y * c0[n][0], x * cp[n][1] - y * c0[n][1]) if n <= K else (0, 0)
                own = cp
            elif comp == 'm':
                g = (u * cub_m[n][0] + pr_m[n][0], u * cub_m[n][1] + pr_m[n][1])
                lin = (x * cm[n][0] - y * c0[n][0], x * cm[n][1] - y * c0[n][1]) if n <= K else (0, 0)
                own = cm
            else:
                g = (u * cub_0[n][0] + 2 * pr_0[n][0], u * cub_0[n][1] + 2 * pr_0[n][1])
                lin = (-y * (cp[n][0] + cm[n][0]), -y * (cp[n][1] + cm[n][1])) if n <= K else (0, 0)
                own = c0
            gr = g[0] + lin[0] * S; gi = g[1] + lin[1] * S          # dH/dconj(z), scale 2^(3P)
            fr, fi = gi, -gr                                         # F = -i dH/dconj(z)
            if n < K:
                fr -= (n + 1) * own[n + 1][0] * S
                fi -= (n + 1) * own[n + 1][1] * S
            tot += fr * fr + fi * fi
        out.append(tot / (1 << (6 * P)))
    return out


def load(path):
    spec = importlib.util.spec_from_file_location('traj_audit', path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def parse_sci(s):
    m, e = s.split('e')
    a, b = m.split('.')
    v = Fr(int(a + b), 10 ** len(b))
    e = int(e)
    return v * 10 ** e if e >= 0 else v / 10 ** (-e)


def fields(row):
    return dict(p.split('=', 1) for p in row.split('|')[1:] if '=' in p)


def exact_obs(P, z0, zp, zm):
    """X, |A|^2, 4|B|^2, f and A at the integer state, exact rationals"""
    q = Fr(1, 1 << P)
    Z0 = (z0[0] * q, z0[1] * q); Zp = (zp[0] * q, zp[1] * q); Zm = (zm[0] * q, zm[1] * q)
    mul = lambda a, b: (a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0])
    cj = lambda a: (a[0], -a[1])
    n2 = lambda a: a[0] * a[0] + a[1] * a[1]
    A = tuple(s + t for s, t in zip(mul(cj(Z0), Zp), mul(cj(Zm), Z0)))
    Bq = mul(cj(Zm), Zp)
    X = n2(Z0) * (n2(Zp) + n2(Zm)) + 2 * mul(mul(cj(Zp), cj(Zm)), mul(Z0, Z0))[0]
    return X, n2(A), 4 * n2(Bq), n2(Zp) + n2(Zm), A


def main():
    mod, d, yy, nsteps = sys.argv[1], Fr(sys.argv[2]), Fr(sys.argv[3]), int(sys.argv[4])
    label = sys.argv[5] if len(sys.argv) > 5 else 'audit'
    outdir = sys.argv[6] if len(sys.argv) > 6 else None
    NN = int(sys.argv[7]) if len(sys.argv) > 7 else 729
    rows = [clear('check_audit_' + label, d, [yy])]
    T = load(mod)
    P = T.P
    qu = Fr(1, 1 << P)
    fails = {'LOCAL_LO': 0, 'LOCAL_HI': 0, 'GLOBAL_LO': 0, 'ROW_LO': 0, 'ROW_T': 0, 'OBS_ROUND': 0, 'OBS_LO': 0,
             'R_COVER': 0, 'OBS_EXACT': 0, 'HALF_AUDITED': 0}
    worst = {'local_lo_margin': None, 'global_lo_margin': None, 'round_ratio': Fr(0)}
    worst_by = {k: Fr(0) for k in ('X', 'A2', 'D2sq', 'f', 'A')}
    stats = {'steps': 0, 'half_steps': 0, 'obs_states': 0}

    def round_needs(R):
        R2 = R * R
        return {'f': 2 * qu, 'A': 2 * SQ2_HI * qu, 'A2': 4 * R2 * qu + qu + 8 * qu * qu,
                'X': (2 + 2 * SQ2_HI) * R2 * qu + 3 * qu + 6 * qu * qu, 'D2sq': 4 * SQ2_HI * R2 * qu + 4 * qu + 8 * qu * qu}

    def obs_round(tr):
        """OBS_ROUND at the current integer state of tr"""
        o = tr.obs(NN)
        X, A2, D2sq, ff, A = exact_obs(P, tr.z0, tr.zp, tr.zm)
        need = round_needs(tr.bR)
        dA = sqrt_hi((o['A_re'] - A[0]) ** 2 + (o['A_im'] - A[1]) ** 2)
        errs = {'X': abs(o['X'] - X), 'A2': abs(o['A2'] - A2), 'D2sq': abs(o['D2sq'] - D2sq), 'f': abs(o['f'] - ff), 'A': dA}
        ok = X == A2 and all(errs[k] <= need[k] for k in errs)
        for k in errs:
            r = errs[k] / need[k]
            worst_by[k] = max(worst_by[k], r)
            if r > worst['round_ratio']:
                worst['round_ratio'] = r
        stats['obs_states'] += 1
        return ok

    def obs_lo(tr):
        """OBS_LO: the printed TRAJ_OBS_BOUND row against this script's needs"""
        f = fields(tr.obs_bound_row(NN))
        o = tr.obs(NN)
        e = tr.berr; R = tr.bR; R2 = R * R
        need = round_needs(R)
        X_ex = e * (R + 1) * (R2 + 1)
        n = {'X_exact_part_le': X_ex, 'X_round_part_le': need['X'], 'X_err_le': X_ex + need['X'],
             'C1_err_le': Fr(2 * NN, NN - 1) * (X_ex + need['X']), 'A2_round_part_le': need['A2'],
             'D2_exact_part_le': 2 * e * (R + 1), 'D2sq_exact_part_le': 2 * e * (R + 1) * (R2 + 1),
             'D2sq_round_part_le': need['D2sq'], 'D2sq_err_le': 2 * e * (R + 1) * (R2 + 1) + need['D2sq'],
             'f_err_le': e * (R + 1) + need['f'], 'A_over_N_err_le': e * (R + 1) + need['A'],
             'A1_err_le': 2 * (e * (R + 1) + need['A']), 'state_err_2norm_le': e, 'R_now_le': R}
        s = sqrt_lo(o['D2sq'])
        d2r = need['D2sq'] / s if s > 0 else sqrt_hi(need['D2sq'])
        n['D2_round_part_le'] = d2r
        n['D2_err_le'] = 2 * e * (R + 1) + d2r
        ok = all((f[k] == '0' and v == 0) or (f[k] != '0' and parse_sci(f[k]) >= v) for k, v in n.items())
        if o['X'] > 0:
            ok = ok and f['V2_identity_err_le'] != 'undefined_X=0' and parse_sci(f['V2_identity_err_le']) >= (need['A2'] + need['X']) / o['X']
        else:
            ok = ok and f['V2_identity_err_le'] == 'undefined_X=0'
        t_ex, _ = tr._obs_terms(NN)
        if o['D2sq'] > 0:
            d2_dir = t_ex['D2_round'] ** 2 * o['D2sq'] >= t_ex['D2sq_round'] ** 2
        else:
            d2_dir = t_ex['D2_round'] ** 2 >= t_ex['D2sq_round'] > 0
        ex_ok = (d2_dir and t_ex['A2_round'] >= need['A2'] and t_ex['X_round'] >= need['X'] and t_ex['D2sq_round'] >= need['D2sq']
                 and t_ex['X_exact'] >= X_ex and t_ex['D2sq_exact'] >= n['D2sq_exact_part_le'] and t_ex['D2_exact'] >= n['D2_exact_part_le']
                 and t_ex['f_err'] >= n['f_err_le'] and t_ex['A_err'] >= n['A_over_N_err_le'])
        fails['OBS_EXACT'] += 0 if ex_ok else 1
        tt = Fr(2 * tr.step_count + tr.half_step, 2 * tr.hden)
        ok_t = (Fr(f['t']) == tt and int(f['steps']) == tr.step_count and int(f['half_step']) == tr.half_step
                and f['h'] == '1/%d' % tr.hden and int(f['N']) == NN)
        return ok, ok_t

    class Cap(T.Traj):
        def _bound_step(self, Z0, ZP, ZM):
            e0 = self.berr; s0 = self.bsum
            T.Traj._bound_step(self, Z0, ZP, ZM)
            local = self.bsum - s0
            e1 = self.berr
            h = Fr(1, self.hden)
            x = self.delta - self.u; u = self.u; y = self.y
            if u != 1:
                raise AssertionError('the audit derives mu at u = 1')
            c0 = [tuple(c) for c in Z0]; cp = [tuple(c) for c in ZP]; cm = [tuple(c) for c in ZM]
            K = len(c0) - 1
            rs = rho_sq(c0, cp, cm, x, u, y, P)
            Ir_lo = sum(sqrt_lo(rs[n]) * h ** (n + 1) / (n + 1) for n in range(len(rs)))
            Ir_hi = sum(sqrt_hi(rs[n]) * h ** (n + 1) / (n + 1) for n in range(len(rs)))
            Rp_lo = Fr(0); Rp_hi = Fr(0)
            for n in range(K + 1):
                nn = Fr(c0[n][0] ** 2 + c0[n][1] ** 2 + cp[n][0] ** 2 + cp[n][1] ** 2 + cm[n][0] ** 2 + cm[n][1] ** 2, 1 << (2 * P))
                Rp_lo += sqrt_lo(nn) * h ** n; Rp_hi += sqrt_hi(nn) * h ** n
            ph = [sum((Fr(C[n][k], 1 << P) * h ** n for n in range(K + 1)), Fr(0)) for C in (c0, cp, cm) for k in (0, 1)]
            zn = [Fr(v, 1 << P) for z in (self.z0, self.zp, self.zm) for v in z]
            dh = sum((a - b) ** 2 for a, b in zip(zn, ph))
            hor_lo = sqrt_lo(dh); hor_hi = sqrt_hi(dh)
            mu_p_lo = SQ2_LO * Rp_lo ** 2; mu_p_hi = SQ2_HI * Rp_hi ** 2
            need_lo = hor_lo + exp_lo(mu_p_lo * h) * Ir_lo
            cap_hi = (hor_hi + exp_hi(mu_p_hi * h) * Ir_hi) * (1 + Fr(1, 1 << 40))
            zj2 = Fr(sum(v * v for C in (c0, cp, cm) for v in C[0]), 1 << (2 * P))
            mu_g_lo = SQ2_LO * max(Fr(1), zj2)
            g_need = exp_lo(mu_g_lo * h) * e0 + local
            ok_lo = local >= need_lo; ok_hi = local <= cap_hi; ok_g = e1 >= g_need
            fails['LOCAL_LO'] += 0 if ok_lo else 1
            fails['LOCAL_HI'] += 0 if ok_hi else 1
            fails['GLOBAL_LO'] += 0 if ok_g else 1
            m1 = (local - need_lo) / need_lo if need_lo > 0 else None
            m2 = (e1 - g_need) / g_need if g_need > 0 else None
            if m1 is not None and (worst['local_lo_margin'] is None or m1 < worst['local_lo_margin']):
                worst['local_lo_margin'] = m1
            if m2 is not None and (worst['global_lo_margin'] is None or m2 < worst['global_lo_margin']):
                worst['global_lo_margin'] = m2
            stats['steps'] += 1
            if self.hden != tr_hden[0]:
                stats['half_steps'] += 1
            fails['OBS_ROUND'] += 0 if obs_round(self) else 1
            z2 = Fr(sum(v * v for v in (self.z0[0], self.z0[1], self.zp[0], self.zp[1], self.zm[0], self.zm[1])), 1 << (2 * P))
            fails['R_COVER'] += 0 if (self.bR >= 1 and self.bR * self.bR >= z2) else 1

    tr_hden = [32]
    tr = Cap(d, yy, bound=True)
    tr_hden[0] = tr.hden
    for _ in range(nsteps):
        tr.taylor_step()
    sci = T._sci_up
    checked = []
    for which, run in (('main', tr), ('half_step_read', tr.read_at(Fr(2 * nsteps + 1, 2 * tr.hden)))):
        row = run.bound_row()
        f = fields(row)
        e = run.berr; Rn = run.bR
        f_need = e * (Rn + 1) + 2 * qu
        A_need = e * (Rn + 1) + SQ2_HI * 2 * qu
        ok_row = (parse_sci(f['f_err_le']) >= f_need and parse_sci(f['A_over_N_err_le']) >= A_need and parse_sci(f['R_now_le']) >= Rn
                  and ((f['state_err_2norm_le'] == '0' and e == 0) or (f['state_err_2norm_le'] != '0' and parse_sci(f['state_err_2norm_le']) >= e)))
        fails['ROW_LO'] += 0 if ok_row else 1
        hden_row = int(f['h'].split('/')[1])
        want_t = Fr(2 * nsteps + (1 if which != 'main' else 0), 2 * hden_row)
        ok_t = (Fr(f['t']) == want_t and int(f['steps']) == nsteps and int(f['half_step']) == (0 if which == 'main' else 1)
                and hden_row == tr.hden)
        ok_o, ok_ot = obs_lo(run)
        fails['ROW_T'] += 0 if (ok_t and ok_ot) else 1
        fails['OBS_LO'] += 0 if ok_o else 1
        if which != 'main':
            fails['OBS_ROUND'] += 0 if obs_round(run) else 1
        checked.append((which, f, fields(run.obs_bound_row(NN))))
    fails['HALF_AUDITED'] += 0 if stats['half_steps'] == 1 else 1
    total = sum(fails.values())
    fm, fo = checked[0][1], checked[0][2]
    rows.append('AUDIT|engine=%s|delta=%s|y=%s|steps=%d|half_steps=%d|obs_states=%d|K=%d|h=1/%d|P=%d|N=%d|LOCAL_LO_fail=%d|'
                'LOCAL_HI_fail=%d|GLOBAL_LO_fail=%d|ROW_LO_fail=%d|ROW_T_fail=%d|OBS_ROUND_fail=%d|OBS_LO_fail=%d|R_COVER_fail=%d|'
                'OBS_EXACT_fail=%d|HALF_AUDITED_fail=%d|row_t=%s|'
                'read_t=%s|smallest_local_margin=%s|smallest_global_margin=%s|largest_rounding_over_derived=%s|rounding_over_derived_by_term=%s|state_bound=%s|'
                'printed_C1_err=%s|printed_D2_err=%s|printed_V2_identity_err=%s|verdict=%s|json=0' % (
                    label, d, yy, stats['steps'], stats['half_steps'], stats['obs_states'], tr.K, tr.hden, P, NN,
                    fails['LOCAL_LO'], fails['LOCAL_HI'], fails['GLOBAL_LO'], fails['ROW_LO'], fails['ROW_T'],
                    fails['OBS_ROUND'], fails['OBS_LO'], fails['R_COVER'], fails['OBS_EXACT'], fails['HALF_AUDITED'], fm['t'], checked[1][1]['t'],
                    ('%s%s' % ('-' if worst['local_lo_margin'] < 0 else '', sci(abs(worst['local_lo_margin'])))) if worst['local_lo_margin'] is not None else 'none',
                    ('%s%s' % ('-' if worst['global_lo_margin'] < 0 else '', sci(abs(worst['global_lo_margin'])))) if worst['global_lo_margin'] is not None else 'none',
                    sci(worst['round_ratio']), ','.join('%s:%s' % (k, sci(worst_by[k])) for k in sorted(worst_by)), fm['state_err_2norm_le'], fo['C1_err_le'], fo['D2_err_le'], fo['V2_identity_err_le'],
                    'MEASURED_PASS' if total == 0 else 'MEASURED_FAIL'))
    body = '\n'.join(rows) + '\n'
    if outdir:
        name = os.path.join(outdir, 'audit_%s.hbp' % label)
        with open(name, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(body)
        with open(name + '.sha256', 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('%s  %s\n' % (hashlib.sha256(body.encode('utf-8')).hexdigest(), os.path.basename(name)))
    print(body, end='')
    return total


if __name__ == '__main__':
    raise SystemExit(1 if main() else 0)
