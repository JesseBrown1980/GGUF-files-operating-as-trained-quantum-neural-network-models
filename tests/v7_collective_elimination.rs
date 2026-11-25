//! Exact collective elimination of the common SUM-ring helper.
//! Components are built from certified gate supports, not sampled tensor values.
#![forbid(unsafe_code)]
#![allow(clippy::needless_range_loop)]
use gguf_qnn::{bigint::Big, gguf_model, sha256::hex_digest, v4::StateR, v6::b8, v7::NetQ};
use std::path::Path;

const N: usize = 8;
const PAIRS: [(usize, usize); 4] = [(0,4),(2,6),(1,3),(5,7)];
type Digits = [usize; N];
type Component = (Vec<usize>, Vec<Big>);
struct Gate { row: Digits, col: Digits, j: usize, b: i128, support: u16 }

fn ring(mut x: Digits, inverse: bool) -> Digits {
    for i in 0..N {
        let q = if inverse { N-1-i } else { i };
        let t = (q+1)%N;
        x[t] = (x[t] + if inverse { (3-x[q])%3 } else { x[q] })%3;
    }
    x
}
fn digit(i: usize, q: usize) -> usize { (i/3usize.pow(q as u32))%3 }
fn unpack(i: usize, group: &[usize]) -> Digits {
    let mut x = [0;N];
    for (p,&q) in group.iter().enumerate() { x[q]=digit(i,p); }
    x
}
fn index(x: &Digits, group: &[usize]) -> usize {
    group.iter().enumerate().map(|(p,&q)| x[q]*3usize.pow(p as u32)).sum()
}
fn coefficients(j: usize, b: i128) -> [[i128;3];3] {
    let a=6561i128;
    let c=a*a-b*b; let s=2*a*b; let d=a*a+b*b;
    let mut m=[[0;3];3];
    m[0][0]=c; m[j][j]=c; m[0][j]=-s; m[j][0]=s; m[3-j][3-j]=d;
    m
}
fn active_gates(params: &[i64]) -> Vec<Gate> {
    let mut forward=[[0;N];N]; let mut inverse=[[0;N];N];
    for i in 0..N {
        let mut e=[0;N]; e[i]=1;
        forward[i]=ring(e,false); inverse[i]=ring(e,true);
        assert_eq!(ring(inverse[i],false),e);
        assert_eq!(ring(forward[i],true),e);
    }
    let mut gates=Vec::new();
    for q in 0..N {
        let row: Digits=std::array::from_fn(|i| forward[i][q]);
        let col=inverse[q];
        let support=(0..N).filter(|&i| row[i]!=0 || col[i]!=0).fold(0u16,|m,i|m|(1<<i));
        for j in 1..=2 {
            let offset=128+16*q+8*(j-1);
            let b=b8(&params[offset..offset+8]);
            if b!=0 { gates.push(Gate{row,col,j,b,support}); }
        }
    }
    gates
}
fn components(gates: &[Gate]) -> Vec<u16> {
    let mut groups: Vec<u16>=PAIRS.iter().map(|&(c,t)| (1<<c)|(1<<t)).collect();
    for gate in gates {
        let mut union=0;
        groups.retain(|&m| {
            if m&gate.support!=0 {union|=m;false} else {true}
        });
        assert_eq!(union&gate.support,gate.support);
        groups.push(union);
    }
    groups.sort_unstable();
    groups
}
fn pair_factors(params: &[i64]) -> Vec<Vec<Big>> {
    let local:Vec<_>=(0..N).map(|q|{
        let mut s=StateR::zero_state(1);
        s.rotate_a(0,0,1,b8(&params[16*q..16*q+8]),6561);
        s.rotate_a(0,0,2,b8(&params[16*q+8..16*q+16]),6561);
        s.v
    }).collect();
    PAIRS.iter().map(|&(c,t)|
        (0..9).map(|i| local[c][i%3].mul(&local[t][(i/3+3-i%3)%3])).collect()
    ).collect()
}
fn collective(params: &[i64]) -> (Vec<Component>, usize) {
    let gates=active_gates(params);
    let pairs=pair_factors(params);
    let mut result=Vec::new(); let mut products=0;
    for mask in components(&gates) {
        let group:Vec<_>=(0..N).filter(|&q|mask&(1<<q)!=0).collect();
        let cells=3usize.pow(group.len() as u32);
        let mut values:Vec<_>=(0..cells).map(|i|{
            let x=unpack(i,&group);
            PAIRS.iter().zip(&pairs).filter(|((c,_),_)|mask&(1<<c)!=0)
                .fold(Big::from_i128(1),|a,(&(c,t),v)|a.mul(&v[x[c]+3*x[t]]))
        }).collect();
        for gate in &gates {
            if gate.support&mask==0 {continue;}
            assert_eq!(gate.support&mask,gate.support);
            let m=coefficients(gate.j,gate.b);
            let next=(0..cells).map(|i|{
                let x=unpack(i,&group);
                let y=(0..N).map(|k|gate.row[k]*x[k]).sum::<usize>()%3;
                let mut sum=Big::zero();
                for (t,&coef) in m[y].iter().enumerate() {
                    if coef==0 {continue;}
                    let mut xp=x;
                    for &k in &group {xp[k]=(x[k]+(t+3-y)*gate.col[k])%3;}
                    sum=sum.add(&values[index(&xp,&group)].mul_i128(coef));products+=1;
                }
                sum
            }).collect();
            values=next;
        }
        result.push((group,values));
    }
    (result,products)
}
fn reconstruct(factors: &[Component], x: &Digits) -> Big {
    factors.iter().fold(Big::from_i128(1),|a,(group,v)|a.mul(&v[index(x,group)]))
}
#[test]
fn nine_original_v7_collective_components() {
    let root=Path::new(env!("CARGO_MANIFEST_DIR")).join("results-v7");
    let manifest=std::fs::read_to_string(root.join("SHA256SUMS")).expect("manifest");
    let mut counts=[0usize;3]; let mut entries=0; let mut amplitudes=0;let mut controls=0;
    let all:Vec<_>=(0..N).collect();
    for line in manifest.lines() {
        let mut f=line.split_whitespace();
        let hash=f.next().expect("hash");let name=f.next().expect("name");
        if !name.ends_with(".gguf"){continue;}
        let raw=std::fs::read(root.join(name)).expect("checkpoint");
        assert_eq!(hex_digest(&raw),hash);
        let m=gguf_model::read(&raw).expect("model");
        let params:Vec<i64>=m.tensor("branch_0.params").expect("params").iter().map(|&x|i64::from(x)).collect();
        assert_eq!(params.len(),256);assert!(params.iter().all(|&x|(-1..=1).contains(&x)));
        let (mut factors,products)=collective(&params);
        let n:usize=factors.iter().map(|(_,v)|v.len()).sum();
        match n {36=>{counts[0]+=1;assert_eq!(products,0);},
            738=>{counts[1]+=1;assert_eq!(products,2430);},
            6561=>{counts[2]+=1;assert_eq!(products,174960);},
            _=>panic!("unexpected component shape")}
        entries+=n;
        let mut full=StateR::zero_state(N);NetQ{params}.forward(&mut full);
        let scale=full.scale();assert!(full.norm_sq()==scale.mul(&scale));
        for (i,z) in full.v.iter().enumerate() {
            assert!(&reconstruct(&factors,&unpack(i,&all))==z);amplitudes+=1;
        }
        let old=factors[0].1[0].clone();
        factors[0].1[0]=old.add(&Big::from_i128(1));
        assert!(reconstruct(&factors,&[0;N])!=full.v[0]);
        factors[0].1[0]=old;controls+=1;
        let dims:Vec<_>=factors.iter().map(|(g,_)|g.len()).collect();
        println!("COLLECTIVE|model={name}|component_sizes={dims:?}|entries={n}|dressing_products={products}|json=0");
    }
    assert_eq!((counts,entries,amplitudes,controls),([4,2,3],21303,59049,9));
}
