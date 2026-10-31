//! The virtual QNN of Zhao, Zhao, Li, Li & Chiribella, with balanced-trit coefficients:
//! score_c(x) = sum_b c_b * (P_b(0) - P_b(1)), c in {-1, 0, +1}^B. Every branch here has
//! the same scale 3^k, so the score is an exact integer numerator. Overhead = ||c||_1.

pub fn weights(b: usize) -> Vec<Vec<i64>> {
    let mut out = vec![vec![]];
    for _ in 0..b {
        out = out
            .into_iter()
            .flat_map(|w| {
                (-1..=1).map(move |c| {
                    let mut x = w.clone();
                    x.push(c);
                    x
                })
            })
            .collect();
    }
    out.into_iter()
        .filter(|w| w.iter().any(|&c| c != 0))
        .collect()
}

pub fn score(c: &[i64], branch_margins: &[Vec<i128>], i: usize) -> i128 {
    c.iter()
        .zip(branch_margins.iter())
        .map(|(&cb, m)| i128::from(cb) * m[i])
        .sum()
}

pub fn correct(c: &[i64], branch_margins: &[Vec<i128>], labels: &[u8]) -> usize {
    (0..labels.len())
        .filter(|&i| u8::from(score(c, branch_margins, i) > 0) == labels[i])
        .count()
}

/// The coefficient vector with the most correct training points; ties go to the smaller
/// overhead, then to the first in enumeration order.
pub fn choose(branch_margins: &[Vec<i128>], labels: &[u8]) -> (Vec<i64>, usize) {
    let mut best: Option<(usize, i64, Vec<i64>)> = None;
    for c in weights(branch_margins.len()) {
        let n = correct(&c, branch_margins, labels);
        let o: i64 = c.iter().map(|x| x.abs()).sum();
        let better = match &best {
            None => true,
            Some((bn, bo, _)) => n > *bn || (n == *bn && o < *bo),
        };
        if better {
            best = Some((n, o, c));
        }
    }
    let (n, _, c) = best.expect("weights");
    (c, n)
}
