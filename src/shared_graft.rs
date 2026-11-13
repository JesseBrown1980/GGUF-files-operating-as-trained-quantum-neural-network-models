//! One shared byte predictor and addressable 81x81 integer logit-delta heads.
//! A populated address is a small trained correction, not an independent model.
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

use crate::gguf_model::{self, Kv};
use crate::specialists::{family_of_byte, log2_q12};
use std::collections::BTreeSet;

pub const PARENTS: usize = 81;
pub const LEAVES_PER_PARENT: usize = 81;
pub const CAPACITY: usize = PARENTS * LEAVES_PER_PARENT;
pub const BLOCK: usize = 256;
pub const TRAIN_LIMIT: usize = 131_072;
pub const VALID_LIMIT: usize = 512;
const BASE_ROW_LIMIT: u32 = 2_048;
const ARCH: &str = "asolaria-shared-graft-byte81x81";

pub type Delta = [i8; 3];

#[derive(Clone)]
pub struct Backbone {
    counts: Vec<u16>,
    prefix: Vec<[u16; 3]>,
    group_sums: Vec<[u16; 3]>,
}

#[derive(Clone, Default)]
pub struct Counts {
    raw: Vec<u32>,
    pub sources: usize,
    pub bytes: u64,
}

impl Counts {
    #[must_use]
    pub fn new() -> Self {
        Self {
            raw: vec![0; 65_536],
            sources: 0,
            bytes: 0,
        }
    }

    pub fn add_file(&mut self, bytes: &[u8]) -> Result<(), &'static str> {
        self.sources += 1;
        self.bytes += bytes.len() as u64;
        let mut prev = 0_u8;
        for &next in bytes {
            let idx = usize::from(prev) * 256 + usize::from(next);
            self.raw[idx] = self.raw[idx].checked_add(1).ok_or("count overflow")?;
            prev = next;
        }
        Ok(())
    }

    #[must_use]
    pub fn finish(self) -> Backbone {
        let mut normalized = vec![0_u16; 65_536];
        for prev in 0..256 {
            let row = &self.raw[prev * 256..(prev + 1) * 256];
            let sum: u64 = row.iter().map(|v| u64::from(*v)).sum();
            for (b, &count) in row.iter().enumerate() {
                normalized[prev * 256 + b] = if sum <= u64::from(BASE_ROW_LIMIT) {
                    count as u16
                } else {
                    (u64::from(count) * u64::from(BASE_ROW_LIMIT) / sum) as u16
                };
            }
        }
        Backbone::from_counts(normalized)
    }
}

impl Backbone {
    fn from_counts(counts: Vec<u16>) -> Self {
        assert_eq!(counts.len(), 65_536);
        let mut prefix = vec![[0_u16; 3]; 65_536];
        let mut group_sums = vec![[0_u16; 3]; 256];
        for (prev, sums) in group_sums.iter_mut().enumerate() {
            let mut seen = [0_u16; 3];
            for next in 0..256 {
                let i = prev * 256 + next;
                prefix[i] = seen;
                let g = family_of_byte(next as u8);
                seen[g] += counts[i] + 1;
            }
            *sums = seen;
        }
        Self {
            counts,
            prefix,
            group_sums,
        }
    }

    #[must_use]
    pub fn trained_entries(&self) -> usize {
        self.counts.iter().filter(|&&x| x > 0).count()
    }

    fn weights(delta: Delta) -> [u32; 3] {
        let mut out = [0; 3];
        for g in 0..3 {
            assert!((-4..=4).contains(&delta[g]));
            out[g] = 1_u32 << ((i32::from(delta[g]) + 4) as u32);
        }
        out
    }

    fn total_with_weights(&self, prev: u8, weights: [u32; 3]) -> u32 {
        self.group_sums[usize::from(prev)]
            .iter()
            .zip(weights)
            .map(|(sum, w)| u32::from(*sum) * w)
            .sum()
    }

    fn cumulative(&self, prev: u8, next: u8, w: [u32; 3]) -> u32 {
        self.prefix[usize::from(prev) * 256 + usize::from(next)]
            .iter()
            .zip(w)
            .map(|(x, weight)| u32::from(*x) * weight)
            .sum()
    }

    #[must_use]
    pub fn bounds(&self, prev: u8, next: u8, delta: Delta) -> (u32, u32, u32) {
        let w = Self::weights(delta);
        let i = usize::from(prev) * 256 + usize::from(next);
        let lo = self.cumulative(prev, next, w);
        let hi = lo + (u32::from(self.counts[i]) + 1) * w[family_of_byte(next)];
        (lo, hi, self.total_with_weights(prev, w))
    }

    #[must_use]
    pub fn symbol_at(&self, prev: u8, value: u32, delta: Delta) -> (u8, u32, u32, u32) {
        let w = Self::weights(delta);
        let total = self.total_with_weights(prev, w);
        assert!(value < total);
        let mut left = 0_usize;
        let mut right = 256_usize;
        while left < right {
            let mid = (left + right) / 2;
            let idx = usize::from(prev) * 256 + mid;
            let upper = self.cumulative(prev, mid as u8, w)
                + (u32::from(self.counts[idx]) + 1) * w[family_of_byte(mid as u8)];
            if value < upper {
                right = mid;
            } else {
                left = mid + 1;
            }
        }
        assert!(left < 256);
        let sym = left as u8;
        let low = self.cumulative(prev, sym, w);
        let high = low
            + (u32::from(self.counts[usize::from(prev) * 256 + left]) + 1) * w[family_of_byte(sym)];
        (sym, low, high, total)
    }

    #[must_use]
    pub fn score(&self, hist: &Histogram, delta: Delta) -> i64 {
        let weights = Self::weights(delta);
        let mut score = 0_i64;
        for (prev, &number) in hist.prev.iter().enumerate() {
            if number != 0 {
                let total = self.total_with_weights(prev as u8, weights);
                score += i64::from(number) * i64::from(log2_q12(total));
            }
        }
        for (g, &number) in hist.groups.iter().enumerate() {
            score -= i64::from(number) * (i64::from(delta[g]) + 4) * 4_096;
        }
        score
    }

    #[must_use]
    pub fn raw_counts(&self) -> &[u16] {
        &self.counts
    }
}

#[derive(Clone)]
pub struct Histogram {
    prev: [u32; 256],
    groups: [u32; 3],
}

impl Default for Histogram {
    fn default() -> Self {
        Self {
            prev: [0; 256],
            groups: [0; 3],
        }
    }
}

impl Histogram {
    pub fn add_file(&mut self, data: &[u8]) {
        let mut prev = 0_u8;
        for &next in data {
            self.prev[usize::from(prev)] += 1;
            self.groups[family_of_byte(next)] += 1;
            prev = next;
        }
    }

    #[must_use]
    pub fn from_past(data: &[u8], begin: usize) -> Self {
        let mut hist = Self::default();
        for index in begin..data.len() {
            let prev = if index == 0 { 0 } else { data[index - 1] };
            hist.prev[usize::from(prev)] += 1;
            hist.groups[family_of_byte(data[index])] += 1;
        }
        hist
    }
}

fn norm(delta: Delta) -> i32 {
    delta.iter().map(|v| i32::from(*v).abs()).sum()
}

#[must_use]
pub fn add_delta(parent: Delta, leaf: Delta) -> Delta {
    [
        parent[0] + leaf[0],
        parent[1] + leaf[1],
        parent[2] + leaf[2],
    ]
}

#[must_use]
pub fn fit_delta(base: &Backbone, val: &Histogram, parent: Delta) -> Delta {
    let mut best = [0_i8; 3];
    let mut best_score = base.score(val, parent);
    for a in -2_i8..=2 {
        for b in -2_i8..=2 {
            for c in -2_i8..=2 {
                let proposed = [a, b, c];
                let score = base.score(val, add_delta(parent, proposed));
                if score < best_score || (score == best_score && norm(proposed) < norm(best)) {
                    best = proposed;
                    best_score = score;
                }
            }
        }
    }
    best
}

#[derive(Clone)]
pub struct Graft {
    pub backbone: Backbone,
    pub parents: [Option<Delta>; PARENTS],
    pub leaves: Vec<Option<Delta>>,
    pub training_sources: u32,
}

impl Graft {
    #[must_use]
    pub fn new(backbone: Backbone, training_sources: u32) -> Self {
        Self {
            backbone,
            parents: [None; PARENTS],
            leaves: vec![None; CAPACITY],
            training_sources,
        }
    }

    #[must_use]
    pub fn learned_leaves(&self) -> usize {
        self.leaves.iter().filter(|x| x.is_some()).count()
    }

    #[must_use]
    pub fn learned_parents(&self) -> usize {
        self.parents.iter().filter(|x| x.is_some()).count()
    }

    #[must_use]
    pub fn first_leaf(&self, parent: usize) -> Option<usize> {
        if parent >= PARENTS {
            return None;
        }
        (parent * LEAVES_PER_PARENT..(parent + 1) * LEAVES_PER_PARENT)
            .find(|&index| self.leaves[index].is_some())
    }

    #[must_use]
    pub fn first_any_leaf(&self) -> Option<usize> {
        (0..CAPACITY).find(|&index| self.leaves[index].is_some())
    }

    #[must_use]
    pub fn shifts(&self, index: usize, mode: RoutingMode) -> Delta {
        if mode == RoutingMode::Base {
            return [0; 3];
        }
        let p = index / LEAVES_PER_PARENT;
        let parent = self.parents[p].unwrap_or([0; 3]);
        if mode == RoutingMode::Parents {
            return parent;
        }
        add_delta(parent, self.leaves[index].unwrap_or([0; 3]))
    }

    /// Exactly one base table and only populated delta addresses are serialized.
    #[must_use]
    pub fn gguf(&self) -> Vec<u8> {
        let mut sparse = Vec::new();
        for (id, &count) in self.backbone.raw_counts().iter().enumerate() {
            if count != 0 {
                sparse.push((id / 256) as u8);
                sparse.push((id % 256) as u8);
                sparse.extend_from_slice(&count.to_le_bytes());
            }
        }
        let mut parents = Vec::new();
        for (i, &head) in self.parents.iter().enumerate() {
            if let Some(delta) = head {
                parents.push(i as u8);
                parents.extend(delta.map(|x| x as u8));
            }
        }
        let mut leaves = Vec::new();
        for (i, &head) in self.leaves.iter().enumerate() {
            if let Some(delta) = head {
                leaves.extend_from_slice(&(i as u16).to_le_bytes());
                leaves.extend(delta.map(|x| x as u8));
            }
        }
        let meta = gguf_model::Model {
            kv: vec![
                ("general.architecture".into(), Kv::Str(ARCH.into())),
                (
                    "general.name".into(),
                    Kv::Str("QNN_SHARED_GRAFT81X81_V1".into()),
                ),
                ("graft.parents_capacity".into(), Kv::U32(PARENTS as u32)),
                ("graft.leaves_capacity".into(), Kv::U32(CAPACITY as u32)),
                (
                    "graft.trained_parents".into(),
                    Kv::U32(self.learned_parents() as u32),
                ),
                (
                    "graft.trained_leaves".into(),
                    Kv::U32(self.learned_leaves() as u32),
                ),
                (
                    "graft.training_sources".into(),
                    Kv::U32(self.training_sources),
                ),
                (
                    "graft.backbone".into(),
                    Kv::Str("byte_bigram_integer".into()),
                ),
                (
                    "graft.scope".into(),
                    Kv::Str("real sparse corrections; no trained empty slot".into()),
                ),
            ],
            tensors: vec![
                (
                    "backbone.sparse".into(),
                    sparse.into_iter().map(|x| x as i8).collect(),
                ),
                (
                    "parents.patch".into(),
                    parents.into_iter().map(|x| x as i8).collect(),
                ),
                (
                    "leaves.patch".into(),
                    leaves.into_iter().map(|x| x as i8).collect(),
                ),
            ],
        };
        gguf_model::write(&meta)
    }

    pub fn from_gguf(raw: &[u8]) -> Result<Self, &'static str> {
        let f = gguf_model::read(raw).ok_or("invalid GGUF")?;
        if f.str("general.architecture") != Some(ARCH)
            || f.u32("graft.parents_capacity") != Some(PARENTS as u32)
            || f.u32("graft.leaves_capacity") != Some(CAPACITY as u32)
            || f.tensors.len() != 3
        {
            return Err("wrong architecture, metadata or tensor count");
        }
        let sparse = f
            .tensor("backbone.sparse")
            .ok_or("missing shared backbone")?;
        let ph = f.tensor("parents.patch").ok_or("missing parent patches")?;
        let lh = f.tensor("leaves.patch").ok_or("missing leaf patches")?;
        if sparse.len() % 4 != 0 || ph.len() % 4 != 0 || lh.len() % 5 != 0 {
            return Err("bad tensor alignment");
        }
        let mut counts = vec![0_u16; 65_536];
        let mut occupied = BTreeSet::new();
        for row in sparse.chunks_exact(4) {
            let id = (row[0] as u8 as usize) * 256 + row[1] as u8 as usize;
            if !occupied.insert(id) {
                return Err("repeated bigram");
            }
            let value = u16::from_le_bytes([row[2] as u8, row[3] as u8]);
            if value == 0 || value > BASE_ROW_LIMIT as u16 {
                return Err("invalid backbone count");
            }
            counts[id] = value;
        }
        for row in counts.chunks_exact(256) {
            let count: u32 = row.iter().map(|&x| u32::from(x)).sum();
            if count > BASE_ROW_LIMIT {
                return Err("backbone row total above normalized cap");
            }
        }
        let mut result = Self::new(
            Backbone::from_counts(counts),
            f.u32("graft.training_sources")
                .ok_or("source count missing")?,
        );
        for row in ph.chunks_exact(4) {
            let id = row[0] as u8 as usize;
            if id >= PARENTS || result.parents[id].is_some() {
                return Err("duplicate or invalid parent");
            }
            let d = [row[1], row[2], row[3]];
            if d.iter().any(|x| !(-2..=2).contains(x)) {
                return Err("bad parent delta");
            }
            result.parents[id] = Some(d);
        }
        for row in lh.chunks_exact(5) {
            let id = u16::from_le_bytes([row[0] as u8, row[1] as u8]) as usize;
            if id >= CAPACITY || result.leaves[id].is_some() {
                return Err("duplicate or invalid leaf");
            }
            let d = [row[2], row[3], row[4]];
            if d.iter().any(|x| !(-2..=2).contains(x)) || result.parents[id / 81].is_none() {
                return Err("bad leaf delta or missing parent");
            }
            result.leaves[id] = Some(d);
        }
        if f.u32("graft.trained_parents") != Some(result.learned_parents() as u32)
            || f.u32("graft.trained_leaves") != Some(result.learned_leaves() as u32)
        {
            return Err("learned-address counts mismatch");
        }
        Ok(result)
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum RoutingMode {
    Base,
    Parents,
    Tree,
}
impl RoutingMode {
    #[must_use]
    pub fn id(self) -> u8 {
        match self {
            Self::Base => 0,
            Self::Parents => 1,
            Self::Tree => 2,
        }
    }

    pub fn parse(id: u8) -> Result<Self, &'static str> {
        match id {
            0 => Ok(Self::Base),
            1 => Ok(Self::Parents),
            2 => Ok(Self::Tree),
            _ => Err("unknown route mode"),
        }
    }
}

/// Parent decision from last 256 already-decoded bytes; leaf decision from
/// bytes since the last parent change. No future input is consulted.
#[derive(Clone)]
pub struct Router {
    pub active: usize,
    pub parent_epoch: usize,
    pub switches: usize,
}

impl Router {
    #[must_use]
    pub fn new(graft: &Graft, mode: RoutingMode) -> Self {
        let active = if mode == RoutingMode::Tree {
            graft.first_any_leaf().expect("no trained leaf")
        } else if mode == RoutingMode::Parents {
            graft
                .parents
                .iter()
                .position(Option::is_some)
                .expect("no parent")
                * 81
        } else {
            0
        };
        Self {
            active,
            parent_epoch: 0,
            switches: 0,
        }
    }

    pub fn select(&mut self, model: &Graft, past: &[u8], mode: RoutingMode) -> usize {
        if mode == RoutingMode::Base || past.len() < BLOCK {
            return self.active;
        }
        let window = Histogram::from_past(past, past.len() - BLOCK);
        let mut parent = self.active / 81;
        let mut best = i64::MAX;
        for id in 0..PARENTS {
            if let Some(delta) = model.parents[id] {
                let score = model.backbone.score(&window, delta);
                if score < best {
                    best = score;
                    parent = id;
                }
            }
        }
        let mut next = parent * 81;
        if mode == RoutingMode::Tree {
            if parent != self.active / 81 {
                self.parent_epoch = past.len();
                next = model
                    .first_leaf(parent)
                    .expect("parent without trained leaf");
            } else if past.len() - self.parent_epoch < BLOCK {
                next = self.active;
            } else {
                let win = Histogram::from_past(past, (past.len() - BLOCK).max(self.parent_epoch));
                let mut best_leaf = i64::MAX;
                for id in parent * 81..(parent + 1) * 81 {
                    if let Some(leaf) = model.leaves[id] {
                        let effective = add_delta(model.parents[parent].unwrap(), leaf);
                        let score = model.backbone.score(&win, effective);
                        if score < best_leaf {
                            best_leaf = score;
                            next = id;
                        }
                    }
                }
            }
        }
        if next != self.active {
            self.switches += 1;
        }
        self.active = next;
        next
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn address_capacity_and_untrained_are_not_independent_models() {
        let mut counts = Counts::new();
        counts.add_file(b"aaabbbc\nqwerty").unwrap();
        let mut g = Graft::new(counts.finish(), 1);
        assert_eq!(g.leaves.len(), 6561);
        assert_eq!(g.learned_leaves(), 0);
        assert_eq!(g.first_any_leaf(), None);
        g.parents[80] = Some([1, -1, 2]);
        g.leaves[6560] = Some([0, -2, 1]);
        let gguf = g.gguf();
        let rebuilt = Graft::from_gguf(&gguf).unwrap();
        assert_eq!(rebuilt.learned_leaves(), 1);
        assert_eq!(rebuilt.first_any_leaf(), Some(6560));
        assert_eq!(rebuilt.shifts(6560, RoutingMode::Tree), [1, -3, 3]);
        let mut corrupted = gguf;
        corrupted[0] ^= 1;
        assert!(Graft::from_gguf(&corrupted).is_err());
    }

    #[test]
    fn count_normalization_and_exact_cumulative_histogram() {
        let mut c = Counts::new();
        c.add_file(&vec![b'A'; 70_000]).unwrap();
        let b = c.finish();
        assert!(b.raw_counts().iter().all(|x| *x <= 2_048));
        for previous in [0, b'A', b'Z'] {
            for delta in [[0; 3], [-4, 2, 4], [4, -3, 1]] {
                let mut sum = 0_u32;
                for n in 0_u16..=255 {
                    let (lo, hi, tot) = b.bounds(previous, n as u8, delta);
                    assert_eq!(lo, sum);
                    sum = hi;
                    assert_eq!(b.symbol_at(previous, lo, delta).0, n as u8);
                    assert!(tot >= hi);
                }
                assert_eq!(sum, b.bounds(previous, 255, delta).2);
            }
        }
    }

    #[test]
    fn validation_only_fits_bounded_delta_and_rejects_bad_head() {
        let mut c = Counts::new();
        c.add_file(b"abcabcabcABCABC\n\n").unwrap();
        let b = c.finish();
        let mut h = Histogram::default();
        h.add_file(b"ABABABABAB\n\n");
        let delta = fit_delta(&b, &h, [0; 3]);
        assert!(delta.iter().all(|x| (-2..=2).contains(x)));
        let mut g = Graft::new(b, 1);
        g.parents[0] = Some(delta);
        g.leaves[0] = Some([0; 3]);
        let raw = g.gguf();
        let mut f = gguf_model::read(&raw).unwrap();
        let patches = f
            .tensors
            .iter_mut()
            .find(|(n, _)| n == "leaves.patch")
            .unwrap();
        patches.1[4] = 20;
        assert!(Graft::from_gguf(&gguf_model::write(&f)).is_err());
    }
}
