//! Radiated slice: exact product-of-pairs route for inactive V7 dressing layer.
#![forbid(unsafe_code)]
use gguf_qnn::{bigint::Big, gguf_model, sha256::hex_digest, v4::StateR, v6::b8, v7::NetQ};
use std::path::Path;
const PAIRS: [(usize,usize);4]=[(0,4),(2,6),(1,3),(5,7)];
fn digit(i:usize,q:usize)->usize { (i/3usize.pow(q as u32))%3 }
fn norm(v:&[Big])->Big {v.iter().fold(Big::zero(),|s,x|s.add(&x.mul(x)))}
fn dot(a:&[Big],b:&[Big])->Big {
    a.iter().zip(b).fold(Big::zero(),|s,(x,y)|s.add(&x.mul(y)))
}
#[test]
fn radiated_pair_factorization() {
    let root=Path::new(env!("CARGO_MANIFEST_DIR")).join("results-v7");
    let manifest=std::fs::read_to_string(root.join("SHA256SUMS")).expect("manifest");
    let (mut eligible,mut amplitudes,mut observables,mut controls,mut fallback)=(0,0,0,0,0);
    for line in manifest.lines() {
        let mut f=line.split_whitespace();
        let hash=f.next().expect("hash");let name=f.next().expect("name");
        if !name.ends_with(".gguf"){continue;}
        let raw=std::fs::read(root.join(name)).expect("checkpoint");assert_eq!(hex_digest(&raw),hash);
        let m=gguf_model::read(&raw).expect("model");
        let params:Vec<i64>=m.tensor("branch_0.params").expect("params").iter().map(|&x|i64::from(x)).collect();
        assert_eq!(params.len(),256);
        assert!(params.iter().all(|&x|(-1..=1).contains(&x)));
        if params[128..].iter().any(|&x|x!=0){fallback+=1;continue;}
        eligible+=1;
        let locals:Vec<_>=(0..8).map(|q|{
            let mut s=StateR::zero_state(1);
            s.rotate_a(0,0,1,b8(&params[16*q..16*q+8]),6561);
            s.rotate_a(0,0,2,b8(&params[16*q+8..16*q+16]),6561);
            s.v
        }).collect();
        let p:Vec<Vec<Big>>=PAIRS.iter().map(|&(c,t)|{
            (0..9).map(|i|locals[c][i%3].mul(&locals[t][(i/3+3-i%3)%3])).collect()
        }).collect();
        let norms:Vec<_>=p.iter().map(|v|norm(v)).collect();
        // Reference expansion is paid only by this acceptance audit.
        let mut full=StateR::zero_state(8);NetQ{params}.forward(&mut full);
        for (i,z) in full.v.iter().enumerate(){
            let got=PAIRS.iter().zip(&p).fold(Big::from_i128(1),|s,(&(c,t),v)|s.mul(&v[digit(i,c)+3*digit(i,t)]));
            assert!(&got==z);amplitudes+=1;
        }
        for i in 0..4 {for j in i+1..4 {
            let (c,t)=PAIRS[i];let (u,v)=PAIRS[j];
            let mut direct=Big::zero();
            for (ix,z) in full.v.iter().enumerate(){
                let mut swapped=ix;
                for (a,b) in [(c,u),(t,v)]{
                    swapped-=digit(ix,a)*3usize.pow(a as u32)+digit(ix,b)*3usize.pow(b as u32);
                    swapped+=digit(ix,b)*3usize.pow(a as u32)+digit(ix,a)*3usize.pow(b as u32);
                }
                direct=direct.add(&z.mul(&full.v[swapped]));
            }
            let d=dot(&p[i],&p[j]);
            let env=(0..4).filter(|&k|k!=i&&k!=j).fold(Big::from_i128(1),|s,k|s.mul(&norms[k]));
            assert!(d.mul(&d).mul(&env)==direct);
            let wrong=d.add(&Big::from_i128(1));
            assert!(wrong.mul(&wrong).mul(&env)!=direct);
            observables+=1;controls+=1;
            println!("RADIATED|model={name}|pairs={i},{j}|observable_sha256={}|json=0",hex_digest(direct.dec().as_bytes()));
        }}
    }
    assert_eq!((eligible,fallback,amplitudes,observables,controls),(4,5,26244,24,24));
    println!("RADIATED_TOTAL|eligible={eligible}|fallback={fallback}|amplitudes={amplitudes}|observables={observables}|controls={controls}|json=0");
}
