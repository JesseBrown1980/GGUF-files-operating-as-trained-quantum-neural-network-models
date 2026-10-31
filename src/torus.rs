//! Z3 lattice gauge theory on an LX x LY periodic torus (v8: 3 x 2). Site s = y*LX + x; its x-link is
//! qutrit 2s, its y-link 2s+1. Plaquette at s: h = g_x(s) + g_y(s+x) - g_x(s+y) - g_y(s) mod 3.
//! H = E + r M, E = sum_links (2 - X - X^dagger), M = sum_p 3*[h_p != 0]: the conventions of ym_z3.

use crate::bigint::Big;
use std::collections::BTreeMap;

pub struct Torus {
    pub lx: usize,
    pub ly: usize,
    pub links: usize,
    pub dim: usize,
    pub orbit_of: Vec<usize>,
    pub reps: Vec<usize>,
    pub sizes: Vec<usize>,
    pub mag: Vec<i64>,
    /// (o, o', number of (c in o, link l) with c + e_l in o')
    pub hop: Vec<(usize, usize, i64)>,
    pub group_order: usize,
}

fn p3(k: usize) -> usize {
    3usize.pow(k as u32)
}

impl Torus {
    fn sx(&self, s: usize) -> usize {
        (s / self.lx) * self.lx + (s % self.lx + 1) % self.lx
    }
    fn sy(&self, s: usize) -> usize {
        ((s / self.lx + 1) % self.ly) * self.lx + s % self.lx
    }
    pub fn digits(&self, mut idx: usize) -> Vec<i64> {
        let mut g = vec![0i64; self.links];
        for d in &mut g {
            *d = (idx % 3) as i64;
            idx /= 3;
        }
        g
    }
    pub fn index(&self, g: &[i64]) -> usize {
        g.iter()
            .rev()
            .fold(0usize, |a, &d| a * 3 + d.rem_euclid(3) as usize)
    }
    pub fn magnetic(&self, g: &[i64]) -> i64 {
        let sites = self.lx * self.ly;
        (0..sites)
            .filter(|&s| {
                (g[2 * s] + g[2 * self.sx(s) + 1] - g[2 * self.sy(s)] - g[2 * s + 1]).rem_euclid(3)
                    != 0
            })
            .count() as i64
            * 3
    }
    pub fn gauge(&self, g: &[i64], a: &[i64]) -> Vec<i64> {
        let mut out = g.to_vec();
        for s in 0..self.lx * self.ly {
            out[2 * s] = (g[2 * s] + a[s] - a[self.sx(s)]).rem_euclid(3);
            out[2 * s + 1] = (g[2 * s + 1] + a[s] - a[self.sy(s)]).rem_euclid(3);
        }
        out
    }
    pub fn new(lx: usize, ly: usize) -> Torus {
        let links = 2 * lx * ly;
        let dim = p3(links);
        let sites = lx * ly;
        let mut t = Torus {
            lx,
            ly,
            links,
            dim,
            orbit_of: vec![usize::MAX; dim],
            reps: Vec::new(),
            sizes: Vec::new(),
            mag: Vec::new(),
            hop: Vec::new(),
            group_order: p3(sites),
        };
        let group: Vec<Vec<i64>> = (0..p3(sites))
            .map(|n| (0..sites).map(|i| ((n / p3(i)) % 3) as i64).collect())
            .collect();
        for c in 0..dim {
            if t.orbit_of[c] != usize::MAX {
                continue;
            }
            let id = t.reps.len();
            let g = t.digits(c);
            let mut members: Vec<usize> = group.iter().map(|a| t.index(&t.gauge(&g, a))).collect();
            members.sort_unstable();
            members.dedup();
            for &m in &members {
                t.orbit_of[m] = id;
            }
            t.reps.push(c);
            t.sizes.push(members.len());
        }
        t.mag = t.reps.iter().map(|&c| t.magnetic(&t.digits(c))).collect();
        let mut counts: BTreeMap<(usize, usize), i64> = BTreeMap::new();
        for c in 0..dim {
            let o = t.orbit_of[c];
            for l in 0..links {
                let st = p3(l);
                let d = (c / st) % 3;
                let up = c - d * st + ((d + 1) % 3) * st;
                *counts.entry((o, t.orbit_of[up])).or_insert(0) += 1;
            }
        }
        t.hop = counts.into_iter().map(|((a, b), k)| (a, b, k)).collect();
        t
    }
    /// The orthonormal-orbit-basis matrix in sturmfast's format (as ym_z3::sturm_matrix): n, unit
    /// weights, the magnetic diagonal, upper triples of E. Requires equal orbit sizes.
    pub fn sturm_matrix(&self) -> String {
        let n = self.reps.len();
        assert!(
            self.sizes.iter().all(|&s| s == self.sizes[0]),
            "equal orbit sizes"
        );
        let mut e: BTreeMap<(usize, usize), i64> = BTreeMap::new();
        for (o, &c) in self.reps.iter().enumerate() {
            *e.entry((o, o)).or_insert(0) += 2 * self.links as i64;
            for l in 0..self.links {
                for d in 1..=2usize {
                    let st = p3(l);
                    let x = (c / st) % 3;
                    let h = c - x * st + ((x + d) % 3) * st;
                    let o2 = self.orbit_of[h];
                    if o2 >= o {
                        *e.entry((o, o2)).or_insert(0) -= 1;
                    }
                }
            }
        }
        let mut s = format!("{n}\n");
        s.push_str(&vec!["1"; n].join(" "));
        s.push('\n');
        s.push_str(
            &self
                .mag
                .iter()
                .map(i64::to_string)
                .collect::<Vec<_>>()
                .join(" "),
        );
        s.push('\n');
        for (&(i, j), &v) in &e {
            if v != 0 {
                s.push_str(&format!("{i} {j} {v}\n"));
            }
        }
        s
    }
    fn weight(&self, o: usize) -> i128 {
        (self.group_order / self.sizes[o]) as i128
    }
    /// exact (E + r M, N) of the gauge-projected real state
    pub fn energy_exact(&self, v: &[Big], r: i64) -> Option<(Big, Big)> {
        let mut sums = vec![Big::zero(); self.reps.len()];
        for (c, z) in v.iter().enumerate() {
            if !z.is_zero() {
                let o = self.orbit_of[c];
                sums[o] = sums[o].add(z);
            }
        }
        let phi: Vec<Big> = sums
            .iter()
            .enumerate()
            .map(|(o, x)| x.mul_i128(self.weight(o)))
            .collect();
        let (mut n, mut m, mut ov) = (Big::zero(), Big::zero(), Big::zero());
        for (o, x) in phi.iter().enumerate() {
            let sq = x.mul(x).mul_i128(self.sizes[o] as i128);
            m = m.add(&sq.mul_i128(i128::from(self.mag[o])));
            n = n.add(&sq);
        }
        if n.is_zero() {
            return None;
        }
        for &(o, o2, k) in &self.hop {
            if !phi[o].is_zero() && !phi[o2].is_zero() {
                ov = ov.add(&phi[o].mul(&phi[o2]).mul_i128(i128::from(k)));
            }
        }
        let e = n.mul_i128(2 * self.links as i128).sub(&ov.mul_i128(2));
        Some((e.add(&m.mul_i128(i128::from(r))), n))
    }
    /// fixed-point energy (units 2^-40) of a fixed-point state; used only to rank training candidates
    pub fn energy_fixed(&self, v: &[i64], r: i64) -> Option<i128> {
        let mut sums = vec![0i128; self.reps.len()];
        for (c, &z) in v.iter().enumerate() {
            if z != 0 {
                sums[self.orbit_of[c]] += i128::from(z);
            }
        }
        let phi: Vec<i128> = sums
            .iter()
            .enumerate()
            .map(|(o, &x)| x * self.weight(o))
            .collect();
        let (mut n, mut m, mut ov) = (0i128, 0i128, 0i128);
        for (o, &x) in phi.iter().enumerate() {
            let sq = x * x * self.sizes[o] as i128;
            n += sq;
            m += sq * i128::from(self.mag[o]);
        }
        for &(o, o2, k) in &self.hop {
            ov += phi[o] * phi[o2] * i128::from(k);
        }
        let num = n * 2 * self.links as i128 - 2 * ov + m * i128::from(r);
        let den = n >> 48;
        if den == 0 {
            return None;
        }
        Some(((num >> 48) << 40) / den)
    }
}

impl Torus {
    /// the image of configuration index c under the translation (dx, dy)
    fn translate(&self, c: usize, dx: usize, dy: usize) -> usize {
        let g = self.digits(c);
        let mut h = vec![0i64; self.links];
        for y in 0..self.ly {
            for x in 0..self.lx {
                let s = y * self.lx + x;
                let t = ((y + dy) % self.ly) * self.lx + (x + dx) % self.lx;
                h[2 * t] = g[2 * s];
                h[2 * t + 1] = g[2 * s + 1];
            }
        }
        self.index(&h)
    }
    /// The translation-invariant sector in sturmfast's weighted format: classes of gauge orbits under
    /// the torus translations, weights = class sizes, Z_ij = moves from the class representative's
    /// representative configuration into class j (W-self-adjoint: w_i Z_ij = w_j Z_ji, checked).
    /// Returns (matrix text, number of classes, w-self-adjoint).
    pub fn sector_matrix(&self) -> (String, usize, bool) {
        let n = self.reps.len();
        let mut class_of = vec![usize::MAX; n];
        let mut reps: Vec<usize> = Vec::new();
        let mut w: Vec<i64> = Vec::new();
        for o in 0..n {
            if class_of[o] != usize::MAX {
                continue;
            }
            let id = reps.len();
            let mut members: Vec<usize> = Vec::new();
            for dy in 0..self.ly {
                for dx in 0..self.lx {
                    members.push(self.orbit_of[self.translate(self.reps[o], dx, dy)]);
                }
            }
            members.sort_unstable();
            members.dedup();
            for &m in &members {
                class_of[m] = id;
            }
            reps.push(o);
            w.push(members.len() as i64);
        }
        let k = reps.len();
        let mut z: Vec<BTreeMap<usize, i64>> = vec![BTreeMap::new(); k];
        for (i, &o) in reps.iter().enumerate() {
            let c = self.reps[o];
            *z[i].entry(i).or_insert(0) += 2 * self.links as i64;
            for l in 0..self.links {
                for d in 1..=2usize {
                    let st = p3(l);
                    let x = (c / st) % 3;
                    let h = c - x * st + ((x + d) % 3) * st;
                    *z[i].entry(class_of[self.orbit_of[h]]).or_insert(0) -= 1;
                }
            }
        }
        let mut adjoint = true;
        for i in 0..k {
            for (&j, &v) in &z[i] {
                adjoint &= w[i] * v == w[j] * z[j].get(&i).copied().unwrap_or(0);
            }
        }
        let mags: Vec<String> = reps.iter().map(|&o| self.mag[o].to_string()).collect();
        let mut s = format!("{k}\n");
        s.push_str(&w.iter().map(i64::to_string).collect::<Vec<_>>().join(" "));
        s.push('\n');
        s.push_str(&mags.join(" "));
        s.push('\n');
        for (i, row) in z.iter().enumerate() {
            for (&j, &v) in row.range(i..) {
                if v != 0 {
                    s.push_str(&format!("{i} {j} {v}\n"));
                }
            }
        }
        (s, k, adjoint)
    }
    /// every off-diagonal hop count is a move (so H's off-diagonal entries are non-positive) and the
    /// orbit graph is connected
    pub fn perron_frobenius_ok(&self) -> bool {
        let n = self.reps.len();
        let mut adj: Vec<Vec<usize>> = vec![Vec::new(); n];
        for &(a, b, k) in &self.hop {
            if k <= 0 {
                return false;
            }
            if a != b {
                adj[a].push(b);
            }
        }
        let mut seen = vec![false; n];
        let mut stack = vec![0usize];
        seen[0] = true;
        while let Some(u) = stack.pop() {
            for &v in &adj[u] {
                if !seen[v] {
                    seen[v] = true;
                    stack.push(v);
                }
            }
        }
        seen.iter().all(|&x| x)
    }
}

fn isqrt_ratio(a: &Big, b: &Big) -> i128 {
    let (mut lo, mut hi) = (0i128, 1i128 << 40);
    while hi - lo > 1 {
        let mid = (lo + hi) / 2;
        if b.mul_i128(mid * mid).sub(a).sign() <= 0 {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    lo
}

impl Torus {
    /// (fraction of the norm that survives gauge projection, per mille; residual |(H - E) phi| / |phi|
    /// of the projected state, milli), both floors; requires equal orbit sizes
    pub fn projection_and_residual(&self, v: &[Big], r: i64, e: &(Big, Big)) -> (i128, i128) {
        let n = self.reps.len();
        let mut s = vec![Big::zero(); n];
        for (c, z) in v.iter().enumerate() {
            if !z.is_zero() {
                s[self.orbit_of[c]] = s[self.orbit_of[c]].add(z);
            }
        }
        let w = (self.group_order / self.sizes[0]) as i128;
        let size = self.sizes[0] as i128;
        let num_p = s
            .iter()
            .fold(Big::zero(), |a, x| a.add(&x.mul(x)))
            .mul_i128(w);
        let den_p = v
            .iter()
            .fold(Big::zero(), |a, x| a.add(&x.mul(x)))
            .mul_i128(self.group_order as i128);
        let frac = isqrt_ratio(&num_p.mul(&num_p).mul_i128(1_000_000), &den_p.mul(&den_p));
        let phi: Vec<Big> = s.iter().map(|x| x.mul_i128(w)).collect();
        let mut a: Vec<Big> = phi
            .iter()
            .enumerate()
            .map(|(o, x)| {
                x.mul_i128(
                    size * (2 * self.links as i128 + i128::from(r) * i128::from(self.mag[o])),
                )
            })
            .collect();
        for &(o, o2, k) in &self.hop {
            a[o] = a[o].sub(&phi[o2].mul_i128(i128::from(k)));
            a[o2] = a[o2].sub(&phi[o].mul_i128(i128::from(k)));
        }
        let q: Vec<Big> = (0..n)
            .map(|o| e.1.mul(&a[o]).sub(&e.0.mul(&phi[o]).mul_i128(size)))
            .collect();
        let rn = q.iter().fold(Big::zero(), |acc, x| acc.add(&x.mul(x)));
        let rd = phi
            .iter()
            .fold(Big::zero(), |acc, x| acc.add(&x.mul(x)))
            .mul(&e.1)
            .mul(&e.1)
            .mul_i128(size * size);
        (frac, isqrt_ratio(&rn.mul_i128(1_000_000), &rd))
    }
}

/// A fixed-point real state at scale 2^36, gates applied with rounded integer division (training only).
#[derive(Clone)]
pub struct StateF {
    pub v: Vec<i64>,
}

pub const FIXED_ONE: i64 = 1 << 36;

fn round_div(n: i128, d: i128) -> i64 {
    let q = if n >= 0 {
        (n + d / 2) / d
    } else {
        -((-n + d / 2) / d)
    };
    q as i64
}

impl StateF {
    pub fn zero_state(links: usize) -> StateF {
        let mut v = vec![0i64; p3(links)];
        v[0] = FIXED_ONE;
        StateF { v }
    }
}

impl crate::v7::Engine for StateF {
    fn rotate(&mut self, q: usize, i: usize, j: usize, b: i128, a: i128) {
        if b == 0 {
            return;
        }
        // the third level keeps its amplitude: (a^2 + b^2) / (a^2 + b^2)
        let (c, s, d) = (a * a - b * b, 2 * a * b, a * a + b * b);
        let st = p3(q);
        for base in 0..self.v.len() {
            if (base / st) % 3 != 0 {
                continue;
            }
            let (xi, xj) = (
                i128::from(self.v[base + i * st]),
                i128::from(self.v[base + j * st]),
            );
            self.v[base + i * st] = round_div(c * xi - s * xj, d);
            self.v[base + j * st] = round_div(s * xi + c * xj, d);
        }
    }
    fn sum(&mut self, c: usize, t: usize, s: i64) {
        let (sc, st) = (p3(c), p3(t));
        let mut out = vec![0i64; self.v.len()];
        for (x, &z) in self.v.iter().enumerate() {
            let dc = ((x / sc) % 3) as i64;
            let dt = (x / st) % 3;
            let nt = (dt as i64 + s * dc).rem_euclid(3) as usize;
            out[x - dt * st + nt * st] = z;
        }
        self.v = out;
    }
}
