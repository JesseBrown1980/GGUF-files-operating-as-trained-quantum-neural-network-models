//! twens 0.4.0: the bridge's ensemble integrator for the three-mode contact model from |N,0,0>, integers only
//! (float_used=0). Rust 1.81, std only, no dependencies.
//!
//! 0.4.0 over 0.3.0 (723b3674): count-weighted reuse, the key memo=1 of run and the trailing argument memo=1 of twens.
//! The noise is a 4096-coin binomial, so a batch's starts repeat: VNC, V1, RN and FLIP read the four integer noise values
//! (c0, c1, c2, c3), c_i = g_i / 2^35 (K4); LOCK reads (c0, c1) (K2). With memo=1 the engine draws the batch's starts,
//! counts each K4 start inside the 4-ball sum c_i^2 <= 88^2 (one byte per cell, wraps carried exactly) and each K2 start
//! inside the box |c0|, |c1| <= 255, integrates each distinct start once and adds its per-record contributions times its
//! count; the starts outside those cores, V0, MODE0, and every variant that shares a pair row with V0 or MODE0 are
//! integrated sample by sample as in 0.3.0. Every summed field is an integer sum of per-sample terms that depend only on
//! the start, so w copies of a term add to w times the term: the rows equal the plain path's byte for byte (the
//! maxima eps_max are maxima over the same set). memo=0 or no key is the 0.3.0 path, operation for operation; the
//! counts and the integrations done are printed on stderr in one TWB_MEMO row, so stdout is the plain path's.
//!
//! 0.3.0 over 0.2.0 (the round-1 build with the second seat's holds R2, R3, R5, R7): the per-sample fixed-point rounding
//! bound of BRIDGE_ERRORS rounding_ensemble (derived below, printed in TWB_ROUND and TWB_PAIR_ROUND rows beside every
//! TWB and TWB_PAIR row, and per sample by dump); the noiseless path NL of C_NOISELESS (c0 = sqrt(N), c+- = 0, one
//! trajectory per batch, TWB_NL rows, a mask name beside the seven); the binary prints the sha256 of its two source files
//! in its head row, and on Windows MSVC it links with /Brepro (.cargo/config.toml) so a rebuild of the same source gives
//! the same binary. The legacy TWENS and TWPAIR rows and the TWCTL rows are unchanged byte for byte.
//! LOCK and FLIP start from VNC's state (the sharp total N + 3/2 on every sample, mode 0 real, read with X_NC): C_JFLIP
//! names all_else_as_VNC; on the locked seeds this start meets the frozen t = 0 value C1_lock = 2/N of
//! BRIDGE_CTRL_PHASE_LOCKED exactly (E[X_NC] = N - 1 for Gaussian seeds), where the controls lane's ring sqrt(N + 1/2)
//! read with X_W gives 2(N + 1/2)/(N(N - 1)).
//!
//! It joins two engines on one integrator:
//!   the ensemble lane's crate twens (source sha256 a971d90dac31f12ffcf3b739ca1d52aef12a1b8fbcd62f807fe6ef173df7eea8) and
//!   the controls lane's crate twctl (source sha256 7fd6807acca72bc340c994ad6cf5343138d3d6d627df2aebc369db72e0509e1f),
//! and carries the changes of PREDICTION.hbp lines 447 to 450 (BRIDGE_ENGINE_CHANGE, the ensemble integrator):
//!   VNC primary, with V1 and V0 (and the old engine's fourth variant RN) on common samples; the controls' switches as
//!   variants on the same samples (FLIP: the pair coupling J with its sign flipped; LOCK: pair-locked seeds
//!   b-(0) = conj(b+(0)); MODE0: mode 0's phase uniform, the partner of VNC's fixed phase); sha256 seeds; the per-sample
//!   derivation seed + index * 0x1000_0000_01B3 (wrapping; BRIDGE_SAMPLING writes 0x100000001B3, hold H1), splitmix64,
//!   xoshiro256**; a variant mask per batch; a start index
//!   (sample indices [start, start + count)); per-record sums beside the old ones; the reserved-point guard in the engine,
//!   lifted only by the explicit argument lift_reserved_guard=1.
//!
//! Fields psi_j = a_j / sqrt(N) as i64 at 2^40, products through i128, RK4 on the classical equations of H. The Weyl symbol
//! of H is H_cl - U N_tot + const, and U N_tot is a global phase, so H_cl gives the same invariant observables.
//!
//! Family twens (subcommands run, dump, twens): Gaussians g = (popcount of 4096 random bits - 2048)/32, variance exactly 1;
//! psi+- = (g_r + i g_i) h, h = floor(2^40/(2 sqrt N)); six Gaussians per sample, g0..g5 in the old engine's order.
//!   VNC   psi0 = sqrt((N + 3/2 - n(0))/N), n(0) = N(|psi+|^2 + |psi-|^2)   (the old engine's VN; read with X_NC)
//!   V1    psi0 = sqrt((N + 1/2)/N)
//!   V0    psi0 = 1 + vacuum noise (g4, g5)
//!   RN    psi0 = 1
//!   FLIP  VNC's start, integrated with the pair coupling's sign flipped (kappa = -1)
//!   LOCK  psi- = conj(psi+) on the sample's psi+, psi0 = sqrt((N + 3/2 - n(0))/N) on those seeds
//!   MODE0 VNC's start rotated as a whole by a unit vector of 30-bit integers drawn after g5 from the same per-sample stream
//!   NL    the noiseless trajectory, psi0 = 1, psi+- = 0 (c0 = sqrt(N)): no samples, computed once per batch (TWB_NL rows)
//! The linear control of each variant: zc = mz + C u + i RS v from the variant's own seeds in mode 0's frame,
//! u = psi+ + conj psi-, v = psi+ - conj psi- (MODE0 takes VNC's, since Z is invariant under the global rotation).
//!
//! Family twctl (subcommand twctl only): Gaussians g = (popcount of 65536 bits - 32768)/128; psi+- at
//! floor(floor(2^40/sqrt N)/2); psi0 = sqrt((N + 1/2)/N); seed modes vac | none | lock0; phase fixed | random | random30;
//! kappa -1, 0, 1; its observables and sums and its TWCTL rows. It shares the integrator, the generator, the lock and the
//! rotation with the twens family.
//!
//! Sums per record are raw integers: plain sums at 2^40; the old squares as sum of floor(v*v / 2^40) (at 2^40); the new
//! products exact (at 2^80). The reader forms means in rationals.

mod sha256;

use std::collections::HashMap;
use std::env;
use std::io::Write;
use std::sync::atomic::{AtomicU64, AtomicU8, AtomicUsize, Ordering};
use std::thread;

const Q: u32 = 40;
const ONE: i64 = 1i64 << Q;
const ONE128: i128 = 1i128 << Q;
const FNV: u64 = 0x1000_0000_01B3;
const PHASE_XOR: u64 = 0x5DEE_CE66_D1CE_F00D;
const PHASE_MUL: u64 = 0x9E37_79B9;
const VERSION: &str = "0.4.0";
/// The two source files this binary was compiled from, as compiled.
const SRC_MAIN: &[u8] = include_bytes!("main.rs");
const SRC_SHA256: &[u8] = include_bytes!("sha256.rs");

/// sha256 of src/main.rs and src/sha256.rs as compiled into this binary.
fn source_sha256() -> String {
    format!(
        "main.rs:{},sha256.rs:{}",
        sha256::hex(&sha256::sha256(SRC_MAIN)),
        sha256::hex(&sha256::sha256(SRC_SHA256))
    )
}

#[inline]
fn m(a: i64, b: i64) -> i64 {
    ((i128::from(a) * i128::from(b)) >> Q) as i64
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

// ---------------------------------------------------------------------------------------------------------------------
// The per-sample rounding bound (BRIDGE_ERRORS rounding_ensemble). Every quantity below is a nonnegative integer that is
// rounded up: magnitudes and coefficients are values at 2^40, errors are in ulps (1 ulp = 2^-40). The reference of the
// bound is exact arithmetic on the same sample: the exact Gaussian values g/2^40, h = 1/(2 sqrt N), the exact square roots
// of the starts, MODE0's integer unit vector as drawn, the exact parameters delta, u, y, the exact RK4 map at the same dtden,
// and the exact observables and linear control. The RK4 truncation itself is the step-halving estimate's (e_int).
//
// DERIVATION (DERIVED; each step rounded up in integers):
//  products m(a, b) floor, so each is below its exact value by less than 1 ulp; divisions truncate, less than 1 ulp;
//  isqrt floors, less than 1 ulp; a sum of k such terms is off by less than k ulps.
//  Start: psi+- = m(g, h) is off by < 1 + |g|/2^40 ulps per real component (h is below 1/(2 sqrt N) by < 1 ulp); the
//  sharp c0 = isqrt((1 + 3/(2N) - nsum) 2^40) is off by < 1 + d_arg/(2 sqrt(arg_lo)) (|sqrt a - sqrt b| <= |a-b|/(2 sqrt
//  min)); the V1 ring by < 2; MODE0's reference is VNC's exact start rotated by the integer vector (c, s) = trunc((a, b)
//  2^40 / r) itself, r = isqrt(a^2+b^2) >= 2^29, so |(c, s)| < 1 + 2^-29: VNC's start error times that, plus 3 ulps of floors.
//  Flow: with E_n the error of the computed state against the exact RK4 trajectory, E_{n+1} = Phi(x~) - Phi(x) + R_n, R_n
//  the rounding of one computed step at its own input. The model is i psi' = dH/dconj(psi), H real, so
//  Df v = -i (M v + S conj v), M Hermitian, S symmetric; the log norm of Df is at most |S| and |Df| <= |M| + |S| =: L
//  (row-sum bounds over the region the step's stage points can reach, R_j = max over the stage inputs of max + min/2 of
//  |re|, |im| (at least the modulus), plus 2 eps + 32: with hL <= 1/2 and h rho <= 8 the exact stage points of any state
//  within eps lie within 1.66 eps + 16 of the computed ones). RK4's step map has DPhi = I + h Abar + R2, Abar the weighted
//  mean of Df at the stage points,
//  |R2| <= (h^2 L^2/6)(3 + hL + h^2 L^2/4), |I + h Abar| <= sqrt(1 + 2 h mu + h^2 L^2), so
//  Lip(Phi) <= 1 + h mu + h^2 L^2 (1 + hL/6 + h^2 L^2/24) (requires hL <= 1/2, checked). R_n follows the stage chain
//  d1 = rho, d2 = rho + L(h d1/2 + 3), d3 = rho + L(h d2/2 + 3), d4 = rho + L(h d3 + 3), |R_n| <= h(d1+2d2+2d3+d4)/6 + 3,
//  rho the rhs rounding over the region (each product's floor and the parameters' 2^40 images, carried through the rhs
//  formula), 3 > sqrt(6) for the six truncations of a stage. So eps_{n+1} = Lip eps_n + |R_n|, eps_0 the 2-norm of the
//  start's error, and every mode's error is at most eps at t > 0 (at t = 0 the per-mode start errors are used).
//  Records: each observable's bound is its own rounding plus the first- and second-order propagation of the state's
//  error through its formula (written beside each line in obs_bounds); a field's bound in a row is the sum of the
//  per-sample bounds of the summed quantity (2|v| b + b^2 for squares and products, + 1 for a floor).

const ONEU: u128 = 1u128 << Q;

/// ceil(a * b / 2^40) for nonnegative a, b.
#[inline]
fn cu(a: u128, b: u128) -> u128 {
    (a * b + (ONEU - 1)) >> Q
}

#[inline]
fn uabs(v: i64) -> u128 {
    u128::from(v.unsigned_abs())
}

/// The modulus of (re, im) at 2^40, rounded up.
fn cmod(re: i64, im: i64) -> u128 {
    let s = uabs(re) * uabs(re) + uabs(im) * uabs(im);
    let r = isqrt(s);
    if r * r == s {
        r
    } else {
        r + 1
    }
}

/// max(|re|, |im|) + min(|re|, |im|)/2 at 2^40, rounded up: at least the modulus ((a + b/2)^2 >= a^2 + b^2 for a >= b),
/// at most 1.118 times it, so the region is the same at every phase of the sample (cheap; no square root).
#[inline]
fn amag(re: i64, im: i64) -> u64 {
    let (a, b) = (re.unsigned_abs(), im.unsigned_abs());
    a.max(b) + a.min(b).div_ceil(2)
}

/// Upper bounds of the exact parameters (values at 2^40) and of their 2^40 images' errors (ulps).
#[derive(Clone, Copy)]
struct Pb {
    dx: u128,
    du: u128,
    dy: u128,
    /// |x|, |u|, |y|, |kappa| at 2^20, rounded up (the step recursion's units).
    x20: u64,
    u20: u64,
    y20: u64,
    k20: u64,
}

/// 1 if parse_q of the text truncates (its value is not a multiple of 2^-40), else 0.
fn parse_inexact(s: &str) -> u128 {
    let (n, d) = match s.split_once('/') {
        Some((a, b)) => (
            a.parse::<i128>().expect("num"),
            b.parse::<i128>().expect("den"),
        ),
        None => (s.parse::<i128>().expect("int"), 1),
    };
    u128::from((n << Q) % d != 0)
}

impl Pb {
    fn new(p: &Par, delta: &str, u: &str, y: &str) -> Self {
        let (ed, eu, ey) = (parse_inexact(delta), parse_inexact(u), parse_inexact(y));
        let at20 = |v: u128| up20(v as u64);
        Self {
            dx: ed + eu,
            du: eu,
            dy: ey,
            x20: at20(uabs(p.x) + ed + eu),
            u20: at20(uabs(p.u) + eu),
            y20: at20(uabs(p.y) + ey),
            k20: if p.kappa == 0 { 0 } else { ONE20 },
        }
    }
}

/// The bound fault: the region or the stage rounding left the range the derivation covers.
fn bound_fault(what: &str) -> ! {
    eprintln!("TWB_FAULT|reason=rounding_bound_{what}|json=0");
    std::process::exit(4);
}

/// The step recursion's magnitudes and coefficients are values at 2^20, rounded up (cheaper than 2^40, and looser by at
/// most 2^-20 of each magnitude); its errors stay in ulps of 2^-40.
const B20: u32 = 20;
const ONE20: u64 = 1 << B20;

/// ceil(a * b / 2^20) for a value a at 2^20 and any b (the result in b's unit).
#[inline]
fn c20(a: u64, b: u64) -> u64 {
    (a * b + (ONE20 - 1)) >> B20
}

/// A value at 2^40 as a value at 2^20, rounded up.
#[inline]
fn up20(v: u64) -> u64 {
    v.div_ceil(1 << (Q - B20))
}

/// One RK4 step of the bound: eps (ulps, 2-norm of the state error) after the step, from eps before it and the stage
/// inputs' magnitudes (amag per mode, at 2^40).
fn step_bound(eps: u128, mag: [u64; 3], pb: &Pb, dtden: i64) -> u128 {
    if eps > (1u128 << 50) {
        bound_fault("state_bound_above_2^50_ulps");
    }
    let e = eps as u64;
    let dt = dtden as u64;
    let marg = up20(2 * e + 32);
    let r0 = up20(mag[0]) + marg;
    let r1 = up20(mag[1]) + marg;
    let r2 = up20(mag[2]) + marg;
    let (r00, r11, r22) = (c20(r0, r0), c20(r1, r1), c20(r2, r2));
    let (r01, r02, r12) = (c20(r0, r1), c20(r0, r2), c20(r1, r2));
    let (k, u, y, x) = (pb.k20, pb.u20, pb.y20, pb.x20);
    // S = d2H/dconj(psi)^2 row sums: the log norm bound mu
    let s0 = 2 * c20(k, r12) + c20(u, r01 + r02);
    let s1 = c20(u, r01 + r12) + c20(k, r00);
    let s2 = c20(u, r02 + r12) + c20(k, r00);
    let mu = s0.max(s1).max(s2);
    // M = d2H/dconj(psi) dpsi row sums
    let c01 = c20(u, r01) + 2 * c20(k, r02) + y;
    let c02 = c20(u, r02) + 2 * c20(k, r01) + y;
    let m0 = c20(u, r11 + r22) + c01 + c02;
    let m1 = x + c20(u, r00 + r22) + c20(u, r12) + c01;
    let m2 = x + c20(u, r00 + r11) + c20(u, r12) + c02;
    let l = m0.max(m1).max(m2) + mu;
    if 2 * l > dt * ONE20 {
        bound_fault("hL_above_1/2");
    }
    // the rhs rounding over the region (ulps): coefficients, then the six real components
    let (dx, du, dy) = (pb.dx as u64, pb.du as u64, pb.dy as u64);
    let u4 = c20(u, 4);
    let dcp = dx + 1 + u4 + c20(r00 + r22, du);
    let dcm = dx + 1 + u4 + c20(r00 + r11, du);
    let dc0 = 1 + u4 + c20(r11 + r22, du);
    let bp = 4 + c20(r1, dcp) + c20(r2, 4) + c20(r0, dy);
    let bm = 4 + c20(r2, dcm) + c20(r1, 4) + c20(r0, dy);
    let cc = 6 + c20(r0, dc0) + c20(r0, 8) + c20(r1 + r2, dy);
    let rho = 2 * (cc + bp + bm);
    if rho > 8 * dt {
        bound_fault("rhs_rounding_above_8_dtden");
    }
    let d1 = rho;
    let d2 = rho + c20(l, d1.div_ceil(2 * dt) + 3);
    let d3 = rho + c20(l, d2.div_ceil(2 * dt) + 3);
    let d4 = rho + c20(l, d3.div_ceil(dt) + 3);
    let r_step = (d1 + 2 * d2 + 2 * d3 + d4).div_ceil(6 * dt) + 3;
    let hmu = mu.div_ceil(dt);
    let hl = l.div_ceil(dt);
    let hl2 = c20(hl, hl);
    let lip = ONE20 + hmu + c20(hl2, ONE20 + hl.div_ceil(6) + hl2.div_ceil(24));
    ((u128::from(lip) * eps + u128::from(ONE20 - 1)) >> B20) + u128::from(r_step)
}

/// The bounds of one state's observables (ulps), from the computed state and the per-mode error bounds e: `o` in the
/// order of Obs (zr, zi, xw, xnc, f, br, bi), then |Z|^2 as z2 = m(zr, zr) + m(zi, zi) and fcl = |psi+|^2 + |psi-|^2.
#[derive(Clone, Copy, Default)]
struct ObsB {
    o: [u128; NO],
    z2: u128,
    fcl: u128,
}

fn obs_bounds(s: &St, n: i64, e: [u128; 3]) -> ObsB {
    let [r0, i0, rp, ip, rm, im] = *s;
    let (a0, a1, a2) = (cmod(r0, i0), cmod(rp, ip), cmod(rm, im));
    let [e0, e1, e2] = e;
    let nn = n as u128;
    // Z = conj(psi0) psi+ + conj(psi-) psi0: 4 floors per component, plus the propagated error
    let bz = 4 + cu(e0, a1 + a2) + cu(a0, e1 + e2) + cu(e0, e1 + e2);
    // |psi_j|^2: 2 floors, plus 2|psi| e + e^2
    let babs = |a: u128, ej: u128| 2 + cu(2 * a, ej) + cu(ej, ej);
    let (b0, b1, b2) = (babs(a0, e0), babs(a1, e1), babs(a2, e2));
    let o = obs(s, n);
    let (zr, zi) = (uabs(o[OZR]), uabs(o[OZI]));
    // z2 = m(zr, zr) + m(zi, zi) from the computed zr, zi
    let bz2 = 2 + cu(2 * zr, bz) + cu(2 * zi, bz) + 2 * cu(bz, bz);
    // xw = z2 - (abs0 + (absp + absm)/2)/n + 1/(2n^2), two truncations and the constant's
    let bxw = bz2 + (b0 + (b1 + b2).div_ceil(2) + 1).div_ceil(nn) + 1 + 1;
    // xnc = nn1 - m(nn1, nn1) + 1/(2n^2) + 2 pair, nn1 = absp + absm - 1/n
    let bnn1 = b1 + b2 + 1;
    let nn1 = uabs(m(rp, rp) + m(ip, ip) + m(rm, rm) + m(im, im) - ONE / n);
    let bmnn = 1 + cu(2 * nn1, bnn1) + cu(bnn1, bnn1);
    let pm_mag = uabs(m(rp, rm) - m(ip, im)) + uabs(m(rp, im) + m(ip, rm));
    let sq_mag = uabs(m(r0, r0) - m(i0, i0)) + uabs(2 * m(r0, i0));
    let bpm = 4 + cu(e1, a2) + cu(a1, e2) + cu(e1, e2);
    let bsq = 3 + cu(2 * a0, e0) + cu(e0, e0);
    let bpair = 2 + cu(pm_mag, bsq) + cu(sq_mag, bpm) + cu(bpm, bsq);
    let bxnc = bnn1 + bmnn + 1 + 2 * bpair;
    // B = conj(psi-) psi+
    let bb = 2 + cu(e2, a1) + cu(a2, e1) + cu(e1, e2);
    ObsB {
        o: [bz, bz, bxw, bxnc, b1 + b2 + 1, bb, bb],
        z2: bz2,
        fcl: b1 + b2,
    }
}

/// A rational "a/b" or "a" at 2^40, truncated toward zero (both old engines). Call after `parse_rat` accepted the text.
fn parse_q(s: &str) -> i64 {
    let (n, d) = match s.split_once('/') {
        Some((a, b)) => (
            a.parse::<i128>().expect("num"),
            b.parse::<i128>().expect("den"),
        ),
        None => (s.parse::<i128>().expect("int"), 1),
    };
    ((n << Q) / d) as i64
}

// ---------------------------------------------------------------------------------------------------------------------
// Exact rationals for the guard.

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

const RAT_LIMIT: i128 = 1i128 << 62;

fn parse_rat(s: &str) -> Result<Rat, String> {
    let (ps, qs) = match s.split_once('/') {
        Some((a, b)) => (a, b),
        None => (s, "1"),
    };
    let p: i128 = ps.parse().map_err(|_| format!("not_a_rational:{s}"))?;
    let q: i128 = qs.parse().map_err(|_| format!("not_a_rational:{s}"))?;
    // |value| <= 1024 keeps (p << 40) / q inside i64 for every parameter.
    if q <= 0 || q > RAT_LIMIT || !(-RAT_LIMIT..=RAT_LIMIT).contains(&p) || p.abs() > 1024 * q {
        return Err(format!("rational_out_of_range:{s}"));
    }
    let g = gcd(p, q).max(1);
    Ok(Rat { p: p / g, q: q / g })
}

/// |a - b| < eps, exactly.
fn within(a: Rat, b: Rat, eps: Rat) -> bool {
    let num = (a.p * b.q - b.p * a.q).abs();
    num * eps.q < eps.p * a.q * b.q
}

const RESERVED_N: [i64; 3] = [81, 729, 6561];

/// The reserved-point guard: None if (N, delta, y) is allowed, else the reason. The reserved set of BRIDGE_RESERVED:
/// delta = 3/5 and delta = -3/5 at every N, y, t; y = 2/27 at N = 81, 729, 6561 (|y|, since y -> -y flips only the sign
/// of E[Re Z]). Refused with it: the same points written as other rationals with the same 2^40 value, and the
/// neighbourhoods |delta -+ 3/5| < 1/20 and ||y| - 2/27| < 1/81 at those N.
fn guard_reason(n: i64, delta: &str, y: &str) -> Option<String> {
    let d = match parse_rat(delta) {
        Ok(v) => v,
        Err(e) => return Some(format!("delta_{e}")),
    };
    let yy = match parse_rat(y) {
        Ok(v) => v,
        Err(e) => return Some(format!("y_{e}")),
    };
    let d35 = Rat { p: 3, q: 5 };
    let dm35 = Rat { p: -3, q: 5 };
    if d == d35 || d == dm35 {
        return Some("reserved_delta".to_string());
    }
    let dq = parse_q(delta);
    if dq == parse_q("3/5") || dq == parse_q("-3/5") {
        return Some("reserved_delta_same_fixed_point".to_string());
    }
    let band_d = Rat { p: 1, q: 20 };
    if within(d, d35, band_d) || within(d, dm35, band_d) {
        return Some("reserved_delta_neighbourhood_1/20".to_string());
    }
    if RESERVED_N.contains(&n) {
        let ay = Rat {
            p: yy.p.abs(),
            q: yy.q,
        };
        let y227 = Rat { p: 2, q: 27 };
        if ay == y227 {
            return Some("reserved_y".to_string());
        }
        if parse_q(y).abs() == parse_q("2/27") {
            return Some("reserved_y_same_fixed_point".to_string());
        }
        if within(ay, y227, Rat { p: 1, q: 81 }) {
            return Some("reserved_y_neighbourhood_1/81".to_string());
        }
    }
    None
}

// ---------------------------------------------------------------------------------------------------------------------
// The shared integrator, generator, lock and rotation.

#[derive(Clone, Copy)]
struct Par {
    x: i64,
    u: i64,
    y: i64,
    kappa: i64,
}

type St = [i64; 6];

/// i d/dt of (psi0, psi+, psi-) as [re0, im0, re+, im+, re-, im-]; kappa = +1 the model, -1 the pair coupling's sign
/// flipped, 0 the pair coupling dropped. At kappa = 1 every product equals the old twens rhs term by term.
fn rhs(s: &St, p: &Par) -> St {
    let [r0, i0, rp, ip, rm, im] = *s;
    let abs0 = m(r0, r0) + m(i0, i0);
    let absp = m(rp, rp) + m(ip, ip);
    let absm = m(rm, rm) + m(im, im);
    let sq_re = p.kappa * (m(r0, r0) - m(i0, i0));
    let sq_im = p.kappa * 2 * m(r0, i0);
    let coefp = p.x + m(p.u, abs0 + absm);
    let coefm = p.x + m(p.u, abs0 + absp);
    let bp_re = m(coefp, rp) + m(rm, sq_re) + m(im, sq_im) - m(p.y, r0);
    let bp_im = m(coefp, ip) + m(rm, sq_im) - m(im, sq_re) - m(p.y, i0);
    let bm_re = m(coefm, rm) + m(rp, sq_re) + m(ip, sq_im) - m(p.y, r0);
    let bm_im = m(coefm, im) + m(rp, sq_im) - m(ip, sq_re) - m(p.y, i0);
    let pm_re = p.kappa * (m(rp, rm) - m(ip, im));
    let pm_im = p.kappa * (m(rp, im) + m(ip, rm));
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
    for i in 0..6 {
        o[i] += (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) / (6 * dtden);
    }
    o
}

/// rk4 with the per-mode magnitudes (amag, at 2^40) of its four stage inputs, maximised, for the rounding bound.
/// The state it returns is rk4's, operation for operation.
fn rk4m(s: &St, p: &Par, dtden: i64) -> (St, [u64; 3]) {
    let mut mag = [0u64; 3];
    let mut see = |x: &St| {
        for (j, mg) in mag.iter_mut().enumerate() {
            *mg = (*mg).max(amag(x[2 * j], x[2 * j + 1]));
        }
    };
    see(s);
    let k1 = rhs(s, p);
    let s2 = addk(s, &k1, 2 * dtden);
    see(&s2);
    let k2 = rhs(&s2, p);
    let s3 = addk(s, &k2, 2 * dtden);
    see(&s3);
    let k3 = rhs(&s3, p);
    let s4 = addk(s, &k3, dtden);
    see(&s4);
    let k4 = rhs(&s4, p);
    let mut o = *s;
    for i in 0..6 {
        o[i] += (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) / (6 * dtden);
    }
    (o, mag)
}

/// Rotate the whole sample by the unit vector (c, sn) at 2^40 (the controls lane's rot).
fn rot(s: &St, c: i64, sn: i64) -> St {
    let r = |re: i64, im: i64| -> (i64, i64) { (m(re, c) - m(im, sn), m(re, sn) + m(im, c)) };
    let (r0, i0) = r(s[0], s[1]);
    let (rp, ip) = r(s[2], s[3]);
    let (rm, im) = r(s[4], s[5]);
    [r0, i0, rp, ip, rm, im]
}

/// Pair-locked seeds: psi- = conj(psi+) (the controls lane's lock0).
fn lock_seeds(rp: i64, ip: i64) -> [i64; 4] {
    [rp, ip, rp, -ip]
}

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
    fn new(seed: u64) -> Self {
        let mut z = seed;
        Self {
            s: [
                splitmix(&mut z),
                splitmix(&mut z),
                splitmix(&mut z),
                splitmix(&mut z),
            ],
        }
    }
    /// The generator of sample `idx` of the point's seed (BRIDGE_SAMPLING per_sample).
    fn sample(seed: u64, idx: u64) -> Self {
        Self::new(seed.wrapping_add(idx.wrapping_mul(FNV)))
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
    /// Binomial(64 W, 1/2) - 32 W, scaled by 2^(Q - S) (variance exactly 1 when 16 W = 4^S): W = 64, S = 5 is the
    /// twens Gaussian, W = 1024, S = 7 the twctl one.
    fn gauss<const W: u32, const S: u32>(&mut self) -> i64 {
        let mut c: i64 = 0;
        for _ in 0..W {
            c += i64::from(self.next().count_ones());
        }
        (c - 32 * i64::from(W)) << (Q - S)
    }
    /// A unit vector (cos, sin) at 2^40 with uniform angle, by rejection in the disc (20-bit integers).
    fn unit(&mut self) -> (i64, i64) {
        loop {
            let a = (self.next() >> 43) as i64 - (1i64 << 20);
            let b = (self.next() >> 43) as i64 - (1i64 << 20);
            let r2 = i128::from(a) * i128::from(a) + i128::from(b) * i128::from(b);
            if !((1i128 << 30)..=(1i128 << 40)).contains(&r2) {
                continue;
            }
            let r = isqrt(r2 as u128) as i128;
            return (
                ((i128::from(a) << Q) / r) as i64,
                ((i128::from(b) << Q) / r) as i64,
            );
        }
    }
    /// The same with 30-bit integers in the disc, so the vector's norm is 1 within 2^-29.
    fn unit30(&mut self) -> (i64, i64) {
        let (c, s, _) = self.unit30x();
        (c, s)
    }
    /// unit30 and, for the rounding bound, ceil(D 2^40 / (2 r^2)) with D = a^2 + b^2 - r^2: the vector's norm exceeds 1 by
    /// at most that many 2^-40 (relative), besides the two truncations.
    fn unit30x(&mut self) -> (i64, i64, u128) {
        loop {
            let a = (self.next() >> 33) as i64 - (1i64 << 30);
            let b = (self.next() >> 33) as i64 - (1i64 << 30);
            let r2 = i128::from(a) * i128::from(a) + i128::from(b) * i128::from(b);
            if !((1i128 << 58)..=(1i128 << 60)).contains(&r2) {
                continue;
            }
            let r = isqrt(r2 as u128) as i128;
            let d = (r2 - r * r) as u128;
            let rr = (r * r) as u128;
            let eta = (d << Q).div_ceil(2 * rr);
            return (
                ((i128::from(a) << Q) / r) as i64,
                ((i128::from(b) << Q) / r) as i64,
                eta,
            );
        }
    }
}

/// Split [start, start + count) into `threads` contiguous chunks whose sizes differ by at most one.
fn chunks(start: u64, count: u64, threads: u64) -> Vec<(u64, u64)> {
    let base = count / threads;
    let rem = count % threads;
    let mut out = Vec::new();
    let mut first = start;
    for t in 0..threads {
        let c = base + u64::from(t < rem);
        out.push((first, c));
        first += c;
    }
    out
}

// ---------------------------------------------------------------------------------------------------------------------
// The twens family: the bridge's variants on common samples.

const NV: usize = 7;
const VNC: usize = 0;
const V1: usize = 1;
const V0: usize = 2;
const RN: usize = 3;
const FLIP: usize = 4;
const LOCK: usize = 5;
const MODE0: usize = 6;
const VNAME: [&str; NV] = ["VNC", "V1", "V0", "RN", "FLIP", "LOCK", "MODE0"];
const VINIT: [&str; NV] = [
    "sharp",
    "ring_half",
    "coherent",
    "ring",
    "sharp",
    "sharp",
    "sharp",
];
const VSEEDS: [&str; NV] = ["vac", "vac", "vac", "vac", "vac", "lock", "vac"];
const VKAPPA: [i64; NV] = [1, 1, 1, 1, -1, 1, 1];
const VPHASE: [&str; NV] = [
    "fixed", "fixed", "fixed", "fixed", "fixed", "fixed", "rot30",
];
/// The old engine's rows, in its order: (variant, its old name).
const LEGACY: [(usize, &str); 4] = [(V1, "V1"), (VNC, "VN"), (V0, "V0"), (RN, "RN")];

// Observables of one state, at 2^40: Z = A_W/N (re, im), X_W/N^2, X_NC/N^2, f = (n - 1)/N, B = B_W/N = conj(psi-) psi+.
const OZR: usize = 0;
const OZI: usize = 1;
const OXW: usize = 2;
const OXNC: usize = 3;
const OF: usize = 4;
const OBR: usize = 5;
const OBI: usize = 6;
const NO: usize = 7;
type Obs = [i64; NO];

/// Pairs on common samples, d = a.obs - b.obs per sample: (a, obs, b, obs, name). The first five are the old engine's
/// TWPAIR pairs in its order.
const NPAIR: usize = 11;
const PAIRS: [(usize, usize, usize, usize, &str); NPAIR] = [
    (V1, OXW, VNC, OXNC, "V1xw-VNCxnc"),
    (V1, OZR, VNC, OZR, "V1zr-VNCzr"),
    (V0, OXW, V1, OXW, "V0xw-V1xw"),
    (V0, OZR, V1, OZR, "V0zr-V1zr"),
    (V1, OXW, VNC, OXW, "V1xw-VNCxw"),
    (MODE0, OZR, VNC, OZR, "MODE0zr-VNCzr"),
    (MODE0, OZI, VNC, OZI, "MODE0zi-VNCzi"),
    (MODE0, OXNC, VNC, OXNC, "MODE0xnc-VNCxnc"),
    (MODE0, OF, VNC, OF, "MODE0f-VNCf"),
    (MODE0, OBR, VNC, OBR, "MODE0br-VNCbr"),
    (MODE0, OBI, VNC, OBI, "MODE0bi-VNCbi"),
];

/// Observables of one state (the old twens obs, plus B).
fn obs(s: &St, n: i64) -> Obs {
    let [r0, i0, rp, ip, rm, im] = *s;
    let zr = m(r0, rp) + m(i0, ip) + m(rm, r0) + m(im, i0);
    let zi = m(r0, ip) - m(i0, rp) + m(rm, i0) - m(im, r0);
    let abs0 = m(r0, r0) + m(i0, i0);
    let absp = m(rp, rp) + m(ip, ip);
    let absm = m(rm, rm) + m(im, im);
    let z2 = m(zr, zr) + m(zi, zi);
    let half_n2 = ONE / (2 * n * n);
    // 3-mode Weyl: X_W/N^2 = |Z|^2 - (|psi0|^2 + (|psi+|^2 + |psi-|^2)/2)/N + 1/(2N^2)
    let xw = z2 - (abs0 + (absp + absm) / 2) / n + half_n2;
    // number-conserving: X_NC/N^2 = (nn - 1)/N - (nn - 1)^2/N^2 + 1/(2N^2) + 2 Re(conj psi+ conj psi- psi0^2), nn = N(|psi+|^2 + |psi-|^2)
    let nn_m1_over_n = absp + absm - ONE / n; // (nn - 1)/N
    let sq_re = m(r0, r0) - m(i0, i0);
    let sq_im = 2 * m(r0, i0);
    let pm_re = m(rp, rm) - m(ip, im);
    let pm_im = m(rp, im) + m(ip, rm);
    // conj(pm) * sq = (pm_re - i pm_im)(sq_re + i sq_im): real part pm_re sq_re + pm_im sq_im
    let pair = m(pm_re, sq_re) + m(pm_im, sq_im);
    let xnc = nn_m1_over_n - m(nn_m1_over_n, nn_m1_over_n) + half_n2 + 2 * pair;
    let f = absp + absm - ONE / n;
    // B_W/N = conj(psi-) psi+ = (rm - i im)(rp + i ip)
    let br = m(rm, rp) + m(im, ip);
    let bi = m(rm, ip) - m(im, rp);
    [zr, zi, xw, xnc, f, br, bi]
}

#[derive(Clone, Copy)]
struct VSum {
    /// zr, zi, dzr, dzi, xw, dxw, xnc, dxnc, f (at 2^40), the old engine's order.
    s: [i128; 9],
    /// floor squares of dzr, dxw, dxnc, zr, xw, xnc, dzi (at 2^40), the old engine's order.
    q: [i128; 7],
    /// f^2, br, bi, br^2, bi^2, br*bi, zr*xw, zr*xnc, dzr*dxw, dzr*dxnc (br, bi at 2^40; products exact at 2^80).
    x: [i128; 10],
    /// exact squares of zr, zi, dzr, dzi, xw, dxw, xnc, dxnc (at 2^80): the variances of both estimators.
    e: [i128; 8],
    /// the rounding bound of every field above, in its order (s, q, x, e), summed over the samples (TWB_ROUND).
    rb: [u128; NRB],
    /// the largest per-sample state bound at this record (ulps, 2-norm).
    epsmax: u128,
}

impl Default for VSum {
    fn default() -> Self {
        Self {
            s: [0; 9],
            q: [0; 7],
            x: [0; 10],
            e: [0; 8],
            rb: [0; NRB],
            epsmax: 0,
        }
    }
}

/// The number of bounded fields of a TWB row: 9 s, 7 q, 10 x, 8 e.
const NRB: usize = 34;
const RB_NAMES: [&str; NRB] = [
    "zr", "zi", "dzr", "dzi", "xw", "dxw", "xnc", "dxnc", "f", "qdzr", "qdxw", "qdxnc", "qzr",
    "qxw", "qxnc", "qdzi", "f2", "br", "bi", "br2", "bi2", "brbi", "zrxw", "zrxnc", "dzrdxw",
    "dzrdxnc", "zr2", "zi2", "dzr2", "dzi2", "xw2", "dxw2", "xnc2", "dxnc2",
];

#[derive(Clone, Copy, Default)]
struct PSum {
    d: i128,
    q: i128,
    d2: i128,
    /// the rounding bound of d, q, d2, summed over the samples (TWB_PAIR_ROUND).
    rb: [u128; 3],
}

#[derive(Clone)]
struct EnsRec {
    v: Vec<[VSum; NV]>,
    p: Vec<[PSum; NPAIR]>,
    count: i128,
}

impl EnsRec {
    fn new(nr: usize) -> Self {
        Self {
            v: vec![[VSum::default(); NV]; nr],
            p: vec![[PSum::default(); NPAIR]; nr],
            count: 0,
        }
    }
    fn add(&mut self, o: &EnsRec) {
        for r in 0..self.v.len() {
            for v in 0..NV {
                let (a, b) = (&mut self.v[r][v], &o.v[r][v]);
                for (x, y) in a.s.iter_mut().zip(b.s.iter()) {
                    *x += y;
                }
                for (x, y) in a.q.iter_mut().zip(b.q.iter()) {
                    *x += y;
                }
                for (x, y) in a.x.iter_mut().zip(b.x.iter()) {
                    *x += y;
                }
                for (x, y) in a.e.iter_mut().zip(b.e.iter()) {
                    *x += y;
                }
                for (x, y) in a.rb.iter_mut().zip(b.rb.iter()) {
                    *x += y;
                }
                a.epsmax = a.epsmax.max(b.epsmax);
            }
            for k in 0..NPAIR {
                let (a, b) = (&mut self.p[r][k], &o.p[r][k]);
                a.d += b.d;
                a.q += b.q;
                a.d2 += b.d2;
                for (x, y) in a.rb.iter_mut().zip(b.rb.iter()) {
                    *x += y;
                }
            }
        }
        self.count += o.count;
    }
}

struct EnsJob {
    n: i64,
    par: Par,
    dtden: i64,
    steps: Vec<usize>,
    ctrl: Vec<(i64, i64, i64)>,
    seed: u64,
    h: i64,
    psi_v1: i64,
    on: [bool; NV],
    /// the noiseless trajectory NL (C_NOISELESS): c0 = sqrt(N), c+- = 0, one trajectory per batch.
    nl: bool,
    /// the rounding bound's parameter bounds (the same for kappa = +1 and -1).
    pb: Pb,
}

impl EnsJob {
    fn new(
        n: i64,
        delta: &str,
        u: &str,
        y: &str,
        dtden: i64,
        steps: Vec<usize>,
        ctrl: Vec<(i64, i64, i64)>,
    ) -> Self {
        let n128 = i128::from(n);
        let (dq, uq, yq) = (parse_q(delta), parse_q(u), parse_q(y));
        let par = Par {
            x: dq - uq,
            u: uq,
            y: yq,
            kappa: 1,
        };
        Self {
            n,
            par,
            dtden,
            steps,
            ctrl,
            seed: 0,
            // h = 2^40 / (2 sqrt N), floored: isqrt(2^80 / (4 N))
            h: isqrt(((ONE128 * ONE128) / (4 * n128)) as u128) as i64,
            psi_v1: isqrt(((((2 * n128 + 1) * ONE128) / (2 * n128)) * ONE128) as u128) as i64,
            on: [true; NV],
            nl: false,
            pb: Pb::new(&par, delta, u, y),
        }
    }
}

/// The 2-norm of three per-mode bounds, rounded up.
fn norm3(e: [u128; 3]) -> u128 {
    let s = e[0] * e[0] + e[1] * e[1] + e[2] * e[2];
    let r = isqrt(s);
    if r * r == s {
        r
    } else {
        r + 1
    }
}

/// Start error of a real component of psi+- = m(g, h): < 1 + |g|/2^40 ulps (h lies below 1/(2 sqrt N) by < 1 ulp).
fn seed_err(g: i64) -> u128 {
    1 + uabs(g).div_ceil(ONEU)
}

/// Start error of the sharp c0 = sharp(nsum, n), from the seed components and their errors: nsum is off by
/// < 4 + sum(2|c| e + e^2), the argument by one more (the truncation of 3/(2N)), and the floor square root by
/// < 1 + d_arg/(2 sqrt(arg_lo)), arg_lo = arg - d_arg.
fn sharp_err(comps: [i64; 4], errs: [u128; 4], n: i64) -> u128 {
    let mut dn: u128 = 4;
    let mut nsum: i64 = 0;
    for (cv, ce) in comps.iter().zip(errs.iter()) {
        dn += cu(2 * uabs(*cv), *ce) + cu(*ce, *ce);
        nsum += m(*cv, *cv);
    }
    let darg = dn + 1;
    let arg = ONE + (3 * ONE) / (2 * n) - nsum;
    let lo = u128::try_from(arg).unwrap_or(0).saturating_sub(darg);
    if lo == 0 {
        bound_fault("sharp_argument_low_end_not_positive");
    }
    let slo = isqrt(lo << Q);
    1 + (darg << Q).div_ceil(2 * slo)
}

/// psi0 = sqrt(1 + 3/(2N) - nsum) at 2^40 (the old engine's VN). A non-positive argument has no square root: the
/// engine stops rather than integrate a wrong sample.
fn sharp(nsum: i64, n: i64) -> i64 {
    let arg = ONE + (3 * ONE) / (2 * n) - nsum;
    if arg <= 0 {
        eprintln!("TWB_FAULT|reason=sharp_mode0_argument_not_positive|arg={arg}|json=0");
        std::process::exit(4);
    }
    isqrt((i128::from(arg) * ONE128) as u128) as i64
}

/// Everything one sample contributes: its six Gaussians, each variant's start and control seeds (u_re, u_im, v_re, v_im),
/// MODE0's unit vector, and the observables at every record.
struct Sample {
    g: [i64; 6],
    init: [St; NV],
    uv: [[i64; 4]; NV],
    rot: (i64, i64),
    vals: Vec<Obs>,
    /// the rounding bound: each variant's per-mode start errors (psi0, psi+, psi-), the bound on its control seeds' error
    /// (|du|, |dv| <= e+ + e- of its seeds), MODE0's unit-vector term, and per record the observables' bounds and the
    /// state's 2-norm bound.
    ib: [[u128; 3]; NV],
    sb: [u128; NV],
    eta: u128,
    ob: Vec<ObsB>,
    eps: Vec<u128>,
}

impl Sample {
    fn new(nr: usize) -> Self {
        Self {
            g: [0; 6],
            init: [[0; 6]; NV],
            uv: [[0; 4]; NV],
            rot: (ONE, 0),
            vals: vec![[0; NO]; nr * NV],
            ib: [[0; 3]; NV],
            sb: [0; NV],
            eta: 0,
            ob: vec![ObsB::default(); nr * NV],
            eps: vec![0; nr * NV],
        }
    }
}

/// Where one integration writes its records: the observables, their bounds and the state bound, every `stride`-th entry.
type RecOut<'a> = (&'a mut [Obs], &'a mut [ObsB], &'a mut [u128], usize);

/// Integrate one start (state, per-mode start errors) to every record, with the rounding bound.
fn integrate(job: &EnsJob, par: &Par, start: (St, [u128; 3]), out: RecOut) {
    let (init, e0) = start;
    let (vals, ob, eps_out, stride) = out;
    let nr = job.steps.len();
    let last = *job.steps.last().unwrap_or(&0);
    let mut st = init;
    let mut eps = norm3(e0);
    let mut next = 0usize;
    for step in 0..=last {
        while next < nr && job.steps[next] == step {
            vals[next * stride] = obs(&st, job.n);
            let e = if step == 0 { e0 } else { [eps; 3] };
            ob[next * stride] = obs_bounds(&st, job.n, e);
            eps_out[next * stride] = eps;
            next += 1;
        }
        if step < last {
            let (ns, mag) = rk4m(&st, par, job.dtden);
            eps = step_bound(eps, mag, &job.pb, job.dtden);
            st = ns;
        }
    }
}

fn uv_of(sp: [i64; 4]) -> [i64; 4] {
    let [rp, ip, rm, im] = sp;
    [rp + rm, ip - im, rp - rm, ip + im]
}

fn ens_sample(job: &EnsJob, idx: u64, out: &mut Sample) {
    let (g, r30) = ens_draw(job, idx);
    ens_build(job, g, r30, &job.on, out);
    ens_integrate(job, &job.on, out);
}

/// The draws of sample `idx` (BRIDGE_SAMPLING per_sample): the six Gaussians, then MODE0's unit vector when MODE0 is
/// on (the same stream, after g5), else (1, 0) with eta 0.
fn ens_draw(job: &EnsJob, idx: u64) -> ([i64; 6], (i64, i64, u128)) {
    let mut rng = Rng::sample(job.seed, idx);
    let mut g = [0i64; 6];
    for x in g.iter_mut() {
        *x = rng.gauss::<64, 5>();
    }
    let r30 = if job.on[MODE0] {
        rng.unit30x()
    } else {
        (ONE, 0, 0)
    };
    (g, r30)
}

/// Every start of one sample from its draws: the starts, control seeds and start errors of the variants in `need`
/// (VNC's sharp start when VNC, FLIP or MODE0 is needed; LOCK's when LOCK is), the others' from the same formulas.
fn ens_build(
    job: &EnsJob,
    g: [i64; 6],
    r30: (i64, i64, u128),
    need: &[bool; NV],
    out: &mut Sample,
) {
    out.g = g;
    let h = job.h;
    let (rp, ip, rm, im) = (m(g[0], h), m(g[1], h), m(g[2], h), m(g[3], h));
    let nsum = m(rp, rp) + m(ip, ip) + m(rm, rm) + m(im, im);
    let on = need;
    let psi_vn = if on[VNC] || on[FLIP] || on[MODE0] {
        sharp(nsum, job.n)
    } else {
        0
    };
    let vac = uv_of([rp, ip, rm, im]);
    out.init[VNC] = [psi_vn, 0, rp, ip, rm, im];
    out.init[V1] = [job.psi_v1, 0, rp, ip, rm, im];
    out.init[V0] = [ONE + m(g[4], h), m(g[5], h), rp, ip, rm, im];
    out.init[RN] = [ONE, 0, rp, ip, rm, im];
    out.init[FLIP] = out.init[VNC];
    let [lp, lip, lm, lim] = lock_seeds(rp, ip);
    let psi_l = if on[LOCK] {
        sharp(m(lp, lp) + m(lip, lip) + m(lm, lm) + m(lim, lim), job.n)
    } else {
        0
    };
    out.init[LOCK] = [psi_l, 0, lp, lip, lm, lim];
    let (c30, s30, eta30) = r30;
    out.rot = (c30, s30);
    out.eta = eta30;
    out.init[MODE0] = rot(&out.init[VNC], out.rot.0, out.rot.1);
    for (v, uv) in out.uv.iter_mut().enumerate() {
        *uv = if v == LOCK {
            uv_of([lp, lip, lm, lim])
        } else {
            vac
        };
    }
    // the start errors of the rounding bound (per mode: psi0, psi+, psi-; per real component of the seeds)
    let ec = [
        seed_err(g[0]),
        seed_err(g[1]),
        seed_err(g[2]),
        seed_err(g[3]),
    ];
    let (ep, em) = (ec[0] + ec[1], ec[2] + ec[3]);
    let e_vn = if on[VNC] || on[FLIP] || on[MODE0] {
        sharp_err([rp, ip, rm, im], ec, job.n)
    } else {
        0
    };
    out.ib[VNC] = [e_vn, ep, em];
    out.ib[V1] = [2, ep, em];
    out.ib[V0] = [seed_err(g[4]) + seed_err(g[5]), ep, em];
    out.ib[RN] = [0, ep, em];
    out.ib[FLIP] = out.ib[VNC];
    let e_l = if on[LOCK] {
        sharp_err([lp, lip, lm, lim], [ec[0], ec[1], ec[0], ec[1]], job.n)
    } else {
        0
    };
    out.ib[LOCK] = [e_l, ep, ep];
    // MODE0's reference: the exact VNC start rotated by the integer vector (c30, s30)/2^40 itself, whose norm is below
    // 1 + 2^-29 (r >= 2^29); C_MODE0 reads "a unit vector exact to at least 2^-29". Its start error is VNC's times that
    // norm, plus the 3 ulps of the rotation's floors (modulus below sqrt(5)).
    let mut ib6 = out.ib[VNC];
    for e in ib6.iter_mut() {
        *e = cu(*e, ONEU + (1 << 11)) + 3;
    }
    out.ib[MODE0] = ib6;
    for (v, sb) in out.sb.iter_mut().enumerate() {
        *sb = if v == LOCK { 2 * ep } else { ep + em };
    }
}

/// Integrate the built starts of the variants in `sel` to every record, with the rounding bound.
fn ens_integrate(job: &EnsJob, sel: &[bool; NV], out: &mut Sample) {
    let flip = Par {
        kappa: -1,
        ..job.par
    };
    for (v, &is_on) in sel.iter().enumerate() {
        if !is_on {
            continue;
        }
        let par = if v == FLIP { &flip } else { &job.par };
        integrate(
            job,
            par,
            (out.init[v], out.ib[v]),
            (&mut out.vals[v..], &mut out.ob[v..], &mut out.eps[v..], NV),
        );
    }
}

/// The noiseless trajectory NL of C_NOISELESS: c0 = sqrt(N) (psi0 = 1 exactly), c+- = 0, the model's coupling; one per batch.
struct NlRec {
    vals: Vec<Obs>,
    ob: Vec<ObsB>,
    eps: Vec<u128>,
    states: Vec<St>,
}

fn nl_run(job: &EnsJob) -> NlRec {
    let nr = job.steps.len();
    let mut r = NlRec {
        vals: vec![[0; NO]; nr],
        ob: vec![ObsB::default(); nr],
        eps: vec![0; nr],
        states: vec![[0; 6]; nr],
    };
    let init: St = [ONE, 0, 0, 0, 0, 0];
    integrate(
        job,
        &job.par,
        (init, [0; 3]),
        (&mut r.vals, &mut r.ob, &mut r.eps, 1),
    );
    // the states at the records, for the trajectory-frame reads (A1, C1, f, D2 from Z, B and |psi+-|^2)
    let last = *job.steps.last().unwrap_or(&0);
    let mut st = init;
    let mut next = 0usize;
    for step in 0..=last {
        while next < nr && job.steps[next] == step {
            r.states[next] = st;
            next += 1;
        }
        if step < last {
            st = rk4m(&st, &job.par, job.dtden).0;
        }
    }
    r
}

/// The linear control of a variant at a record: (zc_re, zc_im, xc).
fn lin(job: &EnsJob, r: usize, uv: &[i64; 4]) -> (i64, i64, i64) {
    let (cc, rs, mz) = job.ctrl[r];
    let [u_re, u_im, v_re, v_im] = *uv;
    let zc_re = mz + m(cc, u_re) - m(rs, v_im);
    let zc_im = m(cc, u_im) + m(rs, v_re);
    let xc = m(zc_re, zc_re) + m(zc_im, zc_im) - ONE / job.n;
    (zc_re, zc_im, xc)
}

fn ens_accumulate(job: &EnsJob, smp: &Sample, rec: &mut EnsRec) {
    ens_accumulate_w(job, smp, rec, 1, &job.on, &[true; NPAIR]);
    rec.count += 1;
}

/// The contributions of one sample's variants in `vsel` and its pair rows in `psel` (a pair also needs both variants
/// on), each taken `w` times: every field is a sum of integer terms, so w equal terms add to w times the term, and a
/// maximum over w equal values is that value. rec.count is the caller's. Inlined, so the plain path's w = 1 folds away.
#[inline(always)]
fn ens_accumulate_w(
    job: &EnsJob,
    smp: &Sample,
    rec: &mut EnsRec,
    w: u64,
    vsel: &[bool; NV],
    psel: &[bool; NPAIR],
) {
    let wi = i128::from(w);
    let wu = u128::from(w);
    for r in 0..job.steps.len() {
        for (v, &vs) in vsel.iter().enumerate() {
            if !(job.on[v] && vs) {
                continue;
            }
            let (zc_re, zc_im, xc) = lin(job, r, &smp.uv[v]);
            let [zr, zi, xw, xnc, f, br, bi] = smp.vals[r * NV + v];
            let d_zr = zr - zc_re;
            let d_zi = zi - zc_im;
            let d_xw = xw - xc;
            let d_xnc = xnc - xc;
            let a = &mut rec.v[r][v];
            for (acc, val) in
                a.s.iter_mut()
                    .zip([zr, zi, d_zr, d_zi, xw, d_xw, xnc, d_xnc, f])
            {
                *acc += wi * i128::from(val);
            }
            for (acc, val) in a.q.iter_mut().zip([d_zr, d_xw, d_xnc, zr, xw, xnc, d_zi]) {
                *acc += wi * ((i128::from(val) * i128::from(val)) >> Q);
            }
            let pw = |p: i64, q: i64| i128::from(p) * i128::from(q);
            let new = [
                pw(f, f),
                i128::from(br),
                i128::from(bi),
                pw(br, br),
                pw(bi, bi),
                pw(br, bi),
                pw(zr, xw),
                pw(zr, xnc),
                pw(d_zr, d_xw),
                pw(d_zr, d_xnc),
            ];
            for (acc, val) in a.x.iter_mut().zip(new) {
                *acc += wi * val;
            }
            for (acc, val) in
                a.e.iter_mut()
                    .zip([zr, zi, d_zr, d_zi, xw, d_xw, xnc, d_xnc])
            {
                *acc += wi * pw(val, val);
            }
            let fb = field_bounds(
                job,
                r,
                smp,
                v,
                [zr, zi, d_zr, d_zi, xw, d_xw, xnc, d_xnc, f, br, bi],
                (zc_re, zc_im),
            );
            for (acc, val) in a.rb.iter_mut().zip(fb) {
                *acc += wu * val;
            }
            a.epsmax = a.epsmax.max(smp.eps[r * NV + v]);
        }
        for (k, &(va, oa, vb, ob, _)) in PAIRS.iter().enumerate() {
            if !(psel[k] && job.on[va] && job.on[vb]) {
                continue;
            }
            let d = smp.vals[r * NV + va][oa] - smp.vals[r * NV + vb][ob];
            let ps = &mut rec.p[r][k];
            ps.d += wi * i128::from(d);
            ps.q += wi * ((i128::from(d) * i128::from(d)) >> Q);
            ps.d2 += wi * (i128::from(d) * i128::from(d));
            // the pair's bound: the two observables' bounds added
            let bd = smp.ob[r * NV + va].o[oa] + smp.ob[r * NV + vb].o[ob];
            let ad = uabs(d);
            ps.rb[0] += wu * bd;
            ps.rb[1] += wu * (cu(2 * ad, bd) + cu(bd, bd) + 1);
            ps.rb[2] += wu * (2 * ad * bd + bd * bd);
        }
    }
}

/// The per-sample bound of each of the NRB fields of a TWB row (RB_NAMES order): the observables' bounds, the linear
/// control's (two floors and its seeds' errors through C and RS; X_lin's three roundings and the propagation), and
/// 2|v| b + b^2 for squares, |v| b_w + |w| b_v + b_v b_w for products (at 2^80), plus 1 for each floored square.
fn field_bounds(
    job: &EnsJob,
    r: usize,
    smp: &Sample,
    v: usize,
    vals: [i64; 11],
    zc: (i64, i64),
) -> [u128; NRB] {
    let ob = smp.ob[r * NV + v];
    let (cc, rs, _) = job.ctrl[r];
    let du = smp.sb[v];
    let bzc = 2 + cu(uabs(cc), du) + cu(uabs(rs), du);
    let (zcr, zci) = (uabs(zc.0), uabs(zc.1));
    let bxc = 3 + cu(2 * zcr, bzc) + cu(2 * zci, bzc) + 2 * cu(bzc, bzc);
    let [zr, zi, dzr, dzi, xw, dxw, xnc, dxnc, f, br, bi] = vals.map(uabs);
    let (bzr, bzi, bxw, bxnc, bf) = (ob.o[OZR], ob.o[OZI], ob.o[OXW], ob.o[OXNC], ob.o[OF]);
    let (bdzr, bdzi, bdxw, bdxnc) = (bzr + bzc, bzi + bzc, bxw + bxc, bxnc + bxc);
    let (bbr, bbi) = (ob.o[OBR], ob.o[OBI]);
    let qb = |a: u128, b: u128| cu(2 * a, b) + cu(b, b) + 1;
    let sq = |a: u128, b: u128| 2 * a * b + b * b;
    let pr = |a: u128, ba: u128, c: u128, bc: u128| a * bc + c * ba + ba * bc;
    [
        bzr,
        bzi,
        bdzr,
        bdzi,
        bxw,
        bdxw,
        bxnc,
        bdxnc,
        bf,
        qb(dzr, bdzr),
        qb(dxw, bdxw),
        qb(dxnc, bdxnc),
        qb(zr, bzr),
        qb(xw, bxw),
        qb(xnc, bxnc),
        qb(dzi, bdzi),
        sq(f, bf),
        bbr,
        bbi,
        sq(br, bbr),
        sq(bi, bbi),
        pr(br, bbr, bi, bbi),
        pr(zr, bzr, xw, bxw),
        pr(zr, bzr, xnc, bxnc),
        pr(dzr, bdzr, dxw, bdxw),
        pr(dzr, bdzr, dxnc, bdxnc),
        sq(zr, bzr),
        sq(zi, bzi),
        sq(dzr, bdzr),
        sq(dzi, bdzi),
        sq(xw, bxw),
        sq(dxw, bdxw),
        sq(xnc, bxnc),
        sq(dxnc, bdxnc),
    ]
}

fn ens_chunk(job: &EnsJob, first: u64, count: u64) -> EnsRec {
    let nr = job.steps.len();
    let mut rec = EnsRec::new(nr);
    let mut smp = Sample::new(nr);
    for idx in first..first + count {
        ens_sample(job, idx, &mut smp);
        ens_accumulate(job, &smp, &mut rec);
    }
    rec
}

fn ens_run(job: &EnsJob, start: u64, count: u64, threads: u64) -> EnsRec {
    let mut total = EnsRec::new(job.steps.len());
    thread::scope(|sc| {
        let mut hs = Vec::new();
        for (first, c) in chunks(start, count, threads) {
            hs.push(sc.spawn(move || ens_chunk(job, first, c)));
        }
        for hh in hs {
            let part = hh.join().expect("thread");
            total.add(&part);
        }
    });
    total
}

// ---------------------------------------------------------------------------------------------------------------------
// Count-weighted reuse (memo=1, 0.4.0). A start is keyed by its integer noise values c_i = g_i / 2^35 (g_i is
// (popcount - 2048) << 35, so the shift is exact): K4 = (c0, c1, c2, c3) for VNC, V1, RN, FLIP; K2 = (c0, c1) for LOCK.
// Phase 1 draws each sample once (four Gaussians, or two for a LOCK-only batch, the same prefix of its stream; all six
// and MODE0's vector when a variant runs sample by sample) and counts its keys; phase 2 integrates each counted key once
// and adds its contributions times its count.

/// The memo's cores and the counts from which a class is memoised.
#[derive(Clone, Copy)]
struct MemoCfg {
    /// K4 core: the 4-ball c0^2 + c1^2 + c2^2 + c3^2 <= r * r, one byte per cell (295937937 cells at r = 88).
    r: i64,
    /// K2 core: the box |c0|, |c1| <= b2, one u64 per cell.
    b2: i64,
    /// K4 is memoised from this count up (below it each sample runs alone), K2 from k2_min up.
    k4_min: u64,
    k2_min: u64,
}

const MEMO: MemoCfg = MemoCfg {
    r: 88,
    b2: 255,
    k4_min: 1 << 22,
    k2_min: 1 << 10,
};

/// The 4-ball's cells in a dense index: for each row (c0, c1, c2) of the box [-r, r]^3, the index of its cell c3 = 0 and
/// its half-width hw (cells c3 in [-hw, hw]), or hw = -1 for a row outside the ball.
struct Ball {
    r: i64,
    w: usize,
    off: Vec<u32>,
    half: Vec<i16>,
    cells: usize,
}

impl Ball {
    fn new(r: i64) -> Self {
        let w = (2 * r + 1) as usize;
        let r2 = r * r;
        let mut off = vec![0u32; w * w * w];
        let mut half = vec![-1i16; w * w * w];
        let mut next: u64 = 0;
        for c0 in -r..=r {
            for c1 in -r..=r {
                for c2 in -r..=r {
                    let s = c0 * c0 + c1 * c1 + c2 * c2;
                    if s > r2 {
                        continue;
                    }
                    let hw = isqrt((r2 - s) as u128) as i64;
                    let i = Self::row_of(r, w, c0, c1, c2);
                    off[i] = u32::try_from(next + hw as u64).expect("ball index above u32");
                    half[i] = hw as i16;
                    next += (2 * hw + 1) as u64;
                }
            }
        }
        Self {
            r,
            w,
            off,
            half,
            cells: usize::try_from(next).expect("cells"),
        }
    }
    #[inline]
    fn row_of(r: i64, w: usize, c0: i64, c1: i64, c2: i64) -> usize {
        (((c0 + r) as usize * w) + (c1 + r) as usize) * w + (c2 + r) as usize
    }
    /// The cell of a key, or None outside the ball.
    #[inline]
    fn index(&self, c: [i64; 4]) -> Option<usize> {
        let r = self.r;
        if c[0].abs() > r || c[1].abs() > r || c[2].abs() > r {
            return None;
        }
        let i = Self::row_of(r, self.w, c[0], c[1], c[2]);
        let hw = i64::from(self.half[i]);
        if hw < 0 || c[3].abs() > hw {
            return None;
        }
        Some((i64::from(self.off[i]) + c[3]) as usize)
    }
}

/// One-byte counters shared by the threads: a wrap 255 -> 0 is recorded by the thread that made it, and each recorded
/// wrap carries 256 back in, so every count is exact.
struct Counter8 {
    c: Vec<AtomicU8>,
}

impl Counter8 {
    fn new(n: usize) -> Self {
        Self {
            c: (0..n).map(|_| AtomicU8::new(0)).collect(),
        }
    }
    /// Count one; true when this increment wrapped the cell (its true count gained 256 beyond the stored byte).
    #[inline]
    fn inc(&self, i: usize) -> bool {
        self.c[i].fetch_add(1, Ordering::Relaxed) == u8::MAX
    }
    #[inline]
    fn get(&self, i: usize, wraps: &HashMap<usize, u64>) -> u64 {
        u64::from(self.c[i].load(Ordering::Relaxed)) + 256 * wraps.get(&i).copied().unwrap_or(0)
    }
}

/// Which variants and pair rows run where in a memo batch.
struct MemoPlan {
    /// sample by sample: V0, MODE0, the variants that share an on pair row with them (closed under the pair rows),
    /// and a class whose count is below its threshold
    ps: [bool; NV],
    ps_pairs: [bool; NPAIR],
    /// memoised on K4, with the pair rows among them
    k4: [bool; NV],
    k4_pairs: [bool; NPAIR],
    k4_on: bool,
    /// memoised on K2 (LOCK)
    k2: [bool; NV],
    k2_on: bool,
}

const K4_VARIANTS: [usize; 4] = [VNC, V1, RN, FLIP];

fn memo_plan(job: &EnsJob, count: u64, cfg: &MemoCfg) -> MemoPlan {
    let on = job.on;
    let mut ps = [false; NV];
    ps[V0] = on[V0];
    ps[MODE0] = on[MODE0];
    // close under the on pair rows: a pair row is summed from both variants of one sample
    loop {
        let mut grew = false;
        for &(va, _, vb, _, _) in PAIRS.iter() {
            if on[va] && on[vb] && (ps[va] != ps[vb]) {
                ps[va] = true;
                ps[vb] = true;
                grew = true;
            }
        }
        if !grew {
            break;
        }
    }
    let mut k4 = [false; NV];
    for &v in K4_VARIANTS.iter() {
        k4[v] = on[v] && !ps[v];
    }
    let k4_on = k4.iter().any(|&b| b) && count >= cfg.k4_min;
    if !k4_on {
        for v in 0..NV {
            ps[v] |= k4[v];
            k4[v] = false;
        }
    }
    let mut k2 = [false; NV];
    k2[LOCK] = on[LOCK];
    let k2_on = on[LOCK] && count >= cfg.k2_min;
    if !k2_on {
        ps[LOCK] |= k2[LOCK];
        k2[LOCK] = false;
    }
    let mut ps_pairs = [false; NPAIR];
    let mut k4_pairs = [false; NPAIR];
    for (k, &(va, _, vb, _, _)) in PAIRS.iter().enumerate() {
        if !(on[va] && on[vb]) {
            continue;
        }
        if ps[va] && ps[vb] {
            ps_pairs[k] = true;
        } else if k4[va] && k4[vb] {
            k4_pairs[k] = true;
        } else {
            // a pair row split across two classes cannot be summed: the closure above rules it out
            eprintln!(
                "TWB_FAULT|reason=memo_pair_split|pair={}|json=0",
                PAIRS[k].4
            );
            std::process::exit(6);
        }
    }
    MemoPlan {
        ps,
        ps_pairs,
        k4,
        k4_pairs,
        k4_on,
        k2,
        k2_on,
    }
}

/// What a memo batch did, for the TWB_MEMO row.
#[derive(Default)]
struct MemoStats {
    k4_in_core: u64,
    k4_distinct: u64,
    k4_outside: u64,
    k4_wraps: u64,
    k2_in_core: u64,
    k2_distinct: u64,
    k2_outside: u64,
    ps_samples: u64,
    /// integrations (one variant, one start, to the last record) done, and the plain path's for the same batch
    integrations: u64,
    plain_integrations: u64,
}

#[inline]
fn key_c(g: i64) -> i64 {
    g >> (Q - 5)
}

/// Phase 1 for one contiguous chunk: draw, count the keys in the cores, integrate the rest one by one.
fn memo_phase1(
    job: &EnsJob,
    mp: &MemoPlan,
    cfg: &MemoCfg,
    cores: (Option<&Ball>, Option<&Counter8>, Option<&[AtomicU64]>),
    first: u64,
    count: u64,
) -> (EnsRec, Vec<usize>, [u64; 4]) {
    let (ball, c4, c2) = cores;
    let nr = job.steps.len();
    let mut rec = EnsRec::new(nr);
    let mut smp = Sample::new(nr);
    let mut wraps: Vec<usize> = Vec::new();
    let any_ps = mp.ps.iter().any(|&b| b);
    let ng = if mp.k4_on { 4 } else { 2 };
    let k2w = (2 * cfg.b2 + 1) as usize;
    let mut sel_lock = [false; NV];
    sel_lock[LOCK] = true;
    // [k4 outside the core, k2 outside the core, sample-by-sample samples, integrations]
    let mut tally = [0u64; 4];
    let nps = mp.ps.iter().filter(|&&b| b).count() as u64;
    let nk4 = mp.k4.iter().filter(|&&b| b).count() as u64;
    for idx in first..first + count {
        let g = if any_ps {
            let (g, r30) = ens_draw(job, idx);
            ens_build(job, g, r30, &mp.ps, &mut smp);
            ens_integrate(job, &mp.ps, &mut smp);
            ens_accumulate_w(job, &smp, &mut rec, 1, &mp.ps, &mp.ps_pairs);
            tally[2] += 1;
            tally[3] += nps;
            g
        } else if mp.k4_on || mp.k2_on {
            let mut rng = Rng::sample(job.seed, idx);
            let mut g = [0i64; 6];
            for x in g.iter_mut().take(ng) {
                *x = rng.gauss::<64, 5>();
            }
            g
        } else {
            [0i64; 6]
        };
        if mp.k4_on {
            let c = [key_c(g[0]), key_c(g[1]), key_c(g[2]), key_c(g[3])];
            match ball.and_then(|b| b.index(c)) {
                Some(i) => {
                    if c4.map(|ct| ct.inc(i)).unwrap_or(false) {
                        wraps.push(i);
                    }
                }
                None => {
                    ens_build(job, g, (ONE, 0, 0), &mp.k4, &mut smp);
                    ens_integrate(job, &mp.k4, &mut smp);
                    ens_accumulate_w(job, &smp, &mut rec, 1, &mp.k4, &mp.k4_pairs);
                    tally[0] += 1;
                    tally[3] += nk4;
                }
            }
        }
        if mp.k2_on {
            let (a, b) = (key_c(g[0]), key_c(g[1]));
            if a.abs() <= cfg.b2 && b.abs() <= cfg.b2 {
                let i = (a + cfg.b2) as usize * k2w + (b + cfg.b2) as usize;
                if let Some(ct) = c2 {
                    ct[i].fetch_add(1, Ordering::Relaxed);
                }
            } else {
                ens_build(job, g, (ONE, 0, 0), &sel_lock, &mut smp);
                ens_integrate(job, &sel_lock, &mut smp);
                ens_accumulate_w(job, &smp, &mut rec, 1, &sel_lock, &[false; NPAIR]);
                tally[1] += 1;
                tally[3] += 1;
            }
        }
    }
    (rec, wraps, tally)
}

/// Phase 2 for one unit of work: K4 unit u < 2r + 1 is the slab c0 = u - r of the ball; K2 unit is the row c0 of the
/// box. Each counted key is built from its c values (g4 = g5 = 0 and MODE0's vector (1, 0): read by no memoised
/// variant), integrated once and added count times.
struct Phase2<'a> {
    job: &'a EnsJob,
    mp: &'a MemoPlan,
    cfg: &'a MemoCfg,
    ball: Option<&'a Ball>,
    c4: Option<&'a Counter8>,
    wraps: &'a HashMap<usize, u64>,
    c2: Option<&'a [AtomicU64]>,
}

impl Phase2<'_> {
    /// Returns (sum of counts, distinct keys, integrations) of the unit into rec.
    fn unit(&self, u: usize, rec: &mut EnsRec, smp: &mut Sample) -> (u64, u64, u64) {
        let (job, mp) = (self.job, self.mp);
        let mut tot = (0u64, 0u64, 0u64);
        let nk4 = mp.k4.iter().filter(|&&b| b).count() as u64;
        let units4 = match self.ball {
            Some(b) if mp.k4_on => (2 * b.r + 1) as usize,
            _ => 0,
        };
        if u < units4 {
            let (b, ct) = match (self.ball, self.c4) {
                (Some(b), Some(ct)) => (b, ct),
                _ => return tot,
            };
            let r = b.r;
            let c0 = u as i64 - r;
            for c1 in -r..=r {
                for c2 in -r..=r {
                    let i = Ball::row_of(r, b.w, c0, c1, c2);
                    let hw = i64::from(b.half[i]);
                    for c3 in -hw..=hw {
                        let cell = (i64::from(b.off[i]) + c3) as usize;
                        let w = ct.get(cell, self.wraps);
                        if w == 0 {
                            continue;
                        }
                        let s = Q - 5;
                        let g = [c0 << s, c1 << s, c2 << s, c3 << s, 0, 0];
                        ens_build(job, g, (ONE, 0, 0), &mp.k4, smp);
                        ens_integrate(job, &mp.k4, smp);
                        ens_accumulate_w(job, smp, rec, w, &mp.k4, &mp.k4_pairs);
                        tot.0 += w;
                        tot.1 += 1;
                        tot.2 += nk4;
                    }
                }
            }
            return tot;
        }
        let Some(ct) = self.c2 else {
            return tot;
        };
        if !mp.k2_on {
            return tot;
        }
        let b2 = self.cfg.b2;
        let k2w = (2 * b2 + 1) as usize;
        let row = u - units4;
        let a = row as i64 - b2;
        let mut sel_lock = [false; NV];
        sel_lock[LOCK] = true;
        for bb in -b2..=b2 {
            let w = ct[row * k2w + (bb + b2) as usize].load(Ordering::Relaxed);
            if w == 0 {
                continue;
            }
            let s = Q - 5;
            let g = [a << s, bb << s, 0, 0, 0, 0];
            ens_build(job, g, (ONE, 0, 0), &sel_lock, smp);
            ens_integrate(job, &sel_lock, smp);
            ens_accumulate_w(job, smp, rec, w, &sel_lock, &[false; NPAIR]);
            tot.0 += w;
            tot.1 += 1;
            tot.2 += 1;
        }
        tot
    }
}

/// The batch [start, start + count) with count-weighted reuse: the same sums as ens_run.
fn ens_run_memo(
    job: &EnsJob,
    start: u64,
    count: u64,
    threads: u64,
    cfg: &MemoCfg,
) -> (EnsRec, MemoStats) {
    let nr = job.steps.len();
    let mp = memo_plan(job, count, cfg);
    let ball = if mp.k4_on {
        Some(Ball::new(cfg.r))
    } else {
        None
    };
    let c4 = ball.as_ref().map(|b| Counter8::new(b.cells));
    let k2w = (2 * cfg.b2 + 1) as usize;
    let c2: Option<Vec<AtomicU64>> = if mp.k2_on {
        Some((0..k2w * k2w).map(|_| AtomicU64::new(0)).collect())
    } else {
        None
    };
    let mut total = EnsRec::new(nr);
    let mut st = MemoStats::default();
    let mut wrap_list: Vec<usize> = Vec::new();
    let mut tally = [0u64; 4];
    thread::scope(|sc| {
        let mut hs = Vec::new();
        for (first, c) in chunks(start, count, threads) {
            let (mpr, b, ct4, ct2) = (&mp, ball.as_ref(), c4.as_ref(), c2.as_deref());
            hs.push(sc.spawn(move || memo_phase1(job, mpr, cfg, (b, ct4, ct2), first, c)));
        }
        for hh in hs {
            let (part, wr, t) = hh.join().expect("thread");
            total.add(&part);
            wrap_list.extend(wr);
            for (x, y) in tally.iter_mut().zip(t) {
                *x += y;
            }
        }
    });
    let mut wraps: HashMap<usize, u64> = HashMap::new();
    for i in wrap_list {
        *wraps.entry(i).or_insert(0) += 1;
    }
    st.k4_wraps = wraps.values().sum();
    st.k4_outside = tally[0];
    st.k2_outside = tally[1];
    st.ps_samples = tally[2];
    st.integrations = tally[3];
    let units4 = if mp.k4_on {
        (2 * cfg.r + 1) as usize
    } else {
        0
    };
    let units2 = if mp.k2_on { k2w } else { 0 };
    let units = units4 + units2;
    let next = AtomicUsize::new(0);
    let p2 = Phase2 {
        job,
        mp: &mp,
        cfg,
        ball: ball.as_ref(),
        c4: c4.as_ref(),
        wraps: &wraps,
        c2: c2.as_deref(),
    };
    // [k4 counts, k4 distinct, k2 counts, k2 distinct, integrations]
    let mut t2 = [0u64; 5];
    thread::scope(|sc| {
        let mut hs = Vec::new();
        for _ in 0..threads {
            let (p2r, nx) = (&p2, &next);
            hs.push(sc.spawn(move || {
                let mut rec = EnsRec::new(nr);
                let mut smp = Sample::new(nr);
                let mut t = [0u64; 5];
                loop {
                    let u = nx.fetch_add(1, Ordering::Relaxed);
                    if u >= units {
                        break;
                    }
                    let (w, d, k) = p2r.unit(u, &mut rec, &mut smp);
                    let o = if u < units4 { 0 } else { 2 };
                    t[o] += w;
                    t[o + 1] += d;
                    t[4] += k;
                }
                (rec, t)
            }));
        }
        for hh in hs {
            let (part, t) = hh.join().expect("thread");
            total.add(&part);
            for (x, y) in t2.iter_mut().zip(t) {
                *x += y;
            }
        }
    });
    st.k4_in_core = t2[0];
    st.k4_distinct = t2[1];
    st.k2_in_core = t2[2];
    st.k2_distinct = t2[3];
    st.integrations += t2[4];
    st.plain_integrations = count * job.on.iter().filter(|&&b| b).count() as u64;
    // every sample is counted once in each class it belongs to; any other total stops the run (fail closed)
    let ok_ps = !mp.ps.iter().any(|&b| b) || st.ps_samples == count;
    let ok4 = !mp.k4_on || st.k4_in_core + st.k4_outside == count;
    let ok2 = !mp.k2_on || st.k2_in_core + st.k2_outside == count;
    if !(ok_ps && ok4 && ok2) {
        eprintln!(
            "TWB_FAULT|reason=memo_count_check|count={count}|ps={}|k4={}+{}|k2={}+{}|json=0",
            st.ps_samples, st.k4_in_core, st.k4_outside, st.k2_in_core, st.k2_outside
        );
        std::process::exit(6);
    }
    total.count = i128::from(count);
    (total, st)
}

fn sel_text(sel: &[bool; NV]) -> String {
    let v: Vec<&str> = (0..NV).filter(|&i| sel[i]).map(|i| VNAME[i]).collect();
    if v.is_empty() {
        "none".to_string()
    } else {
        v.join(",")
    }
}

/// The memo batch's counts on stderr (stdout stays the plain path's).
fn memo_report(job: &EnsJob, count: u64, st: &MemoStats, cfg: &MemoCfg) {
    let mp = memo_plan(job, count, cfg);
    eprintln!(
        "TWB_MEMO|count={count}|per_sample={}|k4={}|k4_core=ball_r{}|k4_in_core={}|k4_distinct={}|k4_outside={}|k4_wraps={}|k2={}|k2_core=box_{}|k2_in_core={}|k2_distinct={}|k2_outside={}|ps_samples={}|integrations={}|plain_integrations={}|json=0",
        sel_text(&mp.ps),
        sel_text(&mp.k4),
        cfg.r,
        st.k4_in_core,
        st.k4_distinct,
        st.k4_outside,
        st.k4_wraps,
        sel_text(&mp.k2),
        cfg.b2,
        st.k2_in_core,
        st.k2_distinct,
        st.k2_outside,
        st.ps_samples,
        st.integrations,
        st.plain_integrations
    );
}

/// What the rows print besides the sums.
struct Meta {
    cli: &'static str,
    delta: String,
    u: String,
    y: String,
    seed_string: String,
    start: u64,
    count: u64,
    samples: u64,
    threads: u64,
    reserved: bool,
    lifted: bool,
    /// count-weighted reuse (memo=1)
    memo: bool,
}

fn binary_sha256() -> String {
    match env::current_exe().and_then(std::fs::read) {
        Ok(b) => sha256::hex(&sha256::sha256(&b)),
        Err(_) => "CANNOT_SEE".to_string(),
    }
}

fn mask_text(on: &[bool; NV], nl: bool) -> String {
    let mut v: Vec<&str> = (0..NV).filter(|&i| on[i]).map(|i| VNAME[i]).collect();
    if nl {
        v.push("NL");
    }
    v.join(",")
}

fn ens_head(out: &mut impl Write, job: &EnsJob, mt: &Meta) -> std::io::Result<()> {
    let steps: Vec<String> = job.steps.iter().map(|s| s.to_string()).collect();
    writeln!(
        out,
        "TWB_HEAD|engine=twens|version={VERSION}|cli={}|binary_sha256={}|source_sha256={}|N={}|delta={}|u={}|y={}|seed={}|seed_string={}|start={}|count={}|samples={}|dtden={}|threads={}|steps={}|mask={}|reserved={}|guard={}|q=40|sums=plain_at_2^40,q_sum_of_floor(v*v/2^40),products_exact_at_2^80|rounding=per-sample_bound_summed_in_TWB_ROUND_and_TWB_PAIR_ROUND|float_used=0|json=0",
        mt.cli,
        binary_sha256(),
        source_sha256(),
        job.n,
        mt.delta,
        mt.u,
        mt.y,
        job.seed,
        mt.seed_string,
        mt.start,
        mt.count,
        mt.samples,
        job.dtden,
        mt.threads,
        steps.join(","),
        mask_text(&job.on, job.nl),
        u8::from(mt.reserved),
        if mt.lifted { "lifted" } else { "active" }
    )
}

fn ens_rows(
    out: &mut impl Write,
    job: &EnsJob,
    mt: &Meta,
    total: &EnsRec,
    nl: Option<&NlRec>,
) -> std::io::Result<()> {
    for r in 0..job.steps.len() {
        let (c0, c1, c2) = job.ctrl[r];
        // The old engine's rows, byte for byte in its format and order.
        for &(v, name) in LEGACY.iter() {
            if !job.on[v] {
                continue;
            }
            let s = total.v[r][v].s;
            let q = total.v[r][v].q;
            writeln!(
                out,
                "TWENS|N={}|delta={}|u={}|y={}|samples={}|seed={}|dtden={}|step={}|variant={}|n={}|h={}|ctrl={}:{}:{}|zr={}|zi={}|dzr={}|dzi={}|xw={}|dxw={}|xnc={}|dxnc={}|f={}|qdzr={}|qdxw={}|qdxnc={}|qzr={}|qxw={}|qxnc={}|qdzi={}|float_used=0|json=0",
                job.n, mt.delta, mt.u, mt.y, mt.samples, job.seed, job.dtden, job.steps[r], name, total.count, job.h,
                c0, c1, c2,
                s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8],
                q[0], q[1], q[2], q[3], q[4], q[5], q[6]
            )?;
        }
        if job.on[V1] && job.on[VNC] && job.on[V0] {
            let p = &total.p[r];
            writeln!(
                out,
                "TWPAIR|N={}|delta={}|y={}|samples={}|step={}|n={}|v1xw_vnxnc={}|q0={}|v1zr_vnzr={}|q1={}|v0xw_v1xw={}|q2={}|v0zr_v1zr={}|q3={}|v1xw_vnxw={}|q4={}|float_used=0|json=0",
                job.n, mt.delta, mt.y, mt.samples, job.steps[r], total.count, p[0].d, p[0].q, p[1].d, p[1].q, p[2].d, p[2].q, p[3].d, p[3].q, p[4].d, p[4].q
            )?;
        }
        // The new rows: every sum of every variant that is on.
        for v in 0..NV {
            if !job.on[v] {
                continue;
            }
            let a = &total.v[r][v];
            let (s, q, x, e) = (a.s, a.q, a.x, a.e);
            writeln!(
                out,
                "TWB|N={}|delta={}|u={}|y={}|seed={}|start={}|count={}|dtden={}|step={}|variant={}|init={}|seeds={}|kappa={}|phase={}|n={}|h={}|ctrl={}:{}:{}|zr={}|zi={}|dzr={}|dzi={}|xw={}|dxw={}|xnc={}|dxnc={}|f={}|qdzr={}|qdxw={}|qdxnc={}|qzr={}|qxw={}|qxnc={}|qdzi={}|f2={}|br={}|bi={}|br2={}|bi2={}|brbi={}|zrxw={}|zrxnc={}|dzrdxw={}|dzrdxnc={}|zr2={}|zi2={}|dzr2={}|dzi2={}|xw2={}|dxw2={}|xnc2={}|dxnc2={}|float_used=0|json=0",
                job.n, mt.delta, mt.u, mt.y, job.seed, mt.start, mt.count, job.dtden, job.steps[r], VNAME[v], VINIT[v], VSEEDS[v], VKAPPA[v], VPHASE[v],
                total.count, job.h, c0, c1, c2,
                s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8],
                q[0], q[1], q[2], q[3], q[4], q[5], q[6],
                x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9],
                e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7]
            )?;
            let rb: Vec<String> = RB_NAMES
                .iter()
                .zip(a.rb.iter())
                .map(|(nm, b)| format!("rb_{nm}={b}"))
                .collect();
            writeln!(
                out,
                "TWB_ROUND|N={}|delta={}|y={}|seed={}|start={}|count={}|dtden={}|step={}|variant={}|n={}|{}|eps_max={}|units=ulps_of_each_field(sums_2^-40,squares_and_products_2^-80)|float_used=0|json=0",
                job.n, mt.delta, mt.y, job.seed, mt.start, mt.count, job.dtden, job.steps[r], VNAME[v], total.count, rb.join("|"), a.epsmax
            )?;
        }
        for (k, &(va, _, vb, _, name)) in PAIRS.iter().enumerate() {
            if !(job.on[va] && job.on[vb]) {
                continue;
            }
            let ps = &total.p[r][k];
            writeln!(
                out,
                "TWB_PAIR|N={}|delta={}|y={}|seed={}|start={}|count={}|dtden={}|step={}|pair={}|n={}|d={}|qd={}|d2={}|float_used=0|json=0",
                job.n, mt.delta, mt.y, job.seed, mt.start, mt.count, job.dtden, job.steps[r], name, total.count, ps.d, ps.q, ps.d2
            )?;
            writeln!(
                out,
                "TWB_PAIR_ROUND|N={}|delta={}|y={}|seed={}|start={}|count={}|dtden={}|step={}|pair={}|n={}|rb_d={}|rb_qd={}|rb_d2={}|float_used=0|json=0",
                job.n, mt.delta, mt.y, job.seed, mt.start, mt.count, job.dtden, job.steps[r], name, total.count, ps.rb[0], ps.rb[1], ps.rb[2]
            )?;
        }
        if let Some(nl) = nl {
            let [zr, zi, xw, xnc, f, br, bi] = nl.vals[r];
            let s = nl.states[r];
            let z2 = m(zr, zr) + m(zi, zi);
            let fcl = m(s[2], s[2]) + m(s[3], s[3]) + m(s[4], s[4]) + m(s[5], s[5]);
            let b = nl.ob[r];
            writeln!(
                out,
                "TWB_NL|N={}|delta={}|u={}|y={}|dtden={}|step={}|init=c0=sqrt(N),c+-=0|kappa=1|zr={zr}|zi={zi}|z2={z2}|xw={xw}|xnc={xnc}|f={f}|fcl={fcl}|br={br}|bi={bi}|rb_zr={}|rb_zi={}|rb_z2={}|rb_xw={}|rb_xnc={}|rb_f={}|rb_fcl={}|rb_br={}|rb_bi={}|eps={}|reads=trajectory_frame:A1=2abs(Z),C1=2N*abs(Z)^2/(N-1),f=fcl,D2=2abs(B);ensemble_frames:C1_NC=2N*xnc/(N-1),C1_W=2N*xw/(N-1),f_W=f=fcl-1/N|at=2^40|float_used=0|json=0",
                job.n, mt.delta, mt.u, mt.y, job.dtden, job.steps[r],
                b.o[OZR], b.o[OZI], b.z2, b.o[OXW], b.o[OXNC], b.o[OF], b.fcl, b.o[OBR], b.o[OBI], nl.eps[r]
            )?;
        }
    }
    Ok(())
}

fn ens_done(out: &mut impl Write, job: &EnsJob, total: &EnsRec) -> std::io::Result<()> {
    writeln!(
        out,
        "TWB_DONE|n={}|records={}|mask={}|float_used=0|json=0",
        total.count,
        job.steps.len(),
        mask_text(&job.on, job.nl)
    )
}

// ---------------------------------------------------------------------------------------------------------------------
// The twctl family: the controls lane's engine, byte for byte.

#[derive(Clone, Copy, PartialEq)]
enum Seed {
    Vac,
    NoNoise,
    Lock0,
}

#[derive(Clone, Default)]
struct Acc {
    zr: i128,
    zi: i128,
    zr2: i128,
    zi2: i128,
    c: i128,
    c2: i128,
    zrc: i128,
    f: i128,
    r2: i128,
    f2: i128,
    count: i128,
}

impl Acc {
    fn add(&mut self, o: &Acc) {
        self.zr += o.zr;
        self.zi += o.zi;
        self.zr2 += o.zr2;
        self.zi2 += o.zi2;
        self.c += o.c;
        self.c2 += o.c2;
        self.zrc += o.zrc;
        self.f += o.f;
        self.r2 += o.r2;
        self.f2 += o.f2;
        self.count += o.count;
    }
}

struct CtlJob {
    n: i128,
    par: Par,
    dtden: i64,
    steps: Vec<usize>,
    seed: u64,
    mode: Seed,
    random_phase: bool,
    fine_phase: bool,
}

fn ctl_chunk(job: &CtlJob, first: u64, count: u64) -> Vec<Acc> {
    let mut accs = vec![Acc::default(); job.steps.len()];
    let one: i128 = 1i128 << Q;
    let inv_sqrt = isqrt(((one * one) / job.n) as u128) as i64; // 1/sqrt(N)
    let half_inv = inv_sqrt / 2;
    let psi0 = isqrt((((2 * job.n + 1) * one * one) / (2 * job.n)) as u128) as i64; // sqrt((N+1/2)/N)
    let inv_n = (one / job.n) as i64;
    let half_inv_n2 = (one / (2 * job.n * job.n)) as i64;
    let last = *job.steps.last().unwrap_or(&0);
    for traj in first..(first + count) {
        let mut rng = Rng::sample(job.seed, traj);
        let (g1, g2, g3, g4) = (
            rng.gauss::<1024, 7>(),
            rng.gauss::<1024, 7>(),
            rng.gauss::<1024, 7>(),
            rng.gauss::<1024, 7>(),
        );
        let [rp, ip, rm, im] = match job.mode {
            Seed::Vac => [
                m(g1, half_inv),
                m(g2, half_inv),
                m(g3, half_inv),
                m(g4, half_inv),
            ],
            Seed::NoNoise => [0, 0, 0, 0],
            Seed::Lock0 => lock_seeds(m(g1, half_inv), m(g2, half_inv)),
        };
        let mut s: St = [psi0, 0, rp, ip, rm, im];
        if job.random_phase {
            // a separate stream for the phase, so the fixed and random runs share every Gaussian
            let mut prng = Rng::new(job.seed ^ PHASE_XOR ^ traj.wrapping_mul(PHASE_MUL));
            let (c, sn) = if job.fine_phase {
                prng.unit30()
            } else {
                prng.unit()
            };
            s = rot(&s, c, sn);
        }
        let mut next_rec = 0usize;
        for step in 0..=last {
            while next_rec < job.steps.len() && job.steps[next_rec] == step {
                let [r0, i0, rp, ip, rm, im] = s;
                let zr = m(r0, rp) + m(i0, ip) + m(rm, r0) + m(im, i0);
                let zi = m(r0, ip) - m(i0, rp) + m(rm, i0) - m(im, r0);
                let abs0 = m(r0, r0) + m(i0, i0);
                let absp = m(rp, rp) + m(ip, ip);
                let absm = m(rm, rm) + m(im, im);
                let r2 = m(zr, zr) + m(zi, zi);
                let fcl = absp + absm;
                let c = r2 - m(abs0, inv_n) - m(fcl, inv_n) / 2 + half_inv_n2;
                let a = &mut accs[next_rec];
                a.zr += i128::from(zr);
                a.zi += i128::from(zi);
                a.zr2 += i128::from(zr) * i128::from(zr);
                a.zi2 += i128::from(zi) * i128::from(zi);
                a.c += i128::from(c);
                a.c2 += i128::from(c) * i128::from(c);
                a.zrc += i128::from(zr) * i128::from(c);
                a.f += i128::from(fcl);
                a.r2 += i128::from(r2);
                a.f2 += i128::from(fcl) * i128::from(fcl);
                a.count += 1;
                next_rec += 1;
            }
            if step < last {
                s = rk4(&s, &job.par, job.dtden);
            }
        }
    }
    accs
}

// ---------------------------------------------------------------------------------------------------------------------
// The command line.

fn fail(msg: &str) -> ! {
    eprintln!("TWB_ERROR|{msg}|json=0");
    std::process::exit(2);
}

fn refuse(n: i64, delta: &str, y: &str, reason: &str) -> ! {
    eprintln!(
        "TWB_REFUSED|reason={reason}|N={n}|delta={delta}|y={y}|guard=active|computed=0|json=0"
    );
    std::process::exit(3);
}

fn num<T: std::str::FromStr>(s: &str, what: &str) -> T {
    s.parse::<T>()
        .unwrap_or_else(|_| fail(&format!("bad_{what}:{s}")))
}

fn rat_text(s: &str, what: &str) -> String {
    if let Err(e) = parse_rat(s) {
        fail(&format!("bad_{what}:{e}"));
    }
    s.to_string()
}

fn parse_steps(s: &str) -> Vec<usize> {
    let steps: Vec<usize> = s.split(',').map(|x| num::<usize>(x, "step")).collect();
    if steps.is_empty() || steps.windows(2).any(|w| w[0] > w[1]) {
        fail("steps_must_be_nondecreasing");
    }
    steps
}

fn parse_ctrl(s: &str) -> Vec<(i64, i64, i64)> {
    s.split(';')
        .map(|t| {
            let v: Vec<i64> = t.split(':').map(|x| num::<i64>(x, "ctrl")).collect();
            if v.len() != 3 {
                fail("ctrl_needs_C:RS:mz");
            }
            (v[0], v[1], v[2])
        })
        .collect()
}

/// The variant mask: any of the seven sampled variants, and NL, the noiseless trajectory computed once per batch.
fn parse_mask(s: &str) -> ([bool; NV], bool) {
    let mut on = [false; NV];
    let mut nl = false;
    for name in s.split(',') {
        if name == "NL" {
            if nl {
                fail("mask_repeats:NL");
            }
            nl = true;
            continue;
        }
        match VNAME.iter().position(|&v| v == name) {
            Some(i) if !on[i] => on[i] = true,
            Some(_) => fail(&format!("mask_repeats:{name}")),
            None => fail(&format!("mask_unknown:{name}")),
        }
    }
    (on, nl)
}

/// key=value arguments, each key at most once and from `known`.
fn kv(args: &[String], known: &[&str]) -> Vec<(String, String)> {
    let mut out: Vec<(String, String)> = Vec::new();
    for a in args {
        let Some((k, v)) = a.split_once('=') else {
            fail(&format!("not_key=value:{a}"))
        };
        if !known.contains(&k) {
            fail(&format!("unknown_key:{k}"));
        }
        if out.iter().any(|(kk, _)| kk == k) {
            fail(&format!("repeated_key:{k}"));
        }
        out.push((k.to_string(), v.to_string()));
    }
    out
}

fn get<'a>(p: &'a [(String, String)], k: &str) -> Option<&'a str> {
    p.iter().find(|(kk, _)| kk == k).map(|(_, v)| v.as_str())
}

fn need<'a>(p: &'a [(String, String)], k: &str) -> &'a str {
    get(p, k).unwrap_or_else(|| fail(&format!("missing_key:{k}")))
}

const RUN_KEYS: [&str; 15] = [
    "N",
    "delta",
    "u",
    "y",
    "seed",
    "seed_string",
    "start",
    "count",
    "dtden",
    "threads",
    "steps",
    "ctrl",
    "mask",
    "lift_reserved_guard",
    "memo",
];

/// Parse a run or dump batch, apply the guard before anything is computed, and build the job.
fn ens_from_kv(args: &[String], cli: &'static str) -> (EnsJob, Meta, u64) {
    let p = kv(args, &RUN_KEYS);
    let n: i64 = num(need(&p, "N"), "N");
    if n < 2 {
        fail("N_below_2");
    }
    let delta = rat_text(need(&p, "delta"), "delta");
    let u = rat_text(need(&p, "u"), "u");
    let y = rat_text(need(&p, "y"), "y");
    let lifted = match get(&p, "lift_reserved_guard") {
        None => false,
        Some("1") => true,
        Some(v) => fail(&format!("lift_reserved_guard_takes_1_only:{v}")),
    };
    let memo = match get(&p, "memo") {
        None | Some("0") => false,
        Some("1") => true,
        Some(v) => fail(&format!("memo_takes_0_or_1:{v}")),
    };
    let reason = guard_reason(n, &delta, &y);
    if let Some(r) = &reason {
        if !lifted {
            refuse(n, &delta, &y, r);
        }
    }
    let (seed, seed_string) = match (get(&p, "seed"), get(&p, "seed_string")) {
        (Some(s), None) => (num::<u64>(s, "seed"), "none".to_string()),
        (None, Some(s)) => {
            if s.is_empty() || s.contains(['|', '\n', '\r']) {
                fail("seed_string_empty_or_has_a_separator");
            }
            (sha256::seed_u64(s), s.to_string())
        }
        _ => fail("give_exactly_one_of_seed_or_seed_string"),
    };
    let start: u64 = num(need(&p, "start"), "start");
    let count: u64 = num(need(&p, "count"), "count");
    if start.checked_add(count).is_none() {
        fail("start_plus_count_overflows");
    }
    let dtden: i64 = num(need(&p, "dtden"), "dtden");
    let threads: u64 = num(need(&p, "threads"), "threads");
    if dtden < 1 || !(1..=256).contains(&threads) {
        fail("dtden_or_threads_out_of_range");
    }
    let steps = parse_steps(need(&p, "steps"));
    let ctrl = parse_ctrl(need(&p, "ctrl"));
    if steps.len() != ctrl.len() {
        fail("one_ctrl_per_record");
    }
    let (on, nl) = parse_mask(need(&p, "mask"));
    let mut job = EnsJob::new(n, &delta, &u, &y, dtden, steps, ctrl);
    job.seed = seed;
    job.on = on;
    job.nl = nl;
    let mt = Meta {
        cli,
        delta,
        u,
        y,
        seed_string,
        start,
        count,
        samples: count,
        threads,
        reserved: reason.is_some(),
        lifted,
        memo,
    };
    (job, mt, threads)
}

fn cmd_run(args: &[String]) {
    let (job, mt, threads) = ens_from_kv(args, "run");
    let total = if mt.memo {
        let (t, st) = ens_run_memo(&job, mt.start, mt.count, threads, &MEMO);
        memo_report(&job, mt.count, &st, &MEMO);
        t
    } else {
        ens_run(&job, mt.start, mt.count, threads)
    };
    let nl = if job.nl { Some(nl_run(&job)) } else { None };
    let stdout = std::io::stdout();
    let mut out = std::io::BufWriter::new(stdout.lock());
    let r = ens_head(&mut out, &job, &mt)
        .and_then(|_| ens_rows(&mut out, &job, &mt, &total, nl.as_ref()))
        .and_then(|_| ens_done(&mut out, &job, &total))
        .and_then(|_| out.flush());
    if r.is_err() {
        std::process::exit(5);
    }
}

/// The same batch on one thread, printing every sample's draws, starts, controls and observables (for the tests).
fn cmd_dump(args: &[String]) {
    let (job, mt, _) = ens_from_kv(args, "dump");
    if mt.memo {
        fail("memo_is_for_run_and_twens");
    }
    if mt.count > 4096 {
        fail("dump_count_above_4096");
    }
    let stdout = std::io::stdout();
    let mut out = std::io::BufWriter::new(stdout.lock());
    let nr = job.steps.len();
    let mut total = EnsRec::new(nr);
    let mut smp = Sample::new(nr);
    let mut lines: Vec<String> = Vec::new();
    for idx in mt.start..mt.start + mt.count {
        ens_sample(&job, idx, &mut smp);
        let g = smp.g;
        lines.push(format!(
            "TWB_DUMP_SAMPLE|idx={idx}|g={}:{}:{}:{}:{}:{}|rot={}:{}|json=0",
            g[0], g[1], g[2], g[3], g[4], g[5], smp.rot.0, smp.rot.1
        ));
        for (v, &is_on) in job.on.iter().enumerate() {
            if !is_on {
                continue;
            }
            let s = smp.init[v];
            let u = smp.uv[v];
            lines.push(format!(
                "TWB_DUMP_INIT|idx={idx}|variant={}|s={}:{}:{}:{}:{}:{}|uv={}:{}:{}:{}|json=0",
                VNAME[v], s[0], s[1], s[2], s[3], s[4], s[5], u[0], u[1], u[2], u[3]
            ));
            let ib = smp.ib[v];
            lines.push(format!(
                "TWB_DUMP_IB|idx={idx}|variant={}|e0={}|ep={}|em={}|seeds={}|eta={}|json=0",
                VNAME[v], ib[0], ib[1], ib[2], smp.sb[v], smp.eta
            ));
            for r in 0..nr {
                let o = smp.vals[r * NV + v];
                let (zc_re, zc_im, xc) = lin(&job, r, &smp.uv[v]);
                lines.push(format!(
                    "TWB_DUMP_OBS|idx={idx}|variant={}|step={}|zr={}|zi={}|xw={}|xnc={}|f={}|br={}|bi={}|zcr={zc_re}|zci={zc_im}|xc={xc}|json=0",
                    VNAME[v], job.steps[r], o[0], o[1], o[2], o[3], o[4], o[5], o[6]
                ));
                let b = smp.ob[r * NV + v];
                lines.push(format!(
                    "TWB_DUMP_RB|idx={idx}|variant={}|step={}|eps={}|b_zr={}|b_zi={}|b_xw={}|b_xnc={}|b_f={}|b_br={}|b_bi={}|b_z2={}|b_fcl={}|json=0",
                    VNAME[v], job.steps[r], smp.eps[r * NV + v], b.o[0], b.o[1], b.o[2], b.o[3], b.o[4], b.o[5], b.o[6], b.z2, b.fcl
                ));
            }
        }
        ens_accumulate(&job, &smp, &mut total);
    }
    let mut r = ens_head(&mut out, &job, &mt);
    for ln in &lines {
        r = r.and_then(|_| writeln!(out, "{ln}"));
    }
    let nl = if job.nl { Some(nl_run(&job)) } else { None };
    let r = r
        .and_then(|_| ens_rows(&mut out, &job, &mt, &total, nl.as_ref()))
        .and_then(|_| ens_done(&mut out, &job, &total))
        .and_then(|_| out.flush());
    if r.is_err() {
        std::process::exit(5);
    }
}

/// twens N delta u y samples seed dtden threads steps(k1,k2,..) ctrl(C:RS:mz;...) [memo=1]: the old engine's arguments; every
/// variant on, start index 0, count = floor(samples/threads)*threads as the old engine processed; the guard is not liftable.
fn cmd_twens(a: &[String]) {
    let memo = a.len() == 11 && a[10] == "memo=1";
    if a.len() != 10 && !memo {
        fail("usage:twens_N_delta_u_y_samples_seed_dtden_threads_steps_ctrl");
    }
    let n: i64 = num(&a[0], "N");
    if n < 2 {
        fail("N_below_2");
    }
    let delta = rat_text(&a[1], "delta");
    let u = rat_text(&a[2], "u");
    let y = rat_text(&a[3], "y");
    if let Some(r) = guard_reason(n, &delta, &y) {
        refuse(n, &delta, &y, &r);
    }
    let samples: u64 = num(&a[4], "samples");
    let seed: u64 = num(&a[5], "seed");
    let dtden: i64 = num(&a[6], "dtden");
    let threads: u64 = num(&a[7], "threads");
    if dtden < 1 || !(1..=256).contains(&threads) {
        fail("dtden_or_threads_out_of_range");
    }
    let steps = parse_steps(&a[8]);
    let ctrl = parse_ctrl(&a[9]);
    if steps.len() != ctrl.len() {
        fail("one_ctrl_per_record");
    }
    let mut job = EnsJob::new(n, &delta, &u, &y, dtden, steps, ctrl);
    job.seed = seed;
    let count = (samples / threads) * threads;
    let mt = Meta {
        cli: "twens",
        delta,
        u,
        y,
        seed_string: "none".to_string(),
        start: 0,
        count,
        samples,
        threads,
        reserved: false,
        lifted: false,
        memo,
    };
    let total = if memo {
        let (t, st) = ens_run_memo(&job, 0, count, threads, &MEMO);
        memo_report(&job, count, &st, &MEMO);
        t
    } else {
        ens_run(&job, 0, count, threads)
    };
    let stdout = std::io::stdout();
    let mut out = std::io::BufWriter::new(stdout.lock());
    let r = ens_head(&mut out, &job, &mt)
        .and_then(|_| ens_rows(&mut out, &job, &mt, &total, None))
        .and_then(|_| ens_done(&mut out, &job, &total))
        .and_then(|_| out.flush());
    if r.is_err() {
        std::process::exit(5);
    }
}

/// twctl N delta u y kappa vac|none|lock0 fixed|random|random30 samples seed dtden threads k1,k2,...: the controls lane's
/// engine and its TWCTL rows; the guard is not liftable.
fn cmd_twctl(a: &[String]) {
    if a.len() != 12 {
        fail("usage:twctl_N_delta_u_y_kappa_seedmode_phase_samples_seed_dtden_threads_steps");
    }
    let n: i128 = num(&a[0], "N");
    if !(2..=i128::from(i64::MAX)).contains(&n) {
        fail("N_out_of_range");
    }
    let delta = rat_text(&a[1], "delta");
    let u = rat_text(&a[2], "u");
    let y = rat_text(&a[3], "y");
    if let Some(r) = guard_reason(n as i64, &delta, &y) {
        refuse(n as i64, &delta, &y, &r);
    }
    let kappa: i64 = num(&a[4], "kappa");
    if !(-1..=1).contains(&kappa) {
        fail("kappa_in_-1,0,1");
    }
    let mode = match a[5].as_str() {
        "vac" => Seed::Vac,
        "none" => Seed::NoNoise,
        "lock0" => Seed::Lock0,
        _ => fail("seed_mode"),
    };
    let (random_phase, fine_phase) = match a[6].as_str() {
        "fixed" => (false, false),
        "random" => (true, false),
        "random30" => (true, true),
        _ => fail("phase"),
    };
    let samples: u64 = num(&a[7], "samples");
    let seed: u64 = num(&a[8], "seed");
    let dtden: i64 = num(&a[9], "dtden");
    let threads: u64 = num(&a[10], "threads");
    if dtden < 1 || !(1..=256).contains(&threads) {
        fail("dtden_or_threads_out_of_range");
    }
    let steps = parse_steps(&a[11]);
    let (dq, uq, yq) = (parse_q(&delta), parse_q(&u), parse_q(&y));
    let job = CtlJob {
        n,
        par: Par {
            x: dq - uq,
            u: uq,
            y: yq,
            kappa,
        },
        dtden,
        steps,
        seed,
        mode,
        random_phase,
        fine_phase,
    };
    let per = samples / threads;
    if per * threads != samples {
        fail("samples_must_divide_by_threads");
    }
    let mut total = vec![Acc::default(); job.steps.len()];
    thread::scope(|sc| {
        let mut handles = Vec::new();
        for (first, c) in chunks(0, samples, threads) {
            let job_ref = &job;
            handles.push(sc.spawn(move || ctl_chunk(job_ref, first, c)));
        }
        for h in handles {
            let part = h.join().expect("thread");
            for (x, y2) in total.iter_mut().zip(part.iter()) {
                x.add(y2);
            }
        }
    });
    let stdout = std::io::stdout();
    let mut out = std::io::BufWriter::new(stdout.lock());
    let mut r = writeln!(
        out,
        "TWB_HEAD|engine=twens|version={VERSION}|cli=twctl|binary_sha256={}|source_sha256={}|N={}|delta={}|u={}|y={}|kappa={}|seed_mode={}|phase={}|samples={}|seed={}|dtden={}|threads={}|reserved=0|guard=active|float_used=0|json=0",
        binary_sha256(),
        source_sha256(),
        n,
        delta,
        u,
        y,
        kappa,
        a[5],
        a[6],
        samples,
        seed,
        dtden,
        threads
    );
    for (i, s) in total.iter().enumerate() {
        r = r.and_then(|_| {
            writeln!(
                out,
                "TWCTL|N={}|delta={}|u={}|y={}|kappa={}|seed_mode={}|phase={}|samples={}|seed={}|dtden={}|step={}|q=40|sum_zr={}|sum_zi={}|sum_zr2={}|sum_zi2={}|sum_c={}|sum_c2={}|sum_zrc={}|sum_f={}|sum_r2={}|count={}|sum_f2={}|float_used=0|json=0",
                job.n, delta, u, y, kappa, a[5], a[6], samples, seed, dtden, job.steps[i],
                s.zr, s.zi, s.zr2, s.zi2, s.c, s.c2, s.zrc, s.f, s.r2, s.count, s.f2
            )
        });
    }
    let r = r
        .and_then(|_| {
            writeln!(
                out,
                "TWB_DONE|records={}|float_used=0|json=0",
                job.steps.len()
            )
        })
        .and_then(|_| out.flush());
    if r.is_err() {
        std::process::exit(5);
    }
}

fn cmd_guard(args: &[String]) {
    let p = kv(args, &["N", "delta", "y"]);
    let n: i64 = num(need(&p, "N"), "N");
    let (delta, y) = (need(&p, "delta"), need(&p, "y"));
    match guard_reason(n, delta, y) {
        None => println!(
            "TWB_GUARD|N={n}|delta={delta}|y={y}|verdict=allowed|reason=none|computed=0|json=0"
        ),
        Some(r) => println!(
            "TWB_GUARD|N={n}|delta={delta}|y={y}|verdict=refused|reason={r}|computed=0|json=0"
        ),
    }
}

fn usage() -> ! {
    eprintln!(
        "usage:\n  twens run N= delta= u= y= (seed=|seed_string=) start= count= dtden= threads= steps=k1,k2,.. ctrl=C:RS:mz;.. mask=VNC,V1,V0,RN,FLIP,LOCK,MODE0,NL (any subset) [lift_reserved_guard=1] [memo=0|1]\n  twens dump <the same keys but memo, count <= 4096>\n  twens twens N delta u y samples seed dtden threads steps ctrl [memo=1]\n  twens twctl N delta u y kappa vac|none|lock0 fixed|random|random30 samples seed dtden threads steps\n  twens seed <seed string>\n  twens guard N= delta= y=\n  twens version"
    );
    std::process::exit(2);
}

fn main() {
    let a: Vec<String> = env::args().collect();
    if a.len() < 2 {
        usage();
    }
    let rest = &a[2..];
    match a[1].as_str() {
        "run" => cmd_run(rest),
        "dump" => cmd_dump(rest),
        "twens" => cmd_twens(rest),
        "twctl" => cmd_twctl(rest),
        "guard" => cmd_guard(rest),
        "seed" => {
            if rest.len() != 1 || rest[0].contains(['|', '\n', '\r']) {
                usage();
            }
            let d = sha256::sha256(rest[0].as_bytes());
            println!(
                "TWB_SEED|seed_string={}|sha256={}|seed_u64={}|json=0",
                rest[0],
                sha256::hex(&d),
                sha256::seed_u64(&rest[0])
            );
        }
        "version" => println!(
            "TWB_VERSION|engine=twens|version={VERSION}|binary_sha256={}|source_sha256={}|float_used=0|json=0",
            binary_sha256(),
            source_sha256()
        ),
        _ => usage(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Copies of the old engines' functions, to hold the shared ones to them.
    fn old_twens_rhs(s: &St, p: &Par) -> St {
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

    fn old_twctl_rhs(s: &St, par: &Par) -> St {
        let [r0, i0, rp, ip, rm, im] = *s;
        let abs0 = m(r0, r0) + m(i0, i0);
        let absp = m(rp, rp) + m(ip, ip);
        let absm = m(rm, rm) + m(im, im);
        let sq_re = par.kappa * (m(r0, r0) - m(i0, i0));
        let sq_im = par.kappa * 2 * m(r0, i0);
        let coefp = par.x + m(par.u, abs0 + absm);
        let coefm = par.x + m(par.u, abs0 + absp);
        let bp_re = m(coefp, rp) + m(rm, sq_re) + m(im, sq_im) - m(par.y, r0);
        let bp_im = m(coefp, ip) + m(rm, sq_im) - m(im, sq_re) - m(par.y, i0);
        let bm_re = m(coefm, rm) + m(rp, sq_re) + m(ip, sq_im) - m(par.y, r0);
        let bm_im = m(coefm, im) + m(rp, sq_im) - m(ip, sq_re) - m(par.y, i0);
        let pm_re = par.kappa * (m(rp, rm) - m(ip, im));
        let pm_im = par.kappa * (m(rp, im) + m(ip, rm));
        let coef0 = m(par.u, absp + absm);
        let c_re = m(coef0, r0) + 2 * (m(pm_re, r0) + m(pm_im, i0)) - m(par.y, rp + rm);
        let c_im = m(coef0, i0) + 2 * (m(pm_im, r0) - m(pm_re, i0)) - m(par.y, ip + im);
        [c_im, -c_re, bp_im, -bp_re, bm_im, -bm_re]
    }

    fn old_gauss_twens(r: &mut Rng) -> i64 {
        let mut c: i64 = 0;
        for _ in 0..64 {
            c += i64::from(r.next().count_ones());
        }
        (c - 2048) << (Q - 5)
    }

    fn old_gauss_twctl(r: &mut Rng) -> i64 {
        let mut c: i64 = 0;
        for _ in 0..1024 {
            c += i64::from(r.next().count_ones());
        }
        (c - 32768) << (Q - 7)
    }

    fn state(r: &mut Rng) -> St {
        let mut s = [0i64; 6];
        for v in s.iter_mut() {
            *v = (r.next() >> 23) as i64 - (1i64 << 40);
        }
        s
    }

    #[test]
    fn rhs_matches_both_old_engines() {
        let mut r = Rng::new(12345);
        for _ in 0..2000 {
            let s = state(&mut r);
            let p1 = Par {
                x: parse_q("1/2") - ONE,
                u: ONE,
                y: parse_q("1/18"),
                kappa: 1,
            };
            assert_eq!(rhs(&s, &p1), old_twens_rhs(&s, &p1));
            for kappa in [-1, 0, 1] {
                let p = Par { kappa, ..p1 };
                assert_eq!(rhs(&s, &p), old_twctl_rhs(&s, &p));
            }
        }
    }

    #[test]
    fn gaussians_match_both_old_engines() {
        for seed in [0u64, 1, 2203, 20261105, u64::MAX] {
            let (mut a, mut b) = (Rng::new(seed), Rng::new(seed));
            for _ in 0..50 {
                assert_eq!(a.gauss::<64, 5>(), old_gauss_twens(&mut b));
            }
            let (mut a, mut b) = (Rng::new(seed), Rng::new(seed));
            for _ in 0..20 {
                assert_eq!(a.gauss::<1024, 7>(), old_gauss_twctl(&mut b));
            }
        }
    }

    #[test]
    fn guard_refuses_the_reserved_set_and_its_aliases() {
        for d in [
            "3/5",
            "-3/5",
            "6/10",
            "-9/15",
            "+3/5",
            "659706976665/1099511627776",
            "61/100",
            "-59/100",
        ] {
            for n in [81, 243, 729, 2187, 6561] {
                assert!(guard_reason(n, d, "1/27").is_some(), "{d} at N={n}");
            }
        }
        for n in [81, 729, 6561] {
            for y in [
                "2/27",
                "-2/27",
                "4/54",
                "81445305761/1099511627776",
                "-81445305761/1099511627776",
                "7/100",
            ] {
                assert!(guard_reason(n, "1/2", y).is_some(), "y={y} at N={n}");
            }
        }
        for d in ["0", "1/2", "-1/2", "1/4", "-1/4", "3/4", "-3/4", "11/20"] {
            assert!(guard_reason(81, d, "1/18").is_none(), "{d}");
            assert!(guard_reason(6561, d, "1/162").is_none(), "{d}");
        }
        assert!(guard_reason(243, "1/2", "2/27").is_none());
        assert!(guard_reason(2187, "0", "2/27").is_none());
        assert!(guard_reason(81, "1/2", "1/18").is_none());
        assert!(guard_reason(81, "1/2", "x").is_some());
        assert!(guard_reason(81, "1/0", "0").is_some());
    }

    fn tiny(mask: [bool; NV]) -> EnsJob {
        let mut job = EnsJob::new(
            81,
            "1/2",
            "1",
            "1/18",
            64,
            vec![0, 8, 16],
            vec![
                (ONE, 0, 0),
                (ONE + 1000, 3000, -5000),
                (ONE + 9000, 7000, -9000),
            ],
        );
        job.seed = sha256::seed_u64("twens_unit_test");
        job.on = mask;
        job
    }

    fn flat(rec: &EnsRec) -> Vec<i128> {
        let mut v = vec![rec.count];
        for r in 0..rec.v.len() {
            for a in rec.v[r].iter() {
                v.extend(a.s);
                v.extend(a.q);
                v.extend(a.x);
                v.extend(a.e);
                v.extend(a.rb.map(|b| b as i128));
                v.push(a.epsmax as i128);
            }
            for p in rec.p[r].iter() {
                v.extend([p.d, p.q, p.d2]);
                v.extend(p.rb.map(|b| b as i128));
            }
        }
        v
    }

    #[test]
    fn thread_count_does_not_change_the_sums() {
        let job = tiny([true; NV]);
        let one = flat(&ens_run(&job, 5, 23, 1));
        for t in [2, 3, 7, 23, 30] {
            assert_eq!(flat(&ens_run(&job, 5, 23, t)), one, "threads={t}");
        }
    }

    #[test]
    fn batches_add_up() {
        let job = tiny([true; NV]);
        let mut a = ens_run(&job, 0, 9, 2);
        let b = ens_run(&job, 9, 14, 3);
        a.add(&b);
        assert_eq!(flat(&a), flat(&ens_run(&job, 0, 23, 4)));
    }

    #[test]
    fn a_variant_off_leaves_the_others_alone() {
        let all = ens_run(&tiny([true; NV]), 0, 12, 3);
        for off in 0..NV {
            let mut mask = [true; NV];
            mask[off] = false;
            let part = ens_run(&tiny(mask), 0, 12, 3);
            for r in 0..3 {
                for v in (0..NV).filter(|&v| v != off) {
                    assert_eq!(all.v[r][v].s, part.v[r][v].s);
                    assert_eq!(all.v[r][v].q, part.v[r][v].q);
                    assert_eq!(all.v[r][v].x, part.v[r][v].x);
                }
                for (k, pr) in PAIRS.iter().enumerate() {
                    if pr.0 != off && pr.2 != off {
                        assert_eq!(all.p[r][k].d2, part.p[r][k].d2);
                    }
                }
            }
        }
    }

    #[test]
    fn mode0_tracks_vnc_sample_by_sample() {
        let job = tiny([true; NV]);
        let rec = ens_run(&job, 0, 40, 4);
        for r in 0..3 {
            // MODE0 - VNC on Re Z: summed squared difference below 40 samples x (2^-20 of 2^40)^2
            let k = PAIRS
                .iter()
                .position(|p| p.4 == "MODE0zr-VNCzr")
                .unwrap_or(0);
            assert!(rec.p[r][k].d2 < 40 * (1i128 << 40), "{}", rec.p[r][k].d2);
        }
    }

    #[test]
    fn rk4m_steps_exactly_as_rk4() {
        let mut r = Rng::new(777);
        let p = Par {
            x: parse_q("1/2") - ONE,
            u: ONE,
            y: parse_q("1/18"),
            kappa: 1,
        };
        for _ in 0..500 {
            let s = state(&mut r);
            for kappa in [-1, 1] {
                let pk = Par { kappa, ..p };
                assert_eq!(rk4m(&s, &pk, 64).0, rk4(&s, &pk, 64));
            }
        }
    }

    #[test]
    fn noiseless_at_zero_field_stays_at_the_fixed_point() {
        let mut job = EnsJob::new(
            81,
            "1/2",
            "1",
            "0",
            64,
            vec![0, 32, 128],
            vec![(ONE, 0, 0); 3],
        );
        job.nl = true;
        let nl = nl_run(&job);
        for r in 0..3 {
            assert_eq!(nl.states[r], [ONE, 0, 0, 0, 0, 0]);
            assert_eq!(nl.vals[r][OZR], 0);
            assert_eq!(nl.vals[r][OF], -(ONE / 81));
        }
        // the bound starts at 0 (the start is exact) and grows step by step
        assert_eq!(nl.eps[0], 0);
        assert!(nl.eps[1] > 0 && nl.eps[2] > nl.eps[1]);
    }

    #[test]
    fn mask_takes_nl_beside_the_seven() {
        let (on, nl) = parse_mask("VNC,NL,LOCK");
        assert!(nl && on[VNC] && on[LOCK] && !on[V1]);
        let (on, nl) = parse_mask("V1");
        assert!(!nl && on[V1]);
        assert_eq!(mask_text(&on, true), "V1,NL");
    }

    fn mask_of(bits: u32) -> [bool; NV] {
        let mut on = [false; NV];
        for (v, o) in on.iter_mut().enumerate() {
            *o = bits & (1 << v) != 0;
        }
        on
    }

    #[test]
    fn memo_equals_plain_on_every_mask_and_core() {
        // every subset of the seven variants, two cores (mostly outside, about half inside), 1 and 3 threads
        for bits in 0..(1u32 << NV) {
            let job = tiny(mask_of(bits));
            let plain = flat(&ens_run(&job, 11, 300, 2));
            for (r, threads) in [(12, 1), (40, 3)] {
                let cfg = MemoCfg {
                    r,
                    b2: 40,
                    k4_min: 0,
                    k2_min: 0,
                };
                let (memo, st) = ens_run_memo(&job, 11, 300, threads, &cfg);
                assert_eq!(flat(&memo), plain, "mask bits {bits:07b}, r={r}");
                let mp = memo_plan(&job, 300, &cfg);
                assert_eq!(mp.k4_on, mp.k4.iter().any(|&b| b));
                if mp.k4_on {
                    assert_eq!(st.k4_in_core + st.k4_outside, 300);
                }
            }
        }
    }

    #[test]
    fn memo_below_its_thresholds_runs_sample_by_sample_with_the_same_sums() {
        let job = tiny([true; NV]);
        let plain = flat(&ens_run(&job, 0, 200, 3));
        let (memo, st) = ens_run_memo(&job, 0, 200, 3, &MEMO);
        assert_eq!(flat(&memo), plain);
        // 200 < 2^10 and 2^22: every variant sample by sample
        assert_eq!((st.ps_samples, st.k4_in_core, st.k2_in_core), (200, 0, 0));
        assert_eq!(st.integrations, st.plain_integrations);
    }

    #[test]
    fn memo_carries_k4_repeats_with_their_counts() {
        // 2^18 draws hold about 207 repeated K4 starts (DERIVED: C(n,2) S^4); the weighted sums equal the plain ones
        let mut job = EnsJob::new(
            81,
            "1/2",
            "1",
            "1/18",
            64,
            vec![0, 1],
            vec![(ONE, 0, 0), (ONE + 1000, 3000, -5000)],
        );
        job.seed = sha256::seed_u64("twens_memo_test");
        job.on = mask_of((1 << VNC) | (1 << V1) | (1 << FLIP) | (1 << LOCK));
        let n = 1u64 << 18;
        let plain = flat(&ens_run(&job, 0, n, 2));
        let cfg = MemoCfg {
            r: 60,
            b2: 255,
            k4_min: 0,
            k2_min: 0,
        };
        let (memo, st) = ens_run_memo(&job, 0, n, 2, &cfg);
        assert_eq!(flat(&memo), plain);
        assert!(
            st.k4_distinct + 100 < st.k4_in_core,
            "{} {}",
            st.k4_distinct,
            st.k4_in_core
        );
        assert!(st.k2_distinct * 4 < st.k2_in_core);
        assert_eq!(st.k2_in_core + st.k2_outside, n);
    }

    #[test]
    fn accumulate_w_is_w_copies() {
        let job = tiny([true; NV]);
        let mut smp = Sample::new(3);
        ens_sample(&job, 5, &mut smp);
        let mut once = EnsRec::new(3);
        for _ in 0..7 {
            ens_accumulate_w(&job, &smp, &mut once, 1, &job.on, &[true; NPAIR]);
        }
        let mut w7 = EnsRec::new(3);
        ens_accumulate_w(&job, &smp, &mut w7, 7, &job.on, &[true; NPAIR]);
        assert_eq!(flat(&once), flat(&w7));
    }

    #[test]
    fn counter8_carries_its_wraps() {
        let ct = Counter8::new(3);
        let wr: Vec<usize> = thread::scope(|sc| {
            let hs: Vec<_> = (0..2)
                .map(|_| {
                    sc.spawn(|| {
                        let mut w = Vec::new();
                        for _ in 0..1000 {
                            if ct.inc(1) {
                                w.push(1);
                            }
                        }
                        for _ in 0..300 {
                            if ct.inc(2) {
                                w.push(2);
                            }
                        }
                        w
                    })
                })
                .collect();
            hs.into_iter().flat_map(|h| h.join().expect("t")).collect()
        });
        let mut wraps: HashMap<usize, u64> = HashMap::new();
        for i in wr {
            *wraps.entry(i).or_insert(0) += 1;
        }
        assert_eq!(ct.get(0, &wraps), 0);
        assert_eq!(ct.get(1, &wraps), 2000);
        assert_eq!(ct.get(2, &wraps), 600);
        // the counts next to a wrap, one thread: 255 (no wrap), 256 (one), 511 (one), 512 (two)
        for n in [255u64, 256, 511, 512] {
            let ct = Counter8::new(1);
            let mut wraps: HashMap<usize, u64> = HashMap::new();
            for _ in 0..n {
                if ct.inc(0) {
                    *wraps.entry(0).or_insert(0) += 1;
                }
            }
            assert_eq!(ct.get(0, &wraps), n, "n={n}");
        }
    }

    #[test]
    fn ball_index_is_a_bijection_onto_its_cells() {
        let r = 5;
        let b = Ball::new(r);
        let mut seen = vec![false; b.cells];
        let mut inside = 0usize;
        for c0 in -r - 1..=r + 1 {
            for c1 in -r - 1..=r + 1 {
                for c2 in -r - 1..=r + 1 {
                    for c3 in -r - 1..=r + 1 {
                        let s = c0 * c0 + c1 * c1 + c2 * c2 + c3 * c3;
                        match b.index([c0, c1, c2, c3]) {
                            Some(i) => {
                                assert!(s <= r * r && !seen[i]);
                                seen[i] = true;
                                inside += 1;
                            }
                            None => assert!(s > r * r),
                        }
                    }
                }
            }
        }
        assert_eq!(inside, b.cells);
        assert!(seen.iter().all(|&x| x));
    }

    #[test]
    fn memo_plan_keeps_each_pair_row_in_one_class() {
        let cfg = MemoCfg {
            k4_min: 0,
            k2_min: 0,
            ..MEMO
        };
        let plan = |bits: u32| memo_plan(&tiny(mask_of(bits)), 10, &cfg);
        let p = plan((1 << V0) | (1 << V1) | (1 << VNC) | (1 << FLIP));
        assert!(p.ps[V0] && p.ps[V1] && p.ps[VNC] && !p.ps[FLIP] && p.k4[FLIP]);
        let p = plan((1 << MODE0) | (1 << V1));
        assert!(p.ps[MODE0] && !p.ps[V1] && p.k4[V1]);
        let p = plan((1 << MODE0) | (1 << V1) | (1 << VNC) | (1 << LOCK));
        assert!(p.ps[MODE0] && p.ps[V1] && p.ps[VNC] && p.k2[LOCK] && !p.k4_on);
        let p = plan((1 << VNC) | (1 << V1) | (1 << RN));
        assert!(p.k4[VNC] && p.k4[V1] && p.k4[RN] && p.k4_pairs[0] && !p.ps.iter().any(|&b| b));
    }

    #[test]
    fn the_bound_of_a_field_is_at_least_its_rounding_count() {
        // every per-sample field bound is at least 1 ulp, and the t = 0 start errors of MODE0 carry its unit vector
        let job = tiny([true; NV]);
        let mut smp = Sample::new(3);
        for idx in 0..20u64 {
            ens_sample(&job, idx, &mut smp);
            for v in 0..NV {
                for r in 0..3 {
                    let b = smp.ob[r * NV + v];
                    assert!(b.o.iter().all(|&x| x >= 1));
                }
                assert!(smp.ib[v][1] >= 2 && smp.ib[v][2] >= 2);
            }
            assert!(smp.ib[MODE0][0] >= smp.ib[VNC][0] + 3);
        }
    }
}
