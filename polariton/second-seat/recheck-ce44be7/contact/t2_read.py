#!/usr/bin/env python3
# t2_read.py -- reads the band grid rows against the law frozen in out/LAW-PREDICTIONS.hbp. Exact rationals, no float.
import sys, glob, os, hashlib
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import chebdrv as D
from law import law, dec

ROOT = 'C:/tmp/opus55/polariton-recheck-contact-20261105/out/'

def load_pred():
    pred = {}
    with open(ROOT + 'LAW-PREDICTIONS.hbp') as fh:
        for ln in fh:
            d = D.parse_row('X|' + ln.strip())
            key = (int(d['N']), Fr(d['delta']), Fr(d['y']), Fr(d['t']))
            pred[key] = d
    return pred

def load_grid(name):
    rows = []
    for path in sorted(glob.glob(ROOT + 'GRID-%s-N*.hbp' % name)):
        with open(path) as fh:
            for ln in fh:
                ln = ln.strip()
                if ln.startswith('ROW|'):
                    rows.append(D.parse_row(ln))
    return rows

def num(d, k, e=18):
    return Fr(int(d[k]), 10**e)

def merged(name):
    pred = load_pred()
    out = []
    for d in load_grid(name):
        N = int(d['N']); delta = Fr(d['delta']); y = Fr(d['y']); t = Fr(d['t'])
        L = law(N, delta, y, t)
        r = dict(N=N, delta=delta, y=y, t=t, s2=y*y*N, L=L,
                 V2=num(d, 'V2_e18'), A1=num(d, 'A1_e18'), C1=num(d, 'C1_e18'), D2=num(d, 'D2_e18'), f=num(d, 'f_e18'),
                 A=num(d, 'A_e18'), B=num(d, 'B_e18'), C2=num(d, 'C2_e18'), raw=d)
        if (N, delta, y, t) in pred:
            r['s'] = Fr(pred[(N, delta, y, t)]['s'])
        out.append(r)
    return out

def ratio(a, b):
    return a/b if b != 0 else None

def rng(vals, digits=4):
    vals = [v for v in vals if v is not None]
    if not vals:
        return 'none'
    return dec(min(vals), digits) + '..' + dec(max(vals), digits)

def band_tables(rows):
    print('TABLE1: ratio read/law by N and predicted depletion f. rows at each delta pooled. delta=+1 is apart since law A1=C1=0 there.')
    for N in sorted(set(r['N'] for r in rows)):
        for (lo, hi, name) in ((Fr(0), Fr(1, 20), 'f<=1/20'), (Fr(1, 20), Fr(1, 10), '1/20<f<=1/10'), (Fr(1, 10), Fr(1, 2), '1/10<f<=1/2'), (Fr(1, 2), Fr(10**9), 'f>1/2')):
            sel = [r for r in rows if r['N'] == N and r['delta'] != 1 and lo < r['L']['f'] <= hi]
            if not sel:
                continue
            print('N=%d %s rows=%d V2/law=%s A1/law=%s C1/law=%s D2/law=%s' % (
                N, name, len(sel),
                rng([ratio(r['V2'], r['L']['V2']) for r in sel]),
                rng([ratio(r['A1'], r['L']['A1']) for r in sel]),
                rng([ratio(r['C1'], r['L']['C1']) for r in sel]),
                rng([ratio(r['D2'], r['L']['D2']) for r in sel])))

def scaling(rows):
    print('TABLE2: (V2/law-1) x N at fixed (delta, y^2N ~ s^2, t), N across, for the smallest-f rows: 1/N scaling appears as a constant.')
    # group by delta, s, t
    groups = {}
    for r in rows:
        if 's' in r:
            groups.setdefault((r['delta'], r['s'], r['t']), []).append(r)
    for key in sorted(groups):
        g = sorted(groups[key], key=lambda r: r['N'])
        if len(g) < 3 or key[0] == 1:
            continue
        if key[2] not in (Fr(1), Fr(2)):
            continue
        if key[1] not in (Fr(1, 4), Fr(1), Fr(4)):
            continue
        parts = []
        for r in g:
            q = ratio(r['V2'], r['L']['V2'])
            a = ratio(r['A1'], r['L']['A1'])
            c = ratio(r['C1'], r['L']['C1'])
            parts.append('N=%d:f=%s,V2:%s,A1:%s,C1:%s' % (r['N'], dec(r['L']['f'], 3), dec((q-1)*r['N'], 2), dec((a-1)*r['N'], 2), dec((c-1)*r['N'], 2)))
        print('delta=%s s=%s t=%s  ' % key + ' '.join(parts))

def per_delta(rows):
    print('TABLE3: per delta, largest |V2/law - 1| at predicted f<=1/20, and the row; the same at f<=1/2. delta=+1 apart.')
    for delta in sorted(set(r['delta'] for r in rows)):
        if delta == 1:
            continue
        for N in sorted(set(r['N'] for r in rows)):
            sel = [r for r in rows if r['N'] == N and r['delta'] == delta]
            for (hi, name) in ((Fr(1, 20), 'f<=1/20'), (Fr(1, 2), 'f<=1/2')):
                s2 = [r for r in sel if r['L']['f'] <= hi]
                if not s2:
                    continue
                w = max(s2, key=lambda r: abs(ratio(r['V2'], r['L']['V2'])-1))
                print('delta=%s N=%d %s rows=%d worst V2/law=%s at y2N=%s t=%s read=%s law=%s f_read=%s' % (delta, N, name, len(s2), dec(ratio(w['V2'], w['L']['V2']), 4), dec(w['s2'], 4), w['t'], dec(w['V2'], 5), dec(w['L']['V2'], 5), dec(w['f'], 4)))

def edge_plus(rows):
    print('TABLE4: delta=+1, law A1=0, C1=0, Y=0, D2=2y^2t^2. Read values, and scaling with N at fixed s.')
    sel = [r for r in rows if r['delta'] == 1]
    for r in sorted(sel, key=lambda r: (r['s'], r['t'], r['N'])):
        if r['t'] in (Fr(1), Fr(2), Fr(3)) and r['s'] in (Fr(1, 4), Fr(1), Fr(4)):
            print('N=%d s=%s t=%s A1=%s C1=%s V2=%s D2/law=%s A1*N^1.5=%s C1*N^2=%s sign_A=%s f=%s' % (
                r['N'], r['s'], r['t'], dec(r['A1'], 10), dec(r['C1'], 10), dec(r['V2'], 6),
                dec(ratio(r['D2'], r['L']['D2']), 4), dec(r['A1']*r['N']*Fr(r['N']**(1), 1)**0, 4), dec(r['C1']*r['N']*r['N'], 3),
                ('-' if r['A'] < 0 else '+'), dec(r['f'], 4)))

def edge_minus(rows):
    print('TABLE5: delta=-1 limit forms.')
    sel = [r for r in rows if r['delta'] == -1]
    for r in sorted(sel, key=lambda r: (r['s'], r['t'], r['N'])):
        if r['s'] in (Fr(1, 4), Fr(1), Fr(4)):
            print('N=%d s=%s t=%s f=%s V2=%s law=%s ratio=%s A1/law=%s C1/law=%s D2/law=%s' % (
                r['N'], r['s'], r['t'], dec(r['f'], 4), dec(r['V2'], 5), dec(r['L']['V2'], 5), dec(ratio(r['V2'], r['L']['V2']), 4),
                dec(ratio(r['A1'], r['L']['A1']), 4), dec(ratio(r['C1'], r['L']['C1']), 4), dec(ratio(r['D2'], r['L']['D2']), 4)))

if __name__ == '__main__':
    print('prediction_file_sha256', hashlib.sha256(open(ROOT + 'LAW-PREDICTIONS.hbp', 'rb').read()).hexdigest())
    rows = merged('band')
    print('rows_read', len(rows))
    band_tables(rows)
    scaling(rows)
    per_delta(rows)
    edge_plus(rows)
    edge_minus(rows)
