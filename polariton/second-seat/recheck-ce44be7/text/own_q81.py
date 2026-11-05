# Own exact pairs at N = 81 on the 42 quench rows of this head's receipt, integer steps at 2^360 in the normalized P = 0 chain. Tests "at most 2.25e-7".
import sys
from math import isqrt
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
out = open(ME + 'out/own_q81.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True); out.write(s + '\n'); out.flush()
BITS = 360
U = 1 << BITS
def chain(n, x, u):
    x, u = F(x), F(u)
    top = n // 2
    fix = lambda q: (F(q).numerator << BITS) // F(q).denominator
    d = [fix(x * 2 * j + u * F((n - 2 * j) * 2 * j + j * j, n)) for j in range(top + 1)]
    o = [isqrt(((j + 1) ** 2 * (n - 2 * j) * (n - 2 * j - 1)) << (2 * BITS)) // n for j in range(top)]
    return d, o
def step(d, o, re, im, dt):
    """Taylor series for exp(-i H dt), integer."""
    size = len(d)
    vr, vi = re[:], im[:]
    outr, outi = re[:], im[:]
    k = 1
    while True:
        wr = [0] * size
        wi = [0] * size
        for j in range(size):
            sr = d[j] * vr[j]
            si = d[j] * vi[j]
            if j + 1 < size:
                sr += o[j] * vr[j + 1]
                si += o[j] * vi[j + 1]
            if j > 0:
                sr += o[j - 1] * vr[j - 1]
                si += o[j - 1] * vi[j - 1]
            wr[j] = sr >> BITS
            wi[j] = si >> BITS
        # multiply by -i dt / k: (a + ib)(-i) = b - ia
        vr = [(b * dt >> BITS) // k for b in wi]
        vi = [(-a * dt >> BITS) // k for a in wr]
        outr = [a + b for a, b in zip(outr, vr)]
        outi = [a + b for a, b in zip(outi, vi)]
        k += 1
        if k > 12 and all(abs(a) < 16 for a in vr) and all(abs(a) < 16 for a in vi):
            break
    return outr, outi
rows = [r for r in R['POLARITON_QUENCH'] if r['N'] == '81']
P('rows', len(rows))
bydelta = {}
for r in rows:
    bydelta.setdefault(r['delta'], []).append(r)
worst = (F(0), None)
wabs = (F(0), None)
for delta, rs in bydelta.items():
    x = F(delta) - 1
    d, o = chain(81, x, 1)
    size = len(d)
    re = [0] * size
    im = [0] * size
    re[0] = U
    now = 0
    dt = U >> 5   # 1/32
    for r in sorted(rs, key=lambda z: int(z['t'])):
        t = int(r['t'])
        while now < t * 32:
            re, im = step(d, o, re, im, dt)
            now += 1
        norm = sum(a * a + b * b for a, b in zip(re, im))
        j = sum(i * (a * a + b * b) for i, (a, b) in enumerate(zip(re, im)))
        jbar = F(j, norm)
        read = F(int(r['jbar_ppb']), 10 ** 9)
        rel = abs(read / jbar - 1)
        ab = abs(read - jbar)
        if rel > worst[0]:
            worst = (rel, (delta, t, dec(jbar, 9), r['jbar_ppb']))
        if ab > wabs[0]:
            wabs = (ab, (delta, t, dec(jbar, 9), r['jbar_ppb']))
        P(' delta', delta, 't', t, 'own jbar', dec(jbar, 9), 'read', r['jbar_ppb'], 'dt', r['dt'], 'rel off e-7', dec(rel * 10 ** 7, 3))
P('largest relative off', dec(worst[0] * 10 ** 7, 3), 'e-7', worst[1], 'largest absolute', dec(wabs[0] * 10 ** 9, 2), 'e-9', wabs[1])
out.close()
