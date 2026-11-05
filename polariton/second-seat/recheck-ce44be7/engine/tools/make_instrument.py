# A copy of the engine at ce44be7 whose left shifts and narrowing casts count bits lost, with no change to any value. One bin, attack2/src/bin/inst.rs.
# Added stages: i_conv729 and i_window729 run one chain each of the heaviest rows, i_step reruns conversion rows at k + 2 at N = 729.
import os

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
src = open(W + "/clean/src/bin/polariton_three_mode.rs", encoding="utf8", newline="").read().replace("\r\n", "\n")


def rep(s, a, b, count=1):
    assert s.count(a) == count, (a, s.count(a))
    return s.replace(a, b)


s = rep(src, "#![forbid(unsafe_code)]\n#![deny(clippy::float_arithmetic)]\n", "#![allow(dead_code,unused)]\n")
s = rep(s, "const WORKERS: usize = 5;\n", """const WORKERS: usize = 2;
const ZERO: AtomicUsize = AtomicUsize::new(0);
static WRAPS: [AtomicUsize; 16] = [ZERO; 16];
const SITES: [&str; 16] = ["rescale_shl", "o2_rem_shl18", "o2_quo_shl18", "count_below_ok_shl30", "sector_d_x_shl60", "sector_d_u_shl60", "sector_d_as_i64", "read_shl64", "build_num_shl", "build_coef_as_i64", "element_as_i64", "apply_as_i64", "lanczos_as_i64", "twisted_z_as_i64", "sector_d_step_shl", "row_shl_bits"];
fn shl_i(v: i128, s: u32, site: usize) -> i128 {
    let r = v << s;
    if (r >> s) != v {
        WRAPS[site].fetch_add(1, Ordering::Relaxed);
    }
    r
}
fn shl_u(v: u128, s: u32, site: usize) -> u128 {
    let r = v << s;
    if (r >> s) != v {
        WRAPS[site].fetch_add(1, Ordering::Relaxed);
    }
    r
}
fn fit(v: i128, site: usize) -> i64 {
    if v > i128::from(i64::MAX) || v < i128::from(i64::MIN) {
        WRAPS[site].fetch_add(1, Ordering::Relaxed);
    }
    v as i64
}
""")
s = rep(s, "value << (to - from)", "shl_i(value, to - from, 0)")
s = rep(s, "                rem <<= 18;\n                quo = (quo << 18) + rem / den;", "                rem = shl_u(rem, 18, 1);\n                quo = shl_u(quo, 18, 2) + rem / den;")
s = rep(s, "(*ok << 30) / q", "shl_i(*ok, 30, 3) / q")
s = rep(s, "let mut d = round_div((x.n * sum) << SCALE, x.d * big);", "let mut d = round_div(shl_i(x.n * sum, SCALE, 4), x.d * big);")
s = rep(s, "d += round_div((u.n * (n0 * sum + plus * minus)) << SCALE, u.d * big * big);", "d += round_div(shl_i(u.n * (n0 * sum + plus * minus), SCALE, 5), u.d * big * big);")
s = rep(s, "d += round_div(dx.sign * (sum << (SCALE - dx.m)), big);", "d += round_div(dx.sign * shl_i(sum, SCALE - dx.m, 14), big);")
s = rep(s, "kappa.sign * ((plus * minus) << (SCALE - kappa.m)),", "kappa.sign * shl_i(plus * minus, SCALE - kappa.m, 14),")
s = rep(s, "            d as i64\n", "            fit(d, 6)\n")
s = rep(s, "isqrt((((p + 1) * (m + 1) * n0 * (n0 - 1)) as u128) << 64)", "isqrt(shl_u(((p + 1) * (m + 1) * n0 * (n0 - 1)) as u128, 64, 7))")
s = rep(s, "isqrt((((p + 1) * n0) as u128) << 64)", "isqrt(shl_u(((p + 1) * n0) as u128, 64, 7))")
s = rep(s, "isqrt((((m + 1) * n0) as u128) << 64)", "isqrt(shl_u(((m + 1) * n0) as u128, 64, 7))")
s = rep(s, "isqrt(((p * (m + 1)) as u128) << 64)", "isqrt(shl_u((p * (m + 1)) as u128, 64, 7))")
s = rep(s, "coef.push(round_div(num << bits, den) as i64);", "coef.push(fit(round_div(shl_i(num, bits, 8), den), 9));")
s = rep(s, "round_div(rescale(root, from, bits), big) as i64", "fit(round_div(rescale(root, from, bits), big), 10)")
s = rep(s, "-(round_div(rescale(root * y.n, from, bits), y.d) as i64)", "-fit(round_div(rescale(root * y.n, from, bits), y.d), 10)")
s = rep(s, "*slot = (s >> right) as i64;", "*slot = fit(s >> right, 11);")
s = rep(s, "let a = dot(&w, &basis[k]) as i64;", "let a = fit(dot(&w, &basis[k]), 12);")
s = rep(s, "*x = ((i128::from(*x) * inverse) >> SCALE) as i64;", "*x = fit((i128::from(*x) * inverse) >> SCALE, 12);")
s = rep(s, "*slot -= ((b * i128::from(*old)) >> SCALE) as i64;", "*slot -= fit((b * i128::from(*old)) >> SCALE, 12);")
s = rep(s, "*slot -= ((i128::from(a) * i128::from(*cur)) >> SCALE) as i64;", "*slot -= fit((i128::from(a) * i128::from(*cur)) >> SCALE, 12);")
s = rep(s, "beta.push(b as i64);", "beta.push(fit(b, 12));")
s = rep(s, "*slot = (*s >> SCALE) as i64;", "*slot = fit(*s >> SCALE, 12);")
s = rep(s, "z.iter().map(|v| *v as i64).collect();", "z.iter().map(|v| fit(*v, 13)).collect();")
s = rep(s, "let energy = i128::from(ground.theta) << bits;", "let energy = shl_i(i128::from(ground.theta), bits, 15);")
s = rep(s, "let residual_units = ((ground.residual << bits) * 1_000_000_000_000) >> SCALE;", "let residual_units = (shl_i(ground.residual, bits, 15) * 1_000_000_000_000) >> SCALE;")
s = rep(s, '        Some("all") => {', """        Some("i_conv729") => {
            for row in conversion_chain(729, q(1, 2), q(4, 27), "4", &[1, 2, 3], time_bits(729), "POLARITON_QUENCH_CONVERSION") {
                println!("{row}");
            }
        }
        Some("i_step729") => {
            let jobs = [(q(1, 2), q(4, 27), "4"), (q(0, 1), q(4, 27), "4"), (q(1, 2), q(1, 27), "1")];
            let rows = parallel(jobs.len(), 3, |i| conversion_chain(729, jobs[i].0, jobs[i].1, jobs[i].2, &[1, 2, 3], time_bits(729) + 2, "POLARITON_QUENCH_CONVERSION"));
            for chain in &rows {
                for row in chain {
                    println!("{row}");
                }
            }
        }
        Some("i_window729") => {
            for row in pin_chain_with(729, q(1, 1), q(-1, 4), 240, window_row) {
                println!("{row}");
            }
        }
        Some("all") => {""")
s = rep(s, '    eprintln!("TIMING|whole|ms={}", start.elapsed().as_millis());', """    for (site, count) in SITES.iter().zip(WRAPS.iter()) {
        println!("WRAP|site={site}|bits_lost_events={}|json=0", count.load(Ordering::Relaxed));
    }
    eprintln!("TIMING|whole|ms={}", start.elapsed().as_millis());""")
os.makedirs(W + "/attack2/src/bin", exist_ok=True)
open(W + "/attack2/Cargo.toml", "w", encoding="utf8", newline="\n").write('[package]\nname = "attack2"\nversion = "0.1.0"\nedition = "2021"\n[dependencies]\n[profile.release]\nopt-level = 3\noverflow-checks = true\n')
open(W + "/attack2/src/bin/inst.rs", "w", encoding="utf8", newline="\n").write(s)
print("INST_WRITTEN")
