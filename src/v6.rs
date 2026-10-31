//! v6: the v5 network on a 9x finer angle grid, a = 6561, eight trits per angle.
//! As sealed in PREREG-V6.hbp.

use crate::bigint::Big;
use crate::v4::{cmp_q, StateR, Z3Orbits};
use crate::v5::PARTNERS;
use crate::ym_z3::LINKS;

pub const A6: i128 = 6561;
pub const TRITS_PER_B: usize = 8;
pub const TRITS_PER_LINK: usize = 2 * TRITS_PER_B;

/// b = 2187 p0 + 729 p1 + ... + p7 from eight balanced trits
pub fn b8(p: &[i64]) -> i128 {
    i128::from(p.iter().take(TRITS_PER_B).fold(0i64, |acc, &x| acc * 3 + x))
}

/// balanced ternary of b in eight trits, most significant first
pub fn trits8(b: i64) -> [i64; TRITS_PER_B] {
    let mut out = [0i64; TRITS_PER_B];
    let mut x = b;
    for t in out.iter_mut().rev() {
        let r = x.rem_euclid(3);
        let d = if r == 2 { -1 } else { r };
        *t = d;
        x = (x - d) / 3;
    }
    assert_eq!(x, 0, "b out of range");
    out
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NetP6 {
    pub layers: usize,
    pub params: Vec<i64>,
}

impl NetP6 {
    pub fn param_count(layers: usize) -> usize {
        TRITS_PER_LINK * LINKS * layers
    }
    fn bs(&self, l: usize, q: usize) -> (i128, i128) {
        let i = (l * LINKS + q) * TRITS_PER_LINK;
        (
            b8(&self.params[i..i + TRITS_PER_B]),
            b8(&self.params[i + TRITS_PER_B..i + TRITS_PER_LINK]),
        )
    }
    pub fn forward(&self, s: &mut StateR) {
        for l in 0..self.layers {
            for q in 0..LINKS {
                let (b1, b2) = self.bs(l, q);
                s.rotate_a(q, 0, 1, b1, A6);
                s.rotate_a(q, 0, 2, b2, A6);
            }
            for &(c, t) in &PARTNERS {
                s.sum(c, t, 1);
            }
        }
    }
    pub fn inverse(&self, s: &mut StateR) {
        for l in (0..self.layers).rev() {
            for &(c, t) in PARTNERS.iter().rev() {
                s.sum(c, t, -1);
            }
            for q in (0..LINKS).rev() {
                let (b1, b2) = self.bs(l, q);
                s.rotate_a(q, 0, 2, -b2, A6);
                s.rotate_a(q, 0, 1, -b1, A6);
            }
        }
    }
    pub fn energy(&self, orbits: &Z3Orbits, r: i64) -> Option<(Big, Big)> {
        let mut s = StateR::zero_state(LINKS);
        self.forward(&mut s);
        orbits.energy(&s, r)
    }
}

/// Coordinate descent over balanced trits, keeping strict decreases (as v4 and v5).
pub fn train(
    orbits: &Z3Orbits,
    seed: &[i64],
    layers: usize,
    r: i64,
    max_sweeps: usize,
) -> (Vec<i64>, (Big, Big), usize, usize) {
    let eval = |p: &[i64]| {
        NetP6 {
            layers,
            params: p.to_vec(),
        }
        .energy(orbits, r)
    };
    let mut params = seed.to_vec();
    let mut best = eval(&params).expect("seed has a physical component");
    let mut evals = 1usize;
    let mut sweeps = 0usize;
    for _ in 0..max_sweeps {
        sweeps += 1;
        let mut changed = false;
        for i in 0..params.len() {
            let keep = params[i];
            let mut best_v = keep;
            for v in -1..=1 {
                if v == keep {
                    continue;
                }
                params[i] = v;
                evals += 1;
                if let Some(e) = eval(&params) {
                    if cmp_q(&e, &best) < 0 {
                        best = e;
                        best_v = v;
                    }
                }
            }
            params[i] = best_v;
            changed |= best_v != keep;
        }
        if !changed {
            break;
        }
    }
    (params, best, evals, sweeps)
}
