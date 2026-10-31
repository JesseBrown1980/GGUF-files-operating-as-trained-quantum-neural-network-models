//! Z[zeta_9]: a0 + a1 z + ... + a5 z^5 with z^6 = -z^3 - 1 (the 9th cyclotomic polynomial
//! x^6 + x^3 + 1). omega = z^3. Every v2 amplitude lives here.

use crate::real3::R3;

pub type Z9 = [i64; 6];
pub const ZERO9: Z9 = [0; 6];
pub const ONE9: Z9 = [1, 0, 0, 0, 0, 0];

/// z * zeta
pub fn times_zeta(a: &Z9) -> Z9 {
    [-a[5], a[0], a[1], a[2] - a[5], a[3], a[4]]
}

/// z * zeta^e, e taken mod 9
pub fn times_zeta_pow(a: &Z9, e: i64) -> Z9 {
    let mut r = *a;
    for _ in 0..e.rem_euclid(9) {
        r = times_zeta(&r);
    }
    r
}

pub fn add(a: &Z9, b: &Z9) -> Z9 {
    let mut r = *a;
    for (x, y) in r.iter_mut().zip(b.iter()) {
        *x += y;
    }
    r
}

/// Reduce a polynomial of degree <= 16 with x^d = -x^(d-3) - x^(d-6), d >= 6.
fn reduce(mut d: Vec<i128>) -> [i128; 6] {
    for deg in (6..d.len()).rev() {
        let c = d[deg];
        if c != 0 {
            d[deg] = 0;
            d[deg - 3] -= c;
            d[deg - 6] -= c;
        }
    }
    [d[0], d[1], d[2], d[3], d[4], d[5]]
}

/// complex conjugate: zeta^i -> zeta^(9 - i)
pub fn conj(a: &Z9) -> [i128; 6] {
    let mut d = vec![0i128; 9];
    d[0] = i128::from(a[0]);
    for i in 1..6 {
        d[9 - i] += i128::from(a[i]);
    }
    reduce(d)
}

/// a * b, with i128 coefficients
pub fn mul_wide(a: &[i128; 6], b: &Z9) -> [i128; 6] {
    let mut d = vec![0i128; 11];
    for i in 0..6 {
        for j in 0..6 {
            d[i + j] += a[i] * i128::from(b[j]);
        }
    }
    reduce(d)
}

pub fn add_wide(a: &[i128; 6], b: &[i128; 6]) -> [i128; 6] {
    let mut r = *a;
    for (x, y) in r.iter_mut().zip(b.iter()) {
        *x += y;
    }
    r
}

/// A real element of Z[zeta_9] written in the basis 1, theta, theta^2 (theta = zeta + zeta^-1).
/// theta = z - z^2 - z^5 and theta^2 = 2 - z + z^2 - z^4 in the power basis.
pub fn to_real(p: &[i128; 6]) -> R3 {
    let c2 = -p[4];
    let c1 = p[1] - p[4];
    let c0 = p[0] + 2 * p[4];
    assert_eq!(p[3], 0, "not real: z^3 coefficient");
    assert_eq!(p[2], -c1 + c2, "not real: z^2 coefficient");
    assert_eq!(p[5], -c1, "not real: z^5 coefficient");
    R3::from_ints(c0, c1, c2)
}

/// |a|^2 as an element of Z[theta]
pub fn norm(a: &Z9) -> R3 {
    to_real(&mul_wide(&conj(a), a))
}

/// 2 Re(<u|v> term) = conj(u) v + u conj(v), as an element of Z[theta]
pub fn two_re_wide(w: &[i128; 6]) -> R3 {
    // conj of a wide element
    let mut d = vec![0i128; 9];
    d[0] = w[0];
    for i in 1..6 {
        d[9 - i] += w[i];
    }
    let c = reduce(d);
    to_real(&add_wide(w, &c))
}
