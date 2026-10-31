//! v4: a real qutrit network with rational rotations, as sealed in PREREG-V4.hbp.
//! Amplitudes are arbitrary-precision integers; the true state is v / D with D the product
//! of a^2 + b^2 over the applied gates. Every energy is an exact rational.

use crate::bigint::Big;
use crate::ym_z3::{digits, index, physical, LINKS};

pub const A: i128 = 729;
pub const TRITS_PER_LINK: usize = 8;

/// A real state on n qutrits: amplitudes v, and the scales of the applied gates.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct StateR {
    pub n: usize,
    pub v: Vec<Big>,
    pub scales: Vec<i128>,
}

fn stride(q: usize) -> usize {
    3usize.pow(q as u32)
}

impl StateR {
    pub fn zero_state(n: usize) -> Self {
        let mut v = vec![Big::zero(); 3usize.pow(n as u32)];
        v[0] = Big::from_i128(1);
        StateR {
            n,
            v,
            scales: Vec::new(),
        }
    }
    /// R_ij(b) on qutrit q: entries a^2-b^2, -2ab, 2ab, a^2-b^2 on levels i, j; a^2+b^2 on the third.
    pub fn rotate(&mut self, q: usize, i: usize, j: usize, b: i128) {
        self.rotate_a(q, i, j, b, A);
    }
    /// R_ij(b) with tan(angle/2) = b/a
    pub fn rotate_a(&mut self, q: usize, i: usize, j: usize, b: i128, a: i128) {
        if b == 0 {
            return;
        }
        let k = 3 - i - j;
        let (c, s, d) = (a * a - b * b, 2 * a * b, a * a + b * b);
        let st = stride(q);
        for base in 0..self.v.len() {
            if (base / st) % 3 != 0 {
                continue;
            }
            let (xi, xj) = (&self.v[base + i * st], &self.v[base + j * st]);
            let ni = xi.mul_i128(c).sub(&xj.mul_i128(s));
            let nj = xi.mul_i128(s).add(&xj.mul_i128(c));
            let nk = self.v[base + k * st].mul_i128(d);
            self.v[base + i * st] = ni;
            self.v[base + j * st] = nj;
            self.v[base + k * st] = nk;
        }
        self.scales.push(d);
    }
    /// SUM_{c -> t}: |x_c, x_t> -> |x_c, x_t + s x_c>
    pub fn sum(&mut self, c: usize, t: usize, s: i64) {
        let st = stride(t);
        let sc = stride(c);
        let mut out = vec![Big::zero(); self.v.len()];
        for (idx, z) in self.v.iter().enumerate() {
            let dc = ((idx / sc) % 3) as i64;
            let dt = (idx / st) % 3;
            let nt = (dt as i64 + s * dc).rem_euclid(3) as usize;
            out[idx - dt * st + nt * st] = z.clone();
        }
        self.v = out;
    }
    pub fn norm_sq(&self) -> Big {
        self.v.iter().fold(Big::zero(), |acc, z| acc.add(&z.mul(z)))
    }
    /// the product of the scales of the applied gates
    pub fn scale(&self) -> Big {
        self.scales
            .iter()
            .fold(Big::from_i128(1), |acc, &d| acc.mul_i128(d))
    }
}

/// b = 27 p0 + 9 p1 + 3 p2 + p3 from four balanced trits
pub fn b_of(p: &[i64]) -> i128 {
    i128::from(27 * p[0] + 9 * p[1] + 3 * p[2] + p[3])
}

/// The v4 network: L layers of [SUM ring, then R_01(b), R_02(b') on every link].
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NetR {
    pub n: usize,
    pub layers: usize,
    pub params: Vec<i64>,
}

impl NetR {
    pub fn param_count(n: usize, layers: usize) -> usize {
        TRITS_PER_LINK * n * layers
    }
    fn bs(&self, l: usize, q: usize) -> (i128, i128) {
        let i = (l * self.n + q) * TRITS_PER_LINK;
        (
            b_of(&self.params[i..i + 4]),
            b_of(&self.params[i + 4..i + 8]),
        )
    }
    pub fn layer(&self, l: usize, s: &mut StateR) {
        for q in 0..self.n {
            s.sum(q, (q + 1) % self.n, 1);
        }
        for q in 0..self.n {
            let (b1, b2) = self.bs(l, q);
            s.rotate(q, 0, 1, b1);
            s.rotate(q, 0, 2, b2);
        }
    }
    pub fn forward(&self, s: &mut StateR) {
        for l in 0..self.layers {
            self.layer(l, s);
        }
    }
    pub fn inverse(&self, s: &mut StateR) {
        for l in (0..self.layers).rev() {
            for q in (0..self.n).rev() {
                let (b1, b2) = self.bs(l, q);
                s.rotate(q, 0, 2, -b2);
                s.rotate(q, 0, 1, -b1);
            }
            for q in (0..self.n).rev() {
                s.sum(q, (q + 1) % self.n, -1);
            }
        }
    }
}

/// The Z3 Hamiltonian on gauge orbits, for exact energies of real states.
pub struct Z3Orbits {
    orbit_of: Vec<usize>,
    /// 81 / orbit size: the gauge projection is phi_c = weight * (sum of psi over the orbit)
    weight: Vec<i128>,
    size: Vec<i128>,
    mag: Vec<i128>,
    /// (o, o', number of (c in o, link l) with c + e_l in o')
    hop: Vec<(usize, usize, i128)>,
}

impl Default for Z3Orbits {
    fn default() -> Self {
        Self::new()
    }
}

impl Z3Orbits {
    pub fn new() -> Self {
        let p = physical();
        let n = p.reps.len();
        let mut counts = vec![0i128; n * n];
        for (c, &o) in p.orbit_of.iter().enumerate() {
            let g = digits(c);
            for l in 0..LINKS {
                let mut h = g;
                h[l] = (h[l] + 1).rem_euclid(3);
                counts[o * n + p.orbit_of[index(&h)]] += 1;
            }
        }
        let hop = counts
            .iter()
            .enumerate()
            .filter(|(_, &k)| k != 0)
            .map(|(i, &k)| (i / n, i % n, k))
            .collect();
        Z3Orbits {
            orbit_of: p.orbit_of,
            weight: p.sizes.iter().map(|&s| (81 / s) as i128).collect(),
            size: p.sizes.iter().map(|&s| s as i128).collect(),
            mag: p.mag.iter().map(|&m| i128::from(m)).collect(),
            hop,
        }
    }
    /// (E + r M, N) of the gauge-projected state, exact integers; None if the projection is zero.
    pub fn energy(&self, s: &StateR, r: i64) -> Option<(Big, Big)> {
        let mut sums = vec![Big::zero(); self.size.len()];
        for (c, z) in s.v.iter().enumerate() {
            if !z.is_zero() {
                let o = self.orbit_of[c];
                sums[o] = sums[o].add(z);
            }
        }
        let phi: Vec<Big> = sums
            .iter()
            .zip(self.weight.iter())
            .map(|(x, &w)| x.mul_i128(w))
            .collect();
        let sq: Vec<Big> = phi.iter().map(|x| x.mul(x)).collect();
        let mut n = Big::zero();
        let mut m = Big::zero();
        for (o, x) in sq.iter().enumerate() {
            n = n.add(&x.mul_i128(self.size[o]));
            m = m.add(&x.mul_i128(self.size[o] * self.mag[o]));
        }
        if n.is_zero() {
            return None;
        }
        let mut overlap = Big::zero();
        for &(o, o2, k) in &self.hop {
            if !phi[o].is_zero() && !phi[o2].is_zero() {
                overlap = overlap.add(&phi[o].mul(&phi[o2]).mul_i128(k));
            }
        }
        // sum_l <phi|(2 - X_l - X_l^dagger)|phi> = 2 L N - 2 sum_l <phi|X_l phi> for real phi
        let e = n.mul_i128(2 * LINKS as i128).sub(&overlap.mul_i128(2));
        Some((e.add(&m.mul_i128(i128::from(r))), n))
    }
}

/// sign of x0/x1 - y0/y1 for positive denominators
pub fn cmp_q(x: &(Big, Big), y: &(Big, Big)) -> i8 {
    x.0.mul(&y.1).sub(&y.0.mul(&x.1)).sign()
}

/// sign of x0/x1 - t/1000
pub fn cmp_milli_q(x: &(Big, Big), t: i128) -> i8 {
    x.0.mul_i128(1000).sub(&x.1.mul_i128(t)).sign()
}

/// t with energy in [t, t+1) milli, by exact bisection on [lo, hi)
pub fn milli_floor_q(x: &(Big, Big), lo: i128, hi: i128) -> Option<i128> {
    let (mut lo, mut hi) = (lo, hi);
    if cmp_milli_q(x, lo) < 0 || cmp_milli_q(x, hi) >= 0 {
        return None;
    }
    while hi - lo > 1 {
        let mid = (lo + hi) / 2;
        if cmp_milli_q(x, mid) >= 0 {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    Some(lo)
}

/// Coordinate descent over balanced trits, keeping strict decreases. Reuses the state after
/// layer 0 when a layer-1 trit changes. Returns (params, best energy, evaluations).
pub fn train(
    orbits: &Z3Orbits,
    seed: &[i64],
    layers: usize,
    r: i64,
    max_sweeps: usize,
) -> (Vec<i64>, (Big, Big), usize) {
    let per_layer = TRITS_PER_LINK * LINKS;
    let prefix = |params: &[i64]| {
        let net = NetR {
            n: LINKS,
            layers,
            params: params.to_vec(),
        };
        let mut s = StateR::zero_state(LINKS);
        net.layer(0, &mut s);
        s
    };
    let finish = |params: &[i64], start: &StateR| {
        let net = NetR {
            n: LINKS,
            layers,
            params: params.to_vec(),
        };
        let mut s = start.clone();
        for l in 1..layers {
            net.layer(l, &mut s);
        }
        orbits.energy(&s, r)
    };
    let mut params = seed.to_vec();
    let mut cache = prefix(&params);
    let mut best = finish(&params, &cache).expect("seed has a physical component");
    let mut evals = 1usize;
    for _ in 0..max_sweeps {
        let mut changed = false;
        for i in 0..params.len() {
            let keep = params[i];
            let mut best_v = keep;
            for v in -1..=1 {
                if v == keep {
                    continue;
                }
                params[i] = v;
                evals += 1;
                let e = if i < per_layer {
                    finish(&params, &prefix(&params))
                } else {
                    finish(&params, &cache)
                };
                if let Some(e) = e {
                    if cmp_q(&e, &best) < 0 {
                        best = e;
                        best_v = v;
                    }
                }
            }
            params[i] = best_v;
            if best_v != keep {
                changed = true;
                if i < per_layer {
                    cache = prefix(&params);
                }
            }
        }
        if !changed {
            break;
        }
    }
    (params, best, evals)
}
