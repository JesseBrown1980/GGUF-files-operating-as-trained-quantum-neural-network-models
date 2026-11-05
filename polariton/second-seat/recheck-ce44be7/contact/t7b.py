#!/usr/bin/env python3
# t7b.py -- sign counts by delta on my grids, the README's pinned digits, and the s^2 term in w1 on receipt rows.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import chebdrv as D
import t2_read as R
import t5_eval as E
from law import law, dec

for grid in ('band', 'outside'):
    rows = R.merged(grid)
    for delta in sorted(set(r['delta'] for r in rows)):
        sel = [r for r in rows if r['delta'] == delta and r['N'] >= 243]
        small = [r for r in sel if r['L']['f'] <= Fr(1, 10)]
        print('%s delta=%s N>=243 rows=%d: <A> sign same as y on %d, opposite on %d ; f_pred<=1/10 rows=%d: same %d, opposite %d ; <B> positive %d, negative %d' % (
            grid, delta, len(sel), sum(1 for r in sel if r['A'] > 0), sum(1 for r in sel if r['A'] < 0),
            len(small), sum(1 for r in small if r['A'] > 0), sum(1 for r in small if r['A'] < 0), sum(1 for r in small if r['B'] > 0), sum(1 for r in small if r['B'] < 0)))
REC = 'C:/tmp/qnn-polariton-wt/polariton/RECEIPT.hbp'
rows = []
for ln in open(REC, encoding='utf8', newline=''):
    ln = ln.rstrip('\r\n')
    if ln.startswith('POLARITON_QUENCH_CONVERSION|') or ln.startswith('POLARITON_QUENCH_PIN|'):
        rows.append(D.parse_row(ln) | {'tag': ln.split('|')[0]})
for r in rows:
    if r['tag'] == 'POLARITON_QUENCH_PIN' and r['N'] == '729' and r['y'] == '1/1024' and r['delta'] == '0':
        t = Fr(r['t']); y = Fr(1, 1024)
        A1 = 2*abs(Fr(int(r['A_ppb']), 10**9))/729
        w1r = E.readme_w1_delta0(t)
        w0 = E.first_order(Fr(0), y, 729, t)['w0']
        print('PIN t=%s A1 exact from A_ppb=%s, A1_ppm field=%s, law=%s ; read/first(README w1) from A_ppb=%s ; from A1_ppm=%s' % (
            t, dec(A1, 8), r['A1_ppm'], dec(law(729, 0, y, t)['A1'], 8), dec(A1/(2*y*abs(w0 + w1r/729)), 5), dec(Fr(int(r['A1_ppm']), 10**6)/(2*y*abs(w0 + w1r/729)), 5)))
print('the s^2 term in w1 on conversion rows, delta=0:')
for r in rows:
    if r['tag'] == 'POLARITON_QUENCH_CONVERSION' and r['delta'] == '0' and r['N'] == '729' and r['t'] in ('1', '2') and r['s'] in ('1', '2', '4'):
        t = Fr(r['t']); y = Fr(r['y']); N = 729
        A1 = 2*abs(Fr(int(r['A_ppb']), 10**9))/N
        fo = E.first_order(Fr(0), y, N, t)
        w1r = E.readme_w1_delta0(t)
        print('  N=729 s=%s t=%s read/law=%s read/(law+full first)=%s read/(law+README w1)=%s' % (r['s'], t, dec(A1/fo['A1_law'], 4), dec(A1/fo['A1_first'], 4), dec(A1/(2*y*abs(fo['w0'] + w1r/N)), 4)))
