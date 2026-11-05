#!/usr/bin/env python3
# t4_summary.py -- per exact trace: first f peak; the first time V2/law leaves 5%; the values of the parts there; V2/law at the peak;
# the first f minimum after the peak (the return); V2 and <A^2>/<A^dag A> there; the largest and smallest V2/law up to t = 12.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import t4_trace_read as T
from law import law, dec

def main():
    for N in [int(v) for v in sys.argv[1:]]:
        rows = T.load(N)
        print('N=%d chains=%d (delta, y2N)' % (N, len(rows)))
        print(' delta y2N Y(t_peak) t_peak f_peak V2/law@peak A1/law@peak C1/law@peak | t_leave5pct V2/law A1/law C1/law f | t_return f_ret V2_ret V2/law_ret A2/AdA_ret D2_ret | max_V2/law at_t | min_V2/law at_t (t>=1)')
        for key in sorted(rows):
            delta, y = key
            ds = rows[key]
            ip = T.first_peak(ds)
            rec = []
            for d in ds:
                t = Fr(d['t'])
                L = law(N, delta, y, t)
                V2 = T.g(d, 'V2_e18')
                rec.append(dict(t=t, L=L, V2=V2, r=V2/L['V2'] if L['V2'] not in (0, None) else None, a=T.g(d, 'A1_e18')/L['A1'] if L['A1'] != 0 else None,
                                c=T.g(d, 'C1_e18')/L['C1'] if L['C1'] != 0 else None, f=T.g(d, 'f_e18'), w=T.g(d, 'Am2_re_e18')/T.g(d, 'Am1_nrm_e18') if T.g(d, 'Am1_nrm_e18') != 0 else None, D2=T.g(d, 'D2_e18')))
            leave = None
            for x in rec:
                if x['t'] >= 1 and x['r'] is not None and abs(x['r']-1) > Fr(1, 20):
                    leave = x
                    break
            ret = None
            if ip is not None:
                for i in range(ip+1, len(rec)-1):
                    if rec[i]['f'] <= rec[i-1]['f'] and rec[i]['f'] <= rec[i+1]['f']:
                        ret = rec[i]
                        break
            sel = [x for x in rec if x['t'] >= 1 and x['r'] is not None]
            mx = max(sel, key=lambda x: x['r'])
            mn = min(sel, key=lambda x: x['r'])
            p = rec[ip] if ip is not None else None
            print(' %s %s %s %s %s %s %s %s | %s | %s | %s %s | %s %s' % (
                delta, dec(y*y*N, 3),
                dec(p['L']['Y'], 3) if p else 'na', p['t'] if p else 'na', dec(p['f'], 3) if p else 'na', dec(p['r'], 3) if p else 'na', dec(p['a'], 3) if p else 'na', dec(p['c'], 3) if p else 'na',
                ('%s %s %s %s %s' % (leave['t'], dec(leave['r'], 3), dec(leave['a'], 3), dec(leave['c'], 3), dec(leave['f'], 3))) if leave else 'none',
                ('%s %s %s %s %s %s' % (ret['t'], dec(ret['f'], 3), dec(ret['V2'], 3), dec(ret['r'], 3), dec(ret['w'], 3), dec(ret['D2'], 4))) if ret else 'none',
                dec(mx['r'], 2), mx['t'], dec(mn['r'], 3), mn['t']))
    return 0

if __name__ == '__main__':
    sys.exit(main())
