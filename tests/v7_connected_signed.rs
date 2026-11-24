//! Two connected signed crossings on the original V7 GGUF amplitudes.
#![forbid(unsafe_code)]
#![allow(clippy::needless_range_loop)]
use gguf_qnn::{bigint::Big, gguf_model, sha256::hex_digest, v4::StateR, v7::NetQ};
use std::{collections::BTreeMap, path::Path};
type Mask = u16;
type Dims = [usize; 10];
type Plan = (usize, usize, Vec<usize>);
const WIRES: [[usize; 4]; 3] = [[0,1,2,3],[0,2,1,3],[0,1,3,2]];
const CHOICES: [u8;4] = *b"RCEF";
fn sign(p: usize, q: usize) -> i128 {
    let a = [(p >> 2) & 1, (p >> 1) & 1, p & 1];
    let b = [(q >> 2) & 1, (q >> 1) & 1, q & 1];
    let mut e = b[0]*a[1]*a[2]+a[0]*b[1]*a[2]+a[0]*a[1]*b[2];
    for i in 0..3 { for j in i..3 {e += a[i]*b[j];} }
    if e%2==0 {1} else {-1}
}
fn vars(m: Mask) -> impl Iterator<Item=usize> { (0..10).filter(move |&i| m & (1<<i) != 0) }
fn size(m:Mask,d:&Dims)->usize { vars(m).map(|i|d[i]).product() }
fn decode(mut ix:usize,m:Mask,d:&Dims)->Dims {
    let mut a=[0;10];
    for i in vars(m) {a[i]=ix%d[i];ix/=d[i];}
    a
}
fn index(m:Mask,d:&Dims,a:&Dims)->usize {
    let mut ix=0;let mut stride=1;
    for i in vars(m) {ix+=a[i]*stride;stride*=d[i];}
    ix
}
fn step(sc:&[Mask],v:usize,d:&Dims)->(Vec<Mask>,usize,usize) {
    let bit=1<<v;let mut union=0;let mut n=0;let mut rest=Vec::new();
    for &s in sc {if s&bit!=0 {union|=s;n+=1;} else {rest.push(s);}}
    let cells=size(union,d);
    rest.push(union&!bit);rest.sort_unstable();
    (rest,(n-1)*cells+cells-cells/d[v],cells)
}
fn plan(sc:Vec<Mask>,d:&Dims,memo:&mut BTreeMap<Vec<Mask>,Plan>)->Plan {
    if let Some(p)=memo.get(&sc) {return p.clone();}
    let all=sc.iter().fold(0,|a,b|a|b);
    let mut best=(usize::MAX,usize::MAX,Vec::new());
    if all==0 {best=(sc.len().saturating_sub(1),1,Vec::new());}
    for v in vars(all) {
        let (rest,c,peak)=step(&sc,v,d);
        let (tail,p,order)=plan(rest,d,memo);
        let mut seq=vec![v];seq.extend(order);
        best=best.min((c+tail,peak.max(p),seq));
    }
    memo.insert(sc,best.clone());best
}
fn fixed(mut sc:Vec<Mask>,d:&Dims,reverse:bool)->usize {
    let mut cost=0;
    loop {
        let all=sc.iter().fold(0,|a,b|a|b);
        if all==0 {return cost+sc.len().saturating_sub(1);}
        let v=if reverse {vars(all).last()} else {vars(all).next()}.expect("variable");
        let (rest,c,_)=step(&sc,v,d);sc=rest;cost+=c;
    }
}
struct Factor { mask:Mask, values:Vec<Big> }
fn factor(m:Mask,d:&Dims,f:impl Fn(&Dims)->Big)->Factor {
    Factor{mask:m,values:(0..size(m,d)).map(|ix|f(&decode(ix,m,d))).collect()}
}
fn contract(mut factors:Vec<Factor>,d:&Dims,order:&[usize])->Big {
    for &v in order {
        let bit=1<<v;let (bucket,mut rest):(Vec<_>,Vec<_>)=factors.into_iter().partition(|f|f.mask&bit!=0);
        let union=bucket.iter().fold(0,|a,f|a|f.mask);
        let reduced=union&!bit;
        let mut out=vec![Big::zero();size(reduced,d)];
        for ix in 0..size(union,d) {
            let a=decode(ix,union,d);
            let mut it=bucket.iter();
            let first=it.next().expect("bucket");
            let mut val=first.values[index(first.mask,d,&a)].clone();
            for f in it {val=val.mul(&f.values[index(f.mask,d,&a)]);}
            let j=index(reduced,d,&a);out[j]=out[j].add(&val);
        }
        rest.push(Factor{mask:reduced,values:out});factors=rest;
    }
    let mut it=factors.into_iter();
    let first=it.next().expect("scalar");
    assert_eq!(first.mask,0);
    it.fold(first.values[0].clone(),|a,f|{assert_eq!(f.mask,0);a.mul(&f.values[0])})
}
fn route(state:&StateR,wire:[usize;4],kinds:[u8;2])->(Big,[usize;3],usize) {
    let mut d=[9;10];d[8]=1;d[9]=1;
    let mut map: Dims=std::array::from_fn(|i|i);
    let mut offset=[0;10];let mut scale=1;
    let mut signed=Vec::new();
    for (n,k) in kinds.into_iter().enumerate() {
        let x=4*n;let y=x+1;let u=x+2;let v=x+3;let z=8+n;
        if k==b'D'||k==b'E'||k==b'F' {
            map[v]=x;map[u]=y;d[v]=1;d[u]=1;
            if k==b'E' {d[x]=1;offset[x]=8;scale*=2;}
            if k==b'F' {d[x]=8;d[y]=1;offset[y]=8;scale*=2;}
        } else {
            for i in [x,y,u,v,z] {d[i]=8;}
            if k==b'R' {signed.extend([[x,y,z],[v,u,z]]);}
            else {assert_eq!(k,b'C');signed.extend([[x,u,z],[v,y,z]]);}
        }
    }
    let mask=|ps:&[usize]|ps.iter().fold(0,|m,&p|if d[map[p]]>1 {m|(1<<map[p])}else{m});
    let get=|a:&Dims,p:usize|a[map[p]]+offset[map[p]];
    let mut f=Vec::new();
    for (i,e) in [0,1,40,80].into_iter().enumerate() {
        let p=i;let q=4+wire[i];
        f.push(factor(mask(&[p,q]),&d,|a|state.v[e*81+9*get(a,q)+get(a,p)].clone()));
    }
    for [p,q,z] in signed {
        f.push(factor(mask(&[p,q,z]),&d,|a|{
            let (x,y,t)=(get(a,p),get(a,q),get(a,z));
            Big::from_i128(if x^y==t {sign(x,y)}else{0})
        }));
    }
    let mut sc:Vec<_>=f.iter().map(|x|x.mask).collect();sc.sort_unstable();
    let mut memo=BTreeMap::new();
    let (best,_,order)=plan(sc.clone(),&d,&mut memo);
    let correction=kinds.iter().filter(|&&k|k==b'E'||k==b'F').count();
    let costs=[best+correction,fixed(sc.clone(),&d,false)+correction,fixed(sc,&d,true)+correction];
    let value=contract(f,&d,&order);
    (if scale==1 {value}else{value.mul_i128(scale)},costs,memo.len())
}
fn brute(state:&StateR,wire:[usize;4])->Big {
    let mut total=Big::zero();
    for a in 0..9 {for b in 0..9 {for c in 0..9 {for d in 0..9 {
        let left=[a,b,b,a];let right=[c,d,d,c];
        let mut w=Big::from_i128(1);
        for (i,e) in [0,1,40,80].into_iter().enumerate() {
            w=w.mul(&state.v[e*81+9*right[wire[i]]+left[i]]);
        }
        total=total.add(&w);
    }}}}
    total
}
#[test]
fn original_v7_two_crossings() {
    let root=Path::new(env!("CARGO_MANIFEST_DIR")).join("results-v7");
    let manifest=std::fs::read_to_string(root.join("SHA256SUMS")).expect("manifest");
    let mut totals=[0;4];let mut comparisons=0;let mut dropped=0;
    for line in manifest.lines() {
        let mut f=line.split_whitespace();let hash=f.next().expect("hash");let name=f.next().expect("name");
        if !name.ends_with(".gguf"){continue;}
        let bytes=std::fs::read(root.join(name)).expect("checkpoint");assert_eq!(hex_digest(&bytes),hash);
        let m=gguf_model::read(&bytes).expect("GGUF");
        let params:Vec<i64>=m.tensor("branch_0.params").expect("params").iter().map(|&x|i64::from(x)).collect();
        assert_eq!(params.len(),256);
        assert!(params.iter().all(|&x|(-1..=1).contains(&x)));
        let mut state=StateR::zero_state(8);NetQ{params}.forward(&mut state);
        let scale=state.scale();assert!(state.norm_sq()==scale.mul(&scale));
        for wire in WIRES {
            let (direct,dc,dp)=route(&state,wire,*b"DD");assert!(direct==brute(&state,wire));
            let mut sum=Big::zero();let mut rr=Big::zero();let mut costs=[15;3];let mut planning=0;
            for k in CHOICES {for l in CHOICES {
                let (val,c,p)=route(&state,wire,[k,l]);
                if k==b'R'&&l==b'R'{rr=val.clone();}
                sum=sum.add(&val);for i in 0..3 {costs[i]+=c[i];}planning+=p;
            }}
            let target=direct.mul_i128(4);assert!(sum==target);
            if sum.sub(&rr)!=target {dropped+=1;}
            comparisons+=1;totals[0]+=dc[0];for i in 0..3 {totals[i+1]+=costs[i];}
            println!("CONNECTED|model={name}|wire={wire:?}|direct={}|guided={}|forward={}|reverse={}|direct_plan_states={dp}|signed_plan_states={planning}|observable_sha256={}|json=0",dc[0],costs[0],costs[1],costs[2],hex_digest(direct.dec().as_bytes()));
        }
    }
    assert_eq!((comparisons,dropped),(27,27));
    assert_eq!(totals,[32049,12899592,14361777,59912721]);
    println!("CONNECTED_TOTAL|comparisons={comparisons}|drop_rejected={dropped}|direct={}|guided={}|forward={}|reverse={}|json=0",totals[0],totals[1],totals[2],totals[3]);
}
