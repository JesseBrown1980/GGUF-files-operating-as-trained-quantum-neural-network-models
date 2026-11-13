#!/usr/bin/env python3
# test_engine.py -- the trajectory engine's guard, step-grid, label and observable-bound tests, in one file.
#   Section R172: the round-1 review's 172 tests (bridge-engine-review-trajectory-20261106/tools/test_proposed_rv.py),
#     same cases and outcomes; its two comparisons with round-1 files read pinned sha256 values here (GOLD_*), which
#     equal those files' output (tools/golden.py of the round-2 lane).
#   Section NEW: the guard's checks one by one (each input's full list of refusing checks), u, the images against fx at
#     2^-256 and 2^-320, the flag's plumbing, every explicit raise with and without python -O, the half-step labels of
#     both bound rows, the rounding parts of the observable bounds at the integer state, the V2 identity, y = 0,
#     the D2 rounding branch at y = 0, reserved_open as each row prints it, and the class of the half-step copy.
# Reserved-point cases call guard()/Traj() with fx, Traj.taylor_step and Traj.obs on tripwires: a model function reached
# there raises before it computes. Model steps run at allowed points only, each after reserved.clear(). Integers and rationals only in the engine.
# usage: python3 -I -B -X utf8 test_engine.py [ENGINE [OUTDIR [LABEL]]]   (exit 0 when every test passes)
#        python3 [-O] -I -B -X utf8 test_engine.py --probe ENGINE         (one line: each explicit check, refused or ran)
import hashlib, importlib.util, os, subprocess, sys
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reserved import clear

GOLD_STATES64 = '1e9d02b8b14131b9f7515cb1257e18e78f527720b7b42b92698757911f3a6ab4'
GOLD_OBS64 = '100fde58239dbef423b279c747f6afd6a3c01de1e5afc5912dd7015f63ccf262'
GOLD_READ364 = '1099c65c96a073804a7d2a5e4ee70b47f155827819b416c9119a2cb6bee65801'
BLIND_Y = [Fr(0), Fr(1, 243), Fr(2, 243), Fr(4, 243), Fr(1, 81), Fr(2, 81), Fr(4, 81), Fr(1, 27), Fr(2, 27), Fr(4, 27)]
DELTA_HITS = ['DELTA_LIST', 'DELTA_RESERVED', 'DELTA_BAND', 'DELTA_IMAGE', 'X_IMAGE']
Y_HITS = ['Y_RESERVED', 'Y_BAND', 'Y_IMAGE']


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def probe(engine):
    """every explicit check at the allowed point (1/2, 1/27): one line, each item refused or ran"""
    clear('probe', '1/2', ['1/27'])
    T = load('traj_probe', engine)
    res = []

    def tryit(name, fn):
        try:
            fn()
            res.append(name + '=ran')
        except (AssertionError, SystemExit):
            res.append(name + '=refused')

    a = T.Traj(Fr(1, 2), Fr(1, 27))
    f0 = T.Traj(Fr(1, 2), Fr(1, 27))
    tryit('read_off_half_grid_ahead', lambda: f0.read_at(Fr(1, 128)))
    tryit('advance_off_grid', lambda: a.advance_to(Fr(1, 64)))
    res.append('steps_after=%d' % a.step_count)
    a.advance_to(Fr(1, 16))
    tryit('advance_behind', lambda: a.advance_to(Fr(1, 32)))
    tryit('read_off_half_grid', lambda: a.read_at(Fr(1, 128)))
    tryit('read_behind', lambda: a.read_at(Fr(1, 32)))
    c = a.read_at(Fr(5, 64))
    tryit('copy_advance', lambda: c.advance_to(Fr(3, 32)))
    tryit('copy_read', lambda: c.read_at(Fr(7, 64)))
    tryit('hden_48', lambda: T.Traj(Fr(1, 2), Fr(1, 27), hden=48))
    tryit('hden_0', lambda: T.Traj(Fr(1, 2), Fr(1, 27), hden=0))
    tryit('K_0', lambda: T.Traj(Fr(1, 2), Fr(1, 27), K=0))
    tryit('exp_up_2', lambda: T._exp_up(Fr(2)))
    tryit('exp_up_neg', lambda: T._exp_up(Fr(-1, 10)))
    tryit('bound_flag_1', lambda: T.Traj(Fr(1, 2), Fr(1, 27), bound=1))
    tryit('reserved_flag_1', lambda: T.Traj(Fr(1, 2), Fr(1, 27), allow_reserved=1))
    tryit('u_9/10', lambda: T.Traj(Fr(1, 2), Fr(1, 27), u=Fr(9, 10)))
    tryit('bound_row_bound_off', lambda: a.bound_row())
    b = T.Traj(Fr(1, 2), Fr(1, 27), bound=True)
    tryit('obs_bound_row_N1', lambda: b.obs_bound_row(1))
    print(','.join(res) + ',asserts=' + ('on' if __debug__ else 'off'))


def main():
    engine = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'traj_int.py')
    outdir = sys.argv[2] if len(sys.argv) > 2 else '.'
    label = sys.argv[3] if len(sys.argv) > 3 else 'engine'
    N = load('traj_under_test', engine)
    rows = ['TEST_ENGINE|engine=%s|sha256=%s|json=0' % (label, hashlib.sha256(open(engine, 'rb').read()).hexdigest())]
    fails = [0]

    def record(section, name, ok, detail):
        fails[0] += 0 if ok else 1
        rows.append('%s|case=%s|%s|pass=%d|json=0' % (section, name, detail, 1 if ok else 0))

    def outcome(fn):
        try:
            fn()
            return 'ADMITTED'
        except SystemExit as e:
            s = str(e)
            for k, v in (('REFUSED: reserved point', 'REFUSED_RESERVED'), ('REFUSED: delta and y take', 'REFUSED_TYPE'),
                         ('REFUSED: y=', 'REFUSED_Y_LIST'), ('REFUSED: delta=', 'REFUSED_DELTA_LIST'),
                         ('REFUSED: allow_reserved=', 'REFUSED_FLAG'), ('REFUSED: bound=', 'REFUSED_BOUND_FLAG'),
                         ('REFUSED: u=', 'REFUSED_U'), ('REFUSED: near a reserved point', 'REFUSED_BAND'),
                         ('REFUSED: the run images', 'REFUSED_IMAGE_MISMATCH')):
                if s.startswith(k):
                    return v
            return 'REFUSED_OTHER'
        except TypeError:
            return 'TYPE_ERROR'
        except AssertionError as e:
            return 'ASSERTION:' + str(e).replace(' ', '_')

    def case(section, name, fn, want):
        got = outcome(fn)
        record(section, name, got == want, 'want=%s|got=%s' % (want, got))

    def hits(name, d, y, want, **kw):
        got = N.guard_checks(d, y, **kw)
        record('NEW_GUARD', name, got == want, 'want=%s|got=%s' % (','.join(want) or 'none', ','.join(got) or 'none'))

    class Tripwire(Exception):
        pass

    def trip(*a, **k):
        raise Tripwire()

    saved = (N.fx, N.Traj.taylor_step, N.Traj.obs)
    N.fx = trip; N.Traj.taylor_step = trip; N.Traj.obs = trip
    tripped = 0
    try:
        # ---------------------------------------------------------------- R172, reserved section (165 cases)
        S = 'R172'
        case(S, 'y_float_2/27_delta_1/2', lambda: N.guard(Fr(1, 2), 2 / 27), 'REFUSED_TYPE')
        case(S, 'y_2/27+2^-300_delta_1/2', lambda: N.guard(Fr(1, 2), Fr(2, 27) + Fr(1, 1 << 300)), 'REFUSED_Y_LIST')
        case(S, 'y_decimal_near_2/27_delta_1/4', lambda: N.guard(Fr(1, 4), '0.0740740740740741'), 'REFUSED_Y_LIST')
        case(S, 'delta_float_0.6_flag_True', lambda: N.guard(3 / 5, Fr(1, 27), allow_reserved=True), 'REFUSED_TYPE')
        case(S, 'delta_bool', lambda: N.guard(True, Fr(1, 27)), 'REFUSED_TYPE')
        case(S, 'y_unlisted_1/3_delta_1/2', lambda: N.guard(Fr(1, 2), Fr(1, 3)), 'REFUSED_Y_LIST')
        for d in (Fr(3, 5), Fr(-3, 5)):
            for y in BLIND_Y + [-v for v in BLIND_Y if v]:
                case(S, 'blind_%s_%s_no_flag' % (d, y), lambda: N.guard(d, y), 'REFUSED_RESERVED')
                case(S, 'blind_%s_%s_flag_True' % (d, y), lambda: N.guard(d, y, allow_reserved=True), 'ADMITTED')
                case(S, 'blind_%s_%s_Traj_no_flag' % (d, y), lambda: N.Traj(d, y), 'REFUSED_RESERVED')
        for d in sorted(N.ALLOWED_DELTA):
            for y in (Fr(2, 27), Fr(-2, 27)):
                case(S, 'y_2/27_%s_%s_flag_True' % (d, y), lambda: N.guard(d, y, allow_reserved=True), 'REFUSED_RESERVED')
                case(S, 'y_2/27_%s_%s_no_flag' % (d, y), lambda: N.guard(d, y), 'REFUSED_RESERVED')
        for d in ('1/2', '-1/2', '3/4'):
            for y in ('1/27', '4/27', '1/81', '4/81', '1/243'):
                case(S, 's2_point_%s_%s' % (d, y), lambda: N.guard(Fr(d), Fr(y)), 'ADMITTED')
        case(S, 'bound_flag_1', lambda: N.Traj(Fr(1, 2), Fr(1, 27), bound=1), 'REFUSED_BOUND_FLAG')
        case(S, 'hden_48', lambda: N.Traj(Fr(1, 2), Fr(1, 27), hden=48), 'ASSERTION:hden_takes_a_power_of_two')
        # ---------------------------------------------------------------- NEW, reserved section
        near_y = Fr(2, 27) + Fr(1, 1 << 300)
        fl = Fr(2 / 27)
        dec = '0.0740740740740741'
        for d in (Fr(1, 2), Fr(1, 4), Fr(0)):
            for nm, y in (('2/27+2^-300', near_y), ('Fraction(float_2/27)', fl), ('decimal_string', dec)):
                for sgn in (1, -1):
                    yy = y if sgn == 1 else (-y if not isinstance(y, str) else '-' + y)
                    for flag in (False, True):
                        hits('F06_%s_%s_y=%s%s_flag=%s' % (nm, d, '' if sgn == 1 else '-', nm, flag), d, yy,
                             ['Y_LIST', 'Y_BAND', 'Y_IMAGE'], allow_reserved=flag)
        for d in (Fr(3, 5), Fr(-3, 5)):
            for nm, y in (('2/27+2^-300', near_y), ('Fraction(float_2/27)', fl), ('decimal_string', dec)):
                hits('F06_%s_at_blind_delta_%s_flag_True' % (nm, d), d, y, ['Y_LIST', 'Y_BAND', 'Y_IMAGE'], allow_reserved=True)
                hits('F06_%s_at_blind_delta_%s_flag_False' % (nm, d), d, y,
                     ['Y_LIST', 'DELTA_LIST', 'DELTA_RESERVED', 'DELTA_BAND', 'Y_BAND', 'DELTA_IMAGE', 'X_IMAGE', 'Y_IMAGE'])
        case('NEW_GUARD', 'y_float_-2/27_type', lambda: N.guard(Fr(1, 2), -2 / 27), 'REFUSED_TYPE')
        rec = N.guard_checks(Fr(1, 2), near_y)
        same_img = N._img(near_y) == N._img(Fr(2, 27))
        record('NEW_GUARD', 'image_of_2/27+2^-300_equals_image_of_2/27', same_img and rec == ['Y_LIST', 'Y_BAND', 'Y_IMAGE'],
               'image_equal=%d|checks=%s' % (1 if same_img else 0, ','.join(rec)))
        for flag in (False, True):
            for nm, d in (('3/5+2^-300', Fr(3, 5) + Fr(1, 1 << 300)), ('-3/5-2^-300', Fr(-3, 5) - Fr(1, 1 << 300)),
                          ('Fraction(float_0.6)', Fr(0.6)), ('3/5+1/21', Fr(3, 5) + Fr(1, 21)), ('decimal_0.6000000000000001', '0.6000000000000001')):
                hits('delta_near_%s_flag=%s' % (nm, flag), d, Fr(1, 27), ['DELTA_LIST', 'DELTA_BAND', 'DELTA_IMAGE', 'X_IMAGE'],
                     allow_reserved=flag)
        hits('delta_band_edge_11/20', Fr(11, 20), Fr(1, 27), ['DELTA_LIST', 'DELTA_IMAGE', 'X_IMAGE'])
        hits('delta_outside_band_27/50', Fr(27, 50), Fr(1, 27), ['DELTA_LIST'])
        hits('y_band_edge_5/81', Fr(1, 2), Fr(5, 81), ['Y_LIST', 'Y_IMAGE'])
        hits('y_inside_band_13/162', Fr(1, 2), Fr(13, 162), ['Y_LIST', 'Y_BAND', 'Y_IMAGE'])
        hits('y_outside_band_5/54', Fr(1, 2), Fr(5, 54), ['Y_LIST'])
        hits('y_list_alone_1/3', Fr(1, 2), Fr(1, 3), ['Y_LIST'])
        hits('delta_list_alone_1/10', Fr(1, 10), Fr(1, 27), ['DELTA_LIST'])
        for d in (Fr(3, 5), Fr(-3, 5)):
            for y in BLIND_Y + [-v for v in BLIND_Y if v]:
                hits('blind_%s_%s_flag_True' % (d, y), d, y, [], allow_reserved=True)
                want = list(DELTA_HITS)
                if abs(y) == Fr(2, 27):
                    want = ['DELTA_LIST', 'DELTA_RESERVED', 'Y_RESERVED', 'DELTA_BAND', 'Y_BAND', 'DELTA_IMAGE', 'X_IMAGE', 'Y_IMAGE']
                hits('blind_%s_%s_no_flag' % (d, y), d, y, want)
        for d in sorted(N.ALLOWED_DELTA):
            for y in BLIND_Y + [-v for v in BLIND_Y if v]:
                if abs(y) == Fr(2, 27):
                    hits('listed_%s_%s_flag_True' % (d, y), d, y, Y_HITS, allow_reserved=True)
                    hits('listed_%s_%s_no_flag' % (d, y), d, y, Y_HITS)
                else:
                    hits('listed_%s_%s_flag_True' % (d, y), d, y, [], allow_reserved=True)
                    hits('listed_%s_%s_no_flag' % (d, y), d, y, [])
        for nm, v in (('1', 1), ('0', 0), ('None', None), ('str_True', 'True'), ('Fraction_1', Fr(1))):
            case('NEW_GUARD', 'flag_%s_guard' % nm, lambda: N.guard(Fr(3, 5), Fr(1, 27), allow_reserved=v), 'REFUSED_FLAG')
            case('NEW_GUARD', 'flag_%s_Traj' % nm, lambda: N.Traj(Fr(3, 5), Fr(1, 27), allow_reserved=v), 'REFUSED_FLAG')
        case('NEW_GUARD', 'flag_positional', lambda: N.guard(Fr(3, 5), Fr(1, 27), True), 'TYPE_ERROR')
        for nm, v in (('abc', 'abc'), ('1/0', '1/0'), ('list', [1]), ('None', None), ('complex', 1j)):
            case('NEW_GUARD', 'y_garbage_%s' % nm, lambda: N.guard(Fr(1, 2), v), 'REFUSED_TYPE')
            case('NEW_GUARD', 'delta_garbage_%s' % nm, lambda: N.guard(v, Fr(1, 27)), 'REFUSED_TYPE')
        for nm, v in (('9/10', Fr(9, 10)), ('float_1.0', 1.0), ('bool_True', True), ('1+2^-300', Fr(1) + Fr(1, 1 << 300)), ('str_2', '2')):
            case('NEW_GUARD', 'u_%s' % nm, lambda: N.Traj(Fr(1, 2), Fr(1, 27), u=v), 'REFUSED_U')
        case('NEW_GUARD', 'reserved_Traj_no_flag_before_any_model_function', lambda: N.Traj(Fr(3, 5), Fr(2, 27)), 'REFUSED_RESERVED')
        # the flag reaches guard from Traj; the stub stops construction before any state is built
        seen = []

        class Stop(Exception):
            pass

        def stub(delta, y, *, allow_reserved=False):
            seen.append(allow_reserved)
            raise Stop()
        real_guard = N.guard
        N.guard = stub
        try:
            for kw in ({}, {'allow_reserved': True}, {'allow_reserved': False}):
                try:
                    N.Traj(Fr(3, 5), Fr(1, 27), **kw)
                except Stop:
                    pass
        finally:
            N.guard = real_guard
        record('NEW_GUARD', 'Traj_passes_its_flag_to_guard', seen == [False, True, False],
               'stub_saw=%s' % ','.join(str(s) for s in seen))
    except Tripwire:
        tripped = 1
    finally:
        N.fx, N.Traj.taylor_step, N.Traj.obs = saved
    fails[0] += tripped
    rows.append('RESERVED_SECTION|model_functions_called=%d|method=fx,taylor_step,obs_replaced_by_tripwires|json=0' % tripped)

    # ---------------------------------------------------------------- images against fx, at 2^-256 and at 2^-320
    qs = [Fr(0), Fr(1, 2), Fr(-1, 2), Fr(-1, 2) - 1, Fr(3, 4) - 1, Fr(1, 27), Fr(-4, 81), Fr(1, 243), Fr(7, 3), Fr(-11, 7),
          Fr(3, 5), Fr(-3, 5), Fr(-2, 5), Fr(-8, 5), Fr(2, 27), Fr(-2, 27), Fr(12345678901234567, 98765432109876543)]
    bad = sum(1 for q in qs if N._img(q) != N.fx(q))
    M = load('traj_under_test_p320', engine)
    M.P = 320; M.ONE = 1 << 320
    bad320 = sum(1 for q in qs if M._img(q) != M.fx(q))
    record('NEW_IMAGE', 'guard_image_equals_fx', bad == 0 and bad320 == 0, 'values=%d|differ_at_2^-256=%d|differ_at_2^-320=%d' % (
        len(qs), bad, bad320))
    rows.append(clear('test_u_admitted', '1/2', ['1/27']))
    for nm, v in (('int_1', 1), ('str_1', '1'), ('Fraction_1', Fr(1))):
        case('NEW_GUARD', 'u_%s_admitted' % nm, lambda: N.Traj(Fr(1, 2), Fr(1, 27), u=v), 'ADMITTED')
    # the run's own images are compared with the guard's: an fx one unit off is refused at construction
    real_fx = N.fx
    N.fx = lambda q: real_fx(q) + 1
    try:
        case('NEW_IMAGE', 'run_images_checked_against_the_guard', lambda: N.Traj(Fr(1, 2), Fr(1, 27)), 'REFUSED_IMAGE_MISMATCH')
    finally:
        N.fx = real_fx

    # ---------------------------------------------------------------- R172, allowed points (7 cases)
    S = 'R172'
    rows.append(clear('test_same_states', '1/2', ['1/27']))
    a = N.Traj(Fr(1, 2), Fr(1, 27))
    st = []
    for _ in range(64):
        a.taylor_step()
        st.append(repr((a.z0, a.zp, a.zm)))
    h = hashlib.sha256('\n'.join(st).encode('ascii')).hexdigest()
    record(S, 'same_states_as_src_64_steps', h == GOLD_STATES64, 'states_sha256=%s|pinned=%s' % (h, GOLD_STATES64))
    rows.append(clear('test_read_label', '1/2', ['4/27']))
    n = N.Traj(Fr(1, 2), Fr(4, 27), bound=True)
    qn = n.read_at(Fr(3, 64))
    f = dict(p.split('=', 1) for p in qn.bound_row().split('|')[1:] if '=' in p)
    s = repr((qn.z0, qn.zp, qn.zm, qn.berr.numerator, qn.berr.denominator))
    same = hashlib.sha256(s.encode('ascii')).hexdigest() == GOLD_READ364
    ok = same and f['t'] == '3/64' and f['h'] == '1/32' and f['steps'] == '1' and f['half_step'] == '1' and qn.time() == Fr(3, 64)
    record(S, 'read_at_3/64_label', ok, 't=%s|h=%s|steps=%s|half_step=%s|state_and_bound_equal_to_lane_proposed=%d' % (
        f['t'], f['h'], f['steps'], f['half_step'], 1 if same else 0))
    case(S, 'read_copy_cannot_step', lambda: qn.advance_to(Fr(1, 16)), 'ASSERTION:time_off_the_step_grid')
    case(S, 'read_copy_cannot_read', lambda: qn.read_at(Fr(5, 64)), 'ASSERTION:time_off_the_half-step_grid_or_behind')
    case(S, 'main_run_reads_behind_refused', lambda: n.read_at(Fr(1, 64)), 'ASSERTION:time_off_the_half-step_grid_or_behind')
    probes = {}
    for flags in (['-I', '-B', '-X', 'utf8'], ['-O', '-I', '-B', '-X', 'utf8']):
        p = subprocess.run([sys.executable] + flags + [os.path.abspath(__file__), '--probe', os.path.abspath(engine)],
                           capture_output=True, text=True)
        out = p.stdout.strip().split('\n')[-1] if p.stdout.strip() else (p.stderr.strip().split('\n') or ['none'])[-1]
        probes['O' if '-O' in flags else 'plain'] = out
        ok = 'advance_off_grid=refused' in out and 'hden_48=refused' in out
        record(S, 'grid_checks_flags_%s' % '_'.join(flags), ok, 'result=%s' % out.replace('|', '/').replace(',', ';'))

    # ---------------------------------------------------------------- NEW: every explicit raise, with and without -O
    items_plain = [x for x in probes['plain'].split(',') if not x.startswith('asserts=')]
    items_O = [x for x in probes['O'].split(',') if not x.startswith('asserts=')]
    every = items_plain == items_O and all(x.endswith('=refused') or x == 'steps_after=0' for x in items_plain) \
        and len(items_plain) == 18 and probes['O'].endswith('asserts=off') and probes['plain'].endswith('asserts=on')
    record('NEW_STEPS', 'every_explicit_check_refuses_with_and_without_-O', every, 'items=%d|same_under_-O=%d|plain=%s' % (
        len(items_plain), 1 if items_plain == items_O else 0, ';'.join(items_plain)))

    # ---------------------------------------------------------------- NEW: labels and the observable bounds
    def fields(row):
        return dict(p.split('=', 1) for p in row.split('|')[1:] if '=' in p)

    ob = fields(qn.obs_bound_row(729))
    record('NEW_LABEL', 'half_step_read_TRAJ_OBS_BOUND', ob['t'] == '3/64' and ob['h'] == '1/32' and ob['steps'] == '1'
           and ob['half_step'] == '1' and ob['N'] == '729', 't=%s|h=%s|steps=%s|half_step=%s' % (ob['t'], ob['h'], ob['steps'], ob['half_step']))
    g = n.read_at(Fr(1, 16))
    fg = fields(g.bound_row())
    record('NEW_LABEL', 'grid_time_read', fg['t'] == '1/16' and fg['steps'] == '2' and fg['half_step'] == '0' and g.time() == Fr(1, 16),
           't=%s|steps=%s|half_step=%s' % (fg['t'], fg['steps'], fg['half_step']))
    fm = fields(n.bound_row())
    record('NEW_LABEL', 'main_run_after_reads', fm['t'] == '1/16' and fm['steps'] == '2' and fm['half_step'] == '0' and n.half_step == 0,
           't=%s|steps=%s|half_step=%s' % (fm['t'], fm['steps'], fm['half_step']))

    def exact_obs(T, z0, zp, zm):
        """X, |A|^2, 4|B|^2, f and A at the integer state, as exact rationals"""
        q = Fr(1, T.ONE)
        Z0 = (Fr(z0[0]) * q, Fr(z0[1]) * q); Zp = (Fr(zp[0]) * q, Fr(zp[1]) * q); Zm = (Fr(zm[0]) * q, Fr(zm[1]) * q)
        mul = lambda a, b: (a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0])
        cj = lambda a: (a[0], -a[1])
        n2 = lambda a: a[0] * a[0] + a[1] * a[1]
        A = tuple(x + y for x, y in zip(mul(cj(Z0), Zp), mul(cj(Zm), Z0)))
        B = mul(cj(Zm), Zp)
        X = n2(Z0) * (n2(Zp) + n2(Zm)) + 2 * mul(mul(cj(Zp), cj(Zm)), mul(Z0, Z0))[0]
        return X, n2(A), 4 * n2(B), n2(Zp) + n2(Zm), A

    def check_round(T, tr, Nn, tag):
        t, o = tr._obs_terms(Nn)
        X, A2, D2sq, ff, A = exact_obs(T, tr.z0, tr.zp, tr.zm)
        q = Fr(1, T.ONE)
        dA2 = (o['A_re'] - A[0]) ** 2 + (o['A_im'] - A[1]) ** 2
        ok = (abs(o['X'] - X) <= t['X_round'] and abs(o['A2'] - A2) <= t['A2_round'] and abs(o['D2sq'] - D2sq) <= t['D2sq_round']
              and abs(o['f'] - ff) <= 2 * q and dA2 <= 9 * q * q and X == A2)
        v2 = abs(o['A2'] / o['X'] - 1) <= t['V2_id_err'] if o['X'] > 0 else t['V2_id_err'] is None
        r = fields(tr.obs_bound_row(Nn))
        printed = all(_parse(r[k]) >= t[v] for k, v in (('X_round_part_le', 'X_round'), ('C1_err_le', 'C1_err'),
                                                        ('D2_err_le', 'D2_err'), ('D2sq_err_le', 'D2sq_err'),
                                                        ('A2_round_part_le', 'A2_round'), ('f_err_le', 'f_err')))
        return ok and v2 and printed, 'X_minus_X(Z)_over_round=%s|identity_X(Z)_equals_absA(Z)^2=%d|V2_identity_within=%d|printed_ge_exact=%d' % (
            T._sci_up(abs(o['X'] - X) / t['X_round']), 1 if X == A2 else 0, 1 if v2 else 0, 1 if printed else 0)

    rows.append(clear('test_obs_terms', '1/2', ['4/27']))
    m = N.Traj(Fr(1, 2), Fr(4, 27), bound=True)
    allok = True; worst = ''
    for k in range(1, 65):
        m.taylor_step()
        if k in (1, 2, 8, 32, 64):
            ok, det = check_round(N, m, 729, k)
            allok = allok and ok
            worst = det
    okq, detq = check_round(N, qn, 81, 'read')
    record('NEW_OBS', 'rounding_parts_hold_at_the_integer_state', allok and okq, 'steps=1,2,8,32,64,read_3/64|last=%s' % worst)
    rows.append(clear('test_zero_field', '1/2', ['0']))
    z = N.Traj(Fr(1, 2), Fr(0), bound=True)
    z.advance_to(Fr(1, 8))
    rz = fields(z.obs_bound_row(729))
    record('NEW_OBS', 'zero_field_fixed_point', (z.z0, z.zp, z.zm) == ((N.ONE, 0), (0, 0), (0, 0)) and z.berr == 0
           and rz['V2_identity_err_le'] == 'undefined_X=0' and rz['state_err_2norm_le'] == '0',
           'state_err=%s|V2_identity=%s' % (rz['state_err_2norm_le'], rz['V2_identity_err_le']))
    tz, oz = z._obs_terms(729)
    record('NEW_OBS', 'zero_field_D2_round_branch', oz['D2sq'] == 0 and tz['D2_round'] > 0 and tz['D2_round'] ** 2 >= tz['D2sq_round'],
           'D2sq=%s|D2_round=%s' % (oz['D2sq'], N._sci_up(tz['D2_round'])))
    lab = fields(z.bound_row())['reserved_open'] + fields(z.obs_bound_row(729))['reserved_open']
    z.reserved_open = True
    lab += fields(z.bound_row())['reserved_open'] + fields(z.obs_bound_row(729))['reserved_open']
    z.reserved_open = False
    record('NEW_LABEL', 'reserved_open_printed_as_held', lab == '0011', 'printed=%s' % lab)

    class Sub(N.Traj):
        pass
    sb = Sub(Fr(1, 2), Fr(0), bound=True)
    record('NEW_STEPS', 'half_step_copy_keeps_the_class', type(sb.read_at(Fr(1, 64))) is Sub, 'class=%s' % type(sb.read_at(Fr(1, 64))).__name__)
    rows.append(clear('test_golden_bound_on', '1/2', ['1/27']))
    for nm, kw in (('bound_on', {'bound': True}), ('flag_True_at_allowed_point', {'allow_reserved': True})):
        b = N.Traj(Fr(1, 2), Fr(1, 27), **kw)
        st = []
        for _ in range(64):
            b.taylor_step()
            st.append(repr((b.z0, b.zp, b.zm)))
        hb = hashlib.sha256('\n'.join(st).encode('ascii')).hexdigest()
        record('NEW_STATES', 'states_64_%s' % nm, hb == GOLD_STATES64 and b.reserved_open is False, 'states_sha256=%s' % hb)
    o = a.obs(729)
    ho = hashlib.sha256('\n'.join('%s=%s' % (k, o[k]) for k in sorted(o)).encode('ascii')).hexdigest()
    record('NEW_STATES', 'obs_729_at_t=2', ho == GOLD_OBS64, 'obs_sha256=%s' % ho)

    n172 = sum(1 for r in rows if r.startswith('R172|'))
    nnew = sum(1 for r in rows if r.startswith('NEW_'))
    rows.append('TEST_ENGINE_SUMMARY|engine=%s|review_tests=%d|new_tests=%d|failed=%d|verdict=%s|json=0' % (
        label, n172, nnew, fails[0], 'MEASURED_PASS' if fails[0] == 0 else 'MEASURED_FAIL'))
    body = '\n'.join(rows) + '\n'
    name = os.path.join(outdir, 'test_engine_%s.hbp' % label)
    with open(name, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(body)
    with open(name + '.sha256', 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('%s  %s\n' % (hashlib.sha256(body.encode('utf-8')).hexdigest(), os.path.basename(name)))
    print('\n'.join(r for r in rows if 'pass=0' in r or r.startswith(('TEST_ENGINE', 'RESERVED_SECTION'))))
    return 1 if fails[0] else 0


def _parse(s):
    """the rational of a printed decimal such as 1.23e-45"""
    mant, ex = s.split('e')
    a, b = mant.split('.')
    v = Fr(int(a + b), 10 ** len(b))
    ex = int(ex)
    return v * 10 ** ex if ex >= 0 else v / 10 ** (-ex)


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--probe':
        probe(sys.argv[2])
    else:
        raise SystemExit(main())
