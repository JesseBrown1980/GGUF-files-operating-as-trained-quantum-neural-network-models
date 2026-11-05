#!/usr/bin/env python3
# chebdrv.py -- driver: exact Bessel coefficients with Python big integers, then the Rust propagator.
# Integers only. J_k(z), z = E t rational, by Miller's backward recurrence in big-integer fixed point,
# normalised by J_0 + 2 Sum J_2k = 1, written at 2^62.
from fractions import Fraction as Fr
import os, subprocess, sys, hashlib, threading

ROOT = 'C:/tmp/opus55/polariton-recheck-contact-20261105'
EXE = ROOT + '/cheb/target/release/cheb.exe'
TABLES = ROOT + '/tables'

def bessel_table(z, qbits=62, guard=640):
    z = Fr(z)
    if z == 0:
        return [1 << qbits]
    # start high enough that J_kstart(z) is far below 2^-(qbits+60)
    zi = int(z) + 1
    r3 = 1
    while r3*r3*r3 < zi: r3 += 1
    kstart = zi + 40*r3 + 200
    num, den = z.numerator, z.denominator
    Fp = 0            # F_{k+1}
    Fc = 1 << guard   # F_k
    vals = [0]*(kstart+1)
    vals[kstart] = Fc
    for k in range(kstart, 0, -1):
        Fm = (2*k*den*Fc)//num - Fp
        Fp, Fc = Fc, Fm
        vals[k-1] = Fc
    S = vals[0] + 2*sum(vals[2:kstart+1:2])
    out = []
    half = S >> 1
    for k in range(kstart+1):
        v = vals[k]
        if v >= 0:
            out.append(int(((v << qbits) + half)//S))
        else:
            out.append(-int((((-v) << qbits) + half)//S))
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out

def check_table(tab, qbits=62):
    # J_0^2 + 2 Sum J_k^2 = 1
    s = tab[0]*tab[0] + 2*sum(v*v for v in tab[1:])
    return (s - (1 << (2*qbits)))/ (1 << (2*qbits)) if False else s - (1 << (2*qbits))

def ratstr(x):
    x = Fr(x)
    return str(x.numerator) if x.denominator == 1 else '%d/%d' % (x.numerator, x.denominator)

def run_chain(N, nmax, u, delta, y, times, threads=1, moments=0, extra_E=0, tag=None):
    """times: list of Fractions. Returns list of ROW text lines."""
    N = int(N); nmax = int(nmax)
    us, ds, ys = ratstr(u), ratstr(delta), ratstr(y)
    r = subprocess.run([EXE, 'bound', str(N), str(nmax), us, ds, ys], capture_output=True, text=True, check=True)
    c, E = [int(v) for v in r.stdout.split()]
    E = E + int(extra_E)
    name = 'T_%d_%d_%s_%s_%s_%d_%d.txt' % (N, nmax, us.replace('/', 'o'), ds.replace('/', 'o').replace('-', 'm'), ys.replace('/', 'o').replace('-', 'm'), E, threading.get_ident() % 100000)
    path = TABLES + '/' + name
    lines = []
    for t in times:
        tab = bessel_table(Fr(E)*Fr(t))
        lines.append('%s %d' % (ratstr(t), len(tab)))
        lines.extend(str(v) for v in tab)
    with open(path, 'w', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')
    try:
        p = subprocess.run([EXE, 'run', str(N), str(nmax), us, ds, ys, str(c), str(E), path, str(threads), str(moments)],
                           capture_output=True, text=True, check=True)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    rows = [ln.strip() for ln in p.stdout.splitlines() if ln.startswith('ROW|')]
    return rows

def parse_row(row):
    d = {}
    for kv in row.split('|')[1:]:
        if '=' in kv:
            k, v = kv.split('=', 1)
            d[k] = v
    return d

if __name__ == '__main__':
    # small self test of the coefficient table: exact sum rule and a value by direct series.
    tab = bessel_table(Fr(5))
    print('BESSEL_SUM_RULE_OFF_units_2^-124', check_table(tab))
    # J_0(5) by the rational series, for comparison at 2^62
    z = Fr(5)
    s = Fr(0); term = Fr(1)
    for k in range(0, 120):
        s += term
        term = -term*(z*z/4)/((k+1)*(k+1))
    print('J0(5)_table', tab[0], 'series', int(s*(1 << 62)))
