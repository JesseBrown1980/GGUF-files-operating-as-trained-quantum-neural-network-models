//! Source-pinned V7 GGUF signed crossing experiment. Original models unchanged.
#![forbid(unsafe_code)]
#![allow(clippy::needless_range_loop)]
use gguf_qnn::{bigint::Big, gguf_model, sha256::hex_digest, v4::StateR, v7::NetQ};
use std::path::Path;

fn sign(p: usize, q: usize) -> i128 {
    let a = [(p >> 2) & 1, (p >> 1) & 1, p & 1];
    let b = [(q >> 2) & 1, (q >> 1) & 1, q & 1];
    let mut e = b[0] * a[1] * a[2] + a[0] * b[1] * a[2] + a[0] * a[1] * b[2];
    for i in 0..3 {
        for j in i..3 { e += a[i] * b[j]; }
    }
    if e % 2 == 0 { 1 } else { -1 }
}
fn zero8() -> [Big; 8] { std::array::from_fn(|_| Big::zero()) }

#[test]
fn signed_crossing_on_original_v7_gguf() {
    for x in 0..8 { for y in 0..8 { for u in 0..8 { for v in 0..8 {
        let n = if x ^ y ^ u ^ v == 0 {
            sign(x,y)*sign(v,u) + sign(x,u)*sign(v,y)
        } else { 0 };
        assert_eq!(n, if x == v && y == u {2} else {0});
    }}}}
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("results-v7");
    let manifest = std::fs::read_to_string(root.join("SHA256SUMS")).expect("manifest");
    let mut models = 0;
    let mut slices = 0;
    let mut dropped = 0;
    let mut cancellations = 0;
    let mut ninth = 0;
    for line in manifest.lines() {
        let mut fields = line.split_whitespace();
        let hash = fields.next().expect("hash");
        let name = fields.next().expect("filename");
        if !name.ends_with(".gguf") { continue; }
        let bytes = std::fs::read(root.join(name)).expect("original GGUF");
        assert_eq!(hex_digest(&bytes), hash);
        let m = gguf_model::read(&bytes).expect("GGUF parse");
        let params: Vec<i64> = m.tensor("branch_0.params").expect("params")
            .iter().map(|&x| i64::from(x)).collect();
        assert_eq!(params.len(), 256);
        assert!(params.iter().all(|&x| (-1..=1).contains(&x)));
        let net = NetQ { params };
        let mut state = StateR::zero_state(8);
        net.forward(&mut state);
        let scale = state.scale();
        assert!(state.norm_sq() == scale.mul(&scale));
        let mut observable = Big::zero();
        for e in 0..81 {
            let a = |x: usize, y: usize| &state.v[81*e+9*y+x];
            let mut direct = Big::zero();
            let mut edge = Big::zero();
            let mut l = zero8();
            let mut r = zero8();
            for x in 0..9 {
                for y in 0..9 {
                    let w = a(x,y).mul(a(y,x));
                    direct = direct.add(&w);
                    if x == 8 || y == 8 {
                        edge = edge.add(&w);
                        if w != Big::zero() { ninth += 1; }
                    } else {
                        l[x^y] = l[x^y].add(&a(x,y).mul_i128(sign(x,y)));
                        r[x^y] = r[x^y].add(&a(x,y).mul_i128(sign(y,x)));
                    }
                }
            }
            let low = (0..8).fold(Big::zero(), |s,k| s.add(&l[k].mul(&r[k])));
            let mut raw_r = Big::zero();
            let mut raw_c = Big::zero();
            let mut high_c = Big::zero();
            let mut high_r = Big::zero();
            for x in 0..8 { for y in 0..8 { for u in 0..8 {
                let v = x ^ y ^ u;
                let sr = sign(x,y)*sign(v,u);
                let sc = sign(x,u)*sign(v,y);
                let w = a(x,y).mul(a(u,v));
                let w2 = a(x,u).mul(a(y,v));
                raw_r = raw_r.add(&w.mul_i128(sr));
                raw_c = raw_c.add(&w2.mul_i128(sc));
                high_c = high_c.add(&w.mul_i128(sc));
                high_r = high_r.add(&w2.mul_i128(sr));
                if sr == -sc && w != Big::zero() { cancellations += 1; }
            }}}
            assert!(low == raw_r && low == raw_c);
            let correction = edge.mul_i128(2);
            let target = direct.mul_i128(2);
            assert!(low.add(&high_c).add(&correction) == target);
            assert!(low.add(&high_r).add(&correction) == target);
            if low.add(&correction) != target { dropped += 1; }
            observable = observable.add(&direct);
            slices += 1;
        }
        println!("QNN_SIGNED|model={name}|sha256={hash}|observable_sha256={}|json=0",
                 hex_digest(observable.dec().as_bytes()));
        models += 1;
    }
    assert_eq!((models,slices,dropped,cancellations,ninth),(9,729,729,326592,12393));
    println!("QNN_SIGNED_TOTAL|models={models}|slices={slices}|drop_rejected={dropped}|cancellations={cancellations}|ninth_nonzero={ninth}|json=0");
}
