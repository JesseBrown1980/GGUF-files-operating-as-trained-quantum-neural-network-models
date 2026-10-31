#![deny(clippy::float_arithmetic)]
use gguf_qnn::qutrit::State;
use gguf_qnn::ym_z3::{digits, energy, fluxes, index, physical, LINKS};

#[test]
fn physical_space_is_243_orbits_of_27_with_9_flat() {
    let p = physical();
    assert_eq!(p.reps.len(), 243);
    assert!(p.sizes.iter().all(|&s| s == 27));
    assert_eq!(p.mag.iter().filter(|&&m| m == 0).count(), 9);
    assert_eq!(p.mag.iter().filter(|&&m| m > 0).min(), Some(&6));
    assert!(p.electric.iter().all(|(&(i, j), _)| i <= j));
}

#[test]
fn fluxes_sum_to_zero_on_the_torus() {
    for c in 0..6561 {
        let h = fluxes(&digits(c));
        assert_eq!(h.iter().sum::<i64>() % 3, 0);
        assert_eq!(index(&digits(c)), c);
    }
}

#[test]
fn the_trivial_flat_orbit_has_energy_exactly_16() {
    for r in [9, 27, 81] {
        let e = energy(&State::basis(LINKS, &[0; LINKS]), r).unwrap();
        assert_eq!(e.0, 16 * e.1);
    }
}
