#!/usr/bin/env python3
# reserved.py -- this lane's own check of every model run against the reserved set, before the run starts; written
# apart from the engine's guard. Reserved (PREDICTION.hbp BRIDGE_RESERVED, the seat's rule): delta = +3/5 or -3/5 at any
# N, y, t; y = 2/27 at N in {81, 729, 6561}. The trajectory is N-free (one run serves every N), so |y| near 2/27 is
# refused at every N. Arguments are taken exact only (int, Fraction, rational string; bool and float refused). Refused
# as well: |delta -+ 3/5| < 1/20 and ||y| - 2/27| < 1/81 on the exact rational, and the same bands on the 2^-256 and
# 2^-320 images (the base and reference fixed points of this lane's runs). Integers and rationals only.
from fractions import Fraction as Fr

RES_DELTA = (Fr(3, 5), Fr(-3, 5))
RES_ABS_Y = Fr(2, 27)
RES_N = (81, 729, 6561)
BAND_D = Fr(1, 20)
BAND_Y = Fr(1, 81)
POINTS_P = (256, 320)


def _q(v, what):
    if isinstance(v, bool) or not isinstance(v, (int, Fr, str)):
        raise SystemExit('RESERVED_REFUSED|arg=%s|reason=type_%s|json=0' % (what, type(v).__name__))
    return Fr(v)


def _image(q, p):
    n = abs(q.numerator) << p
    m = n // q.denominator
    return m if q.numerator >= 0 else -m


def hit(delta, ys):
    """the reason string if delta or any y touches the reserved set or its bands, else None"""
    d = _q(delta, 'delta')
    for r in RES_DELTA:
        if abs(d - r) < BAND_D:
            return 'delta=%s(band_of_%s)' % (d, r)
        for p in POINTS_P:
            w = (BAND_D.numerator << p) // BAND_D.denominator + 1
            if abs(_image(d, p) - _image(r, p)) <= w or abs(_image(d - 1, p) - _image(r - 1, p)) <= w:
                return 'delta=%s(image_band_of_%s_at_2^-%d)' % (d, r, p)
    for y in ys:
        a = abs(_q(y, 'y'))
        if abs(a - RES_ABS_Y) < BAND_Y:
            return 'y=%s(band_of_2/27,trajectory_N-free)' % a
        for p in POINTS_P:
            w = (BAND_Y.numerator << p) // BAND_Y.denominator + 1
            if abs(_image(a, p) - _image(RES_ABS_Y, p)) <= w:
                return 'y=%s(image_band_of_2/27_at_2^-%d)' % (a, p)
    return None


def clear(label, delta, ys, N='any'):
    """the RESERVED_CHECK row when (delta, ys) is clear; SystemExit before any model function runs otherwise"""
    r = hit(delta, ys)
    if r is not None:
        raise SystemExit('RESERVED_REFUSED|run=%s|hit=%s|json=0' % (label, r))
    return 'RESERVED_CHECK|run=%s|delta=%s|y=%s|N=%s|hit=none|checker=tools/reserved.py|json=0' % (
        label, Fr(delta), ','.join(str(Fr(y)) for y in ys), N)


if __name__ == '__main__':
    # self-test of the predicate alone: hit() on exact rationals, with the engine unloaded
    cases = [('3/5', ['1/27'], 1), ('-3/5', ['0'], 1), ('1/2', ['2/27'], 1), ('1/2', ['-2/27'], 1),
             ('1/2', [Fr(2, 27) + Fr(1, 1 << 300)], 1), ('1/4', ['0.0740740740740741'], 1),
             ('1/2', [Fr(2 / 27)], 1), (Fr(3, 5) + Fr(1, 1 << 300), ['1/27'], 1), ('27/50', ['1/27'], 0),
             ('11/20', ['1/27'], 1), ('1/2', ['1/27', '4/27', '1/81', '4/81', '1/243'], 0), ('-1/2', ['1/27'], 0),
             ('3/4', ['4/81'], 0), ('0', ['0'], 0), ('1/2', ['5/81'], 1), ('1/2', ['15/162'], 0), ('1/2', ['13/162'], 1), ('1/2', ['12/162'], 1)]
    bad = 0
    for d, ys, want in cases:
        got = 1 if hit(d, ys) is not None else 0
        bad += 0 if got == want else 1
        print('RESERVED_SELFTEST|delta=%s|y=%s|want_hit=%d|got_hit=%d|json=0' % (Fr(d), ','.join(str(Fr(y)) for y in ys), want, got))
    for v in (0.5, 2 / 27, True):
        try:
            hit(Fr(1, 2), [v])
            bad += 1
            print('RESERVED_SELFTEST|y_type=%s|refused=0|json=0' % type(v).__name__)
        except SystemExit:
            print('RESERVED_SELFTEST|y_type=%s|refused=1|json=0' % type(v).__name__)
    print('RESERVED_SELFTEST_SUMMARY|failed=%d|json=0' % bad)
    raise SystemExit(1 if bad else 0)
