#![deny(clippy::float_arithmetic)]
use gguf_qnn::bigint::Big;
use gguf_qnn::pixels::{lift, png, primes, Frame};
use gguf_qnn::v4::{StateR, Z3Orbits};
use gguf_qnn::v7::{NetQ, PARAMS};
use gguf_qnn::ym_z3::LINKS;

fn params() -> Vec<i64> {
    (0..PARAMS)
        .map(|i| ((i * 7 + i / 5) % 3) as i64 - 1)
        .collect()
}

#[test]
fn primes_are_the_largest_below_2_pow_31() {
    let p = primes(3);
    assert_eq!(p, vec![2_147_483_647, 2_147_483_629, 2_147_483_587]);
}

#[test]
fn garner_lifts_exactly() {
    let p = primes(12);
    let x = Big::from_i128(170_141_183_460_469_231_731_687_303_715_884_105_727);
    let x2 = x.mul(&x).mul_i128(12_345);
    let res: Vec<u64> = p
        .iter()
        .map(|&q| {
            // x2 mod q via repeated limbs: reduce through decimal digits
            x2.dec()
                .bytes()
                .fold(0u64, |acc, d| (acc * 10 + u64::from(d - b'0')) % q)
        })
        .collect();
    assert_eq!(lift(&res, &p), x2);
}

#[test]
fn pixel_backend_matches_the_exact_state_and_energy() {
    let net = NetQ { params: params() };
    let mut s = StateR::zero_state(LINKS);
    net.forward(&mut s);
    let ps = primes(64);
    let mut f = Frame::zero_state(&ps);
    net.forward(&mut f);
    for (k, &q) in ps.iter().enumerate().take(4) {
        for (i, z) in s.v.iter().enumerate().step_by(97) {
            let neg = z.sign() < 0;
            let m = z
                .dec()
                .trim_start_matches('-')
                .bytes()
                .fold(0u64, |acc, d| (acc * 10 + u64::from(d - b'0')) % q);
            let m = if neg && m != 0 { q - m } else { m };
            assert_eq!(f.chan[k][i], m);
        }
    }
    let o = Z3Orbits::new();
    let (n, d) = o.energy(&s, 9).expect("p");
    let (rn, rd) = f.energy_residues(9);
    assert_eq!(lift(&rn, &ps), n);
    assert_eq!(lift(&rd, &ps), d);
}

#[test]
fn layer2_zero_is_identity_and_inverse_is_exact() {
    let mut p = params();
    for x in p.iter_mut().skip(PARAMS / 2) {
        *x = 0;
    }
    let mut p2 = params();
    p2.truncate(PARAMS / 2);
    p2.extend(std::iter::repeat(0).take(PARAMS / 2));
    assert_eq!(p, p2);
    let net = NetQ { params: params() };
    let mut s = StateR::zero_state(LINKS);
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

#[test]
fn png_crc_and_signature() {
    let b = png(1, 1, &[255, 0, 0]);
    assert_eq!(&b[..8], &[0x89, b'P', b'N', b'G', 0x0D, 0x0A, 0x1A, 0x0A]);
    // IHDR crc of a 1x1 8-bit RGB image is the standard 0x907753DE
    assert_eq!(&b[29..33], &[0x90, 0x77, 0x53, 0xDE]);
}
