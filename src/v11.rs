//! v11: v10's two layers plus a tree-frame layer, as sealed in PREREG-V11.hbp. For each tree link t,
//! delta_t = fix(e_t) is the shift its electric move makes on the free links; SUMs from the first free
//! link q with delta_q != 0 map delta_t onto q alone, R_01, R_02 rotate q, and the SUMs are undone.

use crate::gfix::GaugeFixed;
use crate::torus::StateF;
use crate::v10::{param_count, NetV10, TPL};
use crate::v6::{b8, A6, TRITS_PER_B};
use crate::v7::Engine;

/// (q, [(i, s)]) for every tree link: SUM(q -> i, s) puts delta_t on qutrit q alone
pub fn tree_frames(gf: &GaugeFixed) -> Vec<(usize, Vec<(usize, i64)>)> {
    (0..gf.links)
        .filter(|&l| GaugeFixed::is_tree(gf.lx, gf.ly, l))
        .map(|l| {
            let mut g = vec![0i64; gf.links];
            g[l] = 1;
            let f = gf.fix(&g);
            let delta: Vec<i64> = (0..gf.free.len())
                .map(|i| ((f / 3usize.pow(i as u32)) % 3) as i64)
                .collect();
            let q = delta
                .iter()
                .position(|&d| d != 0)
                .expect("tree link moves a free link");
            let dq = delta[q];
            let src = (0..delta.len())
                .filter(|&i| i != q && delta[i] != 0)
                .map(|i| (i, (-(delta[i] * dq)).rem_euclid(3)))
                .collect();
            (q, src)
        })
        .collect()
}

pub fn params_v11(gf: &GaugeFixed) -> usize {
    param_count(gf) + TPL * tree_frames(gf).len()
}

pub struct NetV11<'a> {
    pub gf: &'a GaugeFixed,
    pub params: &'a [i64],
}

impl NetV11<'_> {
    fn split(&self) -> usize {
        param_count(self.gf)
    }
    fn tree(&self, e: &mut dyn Engine, sign: i128) {
        let fr = tree_frames(self.gf);
        let p = &self.params[self.split()..];
        let order: Vec<usize> = if sign > 0 {
            (0..fr.len()).collect()
        } else {
            (0..fr.len()).rev().collect()
        };
        for k in order {
            let pk = &p[k * TPL..(k + 1) * TPL];
            if pk.iter().all(|&x| x == 0) {
                continue;
            }
            let (q, src) = &fr[k];
            for &(i, s) in src {
                e.sum(*q, i, s);
            }
            let (b1, b2) = (b8(&pk[..TRITS_PER_B]), b8(&pk[TRITS_PER_B..]));
            if sign > 0 {
                e.rotate(*q, 0, 1, b1, A6);
                e.rotate(*q, 0, 2, b2, A6);
            } else {
                e.rotate(*q, 0, 2, -b2, A6);
                e.rotate(*q, 0, 1, -b1, A6);
            }
            for &(i, s) in src.iter().rev() {
                e.sum(*q, i, -s);
            }
        }
    }
    pub fn layer1(&self, e: &mut dyn Engine) {
        NetV10 {
            gf: self.gf,
            params: &self.params[..self.split()],
        }
        .layer1(e);
    }
    pub fn rest(&self, e: &mut dyn Engine) {
        NetV10 {
            gf: self.gf,
            params: &self.params[..self.split()],
        }
        .layer2(e, 1);
        self.tree(e, 1);
    }
    pub fn forward(&self, e: &mut dyn Engine) {
        self.layer1(e);
        self.rest(e);
    }
    pub fn inverse(&self, e: &mut dyn Engine) {
        self.tree(e, -1);
        NetV10 {
            gf: self.gf,
            params: &self.params[..self.split()],
        }
        .inverse(e);
    }
}

/// Coordinate descent over all trits ranked by the fixed-point energy; layer-1 output cached.
pub fn train(
    gf: &GaugeFixed,
    seed: &[i64],
    r: i64,
    max_sweeps: usize,
) -> (Vec<i64>, i128, usize, usize) {
    let nq = gf.free.len();
    let l1n = TPL * nq;
    let l1 = |p: &[i64]| {
        let mut s = StateF::zero_state(nq);
        NetV11 { gf, params: p }.layer1(&mut s);
        s
    };
    let fin = |p: &[i64], s1: &StateF| {
        let mut s = s1.clone();
        NetV11 { gf, params: p }.rest(&mut s);
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
                let e = if i < l1n {
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
                if i < l1n {
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
