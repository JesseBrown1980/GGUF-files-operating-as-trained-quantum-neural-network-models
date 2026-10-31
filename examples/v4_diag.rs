//! POST-HOC DIAGNOSTIC on the sealed v4 code (after SEAL-V4; not a verdict).
//! 1. The best product state on the a = 729 grid: every link gets R_01(b), R_02(b').
//! 2. The second-order estimate E2 = 16 - sum_k H_fk^2 / (H_kk - 16) from the flat orbit.
use gguf_qnn::bigint::Big;
use gguf_qnn::v4::{cmp_q, milli_floor_q, StateR, Z3Orbits};
use gguf_qnn::ym_z3::{physical, LINKS};

fn product(o: &Z3Orbits, b1: i128, b2: i128, r: i64) -> (Big, Big) {
    let mut s = StateR::zero_state(LINKS);
    for q in 0..LINKS {
        s.rotate(q, 0, 1, b1);
        s.rotate(q, 0, 2, b2);
    }
    o.energy(&s, r).expect("physical")
}

fn main() {
    if std::env::args().any(|a| a == "holonomy") {
        holonomy_scan();
        return;
    }
    let o = Z3Orbits::new();
    let p = physical();
    let f = p.orbit_of[0];
    for r in [9i64, 27, 81] {
        // product scan
        let mut best: Option<((Big, Big), i128, i128)> = None;
        for b1 in -40i128..=40 {
            for b2 in [b1 - 2, b1 - 1, b1, b1 + 1, b1 + 2] {
                if !(-40..=40).contains(&b2) {
                    continue;
                }
                let e = product(&o, b1, b2, r);
                if best.as_ref().map_or(true, |(x, _, _)| cmp_q(&e, x) < 0) {
                    best = Some((e, b1, b2));
                }
            }
        }
        let (e, b1, b2) = best.expect("scan");
        // second order: numerator/denominator as a sum of fractions
        let mut num = Big::zero();
        let mut den = Big::from_i128(1);
        let n = p.reps.len();
        let mut terms = 0;
        for k in 0..n {
            if k == f {
                continue;
            }
            let key = if f < k { (f, k) } else { (k, f) };
            let h = i128::from(*p.electric.get(&key).unwrap_or(&0));
            if h == 0 {
                continue;
            }
            terms += 1;
            let hkk = i128::from(*p.electric.get(&(k, k)).unwrap_or(&0))
                + i128::from(r) * i128::from(p.mag[k]);
            let d = hkk - 16;
            // num/den += h^2 / d
            num = num.mul_i128(d).add(&den.mul_i128(h * h));
            den = den.mul_i128(d);
        }
        let e2 = (Big::from_i128(16).mul(&den).sub(&num), den);
        println!(
            "DIAG|r={r}|best_product_b={b1},{b2}|best_product_milli={}|second_order_terms={terms}|E2_milli={}|json=0",
            milli_floor_q(&e, 0, 10_000_000).map_or("undecided".into(), |t| t.to_string()),
            milli_floor_q(&e2, 0, 10_000_000).map_or("undecided".into(), |t| t.to_string()),
        );
    }
}

/// Part 3, the holonomy test: D on every link applied to |0..0>, or to the sum over the nine
/// zero-flux configurations with hx on x-links 0 and 4 and hy on y-links 1 and 3.
/// D = 1000 I + k (X + X^dagger), a real circulant dressing used only in this diagnostic.
#[allow(dead_code)]
pub fn holonomy_scan() {
    let o = Z3Orbits::new();
    for r in [9i64, 27, 81] {
        for sectors in [1usize, 9] {
            let mut best: Option<((Big, Big), i128)> = None;
            for k in 0i128..=60 {
                let mut s = StateR::zero_state(LINKS);
                s.v[0] = Big::zero();
                for h in 0..sectors {
                    let (hx, hy) = (h % 3, h / 3);
                    let idx = hx + hx * 81 + hy * 3 + hy * 27; // links 0,4 = hx; links 1,3 = hy
                    s.v[idx] = Big::from_i128(1);
                }
                for q in 0..LINKS {
                    let st = 3usize.pow(q as u32);
                    let mut out = vec![Big::zero(); s.v.len()];
                    for (i, z) in s.v.iter().enumerate() {
                        if z.is_zero() {
                            continue;
                        }
                        let d = (i / st) % 3;
                        let up = i - d * st + ((d + 1) % 3) * st;
                        let dn = i - d * st + ((d + 2) % 3) * st;
                        out[i] = out[i].add(&z.mul_i128(1000));
                        out[up] = out[up].add(&z.mul_i128(k));
                        out[dn] = out[dn].add(&z.mul_i128(k));
                    }
                    s.v = out;
                }
                let e = o.energy(&s, r).expect("physical");
                if best.as_ref().map_or(true, |(x, _)| cmp_q(&e, x) < 0) {
                    best = Some((e, k));
                }
            }
            let (e, k) = best.expect("scan");
            println!(
                "HOLONOMY|r={r}|sectors={sectors}|best_k_per_mille={k}|energy_milli={}|json=0",
                milli_floor_q(&e, 0, 10_000_000).map_or("undecided".into(), |t| t.to_string())
            );
        }
    }
}
