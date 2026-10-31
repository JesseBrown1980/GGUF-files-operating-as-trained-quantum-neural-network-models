//! `v5`: as sealed in PREREG-V5.hbp. Z3 only: six-trit rational rotations on every link,
//! then partner SUMs that carry no flux; five seeds at r = 9, 27, 81.

use gguf_qnn::bigint::Big;
use gguf_qnn::gguf_model::{self, Kv, Model};
use gguf_qnn::hbp::{index, Hbp};
use gguf_qnn::sha256::{digest, hex_digest};
use gguf_qnn::v4::{cmp_milli_q, milli_floor_q, StateR, Z3Orbits};
use gguf_qnn::v5::{b6, train, trits6, NetP, TRITS_PER_B};
use gguf_qnn::ym_z3::LINKS;
use std::fs;
use std::path::Path;

const ARCH: &str = "asolaria-qutrit-vqnn-v5";
const LAYER: &str = "on every link R_01(b), R_02(b'); then SUM 0->4, 2->6, 1->3, 5->7; R_ij(b) = [[a^2-b^2, -2ab], [2ab, a^2-b^2]] on levels i, j and a^2+b^2 on the third; a = 729; b = 243p0+81p1+27p2+9p3+3p4+p5";
const SETS: [&str; 5] = ["STAR", "CLOUD", "SHA", "IDENTITY", "WARM"];
const WARM_B: [(i64, i64); 3] = [(9, 7), (27, 2), (81, 1)];
const V4_PRODUCT_MILLI: [(i64, i128); 3] = [(9, 15_696), (27, 15_901), (81, 15_970)];

fn get(line: &str, key: &str) -> Option<String> {
    line.split('|')
        .find_map(|kv| kv.strip_prefix(key).and_then(|r| r.strip_prefix('=')))
        .map(str::to_string)
}

fn certified_e0_lower(ym: &Path, r: i64) -> i128 {
    let text = fs::read_to_string(ym.join("YM-Z3.hbp")).expect("sealed YM-Z3.hbp");
    let row = text
        .lines()
        .find(|l| l.starts_with("CERTIFIED|") && get(l, "r").as_deref() == Some(&r.to_string()))
        .expect("certified row");
    let e0 = get(row, "E0_in").expect("E0_in");
    let lo = e0.trim_start_matches('[').split(',').next().expect("lo");
    let (a, b) = lo.split_once('.').expect("milli");
    a.parse::<i128>().expect("int") * 1000 + b.parse::<i128>().expect("frac")
}

fn milli_text(x: Option<i128>) -> String {
    x.map_or("undecided".into(), |t| format!("[{t},{})", t + 1))
}

fn energy_of(orbits: &Z3Orbits, params: &[i64], layers: usize, r: i64) -> Option<(Big, Big)> {
    NetP {
        layers,
        params: params.to_vec(),
    }
    .energy(orbits, r)
}

fn warm(r: i64, count: usize) -> Vec<i64> {
    let w = WARM_B.iter().find(|x| x.0 == r).expect("warm b").1;
    let t = trits6(w);
    (0..count).map(|i| t[i % TRITS_PER_B]).collect()
}

fn lookup(table: &[(i64, i128)], r: i64) -> i128 {
    table.iter().find(|x| x.0 == r).expect("r").1
}

#[allow(clippy::too_many_lines)]
pub fn run(stars: &Path, cloud_dir: &Path, ym: &Path, out: &Path, layers: usize, sweeps: usize) {
    fs::create_dir_all(out).expect("out");
    let mut rec = Hbp::new();
    let mut files: Vec<(String, usize, String)> = Vec::new();
    let cloud = fs::read(cloud_dir.join("cloud-star.trits")).expect("cloud star");
    assert_eq!(
        hex_digest(&cloud),
        "73844b0c1e388ceb11fa913b4451badde771d530ef0778fc27c523e5ba9cca32"
    );
    let count = NetP::param_count(layers);
    let (star, _) = crate::star_trits(&stars.join("ACER-MYTHOS-BLUE.gguf"));
    let seeds: Vec<(String, Vec<i64>)> = vec![
        (
            "ACER-MYTHOS-BLUE".into(),
            (0..count)
                .map(|i| star[(i * 4099) % star.len()] - 1)
                .collect(),
        ),
        (
            "CLOUD-STAR@0".into(),
            (0..count)
                .map(|i| i64::from(cloud[i % cloud.len()]) - 1)
                .collect(),
        ),
        (
            "SHA-V5-0".into(),
            (0..count)
                .map(|i| i64::from(digest(format!("V5SEED|0|{i}").as_bytes())[0] % 3) - 1)
                .collect(),
        ),
        ("IDENTITY".into(), vec![0; count]),
        ("WARM-V4-PRODUCT".into(), Vec::new()),
    ];
    let orbits = Z3Orbits::new();
    let (mut z1, mut z2, mut z3, mut z4, mut z7) = (true, true, true, true, true);
    let mut z8 = false;
    let mut models: Vec<(String, i64, Option<i128>)> = Vec::new();
    let mut best9: Option<(i128, &str)> = None;
    let mut best_r: Vec<(i64, i128)> = Vec::new();
    let mut t2_e0 = true;
    for &r in &[9i64, 27, 81] {
        let e0_lo = certified_e0_lower(ym, r);
        for (set, (seed_name, seed0)) in SETS.iter().zip(seeds.iter()) {
            let seed = if *set == "WARM" {
                warm(r, count)
            } else {
                seed0.clone()
            };
            let seed = &seed;
            let start = energy_of(&orbits, seed, layers, r).expect("seed has a physical component");
            let (params, best, evals, sweeps_used) = train(&orbits, seed, layers, r, sweeps);
            let net = NetP {
                layers,
                params: params.clone(),
            };
            let mut s = StateR::zero_state(LINKS);
            let o = s.clone();
            net.forward(&mut s);
            let d = s.scale();
            z1 &= s.norm_sq() == d.mul(&d);
            net.inverse(&mut s);
            z2 &= s.v == o.v.iter().map(|x| x.mul(&d).mul(&d)).collect::<Vec<_>>();
            let exactly16 = best.0 == best.1.mul_i128(16);
            let below16 = cmp_milli_q(&best, 16_000) < 0;
            let above_e0 = cmp_milli_q(&best, e0_lo) >= 0;
            z7 &= above_e0;
            let floor = milli_floor_q(&best, 0, 10_000_000);
            let start_floor = milli_floor_q(&start, 0, 10_000_000);
            if *set == "IDENTITY" {
                z3 &= start.0 == start.1.mul_i128(16);
                if r == 9 {
                    z8 = floor.is_some_and(|t| t < 15_696);
                }
            }
            if *set == "WARM" {
                z4 &= start_floor == Some(lookup(&V4_PRODUCT_MILLI, r));
            }
            if let Some(t) = floor {
                match best_r.iter_mut().find(|x| x.0 == r) {
                    Some(x) => x.1 = x.1.min(t),
                    None => best_r.push((r, t)),
                }
            }
            if r == 9 {
                t2_e0 &= above_e0;
                if let Some(t) = floor {
                    if best9.map_or(true, |(b, _)| t < b) {
                        best9 = Some((t, set));
                    }
                }
            }
            let changed = params
                .iter()
                .zip(seed.iter())
                .filter(|(a, b)| a != b)
                .count();
            let bs: Vec<String> = params
                .chunks(TRITS_PER_B)
                .map(|p| b6(p).to_string())
                .collect();
            println!(
                "{}",
                rec.row(
                    "Z3MODEL",
                    &[
                        ("r", r.to_string()),
                        ("set", (*set).into()),
                        ("seed", seed_name.clone()),
                        ("layers", layers.to_string()),
                        ("params", count.to_string()),
                        ("params_changed_by_training", changed.to_string()),
                        ("sweeps", sweeps_used.to_string()),
                        ("evaluations", evals.to_string()),
                        ("start_energy_milli_in", milli_text(start_floor)),
                        ("energy_milli_in", milli_text(floor)),
                        ("energy_exactly_16", u8::from(exactly16).to_string()),
                        ("energy_lt_16", u8::from(below16).to_string()),
                        ("certified_E0_lower_milli", e0_lo.to_string()),
                        ("energy_ge_certified_E0", u8::from(above_e0).to_string()),
                        ("b_per_link", bs.join(",")),
                        ("energy_numerator", best.0.dec()),
                        ("energy_denominator", best.1.dec()),
                    ],
                )
            );
            let name = format!("v5-z3-r{r}-{}.gguf", set.to_lowercase());
            let kv = vec![
                ("general.architecture".into(), Kv::Str(ARCH.into())),
                ("general.name".into(), Kv::Str(name.clone())),
                ("qnn.layer".into(), Kv::Str(LAYER.into())),
                (
                    "qnn.amplitudes".into(),
                    Kv::Str("real integers over the product of a^2+b^2, exact".into()),
                ),
                ("qnn.seed_set".into(), Kv::Str((*set).into())),
                ("qnn.layers".into(), Kv::U32(layers as u32)),
                ("qnn.branches".into(), Kv::U32(1)),
                (
                    "qnn.task".into(),
                    Kv::Str("variational ground state, Z3 gauge theory, 2x2 torus".into()),
                ),
                ("qnn.seed".into(), Kv::Str(seed_name.clone())),
                ("ym.r".into(), Kv::U32(r as u32)),
                (
                    "ym.energy_milli_floor".into(),
                    Kv::Str(floor.map_or("undecided".into(), |t| t.to_string())),
                ),
                ("ym.certified_E0_milli_lower".into(), Kv::U32(e0_lo as u32)),
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
    }
    let t3 = best9.is_some_and(|(t, _)| t <= 15_420) && t2_e0;
    let b27 = best_r.iter().find(|x| x.0 == 27).map(|x| x.1);
    let b81 = best_r.iter().find(|x| x.0 == 81).map(|x| x.1);
    let z6 = b27.is_some_and(|t| t <= 15_820) && b81.is_some_and(|t| t <= 15_945);
    let z9 = best9.is_some_and(|(_, s)| s == "WARM");

    // Z10: reload every model and recompute its energy
    let mut z10 = true;
    for (name, r, floor) in &models {
        let m = gguf_model::read(&fs::read(out.join(name)).expect("reload")).expect("parse");
        let l = m.u32("qnn.layers").expect("layers") as usize;
        let params: Vec<i64> = m
            .tensor("branch_0.params")
            .expect("p")
            .iter()
            .map(|&x| i64::from(x))
            .collect();
        let again =
            energy_of(&orbits, &params, l, *r).and_then(|e| milli_floor_q(&e, 0, 10_000_000));
        z10 &= again == *floor
            && m.str("ym.energy_milli_floor")
                == Some(floor.map_or("undecided".into(), |t| t.to_string()).as_str());
    }
    let best9_text = best9.map_or("undecided".into(), |(t, s)| format!("{t}_{s}"));
    let opt = |x: Option<i128>| x.map_or("undecided".into(), |t| t.to_string());
    let verdicts = [
        ("T3", t3, format!("best_r9_energy_milli_floor={best9_text}")),
        (
            "Z1",
            z1,
            "norm_sq_equals_scale_squared_every_model".to_string(),
        ),
        (
            "Z2",
            z2,
            "inverse_returns_scale_squared_times_input_every_model".to_string(),
        ),
        (
            "Z3",
            z3,
            "identity_seed_starts_at_exactly_16_at_r_9_27_81".to_string(),
        ),
        (
            "Z4",
            z4,
            "warm_seed_starts_at_15696,15901,15970_milli".to_string(),
        ),
        ("Z5", t3, "T3".to_string()),
        (
            "Z6",
            z6,
            format!(
                "best_r27={}_le_15820,best_r81={}_le_15945",
                opt(b27),
                opt(b81)
            ),
        ),
        (
            "Z7",
            z7,
            "every_trained_energy_ge_certified_E0_lower".to_string(),
        ),
        ("Z8", z8, "trained_identity_r9_below_15696".to_string()),
        ("Z9", z9, format!("best_r9_from_WARM:{best9_text}")),
        ("Z10", z10, format!("models_reloaded={}", models.len())),
    ];
    for (id, pass, measured) in verdicts {
        println!(
            "{}",
            rec.row(
                "VERDICT",
                &[
                    ("id", id.into()),
                    ("measured", measured),
                    ("pass", u8::from(pass).to_string())
                ]
            )
        );
    }
    let text = rec.text();
    fs::write(out.join("V5.hbp"), &text).expect("result");
    files.push(("V5.hbp".into(), text.len(), hex_digest(text.as_bytes())));
    let idx = index("V5INDEX", &files);
    fs::write(out.join("INDEX.hbi"), &idx).expect("index");
    let mut sums = String::new();
    for (f, _, h) in &files {
        sums.push_str(&format!("{h}  {f}\n"));
    }
    sums.push_str(&format!("{}  INDEX.hbi\n", hex_digest(idx.as_bytes())));
    fs::write(out.join("SHA256SUMS"), sums).expect("sums");
    println!("DONE|files={}|json=0", files.len() + 1);
}
