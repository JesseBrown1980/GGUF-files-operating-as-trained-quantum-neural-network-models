# The quench section, What missed, How the engine got here: polariton/README.md lines 131-163.
import sys, re
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
out = open(ME + 'out/check_e.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s); out.write(s + '\n')

Q = R['POLARITON_QUENCH']
Ns = sorted({int(r['N']) for r in Q})
P('quench Ns', Ns, 'rows', len(Q), 'dt', sorted({r['dt'] for r in Q}), 'delta', sorted({r['delta'] for r in Q}), 't', sorted({r['t'] for r in Q}))
P('== band table')
B = R['POLARITON_QUENCH_BAND']
claim = {'-2': '0.0001', '-1': '0.0069', '-1/2': '0.2117', '0': '0.3842', '1/2': '0.6500', '1': '0.0154', '2': '0.0001'}
for r in B:
    if r['N'] == '6561':
        v = F(int(r['largest_f_ppm']), 10 ** 6)
        P(' delta', r['delta'], r['largest_f_ppm'], dec(v, 4), claim[r['delta']], 'OK' if dec(v, 4) == claim[r['delta']] else 'MISMATCH')
P('== reversal')
for r in R['POLARITON_REVERSAL']:
    P(' ', r['_raw'])
P('== pin in the quench line 139')
for r in R['POLARITON_QUENCH_PIN']:
    if r['N'] == '729' and eq(r['delta'], '0') and r['t'] == '1':
        P(' ', r['y'], 'A1_ppm', r['A1_ppm'], 'pred', r['predicted_A1_ppm'], 'A_ppb', r['A_ppb'])
P('closed', dec(4 * F(1, 1024) * (series(1)[1] - 1), 6))
P('== the sign rows inside the band: A negative at y>0')
ins = [r for r in R['POLARITON_QUENCH_PIN'] if F(r['y']) > 0 and abs(F(r['delta'])) < 1]
P(' rows', len(ins), 'A<0', sum(int(r['A_ppb']) < 0 for r in ins), 'delta', sorted({r['delta'] for r in ins}))
P(' at delta=1:', [(r['N'], r['t'], r['A_ppb'], r['A1_ppm']) for r in R['POLARITON_QUENCH_PIN'] if F(r['y']) > 0 and eq(r['delta'], '1')])
P('== wavevector')
for r in R['POLARITON_WAVEVECTOR']:
    P(' ', r['_raw'])
P('== C1 after a quench line 138: C1 vs 4(1-delta)jbar/N on rows N>=6561, jbar<=N/100')
P(' checked below under what missed')
read = load(WT + 'polariton/READ.hbp')['POLARITON_READ']
miss = [r for r in read if r['result'] == 'MISS']
P('== misses', len(miss))
for r in miss:
    P(' ', r['row'], r['read'], r['predicted'])

P('== miss row 1: pair count')
def closed_jbar(delta, t):
    t = F(t)
    shc, ch = series((1 - F(delta) ** 2) * t * t)
    return shc ** 2 * t * t
def row_q(n, d, t):
    return [r for r in Q if int(r['N']) == n and eq(r['delta'], d) and int(r['t']) == int(t)][0]
for n, d, t in ((6561, '-1', 8), (6561, '1', 8)):
    r = row_q(n, d, t)
    ratio = F(int(r['jbar_ppb']), 10 ** 9) / closed_jbar(F(d), t)
    P(' N', n, 'delta', d, 't', t, 'ratio', dec(ratio, 4), 'ppm col', r['ratio_ppm'], 'jbar/N ppm', r['jbar_over_N_ppm'], 'f =2jbar/N', dec(2 * F(int(r['jbar_ppb']), 10 ** 9) / n, 5))
for n in (2187, 6561, 19683):
    r = row_q(n, '1', 4)
    ratio = F(int(r['jbar_ppb']), 10 ** 9) / closed_jbar(F(1), 4)
    P(' delta=1 t=4 N', n, 'deviation %', dec((1 - ratio) * 100, 3), 'N*dev', dec((1 - ratio) * n, 1), 'form', dec(F(1) + (3 - 1) * 16 + F(2, 5) * (4 - 3) * 256, 2))
P(' band-edge deviation coefficient at t^4: delta=1,u=1', F(2, 5) * (4 - 3), ' delta=-1,u=1', F(2, 5) * (4 + 3))
P('== all 12 rows: (read - (J0+J1/N))/J0 over (J1/(N J0))^2, using the J1 closed form')

def J1(delta, u, t):
    d, u = F(delta), F(u)
    t = F(t)
    g2 = 1 - d * d
    if g2 == 0:
        s = 1 if d > 0 else -1
        return -(t ** 2 + (3 - s * u) * t ** 4 + F(2, 5) * (4 - s * 3 * u) * t ** 6)
    # sinh^2(2 g t), g t sinh(2 g t), sinh^2(g t) as functions of (g t)^2, also valid for g2<0
    z2 = g2 * t * t
    shc, ch = series(z2)         # sinh(z)/z, cosh z
    sinh2z = shc ** 2 * z2
    shc2, ch2 = series(4 * z2)   # sinh(2z)/(2z), cosh 2z
    sinh22 = shc2 ** 2 * 4 * z2
    g_t_sinh2 = shc2 * 2 * z2    # z sinh 2z = 2 z^2 shc2
    return (-(4 - 3 * d * u) * sinh22 / 4 + F(3, 2) * (1 + 3 * d * d - d * u * (2 + d * d)) * g_t_sinh2 + d * (3 * u * (1 + d * d) - d * (7 + d * d)) * sinh2z) / g2 ** 3

vals = []
for r in miss:
    m = re.match(r'quench_jbar_N=(\d+)_delta=([-\d/]+)_t=(\d+)', r['row'])
    if not m:
        continue
    n, d, t = int(m.group(1)), m.group(2), int(m.group(3))
    rr = row_q(n, d, t)
    j0 = closed_jbar(F(d), t)
    j1 = J1(d, 1, t)
    read_j = F(int(rr['jbar_ppb']), 10 ** 9)
    first = j1 / (n * j0)
    rest = read_j / j0 - 1 - first
    vals.append((abs(rest) / first ** 2, n, d, t, dec(read_j / j0, 4), dec(first, 4)))
    P(' N', n, 'delta', d, 't', t, 'read/J0', dec(read_j / j0, 4), 'first order', dec(first, 4), 'residual/first^2', dec(abs(rest) / first ** 2, 3), 'signed', dec(rest / first ** 2, 3), 'jbar/N', rr['jbar_over_N_ppm'])
P(' range', dec(min(v[0] for v in vals), 3), dec(max(v[0] for v in vals), 3), 'claim 0.35 to 1.37')

P('== miss row 2: phase')
for r in miss:
    if r['row'].startswith('quench_phase'):
        m = re.match(r'quench_phase_N=(\d+)_delta=([-\d/]+)_t=(\d+)', r['row'])
        n, d, t = int(m.group(1)), m.group(2), int(m.group(3))
        rr = row_q(n, d, t)
        j = F(int(rr['jbar_ppb']), 10 ** 9)
        form = -F(d) + 3 * (j + F(1, 2)) / n
        rd = F(int(rr['re_P_over_N_jbar_ppm']), 10 ** 6)
        P(' N', n, 'delta', d, 't', t, 'read', dec(rd, 4), 'gaussian form', dec(form, 4), 'off from -delta', dec(rd + F(d), 4), 'rel off', dec(abs(rd + F(d)) / max(abs(F(d)), F(1, 50)) * 100, 1) + '%', 'rows pred', r['predicted'])
P('== all phase rows read at delta=0: largest')
rows0 = [r for r in read if r['row'].startswith('quench_phase') and '_delta=0_' in r['row']]
P(' count', len(rows0), 'miss', sum(r['result'] == 'MISS' for r in rows0), 'read', [(r['row'][13:], r['read'], r['result']) for r in rows0])
P('== miss row 3: pinned A1')
for r in miss:
    if r['row'].startswith('quench_pin_A1'):
        P(' ', r['row'], r['read'], r['predicted'])
P('delta=0 t=3 N=729 rows:')
for r in R['POLARITON_QUENCH_PIN']:
    if r['N'] == '729' and eq(r['delta'], '0') and r['t'] == '3' and F(r['y']) > 0:
        j = F(int(r['jbar_ppb']), 10 ** 9)
        P(' A1_ppm', r['A1_ppm'], 'pred', r['predicted_A1_ppm'], 'jbar/N ppm', r['jbar_over_N_ppm'], 'f', dec(2 * j / 729, 4), 'closed f', dec(2 * closed_jbar(F(0), 3) / 729, 4), 'ratio', r['ratio_ppm'])
P('w1 form at delta=0,u=1: read over 2|y||w0+w1/N|, N=729 and 243')
def w(t, n):
    t = F(t)
    s1, c1 = series(t * t); s2, c2 = series(4 * t * t); s3, c3 = series(9 * t * t)
    sinh_t = s1 * t
    w0 = -2 * (c1 - 1)
    w1 = -t * sinh_t + F(65, 12) * c1 - F(11, 3) * c2 + F(5, 4) * c3 - 3
    return w0 + w1 / n
for n in (243, 729):
    line = []
    for t in (1, 2, 3):
        r = [z for z in R['POLARITON_QUENCH_PIN'] if int(z['N']) == n and eq(z['delta'], '0') and int(z['t']) == t and F(z['y']) > 0][0]
        y = F(r['y'])
        a1 = F(2 * abs(int(r['A_ppb'])), n * 10 ** 9)
        form = 2 * abs(y) * abs(w(t, n))
        line.append((t, dec(a1 / form, 4), 'A1_ppm over form', dec(F(int(r['A1_ppm']), 10 ** 6) / form, 4)))
    P(' N', n, line)
P('A1 hits: pattern by t, N, delta')
for r in read:
    if r['row'].startswith('quench_pin_A1'):
        P(' ', r['row'][14:], r['result'], r['read'], r['predicted'])
P('== 12 C1 rows at delta=1 held out')
rows_d1 = [r for r in Q if int(r['N']) >= 6561 and int(r['jbar_over_N_ppm']) <= 10000 and eq(r['delta'], '1') and F(int(r['jbar_ppb']), 10 ** 9) > F(1, 100)]
P(' rows', len(rows_d1), 'largest |C1_ppm|', max(abs(int(r['C1_ppm'])) for r in rows_d1), [(r['N'], r['t'], r['C1_ppm']) for r in rows_d1])
P('== constant A1/y = 2.29 against the 12 pinned A1 rows')
FQ = {'1/2': 9999, '1': 39944, '2': 156537, '4': 490857, '8': 776331, '16': 889412}
ok = 0
for s, f in FQ.items():
    want = 2 * (1 + (1 + F(f, 10 ** 6)) / 10)
    good = abs(F(229, 100) - want) <= want * F(5, 100)
    ok += 2 * good
P(' pass count', ok, 'of 12')
P('== miss row 4 in check_b; miss row 5 in check_c')
P()
P('== engine record: first and third')
first = load(WT + 'polariton/first-run/READ.hbp')
third = load(WT + 'polariton/third-run/READ.hbp')
for name, d in (('first', first), ('third', third)):
    rs = d['POLARITON_READ']
    P(name, 'rows', len(rs), 'met', sum(r['result'] == 'MET' for r in rs), 'miss', sum(r['result'] == 'MISS' for r in rs), 'DONE', d['POLARITON_READ_DONE'][0]['_raw'])
fm = {r['row']: r['result'] for r in first['POLARITON_READ']}
tm = {r['row']: r['result'] for r in third['POLARITON_READ']}
flip = [k for k in fm if k in tm and fm[k] != tm[k]]
P(' rows that flip first->third', len(flip), 'only in first', len(set(fm) - set(tm)), 'only in third', len(set(tm) - set(fm)))
from collections import Counter
P(' families', Counter(k.split('_N=')[0] for k in flip), 'directions', Counter(fm[k] + '>' + tm[k] for k in flip))
P()
RF = load(WT + 'polariton/first-run/RECEIPT.hbp')
zr = [r for r in RF['POLARITON_SECTOR'] if r['P'] == '0' and int(r['e_ppb']) == 0]
P(' first-run rows with e_ppb=0 at P=0', len(zr), 'by delta class', Counter('disordered' if F(r['u']) + F(r['x']) > 1 else 'critical' if F(r['u']) + F(r['x']) == 1 else 'ordered' for r in zr))
zr2 = [r for r in RF['POLARITON_SECTOR'] if r['P'] == '0' and int(r['e_at_2^60']) == 0]
P(' first-run rows with e_at_2^60=0 at P=0', len(zr2), 'smallest N', min(int(r['N']) for r in zr2))
ROUTE1 = load(WT + 'polariton/first-run/ROUTE-SECTOR.hbp')
bad = []
for r in ROUTE1['SECOND_ROUTE_SECTOR']:
    e = F(r['exact_e']); rr = F(r['rust_e'])
    bad.append((abs(e - rr), r['N'], r['u'], r['x'], r['P']))
bad.sort(key=lambda a: -a[0])
P(' first-run route: largest off', dec(bad[0][0], 6), bad[0][1:], 'second', dec(bad[1][0], 6), bad[1][1:], 'rows off>=1e-9', sum(b[0] >= F(1, 10 ** 9) for b in bad), 'rows total', len(bad))
P(' first run route done', ROUTE1['SECOND_ROUTE_SECTOR_DONE'][0]['_raw'])
P()
fx = load(WT + 'polariton/second-seat/text/fix1only/route1.txt')
fxr = fx.get('SECOND_ROUTE_SECTOR', [])
P(' fix1only route rows', len(fxr), fx.get('SECOND_ROUTE_SECTOR_DONE', [{}])[0].get('_raw'))
if fxr:
    offs = sorted(abs(F(r['exact_e']) - F(r['rust_e'])) for r in fxr)
    units = sorted(int(r['off_units_of_2^-60']) for r in fxr)
    P(' fix1only: max off', dec(offs[-1], 15), 'median', dec(offs[len(offs) // 2], 15), 'rows outside 4096 units', sum(u > 4096 for u in units), 'of', len(units))
read1 = load(WT + 'polariton/second-seat/text/fix1only/read1.hbp')
P(' read1 DONE', read1['POLARITON_READ_DONE'][0]['_raw'])
fm1 = {r['row']: r['result'] for r in read1['POLARITON_READ']}
P(' read1 vs third-run: rows differ', sum(fm1.get(k) != tm[k] for k in tm), 'rows only in one', len(set(fm1) ^ set(tm)))
P(' third-run route', load(WT + 'polariton/third-run/SECOND-ROUTE.hbp')['SECOND_ROUTE_SECTOR_DONE'][0]['_raw'])
# fourth vs third on the rows both read
now = {r['row']: r['result'] for r in read}
common = set(now) & set(tm)
P(' fourth vs third: common rows', len(common), 'flips', [k for k in common if now[k] != tm[k]][:12], 'count', sum(now[k] != tm[k] for k in common), 'new rows in fourth', len(set(now) - set(tm)), 'rows dropped', sorted(set(tm) - set(now))[:12], len(set(tm) - set(now)))
new = [k for k in set(now) - set(tm)]
from collections import Counter as C2
P(' new row families', sorted(C2(re.match(r'(.*?)(_?N=|_u=|_delta=|_t=|$)', k).group(1) for k in new).items()))
P(' new rows met/miss', sum(now[k] == 'MET' for k in new), sum(now[k] == 'MISS' for k in new))
out.close()
