# jetread.py -- the jet reads of PLAN-JETS.hbp: for each JET_ROW, the exact Gaussian averages of its jet at the row's
# N and t, for VNC and V1, every observable the frozen ensemble clauses read (E_VNC or E_VNC_ZERO, E_PAIR, E_V1, and the
# D_9_81 and P_PAIRS rows the row feeds), at every order to P, with the truncation estimate, the odd-order check, the
# conservation row and the jet's own e_int. Lane jet-plan-20261106 (opus55, a lane of the second seat for
# ACER-CLAUDE-FABLE5). Exact rationals only (float_used=0); averages by jetcmp.py (the ensemble-skip test's, unchanged),
# closed forms by cf.py (the ensemble design lane's, unchanged).
#
# usage: python3 -I -B -X utf8 jetread.py MODE PLAN ROOT ROW_ORDER [ROW_ORDER ...]
#   MODE   blind  : the plan's JET_LAUNCH output and JET_ROW output paths; prints values only (no verdicts: the read
#                   against the quantum and the closed forms is BRIDGE_ORDER step 6, after the blind runs)
#          analog : the analog paths, the analog delta and y; also prints the pair against its closed form at the
#                   analog delta (the plan's proof)
#   ROOT   the run root (the driver's --root); jets are read from ROOT/<output>, reads written to ROOT/<output>.
# A jet whose JET_HEAD does not carry the plan's binary sha256 and the plan's arguments, or that has no JET_DONE row,
# is refused (exit 4) and nothing is written for its rows.
import hashlib
import os
import sys
from fractions import Fraction as Fr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cf  # noqa: E402
import jetcmp as J  # noqa: E402

OBS_Y = ('C1', 'A1', 'V2', 'f', 'D2', 'ZR')
OBS_Y0 = ('C1', 'f', 'V2')


def fields(line):
    return J.fields(line)


def fail(msg, code=4):
    sys.stderr.write('JR_FAIL|reason=%s|json=0\n' % msg)
    sys.exit(code)


def sha_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def read_plan(path):
    head, launches, rows = None, {}, {}
    with open(path, 'rb') as fh:
        data = fh.read()
    if b'\r' in data:
        fail('CR_in_the_plan')
    for ln in data.decode('utf-8').split('\n'):
        if ln.startswith('PLAN_JETS_HEAD|'):
            head = fields(ln)
        elif ln.startswith('JET_LAUNCH|'):
            f = fields(ln)
            launches[f['id']] = f
        elif ln.startswith('JET_ROW|'):
            f = fields(ln)
            rows[int(f['order'])] = f
    return head, launches, rows


_JETS = {}


def load_jet(path, want_args, want_bin):
    if path in _JETS:
        return _JETS[path]
    if not os.path.exists(path):
        fail('jet_missing:%s' % os.path.basename(path))
    with open(path, 'rb') as fh:
        lines = fh.read().split(b'\n')
    if not lines or not lines[0].startswith(b'JET_HEAD|'):
        fail('no_JET_HEAD:%s' % os.path.basename(path))
    tail = [x for x in lines if x]
    if not tail[-1].startswith(b'JET_DONE|'):
        fail('no_JET_DONE:%s' % os.path.basename(path))
    h = fields(lines[0].decode('ascii'))
    if h.get('binary_sha256') != want_bin:
        fail('binary_sha256_differs_from_the_plan:%s' % os.path.basename(path))
    if h.get('args') != want_args:
        fail('arguments_differ_from_the_plan:%s' % os.path.basename(path))
    head, mons, polys, timing = J.read_jet(path)
    cons = {}
    for x in lines:
        if x.startswith(b'JET_CONS|'):
            c = fields(x.decode('ascii'))
            dev = [int(v.split(':')[1]) for v in c['dev_by_weight'].split(',')]
            cons[int(c['step'])] = (int(c['max_dev_over_scale_ppb']), int(c['weights_with_dev_and_no_scale']), dev)
    _JETS[path] = (head, mons, polys, timing, cons, sha_file(path))
    return _JETS[path]


def per_order(mons, polys, step, N, variant, law, q, P):
    jm = J.jet_means(mons, polys, step, N, variant, law, q, P)
    return jm, {p: J.jet_obs(jm[p]) for p in range(P + 1)}


def cl(x, sig=15):
    return J.sci(x, sig)


def main():
    mode, plan_path, root = sys.argv[1:4]
    orders = [int(v) for v in sys.argv[4:]]
    if mode not in ('blind', 'analog'):
        fail('mode_blind_or_analog')
    head, launches, rows = read_plan(plan_path)
    plan_sha = sha_file(plan_path)
    bin_sha = head['binary_sha256'].split('(')[0]
    reader_sha = sha_file(os.path.abspath(__file__))
    status_out = []
    for o in orders:
        r = rows[o]
        line = int(r['frozen_line'])
        N, t, tau = int(r['N']), Fr(r['t']), Fr(r['tau'])
        if mode == 'analog':
            a = dict(kv.split('=') for kv in r['analog'].split(','))
            d, y = Fr(a['delta']), Fr(a['y'])
            if Fr(a['t']) != t or int(a['N']) != N:
                fail('analog_N_or_t_differs')
        else:
            d, y = Fr(r['delta']), Fr(r['y'])
        L64, L128 = launches[r['jet']], launches[r['eint_jet']]
        key_out = 'output' if mode == 'blind' else 'analog_output'
        key_argv = 'argv' if mode == 'blind' else 'analog_argv'
        jets = []
        for Lx in (L64, L128):
            want = '~'.join(Lx[key_argv].split('~')[1:])
            jets.append(load_jet(os.path.join(root, Lx[key_out]), want, bin_sha))
        (h64, m64, p64, t64, c64, s64), (h128, m128, p128, t128, c128, s128) = jets
        if Fr(h64['delta']) != d or Fr(h64['y']) != y or Fr(h128['delta']) != d or Fr(h128['y']) != y:
            fail('jet_point_differs_from_the_row')
        P, q = int(h64['p']), int(h64['q'])
        if P != int(r['P_read']) or int(h128['p']) != P:
            fail('jet_order_differs_from_the_plan')
        st64, st128 = int(r['step64']), int(r['step128'])
        if Fr(st64, int(h64['dtden'])) != t or Fr(st128, int(h128['dtden'])) != t:
            fail('step_off_the_row_time')
        rows_out = []
        rows_out.append('JR_HEAD|mode=%s|row=L%04d|plan_order=%d|plan_sha256=%s|reader_sha256=%s|N=%d|delta=%s|y=%s|t=%s|step64=%d|step128=%d|tau=%s|P=%d|q=%d|jet=%s|jet_sha256=%s|eint_jet=%s|eint_jet_sha256=%s|binary_sha256=%s|blind_row_delta=%s|blind_row_y=%s|json=0' % (
            mode, line, o, plan_sha, reader_sha, N, d, y, t, st64, st128, tau, P, q, os.path.basename(L64[key_out]), s64,
            os.path.basename(L128[key_out]), s128, bin_sha, r['delta'], r['y']))
        obs_list = OBS_Y if y != 0 else OBS_Y0
        gates = {'G_TRUNC': [], 'G_FALL': [], 'G_ODD': [], 'G_CONS': [], 'G_ZERO': [], 'G_PAIR': []}
        c1 = {}
        for var in ('VNC', 'V1'):
            jm_e, ob_e = per_order(m64, p64, st64, N, var, 'engine', q, P)
            jm_g, ob_g = per_order(m64, p64, st64, N, var, 'gauss', q, P)
            jm_i, ob_i = per_order(m128, p128, st128, N, var, 'engine', q, P)
            c1[var] = {p: ob_e[p]['C1'] for p in range(P + 1)}
            if y == 0:
                for p in range(P + 1):
                    if jm_e[p]['A1sq'] != 0 or jm_e[p]['D2sq'] != 0 or jm_g[p]['A1sq'] != 0 or jm_g[p]['D2sq'] != 0:
                        gates['G_ZERO'].append('%s_p%d' % (var, p))
            for ob in obs_list:
                if ob == 'V2' and y == 0:
                    vals = {p: jm_e[p]['V2'] for p in range(P + 1)}
                    rows_out.append('JR_OBS|row=L%04d|variant=%s|obs=V2|law=engine|value_P=%s|meaning=printed_beside_A1=0(V2_UNDEFINED_as_a_comparison_at_y=0)|json=0' % (
                        line, var, cl(vals[P]) if vals[P] is not None else 'UNDEFINED'))
                    continue
                v = {p: ob_e[p].get(ob) for p in range(P + 1)}
                if v[P] is None:
                    fail('observable_missing:%s_%s' % (var, ob))
                vg = ob_g[P].get(ob)
                vi = ob_i[P].get(ob)
                T = abs(v[P] - v[P - 2])
                T2 = abs(v[P - 2] - v[P - 4])
                trel = T / abs(v[P]) if v[P] != 0 else None
                trel2 = T2 / abs(v[P - 2]) if v[P - 2] != 0 else None
                odd = all(v[p] == v[p - 1] for p in range(1, P + 1, 2))
                eint = 2 * abs(v[P] - vi) if vi is not None else None
                if not odd:
                    gates['G_ODD'].append('%s_%s' % (var, ob))
                if ob != 'ZR':
                    if trel is None or not trel < tau:
                        gates['G_TRUNC'].append('%s_%s' % (var, ob))
                    if T2 > 0 and not T <= T2:
                        gates['G_FALL'].append('%s_%s' % (var, ob))
                evens = ','.join('p%d:%s' % (p, cl(v[p], 13)) for p in range(0, P + 1, 2))
                rows_out.append('JR_OBS|row=L%04d|variant=%s|obs=%s|law=engine|value_P=%s|T_P=%s|Trel_P=%s|T_Pm2=%s|Trel_Pm2=%s|falls=%d|odd_equal_even_below=%d|gauss_P=%s|engine_vs_gauss_rel=%s|e_int=%s|e_int_rel=%s|by_order=%s|json=0' % (
                    line, var, ob, cl(v[P]), J.sci(T, 4), J.sci(trel, 4) if trel is not None else 'NA', J.sci(T2, 4),
                    J.sci(trel2, 4) if trel2 is not None else 'NA', int(T <= T2), int(odd), cl(vg) if vg is not None else 'NA',
                    J.sci((v[P] - vg) / v[P], 3) if (vg is not None and v[P] != 0) else 'NA',
                    J.sci(eint, 4) if eint is not None else 'NA',
                    J.sci(eint / abs(v[P]), 4) if (eint is not None and v[P] != 0) else 'NA', evens))
            if y != 0:
                zr = ob_e[P]['ZR']
                rows_out.append('JR_SIGN|row=L%04d|variant=%s|E_Re_Z_sign=%s|json=0' % (line, var, '-' if zr < 0 else ('+' if zr > 0 else '0')))
        pair = {p: N * N * (c1['V1'][p] - c1['VNC'][p]) for p in range(P + 1)}
        Tp = abs(pair[P] - pair[P - 2])
        if mode == 'blind':
            Pc = Fr(r['P_closed']) if r['P_closed'] != 'none' else None
            Pc_txt = r['P_closed'] + '(frozen_row)'
        else:
            Pc = cf.dC1v_V1(d, t)
            Pc_txt = cl(Pc, 8) + '(cf.dC1v_V1_at_the_analog_delta)'
        if Pc is None or not Tp <= abs(Pc) / 100:
            gates['G_PAIR'].append('pair_T_P')
        extra = ''
        if mode == 'analog':
            g2 = (1 - d * d) * t * t
            sh2 = (cf.cosh_k(2, g2) - 1) / 2
            phi0 = 2 * sh2 / ((1 - d * d) * N)
            tol = 43 * phi0 * abs(Pc) + abs(Pc) / 100
            extra = '|phi0=%s|tol_E_PAIR=%s|abs_pair_minus_P=%s|within_tol=%d|z_in_tol=%s' % (
                J.sci(phi0, 6), J.sci(tol, 6), J.sci(abs(pair[P] - Pc), 6), int(abs(pair[P] - Pc) <= tol),
                J.dec((pair[P] - Pc) / tol, 3))
        rows_out.append('JR_PAIR|row=L%04d|what=N^2*(C1_V1-C1_VNC)|law=engine|value_P=%s|T_P=%s|T_P_over_absP=%s|P_closed=%s%s|by_order=%s|json=0' % (
            line, cl(pair[P]), J.sci(Tp, 4), J.sci(Tp / abs(Pc), 4) if Pc else 'NA', Pc_txt, extra,
            ','.join('p%d:%s' % (p, cl(pair[p], 10)) for p in range(0, P + 1, 2))))
        # G_CONS: the number conservation is exact at t = 0 in both jets, and at the row's time its drift is RK4's own:
        # at every weight above the fixed-point floor (dev_128 > 2^10 units) dev_64 / dev_128 lies in [12, 20] (dt^4: 16),
        # and at a weight at the floor dev_64 stays within 2^15 units.
        for nm, cc in (('jet', c64), ('eint_jet', c128)):
            if 0 not in cc or any(v != 0 for v in cc[0][2]):
                gates['G_CONS'].append('%s_t0_not_exact' % nm)
        d64, d128 = c64[st64][2], c128[st128][2]
        rlo, rhi = None, None
        for w, (a64, a128) in enumerate(zip(d64, d128)):
            if a128 > 1024:
                ratio = Fr(a64, a128)
                rlo = ratio if rlo is None else min(rlo, ratio)
                rhi = ratio if rhi is None else max(rhi, ratio)
                if not Fr(12) <= ratio <= Fr(20):
                    gates['G_CONS'].append('w%d_ratio_off_dt4' % w)
            elif a64 > 32768:
                gates['G_CONS'].append('w%d_drift_without_dt4' % w)
        rows_out.append('JR_CONS|row=L%04d|jet_ppb=%d|eint_jet_ppb=%d|unscaled=%d,%d|t0_exact=%d|dt4_ratio_min=%s|dt4_ratio_max=%s|json=0' % (
            line, c64[st64][0], c128[st128][0], c64[st64][1], c128[st128][1],
            int(all(v == 0 for v in c64[0][2]) and all(v == 0 for v in c128[0][2])),
            J.dec(rlo, 2) if rlo is not None else 'NA', J.dec(rhi, 2) if rhi is not None else 'NA'))
        applicable = ('G_TRUNC', 'G_FALL', 'G_ODD', 'G_CONS', 'G_PAIR') + (('G_ZERO',) if y == 0 else ())
        failing = [g for g in applicable if gates[g]]
        status = 'JET_READY' if not failing else 'JET_NOT_RESOLVED'
        rows_out.append('JR_GATES|row=L%04d|%s|status=%s|json=0' % (
            line, '|'.join('%s=%s' % (g, 'pass' if not gates[g] else 'fail:' + ';'.join(gates[g])) for g in applicable), status))
        rows_out.append('JR_END|row=L%04d|rows=%d|float_used=0|json=0' % (line, len(rows_out) + 1))
        outp = os.path.join(root, r['output'] if mode == 'blind' else r['analog_output'])
        if os.path.exists(outp):
            fail('read_exists:%s' % os.path.basename(outp))
        os.makedirs(os.path.dirname(outp), exist_ok=True)
        with open(outp + '.part', 'w', newline='\n') as fh:
            fh.write('\n'.join(rows_out) + '\n')
        os.replace(outp + '.part', outp)
        status_out.append('JR_DONE|row=L%04d|output=%s|bytes=%d|sha256=%s|status=%s|failing=%s|json=0' % (
            line, r['output'] if mode == 'blind' else r['analog_output'], os.path.getsize(outp), sha_file(outp), status,
            ','.join(failing) or 'none'))
    print('\n'.join(status_out))


if __name__ == '__main__':
    main()
