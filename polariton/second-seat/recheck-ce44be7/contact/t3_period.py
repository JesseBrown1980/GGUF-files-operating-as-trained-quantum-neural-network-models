#!/usr/bin/env python3
# t3_period.py -- does the period pull outside the band scale away with N? First minimum of A1 for delta < -1 at N = 243 ... 59049, integer route, truncated block with edge weight read.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import chebdrv as D
from law import dec, sqrt_fp, fr

pi = Fr(314159265358979323846, 10**20)
rows_out = []
for (delta, s, tmin, tmax, nmax) in ((Fr(-5, 4), Fr(1, 4), Fr(6), Fr(9), 150), (Fr(-2), Fr(1), Fr(5, 2), Fr(9, 2), 200)):
    w = fr(sqrt_fp(delta*delta - 1))
    for (N, root) in ((243, 16), (729, 27), (2187, 47), (6561, 81), (59049, 243)):
        y = s/root
        ts = [Fr(k, 8) for k in range(int(tmin*8), int(tmax*8)+1)]
        nm = min(N, nmax)
        rows = D.run_chain(N, nm, 1, delta, y, ts, threads=2, moments=0)
        vals = []
        for r in rows:
            d = D.parse_row(r)
            vals.append((Fr(d['t']), Fr(int(d['A1_e18']), 10**18), int(d['boundary_e18'])))
        i = min(range(1, len(vals)-1), key=lambda k: vals[k][1])
        # vertex of the parabola through the three points around the grid minimum
        (t0, a0, _), (t1, a1, _), (t2, a2, _) = vals[i-1], vals[i], vals[i+1]
        h = t1 - t0
        den = a0 - 2*a1 + a2
        tv = t1 + (h/2)*(a0 - a2)/den if den != 0 else t1
        line = 'PERIOD|N=%d|nmax=%d|delta=%s|s=%s|t_minA1=%s|law_2pi_over_w=%s|ratio=%s|(1-ratio)N=%s|edge_weight_max_e18=%d|json=0' % (N, nm, delta, s, dec(tv, 4), dec(2*pi/w, 4), dec(tv*w/(2*pi), 5), dec((1 - tv*w/(2*pi))*N, 2), max(v[2] for v in vals))
        print(line, flush=True)
        rows_out.append(line)
open('C:/tmp/opus55/polariton-recheck-contact-20261105/out/PERIOD.hbp', 'w', newline=chr(10)).write(chr(10).join(rows_out) + chr(10))
