#!/usr/bin/env python3
# t7_readme_check.py -- every number in the README contact section, read from the receipt and from my route. Exact rationals.
import sys, re
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import chebdrv as D
import t2_read as R
from law import law, dec

REC = 'C:/tmp/qnn-polariton-wt/polariton/RECEIPT.hbp'

def rec_rows():
    out = []
    with open(REC, encoding='utf8', newline='') as fh:
        for ln in fh:
            ln = ln.rstrip('\r\n')
            if ln.startswith('POLARITON_QUENCH_CONVERSION|'):
                d = D.parse_row(ln)
                N = int(d['N']); delta = Fr(d['delta']); y = Fr(d['y']); t = Fr(d['t'])
                A = Fr(int(d['A_ppb']), 10**9); B = Fr(int(d['B_ppb']), 10**9); C1 = Fr(int(d['C1_ppb']), 10**9); C2 = Fr(int(d['C2_ppb']), 10**9)
                out.append(dict(N=N, delta=delta, y=y, t=t, s=d['s'], A=A, B=B, C1=C1, C2=C2, A1=2*abs(A)/N, D2=2*abs(B)/N, V2=(2*A/N)**2/(2*C1),
                                f=Fr(int(d['f_ppb']), 10**9), L=law(N, delta, y, t), energy=int(d['energy_off_1e-9']), norm=int(d['norm_off_1e-9'])))
    return out

def main():
    rows = rec_rows()
    print('rows', len(rows))
    # table of the README, N=729
    print('README table check at N=729 (read from receipt, law): s, delta, t: V2 law')
    for delta in (Fr(0), Fr(1, 2)):
        for s in ('1/4', '1/2', '1', '2', '4'):
            cells = []
            for t in (Fr(1), Fr(2), Fr(3)):
                r = [x for x in rows if x['N'] == 729 and x['delta'] == delta and x['s'] == s and x['t'] == t][0]
                cells.append('%s %s' % (dec(r['V2'], 5), dec(r['L']['V2'], 5)))
            print('  %s %s | %s' % (delta, s, ' | '.join(cells)))
    big = [r for r in rows if r['N'] >= 243]
    v = [r for r in big if r['L']['f'] <= Fr(1, 10)]
    print('N>=243, f_pred<=1/10: rows=%d V2/law=%s..%s within5=%d' % (len(v), dec(min(r['V2']/r['L']['V2'] for r in v), 4), dec(max(r['V2']/r['L']['V2'] for r in v), 4), sum(1 for r in v if abs(r['V2']/r['L']['V2']-1) <= Fr(1, 20))))
    w = [r for r in big if r['L']['f'] <= Fr(1, 20)]
    print('N>=243, f_pred<=1/20: rows=%d A1 within5=%d D2 within10=%d C1 within5=%d' % (len(w), sum(1 for r in w if abs(r['A1']/r['L']['A1']-1) <= Fr(1, 20)), sum(1 for r in w if abs(r['D2']/r['L']['D2']-1) <= Fr(1, 10)), sum(1 for r in w if abs(r['C1']/r['L']['C1']-1) <= Fr(1, 20))))
    print('  V2 at those rows: %s..%s' % (dec(min(r['V2']/r['L']['V2'] for r in w), 4), dec(max(r['V2']/r['L']['V2'] for r in w), 4)))
    print('signs: f_pred<=1/10 rows: <A> negative %d of %d, <B> positive %d of %d (the 58 of 58 if counted over two signs of 29)' % (sum(1 for r in v if r['A'] < 0), len(v), sum(1 for r in v if r['B'] > 0), len(v)))
    print('signs all 94: <A> negative %d, <B> positive %d' % (sum(1 for r in rows if r['A'] < 0), sum(1 for r in rows if r['B'] > 0)))
    print('negative B rows:', [(r['N'], str(r['delta']), r['s'], str(r['t'])) for r in rows if r['B'] <= 0])
    print('energy max |off| 1e-9 over 94: %d ; norm max |off| %d' % (max(abs(r['energy']) for r in rows), max(abs(r['norm']) for r in rows)))
    p = [r for r in big if r['L']['f'] > Fr(1, 10)]
    print('past range: rows=%d V2/law=%s..%s A1/law min=%s C1/law min=%s' % (len(p), dec(min(r['V2']/r['L']['V2'] for r in p), 4), dec(max(r['V2']/r['L']['V2'] for r in p), 4), dec(min(r['A1']/r['L']['A1'] for r in p), 4), dec(min(r['C1']/r['L']['C1'] for r in p), 4)))
    n81 = [r for r in rows if r['N'] == 81]
    print('N=81: V2/law %s..%s ; max V2 %s ; lowest row:' % (dec(min(r['V2']/r['L']['V2'] for r in n81), 4), dec(max(r['V2']/r['L']['V2'] for r in n81), 4), dec(max(r['V2'] for r in n81), 4)))
    lo = min(n81, key=lambda r: r['V2']/r['L']['V2'])
    print('   ', lo['delta'], lo['s'], lo['t'], dec(lo['V2'], 5), dec(lo['L']['V2'], 5), 'f', dec(lo['f'], 4))
    print('above 1: ', [(r['N'], str(r['delta']), r['s'], str(r['t']), dec(r['V2'], 4)) for r in rows if r['V2'] > 1])
    print('approach, delta=0, s=1/2, t=2: V2/law, A1/law, C1/law, then successive ratios of the deviation')
    ap = sorted([r for r in rows if r['delta'] == 0 and r['s'] == '1/2' and r['t'] == 2], key=lambda r: r['N'])
    for r in ap:
        print('   N=%d y2N=%s  V2 %s A1 %s C1 %s' % (r['N'], dec(r['y']*r['y']*r['N'], 4), dec(r['V2']/r['L']['V2'], 4), dec(r['A1']/r['L']['A1'], 4), dec(r['C1']/r['L']['C1'], 4)))
    for key in ('V2', 'A1', 'C1'):
        devs = [r[key]/r['L'][key]-1 for r in ap]
        print('   %s dev ratios: %s' % (key, ' '.join(dec(devs[i]/devs[i+1], 3) for i in range(len(devs)-1))))
    # the frozen C1 misses
    miss = [r for r in w if abs(r['C1']/r['L']['C1']-1) > Fr(1, 20)]
    print('C1 misses:', [(r['N'], str(r['delta']), r['s'], str(r['t']), dec(r['C1'], 4), dec(r['L']['C1'], 4), dec(r['C1']/r['L']['C1'], 3)) for r in miss])
    # delta=+1 grid
    g = [r for r in R.merged('band') if r['delta'] == 1]
    print('delta=+1 grid rows=%d <A> positive=%d C1 negative=%d V2 negative=%d' % (len(g), sum(1 for r in g if r['A'] > 0), sum(1 for r in g if r['C1'] < 0), sum(1 for r in g if r['V2'] < 0)))
    gs = [r for r in g if r['f'] <= Fr(1, 10)]
    print('delta=+1, f_read<=1/10 rows=%d <A> positive=%d C1 negative=%d V2 negative=%d' % (len(gs), sum(1 for r in gs if r['A'] > 0), sum(1 for r in gs if r['C1'] < 0), sum(1 for r in gs if r['V2'] < 0)))
    for r in g:
        if r['C1'] >= 0:
            print('   C1>=0: N=%d s=%s t=%s C1=%s V2=%s f=%s' % (r['N'], r['s'], r['t'], dec(r['C1'], 6), dec(r['V2'], 3), dec(r['f'], 3)))
    # V2>1 inside the band
    allb = [r for r in R.merged('band') if r['delta'] != 1]
    print('in-band grid, V2>1 rows by N:', {N: sum(1 for r in allb if r['N'] == N and r['V2'] > 1) for N in (81, 243, 729)})
    print('  largest V2 in band by N:', {N: dec(max(r['V2'] for r in allb if r['N'] == N), 4) for N in (81, 243, 729)})
    print('  negative C1 in band (delta<1) by N:', {N: sum(1 for r in allb if r['N'] == N and r['C1'] < 0) for N in (81, 243, 729)})
    return 0

if __name__ == '__main__':
    sys.exit(main())
