//! v2 tasks on the non-Clifford network: the circle task and the Z3 variational energy.
//! Every probability and energy is an exact element of Q(theta); every comparison is an
//! exact sign; an undecided sign is counted as such.

use crate::cyclo::{add_wide, conj, mul_wide, to_real, two_re_wide, Z9, ZERO9};
use crate::qutrit9::{Net9, State9};
use crate::real3::R3;
use crate::task::{Point, QUTRITS};
use crate::ym_z3::{digits, gauge, gauge_group, index, magnetic, DIM, LINKS};

fn wide_norm(z: &Z9) -> [i128; 6] {
    mul_wide(&conj(z), z)
}

/// Exact P(qutrit q = d) numerators over 3^k, as elements of Z[theta].
pub fn marginal(s: &State9, q: usize) -> [R3; 3] {
    let mut acc = [[0i128; 6]; 3];
    let st = 3usize.pow(q as u32);
    for (i, z) in s.v.iter().enumerate() {
        if *z != ZERO9 {
            let d = (i / st) % 3;
            acc[d] = add_wide(&acc[d], &wide_norm(z));
        }
    }
    [to_real(&acc[0]), to_real(&acc[1]), to_real(&acc[2])]
}

pub fn norm_sum(s: &State9) -> R3 {
    let mut acc = [0i128; 6];
    for z in &s.v {
        if *z != ZERO9 {
            acc = add_wide(&acc, &wide_norm(z));
        }
    }
    to_real(&acc)
}

pub fn encode9(p: &Point) -> State9 {
    let d = [
        p.x % 3,
        (p.x / 3) % 3,
        p.x / 9,
        p.y % 3,
        (p.y / 3) % 3,
        p.y / 9,
    ];
    State9::basis(QUTRITS, &d)
}

/// P(0) - P(1) for qutrit 0, an element of Z[theta] over 3^k (k is the same for all inputs).
pub fn margin(net: &Net9, p: &Point) -> R3 {
    let mut s = encode9(p);
    net.forward(&mut s);
    let m = marginal(&s, 0);
    m[0].sub(&m[1])
}

pub fn margins(net: &Net9, pts: &[Point]) -> Vec<R3> {
    pts.iter().map(|p| margin(net, p)).collect()
}

/// (correct, undecided): class 1 iff the margin is exactly positive.
pub fn correct(ms: &[R3], pts: &[Point]) -> (usize, usize) {
    let (mut c, mut u) = (0, 0);
    for (m, p) in ms.iter().zip(pts.iter()) {
        match m.sign() {
            Some(s) => c += usize::from(u8::from(s > 0) == p.label),
            None => u += 1,
        }
    }
    (c, u)
}

pub fn combine(c: &[i64], branch: &[Vec<R3>], i: usize) -> R3 {
    c.iter()
        .zip(branch.iter())
        .fold(R3::int(0), |acc, (&cb, m)| {
            if cb == 0 {
                acc
            } else {
                acc.add(&m[i].scale(i128::from(cb)))
            }
        })
}

pub fn virtual_correct(c: &[i64], branch: &[Vec<R3>], pts: &[Point]) -> (usize, usize) {
    let (mut k, mut u) = (0, 0);
    for (i, p) in pts.iter().enumerate() {
        match combine(c, branch, i).sign() {
            Some(s) => k += usize::from(u8::from(s > 0) == p.label),
            None => u += 1,
        }
    }
    (k, u)
}

pub struct Trained9 {
    pub net: Net9,
    pub train_correct: usize,
    pub sweeps: usize,
    pub evaluations: usize,
}

/// v1's coordinate descent: each trit tries its three values; keep strict gains only.
pub fn train_circle(mut net: Net9, pts: &[Point], max_sweeps: usize) -> Trained9 {
    let mut best = correct(&margins(&net, pts), pts).0;
    let mut evaluations = 1;
    let mut sweeps = 0;
    for _ in 0..max_sweeps {
        sweeps += 1;
        let mut changed = false;
        for i in 0..net.params.len() {
            let keep = net.params[i];
            let mut best_v = keep;
            for v in 0..3 {
                if v == keep {
                    continue;
                }
                net.params[i] = v;
                evaluations += 1;
                let c = correct(&margins(&net, pts), pts).0;
                if c > best {
                    best = c;
                    best_v = v;
                }
            }
            net.params[i] = best_v;
            changed |= best_v != keep;
        }
        if !changed {
            break;
        }
    }
    Trained9 {
        net,
        train_correct: best,
        sweeps,
        evaluations,
    }
}

/// Z3 energy of the gauge-projected state as (numerator E + r M, denominator norm), exact.
pub fn z3_energy(s: &State9, r: i64) -> Option<(R3, R3)> {
    let mut phi = vec![ZERO9; DIM];
    for a in gauge_group() {
        for (c, z) in s.v.iter().enumerate() {
            if *z != ZERO9 {
                let t = index(&gauge(&digits(c), &a));
                for (x, y) in phi[t].iter_mut().zip(z.iter()) {
                    *x += y;
                }
            }
        }
    }
    let mut n = [0i128; 6];
    let mut m = [0i128; 6];
    for (c, z) in phi.iter().enumerate() {
        if *z != ZERO9 {
            let w = wide_norm(z);
            n = add_wide(&n, &w);
            let mag = i128::from(magnetic(&digits(c)));
            m = add_wide(&m, &w.map(|x| x * mag));
        }
    }
    let norm = to_real(&n);
    if norm.is_zero() {
        return None;
    }
    let mut e = R3::int(0);
    for l in 0..LINKS {
        let mut acc = [0i128; 6];
        for (c, z) in phi.iter().enumerate() {
            if *z == ZERO9 {
                continue;
            }
            let mut g = digits(c);
            g[l] = (g[l] + 1).rem_euclid(3);
            let target = &phi[index(&g)];
            if *target != ZERO9 {
                acc = add_wide(&acc, &mul_wide(&conj(target), z));
            }
        }
        // <phi|(2 - X - X^dagger)|phi> = 2 norm - 2 Re <phi|X phi>
        e = e.add(&norm.scale(2)).sub(&two_re_wide(&acc));
    }
    let num = e.add(&to_real(&m).scale(i128::from(r)));
    Some((num, norm))
}

/// sign of a/b - c/d for positive b, d
pub fn cmp_frac(x: &(R3, R3), y: &(R3, R3)) -> Option<i8> {
    x.0.mul(&y.1).sub(&y.0.mul(&x.1)).sign()
}

/// sign of a/b - t/1000
pub fn cmp_milli(x: &(R3, R3), t: i128) -> Option<i8> {
    x.0.scale(1000).sub(&x.1.scale(t)).sign()
}

/// t such that energy is in [t, t+1) milli, by exact bisection; None if any sign is undecided.
pub fn milli_floor(x: &(R3, R3), lo: i128, hi: i128) -> Option<i128> {
    let (mut lo, mut hi) = (lo, hi);
    if cmp_milli(x, lo)? < 0 || cmp_milli(x, hi)? >= 0 {
        return None;
    }
    while hi - lo > 1 {
        let mid = (lo + hi) / 2;
        if cmp_milli(x, mid)? >= 0 {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    Some(lo)
}

pub fn train_z3(mut net: Net9, r: i64, max_sweeps: usize) -> (Net9, (R3, R3), usize) {
    let eval = |n: &Net9| {
        let mut s = State9::basis(LINKS, &[0; LINKS]);
        n.forward(&mut s);
        z3_energy(&s, r)
    };
    let mut best = eval(&net).expect("seed has a physical component");
    let mut evals = 1;
    for _ in 0..max_sweeps {
        let mut changed = false;
        for i in 0..net.params.len() {
            let keep = net.params[i];
            let mut best_v = keep;
            for v in 0..3 {
                if v == keep {
                    continue;
                }
                net.params[i] = v;
                evals += 1;
                if let Some(e) = eval(&net) {
                    if cmp_frac(&e, &best) == Some(-1) {
                        best = e;
                        best_v = v;
                    }
                }
            }
            net.params[i] = best_v;
            changed |= best_v != keep;
        }
        if !changed {
            break;
        }
    }
    (net, best, evals)
}
