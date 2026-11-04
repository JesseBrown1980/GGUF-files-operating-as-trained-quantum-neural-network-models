//! Actual Google qsim gate specifications, exact qubit arithmetic.
//! This is deliberately distinct from the qutrit models in other modules.
//! The 24-qubit test executes Google's published t=0..2 circuit prefix.
//! It supports the special H-all-then-diagonal form and rejects everything else.
#![forbid(unsafe_code)]

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Gate {
    H(usize),
    T(usize),
    Cz(usize, usize),
    Cnot(usize, usize),
}

#[derive(Debug)]
pub struct Circuit {
    pub qubits: usize,
    pub gates: Vec<Gate>,
}

pub fn parse_qsim(text: &str) -> Result<Circuit, String> {
    let mut lines = text.lines();
    let first = lines.next().ok_or("missing qubit count")?;
    let qubits: usize = first.parse().map_err(|_| "invalid qubit count")?;
    if !(1..=24).contains(&qubits) {
        return Err("size outside exact test allocation limit 1..=24".into());
    }
    let mut gates = Vec::new();
    let mut prior_time = 0u32;
    for line in lines {
        if line.is_empty() {
            continue;
        }
        let fields: Vec<&str> = line.split_whitespace().collect();
        if fields.len() < 3 {
            return Err("missing gate arguments".into());
        }
        let time: u32 = fields[0].parse().map_err(|_| "invalid gate time")?;
        if time < prior_time {
            return Err("out-of-order Google gate time".into());
        }
        prior_time = time;
        let q = |i: usize| -> Result<usize, String> {
            let n: usize = fields
                .get(i)
                .ok_or("missing qubit operand")?
                .parse()
                .map_err(|_| "invalid qubit operand")?;
            if n >= qubits {
                return Err("qubit operand outside declared register".into());
            }
            Ok(n)
        };
        let gate = match (fields[1], fields.len()) {
            ("h", 3) => Gate::H(q(2)?),
            ("t", 3) => Gate::T(q(2)?),
            ("cz", 4) => {
                let (a, b) = (q(2)?, q(3)?);
                if a == b {
                    return Err("two-qubit operation reuses one qubit".into());
                }
                Gate::Cz(a, b)
            }
            ("cnot", 4) => {
                let (a, b) = (q(2)?, q(3)?);
                if a == b {
                    return Err("two-qubit operation reuses one qubit".into());
                }
                Gate::Cnot(a, b)
            }
            _ => return Err(format!("unsupported exact Google gate: {}", fields[1])),
        };
        gates.push(gate);
    }
    if gates.is_empty() {
        return Err("no gates in circuit".into());
    }
    Ok(Circuit { qubits, gates })
}

/// The complete Google tutorial example H(0), CNOT(0,1) is simulated as
/// integer numerators divided by sqrt(2)^k. Probability is num²/2^k.
pub fn run_bell(circuit: &Circuit) -> Result<([i64; 4], u32), String> {
    if circuit.qubits != 2 {
        return Err("Bell demo must have exactly two qubits".into());
    }
    let mut state = [1i64, 0, 0, 0];
    let mut power = 0u32;
    for gate in &circuit.gates {
        match *gate {
            Gate::H(bit) => {
                let mask = 1usize << bit;
                for i in 0..4 {
                    if i & mask == 0 {
                        let j = i | mask;
                        let a = state[i];
                        let b = state[j];
                        state[i] = a + b;
                        state[j] = a - b;
                    }
                }
                power += 1;
            }
            Gate::Cnot(control, target) => {
                let c = 1usize << control;
                let t = 1usize << target;
                for i in 0..4 {
                    if i & c != 0 && i & t == 0 {
                        state.swap(i, i | t);
                    }
                }
            }
            _ => return Err("Bell simulator requires H/CNOT gate subset".into()),
        }
    }
    let norm: i64 = state.iter().map(|v| v * v).sum();
    if norm != (1i64 << power) {
        return Err("Bell circuit changed exact norm".into());
    }
    Ok((state, power))
}

#[derive(Debug)]
pub struct DiagonalPlan {
    pub qubits: usize,
    cz: Vec<(u32, u32)>,
    t: Vec<u32>,
    pub gate_count: usize,
}

/// Check that every qubit has exactly one initial Hadamard, followed only by
/// commuting diagonal CZ and T operations. No silent gate substitution.
pub fn compile_diagonal_prefix(circuit: &Circuit) -> Result<DiagonalPlan, String> {
    let mut hadamards = vec![false; circuit.qubits];
    let mut diagonals_started = false;
    let mut cz = Vec::new();
    let mut t = Vec::new();
    for g in &circuit.gates {
        match *g {
            Gate::H(q) => {
                if diagonals_started || hadamards[q] {
                    return Err("non-initial or repeated Hadamard".into());
                }
                hadamards[q] = true;
            }
            Gate::Cz(a, b) => {
                diagonals_started = true;
                if !hadamards.iter().all(|v| *v) {
                    return Err("diagonal gate before all initial Hadamards".into());
                }
                cz.push((1u32 << a, 1u32 << b));
            }
            Gate::T(q) => {
                diagonals_started = true;
                if !hadamards.iter().all(|v| *v) {
                    return Err("T gate before all initial Hadamards".into());
                }
                t.push(1u32 << q);
            }
            Gate::Cnot(_, _) => return Err("CNOT unsupported in diagonal prefix".into()),
        }
    }
    if !hadamards.iter().all(|v| *v) {
        return Err("missing initial Hadamard".into());
    }
    Ok(DiagonalPlan {
        qubits: circuit.qubits,
        cz,
        t,
        gate_count: circuit.gates.len(),
    })
}

impl DiagonalPlan {
    /// Exact amplitude = exp(i*pi*phase/4) / sqrt(2)^qubits.
    /// This is an exact 8th-root representation, with no floating point.
    #[must_use]
    pub fn phase_of(&self, bitstring: u32) -> u8 {
        let mut phase = 0u8;
        for &(a, b) in &self.cz {
            if bitstring & a != 0 && bitstring & b != 0 {
                phase ^= 4;
            }
        }
        for &m in &self.t {
            if bitstring & m != 0 {
                phase = (phase + 1) & 7;
            }
        }
        phase
    }

    /// Enumerates ALL 2^24 distinct measurement bitstrings and their exact
    /// phases in Google's published 24-qubit t<=2 circuit prefix.
    pub fn histogram(&self) -> Result<[u64; 8], String> {
        if self.qubits > 24 {
            return Err("full prefix phase enumeration limited to 24 qubits".into());
        }
        let mut hist = [0u64; 8];
        for bitstring in 0..(1u32 << self.qubits) {
            hist[usize::from(self.phase_of(bitstring))] += 1;
        }
        Ok(hist)
    }

    #[must_use]
    pub fn exact_probability_denominator(&self) -> u64 {
        1u64 << self.qubits
    }

    #[must_use]
    pub fn cz_count(&self) -> usize {
        self.cz.len()
    }

    #[must_use]
    pub fn t_count(&self) -> usize {
        self.t.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const BELL: &str = include_str!("../data/google-qsim/tutorial_bell.txt");
    const Q24: &str = include_str!("../data/google-qsim/circuit_q24_t0_t2.txt");

    #[test]
    fn complete_google_qsim_bell_circuit() {
        let c = parse_qsim(BELL).expect("original tutorial gates");
        assert_eq!(c.gates.len(), 2);
        assert_eq!(run_bell(&c).expect("exact amplitude evolution"), ([1, 0, 0, 1], 1));
    }

    #[test]
    fn original_qsim_24_qubit_48_gate_prefix() {
        assert_eq!(
            crate::sha256::hex_digest(Q24.as_bytes()),
            "87dd34b6026bedac1f989c2f4abd211ff1e3691646aaa2bf578e90df222d0356"
        );
        let c = parse_qsim(Q24).expect("unaltered published Google gate sequence");
        let plan = compile_diagonal_prefix(&c).expect("all initial H then CZ/T");
        assert_eq!((plan.qubits, plan.gate_count, plan.cz_count(), plan.t_count()), (24, 48, 12, 12));
        assert_eq!(plan.phase_of(0), 0);
        assert_eq!(plan.phase_of(1), 1);
        assert_eq!(plan.phase_of(3), 6);
        assert_eq!(plan.phase_of((1u32 << 24) - 1), 4);
        assert_eq!(plan.exact_probability_denominator(), 16_777_216);
        let hist = plan.histogram().expect("all 24 qubit output bitstrings");
        assert_eq!(
            hist,
            [2_031_616, 2_099_712, 2_168_576, 2_094_592, 2_031_616, 2_094_592, 2_156_800, 2_099_712]
        );
        assert_eq!(hist.iter().sum::<u64>(), 16_777_216);
    }

    #[test]
    fn no_qubit_trit_or_gate_substitution() {
        assert!(parse_qsim("24\n0 h 0\n1 fs 0 1 0.2 0.4\n").is_err());
        assert!(parse_qsim("2\n0 h 2\n").is_err());
        assert!(parse_qsim("2\n0 cz 0 0\n").is_err());
        assert!(parse_qsim("103\n0 h 0\n").is_err());
        assert!(parse_qsim("2\n0 h 0\n0 h 1\n1 t 0\n1 h 1\n")
            .and_then(|c| compile_diagonal_prefix(&c))
            .is_err());
        assert!(parse_qsim("2\n0 h 0\n1 t 0\n")
            .and_then(|c| compile_diagonal_prefix(&c))
            .is_err());
        assert!(parse_qsim("2\n0 h 0\n0 h 1\n1 cnot 0 1\n")
            .and_then(|c| compile_diagonal_prefix(&c))
            .is_err());
    }
}
