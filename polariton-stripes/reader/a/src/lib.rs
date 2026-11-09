//! stripes-read-a: stage A of the stripe-phase reader of polariton-stripes/PREDICTION-STRIPE-PHASE.hbp (frozen at
//! 1977d45). One twens 0.4.0 dump stream on stdin, one aggregate block or one STOP row on stdout; integers only.
//! The output grammar is polariton-stripes/reader/AGG-FORMAT.md.

pub mod agg;
pub mod big;
pub mod check;
pub mod eng;
pub mod points;
pub mod row;
pub mod sector;
pub mod sha256;
pub mod side;
pub mod stream;

use std::io::BufRead;
use std::path::PathBuf;

pub const READER: &str = "stripes-read-a";
pub const READER_VERSION: &str = "0.1.0";
/// The exit code of a STOP.
pub const STOP_EXIT: i32 = 3;

/// Why a call is not read: a reason from the list in AGG-FORMAT.md, a detail, and the input line it was found at.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Stop {
    pub reason: String,
    pub detail: String,
    pub line: u64,
}

impl Stop {
    pub fn new(reason: impl Into<String>, detail: impl Into<String>) -> Self {
        Self {
            reason: reason.into(),
            detail: detail.into(),
            line: 0,
        }
    }
}

/// Field text safe inside a row: printable ASCII without '|'.
pub fn clean(s: &str) -> String {
    s.chars()
        .map(|c| {
            if c.is_ascii_graphic() && c != '|' {
                c
            } else {
                '_'
            }
        })
        .collect()
}

pub struct Args {
    pub point: String,
    pub call: u64,
    pub side: Option<PathBuf>,
}

pub fn parse_args(args: &[String]) -> Result<Args, Stop> {
    let mut point: Option<String> = None;
    let mut call: Option<u64> = None;
    let mut side: Option<PathBuf> = None;
    let mut it = args.iter();
    while let Some(a) = it.next() {
        let val = it
            .next()
            .ok_or_else(|| Stop::new("usage", format!("missing_value_for={}", clean(a))))?;
        match a.as_str() {
            "--point" if point.is_none() => point = Some(val.clone()),
            "--call" if call.is_none() => {
                call = Some(
                    row::int::<u64>(val, "call")
                        .map_err(|_| Stop::new("usage", format!("call={}", clean(val))))?,
                )
            }
            "--side" if side.is_none() => {
                if val.is_empty() || clean(val) != *val {
                    return Err(Stop::new(
                        "usage",
                        "side_path_must_be_printable_without_bar",
                    ));
                }
                side = Some(PathBuf::from(val));
            }
            _ => {
                return Err(Stop::new(
                    "usage",
                    format!("unknown_or_repeated={}", clean(a)),
                ))
            }
        }
    }
    match (point, call) {
        (Some(point), Some(call)) => Ok(Args { point, call, side }),
        _ => Err(Stop::new(
            "usage",
            "stripes-read-a_--point_ID_--call_I_[--side_PATH]",
        )),
    }
}

/// What the binary prints and its exit code.
pub struct Report {
    pub out: String,
    pub code: i32,
}

fn stop_row<R>(args: Option<&Args>, s: &Stop, src: &stream::Lines<R>) -> String
where
    R: BufRead,
{
    let (pt, call) = match args {
        Some(a) => (clean(&a.point), a.call.to_string()),
        None => ("-".to_string(), "-".to_string()),
    };
    format!(
        "STOP|reader={READER}|reader_version={READER_VERSION}|point={pt}|call={call}|reason={}|line={}|detail={}|stdin_bytes={}|stdin_lines={}|stdin_sha256={}|json=0\n",
        clean(&s.reason),
        s.line,
        clean(&s.detail),
        src.bytes(),
        src.lines(),
        src.sha256_hex()
    )
}

fn read_call<R: BufRead>(a: &Args, src: &mut stream::Lines<R>) -> Result<String, Stop> {
    let table = points::find(&a.point);
    if table.is_none() && !points::is_test_id(&a.point) {
        return Err(Stop::new("unknown_point", clean(&a.point)));
    }
    if let Some(p) = table {
        if p.needs_side(a.call) && a.side.is_none() {
            return Err(Stop::new(
                "side_file_required",
                format!("point={},call={}", p.id, a.call),
            ));
        }
    }
    let parsed = stream::parse(src, table.map(|p| (p, a.call))).map_err(|mut e| {
        if e.line == 0 {
            e.line = src.lines();
        }
        e
    })?;
    let checked = check::check(&parsed)?;
    let ag = agg::aggregate(&parsed)?;
    let pc = format!("point={}|call={}", a.point, a.call);
    let body = agg::rows(&parsed, &ag, &pc);
    let side_row =
        match &a.side {
            Some(path) => {
                let w = side::write(path, &parsed, &ag.flags)?;
                let vars: Vec<&str> = parsed.vars.iter().map(|&v| eng::VNAME[v]).collect();
                let steps: Vec<String> = w.steps.iter().map(|s| s.to_string()).collect();
                Some(format!(
                "AGG_SIDE|{pc}|path={}|bytes={}|sha256={}|indices={}|variants={}|steps={}|json=0",
                path.display(),
                w.bytes,
                w.sha256,
                w.indices,
                vars.join(","),
                if steps.is_empty() { "none".to_string() } else { steps.join(",") }
            ))
            }
            None => None,
        };
    let h = &parsed.head;
    let mut nl_text = String::new();
    for l in parsed.rec.iter().filter_map(|r| r.nl.as_ref()) {
        nl_text.push_str(l);
        nl_text.push('\n');
    }
    let nl_sha = if h.nl {
        sha256::hex(&sha256::sha256(nl_text.as_bytes()))
    } else {
        "none".to_string()
    };
    let steps: Vec<String> = h.steps.iter().map(|s| s.to_string()).collect();
    let vars: Vec<&str> = parsed.vars.iter().map(|&v| eng::VNAME[v]).collect();
    let ctrl: Vec<String> = parsed
        .rec
        .iter()
        .map(|r| format!("{}:{}:{}", r.ctrl.0, r.ctrl.1, r.ctrl.2))
        .collect();
    let mut rows: Vec<String> = vec![
        format!(
            "AGG_HEAD|reader={READER}|reader_version={READER_VERSION}|{pc}|table={}|stdin_bytes={}|stdin_lines={}|stdin_sha256={}|json=0",
            if table.is_some() { "checked" } else { "none" },
            src.bytes(),
            src.lines(),
            src.sha256_hex()
        ),
        format!("AGG_TWB_HEAD|{}", h.line),
        format!(
            "AGG_CALL|{pc}|N={}|delta={}|u={}|y={}|y_zero={}|seed={}|seed_string={}|start={}|count={}|dtden={}|h={}|steps={}|records={}|mask={}|variants={}|nl={}|ctrl={}|nl_sha256={nl_sha}|json=0",
            h.n,
            h.delta,
            h.u,
            h.y,
            u8::from(h.y_zero),
            h.seed,
            h.seed_string,
            h.start,
            h.count,
            h.dtden,
            eng::h_of(h.n),
            steps.join(","),
            parsed.nr,
            h.mask,
            vars.join(","),
            u8::from(h.nl),
            ctrl.join(";")
        ),
    ];
    rows.extend(body);
    if let Some(sr) = side_row {
        rows.push(sr);
    }
    rows.push(format!(
        "AGG_CHECK|{pc}|samples={}|starts={}|lin={}|rows={}|fields={}|result=all_equal|json=0",
        checked.samples, checked.starts, checked.lin, checked.rows, checked.fields
    ));
    let mut text = String::new();
    for r in &rows {
        text.push_str(r);
        text.push('\n');
    }
    let agg_sha = sha256::hex(&sha256::sha256(text.as_bytes()));
    text.push_str(&format!(
        "AGG_END|{pc}|agg_lines={}|agg_sha256={agg_sha}|json=0\n",
        rows.len()
    ));
    Ok(text)
}

/// Read one call: `args` as the binary takes them, `input` the dump stream.
pub fn run<R: BufRead>(args: &[String], input: R) -> Report {
    let mut src = stream::Lines::new(input);
    let parsed_args = parse_args(args);
    let res = match &parsed_args {
        Ok(a) => read_call(a, &mut src),
        Err(e) => Err(e.clone()),
    };
    match res {
        Ok(out) => Report { out, code: 0 },
        Err(s) => {
            src.drain();
            Report {
                out: stop_row(parsed_args.as_ref().ok(), &s, &src),
                code: STOP_EXIT,
            }
        }
    }
}
