#!/usr/bin/env python3
# t6_spread.py -- std(cos theta) of the law's Rician phase against Y, and Y inverted from the spread read by eye off the paper's Fig S23.
# <cos theta>^2 = R(Y) = (pi/4) Y exp(-Y) [I0(Y/2) + I1(Y/2)]^2 ; <cos 2 theta> = 1 - (1 - exp(-Y))/Y. Exact rationals to 40 digits.
from fractions import Fraction as Fr
from math import isqrt
import sys
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
from law import dec
import t4_trace_read as TR

def expm(Y):
    Y = Fr(Y); s = Fr(0); t = Fr(1)
    for k in range(1, 400):
        s += t
        t = t*(-Y)/k
        t = Fr((t.numerator*10**40)//t.denominator, 10**40)
    return s

def rt(x):
    x = Fr(x)
    return Fr(isqrt((x.numerator << 400)//x.denominator), 1 << 200)

def spread(Y):
    Y = Fr(Y)
    R = TR.Rician(Y)
    c2 = 1 - (1 - expm(Y))/Y
    var = (1 + c2)/2 - R
    return rt(var), R, c2

print('Y  std(cos theta)  R1^2  <cos 2 theta>  V2_law')
for Y in (Fr(175, 10000), Fr(741, 10000), Fr(1, 4), Fr(1, 2), Fr(1), Fr(3, 2), Fr(2), Fr(3), Fr(4), Fr(6), Fr(8), Fr(12), Fr(20), Fr(40)):
    s, R, c2 = spread(Y)
    print('%s %s %s %s %s' % (dec(Y, 4), dec(s, 4), dec(R, 4), dec(c2, 4), dec(Y/(1+Y), 4)))

def inv(target):
    lo, hi = Fr(1, 1000), Fr(40)
    for _ in range(36):
        mid = (lo+hi)/2
        mid = Fr((mid.numerator*10**10)//mid.denominator, 10**10)
        if spread(mid)[0] > target:
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2

print()
print('Spread read from the raster of Fig S23 right panel: marker centres x = 246.65, 132.32, 70.34, 49.34, 53.65 px, ticks 0.25 at x = 96, 0.50 at x = 184.5 (out/t6_figaxis.txt), so 0.676, 0.353, 0.178, 0.118, 0.130, +-0.003. Threshold about 14 mW.')
for P, st in ((Fr(121, 10), Fr(70, 100)), (Fr(150, 10), Fr(3526, 10000)), (Fr(182, 10), Fr(1775, 10000)), (Fr(216, 10), Fr(1182, 10000)), (Fr(252, 10), Fr(1304, 10000))):
    if st >= Fr(70, 100):
        print('P=%s mW spread=%s : at the uniform value' % (dec(P, 1), dec(st, 2)))
        continue
    Y = inv(st)
    print('P=%s mW spread=%s -> Y=%s V2_law=%s R1^2=%s y sqrt N at delta=0=%s' % (dec(P, 1), dec(st, 2), dec(Y, 2), dec(Y/(1+Y), 3), dec(spread(Y)[1], 3), dec(rt(Y/2), 2)))
for Y in (Fr(175, 10000), Fr(741, 10000)):
    print('the README reading Y=%s predicts spread %s' % (dec(Y, 4), dec(spread(Y)[0], 4)))
