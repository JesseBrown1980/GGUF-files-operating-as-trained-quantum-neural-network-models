#![deny(clippy::float_arithmetic)]
use gguf_qnn::v4::{StateR, Z3Orbits};
use gguf_qnn::v5::{trits6, NetP};
use gguf_qnn::v6::{b8, trits8, NetP6};
use gguf_qnn::ym_z3::LINKS;

#[test]
fn balanced_ternary_round_trip() {
    for b in -3280i64..=3280 {
        assert_eq!(b8(&trits8(b)), i128::from(b));
    }
}

#[test]
fn nine_times_b_on_the_finer_grid_is_the_same_rotation() {
    let o = Z3Orbits::new();
    let bs: Vec<i64> = (0..16).map(|i| [0, 7, -7, 243, 2, -40][i % 6]).collect();
    let p5: Vec<i64> = bs.iter().flat_map(|&b| trits6(b)).collect();
    let p6: Vec<i64> = bs.iter().flat_map(|&b| trits8(9 * b)).collect();
    let e5 = NetP {
        layers: 1,
        params: p5,
    }
    .energy(&o, 9)
    .expect("p");
    let e6 = NetP6 {
        layers: 1,
        params: p6,
    }
    .energy(&o, 9)
    .expect("p");
    assert_eq!(e5.0.mul(&e6.1), e6.0.mul(&e5.1));
}

#[test]
fn norm_inverse_and_identity() {
    let o = Z3Orbits::new();
    let zero = NetP6 {
        layers: 1,
        params: vec![0; 128],
    };
    for r in [9, 27, 81] {
        let (n, d) = zero.energy(&o, r).expect("p");
        assert_eq!(n, d.mul_i128(16));
    }
    let params: Vec<i64> = (0..128).map(|i| ((i * 5 + 1) % 3) as i64 - 1).collect();
    let net = NetP6 { layers: 1, params };
    let mut s = StateR::zero_state(LINKS);
    let o0 = s.clone();
    net.forward(&mut s);
    let d = s.scale();
    assert_eq!(s.norm_sq(), d.mul(&d));
    net.inverse(&mut s);
    assert_eq!(
        s.v,
        o0.v.iter().map(|x| x.mul(&d).mul(&d)).collect::<Vec<_>>()
    );
}
