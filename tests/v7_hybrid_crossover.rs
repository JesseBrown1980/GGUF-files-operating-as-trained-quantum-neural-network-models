//! Replay three structural crossover candidates and their stronger product-tree control.
//! Counts are exact modeled arithmetic, not executed large tensor contractions.
#![forbid(unsafe_code)]
use gguf_qnn::sha256::digest;

type Mask = u128;
fn size(m: Mask, d: &[u128]) -> u128 {
    d.iter().enumerate().filter(|(i, _)| m & (1 << i) != 0).map(|(_, x)| *x).product()
}
fn port(a: usize, b: u8) -> usize {
    4 * (a / 2) + if a % 2 == 0 { [0, 3][usize::from(b % 2)] } else { [1, 2][usize::from(b % 2)] }
}
fn fixture(k: usize, seed: usize, i: usize, kind: u8) -> (Vec<Mask>, Vec<u128>) {
    let mut map: Vec<usize> = (0..5*k).collect();
    let mut d = vec![9; 5*k];
    let mut signs = Vec::new();
    for j in 0..k {
        let x=4*j; let y=x+1; let u=x+2; let v=x+3; let z=4*k+j;
        let c=if i==j {kind} else {b'D'};
        if matches!(c,b'D'|b'E'|b'F') {
            map[v]=x; map[u]=y; d[z]=1;
            if c==b'E' {d[x]=1;}
            if c==b'F' {d[x]=8;d[y]=1;}
        } else {
            for p in [x,y,u,v,z] {d[p]=8;}
            if c==b'R' {signs.extend([[x,y,z],[v,u,z]]);}
            else {assert_eq!(c,b'C');signs.extend([[x,u,z],[v,y,z]]);}
        }
    }
    let mask=|p:&[usize]| p.iter().fold(0,|m,&p|if d[map[p]]>1 {m|(1<<map[p])} else {m});
    let mut factors=Vec::new();
    for a in 0..2*k {for b in a+1..2*k {
        let h=digest(format!("port/{seed}/{a}/{b}").as_bytes());
        factors.push(mask(&[port(a,h[0]),port(b,h[1])]));
    }}
    for a in 0..2*k {factors.push(mask(&[4*(a/2)+a%2]));}
    for p in signs {factors.push(mask(&p));}
    (factors,d)
}
fn replay(mut sc: Vec<Mask>,d:&[u128],order:&[usize],refined:bool)->u128 {
    let mut total=0;
    for &v in order {
        let bit=1<<v;
        let (mut b,mut rest):(Vec<_>,Vec<_>)=sc.into_iter().partition(|m|m&bit!=0);
        assert!(!b.is_empty());
        let u=b.iter().fold(0,|m,&p|m|p);
        let cells=size(u,d);
        if refined {
            while b.len()>1 {
                let mut best=(u128::MAX,0,0);
                for i in 0..b.len(){for j in i+1..b.len(){
                    best=best.min((size(b[i]|b[j],d),i,j));
                }}
                let (c,i,j)=best;
                let m=b[i]|b[j];b.remove(j);b.remove(i);b.push(m);total+=c;
            }
        } else {total+=(b.len() as u128-1)*cells;}
        total+=cells-size(u^bit,d);
        rest.push(u^bit);sc=rest;
    }
    assert!(sc.iter().all(|&m|m==0));
    total+sc.len() as u128-1
}
fn direct_formula(n: u32)->u128 {
    (u128::from(n)-1)*9u128.pow(n)+8*9u128.pow(n-1)
        +(1..n).map(|m|u128::from(m)*9u128.pow(m)+8*9u128.pow(m-1)).sum::<u128>()
}
#[test]
fn crossover_and_product_tree_control() {
    let cases = [
        (8,0,2,vec![34,8,10,9,11,0,1,4,5,12,13,16,17,20,21,24,25,28,29],
        vec![0,1,4,5,9,12,13,16,17,20,21,24,25,28,29],
        vec![0,1,4,5,12,13,16,17,20,21,24,25,28,29,8],
        [33093782435275847u128,31455975317196245,4169297072582423,7201230320827301]),
        (9,2,5,vec![41,22,20,23,21,0,1,4,5,8,9,12,13,16,17,24,25,28,29,32,33],
        vec![0,1,4,5,8,9,12,13,16,17,21,24,25,28,29,32,33],
        vec![0,1,4,5,8,9,12,13,16,17,24,25,28,29,32,33,20],
        [3018309306675591698,2952974840278011998,337712935715922842,583245315174785245]),
        (12,0,0,vec![48,1,0,3,2,4,5,8,9,12,13,16,17,20,21,24,25,28,29,32,33,36,37,40,41,44,45],
        vec![1,4,5,8,9,12,13,16,17,20,21,24,25,28,29,32,33,36,37,40,41,44,45],
        vec![4,5,8,9,12,13,16,17,20,21,24,25,28,29,32,33,36,37,40,41,44,45,0],
        [2142476807017872569611211,2089517522273703294058625,179474499007617206747195,309957037312525913845303]),
    ];
    for (k,seed,i,rc,e,f,want) in cases {
        let (sc,d)=fixture(k,seed,i,b'D');
        let direct:Vec<_>=(0..k).flat_map(|j|[4*j,4*j+1]).collect();
        let a=replay(sc.clone(),&d,&direct,false);
        assert_eq!(a,direct_formula((2*k) as u32));
        let c=replay(sc,&d,&direct,true);
        let mut b=4;let mut z=4; // three additions and final exact division
        for (kind,order) in [(b'R',&rc),(b'C',&rc),(b'E',&e),(b'F',&f)] {
            let (sc,d)=fixture(k,seed,i,kind);
            let weight=u128::from(matches!(kind,b'E'|b'F'));
            b+=replay(sc.clone(),&d,order,false)+weight;
            z+=replay(sc,&d,order,true)+weight;
        }
        assert_eq!([a,b,c,z],want);
        assert!(b<a && z>c);
        println!("CROSSOVER|k={k}|direct={a}|signed={b}|direct_tree={c}|signed_tree={z}|json=0");
    }
}
