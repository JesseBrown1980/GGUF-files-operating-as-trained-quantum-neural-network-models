# plan_jets.py -- writes PLAN-JETS.hbp: the flow-map jets beside the frozen Monte Carlo on the first-order BRIDGE_AT
# rows (the operator's decision of 2026-11-06, item 1). Lane jet-plan-20261106 (opus55, a lane of the second seat for
# ACER-CLAUDE-FABLE5). Reads PREDICTION.hbp and AMENDMENT-2026-11-06-F-SAMPLING.hbp as data; computes nothing of any
# model. Exact rationals only (float_used=0).
#
# usage: python3 -I -B -X utf8 plan_jets.py OUT PREDICTION.hbp AMENDMENT.hbp BINARY_SHA256 SOURCE_SHA256 TOOLS_DIR
#
# One JET_ROW per first-order BRIDGE_AT row (first_order_range=1), keyed by its line in PREDICTION.hbp; one JET_LAUNCH
# per (delta, y) the rows need (a jet does not depend on N) and one beside it at dtden=128 (the jet's own e_int).
# The jet order is the order of the ensemble-skip test's agreement (T1_AGREE, 404 of 404 rows at f_law <= 1/50):
# P = 12 at y = 0 and P = 10 at y != 0, q = 64. Analogs for the plan's proof: delta 3/5 -> 1/2, -3/5 -> -1/2; y = 2/27
# -> 1/18 (a jet is N-free and y = 2/27 is reserved at N = 81, 729, 6561); every other y, N and t unchanged.
import hashlib
import os
import sys
from fractions import Fraction as Fr

JET_P_Y0 = 12
JET_P_Y = 10
JET_Q = 64
DT = 64
DT_EINT = 128
ANALOG_DELTA = {Fr(3, 5): Fr(1, 2), Fr(-3, 5): Fr(-1, 2)}
ANALOG_Y = {Fr(2, 27): Fr(1, 18)}
ROW_KEYS = ('N', 'delta', 'y', 's', 'family', 't', 'labels', 'f_law', 'tau', 'P', 'P_tol', 'M_VNC', 'M_V1',
            'first_order_range', 'applies', 'read_and_report', 'blind')


def fields(line):
    out = {}
    for part in line.rstrip('\n').split('|')[1:]:
        if '=' in part:
            k, v = part.split('=', 1)
            out[k] = v
    return out


def sha_file(path):
    with open(path, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def ftag(x):
    x = Fr(x)
    return '0' if x == 0 else str(x).replace('/', 'o').replace('-', 'm')


def rat(x):
    x = Fr(x)
    return str(x.numerator) if x.denominator == 1 else '%d/%d' % (x.numerator, x.denominator)


def main():
    out, pred, amend, bin_sha, src_sha, tools = sys.argv[1:7]
    with open(pred, 'rb') as fh:
        pdata = fh.read()
    with open(amend, 'rb') as fh:
        adata = fh.read()
    if b'\r' in pdata or b'\r' in adata:
        raise SystemExit('PLAN_FAIL|reason=CR_in_a_source|json=0')
    plines = pdata.decode('utf-8').split('\n')
    alines = adata.decode('utf-8').split('\n')
    amended = {}
    for ln in alines:
        if ln.startswith('BRIDGE_AMENDED_AT|'):
            f = fields(ln)
            amended[int(f['frozen_line'])] = f
    diag = []
    pairs = []
    rows = []
    n_at = 0
    for i, ln in enumerate(plines, start=1):
        if ln.startswith('BRIDGE_DIAGNOSTIC|'):
            f = fields(ln)
            if 'N_a' in f:
                diag.append((int(f['N_a']), int(f['N_b']), Fr(f['delta']), Fr(f['s']), Fr(f['t']), i))
        elif ln.startswith('BRIDGE_PAIR|'):
            f = fields(ln)
            pairs.append((int(f['N']), Fr(f['t']), Fr(f['y_plus']), Fr(f['y_minus']), int(f['pair']), i))
        elif ln.startswith('BRIDGE_AT|'):
            n_at += 1
            f = fields(ln)
            if f.get('first_order_range') == '1':
                rows.append((i, f))
    # every amended line is a first-order BRIDGE_AT row of the frozen file
    fo_lines = {i for i, _ in rows}
    for k in amended:
        if k not in fo_lines:
            raise SystemExit('PLAN_FAIL|reason=amended_line_not_first_order|line=%d|json=0' % k)
    jets = {}
    jrows = []
    for i, f in rows:
        N, d, y, t = int(f['N']), Fr(f['delta']), Fr(f['y']), Fr(f['t'])
        if (t * DT).denominator != 1:
            raise SystemExit('PLAN_FAIL|reason=t_off_the_1/64_grid|line=%d|json=0' % i)
        key = (d, y)
        jets.setdefault(key, {'rows': [], 'steps': {0}, 'ns': set()})
        jets[key]['rows'].append(i)
        jets[key]['steps'].add(int(t * DT))
        jets[key]['ns'].add(N)
        jrows.append((i, f))
    # launch order: the blind plan's point order (delta 3/5 then -3/5; y as the points list them)
    order = []
    for i, f in rows:
        key = (Fr(f['delta']), Fr(f['y']))
        if key not in order:
            order.append(key)
    launches = []
    lid = {}
    k = 0
    for (d, y) in order:
        j = jets[(d, y)]
        P = JET_P_Y0 if y == 0 else JET_P_Y
        ns = ','.join(str(n) for n in sorted(j['ns']))
        ad = ANALOG_DELTA[d]
        ay = ANALOG_Y.get(abs(y), abs(y)) * (1 if y >= 0 else -1)
        for dt in (DT, DT_EINT):
            k += 1
            steps = sorted(s * (dt // DT) for s in j['steps'])
            st = ','.join(str(s) for s in steps)
            role = 'jet' if dt == DT else 'e_int'
            ident = 'J-d%s-y%s-dt%d' % (rat(d), rat(y), dt)
            name = 'jet_d%s_y%s_dt%d_p%d.hbp' % (ftag(d), ftag(y), dt, P)
            aname = 'jet_d%s_y%s_dt%d_p%d.hbp' % (ftag(ad), ftag(ay), dt, P)
            argv = ['jet', 'delta=%s' % rat(d), 'y=%s' % rat(y), 'for_n=%s' % ns, 'p=%d' % P, 'q=%d' % JET_Q,
                    'dtden=%d' % dt, 'steps=%s' % st, 'lift_reserved_guard=1']
            aargv = ['jet', 'delta=%s' % rat(ad), 'y=%s' % rat(ay), 'for_n=%s' % ns, 'p=%d' % P, 'q=%d' % JET_Q,
                     'dtden=%d' % dt, 'steps=%s' % st]
            lid[(d, y, dt)] = ident
            launches.append('JET_LAUNCH|order=%d|id=%s|role=%s|engine=jetens_0.2.0|binary_sha256=%s|delta=%s|y=%s|p=%d|q=%d|dtden=%d|steps=%s|t_end=%s|for_n=%s|serves=%s|argv=%s|output=blind/jets/%s|reserved=1|analog_delta=%s|analog_y=%s|analog_argv=%s|analog_output=analog/jets/%s|json=0' % (
                k, ident, role, bin_sha, rat(d), rat(y), P, JET_Q, dt, st, rat(Fr(max(steps), dt)), ns,
                ','.join(str(r) for r in j['rows']), '~'.join(argv), name, rat(ad), rat(ay), '~'.join(aargv), aname))
    out_rows = []
    n_amended = 0
    for idx, (i, f) in enumerate(jrows, start=1):
        N, d, y, s, t = int(f['N']), Fr(f['delta']), Fr(f['y']), Fr(f['s']), Fr(f['t'])
        P = JET_P_Y0 if y == 0 else JET_P_Y
        clauses = [c for c in f['applies'].split(';') if c.startswith('E_')]
        rr = [c for c in f['read_and_report'].split(';') if c in ('E_V1',)]
        feeds = []
        for (na, nb, dd, ss, tt, li) in diag:
            if dd == d and ss == s and tt == t and N in (na, nb):
                feeds.append('D_9_81@L%d' % li)
        for (pn, pt, yp, ym, pid, li) in pairs:
            if pn == N and pt == t and ((d == Fr(3, 5) and y == yp) or (d == Fr(-3, 5) and y == ym)):
                feeds.append('P_PAIRS@L%d' % li)
        if i in amended:
            a = amended[i]
            if int(a['M_VNC_frozen']) != int(f['M_VNC']):
                raise SystemExit('PLAN_FAIL|reason=amendment_frozen_count_mismatch|line=%d|json=0' % i)
            m_vnc, src = int(a['M_VNC_amended']), 'AMENDMENT-2026-11-06-F-SAMPLING.hbp'
            n_amended += 1
        else:
            m_vnc, src = int(f['M_VNC']), 'PREDICTION.hbp'
        ad = ANALOG_DELTA[d]
        ay = ANALOG_Y.get(abs(y), abs(y)) * (1 if y >= 0 else -1)
        obs = 'C1,A1,V2,f,D2,ReZ_sign,pair' if y != 0 else 'C1,f,A1_zero,D2_zero,V2_printed,pair'
        gcons = ('G_CONS:conservation_exact_at_t=0_in_both_jets_and_its_drift_RK4\'s_dt^4'
                 '(dev_64/dev_128_in_[12,20]_above_2^10_units);G_PAIR:T_P(pair)<=abs(P)/100')
        gates = ('G_TRUNC:Trel_P<tau(N)_on_C1,A1,V2,f,D2;G_FALL:T_P<=T_(P-2);G_ODD:odd_orders_equal_the_even_below;'
                 + gcons) if y != 0 else (
                 'G_TRUNC:Trel_P<tau(N)_on_C1,f;G_ZERO:A1=D2=0_exactly;G_FALL:T_P<=T_(P-2);G_ODD:odd_orders_equal_the_even_below;'
                 + gcons)
        out_rows.append('JET_ROW|order=%d|frozen_line=%d|N=%d|delta=%s|y=%s|s=%s|family=%s|t=%s|step64=%d|step128=%d|labels=%s|f_law=%s|tau=%s|first_order_range=1|M_VNC_frozen=%s|M_VNC=%d|M_VNC_from=%s|M_V1=%s|P_closed=%s|P_tol=%s|clauses=%s|read_and_report=%s|feeds=%s|variants=VNC,V1|observables=%s|laws=engine(read),gauss(printed)|jet=%s|eint_jet=%s|P_read=%d|P_min_test=6(T1_ORDER_NEEDED:f_lead<=1/50)|gates=%s|status_rule=JET_READY_if_every_gate_passes,else_JET_NOT_RESOLVED(with_the_failing_gates)|output=blind/reads/L%04d.hbp|analog=N=%d,delta=%s,y=%s,t=%s|analog_output=analog/reads/L%04d.hbp|blind=%s|json=0' % (
            idx, i, N, rat(d), rat(y), rat(s), f['family'], rat(t), int(t * DT), int(t * DT_EINT), f['labels'], f['f_law'],
            f['tau'], f['M_VNC'], m_vnc, src, f['M_V1'], f.get('P', 'none'), f.get('P_tol', 'none'), ','.join(clauses) or 'none',
            ','.join(rr) or 'none', ','.join(feeds) or 'none', obs, lid[(d, y, DT)], lid[(d, y, DT_EINT)], P, gates, i, N,
            rat(ad), rat(ay), rat(t), i, f.get('blind', 'NA')))
    tool_sha = {}
    for nm in ('jetread.py', 'jetcmp.py', 'cf.py', 'drive_jets.py', 'plan_jets.py'):
        tool_sha[nm] = sha_file(os.path.join(tools, nm))
    head = ('PLAN_JETS_HEAD|plan=PLAN-JETS|kind=real|seat=ACER-CLAUDE-FABLE5|pid=8467a937cba309f7|owner=OP-JESSE|by=opus55_jet-plan-20261106|date=2026-11-06|'
            'decision=the_operator\'s_word_of_2026-11-06_item_1:the_ensemble_phase_runs_the_frozen_Monte_Carlo_as_planned_and_the_flow-map_jet_on_the_same_first-order_rows_beside_it,an_independent_second_answer_filed_by_hash_before_the_Monte_Carlo_runs|'
            'PREDICTION.hbp_sha256=%s|AMENDMENT_sha256=%s|engine=jetens_0.2.0(polariton-bridge/engines/jet)|binary_sha256=%s(rustc_1.81.0,x86_64-unknown-linux-gnu;a_binary_built_elsewhere_carries_its_own)|source_sha256=%s|'
            'reader=jetread.py_sha256=%s|jetcmp.py_sha256=%s(the_ensemble-skip_test\'s,unchanged)|cf.py_sha256=%s(the_ensemble_design_lane\'s,unchanged)|driver=drive_jets.py_sha256=%s|generator=plan_jets.py_sha256=%s|'
            'jet_order=P=%d_at_y=0,P=%d_at_y!=0(the_orders_of_the_test\'s_T1_AGREE:404_of_404_rows_at_f_law<=1/50_within_3SE_with_Trel_P<tau)|q=%d|dtden=%d(the_engine\'s_RK4_step),%d(the_jet\'s_e_int=2*abs(O(1/64)-O(1/128)))|'
            'analog=delta_3/5->1/2,-3/5->-1/2;y_2/27->1/18;N,t_unchanged|reserved_points_named=1|run_by_this_writer=0|argv_sep=~|order=after_the_frozen_rows_are_read,before_the_ensemble_phase\'s_Monte_Carlo|float_used=0|json=0') % (
        sha_file(pred), sha_file(amend), bin_sha, src_sha, tool_sha['jetread.py'], tool_sha['jetcmp.py'], tool_sha['cf.py'],
        tool_sha['drive_jets.py'], tool_sha['plan_jets.py'], JET_P_Y0, JET_P_Y, JET_Q, DT, DT_EINT)
    n_dt64 = sum(1 for L in launches if '|role=jet|' in L)
    served = {}
    for L in launches:
        g = fields(L)
        for r in g['serves'].split(','):
            served.setdefault(int(r), []).append((g['role'], int(g['dtden']), set(int(x) for x in g['steps'].split(','))))
    one_each = int(all(sorted(x[0] for x in served.get(i, [])) == ['e_int', 'jet'] for i, _ in jrows))
    cover = int(all(all(int(Fr(f['t']) * dt) in st for (_, dt, st) in served[i]) for i, f in jrows))
    n_res = sum(1 for L in launches if '|reserved=1|' in L)
    check = ('PLAN_JETS_CHECK|BRIDGE_AT_rows=%d|first_order_rows=%d|plan_rows=%d|amended_rows_in_the_plan=%d|BRIDGE_AMENDED_AT_rows=%d|'
             'jets=%d|e_int_jets=%d|launches=%d|every_row_served_by_one_jet_and_one_e_int_jet=%d|every_row_step_in_its_jets\'_steps=%d|'
             'reserved_launches=%d|d_9_81_rows_fed=%d|p_pairs_rows_fed=%d|json=0') % (
        n_at, len(rows), len(out_rows), n_amended, len(amended), n_dt64, len(launches) - n_dt64, len(launches), one_each,
        cover, n_res, sum(1 for r in out_rows if 'D_9_81@' in r), sum(1 for r in out_rows if 'P_PAIRS@' in r))
    body = [head] + launches + out_rows + [check, 'PLAN_JETS_END|launches=%d|rows=%d|line_endings=LF|float_used=0|json=0' % (
        len(launches), len(out_rows))]
    with open(out, 'w', newline='\n') as fh:
        fh.write('\n'.join(body) + '\n')
    print(check)


if __name__ == '__main__':
    main()
