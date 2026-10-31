//! Eisenstein integers a + b*omega, omega = e^{2 pi i / 3}, omega^2 = -1 - omega.
//! Every qutrit amplitude lives here; |a + b*omega|^2 = a^2 - a*b + b^2 is an integer.

use std::ops::{Add, AddAssign, Mul, Neg, Sub};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub struct E {
    pub a: i64,
    pub b: i64,
}

pub const ZERO: E = E { a: 0, b: 0 };
pub const ONE: E = E { a: 1, b: 0 };
pub const OMEGA: E = E { a: 0, b: 1 };

impl E {
    pub const fn new(a: i64, b: i64) -> Self {
        E { a, b }
    }
    /// |z|^2
    pub fn norm(self) -> i128 {
        let (a, b) = (i128::from(self.a), i128::from(self.b));
        a * a - a * b + b * b
    }
    /// z * omega
    pub fn times_omega(self) -> Self {
        E::new(-self.b, self.a - self.b)
    }
    /// z * omega^k, k taken mod 3
    pub fn times_omega_pow(self, k: i64) -> Self {
        match k.rem_euclid(3) {
            0 => self,
            1 => self.times_omega(),
            _ => self.times_omega().times_omega(),
        }
    }
    pub fn scale(self, s: i64) -> Self {
        E::new(self.a * s, self.b * s)
    }
}

impl Add for E {
    type Output = E;
    fn add(self, o: E) -> E {
        E::new(self.a + o.a, self.b + o.b)
    }
}
impl AddAssign for E {
    fn add_assign(&mut self, o: E) {
        self.a += o.a;
        self.b += o.b;
    }
}
impl Sub for E {
    type Output = E;
    fn sub(self, o: E) -> E {
        E::new(self.a - o.a, self.b - o.b)
    }
}
impl Neg for E {
    type Output = E;
    fn neg(self) -> E {
        E::new(-self.a, -self.b)
    }
}
impl Mul for E {
    type Output = E;
    /// (a + b w)(c + d w) = (ac - bd) + (ad + bc - bd) w
    fn mul(self, o: E) -> E {
        E::new(
            self.a * o.a - self.b * o.b,
            self.a * o.b + self.b * o.a - self.b * o.b,
        )
    }
}
