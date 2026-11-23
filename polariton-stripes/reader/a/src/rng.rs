//! The draws of twens 0.4.0 (polariton-bridge/engines/ensemble/src/main.rs, sha256 1d768fa9..., at 4a97736: `Rng`,
//! `splitmix`, `ens_draw`), ported operation for operation in integers, so a table point's draws g, rot and eta rebuild
//! from (seed, idx) (review N8).

use crate::eng::{isqrt, ONE, Q};

/// The per-sample derivation multiplier (BRIDGE_SAMPLING per_sample).
pub const FNV: u64 = 0x1000_0000_01B3;

fn splitmix(z: &mut u64) -> u64 {
    *z = z.wrapping_add(0x9E37_79B9_7F4A_7C15);
    let mut v = *z;
    v = (v ^ (v >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    v = (v ^ (v >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    v ^ (v >> 31)
}

/// xoshiro256** seeded by splitmix64.
pub struct Rng {
    s: [u64; 4],
}

impl Rng {
    pub fn new(seed: u64) -> Self {
        let mut z = seed;
        Self {
            s: [
                splitmix(&mut z),
                splitmix(&mut z),
                splitmix(&mut z),
                splitmix(&mut z),
            ],
        }
    }

    /// The generator of sample `idx` of the point's seed.
    pub fn sample(seed: u64, idx: u64) -> Self {
        Self::new(seed.wrapping_add(idx.wrapping_mul(FNV)))
    }

    /// The engine's `next` (named `next_u64` here: clippy refuses a method named `next` outside `Iterator`).
    pub fn next_u64(&mut self) -> u64 {
        let result = self.s[1].wrapping_mul(5).rotate_left(7).wrapping_mul(9);
        let t = self.s[1] << 17;
        self.s[2] ^= self.s[0];
        self.s[3] ^= self.s[1];
        self.s[1] ^= self.s[2];
        self.s[0] ^= self.s[3];
        self.s[2] ^= t;
        self.s[3] = self.s[3].rotate_left(45);
        result
    }

    /// The twens Gaussian: (popcount of 4096 random bits - 2048) 2^35.
    pub fn gauss(&mut self) -> i64 {
        let mut c: i64 = 0;
        for _ in 0..64 {
            c += i64::from(self.next_u64().count_ones());
        }
        (c - 2048) << (Q - 5)
    }

    /// MODE0's unit vector (cos, sin) at 2^40 by rejection in the disc (30-bit integers), with
    /// eta = ceil((a^2 + b^2 - r^2) 2^40 / (2 r^2)), r = isqrt(a^2 + b^2).
    pub fn unit30x(&mut self) -> (i64, i64, u128) {
        loop {
            let a = (self.next_u64() >> 33) as i64 - (1i64 << 30);
            let b = (self.next_u64() >> 33) as i64 - (1i64 << 30);
            let r2 = i128::from(a) * i128::from(a) + i128::from(b) * i128::from(b);
            if !((1i128 << 58)..=(1i128 << 60)).contains(&r2) {
                continue;
            }
            let r = isqrt(r2 as u128) as i128;
            let d = (r2 - r * r) as u128;
            let rr = (r * r) as u128;
            let eta = (d << Q).div_ceil(2 * rr);
            return (
                ((i128::from(a) << Q) / r) as i64,
                ((i128::from(b) << Q) / r) as i64,
                eta,
            );
        }
    }
}

/// The draws of sample `idx` as `ens_draw` makes them: g0..g5, then MODE0's (rot, eta) when MODE0 is on, else
/// (2^40, 0) and 0.
pub fn draws(seed: u64, idx: u64, mode0: bool) -> ([i64; 6], [i64; 2], u128) {
    let mut rng = Rng::sample(seed, idx);
    let mut g = [0i64; 6];
    for x in g.iter_mut() {
        *x = rng.gauss();
    }
    if mode0 {
        let (c, s, eta) = rng.unit30x();
        (g, [c, s], eta)
    } else {
        (g, [ONE, 0], 0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn splitmix64_reference_vector() {
        let mut z = 0u64;
        let got = [splitmix(&mut z), splitmix(&mut z), splitmix(&mut z)];
        assert_eq!(
            got,
            [
                0xE220_A839_7B1D_CDAF,
                0x6E78_9E6A_A1B9_65F4,
                0x06C4_5D18_8009_454F
            ]
        );
    }

    #[test]
    fn xoshiro256starstar_reference_vector() {
        let mut r = Rng { s: [1, 2, 3, 4] };
        let got = [r.next_u64(), r.next_u64(), r.next_u64(), r.next_u64()];
        assert_eq!(got, [11520, 0, 1_509_978_240, 1_215_971_899_390_074_240]);
    }

    #[test]
    fn draws_are_coin_counts_and_unit_vectors() {
        for idx in [0u64, 1, 4095, 1 << 20] {
            let (g, rot, eta) = draws(0x0123_4567_89AB_CDEF, idx, true);
            for x in g {
                assert_eq!(x % (1 << 35), 0);
                assert!((x >> 35).abs() <= 2048);
            }
            let n2 =
                i128::from(rot[0]) * i128::from(rot[0]) + i128::from(rot[1]) * i128::from(rot[1]);
            let one2 = 1i128 << 80;
            assert!((n2 - one2).abs() < one2 >> 27, "{n2}");
            assert!(eta < 1 << 12, "{eta}");
            assert!(rot[0].unsigned_abs() <= crate::eng::ROT_LIMIT);
            let (g0, rot0, eta0) = draws(0x0123_4567_89AB_CDEF, idx, false);
            assert_eq!((g0, rot0, eta0), (g, [ONE, 0], 0));
        }
    }
}
