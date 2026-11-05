# Own exact read of the sector rows. Integers at 2^220, own Sturm, shares no code with the engine or second_route.py.
# H/N in units JN = 1: n+ = j + P, n- = j, n0 = N - 2j - P.
#   diag_j = [x (n+ + n-) + (u/N)(n0 (n+ + n-) + n+ n-)] / N,  o2_j = (n+ + 1)(n- + 1) n0 (n0 - 1) / N^4
# Part 1: all 143 rows at N <= 243, off in units of 2^-60 with its fraction.
# Part 2: the top-rung ordered rows, on a block around the peak.
import sys
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
SH = 220
ONE_ = 1 << SH


def build(n, u, x, p, lo_j, hi_j):
    u, x = F(u), F(x)
    # common denominators
    du = u.denominator * x.denominator
    un = u.numerator * x.denominator
    xn = x.numerator * u.denominator
    d, o2 = [], []
    for j in range(lo_j, hi_j + 1):
        plus, minus = j + p, j
        n0 = n - 2 * j - p
        num = xn * (plus + minus) * n + un * (n0 * (plus + minus) + plus * minus)
        d.append((num << SH) // (du * n * n))
        if j < hi_j:
            o2.append((((plus + 1) * (minus + 1) * n0 * (n0 - 1)) << SH) // n ** 4)
    return d, o2


def below(d, o2, lam):
    c = 0
    q = d[0] - lam
    if q == 0:
        q = -1
    if q < 0:
        c = 1
    sh = SH
    for k in range(1, len(d)):
        q = d[k] - lam - (o2[k - 1] << sh) // q
        if q == 0:
            q = -1
        if q < 0:
            c += 1
    return c


def level(d, o2, index, lo, hi, width):
    while below(d, o2, lo) > index:
        lo -= (hi - lo)
    while below(d, o2, hi) <= index:
        hi += (hi - lo)
    while hi - lo > width:
        mid = (lo + hi) >> 1
        if below(d, o2, mid) > index:
            hi = mid
        else:
            lo = mid
    return (lo + hi) >> 1


if __name__ == '__main__':
    out = open(ME + 'out/own_sector.txt', 'w', encoding='utf-8', newline='\n')
    def P(*a):
        s = ' '.join(str(x) for x in a)
        print(s, flush=True); out.write(s + '\n'); out.flush()
    rows = [r for r in R['POLARITON_SECTOR'] if int(r['N']) <= 243]
    P('rows', len(rows))
    worst = F(0)
    hist = {}
    for r in rows:
        n, u, x, p = int(r['N']), r['u'], r['x'], int(r['P'])
        top = (n - p) // 2
        d, o2 = build(n, u, x, p, 0, top)
        read = int(r['e_at_2^60'])
        guess = read << (SH - 60)
        e = level(d, o2, 0, guess - (1 << (SH - 40)), guess + (1 << (SH - 40)), 1 << (SH - 110))
        off = F(abs(e - guess), 1 << (SH - 60))
        worst = max(worst, off)
        bucket = int(off)
        hist[bucket] = hist.get(bucket, 0) + 1
        if off >= F(1, 2):
            P(' row N', n, 'u', u, 'x', x, 'P', p, 'off units', dec(off, 3))
    P('largest off in units of 2^-60', dec(worst, 3), 'buckets', sorted(hist.items()))
    out.close()
