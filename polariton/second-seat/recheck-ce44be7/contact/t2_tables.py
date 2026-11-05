#!/usr/bin/env python3
# t2_tables.py -- every band row, and for each (N, delta, t) the range of V2/law, A1/law, C1/law over s, plus (V2/law-1) N.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import t2_read as R
from law import dec

rows = R.merged('band')
with open('C:/tmp/opus55/polariton-recheck-contact-20261105/out/t2_table_band.txt', 'w', newline='\n') as fh:
    fh.write('N delta s y2N t Y law V2_read V2/law (V2/law-1)N A1/law C1/law D2/law f_pred f_read\n')
    for r in sorted(rows, key=lambda r: (r['N'], r['delta'], r['s'], r['t'])):
        L = r['L']
        fh.write('%d %s %s %s %s %s %s %s %s %s %s %s %s %s %s\n' % (
            r['N'], r['delta'], r['s'], dec(r['s2'], 4), r['t'], dec(L['Y'], 4), dec(L['V2'], 5), dec(r['V2'], 5),
            dec(r['V2']/L['V2'], 4) if L['V2'] else 'na', dec((r['V2']/L['V2']-1)*r['N'], 2) if L['V2'] else 'na',
            dec(r['A1']/L['A1'], 4) if L['A1'] else 'na', dec(r['C1']/L['C1'], 4) if L['C1'] else 'na', dec(r['D2']/L['D2'], 4), dec(L['f'], 4), dec(r['f'], 4)))
print('RANGE over s=1/4..4 of V2/law at each N, delta, t; then A1/law; then C1/law')
for N in (81, 243, 729):
    for delta in (Fr(-1), Fr(-3, 4), Fr(-1, 2), Fr(0), Fr(1, 2), Fr(3, 4)):
        parts = []
        for t in (Fr(1, 2), Fr(1), Fr(2), Fr(3)):
            s = [r for r in rows if r['N'] == N and r['delta'] == delta and r['t'] == t]
            v = [r['V2']/r['L']['V2'] for r in s]
            a = [r['A1']/r['L']['A1'] for r in s]
            c = [r['C1']/r['L']['C1'] for r in s]
            parts.append('t=%s V2 %s..%s A1 %s..%s C1 %s..%s' % (t, dec(min(v), 3), dec(max(v), 3), dec(min(a), 3), dec(max(a), 3), dec(min(c), 3), dec(max(c), 3)))
        print('N=%d delta=%s | %s' % (N, delta, ' | '.join(parts)))
