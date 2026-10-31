#![deny(clippy::float_arithmetic)]
use gguf_qnn::eisenstein::{E, OMEGA, ONE};
use gguf_qnn::gguf_model::{read, write, Kv, Model};
use gguf_qnn::qnn::Net;
use gguf_qnn::qutrit::{pow3, State};
use gguf_qnn::task::{encode, points};

#[test]
fn omega_is_a_cube_root_of_one() {
    assert_eq!(OMEGA * OMEGA * OMEGA, ONE);
    assert_eq!(ONE + OMEGA + OMEGA * OMEGA, E::new(0, 0));
    assert_eq!(OMEGA.norm(), 1);
    assert_eq!(E::new(2, 1).norm(), 3);
}

#[test]
fn fourier_to_the_fourth_is_identity_and_norm_is_exact() {
    let (tr, _) = points();
    for p in tr.iter().take(20) {
        let mut s = encode(p);
        let o = s.clone();
        for _ in 0..4 {
            s.fourier(1, 1);
            assert_eq!(s.norm_sum(), pow3(s.k));
        }
        assert!(s.equals_scaled(&o, 2));
    }
}

#[test]
fn circuit_inverse_restores_the_input() {
    let net = Net {
        n: 6,
        layers: 3,
        params: (0..36).map(|i| (i * i + 1) % 3).collect(),
    };
    let (_, te) = points();
    for p in te.iter().take(10) {
        let mut s = encode(p);
        let o = s.clone();
        net.forward(&mut s);
        assert_eq!(s.norm_sum(), pow3(s.k));
        net.inverse(&mut s);
        assert!(s.equals_scaled(&o, s.k / 2));
    }
}

#[test]
fn trit_phase_circuits_are_stabilizer_circuits() {
    // every single-qutrit readout of the sealed v1 circuit is 0, 1/3 or 1 of 3^k
    let (tr, _) = points();
    for seed in 0..3i64 {
        let net = Net {
            n: 6,
            layers: 3,
            params: (0..36).map(|i| (i * 7 + seed * 5 + i * i) % 3).collect(),
        };
        for p in tr.iter().take(60) {
            let mut s = encode(p);
            net.forward(&mut s);
            let full = pow3(s.k);
            for x in s.marginal(0) {
                assert!(x == 0 || x == full || 3 * x == full, "{x} of {full}");
            }
        }
    }
}

#[test]
fn gguf_model_round_trip() {
    let m = Model {
        kv: vec![
            (
                "general.architecture".into(),
                Kv::Str("asolaria-qutrit-vqnn".into()),
            ),
            ("qnn.layers".into(), Kv::U32(3)),
        ],
        tensors: vec![
            ("branch_0.params".into(), vec![0, 1, 2, 2, 1]),
            ("virtual.coefficients".into(), vec![-1, 0, 1]),
        ],
    };
    let b = write(&m);
    let r = read(&b).unwrap();
    assert_eq!(r.str("general.architecture"), Some("asolaria-qutrit-vqnn"));
    assert_eq!(r.u32("qnn.layers"), Some(3));
    assert_eq!(r.tensor("virtual.coefficients"), Some(&[-1i8, 0, 1][..]));
    assert_eq!(r.tensor("branch_0.params"), Some(&[0i8, 1, 2, 2, 1][..]));
    let _ = State::basis(1, &[0]);
}
