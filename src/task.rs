//! The classification task, exactly as sealed in PREREG.hbp.
//! Points (x, y), x, y in 0..=26; label 1 iff (x-13)^2 + (y-13)^2 <= 81.
//! Train: (7x + 11y) mod 3 != 0. Test: (7x + 11y) mod 3 == 0.
//! Encoding: x and y as three base-3 digits each on qutrits 0..=2 and 3..=5.

use crate::qnn::Net;
use crate::qutrit::State;

pub const QUTRITS: usize = 6;

#[derive(Clone, Copy, Debug)]
pub struct Point {
    pub x: usize,
    pub y: usize,
    pub label: u8,
}

pub fn points() -> (Vec<Point>, Vec<Point>) {
    let (mut train, mut test) = (Vec::new(), Vec::new());
    for x in 0..27usize {
        for y in 0..27usize {
            let (dx, dy) = (x as i64 - 13, y as i64 - 13);
            let p = Point {
                x,
                y,
                label: u8::from(dx * dx + dy * dy <= 81),
            };
            if (7 * x + 11 * y) % 3 != 0 {
                train.push(p);
            } else {
                test.push(p);
            }
        }
    }
    (train, test)
}

pub fn encode(p: &Point) -> State {
    let d = [
        p.x % 3,
        (p.x / 3) % 3,
        p.x / 9,
        p.y % 3,
        (p.y / 3) % 3,
        p.y / 9,
    ];
    State::basis(QUTRITS, &d)
}

/// Exact readout: numerators of P(qutrit 0 = 0, 1, 2) over 3^k, and k.
pub fn readout(net: &Net, p: &Point) -> ([i128; 3], u32) {
    let mut s = encode(p);
    net.forward(&mut s);
    (s.marginal(0), s.k)
}

/// The branch's margin P(0) - P(1), as a numerator over 3^k (k is the same for every input).
pub fn margin(net: &Net, p: &Point) -> i128 {
    let (m, _) = readout(net, p);
    m[0] - m[1]
}

pub fn margins(net: &Net, pts: &[Point]) -> Vec<i128> {
    pts.iter().map(|p| margin(net, p)).collect()
}

/// Correct count for a branch: class 1 iff P(0) > P(1).
pub fn correct(margins: &[i128], pts: &[Point]) -> usize {
    margins
        .iter()
        .zip(pts.iter())
        .filter(|(m, p)| u8::from(**m > 0) == p.label)
        .count()
}
