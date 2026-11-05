//! tw: truncated Wigner sampler for the three-mode model from |N,0,0>, in integers only (float_used=0).
//! Fields psi_j = a_j/sqrt(N) at 2^40; RK4 on the classical equations of H; Gaussians are exact binomials: (popcount of 65536 bits - 32768)/128.
//! i dpsi+/dt = x psi+ + u(|psi0|^2 + |psi-|^2) psi+ + conj(psi-) psi0^2 - y psi0, same for psi- with + <-> -,
//! i dpsi0/dt = u(|psi+|^2 + |psi-|^2) psi0 + 2 psi+ psi- conj(psi0) - y (psi+ + psi-).
//! Reads A/N = Z = conj(psi0) psi+ + conj(psi-) psi0 per trajectory: amplitude rho = |Z| and phase theta = arg Z.

use std::env;
use std::thread;

const Q: u32 = 40;

#[inline]
fn m(a: i64, b: i64) -> i64 {
    ((i128::from(a) * i128::from(b)) >> Q) as i64
}

fn isqrt(n: u128) -> u128 {
    if n < 2 {
        return n;
    }
    let bits = 128 - n.leading_zeros();
    let mut x: u128 = 1u128 << bits.div_ceil(2);
    loop {
        let y = (x + n / x) >> 1;
        if y >= x {
            return x;
        }
        x = y;
    }
}

fn parse_q(s: &str) -> i64 {
    let (n, d) = match s.split_once('/') {
        Some((a, b)) => (a.parse::<i128>().expect("num"), b.parse::<i128>().expect("den")),
        None => (s.parse::<i128>().expect("int"), 1),
    };
    ((n << Q) / d) as i64
}

#[derive(Clone, Copy)]
struct Par {
    x: i64,
    u: i64,
    y: i64,
}

#[derive(Clone, Copy, Default)]
struct S {
    r0: i64,
    i0: i64,
    rp: i64,
    ip: i64,
    rm: i64,
    im: i64,
}

fn rhs(s: &S, par: &Par) -> S {
    let abs0 = m(s.r0, s.r0) + m(s.i0, s.i0);
    let absp = m(s.rp, s.rp) + m(s.ip, s.ip);
    let absm = m(s.rm, s.rm) + m(s.im, s.im);
    let sq_re = m(s.r0, s.r0) - m(s.i0, s.i0);
    let sq_im = 2 * m(s.r0, s.i0);
    let coefp = par.x + m(par.u, abs0 + absm);
    let coefm = par.x + m(par.u, abs0 + absp);
    let bp_re = m(coefp, s.rp) + m(s.rm, sq_re) + m(s.im, sq_im) - m(par.y, s.r0);
    let bp_im = m(coefp, s.ip) + m(s.rm, sq_im) - m(s.im, sq_re) - m(par.y, s.i0);
    let bm_re = m(coefm, s.rm) + m(s.rp, sq_re) + m(s.ip, sq_im) - m(par.y, s.r0);
    let bm_im = m(coefm, s.im) + m(s.rp, sq_im) - m(s.ip, sq_re) - m(par.y, s.i0);
    let pm_re = m(s.rp, s.rm) - m(s.ip, s.im);
    let pm_im = m(s.rp, s.im) + m(s.ip, s.rm);
    let coef0 = m(par.u, absp + absm);
    let c_re = m(coef0, s.r0) + 2 * (m(pm_re, s.r0) + m(pm_im, s.i0)) - m(par.y, s.rp + s.rm);
    let c_im = m(coef0, s.i0) + 2 * (m(pm_im, s.r0) - m(pm_re, s.i0)) - m(par.y, s.ip + s.im);
    S {
        r0: c_im,
        i0: -c_re,
        rp: bp_im,
        ip: -bp_re,
        rm: bm_im,
        im: -bm_re,
    }
}

fn addk(a: &S, k: &S, den: i64) -> S {
    S {
        r0: a.r0 + k.r0 / den,
        i0: a.i0 + k.i0 / den,
        rp: a.rp + k.rp / den,
        ip: a.ip + k.ip / den,
        rm: a.rm + k.rm / den,
        im: a.im + k.im / den,
    }
}

fn rk4(s: &S, par: &Par, dtden: i64) -> S {
    let k1 = rhs(s, par);
    let k2 = rhs(&addk(s, &k1, 2 * dtden), par);
    let k3 = rhs(&addk(s, &k2, 2 * dtden), par);
    let k4 = rhs(&addk(s, &k3, dtden), par);
    let sum = |a: i64, b: i64, c: i64, d: i64| -> i64 { (a + 2 * b + 2 * c + d) / (6 * dtden) };
    S {
        r0: s.r0 + sum(k1.r0, k2.r0, k3.r0, k4.r0),
        i0: s.i0 + sum(k1.i0, k2.i0, k3.i0, k4.i0),
        rp: s.rp + sum(k1.rp, k2.rp, k3.rp, k4.rp),
        ip: s.ip + sum(k1.ip, k2.ip, k3.ip, k4.ip),
        rm: s.rm + sum(k1.rm, k2.rm, k3.rm, k4.rm),
        im: s.im + sum(k1.im, k2.im, k3.im, k4.im),
    }
}

struct Rng {
    s: [u64; 4],
}

fn splitmix(z: &mut u64) -> u64 {
    *z = z.wrapping_add(0x9E37_79B9_7F4A_7C15);
    let mut v = *z;
    v = (v ^ (v >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    v = (v ^ (v >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    v ^ (v >> 31)
}

impl Rng {
    fn new(seed: u64) -> Self {
        let mut z = seed;
        Self {
            s: [splitmix(&mut z), splitmix(&mut z), splitmix(&mut z), splitmix(&mut z)],
        }
    }
    fn next(&mut self) -> u64 {
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
    /// Binomial(65536, 1/2) - 32768, divided by 128 at 2^40. Variance exactly 1, excess kurtosis -2/65536.
    fn gauss(&mut self) -> i64 {
        let mut c: i64 = 0;
        for _ in 0..1024 {
            c += i64::from(self.next().count_ones());
        }
        (c - 32768) << (Q - 7)
    }
}

#[derive(Clone)]
struct Acc {
    zr: i128,
    zi: i128,
    r2: i128,
    r1: i128,
    r4: i128,
    cos: i128,
    sin: i128,
    cos2: i128,
    sin2: i128,
    z2r: i128,
    z0: i128,
    zp: i128,
    zm: i128,
    corr: i128,
    ch2: i128,
    rcos2: i128,
    rz: i128,
    zz: i128,
    coss: i128,
    count: i128,
}

impl Acc {
    fn new() -> Self {
        Self {
            zr: 0,
            zi: 0,
            r2: 0,
            r1: 0,
            r4: 0,
            cos: 0,
            sin: 0,
            cos2: 0,
            sin2: 0,
            z2r: 0,
            z0: 0,
            zp: 0,
            zm: 0,
            corr: 0,
            ch2: 0,
            rcos2: 0,
            rz: 0,
            zz: 0,
            coss: 0,
            count: 0,
        }
    }
    fn add(&mut self, o: &Acc) {
        self.zr += o.zr;
        self.zi += o.zi;
        self.r2 += o.r2;
        self.r1 += o.r1;
        self.r4 += o.r4;
        self.cos += o.cos;
        self.sin += o.sin;
        self.cos2 += o.cos2;
        self.sin2 += o.sin2;
        self.z2r += o.z2r;
        self.z0 += o.z0;
        self.zp += o.zp;
        self.zm += o.zm;
        self.corr += o.corr;
        self.ch2 += o.ch2;
        self.rcos2 += o.rcos2;
        self.rz += o.rz;
        self.zz += o.zz;
        self.coss += o.coss;
        self.count += o.count;
    }
}

struct Job {
    n: i128,
    par: Par,
    dtden: i64,
    steps: Vec<usize>,
    labels: Vec<String>,
    tref: usize,
    samples: u64,
    seed: u64,
    root_ratio: i64,
    mean_shift: i64,
}

fn run_chunk(job: &Job, first: u64, count: u64) -> Vec<Acc> {
    let mut accs = vec![Acc::new(); job.steps.len()];
    let one: i128 = 1i128 << Q;
    // 1/(2 sqrt(N)) at 2^40
    let inv_sqrt = isqrt(((one * one) / job.n) as u128) as i64;
    let half_inv = inv_sqrt / 2;
    // psi0 = sqrt((N + 1/2)/N)
    let psi0 = isqrt((((2 * job.n + 1) * one * one) / (2 * job.n)) as u128) as i64;
    let last = *job.steps.iter().max().unwrap_or(&0);
    for traj in first..(first + count) {
        let mut rng = Rng::new(job.seed.wrapping_add(traj.wrapping_mul(0x1000_0000_01B3)));
        let (g1, g2, g3, g4) = (rng.gauss(), rng.gauss(), rng.gauss(), rng.gauss());
        let mut s = S {
            r0: psi0,
            i0: 0,
            rp: m(g1, half_inv),
            ip: m(g2, half_inv),
            rm: m(g3, half_inv),
            im: m(g4, half_inv),
        };
        // Seed of the unstable mode: zeta = [(psi+ + conj psi-) + i r (psi+ - conj psi-)]/2 + mean_shift, r = sqrt((1-d)/(1+d)).
        let (ar, ai) = (s.rp + s.rm, s.ip - s.im);
        let (br, bi) = (s.rp - s.rm, s.ip + s.im);
        let zeta_r = (ar - m(job.root_ratio, bi)) / 2 + job.mean_shift;
        let zeta_i = (ai + m(job.root_ratio, br)) / 2;
        let zeta2 = i128::from(zeta_r) * i128::from(zeta_r) + i128::from(zeta_i) * i128::from(zeta_i);
        let zeta_abs = isqrt(zeta2 as u128) as i64;
        let (zc, zs) = if zeta_abs == 0 {
            (0, 0)
        } else {
            (
                ((i128::from(zeta_r) << Q) / i128::from(zeta_abs)) as i64,
                ((i128::from(zeta_i) << Q) / i128::from(zeta_abs)) as i64,
            )
        };
        // Reference phase is needed before its row, so run once and store e^(i theta) at each recording point.
        let mut rec = vec![(0i64, 0i64, 0i64); job.steps.len()]; // (rho, cos, sin) per record
        let mut next_rec = 0usize;
        for step in 0..=last {
            while next_rec < job.steps.len() && job.steps[next_rec] == step {
                let zr = m(s.r0, s.rp) + m(s.i0, s.ip) + m(s.rm, s.r0) + m(s.im, s.i0);
                let zi = m(s.r0, s.ip) - m(s.i0, s.rp) + m(s.rm, s.i0) - m(s.im, s.r0);
                let rho2 = i128::from(zr) * i128::from(zr) + i128::from(zi) * i128::from(zi);
                let rho = isqrt(rho2 as u128) as i64;
                let (c, sn) = if rho == 0 {
                    (0, 0)
                } else {
                    (
                        ((i128::from(zr) << Q) / i128::from(rho)) as i64,
                        ((i128::from(zi) << Q) / i128::from(rho)) as i64,
                    )
                };
                rec[next_rec] = (rho, c, sn);
                let a = &mut accs[next_rec];
                let abs0 = m(s.r0, s.r0) + m(s.i0, s.i0);
                let absp = m(s.rp, s.rp) + m(s.ip, s.ip);
                let absm = m(s.rm, s.rm) + m(s.im, s.im);
                a.zr += i128::from(zr);
                a.zi += i128::from(zi);
                a.r2 += rho2 >> Q;
                a.r1 += i128::from(rho);
                let r2q = rho2 >> Q;
                a.r4 += (r2q * r2q) >> Q;
                a.cos += i128::from(c);
                a.sin += i128::from(sn);
                a.cos2 += i128::from(m(c, c) - m(sn, sn));
                a.sin2 += i128::from(2 * m(c, sn));
                a.z2r += i128::from(m(zr, zr) - m(zi, zi));
                a.z0 += i128::from(abs0);
                a.zp += i128::from(absp);
                a.zm += i128::from(absm);
                let ch = i128::from(absp - absm);
                a.ch2 += (ch * ch) >> Q;
                a.rcos2 += i128::from(m(rho, m(c, c)));
                a.rz += (i128::from(rho) * i128::from(zeta_abs)) >> (Q - 16);
                a.zz += zeta2 >> (Q - 16);
                a.coss += i128::from(m(c, zc) + m(sn, zs));
                a.count += 1;
                next_rec += 1;
            }
            if step < last {
                s = rk4(&s, &job.par, job.dtden);
            }
        }
        let (_, cr, sr) = rec[job.tref];
        for (i, a) in accs.iter_mut().enumerate() {
            a.corr += i128::from(m(rec[i].1, cr) + m(rec[i].2, sr));
        }
    }
    accs
}

fn e12(v: i128) -> i128 {
    (v * 1_000_000_000_000i128) >> Q
}

fn main() {
    // tw N delta u y samples seed dtden tref_index threads t1,t2,... (t in units of 1/dtden given as integers k = t*dtden)
    let a: Vec<String> = env::args().collect();
    let n: i128 = a[1].parse().expect("N");
    let delta = parse_q(&a[2]);
    let u = parse_q(&a[3]);
    let y = parse_q(&a[4]);
    let samples: u64 = a[5].parse().expect("samples");
    let seed: u64 = a[6].parse().expect("seed");
    let dtden: i64 = a[7].parse().expect("dtden");
    let tref: usize = a[8].parse().expect("tref");
    let threads: u64 = a[9].parse().expect("threads");
    let labels: Vec<String> = a[10].split(',').map(str::to_string).collect();
    let steps: Vec<usize> = labels.iter().map(|s| s.parse::<usize>().expect("step")).collect();
    let par = Par { x: delta - u, u, y };
    let one: i128 = 1i128 << Q;
    let (root_ratio, mean_shift) = if i128::from(delta).abs() < one {
        let ratio = ((one - i128::from(delta)) << Q) / (one + i128::from(delta));
        (
            isqrt((ratio << Q) as u128) as i64,
            -((i128::from(y) << Q) / (one + i128::from(delta))) as i64,
        )
    } else {
        (0, 0)
    };
    let job = Job {
        n,
        par,
        dtden,
        steps,
        labels,
        tref,
        samples,
        seed,
        root_ratio,
        mean_shift,
    };
    let per = samples / threads;
    let mut total = vec![Acc::new(); job.steps.len()];
    thread::scope(|s| {
        let mut handles = Vec::new();
        for t in 0..threads {
            let job_ref = &job;
            handles.push(s.spawn(move || run_chunk(job_ref, t * per, per)));
        }
        for h in handles {
            let part = h.join().expect("thread");
            for (x, y2) in total.iter_mut().zip(part.iter()) {
                x.add(y2);
            }
        }
    });
    for (i, a2) in total.iter().enumerate() {
        let c = a2.count.max(1);
        println!(
            "TW|N={}|delta={}|u={}|y={}|samples={}|dtden={}|step={}|mean_zr_e12={}|mean_zi_e12={}|mean_r2_e12={}|mean_r1_e12={}|mean_r4_e12={}|mean_cos_e12={}|mean_sin_e12={}|mean_cos2_e12={}|mean_sin2_e12={}|mean_z2r_e12={}|mean_a0_e12={}|mean_ap_e12={}|mean_am_e12={}|corr_ref_e12={}|mean_ch2_e12={}|mean_rcos2_e12={}|mean_rz_e16={}|mean_zz_e16={}|mean_coss_e12={}|tref_step={}|float_used=0|json=0",
            job.n,
            a[2],
            a[3],
            a[4],
            job.samples,
            job.dtden,
            job.labels[i],
            e12(a2.zr / c),
            e12(a2.zi / c),
            e12(a2.r2 / c),
            e12(a2.r1 / c),
            e12(a2.r4 / c),
            e12(a2.cos / c),
            e12(a2.sin / c),
            e12(a2.cos2 / c),
            e12(a2.sin2 / c),
            e12(a2.z2r / c),
            e12(a2.z0 / c),
            e12(a2.zp / c),
            e12(a2.zm / c),
            e12(a2.corr / c),
            e12(a2.ch2 / c),
            e12(a2.rcos2 / c),
            e12((a2.rz / c) * 10_000) >> 16,
            e12((a2.zz / c) * 10_000) >> 16,
            e12(a2.coss / c),
            job.steps[job.tref],
        );
    }
}
