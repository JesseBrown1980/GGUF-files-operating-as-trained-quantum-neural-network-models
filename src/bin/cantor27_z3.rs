//! Exact Cantor-27 phase-and-shift circuit on the Z3 2x2 physical gauge space.
//! This is a deterministic qutrit circuit, NOT Schrodinger evolution under H=E+rM.
//! Every gate preserves Gauss law, including intermediate steps. No floats/JSON.
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

use gguf_qnn::gguf_model;
use gguf_qnn::sha256::hex_digest;
use gguf_qnn::ym_z3::{digits, gauge, gauge_group, index, magnetic, LINKS};
use std::collections::BTreeMap;
use std::fs;

const SOURCE_SHA: &str = "1f48fa5083237cd4bdadc3f6c4f9094b864ca1386d7d09b5b27c19b5f27f6913";
type Sparse = BTreeMap<usize, i64>; // a basis amplitude is zeta_9^phase / sqrt(54)

fn cantor() -> Vec<u8> {
    let mut out = Vec::with_capacity(729);
    for i in 0..729usize {
        let mut n = i;
        let mut twos = 0;
        let mut valid = true;
        for _ in 0..6 {
            let digit = n % 3;
            n /= 3;
            if digit == 1 {
                valid = false;
                break;
            }
            twos += digit / 2;
        }
        out.push(if !valid { 0 } else if twos % 2 == 0 { 1 } else { 2 });
    }
    assert_eq!(hex_digest(&out), SOURCE_SHA, "Cantor input digest changed");
    assert_eq!(out.iter().filter(|&&x| x == 1).count(), 32);
    assert_eq!(out.iter().filter(|&&x| x == 2).count(), 32);
    out
}

fn init() -> Sparse {
    let flat = [0; LINKS];
    let mut excited = flat;
    excited[0] = 1;
    let mut map = Sparse::new();
    for a in gauge_group() {
        map.insert(index(&gauge(&flat, &a)), 0);
        map.insert(index(&gauge(&excited, &a)), 0);
    }
    assert_eq!(map.len(), 54);
    map
}

fn shift(mut g: [i64; LINKS], t: usize, inverse: bool) -> [i64; LINKS] {
    let sign = if inverse { -1 } else { 1 };
    g[0] = (g[0] + sign).rem_euclid(3);
    if t % 7 == 1 {
        g[1] = (g[1] + sign).rem_euclid(3);
    }
    g
}

fn sign(trit: u8) -> i64 {
    match trit {
        0 => 0,
        1 => 1,
        2 => -1,
        _ => panic!("invalid trit"),
    }
}

fn step(s: &Sparse, t: usize, pulse: u8) -> Sparse {
    let mut out = Sparse::new();
    for (&key, &old) in s {
        let g = digits(key);
        // Gauge-invariant magnetic M(g); zeta_9^(sign * M(g)).
        let phase = (old + sign(pulse) * magnetic(&g)).rem_euclid(9);
        assert!(out.insert(index(&shift(g, t, false)), phase).is_none());
    }
    out
}

fn undo(s: &Sparse, t: usize, pulse: u8) -> Sparse {
    let mut out = Sparse::new();
    for (&key, &old) in s {
        let g = shift(digits(key), t, true);
        let phase = (old - sign(pulse) * magnetic(&g)).rem_euclid(9);
        assert!(out.insert(index(&g), phase).is_none());
    }
    out
}

fn gauss_invariant(s: &Sparse) -> bool {
    let gg = gauge_group();
    for (&key, &phase) in s {
        let g = digits(key);
        for a in &gg {
            if s.get(&index(&gauge(&g, a))) != Some(&phase) {
                return false;
            }
        }
    }
    true
}

/// Histogram of phases of <psi|X_0|psi>, with common positive denominator 54.
/// X_0 is a gauge-invariant electric shift, not a position measurement.
fn coherence_hist(s: &Sparse) -> [usize; 9] {
    let mut h = [0usize; 9];
    for (&key, &phase) in s {
        let mut g = digits(key);
        g[0] = (g[0] + 1).rem_euclid(3);
        if let Some(&other) = s.get(&index(&g)) {
            h[(phase - other).rem_euclid(9) as usize] += 1;
        }
    }
    h
}

fn execute(seq: &[u8]) -> (Sparse, bool) {
    let initial = init();
    let mut s = initial.clone();
    for (t, &pulse) in seq.iter().enumerate() {
        s = step(&s, t, pulse);
    }
    let terminal = s.clone();
    for (t, &pulse) in seq.iter().enumerate().rev() {
        s = undo(&s, t, pulse);
    }
    (terminal, s == initial)
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let source = a.get(1).map(String::as_str).unwrap_or("results-v3/v3-z3-r9-star.gguf");
    let data = fs::read(source).expect("read v3 GGUF");
    let model = gguf_model::read(&data).expect("invalid GGUF");
    assert_eq!(model.str("general.architecture"), Some("asolaria-qutrit-vqnn-v3"));
    assert_eq!(model.u32("qnn.layers"), Some(2));
    assert_eq!(model.u32("ym.r"), Some(9));
    let params = model.tensor("branch_0.params").expect("model parameters missing");
    assert_eq!(params.len(), 64);
    assert!(params.iter().all(|x| (0..=2).contains(x)));
    let signal = cantor();
    println!(
        "CANTOR_Z3|schema=CANTOR-Z3-GAUSS-EXACT-V1|model_sha256={}|input_sha256={SOURCE_SHA}|model_parameters_checked=64|model_net_executed=0|json=0",
        hex_digest(&data)
    );
    let signed_inverted: Vec<u8> = signal.iter().map(|&q| if q == 1 { 2 } else if q == 2 { 1 } else { 0 }).collect();
    let mut rotated = signal.clone();
    rotated.rotate_left(1);
    for (name, inputs) in [
        ("cantor", signal),
        ("zero", vec![0; 729]),
        ("inverted", signed_inverted),
        ("rotated_one", rotated),
    ] {
        let (state, reversed) = execute(&inputs);
        let gauss = gauss_invariant(&state);
        let h = coherence_hist(&state);
        println!(
            "RESPONSE|control={name}|states={}|slots=729|gauss_invariant={}|inverse_exact={}|electric_shift_coherence_phase_counts={}|norm_denominator=54|json=0",
            state.len(),
            u8::from(gauss),
            u8::from(reversed),
            h.iter().map(usize::to_string).collect::<Vec<_>>().join(",")
        );
        assert!(gauss && reversed);
    }
    println!("BOUNDARY|finite_exact_quantum_circuit=1|classical_simulation=1|trained_v3_net_evaluated=0|S3_hamiltonian_executed=0|spectral_gap_certified=0|physical_qutrits=0|json=0");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cantor_27_exact_gauss_and_reverse() {
        let source = cantor();
        let (state, reverse_ok) = execute(&source);
        assert!(gauss_invariant(&state));
        assert!(reverse_ok);
        assert_eq!(coherence_hist(&state), [0, 0, 0, 0, 0, 0, 27, 0, 0]);
    }

    #[test]
    fn cantor_changes_gauge_invariant_electric_coherence() {
        let (zero, reverse_ok) = execute(&vec![0; 729]);
        assert!(reverse_ok);
        assert_eq!(coherence_hist(&zero), [27, 0, 0, 0, 0, 0, 0, 0, 0]);
        let (signal, reverse_ok) = execute(&cantor());
        assert!(reverse_ok);
        assert_ne!(coherence_hist(&zero), coherence_hist(&signal));
    }
}
