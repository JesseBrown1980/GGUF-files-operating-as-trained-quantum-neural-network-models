//! v7: the v6 layer, then a correlated dressing layer: SUM ring, rotations on every link,
//! inverse SUM ring. With its trits zero the second layer is exactly the identity.
//! As sealed in PREREG-V7.hbp. The circuit is written once against `Engine`, so the same
//! description runs on the big-integer state and on the residue pixel framebuffer.

use crate::bigint::Big;
use crate::v4::{cmp_q, StateR, Z3Orbits};
use crate::v5::PARTNERS;
use crate::v6::{b8, A6, TRITS_PER_B};
use crate::ym_z3::LINKS;

pub const TRITS_PER_LINK: usize = 2 * TRITS_PER_B;
pub const PER_LAYER: usize = TRITS_PER_LINK * LINKS;
pub const PARAMS: usize = 2 * PER_LAYER;

/// The two operations every v7 pass is made of.
pub trait Engine {
    fn rotate(&mut self, q: usize, i: usize, j: usize, b: i128, a: i128);
    fn sum(&mut self, c: usize, t: usize, s: i64);
}

impl Engine for StateR {
    fn rotate(&mut self, q: usize, i: usize, j: usize, b: i128, a: i128) {
        self.rotate_a(q, i, j, b, a);
    }
    fn sum(&mut self, c: usize, t: usize, s: i64) {
        StateR::sum(self, c, t, s);
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NetQ {
    pub params: Vec<i64>,
}

impl NetQ {
    fn bs(&self, l: usize, q: usize) -> (i128, i128) {
        let i = l * PER_LAYER + q * TRITS_PER_LINK;
        (
            b8(&self.params[i..i + TRITS_PER_B]),
            b8(&self.params[i + TRITS_PER_B..i + TRITS_PER_LINK]),
        )
    }
    fn rotations<E: Engine>(&self, l: usize, e: &mut E, sign: i128) {
        if sign > 0 {
            for q in 0..LINKS {
                let (b1, b2) = self.bs(l, q);
                e.rotate(q, 0, 1, b1, A6);
                e.rotate(q, 0, 2, b2, A6);
            }
        } else {
            for q in (0..LINKS).rev() {
                let (b1, b2) = self.bs(l, q);
                e.rotate(q, 0, 2, -b2, A6);
                e.rotate(q, 0, 1, -b1, A6);
            }
        }
    }
    fn ring<E: Engine>(e: &mut E, s: i64) {
        if s > 0 {
            for q in 0..LINKS {
                e.sum(q, (q + 1) % LINKS, 1);
            }
        } else {
            for q in (0..LINKS).rev() {
                e.sum(q, (q + 1) % LINKS, -1);
            }
        }
    }
    fn layer2_active(&self) -> bool {
        self.params[PER_LAYER..].iter().any(|&x| x != 0)
    }
    pub fn forward<E: Engine>(&self, e: &mut E) {
        self.rotations(0, e, 1);
        for &(c, t) in &PARTNERS {
            e.sum(c, t, 1);
        }
        if self.layer2_active() {
            Self::ring(e, 1);
            self.rotations(1, e, 1);
            Self::ring(e, -1);
        }
    }
    pub fn inverse<E: Engine>(&self, e: &mut E) {
        if self.layer2_active() {
            Self::ring(e, 1);
            self.rotations(1, e, -1);
            Self::ring(e, -1);
        }
        for &(c, t) in PARTNERS.iter().rev() {
            e.sum(c, t, -1);
        }
        self.rotations(0, e, -1);
    }
    pub fn energy(&self, orbits: &Z3Orbits, r: i64) -> Option<(Big, Big)> {
        let mut s = StateR::zero_state(LINKS);
        self.forward(&mut s);
        orbits.energy(&s, r)
    }
}

/// Coordinate descent over balanced trits, keeping strict decreases (as v4 to v6).
pub fn train(
    orbits: &Z3Orbits,
    seed: &[i64],
    r: i64,
    max_sweeps: usize,
) -> (Vec<i64>, (Big, Big), usize, usize) {
    let eval = |p: &[i64]| NetQ { params: p.to_vec() }.energy(orbits, r);
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
