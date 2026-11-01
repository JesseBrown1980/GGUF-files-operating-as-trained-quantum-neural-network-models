#![deny(clippy::float_arithmetic)]
use gguf_qnn::torus::{StateF, Torus};
use gguf_qnn::v4::{StateR, Z3Orbits};

use gguf_qnn::v8::{cuts, NetT, LINKS, PARAMS};
use gguf_qnn::ym_z3::{digits, magnetic};

#[test]
fn the_2x2_torus_matches_the_sealed_z3_code() {
    let t = Torus::new(2, 2);
    assert_eq!(t.reps.len(), 243);
    for c in (0..6561).step_by(37) {
        assert_eq!(t.magnetic(&t.digits(c)), magnetic(&digits(c)));
    }
    let o = Z3Orbits::new();
    let mut s = StateR::zero_state(8);
    for q in 0..8 {
        s.rotate(q, 0, 1, 7);
        s.rotate(q, 0, 2, 7);
    }
    s.sum(0, 4, 1);
    let (a, b) = o.energy(&s, 9).expect("p");
    let (c, d) = t.energy_exact(&s.v, 9).expect("p");
    assert_eq!(a.mul(&d), c.mul(&b));
    let sealed = std::fs::read_to_string("results-ym-z3/z3-2x2.mat").expect("sealed matrix");
    assert_eq!(t.sturm_matrix(), sealed);
}

#[test]
fn the_3x2_torus_cuts_carry_no_flux() {
    let t = Torus::new(3, 2);
    assert_eq!(t.reps.len(), 2187);
    for (c, tg) in cuts() {
        for h in 1..3usize {
            let idx = h * 3usize.pow(c as u32) + h * 3usize.pow(tg as u32);
            let mut g = t.digits(idx);
            // a row of y-links needs all three equal: complete the cut
            if c % 2 == 1 {
                for (c2, t2) in cuts() {
                    if c2 == c {
                        g[t2] = h as i64;
                    }
                }
            }
            assert_eq!(t.magnetic(&g), 0, "cut {c}->{tg}");
        }
    }
}

#[test]
fn network_identity_exact_and_fixed_point_close() {
    let t = Torus::new(3, 2);
    let zero = NetT {
        params: vec![0; PARAMS],
    };
    let mut s = StateR::zero_state(LINKS);
    zero.forward(&mut s);
    let (n, d) = t.energy_exact(&s.v, 9).expect("p");
    assert_eq!(n, d.mul_i128(24));
    let params: Vec<i64> = (0..PARAMS)
        .map(|i| if i % 16 == 5 || i % 16 == 13 { 1 } else { 0 })
        .collect();
    let net = NetT { params };
    let mut s = StateR::zero_state(LINKS);
    let o = s.clone();
    net.forward(&mut s);
    let dd = s.scale();
    assert_eq!(s.norm_sq(), dd.mul(&dd));
    let (en, ed) = t.energy_exact(&s.v, 9).expect("p");
    net.inverse(&mut s);
    assert_eq!(
        s.v,
        o.v.iter().map(|x| x.mul(&dd).mul(&dd)).collect::<Vec<_>>()
    );
    let mut f = StateF::zero_state(LINKS);
    net.forward(&mut f);
    let ef = t.energy_fixed(&f.v, 9).expect("p");
    // exact milli floor against the fixed-point estimate
    let exact_milli = gguf_qnn::v4::milli_floor_q(&(en, ed), 0, 100_000_000).expect("m");
    let fixed_milli = (ef * 1000) >> 40;
    assert!(
        (exact_milli - fixed_milli).abs() <= 1,
        "{exact_milli} {fixed_milli}"
    );
}

#[test]
fn sector_matrices_are_w_self_adjoint() {
    let (_, k22, a22) = Torus::new(2, 2).sector_matrix();
    assert!(a22);
    let t = Torus::new(3, 2);
    let (m, k, a) = t.sector_matrix();
    assert!(a && t.perron_frobenius_ok());
    assert!(k22 < 243 && k < 2187);
    std::fs::write(std::env::temp_dir().join("z3-3x2-sector-probe.mat"), m).expect("write");
    println!("SECTOR|k22={k22}|k32={k}");
}

#[test]
fn v9_plaquette_layer_identity_and_exact_inverse() {
    use gguf_qnn::v9::NetV9;
    let t = Torus::new(3, 2);
    let mut s = StateR::zero_state(LINKS);
    NetV9 {
        params: vec![0; PARAMS],
    }
    .forward(&mut s);
    let (n, d) = t.energy_exact(&s.v, 9).expect("p");
    assert_eq!(n, d.mul_i128(24));
    let params: Vec<i64> = (0..PARAMS)
        .map(|i| {
            if i % 16 == 7 || (i > PARAMS / 2 && i % 16 == 15) {
                1
            } else {
                0
            }
        })
        .collect();
    let net = NetV9 { params };
    let mut s = StateR::zero_state(LINKS);
    let o = s.clone();
    net.forward(&mut s);
    let dd = s.scale();
    assert_eq!(s.norm_sq(), dd.mul(&dd));
    net.inverse(&mut s);
    assert_eq!(
        s.v,
        o.v.iter().map(|x| x.mul(&dd).mul(&dd)).collect::<Vec<_>>()
    );
}

#[test]
fn gauge_fixed_basis_matches_the_orbit_basis_on_3x2() {
    use gguf_qnn::bigint::Big;
    use gguf_qnn::gfix::GaugeFixed;
    let gf = GaugeFixed::new(3, 2);
    assert_eq!(gf.free.len(), 7);
    let t = Torus::new(3, 2);
    // a v8-style state, its orbit sums as gauge-fixed amplitudes: same exact energy
    let params: Vec<i64> = (0..PARAMS)
        .map(|i| if i % 16 == 5 || i % 16 == 13 { 1 } else { 0 })
        .collect();
    let mut s = StateR::zero_state(LINKS);
    NetT { params }.forward(&mut s);
    let mut x = vec![Big::zero(); gf.dim];
    for (c, z) in s.v.iter().enumerate() {
        if !z.is_zero() {
            let f = gf.fix(&t.digits(c));
            x[f] = x[f].add(z);
        }
    }
    let (a, b) = t.energy_exact(&s.v, 9).expect("p");
    let (c, d) = gf.energy_exact(&x, 9).expect("p");
    assert_eq!(a.mul(&d), c.mul(&b));
    let (_, k, adj) = gf.block_matrix();
    assert!(adj);
    println!("BLOCK3x2|classes={k}");
}

#[test]
fn v11_tree_frames_move_one_qutrit_and_invert_exactly() {
    use gguf_qnn::gfix::GaugeFixed;
    use gguf_qnn::v11::{params_v11, tree_frames, NetV11};
    let gf = GaugeFixed::new(3, 3);
    assert_eq!(tree_frames(&gf).len(), 8);
    let n = params_v11(&gf);
    let p: Vec<i64> = (0..n)
        .map(|i| if i % 16 == 7 || i % 16 == 15 { 1 } else { 0 })
        .collect();
    let net = NetV11 {
        gf: &gf,
        params: &p,
    };
    let mut s = StateR::zero_state(gf.free.len());
    let o = s.clone();
    net.forward(&mut s);
    let d = s.scale();
    assert_eq!(s.norm_sq(), d.mul(&d));
    net.inverse(&mut s);
    assert_eq!(
        s.v,
        o.v.iter().map(|x| x.mul(&d).mul(&d)).collect::<Vec<_>>()
    );
}
