//! v5: the v4 rotations with six-trit angles, then partner SUMs that carry no flux.
//! As sealed in PREREG-V5.hbp.

use crate::bigint::Big;
use crate::v4::{cmp_q, StateR, Z3Orbits};
use crate::ym_z3::LINKS;

pub const TRITS_PER_B: usize = 6;
pub const TRITS_PER_LINK: usize = 2 * TRITS_PER_B;
/// (control, target): the two x-links of one column, the two y-links of one row
pub const PARTNERS: [(usize, usize); 4] = [(0, 4), (2, 6), (1, 3), (5, 7)];

/// b = 243 p0 + 81 p1 + 27 p2 + 9 p3 + 3 p4 + p5 from six balanced trits
pub fn b6(p: &[i64]) -> i128 {
    i128::from(p.iter().take(TRITS_PER_B).fold(0i64, |acc, &x| acc * 3 + x))
}

/// balanced ternary of b in six trits, most significant first
pub fn trits6(b: i64) -> [i64; TRITS_PER_B] {
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
pub struct NetP {
    pub layers: usize,
    pub params: Vec<i64>,
}

impl NetP {
    pub fn param_count(layers: usize) -> usize {
        TRITS_PER_LINK * LINKS * layers
    }
    fn bs(&self, l: usize, q: usize) -> (i128, i128) {
        let i = (l * LINKS + q) * TRITS_PER_LINK;
        (
            b6(&self.params[i..i + TRITS_PER_B]),
            b6(&self.params[i + TRITS_PER_B..i + TRITS_PER_LINK]),
        )
    }
    pub fn forward(&self, s: &mut StateR) {
        for l in 0..self.layers {
            for q in 0..LINKS {
                let (b1, b2) = self.bs(l, q);
                s.rotate(q, 0, 1, b1);
                s.rotate(q, 0, 2, b2);
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
                s.rotate(q, 0, 2, -b2);
                s.rotate(q, 0, 1, -b1);
            }
        }
    }
    pub fn energy(&self, orbits: &Z3Orbits, r: i64) -> Option<(Big, Big)> {
        let mut s = StateR::zero_state(LINKS);
        self.forward(&mut s);
        orbits.energy(&s, r)
    }
}

/// Coordinate descent over balanced trits, keeping strict decreases (as v4).
pub fn train(
    orbits: &Z3Orbits,
    seed: &[i64],
    layers: usize,
    r: i64,
    max_sweeps: usize,
) -> (Vec<i64>, (Big, Big), usize, usize) {
    let eval = |p: &[i64]| {
        NetP {
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
