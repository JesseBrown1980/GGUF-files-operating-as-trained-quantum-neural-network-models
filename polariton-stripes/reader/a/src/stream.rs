//! One twens 0.4.0 dump stream: the exact row sequence of the engine's cmd_dump, every metadata field held to the head
//! row, and (for a known point) the head held to the point table.

use crate::eng::{
    FIELDS, LEGACY, NF, NPAIR, NV, PAIRS, V0, V1, VINIT, VKAPPA, VNAME, VNC, VPHASE, VSEEDS,
};
use crate::points::{Point, COUNT};
use crate::row::{int, ints, kind, rational_is_zero, same, values};
use crate::sha256::{hex, seed_u64, Sha256};
use crate::Stop;
use std::io::BufRead;

pub const VERSION: &str = "0.4.0";
pub const BINARY_SHA256: &str = "33e62fbe0837aeddc916a57d67848338cbc258aa1dfb85a01cfba53fb8a4e03f";
pub const SOURCE_SHA256: &str = "main.rs:1d768fa9aba719d0439625f08ea2711cc0d28a5e751b25a81667b4b3d5fcacbb,sha256.rs:7447d1e84a95fe1ab84882938a0344119d017c347809e0f7e929c2e8c27d4621";
pub const SUMS_TEXT: &str = "plain_at_2^40,q_sum_of_floor(v*v/2^40),products_exact_at_2^80";
pub const ROUNDING_TEXT: &str = "per-sample_bound_summed_in_TWB_ROUND_and_TWB_PAIR_ROUND";
pub const UNITS_TEXT: &str = "ulps_of_each_field(sums_2^-40,squares_and_products_2^-80)";
pub const NL_INIT: &str = "c0=sqrt(N),c+-=0";
pub const NL_READS: &str = "trajectory_frame:A1=2abs(Z),C1=2N*abs(Z)^2/(N-1),f=fcl,D2=2abs(B);ensemble_frames:C1_NC=2N*xnc/(N-1),C1_W=2N*xw/(N-1),f_W=f=fcl-1/N";

const HEAD_KEYS: [&str; 25] = [
    "engine",
    "version",
    "cli",
    "binary_sha256",
    "source_sha256",
    "N",
    "delta",
    "u",
    "y",
    "seed",
    "seed_string",
    "start",
    "count",
    "samples",
    "dtden",
    "threads",
    "steps",
    "mask",
    "reserved",
    "guard",
    "q",
    "sums",
    "rounding",
    "float_used",
    "json",
];
const SAMPLE_KEYS: [&str; 4] = ["idx", "g", "rot", "json"];
const INIT_KEYS: [&str; 5] = ["idx", "variant", "s", "uv", "json"];
const IB_KEYS: [&str; 8] = ["idx", "variant", "e0", "ep", "em", "seeds", "eta", "json"];
const OBS_KEYS: [&str; 14] = [
    "idx", "variant", "step", "zr", "zi", "xw", "xnc", "f", "br", "bi", "zcr", "zci", "xc", "json",
];
const RB_KEYS: [&str; 14] = [
    "idx", "variant", "step", "eps", "b_zr", "b_zi", "b_xw", "b_xnc", "b_f", "b_br", "b_bi",
    "b_z2", "b_fcl", "json",
];
const TWENS_META: [&str; 12] = [
    "N", "delta", "u", "y", "samples", "seed", "dtden", "step", "variant", "n", "h", "ctrl",
];
const TWPAIR_KEYS: [&str; 18] = [
    "N",
    "delta",
    "y",
    "samples",
    "step",
    "n",
    "v1xw_vnxnc",
    "q0",
    "v1zr_vnzr",
    "q1",
    "v0xw_v1xw",
    "q2",
    "v0zr_v1zr",
    "q3",
    "v1xw_vnxw",
    "q4",
    "float_used",
    "json",
];
const TWB_META: [&str; 17] = [
    "N", "delta", "u", "y", "seed", "start", "count", "dtden", "step", "variant", "init", "seeds",
    "kappa", "phase", "n", "h", "ctrl",
];
const ROUND_META: [&str; 10] = [
    "N", "delta", "y", "seed", "start", "count", "dtden", "step", "variant", "n",
];
const PAIR_META: [&str; 10] = [
    "N", "delta", "y", "seed", "start", "count", "dtden", "step", "pair", "n",
];
const NL_KEYS: [&str; 31] = [
    "N",
    "delta",
    "u",
    "y",
    "dtden",
    "step",
    "init",
    "kappa",
    "zr",
    "zi",
    "z2",
    "xw",
    "xnc",
    "f",
    "fcl",
    "br",
    "bi",
    "rb_zr",
    "rb_zi",
    "rb_z2",
    "rb_xw",
    "rb_xnc",
    "rb_f",
    "rb_fcl",
    "rb_br",
    "rb_bi",
    "eps",
    "reads",
    "at",
    "float_used",
    "json",
];
const DONE_KEYS: [&str; 5] = ["n", "records", "mask", "float_used", "json"];
const TAIL: [&str; 2] = ["float_used", "json"];

/// The input lines, hashed byte for byte as they are read.
pub struct Lines<R> {
    r: R,
    sha: Sha256,
    bytes: u64,
    lines: u64,
    buf: Vec<u8>,
}

impl<R: BufRead> Lines<R> {
    pub fn new(r: R) -> Self {
        Self {
            r,
            sha: Sha256::new(),
            bytes: 0,
            lines: 0,
            buf: Vec::with_capacity(4096),
        }
    }

    /// The next line without its newline; None at the end. A last line without a newline, or a byte outside
    /// printable ASCII, is a STOP.
    pub fn next_line(&mut self) -> Result<Option<&str>, Stop> {
        self.buf.clear();
        let k = self
            .r
            .read_until(b'\n', &mut self.buf)
            .map_err(|e| Stop::new("read_error", e.to_string()))?;
        if k == 0 {
            return Ok(None);
        }
        self.sha.update(&self.buf);
        self.bytes += k as u64;
        self.lines += 1;
        if self.buf.last() != Some(&b'\n') {
            return Err(Stop::new("unterminated_last_line", format!("bytes={k}")));
        }
        self.buf.pop();
        if let Some(pos) = self.buf.iter().position(|b| !(0x20..0x7f).contains(b)) {
            return Err(Stop::new("non_printable_byte", format!("column={pos}")));
        }
        std::str::from_utf8(&self.buf)
            .map(Some)
            .map_err(|_| Stop::new("non_printable_byte", "utf8"))
    }

    fn expect(&mut self, what: &str) -> Result<&str, Stop> {
        match self.next_line()? {
            Some(l) => Ok(l),
            None => Err(Stop::new("truncated", format!("expected={what}"))),
        }
    }

    /// Read and hash the rest of the input (after a STOP), so the engine is not cut off and the hash covers it all.
    pub fn drain(&mut self) {
        loop {
            self.buf.clear();
            match self.r.read_until(b'\n', &mut self.buf) {
                Ok(0) | Err(_) => break,
                Ok(k) => {
                    self.sha.update(&self.buf);
                    self.bytes += k as u64;
                    self.lines += 1;
                }
            }
        }
    }

    pub fn bytes(&self) -> u64 {
        self.bytes
    }
    pub fn lines(&self) -> u64 {
        self.lines
    }
    pub fn sha256_hex(&self) -> String {
        hex(&self.sha.clone().finish())
    }
}

pub struct Head {
    pub line: String,
    pub n: i64,
    pub delta: String,
    pub u: String,
    pub y: String,
    pub y_zero: bool,
    pub seed: u64,
    pub seed_string: String,
    pub start: u64,
    pub count: u64,
    pub dtden: i64,
    pub steps: Vec<u64>,
    pub mask: String,
    pub on: [bool; NV],
    pub nl: bool,
}

pub type RoundRow = ([u128; NF], u128);
pub type PairRow = ([i128; 3], [u128; 3]);

/// The summary rows of one record, indexed by variant (0..7) or pair (0..11).
pub struct Record {
    pub ctrl: (i64, i64, i64),
    pub twens: [Option<[i128; 16]>; NV],
    pub twpair: Option<[i128; 10]>,
    pub twb: [Option<[i128; NF]>; NV],
    pub round: [Option<RoundRow>; NV],
    pub pair: [Option<PairRow>; NPAIR],
    pub nl: Option<String>,
}

/// Everything one stream prints. Per-sample arrays are flat: [s * nv + vi] for starts, [(s * nv + vi) * nr + r] for
/// records, vi the position of the variant in `vars`.
pub struct Parsed {
    pub head: Head,
    pub vars: Vec<usize>,
    pub nr: usize,
    pub g: Vec<[i64; 6]>,
    pub rot: Vec<[i64; 2]>,
    pub init: Vec<[i64; 6]>,
    pub uv: Vec<[i64; 4]>,
    /// e0, ep, em, seeds, eta
    pub ib: Vec<[u128; 5]>,
    /// zr, zi, xw, xnc, f, br, bi, zcr, zci, xc
    pub obs: Vec<[i64; 10]>,
    /// eps, b_zr, b_zi, b_xw, b_xnc, b_f, b_br, b_bi, b_z2, b_fcl
    pub rb: Vec<[u128; 10]>,
    pub rec: Vec<Record>,
    pub h: Option<i64>,
}

impl Parsed {
    pub fn nv(&self) -> usize {
        self.vars.len()
    }
    pub fn sv(&self, s: usize, vi: usize) -> usize {
        s * self.vars.len() + vi
    }
    pub fn svr(&self, s: usize, vi: usize, r: usize) -> usize {
        (s * self.vars.len() + vi) * self.nr + r
    }
    pub fn count(&self) -> usize {
        self.g.len()
    }
}

fn parse_mask(text: &str) -> Result<([bool; NV], bool), Stop> {
    let mut on = [false; NV];
    let mut nl = false;
    let mut last: Option<usize> = None;
    for name in text.split(',') {
        let pos = if name == "NL" {
            NV
        } else {
            VNAME
                .iter()
                .position(|v| *v == name)
                .ok_or_else(|| Stop::new("head_mask", format!("unknown={name}")))?
        };
        if last.is_some_and(|l| pos <= l) {
            return Err(Stop::new("head_mask", format!("order_or_repeat={text}")));
        }
        last = Some(pos);
        if pos == NV {
            nl = true;
        } else {
            on[pos] = true;
        }
    }
    if !on[VNC] {
        return Err(Stop::new("no_VNC", format!("mask={text}")));
    }
    Ok((on, nl))
}

fn parse_head(line: &str) -> Result<Head, Stop> {
    if kind(line) != "TWB_HEAD" {
        return Err(Stop::new(
            "first_row_not_TWB_HEAD",
            format!("kind={}", kind(line)),
        ));
    }
    let v = values(line, "TWB_HEAD", &HEAD_KEYS)?;
    same("engine", v[0], "twens")?;
    if v[1] != VERSION {
        return Err(Stop::new(
            "head_version",
            format!("stream={},expected={VERSION}", v[1]),
        ));
    }
    same("cli", v[2], "dump")?;
    if v[3] != BINARY_SHA256 {
        return Err(Stop::new("head_binary_sha256", format!("stream={}", v[3])));
    }
    if v[4] != SOURCE_SHA256 {
        return Err(Stop::new("head_source_sha256", format!("stream={}", v[4])));
    }
    let n: i64 = int(v[5], "N")?;
    if n < 2 {
        return Err(Stop::new("head_N", v[5]));
    }
    rational_is_zero(v[6], "delta")?;
    rational_is_zero(v[7], "u")?;
    let y_zero = rational_is_zero(v[8], "y")?;
    let seed: u64 = int(v[9], "seed")?;
    let seed_string = v[10].to_string();
    if seed_string == "none" || seed != seed_u64(&seed_string) {
        return Err(Stop::new(
            "head_seed",
            format!("seed={seed},seed_string={seed_string}"),
        ));
    }
    let start: u64 = int(v[11], "start")?;
    let count: u64 = int(v[12], "count")?;
    if v[13] != v[12] || count == 0 || count > COUNT || start.checked_add(count).is_none() {
        return Err(Stop::new(
            "head_count",
            format!("start={start},count={count},samples={}", v[13]),
        ));
    }
    let dtden: i64 = int(v[14], "dtden")?;
    if dtden < 1 {
        return Err(Stop::new("head_dtden", v[14]));
    }
    same("threads", v[15], "1")?;
    let mut steps: Vec<u64> = Vec::new();
    for t in v[16].split(',') {
        let s: u64 = int(t, "steps")?;
        if steps.last().is_some_and(|l| s <= *l) {
            return Err(Stop::new("head_steps_not_increasing", v[16]));
        }
        steps.push(s);
    }
    let (on, nl) = parse_mask(v[17])?;
    if v[18] != "0" {
        return Err(Stop::new("head_reserved", format!("stream={}", v[18])));
    }
    if v[19] != "active" {
        return Err(Stop::new("head_guard", format!("stream={}", v[19])));
    }
    same("q", v[20], "40")?;
    same("sums", v[21], SUMS_TEXT)?;
    same("rounding", v[22], ROUNDING_TEXT)?;
    if v[23] != "0" {
        return Err(Stop::new("head_float_used", format!("stream={}", v[23])));
    }
    same("json", v[24], "0")?;
    Ok(Head {
        line: line.to_string(),
        n,
        delta: v[6].to_string(),
        u: v[7].to_string(),
        y: v[8].to_string(),
        y_zero,
        seed,
        seed_string,
        start,
        count,
        dtden,
        steps,
        mask: v[17].to_string(),
        on,
        nl,
    })
}

fn table_same(what: &str, got: &str, want: &str) -> Result<(), Stop> {
    if got == want {
        Ok(())
    } else {
        Err(Stop::new(
            "table_mismatch",
            format!("field={what},stream={got},table={want}"),
        ))
    }
}

/// The head of call `call` at a known point must be the frozen command's.
pub fn check_table(h: &Head, p: &Point, call: u64) -> Result<(), Stop> {
    if call >= p.calls() {
        return Err(Stop::new(
            "table_call_out_of_range",
            format!("call={call},calls={}", p.calls()),
        ));
    }
    table_same("N", &h.n.to_string(), &p.n.to_string())?;
    table_same("delta", &h.delta, p.delta)?;
    table_same("u", &h.u, "1")?;
    table_same("y", &h.y, p.y)?;
    table_same("seed_string", &h.seed_string, &p.seed_string())?;
    table_same("start", &h.start.to_string(), &(COUNT * call).to_string())?;
    table_same("count", &h.count.to_string(), &COUNT.to_string())?;
    table_same("dtden", &h.dtden.to_string(), "64")?;
    table_same("mask", &h.mask, p.mask(call))?;
    if h.steps.is_empty()
        || h.steps.len() > p.steps.len()
        || h.steps[..] != p.steps[..h.steps.len()]
    {
        let got: Vec<String> = h.steps.iter().map(|s| s.to_string()).collect();
        let want: Vec<String> = p.steps.iter().map(|s| s.to_string()).collect();
        return Err(Stop::new(
            "table_mismatch",
            format!(
                "field=steps,stream={},table_prefix_of={}",
                got.join(","),
                want.join(",")
            ),
        ));
    }
    Ok(())
}

fn idx_is(v: &str, idx: u64) -> Result<(), Stop> {
    let got: u64 = int(v, "idx")?;
    if got != idx {
        return Err(Stop::new(
            "sample_index",
            format!("stream={got},expected={idx}"),
        ));
    }
    Ok(())
}

fn vals<T: std::str::FromStr + ToString + Copy + Default, const K: usize>(
    v: &[&str],
    keys: &[&str],
) -> Result<[T; K], Stop> {
    let mut out = [T::default(); K];
    for ((slot, text), key) in out.iter_mut().zip(v.iter()).zip(keys.iter()) {
        *slot = int::<T>(text, key)?;
    }
    Ok(out)
}

struct Keys {
    twens: Vec<&'static str>,
    twb: Vec<&'static str>,
    round: Vec<String>,
    pair: Vec<&'static str>,
    pair_round: Vec<&'static str>,
}

impl Keys {
    fn new() -> Self {
        let twens: Vec<&'static str> = TWENS_META
            .iter()
            .chain(FIELDS[..16].iter())
            .chain(TAIL.iter())
            .copied()
            .collect();
        let twb: Vec<&'static str> = TWB_META
            .iter()
            .chain(FIELDS.iter())
            .chain(TAIL.iter())
            .copied()
            .collect();
        let mut round: Vec<String> = ROUND_META.iter().map(|s| s.to_string()).collect();
        round.extend(FIELDS.iter().map(|f| format!("rb_{f}")));
        round.extend(
            ["eps_max", "units", "float_used", "json"]
                .iter()
                .map(|s| s.to_string()),
        );
        let pair: Vec<&'static str> = PAIR_META
            .iter()
            .chain(["d", "qd", "d2"].iter())
            .chain(TAIL.iter())
            .copied()
            .collect();
        let pair_round: Vec<&'static str> = PAIR_META
            .iter()
            .chain(["rb_d", "rb_qd", "rb_d2"].iter())
            .chain(TAIL.iter())
            .copied()
            .collect();
        Self {
            twens,
            twb,
            round,
            pair,
            pair_round,
        }
    }
}

fn tail(v: &[&str]) -> Result<(), Stop> {
    let k = v.len();
    if v[k - 2] != "0" {
        return Err(Stop::new("float_used", format!("stream={}", v[k - 2])));
    }
    same("json", v[k - 1], "0")
}

/// Read the whole stream. `table` holds the point and call when the id is known.
pub fn parse<R: BufRead>(src: &mut Lines<R>, table: Option<(&Point, u64)>) -> Result<Parsed, Stop> {
    let first = match src.next_line()? {
        Some(l) => l.to_string(),
        None => return Err(Stop::new("empty_stream", "no_rows")),
    };
    let head = parse_head(&first)?;
    if let Some((p, call)) = table {
        check_table(&head, p, call)?;
    }
    let vars: Vec<usize> = (0..NV).filter(|&v| head.on[v]).collect();
    let nv = vars.len();
    let nr = head.steps.len();
    let count = head.count as usize;
    let step_text: Vec<String> = head.steps.iter().map(|s| s.to_string()).collect();
    let mut p = Parsed {
        vars: vars.clone(),
        nr,
        g: Vec::with_capacity(count),
        rot: Vec::with_capacity(count),
        init: Vec::with_capacity(count * nv),
        uv: Vec::with_capacity(count * nv),
        ib: Vec::with_capacity(count * nv),
        obs: Vec::with_capacity(count * nv * nr),
        rb: Vec::with_capacity(count * nv * nr),
        rec: Vec::with_capacity(nr),
        h: None,
        head,
    };
    for k in 0..p.head.count {
        let idx = p.head.start + k;
        let line = src.expect("TWB_DUMP_SAMPLE")?;
        let v = values(line, "TWB_DUMP_SAMPLE", &SAMPLE_KEYS)?;
        idx_is(v[0], idx)?;
        p.g.push(ints::<i64, 6>(v[1], ':', "g")?);
        p.rot.push(ints::<i64, 2>(v[2], ':', "rot")?);
        same("json", v[3], "0")?;
        for &var in &vars {
            let line = src.expect("TWB_DUMP_INIT")?;
            let v = values(line, "TWB_DUMP_INIT", &INIT_KEYS)?;
            idx_is(v[0], idx)?;
            same("variant", v[1], VNAME[var])?;
            p.init.push(ints::<i64, 6>(v[2], ':', "s")?);
            p.uv.push(ints::<i64, 4>(v[3], ':', "uv")?);
            same("json", v[4], "0")?;
            let line = src.expect("TWB_DUMP_IB")?;
            let v = values(line, "TWB_DUMP_IB", &IB_KEYS)?;
            idx_is(v[0], idx)?;
            same("variant", v[1], VNAME[var])?;
            p.ib.push(vals::<u128, 5>(&v[2..7], &IB_KEYS[2..7])?);
            same("json", v[7], "0")?;
            for st in &step_text {
                let line = src.expect("TWB_DUMP_OBS")?;
                let v = values(line, "TWB_DUMP_OBS", &OBS_KEYS)?;
                idx_is(v[0], idx)?;
                same("variant", v[1], VNAME[var])?;
                same("step", v[2], st)?;
                p.obs.push(vals::<i64, 10>(&v[3..13], &OBS_KEYS[3..13])?);
                same("json", v[13], "0")?;
                let line = src.expect("TWB_DUMP_RB")?;
                let v = values(line, "TWB_DUMP_RB", &RB_KEYS)?;
                idx_is(v[0], idx)?;
                same("variant", v[1], VNAME[var])?;
                same("step", v[2], st)?;
                p.rb.push(vals::<u128, 10>(&v[3..13], &RB_KEYS[3..13])?);
                same("json", v[13], "0")?;
            }
        }
    }
    let keys = Keys::new();
    let h = &p.head;
    let (n_t, seed_t, start_t, count_t, dtden_t) = (
        h.n.to_string(),
        h.seed.to_string(),
        h.start.to_string(),
        h.count.to_string(),
        h.dtden.to_string(),
    );
    let on = h.on;
    let mut h_rows: Option<i64> = None;
    let mut records: Vec<Record> = Vec::with_capacity(nr);
    for st in &step_text {
        let mut rec = Record {
            ctrl: (0, 0, 0),
            twens: [None; NV],
            twpair: None,
            twb: [None; NV],
            round: [None; NV],
            pair: [None; NPAIR],
            nl: None,
        };
        let mut ctrl: Option<(i64, i64, i64)> = None;
        let mut take_ctrl_h = |c: &str, hv: &str| -> Result<(), Stop> {
            let c3 = ints::<i64, 3>(c, ':', "ctrl")?;
            let c3 = (c3[0], c3[1], c3[2]);
            match ctrl {
                None => ctrl = Some(c3),
                Some(prev) if prev != c3 => {
                    return Err(Stop::new("ctrl_differs_within_record", c.to_string()))
                }
                Some(_) => {}
            }
            let hh: i64 = int(hv, "h")?;
            match h_rows {
                None => h_rows = Some(hh),
                Some(prev) if prev != hh => return Err(Stop::new("h_differs", hv.to_string())),
                Some(_) => {}
            }
            Ok(())
        };
        for &(var, name) in LEGACY.iter() {
            if !on[var] {
                continue;
            }
            let line = src.expect("TWENS")?;
            let v = values(line, "TWENS", &keys.twens)?;
            same("N", v[0], &n_t)?;
            same("delta", v[1], &h.delta)?;
            same("u", v[2], &h.u)?;
            same("y", v[3], &h.y)?;
            same("samples", v[4], &count_t)?;
            same("seed", v[5], &seed_t)?;
            same("dtden", v[6], &dtden_t)?;
            same("step", v[7], st)?;
            same("variant", v[8], name)?;
            same("n", v[9], &count_t)?;
            take_ctrl_h(v[11], v[10])?;
            rec.twens[var] = Some(vals::<i128, 16>(&v[12..28], &keys.twens[12..28])?);
            tail(&v)?;
        }
        if on[V1] && on[VNC] && on[V0] {
            let line = src.expect("TWPAIR")?;
            let v = values(line, "TWPAIR", &TWPAIR_KEYS)?;
            same("N", v[0], &n_t)?;
            same("delta", v[1], &h.delta)?;
            same("y", v[2], &h.y)?;
            same("samples", v[3], &count_t)?;
            same("step", v[4], st)?;
            same("n", v[5], &count_t)?;
            rec.twpair = Some(vals::<i128, 10>(&v[6..16], &TWPAIR_KEYS[6..16])?);
            tail(&v)?;
        }
        for &var in &vars {
            let line = src.expect("TWB")?;
            let v = values(line, "TWB", &keys.twb)?;
            same("N", v[0], &n_t)?;
            same("delta", v[1], &h.delta)?;
            same("u", v[2], &h.u)?;
            same("y", v[3], &h.y)?;
            same("seed", v[4], &seed_t)?;
            same("start", v[5], &start_t)?;
            same("count", v[6], &count_t)?;
            same("dtden", v[7], &dtden_t)?;
            same("step", v[8], st)?;
            same("variant", v[9], VNAME[var])?;
            same("init", v[10], VINIT[var])?;
            same("seeds", v[11], VSEEDS[var])?;
            same("kappa", v[12], VKAPPA[var])?;
            same("phase", v[13], VPHASE[var])?;
            same("n", v[14], &count_t)?;
            take_ctrl_h(v[16], v[15])?;
            rec.twb[var] = Some(vals::<i128, NF>(&v[17..51], &keys.twb[17..51])?);
            tail(&v)?;
            let line = src.expect("TWB_ROUND")?;
            let rk: Vec<&str> = keys.round.iter().map(|s| s.as_str()).collect();
            let v = values(line, "TWB_ROUND", &rk)?;
            same("N", v[0], &n_t)?;
            same("delta", v[1], &h.delta)?;
            same("y", v[2], &h.y)?;
            same("seed", v[3], &seed_t)?;
            same("start", v[4], &start_t)?;
            same("count", v[5], &count_t)?;
            same("dtden", v[6], &dtden_t)?;
            same("step", v[7], st)?;
            same("variant", v[8], VNAME[var])?;
            same("n", v[9], &count_t)?;
            let rbs = vals::<u128, NF>(&v[10..44], &rk[10..44])?;
            let eps_max: u128 = int(v[44], "eps_max")?;
            same("units", v[45], UNITS_TEXT)?;
            rec.round[var] = Some((rbs, eps_max));
            tail(&v)?;
        }
        for (k, &(va, _, vb, _, name)) in PAIRS.iter().enumerate() {
            if !(on[va] && on[vb]) {
                continue;
            }
            let meta = |v: &[&str]| -> Result<(), Stop> {
                same("N", v[0], &n_t)?;
                same("delta", v[1], &h.delta)?;
                same("y", v[2], &h.y)?;
                same("seed", v[3], &seed_t)?;
                same("start", v[4], &start_t)?;
                same("count", v[5], &count_t)?;
                same("dtden", v[6], &dtden_t)?;
                same("step", v[7], st)?;
                same("pair", v[8], name)?;
                same("n", v[9], &count_t)?;
                tail(v)
            };
            let line = src.expect("TWB_PAIR")?;
            let v = values(line, "TWB_PAIR", &keys.pair)?;
            meta(&v)?;
            let d = vals::<i128, 3>(&v[10..13], &keys.pair[10..13])?;
            let line = src.expect("TWB_PAIR_ROUND")?;
            let v = values(line, "TWB_PAIR_ROUND", &keys.pair_round)?;
            meta(&v)?;
            let b = vals::<u128, 3>(&v[10..13], &keys.pair_round[10..13])?;
            rec.pair[k] = Some((d, b));
        }
        if h.nl {
            let line = src.expect("TWB_NL")?;
            let v = values(line, "TWB_NL", &NL_KEYS)?;
            same("N", v[0], &n_t)?;
            same("delta", v[1], &h.delta)?;
            same("u", v[2], &h.u)?;
            same("y", v[3], &h.y)?;
            same("dtden", v[4], &dtden_t)?;
            same("step", v[5], st)?;
            same("init", v[6], NL_INIT)?;
            same("kappa", v[7], "1")?;
            vals::<i64, 9>(&v[8..17], &NL_KEYS[8..17])?;
            vals::<u128, 10>(&v[17..27], &NL_KEYS[17..27])?;
            same("reads", v[27], NL_READS)?;
            same("at", v[28], "2^40")?;
            tail(&v)?;
            rec.nl = Some(line.to_string());
        }
        rec.ctrl = ctrl.ok_or_else(|| Stop::new("record_without_ctrl", st.clone()))?;
        if table.is_some() && rec.ctrl != (0, 0, 0) {
            return Err(Stop::new(
                "table_mismatch",
                format!(
                    "field=ctrl,step={st},stream={}:{}:{}",
                    rec.ctrl.0, rec.ctrl.1, rec.ctrl.2
                ),
            ));
        }
        records.push(rec);
    }
    let line = src.expect("TWB_DONE")?;
    let v = values(line, "TWB_DONE", &DONE_KEYS)?;
    same("n", v[0], &count_t)?;
    same("records", v[1], &nr.to_string())?;
    same("mask", v[2], &h.mask)?;
    tail(&v)?;
    if let Some(extra) = src.next_line()? {
        return Err(Stop::new(
            "rows_after_TWB_DONE",
            crate::row::kind(extra).to_string(),
        ));
    }
    p.rec = records;
    p.h = h_rows;
    Ok(p)
}
