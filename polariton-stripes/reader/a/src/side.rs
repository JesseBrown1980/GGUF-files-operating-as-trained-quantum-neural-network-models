//! The per-index side file (P08 and P13, calls below 64): br and b_br of every sampled variant at steps 64 and 128,
//! with each sample's atom flags. Layout: AGG-FORMAT.md, section "Side file".

use crate::sha256::{hex, Sha256};
use crate::stream::Parsed;
use crate::Stop;
use std::fs::File;
use std::io::Write;
use std::path::Path;

pub const MAGIC: &[u8; 8] = b"STRPSIDE";
pub const FORMAT: u32 = 1;
pub const SIDE_STEPS: [u64; 2] = [64, 128];

pub struct Written {
    pub bytes: u64,
    pub sha256: String,
    pub indices: u64,
    pub steps: Vec<u64>,
}

/// The side file's bytes for one call.
pub fn bytes(p: &Parsed, flags: &[u64]) -> Result<(Vec<u8>, Vec<u64>), Stop> {
    let recs: Vec<usize> = (0..p.nr)
        .filter(|&r| SIDE_STEPS.contains(&p.head.steps[r]))
        .collect();
    let steps: Vec<u64> = recs.iter().map(|&r| p.head.steps[r]).collect();
    let mut mask: u32 = 0;
    for &v in &p.vars {
        mask |= 1 << v;
    }
    let count = p.count();
    let mut out: Vec<u8> = Vec::with_capacity(64 + count * (8 + 16 * p.nv() * recs.len()));
    out.extend_from_slice(MAGIC);
    out.extend_from_slice(&FORMAT.to_le_bytes());
    out.extend_from_slice(&(p.nv() as u32).to_le_bytes());
    out.extend_from_slice(&mask.to_le_bytes());
    out.extend_from_slice(&(recs.len() as u32).to_le_bytes());
    for k in 0..2 {
        let s = steps.get(k).copied().unwrap_or(0) as u32;
        out.extend_from_slice(&s.to_le_bytes());
    }
    out.extend_from_slice(&p.head.start.to_le_bytes());
    out.extend_from_slice(&p.head.count.to_le_bytes());
    out.extend_from_slice(&[0u8; 16]);
    for (s, f) in flags.iter().enumerate().take(count) {
        out.extend_from_slice(&f.to_le_bytes());
        for vi in 0..p.nv() {
            for &r in &recs {
                let br = p.obs[p.svr(s, vi, r)][5];
                let bbr = u64::try_from(p.rb[p.svr(s, vi, r)][6])
                    .map_err(|_| Stop::new("side_bound_above_u64", format!("sample={s}")))?;
                out.extend_from_slice(&br.to_le_bytes());
                out.extend_from_slice(&bbr.to_le_bytes());
            }
        }
    }
    Ok((out, steps))
}

pub fn write(path: &Path, p: &Parsed, flags: &[u64]) -> Result<Written, Stop> {
    let (data, steps) = bytes(p, flags)?;
    let mut sha = Sha256::new();
    sha.update(&data);
    let res = File::create(path).and_then(|mut f| f.write_all(&data).and_then(|_| f.sync_all()));
    if let Err(e) = res {
        let _ = std::fs::remove_file(path);
        return Err(Stop::new("side_write", e.to_string()));
    }
    Ok(Written {
        bytes: data.len() as u64,
        sha256: hex(&sha.finish()),
        indices: p.head.count,
        steps,
    })
}
