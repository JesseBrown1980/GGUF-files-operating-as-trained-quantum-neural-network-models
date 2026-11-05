# Own exact read of the rungs at N = 23,887,872 and 43,046,721, including the ordered point x = 0 that the route's top_compare leaves out.
# Exact o^2 and d on a block, integers at 2^220, own Sturm. Block: around the peak for x = 0, low j for x = 1/2 and x = 3/2.
import sys
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
from own_sector import build, below, level, SH
out = open(ME + 'out/own_top.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True); out.write(s + '\n'); out.flush()

CASES = [
    (43046721, '1/2', '0', 43046721 // 5 - 60000, 43046721 // 5 + 60000),
    (23887872, '1/2', '0', 23887872 // 5 - 60000, 23887872 // 5 + 60000),
    (43046721, '1/2', '1/2', 0, 6000),
    (43046721, '1/2', '1/2', 0, 12000),
    (43046721, '1/2', '3/2', 0, 300),
    (23887872, '1/2', '1/2', 0, 6000),
    (23887872, '1/2', '3/2', 0, 300),
]
for n, u, x, a, b in CASES:
    r = sec(n, u, x)
    d, o2 = build(n, u, x, 0, a, b)
    guess = int(r['e_at_2^60']) << (SH - 60)
    gap_read = F(int(r['gap_ppb']), 10 ** 9)
    span = 1 << (SH - 50)
    e0 = level(d, o2, 0, guess - span, guess + span, 1 << (SH - 120))
    gapg = (gap_read.numerator << SH) // (gap_read.denominator * n)
    e1 = level(d, o2, 1, e0 + gapg - gapg // 16 - 1, e0 + gapg + gapg // 16 + 1, 1 << (SH - 120))
    # derivative in x, exact shift of the diagonal: + h (n+ + n-)/N = h 2j/N
    h = 1 << (SH - 60)   # h = 2^-60
    def shifted(sign):
        return [v + sign * ((h * 2 * j) // n) for v, j in zip(d, range(a, b + 1))]
    up = level(shifted(1), o2, 0, e0 - span // 1024, e0 + span, 1 << (SH - 150))
    dn = level(shifted(-1), o2, 0, e0 - span, e0 + span // 1024, 1 << (SH - 150))
    f = F(up - dn, 2 * h)
    jbar = f * n / 2
    gap = F(e1 - e0, 1 << SH) * n
    e = F(e0, 1 << SH)
    P('N', n, 'u', u, 'x', x, 'block', a, b)
    P('  own e', dec(e, 12), 'read e_ppb', r['e_ppb'], 'read e_at_2^60/2^60', dec(F(int(r['e_at_2^60']), 1 << 60), 12))
    P('  own f', dec(f, 12), 'read f_ppb', r['f_ppb'], 'off ppb', dec((F(int(r['f_ppb']), 10 ** 9) - f) * 10 ** 9, 3))
    P('  own jbar', dec(jbar, 9), 'read', dec(F(int(r['jbar_ppb']), 10 ** 9), 9), 'off ppm', dec((F(int(r['jbar_ppb']), 10 ** 9) / jbar - 1) * 10 ** 6, 3))
    P('  own gap', dec(gap, 9), 'read', dec(F(int(r['gap_ppb']), 10 ** 9), 9), 'off ppm', dec((F(int(r['gap_ppb']), 10 ** 9) / gap - 1) * 10 ** 6, 4))
out.close()
