#![deny(clippy::float_arithmetic)]
use gguf_qnn::bigint::Big;
use gguf_qnn::cyclo::{add, norm, times_zeta_pow, ONE9, ZERO9};
use gguf_qnn::qutrit9::{Net9, State9};
use gguf_qnn::real3::{theta_interval, R3};

#[test]
fn zeta_is_a_primitive_ninth_root() {
    assert_eq!(times_zeta_pow(&ONE9, 9), ONE9);
    assert_ne!(times_zeta_pow(&ONE9, 3), ONE9);
    let s = add(
        &add(&times_zeta_pow(&ONE9, 6), &times_zeta_pow(&ONE9, 3)),
        &ONE9,
    );
    assert_eq!(s, ZERO9); // x^6 + x^3 + 1 = 0
}

#[test]
fn norms_land_in_z_theta() {
    assert_eq!(norm(&times_zeta_pow(&ONE9, 4)), R3::int(1));
    let one_plus_zeta = add(&ONE9, &times_zeta_pow(&ONE9, 1));
    assert_eq!(norm(&one_plus_zeta), R3::from_ints(2, 1, 0)); // 2 + 2cos(2pi/9) = 2 + theta
}

#[test]
fn theta_cubed_and_the_isolating_interval() {
    let t = R3::from_ints(0, 1, 0);
    let t2 = R3::from_ints(0, 0, 1);
    assert_eq!(t.mul(&t2), R3::from_ints(-1, 3, 0)); // theta^3 = 3 theta - 1
    let (lo, hi) = theta_interval(64);
    // 1.532 * 2^64 < lo and hi < 1.533 * 2^64
    let s = Big::pow2(64);
    assert_eq!(lo.mul_i128(1000).sub(&s.mul_i128(1532)).sign(), 1);
    assert_eq!(hi.mul_i128(1000).sub(&s.mul_i128(1533)).sign(), -1);
}

#[test]
fn exact_signs() {
    assert_eq!(R3::from_ints(-153, 100, 0).sign(), Some(1)); // theta - 1.53
    assert_eq!(R3::from_ints(-154, 100, 0).sign(), Some(-1)); // theta - 1.54
    assert_eq!(
        R3::from_ints(1, -3, 0).add(&R3::from_ints(0, 0, 0)).sign(),
        Some(-1)
    ); // 1 - 3 theta
    assert_eq!(R3::int(0).sign(), Some(0));
    // theta^2 - 2.347 has theta^2 = 2.34729... so positive
    assert_eq!(R3::from_ints(-2347, 0, 1000).sign(), Some(1));
    assert_eq!(R3::from_ints(-2348, 0, 1000).sign(), Some(-1));
}

#[test]
fn fourier_fourth_power_and_exact_norm() {
    let mut s = State9::basis(3, &[2, 0, 1]);
    let o = s.clone();
    for _ in 0..4 {
        s.fourier(1, 1);
        assert_eq!(s.norm_sum(), R3::int(3i128.pow(s.k)));
    }
    assert!(s.equals_scaled(&o, 2));
}

#[test]
fn inverse_restores_and_the_gate_is_not_clifford() {
    let net = Net9 {
        n: 3,
        layers: 2,
        params: (0..24).map(|i| (i * i + 1) % 3).collect(),
    };
    let mut s = State9::basis(3, &[1, 2, 0]);
    let o = s.clone();
    net.forward(&mut s);
    assert_eq!(s.norm_sum(), R3::int(3i128.pow(s.k)));
    net.inverse(&mut s);
    assert!(s.equals_scaled(&o, s.k / 2));
    // F, diag(1, zeta, zeta^8), F on one qutrit: P(0) is irrational, so not 0, 1/3 or 1
    let mut t = State9::basis(1, &[0]);
    t.fourier(0, 1);
    t.phase9(0, 1, 8);
    t.fourier(0, 1);
    let p = t.marginal(0);
    assert!(!p[0].c[1].is_zero() || !p[0].c[2].is_zero());
}

#[test]
fn z3_energy_of_the_trivial_flat_orbit_is_16_in_v2_arithmetic() {
    for r in [9, 27, 81] {
        let s = State9::basis(8, &[0; 8]);
        let e = gguf_qnn::v2::z3_energy(&s, r).unwrap();
        assert_eq!(e.0, e.1.scale(16));
    }
}

#[test]
fn v3_sandwich_is_identity_at_zero_and_exactly_invertible() {
    use gguf_qnn::qutrit9::Net9S;
    let zero = Net9S {
        n: 8,
        layers: 2,
        params: vec![0; 64],
    };
    let mut s = State9::basis(8, &[0; 8]);
    zero.forward(&mut s);
    assert_eq!(s, State9::basis(8, &[0; 8]));
    let e = gguf_qnn::v2::z3_energy(&s, 9).unwrap();
    assert_eq!(e.0, e.1.scale(16));
    let net = Net9S {
        n: 3,
        layers: 2,
        params: (0..24).map(|i| (i * 5 + 2) % 3).collect(),
    };
    let mut t = State9::basis(3, &[2, 1, 0]);
    let o = t.clone();
    net.forward(&mut t);
    assert_eq!(t.norm_sum(), R3::int(3i128.pow(t.k)));
    net.inverse(&mut t);
    assert!(t.equals_scaled(&o, t.k / 2));
}
