# The window section: polariton/README.md lines 78-103, status line 9, root README and PR body window counts.
import sys
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
out = open(ME + 'out/check_c.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s); out.write(s + '\n')

def rho(u, x):
    u, x = F(u), F(x)
    return (1 - (u + x)) / (4 - 3 * u)
def c0(u, x):
    r = rho(u, x)
    return ((1 - 2 * r) / r - F(u)) / 4
def rotor(u, x, s):
    u_ = F(u); c = c0(u, x); q = F(s) ** 2 * u_ / (16 * c * c)
    f = mathieu_f(q)
    return 2 * rho(u, x) * f, 2 * (1 + (u_ / (8 * c)) * (1 + f)), q, f

TAB = [
 ('1/4','-1/4',729,'0.6154',[('1','0.075577','0.075894'),('4','0.458205','0.457938'),('16','0.576437','0.576913')],('2.4360','2.4360')),
 ('1/4','0',243,'0.4615',[('1','0.013054','0.013283'),('4','0.179567','0.181921'),('16','0.394605','0.401360')],('2.1698','2.1673')),
 ('3/4','0',729,'0.2857',[('1','0.005789','0.005929'),('4','0.085197','0.086940'),('16','0.240916','0.241801')],('2.2288','2.2302')),
 ('3/4','1/8',243,'0.1429',[('1','0.000345','0.000423'),('4','0.005504','0.006759'),('16','0.066277','0.077093')],('2.0718','2.0698')),
 ('1/2','1/4',243,'0.2000',[('1','0.000816','0.000889'),('4','0.012991','0.014160'),('16','0.120401','0.128489')],('2.0755','2.0714')),
]
FROZEN = {('1/4', '-1/4'): (31223, 123327, 417999, 744149, 874846, 937483), ('1/4', '0'): (7199, 28779, 113886, 394162, 732112, 869614), ('3/4', '0'): (5190, 20753, 82548, 304289, 675100, 846304), ('3/4', '1/8'): (740, 2962, 11850, 47314, 183943, 539654), ('1/2', '1/4'): (1111, 4444, 17772, 70798, 266308, 642446)}
SIX = ('1/2', '1', '2', '4', '8', '16')
P('== frozen f(q) against my own Mathieu, ppm, all 30')
worst = 0
for (u, x), t in FROZEN.items():
    for s, f in zip(SIX, t):
        c = c0(u, x); q = F(s) ** 2 * F(u) / (16 * c * c)
        mine = mathieu_f(q)
        d = abs(mine * 10 ** 6 - f)
        worst = max(worst, d)
P('largest |mine - frozen| in ppm', dec(worst, 3))

P('== window inside table cell by cell')
bad = 0
for u, x, n, two_rho, cols, a in TAB:
    P('(u,x)', u, x, 'N', n, '2rho', dec(2 * rho(u, x), 4), two_rho, 'OK' if dec(2 * rho(u, x), 4) == two_rho else 'MISMATCH')
    for s, rd, ro in cols:
        r = win(n, u, x, s)
        d2 = F(int(r['D2_ppm']), 10 ** 6)
        d2b = F(2 * abs(int(r['B_ppb'])), n * 10 ** 9)
        f_frozen = F(FROZEN[(u, x)][SIX.index(s)], 10 ** 6)
        pred = 2 * rho(u, x) * f_frozen
        pred_m, _, q, f_m = rotor(u, x, s)
        ok = dec(d2, 6) == rd and dec(pred, 6) == ro
        if not ok: bad += 1
        P('  yN', s, 'D2_ppm', r['D2_ppm'], 'from B', dec(d2b, 6), 'cell', rd, 'rotor(frozen f)', dec(pred, 6), 'rotor(mine)', dec(pred_m, 6), 'cell', ro, 'OK' if ok else 'MISMATCH', 'ratio', dec(d2b / pred, 4), 'res', r['residual_1e-12'])
    r = win(n, u, x, '4')
    a1y = F(2 * abs(int(r['A_ppb'])), n * 10 ** 9) / (F(4) / n)
    f_frozen = F(FROZEN[(u, x)][3], 10 ** 6)
    want = 2 * (1 + (F(u) / (8 * c0(u, x))) * (1 + f_frozen))
    ok = dec(a1y, 4) == a[0] and dec(want, 4) == a[1]
    if not ok: bad += 1
    P('  A1/y yN=4', dec(a1y, 4), a[0], 'rotor', dec(want, 4), a[1], 'OK' if ok else 'MISMATCH')
P('cell mismatches', bad)

P('== counts of 126 and how many at N = 729')
read = load(WT + 'polariton/READ.hbp')['POLARITON_READ']
fam = lambda pre: [r for r in read if r['row'].startswith(pre)]
ins = fam('window_inside_')
bel = fam('window_below_')
P('inside', len(ins), 'MET', sum(r['result'] == 'MET' for r in ins), 'at N=729', sum('N=729_' in r['row'] for r in ins), 'at N=243', sum('N=243_' in r['row'] for r in ins))
P('below', len(bel), 'MET', sum(r['result'] == 'MET' for r in bel), 'at N=729', sum('N=729_' in r['row'] for r in bel), 'at N=243', sum('N=243_' in r['row'] for r in bel))
P()
P('== D2 ratio line 92')
for (u, x) in (('3/4', '0'), ('1/4', '-1/4')):
    for n in (243, 729):
        r = win(n, u, x, '1')
        d2b = F(2 * abs(int(r['B_ppb'])), n * 10 ** 9)
        pred = 2 * rho(u, x) * F(FROZEN[(u, x)][1], 10 ** 6)
        P(' ', u, x, 'N', n, 'yN=1 ratio', dec(d2b / pred, 3), 'with D2_ppm', dec(F(int(r['D2_ppm']), 10 ** 6) / pred, 3))
P('all five points at all s: D2 ratio by N')
for (u, x) in FROZEN:
    for n in (81, 243, 729):
        rs = [(s, win(n, u, x, s)) for s in SIX]
        if not all(r for _, r in rs):
            continue
        P(' ', u, x, 'N', n, [dec(F(2 * abs(int(r['B_ppb'])), n * 10 ** 9) / (2 * rho(u, x) * F(FROZEN[(u, x)][SIX.index(s)], 10 ** 6)), 3) for s, r in rs])
P()
P('== below table lines 96-101')
BT = [('1','-1/4',729,'0.9994','1.6017','1.6000','0.3202','0.3200','+'),('1','-1/8',243,'0.9931','1.7842','1.7778','0.1961','0.1975','+'),('1/2','-1/4',729,'0.9983','2.6691','2.6667','1.7922','1.7778','-'),('3/4','-1/8',243,'0.9886','2.2936','2.2857','0.4501','0.4354','-')]
for u, x, n, p2c, a_c, a2_c, d_c, d2_c, sg in BT:
    u_, x_ = F(u), F(x)
    r16 = win(n, u, x, '16'); r4 = win(n, u, x, '4')
    p2 = F(int(r16['P2_over_N2_ppm']), 10 ** 6)
    a1y = F(2 * abs(int(r4['A_ppb'])), n * 10 ** 9) / (F(4) / n)
    d2y = F(2 * abs(int(r16['B_ppb'])), n * 10 ** 9) / (F(16) / n) ** 2
    wa = 2 / (u_ - x_); wd = 2 * abs(u_ - x_ - 1) / (u_ * (u_ - x_) ** 2)
    sign = '+' if int(r16['B_ppb']) > 0 else '-'
    ok = dec(p2, 4) == p2c and dec(a1y, 4) == a_c and dec(wa, 4) == a2_c and dec(d2y, 4) == d_c and dec(wd, 4) == d2_c and sign == sg
    P(u, x, n, 'P2', dec(p2, 4), p2c, 'A1/y', dec(a1y, 4), a_c, '2/(u-x)', dec(wa, 4), a2_c, 'D2/y2', dec(d2y, 4), d_c, 'form', dec(wd, 4), d2_c, 'sign', sign, sg, 'OK' if ok else 'MISMATCH')
P()
P('== line 103 and line 9')
r = win(243, '1', '-1/4', '4')
d2b = F(2 * abs(int(r['B_ppb'])), 243 * 10 ** 9)
P('N=243 u=1 x=-1/4 s=4: D2', dec(d2b, 6), r['D2_ppm'], 'A1/y', dec(F(2 * abs(int(r['A_ppb'])), 243 * 10 ** 9) / (F(4) / 243), 4), 'P2', r['P2_over_N2_ppm'], r['_raw'][:200])
ro = rotor('1', '-1/4', '4')
P(' rotor form: D2', dec(ro[0], 4), 'A1/y', dec(ro[1], 4), 'q', dec(ro[2], 3), 'f', dec(ro[3], 4))
for n in (243, 729):
    r = win(n, '1/2', '-1/4', '4')
    P('u=1/2 x=-1/4 N', n, 's=4: D2', dec(F(2 * abs(int(r['B_ppb'])), n * 10 ** 9), 6), r['D2_ppm'])
ro = rotor('1/2', '-1/4', '4')
P(' rotor form at (1/2,-1/4) yN=4: D2', dec(ro[0], 4), 'q', dec(ro[2], 3))
for n in (243,729):
    r = win(n, '1', '-1/4', '4')
    P('u=1 x=-1/4 N', n, 's=4: D2', dec(F(2 * abs(int(r['B_ppb'])), n * 10 ** 9), 6), r['D2_ppm'], 'A1/y', dec(F(2 * abs(int(r['A_ppb'])), n * 10 ** 9) / (F(4) / n), 4), 'P2', r['P2_over_N2_ppm'])
P()
P('== points in the PIN_WINDOW stage')
pts = sorted({(r['u'], r['x']) for r in R['POLARITON_PIN_WINDOW']})
for u, x in pts:
    rs = [r for r in R['POLARITON_PIN_WINDOW'] if (r['u'], r['x']) == (u, x)]
    P(' ', u, x, 'N', sorted({int(r['N']) for r in rs}), 's', sorted({r['s'] for r in rs}), 'rows', len(rs))
P('rows', len(R['POLARITON_PIN_WINDOW']))

P()
P('== edges line 80')
def edge(u):
    u = F(u); a = 4 - 3 * u
    w = (a - root(u * a)) / 2
    return (1 - w) - u
for u in ('0', '1/4', '1/2', '3/4', '1'):
    P(' u', u, 'x edge', dec(edge(u), 4))
P('== plane wave at N=19683')
for u, x in (('1', '-1/4'), ('1/2', '0')):
    e0 = sec(19683, u, x); top = sec(19683, u, x, 19683)
    P(' ', u, x, 'e(0)', e0['e_ppb'], 'e(P=N)', top['e_ppb'] if top else None)
for r in read:
    if r['row'].startswith('plane_wave') or r['row'].startswith('e_rises'):
        P(' ', r['_raw'][:200])
P('== sign rows at u=1/2 below edge etc. A1, s=1/2 at N=243 etc.')
P('== hopfield: a = 0.4/0.54')
a = F(4, 10) / F(54, 100)
u1 = a; u2 = 2 - (a + 1 / a) / 2
P(' a', dec(a, 4), 'u1', dec(u1, 3), 'u2', dec(u2, 4), 'w(n+n-) = 4 - 1/a - 2a', dec(4 - 1 / a - 2 * a, 4), 'mean field u from 4-3u = 4-4u2+u1:', dec((4 - (4 - 4 * u2 + u1)) / 3, 3), 'shift 2-1/a', dec(2 - 1 / a, 4))
P(' with amplitudes X0=0.54,X1=0.4 (X^2 fraction squares): a', dec((F(4, 10) / F(54, 100)) ** 2, 4))
a2 = (F(4, 10) / F(54, 100)) ** 2
P('   u1', dec(a2, 3), 'u2', dec(2 - (a2 + 1 / a2) / 2, 4), 'w', dec(4 - 1 / a2 - 2 * a2, 4))
out.close()
