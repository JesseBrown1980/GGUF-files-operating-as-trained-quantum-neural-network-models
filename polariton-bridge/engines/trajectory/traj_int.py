#!/usr/bin/env python3
# traj_int.py -- single classical trajectory of the FULL three-mode model (z0, z+, z-), integer fixed point, Taylor method.
# Independent of exact.py (no shared code). No float.
#   i z+' = x z+ + u(|z0|^2 + |z-|^2) z+ + conj(z-) z0^2 - y z0
#   i z-' = x z- + u(|z0|^2 + |z+|^2) z- + conj(z+) z0^2 - y z0
#   i z0' = u(|z+|^2 + |z-|^2) z0 + 2 z+ z- conj(z0) - y (z+ + z-)
# z = c / sqrt(N); start z0 = 1, z+ = z- = 0.  Observables in the quantum read's normalisation:
#   A/N = conj(z0) z+ + conj(z-) z0,  A1 = 2|A/N|,  C1 = 2 N/(N-1) [ |z0|^2(|z+|^2+|z-|^2) + 2 Re(conj(z+) conj(z-) z0^2) ],
#   V2 = A1^2/(2 C1),  f = |z+|^2 + |z-|^2,  D2 = 2|conj(z-) z+|.
# RESERVED POINTS ARE REFUSED: delta = +-3/5 at any y, and y = +-2/27 at any delta (the trajectory is N-free).
# The one opening is the keyword allow_reserved=True (the literal True) of guard() and Traj(): it admits delta = +-3/5
#   exactly, at every listed y, the blind points of PREDICTION.hbp, for the blind-run driver after that file is pushed
#   (BRIDGE_ENGINE_CHANGE, PREDICTION.hbp line 446). y = +-2/27 at any other delta stays refused with or without it.
# The guard reads each argument twice: as the exact rational, and as the 2^-P fixed-point image the run would use
#   (delta, x = delta - u at u = 1, and y). Each is checked against the lists, the reserved values and a band around
#   each reserved value (guard_checks names every check that refuses). u takes the frozen map's value 1 only.
# The printed integration bound (BRIDGE_ERRORS integration_trajectory): Traj(..., bound=True) carries an upper bound
#   on |z_int(t) - z(t)|_2 at order K, h = 1/hden, 2^-P fixed point, and bound_row() prints it (method at _bound_step);
#   obs_bound_row(N) prints the bounds of the observables A1, C1, f, D2 and of the V2 identity (method at _obs_terms).
# Every check of the step grid, of the flags and of the arguments is an explicit raise, so python -O keeps it.
from fractions import Fraction as Fr
from math import isqrt, lcm

P = 256
ONE = 1 << P

def fx(q):
    q = Fr(q)
    return (q.numerator << P) // q.denominator if q >= 0 else -((-q.numerator << P) // q.denominator)

def cm(a, b):
    return ((a[0] * b[0] - a[1] * b[1]) >> P, (a[0] * b[1] + a[1] * b[0]) >> P)

def cconj(a):
    return (a[0], -a[1])

def cadd(a, b):
    return (a[0] + b[0], a[1] + b[1])

def cscale_int(a, k):
    return (a[0] * k, a[1] * k)

def cmi(a):          # multiply by -i
    return (a[1], -a[0])

ALLOWED_DELTA = {Fr(0), Fr(1, 2), Fr(-1, 2), Fr(3, 4), Fr(-3, 4), Fr(1, 4), Fr(-1, 4)}
# |y| of the validation runs and of the blind points (BRIDGE_POINT); y = +-2/27 runs only at delta = +-3/5 under the flag
ALLOWED_ABS_Y = {Fr(0), Fr(1, 243), Fr(2, 243), Fr(4, 243), Fr(1, 81), Fr(2, 81), Fr(4, 81), Fr(1, 27), Fr(2, 27), Fr(4, 27)}
RESERVED_DELTA = (Fr(3, 5), Fr(-3, 5))
RESERVED_ABS_Y = Fr(2, 27)
# The bands around the reserved values: |delta -+ 3/5| < 1/20 and ||y| - 2/27| < 1/81 (the ensemble engine's widths).
# They hold the review's 2^-128 neighbourhoods (its reserved_rv.py), a float near 2/27 and a decimal string near it;
# every listed value lies outside them (nearest: delta = 1/2 at 1/10, |y| = 4/81 at 2/81).
BAND_DELTA = Fr(1, 20)
BAND_Y = Fr(1, 81)

def _exact(v, what):
    """the exact rational of an argument: int (not bool), Fraction or a rational string; anything else is refused"""
    if type(v) not in (int, Fr, str):
        raise SystemExit('REFUSED: delta and y take int, Fraction or a rational string, got %s for %s' % (type(v).__name__, what))
    try:
        return Fr(v)
    except (ValueError, ZeroDivisionError):
        raise SystemExit('REFUSED: delta and y take int, Fraction or a rational string, got %r for %s' % (v, what))

def _img(q):
    """the 2^-P fixed-point image of the rational q, truncated toward zero as fx() makes it; written apart from fx"""
    q = Fr(q)
    m = (abs(q.numerator) << P) // q.denominator
    return m if q.numerator >= 0 else -m

def _img_within(a, b, band):
    """images a, b (integers at 2^-P) within the band (a rational), one unit of the last place added for the truncation"""
    return abs(a - b) <= ((band.numerator << P) // band.denominator) + 1

def guard_checks(delta, y, *, allow_reserved=False):
    """the names of the checks that refuse (delta, y), in a list; an empty list admits the run. Every check is computed
    on its own, so each one is tested alone. The flag opens delta = +-3/5 only when the exact rational and every image
    equal the reserved value's, and y = +-2/27 only there."""
    if allow_reserved is not True and allow_reserved is not False:
        raise SystemExit('REFUSED: allow_reserved=%r; the flag takes the literal True or False' % (allow_reserved,))
    d = _exact(delta, 'delta'); yv = _exact(y, 'y'); ay = abs(yv)
    hits = []
    # the exact rationals: the lists and the reserved values
    if ay not in ALLOWED_ABS_Y:
        hits.append('Y_LIST')
    if d not in ALLOWED_DELTA and not (allow_reserved is True and d in RESERVED_DELTA):
        hits.append('DELTA_LIST')
    if d in RESERVED_DELTA and allow_reserved is not True:
        hits.append('DELTA_RESERVED')
    if ay == RESERVED_ABS_Y and not (allow_reserved is True and d in RESERVED_DELTA):
        hits.append('Y_RESERVED')
    # the exact rationals: the bands
    for r in RESERVED_DELTA:
        if abs(d - r) < BAND_DELTA and not (allow_reserved is True and d == r):
            hits.append('DELTA_BAND')
    if abs(ay - RESERVED_ABS_Y) < BAND_Y and not (allow_reserved is True and d in RESERVED_DELTA and ay == RESERVED_ABS_Y):
        hits.append('Y_BAND')
    # the 2^-P images the run would use: delta's own, x = delta - u at u = 1, and |y|'s
    for r in RESERVED_DELTA:
        if _img_within(_img(d), _img(r), BAND_DELTA) and not (allow_reserved is True and d == r and _img(d) == _img(r)):
            hits.append('DELTA_IMAGE')
        if _img_within(_img(d - 1), _img(r - 1), BAND_DELTA) and not (
                allow_reserved is True and d == r and _img(d - 1) == _img(r - 1)):
            hits.append('X_IMAGE')
    iy = abs(_img(yv)); ir = _img(RESERVED_ABS_Y)
    if _img_within(iy, ir, BAND_Y) and not (allow_reserved is True and d in RESERVED_DELTA and ay == RESERVED_ABS_Y and iy == ir):
        hits.append('Y_IMAGE')
    return hits

def guard(delta, y, *, allow_reserved=False):
    """refuses (SystemExit, before any model function runs) every (delta, y) that guard_checks names a check for"""
    hits = guard_checks(delta, y, allow_reserved=allow_reserved)
    if not hits:
        return
    d = Fr(delta); yv = Fr(y)
    tail = ' [checks=%s]' % ','.join(hits)
    if 'Y_LIST' in hits:
        raise SystemExit('REFUSED: y=%s outside the allowed list' % yv + tail)
    if 'DELTA_RESERVED' in hits or 'Y_RESERVED' in hits:
        raise SystemExit('REFUSED: reserved point delta=%s y=%s (CANNOT_SEE by rule)' % (d, yv) + tail)
    if 'DELTA_LIST' in hits:
        raise SystemExit('REFUSED: delta=%s outside the allowed list' % d + tail)
    raise SystemExit('REFUSED: near a reserved point delta=%s y=%s' % (d, yv) + tail)

def guard_u(u):
    """u takes the frozen map's value 1 (BRIDGE_TRAJ_MAP: u=1, x=delta-1), as the exact rational and as its image"""
    if type(u) not in (int, Fr, str):
        raise SystemExit('REFUSED: u=%r; u takes the frozen map value 1 as int, Fraction or a rational string' % (u,))
    try:
        uq = Fr(u)
    except (ValueError, ZeroDivisionError):
        raise SystemExit('REFUSED: u=%r; u takes the frozen map value 1' % (u,))
    if uq != 1 or _img(uq) != ONE:
        raise SystemExit('REFUSED: u=%s; u takes the frozen map value 1' % uq)

# ---------------------------------------------------------------- exact helpers of the bound (integers and rationals)
BND = 768            # every bound is rounded up to a multiple of 2^-BND

def _ceil_dy(q):
    q = Fr(q)
    return Fr(-((-q.numerator << BND) // q.denominator), 1 << BND)

def _isqrt_up(n):
    r = isqrt(n)
    return r if r * r == n else r + 1

def _sqrt_up(q):
    q = Fr(q)
    return Fr(_isqrt_up(-((-q.numerator << (2 * BND)) // q.denominator)), 1 << BND)

def _sqrt_lo(q):
    """a lower bound of sqrt(q) for a rational q >= 0"""
    q = Fr(q)
    return Fr(isqrt((q.numerator << (2 * BND)) // q.denominator), 1 << BND)

def _exp_up(q):
    """an upper bound of e^q for a rational 0 <= q <= 1"""
    q = Fr(-((-Fr(q).numerator << 64) // Fr(q).denominator), 1 << 64)
    if not 0 <= q <= 1:
        raise AssertionError('_exp_up takes 0 <= q <= 1, got %s' % q)
    s = Fr(0); term = Fr(1)
    for k in range(1, 31):
        s += term
        term = term * q / k
    return _ceil_dy(s + 3 * term)       # tail sum_{k>=30} q^k/k! <= (q^30/30!) e^q <= 3 q^30/30!

def _gmax(R2, u):
    """max of s^2 + 2u^2 (R2-s) s + 2(|u| s/2 + R2 - s)^2 over 0 <= s <= R2: the bound of |S|_F^2 on |z|_2^2 <= R2"""
    u = abs(Fr(u)); R2 = Fr(R2)
    al = u / 2 - 1
    A = 1 - 2 * u * u + 2 * al * al
    B = 2 * u * u * R2 + 4 * al * R2
    C = 2 * R2 * R2
    cands = [C, A * R2 * R2 + B * R2 + C]
    if A < 0 and 0 <= -B / (2 * A) <= R2:
        s = -B / (2 * A)
        cands.append(A * s * s + B * s + C)
    return max(cands)

def _pmul(ar, ai, br, bi):
    """exact product of two complex integer polynomials given as real and imaginary coefficient lists"""
    cr = [0] * (len(ar) + len(br) - 1); ci = [0] * (len(ar) + len(br) - 1)
    for i in range(len(ar)):
        p, q = ar[i], ai[i]
        if p == 0 and q == 0:
            continue
        for j in range(len(br)):
            cr[i + j] += p * br[j] - q * bi[j]
            ci[i + j] += p * bi[j] + q * br[j]
    return cr, ci

def _padd(a, b):
    n = max(len(a[0]), len(b[0]))
    pad = lambda v: v + [0] * (n - len(v))
    return [s + t for s, t in zip(pad(a[0]), pad(b[0]))], [s + t for s, t in zip(pad(a[1]), pad(b[1]))]

def _pscale(a, k):
    return [k * v for v in a[0]], [k * v for v in a[1]]

def _residual(Z0, ZP, ZM, Dp, X, U, Y):
    """coefficients of rho = F(p) - p' at scale Dp 2^(3P), F with x = X/Dp, u = U/Dp, y = Y/Dp, as squared norms"""
    K = len(Z0) - 1
    c0 = ([c[0] for c in Z0], [c[1] for c in Z0])
    cp = ([c[0] for c in ZP], [c[1] for c in ZP])
    cq = ([c[0] for c in ZM], [c[1] for c in ZM])
    cj = lambda a: (a[0], [-v for v in a[1]])
    sh = lambda a, k: ([(k * v) << (2 * P) for v in a[0]], [(k * v) << (2 * P) for v in a[1]])
    q0 = _pmul(*c0, *cj(c0)); qp = _pmul(*cp, *cj(cp)); qm = _pmul(*cq, *cj(cq))
    s0 = _pmul(*c0, *c0); pm = _pmul(*cp, *cq)
    Gp = _padd(_padd(_pscale(_pmul(*_padd(q0, qm), *cp), U), _pscale(_pmul(*s0, *cj(cq)), Dp)), _padd(sh(cp, X), sh(c0, -Y)))
    Gm = _padd(_padd(_pscale(_pmul(*_padd(q0, qp), *cq), U), _pscale(_pmul(*s0, *cj(cp)), Dp)), _padd(sh(cq, X), sh(c0, -Y)))
    G0 = _padd(_padd(_pscale(_pmul(*_padd(qp, qm), *c0), U), _pscale(_pmul(*pm, *cj(c0)), 2 * Dp)), sh(_padd(cp, cq), -Y))
    out = []
    for n in range(3 * K + 1):
        s = 0
        for G, c in ((G0, c0), (Gp, cp), (Gm, cq)):
            fr = G[1][n] if n < len(G[1]) else 0           # F = -i G
            fi = -G[0][n] if n < len(G[0]) else 0
            if n < K:                                       # minus p' = (n+1) C_{n+1}
                fr -= ((n + 1) * Dp * c[0][n + 1]) << (2 * P)
                fi -= ((n + 1) * Dp * c[1][n + 1]) << (2 * P)
            s += fr * fr + fi * fi
        out.append(s)
    return out

def _sci_up(q, sig=3):
    """a decimal upper bound of the rational q >= 0 with sig significant digits, integers only"""
    q = Fr(q)
    if q <= 0:
        return '0'
    e = 0
    while q >= 10:
        q /= 10; e += 1
    while q < 1:
        q *= 10; e -= 1
    sc = -((-q.numerator * 10 ** (sig - 1)) // q.denominator)
    if sc >= 10 ** sig:
        sc //= 10; e += 1
    s = str(sc)
    return s[0] + '.' + s[1:] + 'e' + ('%+d' % e)

class Traj:
    def __init__(self, delta, y, u=Fr(1), K=28, hden=32, *, allow_reserved=False, bound=False):
        guard(delta, y, allow_reserved=allow_reserved)
        guard_u(u)
        if not (type(hden) is int and hden > 0 and hden & (hden - 1) == 0):
            raise AssertionError('hden takes a power of two')
        if not (type(K) is int and K >= 1):
            raise AssertionError('K takes a positive integer')
        if bound is not True and bound is not False:
            raise SystemExit('REFUSED: bound=%r; the flag takes the literal True or False' % (bound,))
        self.delta = Fr(delta); self.y = Fr(y); self.u = Fr(u)
        self.x = fx(self.delta - self.u); self.uu = fx(self.u); self.yy = fx(self.y)
        if self.x != _img(self.delta - 1) or self.yy != _img(self.y) or self.uu != ONE:
            raise SystemExit('REFUSED: the run images x=%d y=%d u=%d differ from the images the guard compared' % (
                self.x, self.yy, self.uu))
        self.K = K; self.hden = hden
        self.hb = hden.bit_length() - 1
        self.z0 = (ONE, 0); self.zp = (0, 0); self.zm = (0, 0)
        self.step_count = 0
        self.half_step = 0
        self.reserved_open = allow_reserved is True and self.delta in (Fr(3, 5), Fr(-3, 5))
        self.bound = bound is True
        if self.bound:
            self._bound_init()
    def taylor_step(self):
        K = self.K
        Z0 = [self.z0]; ZP = [self.zp]; ZM = [self.zm]
        Q0 = []; QP = []; QM = []; S0 = []; PM = []
        for n in range(0, K):
            # coefficient n of the auxiliary products
            def cauchy(A, B, conjB=False):
                acc = (0, 0)
                for k in range(0, n + 1):
                    b = B[n - k]
                    acc = cadd(acc, cm(A[k], cconj(b) if conjB else b))
                return acc
            Q0.append(cauchy(Z0, Z0, True)); QP.append(cauchy(ZP, ZP, True)); QM.append(cauchy(ZM, ZM, True))
            S0.append(cauchy(Z0, Z0)); PM.append(cauchy(ZP, ZM))
            # RHS coefficient n
            accp = cm((self.x, 0), ZP[n])
            accm = cm((self.x, 0), ZM[n])
            acc0 = (0, 0)
            for k in range(0, n + 1):
                accp = cadd(accp, cm(cm((self.uu, 0), cadd(Q0[k], QM[k])), ZP[n - k]))
                accm = cadd(accm, cm(cm((self.uu, 0), cadd(Q0[k], QP[k])), ZM[n - k]))
                accp = cadd(accp, cm(cconj(ZM[k]), S0[n - k]))
                accm = cadd(accm, cm(cconj(ZP[k]), S0[n - k]))
                acc0 = cadd(acc0, cm(cm((self.uu, 0), cadd(QP[k], QM[k])), Z0[n - k]))
                acc0 = cadd(acc0, cscale_int(cm(PM[k], cconj(Z0[n - k])), 2))
            yz0 = cm((self.yy, 0), Z0[n])
            accp = (accp[0] - yz0[0], accp[1] - yz0[1])
            accm = (accm[0] - yz0[0], accm[1] - yz0[1])
            ys = cm((self.yy, 0), cadd(ZP[n], ZM[n]))
            acc0 = (acc0[0] - ys[0], acc0[1] - ys[1])
            # X_{n+1} = -i RHS_n / (n+1)
            def nxt(r):
                r = cmi(r)
                return (r[0] // (n + 1), r[1] // (n + 1))
            ZP.append(nxt(accp)); ZM.append(nxt(accm)); Z0.append(nxt(acc0))
        def horner(C):
            acc = (0, 0)
            for k in range(len(C) - 1, -1, -1):
                acc = (C[k][0] + (acc[0] >> self.hb), C[k][1] + (acc[1] >> self.hb))
            return acc
        self.z0 = horner(Z0); self.zp = horner(ZP); self.zm = horner(ZM)
        self.step_count += 1
        if self.bound:
            self._bound_step(Z0, ZP, ZM)
    def time(self):
        return Fr(2 * self.step_count + self.half_step, 2 * self.hden)
    def advance_to(self, t):
        t = Fr(t)
        target = t * self.hden
        if target.denominator != 1 or self.half_step:
            raise AssertionError('time off the step grid')
        if target < self.step_count:
            raise AssertionError('time behind the run')
        while self.step_count < target:
            self.taylor_step()
    def read_at(self, t):
        """the state at t, t a multiple of 1/(2 hden): this run advances to the grid point at or below t, and a copy takes
        one half step from it. The step coefficients depend on the state only, so the copy evaluates the same polynomial
        at s = 1/(2 hden); its bound (bound=True) covers that half step. This run stays on its grid."""
        t = Fr(t)
        j = (t * self.hden).numerator // (t * self.hden).denominator
        if not ((t * 2 * self.hden).denominator == 1 and j >= self.step_count and not self.half_step):
            raise AssertionError('time off the half-step grid or behind')
        self.advance_to(Fr(j, self.hden))
        r = type(self).__new__(type(self))
        r.__dict__.update(self.__dict__)
        if t != self.time():
            r.hden = 2 * self.hden; r.hb = self.hb + 1; r.step_count = 2 * self.step_count
            r.taylor_step()
            r.hden = self.hden; r.hb = self.hb; r.step_count = self.step_count; r.half_step = 1
        return r
    def obs(self, N):
        N = Fr(N)
        z0, zp, zm = self.z0, self.zp, self.zm
        a0 = cm(z0, cconj(z0))[0]; ap = cm(zp, cconj(zp))[0]; am = cm(zm, cconj(zm))[0]
        A = cadd(cm(cconj(z0), zp), cm(cconj(zm), z0))
        A2 = (A[0] * A[0] + A[1] * A[1]) >> P          # |A/N|^2
        Pp = cm(cm(cconj(zp), cconj(zm)), cm(z0, z0))   # P/N^2
        X = ((a0 * (ap + am)) >> P) + 2 * Pp[0]          # [n0(n+ + n-) + 2 Re P]/N^2
        BB = cm(cconj(zm), zp)
        res = {}
        res['A_re'] = Fr(A[0], ONE); res['A_im'] = Fr(A[1], ONE)
        res['A1sq'] = 4 * Fr(A2, ONE)
        res['C1'] = 2 * N / (N - 1) * Fr(X, ONE)
        res['X'] = Fr(X, ONE); res['A2'] = Fr(A2, ONE)
        res['f'] = Fr(ap + am, ONE)
        res['D2sq'] = 4 * Fr((BB[0] * BB[0] + BB[1] * BB[1]) >> P, ONE)
        res['norm'] = Fr(a0 + ap + am, ONE)
        res['sym'] = Fr(abs(zp[0] - zm[0]) + abs(zp[1] - zm[1]), ONE)
        # energy per N in z units
        x = Fr(self.x, ONE); u = Fr(self.uu, ONE); y = Fr(self.yy, ONE)
        Ppm = Fr(Pp[0], ONE)
        E = x * res['f'] + u * (Fr(a0, ONE) * res['f'] + Fr(ap, ONE) * Fr(am, ONE)) + 2 * Ppm \
            - 2 * y * (Fr(cm(cconj(z0), cadd(zp, zm))[0], ONE))
        res['E'] = E
        return res
    # ---------------------------------------------------------------- the printed integration bound
    # e_j bounds |Z_j - z(t_j)|_2: Z_j the integer state after j steps, z the exact solution of the model with the exact
    # rational x = delta - u, u, y (not their 2^-P images). Per step (DERIVED; exact integer and rational arithmetic,
    # every rounding upward):
    #   p(s) = sum_{n<=K} C_n s^n, the step's own coefficients (C_0 = Z_j exactly); w(s) = the exact flow from Z_j.
    #   r = w - p, r(0) = 0, r' = F(p + r) - F(p) + rho, rho = F(p) - p', a polynomial of degree 3K computed exactly;
    #   rho carries the truncation at order K, the rounding of the recursion and the 2^-P images of x, u, y.
    #   The model is i z' = dH/dconj(z) with H real, so the complex-linear part of DF is skew and its logarithmic norm is
    #   at most |S|_F, S = d^2 H/dconj(z)^2 = [[2z+z-, u z0 z+, u z0 z-], [u z0 z+, 0, u z+ z- + z0^2], [u z0 z-, ., 0]],
    #   and |S|_F^2 <= _gmax(R^2) on the ball |z|_2 <= R. |z|_2 is conserved exactly by the exact flow.
    #   |w(h) - p(h)| <= e^(mu_p h) sum_n |rho_n| h^(n+1)/(n+1), mu_p = sqrt(_gmax(R_p^2)), R_p = sum_n |C_n| h^n;
    #   |Z_{j+1} - p(h)| (the Horner rounding) is computed exactly;
    #   e_{j+1} <= e^(mu_g h) e_j + both, mu_g = sqrt(_gmax(max(1, |Z_j|^2))); e_0 = 0 (the start (1, 0, 0) is exact).
    def _bound_init(self):
        xq = self.delta - self.u; uq = self.u; yq = self.y
        Dp = lcm(xq.denominator, uq.denominator, yq.denominator)
        self.bpar = (Dp, xq.numerator * (Dp // xq.denominator), uq.numerator * (Dp // uq.denominator),
                     yq.numerator * (Dp // yq.denominator))
        self.berr = Fr(0); self.bsum = Fr(0); self.bmax_local = Fr(0); self.bmax_res = Fr(0)
        self.bmax_horner = Fr(0); self.bmax_mu_p = Fr(0); self.bmax_mu_g = Fr(0); self.bmax_Rp = Fr(0)
        self.bR = Fr(1)
    def _bound_step(self, Z0, ZP, ZM):
        K = self.K; hb = self.hb; h = Fr(1, self.hden)
        Dp, X, U, Y = self.bpar
        Rp = Fr(0)
        for n in range(K + 1):
            nn = Z0[n][0] ** 2 + Z0[n][1] ** 2 + ZP[n][0] ** 2 + ZP[n][1] ** 2 + ZM[n][0] ** 2 + ZM[n][1] ** 2
            if n == 0:
                Zj2 = Fr(nn, 1 << (2 * P))
            Rp += Fr(_isqrt_up(nn), 1 << (P + hb * n))
        Rp = _ceil_dy(Rp)
        mu_p = _sqrt_up(_gmax(Rp * Rp, self.u))
        res = _residual(Z0, ZP, ZM, Dp, X, U, Y)
        Ir = Fr(0)
        for n in range(len(res)):
            Ir += Fr(_isqrt_up(res[n]), Dp * (n + 1) << (3 * P + hb * (n + 1)))
        Ir = _ceil_dy(Ir)
        dh = 0
        for C, z in ((Z0, self.z0), (ZP, self.zp), (ZM, self.zm)):
            er = (z[0] << (hb * K)) - sum(C[n][0] << (hb * (K - n)) for n in range(K + 1))
            ei = (z[1] << (hb * K)) - sum(C[n][1] << (hb * (K - n)) for n in range(K + 1))
            dh += er * er + ei * ei
        hor = Fr(_isqrt_up(dh), 1 << (P + hb * K))
        local = _ceil_dy(hor + _exp_up(mu_p * h) * Ir)
        mu_g = _sqrt_up(_gmax(max(Fr(1), Zj2), self.u))
        self.berr = _ceil_dy(_exp_up(mu_g * h) * self.berr + local)
        self.bsum += local
        self.bmax_local = max(self.bmax_local, local); self.bmax_res = max(self.bmax_res, Ir)
        self.bmax_horner = max(self.bmax_horner, hor); self.bmax_mu_p = max(self.bmax_mu_p, mu_p)
        self.bmax_mu_g = max(self.bmax_mu_g, mu_g); self.bmax_Rp = max(self.bmax_Rp, Rp)
        n2 = sum(v * v for v in (self.z0[0], self.z0[1], self.zp[0], self.zp[1], self.zm[0], self.zm[1]))
        self.bR = max(Fr(1), _sqrt_up(Fr(n2, 1 << (2 * P))))
    def _bound_on(self):
        if self.bound is not True:
            raise SystemExit('REFUSED: the bound rows need Traj(..., bound=True)')
    def bound_row(self):
        """the printed bound at the current time: the state, and f and A/N as obs() computes them (obs rounding added)"""
        self._bound_on()
        e = self.berr; R = self.bR
        f_err = e * (R + 1) + Fr(2, ONE)
        A_err = 2 * R * e + Fr(3, ONE)
        return ('TRAJ_BOUND|delta=%s|y=%s|t=%s|order=%d|h=1/%d|fixed_point=2^-%d|steps=%d|half_step=%d|state_err_2norm_le=%s|'
                'f_err_le=%s|A_over_N_err_le=%s|sum_local_le=%s|max_local_le=%s|max_residual_part_le=%s|'
                'max_horner_part_le=%s|mu_g_le=%s|mu_p_le=%s|R_p_le=%s|R_now_le=%s|reserved_open=%d|'
                'method=residual_rho=F(p)-dp/ds_exact,log_norm_from_d2H/dconj(z)^2,Horner_exact|float_used=0|json=0') % (
            self.delta, self.y, self.time(), self.K, self.hden, P, self.step_count, self.half_step, _sci_up(e), _sci_up(f_err),
            _sci_up(A_err), _sci_up(self.bsum), _sci_up(self.bmax_local), _sci_up(self.bmax_res),
            _sci_up(self.bmax_horner), _sci_up(self.bmax_mu_g, 6), _sci_up(self.bmax_mu_p, 6), _sci_up(self.bmax_Rp, 6),
            _sci_up(R, 6), 1 if self.reserved_open else 0)
    # ---------------------------------------------------------------- the bounds of the observables (BRIDGE_ERRORS)
    # At the current time e = berr bounds |Z - z|_2, R = bR >= max(1, |Z|_2), the exact flow keeps |z|_2 = 1 <= R, and
    # q = 2^-P. A = conj(z0) z+ + conj(z-) z0 (A/N), B = conj(z-) z+, X = |z0|^2 f + 2 Re(conj(z+) conj(z-) z0^2) = |A|^2
    # for every triple (BRIDGE_TRAJ_V2_IDENTITY), C1 = 2N/(N-1) X, D2 = 2|B| = sqrt(D2sq). DERIVED:
    #   exact-solution parts (Cauchy-Schwarz on each bilinear form; |A| <= |z|^2/sqrt2, |B| <= |z|^2/2):
    #     |dA| <= (R+1) e <= 2 R e,  |dB| <= (R+1) e,  |dX| <= (|A(Z)| + |A(z)|) |dA| <= (R^2+1)(R+1) e,
    #     |dD2| <= 2(R+1) e,  |dD2sq| <= 4(|B(Z)| + |B(z)|) |dB| <= 2(R^2+1)(R+1) e,  |df| <= (R+1) e;
    #   rounding parts of obs() (each >> P floors: an error in [0, 1) units of q per component, at the integer state Z):
    #     f: 2q;  A: 2 sqrt2 q <= 3q;  |A|^2 (A2): 4 R^2 q + q + 8 q^2;  X: (2 + 2 sqrt2) R^2 q + 3q + 6q^2 <= 5 R^2 q + 3q + 6q^2;
    #     D2sq: 4 sqrt2 R^2 q + 4q + 8q^2 <= 6 R^2 q + 4q + 8q^2;  D2 = sqrt(D2sq): D2sq_round / sqrt(D2sq), or sqrt(D2sq_round)
    #     when sqrt(D2sq) rounds to 0 (|sqrt a - sqrt b| <= |a - b| / sqrt a and <= sqrt|a - b|).
    #   T_V2_ID reads V2 N/(N-1) = A2 / X; at Z, |A(Z)|^2 = X(Z) exactly, so |V2 N/(N-1) - 1| <= (A2_round + X_round) / X.
    def _obs_terms(self, N):
        """the observable bounds at the current time as exact rationals (the rows print them rounded up)"""
        self._bound_on()
        N = Fr(N)
        if not N > 1:
            raise SystemExit('REFUSED: N=%s; the observable bounds take N > 1' % N)
        e = self.berr; R = self.bR; q = Fr(1, ONE); R2 = R * R
        o = self.obs(N)
        t = {}
        t['f_err'] = e * (R + 1) + 2 * q
        t['A_err'] = 2 * R * e + 3 * q
        t['A1_err'] = 2 * t['A_err']
        t['X_exact'] = e * (R + 1) * (R2 + 1)
        t['X_round'] = 5 * R2 * q + 3 * q + 6 * q * q
        t['X_err'] = t['X_exact'] + t['X_round']
        t['C1_err'] = 2 * N / (N - 1) * t['X_err']
        t['A2_round'] = 4 * R2 * q + q + 8 * q * q
        t['D2sq_exact'] = 2 * (R2 + 1) * (R + 1) * e
        t['D2sq_round'] = 6 * R2 * q + 4 * q + 8 * q * q
        t['D2sq_err'] = t['D2sq_exact'] + t['D2sq_round']
        t['D2_exact'] = 2 * (R + 1) * e
        s = _sqrt_lo(o['D2sq'])
        t['D2_round'] = t['D2sq_round'] / s if s > 0 else _sqrt_up(t['D2sq_round'])
        t['D2_err'] = t['D2_exact'] + t['D2_round']
        t['V2_id_err'] = (t['A2_round'] + t['X_round']) / o['X'] if o['X'] > 0 else None
        return t, o
    def obs_bound_row(self, N):
        """the printed bounds of A1, C1, f, D2 and the V2 identity at the current time and N, beside obs(N)"""
        t, o = self._obs_terms(N)
        v2 = _sci_up(t['V2_id_err']) if t['V2_id_err'] is not None else 'undefined_X=0'
        return ('TRAJ_OBS_BOUND|delta=%s|y=%s|t=%s|N=%s|order=%d|h=1/%d|fixed_point=2^-%d|steps=%d|half_step=%d|'
                'state_err_2norm_le=%s|R_now_le=%s|f_err_le=%s|A_over_N_err_le=%s|A1_err_le=%s|C1_err_le=%s|X_err_le=%s|'
                'X_exact_part_le=%s|X_round_part_le=%s|D2_err_le=%s|D2_exact_part_le=%s|D2_round_part_le=%s|'
                'D2sq_err_le=%s|D2sq_exact_part_le=%s|D2sq_round_part_le=%s|A2_round_part_le=%s|V2_identity_err_le=%s|'
                'reserved_open=%d|method=exact_parts_from_e_and_R,rounding_parts_of_obs_at_2^-P,V2_identity_from_rounding_alone|'
                'float_used=0|json=0') % (
            self.delta, self.y, self.time(), Fr(N), self.K, self.hden, P, self.step_count, self.half_step,
            _sci_up(self.berr), _sci_up(self.bR, 6), _sci_up(t['f_err']), _sci_up(t['A_err']), _sci_up(t['A1_err']),
            _sci_up(t['C1_err']), _sci_up(t['X_err']), _sci_up(t['X_exact']), _sci_up(t['X_round']), _sci_up(t['D2_err']),
            _sci_up(t['D2_exact']), _sci_up(t['D2_round']), _sci_up(t['D2sq_err']), _sci_up(t['D2sq_exact']),
            _sci_up(t['D2sq_round']), _sci_up(t['A2_round']), v2, 1 if self.reserved_open else 0)
