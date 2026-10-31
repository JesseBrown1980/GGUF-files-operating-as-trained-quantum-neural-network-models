//! v9: v8's layer 1 and a plaquette-flux correlation layer, as sealed in PREREG-V9.hbp. For each
//! plaquette (a, b, c, d) = (x(s), y(s+x), x(s+y), y(s)): SUM a->b, SUM b->c inverse, SUM c->d (link d
//! then holds minus the plaquette flux), R_01, R_02 on c and d, and the three SUMs undone.

use crate::torus::{StateF, Torus};
use crate::v6::{b8, A6, TRITS_PER_B};
use crate::v7::Engine;
use crate::v8::{NetT, LINKS, LX, LY, PARAMS, PER_LAYER};

pub fn plaquettes() -> Vec<[usize; 4]> {
    (0..LX * LY)
        .map(|s| {
            let sx = (s / LX) * LX + (s % LX + 1) % LX;
            let sy = ((s / LX + 1) % LY) * LX + s % LX;
            [2 * s, 2 * sx + 1, 2 * sy, 2 * s + 1]
        })
        .collect()
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NetV9 {
    pub params: Vec<i64>,
}

impl NetV9 {
    fn bpair(&self, k: usize, j: usize) -> (i128, i128) {
        let i = PER_LAYER + (2 * k + j) * 2 * TRITS_PER_B;
        (
            b8(&self.params[i..i + TRITS_PER_B]),
            b8(&self.params[i + TRITS_PER_B..i + 2 * TRITS_PER_B]),
        )
    }
    fn layer1_net(&self) -> NetT {
        let mut p = self.params.clone();
        for x in p.iter_mut().skip(PER_LAYER) {
            *x = 0;
        }
        NetT { params: p }
    }
    pub fn layer1(&self, e: &mut dyn Engine) {
        self.layer1_net().layer1(e);
    }
    fn frame(e: &mut dyn Engine, pl: [usize; 4], s: i64) {
        let [a, b, c, d] = pl;
        if s > 0 {
            e.sum(a, b, 1);
            e.sum(b, c, -1);
            e.sum(c, d, 1);
        } else {
            e.sum(c, d, -1);
            e.sum(b, c, 1);
            e.sum(a, b, -1);
        }
    }
    pub fn layer2(&self, e: &mut dyn Engine) {
        if self.params[PER_LAYER..].iter().all(|&x| x == 0) {
            return;
        }
        for (k, pl) in plaquettes().into_iter().enumerate() {
            Self::frame(e, pl, 1);
            for (j, &q) in [pl[2], pl[3]].iter().enumerate() {
                let (b1, b2) = self.bpair(k, j);
                e.rotate(q, 0, 1, b1, A6);
                e.rotate(q, 0, 2, b2, A6);
            }
            Self::frame(e, pl, -1);
        }
    }
    pub fn forward(&self, e: &mut dyn Engine) {
        self.layer1(e);
        self.layer2(e);
    }
    pub fn inverse(&self, e: &mut dyn Engine) {
        if self.params[PER_LAYER..].iter().any(|&x| x != 0) {
            for (k, pl) in plaquettes().into_iter().enumerate().rev() {
                Self::frame(e, pl, 1);
                for (j, &q) in [pl[2], pl[3]].iter().enumerate().rev() {
                    let (b1, b2) = self.bpair(k, j);
                    e.rotate(q, 0, 2, -b2, A6);
                    e.rotate(q, 0, 1, -b1, A6);
                }
                Self::frame(e, pl, -1);
            }
        }
        self.layer1_net().inverse(e);
    }
}

/// Coordinate descent over balanced trits ranked by the fixed-point energy (as v8).
pub fn train(t: &Torus, seed: &[i64], r: i64, max_sweeps: usize) -> (Vec<i64>, i128, usize, usize) {
    let l1 = |p: &[i64]| {
        let mut s = StateF::zero_state(LINKS);
        NetV9 { params: p.to_vec() }.layer1(&mut s);
        s
    };
    let fin = |p: &[i64], s1: &StateF| {
        let mut s = s1.clone();
        NetV9 { params: p.to_vec() }.layer2(&mut s);
        t.energy_fixed(&s.v, r)
    };
    let mut p = seed.to_vec();
    assert_eq!(p.len(), PARAMS);
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
