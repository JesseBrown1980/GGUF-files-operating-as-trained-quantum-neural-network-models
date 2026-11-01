//! `v11`: as sealed in PREREG-V11.hbp. The 3 x 3 Z3 torus in the gauge-fixed basis with v10's layers
//! and the tree-frame layer; E0 from the sealed V10.hbp; seeds IDENTITY and WARM (sealed v10 models).

use gguf_qnn::bigint::Big;
use gguf_qnn::gfix::GaugeFixed;
use gguf_qnn::gguf_model::{self, Kv, Model};
use gguf_qnn::hbp::{index, Hbp};
use gguf_qnn::sha256::hex_digest;
use gguf_qnn::v10::{param_count, NetV10};
use gguf_qnn::v11::{params_v11, train, NetV11};
use gguf_qnn::v4::{cmp_milli_q, milli_floor_q, StateR};
use gguf_qnn::v6::{b8, TRITS_PER_B};
use std::fs;
use std::path::Path;

const ARCH: &str = "asolaria-qutrit-vqnn-v11";
const LAYER: &str = "gauge-fixed free links; layer 1: R_01, R_02 on every free link; layer 2: plaquette-flux frames; layer 3: tree-link frames (SUMs put delta_t on one free link, R_01, R_02 there, SUMs undone); a = 6561; b = 2187p0+...+p7";
const V10_HBP_SHA: &str = "4ad4dd427efa598dbee026ad7612ad0d6f91ae9656185c62e40f4a9dd46d7302";
const V10_MODELS: [(i64, &str); 3] = [
    (
        9,
        "726b94036a19cd3f08aa623ddefa3b6cb32e76aa28a5e5ebd59c6c62910b99f8",
    ),
    (
        27,
        "c58a56254fe79a44e44800e3c345dee19c28ff2cbc7199287a1b28a02ed21900",
    ),
    (
        81,
        "4a112bfe2ffab8d60c52589f8454af40dc32e87baf28fe208b1d2ee6ab69fe2c",
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

fn e0_upper(v10: &Path, r: i64) -> i64 {
    let bytes = fs::read(v10.join("V10.hbp")).expect("sealed V10.hbp");
    assert_eq!(hex_digest(&bytes), V10_HBP_SHA, "sealed V10.hbp");
    let text = String::from_utf8(bytes).expect("utf8");
    let row = text
        .lines()
        .find(|l| l.starts_with("Z3MODEL|") && get(l, "r").as_deref() == Some(&r.to_string()))
        .expect("v10 row");
    get(row, "certified_E0_in")
        .and_then(|e| {
            e.split(',')
                .nth(1)
                .and_then(|x| x.split(')').next())
                .and_then(|x| x.parse().ok())
        })
        .expect("E0 upper")
}

fn exact(gf: &GaugeFixed, p: &[i64], r: i64) -> (StateR, (Big, Big)) {
    let mut s = StateR::zero_state(gf.free.len());
    NetV11 { gf, params: p }.forward(&mut s);
    let e = gf.energy_exact(&s.v, r).expect("physical");
    (s, e)
}

#[allow(clippy::too_many_lines)]
pub fn run(v10: &Path, out: &Path, sweeps: usize) {
    fs::create_dir_all(out).expect("out");
    let mut rec = Hbp::new();
    let mut files: Vec<(String, usize, String)> = Vec::new();
    let gf = GaugeFixed::new(3, 3);
    let count = params_v11(&gf);
    let split = param_count(&gf);
    let (mut r1, mut r2, mut r5, mut r7, mut r8) = (true, true, true, true, true);
    let (mut t9, mut r4, mut r6) = (false, true, false);
    let mut models: Vec<(String, i64, Option<i128>)> = Vec::new();
    for &r in &[9i64, 27, 81] {
        let e0 = e0_upper(v10, r);
        let mut best: Option<(i128, String, bool)> = None;
        for set in ["IDENTITY", "WARM"] {
            let seed = if set == "WARM" {
                let want = V10_MODELS.iter().find(|x| x.0 == r).expect("sha").1;
                let bytes = fs::read(v10.join(format!("v10-z3-3x3-r{r}-identity.gguf")))
                    .expect("v10 model");
                assert_eq!(hex_digest(&bytes), want, "sealed v10 model");
                let mut p: Vec<i64> = gguf_model::read(&bytes)
                    .expect("parse")
                    .tensor("branch_0.params")
                    .expect("p")
                    .iter()
                    .map(|&x| i64::from(x))
                    .collect();
                let mut s10 = StateR::zero_state(gf.free.len());
                NetV10 {
                    gf: &gf,
                    params: &p,
                }
                .forward(&mut s10);
                let e10 = gf.energy_exact(&s10.v, r).expect("physical");
                p.extend(std::iter::repeat(0).take(count - split));
                let (_, start) = exact(&gf, &p, r);
                r2 &= start.0.mul(&e10.1) == e10.0.mul(&start.1);
                p
            } else {
                vec![0i64; count]
            };
            let (_, start) = exact(&gf, &seed, r);
            let (params, fixed, evals, used) = train(&gf, &seed, r, sweeps);
            let (mut s, e) = exact(&gf, &params, r);
            let o = StateR::zero_state(gf.free.len());
            let d = s.scale();
            let norm_ok = s.norm_sq() == d.mul(&d);
            NetV11 {
                gf: &gf,
                params: &params,
            }
            .inverse(&mut s);
            let inv_ok = s.v == o.v.iter().map(|x| x.mul(&d).mul(&d)).collect::<Vec<_>>();
            r1 &= norm_ok && inv_ok;
            let floor = milli_floor_q(&e, 0, 100_000_000);
            let fixed_milli = (fixed * 1000) >> 40;
            r8 &= floor.is_some_and(|f| (f - fixed_milli).abs() <= 1);
            r5 &= cmp_milli_q(&e, i128::from(e0 - 1)) >= 0;
            let tree_on = params[split..].iter().any(|&x| x != 0);
            if r == 9 && set == "WARM" {
                r6 = cmp_milli_q(&e, 35_322) < 0;
            }
            if let Some(f) = floor {
                if best.as_ref().map_or(true, |b| f < b.0) {
                    best = Some((f, set.to_string(), tree_on));
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
                        ("torus", "3x3".into()),
                        ("r", r.to_string()),
                        ("seed", set.into()),
                        ("params", count.to_string()),
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
                        ("norm_exact", u8::from(norm_ok).to_string()),
                        ("inverse_exact", u8::from(inv_ok).to_string()),
                        ("tree_layer_active", u8::from(tree_on).to_string()),
                        ("b", bs.join(",")),
                        ("energy_numerator", e.0.dec()),
                        ("energy_denominator", e.1.dec()),
                    ],
                )
            );
            let name = format!("v11-z3-3x3-r{r}-{}.gguf", set.to_lowercase());
            let kv = vec![
                ("general.architecture".into(), Kv::Str(ARCH.into())),
                ("general.name".into(), Kv::Str(name.clone())),
                ("qnn.layer".into(), Kv::Str(LAYER.into())),
                (
                    "qnn.amplitudes".into(),
                    Kv::Str("real integers on the gauge-fixed free links, exact".into()),
                ),
                ("qnn.layers".into(), Kv::U32(3)),
                ("qnn.branches".into(), Kv::U32(1)),
                (
                    "qnn.task".into(),
                    Kv::Str("variational ground state, Z3 gauge theory, 3x3 torus".into()),
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
        let (bf, bset, btree) = best.expect("best");
        r7 &= btree;
        let up = i128::from(e0);
        if r == 9 {
            t9 = bf < 35_309;
        } else {
            r4 &= bf < up + 10;
        }
        println!(
            "{}",
            rec.row(
                "BEST",
                &[
                    ("r", r.to_string()),
                    ("seed", bset),
                    ("energy_milli_floor", bf.to_string()),
                    ("above_E0_upper_milli", (bf - up).to_string())
                ]
            )
        );
    }
    let mut r9 = true;
    for (name, r, floor) in &models {
        let m = gguf_model::read(&fs::read(out.join(name)).expect("reload")).expect("parse");
        let p: Vec<i64> = m
            .tensor("branch_0.params")
            .expect("p")
            .iter()
            .map(|&x| i64::from(x))
            .collect();
        let (_, e) = exact(&gf, &p, *r);
        r9 &= milli_floor_q(&e, 0, 100_000_000) == *floor
            && m.str("ym.energy_milli_floor")
                == Some(floor.map_or("undecided".into(), |f| f.to_string()).as_str());
    }
    let verdicts = [
        ("T9", t9, "best_r9_below_35309"),
        ("R1", r1, "exact_norm_and_inverse"),
        ("R2", r2, "warm_starts_at_exactly_the_sealed_v10_energy"),
        ("R3", t9, "T9"),
        ("R4", r4, "best_r27_r81_within_10_milli"),
        ("R5", r5, "every_exact_energy_ge_certified_E0_lower"),
        ("R6", r6, "warm_r9_at_or_below_35321"),
        ("R7", r7, "tree_layer_active_in_the_best_model_every_r"),
        ("R8", r8, "exact_milli_floor_within_1_of_fixed_point"),
        ("R9", r9, "every_model_reloaded_reproduces_its_header"),
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
    fs::write(out.join("V11.hbp"), &text).expect("result");
    files.push(("V11.hbp".into(), text.len(), hex_digest(text.as_bytes())));
    let idx = index("V11INDEX", &files);
    fs::write(out.join("INDEX.hbi"), &idx).expect("index");
    let mut sums = String::new();
    for (f, _, h) in &files {
        sums.push_str(&format!("{h}  {f}\n"));
    }
    sums.push_str(&format!("{}  INDEX.hbi\n", hex_digest(idx.as_bytes())));
    fs::write(out.join("SHA256SUMS"), sums).expect("sums");
    println!("DONE|files={}|json=0", files.len() + 1);
}
