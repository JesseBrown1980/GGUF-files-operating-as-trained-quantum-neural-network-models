# Remaining single statements: read-out 5e-8, first read of the route, V2 share at 2k, the y=1/1024 rows, Fourier K, paper numbers, own chains, own P scan.
import sys
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
from own_sector import build, level, below, SH
import importlib.util
out = open(ME + 'out/check_f.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True); out.write(s + '\n'); out.flush()

P('== line 160: first-run full route rows at N=9')
FR = load(WT + 'polariton/first-run/ROUTE-FULL.hbp')['SECOND_ROUTE_FULL']
for r in FR:
    if r['N'] == '9':
        P(' ', r['u'], r['x'], r['y'], 'A off', dec(abs(F(r['exact_A']) - F(r['rust_A'])) * 10 ** 9, 1), 'e-9', 'B off', dec(abs(F(r['exact_B']) - F(r['rust_B'])) * 10 ** 9, 1), 'E off', dec(abs(F(r['exact_E']) - F(r['rust_E'])) * 10 ** 9, 1))
P(' first-run rows by N', {n: sum(r['N'] == n for r in FR) for n in sorted({r['N'] for r in FR})})
TR = load(WT + 'polariton/third-run/SECOND-ROUTE.hbp')['SECOND_ROUTE_FULL']
for r in TR:
    if r['N'] == '9':
        P(' third', r['u'], r['x'], r['y'], 'A off', dec(abs(F(r['exact_A']) - F(r['rust_A'])) * 10 ** 9, 1), 'B off', dec(abs(F(r['exact_B']) - F(r['rust_B'])) * 10 ** 9, 1))
NOW = S['SECOND_ROUTE_FULL']
P(' now: largest off E, A, B on 60 rows, e-9', dec(max(abs(F(r['exact_E']) - F(r['rust_E'])) for r in NOW) * 10 ** 9, 1), dec(max(abs(F(r['exact_A']) - F(r['rust_A'])) for r in NOW) * 10 ** 9, 1), dec(max(abs(F(r['exact_B']) - F(r['rust_B'])) for r in NOW) * 10 ** 9, 1))
P()
P('== first read of the route')
F1 = load(WT + 'polariton/SECOND-ROUTE-FIRST-READ.hbp')
P(' DONE', F1['SECOND_ROUTE_FULL_DONE'][0]['_raw'], 'rows', len(F1['SECOND_ROUTE_FULL']), 'has HAND_N3', 'HAND_N3_DOUBLET' in F1)
for r in F1['SECOND_ROUTE_FULL']:
    if abs(F(r['exact_B']) - F(r['rust_B'])) >= F(1, 10 ** 5) or abs(F(r['exact_A']) - F(r['rust_A'])) >= F(1, 10 ** 5):
        P(' marked', r['_raw'][:200])
P()
P('== the visible share at 2k in the central rows, D2^2/2C2, against f(q)^2')
FQ = {'1/2': 9999, '1': 39944, '2': 156537, '4': 490857, '8': 776331, '16': 889412}
for n in (243, 729):
    for s, f in FQ.items():
        r = pin(n, '1/2', '0', s)
        d2 = F(2 * abs(int(r['B_ppb'])), n * 10 ** 9)
        c2 = F(int(r['C2_ppm']), 10 ** 6)
        P(' N', n, 'yN', s, 'D2^2/2C2', dec(d2 ** 2 / (2 * c2), 5), 'f^2', dec(F(f, 10 ** 6) ** 2, 5), 'ratio', dec(d2 ** 2 / (2 * c2) / F(f, 10 ** 6) ** 2, 4))
P()
P('== the V2 at y=1/1024 rows, read against the law')
for r in R['POLARITON_QUENCH_PIN']:
    if F(r['y']) == F(1, 1024) and r['delta'] in ('0', '1/2'):
        n = int(r['N'])
        a1 = F(2 * abs(int(r['A_ppb'])), n * 10 ** 9)
        c1 = F(int(r['C1_ppm']), 10 ** 6)
        L = Law(n, F(1, 1024), r['delta'], r['t'])
        v2 = a1 * a1 / (2 * c1)
        P(' N', n, 'delta', r['delta'], 't', r['t'], 'V2 read', dec(v2, 6), 'law', dec(L.v2, 6), 'ratio', dec(v2 / L.v2, 3), 'f pred', dec(L.f, 3), 'A1 ratio', dec(a1 / L.a1, 3), 'C1 ratio', dec(c1 / L.c1, 3))
P()
P('== line 190')
A = F(26, 1000)
# K = a1^2/a0^2 with psi = sqrt(1 + A cos th): exact binomial series in integers
def k_direct(A):
    # sqrt(1+z) series coefficients; moments of cos^m
    from math import comb
    terms = 40
    coef = [F(1)]
    for m in range(1, terms):
        coef.append(coef[-1] * (F(1, 2) - (m - 1)) / m)
    def mom(m):
        return F(comb(m, m // 2), 2 ** m) if m % 2 == 0 else F(0)
    a0 = sum(coef[m] * A ** m * mom(m) for m in range(terms))
    a1 = sum(coef[m] * A ** m * mom(m + 1) for m in range(terms))
    return a1 ** 2 / a0 ** 2
K = k_direct(A)
P(' K direct', dec(K * 10 ** 5, 4), 'e-5', 'A^2/16', dec(A ** 2 / 16 * 10 ** 5, 4), 'e-5', 'A^2/4 %', dec(A ** 2 / 4 * 100, 4), 'K %', dec(K * 100, 5))
need = A ** 2 / (8 * F(5, 1000))
P(' (1-d)V2 with K=0.5%:', dec(need, 4), ' with rho0 = 1/(1+2K), rho = K rho0:', dec(A ** 2 / (16 * F(1) * (F(5, 1000) / (1 + F(1, 100)) ** 2 * 1) * F(1, 2)), 4), ' four times:', dec(4 * need, 4))
for v in (need, 4 * need):
    Y = v / (1 - v)
    P(' V2', dec(v, 4), 'Y', dec(Y, 4), 'y sqrtN', dec(root(Y / 2), 3))
P(' 0.04/2.3 %', dec(F(4, 100) / F(23, 10) * 100, 2), ' 0.04/(1/2.3) %', dec(F(4, 100) * F(23, 10) * 100, 1))
P()
P('== own chains: D2/y^2 over the rotor at y -> 0')
exec(open(ME + 'own_exact2.py', encoding='utf-8').read().split("P('== N(D2 ratio - 1), own exact second order')")[1].split("for u, x, q_over, tag in")[0].replace('SH2 = 240', 'SH2 = 240'))
def rot_chi(u, x, n):
    u, x = F(u), F(x)
    rho = (1 - u - x) / (4 - 3 * u)
    c0 = ((1 - 2 * rho) / rho - u) / 4
    return rho * n * n * u / (16 * c0 * c0), rho, c0
for u, x in (('1/2', '0'), ('1', '-1/4'), ('1/2', '-1/4'), ('1', '-1/8'), ('1/4', '-1/4'), ('3/4', '0'), ('3/4', '1/8')):
    line = []
    for n in (729, 2187, 6561):
        b2, e0, _ = chain(n, u, x)
        chi = 2 * abs(b2) / n
        rc, rho, c0 = rot_chi(u, x, n)
        line.append((n, dec(chi / rc, 5), dec(n * (chi / rc - 1), 2)))
    P(' u', u, 'x', x, 'N, ratio, N(ratio-1)', line)
P('== u = 0: a = (D2/y^2) 16 c0^2/(rho N), own chains, extrapolated from N = 2187, 6561 as 1/N')
from fractions import Fraction
for x in ('-3/4', '-1/2', '-1/4', '0', '1/4', '1/2', '3/4'):
    xx = F(x)
    rho = (1 - xx) / 4
    c0 = ((1 - 2 * rho) / rho) / 4
    vals = {}
    for n in (2187, 6561):
        b2, e0, _ = chain(n, '0', x)
        chi = 2 * abs(b2) / n
        vals[n] = chi * 16 * c0 * c0 / (rho * n)
    ex = (3 * vals[6561] - vals[2187]) / 2
    om = root(1 / (2 * (1 - xx * xx)))
    P(' x', x, 'a(2187)', dec(vals[2187], 6), 'a(6561)', dec(vals[6561], 6), 'extrapolated', dec(ex, 6), '1/omega', dec(om, 6), 'off', dec(abs(ex - om) * 10 ** 6, 2), 'e-6')
P()
P('== own P scan at N = 243: lowest sector over every P, 18 points')
PTS = [('1/2','0'),('1/2','1/4'),('1/2','-1/8'),('1/2','-1/4'),('1/2','-3/8'),('1/2','-1/2'),('1/2','-5/8'),('1/4','-1/4'),('1/4','-3/8'),('1/4','-1/2'),('3/4','0'),('3/4','-1/8'),('3/4','-1/4'),('1','-1/8'),('1','-1/4'),('1','-3/8'),('0','-1/2'),('0','-3/4')]
def edge(u):
    u = F(u); a = 4 - 3 * u
    return (1 - (a - root(u * a)) / 2) - u
n = 243
agree = 0
for u, x in PTS:
    best = None
    for p in range(0, n + 1):
        top = (n - p) // 2
        d, o2 = build(n, u, x, p, 0, top)
        lo = min(d) - (1 << (SH - 0)) // 2
        hi = max(d) + (1 << (SH - 0)) // 2
        e = level(d, o2, 0, lo, hi, 1 << (SH - 40))
        if best is None or e < best[0]:
            best = (e, p)
    want = 0 if F(x) > edge(u) else n
    ok = best[1] == want
    agree += ok
    P(' u', u, 'x', x, 'edge', dec(edge(u), 4), 'lowest P', best[1], 'E/N', dec(F(best[0], 1 << SH), 5), 'expected P', want, 'OK' if ok else 'DIFFERENT')
P(' agree', agree, 'of', len(PTS))
out.close()
