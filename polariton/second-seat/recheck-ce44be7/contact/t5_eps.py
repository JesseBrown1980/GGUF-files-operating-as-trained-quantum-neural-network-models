#!/usr/bin/env python3
# t5_eps.py -- the large-t form of the first correction against the exact coefficients: ratio -> 1 as gamma t grows.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import t5_eval as E
from law import law, dec, exp_fp, fp, mul, sqrt_fp, fr

N = 10**6
print('delta s t gamma_t | V2 coef machine, form, ratio | A1 coef machine, form, ratio | C1 coef machine, form, ratio')
for (delta, s) in ((Fr(0), Fr(1)), (Fr(0), Fr(4)), (Fr(1, 2), Fr(2)), (Fr(-1, 2), Fr(1, 2)), (Fr(3, 4), Fr(1)), (Fr(-3, 4), Fr(1))):
    g2 = 1 - delta*delta
    g = sqrt_fp(g2)
    for t in (Fr(6), Fr(10), Fr(16)):
        y = s/1000  # y^2 N = s^2 at N = 10^6
        fo = E.first_order(delta, y, N, t)
        L = law(N, delta, y, t)
        Y = L['Y']
        e2 = fr(exp_fp(2*mul(g, fp(t))))
        eps = (5 - 2*delta)/(8*g2*g2)*e2
        v_m = 2*fo['w1']/fo['w0'] - fo['C1v']/fo['C0']
        a_m = fo['w1']/fo['w0']
        c_m = fo['C1v']/fo['C0']
        v_f = eps*Y/(1 + Y)
        a_f = -eps*(1 + Y/2)
        c_f = -2*eps*(1 + 2*Y + Y*Y/2)/(1 + Y)
        print('%s %s %s %s | %s %s %s | %s %s %s | %s %s %s' % (delta, s, t, dec(fr(mul(g, fp(t))), 2), dec(v_m, 1), dec(v_f, 1), dec(v_m/v_f, 4), dec(a_m, 1), dec(a_f, 1), dec(a_m/a_f, 4), dec(c_m, 1), dec(c_f, 1), dec(c_m/c_f, 4)))
