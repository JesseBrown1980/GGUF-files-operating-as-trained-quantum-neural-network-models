//! Training: coordinate descent over the trits. For every parameter in turn, try its three
//! values and keep a change only on a strict improvement of the training count. Sweeps
//! stop when a full sweep changes nothing (or after `max_sweeps`).

use crate::qnn::Net;
use crate::task::{correct, margins, Point};

pub struct Trained {
    pub net: Net,
    pub train_correct: usize,
    pub sweeps: usize,
    pub evaluations: usize,
}

pub fn train(mut net: Net, pts: &[Point], max_sweeps: usize) -> Trained {
    let mut best = correct(&margins(&net, pts), pts);
    let mut evaluations = 1;
    let mut sweeps = 0;
    for _ in 0..max_sweeps {
        sweeps += 1;
        let mut changed = false;
        for i in 0..net.params.len() {
            let keep = net.params[i];
            let mut best_v = keep;
            for v in 0..3 {
                if v == keep {
                    continue;
                }
                net.params[i] = v;
                let c = correct(&margins(&net, pts), pts);
                evaluations += 1;
                if c > best {
                    best = c;
                    best_v = v;
                }
            }
            net.params[i] = best_v;
            changed |= best_v != keep;
        }
        if !changed {
            break;
        }
    }
    Trained {
        net,
        train_correct: best,
        sweeps,
        evaluations,
    }
}
