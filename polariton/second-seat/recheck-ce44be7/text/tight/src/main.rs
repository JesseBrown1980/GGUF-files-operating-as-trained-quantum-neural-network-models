//! The three-mode polariton test, in integers.
//!
//! Three plane waves m = 0, +1, -1, so N polaritons are N qutrits in their exact symmetric space, with dimension
//! (N+1)(N+2)/2. In units JN = 1 the Hamiltonian is
//!   H = x(n+ + n-) + (u/N)[n0(n+ + n-) + n+ n-] + (1/N)(P + P^dag) - y[a0^dag(a+ + a-) + h.c.],  P = a+^dag a-^dag a0 a0.
//! Three engines: exact-inertia levels of the fixed-momentum tridiagonal sectors at scale 2^60, restarted Lanczos on the
//! full space for pinned ground states, and a reversible leapfrog of integer shears for a quench from |N,0,0>.
//!
//! usage = polariton_three_mode sector | rotor | pin | quench | quench_pin | reversal | wavevector | taylor | control | window | conversion | all
#![allow(dead_code, unused)]

use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Mutex;
use std::time::Instant;

const SCALE: u32 = 60;
const WORKERS: usize = 5;

#[derive(Clone, Copy, PartialEq, Eq)]
struct Q {
    n: i128,
    d: i128,
}

const fn q(n: i128, d: i128) -> Q {
    Q { n, d }
}

impl Q {
    fn text(self) -> String {
        if self.d == 1 {
            format!("{}", self.n)
        } else {
            format!("{}/{}", self.n, self.d)
        }
    }
}

fn gcd(a: i128, b: i128) -> i128 {
    if b == 0 {
        a.abs()
    } else {
        gcd(b, a % b)
    }
}

fn add(a: Q, b: Q) -> Q {
    let (n, d) = (a.n * b.d + b.n * a.d, a.d * b.d);
    let g = gcd(n, d).max(1);
    Q { n: n / g, d: d / g }
}

fn round_div(num: i128, den: i128) -> i128 {
    if num >= 0 {
        (num + den / 2) / den
    } else {
        -((-num + den / 2) / den)
    }
}

fn isqrt(n: u128) -> u128 {
    if n < 2 {
        return n;
    }
    let mut x = 1u128 << ((129 - n.leading_zeros()) / 2);
    loop {
        let y = (x + n / x) / 2;
        if y >= x {
            return x;
        }
        x = y;
    }
}

/// sqrt(m) with as many fractional bits as fit: floor(sqrt(m) * 2^bits), and bits.
fn root_bits(m: u128) -> (i128, u32) {
    if m == 0 {
        return (0, 0);
    }
    let bits = (126 - (128 - m.leading_zeros())) / 2;
    (isqrt(m << (2 * bits)) as i128, bits)
}

/// value * 2^(to - from), with a shift either way.
fn rescale(value: i128, from: u32, to: u32) -> i128 {
    if from >= to {
        value >> (from - to)
    } else {
        value << (to - from)
    }
}

fn parallel<T: Send, F: Fn(usize) -> T + Sync>(count: usize, workers: usize, job: F) -> Vec<T> {
    let next = AtomicUsize::new(0);
    let out: Mutex<Vec<Option<T>>> = Mutex::new((0..count).map(|_| None).collect());
    std::thread::scope(|s| {
        for _ in 0..workers {
            s.spawn(|| loop {
                let i = next.fetch_add(1, Ordering::SeqCst);
                if i >= count {
                    break;
                }
                let value = job(i);
                out.lock().unwrap()[i] = Some(value);
            });
        }
    });
    out.into_inner()
        .unwrap()
        .into_iter()
        .map(|v| v.unwrap())
        .collect()
}

fn ppb(fix: i128) -> i128 {
    (fix * 1_000_000_000) >> SCALE
}

fn ppm(fix: i128) -> i128 {
    (fix * 1_000_000) >> SCALE
}

// ---- Levels of a fixed-momentum sector: n+ = j + P, n- = j, entries of H/N at scale 2^60.

/// o^2 of the tridiagonal at 2^90: (n+ + 1)(n- + 1) n0 (n0 - 1) / N^4, floor exact by long division, with no roots.
fn sector_o2(n: u64, charge: u64) -> Vec<i128> {
    let top = (n - charge) / 2;
    let big = i128::from(n);
    (0..top)
        .map(|j| {
            let (plus, minus) = (i128::from(j + charge), i128::from(j));
            let n0 = big - 2 * minus - i128::from(charge);
            let den = (big * big * big * big) as u128;
            let mut rem = ((plus + 1) * (minus + 1) * n0 * (n0 - 1)) as u128;
            let mut quo = 0u128;
            for _ in 0..5 {
                rem <<= 18;
                quo = (quo << 18) + rem / den;
                rem %= den;
            }
            quo as i128
        })
        .collect()
}

/// Perturbation of x or of kappa, in steps of 2^-m.
#[derive(Clone, Copy)]
struct Shift {
    sign: i128,
    m: u32,
}

const NO_SHIFT: Shift = Shift { sign: 0, m: 1 };

fn sector_d(n: u64, charge: u64, x: Q, u: Q, dx: Shift, kappa: Shift) -> Vec<i64> {
    let top = (n - charge) / 2;
    let big = i128::from(n);
    (0..=top)
        .map(|j| {
            let (plus, minus) = (i128::from(j + charge), i128::from(j));
            let n0 = big - plus - minus;
            let sum = plus + minus;
            let mut d = round_div((x.n * sum) << SCALE, x.d * big);
            if dx.sign != 0 {
                d += round_div(dx.sign * (sum << (SCALE - dx.m)), big);
            }
            d += round_div((u.n * (n0 * sum + plus * minus)) << SCALE, u.d * big * big);
            if kappa.sign != 0 {
                d += round_div(
                    kappa.sign * ((plus * minus) << (SCALE - kappa.m)),
                    big * big,
                );
            }
            d as i64
        })
        .collect()
}

fn count_below(d: &[i64], o2: &[i128], lambda: i64) -> usize {
    // A zero pivot is read as a tiny negative one, so it is counted as negative. Here o^2 is at 2^90.
    let signed = |q: i128| if q == 0 { -1 } else { q };
    let mut q = signed(i128::from(d[0] - lambda));
    let mut count = usize::from(q < 0);
    for (dk, ok) in d[1..].iter().zip(o2.iter()) {
        q = signed(i128::from(*dk - lambda) - (*ok << 30) / q);
        if q < 0 {
            count += 1;
        }
    }
    count
}

fn level(d: &[i64], o2: &[i128], index: usize, seed: i64, start_width: i64) -> i64 {
    let mut w = start_width.max(16);
    let mut lo = seed.saturating_sub(w);
    while count_below(d, o2, lo) > index {
        w = w.saturating_mul(4);
        lo = seed.saturating_sub(w);
    }
    w = start_width.max(16);
    let mut hi = seed.saturating_add(w);
    while count_below(d, o2, hi) <= index {
        w = w.saturating_mul(4);
        hi = seed.saturating_add(w);
    }
    while hi - lo > 1 {
        let mid = lo + (hi - lo) / 2;
        if count_below(d, o2, mid) > index {
            hi = mid;
        } else {
            lo = mid;
        }
    }
    lo
}

fn sector_point(n: u64, u: Q, x: Q, critical: bool) -> String {
    let o2 = sector_o2(n, 0);
    let power = {
        let (mut p, mut v) = (0u32, n);
        while v > 1 {
            v /= 3;
            p += 1;
        }
        p
    };
    let m = if critical { 20 + power / 2 } else { 20 };
    let hh = 1i64 << (SCALE - m);
    let plain = |s: i128| Shift { sign: s, m };
    let d0 = sector_d(n, 0, x, u, NO_SHIFT, NO_SHIFT);
    let e0 = level(&d0, &o2, 0, 0, 1 << 56);
    let gap_seed = e0 + ((1i64 << SCALE) / n as i64);
    let e1 = if d0.len() > 1 {
        level(&d0, &o2, 1, gap_seed, (1i64 << SCALE) / n as i64)
    } else {
        e0
    };
    drop(d0);
    let solve = |dx: Shift, kappa: Shift, seed: i64, width: i64| -> i64 {
        let d = sector_d(n, 0, x, u, dx, kappa);
        level(&d, &o2, 0, seed, width)
    };
    let up = solve(plain(1), NO_SHIFT, e0, hh);
    let down = solve(plain(-1), NO_SHIFT, e0 - (up - e0), 1 << 12);
    let k_up = solve(NO_SHIFT, plain(1), e0, hh);
    let k_down = solve(NO_SHIFT, plain(-1), e0 - (k_up - e0), 1 << 12);
    // Central differences at 2^60: f = <n+ + n->/N and s = <n+ n->/N^2.
    let f = i128::from(up - down) << (m - 1);
    let s = i128::from(k_up - k_down) << (m - 1);
    let jbar_ppb = (f * i128::from(n) / 2 * 1_000_000_000) >> SCALE;
    let big = i128::from(n);
    let gap_ppb = ppb(i128::from(e1 - e0) * big);
    // W_k/N^2 = (f - 4s) + 2Re<P>/N^2, and the energy gives 2Re<P>/N^2 = e - x f - u (f - 3s).
    let e = i128::from(e0);
    let xf = (f * x.n) / x.d;
    let uterm = ((f - 3 * s) * u.n) / u.d;
    let wk = f - 4 * s + e - xf - uterm;
    let n_over = if n > 1 {
        big * (1 << 20) / (big - 1)
    } else {
        1 << 20
    };
    let c1 = (2 * wk * n_over) >> 20;
    let c2 = (2 * s * n_over) >> 20;
    format!(
        "POLARITON_SECTOR|N={n}|u={}|x={}|P=0|e_at_2^60={e0}|e_ppb={}|f_ppb={}|jbar_ppb={jbar_ppb}|gap_ppb={gap_ppb}|C1_ppm={}|C1_times_N_ppm={}|C2_ppm={}|fd_step=2^-{m}|json=0",
        u.text(),
        x.text(),
        ppb(e),
        ppb(f),
        ppm(c1),
        ppm(c1 * big),
        ppm(c2)
    )
}

fn rotor_point(n: u64, u: Q, x: Q, charge: u64) -> String {
    let d0 = sector_d(n, 0, x, u, NO_SHIFT, NO_SHIFT);
    let e0 = level(&d0, &sector_o2(n, 0), 0, 0, 1 << 56);
    drop(d0);
    let o2 = sector_o2(n, charge);
    let d = sector_d(n, charge, x, u, NO_SHIFT, NO_SHIFT);
    let e = level(&d, &o2, 0, e0, 1 << 56);
    let big = i128::from(n);
    let above = i128::from(e - e0);
    format!(
        "POLARITON_SECTOR|N={n}|u={}|x={}|P={charge}|e_at_2^60={e}|e_ppb={}|N2_times_e_above_P0_ppm={}|json=0",
        u.text(),
        x.text(),
        ppb(i128::from(e)),
        (above * big * big * 1_000_000) >> SCALE
    )
}

fn run_sector() {
    let ordered = [
        (q(0, 1), q(0, 1)),
        (q(0, 1), q(1, 2)),
        (q(0, 1), q(-1, 2)),
        (q(1, 2), q(0, 1)),
        (q(1, 2), q(1, 4)),
        (q(1, 1), q(-1, 4)),
        (q(1, 1), q(-1, 8)),
    ];
    let disordered = [q(2, 1), q(3, 2)];
    let units = [q(0, 1), q(1, 2), q(1, 1)];
    let mut jobs: Vec<(u64, Q, Q, bool)> = Vec::new();
    let mut n = 1u64;
    for power in 1..=16u32 {
        n *= 3;
        if power <= 13 {
            for &(u, x) in &ordered {
                jobs.push((n, u, x, false));
            }
            for &delta in &disordered {
                for &u in &units {
                    jobs.push((n, u, add(delta, q(-u.n, u.d)), false));
                }
            }
            for &u in &units {
                jobs.push((n, u, add(q(1, 1), q(-u.n, u.d)), true));
            }
        } else {
            jobs.push((n, q(1, 2), q(1, 2), true));
            jobs.push((n, q(1, 2), q(0, 1), false));
            jobs.push((n, q(1, 2), q(3, 2), false));
        }
    }
    let n23 = 23_887_872u64;
    jobs.push((n23, q(1, 2), q(1, 2), true));
    jobs.push((n23, q(1, 2), q(0, 1), false));
    jobs.push((n23, q(1, 2), q(3, 2), false));
    let start = Instant::now();
    let rows = parallel(jobs.len(), WORKERS, |i| {
        let (n, u, x, critical) = jobs[i];
        let t = Instant::now();
        let row = sector_point(n, u, x, critical);
        eprintln!(
            "TIMING|sector_N={n}|u={}|x={}|ms={}",
            u.text(),
            x.text(),
            t.elapsed().as_millis()
        );
        row
    });
    for row in &rows {
        println!("{row}");
    }
    eprintln!("TIMING|sector_all|ms={}", start.elapsed().as_millis());
}

fn run_rotor() {
    let mut jobs: Vec<(u64, Q, Q, u64)> = Vec::new();
    let points = [
        (q(0, 1), q(0, 1)),
        (q(1, 2), q(0, 1)),
        (q(1, 1), q(-1, 4)),
        (q(0, 1), q(1, 2)),
        (q(0, 1), q(-1, 2)),
        (q(1, 2), q(1, 4)),
        (q(1, 1), q(-1, 8)),
    ];
    let mut n = 1u64;
    for power in 1..=12u32 {
        n *= 3;
        if power < 3 {
            continue;
        }
        for &(u, x) in &points {
            for charge in 1..=3u64 {
                jobs.push((n, u, x, charge));
            }
        }
    }
    let n = 19_683u64;
    for &(u, x) in &[(q(1, 2), q(0, 1)), (q(1, 1), q(-1, 4))] {
        for &charge in &[n / 9, n / 3, 2 * n / 3, n] {
            jobs.push((n, u, x, charge));
        }
    }
    let rows = parallel(jobs.len(), WORKERS, |i| {
        let (n, u, x, charge) = jobs[i];
        rotor_point(n, u, x, charge)
    });
    for row in &rows {
        println!("{row}");
    }
}

// ---- The full space, or the sector P = 0, as a sparse symmetric matrix.

struct Space {
    n: i128,
    states: Vec<(i128, i128)>,
    full: bool,
    row_start: Vec<usize>,
}

impl Space {
    fn full(n: u64) -> Self {
        let big = i128::from(n);
        let mut states = Vec::new();
        let mut row_start = Vec::new();
        for p in 0..=big {
            row_start.push(states.len());
            for m in 0..=(big - p) {
                states.push((p, m));
            }
        }
        Self {
            n: big,
            states,
            full: true,
            row_start,
        }
    }

    fn sector(n: u64) -> Self {
        let big = i128::from(n);
        let states = (0..=(big / 2)).map(|j| (j, j)).collect();
        Self {
            n: big,
            states,
            full: false,
            row_start: Vec::new(),
        }
    }

    fn index(&self, p: i128, m: i128) -> Option<usize> {
        if p < 0 || m < 0 || p + m > self.n {
            return None;
        }
        if self.full {
            Some(self.row_start[p as usize] + m as usize)
        } else if p == m {
            Some(p as usize)
        } else {
            None
        }
    }
}

#[derive(Clone, Copy)]
struct Params {
    x: Q,
    u: Q,
    y: Q,
    no_bose: bool,
}

struct Sparse {
    start: Vec<u32>,
    col: Vec<u32>,
    coef: Vec<i64>,
}

fn pair_element(p: i128, m: i128, n0: i128, big: i128, bits: u32, no_bose: bool) -> i64 {
    let bose = if no_bose { 1 } else { (p + 1) * (m + 1) };
    let (root, from) = root_bits((bose * n0 * (n0 - 1)) as u128);
    round_div(rescale(root, from, bits), big) as i64
}

fn linear_element(a: i128, b: i128, y: Q, bits: u32) -> i64 {
    let (root, from) = root_bits((a * b) as u128);
    -(round_div(rescale(root * y.n, from, bits), y.d) as i64)
}

fn build(space: &Space, par: Params, shift: u32) -> Sparse {
    let big = space.n;
    let bits = SCALE - shift;
    let mut start = Vec::with_capacity(space.states.len() + 1);
    let mut col = Vec::new();
    let mut coef = Vec::new();
    start.push(0u32);
    for &(p, m) in &space.states {
        let n0 = big - p - m;
        let sum = p + m;
        let num = par.x.n * sum * par.u.d * big + par.u.n * (n0 * sum + p * m) * par.x.d;
        let den = par.x.d * par.u.d * big;
        col.push(space.index(p, m).unwrap() as u32);
        coef.push(round_div(num << bits, den) as i64);
        if n0 >= 2 {
            col.push(space.index(p + 1, m + 1).unwrap() as u32);
            coef.push(pair_element(p, m, n0, big, bits, par.no_bose));
        }
        if p >= 1 && m >= 1 {
            col.push(space.index(p - 1, m - 1).unwrap() as u32);
            coef.push(pair_element(p - 1, m - 1, n0 + 2, big, bits, par.no_bose));
        }
        if par.y.n != 0 {
            if n0 >= 1 {
                let value = linear_element(p + 1, n0, par.y, bits);
                col.push(space.index(p + 1, m).unwrap() as u32);
                coef.push(value);
                let value = linear_element(m + 1, n0, par.y, bits);
                col.push(space.index(p, m + 1).unwrap() as u32);
                coef.push(value);
            }
            if p >= 1 {
                let value = linear_element(p, n0 + 1, par.y, bits);
                col.push(space.index(p - 1, m).unwrap() as u32);
                coef.push(value);
            }
            if m >= 1 {
                let value = linear_element(m, n0 + 1, par.y, bits);
                col.push(space.index(p, m - 1).unwrap() as u32);
                coef.push(value);
            }
        }
        start.push(col.len() as u32);
    }
    Sparse { start, col, coef }
}

impl Sparse {
    /// out[i] = (H v)[i] at the matrix's own scale, with the shift given, floor rounded.
    fn apply_into(&self, v: &[i64], out: &mut [i64], right: u32) {
        for (i, slot) in out.iter_mut().enumerate() {
            let (a, b) = (self.start[i] as usize, self.start[i + 1] as usize);
            let mut s = 0i128;
            for (c, k) in self.col[a..b].iter().zip(self.coef[a..b].iter()) {
                s += i128::from(*k) * i128::from(v[*c as usize]);
            }
            *slot = (s >> right) as i64;
        }
    }
}

// ---- Reading a state.

#[derive(Default, Clone, Copy)]
struct Reading {
    norm: i128,
    pairs: i128,
    np_nm: i128,
    n0_pairs: i128,
    re_p: i128,
    a: i128,
    b: i128,
}

/// Expectations at 2^60, divided by the norm. `v` may be all zero for a real state.
fn read(space: &Space, u: &[i64], v: &[i64]) -> Reading {
    let product = |a: usize, b: usize| -> i128 {
        (i128::from(u[a]) * i128::from(u[b]) + i128::from(v[a]) * i128::from(v[b])) >> SCALE
    };
    let mut r = Reading::default();
    let big = space.n;
    for (i, &(p, m)) in space.states.iter().enumerate() {
        let weight = product(i, i);
        r.norm += weight;
        if weight != 0 {
            r.pairs += weight * (p + m);
            r.np_nm += weight * p * m;
            r.n0_pairs += weight * (big - p - m) * (p + m);
        }
        let n0 = big - p - m;
        if n0 >= 2 {
            if let Some(t) = space.index(p + 1, m + 1) {
                let root = isqrt((((p + 1) * (m + 1) * n0 * (n0 - 1)) as u128) << 64) as i128;
                r.re_p += (product(t, i) * root) >> 32;
            }
        }
        if space.full {
            if n0 >= 1 {
                if let Some(t) = space.index(p + 1, m) {
                    let root = isqrt((((p + 1) * n0) as u128) << 64) as i128;
                    r.a += (product(t, i) * root) >> 32;
                }
                if let Some(t) = space.index(p, m + 1) {
                    let root = isqrt((((m + 1) * n0) as u128) << 64) as i128;
                    r.a += (product(t, i) * root) >> 32;
                }
            }
            if p >= 1 {
                if let Some(t) = space.index(p - 1, m + 1) {
                    let root = isqrt(((p * (m + 1)) as u128) << 64) as i128;
                    r.b += (product(t, i) * root) >> 32;
                }
            }
        }
    }
    let inverse = (1i128 << 96) / r.norm.max(1); // 2^36 / norm, with norm near 1 at 2^60
    let scale = |value: i128| -> i128 { (value * inverse) >> 36 };
    Reading {
        norm: r.norm,
        pairs: scale(r.pairs),
        np_nm: scale(r.np_nm),
        n0_pairs: scale(r.n0_pairs),
        re_p: scale(r.re_p),
        a: scale(r.a),
        b: scale(r.b),
    }
}

// ---- Lanczos.

fn dot(a: &[i64], b: &[i64]) -> i128 {
    let mut s = 0i128;
    for (x, y) in a.iter().zip(b.iter()) {
        s += i128::from(*x) * i128::from(*y);
    }
    s >> SCALE
}

fn normalize(v: &mut [i64]) -> i128 {
    let mut s = 0u128;
    for x in v.iter() {
        s += (i128::from(*x) * i128::from(*x)) as u128;
    }
    let root = isqrt(s) as i128; // at 2^60
    if root == 0 {
        return 0;
    }
    let inverse = (1i128 << 120) / root;
    for x in v.iter_mut() {
        *x = ((i128::from(*x) * inverse) >> SCALE) as i64;
    }
    root
}

fn twisted_vector(alpha: &[i64], beta: &[i64], theta: i64) -> Vec<i64> {
    let m = alpha.len();
    if m == 1 {
        return vec![1i64 << SCALE];
    }
    let b2: Vec<i128> = beta
        .iter()
        .map(|b| (i128::from(*b) * i128::from(*b)) >> SCALE)
        .collect();
    let safe = |q: i128| if q == 0 { 1 } else { q };
    let mut plus = vec![0i128; m];
    let mut minus = vec![0i128; m];
    plus[0] = i128::from(alpha[0] - theta);
    for k in 1..m {
        plus[k] = i128::from(alpha[k] - theta) - (b2[k - 1] << SCALE) / safe(plus[k - 1]);
    }
    minus[m - 1] = i128::from(alpha[m - 1] - theta);
    for k in (0..m - 1).rev() {
        minus[k] = i128::from(alpha[k] - theta) - (b2[k] << SCALE) / safe(minus[k + 1]);
    }
    let mut best = 0usize;
    let mut low = i128::MAX;
    for k in 0..m {
        let gamma = (plus[k] + minus[k] - i128::from(alpha[k] - theta)).abs();
        if gamma < low {
            low = gamma;
            best = k;
        }
    }
    let mut z = vec![0i128; m];
    z[best] = 1i128 << 56;
    for k in (0..best).rev() {
        z[k] = -(i128::from(beta[k]) * z[k + 1]) / safe(plus[k]);
    }
    for k in best + 1..m {
        z[k] = -(i128::from(beta[k - 1]) * z[k - 1]) / safe(minus[k]);
    }
    let mut out: Vec<i64> = z.iter().map(|v| *v as i64).collect();
    normalize(&mut out);
    out
}

struct Ground {
    theta: i64,
    vector: Vec<i64>,
    residual: i128,
    cycles: usize,
}

fn lanczos(op: &Sparse, start: Vec<i64>, krylov: usize, tol: i128, max_cycles: usize) -> Ground {
    let size = start.len();
    let mut x = start;
    normalize(&mut x);
    let mut w = vec![0i64; size];
    let mut theta = 0i64;
    let mut residual = i128::MAX;
    let mut cycles = 0usize;
    while cycles < max_cycles {
        cycles += 1;
        let mut basis: Vec<Vec<i64>> = vec![x.clone()];
        let (mut alpha, mut beta): (Vec<i64>, Vec<i64>) = (Vec::new(), Vec::new());
        for k in 0..krylov.min(size) {
            op.apply_into(&basis[k], &mut w, SCALE);
            if k > 0 {
                let b = i128::from(beta[k - 1]);
                for (slot, old) in w.iter_mut().zip(basis[k - 1].iter()) {
                    *slot -= ((b * i128::from(*old)) >> SCALE) as i64;
                }
            }
            let a = dot(&w, &basis[k]) as i64;
            alpha.push(a);
            for (slot, cur) in w.iter_mut().zip(basis[k].iter()) {
                *slot -= ((i128::from(a) * i128::from(*cur)) >> SCALE) as i64;
            }
            if k + 1 == krylov.min(size) {
                break;
            }
            let mut next = w.clone();
            let b = normalize(&mut next);
            if b < (1i128 << 12) {
                break;
            }
            beta.push(b as i64);
            basis.push(next);
        }
        let o2: Vec<i128> = beta
            .iter()
            .map(|b| (i128::from(*b) * i128::from(*b)) >> 30)
            .collect();
        let d = &alpha;
        theta = level(d, &o2, 0, theta, 1 << 40);
        let z = twisted_vector(&alpha, &beta, theta);
        let mut sum = vec![0i128; size];
        for (zk, vk) in z.iter().zip(basis.iter()) {
            for (s, value) in sum.iter_mut().zip(vk.iter()) {
                *s += i128::from(*zk) * i128::from(*value);
            }
        }
        for (slot, s) in x.iter_mut().zip(sum.iter()) {
            *slot = (*s >> SCALE) as i64;
        }
        normalize(&mut x);
        op.apply_into(&x, &mut w, SCALE);
        let mut r = 0u128;
        for (a, b) in w.iter().zip(x.iter()) {
            let e = i128::from(*a) - ((i128::from(theta) * i128::from(*b)) >> SCALE);
            r += (e * e) as u128;
        }
        residual = isqrt(r) as i128;
        if residual <= tol {
            break;
        }
    }
    Ground {
        theta,
        vector: x,
        residual,
        cycles,
    }
}

fn even_start(space: &Space) -> Vec<i64> {
    let mut seed = 0x504f_4c41_5249_544fu64;
    let side = space.n as usize + 1;
    let mut table = vec![0i64; side * side];
    for p in 0..side {
        for m in p..side {
            seed ^= seed << 13;
            seed ^= seed >> 7;
            seed ^= seed << 17;
            let value = (seed >> 20) as i64 - (1i64 << 43);
            table[p * side + m] = value;
            table[m * side + p] = value;
        }
    }
    space
        .states
        .iter()
        .map(|&(p, m)| table[p as usize * side + m as usize])
        .collect()
}

fn spectral_bits(n: i128, par: Params) -> u32 {
    // A bound on the norm: (|x| + |u| + 1/4 + 4|y|) N + 2.
    let num = (par.x.n.abs() * par.u.d * par.y.d * 4
        + par.u.n.abs() * par.x.d * par.y.d * 4
        + par.x.d * par.u.d * par.y.d
        + 16 * par.y.n.abs() * par.x.d * par.u.d)
        * n;
    let den = 4 * par.x.d * par.u.d * par.y.d;
    let bound = num / den + 3;
    128 - (bound as u128).leading_zeros()
}

fn pin_row(
    space: &Space,
    par: Params,
    ground: &Ground,
    bits: u32,
    y_text: &str,
    s_text: &str,
) -> String {
    let zero = vec![0i64; ground.vector.len()];
    let r = read(space, &ground.vector, &zero);
    let big = space.n;
    let energy = i128::from(ground.theta) << bits;
    let a1 = 2 * r.a.abs() / big;
    let d2 = 2 * r.b.abs() / big;
    let wk = r.n0_pairs + 2 * r.re_p;
    let (c1, c2) = if big > 1 {
        (2 * wk / (big * (big - 1)), 2 * r.np_nm / (big * (big - 1)))
    } else {
        (0, 0)
    };
    let residual_units = ((ground.residual << bits) * 1_000_000_000_000) >> SCALE;
    format!(
        "POLARITON_PIN|N={big}|u={}|x={}|y={y_text}|s={s_text}|energy_ppb={}|A_ppb={}|B_ppb={}|A1_ppm={}|D2_ppm={}|C1_ppm={}|C2_ppm={}|f_ppm={}|residual_1e-12={residual_units}|cycles={}|json=0",
        par.u.text(),
        par.x.text(),
        ppb(energy),
        ppb(r.a),
        ppb(r.b),
        ppm(a1),
        ppm(d2),
        ppm(c1),
        ppm(c2),
        ppm(r.pairs / big),
        ground.cycles
    )
}

type RowMaker = fn(&Space, Params, &Ground, u32, &str, &str) -> String;

/// A pin row with <(n+ - n-)^2>/N^2 beside it, which tells the pair state from the plane waves.
fn window_row(
    space: &Space,
    par: Params,
    ground: &Ground,
    bits: u32,
    y_text: &str,
    s_text: &str,
) -> String {
    let mut charge_squared = 0i128;
    let mut norm = 0i128;
    for (i, &(p, m)) in space.states.iter().enumerate() {
        let value = i128::from(ground.vector[i]);
        let weight = (value * value) >> SCALE;
        norm += weight;
        charge_squared += weight * (p - m) * (p - m);
    }
    let big = space.n;
    let share = (charge_squared / (big * big) * 1_000_000) / norm.max(1);
    pin_row(space, par, ground, bits, y_text, s_text)
        .replace("POLARITON_PIN|", "POLARITON_PIN_WINDOW|")
        .replace("|json=0", &format!("|P2_over_N2_ppm={share}|json=0"))
}

fn pin_chain(n: u64, u: Q, x: Q, krylov: usize) -> Vec<String> {
    pin_chain_with(n, u, x, krylov, pin_row)
}

fn pin_chain_with(n: u64, u: Q, x: Q, krylov: usize, make: RowMaker) -> Vec<String> {
    let space = Space::full(n);
    let big = i128::from(n);
    let mut rows = Vec::new();
    let mut start = even_start(&space);
    // From strong pinning down to none, each state starting the next.
    let list = [(16, 1), (8, 1), (4, 1), (2, 1), (1, 1), (1, 2), (0, 1)];
    for &(sn, sd) in &list {
        let y = Q { n: sn, d: sd * big };
        let par = Params {
            x,
            u,
            y,
            no_bose: false,
        };
        let bits = spectral_bits(big, par);
        let op = build(&space, par, bits);
        let tol = (1i128 << 30) >> bits;
        let t = Instant::now();
        let ground = if sn == 0 {
            // At zero field, start again from the generic even vector, so that nothing is assumed about the sector.
            lanczos(&op, even_start(&space), krylov, tol, 600)
        } else {
            lanczos(&op, start.clone(), krylov, tol, 600)
        };
        eprintln!(
            "TIMING|pin_N={n}|u={}|x={}|s={sn}/{sd}|cycles={}|ms={}",
            u.text(),
            x.text(),
            ground.cycles,
            t.elapsed().as_millis()
        );
        let s_text = Q { n: sn, d: sd }.text();
        rows.push(make(&space, par, &ground, bits, &y.text(), &s_text));
        start = ground.vector;
    }
    rows
}

fn run_pin() {
    let points = [
        (q(1, 2), q(0, 1)),
        (q(0, 1), q(0, 1)),
        (q(1, 2), q(1, 2)),
        (q(1, 2), q(3, 2)),
    ];
    let mut jobs: Vec<(u64, Q, Q, usize)> = Vec::new();
    for &(n, krylov) in &[(3u64, 60usize), (9, 60), (27, 120), (81, 160), (243, 200)] {
        for &(u, x) in &points {
            jobs.push((n, u, x, krylov));
        }
    }
    let rows = parallel(jobs.len(), WORKERS, |i| {
        let (n, u, x, krylov) = jobs[i];
        pin_chain(n, u, x, krylov)
    });
    for chain in &rows {
        for row in chain {
            println!("{row}");
        }
    }
    // The top rung, with fewer workers for memory.
    let top: Vec<(Q, Q)> = points.to_vec();
    let rows = parallel(top.len(), 3, |i| pin_chain(729, top[i].0, top[i].1, 240));
    for chain in &rows {
        for row in chain {
            println!("{row}");
        }
    }
    // y -> -y at N = 243, s = 4, from the generic start.
    let n = 243u64;
    let big = i128::from(n);
    let space = Space::full(n);
    for sign in [1i128, -1] {
        let y = Q {
            n: sign * 4,
            d: big,
        };
        let par = Params {
            x: q(0, 1),
            u: q(1, 2),
            y,
            no_bose: false,
        };
        let bits = spectral_bits(big, par);
        let op = build(&space, par, bits);
        let ground = lanczos(&op, even_start(&space), 200, (1i128 << 30) >> bits, 600);
        let row = pin_row(
            &space,
            par,
            &ground,
            bits,
            &y.text(),
            &q(sign * 4, 1).text(),
        );
        println!("{}", row.replace("POLARITON_PIN|", "POLARITON_SYMMETRY|"));
    }
    // The hand case, N = 2: J = 2, Delta = 1, so x = 1/4 and y = h/4.
    for &(yn, yd) in &[(0i128, 1i128), (1, 64), (-1, 64), (1, 1024)] {
        let n = 2u64;
        let space = Space::full(n);
        let y = Q { n: yn, d: yd };
        let par = Params {
            x: q(1, 4),
            u: q(0, 1),
            y,
            no_bose: false,
        };
        let bits = spectral_bits(2, par);
        let op = build(&space, par, bits);
        let ground = lanczos(&op, even_start(&space), 6, (1i128 << 20) >> bits, 200);
        println!("{}", pin_row(&space, par, &ground, bits, &y.text(), "hand"));
    }
}

/// The pinned ground state across the window: inside it, and on the plane-wave side.
fn run_window() {
    let everywhere = [
        (q(1, 4), q(-1, 4)),
        (q(1, 4), q(0, 1)),
        (q(3, 4), q(0, 1)),
        (q(3, 4), q(1, 8)),
        (q(1, 2), q(1, 4)),
        (q(1, 1), q(-1, 4)),
        (q(1, 1), q(-1, 8)),
        (q(1, 2), q(-1, 4)),
        (q(3, 4), q(-1, 8)),
    ];
    let small = [(q(1, 4), q(-1, 4)), (q(3, 4), q(0, 1)), (q(1, 1), q(-1, 4))];
    let mut jobs: Vec<(u64, Q, Q, usize)> = Vec::new();
    for &(n, krylov) in &[(3u64, 60usize), (9, 60)] {
        for &(u, x) in &small {
            jobs.push((n, u, x, krylov));
        }
    }
    for &(n, krylov) in &[(81u64, 160usize), (243, 200)] {
        for &(u, x) in &everywhere {
            jobs.push((n, u, x, krylov));
        }
    }
    let rows = parallel(jobs.len(), WORKERS, |i| {
        let (n, u, x, krylov) = jobs[i];
        pin_chain_with(n, u, x, krylov, window_row)
    });
    for chain in &rows {
        for row in chain {
            println!("{row}");
        }
    }
    let top = [
        (q(1, 4), q(-1, 4)),
        (q(3, 4), q(0, 1)),
        (q(1, 1), q(-1, 4)),
        (q(1, 2), q(-1, 4)),
    ];
    let rows = parallel(top.len(), 3, |i| {
        pin_chain_with(729, top[i].0, top[i].1, 240, window_row)
    });
    for chain in &rows {
        for row in chain {
            println!("{row}");
        }
    }
}

// ---- The quench.

fn advance(op: &Sparse, u: &mut [i64], v: &mut [i64], work: &mut [i64], steps: u64) {
    // A half kick, whole drift and kick pairs, a half kick: all integer shears.
    let half = SCALE + 1;
    op.apply_into(u, work, half);
    for (slot, k) in v.iter_mut().zip(work.iter()) {
        *slot -= *k;
    }
    for step in 0..steps {
        op.apply_into(v, work, SCALE);
        for (slot, k) in u.iter_mut().zip(work.iter()) {
            *slot += *k;
        }
        let right = if step + 1 == steps { half } else { SCALE };
        op.apply_into(u, work, right);
        for (slot, k) in v.iter_mut().zip(work.iter()) {
            *slot -= *k;
        }
    }
}

fn retreat(op: &Sparse, u: &mut [i64], v: &mut [i64], work: &mut [i64], steps: u64) {
    let half = SCALE + 1;
    for step in 0..steps {
        let right = if step == 0 { half } else { SCALE };
        op.apply_into(u, work, right);
        for (slot, k) in v.iter_mut().zip(work.iter()) {
            *slot += *k;
        }
        op.apply_into(v, work, SCALE);
        for (slot, k) in u.iter_mut().zip(work.iter()) {
            *slot -= *k;
        }
    }
    op.apply_into(u, work, half);
    for (slot, k) in v.iter_mut().zip(work.iter()) {
        *slot += *k;
    }
}

fn time_bits(n: u64) -> u32 {
    let need = if n <= 243 { 64 * n } else { 4 * n };
    64 - (need - 1).leading_zeros()
}

/// cosh and sinh of z, and cos and sin, with z at 2^40, from the series.
fn hyperbolic(z: i128) -> (i128, i128, i128, i128) {
    let one = 1i128 << 40;
    let (mut ch, mut sh, mut co, mut si) = (one, 0i128, one, 0i128);
    let mut term = one;
    for k in 1..120i128 {
        term = ((term * z) >> 40) / k;
        if term == 0 {
            break;
        }
        match k % 4 {
            1 => {
                sh += term;
                si += term;
            }
            2 => {
                ch += term;
                co -= term;
            }
            3 => {
                sh += term;
                si -= term;
            }
            _ => {
                ch += term;
                co += term;
            }
        }
    }
    (ch, sh, co, si)
}

/// The closed forms, at 2^40: jbar(t), and (cosh(gamma t) - 1)/(1 + delta) for |delta| < 1.
fn closed_forms(delta: Q, t: i128) -> (i128, i128) {
    let one = 1i128 << 40;
    let square = delta.d * delta.d - delta.n * delta.n; // 1 - delta^2, over d^2
    if square == 0 {
        return (t * t * one, 0);
    }
    let magnitude =
        isqrt(((square.unsigned_abs()) << 80) / (delta.d * delta.d).unsigned_abs()) as i128; // at 2^40
    let (ch, sh, _, si) = hyperbolic(magnitude * t);
    let inverse_square = (one * one) / ((square.abs() * one) / (delta.d * delta.d));
    if square > 0 {
        let growth = (((sh * sh) >> 40) * inverse_square) >> 40;
        let plus = ((delta.d + delta.n) * one) / delta.d;
        (growth, ((ch - one) * one) / plus)
    } else {
        ((((si * si) >> 40) * inverse_square) >> 40, 0)
    }
}

fn quench_rows(
    n: u64,
    par: Params,
    delta: Q,
    times: &[i128],
    full: bool,
    tag: &str,
) -> (Vec<String>, i128) {
    let space = if full {
        Space::full(n)
    } else {
        Space::sector(n)
    };
    let big = i128::from(n);
    let k = time_bits(n);
    let op = build(&space, par, k);
    let size = space.states.len();
    let mut u = vec![0i64; size];
    let mut v = vec![0i64; size];
    let mut work = vec![0i64; size];
    u[space.index(0, 0).unwrap()] = 1i64 << SCALE;
    let mut rows = Vec::new();
    let mut now = 0i128;
    let mut largest_f = 0i128;
    for &t in times {
        let steps = ((t - now) << k) as u64;
        advance(&op, &mut u, &mut v, &mut work, steps);
        now = t;
        let r = read(&space, &u, &v);
        let jbar = r.pairs / 2;
        let f = r.pairs / big;
        largest_f = largest_f.max(f);
        let (closed, cosh_term) = closed_forms(delta, t);
        let closed_fix = closed << 20;
        let ratio = if closed_fix != 0 {
            (jbar * 1_000_000) / closed_fix
        } else {
            0
        };
        let phase = if jbar != 0 {
            (r.re_p * 1_000_000) / (big * jbar)
        } else {
            0
        };
        let wk = r.n0_pairs + 2 * r.re_p;
        let c1 = 2 * wk / (big * (big - 1));
        let c2 = 2 * r.np_nm / (big * (big - 1));
        let predicted_c1 = {
            let top = 4 * (delta.d - delta.n) * jbar;
            top / (delta.d * big)
        };
        let energy_fix = (r.pairs * par.x.n) / par.x.d
            + ((r.n0_pairs + r.np_nm) * par.u.n) / (par.u.d * big)
            + (2 * r.re_p) / big
            - (2 * r.a * par.y.n) / par.y.d;
        let a1 = 2 * r.a.abs() / big;
        let predicted_a1 = (4 * par.y.n.abs() * (cosh_term << 20)) / par.y.d;
        rows.push(format!(
            "{tag}|N={n}|u={}|x={}|y={}|delta={}|dt=2^-{k}|t={t}|jbar_ppb={}|closed_ppb={}|ratio_ppm={ratio}|jbar_over_N_ppm={}|re_P_over_N_jbar_ppm={phase}|C1_ppm={}|predicted_C1_ppm={}|C2_ppm={}|A_ppb={}|A1_ppm={}|predicted_A1_ppm={}|energy_off_1e-9={}|norm_off_1e-9={}|json=0",
            par.u.text(),
            par.x.text(),
            par.y.text(),
            delta.text(),
            ppb(jbar),
            ppb(closed_fix),
            ppm(jbar / big),
            ppm(c1),
            ppm(predicted_c1),
            ppm(c2),
            ppb(r.a),
            ppm(a1),
            ppm(predicted_a1),
            ppb(energy_fix),
            ppb(r.norm - (1i128 << SCALE))
        ));
    }
    (rows, largest_f)
}

fn run_quench() {
    let deltas = [
        q(-2, 1),
        q(-1, 1),
        q(-1, 2),
        q(0, 1),
        q(1, 2),
        q(1, 1),
        q(2, 1),
    ];
    let times = [1i128, 2, 3, 4, 6, 8];
    let u = q(1, 1);
    let mut jobs: Vec<(u64, Q)> = Vec::new();
    for &n in &[81u64, 243, 729, 2187, 6561] {
        for &delta in &deltas {
            jobs.push((n, delta));
        }
    }
    for &delta in &[q(-1, 2), q(0, 1), q(1, 2), q(1, 1), q(2, 1)] {
        jobs.push((19_683, delta));
    }
    let rows = parallel(jobs.len(), WORKERS, |i| {
        let (n, delta) = jobs[i];
        let par = Params {
            x: add(delta, q(-u.n, u.d)),
            u,
            y: q(0, 1),
            no_bose: false,
        };
        let t = Instant::now();
        let out = quench_rows(n, par, delta, &times, false, "POLARITON_QUENCH");
        eprintln!(
            "TIMING|quench_N={n}|delta={}|ms={}",
            delta.text(),
            t.elapsed().as_millis()
        );
        out
    });
    for (chain, largest) in &rows {
        for row in chain {
            println!("{row}");
        }
        let head = chain[0].split("|t=").next().unwrap_or("").to_string();
        println!(
            "POLARITON_QUENCH_BAND|{}|largest_f_ppm={}|json=0",
            head.trim_start_matches("POLARITON_QUENCH|"),
            ppm(*largest)
        );
    }
    let same = [q(0, 1), q(1, 2)];
    let rows = parallel(same.len(), 2, |i| {
        let delta = same[i];
        let v = q(1, 2);
        let par = Params {
            x: add(delta, q(-v.n, v.d)),
            u: v,
            y: q(0, 1),
            no_bose: false,
        };
        quench_rows(
            6561,
            par,
            delta,
            &times[..4],
            false,
            "POLARITON_QUENCH_OTHER_U",
        )
        .0
    });
    for chain in &rows {
        for row in chain {
            println!("{row}");
        }
    }
}

fn run_quench_pin() {
    let times = [1i128, 2, 3];
    let mut jobs: Vec<(u64, Q, Q)> = Vec::new();
    for &n in &[243u64, 729] {
        for &delta in &[q(0, 1), q(1, 2), q(1, 1)] {
            for &y in &[q(1, 1024), q(-1, 1024), q(0, 1)] {
                jobs.push((n, delta, y));
            }
        }
    }
    let u = q(1, 1);
    let rows = parallel(jobs.len(), WORKERS, |i| {
        let (n, delta, y) = jobs[i];
        let par = Params {
            x: add(delta, q(-u.n, u.d)),
            u,
            y,
            no_bose: false,
        };
        let t = Instant::now();
        let out = quench_rows(n, par, delta, &times, true, "POLARITON_QUENCH_PIN").0;
        eprintln!(
            "TIMING|quench_pin_N={n}|delta={}|y={}|ms={}",
            delta.text(),
            y.text(),
            t.elapsed().as_millis()
        );
        out
    });
    for chain in &rows {
        for row in chain {
            println!("{row}");
        }
    }
    // At y = 0: amplitudes off the P = 0 line stay exactly 0, and the rest equal the sector engine's bytes.
    for &n in &[243u64, 729] {
        let par = Params {
            x: q(-1, 1),
            u,
            y: q(0, 1),
            no_bose: false,
        };
        let k = time_bits(n);
        let full = Space::full(n);
        let sector = Space::sector(n);
        let op_full = build(&full, par, k);
        let op_sector = build(&sector, par, k);
        let mut uf = vec![0i64; full.states.len()];
        let mut vf = vec![0i64; full.states.len()];
        let mut wf = vec![0i64; full.states.len()];
        let mut us = vec![0i64; sector.states.len()];
        let mut vs = vec![0i64; sector.states.len()];
        let mut ws = vec![0i64; sector.states.len()];
        uf[0] = 1i64 << SCALE;
        us[0] = 1i64 << SCALE;
        let steps = 3u64 << k;
        advance(&op_full, &mut uf, &mut vf, &mut wf, steps);
        advance(&op_sector, &mut us, &mut vs, &mut ws, steps);
        let (mut off_line_nonzero, mut on_line_different) = (0u64, 0u64);
        for (i, &(p, m)) in full.states.iter().enumerate() {
            if p == m {
                let j = p as usize;
                if uf[i] != us[j] || vf[i] != vs[j] {
                    on_line_different += 1;
                }
            } else if uf[i] != 0 || vf[i] != 0 {
                off_line_nonzero += 1;
            }
        }
        println!("POLARITON_SECTOR_EQUALS_FULL|N={n}|t=3|off_line_nonzero={off_line_nonzero}|on_line_different={on_line_different}|json=0");
    }
}

/// A quench with the field on, read with everything the conversion needs at 10^-9.
fn conversion_chain(
    n: u64,
    delta: Q,
    y: Q,
    s_text: &str,
    times: &[i128],
    k: u32,
    tag: &str,
) -> Vec<String> {
    let par = Params {
        x: add(delta, q(-1, 1)),
        u: q(1, 1),
        y,
        no_bose: false,
    };
    let space = Space::full(n);
    let op = build(&space, par, k);
    let size = space.states.len();
    let (mut a, mut b, mut w) = (vec![0i64; size], vec![0i64; size], vec![0i64; size]);
    a[space.index(0, 0).unwrap()] = 1i64 << SCALE;
    let mut rows = Vec::new();
    let mut now = 0i128;
    for &t in times {
        advance(&op, &mut a, &mut b, &mut w, ((t - now) << k) as u64);
        now = t;
        let r = read(&space, &a, &b);
        let big = space.n;
        let wk = r.n0_pairs + 2 * r.re_p;
        let c1 = 2 * wk / (big * (big - 1));
        let c2 = 2 * r.np_nm / (big * (big - 1));
        let energy = (r.pairs * par.x.n) / par.x.d
            + ((r.n0_pairs + r.np_nm) * par.u.n) / (par.u.d * big)
            + (2 * r.re_p) / big
            - (2 * r.a * par.y.n) / par.y.d;
        rows.push(format!(
            "{tag}|N={big}|u={}|x={}|y={}|s={s_text}|delta={}|dt=2^-{k}|t={t}|jbar_ppb={}|f_ppb={}|A_ppb={}|B_ppb={}|C1_ppb={}|C2_ppb={}|energy_off_1e-9={}|norm_off_1e-9={}|json=0",
            par.u.text(),
            par.x.text(),
            par.y.text(),
            delta.text(),
            ppb(r.pairs / 2),
            ppb(r.pairs / big),
            ppb(r.a),
            ppb(r.b),
            ppb(c1),
            ppb(c2),
            ppb(energy),
            ppb(r.norm - (1i128 << SCALE))
        ));
    }
    rows
}

fn run_conversion() {
    let fields = [(1i128, 4i128), (1, 2), (1, 1), (2, 1), (4, 1)];
    let mut jobs: Vec<(u64, Q, Q, Q, Vec<i128>)> = Vec::new();
    for &(n, root) in &[(81u64, 9i128), (243, 16), (729, 27)] {
        for &delta in &[q(0, 1), q(1, 2)] {
            for &(sn, sd) in &fields {
                let s = q(sn, sd);
                jobs.push((n, delta, q(sn, sd * root), s, vec![1, 2, 3]));
            }
        }
    }
    for &(sn, sd) in &[(1i128, 2i128), (1, 1)] {
        jobs.push((2187, q(0, 1), q(sn, sd * 47), q(sn, sd), vec![1, 2]));
    }
    let rows = parallel(jobs.len(), WORKERS, |i| {
        let (n, delta, y, s, times) = &jobs[i];
        let t = Instant::now();
        let out = conversion_chain(
            *n,
            *delta,
            *y,
            &s.text(),
            times,
            time_bits(*n),
            "POLARITON_QUENCH_CONVERSION",
        );
        eprintln!(
            "TIMING|conversion_N={n}|delta={}|y={}|ms={}",
            delta.text(),
            y.text(),
            t.elapsed().as_millis()
        );
        out
    });
    for chain in &rows {
        for row in chain {
            println!("{row}");
        }
    }
}

fn run_reversal() {
    let mut cases: Vec<(u64, bool, Q)> = vec![(243, true, q(1, 1024))];
    for &n in &[81u64, 243, 729, 2187] {
        cases.push((n, false, q(0, 1)));
    }
    let rows = parallel(cases.len(), WORKERS, |i| {
        let (n, full, y) = cases[i];
        let space = if full {
            Space::full(n)
        } else {
            Space::sector(n)
        };
        let par = Params {
            x: q(-1, 1),
            u: q(1, 1),
            y,
            no_bose: false,
        };
        let k = time_bits(n);
        let op = build(&space, par, k);
        let size = space.states.len();
        let (mut u, mut v, mut w) = (vec![0i64; size], vec![0i64; size], vec![0i64; size]);
        u[space.index(0, 0).unwrap()] = 1i64 << SCALE;
        let (u0, v0) = (u.clone(), v.clone());
        let steps = 3u64 << k;
        advance(&op, &mut u, &mut v, &mut w, steps);
        let moved = u != u0;
        retreat(&op, &mut u, &mut v, &mut w, steps);
        format!(
            "POLARITON_REVERSAL|N={n}|full={}|y={}|steps={steps}|state_moved={}|every_byte_returned={}|json=0",
            u8::from(full),
            y.text(),
            u8::from(moved),
            u8::from(u == u0 && v == v0)
        )
    });
    for row in &rows {
        println!("{row}");
    }
}

fn run_wavevector() {
    let units = [q(0, 1), q(1, 2), q(1, 1)];
    for &u in &units {
        let grid: Vec<Q> = (-40..=16).map(|i| q(i, 16)).collect();
        let values = parallel(grid.len(), WORKERS, |i| {
            let par = Params {
                x: grid[i],
                u,
                y: q(0, 1),
                no_bose: false,
            };
            let delta = add(grid[i], u);
            let (rows, _) = quench_rows(2187, par, delta, &[2], false, "ROW");
            let text = rows[0].split("|jbar_ppb=").nth(1).unwrap_or("0");
            text.split('|')
                .next()
                .unwrap_or("0")
                .parse::<i128>()
                .unwrap_or(0)
        });
        let mut best = 0usize;
        for (i, value) in values.iter().enumerate() {
            if *value > values[best] {
                best = i;
            }
        }
        println!(
            "POLARITON_WAVEVECTOR|N=2187|u={}|t=2|grid_step=1/16|argmax_x={}|predicted_x=-u|jbar_ppb_at_max={}|json=0",
            u.text(),
            grid[best].text(),
            values[best]
        );
    }
}

fn run_taylor() {
    let points: [(u64, Q, Q, Q, i128); 6] = [
        (27, q(1, 1), q(-1, 1), q(0, 1), 1),
        (27, q(1, 1), q(-1, 1), q(0, 1), 2),
        (27, q(1, 2), q(0, 1), q(0, 1), 2),
        (9, q(1, 1), q(-1, 1), q(1, 64), 1),
        (9, q(1, 1), q(-1, 1), q(1, 64), 2),
        (9, q(1, 2), q(1, 2), q(-1, 64), 2),
    ];
    for &(n, u, x, y, t) in &points {
        let space = Space::full(n);
        let par = Params {
            x,
            u,
            y,
            no_bose: false,
        };
        let k = 16u32;
        let op = build(&space, par, k);
        let size = space.states.len();
        let (mut a, mut b, mut w) = (vec![0i64; size], vec![0i64; size], vec![0i64; size]);
        a[space.index(0, 0).unwrap()] = 1i64 << SCALE;
        advance(&op, &mut a, &mut b, &mut w, (t as u64) << k);
        let r = read(&space, &a, &b);
        println!(
            "POLARITON_TAYLOR_POINT|N={n}|u={}|x={}|y={}|t={t}|jbar_ppb={}|A_ppb={}|json=0",
            u.text(),
            x.text(),
            y.text(),
            ppb(r.pairs / 2),
            ppb(r.a)
        );
    }
    // The conversion's read-out against the exact series.
    let more: [(u64, Q, Q, i128); 4] = [
        (27, q(0, 1), q(1, 5), 1),
        (27, q(0, 1), q(1, 5), 2),
        (27, q(1, 2), q(2, 5), 1),
        (9, q(0, 1), q(1, 3), 2),
    ];
    for &(n, delta, y, t) in &more {
        for row in conversion_chain(n, delta, y, "taylor", &[t], 16, "POLARITON_TAYLOR_CONVERT") {
            println!("{row}");
        }
    }
}

fn run_control() {
    // The pair element without its Bose factor, against the quench closed form.
    let u = q(1, 1);
    let delta = q(0, 1);
    let par = Params {
        x: q(-1, 1),
        u,
        y: q(0, 1),
        no_bose: true,
    };
    let (rows, _) = quench_rows(
        6561,
        par,
        delta,
        &[1, 2, 3, 4],
        false,
        "POLARITON_CONTROL_NO_BOSE",
    );
    for row in &rows {
        println!("{row}");
    }
}

fn engine_main() -> Result<(), String> {
    let args: Vec<String> = std::env::args().collect();
    let start = Instant::now();
    match args.get(1).map(String::as_str) {
        Some("sector") => run_sector(),
        Some("rotor") => run_rotor(),
        Some("pin") => run_pin(),
        Some("quench") => run_quench(),
        Some("quench_pin") => run_quench_pin(),
        Some("reversal") => run_reversal(),
        Some("wavevector") => run_wavevector(),
        Some("taylor") => run_taylor(),
        Some("control") => run_control(),
        Some("window") => run_window(),
        Some("conversion") => run_conversion(),
        Some("all") => {
            run_taylor();
            run_reversal();
            run_control();
            run_wavevector();
            run_quench();
            run_quench_pin();
            run_pin();
            run_rotor();
            run_sector();
            run_window();
            run_conversion();
        }
        _ => return Err("usage = polariton_three_mode sector | rotor | pin | quench | quench_pin | reversal | wavevector | taylor | control | window | conversion | all".into()),
    }
    eprintln!("TIMING|whole|ms={}", start.elapsed().as_millis());
    println!("POLARITON_DONE|json=0");
    Ok(())
}

fn main() {
    // tight N u_n u_d x_n x_d krylov tolbits
    let a: Vec<String> = std::env::args().collect();
    let n: u64 = a[1].parse().unwrap();
    let u = q(a[2].parse().unwrap(), a[3].parse().unwrap());
    let x = q(a[4].parse().unwrap(), a[5].parse().unwrap());
    let kr: usize = a[6].parse().unwrap();
    let tolbits: u32 = a[7].parse().unwrap();
    let space = Space::full(n);
    let big = i128::from(n);
    let y = Q { n: 0, d: big };
    let par = Params { x, u, y, no_bose: false };
    let bits = spectral_bits(big, par);
    let op = build(&space, par, bits);
    let tol = (1i128 << tolbits) >> bits;
    let g = lanczos(&op, even_start(&space), kr, tol, 1500);
    println!("{}", pin_row(&space, par, &g, bits, &y.text(), "0"));
}
