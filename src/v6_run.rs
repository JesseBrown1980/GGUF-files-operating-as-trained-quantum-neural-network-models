//! `v6`: as sealed in PREREG-V6.hbp. The v5 network on a 9x finer angle grid: a = 6561,
//! eight trits per angle; five seeds at r = 9, 27, 81, WARM from the sealed v5 models.

use gguf_qnn::bigint::Big;
use gguf_qnn::gguf_model::{self, Kv, Model};
use gguf_qnn::hbp::{index, Hbp};
use gguf_qnn::sha256::{digest, hex_digest};
use gguf_qnn::v4::{cmp_milli_q, milli_floor_q, StateR, Z3Orbits};
use gguf_qnn::v5::{b6, NetP};
use gguf_qnn::v6::{b8, train, trits8, NetP6, TRITS_PER_B};
use gguf_qnn::ym_z3::LINKS;
use std::fs;
use std::path::Path;

const ARCH: &str = "asolaria-qutrit-vqnn-v6";
const LAYER: &str = "on every link R_01(b), R_02(b'); then SUM 0->4, 2->6, 1->3, 5->7; R_ij(b) = [[a^2-b^2, -2ab], [2ab, a^2-b^2]] on levels i, j and a^2+b^2 on the third; a = 6561; b = 2187p0+729p1+243p2+81p3+27p4+9p5+3p6+p7";
const SETS: [&str; 5] = ["STAR", "CLOUD", "SHA", "IDENTITY", "WARM"];
const WARM_SHA: [(i64, &str); 3] = [
    (
        9,
        "33cd99d104aca3ca9f756ac2fab4b9f3248c1f71263b910414a107ac158aeccd",
    ),
    (
        27,
        "09dcc66fd5f5521036907c8858828f1a91e1c376a4aa6006723787e99226a4f8",
    ),
    (
        81,
        "8326c475d696487945593592587fdaa3e946ac7870f6086b3a0631965d7b6b7b",
    ),
];

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
    NetP6 {
        layers,
        params: params.to_vec(),
    }
    .energy(orbits, r)
}

/// The sealed v5 IDENTITY model at r: its v5 params, and the same angles as v6 params (b * 9).
fn warm(v5: &Path, r: i64) -> (Vec<i64>, Vec<i64>) {
    let bytes = fs::read(v5.join(format!("v5-z3-r{r}-identity.gguf"))).expect("v5 model");
    let want = WARM_SHA.iter().find(|x| x.0 == r).expect("sha").1;
    assert_eq!(hex_digest(&bytes), want, "sealed v5 model");
    let m = gguf_model::read(&bytes).expect("parse v5");
    let p5: Vec<i64> = m
        .tensor("branch_0.params")
        .expect("p")
        .iter()
        .map(|&x| i64::from(x))
        .collect();
    let p6: Vec<i64> = p5
        .chunks(6)
        .flat_map(|c| trits8(9 * i64::try_from(b6(c)).expect("b")))
        .collect();
    (p5, p6)
}

#[allow(clippy::too_many_lines)]
pub fn run(
    stars: &Path,
    cloud_dir: &Path,
    ym: &Path,
    v5: &Path,
    out: &Path,
    layers: usize,
    sweeps: usize,
) {
    fs::create_dir_all(out).expect("out");
    let mut rec = Hbp::new();
    let mut files: Vec<(String, usize, String)> = Vec::new();
    let cloud = fs::read(cloud_dir.join("cloud-star.trits")).expect("cloud star");
    assert_eq!(
        hex_digest(&cloud),
        "73844b0c1e388ceb11fa913b4451badde771d530ef0778fc27c523e5ba9cca32"
    );
    let count = NetP6::param_count(layers);
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
            "SHA-V6-0".into(),
            (0..count)
                .map(|i| i64::from(digest(format!("V6SEED|0|{i}").as_bytes())[0] % 3) - 1)
                .collect(),
        ),
        ("IDENTITY".into(), vec![0; count]),
        ("WARM-V5-IDENTITY".into(), Vec::new()),
    ];
    let orbits = Z3Orbits::new();
    let (mut z1, mut z2, mut z3, mut z4, mut z7, mut z8) = (true, true, true, true, true, true);
    let mut models: Vec<(String, i64, Option<i128>)> = Vec::new();
    let mut best_r: Vec<(i64, i128)> = Vec::new();
    for &r in &[9i64, 27, 81] {
        let e0_lo = certified_e0_lower(ym, r);
        for (set, (seed_name, seed0)) in SETS.iter().zip(seeds.iter()) {
            let (p5, wp) = warm(v5, r);
            let seed = if *set == "WARM" { wp } else { seed0.clone() };
            let seed = &seed;
            let start = energy_of(&orbits, seed, layers, r).expect("seed has a physical component");
            let (params, best, evals, sweeps_used) = train(&orbits, seed, layers, r, sweeps);
            let net = NetP6 {
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
            }
            if *set == "WARM" {
                let e5 = NetP {
                    layers: 1,
                    params: p5.clone(),
                }
                .energy(&orbits, r)
                .expect("v5 energy");
                z4 &= start.0.mul(&e5.1) == e5.0.mul(&start.1);
            }
            if *set == "STAR" {
                z8 &= cmp_milli_q(&best, 16_000) > 0;
            }
            if let Some(t) = floor {
                match best_r.iter_mut().find(|x| x.0 == r) {
                    Some(x) => x.1 = x.1.min(t),
                    None => best_r.push((r, t)),
                }
            }
            let changed = params
                .iter()
                .zip(seed.iter())
                .filter(|(a, b)| a != b)
                .count();
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
            let name = format!("v6-z3-r{r}-{}.gguf", set.to_lowercase());
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
    let b9 = best_r.iter().find(|x| x.0 == 9).map(|x| x.1);
    let b27 = best_r.iter().find(|x| x.0 == 27).map(|x| x.1);
    let b81 = best_r.iter().find(|x| x.0 == 81).map(|x| x.1);
    let t4 = b81.is_some_and(|t| (15_933..=15_937).contains(&t)) && z7;
    let z6 = b9.is_some_and(|t| t <= 15_384) && b27.is_some_and(|t| t <= 15_802);

    // V9: reload every model and recompute its energy
    let mut z9 = true;
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
        z9 &= again == *floor
            && m.str("ym.energy_milli_floor")
                == Some(floor.map_or("undecided".into(), |t| t.to_string()).as_str());
    }
    let opt = |x: Option<i128>| x.map_or("undecided".into(), |t| t.to_string());
    let verdicts = [
        (
            "T4",
            t4,
            format!("best_r81_energy_milli_floor={}", opt(b81)),
        ),
        (
            "V1",
            z1,
            "norm_sq_equals_scale_squared_every_model".to_string(),
        ),
        (
            "V2",
            z2,
            "inverse_returns_scale_squared_times_input_every_model".to_string(),
        ),
        (
            "V3",
            z3,
            "identity_seed_starts_at_exactly_16_at_r_9_27_81".to_string(),
        ),
        (
            "V4",
            z4,
            "warm_start_equals_the_sealed_v5_identity_energy_exactly".to_string(),
        ),
        ("V5", t4, "T4".to_string()),
        (
            "V6",
            z6,
            format!(
                "best_r9={}_le_15384,best_r27={}_le_15802",
                opt(b9),
                opt(b27)
            ),
        ),
        (
            "V7",
            z7,
            "every_trained_energy_ge_certified_E0_lower".to_string(),
        ),
        ("V8", z8, "star_seed_above_16_at_r_9_27_81".to_string()),
        ("V9", z9, format!("models_reloaded={}", models.len())),
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
    fs::write(out.join("V6.hbp"), &text).expect("result");
    files.push(("V6.hbp".into(), text.len(), hex_digest(text.as_bytes())));
    let idx = index("V6INDEX", &files);
    fs::write(out.join("INDEX.hbi"), &idx).expect("index");
    let mut sums = String::new();
    for (f, _, h) in &files {
        sums.push_str(&format!("{h}  {f}\n"));
    }
    sums.push_str(&format!("{}  INDEX.hbi\n", hex_digest(idx.as_bytes())));
    fs::write(out.join("SHA256SUMS"), sums).expect("sums");
    println!("DONE|files={}|json=0", files.len() + 1);
}
