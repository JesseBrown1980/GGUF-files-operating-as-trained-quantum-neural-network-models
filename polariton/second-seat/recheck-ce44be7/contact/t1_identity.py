#!/usr/bin/env python3
# t1_identity.py -- exact small-N check, all in Fractions, sharing no code with the repo.
# Representation: homogeneous polynomials of degree N in (x0, xp, xm). a^dag = multiply, a = d/dx.
# Monomial x0^a xp^b xm^c has norm^2 a! b! c!. Every operator below is an INTEGER matrix in this basis,
# so the square roots of the Fock basis never appear and expectations are exact rationals (Gaussian rationals).
from fractions import Fraction as Fr
from math import factorial
import random, sys

def basis(N):
    return [(N-p-m, p, m) for p in range(N+1) for m in range(N+1-p)]

# an operator is a function monomial -> dict monomial -> int
def op_mul_d(i, j):
    # a_i^dag a_j
    def f(mon):
        if mon[j] == 0: return {}
        c = mon[j]
        m = list(mon); m[j] -= 1; m[i] += 1
        return {tuple(m): c}
    return f

def compose(f, g):
    # f after g : (f g)(mon)
    def h(mon):
        out = {}
        for k, c in g(mon).items():
            for k2, c2 in f(k).items():
                out[k2] = out.get(k2, 0) + c*c2
        return out
    return h

def add(*fs):
    def h(mon):
        out = {}
        for s, f in fs:
            for k, c in f(mon).items():
                out[k] = out.get(k, 0) + s*c
        return out
    return h

def op_four(i, j, k, l):
    # a_i^dag a_j^dag a_k a_l applied as polynomial operator
    def f(mon):
        m = list(mon)
        c = 1
        c *= m[l]
        if c == 0: return {}
        m[l] -= 1
        c *= m[k]
        if c == 0: return {}
        m[k] -= 1
        m[j] += 1
        m[i] += 1
        return {tuple(m): c}
    return f

Z, P, M = 0, 1, 2

A   = add((1, op_mul_d(Z, P)), (1, op_mul_d(M, Z)))    # a0^dag a+ + a-^dag a0
Ad  = add((1, op_mul_d(P, Z)), (1, op_mul_d(Z, M)))    # a+^dag a0 + a0^dag a-
n0  = op_mul_d(Z, Z)
np_ = op_mul_d(P, P)
nm  = op_mul_d(M, M)
Pair  = op_four(P, M, Z, Z)
Paird = op_four(Z, Z, P, M)
def diag_nn(i, j):  # :n_i n_j: for i != j, n_i n_j
    return compose(op_mul_d(i, i), op_mul_d(j, j))
X_direct = add((1, diag_nn(Z, P)), (1, diag_nn(Z, M)), (1, Pair), (1, Paird))
AdA = compose(Ad, A)
X_from_AdA = add((1, AdA), (-1, n0), (-1, np_))

def matrix_equal(f, g, N):
    bad = 0
    for mon in basis(N):
        a = {k: v for k, v in f(mon).items() if v != 0}
        b = {k: v for k, v in g(mon).items() if v != 0}
        if a != b: bad += 1
    return bad

# complex rationals as (Fr, Fr)
class C:
    __slots__ = ('re', 'im')
    def __init__(s, re=0, im=0):
        s.re = Fr(re); s.im = Fr(im)
    def __add__(s, o): return C(s.re+o.re, s.im+o.im)
    def __sub__(s, o): return C(s.re-o.re, s.im-o.im)
    def __mul__(s, o):
        if not isinstance(o, C): o = C(o)
        return C(s.re*o.re - s.im*o.im, s.re*o.im + s.im*o.re)
    def conj(s): return C(s.re, -s.im)
    def abs2(s): return s.re*s.re + s.im*s.im

def norm2(mon):
    return factorial(mon[0])*factorial(mon[1])*factorial(mon[2])

def apply(f, psi):
    out = {}
    for mon, amp in psi.items():
        for k, c in f(mon).items():
            out[k] = out.get(k, C()) + amp*C(c)
    return out

def inner(phi, psi):
    tot = C()
    for mon, amp in psi.items():
        if mon in phi:
            tot = tot + phi[mon].conj()*amp*C(norm2(mon))
    return tot

def expect(f, psi, nn):
    v = inner(psi, apply(f, psi))
    return C(v.re/nn, v.im/nn)

# g2 by the definition: Sum_{m+n=p+q} <a_m^dag a_n^dag a_p a_q> e^{ik(p-n)r}, read harmonic by harmonic.
LAB = {0: Z, 1: P, -1: M}
def g2_harmonics(psi, nn):
    # returns dict h -> complex coefficient of e^{ikhr}
    h = {}
    for m in (0, 1, -1):
        for n in (0, 1, -1):
            for p in (0, 1, -1):
                for q in (0, 1, -1):
                    if m+n != p+q: continue
                    # a_m^dag a_n^dag a_p a_q
                    f = op_four(LAB[m], LAB[n], LAB[p], LAB[q])
                    v = expect(f, psi, nn)
                    key = p-n
                    h[key] = h.get(key, C()) + v
    return h

def run_state(N, psi, label):
    nn = inner(psi, psi).re
    a = expect(A, psi, nn)
    ada = expect(AdA, psi, nn)
    n0e = expect(n0, psi, nn)
    npe = expect(np_, psi, nn)
    h = g2_harmonics(psi, nn)
    # g2(r) = 1 + C1 cos kr + C2 cos 2kr + (sine part if any)
    h0 = h[0]; h1 = h[1]; hm1 = h[-1]; h2 = h[2]; hm2 = h[-2]
    norm = Fr(N*(N-1))
    C1 = (h1.re + hm1.re)/norm
    C1_sin = (h1.im - hm1.im)/norm
    C2 = (h2.re + hm2.re)/norm
    A1 = None
    A1sq = 4*a.abs2()/Fr(N*N)
    if C1 == 0:
        return (label, 'C1=0', a.abs2())
    V2_def = A1sq/(2*C1)
    denom = ada.re - n0e.re - npe.re
    V2_id = Fr(N-1, N)*a.abs2()/denom
    ok = (V2_def == V2_id)
    return (label, 'N=%d' % N, 'h0/N(N-1)=%s' % str(h0.re/norm), 'h0im=%s' % str(h0.im), 'C1_sin=%s' % str(C1_sin),
            'imAd A=%s' % str(ada.im), 'identity_exact=%s' % ok,
            'V2_id=%.12g' % float(V2_id), 'C1=%.12g' % float(C1), 'C2=%.12g' % float(C2))

def rand_state(N, rng, parity_sym, complex_amp, sparse=None):
    psi = {}
    for mon in basis(N):
        if sparse is not None and rng.random() > sparse: continue
        re = Fr(rng.randint(-9, 9), rng.randint(1, 9))
        im = Fr(rng.randint(-9, 9), rng.randint(1, 9)) if complex_amp else Fr(0)
        psi[mon] = C(re, im)
    if not psi:
        psi[(N, 0, 0)] = C(1)
    if parity_sym:
        out = {}
        for mon, v in psi.items():
            mir = (mon[0], mon[2], mon[1])
            out[mon] = out.get(mon, C()) + v
            out[mir] = out.get(mir, C()) + v
        psi = out
    return psi

def main():
    rng = random.Random(2026110501)
    print("IDENTITY_MATRIX|statement=A^dag A - n0 - n+ == n0(n+ + n-) + P + P^dag|integer_matrices_in_monomial_basis|json=0")
    tot_bad = 0
    for N in range(0, 26):
        bad = matrix_equal(X_direct, X_from_AdA, N)
        tot_bad += bad
    print("IDENTITY_MATRIX|N=0..25|rows_differing=%d|json=0" % tot_bad)
    # commutator [A, A^dag] = n- - n+
    comm = add((1, compose(A, Ad)), (-1, AdA))
    target = add((1, nm), (-1, np_))
    tb = sum(matrix_equal(comm, target, N) for N in range(0, 26))
    print("COMMUTATOR|[A,A^dag]=n- - n+|N=0..25|rows_differing=%d|json=0" % tb)
    states_ok = 0; states_tot = 0
    for N in (2, 3, 4, 5, 6, 8, 12):
        for (par, cx, label) in ((True, False, 'parity_real'), (True, True, 'parity_complex'), (False, False, 'noparity_real'), (False, True, 'noparity_complex')):
            for rep in range(4):
                psi = rand_state(N, rng, par, cx, sparse=(None if rep < 2 else 0.5))
                r = run_state(N, psi, label+'#%d' % rep)
                states_tot += 1
                if 'identity_exact=True' in r:
                    states_ok += 1
                if rep == 0 and N in (3, 6):
                    print("STATE|" + "|".join(str(v) for v in r) + "|json=0")
    print("STATE_SUMMARY|states=%d|identity_exact=%d|json=0" % (states_tot, states_ok))
    # the Fock start: C1 = 0 and <A> = 0 -> 0/0 at t=0.
    N = 5
    psi = {(N, 0, 0): C(1)}
    print("START|N=5|" + "|".join(str(v) for v in run_state(N, psi, 'fock')) + "|json=0")
    # a state with V^2 > 1 at small N: X < |A|^2 is possible. Search parity_real small N for the bound.
    # V^2 can exceed 1 or be negative: exhibit exact witnesses.
    wit_neg = None; wit_big = None
    for N in (3, 4, 5, 6):
        for rep in range(4000):
            psi = rand_state(N, rng, True, False, sparse=0.35)
            nn = inner(psi, psi).re
            if nn == 0: continue
            a = expect(A, psi, nn); ada = expect(AdA, psi, nn); n0e = expect(n0, psi, nn); npe = expect(np_, psi, nn)
            den = ada.re - n0e.re - npe.re
            if den == 0 or a.abs2() == 0: continue
            v = Fr(N-1, N)*a.abs2()/den
            if v < 0 and wit_neg is None: wit_neg = (N, float(v))
            if v > 1 and wit_big is None: wit_big = (N, float(v))
    print("WITNESS|V2_negative_exists=%s|V2_above_1_exists=%s|searched=random_parity_real_N=3..6|json=0" % (wit_neg, wit_big))
    return 0

if __name__ == '__main__':
    sys.exit(main())
