//! v10: Z3 lattice gauge theory on an LX x LY torus in the gauge-fixed basis. The comb tree (x-links
//! (x,y)->(x+1,y) for x < LX-1 in every row, y-links (0,y)->(0,y+1) for y < LY-1) is set to zero; the
//! remaining LX*LY + 1 free links carry every gauge-invariant state, so no amplitude is unphysical.
//! Conventions as torus.rs: site s = y*LX + x, x-link 2s, y-link 2s+1, H = E + r M.

use crate::bigint::Big;
use std::collections::BTreeMap;

fn p3(k: usize) -> usize {
    3usize.pow(k as u32)
}

pub struct GaugeFixed {
    pub lx: usize,
    pub ly: usize,
    pub links: usize,
    /// link id of every free coordinate
    pub free: Vec<usize>,
    pub dim: usize,
    /// target free index of X_l (shift by +1) applied to free configuration c: hop[c * links + l]
    pub hop: Vec<u32>,
    pub mag: Vec<i64>,
}

impl GaugeFixed {
    fn sx(&self, s: usize) -> usize {
        (s / self.lx) * self.lx + (s % self.lx + 1) % self.lx
    }
    fn sy(&self, s: usize) -> usize {
        ((s / self.lx + 1) % self.ly) * self.lx + s % self.lx
    }
    pub fn is_tree(lx: usize, ly: usize, l: usize) -> bool {
        let s = l / 2;
        let (x, y) = (s % lx, s / lx);
        if l % 2 == 0 {
            x < lx - 1
        } else {
            x == 0 && y < ly - 1
        }
    }
    /// full configuration (tree links zero) of free index c
    pub fn full(&self, c: usize) -> Vec<i64> {
        let mut g = vec![0i64; self.links];
        for (i, &l) in self.free.iter().enumerate() {
            g[l] = ((c / p3(i)) % 3) as i64;
        }
        g
    }
    /// gauge-fix a full configuration onto the tree and return its free index
    pub fn fix(&self, g: &[i64]) -> usize {
        let sites = self.lx * self.ly;
        let mut a = vec![0i64; sites];
        // rows: along x from column 0; column 0: along y from the root
        for y in 0..self.ly {
            let s0 = y * self.lx;
            if y > 0 {
                let below = (y - 1) * self.lx;
                a[s0] = (a[below] + g[2 * below + 1]).rem_euclid(3);
            }
            for x in 0..self.lx - 1 {
                let s = s0 + x;
                a[s + 1] = (a[s] + g[2 * s]).rem_euclid(3);
            }
        }
        let mut idx = 0usize;
        for (i, &l) in self.free.iter().enumerate() {
            let s = l / 2;
            let t = if l % 2 == 0 { self.sx(s) } else { self.sy(s) };
            let v = (g[l] + a[s] - a[t]).rem_euclid(3) as usize;
            idx += v * p3(i);
        }
        idx
    }
    pub fn magnetic(&self, g: &[i64]) -> i64 {
        (0..self.lx * self.ly)
            .filter(|&s| {
                (g[2 * s] + g[2 * self.sx(s) + 1] - g[2 * self.sy(s)] - g[2 * s + 1]).rem_euclid(3)
                    != 0
            })
            .count() as i64
            * 3
    }
    pub fn new(lx: usize, ly: usize) -> GaugeFixed {
        let links = 2 * lx * ly;
        let free: Vec<usize> = (0..links).filter(|&l| !Self::is_tree(lx, ly, l)).collect();
        let dim = p3(free.len());
        let mut gf = GaugeFixed {
            lx,
            ly,
            links,
            free,
            dim,
            hop: Vec::new(),
            mag: Vec::new(),
        };
        let mut hop = vec![0u32; dim * links];
        let mut mag = vec![0i64; dim];
        for c in 0..dim {
            let g = gf.full(c);
            mag[c] = gf.magnetic(&g);
            for l in 0..links {
                let mut h = g.clone();
                h[l] = (h[l] + 1).rem_euclid(3);
                hop[c * links + l] = gf.fix(&h) as u32;
            }
        }
        gf.hop = hop;
        gf.mag = mag;
        gf
    }
    /// exact (E + r M, N) of a gauge-fixed real state
    pub fn energy_exact(&self, x: &[Big], r: i64) -> Option<(Big, Big)> {
        let (mut n, mut m, mut ov) = (Big::zero(), Big::zero(), Big::zero());
        for c in 0..self.dim {
            if x[c].is_zero() {
                continue;
            }
            let sq = x[c].mul(&x[c]);
            m = m.add(&sq.mul_i128(i128::from(self.mag[c])));
            n = n.add(&sq);
            let mut acc = Big::zero();
            for l in 0..self.links {
                let t = self.hop[c * self.links + l] as usize;
                if !x[t].is_zero() {
                    acc = acc.add(&x[t]);
                }
            }
            if !acc.is_zero() {
                ov = ov.add(&acc.mul(&x[c]));
            }
        }
        if n.is_zero() {
            return None;
        }
        let e = n.mul_i128(2 * self.links as i128).sub(&ov.mul_i128(2));
        Some((e.add(&m.mul_i128(i128::from(r))), n))
    }
    /// fixed-point energy (units 2^-40), used only to rank training candidates
    pub fn energy_fixed(&self, x: &[i64], r: i64) -> Option<i128> {
        let (mut n, mut m, mut ov) = (0i128, 0i128, 0i128);
        for c in 0..self.dim {
            let xc = i128::from(x[c]);
            if xc == 0 {
                continue;
            }
            let sq = xc * xc;
            n += sq;
            m += sq * i128::from(self.mag[c]);
            let mut acc = 0i128;
            for l in 0..self.links {
                acc += i128::from(x[self.hop[c * self.links + l] as usize]);
            }
            ov += acc * xc;
        }
        let num = n * 2 * self.links as i128 - 2 * ov + m * i128::from(r);
        let den = n >> 48;
        if den == 0 {
            return None;
        }
        Some(((num >> 48) << 40) / den)
    }
    fn translate(&self, g: &[i64], dx: usize, dy: usize) -> Vec<i64> {
        let mut h = vec![0i64; self.links];
        for y in 0..self.ly {
            for x in 0..self.lx {
                let s = y * self.lx + x;
                let t = ((y + dy) % self.ly) * self.lx + (x + dx) % self.lx;
                h[2 * t] = g[2 * s];
                h[2 * t + 1] = g[2 * s + 1];
            }
        }
        h
    }
    /// the zero-winding, zero-momentum block in sturmfast's weighted format: classes of free
    /// configurations under translations and the two cut shifts (all x-links of column 0; all y-links of
    /// row 0), weights = class sizes, Z_ij = moves from class i's representative into class j.
    /// Returns (text, classes, w_self_adjoint, class sizes).
    pub fn block_matrix(&self) -> (String, usize, bool) {
        let mut class_of = vec![u32::MAX; self.dim];
        let mut reps: Vec<usize> = Vec::new();
        let mut w: Vec<i64> = Vec::new();
        for c in 0..self.dim {
            if class_of[c] != u32::MAX {
                continue;
            }
            let id = reps.len() as u32;
            let mut stack = vec![c];
            class_of[c] = id;
            let mut size = 0i64;
            while let Some(u) = stack.pop() {
                size += 1;
                let g = self.full(u);
                let mut nbrs = vec![
                    self.fix(&self.translate(&g, 1, 0)),
                    self.fix(&self.translate(&g, 0, 1)),
                ];
                let mut hx = g.clone();
                for y in 0..self.ly {
                    hx[2 * (y * self.lx)] = (hx[2 * (y * self.lx)] + 1).rem_euclid(3);
                }
                nbrs.push(self.fix(&hx));
                let mut hy = g.clone();
                for x in 0..self.lx {
                    hy[2 * x + 1] = (hy[2 * x + 1] + 1).rem_euclid(3);
                }
                nbrs.push(self.fix(&hy));
                for v in nbrs {
                    if class_of[v] == u32::MAX {
                        class_of[v] = id;
                        stack.push(v);
                    }
                }
            }
            reps.push(c);
            w.push(size);
        }
        let k = reps.len();
        let mut z: Vec<BTreeMap<usize, i64>> = vec![BTreeMap::new(); k];
        for (i, &c) in reps.iter().enumerate() {
            *z[i].entry(i).or_insert(0) += 2 * self.links as i64;
            let g = self.full(c);
            for l in 0..self.links {
                for d in 1..=2i64 {
                    let mut h = g.clone();
                    h[l] = (h[l] + d).rem_euclid(3);
                    *z[i].entry(class_of[self.fix(&h)] as usize).or_insert(0) -= 1;
                }
            }
        }
        let mut adjoint = true;
        for i in 0..k {
            for (&j, &v) in &z[i] {
                adjoint &= w[i] * v == w[j] * z[j].get(&i).copied().unwrap_or(0);
            }
        }
        let mut s = format!("{k}\n");
        s.push_str(&w.iter().map(i64::to_string).collect::<Vec<_>>().join(" "));
        s.push('\n');
        s.push_str(
            &reps
                .iter()
                .map(|&c| self.mag[c].to_string())
                .collect::<Vec<_>>()
                .join(" "),
        );
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
    /// the plaquettes as (link, sign) lists restricted to free links
    pub fn plaquette_free_links(&self) -> Vec<Vec<(usize, i64)>> {
        (0..self.lx * self.ly)
            .map(|s| {
                let ls = [
                    (2 * s, 1i64),
                    (2 * self.sx(s) + 1, 1),
                    (2 * self.sy(s), -1),
                    (2 * s + 1, -1),
                ];
                ls.iter()
                    .filter_map(|&(l, sg)| self.free.iter().position(|&f| f == l).map(|i| (i, sg)))
                    .collect()
            })
            .collect()
    }
}

impl GaugeFixed {
    /// the image of free configuration c under generator k: 0, 1 the cut shifts (column-0 x-links,
    /// row-0 y-links), 2, 3 the translations by x and by y
    pub fn generator(&self, c: usize, k: usize) -> usize {
        let g = self.full(c);
        let h = match k {
            0 => {
                let mut h = g;
                for y in 0..self.ly {
                    h[2 * (y * self.lx)] = (h[2 * (y * self.lx)] + 1).rem_euclid(3);
                }
                h
            }
            1 => {
                let mut h = g;
                for x in 0..self.lx {
                    h[2 * x + 1] = (h[2 * x + 1] + 1).rem_euclid(3);
                }
                h
            }
            2 => self.translate(&g, 1, 0),
            _ => self.translate(&g, 0, 1),
        };
        self.fix(&h)
    }
    /// every electric target of c (each link, shifts +1 and +2), sorted
    fn targets(&self, c: usize) -> Vec<usize> {
        let g = self.full(c);
        let mut t = Vec::with_capacity(2 * self.links);
        for l in 0..self.links {
            for d in 1..=2i64 {
                let mut h = g.clone();
                h[l] = (h[l] + d).rem_euclid(3);
                t.push(self.fix(&h));
            }
        }
        t.sort_unstable();
        t
    }
    /// QA: every generator W commutes with H (M(Wc) = M(c) and targets(Wc) = W(targets(c)) as
    /// multisets) for every state; QB: every off-diagonal entry of H is <= 0 and the electric-move graph
    /// is connected
    pub fn symmetry_checks(&self) -> (bool, bool) {
        let mut qa = true;
        for c in 0..self.dim {
            let tc = self.targets(c);
            for k in 0..4 {
                let wc = self.generator(c, k);
                let mut mapped: Vec<usize> = tc.iter().map(|&t| self.generator(t, k)).collect();
                mapped.sort_unstable();
                qa &= self.mag[wc] == self.mag[c] && self.targets(wc) == mapped;
            }
            if !qa {
                break;
            }
        }
        // off-diagonal entries are minus counts of moves: <= 0 by the sign scan below
        let mut qb = true;
        let mut seen = vec![false; self.dim];
        let mut stack = vec![0usize];
        seen[0] = true;
        while let Some(u) = stack.pop() {
            let mut counts: BTreeMap<usize, i64> = BTreeMap::new();
            for t in self.targets(u) {
                *counts.entry(t).or_insert(0) -= 1;
            }
            for (&t, &v) in &counts {
                if t != u {
                    qb &= v <= 0;
                    if !seen[t] {
                        seen[t] = true;
                        stack.push(t);
                    }
                }
            }
        }
        (qa, qb && seen.iter().all(|&x| x))
    }
}
