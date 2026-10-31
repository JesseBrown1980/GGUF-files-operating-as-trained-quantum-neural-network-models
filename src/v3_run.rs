//! `v3`: as sealed in PREREG-V3.hbp. Circle at 2 layers; Z3 with the identity-reachable
//! sandwich network F . diag . F^dagger . SUM ring, and an IDENTITY seed.

use gguf_qnn::gguf_model::{self, Kv, Model};
use gguf_qnn::hbp::{index, Hbp};
use gguf_qnn::qutrit9::{Net9, Net9S, State9};
use gguf_qnn::real3::R3;
use gguf_qnn::sha256::{digest, hex_digest};
use gguf_qnn::task::{points, QUTRITS};
use gguf_qnn::v2::{
    cmp_frac, cmp_milli, correct, encode9, marginal, margins, milli_floor, norm_sum, train_circle,
    virtual_correct, z3_energy,
};
use gguf_qnn::virtual_qnn::weights;
use gguf_qnn::ym_z3::LINKS;
use std::fs;
use std::path::Path;

const STARS: [&str; 3] = ["ACER-OPUS-RED", "ACER-FABLE-GREEN", "ACER-MYTHOS-BLUE"];
const CLOUD_OFFSETS: [usize; 3] = [0, 3692, 7384];
const ARCH: &str = "asolaria-qutrit-vqnn-v3";
const GATE: &str =
    "F each; diag(1, zeta^(3a+c), zeta^(3a'+c')) each; SUM ring q->q+1; zeta = e^(2 pi i/9)";

fn get(line: &str, key: &str) -> Option<String> {
    line.split('|')
        .find_map(|kv| kv.strip_prefix(key).and_then(|r| r.strip_prefix('=')))
        .map(str::to_string)
}

fn r3s(x: &R3) -> String {
    x.c.iter()
        .map(|b| format!("{b:?}"))
        .collect::<Vec<_>>()
        .join(";")
}

fn seeds(set: &str, stars: &Path, cloud: &[u8], count: usize) -> Vec<(String, Vec<i64>)> {
    (0..3)
        .map(|b| match set {
            "STAR" => {
                let (t, _) = crate::star_trits(&stars.join(format!("{}.gguf", STARS[b])));
                (
                    STARS[b].to_string(),
                    (0..count).map(|i| t[(i * 4099) % t.len()]).collect(),
                )
            }
            "CLOUD" => (
                format!("CLOUD-STAR@{}", CLOUD_OFFSETS[b]),
                (0..count)
                    .map(|i| i64::from(cloud[(CLOUD_OFFSETS[b] + i) % cloud.len()]))
                    .collect(),
            ),
            _ => (
                format!("SHA-V2-{b}"),
                (0..count)
                    .map(|i| i64::from(digest(format!("V2SEED|{b}|{i}").as_bytes())[0] % 3))
                    .collect(),
            ),
        })
        .collect()
}

fn permille(c: usize, n: usize) -> usize {
    c * 1000 / n.max(1)
}

/// The certified E0 lower bound (milli) at r from the sealed ym-z3 receipt.
fn certified_e0_lower(ym: &Path, r: i64) -> i128 {
    let text = fs::read_to_string(ym.join("YM-Z3.hbp")).expect("sealed YM-Z3.hbp");
    let row = text
        .lines()
        .find(|l| l.starts_with("CERTIFIED|") && get(l, "r").as_deref() == Some(&r.to_string()))
        .expect("certified row");
    let e0 = get(row, "E0_in").expect("E0_in"); // "[15.378,15.379)"
    let lo = e0.trim_start_matches('[').split(',').next().expect("lo");
    let (a, b) = lo.split_once('.').expect("milli");
    a.parse::<i128>().expect("int") * 1000 + b.parse::<i128>().expect("frac")
}

fn net_model(
    name: &str,
    set: &str,
    layers: usize,
    nets: &[Net9],
    c: &[i64],
    kv_extra: Vec<(String, Kv)>,
) -> Vec<u8> {
    let mut kv = vec![
        ("general.architecture".into(), Kv::Str(ARCH.into())),
        ("general.name".into(), Kv::Str(name.into())),
        ("qnn.layer".into(), Kv::Str(GATE.into())),
        (
            "qnn.amplitudes".into(),
            Kv::Str("Z[zeta_9] over sqrt(3)^k, exact; probabilities in Z[2cos(2pi/9)]".into()),
        ),
        ("qnn.seed_set".into(), Kv::Str(set.into())),
        ("qnn.layers".into(), Kv::U32(layers as u32)),
        ("qnn.branches".into(), Kv::U32(nets.len() as u32)),
    ];
    kv.extend(kv_extra);
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
    gguf_model::write(&Model { kv, tensors })
}

fn circle_eval(m: &Model) -> (usize, usize) {
    let layers = m.u32("qnn.layers").expect("layers") as usize;
    let nb = m.u32("qnn.branches").expect("branches") as usize;
    let c: Vec<i64> = m
        .tensor("virtual.coefficients")
        .expect("c")
        .iter()
        .map(|&x| i64::from(x))
        .collect();
    let nets: Vec<Net9> = (0..nb)
        .map(|b| Net9 {
            n: QUTRITS,
            layers,
            params: m
                .tensor(&format!("branch_{b}.params"))
                .expect("p")
                .iter()
                .map(|&x| i64::from(x))
                .collect(),
        })
        .collect();
    let (tr, te) = points();
    let mtr: Vec<_> = nets.iter().map(|n| margins(n, &tr)).collect();
    let mte: Vec<_> = nets.iter().map(|n| margins(n, &te)).collect();
    (
        virtual_correct(&c, &mtr, &tr).0,
        virtual_correct(&c, &mte, &te).0,
    )
}

#[allow(clippy::too_many_lines)]
pub fn run(
    stars: &Path,
    cloud_dir: &Path,
    ym: &Path,
    out: &Path,
    circle_layers: usize,
    z3_layers: usize,
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
    let (tr, te) = points();
    let majority = 154usize;
    let ccount = Net9::param_count(QUTRITS, circle_layers);
    let (mut w1, mut w2, mut w3) = (true, true, false);
    let mut set_best = Vec::new();
    let mut w5 = true;
    let mut circle_models: Vec<String> = Vec::new();
    for set in ["STAR", "CLOUD", "SHA"] {
        let mut nets = Vec::new();
        let (mut best_tr, mut best_te) = (0usize, 0usize);
        for (b, (seed_name, seed)) in seeds(set, stars, &cloud, ccount).into_iter().enumerate() {
            let t = train_circle(
                Net9 {
                    n: QUTRITS,
                    layers: circle_layers,
                    params: seed.clone(),
                },
                &tr,
                sweeps,
            );
            let mte = margins(&t.net, &te);
            let (te_c, te_u) = correct(&mte, &te);
            let mtr = margins(&t.net, &tr);
            let (tr_c, tr_u) = correct(&mtr, &tr);
            assert_eq!(tr_c, t.train_correct);
            best_tr = best_tr.max(tr_c);
            best_te = best_te.max(te_c);
            for p in &te {
                let mut s = encode9(p);
                let o = s.clone();
                t.net.forward(&mut s);
                w1 &= norm_sum(&s) == R3::int(3i128.pow(s.k));
                let m0 = marginal(&s, 0);
                w3 |= m0.iter().any(|x| !x.c[1].is_zero() || !x.c[2].is_zero());
                t.net.inverse(&mut s);
                w2 &= s.equals_scaled(&o, s.k / 2);
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
                        ("params", ccount.to_string()),
                        ("params_changed_by_training", changed.to_string()),
                        ("sweeps", t.sweeps.to_string()),
                        ("evaluations", t.evaluations.to_string()),
                        ("train_correct", tr_c.to_string()),
                        ("train_undecided", tr_u.to_string()),
                        ("test_correct", te_c.to_string()),
                        ("test_undecided", te_u.to_string()),
                        ("test_permille", permille(te_c, te.len()).to_string()),
                        (
                            "params_trits",
                            t.net.params.iter().map(i64::to_string).collect::<String>()
                        ),
                    ],
                )
            );
            let name = format!("v3-circle-{}-branch-{b}.gguf", set.to_lowercase());
            let bytes = net_model(
                &name,
                set,
                circle_layers,
                std::slice::from_ref(&t.net),
                &[1],
                vec![
                    ("qnn.task".into(), Kv::Str("circle-27".into())),
                    ("qnn.seed".into(), Kv::Str(seed_name.clone())),
                    ("qnn.train_correct".into(), Kv::U32(tr_c as u32)),
                    ("qnn.test_correct".into(), Kv::U32(te_c as u32)),
                ],
            );
            fs::write(out.join(&name), &bytes).expect("gguf");
            files.push((name.clone(), bytes.len(), hex_digest(&bytes)));
            circle_models.push(name);
            nets.push(t.net);
        }
        let mtr: Vec<_> = nets.iter().map(|n| margins(n, &tr)).collect();
        let mte: Vec<_> = nets.iter().map(|n| margins(n, &te)).collect();
        let mut best: Option<(usize, i64, Vec<i64>)> = None;
        for c in weights(3) {
            let n = virtual_correct(&c, &mtr, &tr).0;
            let o: i64 = c.iter().map(|x| x.abs()).sum();
            let better = match &best {
                None => true,
                Some((bn, bo, _)) => n > *bn || (n == *bn && o < *bo),
            };
            if better {
                best = Some((n, o, c));
            }
        }
        let (vtr, overhead, c) = best.expect("weights");
        let (vte, vte_u) = virtual_correct(&c, &mte, &te);
        w5 &= vte >= best_te;
        set_best.push((set, best_tr, best_te, vte));
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
                    ("test_correct", vte.to_string()),
                    ("test_undecided", vte_u.to_string()),
                    ("best_single_train", best_tr.to_string()),
                    ("best_single_test", best_te.to_string()),
                ],
            )
        );
        let name = format!("v3-circle-{}-virtual.gguf", set.to_lowercase());
        let bytes = net_model(
            &name,
            set,
            circle_layers,
            &nets,
            &c,
            vec![
                ("qnn.task".into(), Kv::Str("circle-27".into())),
                ("qnn.train_correct".into(), Kv::U32(vtr as u32)),
                ("qnn.test_correct".into(), Kv::U32(vte as u32)),
            ],
        );
        fs::write(out.join(&name), &bytes).expect("gguf");
        files.push((name.clone(), bytes.len(), hex_digest(&bytes)));
        circle_models.push(name);
    }

    // Z3: the identity-reachable sandwich network, four seeds per coupling
    let zcount = Net9S::param_count(LINKS, z3_layers);
    let z3_seeds: Vec<(String, Vec<i64>)> = vec![
        seeds("STAR", stars, &cloud, zcount)
            .into_iter()
            .nth(2)
            .expect("mythos"),
        seeds("CLOUD", stars, &cloud, zcount)
            .into_iter()
            .next()
            .expect("cloud"),
        (
            "SHA-V3-0".to_string(),
            (0..zcount)
                .map(|i| i64::from(digest(format!("V3SEED|0|{i}").as_bytes())[0] % 3))
                .collect(),
        ),
        ("IDENTITY".to_string(), vec![0; zcount]),
    ];
    let mut x6 = true;
    let mut x1z = true;
    let mut x2z = true;
    let mut t2_e0 = true;
    let mut z3_models: Vec<(String, i64, Option<i128>)> = Vec::new();
    for &r in &[9i64, 27, 81] {
        let e0_lo = certified_e0_lower(ym, r);
        for (set, (seed_name, seed)) in ["STAR", "CLOUD", "SHA", "IDENTITY"]
            .iter()
            .zip(z3_seeds.iter())
        {
            let eval = |params: &[i64]| {
                let net = Net9S {
                    n: LINKS,
                    layers: z3_layers,
                    params: params.to_vec(),
                };
                let mut s = State9::basis(LINKS, &[0; LINKS]);
                net.forward(&mut s);
                z3_energy(&s, r)
            };
            let start = eval(seed).expect("seed has a physical component");
            if *set == "IDENTITY" {
                x6 &= start.0 == start.1.scale(16);
            }
            let mut params = seed.clone();
            let mut best = start.clone();
            let mut evals = 1usize;
            for _ in 0..sweeps {
                let mut changed = false;
                for i in 0..params.len() {
                    let keep = params[i];
                    let mut best_v = keep;
                    for v in 0..3 {
                        if v == keep {
                            continue;
                        }
                        params[i] = v;
                        evals += 1;
                        if let Some(e) = eval(&params) {
                            if cmp_frac(&e, &best) == Some(-1) {
                                best = e;
                                best_v = v;
                            }
                        }
                    }
                    params[i] = best_v;
                    changed |= best_v != keep;
                }
                if !changed {
                    break;
                }
            }
            let net = Net9S {
                n: LINKS,
                layers: z3_layers,
                params: params.clone(),
            };
            let mut s = State9::basis(LINKS, &[0; LINKS]);
            let o = s.clone();
            net.forward(&mut s);
            x1z &= norm_sum(&s) == R3::int(3i128.pow(s.k));
            net.inverse(&mut s);
            x2z &= s.equals_scaled(&o, s.k / 2);
            let below16 = cmp_milli(&best, 16_000) == Some(-1);
            let above_e0 = cmp_milli(&best, e0_lo).is_some_and(|x| x >= 0);
            if r == 9 {
                t2_e0 &= above_e0;
            }
            let floor = milli_floor(&best, 0, 1_000_000);
            let exactly16 = best.0 == best.1.scale(16);
            let changed = params
                .iter()
                .zip(seed.iter())
                .filter(|(a, b)| a != b)
                .count();
            println!(
                "{}",
                rec.row(
                    "Z3MODEL",
                    &[
                        ("r", r.to_string()),
                        ("set", (*set).into()),
                        ("seed", seed_name.clone()),
                        ("layers", z3_layers.to_string()),
                        ("params", zcount.to_string()),
                        ("params_changed_by_training", changed.to_string()),
                        ("evaluations", evals.to_string()),
                        (
                            "start_energy_milli_in",
                            milli_floor(&start, 0, 1_000_000)
                                .map_or("undecided".into(), |t| format!("[{t},{})", t + 1))
                        ),
                        (
                            "energy_milli_in",
                            floor.map_or("undecided".into(), |t| format!("[{t},{})", t + 1))
                        ),
                        ("energy_exactly_16", u8::from(exactly16).to_string()),
                        ("energy_lt_16", u8::from(below16).to_string()),
                        ("certified_E0_lower_milli", e0_lo.to_string()),
                        ("energy_ge_certified_E0", u8::from(above_e0).to_string()),
                        ("energy_numerator_theta_basis", r3s(&best.0)),
                        ("energy_denominator_theta_basis", r3s(&best.1)),
                        (
                            "params_trits",
                            params.iter().map(i64::to_string).collect::<String>()
                        ),
                    ],
                )
            );
            let name = format!("v3-z3-r{r}-{}.gguf", set.to_lowercase());
            let mut kv = vec![
                ("general.architecture".into(), Kv::Str(ARCH.into())),
                ("general.name".into(), Kv::Str(name.clone())),
                ("qnn.layer".into(), Kv::Str("every link: F, diag(1, zeta^(3a+c), zeta^(3a'+c')), F^dagger; then SUM ring".into())),
                ("qnn.amplitudes".into(), Kv::Str("Z[zeta_9] over sqrt(3)^k, exact".into())),
                ("qnn.seed_set".into(), Kv::Str((*set).into())),
                ("qnn.layers".into(), Kv::U32(z3_layers as u32)),
                ("qnn.branches".into(), Kv::U32(1)),
            ];
            kv.push((
                "qnn.task".into(),
                Kv::Str("variational ground state, Z3 gauge theory, 2x2 torus".into()),
            ));
            kv.push(("qnn.seed".into(), Kv::Str(seed_name.clone())));
            kv.push(("ym.r".into(), Kv::U32(r as u32)));
            kv.push((
                "ym.energy_milli_floor".into(),
                Kv::Str(floor.map_or("undecided".into(), |t| t.to_string())),
            ));
            kv.push(("ym.certified_E0_milli_lower".into(), Kv::U32(e0_lo as u32)));
            let bytes = gguf_model::write(&Model {
                kv,
                tensors: vec![
                    (
                        "branch_0.params".into(),
                        params.iter().map(|&x| x as i8).collect(),
                    ),
                    ("virtual.coefficients".into(), vec![1]),
                ],
            });
            fs::write(out.join(&name), &bytes).expect("gguf");
            files.push((name.clone(), bytes.len(), hex_digest(&bytes)));
            z3_models.push((name, r, floor));
        }
    }
    let best9 = z3_models
        .iter()
        .filter(|m| m.1 == 9)
        .filter_map(|m| m.2)
        .min();
    let t2 = best9.is_some_and(|t| t < 16_000) && t2_e0;
    let x7 = !t2 && best9 == Some(16_000);

    // X8: reload every model and recompute
    let mut x8 = true;
    for name in &circle_models {
        let m = gguf_model::read(&fs::read(out.join(name)).expect("reload")).expect("parse");
        let (a, b) = circle_eval(&m);
        x8 &= Some(a as u32) == m.u32("qnn.train_correct")
            && Some(b as u32) == m.u32("qnn.test_correct");
    }
    for (name, r, floor) in &z3_models {
        let m = gguf_model::read(&fs::read(out.join(name)).expect("reload")).expect("parse");
        let layers = m.u32("qnn.layers").expect("layers") as usize;
        let params: Vec<i64> = m
            .tensor("branch_0.params")
            .expect("p")
            .iter()
            .map(|&x| i64::from(x))
            .collect();
        let net = Net9S {
            n: LINKS,
            layers,
            params,
        };
        let mut s = State9::basis(LINKS, &[0; LINKS]);
        net.forward(&mut s);
        let again = z3_energy(&s, *r).and_then(|e| milli_floor(&e, 0, 1_000_000));
        x8 &= again == *floor
            && m.str("ym.energy_milli_floor")
                == Some(floor.map_or("undecided".into(), |t| t.to_string()).as_str());
    }
    let best_any = set_best.iter().map(|s| s.2).max().unwrap_or(0);
    let t1 = best_any > majority;
    let verdicts = [
        (
            "T1",
            t1,
            format!("best_branch_test_correct={best_any}_against_154"),
        ),
        (
            "T2",
            t2,
            format!(
                "best_r9_energy_milli_floor={}",
                best9.map_or("undecided".into(), |t| t.to_string())
            ),
        ),
        (
            "X1",
            w1 && x1z,
            "exact_norm_every_trained_circle_branch_every_test_point_and_every_z3_model"
                .to_string(),
        ),
        (
            "X2",
            w2 && x2z,
            "exact_inverse_every_trained_circle_branch_every_test_point_and_every_z3_model"
                .to_string(),
        ),
        (
            "X3",
            w3,
            "readout_qutrit_0_irrational_for_some_trained_circle_branch_at_some_test_point"
                .to_string(),
        ),
        ("X4", t1, "T1".to_string()),
        (
            "X5",
            w5,
            set_best
                .iter()
                .map(|s| format!("{}:{}>={}", s.0, s.3, s.2))
                .collect::<Vec<_>>()
                .join(","),
        ),
        (
            "X6",
            x6,
            "identity_seed_starts_at_exactly_16_at_r_9_27_81".to_string(),
        ),
        (
            "X7",
            x7,
            format!(
                "T2_fails_and_best_r9_is_exactly_16:best_r9_milli_floor={}",
                best9.map_or("undecided".into(), |t| t.to_string())
            ),
        ),
        (
            "X8",
            x8,
            format!("models_reloaded={}", circle_models.len() + z3_models.len()),
        ),
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
    fs::write(out.join("V3.hbp"), &text).expect("result");
    files.push(("V3.hbp".into(), text.len(), hex_digest(text.as_bytes())));
    let idx = index("V3INDEX", &files);
    fs::write(out.join("INDEX.hbi"), &idx).expect("index");
    let mut sums = String::new();
    for (f, _, h) in &files {
        sums.push_str(&format!("{h}  {f}\n"));
    }
    sums.push_str(&format!("{}  INDEX.hbi\n", hex_digest(idx.as_bytes())));
    fs::write(out.join("SHA256SUMS"), sums).expect("sums");
    println!("DONE|files={}|json=0", files.len() + 1);
}
