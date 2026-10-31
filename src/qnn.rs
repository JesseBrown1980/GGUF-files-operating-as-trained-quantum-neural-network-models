//! The qutrit network: L layers of [F on every qutrit, diag(1, w^a, w^b) on every
//! qutrit, SUM ring q -> q+1]. Its parameters are trits, two per qutrit per layer.

use crate::qutrit::State;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Net {
    pub n: usize,
    pub layers: usize,
    /// a_{l,q}, b_{l,q} laid out as [(l * n + q) * 2], [(l * n + q) * 2 + 1], each in {0,1,2}
    pub params: Vec<i64>,
}

impl Net {
    pub fn param_count(n: usize, layers: usize) -> usize {
        2 * n * layers
    }
    pub fn forward(&self, s: &mut State) {
        for l in 0..self.layers {
            for q in 0..self.n {
                s.fourier(q, 1);
            }
            for q in 0..self.n {
                let i = (l * self.n + q) * 2;
                s.phase(q, self.params[i], self.params[i + 1]);
            }
            for q in 0..self.n {
                s.sum(q, (q + 1) % self.n, 1);
            }
        }
    }
    /// The exact inverse: undoes `forward` (the scale grows by one per F^dagger).
    pub fn inverse(&self, s: &mut State) {
        for l in (0..self.layers).rev() {
            for q in (0..self.n).rev() {
                s.sum(q, (q + 1) % self.n, -1);
            }
            for q in 0..self.n {
                let i = (l * self.n + q) * 2;
                s.phase(q, -self.params[i], -self.params[i + 1]);
            }
            for q in 0..self.n {
                s.fourier(q, -1);
            }
        }
    }
}
