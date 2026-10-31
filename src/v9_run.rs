//! `v9`: as sealed in PREREG-V9.hbp. The 3 x 2 Z3 torus with v8's layer 1 and the plaquette-flux
//! correlation layer; seeds IDENTITY and WARM (the sealed v8 models); E0 from the sealed V8.hbp.

use gguf_qnn::bigint::Big;
use gguf_qnn::gguf_model::{self, Kv, Model};
use gguf_qnn::hbp::{index, Hbp};
use gguf_qnn::sha256::hex_digest;
use gguf_qnn::torus::Torus;
use gguf_qnn::v4::{cmp_milli_q, milli_floor_q, StateR};
use gguf_qnn::v6::{b8, TRITS_PER_B};
use gguf_qnn::v8::{LINKS, LX, LY, PARAMS, PER_LAYER};
use gguf_qnn::v9::{train, NetV9};
use std::fs;
use std::path::Path;

const ARCH: &str = "asolaria-qutrit-vqnn-v9";
const LAYER: &str = "layer 1: v8 (R_01, R_02 on every link, flux-free cut SUMs); layer 2: for every plaquette (a,b,c,d): SUM a->b, SUM b->c inverse, SUM c->d, R_01, R_02 on c and d, SUMs undone; a = 6561; b = 2187p0+...+p7";
const V8_HBP_SHA: &str = "f5ab3843f0d25a21c75b7b9ad1426d5f165274e62c82056d4641aa74f94e2501";
const V8_MODELS: [(i64, &str); 3] = [
    (
        9,
        "a75c81e88e98324ab855521ae1a12a209500906b31b675ddc930d7466f5f4ed1",
    ),
    (
        27,
        "1fe5879aedfb4719ed615c1fed23034057c1dbd7f79cebe68d5962b382ef42b7",
    ),
    (
        81,
        "9a957eeb66e1ffaff91fb00c696b82d2d5ec6b216618f6fa3986e82c363dc0fa",
    ),
];

fn get(line: &str, key: &str) -> Option<String> {
    line.split('|')
        .find_map(|kv| kv.strip_prefix(key).and_then(|r| r.strip_prefix('=')))
        .map(str::to_string)
}

fn milli_text(x: Option<i128>) -> String {
    x.map_or("undecided".into(), |t| format!("[{t},{})", t + 1))
}

fn exact(t: &Torus, params: &[i64], r: i64) -> (Vec<Big>, (Big, Big)) {
    let mut s = StateR::zero_state(LINKS);
    NetV9 {
        params: params.to_vec(),
    }
    .forward(&mut s);
    let e = t.energy_exact(&s.v, r).expect("physical");
    (s.v, e)
}

/// certified E0 upper end (milli) at r from the sealed V8.hbp
fn e0_upper(v8: &Path, r: i64) -> i64 {
    let bytes = fs::read(v8.join("V8.hbp")).expect("sealed V8.hbp");
    assert_eq!(hex_digest(&bytes), V8_HBP_SHA, "sealed V8.hbp");
    let text = String::from_utf8(bytes).expect("utf8");
    let row = text
        .lines()
        .find(|l| l.starts_with("Z3MODEL|") && get(l, "r").as_deref() == Some(&r.to_string()))
        .expect("v8 row");
    let e0 = get(row, "certified_E0_in").expect("E0"); // "[23298,23299)_milli"
    e0.trim_start_matches('[')
        .split(',')
        .nth(1)
        .and_then(|x| x.split(')').next())
        .and_then(|x| x.parse().ok())
        .expect("E0 upper")
}

fn warm(v8: &Path, r: i64) -> (Vec<i64>, (Big, Big)) {
    let want = V8_MODELS.iter().find(|x| x.0 == r).expect("sha").1;
    let bytes = fs::read(v8.join(format!("v8-z3-3x2-r{r}-identity.gguf"))).expect("v8 model");
    assert_eq!(hex_digest(&bytes), want, "sealed v8 model");
    let p8: Vec<i64> = gguf_model::read(&bytes)
        .expect("parse")
        .tensor("branch_0.params")
        .expect("p")
        .iter()
        .map(|&x| i64::from(x))
        .collect();
    let t = Torus::new(LX, LY);
    let mut s = StateR::zero_state(LINKS);
    gguf_qnn::v8::NetT { params: p8.clone() }.forward(&mut s);
    let e8 = t.energy_exact(&s.v, r).expect("physical");
    let mut p = p8;
    for x in p.iter_mut().skip(PER_LAYER) {
        *x = 0;
    }
    (p, e8)
}

#[allow(clippy::too_many_lines)]
pub fn run(v8: &Path, out: &Path, sweeps: usize) {
    fs::create_dir_all(out).expect("out");
    let mut rec = Hbp::new();
    let mut files: Vec<(String, usize, String)> = Vec::new();
    let t = Torus::new(LX, LY);
    let (mut p1, mut p2, mut p5, mut p7, mut p9) = (true, true, true, true, true);
    let (mut t7, mut p4, mut p6, mut p8) = (false, true, false, false);
    let mut models: Vec<(String, i64, Option<i128>)> = Vec::new();
    for &r in &[9i64, 27, 81] {
        let e0 = e0_upper(v8, r);
        let mut best: Option<(i128, String, bool, i128)> = None;
        for set in ["IDENTITY", "WARM"] {
            let (seed, e8) = if set == "WARM" {
                let (p, e) = warm(v8, r);
                (p, Some(e))
            } else {
                (vec![0i64; PARAMS], None)
            };
            let (_, start) = exact(&t, &seed, r);
            if let Some(e8) = &e8 {
                p2 &= start.0.mul(&e8.1) == e8.0.mul(&start.1);
            }
            let (params, fixed, evals, used) = train(&t, &seed, r, sweeps);
            let net = NetV9 {
                params: params.clone(),
            };
            let mut s = StateR::zero_state(LINKS);
            let o = s.clone();
            net.forward(&mut s);
            let e = t.energy_exact(&s.v, r).expect("physical");
            let (frac, res) = t.projection_and_residual(&s.v, r, &e);
            let d = s.scale();
            let norm_ok = s.norm_sq() == d.mul(&d);
            net.inverse(&mut s);
            let inv_ok = s.v == o.v.iter().map(|x| x.mul(&d).mul(&d)).collect::<Vec<_>>();
            p1 &= norm_ok && inv_ok;
            let floor = milli_floor_q(&e, 0, 100_000_000);
            let fixed_milli = (fixed * 1000) >> 40;
            p9 &= floor.is_some_and(|f| (f - fixed_milli).abs() <= 1);
            p5 &= cmp_milli_q(&e, i128::from(e0 - 1)) >= 0;
            let l2 = params[PER_LAYER..].iter().any(|&x| x != 0);
            if r == 9 && set == "WARM" {
                p6 = cmp_milli_q(&e, 23_303) < 0;
            }
            if let Some(f) = floor {
                if best.as_ref().map_or(true, |b| f < b.0) {
                    best = Some((f, set.to_string(), l2, res));
                }
            }
            let bs: Vec<String> = params
                .chunks(TRITS_PER_B)
                .map(|p| b8(p).to_string())
                .collect();
            println!(
                "{}",
                rec.row(
                    "Z3MODEL",
                    &[
                        ("r", r.to_string()),
                        ("seed", set.into()),
                        ("params", PARAMS.to_string()),
                        ("sweeps", used.to_string()),
                        ("evaluations", evals.to_string()),
                        (
                            "start_energy_milli_in",
                            milli_text(milli_floor_q(&start, 0, 100_000_000))
                        ),
                        ("certified_E0_in", format!("[{},{})_milli", e0 - 1, e0)),
                        ("energy_milli_in", milli_text(floor)),
                        ("fixed_point_estimate_milli", fixed_milli.to_string()),
                        (
                            "energy_minus_E0_upper_milli_floor",
                            floor.map_or("undecided".into(), |f| (f - i128::from(e0)).to_string())
                        ),
                        ("projection_fraction_permille", frac.to_string()),
                        ("residual_milli", res.to_string()),
                        ("norm_exact", u8::from(norm_ok).to_string()),
                        ("inverse_exact", u8::from(inv_ok).to_string()),
                        ("plaquette_layer_active", u8::from(l2).to_string()),
                        ("b_layer1", bs[..2 * LINKS].join(",")),
                        ("b_layer2", bs[2 * LINKS..].join(",")),
                        ("energy_numerator", e.0.dec()),
                        ("energy_denominator", e.1.dec()),
                    ],
                )
            );
            let name = format!("v9-z3-3x2-r{r}-{}.gguf", set.to_lowercase());
            let kv = vec![
                ("general.architecture".into(), Kv::Str(ARCH.into())),
                ("general.name".into(), Kv::Str(name.clone())),
                ("qnn.layer".into(), Kv::Str(LAYER.into())),
                (
                    "qnn.amplitudes".into(),
                    Kv::Str("real integers over the product of a^2+b^2, exact".into()),
                ),
                ("qnn.layers".into(), Kv::U32(2)),
                ("qnn.branches".into(), Kv::U32(1)),
                (
                    "qnn.task".into(),
                    Kv::Str("variational ground state, Z3 gauge theory, 3x2 torus".into()),
                ),
                ("qnn.seed".into(), Kv::Str(set.into())),
                ("ym.r".into(), Kv::U32(r as u32)),
                (
                    "ym.energy_milli_floor".into(),
                    Kv::Str(floor.map_or("undecided".into(), |f| f.to_string())),
                ),
                ("ym.certified_E0_milli_upper".into(), Kv::U32(e0 as u32)),
            ];
            let bytes = gguf_model::write(&Model {
                kv,
                tensors: vec![(
                    "branch_0.params".into(),
                    params.iter().map(|&x| x as i8).collect(),
                )],
            });
            fs::write(out.join(&name), &bytes).expect("gguf");
            files.push((name.clone(), bytes.len(), hex_digest(&bytes)));
            models.push((name, r, floor));
        }
        let (bf, bset, bl2, bres) = best.expect("best");
        p7 &= bl2;
        if r == 9 {
            t7 = (23_298..23_305).contains(&bf);
            p8 = bres < 2071;
        } else {
            let lim = if r == 27 { 23_780 } else { 23_931 };
            p4 &= bf < lim;
        }
        println!(
            "{}",
            rec.row(
                "BEST",
                &[
                    ("r", r.to_string()),
                    ("seed", bset),
                    ("energy_milli_floor", bf.to_string()),
                    ("residual_milli", bres.to_string())
                ]
            )
        );
    }
    let mut p10 = true;
    for (name, r, floor) in &models {
        let m = gguf_model::read(&fs::read(out.join(name)).expect("reload")).expect("parse");
        let params: Vec<i64> = m
            .tensor("branch_0.params")
            .expect("p")
            .iter()
            .map(|&x| i64::from(x))
            .collect();
        let (_, e) = exact(&t, &params, *r);
        p10 &= milli_floor_q(&e, 0, 100_000_000) == *floor
            && m.str("ym.energy_milli_floor")
                == Some(floor.map_or("undecided".into(), |f| f.to_string()).as_str());
    }
    let verdicts = [
        ("T7", t7, "best_r9_below_23305_and_ge_23298"),
        ("P1", p1, "exact_norm_and_inverse"),
        ("P2", p2, "warm_starts_at_exactly_the_sealed_v8_energy"),
        ("P3", t7, "T7"),
        ("P4", p4, "best_r27_below_23780_and_best_r81_below_23931"),
        ("P5", p5, "every_exact_energy_ge_certified_E0_lower"),
        ("P6", p6, "warm_r9_at_or_below_23302"),
        ("P7", p7, "plaquette_layer_active_in_the_best_model_every_r"),
        ("P8", p8, "best_r9_residual_below_2071_milli"),
        ("P9", p9, "exact_milli_floor_within_1_of_fixed_point"),
        ("P10", p10, "every_model_reloaded_reproduces_its_header"),
    ];
    for (id, pass, measured) in verdicts {
        println!(
            "{}",
            rec.row(
                "VERDICT",
                &[
                    ("id", id.into()),
                    ("measured", measured.into()),
                    ("pass", u8::from(pass).to_string())
                ]
            )
        );
    }
    let text = rec.text();
    fs::write(out.join("V9.hbp"), &text).expect("result");
    files.push(("V9.hbp".into(), text.len(), hex_digest(text.as_bytes())));
    let idx = index("V9INDEX", &files);
    fs::write(out.join("INDEX.hbi"), &idx).expect("index");
    let mut sums = String::new();
    for (f, _, h) in &files {
        sums.push_str(&format!("{h}  {f}\n"));
    }
    sums.push_str(&format!("{}  INDEX.hbi\n", hex_digest(idx.as_bytes())));
    fs::write(out.join("SHA256SUMS"), sums).expect("sums");
    println!("DONE|files={}|json=0", files.len() + 1);
}
