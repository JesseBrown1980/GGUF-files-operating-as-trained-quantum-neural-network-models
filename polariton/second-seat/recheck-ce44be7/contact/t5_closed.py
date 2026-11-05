#!/usr/bin/env python3
# t5_closed.py -- the first-correction closed forms exactly as typed into FINDINGS.txt, checked term by term against the machine at held-out delta.
# Every coefficient is compared as an exact rational: (sp, ti, k) -> (A_k, B_k) from t5_general.coeff_table.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import t5_firstcorr as F
import t5_general as G

def typed(d):
    """returns dict quantity -> {(sp, ti, k): (A, B)}; term = s^sp t^ti [A cosh(k g t) + B g sinh(k g t)]."""
    D3 = (1+d)**3*(1-d)**2
    D4 = (1+d)**4*(1-d)**2
    D5 = (1+d)**5*(1-d)**2
    out = {}
    z = {}
    # W10
    z[(1, 0, 1)] = ((Fr(65, 12) - Fr(85, 6)*d + 12*d**2 - 4*d**3)/D3, Fr(0))
    z[(1, 0, 3)] = ((Fr(5, 4) - d/2)/D3, Fr(0))
    z[(1, 0, 2)] = ((d - Fr(11, 3))*(1-d)/D3, Fr(0))
    z[(1, 0, 0)] = ((4*d - 3)*(1-d)**2/D3, Fr(0))
    z[(1, 1, 1)] = (Fr(0), (2*d**3 - 4*d**2 - 1)/D3)
    # W11
    z[(3, 0, 1)] = ((-Fr(53, 4) + Fr(81, 2)*d - 44*d**2 + 16*d**3)/D4, Fr(0))
    z[(3, 0, 3)] = ((Fr(5, 4) - d/2)/D4, Fr(0))
    z[(3, 0, 2)] = ((6*d - 8)*(1-d)/D4, Fr(0))
    z[(3, 0, 0)] = ((20 - 34*d + 16*d**2)*(1-d)/D4, Fr(0))
    z[(3, 1, 1)] = (Fr(0), (17 - 46*d + 34*d**2 - 8*d**3)/D4)
    out['z1'] = z
    c = {}
    # C10
    c[(0, 0, 4)] = ((d - Fr(5, 2))/D3, Fr(0))
    c[(0, 0, 2)] = ((3 + 10*d - 7*d**2)*(1-d)/D3, Fr(0))
    c[(0, 0, 0)] = ((-Fr(1, 2) - 8*d + 17*d**2 - 7*d**3)/D3, Fr(0))
    c[(0, 1, 2)] = (Fr(0), (6 - 12*d + 18*d**2 - 6*d**3)/D3)
    # C11
    c[(2, 0, 4)] = ((4*d - 10)/D4, Fr(0))
    c[(2, 0, 3)] = ((42 - 60*d + 24*d**2)/D4, Fr(0))
    c[(2, 0, 2)] = ((-40 + Fr(140, 3)*d - 16*d**2)*(1-d)/D4, Fr(0))
    c[(2, 0, 1)] = ((22 - Fr(428, 3)*d + Fr(632, 3)*d**2 - 96*d**3)/D4, Fr(0))
    c[(2, 0, 0)] = ((-14 + 112*d - 172*d**2 + 80*d**3)/D4, Fr(0))
    c[(2, 1, 1)] = (Fr(0), (-8 - 32*d**2 + 16*d**3)/D4)
    c[(2, 1, 2)] = (Fr(0), (-16 + 68*d - 28*d**2)/D4)
    # C12
    c[(4, 0, 4)] = ((2*d - 5)/D5, Fr(0))
    c[(4, 0, 3)] = ((42 - 60*d + 24*d**2)/D5, Fr(0))
    c[(4, 0, 2)] = ((-16 - 64*d + 64*d**2)*(1-d)/D5, Fr(0))
    c[(4, 0, 1)] = ((-234 + 700*d - 728*d**2 + 256*d**3)/D5, Fr(0))
    c[(4, 0, 0)] = ((213 - 594*d + 576*d**2 - 192*d**3)/D5, Fr(0))
    c[(4, 1, 1)] = (Fr(0), (136 - 368*d + 272*d**2 - 64*d**3)/D5)
    c[(4, 1, 2)] = (Fr(0), (-68 + 184*d - 136*d**2 + 32*d**3)/D5)
    out['C1_1'] = c
    return out

def main():
    pts = [Fr(0), Fr(1, 2), Fr(-1, 2), Fr(3, 4), Fr(-3, 4), Fr(2, 3), Fr(-5, 7), Fr(1, 9), Fr(5, 4), Fr(-5, 4), Fr(2), Fr(-2)]
    bad = 0; tot = 0
    for d in pts:
        F.W.g2 = 1 - d*d
        res = F.Dyn(F.Ctx(d, Fr(1))).results()
        ty = typed(d)
        for nm in ('z1', 'C1_1'):
            tab = G.coeff_table(res[nm])
            keys = set(tab) | set(ty[nm])
            for key in keys:
                a, b = tab.get(key, (Fr(0), Fr(0)))
                ta, tb = ty[nm].get(key, (Fr(0), Fr(0)))
                tot += 2
                if a != ta:
                    bad += 1; print('MISMATCH', d, nm, key, 'A', a, ta)
                if b != tb:
                    bad += 1; print('MISMATCH', d, nm, key, 'B', b, tb)
    print('CLOSED_FORMS_AS_TYPED|deltas=%d|coefficients=%d|mismatches=%d|float_used=0|json=0' % (len(pts), tot, bad))
    return 0

if __name__ == '__main__':
    sys.exit(main())
