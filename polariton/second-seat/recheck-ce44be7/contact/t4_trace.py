#!/usr/bin/env python3
# t4_trace.py -- exact time traces through the first depletion peak and the recurrence, from the integer Chebyshev route.
# Usage: t4_trace.py N threads moments  ; rows go to out/TRACE-N<N>.hbp
import sys, os, time
from fractions import Fraction as Fr
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import chebdrv as D
ROOT = 'C:/tmp/opus55/polariton-recheck-contact-20261105/out/'
DEN = {81: 9, 243: 16, 729: 27, 2187: 47, 6561: 81}
def main():
    N, threads, moments, workers = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    TT = [Fr(k, 4) for k in range(1, 49)]   # t = 1/4 ... 12
    SS = [Fr(1, 8), Fr(1, 4), Fr(1, 2), Fr(1), Fr(2), Fr(4)]
    DD = [Fr(0), Fr(1, 2), Fr(-1, 2), Fr(-1)]
    jobs = [(N, d, s/DEN[N], s) for d in DD for s in SS]
    path = ROOT + 'TRACE-N%d.hbp' % N
    done = set()
    if os.path.exists(path):
        for ln in open(path):
            dd = D.parse_row(ln.strip())
            done.add((Fr(dd['delta']), Fr(dd['y'])))
    jobs = [j for j in jobs if (j[1], j[2]) not in done]
    def work(j):
        t0 = time.time()
        rows = D.run_chain(j[0], j[0], 1, j[1], j[2], TT, threads=threads, moments=moments)
        return j, rows, time.time() - t0
    with open(path, 'a', newline='\n') as fh, ThreadPoolExecutor(max_workers=workers) as ex:
        for j, rows, sec in ex.map(work, jobs):
            fh.write('\n'.join(rows) + '\n'); fh.flush()
            print('chain', j[0], j[1], j[2], round(sec, 1), flush=True)
    print('finished', flush=True)
if __name__ == '__main__':
    sys.exit(main())
