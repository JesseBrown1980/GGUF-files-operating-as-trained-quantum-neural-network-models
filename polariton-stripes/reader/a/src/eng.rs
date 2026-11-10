//! Integer helpers of twens 0.4.0 (polariton-bridge/engines/ensemble/src/main.rs, sha256 1d768fa9..., at 4a97736),
//! ported operation for operation, so a dump's starts, control seeds, start bounds and field bounds rebuild from its draws.

pub const Q: u32 = 40;
pub const ONE: i64 = 1i64 << Q;
pub const ONE128: i128 = 1i128 << Q;
pub const ONEU: u128 = 1u128 << Q;

pub const NV: usize = 7;
pub const VNC: usize = 0;
pub const V1: usize = 1;
pub const V0: usize = 2;
pub const RN: usize = 3;
pub const FLIP: usize = 4;
pub const LOCK: usize = 5;
pub const MODE0: usize = 6;
pub const VNAME: [&str; NV] = ["VNC", "V1", "V0", "RN", "FLIP", "LOCK", "MODE0"];
pub const VINIT: [&str; NV] = [
    "sharp",
    "ring_half",
    "coherent",
    "ring",
    "sharp",
    "sharp",
    "sharp",
];
pub const VSEEDS: [&str; NV] = ["vac", "vac", "vac", "vac", "vac", "lock", "vac"];
pub const VKAPPA: [&str; NV] = ["1", "1", "1", "1", "-1", "1", "1"];
pub const VPHASE: [&str; NV] = [
    "fixed", "fixed", "fixed", "fixed", "fixed", "fixed", "rot30",
];
/// The legacy TWENS rows, in the engine's order: (variant, its old name).
pub const LEGACY: [(usize, &str); 4] = [(V1, "V1"), (VNC, "VN"), (V0, "V0"), (RN, "RN")];

pub const OZR: usize = 0;
pub const OZI: usize = 1;
pub const OXW: usize = 2;
pub const OXNC: usize = 3;
pub const OF: usize = 4;
pub const OBR: usize = 5;
pub const OBI: usize = 6;

pub const NPAIR: usize = 11;
/// (a, observable, b, observable, name): d = a.obs - b.obs per sample, the engine's TWB_PAIR rows in its order.
pub const PAIRS: [(usize, usize, usize, usize, &str); NPAIR] = [
    (V1, OXW, VNC, OXNC, "V1xw-VNCxnc"),
    (V1, OZR, VNC, OZR, "V1zr-VNCzr"),
    (V0, OXW, V1, OXW, "V0xw-V1xw"),
    (V0, OZR, V1, OZR, "V0zr-V1zr"),
    (V1, OXW, VNC, OXW, "V1xw-VNCxw"),
    (MODE0, OZR, VNC, OZR, "MODE0zr-VNCzr"),
    (MODE0, OZI, VNC, OZI, "MODE0zi-VNCzi"),
    (MODE0, OXNC, VNC, OXNC, "MODE0xnc-VNCxnc"),
    (MODE0, OF, VNC, OF, "MODE0f-VNCf"),
    (MODE0, OBR, VNC, OBR, "MODE0br-VNCbr"),
    (MODE0, OBI, VNC, OBI, "MODE0bi-VNCbi"),
];

pub const NF: usize = 34;
/// The summed fields of a TWB row in its order (9 plain, 7 floored squares, 10 new, 8 exact squares).
pub const FIELDS: [&str; NF] = [
    "zr", "zi", "dzr", "dzi", "xw", "dxw", "xnc", "dxnc", "f", "qdzr", "qdxw", "qdxnc", "qzr",
    "qxw", "qxnc", "qdzi", "f2", "br", "bi", "br2", "bi2", "brbi", "zrxw", "zrxnc", "dzrdxw",
    "dzrdxnc", "zr2", "zi2", "dzr2", "dzi2", "xw2", "dxw2", "xnc2", "dxnc2",
];

pub type St = [i64; 6];

/// m() takes a rot component only when |rot| <= 2^41 (review N9): `starts` refuses a larger one, and stage A's
/// check STOPs `rot_out_of_range` before it.
pub const ROT_LIMIT: u64 = 1 << 41;

#[inline]
pub fn m(a: i64, b: i64) -> i64 {
    ((i128::from(a) * i128::from(b)) >> Q) as i64
}

pub fn isqrt(n: u128) -> u128 {
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

/// ceil(a * b / 2^40) for nonnegative a, b.
#[inline]
pub fn cu(a: u128, b: u128) -> u128 {
    (a * b + (ONEU - 1)) >> Q
}

#[inline]
pub fn uabs(v: i64) -> u128 {
    u128::from(v.unsigned_abs())
}

/// h = floor(2^40 / (2 sqrt N)), as the engine computes it.
pub fn h_of(n: i64) -> i64 {
    isqrt(((ONE128 * ONE128) / (4 * i128::from(n))) as u128) as i64
}

/// V1's psi0 = sqrt((N + 1/2)/N) at 2^40, as the engine computes it.
pub fn psi_v1(n: i64) -> i64 {
    let n128 = i128::from(n);
    isqrt(((((2 * n128 + 1) * ONE128) / (2 * n128)) * ONE128) as u128) as i64
}

/// The sharp psi0 = sqrt(1 + 3/(2N) - nsum); None where the engine stops (argument not positive).
pub fn sharp(nsum: i64, n: i64) -> Option<i64> {
    let arg = ONE + (3 * ONE) / (2 * n) - nsum;
    if arg <= 0 {
        return None;
    }
    Some(isqrt((i128::from(arg) * ONE128) as u128) as i64)
}

/// Start error of a real seed component m(g, h): 1 + ceil(|g| / 2^40) ulps.
pub fn seed_err(g: i64) -> u128 {
    1 + uabs(g).div_ceil(ONEU)
}

/// Start error of the sharp psi0; None where the engine stops (low end of the argument not positive).
pub fn sharp_err(comps: [i64; 4], errs: [u128; 4], n: i64) -> Option<u128> {
    let mut dn: u128 = 4;
    let mut nsum: i64 = 0;
    for (cv, ce) in comps.iter().zip(errs.iter()) {
        dn += cu(2 * uabs(*cv), *ce) + cu(*ce, *ce);
        nsum += m(*cv, *cv);
    }
    let darg = dn + 1;
    let arg = ONE + (3 * ONE) / (2 * n) - nsum;
    let lo = u128::try_from(arg).unwrap_or(0).saturating_sub(darg);
    if lo == 0 {
        return None;
    }
    let slo = isqrt(lo << Q);
    Some(1 + (darg << Q).div_ceil(2 * slo))
}

/// Rotate a whole state by the unit vector (c, sn) at 2^40.
pub fn rot(s: &St, c: i64, sn: i64) -> St {
    let r = |re: i64, im: i64| -> (i64, i64) { (m(re, c) - m(im, sn), m(re, sn) + m(im, c)) };
    let (r0, i0) = r(s[0], s[1]);
    let (rp, ip) = r(s[2], s[3]);
    let (rm, im) = r(s[4], s[5]);
    [r0, i0, rp, ip, rm, im]
}

/// Pair-locked seeds psi- = conj(psi+).
pub fn lock_seeds(rp: i64, ip: i64) -> [i64; 4] {
    [rp, ip, rp, -ip]
}

/// The control seeds (u_re, u_im, v_re, v_im), u = psi+ + conj psi-, v = psi+ - conj psi-.
pub fn uv_of(sp: [i64; 4]) -> [i64; 4] {
    let [rp, ip, rm, im] = sp;
    [rp + rm, ip - im, rp - rm, ip + im]
}

/// The linear control at one record: (zc_re, zc_im, xc) from ctrl (C, RS, mz) and the variant's control seeds.
pub fn lin(ctrl: (i64, i64, i64), uv: &[i64; 4], n: i64) -> (i64, i64, i64) {
    let (cc, rs, mz) = ctrl;
    let [u_re, u_im, v_re, v_im] = *uv;
    let zc_re = mz + m(cc, u_re) - m(rs, v_im);
    let zc_im = m(cc, u_im) + m(rs, v_re);
    let xc = m(zc_re, zc_re) + m(zc_im, zc_im) - ONE / n;
    (zc_re, zc_im, xc)
}

/// Every variant's start, control seeds, per-mode start bounds and seed bound for one sample's draws.
pub struct Starts {
    pub init: [St; NV],
    pub uv: [[i64; 4]; NV],
    pub ib: [[u128; 3]; NV],
    pub sb: [u128; NV],
}

/// Rebuild one sample's starts as ens_build does. Err where the engine would have stopped (exit 4).
pub fn starts(
    n: i64,
    g: &[i64; 6],
    rot30: (i64, i64),
    on: &[bool; NV],
) -> Result<Starts, &'static str> {
    if rot30.0.unsigned_abs() > ROT_LIMIT || rot30.1.unsigned_abs() > ROT_LIMIT {
        return Err("rot_above_2^41");
    }
    let h = h_of(n);
    let (rp, ip, rm, im) = (m(g[0], h), m(g[1], h), m(g[2], h), m(g[3], h));
    let nsum = m(rp, rp) + m(ip, ip) + m(rm, rm) + m(im, im);
    let need_vn = on[VNC] || on[FLIP] || on[MODE0];
    let psi_vn = if need_vn {
        sharp(nsum, n).ok_or("sharp_argument_not_positive")?
    } else {
        0
    };
    let mut init = [[0i64; 6]; NV];
    init[VNC] = [psi_vn, 0, rp, ip, rm, im];
    init[V1] = [psi_v1(n), 0, rp, ip, rm, im];
    init[V0] = [ONE + m(g[4], h), m(g[5], h), rp, ip, rm, im];
    init[RN] = [ONE, 0, rp, ip, rm, im];
    init[FLIP] = init[VNC];
    let [lp, lip, lm, lim] = lock_seeds(rp, ip);
    let psi_l = if on[LOCK] {
        sharp(m(lp, lp) + m(lip, lip) + m(lm, lm) + m(lim, lim), n)
            .ok_or("lock_sharp_argument_not_positive")?
    } else {
        0
    };
    init[LOCK] = [psi_l, 0, lp, lip, lm, lim];
    init[MODE0] = rot(&init[VNC], rot30.0, rot30.1);
    let vac = uv_of([rp, ip, rm, im]);
    let mut uv = [vac; NV];
    uv[LOCK] = uv_of([lp, lip, lm, lim]);
    let ec = [
        seed_err(g[0]),
        seed_err(g[1]),
        seed_err(g[2]),
        seed_err(g[3]),
    ];
    let (ep, em) = (ec[0] + ec[1], ec[2] + ec[3]);
    let e_vn = if need_vn {
        sharp_err([rp, ip, rm, im], ec, n).ok_or("sharp_bound_argument_low_end_not_positive")?
    } else {
        0
    };
    let mut ib = [[0u128; 3]; NV];
    ib[VNC] = [e_vn, ep, em];
    ib[V1] = [2, ep, em];
    ib[V0] = [seed_err(g[4]) + seed_err(g[5]), ep, em];
    ib[RN] = [0, ep, em];
    ib[FLIP] = ib[VNC];
    let e_l = if on[LOCK] {
        sharp_err([lp, lip, lm, lim], [ec[0], ec[1], ec[0], ec[1]], n)
            .ok_or("lock_sharp_bound_argument_low_end_not_positive")?
    } else {
        0
    };
    ib[LOCK] = [e_l, ep, ep];
    let mut ib6 = ib[VNC];
    for e in ib6.iter_mut() {
        *e = cu(*e, ONEU + (1 << 11)) + 3;
    }
    ib[MODE0] = ib6;
    let mut sb = [ep + em; NV];
    sb[LOCK] = 2 * ep;
    Ok(Starts { init, uv, ib, sb })
}

/// The 34 summed terms of one sample at one record (TWB order) and the 11 values the bounds read.
/// obs is (zr, zi, xw, xnc, f, br, bi, zcr, zci, xc) as TWB_DUMP_OBS prints it.
pub fn twb_terms(obs: &[i64; 10]) -> ([i128; NF], [i64; 11]) {
    let [zr, zi, xw, xnc, f, br, bi, zcr, zci, xc] = *obs;
    let (dzr, dzi, dxw, dxnc) = (zr - zcr, zi - zci, xw - xc, xnc - xc);
    let w = i128::from;
    let fq = |v: i64| (w(v) * w(v)) >> Q;
    let terms = [
        w(zr),
        w(zi),
        w(dzr),
        w(dzi),
        w(xw),
        w(dxw),
        w(xnc),
        w(dxnc),
        w(f),
        fq(dzr),
        fq(dxw),
        fq(dxnc),
        fq(zr),
        fq(xw),
        fq(xnc),
        fq(dzi),
        w(f) * w(f),
        w(br),
        w(bi),
        w(br) * w(br),
        w(bi) * w(bi),
        w(br) * w(bi),
        w(zr) * w(xw),
        w(zr) * w(xnc),
        w(dzr) * w(dxw),
        w(dzr) * w(dxnc),
        w(zr) * w(zr),
        w(zi) * w(zi),
        w(dzr) * w(dzr),
        w(dzi) * w(dzi),
        w(xw) * w(xw),
        w(dxw) * w(dxw),
        w(xnc) * w(xnc),
        w(dxnc) * w(dxnc),
    ];
    (terms, [zr, zi, dzr, dzi, xw, dxw, xnc, dxnc, f, br, bi])
}

/// The per-sample bound of each TWB field (the engine's field_bounds). ob is (b_zr, b_zi, b_xw, b_xnc, b_f, b_br, b_bi)
/// of TWB_DUMP_RB, du the variant's seed bound (TWB_DUMP_IB seeds), vals from twb_terms, zc = (zcr, zci).
pub fn field_bounds(
    ctrl: (i64, i64, i64),
    du: u128,
    ob: &[u128; 7],
    vals: [i64; 11],
    zc: (i64, i64),
) -> [u128; NF] {
    let (cc, rs, _) = ctrl;
    let bzc = 2 + cu(uabs(cc), du) + cu(uabs(rs), du);
    let (zcr, zci) = (uabs(zc.0), uabs(zc.1));
    let bxc = 3 + cu(2 * zcr, bzc) + cu(2 * zci, bzc) + 2 * cu(bzc, bzc);
    let [zr, zi, dzr, dzi, xw, dxw, xnc, dxnc, f, br, bi] = vals.map(uabs);
    let [bzr, bzi, bxw, bxnc, bf, bbr, bbi] = *ob;
    let (bdzr, bdzi, bdxw, bdxnc) = (bzr + bzc, bzi + bzc, bxw + bxc, bxnc + bxc);
    let qb = |a: u128, b: u128| cu(2 * a, b) + cu(b, b) + 1;
    let sq = |a: u128, b: u128| 2 * a * b + b * b;
    let pr = |a: u128, ba: u128, c: u128, bc: u128| a * bc + c * ba + ba * bc;
    [
        bzr,
        bzi,
        bdzr,
        bdzi,
        bxw,
        bdxw,
        bxnc,
        bdxnc,
        bf,
        qb(dzr, bdzr),
        qb(dxw, bdxw),
        qb(dxnc, bdxnc),
        qb(zr, bzr),
        qb(xw, bxw),
        qb(xnc, bxnc),
        qb(dzi, bdzi),
        sq(f, bf),
        bbr,
        bbi,
        sq(br, bbr),
        sq(bi, bbi),
        pr(br, bbr, bi, bbi),
        pr(zr, bzr, xw, bxw),
        pr(zr, bzr, xnc, bxnc),
        pr(dzr, bdzr, dxw, bdxw),
        pr(dzr, bdzr, dxnc, bdxnc),
        sq(zr, bzr),
        sq(zi, bzi),
        sq(dzr, bdzr),
        sq(dzi, bdzi),
        sq(xw, bxw),
        sq(dxw, bdxw),
        sq(xnc, bxnc),
        sq(dxnc, bdxnc),
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn isqrt_is_the_floor_root() {
        for n in 0u128..5000 {
            let r = isqrt(n);
            assert!(r * r <= n && (r + 1) * (r + 1) > n, "{n}");
        }
        let big = (1u128 << 100) + 12345;
        let r = isqrt(big);
        assert!(r * r <= big && (r + 1) * (r + 1) > big);
    }

    #[test]
    fn m_floors_toward_minus_infinity() {
        assert_eq!(m(-1, 1), -1);
        assert_eq!(m(ONE, -3), -3);
        assert_eq!(m(ONE / 2, 3), 1);
        assert_eq!(m(-(ONE / 2), 3), -2);
    }

    #[test]
    fn h_at_n27_matches_the_engine_row() {
        // TWB rows of a twens 0.4.0 dump at N=27 print h=105800555712.
        assert_eq!(h_of(27), 105_800_555_712);
    }
}
