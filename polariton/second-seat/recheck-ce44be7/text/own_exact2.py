# Own reads, part 2. Integers and exact rationals, normalized Fock basis with integer roots at 2^600.
#  4. The 4 conversion rows and the 6 Taylor rows: exact series, against the engine's rows, in units of 10^-9 with fractions.
#  5. N = 2 hand rows, N = 3 doublet, engine rows.
#  6. Constants of -lap + r^4 at m = 0.
#  7. N(D2 ratio - 1) at u = 1/2, x = 0 by exact second order on the P = 0, +-1, +-2 chains.
import sys
from math import isqrt, factorial
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
out = open(ME + 'out/own_exact2.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True); out.write(s + '\n'); out.flush()

BITS = 600
UNIT = 1 << BITS
def sq(n):
    return isqrt(n << (2 * BITS))

def build_ops(n, x, u, y):
    x, u, y = F(x), F(u), F(y)
    states = [(p, m) for p in range(n + 1) for m in range(n + 1 - p)]
    idx = {s: i for i, s in enumerate(states)}
    fix = lambda q: (F(q).numerator << BITS) // F(q).denominator
    rows = [[] for _ in states]
    for (p, m), i in idx.items():
        n0 = n - p - m
        rows[i].append((i, fix(x * (p + m) + u * F(n0 * (p + m) + p * m, n))))
        if n0 >= 2:
            t = idx[(p + 1, m + 1)]
            e = (sq(n0 * (n0 - 1) * (p + 1) * (m + 1))) // n
            rows[t].append((i, e))
            rows[i].append((t, e))
        if n0 >= 1 and y != 0:
            t = idx[(p + 1, m)]
            e = (-fix(y) * sq(n0 * (p + 1))) >> BITS
            rows[t].append((i, e)); rows[i].append((t, e))
            t = idx[(p, m + 1)]
            e = (-fix(y) * sq(n0 * (m + 1))) >> BITS
            rows[t].append((i, e)); rows[i].append((t, e))
    return states, idx, rows

def evolve(n, x, u, y, t, terms):
    states, idx, rows = build_ops(n, x, u, y)
    size = len(states)
    t = F(t)
    tn = (t.numerator << BITS) // t.denominator
    re = [0] * size
    im = [0] * size
    re[idx[(0, 0)]] = UNIT
    vr = list(re)
    vi = [0] * size
    # psi = sum (-i t H)^k/k! psi0; iterate: v_{k+1} = (-i t H) v_k /(k+1)
    for k in range(1, terms + 1):
        wr = [0] * size
        wi = [0] * size
        for i, row in enumerate(rows):
            sr, si = 0, 0
            for j, e in row:
                if vr[j]:
                    sr += e * vr[j]
                if vi[j]:
                    si += e * vi[j]
            wr[i] = sr >> BITS
            wi[i] = si >> BITS
        # multiply by -i t/k: (a + i b)(-i) = b - i a
        vr = [(b * tn >> BITS) // k for b in wi]
        vi = [(-a * tn >> BITS) // k for a in wr]
        re = [a + b for a, b in zip(re, vr)]
        im = [a + b for a, b in zip(im, vi)]
        if not any(vr) and not any(vi):
            break
    return states, idx, re, im

def read_state(n, states, idx, re, im):
    pairs, n0s, npm, norm = 0, 0, 0, 0
    a_r, b_r, pp_r, a_i, b_i = 0, 0, 0, 0, 0
    for (p, m), i in idx.items():
        n0 = n - p - m
        w = re[i] * re[i] + im[i] * im[i]
        norm += w
        pairs += w * (p + m)
        n0s += w * n0 * (p + m)
        npm += w * p * m
        if p >= 1:
            t = idx[(p - 1, m)]
            e = sq((n0 + 1) * p)
            a_r += (re[t] * re[i] + im[t] * im[i]) * e >> BITS
            t = idx[(p - 1, m + 1)]
            e = sq((m + 1) * p)
            b_r += (re[t] * re[i] + im[t] * im[i]) * e >> BITS
        if n0 >= 1:
            t = idx[(p, m + 1)]
            e = sq(n0 * (m + 1))
            a_r += (re[t] * re[i] + im[t] * im[i]) * e >> BITS
        if n0 >= 2:
            t = idx[(p + 1, m + 1)]
            e = sq(n0 * (n0 - 1) * (p + 1) * (m + 1))
            pp_r += (re[t] * re[i] + im[t] * im[i]) * e >> BITS
    s2 = UNIT * UNIT
    fq = lambda v: F(v, s2)
    return dict(norm=fq(norm), jbar=fq(pairs) / 2, A=fq(a_r), B=fq(b_r), C1=2 * (fq(n0s) + 2 * fq(pp_r)) / (n * (n - 1)), C2=2 * fq(npm) / (n * (n - 1)))

P('== conversion rows')
for r in R['POLARITON_TAYLOR_CONVERT']:
    n, x, u, y, t = int(r['N']), r['x'], r['u'], r['y'], r['t']
    st, idx, re, im = evolve(n, x, u, y, t, 6 * n + 200)
    v = read_state(n, st, idx, re, im)
    offs = {k: (F(int(r[f]), 10 ** 9) - v[k]) * 10 ** 9 for k, f in (('jbar', 'jbar_ppb'), ('A', 'A_ppb'), ('B', 'B_ppb'), ('C1', 'C1_ppb'), ('C2', 'C2_ppb'))}
    P(' N', n, 'x', x, 'y', y, 't', t, 'norm-1', dec((v['norm'] - 1) * 10 ** 12, 3), 'e-12', {k: dec(o, 3) for k, o in offs.items()}, 'largest', dec(max(abs(o) for o in offs.values()), 3))
P('== taylor rows')
for r in R['POLARITON_TAYLOR_POINT']:
    n, x, u, y, t = int(r['N']), r['x'], r['u'], r['y'], r['t']
    st, idx, re, im = evolve(n, x, u, y, t, 6 * n + 200)
    v = read_state(n, st, idx, re, im)
    P(' N', n, 'u', u, 'x', x, 'y', y, 't', t, 'off jbar e-9', dec((F(int(r['jbar_ppb']), 10 ** 9) - v['jbar']) * 10 ** 9, 3), 'off A e-9', dec((F(int(r['A_ppb']), 10 ** 9) - v['A']) * 10 ** 9, 3))

P('== N=2 hand rows from the receipt')
for r in R['POLARITON_PIN']:
    if r['s'] == 'hand':
        P(' ', r['_raw'][:200])
# exact: J=2, D=1, U=0, at h: from the 2 x 2 at h=0: c0^2=2/3, c1^2=1/3, E=-2 and the response 2/9
c02, c12 = F(2, 3), F(1, 3)
e0 = F(-2)
# element of V=A+A^dag to |1,1,0>: sqrt2 c0 + c1 (with c1 = -c0/sqrt2) => squared
el2 = (2 * c02 + c12 + 2 * (-1) * (F(2, 3)))  # (sqrt2 c0 + c1)^2 = 2c0^2 + c1^2 + 2 sqrt2 c0 c1 and sqrt2 c0 c1 = -c0^2 (c1=-c0/sqrt2)
P(' element^2 to |1,1,0>', el2, ' denominator', F(1) - e0, ' d<A>/dh =', F(1, 2) * 2 * 2 * el2 / (F(1) - e0))
P(' g2(r) coefficients C1, C2 at N=2: <n0(n+ + n-)> =', 0, '; Re<P> = sqrt2 c0 c1 = -c0^2 =', -c02, '; C1 =', 2 * (0 + 2 * (-c02)) / 2, ' C2 =', 2 * c12 / 2)

P('== N=3 doublet, exact')
r73 = root(73)
lvl = -F(1, 3) - r73 / 12
b_ = F(3, 4) * (1 + 1 / r73)
P(' level', dec(lvl, 9), 'P=0 level', dec(-F(1, 8) - root(F(1, 64) + F(2, 3)), 6), 'B closed', dec(b_, 9))
for r in R['POLARITON_PIN_WINDOW']:
    if r['N'] == '3' and eq(r['u'], '1/4') and eq(r['x'], '-1/4') and eq(r['s'], '0'):
        P(' engine row', r['_raw'][:200])

P('== constants of -lap + r^4 at m = 0, oscillator basis, exact rationals truncated to 2^300')
SIZE = 90
# H0 = -lap + r^2 has 4n+2. r^2: <n|r^2|n> = 2n+1, <n|r^2|n+1> = -(n+1).
def r2(i, j):
    if i == j:
        return F(2 * i + 1)
    if abs(i - j) == 1:
        return F(-(min(i, j) + 1))
    return F(0)
BIG = SIZE + 4
r4 = [[sum(r2(i, k) * r2(k, j) for k in range(max(0, i - 1), min(BIG, i + 2))) for j in range(SIZE)] for i in range(SIZE)]
def matrix(lam):
    return [[(F(4 * i + 2) if i == j else F(0)) - r2(i, j) + r4[i][j] + lam * r2(i, j) for j in range(SIZE)] for i in range(SIZE)]
SHF = 300
def count_neg(mat, lam):
    # banded LDL inertia, bandwidth 2, integers at 2^300
    n = SIZE
    A = [[0] * 5 for _ in range(n)]  # A[i][d] = element (i, i+d) for d=0,1,2
    for i in range(n):
        for d in range(3):
            if i + d < n:
                v = mat[i][i + d] - (lam if d == 0 else 0)
                A[i][d] = (v.numerator << SHF) // v.denominator
    neg = 0
    for i in range(n):
        p = A[i][0]
        if p == 0:
            p = 1
        if p < 0:
            neg += 1
        for d in (1, 2):
            if i + d < n and A[i][d]:
                f = (A[i][d] << SHF) // p
                for e in range(d, 3):
                    if i + e < n:
                        A[i + d][e - d] -= (f * A[i][e]) >> SHF
    return neg
def eig(mat, index):
    lo, hi = F(0), F(40)
    for _ in range(170):
        mid = (lo + hi) / 2
        if count_neg(mat, mid) > index:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2
m0 = matrix(F(0))
E0 = eig(m0, 0); E1 = eig(m0, 1)
h = F(1, 1 << 30)
Ep = eig(matrix(h), 0); Em = eig(matrix(-h), 0)
xi2 = (Ep - Em) / (2 * h)
P(' E0', dec(E0, 8), 'E1', dec(E1, 8), 'gap constant', dec(E1 - E0, 6), 'text 7.18495', '<r^2>', dec(xi2, 7), '<r^2>/4', dec(xi2 / 4, 6), 'text 0.162869')

P('== N(D2 ratio - 1), own exact second order')
SH2 = 240
def sector_eval(n, u, x, p):
    from own_sector import build
    top = (n - p) // 2
    return build(n, u, x, p, 0, top)
def solve_shifted(d, o2roots, e, rhs):
    # (T - e) v = rhs, tridiagonal with off-diagonal o (fixed point), Thomas in integers at 2^SH2, where d, e are at 2^220 from build
    n = len(d)
    S = 1 << 220
    c = [0] * n
    r = [0] * n
    b0 = d[0] - e
    if n > 1:
        c[0] = (o2roots[0] << 220) // b0
    r[0] = (rhs[0] << 220) // b0
    for i in range(1, n):
        bi = d[i] - e - ((o2roots[i - 1] * c[i - 1]) >> 220)
        if i < n - 1:
            c[i] = (o2roots[i] << 220) // bi
        r[i] = ((rhs[i] - ((o2roots[i - 1] * r[i - 1]) >> 220)) << 220) // bi
    v = [0] * n
    v[-1] = r[-1]
    for i in range(n - 2, -1, -1):
        v[i] = r[i] - ((c[i] * v[i + 1]) >> 220)
    return v
def chain(n, u, x, shape=None):
    from own_sector import build, level
    SH_ = 220
    d0, o20 = build(n, u, x, 0, 0, n // 2)
    o0 = [isqrt(v << SH_) for v in o20]
    # ground energy of P=0 at H/N scale. Then response with V/N.
    guess_lo, guess_hi = -(4 << SH_), (4 << SH_)
    e0 = level(d0, o20, 0, guess_lo, guess_hi, 1 << (SH_ - 200))
    # ground vector by inverse iteration
    size = len(d0)
    v = [1 << SH_] * size
    eps = 1 << (SH_ - 190)
    for _ in range(4):
        w = solve_shifted(d0, o0, e0 - eps, v)
        nr = isqrt(sum(a * a for a in w))
        v = [(a << SH_) // nr for a in w]
    # Sectors P=1, P=2 (same chains for P=-1, -2 by parity)
    d1, o21 = build(n, u, x, 1, 0, (n - 1) // 2)
    o1 = [isqrt(a << SH_) for a in o21]
    d2, o22 = build(n, u, x, 2, 0, (n - 2) // 2)
    o2 = [isqrt(a << SH_) for a in o22]
    # V = -(A + A^dag), H/N scale: element -y sqrt(...)/N. Use V' = (A + A^dag)/N with the sign applied at the end.
    # |j, P=0> means n+=n-=j, n0=N-2j.  V maps P=0 to P=+1: a+^dag a0 |n0,j,j> -> sqrt(n0 (j+1)) |n0-1,j+1,j> (P=1, index j)
    #                                                       a0^dag a- |n0,j,j> -> sqrt((n0+1) j)  |n0+1,j,j-1> (P=1, index j-1)
    size1 = len(d1)
    rhs = [0] * size1
    for j in range(size):
        n0 = n - 2 * j
        if n0 >= 1 and j < size1:
            rhs[j] += (v[j] * isqrt(n0 * (j + 1) << (2 * SH_)) >> SH_)
        if j >= 1:
            rhs[j - 1] += (v[j] * isqrt((n0 + 1) * j << (2 * SH_)) >> SH_)
    rhs = [a // n for a in rhs]
    # first order: |1,P=1> = -G V|0> with V=-(A+A^dag)/N * y and G=(H/N - e0)^-1, so psi1 = + G (A+A^dag)/N |0> y
    psi1 = solve_shifted(d1, o1, e0, rhs)
    # second order on P=2: psi2 = G (A+A^dag)/N psi1 (P=1 to P=2), minus nothing at this P
    # P=1 |n0,j+1,j> index j. to P=2: a+^dag a0: sqrt(n0 (j+2)) |n0-1,j+2,j> index j; a0^dag a-: sqrt((n0+1) j) |n0+1,j+1,j-1> index j-1
    size2 = len(d2)
    rhs2 = [0] * size2
    for j in range(size1):
        n0 = n - 2 * j - 1
        if n0 >= 1 and j < size2:
            rhs2[j] += (psi1[j] * isqrt(n0 * (j + 2) << (2 * SH_)) >> SH_)
        if j >= 1:
            rhs2[j - 1] += (psi1[j] * isqrt((n0 + 1) * j << (2 * SH_)) >> SH_)
    rhs2 = [a // n for a in rhs2]
    psi2 = solve_shifted(d2, o2, e0, rhs2)
    # <B> at order y^2: B = a-^dag a+ lowers P by 2. By parity the state has amplitudes psi(P) = psi(-P) in matched indices.
    # <B> = 2 Re <0|B|psi2(P=2)> + <psi1(P=-1)|B|psi1(P=1)>.
    # B |n0, j+2, j> (P=2, index j) = sqrt((j+2)(j+1)) |n0, j+1, j+1> (P=0, index j+1)
    t1 = 0
    for j in range(size2):
        if j + 1 < size:
            t1 += (v[j + 1] * psi2[j] >> SH_) * isqrt((j + 2) * (j + 1) << (2 * SH_)) >> SH_
    # B |n0, j+1, j> (P=1, index j) = sqrt((j+1)(j+1)) |n0, j, j+1> (P=-1, index j, same amplitude by parity)
    t2 = 0
    for j in range(size1):
        t2 += ((psi1[j] * psi1[j]) >> SH_) * (j + 1)
    # B' = <B>/y^2 in units of ... H/N scale: y enters as y/N here already by rhs // n, and G from H/N: consistent since rhs is (A+A^dag)/N and denominators are H/N - e0.
    b_y2 = 2 * t1 + t2
    return F(b_y2, 1 << SH_), F(e0, 1 << SH_), v
for u, x, q_over, tag in (('1/2', '0', F(2, 125), 'u=1/2,x=0'),):
    prev = None
    for n in (243, 729, 2187, 6561):
        b2, e0, _ = chain(n, u, x)
        chi = 2 * abs(b2) / n
        rotor = q_over * n * n
        ratio = chi / rotor
        P(tag, 'N', n, 'e0', dec(e0, 9), '<B>/y^2 sign', '-' if b2 < 0 else '+', 'D2/y^2', dec(chi, 3), 'over rotor', dec(ratio, 6), 'N(ratio-1)', dec(n * (ratio - 1), 3))
out.close()
