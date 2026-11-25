//! Exact rank certificates in forward SUM-ring coordinates.
#![forbid(unsafe_code)]
#![allow(clippy::needless_range_loop)]
use gguf_qnn::{bigint::Big, gguf_model, sha256::hex_digest, v4::StateR, v6::b8, v7::NetQ};
use std::{collections::BTreeSet, path::Path};

const N: usize = 8;
const PAIRS: [(usize,usize);4] = [(0,4),(2,6),(1,3),(5,7)];
const PRIME: i64 = 65521;
const CUTS: [([usize;4], &[usize], &[usize]);3] = [
    ([0,1,2,3], &[], &[0,1,3,4,6]),
    ([0,1,3,7], &[2,3,4,6], &[7]),
    ([0,5,6,7], &[1,3,4], &[5,6,7]),
];
type Digits = [usize;N];

fn digit(i:usize,q:usize)->usize { (i/3usize.pow(q as u32))%3 }
fn addr(x:&Digits)->usize { x.iter().enumerate().map(|(q,&z)| z*3usize.pow(q as u32)).sum() }
fn ring_inverse(mut x:Digits)->Digits {
    for q in (0..N).rev() { let t=(q+1)%N; x[t]=(x[t]+3-x[q])%3; }
    x
}
fn rows()->[Digits;N] {
    let mut out=[[0;N];N];
    for p in 0..N {
        let mut x=[0;N];x[p]=1;x=ring_inverse(x);
        for (c,t) in PAIRS { x[t]=(x[t]+3-x[c])%3; }
        for q in 0..N {out[q][p]=x[q];}
    }
    out
}
fn restrictions(l:&[Digits;N],side:&[usize])->Vec<Digits> {
    (0..81).map(|i|std::array::from_fn(|q|side.iter().enumerate()
        .map(|(p,&k)| l[q][k]*digit(i,p)).sum::<usize>()%3)).collect()
}
fn signature(z:&Digits,qs:&[usize])->Vec<usize> { qs.iter().map(|&q|z[q]).collect() }
fn rotate(s:&mut StateR,params:&[i64],side:&[usize],layer:usize) {
    for (p,&q) in side.iter().enumerate() {
        let off=128*layer+16*q;
        s.rotate_a(p,0,1,b8(&params[off..off+8]),6561);
        s.rotate_a(p,0,2,b8(&params[off+8..off+16]),6561);
    }
}
fn vector(local:&[Vec<Big>],rs:&[Digits],pure:&[usize],fixed:&[usize],sig:&[usize],own:&[usize],own_sig:&[usize])->Vec<Big> {
    rs.iter().map(|z|{
        if signature(z,own)!=own_sig {return Big::zero();}
        let a=pure.iter().fold(Big::from_i128(1),|v,&q|v.mul(&local[q][z[q]]));
        fixed.iter().zip(sig).fold(a,|v,(&q,&s)|v.mul(&local[q][(z[q]+s)%3]))
    }).collect()
}
fn residue(x:&Big)->i64 {
    let d=x.dec();let mut v=0;
    for c in d.bytes().filter(u8::is_ascii_digit) { v=(10*v+i64::from(c-b'0'))%PRIME; }
    if d.starts_with('-') {(PRIME-v)%PRIME} else {v}
}
fn powmod(mut x:i64,mut n:i64)->i64 {
    let mut v=1;
    while n>0 {if n%2==1 {v=v*x%PRIME;}x=x*x%PRIME;n/=2;}v
}
fn rank(mut m:Vec<Vec<i64>>)->usize {
    let mut r=0;
    for c in 0..m[0].len() {
        let Some(i)=(r..m.len()).find(|&i|m[i][c]!=0) else {continue;};
        m.swap(i,r);let inv=powmod(m[r][c],PRIME-2);
        for i in r+1..m.len() {
            let f=m[i][c]*inv%PRIME;
            for j in c..m[0].len() {m[i][j]=(m[i][j]-f*m[r][j]).rem_euclid(PRIME);}
        }
        r+=1;if r==m.len(){break;}
    }
    r
}
#[test]
fn exact_rank_27_in_three_ring_cuts() {
    assert!((2..=255).all(|p|PRIME%p!=0));
    let root=Path::new(env!("CARGO_MANIFEST_DIR")).join("results-v7");
    let manifest=std::fs::read_to_string(root.join("SHA256SUMS")).expect("manifest");
    let l=rows();let(mut count,mut controls,mut cuts)=(0,0,0);
    for line in manifest.lines() {
        let mut f=line.split_whitespace();let hash=f.next().expect("hash");let name=f.next().expect("name");
        if !name.ends_with("-star.gguf"){continue;}
        let raw=std::fs::read(root.join(name)).expect("checkpoint");assert_eq!(hex_digest(&raw),hash);
        let m=gguf_model::read(&raw).expect("model");
        let params:Vec<i64>=m.tensor("branch_0.params").expect("params").iter().map(|&x|i64::from(x)).collect();
        assert_eq!(params.len(),256);assert!(params.iter().all(|&x|(-1..=1).contains(&x)));
        let local:Vec<_>=(0..N).map(|q|{let mut s=StateR::zero_state(1);rotate(&mut s,&params,&[q],0);s.v}).collect();
        let mut full=StateR::zero_state(N);NetQ{params:params.clone()}.forward(&mut full);
        for (left,x,y) in CUTS {
            let right:Vec<_>=(0..N).filter(|q|!left.contains(q)).collect();
            let a=restrictions(&l,&left);let b=restrictions(&l,&right);
            let mut pl=Vec::new();let mut pr=Vec::new();let mut mixed=Vec::new();
            for q in 0..N {
                match (left.iter().any(|&p|l[q][p]!=0),right.iter().any(|&p|l[q][p]!=0)) {
                    (true,false)=>pl.push(q),(false,true)=>pr.push(q),(true,true)=>mixed.push(q),_=>panic!("zero row"),
                }
            }
            let mut xy=[x,y].concat();xy.sort_unstable();assert_eq!(mixed,xy);
            let alphas:BTreeSet<_>=a.iter().map(|z|signature(z,x)).collect();
            let betas:BTreeSet<_>=b.iter().map(|z|signature(z,y)).collect();
            assert_eq!(alphas.len()*betas.len(),27);
            let mut factors=Vec::new();
            for alpha in &alphas {for beta in &betas {
                let u=vector(&local,&a,&pl,y,beta,x,alpha);
                let v=vector(&local,&b,&pr,x,alpha,y,beta);
                let mut u=StateR{n:4,v:u,scales:Vec::new()};
                let mut v=StateR{n:4,v,scales:Vec::new()};
                rotate(&mut u,&params,&left,1);rotate(&mut v,&params,&right,1);
                factors.push((u.v,v.v));
            }}
            let mut modmat=vec![vec![0;81];81];
            let mut dropped=false;
            for i in 0..81 {for j in 0..81 {
                let mut z=[0;N];
                for (p,&q) in left.iter().enumerate(){z[q]=digit(i,p);}
                for (p,&q) in right.iter().enumerate(){z[q]=digit(j,p);}
                let got=factors.iter().fold(Big::zero(),|s,(u,v)|s.add(&u[i].mul(&v[j])));
                assert_eq!(got,full.v[addr(&ring_inverse(z))]);
                modmat[i][j]=residue(&got);count+=1;
                if !factors[0].0[i].mul(&factors[0].1[j]).is_zero(){dropped=true;}
            }}
            assert!(dropped);assert_eq!(rank(modmat),27);controls+=1;cuts+=1;
            println!("RING_RANK|model={name}|left={left:?}|alpha={}|beta={}|rank=27|entries=4374",alphas.len(),betas.len());
        }
    }
    assert_eq!((count,controls,cuts),(59049,9,9));
}
