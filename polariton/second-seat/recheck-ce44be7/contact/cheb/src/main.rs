//! cheb: a separate integer Chebyshev propagator for the three-mode model, from |N,0,0>.
//! Amplitudes are i64 at 2^62, Chebyshev coefficients come in as integers at 2^62 from a table made with
//! Python big integers. No float anywhere (float_used=0). No code shared with the repo's engine.
//! H = x n + (u/N)[n0 n + n+ n-] + (1/N)(P + P^dag) - y[a0^dag(a+ + a-) + h.c.], real symmetric, so the
//! Chebyshev vectors are real and exp(-iHt)|start> = Sum (2-d_k0)(-i)^k J_k(E t) phi_k.
//! Parity n+ <-> n- is exact, so the recursion runs on the half space p >= m with mirrored reads.

use std::env;
use std::fs;
use std::thread;

const Q: u32 = 62;
const ONE: i128 = 1i128 << Q;

#[derive(Clone, Copy)]
struct Rat {
    n: i128,
    d: i128,
}

fn parse_rat(s: &str) -> Rat {
    match s.split_once('/') {
        Some((a, b)) => Rat {
            n: a.parse().expect("num"),
            d: b.parse().expect("den"),
        },
        None => Rat {
            n: s.parse().expect("int"),
            d: 1,
        },
    }
}

fn sub_rat(a: Rat, b: Rat) -> Rat {
    Rat {
        n: a.n * b.d - b.n * a.d,
        d: a.d * b.d,
    }
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

/// round(2^62 * mul * sqrt(m) / den), for m >= 0, mul >= 0, den > 0.
fn root_q(m: u128, mul: u128, den: u128) -> i64 {
    if m == 0 || mul == 0 {
        return 0;
    }
    let bits = 128 - m.leading_zeros();
    let s = ((126 - bits) / 2).min(Q);
    let r = isqrt(m << (2 * s));
    let num = (r * mul) << (Q - s);
    ((num + den / 2) / den) as i64
}

#[derive(Clone, Copy)]
struct Params {
    n: i128,
    nmax: i128,
    x: Rat,
    u: Rat,
    y: Rat,
}

impl Params {
    fn diag_num(&self, p: i128, m: i128) -> i128 {
        let n = p + m;
        let n0 = self.n - n;
        self.x.n * self.u.d * self.n * n + self.u.n * self.x.d * (n0 * n + p * m)
    }
    fn diag_den(&self) -> i128 {
        self.x.d * self.u.d * self.n
    }
}

/// Half space p >= m, p + m <= nmax.
struct Half {
    nmax: i128,
    start: Vec<usize>,
    states: Vec<(i128, i128)>,
}

impl Half {
    fn new(nmax: i128) -> Self {
        let mut start = Vec::new();
        let mut states = Vec::new();
        let mut m = 0i128;
        while 2 * m <= nmax {
            start.push(states.len());
            let mut p = m;
            while p + m <= nmax {
                states.push((p, m));
                p += 1;
            }
            m += 1;
        }
        Self { nmax, start, states }
    }
    fn index(&self, p: i128, m: i128) -> Option<usize> {
        if p < 0 || m < 0 || p + m > self.nmax {
            return None;
        }
        let (a, b) = if p >= m { (p, m) } else { (m, p) };
        Some(self.start[b as usize] + (a - b) as usize)
    }
}

/// Gershgorin bounds at 2^20: returns (c, e) with integer c, e and spec(H - c) inside [-e, e].
fn bound(par: Params) -> (i128, i128) {
    let half = Half::new(par.nmax);
    let den = par.diag_den();
    let yn = par.y.n.unsigned_abs();
    let yd = par.y.d as u128;
    let bign = par.n;
    let mut lo = i128::MAX;
    let mut hi = i128::MIN;
    let up_pair = |p: i128, m: i128| -> i128 {
        let n0 = bign - p - m;
        if n0 < 2 || p + m + 2 > par.nmax {
            return 0;
        }
        let root = isqrt(((p + 1) as u128 * (m + 1) as u128 * n0 as u128 * (n0 - 1) as u128) << 40) + 1;
        (root / bign as u128) as i128 + 1
    };
    let up_field = |a: i128, b: i128| -> i128 {
        if a <= 0 || b <= 0 {
            return 0;
        }
        let root = isqrt((a as u128 * b as u128) << 40) + 1;
        (root * yn / yd) as i128 + 1
    };
    for &(p, m) in &half.states {
        let n0 = bign - p - m;
        let d20 = (par.diag_num(p, m) << 20).div_euclid(den);
        let mut r: i128 = up_pair(p, m);
        if p >= 1 && m >= 1 {
            r += up_pair(p - 1, m - 1);
        }
        if p + m < par.nmax {
            r += up_field(p + 1, n0) + up_field(m + 1, n0);
        }
        r += up_field(p, n0 + 1) + up_field(m, n0 + 1);
        lo = lo.min(d20 - r - 1);
        hi = hi.max(d20 + r + 2);
    }
    let c = (lo + hi).div_euclid(2 << 20);
    let e_lo = c - (lo >> 20);
    let e_hi = (hi >> 20) + 1 - c;
    let e = e_lo.max(e_hi) + 1;
    (c, e)
}

struct Csr {
    start: Vec<u32>,
    col: Vec<u32>,
    coef: Vec<i64>,
}

fn build(par: Params, half: &Half, c: i128, e: i128) -> Csr {
    let dim = half.states.len();
    let mut start = Vec::with_capacity(dim + 1);
    let mut col = Vec::with_capacity(dim * 7);
    let mut coef = Vec::with_capacity(dim * 7);
    let bign = par.n;
    let den = par.diag_den();
    let scale = (bign * e) as u128;
    let yn = par.y.n;
    let yabs = yn.unsigned_abs();
    let ydn = par.y.d as u128 * e as u128;
    start.push(0u32);
    for &(p, m) in &half.states {
        let n0 = bign - p - m;
        let dnum = par.diag_num(p, m) - c * den;
        let dq = ((dnum << Q) + (den * e) / 2).div_euclid(den * e);
        col.push(half.index(p, m).unwrap() as u32);
        coef.push(dq as i64);
        // pair up: (p,m) <- (p+1,m+1)
        if n0 >= 2 {
            if let Some(j) = half.index(p + 1, m + 1) {
                let mm = (p + 1) as u128 * (m + 1) as u128 * n0 as u128 * (n0 - 1) as u128;
                col.push(j as u32);
                coef.push(root_q(mm, 1, scale));
            }
        }
        // pair down: (p,m) <- (p-1,m-1)
        if p >= 1 && m >= 1 {
            if let Some(j) = half.index(p - 1, m - 1) {
                let mm = p as u128 * m as u128 * (n0 + 2) as u128 * (n0 + 1) as u128;
                col.push(j as u32);
                coef.push(root_q(mm, 1, scale));
            }
        }
        let sign = if yn >= 0 { -1i64 } else { 1i64 };
        if yn != 0 {
            // field: -y sqrt((p+1) n0) to (p+1,m); -y sqrt(p (n0+1)) to (p-1,m); same for m.
            if n0 >= 1 {
                if let Some(j) = half.index(p + 1, m) {
                    col.push(j as u32);
                    coef.push(sign * root_q((p + 1) as u128 * n0 as u128, yabs, ydn));
                }
                if let Some(j) = half.index(p, m + 1) {
                    col.push(j as u32);
                    coef.push(sign * root_q((m + 1) as u128 * n0 as u128, yabs, ydn));
                }
            }
            if p >= 1 {
                if let Some(j) = half.index(p - 1, m) {
                    col.push(j as u32);
                    coef.push(sign * root_q(p as u128 * (n0 + 1) as u128, yabs, ydn));
                }
            }
            if m >= 1 {
                if let Some(j) = half.index(p, m - 1) {
                    col.push(j as u32);
                    coef.push(sign * root_q(m as u128 * (n0 + 1) as u128, yabs, ydn));
                }
            }
        }
        start.push(col.len() as u32);
    }
    Csr { start, col, coef }
}

/// row-range mat-vec, in place on `prev`: prev <- round(mult * H phi) - prev, or prev <- round(H phi) when first.
fn step_rows(a: &Csr, phi: &[i64], prev: &mut [i64], first_row: usize, first: bool) {
    let shift = if first { Q } else { Q - 1 };
    let half_ulp = 1i128 << (shift - 1);
    for (i, slot) in prev.iter_mut().enumerate() {
        let r = first_row + i;
        let (s, t) = (a.start[r] as usize, a.start[r + 1] as usize);
        let mut sum: i128 = 0;
        for (col, coef) in a.col[s..t].iter().zip(a.coef[s..t].iter()) {
            sum += i128::from(*coef) * i128::from(phi[*col as usize]);
        }
        let v = ((sum + half_ulp) >> shift) as i64;
        *slot = if first { v } else { v - *slot };
    }
}

struct TimeTable {
    label: String,
    coef: Vec<i64>,
}

fn load_table(path: &str) -> Vec<TimeTable> {
    let text = fs::read_to_string(path).expect("table");
    let mut it = text.lines();
    let mut out = Vec::new();
    while let Some(head) = it.next() {
        let mut w = head.split_whitespace();
        let label = w.next().expect("label").to_string();
        let count: usize = w.next().expect("count").parse().expect("count");
        let mut coef = Vec::with_capacity(count);
        for _ in 0..count {
            coef.push(it.next().expect("row").trim().parse::<i64>().expect("coef"));
        }
        out.push(TimeTable { label, coef });
    }
    out
}

/// Full space on (p, m), p + m <= nmax.
struct Full {
    nmax: i128,
    start: Vec<usize>,
    dim: usize,
}

impl Full {
    fn new(nmax: i128) -> Self {
        let mut start = Vec::with_capacity(nmax as usize + 2);
        let mut d = 0usize;
        for p in 0..=nmax {
            start.push(d);
            d += (nmax - p + 1) as usize;
        }
        Self { nmax, start, dim: d }
    }
    fn index(&self, p: i128, m: i128) -> usize {
        self.start[p as usize] + m as usize
    }
    fn has(&self, p: i128, m: i128) -> bool {
        p >= 0 && m >= 0 && p + m <= self.nmax
    }
}

#[derive(Clone, Default)]
struct Cx {
    re: i128,
    im: i128,
}

fn q60(v: i128) -> i128 {
    v >> 64
}

fn e18_from_q60(v: i128) -> i128 {
    (v * 1_000_000_000_000_000_000i128) >> 60
}

#[inline]
fn mul_q(e: i64, v: i64) -> i64 {
    ((i128::from(e) * i128::from(v) + (1i128 << (Q - 1))) >> Q) as i64
}

#[inline]
fn add_term(acc: &mut Cx, a: (i64, i64), e: i64, b: (i64, i64)) {
    let (ar, ai) = (i128::from(a.0), i128::from(a.1));
    let (br, bi) = (i128::from(mul_q(e, b.0)), i128::from(mul_q(e, b.1)));
    acc.re += ar * br + ai * bi;
    acc.im += ar * bi - ai * br;
}

#[derive(Default)]
struct Sums {
    norm: Cx,
    f: Cx,
    c2: Cx,
    n0n: Cx,
    n2: Cx,
    ch2: Cx,
    p: Cx,
    a: Cx,
    b: Cx,
    boundary: Cx,
    n0pl: Cx,
}

/// (A/N) applied to a full-space vector: (A psi)(p,m) = sqrt((p+1) n0) psi(p+1,m) + sqrt(m (n0+1)) psi(p,m-1).
fn apply_a(full: &Full, bign: i128, re: &[i64], im: &[i64]) -> (Vec<i64>, Vec<i64>) {
    let den = bign as u128;
    let mut out_re = vec![0i64; full.dim];
    let mut out_im = vec![0i64; full.dim];
    for p in 0..=full.nmax {
        for m in 0..=(full.nmax - p) {
            let n0 = bign - p - m;
            let i = full.index(p, m);
            let mut sr = 0i128;
            let mut si = 0i128;
            if full.has(p + 1, m) && n0 >= 1 {
                let j = full.index(p + 1, m);
                let e = root_q((p + 1) as u128 * n0 as u128, 1, den);
                sr += i128::from(mul_q(e, re[j]));
                si += i128::from(mul_q(e, im[j]));
            }
            if m >= 1 {
                let j = full.index(p, m - 1);
                let e = root_q(m as u128 * (n0 + 1) as u128, 1, den);
                sr += i128::from(mul_q(e, re[j]));
                si += i128::from(mul_q(e, im[j]));
            }
            out_re[i] = sr as i64;
            out_im[i] = si as i64;
        }
    }
    (out_re, out_im)
}

fn dot(re_a: &[i64], im_a: &[i64], re_b: &[i64], im_b: &[i64]) -> Cx {
    let mut c = Cx::default();
    for i in 0..re_a.len() {
        let (ar, ai) = (i128::from(re_a[i]), i128::from(im_a[i]));
        let (br, bi) = (i128::from(re_b[i]), i128::from(im_b[i]));
        c.re += ar * br + ai * bi;
        c.im += ar * bi - ai * br;
    }
    c
}

fn read_row(par: Params, full: &Full, re: &[i64], im: &[i64], moments: usize) -> String {
    let bign = par.n;
    let n2u = (bign * bign) as u128;
    let nu = bign as u128;
    let mut s = Sums::default();
    let frac = |num: i128, den: i128| -> i64 { ((num << Q) / den) as i64 };
    for p in 0..=full.nmax {
        for m in 0..=(full.nmax - p) {
            let i = full.index(p, m);
            let v = (re[i], im[i]);
            if v.0 == 0 && v.1 == 0 {
                continue;
            }
            let n = p + m;
            let n0 = bign - n;
            let w = i128::from(v.0) * i128::from(v.0) + i128::from(v.1) * i128::from(v.1);
            s.norm.re += w;
            if n + 2 >= full.nmax && full.nmax < bign {
                s.boundary.re += w;
            }
            add_term(&mut s.f, v, frac(n, bign), v);
            add_term(&mut s.c2, v, frac(p * m, bign * bign), v);
            add_term(&mut s.n0n, v, frac(n0 * n, bign * bign), v);
            add_term(&mut s.n2, v, frac(n * n, bign * bign), v);
            add_term(&mut s.ch2, v, frac((p - m) * (p - m), bign * bign), v);
            add_term(&mut s.n0pl, v, frac(n0 + p, bign), v);
            if n0 >= 2 && full.has(p + 1, m + 1) {
                let t = full.index(p + 1, m + 1);
                let e = root_q((p + 1) as u128 * (m + 1) as u128 * n0 as u128 * (n0 - 1) as u128, 1, n2u);
                add_term(&mut s.p, (re[t], im[t]), e, v);
            }
            if n0 >= 1 && full.has(p + 1, m) {
                // a0^dag a+ from (p+1,m) to (p,m)
                let t = full.index(p + 1, m);
                let e = root_q((p + 1) as u128 * n0 as u128, 1, nu);
                add_term(&mut s.a, v, e, (re[t], im[t]));
            }
            if n0 >= 1 && full.has(p, m + 1) {
                // a-^dag a0 from (p,m) to (p,m+1)
                let t = full.index(p, m + 1);
                let e = root_q((m + 1) as u128 * n0 as u128, 1, nu);
                add_term(&mut s.a, (re[t], im[t]), e, v);
            }
            if p >= 1 && full.has(p - 1, m + 1) {
                // a-^dag a+ from (p,m) to (p-1,m+1)
                let t = full.index(p - 1, m + 1);
                let e = root_q(p as u128 * (m + 1) as u128, 1, nu);
                add_term(&mut s.b, (re[t], im[t]), e, v);
            }
        }
    }
    let bq = bign;
    let x_tilde_q104 = (s.n0n.re + 2 * s.p.re) >> 20;
    let c1_q104 = x_tilde_q104 * 2 * bq / (bq - 1);
    let c2_q104 = (s.c2.re >> 20) * 2 * bq / (bq - 1);
    let a_q60 = q60(s.a.re);
    let b_q60 = q60(s.b.re);
    let a1_q60 = 2 * a_q60.abs();
    let d2_q60 = 2 * b_q60.abs();
    let c1_q60 = c1_q104 >> 44;
    let c2_q60 = c2_q104 >> 44;
    // V^2 = A1^2/(2 C1) with A1, C1 at 2^60 each: A1^2 is 2^120. Keep 2^60.
    let v2_q60 = if c1_q60 == 0 {
        0
    } else {
        (a1_q60 * a1_q60) / (2 * c1_q60)
    };
    // energy/N = x f + u (n0n + c2) + 2 Re P - 2 y Re A  (each piece at 2^124 -> 2^60)
    let f_q60 = q60(s.f.re);
    let en = (f_q60 * par.x.n) / par.x.d + ((q60(s.n0n.re) + q60(s.c2.re)) * par.u.n) / par.u.d + 2 * q60(s.p.re)
        - (2 * a_q60 * par.y.n) / par.y.d;
    let mut row = format!(
        "norm_off_e18={}|f_e18={}|jbar_e12={}|A_e18={}|Aim_e18={}|B_e18={}|Bim_e18={}|C1_e18={}|C2_e18={}|A1_e18={}|D2_e18={}|V2_e18={}|energy_over_N_e18={}|n2_e18={}|ch2_e18={}|Pre_e18={}|Pim_e18={}|boundary_e18={}",
        e18_from_q60(q60(s.norm.re) - (1i128 << 60)),
        e18_from_q60(f_q60),
        (((f_q60 * bign) / 2) * 1_000_000_000_000i128) >> 60,
        e18_from_q60(a_q60),
        e18_from_q60(q60(s.a.im)),
        e18_from_q60(b_q60),
        e18_from_q60(q60(s.b.im)),
        e18_from_q60(c1_q60),
        e18_from_q60(c2_q60),
        e18_from_q60(a1_q60),
        e18_from_q60(d2_q60),
        e18_from_q60(v2_q60),
        e18_from_q60(en),
        e18_from_q60(q60(s.n2.re)),
        e18_from_q60(q60(s.ch2.re)),
        e18_from_q60(q60(s.p.re)),
        e18_from_q60(q60(s.p.im)),
        e18_from_q60(q60(s.boundary.re)),
    );
    if moments > 0 {
        // w1 = (A/N) psi, ..., read <A^m>/N^m and ||A^m psi||^2/N^(2m)
        let mut wr = re.to_vec();
        let mut wi = im.to_vec();
        for k in 1..=moments {
            let (nr, ni) = apply_a(full, bign, &wr, &wi);
            wr = nr;
            wi = ni;
            let mean = dot(re, im, &wr, &wi);
            let nrm = dot(&wr, &wi, &wr, &wi);
            row.push_str(&format!(
                "|Am{k}_re_e18={}|Am{k}_im_e18={}|Am{k}_nrm_e18={}",
                e18_from_q60(q60(mean.re)),
                e18_from_q60(q60(mean.im)),
                e18_from_q60(q60(nrm.re))
            ));
            if k == 1 {
                // the identity read on the state: X/N^2 = ||A psi||^2/N^2 - <n0 + n+>/N^2
                let n0pl_q60 = q60(s.n0pl.re) / bign;
                let x_id_q60 = q60(nrm.re) - n0pl_q60;
                let x_dir_q60 = x_tilde_q104 >> 44;
                row.push_str(&format!(
                    "|identity_X_off_e18={}",
                    e18_from_q60(x_id_q60 - x_dir_q60)
                ));
            }
        }
    }
    row
}

struct RunArgs<'a> {
    par: Params,
    c: i128,
    e: i128,
    tables: &'a [TimeTable],
    threads: usize,
    moments: usize,
    delta_text: &'a str,
    y_text: &'a str,
    u_text: &'a str,
}

fn run(a: &RunArgs) {
    let par = a.par;
    let half = Half::new(par.nmax);
    let dim = half.states.len();
    let csr = build(par, &half, a.c, a.e);
    let nt = a.tables.len();
    let kmax = a.tables.iter().map(|t| t.coef.len()).max().unwrap_or(0);
    let slots = 2 * nt;
    let mut acc = vec![0i128; dim * slots];
    let mut prev = vec![0i64; dim];
    let mut cur = vec![0i64; dim];
    cur[0] = ONE as i64; // phi_0, index of (0,0) is 0
    let threads = a.threads.max(1);
    let chunk = dim.div_ceil(threads);
    for k in 0..kmax {
        // accumulate phi_k into each time
        let mut active: Vec<(usize, i64, u32)> = Vec::with_capacity(nt);
        for (j, t) in a.tables.iter().enumerate() {
            if k < t.coef.len() && t.coef[k] != 0 {
                let c = t.coef[k];
                let sh = if k == 0 { 24 } else { 23 };
                // (-i)^k
                let (slot, signed) = match k % 4 {
                    0 => (2 * j, c),
                    1 => (2 * j + 1, -c),
                    2 => (2 * j, -c),
                    _ => (2 * j + 1, c),
                };
                active.push((slot, signed, sh));
            }
        }
        let next_needed = k + 1 < kmax;
        if threads == 1 {
            for (row, cells) in acc.chunks_mut(slots).enumerate() {
                let v = i128::from(cur[row]);
                if v != 0 {
                    for &(slot, coef, sh) in &active {
                        cells[slot] += (i128::from(coef) * v) >> sh;
                    }
                }
            }
            if next_needed {
                step_rows(&csr, &cur, &mut prev, 0, k == 0);
            }
        } else {
            thread::scope(|s| {
                let cur_ref = &cur;
                let csr_ref = &csr;
                let active_ref = &active;
                let first = k == 0;
                for (ci, (acc_chunk, prev_chunk)) in acc.chunks_mut(chunk * slots).zip(prev.chunks_mut(chunk)).enumerate() {
                    s.spawn(move || {
                        let first_row = ci * chunk;
                        for (i, cells) in acc_chunk.chunks_mut(slots).enumerate() {
                            let v = i128::from(cur_ref[first_row + i]);
                            if v != 0 {
                                for &(slot, coef, sh) in active_ref {
                                    cells[slot] += (i128::from(coef) * v) >> sh;
                                }
                            }
                        }
                        if next_needed {
                            step_rows(csr_ref, cur_ref, prev_chunk, first_row, first);
                        }
                    });
                }
            });
        }
        std::mem::swap(&mut prev, &mut cur);
        // now cur = phi_{k+1}, prev = phi_k
    }
    // read out each time on the full space
    let full = Full::new(par.nmax);
    let round38 = 1i128 << 37;
    for (j, t) in a.tables.iter().enumerate() {
        let mut re = vec![0i64; full.dim];
        let mut im = vec![0i64; full.dim];
        for p in 0..=par.nmax {
            for m in 0..=(par.nmax - p) {
                let h = half.index(p, m).unwrap();
                let i = full.index(p, m);
                re[i] = ((acc[h * slots + 2 * j] + round38) >> 38) as i64;
                im[i] = ((acc[h * slots + 2 * j + 1] + round38) >> 38) as i64;
            }
        }
        let body = read_row(par, &full, &re, &im, a.moments);
        println!(
            "ROW|N={}|nmax={}|u={}|delta={}|y={}|t={}|c={}|E={}|k={}|float_used=0|{}|json=0",
            par.n,
            par.nmax,
            a.u_text,
            a.delta_text,
            a.y_text,
            t.label,
            a.c,
            a.e,
            t.coef.len(),
            body
        );
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mode = args.get(1).map(String::as_str).unwrap_or("");
    let get = |i: usize| -> &str { args.get(i).map(String::as_str).expect("argument") };
    match mode {
        "bound" => {
            // bound N nmax u delta y
            let n: i128 = get(2).parse().expect("N");
            let nmax: i128 = get(3).parse().expect("nmax");
            let u = parse_rat(get(4));
            let delta = parse_rat(get(5));
            let y = parse_rat(get(6));
            let x = sub_rat(delta, u);
            let (c, e) = bound(Params { n, nmax, x, u, y });
            println!("{c} {e}");
        }
        "run" => {
            // run N nmax u delta y c E table threads moments
            let n: i128 = get(2).parse().expect("N");
            let nmax: i128 = get(3).parse().expect("nmax");
            let u = parse_rat(get(4));
            let delta = parse_rat(get(5));
            let y = parse_rat(get(6));
            let x = sub_rat(delta, u);
            let c: i128 = get(7).parse().expect("c");
            let e: i128 = get(8).parse().expect("E");
            let tables = load_table(get(9));
            let threads: usize = get(10).parse().expect("threads");
            let moments: usize = get(11).parse().expect("moments");
            run(&RunArgs {
                par: Params { n, nmax, x, u, y },
                c,
                e,
                tables: &tables,
                threads,
                moments,
                delta_text: get(5),
                y_text: get(6),
                u_text: get(4),
            });
        }
        _ => {
            eprintln!("usage: cheb bound N nmax u delta y | cheb run N nmax u delta y c E table threads moments");
            std::process::exit(2);
        }
    }
}
