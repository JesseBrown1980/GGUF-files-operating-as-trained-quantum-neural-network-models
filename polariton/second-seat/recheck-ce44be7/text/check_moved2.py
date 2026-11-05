# How far the pin and sector rows moved between the third run and this head, and the parity rows filed at 8dfa11a.
import sys
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
out = open(ME + 'out/check_moved2.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s); out.write(s + '\n')
T3 = load(WT + 'polariton/third-run/RECEIPT.hbp')
a = {(r['N'], r['u'], r['x'], r['y'], r['s']): r for r in T3['POLARITON_PIN']}
b = {(r['N'], r['u'], r['x'], r['y'], r['s']): r for r in R['POLARITON_PIN']}
fields = ['energy_ppb', 'A_ppb', 'B_ppb', 'A1_ppm', 'D2_ppm', 'C1_ppm', 'C2_ppm', 'f_ppm', 'residual_1e-12', 'cycles']
for f in fields:
    diffs = [(abs(int(a[k][f]) - int(b[k][f])), k) for k in a]
    m = max(diffs, key=lambda d: d[0])
    P(f, 'largest change', m[0], 'at', m[1], 'rows changed', sum(d[0] != 0 for d in diffs))
P('largest residual third', max(int(r['residual_1e-12']) for r in T3['POLARITON_PIN']), 'fourth', max(int(r['residual_1e-12']) for r in R['POLARITON_PIN']))
P('central rows N=243,729, A_ppb and B_ppb third vs fourth:')
for n in ('243', '729'):
    for s in ('0', '1/2', '1', '2', '4', '8', '16'):
        k = [k for k in a if k[0] == n and k[1] == '1/2' and k[2] == '0' and k[4] == s][0]
        P(' ', n, s, a[k]['A_ppb'], b[k]['A_ppb'], a[k]['B_ppb'], b[k]['B_ppb'], a[k]['D2_ppm'], b[k]['D2_ppm'], a[k]['residual_1e-12'], b[k]['residual_1e-12'])
c = {(r['N'], r['u'], r['x'], r['P']): r for r in T3['POLARITON_SECTOR']}
d = {(r['N'], r['u'], r['x'], r['P']): r for r in R['POLARITON_SECTOR']}
for f in ('e_ppb', 'f_ppb', 'jbar_ppb', 'gap_ppb', 'C2_ppm', 'C1_ppm', 'C1_times_N_ppm', 'N2_times_e_above_P0_ppm'):
    diffs = [(abs(int(c[k][f]) - int(d[k][f])), k) for k in c if f in c[k] and f in d[k]]
    m = max(diffs, key=lambda z: z[0])
    P('sector', f, 'largest change', m[0], 'at', m[1], 'rows changed', sum(z[0] != 0 for z in diffs))
P()
P('parity rows at 8dfa11a')
for name in ('parity_729.hbp',):
    rows = load(WT + 'polariton/second-seat/engine/out/' + name)
    for t, rs in rows.items():
        P(t, len(rs))
        for r in rs:
            P(' ', r['_raw'][:260])
pb = load(WT + 'polariton/second-seat/engine/out/parity_243.hbp')
for t, rs in pb.items():
    P(t, len(rs))
    for r in rs:
        if eq(r.get('u', '0'), '1/2') and eq(r.get('x', '1'), '0') and r.get('s') == '16':
            P(' ', r['_raw'][:260])
pi = load(WT + 'polariton/second-seat/engine/out/parity_inertia.hbp')
for t, rs in pi.items():
    P(t, len(rs), 'by N', {n: sum(r.get('N') == n for r in rs) for n in sorted({r.get('N') for r in rs}, key=str)}, 'ground_is_even', {v: sum(r.get('ground_is_even') == v for r in rs) for v in {r.get('ground_is_even') for r in rs}})
ps = load(WT + 'polariton/second-seat/engine/out/parity_small.hbp')
for t, rs in ps.items():
    P(t, len(rs), 'by N', {n: sum(r.get('N') == n for r in rs) for n in sorted({r.get('N') for r in rs}, key=str)})
    P(rs[0]['_raw'][:260])
out.close()
