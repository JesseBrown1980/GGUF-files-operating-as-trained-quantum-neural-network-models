//! POST-HOC DIAGNOSTIC on the sealed v10 r = 9 model, 3 x 3 torus (not a verdict).
//! Hypothesis: in the gauge-fixed basis a tree link's electric move X_t shifts several free links at
//! once (the fixed vector delta_t = fix(e_t)), so layer 1, which rotates single free links, cannot dress
//! tree links. Test: keep the sealed v10 network and add a tree-frame layer: for each of the 8 tree
//! links, SUMs map delta_t onto one free qutrit q, R_01, R_02 rotate q, the SUMs are undone (16 trits
//! per tree link). Train only that layer for 2 sweeps (fixed-point ranking), report exact energies.
//! usage: cargo run --release --example v10_diag -- RESULTS_V10_DIR
use gguf_qnn::gfix::GaugeFixed;
use gguf_qnn::gguf_model;
use gguf_qnn::torus::StateF;
use gguf_qnn::v10::{NetV10, TPL};
use gguf_qnn::v4::{milli_floor_q, StateR};
use gguf_qnn::v6::{b8, A6, TRITS_PER_B};
use gguf_qnn::v7::Engine;
use std::path::Path;

const R: i64 = 9;

/// (q, [(i, s)]): SUM(q -> i, s) for each i, so that delta_t lands on qutrit q alone
fn frames(gf: &GaugeFixed) -> Vec<(usize, Vec<(usize, i64)>)> {
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
            let dq = delta[q]; // 1 or 2; its inverse mod 3 is itself
            let src = (0..delta.len())
                .filter(|&i| i != q && delta[i] != 0)
                .map(|i| (i, (-(delta[i] * dq)).rem_euclid(3)))
                .collect();
            (q, src)
        })
        .collect()
}

fn tree_layer(fr: &[(usize, Vec<(usize, i64)>)], p: &[i64], e: &mut dyn Engine) {
    for (k, (q, src)) in fr.iter().enumerate() {
        if p[k * TPL..(k + 1) * TPL].iter().all(|&x| x == 0) {
            continue;
        }
        for &(i, s) in src {
            e.sum(*q, i, s);
        }
        e.rotate(*q, 0, 1, b8(&p[k * TPL..k * TPL + TRITS_PER_B]), A6);
        e.rotate(*q, 0, 2, b8(&p[k * TPL + TRITS_PER_B..(k + 1) * TPL]), A6);
        for &(i, s) in src.iter().rev() {
            e.sum(*q, i, -s);
        }
    }
}

fn main() {
    let dir = std::env::args().nth(1).expect("RESULTS_V10_DIR");
    let b = std::fs::read(Path::new(&dir).join("v10-z3-3x3-r9-identity.gguf"))
        .expect("sealed v10 model");
    let p10: Vec<i64> = gguf_model::read(&b)
        .expect("parse")
        .tensor("branch_0.params")
        .expect("p")
        .iter()
        .map(|&x| i64::from(x))
        .collect();
    let gf = GaugeFixed::new(3, 3);
    let fr = frames(&gf);
    let nq = gf.free.len();
    let exact = |pt: &[i64]| {
        let mut s = StateR::zero_state(nq);
        NetV10 {
            gf: &gf,
            params: &p10,
        }
        .forward(&mut s);
        tree_layer(&fr, pt, &mut s);
        let e = gf.energy_exact(&s.v, R).expect("physical");
        milli_floor_q(&e, 0, 100_000_000).expect("milli")
    };
    let zero = vec![0i64; fr.len() * TPL];
    println!(
        "DIAG10|sealed_r9_model|energy_milli_floor={}|json=0",
        exact(&zero)
    );
    let mut base = StateF::zero_state(nq);
    NetV10 {
        gf: &gf,
        params: &p10,
    }
    .forward(&mut base);
    let eval = |pt: &[i64]| {
        let mut s = base.clone();
        tree_layer(&fr, pt, &mut s);
        gf.energy_fixed(&s.v, R)
    };
    let mut p = zero.clone();
    let mut best = eval(&p).expect("physical");
    for sweep in 1..=2 {
        for i in 0..p.len() {
            let keep = p[i];
            let mut bv = keep;
            for v in -1..=1 {
                if v == keep {
                    continue;
                }
                p[i] = v;
                if let Some(e) = eval(&p) {
                    if e < best {
                        best = e;
                        bv = v;
                    }
                }
            }
            p[i] = bv;
        }
        println!(
            "DIAG10|tree_frame_layer_sweeps={sweep}|energy_milli_floor={}|trits_changed={}|json=0",
            exact(&p),
            p.iter().filter(|&&x| x != 0).count()
        );
    }
}
