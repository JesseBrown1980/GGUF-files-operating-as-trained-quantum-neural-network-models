//! Rules SECTOR and ATOMS of PREDICTION-STRIPE-PHASE.hbp, by integer sign and comparison tests only.

/// sigma(X, Y) in 0..16 (rule SECTOR): quadrant 0 if Y>=0, X>0; 1 if X<=0, Y>0; 2 if Y<=0, X<0; 3 if X>=0, Y<0;
/// rotated to (a, b), a>0, b>=0; sub 0 if (a+b)^2<2a^2, 1 if b<a, 2 if (a+b)^2>2b^2, else 3. None at (0, 0).
/// The caller keeps |X|, |Y| below 2^63.
pub fn sigma(x: i128, y: i128) -> Option<u8> {
    let (q, a, b) = if y >= 0 && x > 0 {
        (0u8, x, y)
    } else if x <= 0 && y > 0 {
        (1, y, -x)
    } else if y <= 0 && x < 0 {
        (2, -x, -y)
    } else if x >= 0 && y < 0 {
        (3, -y, x)
    } else {
        return None;
    };
    let (a, b) = (a.unsigned_abs(), b.unsigned_abs());
    let s2 = (a + b) * (a + b);
    let sub = if s2 < 2 * a * a {
        0
    } else if b < a {
        1
    } else if s2 > 2 * b * b {
        2
    } else {
        3
    };
    Some(4 * q + sub)
}

/// On an axis or a diagonal (the integer-reachable sector edges).
pub fn on_edge(x: i128, y: i128) -> bool {
    x == 0 || y == 0 || x.unsigned_abs() == y.unsigned_abs()
}

const LIMIT: u128 = 1u128 << 63;

/// The certified sigma of B = (br, bi) with bounds (b_br, b_bi): the four corners share sigma and none lies on an axis
/// or a diagonal. None is ambiguous (also when a corner leaves |.| < 2^63, where the box is not resolved).
pub fn certify(br: i64, bi: i64, bbr: u128, bbi: u128) -> Option<u8> {
    if bbr >= LIMIT || bbi >= LIMIT {
        return None;
    }
    let (dr, di) = (bbr as i128, bbi as i128);
    let (r, i) = (i128::from(br), i128::from(bi));
    let mut common: Option<u8> = None;
    for (x, y) in [
        (r - dr, i - di),
        (r - dr, i + di),
        (r + dr, i - di),
        (r + dr, i + di),
    ] {
        if x.unsigned_abs() >= LIMIT || y.unsigned_abs() >= LIMIT || on_edge(x, y) {
            return None;
        }
        let s = sigma(x, y)?;
        match common {
            None => common = Some(s),
            Some(c) if c != s => return None,
            Some(_) => {}
        }
    }
    common
}

/// A certified sign: Pos or Neg when |v| > b, else Amb.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Sign {
    Pos,
    Neg,
    Amb,
}

impl Sign {
    pub fn of(v: i64, b: u128) -> Sign {
        if u128::from(v.unsigned_abs()) > b {
            if v > 0 {
                Sign::Pos
            } else {
                Sign::Neg
            }
        } else {
            Sign::Amb
        }
    }
    pub fn index(self) -> usize {
        match self {
            Sign::Pos => 0,
            Sign::Neg => 1,
            Sign::Amb => 2,
        }
    }
}

/// The atom flags of one sample (rule ATOMS) from its integer noise values c_i = g_i / 2^35.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Atoms {
    /// non-LOCK Klein atom: (c0, c1) = R^k (c2, c3), k = 0..3, R(a, b) = (-b, a)
    pub nl_klein: bool,
    /// non-LOCK exchange atom: c0 = c2 and c1 = c3
    pub nl_exch: bool,
    /// LOCK Klein atom: c0 c1 (c0^2 - c1^2) = 0
    pub lk_klein: bool,
    /// LOCK exchange atom: c1 = 0
    pub lk_exch: bool,
}

impl Atoms {
    pub fn of(c: [i64; 4]) -> Atoms {
        let [c0, c1, c2, c3] = c;
        let nl_exch = c0 == c2 && c1 == c3;
        Atoms {
            nl_klein: nl_exch
                || (c0 == -c3 && c1 == c2)
                || (c0 == -c2 && c1 == -c3)
                || (c0 == c3 && c1 == -c2),
            nl_exch,
            lk_klein: c0 == 0 || c1 == 0 || c0 == c1 || c0 == -c1,
            lk_exch: c1 == 0,
        }
    }

    /// The atom set rule ATOMS leaves out of the sector and sign tests: Klein atoms at y = 0, exchange atoms at y != 0.
    pub fn atom(self, lock: bool, y_zero: bool) -> bool {
        match (lock, y_zero) {
            (false, true) => self.nl_klein,
            (false, false) => self.nl_exch,
            (true, true) => self.lk_klein,
            (true, false) => self.lk_exch,
        }
    }

    /// Exchange atoms (psi+ = psi- bit-exactly), at every y.
    pub fn exch(self, lock: bool) -> bool {
        if lock {
            self.lk_exch
        } else {
            self.nl_exch
        }
    }

    /// The side-file flag word: bit 0 nl_klein, 1 nl_exch, 2 lk_klein, 3 lk_exch.
    pub fn bits(self) -> u64 {
        u64::from(self.nl_klein)
            | u64::from(self.nl_exch) << 1
            | u64::from(self.lk_klein) << 2
            | u64::from(self.lk_exch) << 3
    }
}

/// sigma of LOCK's start lattice point c^2 = (c0^2 - c1^2, 2 c0 c1).
pub fn lattice_sigma(c0: i64, c1: i64) -> Option<u8> {
    let (a, b) = (i128::from(c0), i128::from(c1));
    sigma(a * a - b * b, 2 * a * b)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// sign(p + q sqrt 2) for integers.
    fn sgn_q2(p: i128, q: i128) -> i32 {
        let sp = p.signum() as i32;
        let sq = q.signum() as i32;
        if sp == sq || sq == 0 {
            return sp;
        }
        if sp == 0 {
            return sq;
        }
        let lhs = p * p;
        let rhs = 2 * q * q;
        if lhs > rhs {
            sp
        } else {
            sq
        }
    }

    /// An independent sector: the quadrant by the half-open rule, then count the rays k pi/8 (k = 1, 2, 3) at or below
    /// the angle of (a, b): b >= tan(k pi/8) a with tan = sqrt2 - 1, 1, sqrt2 + 1.
    fn oracle(x: i128, y: i128) -> Option<u8> {
        let (q, a, b) = if y >= 0 && x > 0 {
            (0, x, y)
        } else if x <= 0 && y > 0 {
            (1, y, -x)
        } else if y <= 0 && x < 0 {
            (2, -x, -y)
        } else if x >= 0 && y < 0 {
            (3, -y, x)
        } else {
            return None;
        };
        let mut sub = 0;
        if sgn_q2(b + a, -a) >= 0 {
            sub += 1;
        }
        if b >= a {
            sub += 1;
        }
        if sgn_q2(b - a, -a) >= 0 {
            sub += 1;
        }
        Some(4 * q + sub)
    }

    #[test]
    fn sigma_agrees_with_the_sqrt2_oracle_on_a_grid() {
        for x in -60i128..=60 {
            for y in -60i128..=60 {
                assert_eq!(sigma(x, y), oracle(x, y), "({x},{y})");
            }
        }
        for &(x, y) in &[
            (1i128 << 61, 3),
            (12345678901, -98765432109),
            (-(1i128 << 62), 1),
        ] {
            assert_eq!(sigma(x, y), oracle(x, y));
        }
    }

    #[test]
    fn sigma_known_points_and_symmetries() {
        assert_eq!(sigma(1, 0), Some(0));
        assert_eq!(sigma(10, 3), Some(0));
        assert_eq!(sigma(10, 5), Some(1));
        assert_eq!(sigma(10, 10), Some(2));
        assert_eq!(sigma(3, 10), Some(3));
        assert_eq!(sigma(0, 10), Some(4));
        assert_eq!(sigma(-10, 0), Some(8));
        assert_eq!(sigma(0, -1), Some(12));
        assert_eq!(sigma(0, 0), None);
        for x in -30i128..=30 {
            for y in -30i128..=30 {
                if x == 0 && y == 0 {
                    continue;
                }
                let s = sigma(x, y).unwrap_or(99);
                assert_eq!(sigma(-y, x), Some((s + 4) % 16));
                assert_eq!(sigma(-x, -y), Some((s + 8) % 16));
                if !on_edge(x, y) {
                    assert_eq!(sigma(x, -y), Some(15 - s));
                }
            }
        }
    }

    #[test]
    fn certification_needs_the_whole_box_inside_one_open_sector() {
        assert_eq!(certify(1000, 100, 10, 10), Some(0));
        assert_eq!(certify(1000, 5, 10, 10), None);
        assert_eq!(certify(1000, 1000, 1, 1), None);
        assert_eq!(certify(1000, 420, 0, 0), Some(1));
        assert_eq!(certify(1000, 414, 0, 0), Some(0));
        assert_eq!(certify(1000, 414, 0, 1), None);
        assert_eq!(certify(7, 7, 0, 0), None);
        assert_eq!(certify(0, 7, 0, 0), None);
        assert_eq!(certify(5, 3, 0, 0), Some(1));
        assert_eq!(certify(5, -3, 0, 0), Some(14));
        assert_eq!(certify(i64::MAX, 0, 1 << 62, 0), None);
    }

    #[test]
    fn certified_signs() {
        assert_eq!(Sign::of(5, 4), Sign::Pos);
        assert_eq!(Sign::of(-5, 4), Sign::Neg);
        assert_eq!(Sign::of(5, 5), Sign::Amb);
        assert_eq!(Sign::of(0, 0), Sign::Amb);
        assert_eq!(Sign::of(i64::MIN, 0), Sign::Neg);
    }

    #[test]
    fn atoms_by_rule() {
        let a = Atoms::of([3, -2, 3, -2]);
        assert!(a.nl_exch && a.nl_klein && !a.lk_klein && !a.lk_exch);
        let a = Atoms::of([2, 3, 3, -2]);
        assert!(!a.nl_exch && a.nl_klein);
        let a = Atoms::of([-3, 2, 3, -2]);
        assert!(a.nl_klein && !a.nl_exch);
        let a = Atoms::of([2, -3, 3, 2]);
        assert!(a.nl_klein);
        let a = Atoms::of([2, 3, 2, -3]);
        assert!(!a.nl_klein);
        let a = Atoms::of([4, 0, 1, 1]);
        assert!(a.lk_exch && a.lk_klein && !a.nl_klein);
        let a = Atoms::of([0, 5, 1, 2]);
        assert!(a.lk_klein && !a.lk_exch);
        let a = Atoms::of([-5, 5, 1, 2]);
        assert!(a.lk_klein && !a.lk_exch);
        assert!(a.atom(true, true) && !a.atom(true, false));
        let a = Atoms::of([0, 0, 0, 0]);
        assert_eq!(a.bits(), 15);
    }

    #[test]
    fn lattice_points_off_the_atoms_are_never_on_an_edge() {
        for c0 in -40i64..=40 {
            for c1 in -40i64..=40 {
                let (a, b) = (i128::from(c0), i128::from(c1));
                let edge = on_edge(a * a - b * b, 2 * a * b);
                assert_eq!(edge, Atoms::of([c0, c1, 0, 0]).lk_klein, "({c0},{c1})");
            }
        }
        assert_eq!(lattice_sigma(3, 1), sigma(8, 6));
    }
}
