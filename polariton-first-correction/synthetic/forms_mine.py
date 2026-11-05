# forms_mine.py: the law and first correction, typed by hand from F5 in
# polariton/second-seat/recheck-ce44be7/contact/FINDINGS.txt, exact rationals, sharing no code with
# read_first_correction.py: no parser, no walk, no series of the reader.
#
# c_k and gs_k are built from c_1 and s_1 alone by the Chebyshev identities
#   cosh((k+1)x) = 2 cosh(x) cosh(kx) - cosh((k-1)x)
#   sinh((k+1)x) = 2 cosh(x) sinh(kx) - sinh((k-1)x)
# where x = gamma t. gamma is irrational, so sinh enters as gt_sinh(k) = gamma t sinh(k gamma t), a value in Q(x^2).
# Everything is a Fraction. Evaluating closed forms runs no model.
from fractions import Fraction as Fr


def series_cosh_gts(g2, terms):
    """cosh(x) and x sinh(x) from their series in x^2 = g2, to a stated length, with a rigorous tail bound returned."""
    c = Fr(0)
    xs = Fr(0)
    term = Fr(1)  # x^(2m)/(2m)!
    for m in range(terms):
        c += term
        # x sinh x = Sum x^(2m+2)/(2m+1)!
        xs += term * g2 / (2 * m + 1)
        term = term * g2 / ((2 * m + 1) * (2 * m + 2))
    # Past the peak the terms fall at least by half; twice the next term covers the rest.
    tail = 2 * abs(term) * (1 + abs(g2))
    return c, xs, tail


class Point:
    def __init__(self, n, d, y, t, terms=200):
        n, d, y, t = Fr(n), Fr(d), Fr(y), Fr(t)
        self.n, self.d, self.y, self.t = n, d, y, t
        self.s2 = n * y * y
        self.s4 = self.s2 * self.s2
        g2 = (1 - d * d) * t * t
        self.g2 = g2
        c1, x_s1, tail = series_cosh_gts(g2, terms)
        self.tail = tail
        # c[k] = cosh(k x), xs[k] = x sinh(k x), k = 0..4.
        c = [Fr(1), c1]
        xs = [Fr(0), x_s1]
        for k in range(1, 4):
            c.append(2 * c1 * c[k] - c[k - 1])
            xs.append(2 * c1 * xs[k] - xs[k - 1])
        self.c = c
        self.xs = xs

    def forms(self):
        d = self.d
        c, gs = self.c, self.xs
        c1, c2, c3, c4 = c[1], c[2], c[3], c[4]
        gs1, gs2 = gs[1], gs[2]
        D3 = (1 + d) ** 3 * (1 - d) ** 2
        D4 = (1 + d) ** 4 * (1 - d) ** 2
        D5 = (1 + d) ** 5 * (1 - d) ** 2
        # sinh^2(x) = (cosh(2x) - 1)/2
        sinh2 = (c2 - 1) / 2
        w0 = -2 * (c1 - 1) / (1 + d)
        C0 = 4 * sinh2 / (1 + d) + 8 * self.s2 * (c1 - 1) ** 2 / (1 + d) ** 2
        # F5, typed line by line.
        w10 = ((Fr(65, 12) - Fr(85, 6) * d + 12 * d ** 2 - 4 * d ** 3) * c1
               + (Fr(5, 4) - d / 2) * c3
               + (d - Fr(11, 3)) * (1 - d) * c2
               + (4 * d - 3) * (1 - d) ** 2
               + (2 * d ** 3 - 4 * d ** 2 - 1) * gs1) / D3
        w11 = ((Fr(-53, 4) + Fr(81, 2) * d - 44 * d ** 2 + 16 * d ** 3) * c1
               + (Fr(5, 4) - d / 2) * c3
               + (6 * d - 8) * (1 - d) * c2
               + (20 - 34 * d + 16 * d ** 2) * (1 - d)
               + (17 - 46 * d + 34 * d ** 2 - 8 * d ** 3) * gs1) / D4
        C10 = ((d - Fr(5, 2)) * c4
               + (3 + 10 * d - 7 * d ** 2) * (1 - d) * c2
               + (Fr(-1, 2) - 8 * d + 17 * d ** 2 - 7 * d ** 3)
               + (6 - 12 * d + 18 * d ** 2 - 6 * d ** 3) * gs2) / D3
        C11 = ((4 * d - 10) * c4
               + (42 - 60 * d + 24 * d ** 2) * c3
               + (-40 + Fr(140, 3) * d - 16 * d ** 2) * (1 - d) * c2
               + (22 - Fr(428, 3) * d + Fr(632, 3) * d ** 2 - 96 * d ** 3) * c1
               + (-14 + 112 * d - 172 * d ** 2 + 80 * d ** 3)
               + (-8 - 32 * d ** 2 + 16 * d ** 3) * gs1
               + (-16 + 68 * d - 28 * d ** 2) * gs2) / D4
        C12 = ((2 * d - 5) * c4
               + (42 - 60 * d + 24 * d ** 2) * c3
               + (-16 - 64 * d + 64 * d ** 2) * (1 - d) * c2
               + (-234 + 700 * d - 728 * d ** 2 + 256 * d ** 3) * c1
               + (213 - 594 * d + 576 * d ** 2 - 192 * d ** 3)
               + (136 - 368 * d + 272 * d ** 2 - 64 * d ** 3) * gs1
               + (-68 + 184 * d - 136 * d ** 2 + 32 * d ** 3) * gs2) / D5
        n, y = self.n, self.y
        ay = abs(y)
        A1_law = 2 * ay * abs(w0)
        A1_first = 2 * ay * abs(w0 + (w10 + self.s2 * w11) / n)
        C1_law = C0 / n
        C1_first = C0 / n + (C10 + self.s2 * C11 + self.s4 * C12) / (n * n)
        V2_first = A1_first ** 2 / (2 * C1_first)
        # Line 39 of the prediction: J0 = sinh^2/gamma^2, n_coh = 2 N y^2 [(c_1 - 1)^2/(1+d)^2 + J0], f = (2 J0 + n_coh)/N.
        j0 = sinh2 / (1 - d * d)
        n_coh = 2 * self.s2 * ((c1 - 1) ** 2 / (1 + d) ** 2 + j0)
        f = (2 * j0 + n_coh) / n
        return dict(w0=w0, C0=C0, w10=w10, w11=w11, C10=C10, C11=C11, C12=C12,
                    A1_law=A1_law, A1_first=A1_first, C1_law=C1_law, C1_first=C1_first, V2_first=V2_first, f=f)

    def delta0_forms(self):
        """F5's own delta = 0 lines, as a second typing. Valid at d = 0. t must be such that sinh t comes from gs_1/t."""
        assert self.d == 0
        t = self.t
        c = self.c
        # At d = 0, x = t, so xs[k] = t sinh(k t).
        t_sinh_t, t_sinh_2t = self.xs[1], self.xs[2]
        w10 = -t_sinh_t + Fr(65, 12) * c[1] - Fr(11, 3) * c[2] + Fr(5, 4) * c[3] - 3
        w11 = 17 * t_sinh_t - Fr(53, 4) * c[1] - 8 * c[2] + Fr(5, 4) * c[3] + 20
        C10 = 6 * t_sinh_2t - Fr(5, 2) * c[4] + 3 * c[2] - Fr(1, 2)
        C11 = -8 * t_sinh_t - 16 * t_sinh_2t - 10 * c[4] + 42 * c[3] - 40 * c[2] + 22 * c[1] - 14
        C12 = 136 * t_sinh_t - 68 * t_sinh_2t - 5 * c[4] + 42 * c[3] - 16 * c[2] - 234 * c[1] + 213
        return dict(w10=w10, w11=w11, C10=C10, C11=C11, C12=C12)


def e_fixed(value, digits=12):
    """Fixed-point text of a Fraction, integers only."""
    sign = "-" if value < 0 else ""
    v = abs(value)
    whole = v.__floor__()
    frac = ((v - whole) * 10 ** digits).__floor__()
    return "%s%d.%0*d" % (sign, whole, digits, frac)
