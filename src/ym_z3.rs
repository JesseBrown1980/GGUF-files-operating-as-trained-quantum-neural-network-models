//! Z3 lattice gauge theory on the 2x2 periodic torus: the rotation subgroup of S3.
//! Links are qutrits g in Z3. Site s = j*2 + i; its x-link is qutrit 2s, its y-link 2s+1.
//! Plaquette at s: h = g_x(s) + g_y(s+x) - g_x(s+y) - g_y(s) mod 3.
//! H = J_E * E + J_B * M,  E = sum_links (2 - X - X^dagger),  M = sum_p 3*[h_p != 0].

use crate::eisenstein::{E, ZERO};
use crate::qutrit::State;
use std::collections::BTreeMap;

pub const LINKS: usize = 8;
pub const SITES: usize = 4;
pub const DIM: usize = 6561; // 3^8

fn sx(s: usize) -> usize {
    (s % 2 + 1) % 2 + (s / 2) * 2
}
fn sy(s: usize) -> usize {
    s % 2 + ((s / 2 + 1) % 2) * 2
}

pub fn digits(mut idx: usize) -> [i64; LINKS] {
    let mut g = [0i64; LINKS];
    for d in g.iter_mut() {
        *d = (idx % 3) as i64;
        idx /= 3;
    }
    g
}

pub fn index(g: &[i64; LINKS]) -> usize {
    g.iter()
        .rev()
        .fold(0usize, |acc, &d| acc * 3 + d.rem_euclid(3) as usize)
}

pub fn fluxes(g: &[i64; LINKS]) -> [i64; SITES] {
    let mut h = [0i64; SITES];
    for (s, hs) in h.iter_mut().enumerate() {
        *hs = (g[2 * s] + g[2 * sx(s) + 1] - g[2 * sy(s)] - g[2 * s + 1]).rem_euclid(3);
    }
    h
}

/// M(c) = 3 * number of plaquettes carrying flux.
pub fn magnetic(g: &[i64; LINKS]) -> i64 {
    3 * fluxes(g).iter().filter(|&&h| h != 0).count() as i64
}

/// Gauge transformation by a in Z3^4: the link s -> s' becomes g + a_s - a_{s'}.
pub fn gauge(g: &[i64; LINKS], a: &[i64; SITES]) -> [i64; LINKS] {
    let mut out = *g;
    for s in 0..SITES {
        out[2 * s] = (g[2 * s] + a[s] - a[sx(s)]).rem_euclid(3);
        out[2 * s + 1] = (g[2 * s + 1] + a[s] - a[sy(s)]).rem_euclid(3);
    }
    out
}

pub fn gauge_group() -> Vec<[i64; SITES]> {
    (0..81usize)
        .map(|n| {
            [
                (n % 3) as i64,
                ((n / 3) % 3) as i64,
                ((n / 9) % 3) as i64,
                (n / 27) as i64,
            ]
        })
        .collect()
}

pub struct Physical {
    /// orbit id of every configuration
    pub orbit_of: Vec<usize>,
    /// a representative per orbit and the orbit size
    pub reps: Vec<usize>,
    pub sizes: Vec<usize>,
    pub mag: Vec<i64>,
    /// the electric operator in the orthonormal orbit basis, upper triangle including the diagonal
    pub electric: BTreeMap<(usize, usize), i64>,
}

pub fn physical() -> Physical {
    let group = gauge_group();
    let mut orbit_of = vec![usize::MAX; DIM];
    let mut reps = Vec::new();
    let mut sizes = Vec::new();
    for c in 0..DIM {
        if orbit_of[c] != usize::MAX {
            continue;
        }
        let id = reps.len();
        let g = digits(c);
        let mut members: Vec<usize> = group.iter().map(|a| index(&gauge(&g, a))).collect();
        members.sort_unstable();
        members.dedup();
        for &m in &members {
            orbit_of[m] = id;
        }
        reps.push(c);
        sizes.push(members.len());
    }
    let mag: Vec<i64> = reps.iter().map(|&c| magnetic(&digits(c))).collect();
    let mut electric: BTreeMap<(usize, usize), i64> = BTreeMap::new();
    for (o, &c) in reps.iter().enumerate() {
        *electric.entry((o, o)).or_insert(0) += 2 * LINKS as i64;
        let g = digits(c);
        for l in 0..LINKS {
            for d in 1..=2 {
                let mut h = g;
                h[l] = (h[l] + d).rem_euclid(3);
                let o2 = orbit_of[index(&h)];
                if o2 >= o {
                    *electric.entry((o, o2)).or_insert(0) -= 1;
                }
            }
        }
    }
    Physical {
        orbit_of,
        reps,
        sizes,
        mag,
        electric,
    }
}

/// The matrix in the format of HEB-C's sturmfast: n, weights, magnetic diagonal, triples.
pub fn sturm_matrix(p: &Physical) -> String {
    let n = p.reps.len();
    let mut s = format!("{n}\n");
    s.push_str(&vec!["1"; n].join(" "));
    s.push('\n');
    s.push_str(
        &p.mag
            .iter()
            .map(i64::to_string)
            .collect::<Vec<_>>()
            .join(" "),
    );
    s.push('\n');
    for (&(i, j), &v) in &p.electric {
        if v != 0 {
            s.push_str(&format!("{i} {j} {v}\n"));
        }
    }
    s
}

fn conj(z: E) -> E {
    E::new(z.a - z.b, -z.b)
}

/// The gauge-projected trial state phi = sum_a U_a psi.
pub fn project(psi: &[E]) -> Vec<E> {
    let mut phi = vec![ZERO; DIM];
    for a in gauge_group() {
        for (c, &z) in psi.iter().enumerate() {
            if z != ZERO {
                phi[index(&gauge(&digits(c), &a))] += z;
            }
        }
    }
    phi
}

/// Exact energy of phi as (E_num, M_num, norm): <H> = (E_num + r*M_num) / norm.
pub fn energy_parts(phi: &[E]) -> (i128, i128, i128) {
    let norm: i128 = phi.iter().map(|z| z.norm()).sum();
    let mut e_num = 0i128;
    for l in 0..LINKS {
        // <phi | X_l phi>: (X_l phi)[c + e_l] = phi[c]
        let mut acc = ZERO;
        for (c, &z) in phi.iter().enumerate() {
            if z == ZERO {
                continue;
            }
            let mut g = digits(c);
            g[l] = (g[l] + 1).rem_euclid(3);
            acc += conj(phi[index(&g)]) * z;
        }
        // <phi|(2 - X - X^dagger)|phi> = 2 norm - 2 Re<phi|X phi>,  2 Re(a + b w) = 2a - b
        e_num += 2 * norm - (2 * i128::from(acc.a) - i128::from(acc.b));
    }
    let m_num: i128 = phi
        .iter()
        .enumerate()
        .map(|(c, z)| z.norm() * i128::from(magnetic(&digits(c))))
        .sum();
    (e_num, m_num, norm)
}

/// Energy as an exact fraction (numerator, denominator) at coupling r; None if phi = 0.
pub fn energy(s: &State, r: i64) -> Option<(i128, i128)> {
    let phi = project(&s.v);
    let (e, m, n) = energy_parts(&phi);
    if n == 0 {
        None
    } else {
        Some((e + i128::from(r) * m, n))
    }
}

/// a/b < c/d for positive b, d.
pub fn less(x: (i128, i128), y: (i128, i128)) -> bool {
    x.0 * y.1 < y.0 * x.1
}
