//! V3 scope regression: a zero-parameter SUM-ring is NOT the identity operator,
//! and the unchanged V3 circuit cannot be substituted for Gauss-invariant YM evolution.
#![deny(clippy::float_arithmetic)]

use gguf_qnn::cyclo::ZERO9;
use gguf_qnn::qutrit9::{Net9S, State9};
use gguf_qnn::ym_z3::{digits, gauge, magnetic, LINKS};

#[test]
fn zero_params_are_identity_only_on_the_all_zero_basis_input() {
    let net = Net9S {
        n: LINKS,
        layers: 2,
        params: vec![0; Net9S::param_count(LINKS, 2)],
    };
    let mut zero = State9::basis(LINKS, &[0; LINKS]);
    net.forward(&mut zero);
    assert_eq!(zero, State9::basis(LINKS, &[0; LINKS]));

    let mut one = State9::basis(LINKS, &[1, 0, 0, 0, 0, 0, 0, 0]);
    let initial = one.clone();
    net.forward(&mut one);
    assert_ne!(one, initial, "SUM ring acts even when phases vanish");
    net.inverse(&mut one);
    assert_eq!(one, initial, "the circuit is still exactly reversible");
}

#[test]
fn v3_zero_param_sum_ring_does_not_preserve_z3_gauss_subspace() {
    let net = Net9S {
        n: LINKS,
        layers: 2,
        params: vec![0; Net9S::param_count(LINKS, 2)],
    };
    let zero = [0_i64; LINKS];
    let gauge_related = gauge(&zero, &[1, 0, 0, 0]);
    assert_eq!(magnetic(&gauge_related), 0);
    let digits_in = gauge_related.map(|x| x as usize);
    let mut psi = State9::basis(LINKS, &digits_in);
    net.forward(&mut psi);
    let final_basis: Vec<usize> = psi
        .v
        .iter()
        .enumerate()
        .filter_map(|(i, z)| (*z != ZERO9).then_some(i))
        .collect();
    assert_eq!(final_basis.len(), 1);
    let new_flux_cost = magnetic(&digits(final_basis[0]));
    assert_ne!(new_flux_cost, 0,
        "gauge-equivalent zero and transformed zero must not acquire different plaquette flux");
    // This is a deliberately passing negative control: the existing V3 SUM-ring
    // is unitary, but it is NOT a gauge-preserving physical evolution.
}
