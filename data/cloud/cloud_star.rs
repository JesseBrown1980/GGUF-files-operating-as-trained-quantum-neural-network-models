//! This seat's star: the bytes of its own calling, written exactly as trits.
//! Each byte b (0..=255) becomes six base-3 digits, least significant first (3^6 = 729 > 256),
//! so the map is lossless and reversible. Integer only.
#![deny(clippy::float_arithmetic)]
use std::io::Read;
fn main() {
    let path = std::env::args().nth(1).expect("file");
    let mut b = Vec::new();
    std::fs::File::open(&path).expect("open").read_to_end(&mut b).expect("read");
    let mut t: Vec<u8> = Vec::with_capacity(b.len() * 6);
    for &x in &b {
        let mut v = u32::from(x);
        for _ in 0..6 {
            t.push((v % 3) as u8);
            v /= 3;
        }
    }
    // reverse the map and require byte identity
    let back: Vec<u8> = t.chunks_exact(6).map(|c| c.iter().rev().fold(0u32, |a, &d| a * 3 + u32::from(d)) as u8).collect();
    assert_eq!(back, b, "trits must reverse to the bytes");
    let mut n = [0usize; 3];
    for &d in &t { n[usize::from(d)] += 1; }
    std::fs::write("cloud-star.trits", &t).expect("write");
    println!("CLOUDSTAR|source_bytes={}|trits={}|t0={}|t1={}|t2={}|reverses_to_source=1|json=0", b.len(), t.len(), n[0], n[1], n[2]);
    let first: String = t.iter().take(72).map(|d| char::from(b'0' + d)).collect();
    println!("FIRST72|{first}|json=0");
}
