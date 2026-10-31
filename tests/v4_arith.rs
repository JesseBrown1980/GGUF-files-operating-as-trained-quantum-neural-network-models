#![deny(clippy::float_arithmetic)]
use gguf_qnn::bigint::Big;
use gguf_qnn::cyclo::ZERO9;
use gguf_qnn::qutrit9::State9;
use gguf_qnn::v2::z3_energy;
use gguf_qnn::v4::{cmp_milli_q, NetR, StateR, Z3Orbits};
use gguf_qnn::ym_z3::{DIM, LINKS};

fn pseudo(i: usize, salt: usize) -> i64 {
    ((i * 2_654_435_761 + salt * 40_503) % 7) as i64 - 3
}

#[test]
fn orbit_energy_matches_the_v2_full_projection() {
    let o = Z3Orbits::new();
    for salt in 0..3 {
        let ints: Vec<i64> = (0..DIM).map(|i| pseudo(i, salt)).collect();
        let s = StateR {
            n: LINKS,
            v: ints
                .iter()
                .map(|&x| Big::from_i128(i128::from(x)))
                .collect(),
            scales: Vec::new(),
        };
        let mut s9 = State9::basis(LINKS, &[0; LINKS]);
        s9.v = ints
            .iter()
            .map(|&x| {
                let mut z = ZERO9;
                z[0] = x;
                z
            })
            .collect();
        for r in [9i64, 81] {
            let (n4, d4) = o.energy(&s, r).expect("physical");
            let (n2, d2) = z3_energy(&s9, r).expect("physical");
            assert!(n2.c[1].is_zero() && n2.c[2].is_zero() && d2.c[1].is_zero());
            assert_eq!(n4.mul(&d2.c[0]), n2.c[0].mul(&d4));
        }
    }
}

#[test]
fn identity_is_exactly_16() {
    let o = Z3Orbits::new();
    let mut s = StateR::zero_state(LINKS);
    NetR {
        n: LINKS,
        layers: 2,
        params: vec![0; 128],
    }
    .forward(&mut s);
    for r in [9, 27, 81] {
        let (n, d) = o.energy(&s, r).expect("physical");
        assert_eq!(n, d.mul_i128(16));
    }
}

#[test]
fn rotations_are_orthogonal_up_to_scale_and_invert_exactly() {
    let params: Vec<i64> = (0..128).map(|i| pseudo(i, 5).rem_euclid(3) - 1).collect();
    let net = NetR {
        n: LINKS,
        layers: 2,
        params,
    };
    let mut s = StateR::zero_state(LINKS);
    let o = s.clone();
    net.forward(&mut s);
    let d = s.scale();
    assert_eq!(s.norm_sq(), d.mul(&d));
    net.inverse(&mut s);
    let dd = s.scale();
    let back: Vec<Big> = o.v.iter().map(|x| x.mul(&d).mul(&d)).collect();
    assert_eq!(s.v, back);
    assert_eq!(dd, d.mul(&d));
}

#[test]
fn a_small_tilt_lowers_the_energy_at_r9() {
    let o = Z3Orbits::new();
    let mut best = 1i8;
    for b in [-8i64, 8] {
        let mut s = StateR::zero_state(LINKS);
        for q in 0..LINKS {
            s.rotate(q, 0, 1, i128::from(b));
            s.rotate(q, 0, 2, i128::from(b));
        }
        best = best.min(cmp_milli_q(&o.energy(&s, 9).expect("p"), 16_000));
    }
    assert_eq!(best, -1);
}

#[test]
fn decimal_printing() {
    assert_eq!(Big::from_i128(0).dec(), "0");
    assert_eq!(Big::from_i128(-1_000_000_007).dec(), "-1000000007");
    let x = Big::from_i128(123_456_789_012_345_678_901_234_567_890);
    assert_eq!(
        x.mul(&x).dec(),
        "15241578753238836750495351562536198787501905199875019052100"
    );
}
