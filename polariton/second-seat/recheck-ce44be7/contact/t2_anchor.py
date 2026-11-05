#!/usr/bin/env python3
# t2_anchor.py -- a third route, separate from the Rust Chebyshev reader and from the repo's leapfrog:
# exact Taylor series of exp(-iHt)|N,0,0> in big-integer fixed point at 2^-Pbits on the orthonormal Fock basis.
# All integers (math.isqrt for the roots at 2^-Pbits). Terms grow to (E t)^k/k! so Pbits is set well above log2 of that peak.
# Rows: N, delta, y, t given on the command line as rationals. Prints the same observables at 30 digits.
import sys, time
from fractions import Fraction as Fr
from math import isqrt, factorial

def run(N, delta, y, t, u=Fr(1), Pbits=None):
    delta, y, t, u = Fr(delta), Fr(y), Fr(t), Fr(u)
    x = delta - u
    # half space with mirrors would save time, but full space keeps this short.
    states = [(p, m) for p in range(N+1) for m in range(N+1-p)]
    idx = {s: i for i, s in enumerate(states)}
    # Bound for H: Gershgorin, in integers (crude, only sets the truncation)
    ybound = abs(y)
    Et = Fr(0)
    Emax = 0
    for (p, m) in states:
        n = p+m; n0 = N-n
        d = abs(x*n + u*Fr(n0*n + p*m, N))
        r = d + (Fr(isqrt((p+1)*(m+1)*n0*(n0-1)) + 1, N) if n0 >= 2 else 0)
        r += (Fr(isqrt(p*m*(n0+2)*(n0+1)) + 1, N) if p >= 1 and m >= 1 else 0)
        r += ybound*(isqrt((p+1)*n0) + isqrt((m+1)*n0) + isqrt(p*(n0+1)) + isqrt(m*(n0+1)) + 4)
        if r > Emax: Emax = r
    z = Emax*t
    zi = int(z) + 1
    # peak of z^k/k! is about e^z: log2 = z*1.4427
    peak_bits = (zi*1443)//1000 + 8
    if Pbits is None:
        Pbits = peak_bits + 256
    ONE = 1 << Pbits
    # matrix rows in integers at Pbits: diag, then (col, value)
    diag = [((x*(p+m) + u*Fr((N-p-m)*(p+m) + p*m, N)).numerator << Pbits)//(x*(p+m) + u*Fr((N-p-m)*(p+m) + p*m, N)).denominator for (p, m) in states]
    def rootp(val):  # sqrt(val) at Pbits
        return isqrt(val << (2*Pbits))
    off = []
    yn, yd = y.numerator, y.denominator
    for (p, m) in states:
        n0 = N-p-m
        row = []
        if n0 >= 2:
            row.append((idx[(p+1, m+1)], rootp((p+1)*(m+1)*n0*(n0-1))//N))
        if p >= 1 and m >= 1:
            row.append((idx[(p-1, m-1)], rootp(p*m*(n0+2)*(n0+1))//N))
        if yn != 0:
            if n0 >= 1:
                row.append((idx[(p+1, m)], -rootp((p+1)*n0)*yn//yd))
                row.append((idx[(p, m+1)], -rootp((m+1)*n0)*yn//yd))
            if p >= 1:
                row.append((idx[(p-1, m)], -rootp(p*(n0+1))*yn//yd))
            if m >= 1:
                row.append((idx[(p, m-1)], -rootp(m*(n0+1))*yn//yd))
        off.append(row)
    dim = len(states)
    v = [0]*dim
    v[idx[(0, 0)]] = ONE
    re = v[:]  # partial sums
    im = [0]*dim
    tn, td = t.numerator, t.denominator
    k = 0
    cur = v
    t0 = time.time()
    while True:
        k += 1
        nxt = [0]*dim
        for i in range(dim):
            ci = cur[i]
            if ci == 0: continue
            nxt[i] += (diag[i]*ci) >> Pbits
            for (j, val) in off[i]:
                nxt[j] += (val*ci) >> Pbits
        # term k = (-i t)^k H^k v / k!
        cur = [(a*tn)//(td*k) for a in nxt]
        mx = max(abs(a) for a in cur)
        s = k % 4
        if s == 0:
            re = [a+b for a, b in zip(re, cur)]
        elif s == 1:
            im = [a-b for a, b in zip(im, cur)]
        elif s == 2:
            re = [a-b for a, b in zip(re, cur)]
        else:
            im = [a+b for a, b in zip(im, cur)]
        if mx == 0 or (mx < (1 << 64) and k > z):
            break
    # read-out with exact roots at Pbits
    def prod(a, b):
        return (re[a]*re[b] + im[a]*im[b]) >> Pbits
    def prodim(a, b):
        return (re[a]*im[b] - im[a]*re[b]) >> Pbits
    nrm = f = c2 = n0n = reP = Are = Aim = Bre = 0
    for i, (p, m) in enumerate(states):
        n = p+m; n0 = N-n
        w = prod(i, i)
        nrm += w; f += w*n; c2 += w*p*m; n0n += w*n0*n
        if n0 >= 2:
            j = idx[(p+1, m+1)]
            reP += (prod(j, i)*rootp((p+1)*(m+1)*n0*(n0-1))) >> Pbits
        if n0 >= 1:
            j = idx[(p+1, m)]
            Are += (prod(i, j)*rootp((p+1)*n0)) >> Pbits
            Aim += (prodim(i, j)*rootp((p+1)*n0)) >> Pbits
            j = idx[(p, m+1)]
            Are += (prod(j, i)*rootp((m+1)*n0)) >> Pbits
            Aim += (prodim(j, i)*rootp((m+1)*n0)) >> Pbits
        if p >= 1:
            j = idx[(p-1, m+1)]
            Bre += (prod(j, i)*rootp(p*(m+1))) >> Pbits
    def F(v): return Fr(v, ONE)
    X = F(n0n) + 2*F(reP)
    C1 = 2*X/(N*(N-1))
    C2 = 2*F(c2)/(N*(N-1))
    A1 = 2*abs(F(Are))/N
    D2 = 2*abs(F(Bre))/N
    V2 = A1*A1/(2*C1)
    return dict(norm_off=F(nrm)-1, f=F(f)/N, A=F(Are), Aim=F(Aim), B=F(Bre), C1=C1, C2=C2, A1=A1, D2=D2, V2=V2, k=k, Pbits=Pbits, sec=time.time()-t0, jbar=F(f)/2)

def dec(x, digits=24):
    x = Fr(x)
    neg = x < 0
    x = abs(x)
    s = (x.numerator*10**digits + x.denominator//2)//x.denominator
    return ('-' if neg else '') + str(s//10**digits) + '.' + str(s % 10**digits).zfill(digits)

if __name__ == '__main__':
    # args: N delta y t
    N = int(sys.argv[1]); delta = Fr(sys.argv[2]); y = Fr(sys.argv[3]); t = Fr(sys.argv[4])
    r = run(N, delta, y, t)
    print('ANCHOR|N=%d|delta=%s|y=%s|t=%s|k=%d|Pbits=%d|sec=%d|norm_off=%s|f=%s|jbar=%s|A=%s|Aim=%s|B=%s|C1=%s|C2=%s|A1=%s|D2=%s|V2=%s|float_used=0|json=0' % (
        N, delta, y, t, r['k'], r['Pbits'], int(r['sec']), dec(r['norm_off'], 30), dec(r['f']), dec(r['jbar']), dec(r['A']), dec(r['Aim']), dec(r['B']), dec(r['C1']), dec(r['C2']), dec(r['A1']), dec(r['D2']), dec(r['V2'])))
