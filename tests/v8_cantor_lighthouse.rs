#![deny(clippy::float_arithmetic)]
//! V8 candidate test, not a V8 training claim or a quantum/GPU measurement.
//! Replays the sealed V7 model and applies Cantor-27 pulses as exact,
//! Gauss-compatible operations on the 3^8 configuration basis.
//! Compare the 64-channel 81x81 framebuffer to arbitrary-precision integers.
use gguf_qnn::bigint::Big;
use gguf_qnn::gguf_model;
use gguf_qnn::pixels::{lift, primes, Frame};
use gguf_qnn::v4::{milli_floor_q, StateR, Z3Orbits};
use gguf_qnn::v7::{NetQ, PARAMS};
use gguf_qnn::ym_z3::{digits, fluxes, gauge, gauge_group, index, DIM, LINKS};

const TICKS: usize = 729;
const V7_R9_IDENTITY: &[u8] = include_bytes!("../results-v7/v7-z3-r9-identity.gguf");

/// Cantor support = six base-three digits from {0,2}, parity determines sign.
fn cantor(tick: usize) -> i64 {
    let (mut x, mut twos) = (tick, 0);
    for _ in 0..6 {
        let digit = x % 3;
        if digit == 1 {
            return 0;
        }
        if digit == 2 {
            twos += 1;
        }
        x /= 3;
    }
    if twos % 2 == 0 { 1 } else { -1 }
}

fn wilson_x(cfg: &[i64; LINKS]) -> i64 {
    (cfg[0] + cfg[2]).rem_euclid(3)
}

/// Add equal link values to the two x-links of one column or y-links of a row.
/// These vectors have zero lattice curl; translations commute with Z3 gauge transformations.
fn shift_config(mut cfg: [i64; LINKS], pair: [usize; 2], s: i64) -> [i64; LINKS] {
    for q in pair {
        cfg[q] = (cfg[q] + s).rem_euclid(3);
    }
    cfg
}

/// A reversible permutation, implemented independently in the integer and pixel engines.
fn loop_shift(s: &mut StateR, f: &mut Frame, pair: [usize; 2], step: i64) {
    let targets: Vec<usize> = (0..DIM)
        .map(|x| index(&shift_config(digits(x), pair, step)))
        .collect();
    let mut big = vec![Big::zero(); DIM];
    for (i, &j) in targets.iter().enumerate() {
        big[j] = s.v[i].clone();
    }
    s.v = big;
    for ch in &mut f.chan {
        let mut dst = vec![0u64; DIM];
        for (i, &j) in targets.iter().enumerate() {
            dst[j] = ch[i];
        }
        *ch = dst;
    }
    f.passes += 1;
}

/// Real +/-1 Wilson-loop kick. This is an exact classical qutrit-circuit
/// simulation, NOT the complex qutrit omega phase or a physical anneal.
/// Its target is gauge invariant, and applying it twice is identity.
fn wilson_kick(s: &mut StateR, f: &mut Frame, signed: i64) {
    let target = if signed > 0 { 1 } else { 2 };
    for i in 0..DIM {
        if wilson_x(&digits(i)) == target {
            s.v[i] = s.v[i].mul_i128(-1);
            for (ch, &p) in f.chan.iter_mut().zip(&f.p) {
                if ch[i] != 0 {
                    ch[i] = p - ch[i];
                }
            }
        }
    }
    f.passes += 1;
}

/// Three Rime lighthouse phases; use ACTIVE-PULSE index rather than
/// tick modulo three, because Cantor support never has tick mod 3 = 1.
fn pulse(s: &mut StateR, f: &mut Frame, phase: usize, signed: i64, undo: bool) {
    match phase % 3 {
        0 => loop_shift(s, f, [0, 4], if undo { -signed } else { signed }),
        1 => wilson_kick(s, f, signed),
        _ => loop_shift(s, f, [1, 3], if undo { -signed } else { signed }),
    }
}

fn exact_vs_pixel(s: &StateR, f: &Frame, orbits: &Z3Orbits, label: &str) {
    let (n, d) = orbits.energy(s, 9).expect("physical projection not zero");
    let (rn, rd) = f.energy_residues(9);
    assert_eq!(lift(&rn, &f.p), n, "{label} numerator");
    assert_eq!(lift(&rd, &f.p), d, "{label} denominator");
    // Verify actual amplitudes modulo the first and last prime,
    // not just the two aggregate energy integers.
    for &k in &[0usize, 63] {
        let p = f.p[k];
        for (i, z) in s.v.iter().enumerate().step_by(113) {
            let neg = z.sign() < 0;
            let m = z
                .dec()
                .trim_start_matches('-')
                .bytes()
                .fold(0u64, |acc, d| (acc * 10 + u64::from(d - b'0')) % p);
            let want = if neg && m != 0 { p - m } else { m };
            assert_eq!(f.chan[k][i], want, "{label} pixel={i} prime={k}");
        }
    }
    let milli = milli_floor_q(&(n, d), 0, 10_000_000);
    println!("V8CHECK|checkpoint={label}|pixel_backend_equals_exact=1|energy_milli_floor={milli:?}|json=0");
}

fn load_v7() -> NetQ {
    let m = gguf_model::read(V7_R9_IDENTITY).expect("sealed V7 GGUF");
    assert_eq!(m.str("general.architecture"), Some("asolaria-qutrit-vqnn-v7"));
    assert_eq!(m.u32("ym.r"), Some(9));
    let params: Vec<i64> = m
        .tensor("branch_0.params")
        .expect("V7 parameters")
        .iter()
        .map(|&x| i64::from(x))
        .collect();
    assert_eq!(params.len(), PARAMS);
    NetQ { params }
}

#[test]
fn cantor_signal_exact_support_and_lighthouse_phase_coverage() {
    let seq: Vec<i64> = (0..TICKS).map(cantor).collect();
    assert_eq!(seq.iter().filter(|&&x| x == 1).count(), 32);
    assert_eq!(seq.iter().filter(|&&x| x == -1).count(), 32);
    assert_eq!(seq.iter().filter(|&&x| x == 0).count(), 665);
    let active: Vec<i64> = seq.into_iter().filter(|&x| x != 0).collect();
    assert_eq!(active.len(), 64);
    for phase in 0..3 {
        assert!(active.iter().enumerate().any(|(i, _)| i % 3 == phase));
    }
}

#[test]
fn gates_preserve_z3_gauss_and_flux_of_closed_loop_translations() {
    let group = gauge_group();
    for i in 0..DIM {
        let cfg = digits(i);
        let wx = wilson_x(&cfg);
        for pair in [[0, 4], [1, 3]] {
            let shifted = shift_config(cfg, pair, 1);
            assert_eq!(fluxes(&shifted), fluxes(&cfg));
        }
        for a in &group {
            let transformed = gauge(&cfg, a);
            assert_eq!(wilson_x(&transformed), wx);
            for pair in [[0, 4], [1, 3]] {
                let left = shift_config(transformed, pair, 1);
                let right = gauge(&shift_config(cfg, pair, 1), a);
                assert_eq!(left, right);
            }
        }
    }
}

#[test]
fn sealed_v7_cantor_stream_matches_pixel_engine_and_reverses() {
    let net = load_v7();
    let orbits = Z3Orbits::new();
    let ps = primes(64);
    let mut initial_big = StateR::zero_state(LINKS);
    let mut initial_pixel = Frame::zero_state(&ps);
    net.forward(&mut initial_big);
    net.forward(&mut initial_pixel);
    exact_vs_pixel(&initial_big, &initial_pixel, &orbits, "baseline_v7");
    let base = orbits.energy(&initial_big, 9).unwrap();
    assert_eq!(milli_floor_q(&base, 0, 10_000_000), Some(15_381));

    let active: Vec<(usize, i64)> = (0..TICKS)
        .filter_map(|t| { let s = cantor(t); if s == 0 { None } else { Some((t, s)) } })
        .collect();
    assert_eq!(active.len(), 64);
    let reference: Vec<i64> = active.iter().map(|&(_, s)| s).collect();
    for kind in ["cantor", "inverted", "shuffled"] {
        let mut s = StateR {
            n: initial_big.n,
            v: initial_big.v.clone(),
            scales: initial_big.scales.clone(),
        };
        let mut f = Frame {
            p: ps.clone(),
            chan: initial_pixel.chan.clone(),
            passes: initial_pixel.passes,
        };
        let mut actions = Vec::new();
        for (j, &(tick, x)) in active.iter().enumerate() {
            let sign = match kind {
                "inverted" => -x,
                "shuffled" => reference[(j * 7) % reference.len()],
                _ => x,
            };
            let phase = j % 3;
            pulse(&mut s, &mut f, phase, sign, false);
            actions.push((phase, sign));
            if kind == "cantor" && (tick == 0 || tick == 26) {
                exact_vs_pixel(&s, &f, &orbits, &format!("{kind}_tick{}", tick + 1));
            }
        }
        exact_vs_pixel(&s, &f, &orbits, &format!("{kind}_tick729"));
        assert_eq!(s.norm_sq(), initial_big.norm_sq(), "{kind} norm");
        for &(phase, sign) in actions.iter().rev() {
            pulse(&mut s, &mut f, phase, sign, true);
        }
        assert_eq!(s.v, initial_big.v, "{kind} reversed amplitudes");
        assert_eq!(f.chan, initial_pixel.chan, "{kind} reversed pixels");
        println!("V8CHECK|control={kind}|pulses=64|inverse=PASS|norm=PASS|json=0");
    }
    // The all-zero signal is exactly the unchanged frozen V7 baseline.
    exact_vs_pixel(&initial_big, &initial_pixel, &orbits, "zero_signal");
}
