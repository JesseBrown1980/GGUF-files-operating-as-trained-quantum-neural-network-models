//! Measured, fail-closed Google qsim source-circuit compatibility test.
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

use gguf_qnn::google_qsim::{compile_diagonal_prefix, parse_qsim, run_bell};
use gguf_qnn::sha256::hex_digest;
use std::time::Instant;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    const BELL: &str = include_str!("../../data/google-qsim/tutorial_bell.txt");
    const Q24: &str = include_str!("../../data/google-qsim/circuit_q24_t0_t2.txt");
    const PIN: &str = "87dd34b6026bedac1f989c2f4abd211ff1e3691646aaa2bf578e90df222d0356";
    if hex_digest(Q24.as_bytes()) != PIN {
        return Err("pinned Google qsim fixture mismatch".into());
    }

    let bell = parse_qsim(BELL)?;
    let (state, k) = run_bell(&bell)?;
    if state != [1, 0, 0, 1] || k != 1 {
        return Err("Google tutorial Bell circuit output mismatch".into());
    }
    println!("GOOGLE_QSIM_BELL|qubits=2|gates=2|prob_00=1/2|prob_01=0/2|prob_10=0/2|prob_11=1/2|exact=PASS|json=0");

    let start = Instant::now();
    let original = parse_qsim(Q24)?;
    let plan = compile_diagonal_prefix(&original)?;
    if plan.qubits != 24 || plan.gate_count != 48 || plan.cz_count() != 12 || plan.t_count() != 12 {
        return Err("Google 24-qubit published prefix gate list mismatch".into());
    }
    let hist = plan.histogram()?;
    let expected = [
        2_031_616, 2_099_712, 2_168_576, 2_094_592, 2_031_616, 2_094_592, 2_156_800,
        2_099_712,
    ];
    if hist != expected || hist.iter().sum::<u64>() != 16_777_216 {
        return Err("complete Google 24-qubit prefix amplitude-phase histogram mismatch".into());
    }
    let ns = start.elapsed().as_nanos();
    println!("GOOGLE_QSIM_24|source=quantumlib/qsim/circuits/circuit_q24|source_git_blob=0c96e260ac6a9b765a703f4ca971924f674b76f3|fixture_sha256={PIN}|max_time=2|qubits=24|gates=48|h=24|cz=12|t=12|outputs=16777216|prob_each=1/16777216|compute_ns={ns}|result=PASS|json=0");
    for (p, count) in hist.iter().enumerate() {
        println!("GOOGLE_QSIM_PHASE|phase_mod8={p}|count={count}|denom_sqrt2_power=24|result=PASS|json=0");
    }
    if parse_qsim("103\n0 h 0\n").is_ok()
        || parse_qsim("2\n0 fs 0 1 0.2 0.4\n").is_ok()
        || parse_qsim("2\n0 h 2\n").is_ok()
    {
        return Err("unsupported qubit/gate controls accepted".into());
    }
    println!("GOOGLE_QSIM_NEGATIVE|unsupported_103=REJECTED|unsupported_fsim=REJECTED|bad_qubit_index=REJECTED|result=PASS|json=0");
    println!("GOOGLE_QSIM_SCOPE|google_tutorial_bell_full=PASS|google_qsim_24_time_0_to_2=PASS|google_qsim_24_full=NOT_RUN|willow_103_depth40=NOT_RUN|http0_address_equivalence=UNPROVEN|physical_quantum_processor=0|json=0");
    Ok(())
}
