//! v10: the network on the gauge-fixed free links, as sealed in PREREG-V10.hbp. Layer 1: R_01(b),
//! R_02(b') on every free link. Layer 2: for every plaquette, SUMs from its other free links into its last
//! free link with the signs that make that link hold the plaquette flux, R_01, R_02 on it, SUMs undone.

use crate::gfix::GaugeFixed;
use crate::torus::StateF;
use crate::v6::{b8, A6, TRITS_PER_B};
use crate::v7::Engine;

pub const TPL: usize = 2 * TRITS_PER_B;

pub struct NetV10<'a> {
    pub gf: &'a GaugeFixed,
    pub params: &'a [i64],
}

pub fn param_count(gf: &GaugeFixed) -> usize {
    TPL * (gf.free.len() + gf.lx * gf.ly)
}

impl NetV10<'_> {
    fn l1(&self) -> usize {
        TPL * self.gf.free.len()
    }
    fn b(&self, i: usize) -> (i128, i128) {
        (
            b8(&self.params[i..i + TRITS_PER_B]),
            b8(&self.params[i + TRITS_PER_B..i + TPL]),
        )
    }
    pub fn layer1(&self, e: &mut dyn Engine) {
        for q in 0..self.gf.free.len() {
            let (b1, b2) = self.b(q * TPL);
            e.rotate(q, 0, 1, b1, A6);
            e.rotate(q, 0, 2, b2, A6);
        }
    }
    /// (target, [(source, sign)]) for every plaquette: the SUMs put sign_t * flux into the target
    fn frames(&self) -> Vec<(usize, Vec<(usize, i64)>)> {
        self.gf
            .plaquette_free_links()
            .into_iter()
            .filter(|p| !p.is_empty())
            .map(|p| {
                let (t, st) = *p.last().expect("free link");
                let src = p[..p.len() - 1]
                    .iter()
                    .map(|&(o, so)| (o, so * st))
                    .collect();
                (t, src)
            })
            .collect()
    }
    fn active2(&self) -> bool {
        self.params[self.l1()..].iter().any(|&x| x != 0)
    }
    pub fn layer2(&self, e: &mut dyn Engine, sign: i128) {
        if !self.active2() {
            return;
        }
        let frames = self.frames();
        let order: Vec<usize> = if sign > 0 {
            (0..frames.len()).collect()
        } else {
            (0..frames.len()).rev().collect()
        };
        let plaq_ids: Vec<usize> = self
            .gf
            .plaquette_free_links()
            .iter()
            .enumerate()
            .filter(|(_, p)| !p.is_empty())
            .map(|(k, _)| k)
            .collect();
        for k in order {
            let (t, src) = &frames[k];
            for &(o, s) in src {
                e.sum(o, *t, s);
            }
            let (b1, b2) = self.b(self.l1() + plaq_ids[k] * TPL);
            if sign > 0 {
                e.rotate(*t, 0, 1, b1, A6);
                e.rotate(*t, 0, 2, b2, A6);
            } else {
                e.rotate(*t, 0, 2, -b2, A6);
                e.rotate(*t, 0, 1, -b1, A6);
            }
            for &(o, s) in src.iter().rev() {
                e.sum(o, *t, -s);
            }
        }
    }
    pub fn forward(&self, e: &mut dyn Engine) {
        self.layer1(e);
        self.layer2(e, 1);
    }
    pub fn inverse(&self, e: &mut dyn Engine) {
        self.layer2(e, -1);
        for q in (0..self.gf.free.len()).rev() {
            let (b1, b2) = self.b(q * TPL);
            e.rotate(q, 0, 2, -b2, A6);
            e.rotate(q, 0, 1, -b1, A6);
        }
    }
}

/// Coordinate descent over balanced trits ranked by the fixed-point energy (as v8 and v9).
pub fn train(
    gf: &GaugeFixed,
    seed: &[i64],
    r: i64,
    max_sweeps: usize,
) -> (Vec<i64>, i128, usize, usize) {
    let nq = gf.free.len();
    let split = TPL * nq;
    let l1 = |p: &[i64]| {
        let mut s = StateF::zero_state(nq);
        NetV10 { gf, params: p }.layer1(&mut s);
        s
    };
    let fin = |p: &[i64], s1: &StateF| {
        let mut s = s1.clone();
        NetV10 { gf, params: p }.layer2(&mut s, 1);
        gf.energy_fixed(&s.v, r)
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
                let e = if i < split {
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
                if i < split {
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
