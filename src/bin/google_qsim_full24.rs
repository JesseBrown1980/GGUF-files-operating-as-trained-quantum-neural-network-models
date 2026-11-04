//! Google's whole qsim sample circuit_q24, 1,257 gates on 24 qubits, in integers alone.
//!
//! Two separate records run on the same gates. The exact record holds each amplitude in Z[omega], omega^8 = 1, over a
//! power of sqrt(2), with coordinates mod 2^61 - 1: every gate of this circuit is additions and coordinate rotations, so
//! the sum of |a|^2 can be read exactly. The fixed-point record holds re and im at scale 2^60, for real values to compare
//! with Google's simulator. Its rounding per gate has l2 norm at most about sqrt(2^25) ulps, and the gates are unitary.
//!
//! usage = google_qsim_full24 CIRCUIT BITSTRINGS [mutate=y2_sign]
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

use std::time::Instant;

const P: u64 = (1 << 61) - 1;
const SCALE_BITS: u32 = 60;
const READINGS: [u32; 7] = [2, 10, 20, 40, 60, 80, 100];
const PREFIX_HISTOGRAM: [u64; 8] = [
    2_031_616, 2_099_712, 2_168_576, 2_094_592, 2_031_616, 2_094_592, 2_156_800, 2_099_712,
];

#[derive(Clone, Copy)]
enum Gate {
    H(usize),
    T(usize),
    X2(usize),
    Y2(usize),
    Cz(usize, usize),
}

fn parse(text: &str) -> Result<(usize, Vec<(u32, Gate)>), String> {
    let mut lines = text.lines();
    let qubits: usize = lines
        .next()
        .ok_or("empty")?
        .trim()
        .parse()
        .map_err(|_| "qubit count")?;
    let mut gates = Vec::new();
    for line in lines {
        let f: Vec<&str> = line.split_whitespace().collect();
        if f.is_empty() {
            continue;
        }
        let time: u32 = f[0].parse().map_err(|_| "time")?;
        let q = |i: usize| -> Result<usize, String> {
            let n: usize = f.get(i).ok_or("operand")?.parse().map_err(|_| "operand")?;
            if n >= qubits {
                return Err("qubit outside the register".into());
            }
            Ok(n)
        };
        let gate = match f[1] {
            "h" => Gate::H(q(2)?),
            "t" => Gate::T(q(2)?),
            "x_1_2" => Gate::X2(q(2)?),
            "y_1_2" => Gate::Y2(q(2)?),
            "cz" => Gate::Cz(q(2)?, q(3)?),
            other => return Err(format!("gate outside this circuit: {other}")),
        };
        gates.push((time, gate));
    }
    Ok((qubits, gates))
}

// ---- The exact record.
type W = [u64; 4];

#[inline]
fn add(a: u64, b: u64) -> u64 {
    let s = a + b;
    if s >= P {
        s - P
    } else {
        s
    }
}

#[inline]
fn neg(a: u64) -> u64 {
    if a == 0 {
        0
    } else {
        P - a
    }
}

#[inline]
fn w_add(a: W, b: W) -> W {
    [
        add(a[0], b[0]),
        add(a[1], b[1]),
        add(a[2], b[2]),
        add(a[3], b[3]),
    ]
}

#[inline]
fn w_neg(a: W) -> W {
    [neg(a[0]), neg(a[1]), neg(a[2]), neg(a[3])]
}

#[inline]
fn w_sub(a: W, b: W) -> W {
    w_add(a, w_neg(b))
}

#[inline]
fn w_omega(a: W) -> W {
    [neg(a[3]), a[0], a[1], a[2]]
}

#[inline]
fn w_i(a: W) -> W {
    [neg(a[2]), neg(a[3]), a[0], a[1]]
}

fn mul(a: u64, b: u64) -> u64 {
    let product = u128::from(a) * u128::from(b);
    let low = (product & u128::from(P)) as u64;
    let high = (product >> 61) as u64;
    add(low, high)
}

fn exact_step(state: &mut [W], gate: Gate) -> u32 {
    let n = state.len();
    match gate {
        Gate::H(q) => {
            let m = 1usize << q;
            for i in 0..n {
                if i & m == 0 {
                    let (x, y) = (state[i], state[i | m]);
                    state[i] = w_add(x, y);
                    state[i | m] = w_sub(x, y);
                }
            }
            1
        }
        Gate::T(q) => {
            let m = 1usize << q;
            for (i, a) in state.iter_mut().enumerate() {
                if i & m != 0 {
                    *a = w_omega(*a);
                }
            }
            0
        }
        Gate::Cz(p, q) => {
            let m = (1usize << p) | (1usize << q);
            for (i, a) in state.iter_mut().enumerate() {
                if i & m == m {
                    *a = w_neg(*a);
                }
            }
            0
        }
        Gate::X2(q) => {
            let m = 1usize << q;
            for i in 0..n {
                if i & m == 0 {
                    let (x, y) = (state[i], state[i | m]);
                    let (ix, iy) = (w_i(x), w_i(y));
                    state[i] = w_add(w_add(x, ix), w_sub(y, iy));
                    state[i | m] = w_add(w_sub(x, ix), w_add(y, iy));
                }
            }
            2
        }
        Gate::Y2(q) => {
            let m = 1usize << q;
            for i in 0..n {
                if i & m == 0 {
                    let (x, y) = (state[i], state[i | m]);
                    let (d, s) = (w_sub(x, y), w_add(x, y));
                    state[i] = w_add(d, w_i(d));
                    state[i | m] = w_add(s, w_i(s));
                }
            }
            2
        }
    }
}

fn phase_histogram(state: &[W]) -> Result<[u64; 8], String> {
    let mut out = [0u64; 8];
    let m = P - 1;
    for a in state {
        let phase = match *a {
            [1, 0, 0, 0] => 0,
            [0, 1, 0, 0] => 1,
            [0, 0, 1, 0] => 2,
            [0, 0, 0, 1] => 3,
            [x, 0, 0, 0] if x == m => 4,
            [0, x, 0, 0] if x == m => 5,
            [0, 0, x, 0] if x == m => 6,
            [0, 0, 0, x] if x == m => 7,
            _ => {
                return Err(
                    "an amplitude at the end of time 2 is not an eighth root of unity".into(),
                )
            }
        };
        out[phase] += 1;
    }
    Ok(out)
}

fn run_exact(qubits: usize, gates: &[(u32, Gate)]) -> Result<(), String> {
    let start = Instant::now();
    let mut state: Vec<W> = vec![[0, 0, 0, 0]; 1usize << qubits];
    state[0] = [1, 0, 0, 0];
    let mut power = 0u32;
    let mut prefix_done = false;
    for &(time, gate) in gates {
        if time > 2 && !prefix_done {
            let hist = phase_histogram(&state)?;
            println!(
                "FULL_Q24_PREFIX|time=2|sqrt2_power={power}|histogram={},{},{},{},{},{},{},{}|equals_the_prediction={}|json=0",
                hist[0], hist[1], hist[2], hist[3], hist[4], hist[5], hist[6], hist[7],
                u8::from(hist == PREFIX_HISTOGRAM)
            );
            prefix_done = true;
        }
        power += exact_step(&mut state, gate);
    }
    let (mut rational, mut root_part) = (0u64, 0u64);
    for a in &state {
        for x in a {
            rational = add(rational, mul(*x, *x));
        }
        root_part = add(root_part, mul(a[0], a[1]));
        root_part = add(root_part, mul(a[1], a[2]));
        root_part = add(root_part, mul(a[2], a[3]));
        root_part = add(root_part, neg(mul(a[0], a[3])));
    }
    let mut expected = 1u64;
    for _ in 0..power {
        expected = add(expected, expected);
    }
    println!(
        "FULL_Q24_EXACT|gates={}|sqrt2_power={power}|rational_part_equals_2^power={}|sqrt2_part_zero={}|json=0",
        gates.len(),
        u8::from(rational == expected),
        u8::from(root_part == 0)
    );
    eprintln!("TIMING|exact_record_ms={}", start.elapsed().as_millis());
    Ok(())
}

// ---- The fixed-point record.
type C = (i64, i64);

fn isqrt(n: u128) -> u128 {
    let mut x = n;
    let mut y = (x + 1) / 2;
    while y < x {
        x = y;
        y = (x + n / x) / 2;
    }
    x
}

#[inline]
fn times_root(value: i64, root: i64) -> i64 {
    ((i128::from(value) * i128::from(root)) >> SCALE_BITS) as i64
}

fn fixed_step(state: &mut [C], gate: Gate, root: i64, flip_y2: bool) {
    let n = state.len();
    match gate {
        Gate::H(q) => {
            let m = 1usize << q;
            for i in 0..n {
                if i & m == 0 {
                    let (x, y) = (state[i], state[i | m]);
                    state[i] = (times_root(x.0 + y.0, root), times_root(x.1 + y.1, root));
                    state[i | m] = (times_root(x.0 - y.0, root), times_root(x.1 - y.1, root));
                }
            }
        }
        Gate::T(q) => {
            let m = 1usize << q;
            for (i, a) in state.iter_mut().enumerate() {
                if i & m != 0 {
                    *a = (times_root(a.0 - a.1, root), times_root(a.0 + a.1, root));
                }
            }
        }
        Gate::Cz(p, q) => {
            let m = (1usize << p) | (1usize << q);
            for (i, a) in state.iter_mut().enumerate() {
                if i & m == m {
                    *a = (-a.0, -a.1);
                }
            }
        }
        Gate::X2(q) => {
            let m = 1usize << q;
            for i in 0..n {
                if i & m == 0 {
                    let ((a, b), (c, d)) = (state[i], state[i | m]);
                    state[i] = ((a - b + c + d) >> 1, (a + b - c + d) >> 1);
                    state[i | m] = ((a + b + c - d) >> 1, (b - a + c + d) >> 1);
                }
            }
        }
        Gate::Y2(q) => {
            let m = 1usize << q;
            for i in 0..n {
                if i & m == 0 {
                    let ((a, b), (c, d)) = (state[i], state[i | m]);
                    let (u, v) = if flip_y2 {
                        (a + c, b + d)
                    } else {
                        (a - c, b - d)
                    };
                    let (s, t) = if flip_y2 {
                        (a - c, b - d)
                    } else {
                        (a + c, b + d)
                    };
                    state[i] = ((u - v) >> 1, (u + v) >> 1);
                    state[i | m] = ((s - t) >> 1, (s + t) >> 1);
                }
            }
        }
    }
}

fn read_statistics(state: &[C], time: u32) {
    let (mut norm, mut sum_p, mut sum_p2) = (0u128, 0u128, 0u128);
    for &(re, im) in state {
        let square = (i128::from(re) * i128::from(re) + i128::from(im) * i128::from(im)) as u128;
        norm += square;
        let p = square >> SCALE_BITS;
        sum_p += p;
        sum_p2 += p * p;
    }
    let one = 1u128 << (2 * SCALE_BITS);
    let (above, off) = if norm >= one {
        (1, norm - one)
    } else {
        (0, one - norm)
    };
    let off_ppb = ((off >> 60) * 1_000_000_000) >> 60;
    let quotient = (sum_p2 << 20) / sum_p;
    let statistic_ppm = (quotient * 1_000_000 * 16) / sum_p;
    println!("FULL_Q24_FIXED|time={time}|norm_off_ppb={off_ppb}|norm_above_one={above}|xeb_2^24_sum_p2_ppm={statistic_ppm}|json=0");
}

fn run_fixed(qubits: usize, gates: &[(u32, Gate)], wanted: &[usize], flip_y2: bool) {
    let start = Instant::now();
    let root = isqrt(1u128 << (2 * SCALE_BITS - 1)) as i64;
    let mut state: Vec<C> = vec![(0, 0); 1usize << qubits];
    state[0] = (1i64 << SCALE_BITS, 0);
    let mut next = 0usize;
    for (index, &(time, gate)) in gates.iter().enumerate() {
        fixed_step(&mut state, gate, root, flip_y2);
        let last_of_time = index + 1 == gates.len() || gates[index + 1].0 > time;
        if last_of_time && next < READINGS.len() && time == READINGS[next] {
            read_statistics(&state, time);
            next += 1;
        }
    }
    for &b in wanted {
        println!(
            "FULL_Q24_AMPLITUDE|index={b}|re_at_2^60={}|im_at_2^60={}|json=0",
            state[b].0, state[b].1
        );
    }
    eprintln!("TIMING|fixed_record_ms={}", start.elapsed().as_millis());
}

fn main() -> Result<(), String> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        return Err("usage = google_qsim_full24 CIRCUIT BITSTRINGS [mutate=y2_sign]".into());
    }
    let flip_y2 = args.get(3).is_some_and(|a| a == "mutate=y2_sign");
    let text = std::fs::read_to_string(&args[1]).map_err(|e| e.to_string())?;
    let (qubits, gates) = parse(&text)?;
    let count = |f: fn(&Gate) -> bool| gates.iter().filter(|(_, g)| f(g)).count();
    println!(
        "FULL_Q24_GATES|qubits={qubits}|total={}|h={}|cz={}|t={}|x_1_2={}|y_1_2={}|max_time={}|json=0",
        gates.len(),
        count(|g| matches!(g, Gate::H(_))),
        count(|g| matches!(g, Gate::Cz(_, _))),
        count(|g| matches!(g, Gate::T(_))),
        count(|g| matches!(g, Gate::X2(_))),
        count(|g| matches!(g, Gate::Y2(_))),
        gates.iter().map(|(t, _)| *t).max().unwrap_or(0)
    );
    let wanted_text = std::fs::read_to_string(&args[2]).map_err(|e| e.to_string())?;
    let mut wanted = Vec::new();
    for line in wanted_text.lines().filter(|l| !l.is_empty()) {
        let mut b = 0usize;
        for (p, c) in line.chars().enumerate() {
            if c == '1' {
                b |= 1usize << p;
            }
        }
        wanted.push(b);
    }
    if !flip_y2 {
        run_exact(qubits, &gates)?;
    }
    run_fixed(qubits, &gates, &wanted, flip_y2);
    Ok(())
}
