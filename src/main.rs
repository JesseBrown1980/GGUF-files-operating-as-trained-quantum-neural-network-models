//! gguf-qnn: train qutrit virtual QNNs exactly and store them as GGUF files.
//!   gguf-qnn train STAR_DIR OUT_DIR [LAYERS] [MAX_SWEEPS]
//!   gguf-qnn infer MODEL.gguf X Y
//!   gguf-qnn verify OUT_DIR
//!   gguf-qnn ym-z3 STURMFAST STAR_DIR OUT_DIR [LAYERS]
//!   gguf-qnn v3 STAR_DIR CLOUD_DIR YM_Z3_RESULTS OUT_DIR [CIRCLE_LAYERS] [Z3_LAYERS] [SWEEPS]
//!   gguf-qnn v4 STAR_DIR CLOUD_DIR YM_Z3_RESULTS OUT_DIR [Z3_LAYERS] [SWEEPS]
//!   gguf-qnn v5 STAR_DIR CLOUD_DIR YM_Z3_RESULTS OUT_DIR [Z3_LAYERS] [SWEEPS]
//!   gguf-qnn v6 STAR_DIR CLOUD_DIR YM_Z3_RESULTS V5_RESULTS OUT_DIR [Z3_LAYERS] [SWEEPS]
//!   gguf-qnn v2 STAR_DIR CLOUD_DIR YM_Z3_RESULTS OUT_DIR [CIRCLE_LAYERS] [Z3_LAYERS] [SWEEPS]
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

use gguf_qnn::gguf_model::{self, Kv, Model};
use gguf_qnn::gguf_read;
use gguf_qnn::hbp::{index, Hbp};
use gguf_qnn::qnn::Net;
use gguf_qnn::qutrit::pow3;
use gguf_qnn::sha256::{digest, hex_digest};
use gguf_qnn::task::{correct, encode, margins, points, readout, Point, QUTRITS};
use gguf_qnn::train::train;
use gguf_qnn::virtual_qnn;
use std::fs;
use std::path::Path;

mod v2_run;
mod v3_run;
mod v4_run;
mod v5_run;
mod v6_run;
mod ym_run;

const STARS: [&str; 3] = ["ACER-OPUS-RED", "ACER-FABLE-GREEN", "ACER-MYTHOS-BLUE"];
const ARCH: &str = "asolaria-qutrit-vqnn";

/// Star trits by the Mythos rule (raw F32 bits: 0 -> 0, up to 1.0 -> 1, above -> 2).
pub(crate) fn star_trits(path: &Path) -> (Vec<i64>, String) {
    let raw = fs::read(path).expect("star gguf");
    let g = gguf_read::parse(&raw).expect("parse star");
    let mut t = Vec::new();
    for name in ["slice_A", "slice_B", "slice_C"] {
        let x = g.tensors.iter().find(|x| x.name == name).expect("slice");
        t.extend(x.mags.iter().map(|&w| match w {
            0 => 0,
            1..=0x3F80_0000 => 1,
            _ => 2,
        }));
    }
    (t, hex_digest(&raw))
}

fn seed_from_star(t: &[i64], count: usize) -> Vec<i64> {
    (0..count).map(|i| t[(i * 4099) % t.len()]).collect()
}

fn seed_from_sha(b: usize, count: usize) -> Vec<i64> {
    (0..count)
        .map(|i| i64::from(digest(format!("SEED|{b}|{i}").as_bytes())[0] % 3))
        .collect()
}

fn permille(c: usize, n: usize) -> u32 {
    (c * 1000 / n.max(1)) as u32
}

fn labels(p: &[Point]) -> Vec<u8> {
    p.iter().map(|x| x.label).collect()
}

fn base_kv(name: &str, layers: usize) -> Vec<(String, Kv)> {
    vec![
        ("general.architecture".into(), Kv::Str(ARCH.into())),
        ("general.name".into(), Kv::Str(name.into())),
        (
            "qnn.task".into(),
            Kv::Str("circle-27: label 1 iff (x-13)^2+(y-13)^2 <= 81".into()),
        ),
        ("qnn.qutrits".into(), Kv::U32(QUTRITS as u32)),
        ("qnn.layers".into(), Kv::U32(layers as u32)),
        ("qnn.readout_qutrit".into(), Kv::U32(0)),
        (
            "qnn.layer".into(),
            Kv::Str("F each; diag(1,w^a,w^b) each; SUM ring q->q+1".into()),
        ),
        (
            "qnn.encoding".into(),
            Kv::Str("x,y as 3 base-3 digits each on qutrits 0-2, 3-5".into()),
        ),
        (
            "qnn.class_rule".into(),
            Kv::Str("1 iff sum_b c_b (P_b(0)-P_b(1)) > 0".into()),
        ),
        (
            "qnn.amplitudes".into(),
            Kv::Str("Eisenstein integers over sqrt(3)^k, exact".into()),
        ),
    ]
}

/// Rebuild the branch nets of a model file and recompute its accuracies.
fn evaluate_model(m: &Model) -> (usize, usize) {
    let layers = m.u32("qnn.layers").expect("layers") as usize;
    let nb = m.u32("qnn.branches").expect("branches") as usize;
    let coeff = m.tensor("virtual.coefficients").expect("coefficients");
    let c: Vec<i64> = coeff.iter().map(|&x| i64::from(x)).collect();
    let nets: Vec<Net> = (0..nb)
        .map(|b| Net {
            n: QUTRITS,
            layers,
            params: m
                .tensor(&format!("branch_{b}.params"))
                .expect("params")
                .iter()
                .map(|&x| i64::from(x))
                .collect(),
        })
        .collect();
    let (tr, te) = points();
    let mtr: Vec<Vec<i128>> = nets.iter().map(|n| margins(n, &tr)).collect();
    let mte: Vec<Vec<i128>> = nets.iter().map(|n| margins(n, &te)).collect();
    (
        virtual_qnn::correct(&c, &mtr, &labels(&tr)),
        virtual_qnn::correct(&c, &mte, &labels(&te)),
    )
}

#[allow(clippy::too_many_lines)]
fn cmd_train(star_dir: &Path, out: &Path, layers: usize, max_sweeps: usize) {
    fs::create_dir_all(out).expect("out");
    let mut rec = Hbp::new();
    let (tr, te) = points();
    let ones_tr = tr.iter().filter(|p| p.label == 1).count();
    let ones_te = te.iter().filter(|p| p.label == 1).count();
    let majority_te = ones_te.max(te.len() - ones_te);
    println!(
        "{}",
        rec.row(
            "DATA",
            &[
                ("train", tr.len().to_string()),
                ("train_label1", ones_tr.to_string()),
                ("test", te.len().to_string()),
                ("test_label1", ones_te.to_string()),
                ("test_majority_correct", majority_te.to_string()),
                (
                    "test_majority_permille",
                    permille(majority_te, te.len()).to_string()
                ),
            ],
        )
    );
    let count = Net::param_count(QUTRITS, layers);

    // Q1 / Q2 on the simulator itself
    let mut s = encode(&tr[5]);
    let orig = s.clone();
    for _ in 0..4 {
        s.fourier(2, 1);
    }
    let f4 = s.equals_scaled(&orig, 2) && s.norm_sum() == pow3(s.k);

    let mut files: Vec<(String, usize, String)> = Vec::new();
    let mut set_rows = Vec::new();
    let mut q1 = f4;
    let mut q2 = f4;
    let mut q3 = true;
    for (set, seeds) in [
        (
            "star",
            STARS
                .iter()
                .map(|s| {
                    let (t, h) = star_trits(&star_dir.join(format!("{s}.gguf")));
                    (s.to_string(), h, seed_from_star(&t, count))
                })
                .collect::<Vec<_>>(),
        ),
        (
            "sha",
            (0..3)
                .map(|b| {
                    (
                        format!("SHA-SEED-{b}"),
                        "-".to_string(),
                        seed_from_sha(b, count),
                    )
                })
                .collect::<Vec<_>>(),
        ),
    ] {
        let mut nets = Vec::new();
        let mut best_single_tr = 0;
        let mut best_single_te = 0;
        for (b, (seed_name, seed_sha, seed)) in seeds.iter().enumerate() {
            let t = train(
                Net {
                    n: QUTRITS,
                    layers,
                    params: seed.clone(),
                },
                &tr,
                max_sweeps,
            );
            let mte = margins(&t.net, &te);
            let te_c = correct(&mte, &te);
            best_single_tr = best_single_tr.max(t.train_correct);
            best_single_te = best_single_te.max(te_c);
            q3 &= te_c > majority_te;
            // Q1 and Q2 on this trained net: exact norm, exact inverse, on every test point
            for p in &te {
                let mut s = encode(p);
                let o = s.clone();
                t.net.forward(&mut s);
                q1 &= s.norm_sum() == pow3(s.k);
                t.net.inverse(&mut s);
                q2 &= s.equals_scaled(&o, s.k / 2);
            }
            let changed = t
                .net
                .params
                .iter()
                .zip(seed.iter())
                .filter(|(a, b)| a != b)
                .count();
            println!(
                "{}",
                rec.row(
                    "BRANCH",
                    &[
                        ("set", set.into()),
                        ("branch", b.to_string()),
                        ("seed", seed_name.clone()),
                        ("seed_gguf_sha256", seed_sha.clone()),
                        ("params", count.to_string()),
                        ("params_changed_by_training", changed.to_string()),
                        ("sweeps", t.sweeps.to_string()),
                        ("evaluations", t.evaluations.to_string()),
                        ("train_correct", t.train_correct.to_string()),
                        (
                            "train_permille",
                            permille(t.train_correct, tr.len()).to_string()
                        ),
                        ("test_correct", te_c.to_string()),
                        ("test_permille", permille(te_c, te.len()).to_string()),
                        (
                            "params_trits",
                            t.net.params.iter().map(i64::to_string).collect::<String>()
                        ),
                    ],
                )
            );
            // the branch as its own GGUF model (virtual coefficients = this branch alone)
            let mut kv = base_kv(&format!("{set}-branch-{b}"), layers);
            kv.push(("qnn.seed".into(), Kv::Str(seed_name.clone())));
            kv.push(("qnn.branches".into(), Kv::U32(1)));
            kv.push(("qnn.train_correct".into(), Kv::U32(t.train_correct as u32)));
            kv.push(("qnn.train_total".into(), Kv::U32(tr.len() as u32)));
            kv.push(("qnn.test_correct".into(), Kv::U32(te_c as u32)));
            kv.push(("qnn.test_total".into(), Kv::U32(te.len() as u32)));
            let model = Model {
                kv,
                tensors: vec![
                    (
                        "branch_0.params".into(),
                        t.net.params.iter().map(|&x| x as i8).collect(),
                    ),
                    ("virtual.coefficients".into(), vec![1]),
                ],
            };
            let bytes = gguf_model::write(&model);
            let name = format!("{set}-branch-{b}.gguf");
            fs::write(out.join(&name), &bytes).expect("gguf");
            files.push((name, bytes.len(), hex_digest(&bytes)));
            nets.push(t.net);
        }
        // the virtual combination, c chosen on the training set only
        let mtr: Vec<Vec<i128>> = nets.iter().map(|n| margins(n, &tr)).collect();
        let mte: Vec<Vec<i128>> = nets.iter().map(|n| margins(n, &te)).collect();
        let (c, vtr) = virtual_qnn::choose(&mtr, &labels(&tr));
        let vte = virtual_qnn::correct(&c, &mte, &labels(&te));
        let overhead: i64 = c.iter().map(|x| x.abs()).sum();
        println!(
            "{}",
            rec.row(
                "VIRTUAL",
                &[
                    ("set", set.into()),
                    (
                        "c",
                        c.iter().map(i64::to_string).collect::<Vec<_>>().join(",")
                    ),
                    ("overhead", overhead.to_string()),
                    ("train_correct", vtr.to_string()),
                    ("train_permille", permille(vtr, tr.len()).to_string()),
                    ("test_correct", vte.to_string()),
                    ("test_permille", permille(vte, te.len()).to_string()),
                    ("best_single_train_correct", best_single_tr.to_string()),
                    ("best_single_test_correct", best_single_te.to_string()),
                ],
            )
        );
        let mut kv = base_kv(&format!("{set}-virtual"), layers);
        kv.push(("qnn.branches".into(), Kv::U32(nets.len() as u32)));
        kv.push(("qnn.overhead".into(), Kv::U32(overhead as u32)));
        kv.push(("qnn.train_correct".into(), Kv::U32(vtr as u32)));
        kv.push(("qnn.train_total".into(), Kv::U32(tr.len() as u32)));
        kv.push(("qnn.test_correct".into(), Kv::U32(vte as u32)));
        kv.push(("qnn.test_total".into(), Kv::U32(te.len() as u32)));
        for (b, (seed_name, _, _)) in seeds.iter().enumerate() {
            kv.push((format!("qnn.branch_{b}.seed"), Kv::Str(seed_name.clone())));
        }
        let mut tensors: Vec<(String, Vec<i8>)> = nets
            .iter()
            .enumerate()
            .map(|(b, n)| {
                (
                    format!("branch_{b}.params"),
                    n.params.iter().map(|&x| x as i8).collect(),
                )
            })
            .collect();
        tensors.push((
            "virtual.coefficients".into(),
            c.iter().map(|&x| x as i8).collect(),
        ));
        let bytes = gguf_model::write(&Model { kv, tensors });
        let name = format!("{set}-virtual.gguf");
        fs::write(out.join(&name), &bytes).expect("gguf");
        files.push((name, bytes.len(), hex_digest(&bytes)));
        set_rows.push((set, vtr, vte, best_single_tr, best_single_te));
    }

    // Q7: every model reloaded from its bytes reproduces its header
    let mut q7 = true;
    for (name, _, _) in &files {
        let m = gguf_model::read(&fs::read(out.join(name)).expect("reload")).expect("parse model");
        let (a, b) = evaluate_model(&m);
        q7 &= a == m.u32("qnn.train_correct").expect("tc") as usize
            && b == m.u32("qnn.test_correct").expect("tc") as usize;
    }
    let star = set_rows[0];
    let sha = set_rows[1];
    let q4 = set_rows.iter().all(|r| r.1 >= r.3);
    let q5 = set_rows.iter().all(|r| r.2 >= r.4);
    let best_te = |r: &(&str, usize, usize, usize, usize)| r.2.max(r.4);
    let gap = (permille(best_te(&star), te.len()) as i64
        - permille(best_te(&sha), te.len()) as i64)
        .abs();
    let q6 = gap <= 50;
    for (id, pass, measured) in [
        (
            "Q1",
            q1,
            "norm_sum_eq_3_pow_k_every_trained_branch_every_test_point".to_string(),
        ),
        (
            "Q2",
            q2,
            "F4_eq_identity_and_inverse_restores_every_test_point".to_string(),
        ),
        ("Q3", q3, format!("test_majority_correct={majority_te}")),
        (
            "Q4",
            q4,
            format!("star {}>={} sha {}>={}", star.1, star.3, sha.1, sha.3),
        ),
        (
            "Q5",
            q5,
            format!("star {}>={} sha {}>={}", star.2, star.4, sha.2, sha.4),
        ),
        ("Q6", q6, format!("best_test_permille_gap={gap}")),
        ("Q7", q7, format!("models_reloaded={}", files.len())),
    ] {
        println!(
            "{}",
            rec.row(
                "VERDICT",
                &[
                    ("id", id.into()),
                    ("measured", measured.replace(' ', "_")),
                    ("pass", u8::from(pass).to_string())
                ]
            )
        );
    }
    let text = rec.text();
    fs::write(out.join("RESULT.hbp"), &text).expect("result");
    files.push(("RESULT.hbp".into(), text.len(), hex_digest(text.as_bytes())));
    let idx = index("MODELINDEX", &files);
    fs::write(out.join("INDEX.hbi"), &idx).expect("index");
    let mut sums = String::new();
    for (f, _, h) in &files {
        sums.push_str(&format!("{h}  {f}\n"));
    }
    sums.push_str(&format!("{}  INDEX.hbi\n", hex_digest(idx.as_bytes())));
    fs::write(out.join("SHA256SUMS"), sums).expect("sums");
    println!("DONE|files={}|json=0", files.len() + 1);
}

fn cmd_infer(model: &Path, x: usize, y: usize) {
    let m = gguf_model::read(&fs::read(model).expect("model")).expect("parse model");
    let layers = m.u32("qnn.layers").expect("layers") as usize;
    let nb = m.u32("qnn.branches").expect("branches") as usize;
    let c = m.tensor("virtual.coefficients").expect("coefficients");
    let (dx, dy) = (x as i64 - 13, y as i64 - 13);
    let p = Point {
        x,
        y,
        label: u8::from(dx * dx + dy * dy <= 81),
    };
    let mut score = 0i128;
    let mut h = Hbp::new();
    for (b, &cb) in c.iter().enumerate().take(nb) {
        let params: Vec<i64> = m
            .tensor(&format!("branch_{b}.params"))
            .expect("params")
            .iter()
            .map(|&v| i64::from(v))
            .collect();
        let net = Net {
            n: QUTRITS,
            layers,
            params,
        };
        let (pr, k) = readout(&net, &p);
        score += i128::from(cb) * (pr[0] - pr[1]);
        h.row(
            "BRANCH",
            &[
                ("b", b.to_string()),
                ("c", cb.to_string()),
                ("P0", format!("{}/3^{k}", pr[0])),
                ("P1", format!("{}/3^{k}", pr[1])),
                ("P2", format!("{}/3^{k}", pr[2])),
            ],
        );
    }
    h.row(
        "INFER",
        &[
            ("model", m.str("general.name").unwrap_or("?").into()),
            ("x", x.to_string()),
            ("y", y.to_string()),
            ("score_numerator", score.to_string()),
            ("class", u8::from(score > 0).to_string()),
            ("label", p.label.to_string()),
        ],
    );
    print!("{}", h.text());
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    match a.get(1).map(String::as_str) {
        Some("train") if a.len() >= 4 => {
            let layers = a.get(4).and_then(|v| v.parse().ok()).unwrap_or(3);
            let sweeps = a.get(5).and_then(|v| v.parse().ok()).unwrap_or(4);
            cmd_train(Path::new(&a[2]), Path::new(&a[3]), layers, sweeps);
        }
        Some("v6") if a.len() >= 7 => {
            let zl = a.get(7).and_then(|v| v.parse().ok()).unwrap_or(1);
            let sw = a.get(8).and_then(|v| v.parse().ok()).unwrap_or(8);
            v6_run::run(
                Path::new(&a[2]),
                Path::new(&a[3]),
                Path::new(&a[4]),
                Path::new(&a[5]),
                Path::new(&a[6]),
                zl,
                sw,
            );
        }
        Some("v5") if a.len() >= 6 => {
            let zl = a.get(6).and_then(|v| v.parse().ok()).unwrap_or(1);
            let sw = a.get(7).and_then(|v| v.parse().ok()).unwrap_or(8);
            v5_run::run(
                Path::new(&a[2]),
                Path::new(&a[3]),
                Path::new(&a[4]),
                Path::new(&a[5]),
                zl,
                sw,
            );
        }
        Some("v4") if a.len() >= 6 => {
            let zl = a.get(6).and_then(|v| v.parse().ok()).unwrap_or(2);
            let sw = a.get(7).and_then(|v| v.parse().ok()).unwrap_or(4);
            v4_run::run(
                Path::new(&a[2]),
                Path::new(&a[3]),
                Path::new(&a[4]),
                Path::new(&a[5]),
                zl,
                sw,
            );
        }
        Some("v3") if a.len() >= 6 => {
            let cl = a.get(6).and_then(|v| v.parse().ok()).unwrap_or(2);
            let zl = a.get(7).and_then(|v| v.parse().ok()).unwrap_or(2);
            let sw = a.get(8).and_then(|v| v.parse().ok()).unwrap_or(4);
            v3_run::run(
                Path::new(&a[2]),
                Path::new(&a[3]),
                Path::new(&a[4]),
                Path::new(&a[5]),
                cl,
                zl,
                sw,
            );
        }
        Some("v2") if a.len() >= 6 => {
            let cl = a.get(6).and_then(|v| v.parse().ok()).unwrap_or(3);
            let zl = a.get(7).and_then(|v| v.parse().ok()).unwrap_or(2);
            let sw = a.get(8).and_then(|v| v.parse().ok()).unwrap_or(4);
            v2_run::run(
                Path::new(&a[2]),
                Path::new(&a[3]),
                Path::new(&a[4]),
                Path::new(&a[5]),
                cl,
                zl,
                sw,
            );
        }
        Some("ym-z3") if a.len() >= 5 => {
            let layers = a.get(5).and_then(|v| v.parse().ok()).unwrap_or(2);
            ym_run::run(Path::new(&a[2]), Path::new(&a[3]), Path::new(&a[4]), layers);
        }
        Some("infer") if a.len() == 5 => {
            cmd_infer(
                Path::new(&a[2]),
                a[3].parse().expect("x"),
                a[4].parse().expect("y"),
            );
        }
        Some("verify") if a.len() == 3 => {
            let dir = Path::new(&a[2]);
            let mut names: Vec<_> = fs::read_dir(dir)
                .expect("dir")
                .filter_map(|e| e.ok().map(|e| e.file_name().to_string_lossy().into_owned()))
                .filter(|n| n.ends_with(".gguf"))
                .collect();
            names.sort();
            for n in names {
                let m = gguf_model::read(&fs::read(dir.join(&n)).expect("read")).expect("parse");
                let (tr, te) = evaluate_model(&m);
                let ok = Some(tr as u32) == m.u32("qnn.train_correct")
                    && Some(te as u32) == m.u32("qnn.test_correct");
                println!("VERIFY|model={n}|train_correct={tr}|test_correct={te}|matches_header={}|json=0", u8::from(ok));
            }
        }
        _ => {
            eprintln!("usage: gguf-qnn train STAR_DIR OUT_DIR [LAYERS] [MAX_SWEEPS] | infer MODEL X Y | verify OUT_DIR");
            std::process::exit(2);
        }
    }
}
