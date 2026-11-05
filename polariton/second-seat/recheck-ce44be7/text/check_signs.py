# Frozen statements of rows 37-39 beyond what the reader reads; TIMING 'whole' rows; miscellaneous counts for the text.
import sys
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
out = open(ME + 'out/check_signs.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s); out.write(s + '\n')
Q = R['POLARITON_QUENCH_CONVERSION']
bad_a = [r for r in Q if int(r['A_ppb']) >= 0]
bad_b = [r for r in Q if int(r['B_ppb']) <= 0]
P('conversion rows', len(Q), 'A>=0', [(r['N'], r['delta'], r['s'], r['t'], r['A_ppb'], r['f_ppb']) for r in bad_a], 'B<=0', [(r['N'], r['delta'], r['s'], r['t'], r['B_ppb']) for r in bad_b])
WB = [r for r in R['POLARITON_PIN_WINDOW'] if (r['u'], r['x']) in (('1', '-1/4'), ('1', '-1/8'), ('1/2', '-1/4'), ('3/4', '-1/8'))]
for r in WB:
    if int(r['N']) >= 243 and F(r['s']) > 0 and F(r['s']) < 4:
        sign = 1 if F(r['u']) - F(r['x']) - 1 > 0 else -1
        if int(r['B_ppb']) * sign <= 0:
            P(' below sign fails s<4', r['N'], r['u'], r['x'], r['s'], r['B_ppb'])
P('below s<4 sign rows checked')
# D2/y^2 at s<4 below the edge, unread by tolerance
for (u, x) in (('1', '-1/4'), ('1/2', '-1/4')):
    for s in ('1/2', '1', '2', '4', '8', '16'):
        r = win(729, u, x, s)
        y = F(s) / 729
        P(' ', u, x, 'N=729 s', s, 'D2/y2', dec(F(2 * abs(int(r['B_ppb'])), 729 * 10 ** 9) / y ** 2, 4), 'B', r['B_ppb'], 'A1/y', dec(F(2 * abs(int(r['A_ppb'])), 729 * 10 ** 9) / y, 4), 'P2', r['P2_over_N2_ppm'], 'res', r['residual_1e-12'])
P()
for name, path in (('third', WT + 'polariton/third-run/TIMING-LOCAL-20261104.hbp'), ('fourth', WT + 'polariton/TIMING-LOCAL-20261104.hbp')):
    d = load(path)
    wh = [(r['stage'], int(r['ms'])) for r in d['TIMING'] if r['_raw'].split('|')[1] == 'whole']
    P(name, 'whole rows', wh, 'sum minutes', dec(F(sum(v for _, v in wh), 60000), 1))
P()
P('READ rows by kind that are existence or construction checks')
read = load(WT + 'polariton/READ.hbp')['POLARITON_READ']
P(' rows_* count checks', sum(r['row'].startswith('rows_') for r in read), 'hand_rows', sum(r['row'] == 'hand_rows' for r in read))
P(' energy rows (conversion + quench)', sum(r['row'].startswith(('energy_', 'conversion_energy')) for r in read))
P(' zero-A rows at y=0', sum(r['row'].startswith('quench_pin_zero_A') for r in read), 'sign rows', sum('_negative_' in r['row'] or '_positive_' in r['row'] or 'sign' in r['row'] for r in read))
P()
P('== the 26 rows, exact, with the 1.07')
z = pin(3, '0', '0', '0'); s_ = sec(3, '0', '0')
P(' N=3 u=0: energy_ppb', z['energy_ppb'], 'N e', dec(3 * F(int(s_['e_at_2^60']), 1 << 60), 12), 'diff ppb', dec((F(int(z['energy_ppb']), 10 ** 9) - 3 * F(int(s_['e_at_2^60']), 1 << 60)) * 10 ** 9, 3))
P()
P('== the 0.92 and the 0.95 at yN=1/2, N=729')
r = pin(729, '1/2', '0', '1/2')
d2b = F(2 * abs(int(r['B_ppb'])), 729 * 10 ** 9)
pred = F(2, 5) * mathieu_f(F(1, 50))
P(' D2 from B', dec(d2b, 8), 'D2_ppm', r['D2_ppm'], '2 rho f', dec(pred, 8), 'shortfall %', dec((1 - d2b / pred) * 100, 3), 'from the printed six digits', dec((1 - F(3962, 10 ** 6) / F(4000, 10 ** 6)) * 100, 3), '6.72/729 %', dec(F(672, 100) / 729 * 100, 3))
for s in ('1/2','1','2','4','8','16'):
    r = pin(729, '1/2', '0', s)
    d2b = F(2 * abs(int(r['B_ppb'])), 729 * 10 ** 9)
    q = F(2, 25) * F(s) ** 2
    pred = F(2, 5) * mathieu_f(q)
    P('  s', s, 'shortfall %', dec((1 - d2b / pred) * 100, 3), 'range check D2 within', 'off', dec(abs(1 - d2b / pred) * 100, 3))
P()
P('== A1/y, D2 at N=243 within their tolerances: how close')
FQ = {'1/2': 9999, '1': 39944, '2': 156537, '4': 490857, '8': 776331, '16': 889412}
for n in (243, 729):
    o = []
    for s, f in FQ.items():
        r = pin(n, '1/2', '0', s)
        d2b = F(2 * abs(int(r['B_ppb'])), n * 10 ** 9)
        o.append(dec(d2b / (F(2, 5) * F(f, 10 ** 6)), 4))
    P(' N', n, 'D2 ratio', o)
P()
P('== window inside: lowest ratio against the frozen tolerance')
FROZEN = {('1/4', '-1/4'): (31223, 123327, 417999, 744149, 874846, 937483), ('1/4', '0'): (7199, 28779, 113886, 394162, 732112, 869614), ('3/4', '0'): (5190, 20753, 82548, 304289, 675100, 846304), ('3/4', '1/8'): (740, 2962, 11850, 47314, 183943, 539654), ('1/2', '1/4'): (1111, 4444, 17772, 70798, 266308, 642446)}
SIX = ('1/2', '1', '2', '4', '8', '16')
low = {}
for (u, x), t in FROZEN.items():
    uu, xx = F(u), F(x)
    rho = (1 - uu - xx) / (4 - 3 * uu)
    for n in (243, 729):
        for s, f in zip(SIX, t):
            r = win(n, u, x, s)
            if r is None: continue
            d = F(2 * abs(int(r['B_ppb'])), n * 10 ** 9) / (2 * rho * F(f, 10 ** 6))
            low.setdefault(n, []).append((d, u, x, s))
for n, v in low.items():
    v.sort(key=lambda a: a[0])
    P(' N', n, 'rows', len(v), 'lowest', [(dec(a[0], 4),) + a[1:] for a in v[:4]], 'highest', [(dec(a[0], 4),) + a[1:] for a in v[-2:]])
out.close()
