//! `v8`: as sealed in PREREG-V8.hbp. The 3 x 2 Z3 torus: E0 certified by HEB-C's sturmfast, the v7
//! network carried over with flux-free cut SUMs, trained on fixed-point energies, reported exactly.

use gguf_qnn::bigint::Big;
use gguf_qnn::gguf_model::{self, Kv, Model};
use gguf_qnn::hbp::{index, Hbp};
use gguf_qnn::sha256::hex_digest;
use gguf_qnn::torus::{StateF, Torus};
use gguf_qnn::v4::{milli_floor_q, StateR};
use gguf_qnn::v6::{b8, TRITS_PER_B};
use gguf_qnn::v8::{train, NetT, LINKS, LX, LY, PARAMS};
use std::fs;
use std::path::Path;
use std::process::Command;

const ARCH: &str = "asolaria-qutrit-vqnn-v8";
const LAYER: &str = "layer 1: on every link R_01(b), R_02(b'), then cut SUMs (x: row 0 to row 1 in every column; y: column 0 to columns 1 and 2 in every row); layer 2: SUM ring, R_01, R_02 on every link, inverse ring; a = 6561; b = 2187p0+...+p7";

fn get(line: &str, key: &str) -> Option<String> {
    line.split('|')
        .find_map(|kv| kv.strip_prefix(key).and_then(|r| r.strip_prefix('=')))
        .map(str::to_string)
}

fn below(sturm: &Path, mat: &Path, r: i64, t: i64, calls: &mut usize, clean: &mut bool) -> usize {
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
    *clean &= get(line, "status").as_deref() == Some("COMPLETE")
        && get(line, "ambiguous").as_deref() == Some("0");
    get(line, "negative")
        .and_then(|v| v.parse().ok())
        .expect("negative")
}

/// smallest t (milli) with at least one eigenvalue below it: E0 in [(t-1)/1000, t/1000)
fn e0_milli(sturm: &Path, mat: &Path, r: i64, calls: &mut usize, clean: &mut bool) -> i64 {
    e0_milli_from(sturm, mat, r, 24_000, calls, clean)
}

fn e0_milli_from(
    sturm: &Path,
    mat: &Path,
    r: i64,
    top: i64,
    calls: &mut usize,
    clean: &mut bool,
) -> i64 {
    let (mut lo, mut hi) = (0i64, top);
    assert!(below(sturm, mat, r, hi, calls, clean) > 0);
    assert_eq!(below(sturm, mat, r, lo, calls, clean), 0);
    while hi - lo > 1 {
        let mid = (lo + hi) / 2;
        if below(sturm, mat, r, mid, calls, clean) > 0 {
            hi = mid;
        } else {
            lo = mid;
        }
    }
    hi
}

fn milli_text(x: Option<i128>) -> String {
    x.map_or("undecided".into(), |t| format!("[{t},{})", t + 1))
}

fn exact(t: &Torus, params: &[i64], r: i64) -> Option<(Big, Big)> {
    let mut s = StateR::zero_state(LINKS);
    NetT {
        params: params.to_vec(),
    }
    .forward(&mut s);
    t.energy_exact(&s.v, r)
}

#[allow(clippy::too_many_lines)]
pub fn run(sturm: &Path, out: &Path, sweeps: usize) {
    fs::create_dir_all(out).expect("out");
    let mut rec = Hbp::new();
    let mut files: Vec<(String, usize, String)> = Vec::new();
    let t = Torus::new(LX, LY);
    let c1 = t.reps.len() == 2187 && t.sizes.iter().all(|&s| s == 243);
    let (mat_text, classes, adjoint) = t.sector_matrix();
    let pf = t.perron_frobenius_ok();
    let mat = out.join("z3-3x2-sector.mat");
    fs::write(&mat, &mat_text).expect("matrix");
    files.push((
        "z3-3x2-sector.mat".into(),
        mat_text.len(),
        hex_digest(mat_text.as_bytes()),
    ));
    // C2b: the same construction on the sealed 2x2 torus at r = 9
    let t22 = Torus::new(2, 2);
    let (m22, k22, adj22) = t22.sector_matrix();
    let mat22 = out.join("z3-2x2-sector.mat");
    fs::write(&mat22, &m22).expect("matrix 2x2");
    files.push((
        "z3-2x2-sector.mat".into(),
        m22.len(),
        hex_digest(m22.as_bytes()),
    ));
    let sturm_sha = hex_digest(&fs::read(sturm).expect("sturmfast binary"));
    println!(
        "{}",
        rec.row(
            "LATTICE",
            &[
                ("torus", format!("{LX}x{LY}")),
                ("links", LINKS.to_string()),
                ("amplitudes", t.dim.to_string()),
                ("orbits", t.reps.len().to_string()),
                ("orbit_size", t.sizes[0].to_string()),
                ("sector_classes", classes.to_string()),
                ("sector_w_self_adjoint", u8::from(adjoint).to_string()),
                (
                    "perron_frobenius_offdiag_nonpositive_connected",
                    u8::from(pf).to_string()
                ),
                ("sector_matrix_sha256", hex_digest(mat_text.as_bytes())),
                ("sturmfast_sha256", sturm_sha),
            ],
        )
    );
    let (mut calls, mut clean) = (0usize, true);
    let e0_22 = e0_milli_from(sturm, &mat22, 9, 16_000, &mut calls, &mut clean);
    let c2b = adj22 && e0_22 == 15_379;
    println!(
        "{}",
        rec.row(
            "CHECK_2X2",
            &[
                ("sector_classes", k22.to_string()),
                ("w_self_adjoint", u8::from(adj22).to_string()),
                ("E0_r9_in", format!("[{},{})_milli", e0_22 - 1, e0_22)),
                ("sealed", "[15378,15379)".into()),
            ],
        )
    );
    let (mut c3, mut c5, mut c6, mut c7, mut c8, mut t6) = (true, true, true, true, true, false);
    let mut models: Vec<(String, i64, Option<i128>)> = Vec::new();
    for &r in &[9i64, 27, 81] {
        let e0 = e0_milli(sturm, &mat, r, &mut calls, &mut clean);
        let seed = vec![0i64; PARAMS];
        let start = exact(&t, &seed, r).expect("physical");
        c3 &= start.0 == start.1.mul_i128(24);
        let (params, fixed, evals, used) = train(&t, &seed, r, sweeps);
        let net = NetT {
            params: params.clone(),
        };
        let mut s = StateR::zero_state(LINKS);
        let o = s.clone();
        net.forward(&mut s);
        let best = t.energy_exact(&s.v, r).expect("physical");
        let d = s.scale();
        let norm_ok = s.norm_sq() == d.mul(&d);
        net.inverse(&mut s);
        let inv_ok = s.v == o.v.iter().map(|x| x.mul(&d).mul(&d)).collect::<Vec<_>>();
        c7 &= norm_ok && inv_ok;
        let floor = milli_floor_q(&best, 0, 100_000_000);
        let fixed_milli = (fixed * 1000) >> 40;
        c8 &= floor.is_some_and(|f| (f - fixed_milli).abs() <= 1);
        let lo_ok = floor.is_some_and(|f| f >= i128::from(e0 - 1));
        c6 &= lo_ok;
        // within W milli of the certified upper end e0/1000: exact energy < (e0 + W)/1000
        let within = |w: i64| gguf_qnn::v4::cmp_milli_q(&best, i128::from(e0 + w)) < 0;
        if r == 9 {
            t6 = within(20) && lo_ok;
        } else {
            c5 &= within(10);
        }
        let layer2 = params[PARAMS / 2..].iter().any(|&x| x != 0);
        let mut f = StateF::zero_state(LINKS);
        net.forward(&mut f);
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
                    ("seed", "IDENTITY".into()),
                    ("params", PARAMS.to_string()),
                    (
                        "params_changed_by_training",
                        params.iter().filter(|&&x| x != 0).count().to_string()
                    ),
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
                    ("layer2_active", u8::from(layer2).to_string()),
                    ("b_layer1", bs[..2 * LINKS].join(",")),
                    ("b_layer2", bs[2 * LINKS..].join(",")),
                    ("energy_numerator", best.0.dec()),
                    ("energy_denominator", best.1.dec()),
                ],
            )
        );
        let name = format!("v8-z3-3x2-r{r}-identity.gguf");
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
            ("qnn.seed".into(), Kv::Str("IDENTITY".into())),
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
    let mut c9 = true;
    for (name, r, floor) in &models {
        let m = gguf_model::read(&fs::read(out.join(name)).expect("reload")).expect("parse");
        let params: Vec<i64> = m
            .tensor("branch_0.params")
            .expect("p")
            .iter()
            .map(|&x| i64::from(x))
            .collect();
        let again = exact(&t, &params, *r).and_then(|e| milli_floor_q(&e, 0, 100_000_000));
        c9 &= again == *floor
            && m.str("ym.energy_milli_floor")
                == Some(floor.map_or("undecided".into(), |f| f.to_string()).as_str());
    }
    println!(
        "{}",
        rec.row(
            "CERTIFIER",
            &[
                ("sturmfast_calls", calls.to_string()),
                (
                    "every_call_complete_and_unambiguous",
                    u8::from(clean).to_string()
                )
            ]
        )
    );
    let verdicts = [
        (
            "T6",
            t6,
            "r9_exact_energy_within_20_milli_of_certified_E0_upper_and_above_its_lower".to_string(),
        ),
        ("C1", c1, "2187_orbits_each_of_size_243".to_string()),
        (
            "C2",
            clean,
            "sturmfast_complete_and_unambiguous_at_r_9_27_81".to_string(),
        ),
        (
            "C2b",
            c2b,
            format!("2x2_sector_E0_r9_milli_upper={e0_22}_sealed_15379"),
        ),
        (
            "C2c",
            pf && adjoint,
            "offdiag_nonpositive_orbit_graph_connected_sector_w_self_adjoint".to_string(),
        ),
        ("C3", c3, "identity_starts_at_exactly_24".to_string()),
        ("C4", t6, "T6".to_string()),
        (
            "C5",
            c5,
            "r27_r81_within_10_milli_of_certified_E0_upper".to_string(),
        ),
        (
            "C6",
            c6,
            "every_exact_energy_ge_certified_E0_lower".to_string(),
        ),
        ("C7", c7, "exact_norm_and_inverse".to_string()),
        (
            "C8",
            c8,
            "exact_milli_floor_within_1_of_fixed_point_estimate".to_string(),
        ),
        ("C9", c9, format!("models_reloaded={}", models.len())),
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
    fs::write(out.join("V8.hbp"), &text).expect("result");
    files.push(("V8.hbp".into(), text.len(), hex_digest(text.as_bytes())));
    let idx = index("V8INDEX", &files);
    fs::write(out.join("INDEX.hbi"), &idx).expect("index");
    let mut sums = String::new();
    for (f, _, h) in &files {
        sums.push_str(&format!("{h}  {f}\n"));
    }
    sums.push_str(&format!("{}  INDEX.hbi\n", hex_digest(idx.as_bytes())));
    fs::write(out.join("SHA256SUMS"), sums).expect("sums");
    println!("DONE|files={}|json=0", files.len() + 1);
}
