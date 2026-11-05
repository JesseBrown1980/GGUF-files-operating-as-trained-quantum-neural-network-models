#!/usr/bin/env python3
# t2_compare_receipt.py -- every receipt row at u=1 from |N,0,0> that names (N, delta, y, t) is read by the separate
# integer Chebyshev route and compared in the receipt's own units (ppb on A, B, jbar, C1, C2, f).
# Writes out/compare_receipt.hbp as rows. Integers only on the model side; the differences are integers in 1e-9 units.
import sys, os, time, hashlib
from fractions import Fraction as Fr
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import chebdrv as D

REC = 'C:/tmp/qnn-polariton-wt/polariton/RECEIPT.hbp'
OUT = 'C:/tmp/opus55/polariton-recheck-contact-20261105/out/compare_receipt.hbp'

def rows_of():
    rows = []
    with open(REC, encoding='utf8', newline='') as fh:
        for ln in fh:
            ln = ln.rstrip('\r\n')
            if ln.startswith('POLARITON_QUENCH_CONVERSION|') or ln.startswith('POLARITON_TAYLOR_CONVERT|') or ln.startswith('POLARITON_QUENCH_PIN|'):
                d = {}
                parts = ln.split('|')
                d['tag'] = parts[0]
                for kv in parts[1:]:
                    if '=' in kv:
                        k, v = kv.split('=', 1)
                        d[k] = v
                rows.append(d)
    return rows

def key(d):
    return (int(d['N']), d['u'], d['x'], d['y'], d.get('delta', ''))

def main():
    rows = rows_of()
    chains = {}
    for d in rows:
        chains.setdefault(key(d), []).append(d)
    print('rows', len(rows), 'chains', len(chains), flush=True)
    results = []
    def work(k):
        N, us, xs, ys, ds = k
        u = Fr(us); x = Fr(xs); y = Fr(ys)
        delta = x + u
        times = sorted(set(Fr(d['t']) for d in chains[k]))
        th = 4 if N >= 729 else 1
        t0 = time.time()
        out = D.run_chain(N, N, u, delta, y, times, threads=th, moments=1)
        return k, out, time.time() - t0
    # N = 2187 last, one at a time
    small = [k for k in chains if k[0] < 729]
    big = [k for k in chains if k[0] >= 729]
    with ThreadPoolExecutor(max_workers=4) as ex:
        for r in ex.map(work, small):
            results.append(r)
    for k in sorted(big):
        results.append(work(k))
        print('done', k[:1], k[3], k[4], round(results[-1][2], 1), flush=True)
    mine = {}
    for k, out, sec in results:
        for row in out:
            d = D.parse_row(row)
            mine[(k, Fr(d['t']))] = d
    worst = {}
    lines = []
    for d in rows:
        k = key(d)
        m = mine[(k, Fr(d['t']))]
        def e18_to_ppb(s): return Fr(int(s), 10**9)
        # receipt ppb integer versus mine
        N = int(d['N'])
        mine_A = Fr(int(m['A_e18']), 10**18)*N      # <A>, in the receipt's A_ppb units after 1e9
        mine_B = Fr(int(m['B_e18']), 10**18)*N
        mine_j = Fr(int(m['jbar_e12']), 10**12)
        pairs = {
            'A': (Fr(int(d['A_ppb']), 10**9), mine_A),
            'jbar': (Fr(int(d['jbar_ppb']), 10**9), mine_j),
        }
        if 'B_ppb' in d:
            pairs['B'] = (Fr(int(d['B_ppb']), 10**9), mine_B)
            pairs['C1'] = (Fr(int(d['C1_ppb']), 10**9), Fr(int(m['C1_e18']), 10**18))
            pairs['C2'] = (Fr(int(d['C2_ppb']), 10**9), Fr(int(m['C2_e18']), 10**18))
            pairs['f'] = (Fr(int(d['f_ppb']), 10**9), Fr(int(m['f_e18']), 10**18))
        elif 'C1_ppm' in d:
            pairs['C1'] = (Fr(int(d['C1_ppm']), 10**6), Fr(int(m['C1_e18']), 10**18))
            pairs['C2'] = (Fr(int(d['C2_ppm']), 10**6), Fr(int(m['C2_e18']), 10**18))
        vals = []
        for name, (a, b) in pairs.items():
            off = abs(a-b)
            rel = off/abs(a) if a != 0 else Fr(0)
            tagk = (d['tag'], name)
            if tagk not in worst or off > worst[tagk][0]:
                worst[tagk] = (off, rel, N, d.get('y'), d.get('delta'), d['t'])
            vals.append('%s_off_e12=%d' % (name, int(off*10**12)))
        lines.append('CMP|tag=%s|N=%d|delta=%s|y=%s|t=%s|%s|mine_norm_off_e18=%s|mine_energy_e18=%s|identity_X_off_e18=%s|mine_Aim_e18=%s|json=0' % (
            d['tag'], N, d.get('delta', ''), d['y'], d['t'], '|'.join(vals), m['norm_off_e18'], m['energy_over_N_e18'], m.get('identity_X_off_e18', ''), m['Aim_e18']))
    with open(OUT, 'w', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')
    for tagk, w in sorted(worst.items()):
        print('WORST|tag=%s|obs=%s|abs_off=%.3e|rel_off=%.3e|at_N=%d|y=%s|delta=%s|t=%s' % (tagk[0], tagk[1], float(w[0]), float(w[1]), w[2], w[3], w[4], w[5]))
    secs = sum(r[2] for r in results)
    print('chains', len(results), 'seconds_sum', round(secs, 1))
    return 0

if __name__ == '__main__':
    sys.exit(main())
