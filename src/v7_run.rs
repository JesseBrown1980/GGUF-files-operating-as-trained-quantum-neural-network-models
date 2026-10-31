//! `v7`: as sealed in PREREG-V7.hbp. The v6 layer plus a correlated dressing layer
//! (SUM ring, rotations, inverse ring); every trained model is recomputed on the pixel
//! backend (64 residue channels, per-pixel gathers) and lifted back to exact integers.

use gguf_qnn::bigint::Big;
use gguf_qnn::gguf_model::{self, Kv, Model};
use gguf_qnn::hbp::{index, Hbp};
use gguf_qnn::pixels::{lift, primes, render, Frame};
use gguf_qnn::sha256::hex_digest;
use gguf_qnn::v4::{cmp_milli_q, milli_floor_q, StateR, Z3Orbits};
use gguf_qnn::v6::{b8, NetP6, TRITS_PER_B};
use gguf_qnn::v7::{train, Engine, NetQ, PARAMS, PER_LAYER};
use gguf_qnn::ym_z3::{digits, gauge, gauge_group, index as cfg_index, DIM, LINKS};
use std::fs;
use std::path::Path;

const ARCH: &str = "asolaria-qutrit-vqnn-v7";
const LAYER: &str = "layer 1: on every link R_01(b), R_02(b'), then SUM 0->4, 2->6, 1->3, 5->7; layer 2: SUM ring q->q+1, R_01(b), R_02(b') on every link, inverse SUM ring; R_ij(b) = [[a^2-b^2, -2ab], [2ab, a^2-b^2]] on levels i, j and a^2+b^2 on the third; a = 6561; b = 2187p0+...+p7";
const SETS: [&str; 3] = ["IDENTITY", "WARM", "STAR"];
const CHANNELS: usize = 64;
const WARM_SHA: [(i64, &str); 3] = [
    (
        9,
        "8a1481e4635c7ba06f8c6b89e0e236022dfe12e9b8c1354a05a873e860020a72",
    ),
    (
        27,
        "c71dfe835411601b095c74a2587fc59c647b2f3011d374b97bcb11d68e628213",
    ),
    (
        81,
        "c9f7a00941be1746608f27e6a680456e01f938605b24817134e8cf39b1296571",
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

/// The sealed v6 IDENTITY model at r: its params (layer 1 of v7).
fn warm(v6: &Path, r: i64) -> Vec<i64> {
    let bytes = fs::read(v6.join(format!("v6-z3-r{r}-identity.gguf"))).expect("v6 model");
    let want = WARM_SHA.iter().find(|x| x.0 == r).expect("sha").1;
    assert_eq!(hex_digest(&bytes), want, "sealed v6 model");
    let m = gguf_model::read(&bytes).expect("parse v6");
    m.tensor("branch_0.params")
        .expect("p")
        .iter()
        .map(|&x| i64::from(x))
        .collect()
}

/// Records a PNG frame of the exact state after every pass.
struct Recorder {
    s: StateR,
    frames: Vec<(String, Vec<u8>)>,
    tag: String,
}

impl Recorder {
    fn snap(&mut self, what: &str) {
        let n = self.frames.len();
        self.frames.push((
            format!("frames/{}-{n:02}-{what}.png", self.tag),
            render(&self.s.v, 2),
        ));
    }
}

impl Engine for Recorder {
    fn rotate(&mut self, q: usize, i: usize, j: usize, b: i128, a: i128) {
        if b != 0 {
            self.s.rotate_a(q, i, j, b, a);
            self.snap(&format!("R{i}{j}-link{q}-b{b}"));
        }
    }
    fn sum(&mut self, c: usize, t: usize, s: i64) {
        self.s.sum(c, t, s);
        let sign = if s > 0 { "" } else { "inv" };
        self.snap(&format!("SUM{sign}-{c}to{t}"));
    }
}

fn projected(v: &[Big]) -> Vec<Big> {
    let group = gauge_group();
    (0..DIM)
        .map(|c| {
            let g = digits(c);
            group
                .iter()
                .fold(Big::zero(), |acc, a| acc.add(&v[cfg_index(&gauge(&g, a))]))
        })
        .collect()
}

#[allow(clippy::too_many_lines)]
pub fn run(stars: &Path, ym: &Path, v6: &Path, out: &Path, sweeps: usize) {
    fs::create_dir_all(out.join("frames")).expect("out");
    let mut rec = Hbp::new();
    let mut files: Vec<(String, usize, String)> = Vec::new();
    let (star, _) = crate::star_trits(&stars.join("ACER-MYTHOS-BLUE.gguf"));
    let ps = primes(CHANNELS);
    println!(
        "{}",
        rec.row(
            "BACKEND",
            &[
                ("gpu", "none_in_this_workspace".into()),
                ("framebuffer", "81x81_x=links0..3_y=links4..7".into()),
                ("channels", CHANNELS.to_string()),
                ("largest_prime", ps[0].to_string()),
                ("smallest_prime", ps[CHANNELS - 1].to_string()),
            ],
        )
    );
    let orbits = Z3Orbits::new();
    let (mut u1, mut u2, mut u3, mut u4, mut u7, mut u8_, mut u9) =
        (true, true, true, true, true, true, true);
    let mut models: Vec<(String, i64, Option<i128>)> = Vec::new();
    let mut best_r: Vec<(i64, i128, String, Vec<i64>)> = Vec::new();
    for &r in &[9i64, 27, 81] {
        let e0_lo = certified_e0_lower(ym, r);
        let w6 = warm(v6, r);
        for set in SETS {
            let (seed_name, seed): (String, Vec<i64>) = match set {
                "IDENTITY" => ("IDENTITY".into(), vec![0; PARAMS]),
                "WARM" => {
                    let mut p = w6.clone();
                    p.extend(std::iter::repeat(0).take(PARAMS - PER_LAYER));
                    ("WARM-V6-IDENTITY".into(), p)
                }
                _ => (
                    "ACER-MYTHOS-BLUE".into(),
                    (0..PARAMS)
                        .map(|i| star[(i * 4099) % star.len()] - 1)
                        .collect(),
                ),
            };
            let start = NetQ {
                params: seed.clone(),
            }
            .energy(&orbits, r)
            .expect("physical");
            let (params, best, evals, sweeps_used) = train(&orbits, &seed, r, sweeps);
            let net = NetQ {
                params: params.clone(),
            };
            // exact norm and inverse on the big-integer state
            let mut s = StateR::zero_state(LINKS);
            let o = s.clone();
            net.forward(&mut s);
            let d = s.scale();
            u1 &= s.norm_sq() == d.mul(&d);
            net.inverse(&mut s);
            u2 &= s.v == o.v.iter().map(|x| x.mul(&d).mul(&d)).collect::<Vec<_>>();
            // the pixel backend
            let mut f = Frame::zero_state(&ps);
            net.forward(&mut f);
            let (rn, rd) = f.energy_residues(r);
            let (ln, ld) = (lift(&rn, &ps), lift(&rd, &ps));
            let pixel_ok = ln == best.0 && ld == best.1;
            u8_ &= pixel_ok;
            if set == "IDENTITY" {
                u3 &= start.0 == start.1.mul_i128(16);
            }
            if set == "WARM" {
                let e6 = NetP6 {
                    layers: 1,
                    params: w6.clone(),
                }
                .energy(&orbits, r)
                .expect("v6 energy");
                u4 &= start.0.mul(&e6.1) == e6.0.mul(&start.1);
            }
            if set == "STAR" {
                u9 &= cmp_milli_q(&best, 16_000) > 0;
            }
            let above_e0 = cmp_milli_q(&best, e0_lo) >= 0;
            u7 &= above_e0;
            let floor = milli_floor_q(&best, 0, 10_000_000);
            if let Some(t) = floor {
                match best_r.iter_mut().find(|x| x.0 == r) {
                    Some(x) => {
                        if t < x.1 {
                            *x = (r, t, set.to_string(), params.clone());
                        }
                    }
                    None => best_r.push((r, t, set.to_string(), params.clone())),
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
                        ("set", set.into()),
                        ("seed", seed_name.clone()),
                        ("params", PARAMS.to_string()),
                        ("params_changed_by_training", changed.to_string()),
                        ("sweeps", sweeps_used.to_string()),
                        ("evaluations", evals.to_string()),
                        (
                            "start_energy_milli_in",
                            milli_text(milli_floor_q(&start, 0, 10_000_000))
                        ),
                        ("energy_milli_in", milli_text(floor)),
                        ("certified_E0_lower_milli", e0_lo.to_string()),
                        ("energy_ge_certified_E0", u8::from(above_e0).to_string()),
                        ("pixel_backend_passes", f.passes.to_string()),
                        ("pixel_backend_equals_exact", u8::from(pixel_ok).to_string()),
                        ("b_layer1", bs[..2 * LINKS].join(",")),
                        ("b_layer2", bs[2 * LINKS..].join(",")),
                        ("energy_numerator", best.0.dec()),
                        ("energy_denominator", best.1.dec()),
                    ],
                )
            );
            let name = format!("v7-z3-r{r}-{}.gguf", set.to_lowercase());
            let kv = vec![
                ("general.architecture".into(), Kv::Str(ARCH.into())),
                ("general.name".into(), Kv::Str(name.clone())),
                ("qnn.layer".into(), Kv::Str(LAYER.into())),
                (
                    "qnn.amplitudes".into(),
                    Kv::Str("real integers over the product of a^2+b^2, exact".into()),
                ),
                ("qnn.seed_set".into(), Kv::Str(set.into())),
                ("qnn.layers".into(), Kv::U32(2)),
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
    // frames: every pass of the best r9 model; the final and projected state at every r
    for (r, _, set, params) in &best_r {
        let net = NetQ {
            params: params.clone(),
        };
        let mut recd = Recorder {
            s: StateR::zero_state(LINKS),
            frames: Vec::new(),
            tag: format!("r{r}-{}", set.to_lowercase()),
        };
        if *r == 9 {
            recd.snap("input");
            net.forward(&mut recd);
        } else {
            net.forward(&mut recd.s);
            recd.snap("final");
        }
        let phi = projected(&recd.s.v);
        let n = recd.frames.len();
        recd.frames.push((
            format!("frames/{}-{n:02}-gauge-projected.png", recd.tag),
            render(&phi, 2),
        ));
        for (name, bytes) in recd.frames {
            fs::write(out.join(&name), &bytes).expect("frame");
            files.push((name, bytes.len(), hex_digest(&bytes)));
        }
    }
    let b = |r: i64| best_r.iter().find(|x| x.0 == r).map(|x| x.1);
    let opt = |x: Option<i128>| x.map_or("undecided".into(), |t| t.to_string());
    let t5 = b(9).is_some_and(|t| t <= 15_381) && u7;
    let u6 = b(27).is_some_and(|t| t <= 15_800) && b(81).is_some_and(|t| t <= 15_933);

    // U10: reload every model and recompute its energy
    let mut u10 = true;
    for (name, r, floor) in &models {
        let m = gguf_model::read(&fs::read(out.join(name)).expect("reload")).expect("parse");
        let params: Vec<i64> = m
            .tensor("branch_0.params")
            .expect("p")
            .iter()
            .map(|&x| i64::from(x))
            .collect();
        let again = NetQ { params }
            .energy(&orbits, *r)
            .and_then(|e| milli_floor_q(&e, 0, 10_000_000));
        u10 &= again == *floor
            && m.str("ym.energy_milli_floor")
                == Some(floor.map_or("undecided".into(), |t| t.to_string()).as_str());
    }
    let best9 = best_r
        .iter()
        .find(|x| x.0 == 9)
        .map_or("undecided".into(), |x| format!("{}_{}", x.1, x.2));
    let verdicts = [
        ("T5", t5, format!("best_r9_energy_milli_floor={best9}")),
        (
            "U1",
            u1,
            "norm_sq_equals_scale_squared_every_model".to_string(),
        ),
        (
            "U2",
            u2,
            "inverse_returns_scale_squared_times_input_every_model".to_string(),
        ),
        (
            "U3",
            u3,
            "identity_seed_starts_at_exactly_16_at_r_9_27_81".to_string(),
        ),
        (
            "U4",
            u4,
            "warm_start_equals_the_sealed_v6_identity_energy_exactly".to_string(),
        ),
        ("U5", t5, "T5".to_string()),
        (
            "U6",
            u6,
            format!(
                "best_r27={}_le_15800,best_r81={}_le_15933",
                opt(b(27)),
                opt(b(81))
            ),
        ),
        (
            "U7",
            u7,
            "every_trained_energy_ge_certified_E0_lower".to_string(),
        ),
        (
            "U8",
            u8_,
            format!(
                "pixel_backend_lift_equals_exact_for_{}_models",
                models.len()
            ),
        ),
        ("U9", u9, "star_seed_above_16_at_r_9_27_81".to_string()),
        ("U10", u10, format!("models_reloaded={}", models.len())),
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
    fs::write(out.join("V7.hbp"), &text).expect("result");
    files.push(("V7.hbp".into(), text.len(), hex_digest(text.as_bytes())));
    let idx = index("V7INDEX", &files);
    fs::write(out.join("INDEX.hbi"), &idx).expect("index");
    let mut sums = String::new();
    for (f, _, h) in &files {
        sums.push_str(&format!("{h}  {f}\n"));
    }
    sums.push_str(&format!("{}  INDEX.hbi\n", hex_digest(idx.as_bytes())));
    fs::write(out.join("SHA256SUMS"), sums).expect("sums");
    println!("DONE|files={}|json=0", files.len() + 1);
}
