# Own exact <A>, <B>, E at N = 9, full space, dense, integer inverse iteration at 2^400 in the parity-even block, against the first run, the third run and this head.
# Tests "<A> at N = 9 sat about 5e-8 from exact" and the route's own digits. Also N = 2 parity by hand.
import sys
from math import isqrt
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
out = open(ME + 'out/own_n9.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True); out.write(s + '\n'); out.flush()
BITS = 400
U = 1 << BITS
def sq(n):
    return isqrt(n << (2 * BITS))
def fix(q):
    q = F(q)
    return (q.numerator << BITS) // q.denominator
def mat(n, x, u, y, parity):
    """Even (parity=1) or odd (parity=-1) block in the normalized basis: |p,m>_e = (|p,m>+|m,p>)/sqrt2 for p>m, |p,p>; odd = (|p,m>-|m,p>)/sqrt2 for p>m."""
    x, u, y = F(x), F(u), F(y)
    full = [(p, m) for p in range(n + 1) for m in range(n + 1 - p)]
    if parity == 1:
        basis = [(p, m) for p, m in full if p >= m]
    else:
        basis = [(p, m) for p, m in full if p > m]
    idx = {s: i for i, s in enumerate(basis)}
    size = len(basis)
    M = [[0] * size for _ in range(size)]
    r2 = sq(2)
    def coef(s):
        p, m = s
        if p == m:
            return [((p, m), U)]
        c = (U << BITS) // r2
        return [((p, m), c), ((m, p), parity * c)]
    def h_full(p, m):
        """H |p,m> as {state: element at 2^BITS}."""
        n0 = n - p - m
        o = {}
        o[(p, m)] = fix(x * (p + m) + u * F(n0 * (p + m) + p * m, n))
        if n0 >= 2:
            o[(p + 1, m + 1)] = sq(n0 * (n0 - 1) * (p + 1) * (m + 1)) // n
        if p >= 1 and m >= 1:
            o[(p - 1, m - 1)] = sq((n0 + 1) * (n0 + 2) * p * m) // n
        yf = fix(y)
        if n0 >= 1:
            o[(p + 1, m)] = o.get((p + 1, m), 0) - ((yf * sq(n0 * (p + 1))) >> BITS)
            o[(p, m + 1)] = o.get((p, m + 1), 0) - ((yf * sq(n0 * (m + 1))) >> BITS)
        if p >= 1:
            o[(p - 1, m)] = o.get((p - 1, m), 0) - ((yf * sq((n0 + 1) * p)) >> BITS)
        if m >= 1:
            o[(p, m - 1)] = o.get((p, m - 1), 0) - ((yf * sq((n0 + 1) * m)) >> BITS)
        return o
    for s in basis:
        j = idx[s]
        col = {}
        for st, c in coef(s):
            for t, e in h_full(*st).items():
                col[t] = col.get(t, 0) + ((c * e) >> BITS)
        for t, v in col.items():
            # project onto the block
            tp, tm = t
            if tp == tm:
                if parity == 1:
                    i = idx[(tp, tm)]
                    M[i][j] += v
            else:
                rep = (max(t), min(t))
                sgn = 1 if tp > tm else parity
                i = idx[rep]
                M[i][j] += (v * sgn * ((U << BITS) // r2)) >> BITS
    return basis, idx, M
def lowest(M):
    """Lowest eigenpair of a symmetric integer matrix, by bisection on LDL inertia then inverse iteration."""
    size = len(M)
    def neg(lam):
        A = [row[:] for row in M]
        for i in range(size):
            A[i][i] -= lam
        c = 0
        for i in range(size):
            p = A[i][i]
            if p == 0:
                p = 1
            if p < 0:
                c += 1
            for r in range(i + 1, size):
                if A[r][i]:
                    f = (A[r][i] << BITS) // p
                    for k in range(i + 1, size):
                        if A[i][k]:
                            A[r][k] -= (f * A[i][k]) >> BITS
        return c
    bound = 2 + max(sum(abs(v) for v in row) for row in M)
    lo, hi = -bound, bound
    while hi - lo > (U >> 60):
        mid = (lo + hi) >> 1
        if neg(mid) >= 1:
            hi = mid
        else:
            lo = mid
    lam = lo - (U >> 90)
    # inverse iteration
    v = [U + (i * U >> 6) for i in range(size)]
    for _ in range(6):
        A = [row[:] + [v[i]] for i, row in enumerate(M)]
        for i in range(size):
            A[i][i] -= lam
        for i in range(size):
            p = A[i][i]
            for r in range(i + 1, size):
                if A[r][i]:
                    f = (A[r][i] << BITS) // p
                    for k in range(i, size + 1):
                        if A[i][k]:
                            A[r][k] -= (f * A[i][k]) >> BITS
        x_ = [0] * size
        for i in range(size - 1, -1, -1):
            s = A[i][size]
            for k in range(i + 1, size):
                if A[i][k] and x_[k]:
                    s -= (A[i][k] * x_[k]) >> BITS
            x_[i] = (s << BITS) // A[i][i]
        nr = isqrt(sum(a * a for a in x_))
        v = [(a << BITS) // nr for a in x_]
    return lam, v
def expect(n, basis, idx, v):
    """<A>, <B>, E is separate. Even block."""
    amp = {}
    r2 = sq(2)
    c = (U << BITS) // r2
    for s, a_ in zip(basis, v):
        p, m = s
        if p == m:
            amp[(p, m)] = a_
        else:
            amp[(p, m)] = (a_ * c) >> BITS
            amp[(m, p)] = (a_ * c) >> BITS
    A = 0
    B = 0
    for (p, m), a_ in amp.items():
        n0 = n - p - m
        if p >= 1:
            t = (p - 1, m)
            if t in amp:
                A += (((amp[t] * a_) >> BITS) * sq((n0 + 1) * p)) >> BITS
            t = (p - 1, m + 1)
            if t in amp:
                B += (((amp[t] * a_) >> BITS) * sq((m + 1) * p)) >> BITS
        if n0 >= 1:
            t = (p, m + 1)
            if t in amp:
                A += (((amp[t] * a_) >> BITS) * sq(n0 * (m + 1))) >> BITS
    return F(A, U), F(B, U)
R1 = load(WT + 'polariton/first-run/RECEIPT.hbp')
R3 = load(WT + 'polariton/third-run/RECEIPT.hbp')
def row(rr, n, u, x, s, tag='POLARITON_PIN'):
    for r in rr.get(tag, []):
        if r['s'] != 'hand' and int(r['N']) == n and eq(r['u'], u) and eq(r['x'], x) and eq(r['s'], s):
            return r
worst = {}
P('N=9 pin rows: off in units of 1e-9, first run, third run, this head')
for u, x in (('1/2', '0'), ('0', '0'), ('1/2', '1/2'), ('1/2', '3/2')):
    for s in ('1/2', '1', '2', '4', '8', '16'):
        y = F(s) / 9
        basis, idx, M = mat(9, x, u, y, 1)
        lam, v = lowest(M)
        a_, b_ = expect(9, basis, idx, v)
        r1, r3, r4 = row(R1, 9, u, x, s), row(R3, 9, u, x, s), row(R, 9, u, x, s)
        offs = []
        for nm, rr in (('first', r1), ('third', r3), ('head', r4)):
            da = (F(int(rr['A_ppb']), 10 ** 9) - a_) * 10 ** 9
            db = (F(int(rr['B_ppb']), 10 ** 9) - b_) * 10 ** 9
            de = (F(int(rr['energy_ppb']), 10 ** 9) - F(lam, U)) * 10 ** 9
            offs.append('%s A %s B %s E %s' % (nm, dec(da, 1), dec(db, 1), dec(de, 1)))
            worst[nm] = max(worst.get(nm, F(0)), abs(da))
        P(' u', u, 'x', x, 's', s, '|', ' | '.join(offs))
P('largest |off A| in 1e-9', {k: dec(v, 1) for k, v in worst.items()})
P('N=2, even and odd lowest, four hand rows')
for y in ('0', '1/64', '-1/64', '1/1024'):
    basis, idx, M = mat(2, '1/4', '0', y, 1)
    le, ve = lowest(M)
    bo, io, Mo = mat(2, '1/4', '0', y, -1)
    lo, vo = lowest(Mo)
    P(' y', y, 'E_even', dec(F(le, U), 9), 'E_odd', dec(F(lo, U), 9), 'even below odd', le < lo, 'A', dec(expect(2, basis, idx, ve)[0], 9), 'B', dec(expect(2, basis, idx, ve)[1], 9))
out.close()

# The read-out alone: exact eigenvector at N = 9, roots floored at 20 fractional bits, as f47d662's read() does.
out = open(ME + 'out/own_n9_readout.txt', 'w', encoding='utf-8', newline='\n')
def expect20(n, basis, idx, v, frac):
    amp = {}
    r2 = sq(2)
    c = (U << BITS) // r2
    for s, a_ in zip(basis, v):
        p, m = s
        if p == m:
            amp[(p, m)] = a_
        else:
            amp[(p, m)] = (a_ * c) >> BITS
            amp[(m, p)] = (a_ * c) >> BITS
    def rt(k):
        return isqrt(k << (2 * frac)) << (BITS - frac)
    A = 0
    for (p, m), a_ in amp.items():
        n0 = n - p - m
        if n0 >= 1:
            t = (p + 1, m)
            if t in amp:
                A += (((amp[t] * a_) >> BITS) * rt((p + 1) * n0)) >> BITS
            t = (p, m + 1)
            if t in amp:
                A += (((amp[t] * a_) >> BITS) * rt((m + 1) * n0)) >> BITS
    return F(A, U)
vals = []
for u, x in (('1/2', '0'), ('0', '0'), ('1/2', '1/2'), ('1/2', '3/2')):
    for s in ('1/2', '1', '2', '4', '8', '16'):
        y = F(s) / 9
        basis, idx, M = mat(9, x, u, y, 1)
        lam, v = lowest(M)
        a_, b_ = expect(9, basis, idx, v)
        a20 = expect20(9, basis, idx, v, 20)
        a32 = expect20(9, basis, idx, v, 32)
        r1 = row(R1, 9, u, x, s)
        vals.append((a20 - a_, a32 - a_, F(int(r1['A_ppb']), 10 ** 9) - a_))
        P(' u', u, 'x', x, 's', s, 'A exact', dec(a_, 9), 'read-out alone at 20 bits, off 1e-9', dec((a20 - a_) * 10 ** 9, 1), 'at 32 bits', dec((a32 - a_) * 10 ** 9, 3), 'first run off', dec((F(int(r1['A_ppb']), 10 ** 9) - a_) * 10 ** 9, 1))
ab = sorted(abs(a) for a, _, _ in vals)
fr = sorted(abs(c) for _, _, c in vals)
P('read-out alone: |off| min', dec(ab[0] * 10 ** 9, 1), 'median', dec(ab[len(ab) // 2] * 10 ** 9, 1), 'max', dec(ab[-1] * 10 ** 9, 1), '1e-9')
P('first run: |off| min', dec(fr[0] * 10 ** 9, 1), 'median', dec(fr[len(fr) // 2] * 10 ** 9, 1), 'max', dec(fr[-1] * 10 ** 9, 1), '1e-9')
out.close()
