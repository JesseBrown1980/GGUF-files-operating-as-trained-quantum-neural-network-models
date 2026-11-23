//! Test streams: an emulator of twens 0.4.0 cmd_dump output (a stream is built from per-sample draws, observables and
//! bounds, with every start and summary row the engine would print), a parser that turns a real dump back into that
//! form (so a real dump can be re-rendered, byte for byte, and then altered), and oracles for the aggregate written
//! apart from src/agg.rs.
#![allow(dead_code)]

use std::collections::HashMap;
use stripes_read_a::eng::{self, LEGACY, LOCK, NV, PAIRS, V0, V1, VNAME, VNC};
use stripes_read_a::sha256::seed_u64;
use stripes_read_a::stream::{BINARY_SHA256, NL_READS, SOURCE_SHA256};

pub const ALL: [bool; NV] = [true; NV];

#[derive(Clone)]
pub struct SynSample {
    /// the six coin counts c_i (g_i = c_i 2^35)
    pub c: [i64; 6],
    pub rot: (i64, i64),
    pub eta: u128,
    /// [vi][r]: zr, zi, xw, xnc, f, br, bi
    pub obs: Vec<Vec<[i64; 7]>>,
    /// [vi][r]: eps, b_zr, b_zi, b_xw, b_xnc, b_f, b_br, b_bi, b_z2, b_fcl
    pub rb: Vec<Vec<[u128; 10]>>,
}

#[derive(Clone)]
pub struct Syn {
    pub version: String,
    pub n: i64,
    pub delta: String,
    pub u: String,
    pub y: String,
    pub seed_string: String,
    pub start: u64,
    pub dtden: i64,
    pub steps: Vec<u64>,
    pub ctrl: Vec<(i64, i64, i64)>,
    pub on: [bool; NV],
    pub nl: bool,
    pub nl_rows: Vec<String>,
    pub samples: Vec<SynSample>,
}

pub fn vars(on: &[bool; NV]) -> Vec<usize> {
    (0..NV).filter(|&v| on[v]).collect()
}

pub fn mask_text(on: &[bool; NV], nl: bool) -> String {
    let mut v: Vec<&str> = (0..NV).filter(|&i| on[i]).map(|i| VNAME[i]).collect();
    if nl {
        v.push("NL");
    }
    v.join(",")
}

fn g_of(c: &[i64; 6]) -> [i64; 6] {
    c.map(|x| x << 35)
}

impl Syn {
    pub fn new(n: i64, y: &str, steps: &[u64], on: [bool; NV], nl: bool) -> Self {
        Self {
            version: "0.4.0".to_string(),
            n,
            delta: "1/4".to_string(),
            u: "1".to_string(),
            y: y.to_string(),
            seed_string: format!("stripes-test:N{n}:y{y}"),
            start: 0,
            dtden: 64,
            steps: steps.to_vec(),
            ctrl: vec![(0, 0, 0); steps.len()],
            on,
            nl,
            nl_rows: Vec::new(),
            samples: Vec::new(),
        }
    }

    pub fn seed(&self) -> u64 {
        seed_u64(&self.seed_string)
    }

    pub fn head(&self) -> String {
        let steps: Vec<String> = self.steps.iter().map(|s| s.to_string()).collect();
        let count = self.samples.len();
        format!(
            "TWB_HEAD|engine=twens|version={}|cli=dump|binary_sha256={BINARY_SHA256}|source_sha256={SOURCE_SHA256}|N={}|delta={}|u={}|y={}|seed={}|seed_string={}|start={}|count={count}|samples={count}|dtden={}|threads=1|steps={}|mask={}|reserved=0|guard=active|q=40|sums=plain_at_2^40,q_sum_of_floor(v*v/2^40),products_exact_at_2^80|rounding=per-sample_bound_summed_in_TWB_ROUND_and_TWB_PAIR_ROUND|float_used=0|json=0",
            self.version,
            self.n,
            self.delta,
            self.u,
            self.y,
            self.seed(),
            self.seed_string,
            self.start,
            self.dtden,
            steps.join(","),
            mask_text(&self.on, self.nl)
        )
    }

    fn nl_row(&self, r: usize) -> String {
        if let Some(l) = self.nl_rows.get(r) {
            return l.clone();
        }
        format!(
            "TWB_NL|N={}|delta={}|u={}|y={}|dtden={}|step={}|init=c0=sqrt(N),c+-=0|kappa=1|zr=0|zi=0|z2=0|xw=-1|xnc=-1|f=-1|fcl=0|br={}|bi=0|rb_zr=1|rb_zi=1|rb_z2=1|rb_xw=1|rb_xnc=1|rb_f=1|rb_fcl=1|rb_br=1|rb_bi=1|eps=1|reads={NL_READS}|at=2^40|float_used=0|json=0",
            self.n, self.delta, self.u, self.y, self.dtden, self.steps[r], 1000 + r
        )
    }

    /// The whole stream as the engine would print it.
    pub fn render(&self) -> String {
        let vs = vars(&self.on);
        let nr = self.steps.len();
        let n = self.n;
        let count = self.samples.len();
        let mut out = String::new();
        out.push_str(&self.head());
        out.push('\n');
        let mut uvs: Vec<Vec<[i64; 4]>> = Vec::new();
        let mut sbs: Vec<Vec<u128>> = Vec::new();
        for (k, s) in self.samples.iter().enumerate() {
            let idx = self.start + k as u64;
            let g = g_of(&s.c);
            out.push_str(&format!(
                "TWB_DUMP_SAMPLE|idx={idx}|g={}:{}:{}:{}:{}:{}|rot={}:{}|json=0\n",
                g[0], g[1], g[2], g[3], g[4], g[5], s.rot.0, s.rot.1
            ));
            let st = eng::starts(n, &g, s.rot, &self.on).expect("synthetic starts");
            let mut uv_row = Vec::new();
            let mut sb_row = Vec::new();
            for (vi, &v) in vs.iter().enumerate() {
                let i = st.init[v];
                let u = st.uv[v];
                uv_row.push(u);
                sb_row.push(st.sb[v]);
                out.push_str(&format!(
                    "TWB_DUMP_INIT|idx={idx}|variant={}|s={}:{}:{}:{}:{}:{}|uv={}:{}:{}:{}|json=0\n",
                    VNAME[v], i[0], i[1], i[2], i[3], i[4], i[5], u[0], u[1], u[2], u[3]
                ));
                let ib = st.ib[v];
                out.push_str(&format!(
                    "TWB_DUMP_IB|idx={idx}|variant={}|e0={}|ep={}|em={}|seeds={}|eta={}|json=0\n",
                    VNAME[v], ib[0], ib[1], ib[2], st.sb[v], s.eta
                ));
                for r in 0..nr {
                    let o = s.obs[vi][r];
                    let (zcr, zci, xc) = eng::lin(self.ctrl[r], &u, n);
                    out.push_str(&format!(
                        "TWB_DUMP_OBS|idx={idx}|variant={}|step={}|zr={}|zi={}|xw={}|xnc={}|f={}|br={}|bi={}|zcr={zcr}|zci={zci}|xc={xc}|json=0\n",
                        VNAME[v], self.steps[r], o[0], o[1], o[2], o[3], o[4], o[5], o[6]
                    ));
                    let b = s.rb[vi][r];
                    out.push_str(&format!(
                        "TWB_DUMP_RB|idx={idx}|variant={}|step={}|eps={}|b_zr={}|b_zi={}|b_xw={}|b_xnc={}|b_f={}|b_br={}|b_bi={}|b_z2={}|b_fcl={}|json=0\n",
                        VNAME[v], self.steps[r], b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7], b[8], b[9]
                    ));
                }
            }
            uvs.push(uv_row);
            sbs.push(sb_row);
        }
        let h = eng::h_of(n);
        let seed = self.seed();
        for r in 0..nr {
            let (c0, c1, c2) = self.ctrl[r];
            let step = self.steps[r];
            let mut sums = vec![[0i128; eng::NF]; vs.len()];
            let mut rbs = vec![[0u128; eng::NF]; vs.len()];
            let mut epsm = vec![0u128; vs.len()];
            for (vi, _) in vs.iter().enumerate() {
                for k in 0..count {
                    let o7 = self.samples[k].obs[vi][r];
                    let (zcr, zci, xc) = eng::lin(self.ctrl[r], &uvs[k][vi], n);
                    let o = [
                        o7[0], o7[1], o7[2], o7[3], o7[4], o7[5], o7[6], zcr, zci, xc,
                    ];
                    let (t, vals) = eng::twb_terms(&o);
                    for (a, x) in sums[vi].iter_mut().zip(t) {
                        *a += x;
                    }
                    let b = self.samples[k].rb[vi][r];
                    let ob = [b[1], b[2], b[3], b[4], b[5], b[6], b[7]];
                    let fb = eng::field_bounds(self.ctrl[r], sbs[k][vi], &ob, vals, (zcr, zci));
                    for (a, x) in rbs[vi].iter_mut().zip(fb) {
                        *a += x;
                    }
                    epsm[vi] = epsm[vi].max(b[0]);
                }
            }
            let pos = |v: usize| vs.iter().position(|&x| x == v);
            for &(v, name) in LEGACY.iter() {
                let Some(vi) = pos(v) else { continue };
                let s = &sums[vi];
                out.push_str(&format!(
                    "TWENS|N={n}|delta={}|u={}|y={}|samples={count}|seed={seed}|dtden={}|step={step}|variant={name}|n={count}|h={h}|ctrl={c0}:{c1}:{c2}|zr={}|zi={}|dzr={}|dzi={}|xw={}|dxw={}|xnc={}|dxnc={}|f={}|qdzr={}|qdxw={}|qdxnc={}|qzr={}|qxw={}|qxnc={}|qdzi={}|float_used=0|json=0\n",
                    self.delta, self.u, self.y, self.dtden,
                    s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10], s[11], s[12], s[13], s[14], s[15]
                ));
            }
            let mut pd = [[0i128; 3]; PAIRS.len()];
            let mut prb = [[0u128; 3]; PAIRS.len()];
            for (kp, &(va, oa, vb, ob, _)) in PAIRS.iter().enumerate() {
                let (Some(ia), Some(ib)) = (pos(va), pos(vb)) else {
                    continue;
                };
                for s in &self.samples {
                    let d = s.obs[ia][r][oa] - s.obs[ib][r][ob];
                    let d128 = i128::from(d);
                    pd[kp][0] += d128;
                    pd[kp][1] += (d128 * d128) >> 40;
                    pd[kp][2] += d128 * d128;
                    let bd = s.rb[ia][r][1 + oa] + s.rb[ib][r][1 + ob];
                    let ad = u128::from(d.unsigned_abs());
                    prb[kp][0] += bd;
                    prb[kp][1] += eng::cu(2 * ad, bd) + eng::cu(bd, bd) + 1;
                    prb[kp][2] += 2 * ad * bd + bd * bd;
                }
            }
            if self.on[V1] && self.on[VNC] && self.on[V0] {
                out.push_str(&format!(
                    "TWPAIR|N={n}|delta={}|y={}|samples={count}|step={step}|n={count}|v1xw_vnxnc={}|q0={}|v1zr_vnzr={}|q1={}|v0xw_v1xw={}|q2={}|v0zr_v1zr={}|q3={}|v1xw_vnxw={}|q4={}|float_used=0|json=0\n",
                    self.delta, self.y, pd[0][0], pd[0][1], pd[1][0], pd[1][1], pd[2][0], pd[2][1], pd[3][0], pd[3][1], pd[4][0], pd[4][1]
                ));
            }
            for (vi, &v) in vs.iter().enumerate() {
                let fields: Vec<String> = eng::FIELDS
                    .iter()
                    .zip(sums[vi].iter())
                    .map(|(f, x)| format!("{f}={x}"))
                    .collect();
                out.push_str(&format!(
                    "TWB|N={n}|delta={}|u={}|y={}|seed={seed}|start={}|count={count}|dtden={}|step={step}|variant={}|init={}|seeds={}|kappa={}|phase={}|n={count}|h={h}|ctrl={c0}:{c1}:{c2}|{}|float_used=0|json=0\n",
                    self.delta, self.u, self.y, self.start, self.dtden, VNAME[v], eng::VINIT[v], eng::VSEEDS[v], eng::VKAPPA[v], eng::VPHASE[v], fields.join("|")
                ));
                let rbf: Vec<String> = eng::FIELDS
                    .iter()
                    .zip(rbs[vi].iter())
                    .map(|(f, x)| format!("rb_{f}={x}"))
                    .collect();
                out.push_str(&format!(
                    "TWB_ROUND|N={n}|delta={}|y={}|seed={seed}|start={}|count={count}|dtden={}|step={step}|variant={}|n={count}|{}|eps_max={}|units=ulps_of_each_field(sums_2^-40,squares_and_products_2^-80)|float_used=0|json=0\n",
                    self.delta, self.y, self.start, self.dtden, VNAME[v], rbf.join("|"), epsm[vi]
                ));
            }
            for (kp, &(va, _, vb, _, name)) in PAIRS.iter().enumerate() {
                if !(self.on[va] && self.on[vb]) {
                    continue;
                }
                let meta = format!(
                    "N={n}|delta={}|y={}|seed={seed}|start={}|count={count}|dtden={}|step={step}|pair={name}|n={count}",
                    self.delta, self.y, self.start, self.dtden
                );
                out.push_str(&format!(
                    "TWB_PAIR|{meta}|d={}|qd={}|d2={}|float_used=0|json=0\n",
                    pd[kp][0], pd[kp][1], pd[kp][2]
                ));
                out.push_str(&format!(
                    "TWB_PAIR_ROUND|{meta}|rb_d={}|rb_qd={}|rb_d2={}|float_used=0|json=0\n",
                    prb[kp][0], prb[kp][1], prb[kp][2]
                ));
            }
            if self.nl {
                out.push_str(&self.nl_row(r));
                out.push('\n');
            }
        }
        out.push_str(&format!(
            "TWB_DONE|n={count}|records={nr}|mask={}|float_used=0|json=0\n",
            mask_text(&self.on, self.nl)
        ));
        out
    }
}

fn fields_of(line: &str) -> HashMap<String, String> {
    line.split('|')
        .skip(1)
        .filter_map(|t| t.split_once('='))
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .collect()
}

fn num<T: std::str::FromStr>(m: &HashMap<String, String>, k: &str) -> T {
    match m.get(k).map(|v| v.parse::<T>()) {
        Some(Ok(v)) => v,
        _ => panic!("field {k}"),
    }
}

fn colon<const K: usize>(s: &str) -> [i64; K] {
    let v: Vec<i64> = s.split(':').map(|x| x.parse().expect("int")).collect();
    let mut out = [0i64; K];
    out.copy_from_slice(&v);
    out
}

/// A real dump back into the emulator's form (head fields, draws, observables, bounds, ctrl, NL rows verbatim).
pub fn parse_dump(text: &str) -> Syn {
    let mut lines = text.lines();
    let head = fields_of(lines.next().expect("head"));
    let steps: Vec<u64> = head["steps"]
        .split(',')
        .map(|s| s.parse().expect("step"))
        .collect();
    let mut on = [false; NV];
    let mut nl = false;
    for name in head["mask"].split(',') {
        match VNAME.iter().position(|v| *v == name) {
            Some(i) => on[i] = true,
            None => nl = true,
        }
    }
    let vs = vars(&on);
    let nr = steps.len();
    let mut syn = Syn {
        version: head["version"].clone(),
        n: num(&head, "N"),
        delta: head["delta"].clone(),
        u: head["u"].clone(),
        y: head["y"].clone(),
        seed_string: head["seed_string"].clone(),
        start: num(&head, "start"),
        dtden: num(&head, "dtden"),
        steps: steps.clone(),
        ctrl: vec![(0, 0, 0); nr],
        on,
        nl,
        nl_rows: Vec::new(),
        samples: Vec::new(),
    };
    for line in lines {
        let kind = line.split('|').next().unwrap_or("");
        let f = fields_of(line);
        match kind {
            "TWB_DUMP_SAMPLE" => {
                let g: [i64; 6] = colon(&f["g"]);
                let rot: [i64; 2] = colon(&f["rot"]);
                syn.samples.push(SynSample {
                    c: g.map(|x| x >> 35),
                    rot: (rot[0], rot[1]),
                    eta: 0,
                    obs: vec![vec![[0; 7]; nr]; vs.len()],
                    rb: vec![vec![[0; 10]; nr]; vs.len()],
                });
            }
            "TWB_DUMP_IB" => {
                let s = syn.samples.last_mut().expect("sample");
                s.eta = num(&f, "eta");
            }
            "TWB_DUMP_OBS" | "TWB_DUMP_RB" => {
                let v = VNAME
                    .iter()
                    .position(|x| *x == f["variant"])
                    .expect("variant");
                let vi = vs.iter().position(|&x| x == v).expect("on");
                let step: u64 = num(&f, "step");
                let r = steps.iter().position(|&x| x == step).expect("step");
                let s = syn.samples.last_mut().expect("sample");
                if kind == "TWB_DUMP_OBS" {
                    let k = ["zr", "zi", "xw", "xnc", "f", "br", "bi"];
                    for (j, key) in k.iter().enumerate() {
                        s.obs[vi][r][j] = num(&f, key);
                    }
                } else {
                    let k = [
                        "eps", "b_zr", "b_zi", "b_xw", "b_xnc", "b_f", "b_br", "b_bi", "b_z2",
                        "b_fcl",
                    ];
                    for (j, key) in k.iter().enumerate() {
                        s.rb[vi][r][j] = num(&f, key);
                    }
                }
            }
            "TWB" => {
                let step: u64 = num(&f, "step");
                let r = steps.iter().position(|&x| x == step).expect("step");
                let c: [i64; 3] = colon(&f["ctrl"]);
                syn.ctrl[r] = (c[0], c[1], c[2]);
            }
            "TWB_NL" => syn.nl_rows.push(line.to_string()),
            _ => {}
        }
    }
    syn
}

/// Lines joined back into stream text, each with its newline.
pub fn joined<'a>(lines: impl Iterator<Item = &'a str>) -> String {
    let mut out = String::new();
    for l in lines {
        out.push_str(l);
        out.push('\n');
    }
    out
}

/// Run the reader in-process.
pub fn read(args: &[&str], stream: &str) -> stripes_read_a::Report {
    let a: Vec<String> = args.iter().map(|s| s.to_string()).collect();
    stripes_read_a::run(&a, stream.as_bytes())
}

/// The reader's output rows, keyed by (kind, step, variant, extra) with extra = set or n.
pub fn agg_map(out: &str) -> HashMap<(String, String, String, String), HashMap<String, String>> {
    let mut m = HashMap::new();
    for line in out.lines() {
        let kind = line.split('|').next().unwrap_or("").to_string();
        let f = fields_of(line);
        let g = |k: &str| f.get(k).cloned().unwrap_or_default();
        let extra = if f.contains_key("set") {
            g("set")
        } else {
            g("n")
        };
        m.insert((kind, g("step"), g("variant"), extra), f);
    }
    m
}

pub fn stop_reason(out: &str) -> Option<String> {
    let first = out.lines().next()?;
    if !first.starts_with("STOP|") {
        return None;
    }
    fields_of(first).get("reason").cloned()
}

// ---------------------------------------------------------------------------------------------------------------------
// Oracles, written apart from src/agg.rs and src/sector.rs.

/// sign(p + q sqrt 2).
fn sgn_q2(p: i128, q: i128) -> i32 {
    let (sp, sq) = (p.signum() as i32, q.signum() as i32);
    if sp == sq || sq == 0 {
        return sp;
    }
    if sp == 0 {
        return sq;
    }
    if p * p > 2 * q * q {
        sp
    } else {
        sq
    }
}

/// The sector of an integer point by counting the rays k pi/8 at or below its angle inside its half-open quadrant.
pub fn oracle_sigma(x: i128, y: i128) -> Option<u8> {
    let (q, a, b) = match (x.signum(), y.signum()) {
        (1, 0) | (1, 1) => (0, x, y),
        (0, 1) | (-1, 1) => (1, y, -x),
        (-1, 0) | (-1, -1) => (2, -x, -y),
        (0, -1) | (1, -1) => (3, -y, x),
        _ => return None,
    };
    let rays = [sgn_q2(b + a, -a) >= 0, b >= a, sgn_q2(b - a, -a) >= 0];
    Some(4 * q + rays.iter().filter(|&&t| t).count() as u8)
}

pub fn oracle_cert(br: i64, bi: i64, bbr: u128, bbi: u128) -> Option<u8> {
    let (r, i, dr, di) = (i128::from(br), i128::from(bi), bbr as i128, bbi as i128);
    let corners = [
        (r + dr, i + di),
        (r + dr, i - di),
        (r - dr, i + di),
        (r - dr, i - di),
    ];
    if corners
        .iter()
        .any(|&(x, y)| x == 0 || y == 0 || x.abs() == y.abs())
    {
        return None;
    }
    let s: Vec<Option<u8>> = corners.iter().map(|&(x, y)| oracle_sigma(x, y)).collect();
    if s.iter().all(|v| *v == s[0]) {
        s[0]
    } else {
        None
    }
}

/// 0 certified positive, 1 certified negative, 2 ambiguous.
pub fn oracle_sign(v: i64, b: u128) -> usize {
    let a = u128::from(v.unsigned_abs());
    if a <= b {
        2
    } else if v > 0 {
        0
    } else {
        1
    }
}

/// The atom flag of rule ATOMS for one variant.
pub fn oracle_atom(c: &[i64; 6], v: usize, y_zero: bool) -> bool {
    let [c0, c1, c2, c3, _, _] = *c;
    if v == LOCK {
        if y_zero {
            c0 * c1 * (c0 * c0 - c1 * c1) == 0
        } else {
            c1 == 0
        }
    } else if y_zero {
        let mut p = (c2, c3);
        let mut hit = false;
        for _ in 0..4 {
            hit |= (c0, c1) == p;
            p = (-p.1, p.0);
        }
        hit
    } else {
        c0 == c2 && c1 == c3
    }
}

pub fn oracle_xatom(c: &[i64; 6], v: usize) -> bool {
    if v == LOCK {
        c[1] == 0
    } else {
        c[0] == c[2] && c[1] == c[3]
    }
}

/// The expected AGG_VR, AGG_SUM (all) and AGG_BLK numbers of one (record, variant), as strings by key.
pub fn oracle_vr(syn: &Syn, vi: usize, r: usize) -> HashMap<String, String> {
    let v = vars(&syn.on)[vi];
    let y_zero = syn.y == "0";
    let mut m: HashMap<String, String> = HashMap::new();
    let mut sec = [0u64; 16];
    let (mut amb, mut atoms, mut xatoms, mut xnz, mut nab0) = (0u64, 0u64, 0u64, 0u64, 0u64);
    let mut brs = [0u64; 3];
    let mut bis = [0u64; 3];
    let (mut sbr, mut sbi, mut sbr2, mut sbi2, mut sbbr, mut sbbr2) =
        (0i128, 0i128, 0i128, 0i128, 0u128, 0u128);
    for s in &syn.samples {
        let (br, bi) = (s.obs[vi][r][5], s.obs[vi][r][6]);
        let (bbr, bbi) = (s.rb[vi][r][6], s.rb[vi][r][7]);
        sbr += i128::from(br);
        sbi += i128::from(bi);
        sbr2 += i128::from(br).pow(2);
        sbi2 += i128::from(bi).pow(2);
        sbbr += bbr;
        sbbr2 += bbr * bbr;
        if oracle_xatom(&s.c, v) {
            xatoms += 1;
            xnz += u64::from(bi != 0);
        }
        if oracle_atom(&s.c, v, y_zero) {
            atoms += 1;
            continue;
        }
        match oracle_cert(br, bi, bbr, bbi) {
            Some(k) => sec[usize::from(k)] += 1,
            None => amb += 1,
        }
        brs[oracle_sign(br, bbr)] += 1;
        bis[oracle_sign(bi, bbi)] += 1;
        nab0 += u64::from(bi == 0);
    }
    let secs: Vec<String> = sec.iter().map(|x| x.to_string()).collect();
    for (k, val) in [
        ("atoms", atoms.to_string()),
        ("xatoms", xatoms.to_string()),
        ("xatom_bi_nz", xnz.to_string()),
        ("na_bi0", nab0.to_string()),
        ("sec", secs.join(":")),
        ("amb", amb.to_string()),
        ("br_pos", brs[0].to_string()),
        ("br_neg", brs[1].to_string()),
        ("br_amb", brs[2].to_string()),
        ("bi_pos", bis[0].to_string()),
        ("bi_neg", bis[1].to_string()),
        ("bi_amb", bis[2].to_string()),
        ("sum_br", sbr.to_string()),
        ("sum_bi", sbi.to_string()),
        ("sum_br2", sbr2.to_string()),
        ("sum_bi2", sbi2.to_string()),
        ("sum_bbr", sbbr.to_string()),
        ("sum_bbr2", sbbr2.to_string()),
    ] {
        m.insert(k.to_string(), val);
    }
    m
}

/// Sum over blocks of n consecutive samples of |S_b|^2, and the block count, by slicing.
pub fn oracle_blocks(syn: &Syn, vi: usize, r: usize, n: usize) -> (u64, u128) {
    let mut k = 0u64;
    let mut s2 = 0u128;
    for chunk in syn.samples.chunks(n) {
        if chunk.len() < n {
            break;
        }
        let sr: i128 = chunk.iter().map(|s| i128::from(s.obs[vi][r][5])).sum();
        let si: i128 = chunk.iter().map(|s| i128::from(s.obs[vi][r][6])).sum();
        s2 += (sr * sr + si * si) as u128;
        k += 1;
    }
    (k, s2)
}

/// The sign table of variant vi against VNC (vi 0) over samples that are non-atoms in both: [x][ref] flattened.
pub fn oracle_cmp_br(syn: &Syn, vi: usize, r: usize) -> (u64, [u64; 9]) {
    let vs = vars(&syn.on);
    let y_zero = syn.y == "0";
    let mut t = [0u64; 9];
    let mut common = 0;
    for s in &syn.samples {
        if oracle_atom(&s.c, vs[vi], y_zero) || oracle_atom(&s.c, VNC, y_zero) {
            continue;
        }
        common += 1;
        let x = oracle_sign(s.obs[vi][r][5], s.rb[vi][r][6]);
        let rf = oracle_sign(s.obs[0][r][5], s.rb[0][r][6]);
        t[3 * x + rf] += 1;
    }
    (common, t)
}

/// A small deterministic generator (no float).
pub struct Lcg(pub u64);

impl Lcg {
    pub fn next(&mut self) -> u64 {
        self.0 = self
            .0
            .wrapping_mul(6_364_136_223_846_793_005)
            .wrapping_add(1_442_695_040_888_963_407);
        self.0 >> 11
    }
    /// An integer in [-k, k].
    pub fn int(&mut self, k: i64) -> i64 {
        (self.next() % (2 * k as u64 + 1)) as i64 - k
    }
}

/// A synthetic sample: noise values c, and per variant and record an observable row and a bound row.
pub fn sample(rng: &mut Lcg, c: [i64; 6], nv: usize, nr: usize, mode0: bool) -> SynSample {
    let mut obs = vec![vec![[0i64; 7]; nr]; nv];
    let mut rb = vec![vec![[0u128; 10]; nr]; nv];
    for vi in 0..nv {
        for r in 0..nr {
            for j in 0..5 {
                obs[vi][r][j] = rng.int(1 << 38);
            }
            obs[vi][r][5] = rng.int(1 << 36);
            obs[vi][r][6] = rng.int(1 << 36);
            for j in 0..10 {
                rb[vi][r][j] = (rng.next() % 5000) as u128;
            }
        }
    }
    SynSample {
        c,
        rot: if mode0 {
            (777_777_777_777, -555_555_555_555)
        } else {
            (1 << 40, 0)
        },
        eta: if mode0 { 389 } else { 0 },
        obs,
        rb,
    }
}
