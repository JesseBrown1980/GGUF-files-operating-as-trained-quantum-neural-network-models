//! Stage A on real twens 0.4.0 dumps at the excluded points X1 (N=27, delta=1/4, u=1, y=1/40) and X0 (y=0): calls 0
//! and 1, count=4096, every variant and NL, steps 64,128, ctrl 0:0:0;0:0:0. The dumps are kept outside the repo; run
//! with STRIPES_EXCL_DIR=<dir holding X1.0.txt X1.1.txt X0.0.txt X0.1.txt> cargo test -- --ignored.

mod common;

use common::*;
use std::collections::HashMap;
use stripes_read_a::eng::{LOCK, VNAME};

const FILES: [(&str, &str, u64); 4] = [
    ("X1", "X1.0", 0),
    ("X1", "X1.1", 1),
    ("X0", "X0.0", 0),
    ("X0", "X0.1", 1),
];

fn dump(name: &str) -> String {
    let dir = std::env::var("STRIPES_EXCL_DIR")
        .expect("set STRIPES_EXCL_DIR to the excluded-dump folder");
    std::fs::read_to_string(format!("{dir}/{name}.txt")).expect("dump file")
}

fn args(point: &str, call: u64) -> Vec<String> {
    vec![
        "--point".into(),
        point.into(),
        "--call".into(),
        call.to_string(),
    ]
}

fn read_s(a: &[String], text: &str) -> stripes_read_a::Report {
    stripes_read_a::run(a, text.as_bytes())
}

#[test]
#[ignore]
fn the_emulator_rerenders_each_dump_byte_for_byte() {
    for (_, name, _) in FILES {
        let text = dump(name);
        let syn = parse_dump(&text);
        assert_eq!(syn.samples.len(), 4096);
        assert!(syn.render() == text, "{name}: re-rendered stream differs");
    }
}

#[test]
#[ignore]
fn each_dump_reads_and_its_aggregate_equals_the_oracles() {
    let mut nl: HashMap<&str, Vec<String>> = HashMap::new();
    for (point, name, call) in FILES {
        let text = dump(name);
        let rep = read_s(&args(point, call), &text);
        assert_eq!(rep.code, 0, "{name}: {}", rep.out);
        assert!(rep.out.contains("|table=checked|"));
        assert!(rep.out.contains("|result=all_equal|"));
        let syn = parse_dump(&text);
        let m = agg_map(&rep.out);
        let vs = vars(&syn.on);
        for r in 0..syn.steps.len() {
            let step = syn.steps[r].to_string();
            for (vi, &v) in vs.iter().enumerate() {
                let name_v = VNAME[v].to_string();
                let want = oracle_vr(&syn, vi, r);
                let vr = &m[&(
                    "AGG_VR".to_string(),
                    step.clone(),
                    name_v.clone(),
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
                    assert_eq!(vr[key], want[key], "{name} {step} {name_v} {key}");
                }
                let sum = &m[&(
                    "AGG_SUM".to_string(),
                    step.clone(),
                    name_v.clone(),
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
                    assert_eq!(sum[key], want[wk], "{name} {step} {name_v} {key}");
                }
                for n in stripes_read_a::agg::BLOCKS {
                    let blk = &m[&(
                        "AGG_BLK".to_string(),
                        step.clone(),
                        name_v.clone(),
                        n.to_string(),
                    )];
                    let (k, s2) = oracle_blocks(&syn, vi, r, n as usize);
                    assert_eq!(
                        (blk["K"].as_str(), blk["s2"].as_str()),
                        (k.to_string().as_str(), s2.to_string().as_str())
                    );
                }
                if vi > 0 {
                    let cmp = &m[&(
                        "AGG_CMP".to_string(),
                        step.clone(),
                        name_v.clone(),
                        String::new(),
                    )];
                    let (common, t) = oracle_cmp_br(&syn, vi, r);
                    let ts: Vec<String> = t.iter().map(|x| x.to_string()).collect();
                    assert_eq!(
                        (cmp["common"].clone(), cmp["br"].clone()),
                        (common.to_string(), ts.join(":"))
                    );
                }
            }
        }
        let h = rep
            .out
            .lines()
            .find(|l| l.starts_with("AGG_CALL|"))
            .expect("call row")
            .to_string();
        let nls = h
            .split('|')
            .find(|t| t.starts_with("nl_sha256="))
            .expect("nl")
            .to_string();
        nl.entry(point).or_default().push(nls);
    }
    for (point, v) in nl {
        assert_eq!(v.len(), 2);
        assert_eq!(v[0], v[1], "{point}: NL rows differ across calls");
    }
}

/// The first sample of a dump that is an exchange atom for variant v, with its index.
fn exchange_atom(syn: &Syn, v: usize) -> usize {
    syn.samples
        .iter()
        .position(|s| oracle_xatom(&s.c, v))
        .expect("an exchange atom in this call")
}

#[test]
#[ignore]
fn sabotage_on_a_real_dump() {
    let text = dump("X1.0");
    let syn = parse_dump(&text);
    let a = args("X1", 0);
    let base = read_s(&a, &text);
    assert_eq!(base.code, 0);
    let mut results: Vec<String> = Vec::new();
    for v in [LOCK, 0] {
        let s = exchange_atom(&syn, v);
        assert_eq!(
            syn.samples[s].obs[v][0][6], 0,
            "exchange atoms keep bi = 0 in the engine"
        );
        let prefix = format!("TWB_DUMP_OBS|idx={s}|variant={}|step=64|", VNAME[v]);
        let row = text
            .lines()
            .find(|l| l.starts_with(&prefix))
            .expect("row")
            .to_string();
        // S1a: the sign of bi flipped literally on the exchange atom: 0 -> -0.
        let t = text.replacen(&row, &row.replace("|bi=0|", "|bi=-0|"), 1);
        let rep = read_s(&a, &t);
        assert_eq!(
            stop_reason(&rep.out).as_deref(),
            Some("bad_integer"),
            "{}",
            rep.out
        );
        results.push(format!("S1a {} idx={s}: {}", VNAME[v], rep.out.trim_end()));
        // S1b: a nonzero bi of either sign on the exchange atom, summary rows left as printed.
        for bad in ["1", "-1"] {
            let t = text.replacen(&row, &row.replace("|bi=0|", &format!("|bi={bad}|")), 1);
            let rep = read_s(&a, &t);
            assert_eq!(
                stop_reason(&rep.out).as_deref(),
                Some("summary_mismatch"),
                "{}",
                rep.out
            );
            assert!(
                rep.out
                    .contains(&format!("row=TWB,step=64,of={},field=bi,", VNAME[v])),
                "{}",
                rep.out
            );
            results.push(format!("S1b {} bi={bad}: {}", VNAME[v], rep.out.trim_end()));
        }
        // S1c: the same fault with every summary row recomputed to match: the stream is consistent and the reader
        // reports the falsifier count of rule ATOMS / row E02.
        let mut planted = syn.clone();
        planted.samples[s].obs[v][0][6] = -1;
        let rep = read_s(&a, &planted.render());
        assert_eq!(rep.code, 0, "{}", rep.out);
        let m = agg_map(&rep.out);
        let key = (
            "AGG_VR".to_string(),
            "64".to_string(),
            VNAME[v].to_string(),
            String::new(),
        );
        let b = agg_map(&base.out);
        assert_eq!(b[&key]["xatom_bi_nz"], "0");
        assert_eq!(m[&key]["xatom_bi_nz"], "1");
        results.push(format!("S1c {}: xatom_bi_nz 0 -> 1", VNAME[v]));
    }
    // S2: an altered TWB sum.
    let row = text
        .lines()
        .find(|l| l.starts_with("TWB|") && l.contains("|step=64|variant=VNC|"))
        .expect("TWB")
        .to_string();
    let br: i128 = row
        .split('|')
        .find_map(|t| t.strip_prefix("br="))
        .expect("br")
        .parse()
        .expect("int");
    let t = text.replacen(
        &row,
        &row.replacen(&format!("|br={br}|"), &format!("|br={}|", br + 1), 1),
        1,
    );
    let rep = read_s(&a, &t);
    assert_eq!(
        stop_reason(&rep.out).as_deref(),
        Some("summary_mismatch"),
        "{}",
        rep.out
    );
    results.push(format!("S2: {}", rep.out.trim_end()));
    // S3: a wrong TWB_HEAD version.
    let t = text.replacen("|version=0.4.0|", "|version=0.3.0|", 1);
    let rep = read_s(&a, &t);
    assert_eq!(
        stop_reason(&rep.out).as_deref(),
        Some("head_version"),
        "{}",
        rep.out
    );
    results.push(format!("S3: {}", rep.out.trim_end()));
    // S4: truncated streams: no TWB_DONE; cut inside a line; the summary rows after the last sample block lost.
    let k = text.trim_end_matches('\n').rfind('\n').expect("nl") + 1;
    let rep = read_s(&a, &text[..k]);
    assert_eq!(
        stop_reason(&rep.out).as_deref(),
        Some("truncated"),
        "{}",
        rep.out
    );
    results.push(format!("S4a: {}", rep.out.trim_end()));
    let mid = text[..text.len() / 2].rfind('\n').expect("nl") + 25;
    let rep = read_s(&a, &text[..mid]);
    assert_eq!(
        stop_reason(&rep.out).as_deref(),
        Some("unterminated_last_line"),
        "{}",
        rep.out
    );
    results.push(format!("S4b: {}", rep.out.trim_end()));
    let first_summary = text.find("\nTWENS|").expect("summary") + 1;
    let rep = read_s(&a, &text[..first_summary]);
    assert_eq!(
        stop_reason(&rep.out).as_deref(),
        Some("truncated"),
        "{}",
        rep.out
    );
    results.push(format!("S4c: {}", rep.out.trim_end()));
    if let Ok(dir) = std::env::var("STRIPES_EXCL_DIR") {
        let mut body = results.join("\n");
        body.push('\n');
        std::fs::write(format!("{dir}/SABOTAGE.txt"), body).expect("write sabotage log");
    }
}
