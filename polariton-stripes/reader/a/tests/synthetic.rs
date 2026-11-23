//! Stage A on synthetic streams: the aggregate against oracles written apart from the crate, every STOP path, the
//! planted faults, the table checks, the side file and the binary end to end. No engine runs here.

mod common;

use common::*;
use std::io::Write;
use std::process::{Command, Stdio};
use stripes_read_a::eng::{LOCK, MODE0, NV, VNAME};
use stripes_read_a::points;
use stripes_read_a::sha256::{hex, sha256};
use stripes_read_a::stream::{check_table, Head};

const NR: usize = 2;
const STEPS: [u64; 2] = [64, 128];

/// A stream at an excluded test point with designed cases: exchange and Klein atoms, axis and diagonal points,
/// boxes across an edge, uncertified signs, and one exchange atom with bi != 0.
fn designed(y: &str, k: usize, cmax: i64, seed: u64) -> Syn {
    let mut syn = Syn::new(27, y, &STEPS, ALL, true);
    let mut rng = Lcg(seed);
    for i in 0..k {
        let mut c = [0i64; 6];
        for x in c.iter_mut() {
            *x = rng.int(cmax);
        }
        if i % 37 == 5 {
            c[2] = c[0];
            c[3] = c[1];
        }
        if i % 41 == 7 {
            c[2] = c[1];
            c[3] = -c[0];
        }
        if i % 13 == 3 {
            c[1] = 0;
        }
        let mut s = sample(&mut rng, c, NV, NR, true);
        for vi in 0..NV {
            for r in 0..NR {
                let o = &mut s.obs[vi][r];
                let b = &mut s.rb[vi][r];
                match i % 11 {
                    1 => o[6] = 0,
                    2 => o[6] = o[5],
                    3 => o[6] = -o[5],
                    4 => o[5] = 0,
                    5 => {
                        o[5] = rng.int(3000);
                        o[6] = rng.int(3000);
                    }
                    6 => {
                        o[5] = 1_000_000;
                        o[6] = 414_214 + rng.int(3);
                        b[6] = 2;
                        b[7] = 2;
                    }
                    _ => {}
                }
                let exch = if vi == LOCK {
                    c[1] == 0
                } else {
                    c[0] == c[2] && c[1] == c[3]
                };
                if exch && i != 5 {
                    o[6] = 0;
                }
            }
        }
        syn.samples.push(s);
    }
    syn
}

fn check_against_oracles(syn: &Syn) {
    let text = syn.render();
    let rep = read(&["--point", "Tsyn", "--call", "0"], &text);
    assert_eq!(rep.code, 0, "{}", rep.out);
    let m = agg_map(&rep.out);
    let vs = vars(&syn.on);
    let mut checked = 0;
    for r in 0..NR {
        let step = syn.steps[r].to_string();
        for (vi, &v) in vs.iter().enumerate() {
            let name = VNAME[v].to_string();
            let want = oracle_vr(syn, vi, r);
            let vr = &m[&(
                "AGG_VR".to_string(),
                step.clone(),
                name.clone(),
                String::new(),
            )];
            for key in [
                "atoms",
                "xatoms",
                "xatom_bi_nz",
                "na_bi0",
                "sec",
                "amb",
                "br_pos",
                "br_neg",
                "br_amb",
                "bi_pos",
                "bi_neg",
                "bi_amb",
            ] {
                assert_eq!(vr[key], want[key], "step {step} {name} {key}");
                checked += 1;
            }
            let sum = &m[&(
                "AGG_SUM".to_string(),
                step.clone(),
                name.clone(),
                "all".to_string(),
            )];
            for (key, wk) in [
                ("br", "sum_br"),
                ("bi", "sum_bi"),
                ("br2", "sum_br2"),
                ("bi2", "sum_bi2"),
                ("bbr", "sum_bbr"),
                ("bbr2", "sum_bbr2"),
            ] {
                assert_eq!(sum[key], want[wk], "step {step} {name} {key}");
                checked += 1;
            }
            for n in stripes_read_a::agg::BLOCKS {
                let blk = &m[&(
                    "AGG_BLK".to_string(),
                    step.clone(),
                    name.clone(),
                    n.to_string(),
                )];
                let (k, s2) = oracle_blocks(syn, vi, r, n as usize);
                assert_eq!(blk["K"], k.to_string(), "{name} n={n}");
                assert_eq!(blk["s2"], s2.to_string(), "{name} n={n}");
                checked += 2;
            }
            if vi > 0 {
                let cmp = &m[&(
                    "AGG_CMP".to_string(),
                    step.clone(),
                    name.clone(),
                    String::new(),
                )];
                let (common, t) = oracle_cmp_br(syn, vi, r);
                let ts: Vec<String> = t.iter().map(|x| x.to_string()).collect();
                assert_eq!(cmp["common"], common.to_string());
                assert_eq!(cmp["br"], ts.join(":"), "{name}");
                checked += 2;
            }
        }
    }
    assert!(checked > 500);
}

#[test]
fn aggregate_equals_the_oracles_at_y_nonzero() {
    let syn = designed("1/40", 420, 6, 11);
    check_against_oracles(&syn);
    let rep = read(&["--point", "Tsyn", "--call", "0"], &syn.render());
    let m = agg_map(&rep.out);
    let key = (
        "AGG_VR".to_string(),
        "64".to_string(),
        "VNC".to_string(),
        String::new(),
    );
    assert_eq!(
        m[&key]["xatom_bi_nz"], "1",
        "the planted exchange atom with bi != 0 is counted"
    );
}

#[test]
fn aggregate_equals_the_oracles_at_y_zero() {
    let syn = designed("0", 420, 3, 12);
    check_against_oracles(&syn);
}

#[test]
fn lock_lattice_and_mode0_rows() {
    let mut syn = designed("0", 200, 5, 13);
    for s in syn.samples.iter_mut() {
        let (a, b) = (s.c[0] as i128, s.c[1] as i128);
        for r in 0..NR {
            s.obs[LOCK][r][5] = ((a * a - b * b) * 1000) as i64;
            s.obs[LOCK][r][6] = (2 * a * b * 1000) as i64;
            s.rb[LOCK][r][6] = 1;
            s.rb[LOCK][r][7] = 1;
            s.obs[MODE0][r][5] = s.obs[0][r][5];
            s.obs[MODE0][r][6] = s.obs[0][r][6];
            s.rb[MODE0][r][6] = s.rb[0][r][6];
            s.rb[MODE0][r][7] = s.rb[0][r][7];
        }
    }
    let rep = read(&["--point", "Tsyn", "--call", "0"], &syn.render());
    assert_eq!(rep.code, 0, "{}", rep.out);
    let lock: Vec<&str> = rep
        .out
        .lines()
        .filter(|l| l.starts_with("AGG_LOCK|"))
        .collect();
    assert_eq!(lock.len(), 2);
    for l in lock {
        assert!(l.contains("|mis=0|"), "{l}");
        assert!(!l.contains("|cert=0|"), "{l}");
    }
    let m = agg_map(&rep.out);
    let cmp = &m[&(
        "AGG_CMP".to_string(),
        "64".to_string(),
        "MODE0".to_string(),
        String::new(),
    )];
    assert_eq!(cmp["mis"], "0");
    assert_eq!(cmp["cert2"], cmp["cert2_big_any"]);
    let lat: Vec<&str> = rep
        .out
        .lines()
        .filter(|l| l.starts_with("AGG_LAT|"))
        .collect();
    assert_eq!(lat.len(), 1);
}

fn small() -> Syn {
    designed("1/40", 24, 6, 21)
}

fn replace_nth(text: &str, prefix: &str, nth: usize, f: &dyn Fn(&str) -> String) -> String {
    let mut k = 0;
    let mut out = String::new();
    for line in text.lines() {
        if line.starts_with(prefix) {
            if k == nth {
                out.push_str(&f(line));
            } else {
                out.push_str(line);
            }
            k += 1;
        } else {
            out.push_str(line);
        }
        out.push('\n');
    }
    out
}

fn set_field(line: &str, key: &str, val: &str) -> String {
    line.split('|')
        .map(|t| match t.split_once('=') {
            Some((k, _)) if k == key => format!("{k}={val}"),
            _ => t.to_string(),
        })
        .collect::<Vec<_>>()
        .join("|")
}

fn bump(line: &str, key: &str) -> String {
    let v: i128 = line
        .split('|')
        .find_map(|t| t.strip_prefix(&format!("{key}=")))
        .expect("key")
        .parse()
        .expect("int");
    set_field(line, key, &(v + 1).to_string())
}

/// `key=` set to `val` on every row that has the key.
fn set_all(text: &str, key: &str, val: &str) -> String {
    let mut out = String::new();
    for line in text.lines() {
        out.push_str(&set_field(line, key, val));
        out.push('\n');
    }
    out
}

/// The `:`-joined list `key` with `f` applied to its entries.
fn edit_list(line: &str, key: &str, f: &dyn Fn(&mut Vec<i64>)) -> String {
    let text = line
        .split('|')
        .find_map(|t| t.strip_prefix(&format!("{key}=")))
        .expect("key")
        .to_string();
    let mut p: Vec<i64> = text.split(':').map(|x| x.parse().expect("i")).collect();
    f(&mut p);
    let t: Vec<String> = p.iter().map(|x| x.to_string()).collect();
    set_field(line, key, &t.join(":"))
}

/// A VNC-only stream of 300 draws at Tsyn, with no MODE0 (so every rot is 2^40:0).
fn vnc_only() -> Syn {
    let mut vnc = Syn::new(
        27,
        "1/40",
        &STEPS,
        [true, false, false, false, false, false, false],
        false,
    );
    let mut rng = Lcg(31);
    for _ in 0..300 {
        let mut c = [0i64; 6];
        for x in c.iter_mut() {
            *x = rng.int(4);
        }
        vnc.samples.push(sample(&mut rng, c, 1, NR, false));
    }
    vnc
}

/// The faulty streams of every_stop_path, each with the STOP reason it must give at a test id.
fn stop_cases(good: &str) -> Vec<(&'static str, String)> {
    let good = good.to_string();
    let lines: Vec<&str> = good.lines().collect();
    let without_done = joined(lines[..lines.len() - 1].iter().copied());
    let mid = good[..good.len() / 2].rfind('\n').expect("newline") + 10;
    let half = &good[..mid];
    let cut_line = &good[..good.len() - 7];
    vec![
        (
            "head_version",
            replace_nth(&good, "TWB_HEAD|", 0, &|l| set_field(l, "version", "0.3.0")),
        ),
        (
            "head_binary_sha256",
            replace_nth(&good, "TWB_HEAD|", 0, &|l| {
                set_field(l, "binary_sha256", "75530df9")
            }),
        ),
        (
            "head_source_sha256",
            replace_nth(&good, "TWB_HEAD|", 0, &|l| {
                set_field(l, "source_sha256", "x")
            }),
        ),
        (
            "head_reserved",
            replace_nth(&good, "TWB_HEAD|", 0, &|l| set_field(l, "reserved", "1")),
        ),
        (
            "head_guard",
            replace_nth(&good, "TWB_HEAD|", 0, &|l| set_field(l, "guard", "lifted")),
        ),
        (
            "head_float_used",
            replace_nth(&good, "TWB_HEAD|", 0, &|l| set_field(l, "float_used", "1")),
        ),
        (
            "head_seed",
            replace_nth(&good, "TWB_HEAD|", 0, &|l| bump(l, "seed")),
        ),
        (
            "field_value",
            replace_nth(&good, "TWB_HEAD|", 0, &|l| set_field(l, "threads", "2")),
        ),
        (
            "no_VNC",
            replace_nth(&good, "TWB_HEAD|", 0, &|l| {
                set_field(l, "mask", "V1,V0,RN,FLIP,LOCK,MODE0,NL")
            }),
        ),
        (
            "head_mask",
            replace_nth(&good, "TWB_HEAD|", 0, &|l| {
                set_field(l, "mask", "V1,VNC,V0,RN,FLIP,LOCK,MODE0,NL")
            }),
        ),
        (
            "head_count",
            replace_nth(&good, "TWB_HEAD|", 0, &|l| set_field(l, "samples", "23")),
        ),
        (
            "head_count",
            replace_nth(&good, "TWB_HEAD|", 0, &|l| {
                set_field(&set_field(l, "count", "0"), "samples", "0")
            }),
        ),
        (
            "summary_mismatch",
            replace_nth(&good, "TWB|", 0, &|l| bump(l, "br")),
        ),
        (
            "summary_mismatch",
            replace_nth(&good, "TWB|", 3, &|l| bump(l, "bi2")),
        ),
        (
            "summary_mismatch",
            replace_nth(&good, "TWB_ROUND|", 2, &|l| bump(l, "rb_br")),
        ),
        (
            "summary_mismatch",
            replace_nth(&good, "TWB_ROUND|", 2, &|l| bump(l, "eps_max")),
        ),
        (
            "summary_mismatch",
            replace_nth(&good, "TWENS|", 1, &|l| bump(l, "qdzr")),
        ),
        (
            "summary_mismatch",
            replace_nth(&good, "TWPAIR|", 0, &|l| bump(l, "q3")),
        ),
        (
            "summary_mismatch",
            replace_nth(&good, "TWB_PAIR|", 9, &|l| bump(l, "d")),
        ),
        (
            "summary_mismatch",
            replace_nth(&good, "TWB_PAIR_ROUND|", 4, &|l| bump(l, "rb_d2")),
        ),
        (
            "summary_mismatch",
            replace_nth(&good, "TWB_DUMP_OBS|", 30, &|l| bump(l, "br")),
        ),
        (
            "summary_mismatch",
            replace_nth(&good, "TWB_DUMP_RB|", 30, &|l| bump(l, "b_bi")),
        ),
        (
            "float_used",
            replace_nth(&good, "TWB|", 2, &|l| set_field(l, "float_used", "1")),
        ),
        (
            "start_mismatch",
            replace_nth(&good, "TWB_DUMP_INIT|", 3, &|l| {
                let s = l
                    .split('|')
                    .find_map(|t| t.strip_prefix("s="))
                    .expect("s")
                    .to_string();
                let mut p: Vec<i64> = s.split(':').map(|x| x.parse().expect("i")).collect();
                p[2] += 1;
                let t: Vec<String> = p.iter().map(|x| x.to_string()).collect();
                set_field(l, "s", &t.join(":"))
            }),
        ),
        (
            "start_mismatch",
            replace_nth(&good, "TWB_DUMP_SAMPLE|", 2, &|l| {
                let g = l
                    .split('|')
                    .find_map(|t| t.strip_prefix("g="))
                    .expect("g")
                    .to_string();
                let mut p: Vec<i64> = g.split(':').map(|x| x.parse().expect("i")).collect();
                p[0] += 1 << 35;
                let t: Vec<String> = p.iter().map(|x| x.to_string()).collect();
                set_field(l, "g", &t.join(":"))
            }),
        ),
        (
            "draw_not_a_coin_count",
            replace_nth(&good, "TWB_DUMP_SAMPLE|", 2, &|l| {
                let g = l
                    .split('|')
                    .find_map(|t| t.strip_prefix("g="))
                    .expect("g")
                    .to_string();
                let mut p: Vec<i64> = g.split(':').map(|x| x.parse().expect("i")).collect();
                p[5] += 1;
                let t: Vec<String> = p.iter().map(|x| x.to_string()).collect();
                set_field(l, "g", &t.join(":"))
            }),
        ),
        (
            "linear_control_mismatch",
            replace_nth(&good, "TWB_DUMP_OBS|", 5, &|l| bump(l, "zcr")),
        ),
        (
            "start_bound_mismatch",
            replace_nth(&good, "TWB_DUMP_IB|", 4, &|l| bump(l, "seeds")),
        ),
        (
            "eta_mismatch",
            replace_nth(&good, "TWB_DUMP_IB|", 4, &|l| bump(l, "eta")),
        ),
        (
            "sample_index",
            replace_nth(&good, "TWB_DUMP_SAMPLE|", 3, &|l| bump(l, "idx")),
        ),
        (
            "field_value",
            replace_nth(&good, "TWB_DUMP_OBS|", 3, &|l| set_field(l, "step", "65")),
        ),
        (
            "bad_integer",
            replace_nth(&good, "TWB_DUMP_OBS|", 3, &|l| set_field(l, "bi", "+5")),
        ),
        (
            "row_key",
            replace_nth(&good, "TWB_DUMP_OBS|", 3, &|l| l.replace("|xw=", "|xW=")),
        ),
        (
            "row_long",
            replace_nth(&good, "TWB_DONE|", 0, &|l| format!("{l}|x=1")),
        ),
        (
            "row_kind",
            replace_nth(&good, "TWB_DUMP_RB|", 7, &|l| {
                l.replace("TWB_DUMP_RB", "TWB_DUMP_OBS")
            }),
        ),
        (
            "field_value",
            replace_nth(&good, "TWB_DONE|", 0, &|l| set_field(l, "n", "23")),
        ),
        (
            "rows_after_TWB_DONE",
            format!("{good}TWB_DONE|n=24|records=2|mask=VNC|float_used=0|json=0\n"),
        ),
        ("truncated", without_done),
        ("unterminated_last_line", half.to_string()),
        ("unterminated_last_line", cut_line.to_string()),
        ("empty_stream", String::new()),
        ("first_row_not_TWB_HEAD", joined(good.lines().skip(1))),
        (
            "non_printable_byte",
            good.replacen("|json=0\n", "|json=0\r\n", 1),
        ),
        (
            "bad_list",
            replace_nth(&good, "TWB_DUMP_SAMPLE|", 2, &|l| {
                edit_list(l, "g", &|p| {
                    p.pop();
                })
            }),
        ),
        (
            "head_steps_not_increasing",
            replace_nth(&good, "TWB_HEAD|", 0, &|l| set_field(l, "steps", "128,64")),
        ),
        (
            "control_seed_mismatch",
            replace_nth(&good, "TWB_DUMP_INIT|", 3, &|l| {
                edit_list(l, "uv", &|p| p[0] += 1)
            }),
        ),
        (
            "h_differs",
            replace_nth(&good, "TWB|", 2, &|l| bump(l, "h")),
        ),
        (
            "h_mismatch",
            set_all(&good, "h", &(stripes_read_a::eng::h_of(27) + 1).to_string()),
        ),
        (
            "ctrl_differs_within_record",
            replace_nth(&good, "TWB|", 1, &|l| set_field(l, "ctrl", "0:0:1")),
        ),
        (
            "start_rebuild",
            replace_nth(&good, "TWB_DUMP_SAMPLE|", 2, &|l| {
                edit_list(l, "g", &|p| {
                    p[0] = 2048 << 35;
                    p[1] = 2048 << 35;
                })
            }),
        ),
        (
            "rot_without_MODE0",
            replace_nth(&vnc_only().render(), "TWB_DUMP_SAMPLE|", 4, &|l| {
                edit_list(l, "rot", &|p| p[1] = 1)
            }),
        ),
    ]
}

/// The argument faults of every_stop_path: (arguments, STOP reason).
fn arg_cases() -> Vec<(Vec<&'static str>, &'static str)> {
    vec![
        (vec!["--point", "Tsyn"], "usage"),
        (vec!["--point", "Tsyn", "--call", "-1"], "usage"),
        (vec!["--point", "Tsyn", "--call", "007"], "usage"),
        (vec!["--point", "Tsyn", "--call", "0", "--x", "1"], "usage"),
        (vec!["--point", "P99", "--call", "0"], "unknown_point"),
        (vec!["--point", "P08", "--call", "0"], "side_file_required"),
        (vec!["--point", "P13", "--call", "63"], "side_file_required"),
        (vec!["--point", "X1", "--call", "0"], "table_mismatch"),
        (
            vec!["--point", "X1", "--call", "8"],
            "table_call_out_of_range",
        ),
        (
            vec![
                "--point",
                "Tsyn",
                "--call",
                "0",
                "--side",
                "/dev/null/side.bin",
            ],
            "side_write",
        ),
    ]
}

/// One probe: what it plants, the arguments, the stream, and the STOP reason both readers give (None: a block).
type Probe = (
    &'static str,
    Vec<&'static str>,
    String,
    Option<&'static str>,
);

/// The probes of the PR #18 review (M7): the first 16 gave a different outcome, reason or line in stage A and in
/// check_a.py before the fix; the last 3 are controls on which the two already agreed. At Tsyn and at X1 only.
fn probe_cases() -> Vec<Probe> {
    let tsyn = vec!["--point", "Tsyn", "--call", "0"];
    let x1 = vec!["--point", "X1", "--call", "2"];
    let good = small().render();
    let p = points::find("X1").expect("X1");
    let x1_text = table_stream(p, 2, &STEPS, 106).render();
    let none_seed = stripes_read_a::sha256::seed_u64("none").to_string();
    let two_faults = replace_nth(
        &replace_nth(&good, "TWB_DUMP_INIT|", 3, &|l| {
            edit_list(l, "s", &|p| p[2] += 1)
        }),
        "TWB_DONE|",
        0,
        &|l| set_field(l, "n", "23"),
    );
    let lone_head = joined(std::iter::once("TWB_HEAD").chain(good.lines().skip(1)));
    let key_alone = replace_nth(&good, "TWB_DUMP_OBS|", 3, &|l| {
        l.split('|')
            .map(|t| if t.starts_with("xw=") { "xw" } else { t })
            .collect::<Vec<_>>()
            .join("|")
    });
    vec![
        (
            "y=-0 on every row",
            tsyn.clone(),
            set_all(&good, "y", "-0"),
            Some("bad_rational"),
        ),
        (
            "y=+1/40",
            tsyn.clone(),
            set_all(&good, "y", "+1/40"),
            Some("bad_rational"),
        ),
        (
            "y=01/40",
            tsyn.clone(),
            set_all(&good, "y", "01/40"),
            Some("bad_rational"),
        ),
        (
            "y=1/040",
            tsyn.clone(),
            set_all(&good, "y", "1/040"),
            Some("bad_rational"),
        ),
        (
            "delta=+1/4",
            tsyn.clone(),
            set_all(&good, "delta", "+1/4"),
            Some("bad_rational"),
        ),
        (
            "u=+1",
            tsyn.clone(),
            set_all(&good, "u", "+1"),
            Some("bad_rational"),
        ),
        (
            "seed_string=none with seed = sha256(none) on every row",
            tsyn.clone(),
            set_all(&set_all(&good, "seed_string", "none"), "seed", &none_seed),
            Some("head_seed"),
        ),
        (
            "dtden=0",
            tsyn.clone(),
            set_all(&good, "dtden", "0"),
            Some("head_dtden"),
        ),
        (
            "N=1",
            tsyn.clone(),
            set_all(&good, "N", "1"),
            Some("head_N"),
        ),
        (
            "a token without = that is not the key",
            tsyn.clone(),
            replace_nth(&good, "TWB_DUMP_OBS|", 3, &|l| l.replacen("|xw=", "|xw", 1)),
            Some("row_field_without_value"),
        ),
        (
            "two faults: a start, then TWB_DONE n",
            tsyn.clone(),
            two_faults,
            Some("field_value"),
        ),
        (
            "a first row TWB_HEAD alone",
            tsyn.clone(),
            lone_head,
            Some("row_short"),
        ),
        (
            "dtden=32 at X1",
            x1.clone(),
            set_all(&x1_text, "dtden", "32"),
            Some("table_mismatch"),
        ),
        (
            "y=-0 at X1",
            x1.clone(),
            set_all(&x1_text, "y", "-0"),
            Some("bad_rational"),
        ),
        (
            "ctrl 1:0:0 at X1",
            x1.clone(),
            set_all(&x1_text, "ctrl", "1:0:0"),
            Some("table_mismatch"),
        ),
        (
            "y with a 43-digit denominator",
            tsyn.clone(),
            set_all(&good, "y", "1/1000000000000000000000000000000000000000000"),
            None,
        ),
        (
            "control: the token xw alone",
            tsyn.clone(),
            key_alone,
            Some("row_field_without_value"),
        ),
        (
            "control: y=0/7",
            tsyn.clone(),
            set_all(&good, "y", "0/7"),
            None,
        ),
        ("control: y=-1/40", tsyn, set_all(&good, "y", "-1/40"), None),
    ]
}

/// The draws at a table point (review N8) and the rot bound (review N9). At a table point stage A rebuilds g, rot and
/// eta from (seed, idx); each stream below is consistent in every other way (its starts and sums are rendered from the
/// moved draw), so only that rebuild sees it. At Tsyn a rot component above 2^41 is refused before m() takes it; one
/// of exactly 2^41 passes that check and fails the start rebuild (the rot was edited in the text).
fn draw_cases() -> Vec<Probe> {
    let x1 = vec!["--point", "X1", "--call", "2"];
    let x0 = vec!["--point", "X0", "--call", "5", "--side", "@SIDE@"];
    let tsyn = vec!["--point", "Tsyn", "--call", "0"];
    let px1 = points::find("X1").expect("X1");
    let px0 = points::find("X0").expect("X0");
    let mut g_moved = table_stream(px1, 2, &STEPS, 106);
    g_moved.samples[7].c[0] += 1;
    let mut rot_moved = table_stream(px0, 5, &STEPS, 107);
    rot_moved.samples[9].rot.0 += 1;
    let mut eta_moved = table_stream(px0, 5, &STEPS, 107);
    eta_moved.samples[11].eta += 1;
    let good = small().render();
    let rot_text = |v: &str| replace_nth(&good, "TWB_DUMP_SAMPLE|", 3, &|l| set_field(l, "rot", v));
    vec![
        (
            "g0 of sample 7 moved by 2^35 at X1",
            x1,
            g_moved.render(),
            Some("draw_mismatch"),
        ),
        (
            "rot of sample 9 moved by 1 at X0",
            x0.clone(),
            rot_moved.render(),
            Some("draw_mismatch"),
        ),
        (
            "eta of sample 11 moved by 1 at X0",
            x0,
            eta_moved.render(),
            Some("draw_mismatch"),
        ),
        (
            "rot 2^41+1:0 at Tsyn",
            tsyn.clone(),
            rot_text("2199023255553:0"),
            Some("rot_out_of_range"),
        ),
        (
            "rot 0:-(2^41+1) at Tsyn",
            tsyn.clone(),
            rot_text("0:-2199023255553"),
            Some("rot_out_of_range"),
        ),
        (
            "rot 2^41:0 at Tsyn passes the bound",
            tsyn,
            rot_text("2199023255552:0"),
            Some("start_mismatch"),
        ),
    ]
}

#[test]
fn draws_rebuilt_at_table_points_and_rot_bounded() {
    let side = std::path::PathBuf::from(env!("CARGO_TARGET_TMPDIR")).join("draws.side");
    let side = side.to_str().expect("utf8 path").to_string();
    for (what, args, text, want) in draw_cases() {
        let args: Vec<&str> = args
            .iter()
            .map(|a| if *a == "@SIDE@" { side.as_str() } else { a })
            .collect();
        let rep = read(&args, &text);
        assert_eq!(rep.code, 3, "{what}: {}", rep.out);
        assert_eq!(
            stop_reason(&rep.out).as_deref(),
            want,
            "{what}: {}",
            rep.out
        );
    }
    for (id, call, with_side) in [("X1", 2u64, false), ("X0", 5, true), ("X1", 7, true)] {
        let p = points::find(id).expect("point");
        let c = call.to_string();
        let mut args = vec!["--point", id, "--call", c.as_str()];
        if with_side {
            args.extend(["--side", side.as_str()]);
        }
        let rep = read(&args, &table_stream(p, call, &STEPS, 108).render());
        assert_eq!(rep.code, 0, "{id}: {}", rep.out);
        assert!(rep.out.contains("|table=checked|"), "{id}");
    }
}

#[test]
fn review_probes_read_as_stated() {
    let cases = probe_cases();
    assert_eq!(cases.len(), 19);
    for (what, args, text, want) in &cases {
        let rep = read(args, text);
        match want {
            Some(reason) => {
                assert_eq!(rep.code, 3, "{what}: {}", rep.out);
                assert_eq!(
                    stop_reason(&rep.out).as_deref(),
                    Some(*reason),
                    "{what}: {}",
                    rep.out
                );
            }
            None => assert_eq!(rep.code, 0, "{what}: {}", rep.out),
        }
    }
    let two = &cases[10].2;
    let line = two
        .lines()
        .position(|l| l.starts_with("TWB_DONE|"))
        .expect("done")
        + 1;
    let rep = read(&cases[10].1, two);
    assert!(
        rep.out.contains(&format!("|line={line}|")),
        "the parse fault comes first: {}",
        rep.out
    );
    let y0 = read(&cases[17].1, &cases[17].2);
    assert!(y0.out.contains("|y=0/7|y_zero=1|"), "{}", y0.out);
}

#[test]
fn every_stop_path() {
    let good = small().render();
    let ok = read(&["--point", "Tsyn", "--call", "0"], &good);
    assert_eq!(ok.code, 0, "{}", ok.out);
    let cases = stop_cases(&good);
    for (want, text) in &cases {
        let rep = read(&["--point", "Tsyn", "--call", "0"], text);
        assert_eq!(rep.code, 3, "{want}: {}", rep.out);
        assert_eq!(stop_reason(&rep.out).as_deref(), Some(*want), "{}", rep.out);
        assert_eq!(rep.out.lines().count(), 1, "a STOP prints one row only");
    }
    for (args, want) in arg_cases() {
        let rep = read(&args, &good);
        assert_eq!(
            stop_reason(&rep.out).as_deref(),
            Some(want),
            "{args:?}: {}",
            rep.out
        );
    }
}

#[test]
fn a_stop_still_hashes_the_whole_input() {
    let good = small().render();
    let bad = replace_nth(&good, "TWB_HEAD|", 0, &|l| set_field(l, "version", "0.3.0"));
    let rep = read(&["--point", "Tsyn", "--call", "0"], &bad);
    let sha = hex(&sha256(bad.as_bytes()));
    assert!(
        rep.out.contains(&format!("|stdin_sha256={sha}|")),
        "{}",
        rep.out
    );
    assert!(rep
        .out
        .contains(&format!("|stdin_lines={}|", bad.lines().count())));
    assert!(rep.out.contains("|line=1|"));
}

#[test]
fn planted_exchange_atom_faults() {
    let syn = small();
    let good = syn.render();
    let vi = LOCK;
    let s = syn
        .samples
        .iter()
        .position(|s| s.c[1] == 0)
        .expect("a LOCK exchange atom in the small stream");
    assert_eq!(syn.samples[s].obs[vi][0][6], 0);
    let idx = format!("TWB_DUMP_OBS|idx={s}|variant=LOCK|step=64|");
    let row = good
        .lines()
        .find(|l| l.starts_with(&idx))
        .expect("row")
        .to_string();
    let lit = good.replacen(&row, &row.replace("|bi=0|", "|bi=-0|"), 1);
    let rep = read(&["--point", "Tsyn", "--call", "0"], &lit);
    assert_eq!(
        stop_reason(&rep.out).as_deref(),
        Some("bad_integer"),
        "literal sign flip -0"
    );
    let stale = good.replacen(&row, &row.replace("|bi=0|", "|bi=-7|"), 1);
    let rep = read(&["--point", "Tsyn", "--call", "0"], &stale);
    assert_eq!(
        stop_reason(&rep.out).as_deref(),
        Some("summary_mismatch"),
        "{}",
        rep.out
    );
    assert!(
        rep.out.contains("row=TWB,step=64,of=LOCK,field=bi,"),
        "{}",
        rep.out
    );
    let mut planted = syn.clone();
    planted.samples[s].obs[vi][0][6] = -7;
    let rep = read(&["--point", "Tsyn", "--call", "0"], &planted.render());
    assert_eq!(rep.code, 0, "{}", rep.out);
    let m = agg_map(&rep.out);
    let base = agg_map(&read(&["--point", "Tsyn", "--call", "0"], &good).out);
    let key = (
        "AGG_VR".to_string(),
        "64".to_string(),
        "LOCK".to_string(),
        String::new(),
    );
    let before: u64 = base[&key]["xatom_bi_nz"].parse().expect("n");
    let after: u64 = m[&key]["xatom_bi_nz"].parse().expect("n");
    assert_eq!(
        after,
        before + 1,
        "a consistent stream with the fault: the falsifier count rises by one"
    );
}

#[test]
fn agg_end_hash_covers_every_row_before_it() {
    let rep = read(&["--point", "Tsyn", "--call", "0"], &small().render());
    let lines: Vec<&str> = rep.out.lines().collect();
    let end = lines.last().expect("end");
    assert!(end.starts_with("AGG_END|"));
    let body = joined(lines[..lines.len() - 1].iter().copied());
    assert!(end.contains(&format!("|agg_sha256={}|", hex(&sha256(body.as_bytes())))));
    assert!(end.contains(&format!("|agg_lines={}|", lines.len() - 1)));
    let vr = lines
        .iter()
        .position(|l| l.starts_with("AGG_VR|"))
        .expect("vr");
    let swapped = body.replacen(lines[vr], &lines[vr].replacen("|sec=", "|sec=9", 1), 1);
    assert!(
        !end.contains(&hex(&sha256(swapped.as_bytes()))),
        "an edited sector count fails the hash"
    );
}

fn head_for(p: &points::Point, call: u64, steps: &[u64]) -> Head {
    let (on, nl) = if call < p.all_calls {
        ([true; NV], true)
    } else {
        ([true, false, false, false, false, false, false], false)
    };
    Head {
        line: String::new(),
        n: p.n,
        delta: p.delta.to_string(),
        u: "1".to_string(),
        y: p.y.to_string(),
        y_zero: p.y == "0",
        seed: 0,
        seed_string: p.seed_string(),
        start: 4096 * call,
        count: 4096,
        dtden: 64,
        steps: steps.to_vec(),
        mask: p.mask(call).to_string(),
        on,
        nl,
    }
}

#[test]
fn table_checks_at_every_point() {
    for p in points::POINTS.iter() {
        let calls = [0, p.all_calls.saturating_sub(1), p.all_calls, p.calls() - 1];
        for call in calls.into_iter().filter(|&c| c < p.calls()) {
            assert!(
                check_table(&head_for(p, call, p.steps), p, call).is_ok(),
                "{} {call}",
                p.id
            );
            assert!(
                check_table(&head_for(p, call, &p.steps[..1]), p, call).is_ok(),
                "prefix {}",
                p.id
            );
        }
        let h = head_for(p, 0, p.steps);
        assert!(
            check_table(&h, p, p.calls()).is_err(),
            "call out of range {}",
            p.id
        );
        assert!(
            check_table(&h, p, 1).is_err(),
            "start of another call {}",
            p.id
        );
        let mut bad = head_for(p, 0, p.steps);
        bad.seed_string.push('x');
        assert!(check_table(&bad, p, 0).is_err());
        let mut bad = head_for(p, 0, p.steps);
        bad.mask = if bad.mask == points::MASK_VNC {
            points::MASK_ALL
        } else {
            points::MASK_VNC
        }
        .to_string();
        assert!(check_table(&bad, p, 0).is_err(), "mask {}", p.id);
        let mut bad = head_for(p, 0, p.steps);
        bad.steps = p.steps[1..].to_vec();
        assert!(
            check_table(&bad, p, 0).is_err(),
            "steps not a prefix {}",
            p.id
        );
        let mut longer = p.steps.to_vec();
        longer.push(320);
        assert!(check_table(&head_for(p, 0, &longer), p, 0).is_err());
        let mut bad = head_for(p, 0, p.steps);
        bad.y = "1/7".to_string();
        assert!(check_table(&bad, p, 0).is_err());
    }
}

#[test]
fn side_file_layout() {
    let syn = small();
    let dir = std::path::PathBuf::from(env!("CARGO_TARGET_TMPDIR"));
    let path = dir.join("synthetic.side");
    let p = path.to_str().expect("utf8 path");
    let rep = read(
        &["--point", "Tsyn", "--call", "0", "--side", p],
        &syn.render(),
    );
    assert_eq!(rep.code, 0, "{}", rep.out);
    let data = std::fs::read(&path).expect("side file");
    let sha = hex(&sha256(&data));
    let row = rep
        .out
        .lines()
        .find(|l| l.starts_with("AGG_SIDE|"))
        .expect("side row");
    assert!(
        row.contains(&format!("|bytes={}|sha256={sha}|", data.len())),
        "{row}"
    );
    assert!(row.contains("|indices=24|variants=VNC,V1,V0,RN,FLIP,LOCK,MODE0|steps=64,128|"));
    let u32_at = |o: usize| u32::from_le_bytes([data[o], data[o + 1], data[o + 2], data[o + 3]]);
    let u64_at = |o: usize| u64::from_le_bytes(data[o..o + 8].try_into().expect("8"));
    assert_eq!(&data[..8], b"STRPSIDE");
    assert_eq!(
        (
            u32_at(8),
            u32_at(12),
            u32_at(16),
            u32_at(20),
            u32_at(24),
            u32_at(28)
        ),
        (1, 7, 127, 2, 64, 128)
    );
    assert_eq!((u64_at(32), u64_at(40)), (0, 24));
    assert_eq!(data.len(), 64 + 24 * (8 + 7 * 2 * 16));
    let per = 8 + 7 * 2 * 16;
    for (k, s) in syn.samples.iter().enumerate() {
        let o = 64 + k * per;
        let c = s.c;
        let flags = u64::from(oracle_atom(&c, 0, true))
            | u64::from(oracle_xatom(&c, 0)) << 1
            | u64::from(oracle_atom(&c, LOCK, true)) << 2
            | u64::from(oracle_xatom(&c, LOCK)) << 3;
        assert_eq!(u64_at(o), flags);
        for vi in 0..NV {
            for r in 0..NR {
                let q = o + 8 + (vi * NR + r) * 16;
                assert_eq!(u64_at(q) as i64, s.obs[vi][r][5]);
                assert_eq!(u64_at(q + 8) as u128, s.rb[vi][r][6]);
            }
        }
    }
}

#[test]
fn the_binary_end_to_end() {
    let exe = env!("CARGO_BIN_EXE_stripes-read-a");
    let run = |args: &[&str], input: &str| {
        let mut child = Command::new(exe)
            .args(args)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .expect("spawn");
        child
            .stdin
            .take()
            .expect("stdin")
            .write_all(input.as_bytes())
            .expect("write");
        child.wait_with_output().expect("wait")
    };
    let good = small().render();
    let out = run(&["--point", "Tsyn", "--call", "0"], &good);
    assert_eq!(out.status.code(), Some(0));
    let text = String::from_utf8(out.stdout).expect("utf8");
    assert_eq!(text, read(&["--point", "Tsyn", "--call", "0"], &good).out);
    assert!(out.stderr.is_empty());
    let bad = replace_nth(&good, "TWB|", 0, &|l| bump(l, "br"));
    let out = run(&["--point", "Tsyn", "--call", "0"], &bad);
    assert_eq!(out.status.code(), Some(3));
    let text = String::from_utf8(out.stdout).expect("utf8");
    assert!(text.starts_with("STOP|reader=stripes-read-a|"), "{text}");
    assert_eq!(String::from_utf8(out.stderr).expect("utf8"), text);
    let out = run(&[], "");
    assert_eq!(out.status.code(), Some(3));
}

/// A stream of 4096 samples at a table point or an excluded point, with the call's mask and the records given. The
/// draws g, rot and eta are the engine's from (seed, idx) (stage A rebuilds them at a table point, review N8); the
/// observables and bounds are LCG values (no engine runs).
fn table_stream(p: &points::Point, call: u64, steps: &[u64], seed: u64) -> Syn {
    let all = call < p.all_calls;
    let on = if all {
        [true; NV]
    } else {
        [true, false, false, false, false, false, false]
    };
    let mut syn = Syn::new(p.n, p.y, steps, on, all);
    syn.delta = p.delta.to_string();
    syn.seed_string = p.seed_string();
    syn.start = 4096 * call;
    let vs = vars(&on);
    let mut rng = Lcg(seed);
    for i in 0..4096u64 {
        let (g, rot, eta) = stripes_read_a::rng::draws(syn.seed(), syn.start + i, on[MODE0]);
        let c = g.map(|x| x >> 35);
        let mut s = sample(&mut rng, c, vs.len(), steps.len(), on[MODE0]);
        s.rot = (rot[0], rot[1]);
        s.eta = eta;
        for (vi, &v) in vs.iter().enumerate() {
            let exch = if v == LOCK {
                c[1] == 0
            } else {
                c[0] == c[2] && c[1] == c[3]
            };
            for r in 0..steps.len() {
                if exch {
                    s.obs[vi][r][6] = 0;
                }
                if i % 17 == 2 {
                    s.rb[vi][r][6] = 1 << 37;
                }
            }
        }
        syn.samples.push(s);
    }
    syn
}

/// Writes the synthetic streams of the independent check (reader/check/compare.py) to $STRIPES_EMIT_DIR: per case
/// NAME.args (one argument per line, @SIDE@ for a side-file path) and NAME.txt (the stream). No engine runs here.
#[test]
#[ignore]
fn emit_streams_for_the_independent_check() {
    let dir = std::path::PathBuf::from(
        std::env::var("STRIPES_EMIT_DIR").expect("set STRIPES_EMIT_DIR to an empty folder"),
    );
    std::fs::create_dir_all(&dir).expect("emit dir");
    let put = |name: &str, args: &[&str], text: &str| {
        std::fs::write(dir.join(format!("{name}.args")), args.join("\n") + "\n").expect("args");
        std::fs::write(dir.join(format!("{name}.txt")), text).expect("txt");
    };
    let tsyn = ["--point", "Tsyn", "--call", "0"];
    let side = ["--point", "Tsyn", "--call", "0", "--side", "@SIDE@"];
    put("good_y40", &tsyn, &designed("1/40", 420, 6, 11).render());
    put("good_y0", &tsyn, &designed("0", 420, 3, 12).render());
    put("good_small_side", &side, &small().render());
    let mut lock = designed("0", 200, 5, 13);
    for s in lock.samples.iter_mut() {
        let (a, b) = (s.c[0] as i128, s.c[1] as i128);
        for r in 0..NR {
            s.obs[LOCK][r][5] = ((a * a - b * b) * 1000) as i64;
            s.obs[LOCK][r][6] = (2 * a * b * 1000) as i64;
            s.rb[LOCK][r][6] = 1;
            s.rb[LOCK][r][7] = 1;
        }
    }
    put("good_lock_lattice", &tsyn, &lock.render());
    put("good_vnc_only", &tsyn, &vnc_only().render());
    // Excluded points only (review N8): stage A rebuilds a table point's draws from its seed, and no test computes the
    // draws of a row point's seed, so no stream here carries a row-point id (the head checks of every point are in
    // table_checks_at_every_point).
    let tables: [(&str, u64, &[u64], bool); 5] = [
        ("X1", 2, &[64, 128], false),
        ("X0", 5, &[64, 128], true),
        ("X1", 0, &[64], false),
        ("X0", 7, &[64], true),
        ("X1", 6, &[64, 128], true),
    ];
    for (k, (id, call, steps, with_side)) in tables.iter().enumerate() {
        let p = points::find(id).expect("point");
        let text = table_stream(p, *call, steps, 100 + k as u64).render();
        let c = call.to_string();
        let mut args = vec!["--point", *id, "--call", c.as_str()];
        if *with_side {
            args.extend(["--side", "@SIDE@"]);
        }
        put(&format!("table_{id}_{call}_r{}", steps.len()), &args, &text);
    }
    let good = small().render();
    for (k, (want, text)) in stop_cases(&good).iter().enumerate() {
        put(&format!("stop{k:02}_{want}"), &tsyn, text);
    }
    for (k, (args, want)) in arg_cases().iter().enumerate() {
        put(&format!("args{k:02}_{want}"), args, &good);
    }
    for (k, (_, args, text, want)) in probe_cases().iter().enumerate() {
        put(
            &format!("probe{k:02}_{}", want.unwrap_or("block")),
            args,
            text,
        );
    }
    for (k, (_, args, text, want)) in draw_cases().iter().enumerate() {
        put(
            &format!("draw{k:02}_{}", want.unwrap_or("block")),
            args,
            text,
        );
    }
    let syn = small();
    let s = syn
        .samples
        .iter()
        .position(|s| s.c[1] == 0)
        .expect("a LOCK exchange atom");
    let idx = format!("TWB_DUMP_OBS|idx={s}|variant=LOCK|step=64|");
    let row = good
        .lines()
        .find(|l| l.starts_with(&idx))
        .expect("row")
        .to_string();
    put(
        "xatom_literal_minus0",
        &tsyn,
        &good.replacen(&row, &row.replace("|bi=0|", "|bi=-0|"), 1),
    );
    put(
        "xatom_stale_sums",
        &tsyn,
        &good.replacen(&row, &row.replace("|bi=0|", "|bi=-7|"), 1),
    );
    let mut planted = syn.clone();
    planted.samples[s].obs[LOCK][0][6] = -7;
    put("xatom_consistent", &tsyn, &planted.render());
}
