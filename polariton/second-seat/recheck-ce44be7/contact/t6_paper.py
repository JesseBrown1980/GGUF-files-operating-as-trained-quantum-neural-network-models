#!/usr/bin/env python3
# t6_paper.py -- the README's reading of the 2.6%: its arithmetic, and what the law then says about other numbers the paper gives.
# Exact rationals; roots by integer isqrt at 2^-200.
from fractions import Fraction as Fr
from math import isqrt
import sys
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
from law import dec
import t4_trace_read as TR

def rt(x):
    x = Fr(x)
    return Fr(isqrt((x.numerator << 400)//x.denominator), 1 << 200)

A = Fr(26, 1000)
K = Fr(5, 1000)
rho = K/(1 + 2*K)      # K = rho/rho0, rho0 = 1 - 2 rho
rho0 = 1 - 2*rho
print('rho=%s rho0=%s' % (dec(rho, 6), dec(rho0, 6)))
r1 = A*A/(8*rho0*rho)
r1b = A*A/(8*K)
print('(1-d)V2 from A^2 = 8 rho0 rho (1-d) V2: %s; with rho0=1, rho=K: %s; README 0.017' % (dec(r1, 5), dec(r1b, 5)))
print('paper K = A^2/4 gives %s; a density 1 + A cos kx has K = A^2/16 = %s' % (dec(A*A/4, 7), dec(A*A/16, 8)))
r2 = 4*r1
print('with the paper factor (A^2/4 against A^2/16, a factor 4): %s ; with rho0=1 %s; README 0.068' % (dec(r2, 5), dec(4*r1b, 5)))

def s_of(V2, delta=Fr(0)):
    Y = V2/(1-V2)
    return rt(Y*(1+delta)/2)

print('y sqrt N at delta=0, tanh->1: for 0.017 %s ; for 0.068 %s ; README 0.09, 0.19' % (dec(s_of(Fr(17, 1000)), 4), dec(s_of(Fr(68, 1000)), 4)))
print('exact values with (1-d)V2 = %s, %s: %s, %s' % (dec(r1, 5), dec(r2, 5), dec(s_of(r1), 4), dec(s_of(r2), 4)))
print('delta dependence: (1-d)V2 = c, V2 = c/(1-d), Y = 2 s^2/(1+d)')
for d in (Fr(-1), Fr(-3, 4), Fr(-1, 2), Fr(-1, 4), Fr(0), Fr(1, 4), Fr(1, 2), Fr(3, 4)):
    res = []
    for c in (Fr(17, 1000), Fr(68, 1000)):
        V2 = c/(1-d)
        if d == -1:
            # Y = N y^2 t^2 at the edge: give y sqrt(N) t
            Y = V2/(1-V2)
            res.append('V2=%s s*t=%s' % (dec(V2, 4), dec(rt(Y), 4)))
        else:
            res.append('V2=%s s=%s' % (dec(V2, 4), dec(s_of(V2, d), 4)))
    print('  delta=%s : %s | %s' % (d, res[0], res[1]))
print()
print('WHAT ELSE THE LAW SAYS, large t, from A = 2.6%, K = 0.5%:')
for (name, c, A1) in (('reading A1=A', r1, A), ('reading A1=2A (paper factor)', r2, 2*A)):
    print(' %s: (1-d)V2=%s' % (name, dec(c, 4)))
    print('   C1 = 4 rho (1-d) = %s x (1-d), against A1^2/2 = %s' % (dec(4*rho, 5), dec(A1*A1/2, 6)))
    print('   D2 = A1^2/(4(1-d)) = %s /(1-d)' % dec(A1*A1/4, 6))
    print('   single-shot harmonic sqrt(2 C1) = %s x sqrt(1-d)' % dec(rt(8*rho), 4))
    print('   phase coherence of the position R1^2 ~ (pi/4) Y at small Y, at delta=0: Y=%s, R1^2=%s, R1=%s' % (dec(c/(1-c), 4), dec(TR.Rician(c/(1-c)), 4), dec(rt(TR.Rician(c/(1-c))), 4)))
print(' g1(r) averaged over x = (1 - 2 rho) + 2 rho cos kr: fast oscillation amplitude 2 rho = %s ; the paper reads about 1.5%%, which would be K about %s' % (dec(2*rho, 5), dec(Fr(15, 2000)/(1-Fr(15, 1000)), 5)))
print()
print('PHASE WIDTH: the paper SI, Fig S22b: phase distribution at fixed k_r narrows to about 135 degrees at 500 uW, "mostly distributed over the first quadrant".')
pi = Fr(314159265358979323846, 10**20)
# sin(x) by exact series
def sin_fr(x):
    x = Fr(x); s = Fr(0); t = x
    for k in range(1, 40):
        s += t
        t = -t*x*x/((2*k)*(2*k+1))
        t = Fr((t.numerator*10**40)//t.denominator, 10**40)
    return s
def cos_fr(x):
    x = Fr(x); s = Fr(0); t = Fr(1)
    for k in range(1, 40):
        s += t
        t = -t*x*x/((2*k-1)*(2*k))
        t = Fr((t.numerator*10**40)//t.denominator, 10**40)
    return s
def exp_fr(x):
    x = Fr(x); s = Fr(0); t = Fr(1)
    for k in range(1, 200):
        s += t
        t = t*x/k
        t = Fr((t.numerator*10**40)//t.denominator, 10**40)
    return s
wid = Fr(135, 180)*pi
R_uni = sin_fr(wid/2)/(wid/2)
print(' if uniform over 135 deg: R1 = %s, R1^2 = %s' % (dec(R_uni, 4), dec(R_uni*R_uni, 4)))
# wrapped normal with 135 deg = FWHM: sigma = wid/2.3548; with 135 deg = 4 sigma
for nm, sig in (('135 deg as FWHM', wid/(Fr(23548, 10000))), ('135 deg as 4 sigma', wid/4)):
    R = exp_fr(-sig*sig/2)
    print(' wrapped normal, %s: sigma=%s rad, R1=%s, R1^2=%s' % (nm, dec(sig, 3), dec(R, 4), dec(R*R, 4)))
def inv_R(target):
    lo, hi = Fr(0), Fr(40)
    for _ in range(40):
        mid = (lo+hi)/2
        mid = Fr((mid.numerator*10**12)//mid.denominator, 10**12)
        if TR.Rician(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo+hi)/2
for nm, Rsq in (('uniform 135', R_uni*R_uni), ('FWHM 135', exp_fr(-(wid/Fr(23548, 10000))**2)), ('4 sigma 135', exp_fr(-(wid/4)**2))):
    Y = inv_R(Rsq)
    V2 = Y/(1+Y)
    print(' read through the Rician of the law: %s: R1^2=%s -> Y=%s, V2_law=%s, y sqrt N at delta=0 = %s, implied A1 = sqrt(8 rho0 rho V2) = %s' % (nm, dec(Rsq, 4), dec(Y, 3), dec(V2, 3), dec(rt(Y/2), 3), dec(rt(8*rho0*rho*V2), 4)))
# transverse rotation of 1.1 pi
sinc = sin_fr(Fr(55, 100)*pi)/(Fr(55, 100)*pi)
print(' transverse rotation 1.1 pi, if the 2.6%% is a transverse average with uniform weight: factor %s on A, so A1 before it = %s, (1-d)V2 = %s, and with the paper factor %s; y sqrt N at delta=0 %s, %s' % (
    dec(sinc, 4), dec(A/sinc, 4), dec(r1/(sinc*sinc), 4), dec(r2/(sinc*sinc), 4), dec(s_of(r1/(sinc*sinc)), 3), dec(s_of(r2/(sinc*sinc)), 3)))
print(' time-integration: if V^2 is fixed and A1 follows sqrt(rho(t)), <A1>^2 <= 8(1-d)V2 <rho> by Cauchy-Schwarz, so A^2/(8<rho>) is a lower bound on (1-d)V2 under that assumption.')
