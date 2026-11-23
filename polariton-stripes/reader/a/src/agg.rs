//! The per-call aggregate: rules SECTOR and ATOMS per sample, and per (record, variant) the certified counts, the sign
//! counts, the moment sums, the block sums for n = 4..4096 and the comparisons against VNC on common samples.

use crate::big::U256;
use crate::check::noise_values;
use crate::eng::{LOCK, NV, VNAME, VNC};
use crate::sector::{certify, lattice_sigma, on_edge, Atoms, Sign};
use crate::stream::Parsed;
use crate::Stop;

/// Block sizes n = 2^k, k = 2..12.
pub const BLOCKS: [u64; 11] = [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096];
/// |B| >= 2^-20 at 2^40: br^2 + bi^2 >= 2^40.
pub const BIG_B2: i128 = 1 << 40;

#[derive(Clone, Copy, Default)]
pub struct Sums {
    pub m: u64,
    pub br: i128,
    pub bi: i128,
    pub br2: i128,
    pub bi2: i128,
    pub brbi: i128,
    pub bbr: u128,
    pub bbi: u128,
    pub bbr2: u128,
    pub bbi2: u128,
}

impl Sums {
    fn add(&mut self, br: i64, bi: i64, bbr: u128, bbi: u128) {
        let (r, i) = (i128::from(br), i128::from(bi));
        self.m += 1;
        self.br += r;
        self.bi += i;
        self.br2 += r * r;
        self.bi2 += i * i;
        self.brbi += r * i;
        self.bbr += bbr;
        self.bbi += bbi;
        self.bbr2 += bbr * bbr;
        self.bbi2 += bbi * bbi;
    }
}

#[derive(Clone, Copy)]
pub struct Blk {
    pub n: u64,
    pub k: u64,
    fill: u64,
    cr: i128,
    ci: i128,
    cw: u128,
    pub s2: u128,
    pub s4: U256,
    pub w: u128,
    pub w2: U256,
    pub sw: U256,
}

fn add256(a: U256, b: U256) -> Result<U256, Stop> {
    a.checked_add(b)
        .ok_or_else(|| Stop::new("block_sum_overflow", "u256"))
}

impl Blk {
    fn new(n: u64) -> Self {
        Self {
            n,
            k: 0,
            fill: 0,
            cr: 0,
            ci: 0,
            cw: 0,
            s2: 0,
            s4: U256::ZERO,
            w: 0,
            w2: U256::ZERO,
            sw: U256::ZERO,
        }
    }

    fn push(&mut self, br: i64, bi: i64) -> Result<(), Stop> {
        let (r, i) = (i128::from(br), i128::from(bi));
        self.cr += r;
        self.ci += i;
        self.cw += (r * r + i * i) as u128;
        self.fill += 1;
        if self.fill == self.n {
            let x = self
                .cr
                .checked_mul(self.cr)
                .and_then(|a| self.ci.checked_mul(self.ci).and_then(|b| a.checked_add(b)))
                .ok_or_else(|| Stop::new("block_sum_overflow", "abs_S_b_squared"))?
                as u128;
            self.s2 += x;
            self.s4 = add256(self.s4, U256::mul_u128(x, x))?;
            self.w += self.cw;
            self.w2 = add256(self.w2, U256::mul_u128(self.cw, self.cw))?;
            self.sw = add256(self.sw, U256::mul_u128(x, self.cw))?;
            self.k += 1;
            self.fill = 0;
            self.cr = 0;
            self.ci = 0;
            self.cw = 0;
        }
        Ok(())
    }
}

/// One (record, variant).
#[derive(Clone)]
pub struct Vr {
    pub atoms: u64,
    pub xatoms: u64,
    pub xatom_bi_nz: u64,
    pub na_bi0: u64,
    pub sec: [u64; 16],
    pub amb: u64,
    pub br: [u64; 3],
    pub bi: [u64; 3],
    pub at_br: [u64; 3],
    pub at_bi: [u64; 3],
    pub all: Sums,
    pub atom: Sums,
    pub blk: Vec<Blk>,
    pub lock_cert: u64,
    pub lock_mis: u64,
}

impl Vr {
    fn new() -> Self {
        Self {
            atoms: 0,
            xatoms: 0,
            xatom_bi_nz: 0,
            na_bi0: 0,
            sec: [0; 16],
            amb: 0,
            br: [0; 3],
            bi: [0; 3],
            at_br: [0; 3],
            at_bi: [0; 3],
            all: Sums::default(),
            atom: Sums::default(),
            blk: BLOCKS.iter().map(|&n| Blk::new(n)).collect(),
            lock_cert: 0,
            lock_mis: 0,
        }
    }
}

/// One (record, variant other than VNC) against VNC on the samples that are non-atoms in both.
#[derive(Clone, Copy, Default)]
pub struct Cmp {
    pub common: u64,
    pub br: [[u64; 3]; 3],
    pub bi: [[u64; 3]; 3],
    pub cert2: u64,
    pub mis: u64,
    pub cert2_big_both: u64,
    pub mis_big_both: u64,
    pub cert2_big_any: u64,
    pub mis_big_any: u64,
}

pub struct Agg {
    pub m: u64,
    pub nl_klein: u64,
    pub nl_exch: u64,
    pub lk_klein: u64,
    pub lk_exch: u64,
    pub lock_atoms: u64,
    pub lat: [u64; 16],
    pub lat_edge: u64,
    /// [r][vi]
    pub vr: Vec<Vec<Vr>>,
    /// [r][vi], None for VNC
    pub cmp: Vec<Vec<Option<Cmp>>>,
    /// per sample, the side-file flag word
    pub flags: Vec<u64>,
}

#[derive(Clone, Copy)]
struct One {
    atom: bool,
    cert: Option<u8>,
    sbr: Sign,
    sbi: Sign,
    big: bool,
}

pub fn aggregate(p: &Parsed) -> Result<Agg, Stop> {
    let h = &p.head;
    let (nv, nr, count) = (p.nv(), p.nr, p.count());
    let mut a = Agg {
        m: count as u64,
        nl_klein: 0,
        nl_exch: 0,
        lk_klein: 0,
        lk_exch: 0,
        lock_atoms: 0,
        lat: [0; 16],
        lat_edge: 0,
        vr: vec![vec![Vr::new(); nv]; nr],
        cmp: (0..nr)
            .map(|_| {
                (0..nv)
                    .map(|vi| if vi == 0 { None } else { Some(Cmp::default()) })
                    .collect()
            })
            .collect(),
        flags: Vec::with_capacity(count),
    };
    if p.vars.first() != Some(&VNC) {
        return Err(Stop::new("no_VNC", "mask"));
    }
    let mut one = [One {
        atom: false,
        cert: None,
        sbr: Sign::Amb,
        sbi: Sign::Amb,
        big: false,
    }; NV];
    for s in 0..count {
        let c = noise_values(&p.g[s], h.start + s as u64)?;
        let at = Atoms::of([c[0], c[1], c[2], c[3]]);
        a.flags.push(at.bits());
        a.nl_klein += u64::from(at.nl_klein);
        a.nl_exch += u64::from(at.nl_exch);
        a.lk_klein += u64::from(at.lk_klein);
        a.lk_exch += u64::from(at.lk_exch);
        let lock_atom = at.atom(true, h.y_zero);
        let lat_sigma = lattice_sigma(c[0], c[1]);
        if lock_atom {
            a.lock_atoms += 1;
        } else {
            let (x, y) = (i128::from(c[0]), i128::from(c[1]));
            match lat_sigma {
                Some(k) if !on_edge(x * x - y * y, 2 * x * y) => a.lat[usize::from(k)] += 1,
                _ => a.lat_edge += 1,
            }
        }
        for r in 0..nr {
            for (vi, &v) in p.vars.iter().enumerate() {
                let lock = v == LOCK;
                let o = &p.obs[p.svr(s, vi, r)];
                let b = &p.rb[p.svr(s, vi, r)];
                let (br, bi, bbr, bbi) = (o[5], o[6], b[6], b[7]);
                let atom = at.atom(lock, h.y_zero);
                let cert = if atom {
                    None
                } else {
                    certify(br, bi, bbr, bbi)
                };
                let (sbr, sbi) = (Sign::of(br, bbr), Sign::of(bi, bbi));
                let big =
                    i128::from(br) * i128::from(br) + i128::from(bi) * i128::from(bi) >= BIG_B2;
                one[vi] = One {
                    atom,
                    cert,
                    sbr,
                    sbi,
                    big,
                };
                let q = &mut a.vr[r][vi];
                q.all.add(br, bi, bbr, bbi);
                if atom {
                    q.atoms += 1;
                    q.atom.add(br, bi, bbr, bbi);
                    q.at_br[sbr.index()] += 1;
                    q.at_bi[sbi.index()] += 1;
                } else {
                    match cert {
                        Some(k) => q.sec[usize::from(k)] += 1,
                        None => q.amb += 1,
                    }
                    q.br[sbr.index()] += 1;
                    q.bi[sbi.index()] += 1;
                    if bi == 0 {
                        q.na_bi0 += 1;
                    }
                    if lock {
                        if let Some(k) = cert {
                            q.lock_cert += 1;
                            if Some(k) != lat_sigma {
                                q.lock_mis += 1;
                            }
                        }
                    }
                }
                if at.exch(lock) {
                    q.xatoms += 1;
                    if bi != 0 {
                        q.xatom_bi_nz += 1;
                    }
                }
                for blk in q.blk.iter_mut() {
                    blk.push(br, bi)?;
                }
            }
            let rf = one[0];
            for (vi, x) in one.iter().enumerate().take(nv).skip(1) {
                let Some(cm) = a.cmp[r][vi].as_mut() else {
                    continue;
                };
                if x.atom || rf.atom {
                    continue;
                }
                cm.common += 1;
                cm.br[x.sbr.index()][rf.sbr.index()] += 1;
                cm.bi[x.sbi.index()][rf.sbi.index()] += 1;
                if let (Some(kx), Some(kr)) = (x.cert, rf.cert) {
                    let differ = u64::from(kx != kr);
                    cm.cert2 += 1;
                    cm.mis += differ;
                    if x.big && rf.big {
                        cm.cert2_big_both += 1;
                        cm.mis_big_both += differ;
                    }
                    if x.big || rf.big {
                        cm.cert2_big_any += 1;
                        cm.mis_big_any += differ;
                    }
                }
            }
        }
    }
    for (r, row) in a.vr.iter().enumerate() {
        for (vi, q) in row.iter().enumerate() {
            let v = p.vars[vi];
            let mp = a.m - q.atoms;
            let sec: u64 = q.sec.iter().sum::<u64>() + q.amb;
            let twb = p.rec[r].twb[v].unwrap_or([0; crate::eng::NF]);
            let rb = p.rec[r].round[v]
                .map(|x| x.0)
                .unwrap_or([0; crate::eng::NF]);
            let s = &q.all;
            let w_all = (s.br2 + s.bi2) as u128;
            let blocks_ok = q.blk.iter().all(|b| b.k * b.n != a.m || b.w == w_all);
            if sec != mp
                || q.br.iter().sum::<u64>() != mp
                || q.bi.iter().sum::<u64>() != mp
                || q.at_br.iter().sum::<u64>() != q.atoms
                || q.at_bi.iter().sum::<u64>() != q.atoms
                || q.all.m != a.m
                || q.atom.m != q.atoms
                || [s.br, s.bi, s.br2, s.bi2, s.brbi]
                    != [twb[17], twb[18], twb[19], twb[20], twb[21]]
                || [s.bbr, s.bbi] != [rb[17], rb[18]]
                || !blocks_ok
            {
                return Err(Stop::new(
                    "aggregate_identity",
                    format!("step={},variant={}", h.steps[r], VNAME[p.vars[vi]]),
                ));
            }
        }
    }
    Ok(a)
}

fn join<T: ToString>(v: &[T], sep: &str) -> String {
    v.iter()
        .map(|x| x.to_string())
        .collect::<Vec<_>>()
        .join(sep)
}

fn table9(t: &[[u64; 3]; 3]) -> String {
    let flat: Vec<u64> = t.iter().flat_map(|row| row.iter().copied()).collect();
    join(&flat, ":")
}

/// The AGG rows of one call between AGG_CALL and AGG_SIDE (grammar: AGG-FORMAT.md).
pub fn rows(p: &Parsed, a: &Agg, pc: &str) -> Vec<String> {
    let h = &p.head;
    let mut out = Vec::new();
    out.push(format!(
        "AGG_ATOMS|{pc}|M={}|nl_klein={}|nl_exch={}|lk_klein={}|lk_exch={}|json=0",
        a.m, a.nl_klein, a.nl_exch, a.lk_klein, a.lk_exch
    ));
    out.push(format!(
        "AGG_LAT|{pc}|lock_atoms={}|lat_edge={}|lat={}|json=0",
        a.lock_atoms,
        a.lat_edge,
        join(&a.lat, ":")
    ));
    for r in 0..p.nr {
        let step = h.steps[r];
        for (vi, &v) in p.vars.iter().enumerate() {
            let q = &a.vr[r][vi];
            let key = format!("{pc}|step={step}|variant={}", VNAME[v]);
            out.push(format!(
                "AGG_VR|{key}|M={}|atoms={}|xatoms={}|xatom_bi_nz={}|mp={}|na_bi0={}|sec={}|amb={}|br_pos={}|br_neg={}|br_amb={}|bi_pos={}|bi_neg={}|bi_amb={}|at_br_pos={}|at_br_neg={}|at_br_amb={}|at_bi_pos={}|at_bi_neg={}|at_bi_amb={}|json=0",
                a.m,
                q.atoms,
                q.xatoms,
                q.xatom_bi_nz,
                a.m - q.atoms,
                q.na_bi0,
                join(&q.sec, ":"),
                q.amb,
                q.br[0],
                q.br[1],
                q.br[2],
                q.bi[0],
                q.bi[1],
                q.bi[2],
                q.at_br[0],
                q.at_br[1],
                q.at_br[2],
                q.at_bi[0],
                q.at_bi[1],
                q.at_bi[2]
            ));
            for (set, sm) in [("all", &q.all), ("atom", &q.atom)] {
                out.push(format!(
                    "AGG_SUM|{key}|set={set}|m={}|br={}|bi={}|br2={}|bi2={}|brbi={}|bbr={}|bbi={}|bbr2={}|bbi2={}|json=0",
                    sm.m, sm.br, sm.bi, sm.br2, sm.bi2, sm.brbi, sm.bbr, sm.bbi, sm.bbr2, sm.bbi2
                ));
            }
            for b in &q.blk {
                out.push(format!(
                    "AGG_BLK|{key}|n={}|K={}|s2={}|s4={}|w={}|w2={}|sw={}|json=0",
                    b.n, b.k, b.s2, b.s4, b.w, b.w2, b.sw
                ));
            }
            if let Some(cm) = &a.cmp[r][vi] {
                out.push(format!(
                    "AGG_CMP|{key}|ref=VNC|common={}|br={}|bi={}|cert2={}|mis={}|cert2_big_both={}|mis_big_both={}|cert2_big_any={}|mis_big_any={}|json=0",
                    cm.common,
                    table9(&cm.br),
                    table9(&cm.bi),
                    cm.cert2,
                    cm.mis,
                    cm.cert2_big_both,
                    cm.mis_big_both,
                    cm.cert2_big_any,
                    cm.mis_big_any
                ));
            }
            if v == LOCK {
                out.push(format!(
                    "AGG_LOCK|{pc}|step={step}|cert={}|mis={}|json=0",
                    q.lock_cert, q.lock_mis
                ));
            }
        }
        if let Some(nl) = &p.rec[r].nl {
            out.push(format!("AGG_NL|{nl}"));
        }
    }
    out
}
