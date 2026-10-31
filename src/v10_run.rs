//! `v10`: as sealed in PREREG-V10.hbp with ADDENDUM-V10 and ADDENDUM-V10b. The 3 x 3 Z3 torus in the
//! gauge-fixed basis; E0 certified by HEB-C's sturmfast on the zero-winding zero-momentum block, after
//! the exact symmetry checks QA and QB and the 2x2 and 3x2 controls.

use gguf_qnn::bigint::Big;
use gguf_qnn::gfix::GaugeFixed;
use gguf_qnn::gguf_model::{self, Kv, Model};
use gguf_qnn::hbp::{index, Hbp};
use gguf_qnn::sha256::hex_digest;
use gguf_qnn::torus::Torus;
use gguf_qnn::v10::{param_count, train, NetV10};
use gguf_qnn::v4::{cmp_milli_q, milli_floor_q, StateR};
use gguf_qnn::v6::{b8, TRITS_PER_B};
use gguf_qnn::v9::NetV9;
use std::fs;
use std::path::Path;
use std::process::Command;

const ARCH: &str = "asolaria-qutrit-vqnn-v10";
const LAYER: &str = "gauge-fixed free links; layer 1: R_01(b), R_02(b') on every free link; layer 2: for every plaquette, SUMs from its other free links put the plaquette flux on its last free link, R_01, R_02 there, SUMs undone; a = 6561; b = 2187p0+...+p7";
const V9_R9_SHA: &str = "df5e4d6952b942ba88376ca1f17fa370fb8ecbbeeb303000bc6578dd715ab5bc";

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

/// smallest t (milli) with an eigenvalue below it: E0 in [(t-1)/1000, t/1000)
fn e0_milli(
    sturm: &Path,
    mat: &Path,
    r: i64,
    top: i64,
    calls: &mut usize,
    clean: &mut bool,
) -> i64 {
    let (mut lo, mut hi) = (0i64, top);
    *clean &=
        below(sturm, mat, r, hi, calls, clean) > 0 && below(sturm, mat, r, lo, calls, clean) == 0;
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

#[allow(clippy::too_many_lines)]
pub fn run(sturm: &Path, v9: &Path, out: &Path, sweeps: usize) {
    fs::create_dir_all(out).expect("out");
    let mut rec = Hbp::new();
    let mut files: Vec<(String, usize, String)> = Vec::new();
    let (mut calls, mut clean) = (0usize, true);
    let (mut qa_all, mut qb_all) = (true, true);
    let mut blocks: Vec<(usize, usize, GaugeFixed, std::path::PathBuf, usize)> = Vec::new();
    for (lx, ly) in [(2usize, 2usize), (3, 2), (3, 3)] {
        let gf = GaugeFixed::new(lx, ly);
        let (qa, qb) = gf.symmetry_checks();
        qa_all &= qa;
        qb_all &= qb;
        let (text, k, adj) = gf.block_matrix();
        qa_all &= adj;
        let name = format!("z3-{lx}x{ly}-block.mat");
        let path = out.join(&name);
        fs::write(&path, &text).expect("matrix");
        files.push((name, text.len(), hex_digest(text.as_bytes())));
        println!(
            "{}",
            rec.row(
                "BLOCK",
                &[
                    ("torus", format!("{lx}x{ly}")),
                    ("free_links", gf.free.len().to_string()),
                    ("gauge_fixed_states", gf.dim.to_string()),
                    ("zero_winding_zero_momentum_classes", k.to_string()),
                    ("w_self_adjoint", u8::from(adj).to_string()),
                    ("QA_commutation", u8::from(qa).to_string()),
                    ("QB_offdiag_nonpositive_connected", u8::from(qb).to_string()),
                    ("matrix_sha256", hex_digest(text.as_bytes())),
                ],
            )
        );
        blocks.push((lx, ly, gf, path, k));
    }
    let q1 = blocks[2].4 == 753;
    // Q2: 2x2 control at r = 9
    let e22 = e0_milli(sturm, &blocks[0].3, 9, 16_000, &mut calls, &mut clean);
    let q2 = e22 == 15_379;
    // Q3: 3x2 control at r = 9, 27, 81 against the sealed v8 intervals
    let sealed32 = [(9i64, 23_299i64), (27, 23_775), (81, 23_926)];
    let mut q3 = blocks[1].4 == 46;
    let mut e32 = Vec::new();
    for &(r, want) in &sealed32 {
        let e = e0_milli(sturm, &blocks[1].3, r, 24_000, &mut calls, &mut clean);
        q3 &= e == want;
        e32.push(format!("r{r}:[{},{})", e - 1, e));
    }
    println!(
        "{}",
        rec.row(
            "CONTROLS",
            &[
                (
                    "2x2_r9",
                    format!("[{},{})_milli_sealed_[15378,15379)", e22 - 1, e22)
                ),
                ("3x2", e32.join(",")),
                (
                    "3x2_sealed",
                    "r9:[23298,23299),r27:[23774,23775),r81:[23925,23926)".into()
                ),
            ],
        )
    );
    // Q5: the sealed v9 3x2 r9 model, mapped into the gauge-fixed basis
    let bytes = fs::read(v9.join("v9-z3-3x2-r9-identity.gguf")).expect("sealed v9 model");
    assert_eq!(hex_digest(&bytes), V9_R9_SHA, "sealed v9 model");
    let p9: Vec<i64> = gguf_model::read(&bytes)
        .expect("parse")
        .tensor("branch_0.params")
        .expect("p")
        .iter()
        .map(|&x| i64::from(x))
        .collect();
    let t32 = Torus::new(3, 2);
    let mut s9 = StateR::zero_state(12);
    NetV9 { params: p9 }.forward(&mut s9);
    let e_orbit = t32.energy_exact(&s9.v, 9).expect("physical");
    let mut x = vec![Big::zero(); blocks[1].2.dim];
    for (c, z) in s9.v.iter().enumerate() {
        if !z.is_zero() {
            let f = blocks[1].2.fix(&t32.digits(c));
            x[f] = x[f].add(z);
        }
    }
    let e_fixed = blocks[1].2.energy_exact(&x, 9).expect("physical");
    let q5 = e_orbit.0.mul(&e_fixed.1) == e_fixed.0.mul(&e_orbit.1)
        && milli_floor_q(&e_fixed, 0, 100_000_000) == Some(23_301);

    // the 3x3 certificate and the network
    let gf = &blocks[2].2;
    let count = param_count(gf);
    let (mut q6, mut q8, mut q9, mut q10, mut t8) = (true, true, true, true, false);
    let mut models: Vec<(String, i64, Option<i128>)> = Vec::new();
    for &r in &[9i64, 27, 81] {
        let e0 = e0_milli(sturm, &blocks[2].3, r, 36_000, &mut calls, &mut clean);
        let seed = vec![0i64; count];
        let mut s0 = StateR::zero_state(gf.free.len());
        NetV10 { gf, params: &seed }.forward(&mut s0);
        let start = gf.energy_exact(&s0.v, r).expect("physical");
        q6 &= start.0 == start.1.mul_i128(36);
        let (params, fixed, evals, used) = train(gf, &seed, r, sweeps);
        let net = NetV10 {
            gf,
            params: &params,
        };
        let mut s = StateR::zero_state(gf.free.len());
        let o = s.clone();
        net.forward(&mut s);
        let e = gf.energy_exact(&s.v, r).expect("physical");
        let d = s.scale();
        let norm_ok = s.norm_sq() == d.mul(&d);
        net.inverse(&mut s);
        let inv_ok = s.v == o.v.iter().map(|x| x.mul(&d).mul(&d)).collect::<Vec<_>>();
        q10 &= norm_ok && inv_ok;
        let floor = milli_floor_q(&e, 0, 100_000_000);
        q9 &= cmp_milli_q(&e, i128::from(e0 - 1)) >= 0;
        let within = |w: i64| cmp_milli_q(&e, i128::from(e0 + w)) < 0;
        if r == 9 {
            t8 = within(10);
        } else {
            q8 &= within(5);
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
                    ("seed", "IDENTITY".into()),
                    ("params", count.to_string()),
                    ("sweeps", used.to_string()),
                    ("evaluations", evals.to_string()),
                    (
                        "start_energy_milli_in",
                        milli_text(milli_floor_q(&start, 0, 100_000_000))
                    ),
                    ("certified_E0_in", format!("[{},{})_milli", e0 - 1, e0)),
                    ("energy_milli_in", milli_text(floor)),
                    (
                        "fixed_point_estimate_milli",
                        ((fixed * 1000) >> 40).to_string()
                    ),
                    (
                        "energy_minus_E0_upper_milli_floor",
                        floor.map_or("undecided".into(), |f| (f - i128::from(e0)).to_string())
                    ),
                    ("norm_exact", u8::from(norm_ok).to_string()),
                    ("inverse_exact", u8::from(inv_ok).to_string()),
                    ("b", bs.join(",")),
                    ("energy_numerator", e.0.dec()),
                    ("energy_denominator", e.1.dec()),
                ],
            )
        );
        let name = format!("v10-z3-3x3-r{r}-identity.gguf");
        let kv = vec![
            ("general.architecture".into(), Kv::Str(ARCH.into())),
            ("general.name".into(), Kv::Str(name.clone())),
            ("qnn.layer".into(), Kv::Str(LAYER.into())),
            (
                "qnn.amplitudes".into(),
                Kv::Str("real integers on the gauge-fixed free links, exact".into()),
            ),
            ("qnn.layers".into(), Kv::U32(2)),
            ("qnn.branches".into(), Kv::U32(1)),
            (
                "qnn.task".into(),
                Kv::Str("variational ground state, Z3 gauge theory, 3x3 torus".into()),
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
    let mut q11 = true;
    for (name, r, floor) in &models {
        let m = gguf_model::read(&fs::read(out.join(name)).expect("reload")).expect("parse");
        let params: Vec<i64> = m
            .tensor("branch_0.params")
            .expect("p")
            .iter()
            .map(|&x| i64::from(x))
            .collect();
        let mut s = StateR::zero_state(gf.free.len());
        NetV10 {
            gf,
            params: &params,
        }
        .forward(&mut s);
        let again = gf
            .energy_exact(&s.v, *r)
            .and_then(|e| milli_floor_q(&e, 0, 100_000_000));
        q11 &= again == *floor
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
        ("T8", t8, "r9_within_10_milli_of_certified_3x3_E0_upper"),
        (
            "QA",
            qa_all,
            "commutation_exact_and_blocks_w_self_adjoint_2x2_3x2_3x3",
        ),
        (
            "QB",
            qb_all,
            "offdiag_nonpositive_and_connected_2x2_3x2_3x3",
        ),
        ("Q1", q1, "3x3_block_has_753_classes"),
        ("Q2", q2, "2x2_block_E0_r9_in_sealed_interval"),
        (
            "Q3",
            q3,
            "3x2_block_has_46_classes_and_E0_in_sealed_v8_intervals",
        ),
        ("Q4", clean, "sturmfast_complete_and_unambiguous"),
        (
            "Q5",
            q5,
            "sealed_v9_r9_energy_reproduced_in_the_gauge_fixed_basis",
        ),
        ("Q6", q6, "identity_starts_at_exactly_36"),
        ("Q7", t8, "T8"),
        ("Q8", q8, "r27_r81_within_5_milli"),
        ("Q9", q9, "every_exact_energy_ge_certified_E0_lower"),
        ("Q10", q10, "exact_norm_and_inverse"),
        ("Q11", q11, "every_model_reloaded_reproduces_its_header"),
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
    fs::write(out.join("V10.hbp"), &text).expect("result");
    files.push(("V10.hbp".into(), text.len(), hex_digest(text.as_bytes())));
    let idx = index("V10INDEX", &files);
    fs::write(out.join("INDEX.hbi"), &idx).expect("index");
    let mut sums = String::new();
    for (f, _, h) in &files {
        sums.push_str(&format!("{h}  {f}\n"));
    }
    sums.push_str(&format!("{}  INDEX.hbi\n", hex_digest(idx.as_bytes())));
    fs::write(out.join("SHA256SUMS"), sums).expect("sums");
    println!("DONE|files={}|json=0", files.len() + 1);
}
