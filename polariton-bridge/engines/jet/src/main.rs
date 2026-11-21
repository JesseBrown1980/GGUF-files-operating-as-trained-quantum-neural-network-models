//! jetens 0.2.0: the flow-map jet of the polariton bridge's ensemble engine, integers only (float_used=0), Rust 1.81,
//! std only. From jetens 0.1.0 of the ensemble-skip test (lane ensemble-skip-20261106), with the engine holds of its
//! check (ensemble-skip-check-20261106) applied in lane jet-plan-20261106:
//!   H4  every JET_HEAD names the binary's own sha256 and the sha256 of the two source files as compiled (include_bytes);
//!       `jetens version` prints the same.
//!   H5  a JET_CONS row beside every record: the number conservation n0 + ns - (1 + e + |a|^2 + |b|^2), coefficientwise.
//!   H7  a jet is N-free, so the jet subcommand refuses the y band ||y| - 2/27| <= 1/81 at every N, not only at the N
//!       listed in for_n.
//! Also: the record steps must be strictly increasing (0.1.0 skipped a record silently when they were not), and the jet
//! subcommand takes lift_reserved_guard=1 (the literal 1 only), as twens does, printing reserved=1|guard=lifted.
//! Three subcommands and version:
//!
//! jet   The jet of the ensemble engine's own map (RK4 at dt = 1/dtden on the scaled equations of BRIDGE_TRAJ_MAP,
//!       u = 1, x = delta - 1) in the start noise a = z+(0), b = z-(0), their conjugates, and a start variable e with
//!       z0(0) = sqrt(1 + e). Weights 1, 1, 1, 1, 2; every product is truncated at total weight P, so the coefficients of
//!       weight w depend only on coefficients of weight <= w and one run at P carries every lower order exactly.
//!       Coefficients are complex, each part an i128 at 2^-q; a product goes through 256 bits and is truncated toward
//!       zero (an error below one unit of 2^-q per term). At each record it prints the observable polynomials
//!       Z = conj(z0) z+ + conj(z-) z0, B = conj(z-) z+, n0 = |z0|^2, ns = |z+|^2 + |z-|^2, Pr = conj(z+) conj(z-) z0^2,
//!       Z2 = |Z|^2 and ns2 = ns^2, each truncated at weight P, and the JET_CONS row.
//! steps Per-sample RK4 (the engine's rk4, operation for operation, i64 at 2^40) and a Taylor step of order K at
//!       h = 2^-hb (the recursion of traj_int.py, at the engine's 2^40 fixed point) on starts read from a file.
//! dup   The engine's per-sample generator (seed + idx * 0x100000001B3, splitmix64, xoshiro256**, popcount Gaussians);
//!       counts repeated Gaussian tuples and repeated states (exact and by sha256) after RK4 to a record.
//!
//! The jet guard refuses delta = +-3/5 (and |delta -+ 3/5| <= 1/20), delta outside the allowed list, y = +-2/27 and
//! ||y| - 2/27| <= 1/81 at every N, and the 2^-q images of the reserved values, before anything is computed; it lifts
//! only on lift_reserved_guard=1. steps and dup keep 0.1.0's guard (they run at one N) and never lift.

#[allow(dead_code)]
#[path = "../../ensemble/src/sha256.rs"]
mod sha256;

use std::collections::{HashMap, HashSet};
use std::env;
use std::io::{BufRead, BufWriter, Write};
use std::time::Instant;

const VERSION: &str = "0.2.0";
/// The two source files this binary was compiled from, as compiled.
const SRC_MAIN: &[u8] = include_bytes!("main.rs");
const SRC_SHA256: &[u8] = include_bytes!("../../ensemble/src/sha256.rs");

/// sha256 of src/main.rs and of the ensemble engine's src/sha256.rs (reused by #[path]) as compiled into this binary.
fn source_sha256() -> String {
    format!(
        "main.rs:{},sha256.rs:{}",
        sha256::hex(&sha256::sha256(SRC_MAIN)),
        sha256::hex(&sha256::sha256(SRC_SHA256))
    )
}

/// sha256 of the running binary's own bytes.
fn binary_sha256() -> String {
    match env::current_exe().and_then(std::fs::read) {
        Ok(b) => sha256::hex(&sha256::sha256(&b)),
        Err(_) => "CANNOT_SEE".to_string(),
    }
}

fn fail(msg: &str) -> ! {
    eprintln!("JET_FAIL|reason={msg}|json=0");
    std::process::exit(2);
}

// ---------------------------------------------------------------------------------------------------------------------
// Rationals and the guard.

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
struct Rat {
    p: i128,
    q: i128,
}

fn gcd(a: i128, b: i128) -> i128 {
    let (mut a, mut b) = (a.abs(), b.abs());
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    a
}

impl Rat {
    fn new(p: i128, q: i128) -> Rat {
        if q == 0 {
            fail("zero_denominator");
        }
        let g = gcd(p, q).max(1);
        let s = if q < 0 { -1 } else { 1 };
        Rat {
            p: s * p / g,
            q: s * q / g,
        }
    }
    fn parse(s: &str) -> Rat {
        let (a, b) = s.split_once('/').unwrap_or((s, "1"));
        let p: i128 = a.parse().unwrap_or_else(|_| fail("not_a_rational"));
        let q: i128 = b.parse().unwrap_or_else(|_| fail("not_a_rational"));
        if p.abs() > 1 << 40 || q <= 0 || q > 1 << 40 {
            fail("rational_out_of_range");
        }
        Rat::new(p, q)
    }
    fn sub(self, o: Rat) -> Rat {
        Rat::new(self.p * o.q - o.p * self.q, self.q * o.q)
    }
    fn abs(self) -> Rat {
        Rat {
            p: self.p.abs(),
            q: self.q,
        }
    }
    fn le(self, o: Rat) -> bool {
        self.p * o.q <= o.p * self.q
    }
    /// The value at 2^-q, truncated toward zero.
    fn fixed(self, q: u32) -> i128 {
        (self.p << q) / self.q
    }
}

const RESERVED_N: [i64; 3] = [81, 729, 6561];
const ALLOWED_DELTA: [&str; 7] = ["0", "1/4", "-1/4", "1/2", "-1/2", "3/4", "-3/4"];

fn guard(delta: Rat, y: Rat, ns: &[i64]) -> Option<&'static str> {
    for r in [Rat::new(3, 5), Rat::new(-3, 5)] {
        if delta == r {
            return Some("reserved_delta");
        }
        if delta.sub(r).abs().le(Rat::new(1, 20)) {
            return Some("reserved_delta_neighbourhood_1/20");
        }
    }
    if !ALLOWED_DELTA.iter().any(|a| Rat::parse(a) == delta) {
        return Some("delta_not_in_the_allowed_list");
    }
    let y227 = Rat::new(2, 27);
    if y.abs() == y227 {
        return Some("reserved_y_refused_at_every_N_here");
    }
    for n in ns {
        if RESERVED_N.contains(n) && y.abs().sub(y227).abs().le(Rat::new(1, 81)) {
            return Some("reserved_y_neighbourhood_1/81");
        }
    }
    None
}

/// The jet guard (H7): a jet does not depend on N (N enters only the averages), so the y band is refused at every N.
/// None if (delta, y) is allowed at fixed point 2^-q, else the reason.
fn guard_jet(delta: Rat, y: Rat, q: u32) -> Option<&'static str> {
    let one = Rat::new(1, 1);
    for r in [Rat::new(3, 5), Rat::new(-3, 5)] {
        if delta == r {
            return Some("reserved_delta");
        }
        if delta.sub(one).fixed(q) == r.sub(one).fixed(q) {
            return Some("reserved_delta_same_fixed_point");
        }
        if delta.sub(r).abs().le(Rat::new(1, 20)) {
            return Some("reserved_delta_neighbourhood_1/20");
        }
    }
    if !ALLOWED_DELTA.iter().any(|a| Rat::parse(a) == delta) {
        return Some("delta_not_in_the_allowed_list");
    }
    let y227 = Rat::new(2, 27);
    if y.abs() == y227 {
        return Some("reserved_y");
    }
    if y.fixed(q).abs() == y227.fixed(q) {
        return Some("reserved_y_same_fixed_point");
    }
    if y.abs().sub(y227).abs().le(Rat::new(1, 81)) {
        return Some("reserved_y_neighbourhood_1/81_at_every_N");
    }
    None
}

/// Under lift_reserved_guard=1 the jet runs at an allowed delta or at delta = +-3/5 exactly, at any y.
fn lift_admits(delta: Rat) -> bool {
    delta == Rat::new(3, 5)
        || delta == Rat::new(-3, 5)
        || ALLOWED_DELTA.iter().any(|a| Rat::parse(a) == delta)
}

fn kv(args: &[String]) -> HashMap<String, String> {
    let mut m = HashMap::new();
    for a in args {
        if a.contains(['|', '~', '\n', '\r']) {
            fail("argument_with_a_separator");
        }
        match a.split_once('=') {
            Some((k, v)) => {
                if m.insert(k.to_string(), v.to_string()).is_some() {
                    fail("duplicate_key");
                }
            }
            None => fail("argument_without_equals"),
        }
    }
    m
}

const JET_KEYS: [&str; 8] = [
    "delta",
    "y",
    "for_n",
    "p",
    "q",
    "dtden",
    "steps",
    "lift_reserved_guard",
];

/// The jet's arguments, its guard before anything is computed, and its lift: (delta, y, for_n, q, reserved, lifted).
fn checked_guard_jet(m: &HashMap<String, String>) -> (Rat, Rat, Vec<i64>, u32, bool, bool) {
    for k in m.keys() {
        if !JET_KEYS.contains(&k.as_str()) {
            fail("unknown_key");
        }
    }
    let delta = Rat::parse(need(m, "delta"));
    let y = Rat::parse(need(m, "y"));
    let ns: Vec<i64> = list(need(m, "for_n"));
    if ns.iter().any(|&n| n < 2) {
        fail("for_n_below_2");
    }
    let q: u32 = num(need(m, "q"));
    if !(40..=100).contains(&q) {
        fail("q_out_of_range");
    }
    let lifted = match m.get("lift_reserved_guard").map(|s| s.as_str()) {
        None => false,
        Some("1") => true,
        Some(_) => fail("lift_reserved_guard_takes_1_only"),
    };
    let reason = guard_jet(delta, y, q);
    if let Some(r) = reason {
        if !lifted || !lift_admits(delta) {
            eprintln!(
                "JET_REFUSED|reason={r}|delta={}/{}|y={}/{}|lift_requested={}|guard=active|computed=0|json=0",
                delta.p,
                delta.q,
                y.p,
                y.q,
                u8::from(lifted)
            );
            std::process::exit(3);
        }
    }
    (delta, y, ns, q, reason.is_some(), lifted)
}

fn need<'a>(m: &'a HashMap<String, String>, k: &str) -> &'a str {
    m.get(k)
        .map(|s| s.as_str())
        .unwrap_or_else(|| fail(&format!("missing_{k}")))
}

fn num<T: std::str::FromStr>(s: &str) -> T {
    s.parse().unwrap_or_else(|_| fail("not_a_number"))
}

fn list<T: std::str::FromStr>(s: &str) -> Vec<T> {
    s.split(',').map(num).collect()
}

fn checked_guard(m: &HashMap<String, String>) -> (Rat, Rat, Vec<i64>) {
    let delta = Rat::parse(need(m, "delta"));
    let y = Rat::parse(need(m, "y"));
    let ns: Vec<i64> = list(need(m, "for_n"));
    if let Some(r) = guard(delta, y, &ns) {
        println!(
            "CANNOT_SEE|reason={r}|delta={}/{}|y={}/{}|json=0",
            delta.p, delta.q, y.p, y.q
        );
        std::process::exit(3);
    }
    (delta, y, ns)
}

// ---------------------------------------------------------------------------------------------------------------------
// 256-bit fixed-point product.

const M64: u128 = (1u128 << 64) - 1;

/// x * y / 2^q truncated toward zero, through a 256-bit product; refuses a result at or above 2^126.
#[inline]
fn mq(x: i128, y: i128, q: u32) -> i128 {
    let neg = (x < 0) != (y < 0);
    let ux = x.unsigned_abs();
    let uy = y.unsigned_abs();
    let (x1, x0) = (ux >> 64, ux & M64);
    let (y1, y0) = (uy >> 64, uy & M64);
    let ll = x0 * y0;
    let lh = x0 * y1;
    let hl = x1 * y0;
    let hh = x1 * y1;
    let (mid, c1) = lh.overflowing_add(hl);
    let (lo, c2) = ll.overflowing_add(mid << 64);
    let hi = hh + (mid >> 64) + (u128::from(c1) << 64) + u128::from(c2);
    if hi >> (q - 2) != 0 {
        fail("product_overflow");
    }
    let r = ((hi << (128 - q)) | (lo >> q)) as i128;
    if neg {
        -r
    } else {
        r
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// Weighted truncated polynomials in (a, conj a, b, conj b, e).

type Cx = (i128, i128);
type Poly = Vec<Cx>;

struct Basis {
    n: usize,
    mons: Vec<[u8; 5]>,
    wt: Vec<u8>,
    cj: Vec<usize>,
    off: Vec<usize>,
    pr: Vec<(u32, u32)>,
}

impl Basis {
    fn new(p: u8) -> Basis {
        let mut mons: Vec<[u8; 5]> = Vec::new();
        for w in 0..=p {
            for m in 0..=w / 2 {
                let d = w - 2 * m;
                for i in 0..=d {
                    for j in 0..=(d - i) {
                        for k in 0..=(d - i - j) {
                            mons.push([i, j, k, d - i - j - k, m]);
                        }
                    }
                }
            }
        }
        let wt: Vec<u8> = mons
            .iter()
            .map(|e| e[0] + e[1] + e[2] + e[3] + 2 * e[4])
            .collect();
        let idx: HashMap<[u8; 5], usize> = mons.iter().enumerate().map(|(i, &e)| (e, i)).collect();
        let cj: Vec<usize> = mons
            .iter()
            .map(|e| idx[&[e[1], e[0], e[3], e[2], e[4]]])
            .collect();
        let n = mons.len();
        let mut upto = vec![0usize; usize::from(p) + 1];
        for (w, u) in upto.iter_mut().enumerate() {
            *u = wt.iter().filter(|&&x| usize::from(x) <= w).count();
        }
        let mut off = vec![0usize];
        let mut pr: Vec<(u32, u32)> = Vec::new();
        for a in 0..n {
            let room = usize::from(p - wt[a]);
            for b in 0..upto[room] {
                let mut s = [0u8; 5];
                for (t, sv) in s.iter_mut().enumerate() {
                    *sv = mons[a][t] + mons[b][t];
                }
                pr.push((b as u32, idx[&s] as u32));
            }
            off.push(pr.len());
        }
        Basis {
            n,
            mons,
            wt,
            cj,
            off,
            pr,
        }
    }
    fn zero(&self) -> Poly {
        vec![(0, 0); self.n]
    }
    fn conj(&self, a: &Poly) -> Poly {
        let mut c = self.zero();
        for (i, &(re, im)) in a.iter().enumerate() {
            c[self.cj[i]] = (re, -im);
        }
        c
    }
    fn mul(&self, a: &Poly, b: &Poly, q: u32, count: &mut u64) -> Poly {
        let mut c = self.zero();
        for (ia, &(ar, ai)) in a.iter().enumerate() {
            if ar == 0 && ai == 0 {
                continue;
            }
            for &(ib, ic) in &self.pr[self.off[ia]..self.off[ia + 1]] {
                let (br, bi) = b[ib as usize];
                if br == 0 && bi == 0 {
                    continue;
                }
                *count += 1;
                let cc = &mut c[ic as usize];
                cc.0 += mq(ar, br, q) - mq(ai, bi, q);
                cc.1 += mq(ar, bi, q) + mq(ai, br, q);
            }
        }
        c
    }
}

fn padd(a: &Poly, b: &Poly) -> Poly {
    a.iter()
        .zip(b.iter())
        .map(|(x, y)| (x.0 + y.0, x.1 + y.1))
        .collect()
}

fn psub(a: &Poly, b: &Poly) -> Poly {
    a.iter()
        .zip(b.iter())
        .map(|(x, y)| (x.0 - y.0, x.1 - y.1))
        .collect()
}

fn pint(a: &Poly, k: i128) -> Poly {
    a.iter().map(|x| (x.0 * k, x.1 * k)).collect()
}

/// Real scalar s (at 2^-q) times a.
fn psc(a: &Poly, s: i128, q: u32) -> Poly {
    a.iter().map(|x| (mq(x.0, s, q), mq(x.1, s, q))).collect()
}

/// -i a.
fn pmi(a: &Poly) -> Poly {
    a.iter().map(|x| (x.1, -x.0)).collect()
}

/// a + k / den per coefficient (truncating division, as the engine's addk).
fn paddk(a: &Poly, k: &Poly, den: i128) -> Poly {
    a.iter()
        .zip(k.iter())
        .map(|(x, y)| (x.0 + y.0 / den, x.1 + y.1 / den))
        .collect()
}

struct JPar {
    x: i128,
    y: i128,
    q: u32,
}

type JSt = [Poly; 3];

fn jrhs(bs: &Basis, s: &JSt, p: &JPar, cnt: &mut u64) -> JSt {
    let q = p.q;
    let (z0, zp, zm) = (&s[0], &s[1], &s[2]);
    let c0 = bs.conj(z0);
    let cp = bs.conj(zp);
    let cm = bs.conj(zm);
    let abs0 = bs.mul(z0, &c0, q, cnt);
    let absp = bs.mul(zp, &cp, q, cnt);
    let absm = bs.mul(zm, &cm, q, cnt);
    let sq = bs.mul(z0, z0, q, cnt);
    let mut coefp = padd(&abs0, &absm);
    coefp[0].0 += p.x;
    let mut coefm = padd(&abs0, &absp);
    coefm[0].0 += p.x;
    let yz0 = psc(z0, p.y, q);
    let gp = psub(
        &padd(&bs.mul(&coefp, zp, q, cnt), &bs.mul(&cm, &sq, q, cnt)),
        &yz0,
    );
    let gm = psub(
        &padd(&bs.mul(&coefm, zm, q, cnt), &bs.mul(&cp, &sq, q, cnt)),
        &yz0,
    );
    let pm = bs.mul(zp, zm, q, cnt);
    let coef0 = padd(&absp, &absm);
    let g0 = psub(
        &padd(
            &bs.mul(&coef0, z0, q, cnt),
            &pint(&bs.mul(&pm, &c0, q, cnt), 2),
        ),
        &psc(&padd(zp, zm), p.y, q),
    );
    [pmi(&g0), pmi(&gp), pmi(&gm)]
}

fn jaddk(s: &JSt, k: &JSt, den: i128) -> JSt {
    [
        paddk(&s[0], &k[0], den),
        paddk(&s[1], &k[1], den),
        paddk(&s[2], &k[2], den),
    ]
}

fn jrk4(bs: &Basis, s: &JSt, p: &JPar, dtden: i128, cnt: &mut u64) -> JSt {
    let k1 = jrhs(bs, s, p, cnt);
    let k2 = jrhs(bs, &jaddk(s, &k1, 2 * dtden), p, cnt);
    let k3 = jrhs(bs, &jaddk(s, &k2, 2 * dtden), p, cnt);
    let k4 = jrhs(bs, &jaddk(s, &k3, dtden), p, cnt);
    let mut o = s.clone();
    for m in 0..3 {
        for (i, oc) in o[m].iter_mut().enumerate() {
            let sr = k1[m][i].0 + 2 * k2[m][i].0 + 2 * k3[m][i].0 + k4[m][i].0;
            let si = k1[m][i].1 + 2 * k2[m][i].1 + 2 * k3[m][i].1 + k4[m][i].1;
            oc.0 += sr / (6 * dtden);
            oc.1 += si / (6 * dtden);
        }
    }
    o
}

fn print_poly(out: &mut impl Write, step: usize, dtden: i128, name: &str, a: &Poly) {
    let re: Vec<String> = a.iter().map(|c| c.0.to_string()).collect();
    let im: Vec<String> = a.iter().map(|c| c.1.to_string()).collect();
    writeln!(
        out,
        "JET_POLY|step={step}|dtden={dtden}|obs={name}|re={}|im={}|json=0",
        re.join(","),
        im.join(",")
    )
    .unwrap_or_else(|_| fail("write"));
}

/// The largest |coefficient| at each weight 0..=p (re and im parts both counted).
fn max_by_weight(bs: &Basis, a: &Poly, p: u8) -> Vec<i128> {
    let mut w = vec![0i128; usize::from(p) + 1];
    for (i, c) in a.iter().enumerate() {
        let v = c.0.abs().max(c.1.abs());
        let k = usize::from(bs.wt[i]);
        if v > w[k] {
            w[k] = v;
        }
    }
    w
}

fn join_weights(w: &[i128]) -> String {
    let v: Vec<String> = w
        .iter()
        .enumerate()
        .map(|(k, x)| format!("{k}:{x}"))
        .collect();
    v.join(",")
}

/// H5: the number conservation n0 + ns - (1 + e + |a|^2 + |b|^2), coefficientwise, beside a record.
fn print_cons(
    out: &mut impl Write,
    step: usize,
    dtden: i128,
    bs: &Basis,
    n0: &Poly,
    nsum: &Poly,
    q: u32,
) {
    let p = bs.wt.iter().max().copied().unwrap_or(0);
    let one = 1i128 << q;
    let mut dev = padd(n0, nsum);
    for key in [
        [0u8, 0, 0, 0, 0],
        [0, 0, 0, 0, 1],
        [1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0],
    ] {
        let i = bs
            .mons
            .iter()
            .position(|e| *e == key)
            .unwrap_or_else(|| fail("basis"));
        dev[i].0 -= one;
    }
    let dw = max_by_weight(bs, &dev, p);
    let sw = max_by_weight(bs, n0, p);
    let mut ppb: i128 = 0;
    let mut unscaled = 0u32;
    for (d, s) in dw.iter().zip(sw.iter()) {
        if *d == 0 {
            continue;
        }
        if *s == 0 {
            unscaled += 1;
            continue;
        }
        let r = d
            .checked_mul(1_000_000_000)
            .unwrap_or_else(|| fail("cons_overflow"))
            / s;
        ppb = ppb.max(r);
    }
    writeln!(
        out,
        "JET_CONS|step={step}|dtden={dtden}|what=n0+ns-(1+e+abs(a)^2+abs(b)^2)|dev_by_weight={}|n0_scale_by_weight={}|max_dev_over_scale_ppb={ppb}|weights_with_dev_and_no_scale={unscaled}|units=2^-{q}|json=0",
        join_weights(&dw),
        join_weights(&sw)
    )
    .unwrap_or_else(|_| fail("write"));
}

/// The start: z0(0) = sqrt(1 + e) = sum_m binom(1/2, m) e^m (dyadic coefficients, exact at 2^-q); z+(0) = a; z-(0) = b.
fn jet_start(bs: &Basis, p: u8, q: u32) -> JSt {
    let mut z0 = bs.zero();
    let mut c = Rat::new(1, 1);
    for mm in 0..=(p / 2) {
        let idx = bs
            .mons
            .iter()
            .position(|e| *e == [0, 0, 0, 0, mm])
            .unwrap_or_else(|| fail("basis"));
        z0[idx].0 = c.fixed(q);
        let k = i128::from(mm);
        c = Rat::new(c.p * (1 - 2 * k), c.q * 2 * (k + 1));
    }
    let mut zp = bs.zero();
    let mut zm = bs.zero();
    let one = 1i128 << q;
    let pos = |key: [u8; 5]| -> usize {
        bs.mons
            .iter()
            .position(|e| *e == key)
            .unwrap_or_else(|| fail("basis"))
    };
    zp[pos([1, 0, 0, 0, 0])].0 = one;
    zm[pos([0, 0, 1, 0, 0])].0 = one;
    [z0, zp, zm]
}

fn cmd_jet(args: &[String]) {
    let km = kv(args);
    let (delta, y, ns, q, reserved, lifted) = checked_guard_jet(&km);
    let p: u8 = num(need(&km, "p"));
    let dtden: i128 = num(need(&km, "dtden"));
    let steps: Vec<usize> = list(need(&km, "steps"));
    if !(2..=14).contains(&p) || !(1..=4096).contains(&dtden) {
        fail("p_or_dtden_out_of_range");
    }
    if steps.is_empty() || steps.windows(2).any(|w| w[0] >= w[1]) {
        fail("steps_must_be_strictly_increasing");
    }
    let t0 = Instant::now();
    let bs = Basis::new(p);
    let basis_ms = t0.elapsed().as_millis();
    let par = JPar {
        x: delta.sub(Rat::new(1, 1)).fixed(q),
        y: y.fixed(q),
        q,
    };
    let mut st: JSt = jet_start(&bs, p, q);
    let stdout = std::io::stdout();
    let mut out = BufWriter::new(stdout.lock());
    let nlist: Vec<String> = ns.iter().map(|v| v.to_string()).collect();
    let slist: Vec<String> = steps.iter().map(|v| v.to_string()).collect();
    writeln!(
        out,
        "JET_HEAD|tool=jetens_{VERSION}|binary_sha256={}|source_sha256={}|args={}|delta={}/{}|y={}/{}|for_n={}|p={p}|q={q}|dtden={dtden}|steps={}|monomials={}|max_weight={}|product_pairs={}|x_fixed={}|y_fixed={}|reserved={}|guard={}|map=RK4_on_the_scaled_equations(u=1,x=delta-1)|vars=a,conj_a,b,conj_b,e|weights=1,1,1,1,2|start=z0=sqrt(1+e),z+=a,z-=b|float_used=0|json=0",
        binary_sha256(),
        source_sha256(),
        args.join("~"),
        delta.p,
        delta.q,
        y.p,
        y.q,
        nlist.join(","),
        slist.join(","),
        bs.n,
        bs.wt.iter().max().copied().unwrap_or(0),
        bs.pr.len(),
        par.x,
        par.y,
        u8::from(reserved),
        if lifted { "lifted" } else { "active" }
    )
    .unwrap_or_else(|_| fail("write"));
    let mons: Vec<String> = bs
        .mons
        .iter()
        .map(|e| format!("{}.{}.{}.{}.{}", e[0], e[1], e[2], e[3], e[4]))
        .collect();
    writeln!(out, "JET_BASIS|mons={}|json=0", mons.join(";")).unwrap_or_else(|_| fail("write"));
    let last = *steps.iter().max().unwrap_or(&0);
    let mut cnt: u64 = 0;
    let mut next = 0usize;
    let mut int_ns: u128 = 0;
    let mut obs_ns: u128 = 0;
    for step in 0..=last {
        while next < steps.len() && steps[next] == step {
            let to = Instant::now();
            let mut oc: u64 = 0;
            let (z0, zp, zm) = (&st[0], &st[1], &st[2]);
            let c0 = bs.conj(z0);
            let cm = bs.conj(zm);
            let cp = bs.conj(zp);
            let zz = padd(&bs.mul(&c0, zp, q, &mut oc), &bs.mul(&cm, z0, q, &mut oc));
            let bb = bs.mul(&cm, zp, q, &mut oc);
            let n0 = bs.mul(z0, &c0, q, &mut oc);
            let nsum = padd(&bs.mul(zp, &cp, q, &mut oc), &bs.mul(zm, &cm, q, &mut oc));
            let sq = bs.mul(z0, z0, q, &mut oc);
            let cpm = bs.mul(&cp, &cm, q, &mut oc);
            let pr = bs.mul(&cpm, &sq, q, &mut oc);
            let z2 = bs.mul(&zz, &bs.conj(&zz), q, &mut oc);
            let ns2 = bs.mul(&nsum, &nsum, q, &mut oc);
            obs_ns += to.elapsed().as_nanos();
            for (name, poly) in [
                ("Z", &zz),
                ("B", &bb),
                ("n0", &n0),
                ("ns", &nsum),
                ("Pr", &pr),
                ("Z2", &z2),
                ("ns2", &ns2),
            ] {
                print_poly(&mut out, step, dtden, name, poly);
            }
            print_cons(&mut out, step, dtden, &bs, &n0, &nsum, q);
            next += 1;
        }
        if step < last {
            let ti = Instant::now();
            st = jrk4(&bs, &st, &par, dtden, &mut cnt);
            int_ns += ti.elapsed().as_nanos();
        }
    }
    writeln!(
        out,
        "JET_TIME|p={p}|q={q}|basis_ms={basis_ms}|integrate_ms={}|observables_ms={}|steps={last}|complex_term_products={cnt}|total_ms={}|single_thread=1|json=0",
        int_ns / 1_000_000,
        obs_ns / 1_000_000,
        t0.elapsed().as_millis()
    )
    .unwrap_or_else(|_| fail("write"));
    writeln!(out, "JET_DONE|records={}|float_used=0|json=0", steps.len())
        .unwrap_or_else(|_| fail("write"));
    out.flush().unwrap_or_else(|_| fail("write"));
}

// ---------------------------------------------------------------------------------------------------------------------
// The engine's per-sample arithmetic (i64 at 2^40), copied operation for operation from twens 0.3.0 at kappa = 1.

const QE: u32 = 40;
const ONE: i64 = 1i64 << QE;
const ONE128: i128 = 1i128 << QE;

#[inline]
fn m(a: i64, b: i64) -> i64 {
    ((i128::from(a) * i128::from(b)) >> QE) as i64
}

fn isqrt(n: u128) -> u128 {
    if n < 2 {
        return n;
    }
    let bits = 128 - n.leading_zeros();
    let mut x: u128 = 1u128 << bits.div_ceil(2);
    loop {
        let y = (x + n / x) >> 1;
        if y >= x {
            return x;
        }
        x = y;
    }
}

fn parse_q(s: &str) -> i64 {
    let r = Rat::parse(s);
    ((r.p << QE) / r.q) as i64
}

#[derive(Clone, Copy)]
struct Par {
    x: i64,
    u: i64,
    y: i64,
}

type St = [i64; 6];

/// A variant name with its distinct starts, distinct states and distinct state sha256 digests.
type StateSets = (&'static str, HashSet<St>, HashSet<St>, HashSet<[u8; 32]>);

fn rhs(s: &St, p: &Par) -> St {
    let [r0, i0, rp, ip, rm, im] = *s;
    let abs0 = m(r0, r0) + m(i0, i0);
    let absp = m(rp, rp) + m(ip, ip);
    let absm = m(rm, rm) + m(im, im);
    let sq_re = m(r0, r0) - m(i0, i0);
    let sq_im = 2 * m(r0, i0);
    let coefp = p.x + m(p.u, abs0 + absm);
    let coefm = p.x + m(p.u, abs0 + absp);
    let bp_re = m(coefp, rp) + m(rm, sq_re) + m(im, sq_im) - m(p.y, r0);
    let bp_im = m(coefp, ip) + m(rm, sq_im) - m(im, sq_re) - m(p.y, i0);
    let bm_re = m(coefm, rm) + m(rp, sq_re) + m(ip, sq_im) - m(p.y, r0);
    let bm_im = m(coefm, im) + m(rp, sq_im) - m(ip, sq_re) - m(p.y, i0);
    let pm_re = m(rp, rm) - m(ip, im);
    let pm_im = m(rp, im) + m(ip, rm);
    let coef0 = m(p.u, absp + absm);
    let c_re = m(coef0, r0) + 2 * (m(pm_re, r0) + m(pm_im, i0)) - m(p.y, rp + rm);
    let c_im = m(coef0, i0) + 2 * (m(pm_im, r0) - m(pm_re, i0)) - m(p.y, ip + im);
    [c_im, -c_re, bp_im, -bp_re, bm_im, -bm_re]
}

fn addk(a: &St, k: &St, den: i64) -> St {
    let mut o = *a;
    for (oi, ki) in o.iter_mut().zip(k.iter()) {
        *oi += ki / den;
    }
    o
}

fn rk4(s: &St, p: &Par, dtden: i64) -> St {
    let k1 = rhs(s, p);
    let k2 = rhs(&addk(s, &k1, 2 * dtden), p);
    let k3 = rhs(&addk(s, &k2, 2 * dtden), p);
    let k4 = rhs(&addk(s, &k3, dtden), p);
    let mut o = *s;
    for (i, oi) in o.iter_mut().enumerate() {
        *oi += (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) / (6 * dtden);
    }
    o
}

/// The engine's observables of one state: zr, zi, xw, xnc, f, br, bi (at 2^40).
fn obs(s: &St, n: i64) -> [i64; 7] {
    let [r0, i0, rp, ip, rm, im] = *s;
    let zr = m(r0, rp) + m(i0, ip) + m(rm, r0) + m(im, i0);
    let zi = m(r0, ip) - m(i0, rp) + m(rm, i0) - m(im, r0);
    let abs0 = m(r0, r0) + m(i0, i0);
    let absp = m(rp, rp) + m(ip, ip);
    let absm = m(rm, rm) + m(im, im);
    let z2 = m(zr, zr) + m(zi, zi);
    let half_n2 = ONE / (2 * n * n);
    let xw = z2 - (abs0 + (absp + absm) / 2) / n + half_n2;
    let nn_m1_over_n = absp + absm - ONE / n;
    let sq_re = m(r0, r0) - m(i0, i0);
    let sq_im = 2 * m(r0, i0);
    let pm_re = m(rp, rm) - m(ip, im);
    let pm_im = m(rp, im) + m(ip, rm);
    let pair = m(pm_re, sq_re) + m(pm_im, sq_im);
    let xnc = nn_m1_over_n - m(nn_m1_over_n, nn_m1_over_n) + half_n2 + 2 * pair;
    let f = absp + absm - ONE / n;
    let br = m(rm, rp) + m(im, ip);
    let bi = m(rm, ip) - m(im, rp);
    [zr, zi, xw, xnc, f, br, bi]
}

// ---------------------------------------------------------------------------------------------------------------------
// A Taylor step of order K at h = 2^-hb (traj_int.py's recursion), at the engine's 2^40 fixed point.

type C40 = (i64, i64);
const KMAX: usize = 25;

#[inline]
fn c40(a: C40, b: C40) -> C40 {
    (m(a.0, b.0) - m(a.1, b.1), m(a.0, b.1) + m(a.1, b.0))
}

#[inline]
fn cj40(a: C40) -> C40 {
    (a.0, -a.1)
}

#[inline]
fn ca40(a: C40, b: C40) -> C40 {
    (a.0 + b.0, a.1 + b.1)
}

#[inline]
fn cauchy(a: &[C40; KMAX], b: &[C40; KMAX], n: usize, conj_b: bool) -> C40 {
    let mut acc = (0, 0);
    for k in 0..=n {
        let bb = if conj_b { cj40(b[n - k]) } else { b[n - k] };
        acc = ca40(acc, c40(a[k], bb));
    }
    acc
}

/// One Taylor step of order kmax (< KMAX) at h = 2^-hb: the coefficients of z(s) by the Cauchy recursion of the model
/// (traj_int.py's taylor_step), each product floored at 2^-40 as the engine's m(), then Horner at h with shifts.
fn taylor_step(s: &St, p: &Par, kmax: usize, hb: u32) -> St {
    let x = (p.x, 0);
    let y = p.y;
    let mut z0 = [(0i64, 0i64); KMAX];
    let mut zp = [(0i64, 0i64); KMAX];
    let mut zm = [(0i64, 0i64); KMAX];
    let mut q0 = [(0i64, 0i64); KMAX];
    let mut qp = [(0i64, 0i64); KMAX];
    let mut qm = [(0i64, 0i64); KMAX];
    let mut s0 = [(0i64, 0i64); KMAX];
    let mut pm = [(0i64, 0i64); KMAX];
    z0[0] = (s[0], s[1]);
    zp[0] = (s[2], s[3]);
    zm[0] = (s[4], s[5]);
    for n in 0..kmax {
        q0[n] = cauchy(&z0, &z0, n, true);
        qp[n] = cauchy(&zp, &zp, n, true);
        qm[n] = cauchy(&zm, &zm, n, true);
        s0[n] = cauchy(&z0, &z0, n, false);
        pm[n] = cauchy(&zp, &zm, n, false);
        let mut accp = c40(x, zp[n]);
        let mut accm = c40(x, zm[n]);
        let mut acc0: C40 = (0, 0);
        for k in 0..=n {
            accp = ca40(accp, c40(ca40(q0[k], qm[k]), zp[n - k]));
            accm = ca40(accm, c40(ca40(q0[k], qp[k]), zm[n - k]));
            accp = ca40(accp, c40(cj40(zm[k]), s0[n - k]));
            accm = ca40(accm, c40(cj40(zp[k]), s0[n - k]));
            acc0 = ca40(acc0, c40(ca40(qp[k], qm[k]), z0[n - k]));
            let t = c40(pm[k], cj40(z0[n - k]));
            acc0 = ca40(acc0, (2 * t.0, 2 * t.1));
        }
        let yz0 = (m(y, z0[n].0), m(y, z0[n].1));
        accp = (accp.0 - yz0.0, accp.1 - yz0.1);
        accm = (accm.0 - yz0.0, accm.1 - yz0.1);
        let ys = ca40(zp[n], zm[n]);
        acc0 = (acc0.0 - m(y, ys.0), acc0.1 - m(y, ys.1));
        let d = (n + 1) as i64;
        // next coefficient = -i rhs / (n + 1)
        z0[n + 1] = (acc0.1 / d, -acc0.0 / d);
        zp[n + 1] = (accp.1 / d, -accp.0 / d);
        zm[n + 1] = (accm.1 / d, -accm.0 / d);
    }
    let horner = |c: &[C40; KMAX]| -> C40 {
        let mut acc: C40 = (0, 0);
        for v in c[..=kmax].iter().rev() {
            acc = (v.0 + (acc.0 >> hb), v.1 + (acc.1 >> hb));
        }
        acc
    };
    let a0 = horner(&z0);
    let ap = horner(&zp);
    let am = horner(&zm);
    [a0.0, a0.1, ap.0, ap.1, am.0, am.1]
}

fn read_starts(path: &str) -> Vec<(u64, String, St)> {
    let fh = std::fs::File::open(path).unwrap_or_else(|_| fail("open_starts"));
    let mut v = Vec::new();
    for ln in std::io::BufReader::new(fh).lines() {
        let ln = ln.unwrap_or_else(|_| fail("read_starts"));
        let f: Vec<&str> = ln.split('|').collect();
        if f.len() != 9 || f[0] != "S" {
            continue;
        }
        let mut s = [0i64; 6];
        for (i, sv) in s.iter_mut().enumerate() {
            *sv = num(f[3 + i]);
        }
        v.push((num(f[1]), f[2].to_string(), s));
    }
    v
}

fn cmd_steps(args: &[String]) {
    let km = kv(args);
    let (delta, y, ns) = checked_guard(&km);
    if ns.len() != 1 {
        fail("steps_takes_one_N");
    }
    let n = ns[0];
    let par = Par {
        x: parse_q(&format!("{}/{}", delta.p, delta.q)) - ONE,
        u: ONE,
        y: parse_q(&format!("{}/{}", y.p, y.q)),
    };
    let starts = read_starts(need(&km, "file"));
    let method = need(&km, "method").to_string();
    let rec: Vec<usize> = list(need(&km, "rec64"));
    let reps: usize = num(need(&km, "reps"));
    let kmax: usize = km.get("K").map(|s| num(s)).unwrap_or(0);
    let hb: u32 = km.get("hb").map(|s| num(s)).unwrap_or(0);
    let print = km.get("print").map(|s| s == "1").unwrap_or(true);
    // the step in units of 1/64: rk4 at dt = 1/64 takes 1; taylor at h = 2^-hb takes 64 >> hb
    let unit: usize = match method.as_str() {
        "rk4" => 1,
        "taylor" => {
            if !(2..=24).contains(&kmax) || hb > 6 {
                fail("taylor_needs_2<=K<=24_and_hb<=6");
            }
            64usize >> hb
        }
        _ => fail("method_rk4_or_taylor"),
    };
    for r in &rec {
        if r % unit != 0 {
            fail("record_off_the_step_grid");
        }
    }
    let last = *rec.iter().max().unwrap_or(&0);
    let mut best: u128 = u128::MAX;
    let mut vals: Vec<Vec<[i64; 7]>> = Vec::new();
    for _ in 0..reps.max(1) {
        let t0 = Instant::now();
        let mut all = Vec::with_capacity(starts.len());
        for (_, _, s0) in &starts {
            let mut s = *s0;
            let mut out = Vec::with_capacity(rec.len());
            let mut ri = 0usize;
            let mut t = 0usize;
            while ri < rec.len() {
                if t == rec[ri] {
                    out.push(obs(&s, n));
                    ri += 1;
                    continue;
                }
                if t >= last {
                    break;
                }
                s = if unit == 1 {
                    rk4(&s, &par, 64)
                } else {
                    taylor_step(&s, &par, kmax, hb)
                };
                t += unit;
            }
            all.push(out);
        }
        best = best.min(t0.elapsed().as_nanos());
        vals = all;
    }
    let stdout = std::io::stdout();
    let mut o = BufWriter::new(stdout.lock());
    if print {
        for ((idx, var, _), vv) in starts.iter().zip(vals.iter()) {
            for (r, v) in rec.iter().zip(vv.iter()) {
                writeln!(
                    o,
                    "STEP_OBS|idx={idx}|variant={var}|rec64={r}|zr={}|zi={}|xw={}|xnc={}|f={}|br={}|bi={}|json=0",
                    v[0], v[1], v[2], v[3], v[4], v[5], v[6]
                )
                .unwrap_or_else(|_| fail("write"));
            }
        }
    }
    let per = best / (starts.len().max(1) as u128);
    writeln!(
        o,
        "STEP_TIME|method={method}|K={kmax}|hb={hb}|samples={}|reps={reps}|best_total_ns={best}|ns_per_sample={per}|t_end_64ths={last}|single_thread=1|json=0",
        starts.len()
    )
    .unwrap_or_else(|_| fail("write"));
}

// ---------------------------------------------------------------------------------------------------------------------
// The engine's per-sample generator and the repeat counts.

struct Rng {
    s: [u64; 4],
}

fn splitmix(z: &mut u64) -> u64 {
    *z = z.wrapping_add(0x9E37_79B9_7F4A_7C15);
    let mut v = *z;
    v = (v ^ (v >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    v = (v ^ (v >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    v ^ (v >> 31)
}

impl Rng {
    fn sample(seed: u64, idx: u64) -> Self {
        let mut z = seed.wrapping_add(idx.wrapping_mul(0x1000_0000_01B3));
        Self {
            s: [
                splitmix(&mut z),
                splitmix(&mut z),
                splitmix(&mut z),
                splitmix(&mut z),
            ],
        }
    }
    fn next(&mut self) -> u64 {
        let result = self.s[1].wrapping_mul(5).rotate_left(7).wrapping_mul(9);
        let t = self.s[1] << 17;
        self.s[2] ^= self.s[0];
        self.s[3] ^= self.s[1];
        self.s[1] ^= self.s[2];
        self.s[0] ^= self.s[3];
        self.s[2] ^= t;
        self.s[3] = self.s[3].rotate_left(45);
        result
    }
    /// The popcount of 4096 random bits (0..=4096); the engine's Gaussian is (c - 2048) * 2^35 at 2^40.
    fn count(&mut self) -> u64 {
        let mut c: u64 = 0;
        for _ in 0..64 {
            c += u64::from(self.next().count_ones());
        }
        c
    }
}

/// (distinct values, colliding pairs = sum over values of C(multiplicity, 2)).
fn distinct(v: &[u128]) -> (usize, u128) {
    let mut w = v.to_vec();
    w.sort_unstable();
    let mut d = 0usize;
    let mut pairs: u128 = 0;
    let mut i = 0usize;
    while i < w.len() {
        let mut j = i + 1;
        while j < w.len() && w[j] == w[i] {
            j += 1;
        }
        let r = (j - i) as u128;
        pairs += r * (r - 1) / 2;
        d += 1;
        i = j;
    }
    (d, pairs)
}

fn cmd_dup(args: &[String]) {
    let km = kv(args);
    let (delta, y, ns) = checked_guard(&km);
    if ns.len() != 1 {
        fail("dup_takes_one_N");
    }
    let n = ns[0];
    let seed: u64 = num(need(&km, "seed"));
    let count_log: u32 = num(need(&km, "count_log"));
    let states_log: u32 = num(need(&km, "states_log"));
    let rec: usize = num(need(&km, "rec64"));
    if count_log > 24 || states_log > count_log {
        fail("count_log_at_most_24");
    }
    let count = 1u64 << count_log;
    let n128 = i128::from(n);
    let h = isqrt(((ONE128 * ONE128) / (4 * n128)) as u128) as i64;
    let psi_v1 = isqrt(((((2 * n128 + 1) * ONE128) / (2 * n128)) * ONE128) as u128) as i64;
    let par = Par {
        x: parse_q(&format!("{}/{}", delta.p, delta.q)) - ONE,
        u: ONE,
        y: parse_q(&format!("{}/{}", y.p, y.q)),
    };
    let stdout = std::io::stdout();
    let mut o = BufWriter::new(stdout.lock());
    let t0 = Instant::now();
    let mut k2: Vec<u128> = Vec::with_capacity(count as usize);
    let mut k4: Vec<u128> = Vec::with_capacity(count as usize);
    let mut k6: Vec<u128> = Vec::with_capacity(count as usize);
    let mut gs: Vec<[i64; 6]> = Vec::with_capacity(1usize << states_log);
    for idx in 0..count {
        let mut r = Rng::sample(seed, idx);
        let mut c = [0u64; 6];
        for cv in c.iter_mut() {
            *cv = r.count();
        }
        let key = |k: usize| -> u128 {
            let mut v: u128 = 0;
            for cv in c.iter().take(k) {
                v = (v << 13) | u128::from(*cv);
            }
            v
        };
        k2.push(key(2));
        k4.push(key(4));
        k6.push(key(6));
        if idx < (1u64 << states_log) {
            let mut g = [0i64; 6];
            for (gv, cv) in g.iter_mut().zip(c.iter()) {
                *gv = (*cv as i64 - 2048) << (QE - 5);
            }
            gs.push(g);
        }
        if idx < 1024 {
            writeln!(
                o,
                "DUP_G|idx={idx}|g={}:{}:{}:{}:{}:{}|json=0",
                (c[0] as i64 - 2048) << 35,
                (c[1] as i64 - 2048) << 35,
                (c[2] as i64 - 2048) << 35,
                (c[3] as i64 - 2048) << 35,
                (c[4] as i64 - 2048) << 35,
                (c[5] as i64 - 2048) << 35
            )
            .unwrap_or_else(|_| fail("write"));
        }
    }
    let gen_ms = t0.elapsed().as_millis();
    let mut lg = 10u32;
    while lg <= count_log {
        let mm = 1usize << lg;
        let (d2, p2) = distinct(&k2[..mm]);
        let (d4, p4) = distinct(&k4[..mm]);
        let d6 = if lg <= 22 {
            let (d, p) = distinct(&k6[..mm]);
            format!("distinct_k6={d}|repeats_k6={}|pairs_k6={p}", mm - d)
        } else {
            "distinct_k6=not_counted".to_string()
        };
        writeln!(
            o,
            "DUP_TUPLES|seed={seed}|M={mm}|distinct_k2={d2}|repeats_k2={}|pairs_k2={p2}|distinct_k4={d4}|repeats_k4={}|pairs_k4={p4}|{d6}|json=0",
            mm - d2,
            mm - d4
        )
        .unwrap_or_else(|_| fail("write"));
        lg += 2;
    }
    // states: VNC, V1, LOCK, V0 starts of the first 2^states_log samples, RK4 at dt = 1/64 to rec64
    let tst = Instant::now();
    let mut sets: Vec<StateSets> = ["VNC", "V1", "LOCK", "V0"]
        .iter()
        .map(|v| (*v, HashSet::new(), HashSet::new(), HashSet::new()))
        .collect();
    let sharp = |nsum: i64| -> i64 {
        let arg = ONE + (3 * ONE) / (2 * n) - nsum;
        isqrt((i128::from(arg) * ONE128) as u128) as i64
    };
    for (gi, g) in gs.iter().enumerate() {
        let (rp, ip, rm, im) = (m(g[0], h), m(g[1], h), m(g[2], h), m(g[3], h));
        let nsum = m(rp, rp) + m(ip, ip) + m(rm, rm) + m(im, im);
        let lsum = 2 * (m(rp, rp) + m(ip, ip));
        let starts: [St; 4] = [
            [sharp(nsum), 0, rp, ip, rm, im],
            [psi_v1, 0, rp, ip, rm, im],
            [sharp(lsum), 0, rp, ip, rp, -ip],
            [ONE + m(g[4], h), m(g[5], h), rp, ip, rm, im],
        ];
        if gi < 1024 {
            for (k, name) in ["VNC", "V1"].iter().enumerate() {
                let v = starts[k];
                writeln!(
                    o,
                    "DUP_S|idx={gi}|variant={name}|s={}:{}:{}:{}:{}:{}|json=0",
                    v[0], v[1], v[2], v[3], v[4], v[5]
                )
                .unwrap_or_else(|_| fail("write"));
            }
        }
        for (k, s0) in starts.iter().enumerate() {
            let mut s = *s0;
            for _ in 0..rec {
                s = rk4(&s, &par, 64);
            }
            let mut bytes = Vec::with_capacity(48);
            for v in s.iter() {
                bytes.extend_from_slice(&v.to_le_bytes());
            }
            let e = &mut sets[k];
            e.1.insert(*s0);
            e.2.insert(s);
            e.3.insert(sha256::sha256(&bytes));
        }
    }
    for (name, s0, s1, sh) in &sets {
        writeln!(
            o,
            "DUP_STATES|seed={seed}|variant={name}|M={}|rec64={rec}|distinct_starts={}|distinct_states_exact={}|distinct_states_sha256={}|repeats_found_by_hash={}|json=0",
            gs.len(),
            s0.len(),
            s1.len(),
            sh.len(),
            gs.len() - sh.len()
        )
        .unwrap_or_else(|_| fail("write"));
    }
    writeln!(
        o,
        "DUP_TIME|gen_ms={gen_ms}|states_ms={}|json=0",
        tst.elapsed().as_millis()
    )
    .unwrap_or_else(|_| fail("write"));
}

fn main() {
    let a: Vec<String> = env::args().collect();
    if a.len() < 2 {
        fail("usage:jet,steps,dup_with_key=value_arguments,or_version");
    }
    let rest = &a[2..];
    match a[1].as_str() {
        "jet" => cmd_jet(rest),
        "steps" => cmd_steps(rest),
        "dup" => cmd_dup(rest),
        "version" => println!(
            "JET_VERSION|tool=jetens_{VERSION}|binary_sha256={}|source_sha256={}|float_used=0|json=0",
            binary_sha256(),
            source_sha256()
        ),
        _ => fail("unknown_subcommand"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mq_matches_exact_small_products() {
        for (x, y) in [
            (3i128 << 30, 5i128 << 50),
            (-7i128 << 40, 9i128 << 60),
            (1, 1),
            (-(1i128 << 62) - 5, -(1i128 << 61) - 3),
        ] {
            let exact = (x * y) >> 64;
            let r = mq(x, y, 64);
            assert!((r - exact).abs() <= 1, "{x} {y}");
        }
        // a product beyond 2^128: (3 * 2^64 + 7) (5 * 2^64 + 11) / 2^64 = 15 * 2^64 + 68 + floor(77 / 2^64)
        let r = mq((3i128 << 64) + 7, (5i128 << 64) + 11, 64);
        assert_eq!(r, (15i128 << 64) + 68);
        let big = (1i128 << 100) + 12345;
        let r = mq(big, 1i128 << 64, 64);
        assert_eq!(r, big);
    }

    #[test]
    fn guard_refuses_the_reserved_points() {
        assert!(guard(Rat::new(3, 5), Rat::new(0, 1), &[243]).is_some());
        assert!(guard(Rat::new(-3, 5), Rat::new(1, 27), &[243]).is_some());
        assert!(guard(Rat::new(0, 1), Rat::new(2, 27), &[243]).is_some());
        assert!(guard(Rat::new(0, 1), Rat::new(1, 16), &[729]).is_some());
        assert!(guard(Rat::new(0, 1), Rat::new(1, 16), &[243]).is_none());
        assert!(guard(Rat::new(1, 2), Rat::new(1, 27), &[729]).is_none());
        assert!(guard(Rat::new(1, 3), Rat::new(0, 1), &[729]).is_some());
    }

    #[test]
    fn taylor_matches_rk4_on_a_sample() {
        let par = Par {
            x: parse_q("-1"),
            u: ONE,
            y: parse_q("1/27"),
        };
        let s0: St = [ONE, 0, ONE / 60, -ONE / 70, ONE / 80, ONE / 90];
        let mut a = s0;
        for _ in 0..32 {
            a = rk4(&a, &par, 64);
        }
        let mut b = s0;
        for _ in 0..2 {
            b = taylor_step(&b, &par, 14, 2);
        }
        for i in 0..6 {
            assert!((a[i] - b[i]).abs() < 2000, "{i} {} {}", a[i], b[i]);
        }
    }

    #[test]
    fn jet_guard_is_n_free_and_refuses_the_reserved_set() {
        let r = |a: i128, b: i128| Rat::new(a, b);
        for (d, y) in [
            (r(3, 5), r(0, 1)),
            (r(-3, 5), r(1, 27)),
            (r(1, 2), r(2, 27)),
            (r(1, 2), r(-2, 27)),
            (r(0, 1), r(1, 16)),
            (r(-1, 2), r(7, 81)),
            (r(29, 50), r(0, 1)),
            (r(1, 3), r(0, 1)),
        ] {
            assert!(guard_jet(d, y, 64).is_some(), "{d:?} {y:?}");
        }
        for (d, y) in [
            (r(1, 2), r(1, 18)),
            (r(-1, 2), r(4, 81)),
            (r(1, 2), r(1, 27)),
            (r(-1, 2), r(4, 27)),
            (r(0, 1), r(0, 1)),
            (r(1, 2), r(1, 243)),
        ] {
            assert!(guard_jet(d, y, 64).is_none(), "{d:?} {y:?}");
        }
        assert!(lift_admits(r(3, 5)) && lift_admits(r(-3, 5)) && lift_admits(r(1, 2)));
        assert!(!lift_admits(r(29, 50)) && !lift_admits(r(1, 3)));
    }

    #[test]
    fn number_conservation_is_exact_at_the_start() {
        let p = 6u8;
        let q = 64u32;
        let bs = Basis::new(p);
        let st = jet_start(&bs, p, q);
        let mut c = 0u64;
        let n0 = bs.mul(&st[0], &bs.conj(&st[0]), q, &mut c);
        let nsum = padd(
            &bs.mul(&st[1], &bs.conj(&st[1]), q, &mut c),
            &bs.mul(&st[2], &bs.conj(&st[2]), q, &mut c),
        );
        let mut dev = padd(&n0, &nsum);
        for key in [
            [0u8, 0, 0, 0, 0],
            [0, 0, 0, 0, 1],
            [1, 1, 0, 0, 0],
            [0, 0, 1, 1, 0],
        ] {
            let i = bs.mons.iter().position(|e| *e == key).unwrap();
            dev[i].0 -= 1i128 << q;
        }
        assert!(dev.iter().all(|x| *x == (0, 0)));
    }

    #[test]
    fn source_hash_names_both_files() {
        let s = source_sha256();
        assert!(s.starts_with("main.rs:") && s.contains(",sha256.rs:"));
        assert_eq!(s.len(), "main.rs:".len() + 64 + ",sha256.rs:".len() + 64);
    }

    #[test]
    fn jet_at_order_two_is_graded() {
        let b4 = Basis::new(4);
        let b2 = Basis::new(2);
        assert_eq!(b2.n, 15 + 1);
        assert_eq!(&b4.mons[..b2.n], &b2.mons[..]);
    }
}
