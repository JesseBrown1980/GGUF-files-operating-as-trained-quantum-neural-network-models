# The ladder: polariton/README.md lines 113-127 and the route lines 169-170; root README and PR body rung statements.
import sys
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
out = open(ME + 'out/check_d.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s); out.write(s + '\n')

SEC = R['POLARITON_SECTOR']
P('sector rows', len(SEC), 'P=0 rows', sum(r['P'] == '0' for r in SEC), 'P!=0', sum(r['P'] != '0' for r in SEC))
P('fields on a P=0 row', [k for k in SEC[-1].keys() if k != '_raw'])
P0 = [r for r in SEC if r['P'] == '0']
P('P=0 rows with fd_step', sum('fd_step' in r for r in P0), 'steps', sorted({r.get('fd_step') for r in P0}, key=str))
Ns = sorted({int(r['N']) for r in SEC})
P('Ns', Ns)
for n in Ns:
    rs = [r for r in P0 if int(r['N']) == n]
    P(' N', n, 'P=0 rows', len(rs), 'points', sorted({(r['u'], r['x']) for r in rs}), 'fd', sorted({r.get('fd_step') for r in rs}, key=str))
P('dimension checks', 23887872 // 2 + 1, 43046721 // 2 + 1, 730 * 731 // 2)

P()
P('== ladder table')
for n, cols in ((23887872, ('-0.100000011', '0.399999975', '1.095445')), (43046721, ('-0.100000006', '0.399999986', '1.095445'))):
    r = sec(n, '1/2', '0')
    P(' N', n, 'e_ppb', r['e_ppb'], 'f_ppb', r['f_ppb'], 'gap_ppb', r['gap_ppb'], 'C2_ppm', r['C2_ppm'], 'C1N', r['C1_times_N_ppm'], 'cells', cols, 'fd', r.get('fd_step'))
    P('   e', dec(F(int(r['e_ppb']), 10 ** 9), 9), 'f', dec(F(int(r['f_ppb']), 10 ** 9), 9), 'gap', dec(F(int(r['gap_ppb']), 10 ** 9), 6))
P(' sqrt(6/5)', dec(root(F(6, 5)), 6), ' 2sqrt3', dec(2 * root(3), 5))
for n, cols in ((23887872, ('0.07735', '3.46410')), (43046721, ('0.07735', '3.46410'))):
    r = sec(n, '1/2', '3/2')
    P(' N', n, 'x=3/2 jbar', dec(F(int(r['jbar_ppb']), 10 ** 9), 5), 'gap', dec(F(int(r['gap_ppb']), 10 ** 9), 5), 'cells', cols)
for n, cols in ((23887872, ('86.65', '0.013431')), (43046721, ('105.54', '0.011038'))):
    r = sec(n, '1/2', '1/2')
    P(' N', n, 'x=1/2 jbar', dec(F(int(r['jbar_ppb']), 10 ** 9), 2), 'gap', dec(F(int(r['gap_ppb']), 10 ** 9), 6), 'cells', cols, r['jbar_ppb'], r['gap_ppb'])
P(' predicted x=3/2 jbar (delta/omega-1)/2 at delta=2: ', dec((2 / root(3) - 1) / 2, 5))
P(' 2 rho at delta=1/2,u=1/2', F(2) * (F(1, 2) / F(5, 2)))

P()
P('== takeover ratio sequences, u=1/2, x=1/2')
pow3 = [3 ** k for k in range(9, 17)]
j = [F(int(sec(n, '1/2', '1/2')['jbar_ppb']), 10 ** 9) for n in pow3]
g = [F(int(sec(n, '1/2', '1/2')['gap_ppb']), 10 ** 9) for n in pow3]
P(' jbar steps', [dec(b / a, 4) for a, b in zip(j, j[1:])])
P(' gap steps ', [dec(b / a, 4) for a, b in zip(g, g[1:])])
P(' claim jbar 1.4666, 1.4590, 1.4538, 1.4503, 1.4478, 1.4461, 1.4449')
P(' claim gap  0.6945, 0.6941, 0.6939, 0.6937, 0.6936, 0.6935, 0.6935')
P(' 3^(1/3)', '1.44225', '3^(-1/3) 0.69336')
P(' also u=0,x=1 and u=1,x=0:')
for u, x in (('0', '1'), ('1', '0')):
    ns = [n for n in (3 ** k for k in range(1, 17)) if sec(n, u, x)]
    jj = [F(int(sec(n, u, x)['jbar_ppb']), 10 ** 9) for n in ns]
    gg = [F(int(sec(n, u, x)['gap_ppb']), 10 ** 9) for n in ns]
    P('  ', u, x, 'Ns', ns[-5:], 'jbar steps', [dec(b / a, 4) for a, b in zip(jj, jj[1:])][-4:], 'gap', [dec(b / a, 4) for a, b in zip(gg, gg[1:])][-4:])

P()
P('== rotor at N=531441 u=1/2 x=0')
for p, want in ((1, '5/8'), (2, '5/2'), (3, '45/8')):
    r = sec(531441, '1/2', '0', p)
    P(' P', p, r['N2_times_e_above_P0_ppm'], want)
P('largest rotor N in rows', max(int(r['N']) for r in SEC if r['P'] in ('1', '2', '3')))

P()
P('== tolerances at N>=19683 on every ordered row: my own read of the frozen tolerances')
ORD = [('0','0'),('0','1/2'),('0','-1/2'),('1/2','0'),('1/2','1/4'),('1','-1/4'),('1','-1/8')]
worst = {}
tot = 0
for u, x in ORD:
    uu, xx = F(u), F(x); d = uu + xx
    rho = (1 - d) / (4 - 3 * uu); r0 = 1 - 2 * rho
    e = -(1 - d) ** 2 / (4 - 3 * uu); f = 2 * rho; gap = root(4 * (4 - 3 * uu) * rho * r0); c2 = 2 * rho ** 2; c0 = (r0 / rho - uu) / 4
    for n in sorted({int(r['N']) for r in P0 if eq(r['u'], u) and eq(r['x'], x) and int(r['N']) >= 19683}):
        r = sec(n, u, x)
        tot += 1
        offs = {'e': abs(F(int(r['e_ppb']), 10 ** 9) / e - 1), 'f': abs(F(int(r['f_ppb']), 10 ** 9) / f - 1), 'gap': abs(F(int(r['gap_ppb']), 10 ** 9) / gap - 1), 'C2': abs(F(int(r['C2_ppm']), 10 ** 6) / c2 - 1)}
        for k, v in offs.items():
            if v > worst.get(k, (F(0),))[0]:
                worst[k] = (v, n, u, x)
        P_rows = [sec(n, u, x, p) for p in (1, 2, 3)]
        for p, s in zip((1, 2, 3), P_rows):
            if s:
                o = abs(F(int(s['N2_times_e_above_P0_ppm']), 10 ** 6) / (c0 * p * p) - 1)
                if o > worst.get('rotor', (F(0),))[0]:
                    worst['rotor'] = (o, n, u, x, p)
P('ordered rows N>=19683', tot)
for k, v in worst.items():
    P(' worst', k, dec(v[0] * 100, 4), '%', v[1:])
P()
P('== route rows')
T = S['SECOND_ROUTE_TOP']
P('top rows', len(T), S['SECOND_ROUTE_TOP_DONE'][0]['rows'], S['SECOND_ROUTE_TOP_DONE'][0]['bad'])
P('top rows by (u,x):', sorted({(r['u'], r['x']) for r in T}))
P('top rows by N:', sorted({int(r['N']) for r in T}))
P('P=0 rows at N>=59049 in the receipt:', sum(int(r['N']) >= 59049 for r in P0), 'with delta>=1:', sum(int(r['N']) >= 59049 and F(r['u']) + F(r['x']) >= 1 for r in P0), 'with delta<1:', sum(int(r['N']) >= 59049 and F(r['u']) + F(r['x']) < 1 for r in P0))
print(T[0]['_raw'])
def offs(r):
    fields = r['_raw'].split('|')
    v = [f.split('=')[1] for f in fields if f.startswith('off_ppm=')]
    return int(v[0]), int(v[1])
P('largest off_ppm pairs, gap', max(offs(r)[0] for r in T), max(offs(r)[1] for r in T))
for r in T:
    if offs(r)[0] == max(offs(x)[0] for x in T):
        P(' largest pairs at', r['_raw'][:200])
own = []
for r in T:
    ej, rj = F(r['exact_jbar']), F(r['rust_jbar'])
    eg, rg = F(r['exact_gap']), F(r['rust_gap'])
    own.append((abs(rj / ej - 1) * 10 ** 6, abs(rg / eg - 1) * 10 ** 6, r['N'], r['u'], r['x']))
P('own off from the printed digits, pairs max', dec(max(o[0] for o in own), 2), max(own, key=lambda o: o[0])[2:], 'gap max', dec(max(o[1] for o in own), 3), max(own, key=lambda o: o[1])[2:])
for r in T:
    if r['N'] == '43046721' and eq(r['x'], '1/2'):
        P(' top row', r['_raw'])
SS = S['SECOND_ROUTE_SECTOR']
P('route sector rows', len(SS), S['SECOND_ROUTE_SECTOR_DONE'][0], 'largest off', max(int(r['off_units_of_2^-60']) for r in SS), 'count off=1', sum(int(r['off_units_of_2^-60']) == 1 for r in SS), 'off=0', sum(int(r['off_units_of_2^-60']) == 0 for r in SS))
P('route sector N', sorted({int(r['N']) for r in SS}))
FU = S['SECOND_ROUTE_FULL']
P('route full rows', len(FU), S['SECOND_ROUTE_FULL_DONE'][0], 'by N', {n: sum(int(r['N']) == n for r in FU) for n in sorted({int(r['N']) for r in FU})})
P('route taylor', S['SECOND_ROUTE_TAYLOR_DONE'][0], 'convert', S['SECOND_ROUTE_CONVERT_DONE'][0])
off_j, off_a = [], []
for r in S['SECOND_ROUTE_TAYLOR']:
    off_j.append(abs(F(r['exact_jbar']) - F(r['rust_jbar']))); off_a.append(abs(F(r['exact_A']) - F(r['rust_A'])))
P('taylor largest off printed: jbar', dec(max(off_j), 10), 'A', dec(max(off_a), 10))
# Convert against the receipt from printed digits
for r in S['SECOND_ROUTE_CONVERT']:
    rr = [z for z in R['POLARITON_TAYLOR_CONVERT'] if z['N'] == r['N'] and z['x'] == r['x'] and z['y'] == r['y'] and z['t'] == r['t']][0]
    o = {k: abs(F(r['exact_' + a]) - F(int(rr[b]), 10 ** 9)) for k, a, b in (('j', 'jbar', 'jbar_ppb'), ('A', 'A', 'A_ppb'), ('B', 'B', 'B_ppb'), ('C1', 'C1', 'C1_ppb'), ('C2', 'C2', 'C2_ppb'))}
    P(' convert row', r['N'], r['x'], r['y'], r['t'], {k: dec(v * 10 ** 9, 1) for k, v in o.items()}, 'largest_off', r['largest_off_1e-9'])
for r in S['HAND_N2'] + S['HAND_N2_PIN'] + S['HAND_N3_DOUBLET'] + S['MATHIEU']:
    P(' ', r['_raw'])
P()
P('== Takeover constants line 127: at N=43046721')
n = 43046721
gc = F(4 - F(3, 2)) / (16 * n)
# g^(1/3) by integer root at 2^256 scale
def cuberoot(q):
    q = F(q)
    # newton in integers at 2^120 scale
    s = 1 << 120
    target = (q.numerator << 360) // q.denominator
    lo, hi = 0, 1 << 200
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if mid ** 3 <= target:
            lo = mid
        else:
            hi = mid
    return F(lo, s)
g13 = cuberoot(gc)
P(' g', dec(gc * 10 ** 9, 5), 'e-9', 'g^(1/3)', dec(g13, 8))
gap_form = F(718495, 100000) * g13
pairs_form = F(162869, 1000000) / g13
ex = [r for r in T if r['N'] == '43046721' and eq(r['x'], '1/2')][0]
P(' gap form', dec(gap_form, 8), 'exact', ex['exact_gap'], 'ratio exact/form', dec(F(ex['exact_gap']) / gap_form, 5))
P(' pairs form', dec(pairs_form, 3), 'less .44', dec(pairs_form - F(44, 100), 3), 'exact', ex['exact_jbar'])
P('== third-run top rungs for comparison')
T3 = load(WT + 'polariton/third-run/RECEIPT.hbp')
def sec3(n, u, x):
    return [r for r in T3['POLARITON_SECTOR'] if int(r['N']) == n and eq(r['u'], u) and eq(r['x'], x) and r['P'] == '0'][0]
for n in (3 ** 16,):
    for u, x in (('1/2', '1/2'), ('1/2', '3/2')):
        a = sec3(n, u, x); ex = [r for r in T if int(r['N']) == n and eq(r['x'], x)][0]
        P(' third-run', x, 'jbar', a['jbar_ppb'], 'off ppm vs exact', dec((F(int(a['jbar_ppb']), 10 ** 9) / F(ex['exact_jbar']) - 1) * 10 ** 6, 1), 'gap', a['gap_ppb'], 'off ppm', dec((F(int(a['gap_ppb']), 10 ** 9) / F(ex['exact_gap']) - 1) * 10 ** 6, 1))
out.close()
