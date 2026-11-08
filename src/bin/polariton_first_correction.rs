//! polariton_first_correction: certified real-time evolution of the three-mode model on a block near |N,0,0>.
//!
//! From The-matrix-law-essentials: the three-term Chebyshev recurrence (there a Euclidean filter, here the
//! Jacobi-Anger series of exp(-iHt)), restriction near the start (`ball`), the exact symmetry sector (`symsec`),
//! and matrix-free rows (`onfly`). Integers only, Rust 1.81, clippy -D warnings, no float anywhere.
//!
//! H = x n + (u/N)[n0 n + n+ n-] + (1/N)(P + P^dag) - y S, S = a0^dag(a+ + a-) + h.c., units JN = 1.
//! Basis: states even under n+ <-> n-, labelled (q, m) with q = n+ + n-, p = q - m >= m, q <= K.
//!
//! The certificate. With P the block's projector, Q = I - P, B = Q H P and psi_P the block's evolution from a
//! start inside the block, Duhamel gives norm(psi_full(t) - psi_P(t)) <= int_0^t norm(B psi_P(s)) ds.
//! B acts only on shells K-1 and K, since the pair term raises q by 2 and the linear term by 1.
//! In a window [s, s+h], split psi_P(s) into its part on shells > K-R, of norm b, and the rest. One application of H
//! raises q by at most 2, so the rest reaches shell K-1 only through the terms of degree >= m0 = ceil((R-1)/2) of the
//! Chebyshev series, whose coefficients are bounded by rho = Sum_{m >= m0} 2 (Eh/2)^m/m! for every tau in [0, h].
//! So norm(B psi_P(s + tau)) <= norm(B)(b + rho) on the whole window, and epsilon_tail <= Sum_windows h norm(B)(b + rho).
//! The polynomial remainder, the rounding of the recurrence and of the matrix elements add to epsilon.
//! Then |<O>_full - <O>_block| <= epsilon (2 norm(O psi_P) + norm(O) epsilon) <= 2 norm(O) epsilon + norm(O) epsilon^2 at unit state norm.
//!
//! The frozen read this serves: `POLARITON_FIRST_CORRECTION` in polariton/PREDICTION.hbp, pushed before this file.
//! Reads go to stdout and are the same bytes on every machine. Elapsed time and peak memory go to stderr.
//!
//! Reads at dyadic times, for the frozen bridge times of polariton-bridge/PREDICTION.hbp (`BRIDGE_ENGINE_CHANGE`):
//! a time T = a/2^b with b <= W is the end of window T 2^W, and every term of epsilon is a sum over the windows done,
//! each window's term bounding that window alone, so the certificate at T is the same sum stopped there. An integer T
//! reads exactly as before.
//!
//! The streaming layout (`stream`, `BRIDGE_ENGINE_CHANGE` of polariton-bridge/PREDICTION.hbp for a memory-layout
//! change): the same window, computed shell by shell in sweeps of `depth` Chebyshev levels (temporal blocking). At
//! sweep position s, level j works on shell s - 2(j - 1): H moves q by at most 2, so the level below is complete up to
//! that shell + 2. Each level keeps the 5 shells it is still read on; a sweep's last two levels go back to full arrays
//! for the next sweep. A sweep runs in tiles of `tile` rows m, with a margin of levels - j rows on each side of level j
//! (H moves m by at most 1), so the rows a sweep holds at once stay few on the widest shells. Every amplitude is the
//! same integer as in `point`: each row is gathered from the same products `step` adds, in another order, and an
//! integer sum is the same in any order. So every printed field is the same, but array_bytes, which counts this
//! layout's arrays; the COST row prints it beside the `point` layout's count.
//!
//! The Q = 0 sector (`sector`, a `BRIDGE_ENGINE_CHANGE` of polariton-bridge/PREDICTION.hbp for a memory-layout change):
//! at y = 0, H keeps Q = n+ - n-, and |N,0,0> has Q = 0. In the even basis Q = p - m, so the sector is one state per
//! even shell, (q, m) = (2j, j), j = 0..=K/2, joined only by the diagonal and the pair term (2j, j) -> (2j + 2, j + 1).
//! In `point` at y = 0 every linear element is 0 and every amplitude off the sector stays exactly 0, since it only ever
//! receives products with 0. So `sector` keeps the K/2 + 1 sector amplitudes and computes each from the same products
//! `step` adds into that row. Everything `point` takes from the whole block, it takes from the whole block too, shell
//! by shell with no array of the block's size: c and E (the Gershgorin pass of `build`), the elements' rounding bound,
//! norm(B), the tail norm's 1 per state, and the terms the read adds for each state of amplitude 0. So every printed
//! field is the one `point` prints, but array_bytes, which counts this layout's arrays; the COST row prints it beside
//! the `point` layout's count. It refuses y != 0 (exit 2, no row), where Q is not conserved.
//!
//! usage: polariton_first_correction point N K DELTA Y W T[,T2,...] [sabotage=NAME]
//!        polariton_first_correction stream N K DELTA Y W T[,T2,...] [depth=D] [tile=M] [sabotage=NAME]
//!        polariton_first_correction sector N K DELTA 0 W T[,T2,...] [sabotage=NAME]
//!        polariton_first_correction bessel NUM/DEN
//!        polariton_first_correction rows N K DELTA Y
//! W: the window is 2^-W. Each T is an integer or a/2^b with b <= W, a multiple of the window. A sabotage breaks the
//! engine on purpose, and the reader must catch it. D: Chebyshev levels per sweep, at least 2 (default 8). M: rows per
//! tile, at least D (default 512).
#![forbid(unsafe_code)]
#![deny(
    clippy::float_arithmetic,
    clippy::float_cmp,
    clippy::cast_precision_loss
)]

use std::time::Instant;

/// What a negative control breaks. Every field is false on a real run.
#[derive(Clone, Default)]
struct Sabotage {
    /// Empty on a real run. Named in every row otherwise.
    name: String,
    /// The certificate takes norm(B) as 2^-20 of what it is: the off-block coupling understated.
    leak_understated: bool,
    /// The series stops at half its degree while the certificate still reports the full degree's tail.
    bessel_short: bool,
    /// Each window scales the state by 1 + 2^-32 and records nothing.
    norm_drift: bool,
    /// The even basis loses its factor 2 under the root at p = m.
    drop_even_root: bool,
    /// `sector`: c, E and the elements' rounding bound from the Q = 0 chain alone, every coupling of the Q != 0
    /// states dropped from the whole block's account.
    drop_off_sector_couplings: bool,
    /// `sector`: the chain's rows in descending shell order, while the start and the read take ascending order.
    wrong_basis_order: bool,
    /// `sector`: the y = 0 refusal lifted, so the Q = 0 chain runs at y != 0 without the linear rows into Q = 1.
    run_at_nonzero_y: bool,
}

/// The sector mode's negative controls; the sabotages of `point` and `stream` are refused there.
fn parse_sector_sabotage(name: &str) -> Sabotage {
    let mut s = Sabotage {
        name: name.to_string(),
        ..Sabotage::default()
    };
    match name {
        "drop_off_sector_couplings" => s.drop_off_sector_couplings = true,
        "wrong_basis_order" => s.wrong_basis_order = true,
        "run_at_nonzero_y" => s.run_at_nonzero_y = true,
        _ => {
            eprintln!("unknown sector sabotage {name}");
            std::process::exit(2);
        }
    }
    s
}

fn parse_sabotage(name: &str) -> Sabotage {
    let mut s = Sabotage {
        name: name.to_string(),
        ..Sabotage::default()
    };
    match name {
        "leak_understated" => s.leak_understated = true,
        "bessel_short" => s.bessel_short = true,
        "norm_drift" => s.norm_drift = true,
        "drop_even_root" => s.drop_even_root = true,
        _ => {
            eprintln!("unknown sabotage {name}");
            std::process::exit(2);
        }
    }
    s
}

const Q: u32 = 62;
const ONE: i128 = 1i128 << Q;

#[derive(Clone, Copy)]
struct Rat {
    n: i128,
    d: i128,
}

fn gcd(a: i128, b: i128) -> i128 {
    let (mut a, mut b) = (a.abs(), b.abs());
    while b != 0 {
        (a, b) = (b, a % b);
    }
    a.max(1)
}

fn rat(n: i128, d: i128) -> Rat {
    let g = gcd(n, d);
    Rat { n: n / g, d: d / g }
}

fn parse_rat(s: &str) -> Rat {
    match s.split_once('/') {
        Some((a, b)) => rat(a.parse().expect("num"), b.parse().expect("den")),
        None => rat(s.parse().expect("int"), 1),
    }
}

impl Rat {
    fn text(self) -> String {
        if self.d == 1 {
            format!("{}", self.n)
        } else {
            format!("{}/{}", self.n, self.d)
        }
    }
}

/// A read time as its count of windows, T 2^W, with T in lowest terms for the row. T must be positive and its
/// denominator must divide 2^W, so that the read falls at a window's end; anything else is refused.
fn window_time(text: &str, w: u32) -> (i128, Rat) {
    let t = parse_rat(text);
    let windows_per_unit = 1i128 << w;
    let on_grid = t.n >= 1 && t.d >= 1 && windows_per_unit % t.d == 0;
    match t.n.checked_mul(windows_per_unit / t.d.max(1)) {
        Some(windows) if on_grid => (windows, t),
        _ => {
            eprintln!("time {text} is not a positive multiple of the window 2^-{w}");
            std::process::exit(2);
        }
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

/// floor(sqrt(m) * 2^frac), with frac as large as fits up to Q, and frac.
fn root_scaled(m: u128) -> (u128, u32) {
    if m == 0 {
        return (0, Q);
    }
    let bits = 128 - m.leading_zeros();
    let frac = ((127 - bits) / 2).min(Q);
    (isqrt(m << (2 * frac)), frac)
}

/// round(2^Q mul sqrt(m) / den), and an upper bound on its error in units of 2^-Q.
fn scaled_element(m: u128, mul: u128, den: u128) -> (i64, u128) {
    if m == 0 || mul == 0 {
        return (0, 0);
    }
    let (root, frac) = root_scaled(m);
    assert!(frac <= Q, "frac");
    let num = (root * mul) << (Q - frac);
    let value = (num + den / 2) / den;
    let root_err = (mul << (Q - frac)) / den + 1;
    (i64::try_from(value).expect("element"), 1 + root_err)
}

/// sqrt(m) at 2^24, nearest, within 2^-24 of the true root.
fn root24(m: u128) -> i128 {
    let shifted = m << 48;
    let root = isqrt(shifted);
    let nearest = if root * root + root < shifted {
        root + 1
    } else {
        root
    };
    i128::try_from(nearest).expect("root")
}

/// ceil(2^20 * sqrt(m)).
fn root20_up(m: u128) -> i128 {
    i128::try_from(isqrt(m << 40) + 1).expect("root")
}

struct Block {
    n: i128,
    k: usize,
    start: Vec<usize>,
    dim: usize,
    drop_even_root: bool,
}

impl Block {
    fn new(n: i128, k: usize, drop_even_root: bool) -> Block {
        let mut start = vec![0usize; k + 4];
        for q in 0..k + 3 {
            start[q + 1] = start[q] + q / 2 + 1;
        }
        Block {
            n,
            k,
            dim: start[k + 1],
            start,
            drop_even_root,
        }
    }
    fn n0(&self, q: usize) -> i128 {
        self.n - i128::try_from(q).expect("q")
    }
}

/// The rows of H, on the raising side, before scaling, as (mul, m, den) of mul sqrt(m)/den.
#[derive(Clone, Copy)]
struct Raise {
    mul: u128,
    m: u128,
    den: u128,
}

fn pair_raise(b: &Block, q: usize, mi: usize) -> Raise {
    let p = q - mi;
    let n0 = b.n0(q);
    if n0 < 2 {
        return Raise {
            mul: 0,
            m: 0,
            den: 1,
        };
    }
    let m = u128::try_from(
        (i128::try_from(p + 1).unwrap()) * (i128::try_from(mi + 1).unwrap()) * n0 * (n0 - 1),
    )
    .expect("m");
    Raise {
        mul: 1,
        m,
        den: u128::try_from(b.n).unwrap(),
    }
}

/// a+^dag a0 from (q, m) to (q + 1, m), with the even basis' sqrt(2) when p = m.
fn a_raise(b: &Block, y: Rat, q: usize, mi: usize) -> Raise {
    let p = q - mi;
    let n0 = b.n0(q);
    if n0 < 1 || y.n == 0 {
        return Raise {
            mul: 0,
            m: 0,
            den: 1,
        };
    }
    let mut m = u128::try_from(i128::try_from(p + 1).unwrap() * n0).expect("m");
    if p == mi && !b.drop_even_root {
        m *= 2;
    }
    Raise {
        mul: u128::try_from(y.n.abs()).unwrap(),
        m,
        den: u128::try_from(y.d).unwrap(),
    }
}

/// a-^dag a0 from (q, m) to (q + 1, m + 1), when p > m, with sqrt(2) when it lands on p = m.
fn b_raise(b: &Block, y: Rat, q: usize, mi: usize) -> Raise {
    let p = q - mi;
    let n0 = b.n0(q);
    if n0 < 1 || y.n == 0 || p <= mi {
        return Raise {
            mul: 0,
            m: 0,
            den: 1,
        };
    }
    let mut m = u128::try_from(i128::try_from(mi + 1).unwrap() * n0).expect("m");
    if p == mi + 1 {
        m *= 2;
    }
    Raise {
        mul: u128::try_from(y.n.abs()).unwrap(),
        m,
        den: u128::try_from(y.d).unwrap(),
    }
}

fn raise_up20(r: Raise) -> i128 {
    if r.mul == 0 {
        return 0;
    }
    i128::try_from(u128::try_from(root20_up(r.m)).unwrap() * r.mul / r.den + 1).expect("up")
}

/// Diagonal of H as a rational (num, den), den > 0.
fn diag_rat(b: &Block, x: Rat, u: Rat, q: usize, mi: usize) -> (i128, i128) {
    let qi = i128::try_from(q).unwrap();
    let p = i128::try_from(q - mi).unwrap();
    let m = i128::try_from(mi).unwrap();
    let n0 = b.n0(q);
    let den = x.d * u.d * b.n;
    (x.n * qi * u.d * b.n + u.n * x.d * (n0 * qi + p * m), den)
}

struct Op {
    d: Vec<i64>,
    pair: Vec<i64>,
    a: Vec<i64>,
    b: Vec<i64>,
    c: i128,
    e: i128,
    elem_err_units: u128,
}

fn build(block: &Block, x: Rat, u: Rat, y: Rat) -> Op {
    let k = block.k;
    // Gershgorin at 2^20, outward, over the block.
    let mut sums = vec![0i128; block.dim];
    for q in 0..=k {
        for mi in 0..=q / 2 {
            let i = block.start[q] + mi;
            if q + 2 <= k {
                let v = raise_up20(pair_raise(block, q, mi));
                sums[i] += v;
                sums[block.start[q + 2] + mi + 1] += v;
            }
            if q < k {
                let va = raise_up20(a_raise(block, y, q, mi));
                sums[i] += va;
                sums[block.start[q + 1] + mi] += va;
                let vb = raise_up20(b_raise(block, y, q, mi));
                if vb != 0 {
                    sums[i] += vb;
                    sums[block.start[q + 1] + mi + 1] += vb;
                }
            }
        }
    }
    let (mut lo, mut hi) = (i128::MAX, i128::MIN);
    for q in 0..=k {
        for mi in 0..=q / 2 {
            let i = block.start[q] + mi;
            let (num, den) = diag_rat(block, x, u, q, mi);
            let down = (num << 20).div_euclid(den);
            lo = lo.min(down - sums[i]);
            hi = hi.max(down + 1 + sums[i]);
        }
    }
    let c = (lo + hi).div_euclid(2) >> 20;
    let half_hi = (hi - (c << 20)).max((c << 20) - lo);
    let e = (half_hi >> 20) + 2;
    let mut op = Op {
        d: vec![0; block.dim],
        pair: vec![0; block.dim],
        a: vec![0; block.dim],
        b: vec![0; block.dim],
        c,
        e,
        elem_err_units: 1,
    };
    let eu = u128::try_from(e).unwrap();
    let mut worst = 1u128;
    for q in 0..=k {
        for mi in 0..=q / 2 {
            let i = block.start[q] + mi;
            let (num, den) = diag_rat(block, x, u, q, mi);
            let shifted = num - c * den;
            op.d[i] = i64::try_from((shifted << Q).div_euclid(den * e)).expect("diag");
            if q + 2 <= k {
                let r = pair_raise(block, q, mi);
                let (v, err) = scaled_element(r.m, r.mul, r.den * eu);
                op.pair[i] = v;
                worst = worst.max(err);
            }
            if q < k {
                let r = a_raise(block, y, q, mi);
                let (v, err) = scaled_element(r.m, r.mul, r.den * eu);
                op.a[i] = if y.n > 0 { -v } else { v };
                worst = worst.max(err);
                let r = b_raise(block, y, q, mi);
                let (v, err) = scaled_element(r.m, r.mul, r.den * eu);
                op.b[i] = if y.n > 0 { -v } else { v };
                worst = worst.max(err);
            }
        }
    }
    op.elem_err_units = worst;
    op
}

/// out = 2 Htilde v - minus, floored, with the sum at 2^(2Q) carried in i128.
fn step(
    block: &Block,
    op: &Op,
    v: &[i64],
    minus: Option<&[i64]>,
    scale_two: bool,
    sum: &mut [i128],
    out: &mut [i64],
) {
    sum.fill(0);
    let k = block.k;
    for q in 0..=k {
        let s0 = block.start[q];
        let (s1, s2) = (block.start[q + 1], block.start[q + 2]);
        for mi in 0..=q / 2 {
            let i = s0 + mi;
            let vi = i128::from(v[i]);
            sum[i] += i128::from(op.d[i]) * vi;
            if q + 2 <= k {
                let t = s2 + mi + 1;
                let e = i128::from(op.pair[i]);
                sum[i] += e * i128::from(v[t]);
                sum[t] += e * vi;
            }
            if q < k {
                let t = s1 + mi;
                let e = i128::from(op.a[i]);
                sum[i] += e * i128::from(v[t]);
                sum[t] += e * vi;
                let e = i128::from(op.b[i]);
                if e != 0 {
                    let t = s1 + mi + 1;
                    sum[i] += e * i128::from(v[t]);
                    sum[t] += e * vi;
                }
            }
        }
    }
    let shift = if scale_two { Q - 1 } else { Q };
    for i in 0..block.dim {
        let w = i64::try_from(sum[i] >> shift).expect("amplitude");
        out[i] = match minus {
            Some(m) => w - m[i],
            None => w,
        };
    }
}

/// J_k(num/den) at 2^62 for k up to the first index where it and everything after falls under the unit, by Miller's recurrence in i128 with rescaling.
fn bessel(num: i128, den: i128) -> Vec<i128> {
    let z_int = usize::try_from(num / den).unwrap() + 1;
    let mut root3 = 1usize;
    while root3 * root3 * root3 < z_int {
        root3 += 1;
    }
    let top = z_int + 40 * root3 + 120;
    let mut f = vec![0i128; top + 2];
    f[top] = 1i128 << 84;
    let limit = 1i128 << 92;
    for k in (1..=top).rev() {
        let two_k = 2 * i128::try_from(k).unwrap();
        f[k - 1] = (two_k * den * f[k]) / num - f[k + 1];
        while f[k - 1].abs() > limit {
            for value in f.iter_mut().take(top + 1).skip(k - 1) {
                *value >>= 8;
            }
        }
    }
    let mut s = f[0];
    let mut k = 2;
    while k <= top {
        s += 2 * f[k];
        k += 2;
    }
    let negative = s < 0;
    let s_abs = s.unsigned_abs();
    let mut out = Vec::with_capacity(top);
    for &value in f.iter().take(top + 1) {
        // Long division, |value| * 2^70 / s, bit by bit.
        let mut rem = value.unsigned_abs();
        let mut quo = rem / s_abs;
        rem %= s_abs;
        for _ in 0..70 {
            rem <<= 1;
            quo <<= 1;
            if rem >= s_abs {
                rem -= s_abs;
                quo |= 1;
            }
        }
        let signed = i128::try_from(quo).unwrap();
        let signed = if (value < 0) != negative {
            -signed
        } else {
            signed
        };
        out.push((signed + (1 << 7)) >> 8);
    }
    while out.len() > 1 && *out.last().unwrap() == 0 {
        out.pop();
    }
    // The sum rule J_0^2 + 2 Sum J_k^2 = 1, asserted within 2^-54 + (table length) 2^-48: measured off at most 2^-51.8 over E = 1..3000 at W = 6.
    // The route holds the table itself to the exact series.
    let mut rule = (out[0] >> 8) * (out[0] >> 8);
    for value in out.iter().skip(1) {
        rule += 2 * (*value >> 8) * (*value >> 8);
    }
    assert!(
        (rule - (1i128 << 108)).abs() < (1i128 << 54) + (i128::try_from(out.len()).unwrap() << 60),
        "bessel sum rule"
    );
    out
}

/// Upper bound at 2^62 on Sum_{m >= m0} 2 (z/2)^m/m!, with z = num/den. The term is kept as mantissa * 2^exp, rounded up.
fn majorant_from(m0: usize, num: i128, den: i128) -> i128 {
    let (mut mant, mut exp) = (1i128 << 60, -60i32);
    let mut total = 0i128; // at 2^100
    let mut m = 0usize;
    loop {
        let value = if exp + 100 >= 0 {
            if exp + 100 > 60 {
                1i128 << 120
            } else {
                mant << (exp + 100)
            }
        } else if -(exp + 100) >= 100 {
            1
        } else {
            (mant >> (-(exp + 100))) + 1
        };
        if m >= m0 {
            total = (total + value).min(1i128 << 124);
        }
        let mm = i128::try_from(m + 1).unwrap();
        let shrinking = 4 * den * mm >= 2 * num * 2;
        if m >= m0 && shrinking && value < (1i128 << 30) {
            // The rest of a series with ratio at most 1/2.
            total += 2 * value;
            break;
        }
        mant = (mant * num) / (2 * den * mm) + 1;
        while mant >= (1i128 << 60) {
            mant = (mant >> 1) + 1;
            exp += 1;
        }
        while mant < (1i128 << 59) {
            mant <<= 1;
            exp -= 1;
        }
        m += 1;
        assert!(m < 2_000_000, "majorant");
    }
    ((2 * total) >> 38) + 1
}

struct Reads {
    norm: i128,
    q: i128,
    pm: i128,
    n0q: i128,
    re_p: i128,
    a: i128,
    b: i128,
    x_up: i128,
    s_up: i128,
}

fn dot_shift(re: &[i64], im: &[i64], i: usize, t: usize) -> i128 {
    (i128::from(re[i]) * i128::from(re[t]) + i128::from(im[i]) * i128::from(im[t]) + (1i128 << 53))
        >> 54
}

/// Expectations. norm, q, pm, n0q at 2^84; re_p, a, b at 2^94.
/// x_up and s_up: upper bounds at 2^32 on norm(X psi) and norm(S psi) over the full space, X = n0 n + P + P^dag.
fn read(block: &Block, re: &[i64], im: &[i64]) -> Reads {
    let k = block.k;
    let mut r = Reads {
        norm: 0,
        q: 0,
        pm: 0,
        n0q: 0,
        re_p: 0,
        a: 0,
        b: 0,
        x_up: 0,
        s_up: 0,
    };
    let (mut xd, mut xu, mut xl, mut sa, mut sb) = (0i128, 0i128, 0i128, 0i128, 0i128);
    for q in 0..=k {
        let n0 = block.n0(q);
        let qi = i128::try_from(q).unwrap();
        for mi in 0..=q / 2 {
            let i = block.start[q] + mi;
            let p = q - mi;
            let (pi, mm) = (i128::try_from(p).unwrap(), i128::try_from(mi).unwrap());
            let w = (i128::from(re[i]) * i128::from(re[i]) + i128::from(im[i]) * i128::from(im[i]))
                >> 40;
            r.norm += w;
            r.q += qi * w;
            r.pm += pi * mm * w;
            r.n0q += n0 * qi * w;
            let w64 = (w >> 20) + 1;
            xd += (n0 * qi) * (n0 * qi) * w64;
            xu += (pi + 1) * (mm + 1) * n0 * (n0 - 1).max(0) * w64;
            xl += pi * mm * (n0 + 1) * (n0 + 2) * w64;
            // S, on the even state: the raising part and the lowering part, per mode, averaged over the mirror.
            let (up, down) = if p == mi {
                ((pi + 1) * n0, pi * (n0 + 1))
            } else {
                ((pi + mm + 2) * n0 / 2 + 1, (pi + mm) * (n0 + 1) / 2 + 1)
            };
            sa += up * w64;
            sb += down * w64;
            // Pair, into the block.
            if q + 2 <= k && n0 >= 2 {
                let root = root24(u128::try_from((pi + 1) * (mm + 1) * n0 * (n0 - 1)).unwrap());
                r.re_p += root * dot_shift(re, im, i, block.start[q + 2] + mi + 1);
            }
            // Linear, into the block: the matrix of S with positive elements, so <A> = this sum.
            if q < k && n0 >= 1 {
                let mut m = u128::try_from((pi + 1) * n0).unwrap();
                if p == mi && !block.drop_even_root {
                    m *= 2;
                }
                r.a += root24(m) * dot_shift(re, im, i, block.start[q + 1] + mi);
                if p > mi {
                    let mut m = u128::try_from((mm + 1) * n0).unwrap();
                    if p == mi + 1 {
                        m *= 2;
                    }
                    r.a += root24(m) * dot_shift(re, im, i, block.start[q + 1] + mi + 1);
                }
            }
            // B + B^dag at fixed q: <B> = lateral + self/2.
            if p >= mi + 2 {
                let t = block.start[q] + mi + 1;
                let mut m = u128::try_from(pi * (mm + 1)).unwrap();
                if p == mi + 2 {
                    m *= 2;
                }
                r.b += root24(m) * dot_shift(re, im, i, t);
            }
            if p == mi + 1 {
                r.b += (pi * w) << 9; // p w at 2^84 -> (p/2) w at 2^94
            }
        }
    }
    r.x_up = i128::try_from(isqrt(u128::try_from(xd).unwrap())).unwrap()
        + i128::try_from(isqrt(u128::try_from(xu).unwrap())).unwrap()
        + i128::try_from(isqrt(u128::try_from(xl).unwrap())).unwrap()
        + 3;
    // norm(S phi) <= 2 [norm(a+^dag a0 phi) + norm(a0^dag a+ phi)], with sa, sb the squares, per mode.
    r.s_up = 2
        * (i128::try_from(isqrt(u128::try_from(sa).unwrap())).unwrap()
            + i128::try_from(isqrt(u128::try_from(sb).unwrap())).unwrap())
        + 4;
    r
}

/// norm(B) at 2^20 by the Schur test on the two top shells, outward, and the raising rows of B for the log.
fn b_norm(block: &Block, y: Rat) -> i128 {
    let k = block.k;
    let n = usize::try_from(block.n).unwrap();
    if k >= n {
        return 0;
    }
    let mut col_max = 0i128;
    let mut row = vec![0i128; block.start[k + 3] - block.start[k + 1]];
    let base = block.start[k + 1];
    let top = |q: usize, mi: usize, c: &mut i128, row: &mut Vec<i128>| {
        let mut col = 0i128;
        if q + 2 > k {
            let v = raise_up20(pair_raise(block, q, mi));
            col += v;
            row[block.start[q + 2] + mi + 1 - base] += v;
        }
        if q + 1 > k {
            let v = raise_up20(a_raise(block, y, q, mi));
            col += v;
            row[block.start[q + 1] + mi - base] += v;
            let v = raise_up20(b_raise(block, y, q, mi));
            if v != 0 {
                col += v;
                row[block.start[q + 1] + mi + 1 - base] += v;
            }
        }
        *c = (*c).max(col);
    };
    for q in k.saturating_sub(1)..=k {
        for mi in 0..=q / 2 {
            top(q, mi, &mut col_max, &mut row);
        }
    }
    let row_max = row.iter().copied().max().unwrap_or(0);
    i128::try_from(isqrt(u128::try_from(col_max * row_max).unwrap())).unwrap() + 1
}

/// norm(B psi) at 2^62, actual, at a window's start: the log.
fn leak(block: &Block, y: Rat, re: &[i64], im: &[i64]) -> i128 {
    let k = block.k;
    let n = usize::try_from(block.n).unwrap();
    if k >= n {
        return 0;
    }
    let base = block.start[k + 1];
    let size = block.start[k + 3] - base;
    let (mut rr, mut ri) = (vec![0i128; size], vec![0i128; size]);
    let linear_sign: i128 = if y.n > 0 { -1 } else { 1 };
    for q in k.saturating_sub(1)..=k {
        for mi in 0..=q / 2 {
            let i = block.start[q] + mi;
            let mut add = |t: usize, r: Raise, sign: i128| {
                if r.mul != 0 {
                    let v = sign * (root24(r.m) * i128::try_from(r.mul).unwrap())
                        / i128::try_from(r.den).unwrap();
                    rr[t - base] += (v * i128::from(re[i])) >> 34;
                    ri[t - base] += (v * i128::from(im[i])) >> 34;
                }
            };
            if q + 2 > k {
                add(block.start[q + 2] + mi + 1, pair_raise(block, q, mi), 1);
            }
            if q + 1 > k {
                add(
                    block.start[q + 1] + mi,
                    a_raise(block, y, q, mi),
                    linear_sign,
                );
                add(
                    block.start[q + 1] + mi + 1,
                    b_raise(block, y, q, mi),
                    linear_sign,
                );
            }
        }
    }
    // Each component is at 2^52, with squares summed at 2^104 and the root at 2^52, reported at 2^62.
    let mut total = 0u128;
    for (a, b) in rr.iter().zip(ri.iter()) {
        total += u128::try_from(a * a + b * b).unwrap();
    }
    i128::try_from(isqrt(total)).unwrap() << 10
}

/// Norm at 2^42, outward, of the part above shell K - R.
fn tail_norm(block: &Block, r: usize, re: &[i64], im: &[i64]) -> i128 {
    if r > block.k {
        return 1i128 << 42;
    }
    let first = block.start[block.k + 1 - r];
    let mut total = 0i128;
    for i in first..block.dim {
        let w =
            (i128::from(re[i]) * i128::from(re[i]) + i128::from(im[i]) * i128::from(im[i])) >> 40;
        total += w + 1;
    }
    i128::try_from(isqrt(u128::try_from(total).unwrap())).unwrap() + 1
}

/// The terms `read` adds for a state of amplitude 0 (w = 0, so w64 = 1), at (q, m) with p = q - m != m: xd, xu, xl, sa, sb.
fn zero_state_terms(n0: i128, q: usize, mi: usize, t: &mut [i128; 5]) {
    let qi = i128::try_from(q).unwrap();
    let (pi, mm) = (i128::try_from(q - mi).unwrap(), i128::try_from(mi).unwrap());
    t[0] += (n0 * qi) * (n0 * qi);
    t[1] += (pi + 1) * (mm + 1) * n0 * (n0 - 1).max(0);
    t[2] += pi * mm * (n0 + 1) * (n0 + 2);
    t[3] += (pi + mm + 2) * n0 / 2 + 1;
    t[4] += (pi + mm) * (n0 + 1) / 2 + 1;
}

/// `build` for the sector: the same c, E and elements' rounding bound, from the whole block shell by shell (a ring
/// of three shells' Gershgorin sums: shell q is complete once shells q - 2, q - 1 and q have raised into it), the
/// rows of the Q = 0 states (index j for (2j, j); d and pair, the linear rows reaching off the sector), and the read's
/// terms of every state off the sector. With `sector_only` (a negative control) the Q != 0 states are left out of
/// the Gershgorin discs and the elements' bound.
fn sector_build(block: &Block, x: Rat, u: Rat, y: Rat, sector_only: bool) -> (Op, [i128; 5]) {
    let k = block.k;
    let cap = k / 2 + 1;
    let skip = |q: usize, mi: usize| sector_only && q - mi != mi;
    let mut ring = [vec![0i128; cap], vec![0i128; cap], vec![0i128; cap]];
    let (mut lo, mut hi) = (i128::MAX, i128::MIN);
    for q in 0..=k {
        for mi in 0..=q / 2 {
            if skip(q, mi) {
                continue;
            }
            if q + 2 <= k {
                let v = raise_up20(pair_raise(block, q, mi));
                ring[q % 3][mi] += v;
                ring[(q + 2) % 3][mi + 1] += v;
            }
            if q < k {
                let va = raise_up20(a_raise(block, y, q, mi));
                ring[q % 3][mi] += va;
                ring[(q + 1) % 3][mi] += va;
                let vb = raise_up20(b_raise(block, y, q, mi));
                if vb != 0 {
                    ring[q % 3][mi] += vb;
                    ring[(q + 1) % 3][mi + 1] += vb;
                }
            }
        }
        for mi in 0..=q / 2 {
            if skip(q, mi) {
                continue;
            }
            let (num, den) = diag_rat(block, x, u, q, mi);
            let down = (num << 20).div_euclid(den);
            let s = ring[q % 3][mi];
            lo = lo.min(down - s);
            hi = hi.max(down + 1 + s);
        }
        ring[q % 3].fill(0);
    }
    let c = (lo + hi).div_euclid(2) >> 20;
    let half_hi = (hi - (c << 20)).max((c << 20) - lo);
    let e = (half_hi >> 20) + 2;
    let mut op = Op {
        d: vec![0; cap],
        pair: vec![0; cap],
        a: Vec::new(),
        b: Vec::new(),
        c,
        e,
        elem_err_units: 1,
    };
    let eu = u128::try_from(e).unwrap();
    let mut worst = 1u128;
    let mut off = [0i128; 5];
    for q in 0..=k {
        for mi in 0..=q / 2 {
            let on = q - mi == mi;
            if !on {
                zero_state_terms(block.n0(q), q, mi, &mut off);
            }
            if skip(q, mi) {
                continue;
            }
            if on {
                let (num, den) = diag_rat(block, x, u, q, mi);
                let shifted = num - c * den;
                op.d[mi] = i64::try_from((shifted << Q).div_euclid(den * e)).expect("diag");
            }
            if q + 2 <= k {
                let r = pair_raise(block, q, mi);
                let (v, err) = scaled_element(r.m, r.mul, r.den * eu);
                if on {
                    op.pair[mi] = v;
                }
                worst = worst.max(err);
            }
            if q < k {
                let r = a_raise(block, y, q, mi);
                worst = worst.max(scaled_element(r.m, r.mul, r.den * eu).1);
                let r = b_raise(block, y, q, mi);
                worst = worst.max(scaled_element(r.m, r.mul, r.den * eu).1);
            }
        }
    }
    op.elem_err_units = worst;
    (op, off)
}

/// `step` on the Q = 0 sector: row j gets the diagonal and the pair elements joining it to j - 1 and j + 1, the products
/// `step` adds into row (2j, j); every other product `step` adds there is an element times an amplitude 0, or a linear
/// element 0 at y = 0.
fn sector_step(
    op: &Op,
    v: &[i64],
    minus: Option<&[i64]>,
    scale_two: bool,
    sum: &mut [i128],
    out: &mut [i64],
) {
    sum.fill(0);
    let n = v.len();
    for j in 0..n {
        let vj = i128::from(v[j]);
        sum[j] += i128::from(op.d[j]) * vj;
        if j + 1 < n {
            let e = i128::from(op.pair[j]);
            sum[j] += e * i128::from(v[j + 1]);
            sum[j + 1] += e * vj;
        }
    }
    let shift = if scale_two { Q - 1 } else { Q };
    for j in 0..n {
        let w = i64::try_from(sum[j] >> shift).expect("amplitude");
        out[j] = match minus {
            Some(m) => w - m[j],
            None => w,
        };
    }
}

/// `read` of the full-block state that is 0 off the sector: the sector's terms, and `off`, the terms of the states of
/// amplitude 0. The linear and lateral dot products each pair a sector state with one off it, (0 + 2^53) >> 54 = 0, so
/// a and b stay 0.
fn sector_read(block: &Block, re: &[i64], im: &[i64], off: &[i128; 5]) -> Reads {
    let k = block.k;
    let mut r = Reads {
        norm: 0,
        q: 0,
        pm: 0,
        n0q: 0,
        re_p: 0,
        a: 0,
        b: 0,
        x_up: 0,
        s_up: 0,
    };
    let [mut xd, mut xu, mut xl, mut sa, mut sb] = *off;
    for j in 0..re.len() {
        let q = 2 * j;
        let n0 = block.n0(q);
        let qi = i128::try_from(q).unwrap();
        let pm = i128::try_from(j).unwrap();
        let w =
            (i128::from(re[j]) * i128::from(re[j]) + i128::from(im[j]) * i128::from(im[j])) >> 40;
        r.norm += w;
        r.q += qi * w;
        r.pm += pm * pm * w;
        r.n0q += n0 * qi * w;
        let w64 = (w >> 20) + 1;
        xd += (n0 * qi) * (n0 * qi) * w64;
        xu += (pm + 1) * (pm + 1) * n0 * (n0 - 1).max(0) * w64;
        xl += pm * pm * (n0 + 1) * (n0 + 2) * w64;
        sa += (pm + 1) * n0 * w64;
        sb += pm * (n0 + 1) * w64;
        if q + 2 <= k && n0 >= 2 {
            let root = root24(u128::try_from((pm + 1) * (pm + 1) * n0 * (n0 - 1)).unwrap());
            r.re_p += root * dot_shift(re, im, j, j + 1);
        }
    }
    r.x_up = i128::try_from(isqrt(u128::try_from(xd).unwrap())).unwrap()
        + i128::try_from(isqrt(u128::try_from(xu).unwrap())).unwrap()
        + i128::try_from(isqrt(u128::try_from(xl).unwrap())).unwrap()
        + 3;
    r.s_up = 2
        * (i128::try_from(isqrt(u128::try_from(sa).unwrap())).unwrap()
            + i128::try_from(isqrt(u128::try_from(sb).unwrap())).unwrap())
        + 4;
    r
}

/// `leak` of the full-block state that is 0 off the sector: of shells K - 1 and K only the even one holds a sector
/// state, and each row above the block it raises into has no other source of nonzero amplitude.
fn sector_leak(block: &Block, y: Rat, re: &[i64], im: &[i64]) -> i128 {
    let k = block.k;
    let n = usize::try_from(block.n).unwrap();
    if k >= n {
        return 0;
    }
    let base = block.start[k + 1];
    let size = block.start[k + 3] - base;
    let (mut rr, mut ri) = (vec![0i128; size], vec![0i128; size]);
    let linear_sign: i128 = if y.n > 0 { -1 } else { 1 };
    for q in k.saturating_sub(1)..=k {
        if q % 2 == 1 {
            continue;
        }
        let mi = q / 2;
        let mut add = |t: usize, r: Raise, sign: i128| {
            if r.mul != 0 {
                let v = sign * (root24(r.m) * i128::try_from(r.mul).unwrap())
                    / i128::try_from(r.den).unwrap();
                rr[t - base] += (v * i128::from(re[mi])) >> 34;
                ri[t - base] += (v * i128::from(im[mi])) >> 34;
            }
        };
        if q + 2 > k {
            add(block.start[q + 2] + mi + 1, pair_raise(block, q, mi), 1);
        }
        if q + 1 > k {
            add(
                block.start[q + 1] + mi,
                a_raise(block, y, q, mi),
                linear_sign,
            );
            add(
                block.start[q + 1] + mi + 1,
                b_raise(block, y, q, mi),
                linear_sign,
            );
        }
    }
    let mut total = 0u128;
    for (a, b) in rr.iter().zip(ri.iter()) {
        total += u128::try_from(a * a + b * b).unwrap();
    }
    i128::try_from(isqrt(total)).unwrap() << 10
}

/// `tail_norm` of the full-block state that is 0 off the sector: 1 for every state at or above shell K + 1 - R, and the
/// weights of the sector states there.
fn sector_tail_norm(block: &Block, r: usize, re: &[i64], im: &[i64]) -> i128 {
    if r > block.k {
        return 1i128 << 42;
    }
    let first_shell = block.k + 1 - r;
    let mut total = i128::try_from(block.dim - block.start[first_shell]).unwrap();
    for (j, (&a, &b)) in re.iter().zip(im.iter()).enumerate() {
        if 2 * j >= first_shell {
            total += (i128::from(a) * i128::from(a) + i128::from(b) * i128::from(b)) >> 40;
        }
    }
    i128::try_from(isqrt(u128::try_from(total).unwrap())).unwrap() + 1
}

fn e18_s60(v: i128) -> i128 {
    let whole = v >> 60;
    let frac = v - (whole << 60);
    whole * 1_000_000_000_000_000_000i128 + ((frac * 1_000_000_000_000_000_000i128) >> 60)
}

/// Peak resident memory in kB where the system tells it, from the same file on every Linux.
fn peak_rss_text() -> String {
    let Ok(status) = std::fs::read_to_string("/proc/self/status") else {
        return "CANNOT_SEE".to_string();
    };
    for line in status.lines() {
        if let Some(rest) = line.strip_prefix("VmHWM:") {
            return rest.trim().trim_end_matches("kB").trim().to_string();
        }
    }
    "CANNOT_SEE".to_string()
}

/// Which arrays a run keeps: `point`'s full vectors, the streaming sweeps of `depth` levels, or the Q = 0 sector's
/// K/2 + 1 states at y = 0.
#[derive(Clone, Copy)]
enum Layout {
    Dense,
    Stream { depth: usize, tile: usize },
    Sector,
}

/// Bytes per state of the sector layout's arrays, counted as `point` counts its 120: the rows d and pair, the state
/// (32 per state), the sum (16), the two Jacobi-Anger sums (32) and the three Chebyshev levels (24).
const SECTOR_BYTES_PER_STATE: usize = 104;

/// Shells a level keeps in the streaming layout: one written at sweep position s is read up to position s + 4.
const RING: usize = 5;

/// The operator rows a shell's gather reads: its own, and those of shells q - 1 and q - 2 that raise into it.
struct ShellRows<'a> {
    d: &'a [i64],
    pair: &'a [i64],
    a: &'a [i64],
    b: &'a [i64],
    a_below: &'a [i64],
    b_below: &'a [i64],
    pair_below: &'a [i64],
    up1: bool,
    up2: bool,
}

fn shell_rows<'a>(block: &Block, op: &'a Op, q: usize) -> ShellRows<'a> {
    let st = &block.start;
    let own = st[q]..st[q + 1];
    let below1 = if q >= 1 { st[q - 1]..st[q] } else { 0..0 };
    let below2 = if q >= 2 { st[q - 2]..st[q - 1] } else { 0..0 };
    ShellRows {
        d: &op.d[own.clone()],
        pair: &op.pair[own.clone()],
        a: &op.a[own.clone()],
        b: &op.b[own],
        a_below: &op.a[below1.clone()],
        b_below: &op.b[below1],
        pair_below: &op.pair[below2],
        up1: q < block.k,
        up2: q + 2 <= block.k,
    }
}

/// Shell q of a full-length vector; empty outside 0..=K.
fn full_shell<'a>(v: &'a [i64], block: &Block, q: Option<usize>) -> &'a [i64] {
    match q {
        Some(q) if q <= block.k => &v[block.start[q]..block.start[q + 1]],
        _ => &[],
    }
}

/// Shell q of one level's ring; empty outside 0..=K.
fn ring_shell(level: &[i64], cap: usize, k: usize, q: Option<usize>) -> &[i64] {
    match q {
        Some(q) if q <= k => {
            let at = (q % RING) * cap;
            &level[at..at + q / 2 + 1]
        }
        _ => &[],
    }
}

/// Row m of shell q of Htilde times the level below, in its general form: each element checked against the shell's
/// edges. The row is gathered: the diagonal, this row's three raising elements, and the three elements that raise
/// shells q - 1 and q - 2 into it, the same products `step` adds into the same row from both ends.
/// below: the level below on shells q - 2 ..= q + 2, indexed by m, empty outside 0..=K.
fn row_sum(rows: &ShellRows, below: &[&[i64]; 5], m: usize) -> i128 {
    let [c_m2, c_m1, c_0, c_1, c_2] = *below;
    let mut s = i128::from(rows.d[m]) * i128::from(c_0[m]);
    if rows.up2 {
        s += i128::from(rows.pair[m]) * i128::from(c_2[m + 1]);
    }
    if rows.up1 {
        s += i128::from(rows.a[m]) * i128::from(c_1[m]);
        let e = rows.b[m];
        if e != 0 {
            s += i128::from(e) * i128::from(c_1[m + 1]);
        }
    }
    if m < rows.a_below.len() {
        s += i128::from(rows.a_below[m]) * i128::from(c_m1[m]);
    }
    if m >= 1 {
        if m <= rows.b_below.len() {
            s += i128::from(rows.b_below[m - 1]) * i128::from(c_m1[m - 1]);
        }
        if m <= rows.pair_below.len() {
            s += i128::from(rows.pair_below[m - 1]) * i128::from(c_m2[m - 1]);
        }
    }
    s
}

/// floor(s 2^-shift) minus the level two below, as `step` writes an amplitude.
fn amplitude(s: i128, shift: u32, minus: Option<i64>) -> i64 {
    let w = i64::try_from(s >> shift).expect("amplitude");
    match minus {
        Some(m) => w - m,
        None => w,
    }
}

/// One Chebyshev level of one part on rows lo..hi of one shell, every row in the general form.
fn shell_level(
    rows: &ShellRows,
    below: [&[i64]; 5],
    minus: Option<&[i64]>,
    shift: u32,
    out: &mut [i64],
    span: (usize, usize),
) {
    for m in span.0..span.1 {
        out[m] = amplitude(row_sum(rows, &below, m), shift, minus.map(|mm| mm[m]));
    }
}

/// The level below cut to the lengths the inside of a shell of n rows reads: shell q - 2 has n - 1 rows, q - 1 at least
/// n - 1, q exactly n, q + 1 at least n and q + 2 n + 1, of which the inside reads the first n - 1, n - 1, n, n, n.
fn cut_inner<'a>(c: &[&'a [i64]; 5], n: usize) -> [&'a [i64]; 5] {
    [
        &c[0][..n - 1],
        &c[1][..n - 1],
        &c[2][..n],
        &c[3][..n],
        &c[4][..n],
    ]
}

/// The sums a level's own rows of a shell go into: each part's sum over the shell (indexed by m), its 64-bit
/// coefficient, and the own rows.
struct Sums<'a> {
    dest: [&'a mut [i128]; 2],
    coef: [i64; 2],
    own: (usize, usize),
}

impl Sums<'_> {
    /// Row m's terms of both parts, when m is one of the own rows.
    fn add(&mut self, m: usize, v0: i64, v1: i64) {
        if m >= self.own.0 && m < self.own.1 {
            self.dest[0][m] += (i128::from(self.coef[0]) * i128::from(v0)) >> 16;
            self.dest[1][m] += (i128::from(self.coef[1]) * i128::from(v1)) >> 16;
        }
    }
}

/// One Chebyshev level of both parts on rows lo..hi of one shell, and with `sums` the own rows' terms. Rows 0 and
/// n - 1 take the general form. Between them, on a shell with q >= 2 that is not one of the block's top two, all seven
/// elements of every row exist and the row is summed without the edge checks; the b element is then added even where
/// it is 0, which adds nothing.
fn shell_level_pair(
    rows: &ShellRows,
    below: [[&[i64]; 5]; 2],
    minus: Option<[&[i64]; 2]>,
    shift: u32,
    out: [&mut [i64]; 2],
    span: (usize, usize),
    mut sums: Option<Sums>,
) {
    let n = rows.d.len();
    let (lo, hi) = span;
    let [out0, out1] = out;
    let inner = rows.up1 && rows.up2 && !rows.pair_below.is_empty();
    let (f_lo, f_hi) = if inner {
        let f_lo = lo.max(1).min(hi);
        (f_lo, hi.min(n - 1).max(f_lo))
    } else {
        (hi, hi)
    };
    for m in (lo..f_lo).chain(f_hi..hi) {
        let v0 = amplitude(row_sum(rows, &below[0], m), shift, minus.map(|mm| mm[0][m]));
        let v1 = amplitude(row_sum(rows, &below[1], m), shift, minus.map(|mm| mm[1][m]));
        out0[m] = v0;
        out1[m] = v1;
        if let Some(s) = sums.as_mut() {
            s.add(m, v0, v1);
        }
    }
    if f_lo >= f_hi {
        return;
    }
    let (d, pair, a, b) = (&rows.d[..n], &rows.pair[..n], &rows.a[..n], &rows.b[..n]);
    let (a_below, b_below, pair_below) = (
        &rows.a_below[..n - 1],
        &rows.b_below[..n - 1],
        &rows.pair_below[..n - 1],
    );
    let [x_m2, x_m1, x_0, x_1, x_2] = cut_inner(&below[0], n);
    let [z_m2, z_m1, z_0, z_1, z_2] = cut_inner(&below[1], n);
    let (minus0, minus1) = match minus {
        Some([m0, m1]) => (&m0[..n], &m1[..n]),
        None => (&[][..], &[][..]),
    };
    let (out0, out1) = (&mut out0[..n], &mut out1[..n]);
    for m in f_lo..f_hi {
        let (e_d, e_p, e_a, e_b) = (
            i128::from(d[m]),
            i128::from(pair[m]),
            i128::from(a[m]),
            i128::from(b[m]),
        );
        let (e_a1, e_b1, e_p2) = (
            i128::from(a_below[m]),
            i128::from(b_below[m - 1]),
            i128::from(pair_below[m - 1]),
        );
        let s0 = e_d * i128::from(x_0[m])
            + e_p * i128::from(x_2[m + 1])
            + e_a * i128::from(x_1[m])
            + e_b * i128::from(x_1[m + 1])
            + e_a1 * i128::from(x_m1[m])
            + e_b1 * i128::from(x_m1[m - 1])
            + e_p2 * i128::from(x_m2[m - 1]);
        let s1 = e_d * i128::from(z_0[m])
            + e_p * i128::from(z_2[m + 1])
            + e_a * i128::from(z_1[m])
            + e_b * i128::from(z_1[m + 1])
            + e_a1 * i128::from(z_m1[m])
            + e_b1 * i128::from(z_m1[m - 1])
            + e_p2 * i128::from(z_m2[m - 1]);
        let (w0, w1) = (
            i64::try_from(s0 >> shift).expect("amplitude"),
            i64::try_from(s1 >> shift).expect("amplitude"),
        );
        let (v0, v1) = if minus0.is_empty() {
            (w0, w1)
        } else {
            (w0 - minus0[m], w1 - minus1[m])
        };
        out0[m] = v0;
        out1[m] = v1;
        if let Some(s) = sums.as_mut() {
            s.add(m, v0, v1);
        }
    }
}

/// The Jacobi-Anger term kk of part 0 (Re) or 1 (Im) as `point` adds it: (into Re, sign a), or None when a = 0.
fn term(table: &[i128], kk: usize, part: usize) -> Option<(bool, i128)> {
    let a = if kk < table.len() {
        table[kk] * if kk == 0 { 1 } else { 2 }
    } else {
        0
    };
    if a == 0 {
        return None;
    }
    let (dest_is_re, sign) = match (kk + part * 3) % 4 {
        0 => (true, 1i128),
        1 => (false, -1i128),
        2 => (true, -1i128),
        _ => (false, 1i128),
    };
    Some((dest_is_re, sign * a))
}

/// acc += (coef v) >> 16 term by term. The product is exact either way: one 64 x 64 multiply when coef fits in 64
/// bits, as every term's does, else the 128-bit product `point` takes.
fn accumulate(acc: &mut [i128], coef: i128, v: &[i64]) {
    match i64::try_from(coef) {
        Ok(small) => {
            let c = i128::from(small);
            for (t, &x) in acc.iter_mut().zip(v) {
                *t += (c * i128::from(x)) >> 16;
            }
        }
        Err(_) => {
            for (t, &x) in acc.iter_mut().zip(v) {
                *t += (coef * i128::from(x)) >> 16;
            }
        }
    }
}

/// What a sweep reads besides the state: the block, the operator and the Bessel table.
struct Ctx<'a> {
    block: &'a Block,
    op: &'a Op,
    table: &'a [i128],
}

/// The streaming layout's sizes: levels per sweep, rows per tile, and rows of the widest shell.
#[derive(Clone, Copy)]
struct Geom {
    depth: usize,
    tile: usize,
    cap: usize,
}

/// One sweep of a window: Chebyshev levels l0 + 1 ..= l0 + levels; `last` when it ends the window.
#[derive(Clone, Copy)]
struct Pass {
    l0: usize,
    levels: usize,
    last: bool,
}

/// Where a sweep is: level j (Chebyshev level kk = l0 + j) on shell q, in the tile of rows m0..m1, computing rows
/// lo..hi: the tile's rows and, below the sweep's top level, a margin of levels - j rows on each side, which the
/// levels above read.
#[derive(Clone, Copy)]
struct At {
    q: usize,
    j: usize,
    kk: usize,
    pass: Pass,
    tile: (usize, usize),
    span: (usize, usize),
}

impl At {
    /// The rows this level adds into the sums and hands to the next sweep: the tile's own.
    fn own(self) -> (usize, usize) {
        let lo = self.span.0.max(self.tile.0).min(self.span.1);
        (lo, self.span.1.min(self.tile.1).max(lo))
    }

    /// The array this level is handed on in, when the sweep is not the window's last: prev (0) for its second-to-last
    /// level, cur (1) for its last.
    fn hand_on(self) -> Option<usize> {
        if self.pass.last || self.j + 2 <= self.pass.levels {
            None
        } else {
            Some(usize::from(self.j == self.pass.levels))
        }
    }
}

/// The level below on shells q - 2 ..= q + 2, and the level two below on shell q (None for level 1 of a window):
/// `cur` for level l0, `prev` for level l0 - 1, the rings (`lower`, levels 1 .. j - 1 of this sweep) for the rest.
fn level_inputs<'a>(
    block: &Block,
    at: At,
    cur: &'a [i64],
    prev: &'a [i64],
    lower: &'a [i64],
) -> ([&'a [i64]; 5], Option<&'a [i64]>) {
    let (k, q, j) = (block.k, at.q, at.j);
    let cap = k / 2 + 1;
    let len = RING * cap;
    let shells = [
        q.checked_sub(2),
        q.checked_sub(1),
        Some(q),
        Some(q + 1),
        Some(q + 2),
    ];
    let below = if j == 1 {
        shells.map(|s| full_shell(cur, block, s))
    } else {
        let level = &lower[(j - 2) * len..(j - 1) * len];
        shells.map(|s| ring_shell(level, cap, k, s))
    };
    let minus = if at.kk == 1 {
        None
    } else if j == 1 {
        Some(full_shell(prev, block, Some(q)))
    } else if j == 2 {
        Some(full_shell(cur, block, Some(q)))
    } else {
        let level = &lower[(j - 3) * len..(j - 2) * len];
        Some(ring_shell(level, cap, k, Some(q)))
    };
    (below, minus)
}

/// Where shell q's strip rows of (part, array: 0 prev, 1 cur) start in a strip buffer.
fn strip_at(g: Geom, q: usize, part: usize, array: usize) -> usize {
    ((q * 2 + part) * 2 + array) * g.depth
}

/// A level's own rows of shell q into the next sweep's input `dest` (prev or cur of one part). Unless the tile is the
/// last, the next tile's margin rows of `dest`, m1 - levels .. m1, first go to the strip that tile will read.
fn hand_on(
    g: Geom,
    block: &Block,
    at: At,
    strips: &mut [Vec<i64>; 2],
    dest: &mut [i64],
    key: (usize, usize),
    own: &[i64],
) {
    let (part, array) = key;
    let base = block.start[at.q];
    let m1 = at.tile.1;
    if m1 < g.cap {
        let (from, end) = (m1 - at.pass.levels, m1.min(at.q / 2 + 1));
        if from < end {
            let s = strip_at(g, at.q, part, array);
            strips[(at.tile.0 / g.tile) % 2][s..s + end - from]
                .copy_from_slice(&dest[base + from..base + end]);
        }
    }
    let (lo, hi) = at.own();
    dest[base + lo..base + hi].copy_from_slice(own);
}

/// The streaming layout's arrays: per part (0: Re, 1: Im) a ring of 5 shells for each level of a sweep, the level
/// before a sweep's input (`prev`, kept only when a window takes more than one sweep), and the window's sums.
/// A sweep runs tile by tile in m, `tile` rows wide. Below its top level a sweep computes, on each side of the tile, a
/// margin of one row more per level down, so a level's rows are always complete from the level below: H moves m by at
/// most 1. When a sweep writes the next one's input, a tile overwrites rows the next tile still reads in its margin;
/// it keeps their old values (`strips`: `depth` rows of each shell, of prev and of cur, per part), and the next tile
/// swaps them back in place while it runs and out again after.
struct Stream {
    geom: Geom,
    ring: [Vec<i64>; 2],
    prev: [Vec<i64>; 2],
    acc_re: Vec<i128>,
    acc_im: Vec<i128>,
    strips: [Vec<i64>; 2],
}

impl Stream {
    fn new(block: &Block, depth: usize, tile: usize, run_degree: usize) -> Stream {
        assert!(depth >= 2 && tile >= depth, "depth and tile");
        let cap = block.k / 2 + 1;
        let ring = depth.min(run_degree) * RING * cap;
        let more_sweeps = depth < run_degree;
        let prev = if more_sweeps { block.dim } else { 0 };
        let strip = if more_sweeps && tile < cap {
            4 * (block.k + 1) * depth
        } else {
            0
        };
        Stream {
            geom: Geom { depth, tile, cap },
            ring: [vec![0; ring], vec![0; ring]],
            prev: [vec![0; prev], vec![0; prev]],
            acc_re: vec![0; block.dim],
            acc_im: vec![0; block.dim],
            strips: [vec![0; strip], vec![0; strip]],
        }
    }

    /// Bytes of the arrays a run holds, counted as `point` counts its 120 per state: the operator's four rows and
    /// the state (48 per state), then this layout's sums, `prev`, rings and strips.
    fn array_bytes(&self, dim: usize) -> usize {
        dim * 48
            + (self.acc_re.len() + self.acc_im.len()) * 16
            + (self.prev[0].len() + self.prev[1].len()) * 8
            + (self.ring[0].len() + self.ring[1].len()) * 8
            + (self.strips[0].len() + self.strips[1].len()) * 8
    }

    /// One window, exp(-i E h Htilde) on Re and Im, written back into `re` and `im` as `point` writes it.
    /// Returns the applications of Htilde `point` counts: one per level for each part whose source is not zero.
    fn window(
        &mut self,
        ctx: &Ctx,
        run_degree: usize,
        re: &mut [i64],
        im: &mut [i64],
        norm_drift: bool,
    ) -> u64 {
        let active = [re.iter().any(|&v| v != 0), im.iter().any(|&v| v != 0)];
        self.acc_re.fill(0);
        self.acc_im.fill(0);
        let g = self.geom;
        let mut l0 = 0;
        loop {
            let levels = g.depth.min(run_degree - l0);
            let pass = Pass {
                l0,
                levels,
                last: l0 + levels == run_degree,
            };
            let mut cur = [&mut *re, &mut *im];
            let mut m0 = 0;
            while m0 < g.cap {
                let m1 = (m0 + g.tile).min(g.cap);
                // The strip the tile before filled.
                let strip = (m0 / g.tile + 1) % 2;
                let swap = !pass.last && m0 > 0;
                if swap {
                    self.swap_margin(ctx.block, &mut cur, m0, levels, strip);
                }
                self.sweep(ctx, pass, &mut cur, active, (m0, m1));
                if swap {
                    self.swap_margin(ctx.block, &mut cur, m0, levels, strip);
                }
                m0 = m1;
            }
            l0 += levels;
            if pass.last {
                break;
            }
        }
        for i in 0..ctx.block.dim {
            re[i] = i64::try_from(self.acc_re[i] >> (Q - 16)).expect("re");
            im[i] = i64::try_from(self.acc_im[i] >> (Q - 16)).expect("im");
            if norm_drift {
                re[i] += re[i] >> 32;
                im[i] += im[i] >> 32;
            }
        }
        (u64::from(active[0]) + u64::from(active[1])) * u64::try_from(run_degree).unwrap()
    }

    /// Rows m0 - levels .. m0 of every shell, in prev and cur of both parts, swapped with the strip the tile before
    /// kept: before a tile, its margin gets the values the sweep started from back; after it, the new ones.
    fn swap_margin(
        &mut self,
        block: &Block,
        cur: &mut [&mut [i64]; 2],
        m0: usize,
        levels: usize,
        strip: usize,
    ) {
        let g = self.geom;
        let from = m0 - levels;
        for q in 0..=block.k {
            let end = m0.min(q / 2 + 1);
            if end <= from {
                continue;
            }
            let base = block.start[q];
            for (part, state) in cur.iter_mut().enumerate() {
                let s = strip_at(g, q, part, 0);
                self.prev[part][base + from..base + end]
                    .swap_with_slice(&mut self.strips[strip][s..s + end - from]);
                let s = strip_at(g, q, part, 1);
                state[base + from..base + end]
                    .swap_with_slice(&mut self.strips[strip][s..s + end - from]);
            }
        }
    }

    /// The levels of one pass on the tile's rows m0..m1, shell by shell, from `prev` (level l0 - 1) and `cur` (level
    /// l0: the state itself in a window's first sweep). At sweep position s level j works on shell s - 2(j - 1).
    fn sweep(
        &mut self,
        ctx: &Ctx,
        pass: Pass,
        cur: &mut [&mut [i64]; 2],
        active: [bool; 2],
        tile: (usize, usize),
    ) {
        let k = ctx.block.k;
        let end = k + 2 * pass.levels.saturating_sub(1);
        // No shell below this one has a row inside the tile's widest margin.
        let first = 2 * tile.0.saturating_sub(pass.levels);
        for s in first..=end {
            if pass.l0 == 0 && s <= k {
                // Level 0, the state itself, into the sums: the tile's own rows.
                let n = s / 2 + 1;
                let base = ctx.block.start[s];
                let r = base + tile.0.min(n)..base + tile.1.min(n);
                for part in 0..2 {
                    if !active[part] {
                        continue;
                    }
                    if let Some((into_re, coef)) = term(ctx.table, 0, part) {
                        let acc = if into_re {
                            &mut self.acc_re[r.clone()]
                        } else {
                            &mut self.acc_im[r.clone()]
                        };
                        accumulate(acc, coef, &cur[part][r.clone()]);
                    }
                }
            }
            for j in 1..=pass.levels {
                let back = 2 * (j - 1);
                if s < back || s - back > k {
                    continue;
                }
                let q = s - back;
                let n = q / 2 + 1;
                let margin = pass.levels - j;
                let span = (
                    tile.0.saturating_sub(margin).min(n),
                    (tile.1 + margin).min(n),
                );
                if span.0 >= span.1 {
                    continue;
                }
                let at = At {
                    q,
                    j,
                    kk: pass.l0 + j,
                    pass,
                    tile,
                    span,
                };
                if active == [true, true] {
                    self.level_pair(ctx, at, cur);
                } else {
                    for (part, &on) in active.iter().enumerate() {
                        if on {
                            self.level_one(ctx, at, part, cur);
                        }
                    }
                }
            }
        }
    }

    /// A level of one part on one shell, its terms, and its hand-on to the next sweep when it is one of the last two.
    fn level_one(&mut self, ctx: &Ctx, at: At, part: usize, cur: &mut [&mut [i64]; 2]) {
        let block = ctx.block;
        let g = self.geom;
        let base = block.start[at.q];
        let rows = shell_rows(block, ctx.op, at.q);
        let (lower, upper) = self.ring[part].split_at_mut((at.j - 1) * RING * g.cap);
        let slot = (at.q % RING) * g.cap;
        let out = &mut upper[slot..slot + at.q / 2 + 1];
        let (below, minus) = level_inputs(block, at, cur[part], &self.prev[part], lower);
        shell_level(&rows, below, minus, shift_of(at.kk), out, at.span);
        let (lo, hi) = at.own();
        if let Some((into_re, coef)) = term(ctx.table, at.kk, part) {
            let acc = if into_re {
                &mut self.acc_re[base + lo..base + hi]
            } else {
                &mut self.acc_im[base + lo..base + hi]
            };
            accumulate(acc, coef, &out[lo..hi]);
        }
        if let Some(array) = at.hand_on() {
            let dest: &mut [i64] = if array == 1 {
                &mut *cur[part]
            } else {
                &mut self.prev[part]
            };
            hand_on(
                g,
                block,
                at,
                &mut self.strips,
                dest,
                (part, array),
                &out[lo..hi],
            );
        }
    }

    /// A level of both parts on one shell, as `level_one` twice, in one pass over the shell's rows.
    fn level_pair(&mut self, ctx: &Ctx, at: At, cur: &mut [&mut [i64]; 2]) {
        let block = ctx.block;
        let g = self.geom;
        let base = block.start[at.q];
        let n = at.q / 2 + 1;
        let rows = shell_rows(block, ctx.op, at.q);
        let split = (at.j - 1) * RING * g.cap;
        let slot = (at.q % RING) * g.cap;
        let [ring0, ring1] = &mut self.ring;
        let (lower0, upper0) = ring0.split_at_mut(split);
        let (lower1, upper1) = ring1.split_at_mut(split);
        let out0 = &mut upper0[slot..slot + n];
        let out1 = &mut upper1[slot..slot + n];
        let (below0, minus0) = level_inputs(block, at, cur[0], &self.prev[0], lower0);
        let (below1, minus1) = level_inputs(block, at, cur[1], &self.prev[1], lower1);
        let minus = match (minus0, minus1) {
            (Some(m0), Some(m1)) => Some([m0, m1]),
            _ => None,
        };
        let (lo, hi) = at.own();
        let terms = [term(ctx.table, at.kk, 0), term(ctx.table, at.kk, 1)];
        // Both terms exist or neither (a depends on kk alone), and they go into different sums.
        let fused = match terms {
            [Some((part0_re, c0)), Some((_, c1))] => match (i64::try_from(c0), i64::try_from(c1)) {
                (Ok(c0), Ok(c1)) => Some((part0_re, [c0, c1])),
                _ => None,
            },
            _ => None,
        };
        let sums = fused.map(|(part0_re, coef)| {
            let (sum_re, sum_im) = (
                &mut self.acc_re[base..base + n],
                &mut self.acc_im[base..base + n],
            );
            Sums {
                dest: if part0_re {
                    [sum_re, sum_im]
                } else {
                    [sum_im, sum_re]
                },
                coef,
                own: (lo, hi),
            }
        });
        shell_level_pair(
            &rows,
            [below0, below1],
            minus,
            shift_of(at.kk),
            [&mut *out0, &mut *out1],
            at.span,
            sums,
        );
        for (part, out) in [(0, &*out0), (1, &*out1)] {
            if let (None, Some((into_re, coef))) = (fused, terms[part]) {
                // A coefficient wider than 64 bits (none is): the 128-bit product, part by part.
                let acc = if into_re {
                    &mut self.acc_re[base + lo..base + hi]
                } else {
                    &mut self.acc_im[base + lo..base + hi]
                };
                accumulate(acc, coef, &out[lo..hi]);
            }
            if let Some(array) = at.hand_on() {
                let dest: &mut [i64] = if array == 1 {
                    &mut *cur[part]
                } else {
                    &mut self.prev[part]
                };
                hand_on(
                    g,
                    block,
                    at,
                    &mut self.strips,
                    dest,
                    (part, array),
                    &out[lo..hi],
                );
            }
        }
    }
}

/// The shift `step` takes: T_1 = Htilde T_0 at 2^-Q, every later level 2 Htilde T at 2^-(Q - 1).
fn shift_of(kk: usize) -> u32 {
    if kk == 1 {
        Q
    } else {
        Q - 1
    }
}

/// `times`: (window count T 2^W, T), sorted by the count.
#[allow(clippy::too_many_arguments)]
fn point(
    n: i128,
    k_in: usize,
    delta: Rat,
    y: Rat,
    times: &[(i128, Rat)],
    w: u32,
    sab: &Sabotage,
    layout: Layout,
) {
    let began = Instant::now();
    let k = k_in.min(usize::try_from(n).unwrap());
    let block = Block::new(n, k, sab.drop_even_root);
    let u = rat(1, 1);
    let x = rat(delta.n - delta.d, delta.d);
    let sector = matches!(layout, Layout::Sector);
    let (op, off) = if sector {
        let (mut op, off) = sector_build(&block, x, u, y, sab.drop_off_sector_couplings);
        if sab.wrong_basis_order {
            let links = op.pair.len() - 1;
            op.d.reverse();
            op.pair[..links].reverse();
        }
        (op, off)
    } else {
        (build(&block, x, u, y), [0i128; 5])
    };
    let window_den = 1i128 << w;
    let table = bessel(op.e, window_den);
    let mut majorant_m = 1usize;
    while majorant_from(majorant_m, op.e, window_den) > (1i128 << 3) {
        majorant_m += 1;
    }
    let degree = majorant_m.min(table.len().max(2) + 40);
    let rho = majorant_from(degree, op.e, window_den);
    let reach = 2 * degree + 1;
    let bnorm = if sab.leak_understated {
        b_norm(&block, y) >> 20
    } else {
        b_norm(&block, y)
    };
    let run_degree = if sab.bessel_short { degree / 2 } else { degree };
    // Rounding, per window: Sum_k |a_k| k(k+1)/2 sqrt(dim) units, doubled for Re and Im, plus the elements' error z * rows * units, plus the final rounding.
    let dim_root = i128::try_from(isqrt(u128::try_from(block.dim).unwrap())).unwrap() + 1;
    let mut weight = 0i128;
    for (j, value) in table.iter().enumerate().take(degree + 1) {
        let c = if j == 0 { 1 } else { 2 };
        let jj = i128::try_from(j).unwrap();
        weight += ((c * value.abs()) >> 40) * (jj * (jj + 1) / 2 + 1) + 1;
    }
    // weight at 2^22; the recurrence's error in units of 2^-62.
    let degree_i = i128::try_from(degree).unwrap();
    let per_window_units = ((weight >> 22) + 1) * dim_root * 2 * 2
        + dim_root * 4
        + ((op.e >> w) + 1) * 8 * i128::try_from(op.elem_err_units).unwrap()
        + (degree_i + 1) * 2 * 2 * 4;

    // The amplitudes a run holds: the whole block's, or the sector's K/2 + 1.
    let states = if sector { op.d.len() } else { block.dim };
    let (mut re, mut im) = (vec![0i64; states], vec![0i64; states]);
    re[0] = i64::try_from(ONE).unwrap();
    // The point layout's work vectors; the streaming layout keeps its own arrays and leaves these empty.
    let dense = match layout {
        Layout::Dense => block.dim,
        Layout::Stream { .. } => 0,
        Layout::Sector => states,
    };
    let mut sum = vec![0i128; dense];
    let (mut acc_re, mut acc_im) = (vec![0i128; dense], vec![0i128; dense]);
    let (mut p0, mut p1, mut p2) = (vec![0i64; dense], vec![0i64; dense], vec![0i64; dense]);
    let mut stream = match layout {
        Layout::Stream { depth, tile } => Some(Stream::new(&block, depth, tile, run_degree)),
        Layout::Dense => None,
        Layout::Sector => None,
    };
    let ctx = Ctx {
        block: &block,
        op: &op,
        table: &table,
    };
    let mut eps_tail = 0i128; // at 2^62, outward
    let mut eps_poly = 0i128;
    let mut eps_round = 0i128;
    let mut leak_max = 0i128;
    let mut leak_sum = 0i128;
    let mut tail_max = 0i128;
    let mut applies = 0u64;
    let mut done = 0i128;
    let total_windows = times.iter().map(|&(windows, _)| windows).max().unwrap();
    let mut next_read = 0usize;
    // One Chebyshev level: `step` on the whole block, or on the sector.
    let apply = |v: &[i64], minus: Option<&[i64]>, two: bool, sum: &mut [i128], out: &mut [i64]| {
        if sector {
            sector_step(&op, v, minus, two, sum, out);
        } else {
            step(&block, &op, v, minus, two, sum, out);
        }
    };
    while done < total_windows {
        // The certificate over the window that starts here.
        let tail = if sector {
            sector_tail_norm(&block, reach, &re, &im)
        } else {
            tail_norm(&block, reach, &re, &im)
        }; // at 2^42
        tail_max = tail_max.max(tail);
        let lk = if sector {
            sector_leak(&block, y, &re, &im)
        } else {
            leak(&block, y, &re, &im)
        };
        leak_max = leak_max.max(lk);
        leak_sum += (lk >> w) + 1;
        // h norm(B) (b + rho): norm(B) at 2^20, b at 2^42 -> 2^62, rho at 2^62.
        // The tail is read on the computed state, which sits within eps_round + eps_poly of the block's exact one.
        let bound =
            ((bnorm * tail) >> w) + (((bnorm * (rho + eps_round + eps_poly)) >> 20) >> w) + 1;
        eps_tail += if bnorm == 0 { 0 } else { bound };
        eps_poly += rho;
        eps_round += per_window_units;
        // The window: exp(-i E h Htilde) on Re and on Im.
        if let Some(st) = stream.as_mut() {
            applies += st.window(&ctx, run_degree, &mut re, &mut im, sab.norm_drift);
        } else {
            acc_re.fill(0);
            acc_im.fill(0);
            for part in 0..2 {
                let source: &[i64] = if part == 0 { &re } else { &im };
                if source.iter().all(|&v| v == 0) {
                    continue;
                }
                p0.copy_from_slice(source);
                for kk in 0..=run_degree {
                    let a = if kk < table.len() {
                        table[kk] * if kk == 0 { 1 } else { 2 }
                    } else {
                        0
                    };
                    let phase = (kk + part * 3) % 4; // part 1 multiplies by i = (-i)^3
                    if a != 0 {
                        let (dest_is_re, sign) = match phase {
                            0 => (true, 1i128),
                            1 => (false, -1i128),
                            2 => (true, -1i128),
                            _ => (false, 1i128),
                        };
                        let cur: &[i64] = if kk == 0 { &p0 } else { &p1 };
                        let target = if dest_is_re { &mut acc_re } else { &mut acc_im };
                        for (t, &v) in target.iter_mut().zip(cur.iter()) {
                            *t += (sign * a * i128::from(v)) >> 16;
                        }
                    }
                    if kk == run_degree {
                        break;
                    }
                    if kk == 0 {
                        apply(&p0, None, false, &mut sum, &mut p1);
                    } else {
                        apply(&p1, Some(&p0), true, &mut sum, &mut p2);
                        std::mem::swap(&mut p0, &mut p1);
                        std::mem::swap(&mut p1, &mut p2);
                    }
                    applies += 1;
                }
            }
            for i in 0..states {
                re[i] = i64::try_from(acc_re[i] >> (Q - 16)).expect("re");
                im[i] = i64::try_from(acc_im[i] >> (Q - 16)).expect("im");
                if sab.norm_drift {
                    re[i] += re[i] >> 32;
                    im[i] += im[i] >> 32;
                }
            }
        }
        done += 1;
        while next_read < times.len() && times[next_read].0 == done {
            let r = if sector {
                sector_read(&block, &re, &im, &off)
            } else {
                read(&block, &re, &im)
            };
            let big = block.n;
            let nn = big * (big - 1);
            // Observables at 2^60.
            let x_s84 = r.n0q + 2 * (r.re_p >> 10);
            let c1 = (2 * x_s84 / nn) >> 24;
            let c2 = (2 * r.pm / nn) >> 24;
            let f = (r.q / big) >> 24;
            let jbar = r.q >> 25;
            let a_s60 = r.a >> 34;
            let a1 = (2 * r.a.abs() / big) >> 34;
            let b_s60 = r.b >> 34;
            let d2 = (2 * r.b.abs() / big) >> 34;
            let energy = ((x.n * r.q) / x.d
                + (u.n * (r.n0q + r.pm)) / (u.d * big)
                + (2 * (r.re_p >> 10)) / big
                - (2 * (r.a >> 10) * y.n) / y.d)
                >> 24;
            // epsilon at 2^62, outward.
            let eps = eps_tail + eps_poly + eps_round + 16;
            let eps40 = (eps >> 22) + 1;
            // |d<X>| <= eps (2 norm(X phi) + norm(X) eps); norm(X) <= (N + 1)^2 + N.
            let x_norm = (big + 1) * (big + 1) + big;
            let dx_s60 = (eps40 * (2 * r.x_up + ((x_norm * eps40) >> 8))) >> 12;
            // The read-out's own rounding, at 2^60: roots within 2^-24 on Sum |psi_i psi_t| <= 2 per kind, products within 2^-70 times the largest element.
            let dim_i = i128::try_from(block.dim).unwrap();
            let read_x = (2i128 << 37) + ((dim_i * big * big) >> 10) + 1;
            let read_s = (8i128 << 36) + ((dim_i * big) >> 10) + 1;
            let c1_err = ((2 * (dx_s60 + read_x)) / nn) + 1;
            let s_norm = 2 * (big + 1);
            let ds_s60 = (eps40 * (2 * r.s_up + ((s_norm * eps40) >> 8))) >> 12;
            let a1_err = (ds_s60 + read_s) / big + 1;
            let v2 = if c1 > 0 { (a1 * a1) / (2 * c1) } else { 0 };
            let lo = (a1 - a1_err).max(0);
            let hi = a1 + a1_err;
            let c_lo = c1 - c1_err;
            let c_hi = c1 + c1_err;
            let (v2_lo, v2_hi) = if c_lo > 0 {
                ((lo * lo) / (2 * c_hi), (hi * hi) / (2 * c_lo) + 1)
            } else {
                (0, -1)
            };
            let tag = if sab.name.is_empty() {
                String::new()
            } else {
                format!("sabotage={}|", sab.name)
            };
            let (array_bytes, layout_text) = match &stream {
                Some(st) => (
                    st.array_bytes(block.dim),
                    format!(
                        "|layout=stream|depth={}|tile={}|array_bytes_point_layout={}",
                        st.geom.depth,
                        st.geom.tile,
                        block.dim * 120
                    ),
                ),
                None if sector => (
                    states * SECTOR_BYTES_PER_STATE,
                    format!(
                        "|layout=sector|sector=Q0|sector_states={states}|array_bytes_point_layout={}",
                        block.dim * 120
                    ),
                ),
                None => (block.dim * 120, String::new()),
            };
            println!(
                "POLARITON_FIRST_CORRECTION_READ|{tag}N={big}|K={k}|even_states={}|array_bytes={array_bytes}|u=1|x={}|y={}|delta={}|t={}|window=2^-{w}|c={}|E={}|degree={degree}|reach={reach}|applies={applies}|elem_err_units={}|jbar_e18={}|f_e18={}|A_e18={}|B_e18={}|C1_e18={}|C2_e18={}|A1_e18={}|D2_e18={}|V2_e18={}|energy_e18={}|norm_off_e18={}|eps_tail_e18={}|eps_poly_e18={}|eps_round_e18={}|eps_e18={}|C1_err_e18={}|A1_err_e18={}|V2_lo_e18={}|V2_hi_e18={}|norm_B_s20={bnorm}|tail_max_e18={}|leak_max_e18={}|leak_sum_e18={}|float_used=0|json=0",
                block.dim,
                x.text(),
                y.text(),
                delta.text(),
                times[next_read].1.text(),
                op.c,
                op.e,
                op.elem_err_units,
                e18_s60(jbar),
                e18_s60(f),
                e18_s60(a_s60),
                e18_s60(b_s60),
                e18_s60(c1),
                e18_s60(c2),
                e18_s60(a1),
                e18_s60(d2),
                e18_s60(v2),
                e18_s60(energy),
                e18_s60((r.norm >> 24) - (1i128 << 60)),
                e18_s60(eps_tail >> 2),
                e18_s60(eps_poly >> 2),
                e18_s60(eps_round >> 2),
                e18_s60(eps >> 2),
                e18_s60(c1_err),
                e18_s60(a1_err),
                e18_s60(v2_lo),
                e18_s60(v2_hi),
                e18_s60(tail_max << 18),
                e18_s60(leak_max >> 2),
                e18_s60(leak_sum >> 2),
            );
            eprintln!(
                "POLARITON_FIRST_CORRECTION_COST|N={big}|K={k}|even_states={}|array_bytes={array_bytes}|delta={}|y={}|t={}|ms={}|peak_rss_kB={}{layout_text}|json=0",
                block.dim,
                delta.text(),
                y.text(),
                times[next_read].1.text(),
                began.elapsed().as_millis(),
                peak_rss_text(),
            );
            next_read += 1;
        }
    }
}

/// Every element of the block, exact and scaled, for the route's separate construction.
fn rows(n: i128, k_in: usize, delta: Rat, y: Rat) {
    let k = k_in.min(usize::try_from(n).unwrap());
    let block = Block::new(n, k, false);
    let u = rat(1, 1);
    let x = rat(delta.n - delta.d, delta.d);
    let op = build(&block, x, u, y);
    println!(
        "H_BLOCK|N={n}|K={k}|even_states={}|delta={}|y={}|c={}|E={}|elem_err_units={}|json=0",
        block.dim,
        delta.text(),
        y.text(),
        op.c,
        op.e,
        op.elem_err_units,
    );
    let text = |r: Raise| format!("{},{},{}", r.mul, r.m, r.den);
    for q in 0..=k {
        for mi in 0..=q / 2 {
            let i = block.start[q] + mi;
            let (num, den) = diag_rat(&block, x, u, q, mi);
            let pair = if q + 2 <= k {
                pair_raise(&block, q, mi)
            } else {
                Raise {
                    mul: 0,
                    m: 0,
                    den: 1,
                }
            };
            let (ra, rb) = if q < k {
                (a_raise(&block, y, q, mi), b_raise(&block, y, q, mi))
            } else {
                (
                    Raise {
                        mul: 0,
                        m: 0,
                        den: 1,
                    },
                    Raise {
                        mul: 0,
                        m: 0,
                        den: 1,
                    },
                )
            };
            println!(
                "H_STATE|q={q}|m={mi}|diag={num}/{den}|d={}|pair={}|pair_s={}|a={}|a_s={}|b={}|b_s={}|json=0",
                op.d[i],
                text(pair),
                op.pair[i],
                text(ra),
                op.a[i],
                text(rb),
                op.b[i],
            );
        }
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let get = |i: usize| -> &str { args.get(i).map_or("", String::as_str) };
    match get(1) {
        "point" => {
            let n: i128 = get(2).parse().expect("N");
            let k: usize = get(3).parse().expect("K");
            let delta = parse_rat(get(4));
            let y = parse_rat(get(5));
            let w: u32 = get(6).parse().expect("W");
            let mut times: Vec<(i128, Rat)> =
                get(7).split(',').map(|v| window_time(v, w)).collect();
            times.sort_unstable_by_key(|&(windows, _)| windows);
            let sab = match get(8).strip_prefix("sabotage=") {
                Some(rest) => parse_sabotage(rest),
                None => Sabotage::default(),
            };
            point(n, k, delta, y, &times, w, &sab, Layout::Dense);
        }
        "stream" => {
            let n: i128 = get(2).parse().expect("N");
            let k: usize = get(3).parse().expect("K");
            let delta = parse_rat(get(4));
            let y = parse_rat(get(5));
            let w: u32 = get(6).parse().expect("W");
            let mut times: Vec<(i128, Rat)> =
                get(7).split(',').map(|v| window_time(v, w)).collect();
            times.sort_unstable_by_key(|&(windows, _)| windows);
            let (mut sab, mut depth, mut tile) = (Sabotage::default(), 8usize, 512usize);
            for extra in args.iter().skip(8) {
                if let Some(rest) = extra.strip_prefix("sabotage=") {
                    sab = parse_sabotage(rest);
                } else if let Some(rest) = extra.strip_prefix("depth=") {
                    depth = match rest.parse() {
                        Ok(d) if d >= 2 => d,
                        _ => {
                            eprintln!("depth {rest} is not an integer of at least 2");
                            std::process::exit(2);
                        }
                    };
                } else if let Some(rest) = extra.strip_prefix("tile=") {
                    tile = match rest.parse() {
                        Ok(t) if t >= 1 => t,
                        _ => {
                            eprintln!("tile {rest} is not a positive integer");
                            std::process::exit(2);
                        }
                    };
                } else {
                    eprintln!("unknown argument {extra}");
                    std::process::exit(2);
                }
            }
            if tile < depth {
                eprintln!("tile {tile} is narrower than depth {depth}");
                std::process::exit(2);
            }
            point(
                n,
                k,
                delta,
                y,
                &times,
                w,
                &sab,
                Layout::Stream { depth, tile },
            );
        }
        "sector" => {
            let n: i128 = get(2).parse().expect("N");
            let k: usize = get(3).parse().expect("K");
            let delta = parse_rat(get(4));
            let y = parse_rat(get(5));
            let w: u32 = get(6).parse().expect("W");
            let mut times: Vec<(i128, Rat)> =
                get(7).split(',').map(|v| window_time(v, w)).collect();
            times.sort_unstable_by_key(|&(windows, _)| windows);
            let mut sab = Sabotage::default();
            for extra in args.iter().skip(8) {
                match extra.strip_prefix("sabotage=") {
                    Some(rest) => sab = parse_sector_sabotage(rest),
                    None => {
                        eprintln!("unknown argument {extra}");
                        std::process::exit(2);
                    }
                }
            }
            if y.n != 0 && !sab.run_at_nonzero_y {
                eprintln!(
                    "sector mode needs y = 0, where H keeps Q = n+ - n-; y = {} is refused",
                    y.text()
                );
                std::process::exit(2);
            }
            point(n, k, delta, y, &times, w, &sab, Layout::Sector);
        }
        "bessel" => {
            let z = parse_rat(get(2));
            for (k, v) in bessel(z.n, z.d).iter().enumerate() {
                println!("BESSEL|k={k}|J_s62={v}|json=0");
            }
        }
        "rows" => {
            let n: i128 = get(2).parse().expect("N");
            let k: usize = get(3).parse().expect("K");
            rows(n, k, parse_rat(get(4)), parse_rat(get(5)));
        }
        _ => {
            eprintln!("usage: polariton_first_correction point N K DELTA Y W T[,T2,...] [sabotage=NAME] | stream N K DELTA Y W T[,T2,...] [depth=D] [tile=M] [sabotage=NAME] | sector N K DELTA 0 W T[,T2,...] [sabotage=NAME] | bessel NUM/DEN | rows N K DELTA Y");
            std::process::exit(2);
        }
    }
}
