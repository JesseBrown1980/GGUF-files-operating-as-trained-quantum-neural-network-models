//! POST-HOC DIAGNOSTIC on the sealed v8 models, 3 x 2 torus (not a verdict). Three hypotheses for the
//! remaining gap at r = 9, each reported with the exact big-integer energy, the fraction of the norm
//! that survives gauge projection and the residual |(H - E) phi| / |phi| of the projected state:
//!   D1 training budget: resume the sealed r = 9 model to 8 and 16 total sweeps (fixed-point ranking);
//!   D2 holonomy: one sector against nine with a real circulant dressing D = 1000 I + k (X + X^dagger),
//!      and the sealed r = 9 circuit applied to the nine-sector input;
//!   D3 correlation geometry: from the sealed layer 1, train only layer 2 for 2 sweeps, as the v8 ring
//!      and as plaquette-local gates (SUM a->b, SUM b->c inverse, SUM c->d, rotations on c and d,
//!      undone), the same 192 trits and the same sweeps.
//! usage: cargo run --release --example v8_diag -- RESULTS_V8_DIR
use gguf_qnn::bigint::Big;
use gguf_qnn::gguf_model;
use gguf_qnn::torus::{StateF, Torus, FIXED_ONE};
use gguf_qnn::v4::{milli_floor_q, StateR};
use gguf_qnn::v6::{b8, A6, TRITS_PER_B};
use gguf_qnn::v7::Engine;
use gguf_qnn::v8::{train, NetT, LINKS, PARAMS, PER_LAYER};
use std::path::Path;

const R: i64 = 9;

fn milli(e: &(Big, Big)) -> i128 {
    milli_floor_q(e, 0, 100_000_000).expect("milli")
}

/// largest t with t^2 * b <= a
fn isqrt_ratio(a: &Big, b: &Big) -> i128 {
    let (mut lo, mut hi) = (0i128, 1i128 << 40);
    while hi - lo > 1 {
        let mid = (lo + hi) / 2;
        if b.mul_i128(mid * mid).sub(a).sign() <= 0 {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    lo
}

/// (exact energy, projection fraction per mille, residual in milli)
fn report(t: &Torus, v: &[Big]) -> ((Big, Big), i128, i128) {
    let e = t.energy_exact(v, R).expect("physical");
    let n = t.reps.len();
    let mut s = vec![Big::zero(); n];
    for (c, z) in v.iter().enumerate() {
        if !z.is_zero() {
            s[t.orbit_of[c]] = s[t.orbit_of[c]].add(z);
        }
    }
    let w = (t.group_order / t.sizes[0]) as i128;
    let size = t.sizes[0] as i128;
    // fraction = sum_o w S_o^2 / (|G| sum psi^2)
    let num_p = s
        .iter()
        .fold(Big::zero(), |a, x| a.add(&x.mul(x)))
        .mul_i128(w);
    let den_p = v
        .iter()
        .fold(Big::zero(), |a, x| a.add(&x.mul(x)))
        .mul_i128(t.group_order as i128);
    let frac = isqrt_ratio(&num_p.mul(&num_p).mul_i128(1_000_000), &den_p.mul(&den_p));
    // residual: A_o = size (2L + r mag_o) phi_o - sum_o' (K(o,o') + K(o',o)) phi_o'
    let phi: Vec<Big> = s.iter().map(|x| x.mul_i128(w)).collect();
    let mut a: Vec<Big> = phi
        .iter()
        .enumerate()
        .map(|(o, x)| x.mul_i128(size * (2 * LINKS as i128 + i128::from(R) * i128::from(t.mag[o]))))
        .collect();
    for &(o, o2, k) in &t.hop {
        a[o] = a[o].sub(&phi[o2].mul_i128(i128::from(k)));
        a[o2] = a[o2].sub(&phi[o].mul_i128(i128::from(k)));
    }
    let q: Vec<Big> = (0..n)
        .map(|o| e.1.mul(&a[o]).sub(&e.0.mul(&phi[o]).mul_i128(size)))
        .collect();
    let rn = q.iter().fold(Big::zero(), |acc, x| acc.add(&x.mul(x)));
    let rd = phi
        .iter()
        .fold(Big::zero(), |acc, x| acc.add(&x.mul(x)))
        .mul(&e.1)
        .mul(&e.1)
        .mul_i128(size * size);
    let res = isqrt_ratio(&rn.mul_i128(1_000_000), &rd);
    (e, frac, res)
}

fn line(tag: &str, t: &Torus, v: &[Big], extra: &str) {
    let (e, frac, res) = report(t, v);
    println!(
        "DIAG|{tag}|energy_milli_floor={}|projection_fraction_permille={frac}|residual_milli={res}{extra}|json=0",
        milli(&e)
    );
}

fn load(dir: &Path, r: i64) -> Vec<i64> {
    let b =
        std::fs::read(dir.join(format!("v8-z3-3x2-r{r}-identity.gguf"))).expect("sealed v8 model");
    gguf_model::read(&b)
        .expect("parse")
        .tensor("branch_0.params")
        .expect("p")
        .iter()
        .map(|&x| i64::from(x))
        .collect()
}

fn exact_state(p: &[i64], input: Option<&[Big]>) -> Vec<Big> {
    let mut s = StateR::zero_state(LINKS);
    if let Some(v) = input {
        s.v = v.to_vec();
    }
    NetT { params: p.to_vec() }.forward(&mut s);
    s.v
}

/// plaquette-local layer 2 on top of the given layer-1 engine state
struct Plaq<'a> {
    p: &'a [i64],
}

fn plaquettes() -> Vec<[usize; 4]> {
    let (lx, ly) = (3usize, 2usize);
    (0..lx * ly)
        .map(|s| {
            let sx = (s / lx) * lx + (s % lx + 1) % lx;
            let sy = ((s / lx + 1) % ly) * lx + s % lx;
            [2 * s, 2 * sx + 1, 2 * sy, 2 * s + 1]
        })
        .collect()
}

impl Plaq<'_> {
    fn apply(&self, e: &mut dyn Engine) {
        for (k, pl) in plaquettes().iter().enumerate() {
            let [a, b, c, d] = *pl;
            e.sum(a, b, 1);
            e.sum(b, c, -1);
            e.sum(c, d, 1);
            for (j, &q) in [c, d].iter().enumerate() {
                let i = PER_LAYER + (2 * k + j) * 2 * TRITS_PER_B;
                e.rotate(q, 0, 1, b8(&self.p[i..i + TRITS_PER_B]), A6);
                e.rotate(
                    q,
                    0,
                    2,
                    b8(&self.p[i + TRITS_PER_B..i + 2 * TRITS_PER_B]),
                    A6,
                );
            }
            e.sum(c, d, -1);
            e.sum(b, c, 1);
            e.sum(a, b, -1);
        }
    }
}

/// train only layer 2 (indices >= PER_LAYER) for `sweeps`, ranking by fixed point
fn train_layer2(t: &Torus, p0: &[i64], plaq: bool, sweeps: usize) -> Vec<i64> {
    let mut base = StateF::zero_state(LINKS);
    NetT {
        params: p0.to_vec(),
    }
    .layer1(&mut base);
    let eval = |p: &[i64]| {
        let mut s = base.clone();
        if plaq {
            Plaq { p }.apply(&mut s);
        } else {
            NetT { params: p.to_vec() }.layer2(&mut s);
        }
        t.energy_fixed(&s.v, R)
    };
    let mut p = p0.to_vec();
    let mut best = eval(&p).expect("physical");
    for _ in 0..sweeps {
        for i in PER_LAYER..PARAMS {
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
    }
    p
}

fn main() {
    let dir = std::env::args().nth(1).expect("RESULTS_V8_DIR");
    let dir = Path::new(&dir);
    let t = Torus::new(3, 2);
    let p9 = load(dir, 9);
    // the sealed model, as a reference
    let v = exact_state(&p9, None);
    line("sealed_r9_model", &t, &v, "");

    // D1: training budget
    let mut p = p9.clone();
    for (stage, more) in [(8usize, 4usize), (16, 8)] {
        let (np, _, evals, used) = train(&t, &p, R, more);
        p = np;
        let v = exact_state(&p, None);
        line(
            &format!("D1_total_sweeps={stage}"),
            &t,
            &v,
            &format!("|sweeps_used_this_stage={used}|evaluations={evals}"),
        );
    }

    // D2: holonomy
    let p3 = |l: usize| 3usize.pow(l as u32);
    let hol = |sectors: usize| -> Vec<Big> {
        let mut v = vec![Big::zero(); t.dim];
        for h in 0..sectors {
            let (hx, hy) = (h % 3, h / 3);
            v[hx * (p3(0) + p3(6)) + hy * (p3(1) + p3(3) + p3(5))] = Big::from_i128(1);
        }
        v
    };
    for sectors in [1usize, 9] {
        let mut best: Option<(i128, i64)> = None;
        for k in 0..=40i64 {
            let mut f = StateF::zero_state(LINKS);
            f.v[0] = 0;
            for h in 0..sectors {
                let (hx, hy) = (h % 3, h / 3);
                f.v[hx * (p3(0) + p3(6)) + hy * (p3(1) + p3(3) + p3(5))] = FIXED_ONE / 16;
            }
            for q in 0..LINKS {
                let st = p3(q);
                let mut out = vec![0i64; f.v.len()];
                for (i, &z) in f.v.iter().enumerate() {
                    if z == 0 {
                        continue;
                    }
                    let d = (i / st) % 3;
                    out[i] += z;
                    let zk = (i128::from(z) * i128::from(k) / 1000) as i64;
                    out[i - d * st + ((d + 1) % 3) * st] += zk;
                    out[i - d * st + ((d + 2) % 3) * st] += zk;
                }
                f.v = out;
            }
            let e = t.energy_fixed(&f.v, R).expect("physical");
            if best.map_or(true, |(b, _)| e < b) {
                best = Some((e, k));
            }
        }
        let k = best.expect("scan").1;
        let mut v = hol(sectors);
        for q in 0..LINKS {
            let st = p3(q);
            let mut out = vec![Big::zero(); v.len()];
            for (i, z) in v.iter().enumerate() {
                if z.is_zero() {
                    continue;
                }
                let d = (i / st) % 3;
                out[i] = out[i].add(&z.mul_i128(1000));
                let up = i - d * st + ((d + 1) % 3) * st;
                let dn = i - d * st + ((d + 2) % 3) * st;
                out[up] = out[up].add(&z.mul_i128(i128::from(k)));
                out[dn] = out[dn].add(&z.mul_i128(i128::from(k)));
            }
            v = out;
        }
        line(
            &format!("D2_circulant_dressing_sectors={sectors}"),
            &t,
            &v,
            &format!("|k_per_mille={k}"),
        );
    }
    let v = exact_state(&p9, Some(&hol(9)));
    line("D2_sealed_circuit_on_nine_sector_input", &t, &v, "");

    // D3: correlation geometry, equal trits and sweeps
    let mut p0 = p9.clone();
    for x in p0.iter_mut().skip(PER_LAYER) {
        *x = 0;
    }
    let ring = train_layer2(&t, &p0, false, 2);
    let v = exact_state(&ring, None);
    line(
        "D3_layer2_ring_2_sweeps",
        &t,
        &v,
        &format!(
            "|trits_changed={}",
            ring.iter().zip(&p0).filter(|(a, b)| a != b).count()
        ),
    );
    let pl = train_layer2(&t, &p0, true, 2);
    let mut s = StateR::zero_state(LINKS);
    NetT { params: p0.clone() }.layer1(&mut s);
    Plaq { p: &pl }.apply(&mut s);
    line(
        "D3_layer2_plaquette_2_sweeps",
        &t,
        &s.v,
        &format!(
            "|trits_changed={}",
            pl.iter().zip(&p0).filter(|(a, b)| a != b).count()
        ),
    );
}
