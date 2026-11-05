#!/usr/bin/env python3
# t2_run.py -- runs the frozen grids through the integer Chebyshev route; rows go to out/GRID-<grid>-N<N>.hbp, appended chain by chain.
# Usage: t2_run.py band|outside N workers threads moments
import sys, os, time
from fractions import Fraction as Fr
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import chebdrv as D
import t2_predict as G

ROOT = 'C:/tmp/opus55/polariton-recheck-contact-20261105/out/'

def main():
    grid, Nsel, workers, threads, moments = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    sel_s = None
    if len(sys.argv) > 6:
        sel_s = [Fr(v) for v in sys.argv[6].split(',')]
    gen = G.grid_band() if grid == 'band' else G.grid_outside()
    jobs = [j for j in gen if j[0] == Nsel and (sel_s is None or j[3] in sel_s)]
    path = ROOT + 'GRID-%s-N%d.hbp' % (grid, Nsel)
    done = set()
    if os.path.exists(path):
        with open(path) as fh:
            for ln in fh:
                d = D.parse_row(ln.strip())
                done.add((Fr(d['delta']), Fr(d['y'])))
    jobs = [j for j in jobs if (j[1], j[2]) not in done]
    print('jobs', len(jobs), flush=True)
    t00 = time.time()
    def work(j):
        N, d, y, s, TS = j
        t0 = time.time()
        rows = D.run_chain(N, N, 1, d, y, TS, threads=threads, moments=moments)
        return j, rows, time.time() - t0
    with open(path, 'a', newline='\n') as fh, ThreadPoolExecutor(max_workers=workers) as ex:
        for k, (j, rows, sec) in enumerate(ex.map(work, jobs)):
            fh.write('\n'.join(rows) + '\n')
            fh.flush()
            print('chain', k, 'N', j[0], 'delta', j[1], 'y', j[2], 'sec', round(sec, 1), 'total', round(time.time() - t00, 1), flush=True)
    print('finished', round(time.time() - t00, 1), flush=True)
    return 0

if __name__ == '__main__':
    sys.exit(main())
