#![deny(clippy::float_arithmetic)]
use gguf_qnn::v4::{StateR, Z3Orbits};
use gguf_qnn::v5::{b6, trits6, NetP, PARTNERS};
use gguf_qnn::ym_z3::{digits, magnetic, LINKS};

#[test]
fn balanced_ternary_round_trip() {
    for b in -364i64..=364 {
        assert_eq!(b6(&trits6(b)), i128::from(b));
    }
}

#[test]
fn partner_pairs_carry_no_flux() {
    for &(c, t) in &PARTNERS {
        for h in 1..3usize {
            let idx = h * 3usize.pow(c as u32) + h * 3usize.pow(t as u32);
            assert_eq!(magnetic(&digits(idx)), 0);
        }
    }
}

#[test]
fn norm_inverse_and_identity() {
    let o = Z3Orbits::new();
    let zero = NetP {
        layers: 1,
        params: vec![0; 96],
    };
    for r in [9, 27, 81] {
        let (n, d) = zero.energy(&o, r).expect("p");
        assert_eq!(n, d.mul_i128(16));
    }
    let params: Vec<i64> = (0..96).map(|i| ((i * 7 + 3) % 3) as i64 - 1).collect();
    let net = NetP { layers: 1, params };
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
