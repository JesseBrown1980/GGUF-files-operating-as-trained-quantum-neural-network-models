//! The pixel backend: the 3^8 = 6561 link configurations as an 81 x 81 framebuffer
//! (x = links 0..3, y = links 4..7), with one u32 channel per prime. Every pass is a
//! per-pixel gather, as a fragment shader would run it: a pixel reads its own taps and
//! writes only itself. Energies come out as residues and are lifted back to exact
//! integers by Garner's mixed-radix reconstruction. Integer only. PNG frames are written
//! with stored deflate blocks.

use crate::bigint::Big;
use crate::v7::Engine;
use crate::ym_z3::{digits, gauge, gauge_group, index, magnetic, DIM, LINKS};

pub const SIDE: usize = 81;

fn is_prime(n: u64) -> bool {
    if n < 2 {
        return false;
    }
    let mut d = 2u64;
    while d * d <= n {
        if n % d == 0 {
            return false;
        }
        d += 1;
    }
    true
}

/// The k largest primes below 2^31, descending.
pub fn primes(k: usize) -> Vec<u64> {
    let mut out = Vec::with_capacity(k);
    let mut n = (1u64 << 31) - 1;
    while out.len() < k {
        if is_prime(n) {
            out.push(n);
        }
        n -= 1;
    }
    out
}

fn md(x: i128, p: u64) -> u64 {
    x.rem_euclid(i128::from(p)) as u64
}

fn pow_mod(mut b: u64, mut e: u64, p: u64) -> u64 {
    let mut r = 1u64;
    b %= p;
    while e > 0 {
        if e & 1 == 1 {
            r = r * b % p;
        }
        b = b * b % p;
        e >>= 1;
    }
    r
}

/// One framebuffer, one channel per prime: chan[k][pixel].
pub struct Frame {
    pub p: Vec<u64>,
    pub chan: Vec<Vec<u64>>,
    /// number of passes run, for the frame log
    pub passes: usize,
}

fn stride(q: usize) -> usize {
    3usize.pow(q as u32)
}

impl Frame {
    pub fn zero_state(p: &[u64]) -> Self {
        let mut chan = vec![vec![0u64; DIM]; p.len()];
        for c in &mut chan {
            c[0] = 1;
        }
        Frame {
            p: p.to_vec(),
            chan,
            passes: 0,
        }
    }
    /// gather: out[x] = sum_j M[d_q(x)][j] in[x with d_q = j]
    fn gather3(&mut self, q: usize, m: &[[i128; 3]; 3]) {
        let st = stride(q);
        for (k, ch) in self.chan.iter_mut().enumerate() {
            let p = self.p[k];
            let mm: Vec<[u64; 3]> = m.iter().map(|row| row.map(|x| md(x, p))).collect();
            let out: Vec<u64> = (0..DIM)
                .map(|x| {
                    let d = (x / st) % 3;
                    let base = x - d * st;
                    (0..3).fold(0u64, |acc, j| (acc + mm[d][j] * ch[base + j * st]) % p)
                })
                .collect();
            *ch = out;
        }
        self.passes += 1;
    }
    /// the energy numerator E + r M and denominator N as residues, one per channel
    pub fn energy_residues(&self, r: i64) -> (Vec<u64>, Vec<u64>) {
        let group = gauge_group();
        let taps: Vec<Vec<usize>> = (0..DIM)
            .map(|c| {
                let g = digits(c);
                group.iter().map(|a| index(&gauge(&g, a))).collect()
            })
            .collect();
        let mag: Vec<u64> = (0..DIM).map(|c| magnetic(&digits(c)) as u64).collect();
        let hop: Vec<[usize; LINKS]> = (0..DIM)
            .map(|c| {
                let g = digits(c);
                let mut h = [0usize; LINKS];
                for (l, hl) in h.iter_mut().enumerate() {
                    let mut t = g;
                    t[l] = (t[l] + 1).rem_euclid(3);
                    *hl = index(&t);
                }
                h
            })
            .collect();
        let mut nums = Vec::new();
        let mut dens = Vec::new();
        for (k, ch) in self.chan.iter().enumerate() {
            let p = self.p[k];
            // pass: gauge projection, 81 taps per pixel
            let phi: Vec<u64> = taps
                .iter()
                .map(|t| t.iter().fold(0u64, |acc, &i| (acc + ch[i]) % p))
                .collect();
            let (mut n, mut m, mut ov) = (0u64, 0u64, 0u64);
            for c in 0..DIM {
                let sq = phi[c] * phi[c] % p;
                n = (n + sq) % p;
                m = (m + sq * mag[c]) % p;
                for &t in &hop[c] {
                    ov = (ov + phi[c] * phi[t]) % p;
                }
            }
            let e = (n * (2 * LINKS as u64) % p + p - 2 * ov % p) % p;
            nums.push((e + md(i128::from(r), p) * m) % p);
            dens.push(n);
        }
        (nums, dens)
    }
}

impl Engine for Frame {
    fn rotate(&mut self, q: usize, i: usize, j: usize, b: i128, a: i128) {
        if b == 0 {
            return;
        }
        let k = 3 - i - j;
        let (c, s, d) = (a * a - b * b, 2 * a * b, a * a + b * b);
        let mut m = [[0i128; 3]; 3];
        m[i][i] = c;
        m[i][j] = -s;
        m[j][i] = s;
        m[j][j] = c;
        m[k][k] = d;
        self.gather3(q, &m);
    }
    fn sum(&mut self, c: usize, t: usize, s: i64) {
        let (sc, st) = (stride(c), stride(t));
        for ch in &mut self.chan {
            // gather: out[x] = in[x with d_t - s d_c]
            let out: Vec<u64> = (0..DIM)
                .map(|x| {
                    let dc = ((x / sc) % 3) as i64;
                    let dt = (x / st) % 3;
                    let src = (dt as i64 - s * dc).rem_euclid(3) as usize;
                    ch[x - dt * st + src * st]
                })
                .collect();
            *ch = out;
        }
        self.passes += 1;
    }
}

/// Garner: the unique 0 <= x < prod p with x = res[k] mod p[k], as an exact Big.
pub fn lift(res: &[u64], p: &[u64]) -> Big {
    let n = p.len();
    let mut coef = vec![0u64; n];
    for i in 0..n {
        let mut x = res[i] % p[i];
        for j in 0..i {
            let inv = pow_mod(p[j] % p[i], p[i] - 2, p[i]);
            x = (x + p[i] - coef[j] % p[i]) % p[i] * inv % p[i];
        }
        coef[i] = x;
    }
    let mut out = Big::zero();
    let mut radix = Big::from_i128(1);
    for i in 0..n {
        out = out.add(&radix.mul_i128(i128::from(coef[i])));
        radix = radix.mul_i128(i128::from(p[i]));
    }
    out
}

fn crc32(data: &[u8]) -> u32 {
    let mut c = 0xFFFF_FFFFu32;
    for &b in data {
        c ^= u32::from(b);
        for _ in 0..8 {
            c = if c & 1 == 1 {
                0xEDB8_8320 ^ (c >> 1)
            } else {
                c >> 1
            };
        }
    }
    !c
}

fn chunk(out: &mut Vec<u8>, kind: &[u8; 4], data: &[u8]) {
    out.extend_from_slice(&(data.len() as u32).to_be_bytes());
    let mut body = kind.to_vec();
    body.extend_from_slice(data);
    out.extend_from_slice(&body);
    out.extend_from_slice(&crc32(&body).to_be_bytes());
}

/// An RGB PNG with stored (uncompressed) deflate blocks.
pub fn png(w: usize, h: usize, rgb: &[u8]) -> Vec<u8> {
    let mut raw = Vec::with_capacity(h * (3 * w + 1));
    for y in 0..h {
        raw.push(0);
        raw.extend_from_slice(&rgb[y * 3 * w..(y + 1) * 3 * w]);
    }
    let mut z = vec![0x78, 0x01];
    let blocks: Vec<&[u8]> = raw.chunks(65_535).collect();
    for (i, b) in blocks.iter().enumerate() {
        z.push(u8::from(i + 1 == blocks.len()));
        let len = b.len() as u16;
        z.extend_from_slice(&len.to_le_bytes());
        z.extend_from_slice(&(!len).to_le_bytes());
        z.extend_from_slice(b);
    }
    let (mut a, mut bsum) = (1u32, 0u32);
    for &x in &raw {
        a = (a + u32::from(x)) % 65_521;
        bsum = (bsum + a) % 65_521;
    }
    z.extend_from_slice(&((bsum << 16) | a).to_be_bytes());
    let mut out = vec![0x89, b'P', b'N', b'G', 0x0D, 0x0A, 0x1A, 0x0A];
    let mut ihdr = Vec::new();
    ihdr.extend_from_slice(&(w as u32).to_be_bytes());
    ihdr.extend_from_slice(&(h as u32).to_be_bytes());
    ihdr.extend_from_slice(&[8, 2, 0, 0, 0]);
    chunk(&mut out, b"IHDR", &ihdr);
    chunk(&mut out, b"IDAT", &z);
    chunk(&mut out, b"IEND", &[]);
    out
}

/// Render exact amplitudes: red for positive, blue for negative, brightness from the bit
/// length relative to the largest (a 32-bit log scale); black for zero. Scaled up `zoom`.
pub fn render(v: &[Big], zoom: usize) -> Vec<u8> {
    let maxb = v.iter().map(Big::bits).max().unwrap_or(0);
    let side = SIDE * zoom;
    let mut rgb = vec![0u8; side * side * 3];
    for (i, z) in v.iter().enumerate() {
        let (x, y) = (i % SIDE, i / SIDE);
        let level = if z.is_zero() {
            0
        } else {
            let lo = maxb.saturating_sub(32);
            let b = z.bits().max(lo);
            (40 + (b - lo) * 215 / 32).min(255) as u8
        };
        let px = match z.sign() {
            1 => [level, level / 4, 0],
            -1 => [0, level / 4, level],
            _ => [0, 0, 0],
        };
        for dy in 0..zoom {
            for dx in 0..zoom {
                let o = ((y * zoom + dy) * side + x * zoom + dx) * 3;
                rgb[o..o + 3].copy_from_slice(&px);
            }
        }
    }
    png(side, side, &rgb)
}
