//! Q(theta), theta = 2cos(2 pi / 9), the real cubic field: theta^3 = 3 theta - 1.
//! Elements c0 + c1 theta + c2 theta^2 with big-integer coefficients; exact sign by an
//! integer isolating interval for theta. Undecided signs are reported, never guessed.

use crate::bigint::Big;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct R3 {
    pub c: [Big; 3],
}

impl R3 {
    pub fn from_ints(c0: i128, c1: i128, c2: i128) -> Self {
        R3 {
            c: [Big::from_i128(c0), Big::from_i128(c1), Big::from_i128(c2)],
        }
    }
    pub fn int(n: i128) -> Self {
        R3::from_ints(n, 0, 0)
    }
    pub fn is_zero(&self) -> bool {
        self.c.iter().all(Big::is_zero)
    }
    pub fn add(&self, o: &R3) -> R3 {
        R3 {
            c: [
                self.c[0].add(&o.c[0]),
                self.c[1].add(&o.c[1]),
                self.c[2].add(&o.c[2]),
            ],
        }
    }
    pub fn sub(&self, o: &R3) -> R3 {
        R3 {
            c: [
                self.c[0].sub(&o.c[0]),
                self.c[1].sub(&o.c[1]),
                self.c[2].sub(&o.c[2]),
            ],
        }
    }
    pub fn scale(&self, k: i128) -> R3 {
        R3 {
            c: [
                self.c[0].mul_i128(k),
                self.c[1].mul_i128(k),
                self.c[2].mul_i128(k),
            ],
        }
    }
    /// product, reduced with theta^3 = 3 theta - 1 and theta^4 = 3 theta^2 - theta
    pub fn mul(&self, o: &R3) -> R3 {
        let mut d: Vec<Big> = vec![Big::zero(); 5];
        for i in 0..3 {
            for j in 0..3 {
                d[i + j] = d[i + j].add(&self.c[i].mul(&o.c[j]));
            }
        }
        // theta^4 = 3 theta^2 - theta
        let t4 = d[4].clone();
        d[2] = d[2].add(&t4.mul_i128(3));
        d[1] = d[1].sub(&t4);
        // theta^3 = 3 theta - 1
        let t3 = d[3].clone();
        d[1] = d[1].add(&t3.mul_i128(3));
        d[0] = d[0].sub(&t3);
        R3 {
            c: [d[0].clone(), d[1].clone(), d[2].clone()],
        }
    }
    /// 2^(2m) * value at x = n / 2^m
    fn at(&self, n: &Big, m: u32) -> Big {
        let s = Big::pow2(m);
        self.c[0]
            .mul(&s)
            .mul(&s)
            .add(&self.c[1].mul(n).mul(&s))
            .add(&self.c[2].mul(n).mul(n))
    }
    /// Exact sign: Some(-1|0|1), or None if not decided at the precisions tried.
    pub fn sign(&self) -> Option<i8> {
        if self.is_zero() {
            return Some(0);
        }
        for m in [64u32, 128, 256] {
            let (lo, hi) = theta_interval(m);
            let a = self.at(&lo, m).sign();
            let b = self.at(&hi, m).sign();
            if a != 0 && a == b && !vertex_inside(self, &lo, &hi, m) {
                return Some(a);
            }
        }
        None
    }
}

/// q(n / 2^m) * 2^(3m) for q(x) = x^3 - 3x + 1
fn q_at(n: &Big, m: u32) -> Big {
    let s = Big::pow2(m);
    n.mul(n)
        .mul(n)
        .sub(&n.mul(&s).mul(&s).mul_i128(3))
        .add(&s.mul(&s).mul(&s))
}

/// [lo, hi] = [n, n + 1] / 2^m containing theta, the root of x^3 - 3x + 1 in [1.5, 1.875]
/// (q(1.5) < 0 < q(1.875), and q is increasing there).
pub fn theta_interval(m: u32) -> (Big, Big) {
    let mut lo = Big::pow2(m - 1).mul_i128(3); // 1.5 * 2^m
    let mut hi = Big::pow2(m - 3).mul_i128(15); // 1.875 * 2^m
    assert!(q_at(&lo, m).sign() < 0 && q_at(&hi, m).sign() > 0);
    let one = Big::from_i128(1);
    while hi.sub(&lo) != one {
        let mid = lo.add(&hi).half();
        if q_at(&mid, m).sign() < 0 {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    (lo, hi)
}

/// true if the vertex -c1 / (2 c2) of the quadratic lies within [lo, hi] / 2^m
fn vertex_inside(r: &R3, lo: &Big, hi: &Big, m: u32) -> bool {
    if r.c[2].is_zero() {
        return false;
    }
    // vertex x* = -c1 / (2 c2); inside iff lo <= x* * 2^m <= hi, i.e. compare -c1 * 2^m with 2 c2 * lo, 2 c2 * hi
    let num = r.c[1].neg().mul(&Big::pow2(m));
    let two_c2 = r.c[2].mul_i128(2);
    let a = num.sub(&two_c2.mul(lo));
    let b = num.sub(&two_c2.mul(hi));
    // inside iff (num - 2c2 lo) and (num - 2c2 hi) have opposite signs or one is zero, scaled by sign(c2)
    a.sign() == 0 || b.sign() == 0 || a.sign() != b.sign()
}
