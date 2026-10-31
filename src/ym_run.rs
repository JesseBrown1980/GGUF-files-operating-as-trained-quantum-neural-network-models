//! `ym-z3`: the qutrit model on the Z3 sector, certified by HEB-C's sturmfast.

use gguf_qnn::gguf_model::{self, Kv, Model};
use gguf_qnn::hbp::{index, Hbp};
use gguf_qnn::qnn::Net;
use gguf_qnn::qutrit::State;
use gguf_qnn::sha256::{digest, hex_digest};
use gguf_qnn::ym_z3::{energy, less, physical, sturm_matrix, LINKS};
use std::fs;
use std::path::Path;
use std::process::Command;

const RS: [i64; 3] = [9, 27, 81];

fn get(line: &str, key: &str) -> Option<String> {
    line.split('|')
        .find_map(|kv| kv.strip_prefix(key).and_then(|r| r.strip_prefix('=')))
        .map(str::to_string)
}

/// Eigenvalues strictly below t/1000 (J_E = 1, J_B = r), certified; panics if undecided.
fn below(sturm: &Path, mat: &Path, r: i64, t: i64, calls: &mut usize) -> usize {
    *calls += 1;
    let out = Command::new(sturm)
        .arg(mat)
        .arg("1")
        .arg(r.to_string())
        .arg(t.to_string())
        .output()
        .expect("run sturmfast");
    let text = String::from_utf8_lossy(&out.stdout);
    let line = text
        .lines()
        .find(|l| l.starts_with("STURM-FAST|"))
        .expect("sturmfast line");
    assert_eq!(get(line, "status").as_deref(), Some("COMPLETE"), "{line}");
    assert_eq!(get(line, "ambiguous").as_deref(), Some("0"), "{line}");
    get(line, "negative")
        .and_then(|v| v.parse().ok())
        .expect("negative")
}

/// Smallest t (milli J_E) with at least k+1 eigenvalues below it: E_k in [(t-1)/1000, t/1000).
fn level(sturm: &Path, mat: &Path, r: i64, k: usize, hi0: i64, calls: &mut usize) -> i64 {
    let (mut lo, mut hi) = (0i64, hi0);
    assert!(below(sturm, mat, r, hi, calls) > k);
    while hi - lo > 1 {
        let mid = (lo + hi) / 2;
        if below(sturm, mat, r, mid, calls) > k {
            hi = mid;
        } else {
            lo = mid;
        }
    }
    hi
}

fn train_energy(
    seed: Vec<i64>,
    layers: usize,
    r: i64,
    sweeps: usize,
) -> (Net, (i128, i128), usize) {
    let eval = |net: &Net| {
        let mut s = State::basis(LINKS, &[0; LINKS]);
        net.forward(&mut s);
        energy(&s, r)
    };
    let mut net = Net {
        n: LINKS,
        layers,
        params: seed,
    };
    let mut best = eval(&net).unwrap_or((i128::MAX / 4, 1));
    let mut evals = 1;
    for _ in 0..sweeps {
        let mut changed = false;
        for i in 0..net.params.len() {
            let keep = net.params[i];
            let mut best_v = keep;
            for v in 0..3 {
                if v == keep {
                    continue;
                }
                net.params[i] = v;
                evals += 1;
                if let Some(e) = eval(&net) {
                    if less(e, best) {
                        best = e;
                        best_v = v;
                    }
                }
            }
            net.params[i] = best_v;
            changed |= best_v != keep;
        }
        if !changed {
            break;
        }
    }
    (net, best, evals)
}

fn milli_str(t: i64) -> String {
    format!("{}.{:03}", t.div_euclid(1000), t.rem_euclid(1000))
}

#[allow(clippy::too_many_lines)]
pub fn run(sturm: &Path, stars: &Path, out: &Path, layers: usize) {
    fs::create_dir_all(out).expect("out");
    let mut rec = Hbp::new();
    let mut files: Vec<(String, usize, String)> = Vec::new();
    let p = physical();
    let dim = p.reps.len();
    let all27 = p.sizes.iter().all(|&s| s == 27);
    let flat = p.mag.iter().filter(|&&m| m == 0).count();
    let mat_text = sturm_matrix(&p);
    let mat = out.join("z3-2x2.mat");
    fs::write(&mat, &mat_text).expect("matrix");
    files.push((
        "z3-2x2.mat".into(),
        mat_text.len(),
        hex_digest(mat_text.as_bytes()),
    ));
    let min_two = p.mag.iter().filter(|&&m| m > 0).min().copied().unwrap_or(0);
    println!(
        "{}",
        rec.row(
            "PHYSICAL",
            &[
                ("lattice", "2x2_torus".into()),
                ("links", LINKS.to_string()),
                ("configurations", "6561".into()),
                ("gauge_orbits", dim.to_string()),
                ("every_orbit_size_27", u8::from(all27).to_string()),
                ("flat_orbits", flat.to_string()),
                ("smallest_nonzero_M", min_two.to_string()),
                ("electric_upper_entries", p.electric.len().to_string()),
                ("matrix_sha256", hex_digest(mat_text.as_bytes())),
            ],
        )
    );
    let mut calls = 0usize;
    let mut z = [true; 6];
    z[0] = dim == 243 && all27;
    let (mythos, _) = crate::star_trits(&stars.join("ACER-MYTHOS-BLUE.gguf"));
    let count = Net::param_count(LINKS, layers);
    // reference states, not trained: |0..0> projected (the trivial flat orbit) and F on every qutrit
    for &r in &RS {
        let zero = State::basis(LINKS, &[0; LINKS]);
        let mut plus = zero.clone();
        for q in 0..LINKS {
            plus.fourier(q, 1);
        }
        let ez = energy(&zero, r).expect("zero");
        let ep = energy(&plus, r).expect("plus");
        let (gz, gp) = (gcd(ez.0, ez.1), gcd(ep.0, ep.1));
        println!(
            "{}",
            rec.row(
                "REFERENCE",
                &[
                    ("r", r.to_string()),
                    (
                        "energy_trivial_flat_orbit",
                        format!("{}/{}", ez.0 / gz, ez.1 / gz)
                    ),
                    (
                        "energy_F_on_every_link",
                        format!("{}/{}", ep.0 / gp, ep.1 / gp)
                    ),
                ],
            )
        );
    }
    for &r in &RS {
        let c15 = below(sturm, &mat, r, 15_000, &mut calls);
        let c16 = below(sturm, &mat, r, 16_000, &mut calls);
        let c3r = below(sturm, &mat, r, (16 + 3 * r) * 1000, &mut calls);
        let c6m = below(sturm, &mat, r, (16 + 6 * r - 12) * 1000, &mut calls);
        let c6 = below(sturm, &mat, r, (16 + 6 * r) * 1000, &mut calls);
        let top = (16 + 6 * r + 40) * 1000;
        let e0 = level(sturm, &mat, r, 0, top, &mut calls);
        let e8 = level(sturm, &mat, r, 8, top, &mut calls);
        let e9 = level(sturm, &mat, r, 9, top, &mut calls);
        z[1] &= c3r == 9;
        z[2] &= c6m == 9;
        z[3] &= c6 >= 10;
        z[4] &= c15 == 0 && c16 == 9;
        // gap E9 - E8 bracket in milli: E9 in [e9-1, e9), E8 in [e8-1, e8)
        let gap_lo = (e9 - 1) - e8;
        let gap_hi = e9 - (e8 - 1);
        println!(
            "{}",
            rec.row(
                "CERTIFIED",
                &[
                    ("r", r.to_string()),
                    ("below_15", c15.to_string()),
                    ("below_16", c16.to_string()),
                    ("below_16+3r", c3r.to_string()),
                    ("below_16+6r-12", c6m.to_string()),
                    ("below_16+6r", c6.to_string()),
                    (
                        "E0_in",
                        format!("[{},{})", milli_str(e0 - 1), milli_str(e0))
                    ),
                    (
                        "E8_in",
                        format!("[{},{})", milli_str(e8 - 1), milli_str(e8))
                    ),
                    (
                        "E9_in",
                        format!("[{},{})", milli_str(e9 - 1), milli_str(e9))
                    ),
                    (
                        "gap_E9_minus_E8_in",
                        format!("({},{})", milli_str(gap_lo), milli_str(gap_hi))
                    ),
                    (
                        "gap_minus_6r_in",
                        format!(
                            "({},{})",
                            milli_str(gap_lo - 6000 * r),
                            milli_str(gap_hi - 6000 * r)
                        )
                    ),
                ],
            )
        );
        // the trained models
        for (seed_name, seed) in [
            (
                "ACER-MYTHOS-BLUE",
                (0..count)
                    .map(|i| mythos[(i * 4099) % mythos.len()])
                    .collect::<Vec<_>>(),
            ),
            (
                "SHA-SEED",
                (0..count)
                    .map(|i| i64::from(digest(format!("YM|{r}|{i}").as_bytes())[0] % 3))
                    .collect(),
            ),
        ] {
            let (net, en, evals) = train_energy(seed, layers, r, 4);
            let exactly16 = en.0 == 16 * en.1;
            // above the certified ground energy: en >= (e0 - 1)/1000
            let above_e0 = en.0 * 1000 >= i128::from(e0 - 1) * en.1;
            z[5] &= exactly16 && above_e0;
            let g = gcd(en.0, en.1);
            println!(
                "{}",
                rec.row(
                    "MODEL",
                    &[
                        ("r", r.to_string()),
                        ("seed", seed_name.into()),
                        ("layers", layers.to_string()),
                        ("params", count.to_string()),
                        ("evaluations", evals.to_string()),
                        ("energy", format!("{}/{}", en.0 / g, en.1 / g)),
                        ("energy_equals_16", u8::from(exactly16).to_string()),
                        ("energy_ge_certified_E0", u8::from(above_e0).to_string()),
                        (
                            "params_trits",
                            net.params.iter().map(i64::to_string).collect::<String>()
                        ),
                    ],
                )
            );
            let model = Model {
                kv: vec![
                    (
                        "general.architecture".into(),
                        Kv::Str("asolaria-qutrit-vqnn".into()),
                    ),
                    (
                        "general.name".into(),
                        Kv::Str(format!("ym-z3-2x2-r{r}-{seed_name}")),
                    ),
                    (
                        "qnn.task".into(),
                        Kv::Str("variational ground state, Z3 gauge theory, 2x2 torus".into()),
                    ),
                    (
                        "qnn.hamiltonian".into(),
                        Kv::Str("H = E + r*M, E = sum(2 - X - X^dag), M = 3*[h_p != 0]".into()),
                    ),
                    ("qnn.qutrits".into(), Kv::U32(LINKS as u32)),
                    ("qnn.layers".into(), Kv::U32(layers as u32)),
                    ("qnn.branches".into(), Kv::U32(1)),
                    ("ym.r".into(), Kv::U32(r as u32)),
                    (
                        "ym.energy".into(),
                        Kv::Str(format!("{}/{}", en.0 / g, en.1 / g)),
                    ),
                    (
                        "ym.certified_E0_milli_lower".into(),
                        Kv::U32((e0 - 1) as u32),
                    ),
                    ("ym.certified_E0_milli_upper".into(), Kv::U32(e0 as u32)),
                ],
                tensors: vec![
                    (
                        "branch_0.params".into(),
                        net.params.iter().map(|&x| x as i8).collect(),
                    ),
                    ("virtual.coefficients".into(), vec![1]),
                ],
            };
            let bytes = gguf_model::write(&model);
            let name = format!("ym-z3-r{r}-{}.gguf", seed_name.to_lowercase());
            fs::write(out.join(&name), &bytes).expect("gguf");
            files.push((name, bytes.len(), hex_digest(&bytes)));
        }
    }
    let ids = ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6"];
    for (id, pass) in ids.iter().zip(z.iter()) {
        println!(
            "{}",
            rec.row(
                "VERDICT",
                &[("id", (*id).into()), ("pass", u8::from(*pass).to_string())]
            )
        );
    }
    println!(
        "{}",
        rec.row("CALLS", &[("sturmfast_calls", calls.to_string())])
    );
    let text = rec.text();
    fs::write(out.join("YM-Z3.hbp"), &text).expect("result");
    files.push(("YM-Z3.hbp".into(), text.len(), hex_digest(text.as_bytes())));
    let idx = index("YMZ3INDEX", &files);
    fs::write(out.join("INDEX.hbi"), &idx).expect("index");
    let mut sums = String::new();
    for (f, _, h) in &files {
        sums.push_str(&format!("{h}  {f}\n"));
    }
    sums.push_str(&format!("{}  INDEX.hbi\n", hex_digest(idx.as_bytes())));
    fs::write(out.join("SHA256SUMS"), sums).expect("sums");
    println!("DONE|files={}|json=0", files.len() + 1);
}

fn gcd(a: i128, b: i128) -> i128 {
    let (mut a, mut b) = (a.abs(), b.abs());
    while b != 0 {
        let t = a % b;
        a = b;
        b = t;
    }
    a.max(1)
}
