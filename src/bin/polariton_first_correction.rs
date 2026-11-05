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
//! usage: polariton_first_correction point N K DELTA Y W T[,T2,...] [sabotage=NAME]
//!        polariton_first_correction bessel NUM/DEN
//!        polariton_first_correction rows N K DELTA Y
//! W: the window is 2^-W. T are integers. A sabotage breaks the engine on purpose, and the reader must catch it.
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
    // The sum rule J_0^2 + 2 Sum J_k^2 = 1 within 2^-54.
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

fn point(n: i128, k_in: usize, delta: Rat, y: Rat, times: &[i128], w: u32, sab: &Sabotage) {
    let began = Instant::now();
    let k = k_in.min(usize::try_from(n).unwrap());
    let block = Block::new(n, k, sab.drop_even_root);
    let u = rat(1, 1);
    let x = rat(delta.n - delta.d, delta.d);
    let op = build(&block, x, u, y);
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

    let (mut re, mut im) = (vec![0i64; block.dim], vec![0i64; block.dim]);
    re[0] = i64::try_from(ONE).unwrap();
    let mut sum = vec![0i128; block.dim];
    let (mut acc_re, mut acc_im) = (vec![0i128; block.dim], vec![0i128; block.dim]);
    let (mut p0, mut p1, mut p2) = (
        vec![0i64; block.dim],
        vec![0i64; block.dim],
        vec![0i64; block.dim],
    );
    let mut eps_tail = 0i128; // at 2^62, outward
    let mut eps_poly = 0i128;
    let mut eps_round = 0i128;
    let mut leak_max = 0i128;
    let mut leak_sum = 0i128;
    let mut tail_max = 0i128;
    let mut applies = 0u64;
    let mut done = 0i128;
    let last = *times.iter().max().unwrap();
    let total_windows = last << w;
    let mut next_read = 0usize;
    while done < total_windows {
        // The certificate over the window that starts here.
        let tail = tail_norm(&block, reach, &re, &im); // at 2^42
        tail_max = tail_max.max(tail);
        let lk = leak(&block, y, &re, &im);
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
                    step(&block, &op, &p0, None, false, &mut sum, &mut p1);
                } else {
                    step(&block, &op, &p1, Some(&p0), true, &mut sum, &mut p2);
                    std::mem::swap(&mut p0, &mut p1);
                    std::mem::swap(&mut p1, &mut p2);
                }
                applies += 1;
            }
        }
        for i in 0..block.dim {
            re[i] = i64::try_from(acc_re[i] >> (Q - 16)).expect("re");
            im[i] = i64::try_from(acc_im[i] >> (Q - 16)).expect("im");
            if sab.norm_drift {
                re[i] += re[i] >> 32;
                im[i] += im[i] >> 32;
            }
        }
        done += 1;
        while next_read < times.len() && (times[next_read] << w) == done {
            let r = read(&block, &re, &im);
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
            let v2 = (a1 * a1) / (2 * c1);
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
            let array_bytes = block.dim * 120;
            println!(
                "POLARITON_FIRST_CORRECTION_READ|{tag}N={big}|K={k}|even_states={}|array_bytes={array_bytes}|u=1|x={}|y={}|delta={}|t={}|window=2^-{w}|c={}|E={}|degree={degree}|reach={reach}|applies={applies}|elem_err_units={}|jbar_e18={}|f_e18={}|A_e18={}|B_e18={}|C1_e18={}|C2_e18={}|A1_e18={}|D2_e18={}|V2_e18={}|energy_e18={}|norm_off_e18={}|eps_tail_e18={}|eps_poly_e18={}|eps_round_e18={}|eps_e18={}|C1_err_e18={}|A1_err_e18={}|V2_lo_e18={}|V2_hi_e18={}|norm_B_s20={bnorm}|tail_max_e18={}|leak_max_e18={}|leak_sum_e18={}|float_used=0|json=0",
                block.dim,
                x.text(),
                y.text(),
                delta.text(),
                times[next_read],
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
                "POLARITON_FIRST_CORRECTION_COST|N={big}|K={k}|even_states={}|array_bytes={array_bytes}|delta={}|y={}|t={}|ms={}|peak_rss_kB={}|json=0",
                block.dim,
                delta.text(),
                y.text(),
                times[next_read],
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
            let mut times: Vec<i128> = get(7).split(',').map(|v| v.parse().expect("T")).collect();
            times.sort_unstable();
            let sab = match get(8).strip_prefix("sabotage=") {
                Some(rest) => parse_sabotage(rest),
                None => Sabotage::default(),
            };
            point(n, k, delta, y, &times, w, &sab);
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
            eprintln!("usage: polariton_first_correction point N K DELTA Y W T[,T2,...] [sabotage=NAME] | bessel NUM/DEN | rows N K DELTA Y");
            std::process::exit(2);
        }
    }
}
