#!/usr/bin/env python3
# t2_limits.py -- (read/law - 1) N at N = 81, 243, 729 against the first correction's limit, at fixed (delta, y^2 N, t). N=243 uses y = s/16, so its y^2 N differs by 5%.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import t2_read as R
import t5_eval as E
from law import dec

rows = R.merged('band')
print('delta s t | (V2/law-1)N at N=81, 243, 729, limit | (A1/law-1)N at N=81, 243, 729, limit | (C1/law-1)N at N=81, 243, 729, limit')
for delta in (Fr(-1), Fr(-3, 4), Fr(-1, 2), Fr(0), Fr(1, 2), Fr(3, 4)):
    for s in (Fr(1, 4), Fr(1)):
        for t in (Fr(1), Fr(2)):
            sel = {r['N']: r for r in rows if r['delta'] == delta and r['s'] == s and r['t'] == t}
            y = s/27
            fo = E.first_order(delta, y, 729, t)
            lim_a = fo['w1']/fo['w0']
            lim_c = fo['C1v']/fo['C0']
            lim_v = 2*lim_a - lim_c
            def cols(key, lim):
                return ' '.join(dec((sel[N][key]/sel[N]['L'][key]-1)*N, 2) for N in (81, 243, 729)) + ' -> ' + dec(lim, 2)
            print('%s %s %s | %s | %s | %s' % (delta, s, t, cols('V2', lim_v), cols('A1', lim_a), cols('C1', lim_c)))
