# Writes the lite copy of the engine at ce44be7 and one bin per mutant into attack/. Nothing else is touched.
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-engine-20261105/tools")
from mutants_def import M, TOP

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
src = open(W + "/clean/src/bin/polariton_three_mode.rs", encoding="utf8", newline="").read().replace("\r\n", "\n")


def rep(s, a, b, count=1):
    assert s.count(a) == count, (a, s.count(a))
    return s.replace(a, b)


lite = src
lite = rep(lite, "const WORKERS: usize = 5;", "const WORKERS: usize = 3;")
lite = rep(lite, "for power in 1..=16u32 {", "for power in 1..=13u32 {")
lite = rep(lite, "    let n23 = 23_887_872u64;\n    jobs.push((n23, q(1, 2), q(1, 2), true));\n    jobs.push((n23, q(1, 2), q(0, 1), false));\n    jobs.push((n23, q(1, 2), q(3, 2), false));\n", "")
lite = rep(lite, "    for &delta in &[q(-1, 2), q(0, 1), q(1, 2), q(1, 1), q(2, 1)] {\n        jobs.push((19_683, delta));\n    }\n", "")
lite = rep(lite, "for &n in &[81u64, 243, 729, 2187, 6561] {", "for &n in &[81u64, 243, 729, 6561] {")
lite = rep(lite, "for &n in &[243u64, 729] {", "for &n in &[81u64] {", 2)
lite = rep(lite, """    // The top rung, with fewer workers for memory.
    let top: Vec<(Q, Q)> = points.to_vec();
    let rows = parallel(top.len(), 3, |i| pin_chain(729, top[i].0, top[i].1, 240));
    for chain in &rows {
        for row in chain {
            println!("{row}");
        }
    }
""", "")
lite = rep(lite, "let mut cases: Vec<(u64, bool, Q)> = vec![(243, true, q(1, 1024))];", "let mut cases: Vec<(u64, bool, Q)> = vec![(27, true, q(1, 1024))];")
lite = rep(lite, "for &n in &[81u64, 243, 729, 2187] {\n        cases.push", "for &n in &[81u64, 243, 729] {\n        cases.push")
lite = rep(lite, "let grid: Vec<Q> = (-40..=16).map(|i| q(i, 16)).collect();", "let grid: Vec<Q> = (-24..=8).map(|i| q(i, 16)).collect();")
# Window: no N = 729 rung.
lite = rep(lite, """    let top = [
        (q(1, 4), q(-1, 4)),
        (q(3, 4), q(0, 1)),
        (q(1, 1), q(-1, 4)),
        (q(1, 2), q(-1, 4)),
    ];
    let rows = parallel(top.len(), 3, |i| {
        pin_chain_with(729, top[i].0, top[i].1, 240, window_row)
    });
    for chain in &rows {
        for row in chain {
            println!("{row}");
        }
    }
""", "")
# Conversion: N = 81 whole; N = 243 at s = 1/4, 1, 4 and t = 1, 2, which holds the rows the frozen gates read there; no N = 729, 2187.
lite = rep(lite, """    for &(n, root) in &[(81u64, 9i128), (243, 16), (729, 27)] {
        for &delta in &[q(0, 1), q(1, 2)] {
            for &(sn, sd) in &fields {
                let s = q(sn, sd);
                jobs.push((n, delta, q(sn, sd * root), s, vec![1, 2, 3]));
            }
        }
    }
    for &(sn, sd) in &[(1i128, 2i128), (1, 1)] {
        jobs.push((2187, q(0, 1), q(sn, sd * 47), q(sn, sd), vec![1, 2]));
    }
""", """    for &(n, root) in &[(81u64, 9i128), (243, 16)] {
        for &delta in &[q(0, 1), q(1, 2)] {
            for &(sn, sd) in &fields {
                if n == 243 && ((sn, sd) == (1, 2) || (sn, sd) == (2, 1)) {
                    continue;
                }
                let s = q(sn, sd);
                let times = if n == 243 { vec![1, 2] } else { vec![1, 2, 3] };
                jobs.push((n, delta, q(sn, sd * root), s, times));
            }
        }
    }
""")

os.makedirs(W + "/attack/src/bin", exist_ok=True)
open(W + "/attack/Cargo.toml", "w", encoding="utf8", newline="\n").write('[package]\nname = "attack"\nversion = "0.1.0"\nedition = "2021"\n[dependencies]\n[profile.release]\nopt-level = 3\noverflow-checks = true\n')


def hdr(s):
    return rep(s, "#![forbid(unsafe_code)]\n#![deny(clippy::float_arithmetic)]\n", "#![allow(dead_code,unused)]\n")


def write(name, text):
    open(W + "/attack/src/bin/%s.rs" % name, "w", encoding="utf8", newline="\n").write(hdr(text))


write("m_base", lite)
names = ["m_base"]
for mid, grp, subs in M:
    s = lite
    for a, b in subs:
        s = rep(s, a, b)
    name = "m_" + mid.lower().replace("^", "")
    write(name, s)
    names.append(name)
# The top mutants on the whole sector stage: the source unchanged but for the mutation.
full = rep(src, "const WORKERS: usize = 5;", "const WORKERS: usize = 4;")
write("x_base", full)
for mid, subs in TOP:
    s = full
    for a, b in subs:
        s = rep(s, a, b)
    name = "x_" + mid.lower().replace("^", "")
    write(name, s)
    names.append(name)
print("BINS|count=%d|json=0" % len(names))
