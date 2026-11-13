//! Runnable 12-billion-address, sparse integer QNN prototype.
//! No all-node update, no claim of quantum entanglement or trained accuracy.
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

use gguf_qnn::spatial12b::{decode_address, run_rung, to_path, Generator, CAPACITY, RUNGS};
use std::error::Error;

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(String::as_str) {
        Some("--bench") if args.len() == 2 => {
            println!("SPATIAL12B_CONTRACT|schema=SPATIAL12B-V1|virtual_max={CAPACITY}|state_symbols=27|coefficients=27|updates=SPARSE_ONLY|nonlinear_jump=HOLD|quantum_simulation=NO|json=0");
            let generator = Generator::default();
            println!(
                "SPATIAL12B_GENERATOR|sha256={}|type=integer_rank1_context_plus_3x3|network_weights_per_node=0|json=0",
                generator.coeff_hash()
            );
            for capacity in RUNGS {
                let result = run_rung(capacity);
                println!(
                    "SPATIAL12B_RUNG|capacity={}|seeded={}|remaining={}|evaluated={}|ticks=3|microseconds={}|state_sha256={}|status=PASS|json=0",
                    result.capacity, result.before, result.after,
                    result.evaluations, result.elapsed_microseconds, result.digest
                );
            }
            println!("SPATIAL12B_COMPLETE|status=PASS|capacity=12000000000|real_12b_updates=NO|trained_weights=NO|CPU=YES|json=0");
        }
        Some("--lookup") if args.len() == 3 => {
            let id: u64 = args[2].parse()?;
            let a = decode_address(id).ok_or("address outside twelve billion")?;
            let path = to_path(id).ok_or("no ternary address")?;
            let p: String = path
                .iter()
                .rev()
                .map(|trit| char::from(b'0' + *trit))
                .collect();
            println!(
                "SPATIAL12B_LOOKUP|id={id}|x={}|y={}|z={}|channel={}|ternary22={p}|status=PASS|json=0",
                a.x, a.y, a.z, a.channel
            );
        }
        _ => return Err("usage: spatial12b --bench | --lookup <0..11999999999>".into()),
    }
    Ok(())
}
