# Builds a one-row tight read from the engine at this head, unchanged except for the tolerance and main. Own folder only.
W = 'C:/tmp/opus55/polariton-recheck-text-20261105/tight/'
src = open(W + 'engine_head.rs', encoding='utf-8', newline='').read()
hdr = '#![forbid(unsafe_code)]\n#![deny(clippy::float_arithmetic)]\n'
assert src.count(hdr) == 1
src = src.replace(hdr, '#![allow(dead_code, unused)]\n')
marker = 'fn main() -> Result<(), String> {'
assert src.count(marker) == 1
src = src.replace(marker, 'fn engine_main() -> Result<(), String> {')
main = '''
fn main() {
    // tight N u_n u_d x_n x_d krylov tolbits
    let a: Vec<String> = std::env::args().collect();
    let n: u64 = a[1].parse().unwrap();
    let u = q(a[2].parse().unwrap(), a[3].parse().unwrap());
    let x = q(a[4].parse().unwrap(), a[5].parse().unwrap());
    let kr: usize = a[6].parse().unwrap();
    let tolbits: u32 = a[7].parse().unwrap();
    let space = Space::full(n);
    let big = i128::from(n);
    let y = Q { n: 0, d: big };
    let par = Params { x, u, y, no_bose: false };
    let bits = spectral_bits(big, par);
    let op = build(&space, par, bits);
    let tol = (1i128 << tolbits) >> bits;
    let g = lanczos(&op, even_start(&space), kr, tol, 1500);
    println!("{}", pin_row(&space, par, &g, bits, &y.text(), "0"));
}
'''
open(W + 'src/main.rs', 'w', encoding='utf-8', newline='\n').write(src + main)
open(W + 'Cargo.toml', 'w', encoding='utf-8', newline='\n').write('[package]\nname = "tight"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\n\n[profile.release]\nopt-level = 3\noverflow-checks = true\n\n[workspace]\n')
print('ok')
