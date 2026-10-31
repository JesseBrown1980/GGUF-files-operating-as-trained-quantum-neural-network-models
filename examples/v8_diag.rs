//! POST-HOC DIAGNOSTIC on the 3 x 2 torus after SEAL-V8 (fixed-point energies; not a verdict).
//! A real circulant dressing D = 1000 I + k (X + X^dagger) on every link, applied to |0..0> (one
//! holonomy sector) or to the sum of the nine zero-flux holonomy configurations (hx on the column-0
//! x-links 0 and 6, hy on the row-0 y-links 1, 3 and 5); best k per coupling.
//! usage: cargo run --release --example v8_diag
use gguf_qnn::torus::{Torus, FIXED_ONE};

fn dress(v: &[i64], links: usize, k: i64) -> Vec<i64> {
    let mut cur = v.to_vec();
    for q in 0..links {
        let st = 3usize.pow(q as u32);
        let mut out = vec![0i64; cur.len()];
        for (i, &z) in cur.iter().enumerate() {
            if z == 0 {
                continue;
            }
            let d = (i / st) % 3;
            let up = i - d * st + ((d + 1) % 3) * st;
            let dn = i - d * st + ((d + 2) % 3) * st;
            let zi = i128::from(z);
            out[i] += z;
            out[up] += (zi * i128::from(k) / 1000) as i64;
            out[dn] += (zi * i128::from(k) / 1000) as i64;
        }
        cur = out;
    }
    cur
}

fn main() {
    let t = Torus::new(3, 2);
    let p = |l: usize| 3usize.pow(l as u32);
    for r in [9i64, 27, 81] {
        for sectors in [1usize, 9] {
            let mut v = vec![0i64; t.dim];
            for h in 0..sectors {
                let (hx, hy) = (h % 3, h / 3);
                let idx = hx * (p(0) + p(6)) + hy * (p(1) + p(3) + p(5));
                v[idx] = FIXED_ONE / 16;
            }
            let mut best: Option<(i128, i64)> = None;
            for k in 0..=40i64 {
                let e = t.energy_fixed(&dress(&v, t.links, k), r).expect("physical");
                if best.map_or(true, |(b, _)| e < b) {
                    best = Some((e, k));
                }
            }
            let (e, k) = best.expect("scan");
            println!(
                "HOLONOMY_3X2|r={r}|sectors={sectors}|best_k_per_mille={k}|energy_milli_fixed_point={}|json=0",
                (e * 1000) >> 40
            );
        }
    }
}
