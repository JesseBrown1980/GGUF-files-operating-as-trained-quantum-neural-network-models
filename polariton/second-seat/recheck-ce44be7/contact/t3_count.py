import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import t2_read as R
from law import dec
rows = R.merged('outside')
for N in (81, 243, 729):
    for delta in (Fr(-5, 4), Fr(-5, 3), Fr(-2)):
        s = [r for r in rows if r['N'] == N and r['delta'] == delta]
        print('N=%d delta=%s rows=%d C1<0 on %d, V2<0 on %d, V2>1 on %d, law V2 in [0,1) on %d ; max V2 %s' % (N, delta, len(s), sum(1 for r in s if r['C1'] < 0), sum(1 for r in s if r['V2'] < 0), sum(1 for r in s if r['V2'] > 1), sum(1 for r in s if 0 <= r['L']['V2'] < 1), dec(max(r['V2'] for r in s), 4)))
s = [r for r in rows if r['delta'] < -1 and r['N'] == 729 and r['t'] <= 1]
print('delta<-1, N=729, t<=1: rows=%d V2/law %s..%s A1/law %s..%s C1/law %s..%s' % (len(s), dec(min(r['V2']/r['L']['V2'] for r in s), 4), dec(max(r['V2']/r['L']['V2'] for r in s), 4), dec(min(r['A1']/r['L']['A1'] for r in s), 4), dec(max(r['A1']/r['L']['A1'] for r in s), 4), dec(min(r['C1']/r['L']['C1'] for r in s), 4), dec(max(r['C1']/r['L']['C1'] for r in s), 4)))
s = [r for r in rows if r['delta'] > 1 and r['N'] == 729 and abs(1+r['L']['Y']) >= Fr(1, 4)]
print('delta>1, N=729, |1+Y|>=1/4: rows=%d V2/law %s..%s A1/law %s..%s D2/law %s..%s' % (len(s), dec(min(r['V2']/r['L']['V2'] for r in s if r['L']['V2']), 4), dec(max(r['V2']/r['L']['V2'] for r in s if r['L']['V2']), 4), dec(min(r['A1']/r['L']['A1'] for r in s if r['L']['A1']), 4), dec(max(r['A1']/r['L']['A1'] for r in s if r['L']['A1']), 4), dec(min(r['D2']/r['L']['D2'] for r in s), 4), dec(max(r['D2']/r['L']['D2'] for r in s), 4)))
s2 = [r for r in s if r['t'] <= 3]
print('delta>1, N=729, |1+Y|>=1/4, t<=3: rows=%d V2/law %s..%s' % (len(s2), dec(min(r['V2']/r['L']['V2'] for r in s2 if r['L']['V2']), 4), dec(max(r['V2']/r['L']['V2'] for r in s2 if r['L']['V2']), 4)))
for r in sorted(s, key=lambda r: abs(r['V2']/r['L']['V2']-1))[-4:]:
    print('  worst: delta=%s s=%s t=%s Y=%s law=%s read=%s' % (r['delta'], r.get('s'), r['t'], dec(r['L']['Y'], 4), dec(r['L']['V2'], 4), dec(r['V2'], 4)))
