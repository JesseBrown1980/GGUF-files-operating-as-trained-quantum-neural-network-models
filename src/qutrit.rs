//! Exact state-vector simulator for n qutrits. The true state is v / sqrt(3)^k, with v a
//! vector of Eisenstein integers and k counted. Every probability is an exact fraction
//! (sum of |v_j|^2) / 3^k.

use crate::eisenstein::{E, ONE, ZERO};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct State {
    pub n: usize,
    pub v: Vec<E>,
    pub k: u32,
}

pub fn pow3(e: u32) -> i128 {
    3i128.pow(e)
}

impl State {
    /// |d_0 d_1 ... d_{n-1}>, qutrit q holding digit d_q.
    pub fn basis(n: usize, digits: &[usize]) -> Self {
        let mut v = vec![ZERO; 3usize.pow(n as u32)];
        let idx: usize = digits
            .iter()
            .enumerate()
            .map(|(q, &d)| d * 3usize.pow(q as u32))
            .sum();
        v[idx] = ONE;
        State { n, v, k: 0 }
    }
    fn stride(q: usize) -> usize {
        3usize.pow(q as u32)
    }
    fn digit(i: usize, q: usize) -> usize {
        (i / Self::stride(q)) % 3
    }
    /// sum |v_j|^2; equals 3^k for every unitary circuit.
    pub fn norm_sum(&self) -> i128 {
        self.v.iter().map(|z| z.norm()).sum()
    }
    /// Numerators of P(qutrit q = 0, 1, 2); the denominator is 3^k.
    pub fn marginal(&self, q: usize) -> [i128; 3] {
        let mut p = [0i128; 3];
        for (i, z) in self.v.iter().enumerate() {
            p[Self::digit(i, q)] += z.norm();
        }
        p
    }
    /// Cyclic shift X^s: |j> -> |j + s>.
    pub fn shift(&mut self, q: usize, s: usize) {
        let s = s % 3;
        if s == 0 {
            return;
        }
        let st = Self::stride(q);
        let mut out = vec![ZERO; self.v.len()];
        for (i, &z) in self.v.iter().enumerate() {
            let d = Self::digit(i, q);
            out[i - d * st + ((d + s) % 3) * st] = z;
        }
        self.v = out;
    }
    /// diag(1, w^a, w^b) on qutrit q (a, b are the trainable trits; Z = phase(1, 2)).
    pub fn phase(&mut self, q: usize, a: i64, b: i64) {
        for (i, z) in self.v.iter_mut().enumerate() {
            match Self::digit(i, q) {
                1 => *z = z.times_omega_pow(a),
                2 => *z = z.times_omega_pow(b),
                _ => {}
            }
        }
    }
    /// Fourier F: |j> -> (1/sqrt 3) sum_m w^{s j m} |m>, s = +1 (F) or -1 (F^dagger). k += 1.
    pub fn fourier(&mut self, q: usize, s: i64) {
        let st = Self::stride(q);
        let mut out = vec![ZERO; self.v.len()];
        for i in 0..self.v.len() {
            if Self::digit(i, q) != 0 {
                continue;
            }
            let x = [self.v[i], self.v[i + st], self.v[i + 2 * st]];
            for m in 0..3usize {
                let mut acc = ZERO;
                for (j, &xj) in x.iter().enumerate() {
                    acc += xj.times_omega_pow(s * (j * m) as i64);
                }
                out[i + m * st] = acc;
            }
        }
        self.v = out;
        self.k += 1;
    }
    /// SUM: |c, t> -> |c, t + s*c>, s = +1 or -1 (its inverse).
    pub fn sum(&mut self, c: usize, t: usize, s: i64) {
        let st = Self::stride(t);
        let mut out = vec![ZERO; self.v.len()];
        for (i, &z) in self.v.iter().enumerate() {
            let dc = Self::digit(i, c) as i64;
            let dt = Self::digit(i, t);
            let nt = (dt as i64 + s * dc).rem_euclid(3) as usize;
            out[i - dt * st + nt * st] = z;
        }
        self.v = out;
    }
    /// true if self = 3^(e) * other as vectors (same state up to the counted scale).
    pub fn equals_scaled(&self, other: &State, e: u32) -> bool {
        let f = 3i64.pow(e);
        self.v.len() == other.v.len()
            && self
                .v
                .iter()
                .zip(other.v.iter())
                .all(|(a, b)| *a == b.scale(f))
    }
}
