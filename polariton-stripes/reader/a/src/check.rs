//! The stream checked against itself: each sample's starts, control seeds and start bounds rebuilt from its draws,
//! each linear control from its seeds, and every TWENS, TWPAIR, TWB, TWB_ROUND, TWB_PAIR and TWB_PAIR_ROUND field
//! from the per-sample rows. Any difference is a STOP.

use crate::eng::{
    cu, field_bounds, h_of, lin, starts, twb_terms, uabs, FIELDS, LEGACY, MODE0, NF, NV, ONE,
    PAIRS, VNAME,
};
use crate::stream::Parsed;
use crate::Stop;

/// What was compared, for the AGG_CHECK row.
pub struct Checked {
    pub samples: u64,
    pub starts: u64,
    pub lin: u64,
    pub rows: u64,
    pub fields: u64,
}

pub const G_UNIT: i64 = 1 << 35;
pub const C_MAX: i64 = 2048;

/// c_i = g_i / 2^35 (rule ATOMS); every g_i must be a multiple of 2^35 with |c_i| <= 2048.
pub fn noise_values(g: &[i64; 6], idx: u64) -> Result<[i64; 6], Stop> {
    let mut c = [0i64; 6];
    for (k, (ci, gi)) in c.iter_mut().zip(g.iter()).enumerate() {
        if gi % G_UNIT != 0 || (gi / G_UNIT).abs() > C_MAX {
            return Err(Stop::new(
                "draw_not_a_coin_count",
                format!("idx={idx},g{k}={gi}"),
            ));
        }
        *ci = gi / G_UNIT;
    }
    Ok(c)
}

fn mismatch(row: &str, step: u64, who: &str, field: &str, stream: String, reader: String) -> Stop {
    Stop::new(
        "summary_mismatch",
        format!("row={row},step={step},of={who},field={field},stream={stream},reader={reader}"),
    )
}

pub fn check(p: &Parsed) -> Result<Checked, Stop> {
    let h = &p.head;
    let n = h.n;
    let on = h.on;
    let count = p.count();
    let mut done = Checked {
        samples: count as u64,
        starts: 0,
        lin: 0,
        rows: 0,
        fields: 0,
    };
    if let Some(hr) = p.h {
        if hr != h_of(n) {
            return Err(Stop::new(
                "h_mismatch",
                format!("stream={hr},reader={}", h_of(n)),
            ));
        }
    }
    for s in 0..count {
        let idx = h.start + s as u64;
        noise_values(&p.g[s], idx)?;
        let rot = p.rot[s];
        if !on[MODE0] && rot != [ONE, 0] {
            return Err(Stop::new("rot_without_MODE0", format!("idx={idx}")));
        }
        let st = starts(n, &p.g[s], (rot[0], rot[1]), &on)
            .map_err(|e| Stop::new("start_rebuild", format!("idx={idx},why={e}")))?;
        let eta0 = p.ib[p.sv(s, 0)][4];
        for (vi, &v) in p.vars.iter().enumerate() {
            let k = p.sv(s, vi);
            let who = format!("idx={idx},variant={}", VNAME[v]);
            if p.init[k] != st.init[v] {
                return Err(Stop::new("start_mismatch", who));
            }
            if p.uv[k] != st.uv[v] {
                return Err(Stop::new("control_seed_mismatch", who));
            }
            let ib = p.ib[k];
            if [ib[0], ib[1], ib[2]] != st.ib[v] || ib[3] != st.sb[v] {
                return Err(Stop::new("start_bound_mismatch", who));
            }
            if ib[4] != eta0 || (!on[MODE0] && ib[4] != 0) {
                return Err(Stop::new("eta_mismatch", who));
            }
            done.starts += 1;
        }
    }
    let mut pos = [None; NV];
    for (vi, &v) in p.vars.iter().enumerate() {
        pos[v] = Some(vi);
    }
    for r in 0..p.nr {
        let rec = &p.rec[r];
        let step = h.steps[r];
        for (vi, &v) in p.vars.iter().enumerate() {
            let mut sums = [0i128; NF];
            let mut rbs = [0u128; NF];
            let mut eps_max = 0u128;
            for s in 0..count {
                let o = &p.obs[p.svr(s, vi, r)];
                let (zcr, zci, xc) = lin(rec.ctrl, &p.uv[p.sv(s, vi)], n);
                if (o[7], o[8], o[9]) != (zcr, zci, xc) {
                    return Err(Stop::new(
                        "linear_control_mismatch",
                        format!(
                            "idx={},variant={},step={step}",
                            h.start + s as u64,
                            VNAME[v]
                        ),
                    ));
                }
                done.lin += 1;
                let (terms, vals) = twb_terms(o);
                for (a, t) in sums.iter_mut().zip(terms) {
                    *a += t;
                }
                let b = &p.rb[p.svr(s, vi, r)];
                let ob = [b[1], b[2], b[3], b[4], b[5], b[6], b[7]];
                let fb = field_bounds(rec.ctrl, p.ib[p.sv(s, vi)][3], &ob, vals, (zcr, zci));
                for (a, t) in rbs.iter_mut().zip(fb) {
                    *a += t;
                }
                eps_max = eps_max.max(b[0]);
            }
            let twb = rec.twb[v].ok_or_else(|| Stop::new("missing_TWB", VNAME[v]))?;
            for k in 0..NF {
                if twb[k] != sums[k] {
                    return Err(mismatch(
                        "TWB",
                        step,
                        VNAME[v],
                        FIELDS[k],
                        twb[k].to_string(),
                        sums[k].to_string(),
                    ));
                }
            }
            let (rrb, reps) =
                rec.round[v].ok_or_else(|| Stop::new("missing_TWB_ROUND", VNAME[v]))?;
            for k in 0..NF {
                if rrb[k] != rbs[k] {
                    let f = format!("rb_{}", FIELDS[k]);
                    return Err(mismatch(
                        "TWB_ROUND",
                        step,
                        VNAME[v],
                        &f,
                        rrb[k].to_string(),
                        rbs[k].to_string(),
                    ));
                }
            }
            if reps != eps_max {
                return Err(mismatch(
                    "TWB_ROUND",
                    step,
                    VNAME[v],
                    "eps_max",
                    reps.to_string(),
                    eps_max.to_string(),
                ));
            }
            done.rows += 2;
            done.fields += 2 * NF as u64 + 1;
            if let Some(&(_, name)) = LEGACY.iter().find(|(lv, _)| *lv == v) {
                let tw = rec.twens[v].ok_or_else(|| Stop::new("missing_TWENS", name))?;
                for k in 0..16 {
                    if tw[k] != sums[k] {
                        return Err(mismatch(
                            "TWENS",
                            step,
                            name,
                            FIELDS[k],
                            tw[k].to_string(),
                            sums[k].to_string(),
                        ));
                    }
                }
                done.rows += 1;
                done.fields += 16;
            }
        }
        let mut pd = [[0i128; 3]; PAIRS.len()];
        let mut prb = [[0u128; 3]; PAIRS.len()];
        for (k, &(va, oa, vb, ob, _)) in PAIRS.iter().enumerate() {
            let (Some(ia), Some(ib)) = (pos[va], pos[vb]) else {
                continue;
            };
            for s in 0..count {
                let d = p.obs[p.svr(s, ia, r)][oa] - p.obs[p.svr(s, ib, r)][ob];
                let d128 = i128::from(d);
                pd[k][0] += d128;
                pd[k][1] += (d128 * d128) >> crate::eng::Q;
                pd[k][2] += d128 * d128;
                let bd = p.rb[p.svr(s, ia, r)][1 + oa] + p.rb[p.svr(s, ib, r)][1 + ob];
                let ad = uabs(d);
                prb[k][0] += bd;
                prb[k][1] += cu(2 * ad, bd) + cu(bd, bd) + 1;
                prb[k][2] += 2 * ad * bd + bd * bd;
            }
            let name = PAIRS[k].4;
            let (sd, sb) = rec.pair[k].ok_or_else(|| Stop::new("missing_TWB_PAIR", name))?;
            for (j, f) in ["d", "qd", "d2"].iter().enumerate() {
                if sd[j] != pd[k][j] {
                    return Err(mismatch(
                        "TWB_PAIR",
                        step,
                        name,
                        f,
                        sd[j].to_string(),
                        pd[k][j].to_string(),
                    ));
                }
            }
            for (j, f) in ["rb_d", "rb_qd", "rb_d2"].iter().enumerate() {
                if sb[j] != prb[k][j] {
                    return Err(mismatch(
                        "TWB_PAIR_ROUND",
                        step,
                        name,
                        f,
                        sb[j].to_string(),
                        prb[k][j].to_string(),
                    ));
                }
            }
            done.rows += 2;
            done.fields += 6;
        }
        if let Some(tp) = rec.twpair {
            const NAMES: [&str; 10] = [
                "v1xw_vnxnc",
                "q0",
                "v1zr_vnzr",
                "q1",
                "v0xw_v1xw",
                "q2",
                "v0zr_v1zr",
                "q3",
                "v1xw_vnxw",
                "q4",
            ];
            for k in 0..5 {
                for j in 0..2 {
                    if tp[2 * k + j] != pd[k][j] {
                        return Err(mismatch(
                            "TWPAIR",
                            step,
                            "legacy",
                            NAMES[2 * k + j],
                            tp[2 * k + j].to_string(),
                            pd[k][j].to_string(),
                        ));
                    }
                }
            }
            done.rows += 1;
            done.fields += 10;
        }
    }
    Ok(done)
}
