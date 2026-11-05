# Last rows: closed forms printed in the receipt against my own, float words in the reader and route, the first-run hash record.
import sys, re
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
out = open(ME + 'out/check_g.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s); out.write(s + '\n')
Q = R['POLARITON_QUENCH']
worst = F(0)
bad = 0
for r in Q:
    d, t = F(r['delta']), F(r['t'])
    shc, ch = series((1 - d * d) * t * t)
    j0 = shc ** 2 * t * t
    off = abs(F(int(r['closed_ppb']), 10 ** 9) - j0)
    worst = max(worst, off / j0)
    if off > F(1, 10 ** 8):
        bad += 1
P('closed_ppb against own on', len(Q), 'rows: largest relative off', dec(worst * 10 ** 9, 3), 'e-9; rows off by over 1e-8:', bad)
QP = R['POLARITON_QUENCH_PIN']
worst = F(0)
n = 0
for r in QP:
    y = F(r['y'])
    if y == 0 or F(r['delta']) == 1:
        continue
    L = Law(int(r['N']), y, r['delta'], r['t'])
    off = abs(F(int(r['predicted_A1_ppm']), 10 ** 6) - L.a1)
    worst = max(worst, off)
    n += 1
P('predicted_A1_ppm against own on', n, 'rows: largest off', dec(worst * 10 ** 6, 2), 'ppm')
for name in ('polariton/read_prediction.py', 'polariton/second_route.py'):
    t = open(WT + name, encoding='utf-8').read()
    P(name, 'float( hits', len(re.findall(r'\bfloat\(', t)), 'math float funcs', len(re.findall(r'\bmath\.(sqrt|exp|log|cos|sin)', t)), 'imports', re.findall(r'^(?:from|import) .*$', t, re.M))
# C1 after a quench: C1 vs 4(1-delta)jbar/N on the frozen rows, range of read
rows = [r for r in Q if int(r['N']) >= 6561 and int(r['jbar_over_N_ppm']) <= 10000 and F(int(r['jbar_ppb']), 10 ** 9) > F(1, 100) and F(r['delta']) != 1]
rat = []
for r in rows:
    want = 4 * (1 - F(r['delta'])) * F(int(r['jbar_ppb']), 10 ** 9) / int(r['N'])
    rat.append(F(int(r['C1_ppm']), 10 ** 6) / want)
P('C1 over 4(1-d)jbar/N on', len(rows), 'rows: range', dec(min(rat), 4), dec(max(rat), 4))
# ground-state C1 of order 1/N: C1*N on the ordered rows
vals = [int(r['C1_times_N_ppm']) for r in R['POLARITON_SECTOR'] if r['P'] == '0' and 'C1_times_N_ppm' in r and F(r['u']) + F(r['x']) < 1 and int(r['N']) >= 19683]
P('C1*N on ordered rows N>=19683: range', min(vals), max(vals), 'ppm')
out.close()
