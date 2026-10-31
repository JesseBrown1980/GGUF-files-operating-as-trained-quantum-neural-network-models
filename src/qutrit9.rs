//! The v2 exact simulator: amplitudes in Z[zeta_9], true state v / sqrt(3)^k.

use crate::cyclo::{add, norm, times_zeta_pow, ONE9, Z9, ZERO9};
use crate::real3::R3;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct State9 {
    pub n: usize,
    pub v: Vec<Z9>,
    pub k: u32,
}

fn stride(q: usize) -> usize {
    3usize.pow(q as u32)
}
fn digit(i: usize, q: usize) -> usize {
    (i / stride(q)) % 3
}

impl State9 {
    pub fn basis(n: usize, digits: &[usize]) -> Self {
        let mut v = vec![ZERO9; 3usize.pow(n as u32)];
        let idx: usize = digits.iter().enumerate().map(|(q, &d)| d * stride(q)).sum();
        v[idx] = ONE9;
        State9 { n, v, k: 0 }
    }
    pub fn norm_sum(&self) -> R3 {
        self.v.iter().fold(R3::int(0), |acc, z| acc.add(&norm(z)))
    }
    pub fn marginal(&self, q: usize) -> [R3; 3] {
        let mut p = [R3::int(0), R3::int(0), R3::int(0)];
        for (i, z) in self.v.iter().enumerate() {
            if *z != ZERO9 {
                let d = digit(i, q);
                p[d] = p[d].add(&norm(z));
            }
        }
        p
    }
    /// diag(1, zeta^e1, zeta^e2) on qutrit q (sign s = +1 or -1 for the inverse)
    pub fn phase9(&mut self, q: usize, e1: i64, e2: i64) {
        for (i, z) in self.v.iter_mut().enumerate() {
            match digit(i, q) {
                1 => *z = times_zeta_pow(z, e1),
                2 => *z = times_zeta_pow(z, e2),
                _ => {}
            }
        }
    }
    /// F (s = +1) or F^dagger (s = -1): |j> -> (1/sqrt 3) sum_m omega^(s j m) |m>; k += 1
    pub fn fourier(&mut self, q: usize, s: i64) {
        let st = stride(q);
        let mut out = vec![ZERO9; self.v.len()];
        for i in 0..self.v.len() {
            if digit(i, q) != 0 {
                continue;
            }
            let x = [self.v[i], self.v[i + st], self.v[i + 2 * st]];
            for m in 0..3usize {
                let mut acc = ZERO9;
                for (j, xj) in x.iter().enumerate() {
                    acc = add(&acc, &times_zeta_pow(xj, 3 * s * (j * m) as i64));
                }
                out[i + m * st] = acc;
            }
        }
        self.v = out;
        self.k += 1;
    }
    pub fn sum(&mut self, c: usize, t: usize, s: i64) {
        let st = stride(t);
        let mut out = vec![ZERO9; self.v.len()];
        for (i, &z) in self.v.iter().enumerate() {
            let dc = digit(i, c) as i64;
            let dt = digit(i, t);
            let nt = (dt as i64 + s * dc).rem_euclid(3) as usize;
            out[i - dt * st + nt * st] = z;
        }
        self.v = out;
    }
    pub fn equals_scaled(&self, other: &State9, e: u32) -> bool {
        let f = 3i64.pow(e);
        self.v.len() == other.v.len()
            && self
                .v
                .iter()
                .zip(other.v.iter())
                .all(|(a, b)| a.iter().zip(b.iter()).all(|(x, y)| *x == y * f))
    }
}

/// The v2 network: L layers of [F each, diag(1, zeta^e1, zeta^e2) each, SUM ring].
/// Four trits per qutrit per layer: e1 = 3*p[0] + p[1], e2 = 3*p[2] + p[3].
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Net9 {
    pub n: usize,
    pub layers: usize,
    pub params: Vec<i64>,
}

impl Net9 {
    pub fn param_count(n: usize, layers: usize) -> usize {
        4 * n * layers
    }
    fn exps(&self, l: usize, q: usize) -> (i64, i64) {
        let i = (l * self.n + q) * 4;
        let p = &self.params;
        (3 * p[i] + p[i + 1], 3 * p[i + 2] + p[i + 3])
    }
    pub fn forward(&self, s: &mut State9) {
        for l in 0..self.layers {
            for q in 0..self.n {
                s.fourier(q, 1);
            }
            for q in 0..self.n {
                let (e1, e2) = self.exps(l, q);
                s.phase9(q, e1, e2);
            }
            for q in 0..self.n {
                s.sum(q, (q + 1) % self.n, 1);
            }
        }
    }
    pub fn inverse(&self, s: &mut State9) {
        for l in (0..self.layers).rev() {
            for q in (0..self.n).rev() {
                s.sum(q, (q + 1) % self.n, -1);
            }
            for q in 0..self.n {
                let (e1, e2) = self.exps(l, q);
                s.phase9(q, -e1, -e2);
            }
            for q in 0..self.n {
                s.fourier(q, -1);
            }
        }
    }
}

/// The v3 Z3 network: L layers of [F, diag(1, zeta^e1, zeta^e2), F^dagger on every link,
/// then the SUM ring]. With every trit zero it is exactly the identity.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Net9S {
    pub n: usize,
    pub layers: usize,
    pub params: Vec<i64>,
}

impl Net9S {
    pub fn param_count(n: usize, layers: usize) -> usize {
        4 * n * layers
    }
    fn exps(&self, l: usize, q: usize) -> (i64, i64) {
        let i = (l * self.n + q) * 4;
        let p = &self.params;
        (3 * p[i] + p[i + 1], 3 * p[i + 2] + p[i + 3])
    }
    pub fn forward(&self, s: &mut State9) {
        for l in 0..self.layers {
            for q in 0..self.n {
                let (e1, e2) = self.exps(l, q);
                if e1 != 0 || e2 != 0 {
                    s.fourier(q, 1);
                    s.phase9(q, e1, e2);
                    s.fourier(q, -1);
                }
            }
            for q in 0..self.n {
                s.sum(q, (q + 1) % self.n, 1);
            }
        }
    }
    pub fn inverse(&self, s: &mut State9) {
        for l in (0..self.layers).rev() {
            for q in (0..self.n).rev() {
                s.sum(q, (q + 1) % self.n, -1);
            }
            for q in 0..self.n {
                let (e1, e2) = self.exps(l, q);
                if e1 != 0 || e2 != 0 {
                    s.fourier(q, 1);
                    s.phase9(q, -e1, -e2);
                    s.fourier(q, -1);
                }
            }
        }
    }
}
