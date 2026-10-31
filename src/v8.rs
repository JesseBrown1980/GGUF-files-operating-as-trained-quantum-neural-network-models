//! v8: the v7 network carried to the 3 x 2 torus, as sealed in PREREG-V8.hbp. Layer 1: R_01(b), R_02(b')
//! on every link, then the cut SUMs (x: row-0 x-link to row-1 x-link in every column; y: column-0 y-link
//! to the column-1 and column-2 y-links in every row). Layer 2: SUM ring, R_01, R_02 on every link,
//! inverse ring. Training ranks candidates with the fixed-point state; reported energies are exact.

use crate::torus::{StateF, Torus};
use crate::v6::{b8, A6, TRITS_PER_B};
use crate::v7::Engine;

pub const LX: usize = 3;
pub const LY: usize = 2;
pub const LINKS: usize = 2 * LX * LY;
pub const TRITS_PER_LINK: usize = 2 * TRITS_PER_B;
pub const PER_LAYER: usize = TRITS_PER_LINK * LINKS;
pub const PARAMS: usize = 2 * PER_LAYER;

fn xl(x: usize, y: usize) -> usize {
    2 * (y * LX + x)
}
fn yl(x: usize, y: usize) -> usize {
    2 * (y * LX + x) + 1
}

/// (control, target) SUMs along flux-free cuts
pub fn cuts() -> Vec<(usize, usize)> {
    let mut v: Vec<(usize, usize)> = (0..LX).map(|x| (xl(x, 0), xl(x, 1))).collect();
    for y in 0..LY {
        for x in 1..LX {
            v.push((yl(0, y), yl(x, y)));
        }
    }
    v
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NetT {
    pub params: Vec<i64>,
}

impl NetT {
    fn bs(&self, l: usize, q: usize) -> (i128, i128) {
        let i = l * PER_LAYER + q * TRITS_PER_LINK;
        (
            b8(&self.params[i..i + TRITS_PER_B]),
            b8(&self.params[i + TRITS_PER_B..i + TRITS_PER_LINK]),
        )
    }
    fn rotations(&self, l: usize, e: &mut dyn Engine, sign: i128) {
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
    fn ring(e: &mut dyn Engine, s: i64) {
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
    pub fn layer1(&self, e: &mut dyn Engine) {
        self.rotations(0, e, 1);
        for (c, t) in cuts() {
            e.sum(c, t, 1);
        }
    }
    pub fn layer2(&self, e: &mut dyn Engine) {
        if self.layer2_active() {
            Self::ring(e, 1);
            self.rotations(1, e, 1);
            Self::ring(e, -1);
        }
    }
    pub fn forward(&self, e: &mut dyn Engine) {
        self.layer1(e);
        self.layer2(e);
    }
    pub fn inverse(&self, e: &mut dyn Engine) {
        if self.layer2_active() {
            Self::ring(e, 1);
            self.rotations(1, e, -1);
            Self::ring(e, -1);
        }
        for (c, t) in cuts().into_iter().rev() {
            e.sum(c, t, -1);
        }
        self.rotations(0, e, -1);
    }
}

/// Coordinate descent over balanced trits ranked by the fixed-point energy, keeping strict decreases.
/// Returns (params, fixed-point energy, evaluations, sweeps).
pub fn train(t: &Torus, seed: &[i64], r: i64, max_sweeps: usize) -> (Vec<i64>, i128, usize, usize) {
    let l1 = |p: &[i64]| {
        let mut s = StateF::zero_state(LINKS);
        NetT { params: p.to_vec() }.layer1(&mut s);
        s
    };
    let fin = |p: &[i64], s1: &StateF| {
        let mut s = s1.clone();
        NetT { params: p.to_vec() }.layer2(&mut s);
        t.energy_fixed(&s.v, r)
    };
    let mut p = seed.to_vec();
    let mut cache = l1(&p);
    let mut best = fin(&p, &cache).expect("physical seed");
    let (mut evals, mut sweeps) = (1usize, 0usize);
    for _ in 0..max_sweeps {
        sweeps += 1;
        let mut changed = false;
        for i in 0..p.len() {
            let keep = p[i];
            let mut best_v = keep;
            for v in -1..=1 {
                if v == keep {
                    continue;
                }
                p[i] = v;
                evals += 1;
                let e = if i < PER_LAYER {
                    fin(&p, &l1(&p))
                } else {
                    fin(&p, &cache)
                };
                if let Some(e) = e {
                    if e < best {
                        best = e;
                        best_v = v;
                    }
                }
            }
            p[i] = best_v;
            if best_v != keep {
                changed = true;
                if i < PER_LAYER {
                    cache = l1(&p);
                }
            }
        }
        if !changed {
            break;
        }
    }
    (p, best, evals, sweeps)
}
