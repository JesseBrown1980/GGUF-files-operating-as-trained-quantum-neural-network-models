# Status, central result, conversion, pin rows, u = 0: polariton/README.md lines 5-42.
import sys
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
out = open(ME + 'out/check_a.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s); out.write(s + '\n')

# READ counts by my own parser of READ.hbp
read = load(WT + 'polariton/READ.hbp')
rows = read['POLARITON_READ']
met = sum(r['result'] == 'MET' for r in rows); miss = sum(r['result'] == 'MISS' for r in rows)
P('READ.hbp rows', len(rows), 'MET', met, 'MISS', miss, 'DONE', read['POLARITON_READ_DONE'][0]['met'], read['POLARITON_READ_DONE'][0]['miss'])
names = [r['row'] for r in rows]
P('duplicate row names', len(names) - len(set(names)))

# group by leading tag
import re
def fam(n):
    m = re.match(r'(.*?)(_?N=|_u=|_delta=|_t=|$)', n)
    return m.group(1) if m and m.group(1) else n
from collections import Counter
c = Counter(); cm = Counter()
for r in rows:
    k = fam(r['row'])
    c[k] += 1
    if r['result'] == 'MISS': cm[k] += 1
for k in sorted(c):
    P('  fam', k, 'rows', c[k], 'miss', cm[k])

P()
P('== central table N=729 u=1/2 x=0')
FQ = {'1/2': 9999, '1': 39944, '2': 156537, '4': 490857, '8': 776331, '16': 889412}
TAB = {'1/2': ('0.02', '0.003962', '0.004000', '2.2028', '2.2020'), '1': ('0.08', '0.015830', '0.015978', '2.2087', '2.2080'), '2': ('0.32', '0.062062', '0.062615', '2.2317', '2.2313'), '4': ('1.28', '0.195339', '0.196343', '2.2980', '2.2982'), '8': ('5.12', '0.310305', '0.310532', '2.3551', '2.3553'), '16': ('20.48', '0.355329', '0.355765', '2.3774', '2.3779')}
for s, (q_c, d_c, dp_c, a_c, ap_c) in TAB.items():
    r = pin(729, '1/2', '0', s)
    yN = F(s); y = yN / 729
    q = F(2, 25) * yN ** 2
    fa = mathieu_f(q)
    d2 = F(2 * abs(int(r['B_ppb'])), 729 * 10 ** 9)
    a1y = F(2 * abs(int(r['A_ppb'])), 729 * 10 ** 9) / y
    dp = F(2, 5) * F(FQ[s], 10 ** 6)
    ap = 2 * (1 + (1 + F(FQ[s], 10 ** 6)) / 10)
    ok = (dec(q, 2) == q_c, dec(d2, 6) == d_c, dec(dp, 6) == dp_c, dec(a1y, 4) == a_c, dec(ap, 4) == ap_c)
    P('s', s, 'q', dec(q, 2), q_c, 'D2', dec(d2, 6), d_c, r['D2_ppm'], 'pred', dec(dp, 6), dp_c, 'A1/y', dec(a1y, 4), a_c, 'pred', dec(ap, 4), ap_c, 'f_mine', dec(fa, 6), 'ALLOK' if all(ok) else 'MISMATCH %s' % (ok,), 'res', r['residual_1e-12'], 'ratio', dec(d2 / dp, 4))

P()
P('== zero field lines 26')
for n in (81, 243, 729):
    z = pin(n, '1/2', '0', '0')
    P('N', n, {k: z[k] for k in ('A_ppb', 'B_ppb', 'C1_ppm', 'C2_ppm', 'residual_1e-12', 'cycles', 'energy_ppb', 'f_ppm')})
P('C2 N=729 float-free', dec(F(int(pin(729, '1/2', '0', '0')['C2_ppm']), 10 ** 6), 4), 'against 0.0801; 2rho^2 = 2/25')
z = pin(729, '1/2', '0', '0')
P('sqrt(2C2) N=729', dec(root(2 * F(int(z['C2_ppm']), 10 ** 6)), 5), 'claim 0.40022')
P()
P('== y=0 rows of all (N,u,x) in PIN and PIN_WINDOW: energy against N*e of sector P=0')
zero_rows = [r for r in R['POLARITON_PIN'] if r['s'] != 'hand' and F(r['y']) == 0] + [r for r in R['POLARITON_PIN_WINDOW'] if F(r['y']) == 0]
P('y=0 rows', len(zero_rows))
inside, below, nosec = [], [], []
for r in zero_rows:
    n = int(r['N'])
    sr = sec(n, r['u'], r['x'])
    if sr is None:
        nosec.append(r); continue
    # e_ppb is E/N^2 in units of J: E(in JN units)= N e
    e_sec = F(int(sr['e_at_2^60']), 1 << 60)
    en = F(int(r['energy_ppb']), 10 ** 9)
    diff = en - n * e_sec
    r['_diff'] = diff
    (inside if abs(diff) <= F(1, 10 ** 9) else below).append(r)
P('within 1 ppb', len(inside), 'outside', len(below), 'no sector row', len(nosec))
P('largest within', dec(max(abs(r['_diff']) for r in inside), 12))
for r in sorted(inside, key=lambda r: (F(r['u']), F(r['x']), int(r['N']))):
    P('  in', r['_raw'].split('|')[0], r['N'], r['u'], r['x'], 'P2?', r.get('P2_over_N2_ppm', '-'), 'diff', dec(r['_diff'], 12))
for r in sorted(below, key=lambda r: (F(r['u']), F(r['x']), int(r['N']))):
    P('  below', r['_raw'].split('|')[0], r['N'], r['u'], r['x'], 'P2', r.get('P2_over_N2_ppm', '-'), 'E', dec(F(int(r['energy_ppb']), 10 ** 9), 6), 'diff', dec(r['_diff'], 6))
for r in sorted(nosec, key=lambda r: (F(r['u']), F(r['x']), int(r['N']))):
    P('  nosec', r['_raw'].split('|')[0], r['N'], r['u'], r['x'], 'P2', r.get('P2_over_N2_ppm', '-'), 'E', dec(F(int(r['energy_ppb']), 10 ** 9), 6))

P()
P('== conversion line 39: D2 over f*sqrt(2C2(y=0)) and over f*2rho')
for n in (81, 243, 729):
    z = pin(n, '1/2', '0', '0')
    c2 = F(int(z['C2_ppm']), 10 ** 6)
    sq = root(2 * c2)
    for s in ('4', '8', '16'):
        r = pin(n, '1/2', '0', s)
        d2 = F(2 * abs(int(r['B_ppb'])), n * 10 ** 9)
        f = F(FQ[s], 10 ** 6)
        a = d2 / (f * sq); b = d2 / (f * F(2, 5))
        closer = 'rho_closer' if abs(b - 1) < abs(a - 1) else 'C2_closer' if abs(a - 1) < abs(b - 1) else 'equal'
        P('N', n, 's', s, 'sqrt2C2', dec(sq, 5), 'C2', z['C2_ppm'], 'D2/(f sqrt2C2)', dec(a, 5), 'off%', dec((a - 1) * 100, 3), 'D2/(f 2rho)', dec(b, 5), closer, 'C2 at s', r['C2_ppm'])
P()
P('== sign, symmetry line 40')
for n in (81, 243, 729):
    P('N', n, [(s, 'A>0' if int(pin(n, '1/2', '0', s)['A_ppb']) > 0 else 'A<=0', 'B<0' if int(pin(n, '1/2', '0', s)['B_ppb']) < 0 else 'B>=0') for s in FQ])
a, b = R['POLARITON_SYMMETRY']
P('sym', a['A_ppb'], b['A_ppb'], a['B_ppb'], b['B_ppb'], a['energy_ppb'], b['energy_ppb'])
P()
P('== susceptibility line 41: from B_ppb')
chi = {}
for n in (81, 243, 729):
    r = pin(n, '1/2', '0', '1/2'); y = F(1, 2 * n)
    chi[n] = F(2 * abs(int(r['B_ppb'])), n * 10 ** 9) / y ** 2
P('chi', {n: dec(v, 3) for n, v in chi.items()}, 'ratios', dec(chi[243] / chi[81], 3), dec(chi[729] / chi[243], 3), 'claim 9.57 9.17')
P('delta=2 D2/y^2 at (1/2, 3/2):')
for n in (81, 243, 729):
    P(' N', n, [(s, dec(F(2 * abs(int(pin(n, '1/2', '3/2', s)['B_ppb'])), n * 10 ** 9) / (F(s) / n) ** 2, 4)) for s in FQ if pin(n, '1/2', '3/2', s)], '2/9=0.2222')
P('A1/y at (1/2,3/2) N=729', [(s, dec(F(2 * abs(int(pin(729, '1/2', '3/2', s)['A_ppb'])), 729 * 10 ** 9) / (F(s) / 729), 4)) for s in FQ], '4/3=1.3333')
P('0.95% check', dec((1 - F(3962, 10 ** 6) / F(4000, 10 ** 6)) * 100, 3), ' -6.72/729 in percent', dec(F(-672, 100) / 729 * 100, 3))
P()
P('== u=0 line 42')
for n in (243, 729):
    for s in ('1/2', '1', '2', '4', '8', '16'):
        r = pin(n, '0', '0', s)
        if r is None:
            P('N', n, 's', s, 'no row'); continue
        y = F(s) / n
        P('N', n, 's', s, 'D2', dec(F(2 * abs(int(r['B_ppb'])), n * 10 ** 9), 6), 'A1/y', dec(F(2 * abs(int(r['A_ppb'])), n * 10 ** 9) / y, 4), 'B sign', '+' if int(r['B_ppb']) > 0 else '-', 'res', r['residual_1e-12'])
P('N=729 u=1/2 s=4 D2', dec(F(2 * abs(int(pin(729, '1/2', '0', '4')['B_ppb'])), 729 * 10 ** 9), 4), 'claim 0.1953')
P('Pin (u,x) points', sorted({(r['u'], r['x']) for r in R['POLARITON_PIN'] if r['s'] != 'hand'}))
P('Pin Ns', sorted({int(r['N']) for r in R['POLARITON_PIN'] if r['s'] != 'hand'}))
P()
P('== residuals')
for name, rows_ in (('PIN', [r for r in R['POLARITON_PIN'] if r['s'] != 'hand']), ('WINDOW', R['POLARITON_PIN_WINDOW'])):
    big = [r for r in rows_ if int(r['N']) >= 243]
    P(name, 'N>=243 rows', len(big), 'max residual', max(int(r['residual_1e-12']) for r in big), 'at', max(big, key=lambda r: int(r['residual_1e-12']))['_raw'][:90])
    cen = [r for r in big if eq(r['u'], '1/2') and eq(r['x'], '0')]
    if cen:
        P('  central rows', len(cen), 'max', max(int(r['residual_1e-12']) for r in cen), 'at', max(cen, key=lambda r: int(r['residual_1e-12']))['_raw'][:90])
sym = R['POLARITON_SYMMETRY']
P('symmetry residuals', [r['residual_1e-12'] for r in sym])
out.close()
