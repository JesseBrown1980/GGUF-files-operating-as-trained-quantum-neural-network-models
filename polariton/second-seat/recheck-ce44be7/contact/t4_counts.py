#!/usr/bin/env python3
# t4_counts.py -- counts quoted in F4.1, and the small-y coefficient of V^2's first correction.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import t4_split as S
import chebdrv as D
import t5_eval as E
from law import law, dec, exp_fp, fp, fr

rows = S.rows()
sel = []
for d in rows:
    N = int(d['N']); delta = Fr(d['delta']); y = Fr(d['y']); t = Fr(d['t'])
    L = law(N, delta, y, t)
    if N >= 243 and L['f'] > Fr(1, 10):
        A = Fr(int(d['A_ppb']), 10**9); C1 = Fr(int(d['C1_ppb']), 10**9)
        A1 = 2*abs(A)/N
        sel.append((L, A1*A1/(2*C1)))
large = [(L, V) for (L, V) in sel if L['V2'] > Fr(1, 2)]
small = [(L, V) for (L, V) in sel if L['V2'] <= Fr(1, 2)]
lo, hi = Fr(9598, 10000), Fr(11532, 10000)
print('large-Y rows', len(large), 'with 1/law inside the read range', sum(1 for (L, V) in large if lo <= 1/L['V2'] <= hi))
print('nearer to 1 than to the law', sum(1 for (L, V) in large if abs(1-V) < abs(V-L['V2'])))
print('all above the law', sum(1 for (L, V) in large if V > L['V2']))
print('small-Y rows', len(small), 'above the law', sum(1 for (L, V) in small if V > L['V2']))
print('share of the way from the law to 1, large-Y rows: %s..%s' % (dec(min((V-L['V2'])/(1-L['V2']) for (L, V) in large), 3), dec(max((V-L['V2'])/(1-L['V2']) for (L, V) in large), 3)))
# V^2's first correction at y -> 0, delta = 0: 2 w1/w0 - C1v/C0 against (7/6) e^t
res = E.results(Fr(0))
for t in (Fr(2), Fr(3), Fr(4), Fr(6), Fr(8), Fr(10)):
    sub1 = {k: v for k, v in res['z1'].items() if k[0] == 1}
    sub0 = {k: v for k, v in res['z0'].items() if k[0] == 1}
    w1 = E.evaluate(sub1, 0, 1, t)[0]
    w0 = E.evaluate(sub0, 0, 1, t)[0]
    c0 = E.evaluate({k: v for k, v in res['C1_0'].items() if k[0] == 0}, 0, 1, t)[0]
    c1 = E.evaluate({k: v for k, v in res['C1_1'].items() if k[0] == 0}, 0, 1, t)[0]
    v = 2*w1/w0 - c1/c0
    et = fr(exp_fp(fp(t)))
    a = w1/w0
    print('t=%s V2 coefficient at y->0: %s ; (7/6)e^t=%s ; ratio %s ; A1 coefficient %s ; C1 coefficient %s ; -(5/4)e^(2t)=%s' % (t, dec(v, 3), dec(Fr(7, 6)*et, 3), dec(v/(Fr(7, 6)*et), 4), dec(a, 3), dec(c1/c0, 3), dec(-Fr(5, 4)*et*et, 3)))
