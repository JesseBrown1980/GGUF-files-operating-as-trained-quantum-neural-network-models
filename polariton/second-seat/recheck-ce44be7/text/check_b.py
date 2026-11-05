# The contact section: polariton/README.md lines 48-74, the root README and the PR body's law rows.
import sys
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
out = open(ME + 'out/check_b.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s); out.write(s + '\n')

Q = R['POLARITON_QUENCH_CONVERSION']
P('rows', len(Q), 'by N', {n: sum(int(r['N']) == n for r in Q) for n in sorted({int(r['N']) for r in Q})})
for n in sorted({int(r['N']) for r in Q}):
    rs = [r for r in Q if int(r['N']) == n]
    ys = sorted({F(r['y']) for r in rs})
    P(' N', n, 'y', [str(v) for v in ys], 's', sorted({r['s'] for r in rs}), 'delta', sorted({r['delta'] for r in rs}), 't', sorted({r['t'] for r in rs}), 'y*sqrtN', [dec(v * root(n), 5) for v in ys])

# The table lines 59-68
TAB = [
 ('0','1/4',('0.02604','0.02600','0.06814','0.06760','0.09457','0.09290')),
 ('0','1/2',('0.09667','0.09647','0.22805','0.22481','0.30552','0.29060')),
 ('0','1',('0.30032','0.29928','0.55140','0.53705','0.68060','0.62101')),
 ('0','2',('0.63444','0.63078','0.85066','0.82270','0.93713','0.86763')),
 ('0','4',('0.87872','0.87235','0.97334','0.94888','0.99410','0.96326')),
 ('1/2','1/4',('0.01367','0.01367','0.03906','0.03916','0.05761','0.05824')),
 ('1/2','1/2',('0.05256','0.05253','0.14054','0.14018','0.20072','0.19832')),
 ('1/2','1',('0.18192','0.18152','0.40086','0.39472','0.52650','0.49737')),
 ('1/2','2',('0.47278','0.47008','0.74486','0.72287','0.86093','0.79831')),
 ('1/2','4',('0.78754','0.78014','0.94056','0.91254','0.98240','0.94059')),
]
P()
P('== table: at N = 729, cell by cell (read, law, ratio, predicted f)')
bad = 0
for d, s, cells in TAB:
    for i, t in enumerate((1, 2, 3)):
        r = conv(729, d, s, t)
        a1, d2, c1, v2 = read_conv(r)
        L = Law(729, r['y'], d, t)
        rc, lc = cells[2 * i], cells[2 * i + 1]
        ok = dec(v2, 5) == rc and dec(L.v2, 5) == lc
        if not ok: bad += 1
        P('delta', d, 's', s, 't', t, 'y', r['y'], 'read', dec(v2, 5), rc, 'law', dec(L.v2, 5), lc, 'ratio', dec(v2 / L.v2, 4), 'f_pred', dec(L.f, 4), 'f_read', dec(F(int(r['f_ppb']), 10**9), 4), 'OK' if ok else 'MISMATCH')
P('table cell mismatches', bad)

P()
P('== tolerance read at N>=243, by my own law')
v_rows, a_rows = [], []
for r in Q:
    n = int(r['N'])
    if n < 243: continue
    L = Law(n, r['y'], r['delta'], r['t'])
    a1, d2, c1, v2 = read_conv(r)
    rec = dict(r=r, L=L, a1=a1, d2=d2, c1=c1, v2=v2)
    if L.f <= F(1, 10): v_rows.append(rec)
    if L.f <= F(1, 20): a_rows.append(rec)
P('rows f<=1/10', len(v_rows), 'rows f<=1/20', len(a_rows))
rat = [x['v2'] / x['L'].v2 for x in v_rows]
P('V2 ratio range', dec(min(rat), 4), dec(max(rat), 4), 'all within 5%:', all(abs(q - 1) <= F(5, 100) for q in rat), 'largest |off|', dec(max(abs(q - 1) for q in rat) * 100, 3), '%')
for x, q in sorted(zip(v_rows, rat), key=lambda p: p[1]):
    if q == min(rat) or q == max(rat):
        r = x['r']; P('  extreme', r['N'], r['delta'], r['s'], r['t'], dec(q, 5), 'law', dec(x['L'].v2, 5), 'read', dec(x['v2'], 5), 'f_pred', dec(x['L'].f, 4))
P('A1 within 5%', sum(abs(x['a1'] / x['L'].a1 - 1) <= F(5, 100) for x in a_rows), 'of', len(a_rows), 'range', dec(min(x['a1'] / x['L'].a1 for x in a_rows), 4), dec(max(x['a1'] / x['L'].a1 for x in a_rows), 4))
P('D2 within 10%', sum(abs(x['d2'] / x['L'].d2 - 1) <= F(10, 100) for x in a_rows), 'of', len(a_rows), 'range', dec(min(x['d2'] / x['L'].d2 for x in a_rows), 4), dec(max(x['d2'] / x['L'].d2 for x in a_rows), 4))
P('C1 within 5%', sum(abs(x['c1'] / x['L'].c1 - 1) <= F(5, 100) for x in a_rows), 'of', len(a_rows), 'range', dec(min(x['c1'] / x['L'].c1 for x in a_rows), 4), dec(max(x['c1'] / x['L'].c1 for x in a_rows), 4))
for x in a_rows:
    q = x['c1'] / x['L'].c1
    if abs(q - 1) > F(5, 100):
        r = x['r']
        P('  C1 miss N', r['N'], 'delta', r['delta'], 's', r['s'], 'y', r['y'], 't', r['t'], 'read', dec(x['c1'], 4), 'form', dec(x['L'].c1, 4), 'ratio', dec(q, 4), 'off%', dec((1 - q) * 100, 2), 'A1 ratio', dec(x['a1'] / x['L'].a1, 4), 'D2 ratio', dec(x['d2'] / x['L'].d2, 4), 'y*sqrtN', dec(F(r['y']) * root(int(r['N'])), 4), 'f_pred', dec(x['L'].f, 4))
signs = sum(int(x['r']['A_ppb']) < 0 for x in v_rows) + sum(int(x['r']['B_ppb']) > 0 for x in v_rows)
P('signs', signs, 'of', 2 * len(v_rows))
P('energy max |off|', max(abs(int(r['energy_off_1e-9'])) for r in Q), 'on', len(Q), 'rows; at', max(Q, key=lambda r: abs(int(r['energy_off_1e-9'])))['_raw'][:100])
P('N=729 rows among V2 29', sum(int(x['r']['N']) == 729 for x in v_rows), 'N=243', sum(int(x['r']['N']) == 243 for x in v_rows), 'N=2187', sum(int(x['r']['N']) == 2187 for x in v_rows))
P('the same counts at f<=1/20:', 'N=729', sum(int(x['r']['N']) == 729 for x in a_rows), 'N=243', sum(int(x['r']['N']) == 243 for x in a_rows), 'N=2187', sum(int(x['r']['N']) == 2187 for x in a_rows))
in_table = [x for x in v_rows if int(x['r']['N']) == 729]
tot_cells = 30
P('of the 30 table cells at N=729:', len(in_table), 'are in the frozen V2 range; ratio over all 30 cells:')
all30 = []
for d, s, cells in TAB:
    for t in (1, 2, 3):
        r = conv(729, d, s, t)
        a1, d2, c1, v2 = read_conv(r)
        L = Law(729, r['y'], d, t)
        all30.append((v2 / L.v2, d, s, t, L.f))
P('  min', dec(min(a[0] for a in all30), 4), 'max', dec(max(a[0] for a in all30), 4), 'at', [(a[1], a[2], a[3], dec(a[4], 3)) for a in all30 if a[0] == max(b[0] for b in all30)])
P('  cells off by more than 2.7%:', sum(abs(a[0] - 1) > F(27, 1000) for a in all30))

P()
P('== the approach line 71')
for n, s in ((81, '1/2'), (243, '1/2'), (729, '1/2'), (2187, '1/2')):
    r = conv(n, '0', s, 2)
    a1, d2, c1, v2 = read_conv(r)
    L = Law(n, r['y'], '0', 2)
    P('N', n, 'y', r['y'], 'y*sqrtN', dec(F(r['y']) * root(n), 4), 'V2', dec(v2 / L.v2, 4), 'A1', dec(a1 / L.a1, 4), 'C1', dec(c1 / L.c1, 4), 'D2', dec(d2 / L.d2, 4))
seq = {}
for n in (81, 243, 729, 2187):
    r = conv(n, '0', '1/2', 2)
    a1, d2, c1, v2 = read_conv(r)
    L = Law(n, r['y'], '0', 2)
    seq[n] = (abs(v2 / L.v2 - 1), abs(a1 / L.a1 - 1), abs(c1 / L.c1 - 1))
for a, b in ((81, 243), (243, 729), (729, 2187)):
    P(' deviation over one tripling', a, b, [dec(seq[a][i] / seq[b][i], 3) for i in range(3)], ' N*dev at', a, [dec(seq[a][i] * a, 2) for i in range(3)])
P(' N*dev at 2187', [dec(seq[2187][i] * 2187, 2) for i in range(3)])

P()
P('== past the depletion line 72')
hi = []
for r in Q:
    n = int(r['N'])
    if n < 243: continue
    L = Law(n, r['y'], r['delta'], r['t'])
    if L.f > F(1, 10):
        a1, d2, c1, v2 = read_conv(r)
        hi.append(dict(r=r, L=L, a1=a1, c1=c1, v2=v2, d2=d2))
P('rows', len(hi), 'V2 ratio', dec(min(x['v2'] / x['L'].v2 for x in hi), 4), dec(max(x['v2'] / x['L'].v2 for x in hi), 4), 'A1 ratio min', dec(min(x['a1'] / x['L'].a1 for x in hi), 4), 'max', dec(max(x['a1'] / x['L'].a1 for x in hi), 4), 'C1 ratio min', dec(min(x['c1'] / x['L'].c1 for x in hi), 5), 'max', dec(max(x['c1'] / x['L'].c1 for x in hi), 5))
for x in sorted(hi, key=lambda x: x['v2'] / x['L'].v2):
    r = x['r']
    P('  N', r['N'], 'd', r['delta'], 's', r['s'], 't', r['t'], 'f_pred', dec(x['L'].f, 3), 'f_read', dec(F(int(r['f_ppb']), 10**9), 3), 'Y', dec(x['L'].Y, 3), 'law', dec(x['L'].v2, 4), 'read', dec(x['v2'], 4), 'ratio', dec(x['v2'] / x['L'].v2, 4), 'A1r', dec(x['a1'] / x['L'].a1, 3), 'C1r', dec(x['c1'] / x['L'].c1, 4))
P('rows with law V2 >= 0.8:', sum(x['L'].v2 >= F(4, 5) for x in hi), 'law V2 >= 0.5:', sum(x['L'].v2 >= F(1, 2) for x in hi), 'of', len(hi))
lo = [x for x in hi if x['L'].v2 < F(1, 2)]
P('rows with law V2 < 0.5: ratio range', dec(min(x['v2'] / x['L'].v2 for x in lo), 4), dec(max(x['v2'] / x['L'].v2 for x in lo), 4))
P('N=81 spread:')
n81 = []
for r in Q:
    if int(r['N']) != 81: continue
    L = Law(81, r['y'], r['delta'], r['t'])
    a1, d2, c1, v2 = read_conv(r)
    n81.append((v2 / L.v2, r['delta'], r['s'], r['t'], dec(F(int(r['f_ppb']), 10**9), 4), dec(v2, 4), dec(L.v2, 4), dec(L.f, 3)))
n81.sort(key=lambda a: a[0])
P(' lowest', [(dec(a[0], 4),) + a[1:] for a in n81[:3]])
P(' highest', [(dec(a[0], 4),) + a[1:] for a in n81[-3:]])

P()
P('== above 1 line 73: the read V2 itself')
over = []
for r in Q:
    a1, d2, c1, v2 = read_conv(r)
    if v2 > 1:
        over.append((int(r['N']), r['delta'], r['s'], r['t'], dec(v2, 4), r['f_ppb']))
P(' rows with V2 > 1:', over)
P()
P('== identity line 73 on the rows: V2 = ((N-1)/N)|A|^2/(<A^dag A> - <n0+n+>) needs an operator check; done in check_identity.py')
P()
P('== which harmonic, line 191')
r = pin(729, '1/2', '0', '4')
P('pin N=729 yN=4: D2', dec(F(2 * abs(int(r['B_ppb'])), 729 * 10 ** 9), 4), 'A1', dec(F(2 * abs(int(r['A_ppb'])), 729 * 10 ** 9), 4), 'rows D2_ppm', r['D2_ppm'], 'A1_ppm', r['A1_ppm'])
r = conv(729, '0', '1', 1)
a1, d2, c1, v2 = read_conv(r)
P('contact N=729 d=0 s=1 t=1: A1', dec(a1, 4), 'D2', dec(d2, 4))
P()
P('== PR body and README C1 misses and table: PR table N=729 delta=0 t=2')
for s in ('1/4', '1/2', '1', '2', '4'):
    r = conv(729, '0', s, 2); a1, d2, c1, v2 = read_conv(r); L = Law(729, r['y'], '0', 2)
    P(' s', s, dec(v2, 5), dec(L.v2, 5))
P()
P('== Route on the 4 conversion rows line 74')
offs = []
for r in S['SECOND_ROUTE_CONVERT']:
    P(' ', r['_raw'][:220])
out.close()
