//! Prospective source-disjoint, actual byte-stream test of compact specialist
//! weight corrections and decoder-side past-only activation.
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

use gguf_qnn::sha256::hex_digest;
use gguf_qnn::specialists::{decode, encode, static_expert, Expert, BLOCK};
use std::error::Error;
use std::fs;
use std::path::Path;
use std::time::Instant;

const TRAIN: [[&str; 3]; 3] = [
    ["src/qnn.rs", "src/gguf_model.rs", "src/qutrit.rs"],
    ["README.md", "polariton/README.md", "spatial12b/README.md"],
    [
        "PREREG.hbp",
        "PREREG-YM-Z3.hbp",
        "spatial12b/PREDICTION.hbp",
    ],
];
const VALIDATION: [&str; 3] = [
    "src/train.rs",
    "docs/GOOGLE-QSIM-LIKE-FOR-LIKE-20261104.md",
    "SEAL-YM-Z3.hbp",
];
const TEST: [[&str; 2]; 3] = [
    ["src/virtual_qnn.rs", "src/task.rs"],
    [
        "docs/FULL-Q24-INTEGER-20261104.md",
        "docs/QSIM-OFFICIAL-REFERENCE-20261104.md",
    ],
    [
        "docs/PREDICTION-GOOGLE-QSIM-20261104.hbp",
        "docs/GOOGLE-QSIM-OFFICIAL-REFERENCE-20261104.hbp",
    ],
];
const TRAIN_LIMIT: usize = 1_400;

fn read_required(path: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let bytes = fs::read(path)?;
    if bytes.is_empty() {
        return Err(format!("empty input: {path}").into());
    }
    println!(
        "SOURCE|path={path}|bytes={}|sha256={}|json=0",
        bytes.len(),
        hex_digest(&bytes)
    );
    Ok(bytes)
}

fn build_experts(training: &[Vec<Vec<u8>>], size: usize) -> Vec<Expert> {
    let mut experts = Vec::with_capacity(size);
    for (family, files) in training.iter().enumerate() {
        for data in files {
            if size == 9 {
                experts.push(Expert::from_training(data, family as u8));
            } else {
                assert_eq!(size, 27);
                for shard in 0..3 {
                    let start = data.len() * shard / 3;
                    let end = data.len() * (shard + 1) / 3;
                    experts.push(Expert::from_training(&data[start..end], family as u8));
                }
            }
        }
    }
    assert_eq!(experts.len(), size);
    experts
}

fn interleave_piecewise(files: &[Vec<u8>]) -> Vec<u8> {
    let mut offsets = vec![0_usize; files.len()];
    let mut result = Vec::with_capacity(files.iter().map(Vec::len).sum());
    loop {
        let mut progressed = false;
        for (file, offset) in files.iter().zip(offsets.iter_mut()) {
            let end = (*offset + BLOCK).min(file.len());
            if *offset < end {
                result.extend_from_slice(&file[*offset..end]);
                *offset = end;
                progressed = true;
            }
        }
        if !progressed {
            break;
        }
    }
    result
}

fn run_case(
    name: &str,
    experts: &[Expert],
    validation: &[Vec<u8>],
    heldout: &[u8],
    out: &Path,
) -> Result<(), Box<dyn Error>> {
    let starting = static_expert(experts, validation);
    let start = Instant::now();
    let coded = encode(heldout, experts, starting);
    let elapsed = start.elapsed().as_micros();
    // Only these two serialized byte objects are needed for decoding.
    let (decoded, replay_routes) = decode(&coded.stream, &coded.model_bytes)?;
    if decoded != heldout || coded.routes != replay_routes {
        return Err(format!("{name}: byte or routing mismatch").into());
    }
    fs::write(out.join(format!("{name}.model")), &coded.model_bytes)?;
    fs::write(out.join(format!("{name}.stream")), &coded.stream)?;
    let nonzero: usize = experts.iter().map(Expert::nonzero_entries).sum();
    let corrected = experts
        .iter()
        .flat_map(|expert| expert.correction)
        .filter(|&delta| delta != 0)
        .count();
    let route_sha = hex_digest(&coded.routes);
    println!(
        "SPECIALIST_RESULT|name={name}|heldout_bytes={}|models={}|first={starting}|nonzero_entries={nonzero}|changed_corrections={corrected}|model_bytes={}|stream_bytes={}|full_bytes={}|switches={}|route_blocks={}|route_sha256={route_sha}|decoded_sha256={}|encode_us={elapsed}|replay=PASS|json=0",
        heldout.len(),
        experts.len(),
        coded.model_bytes.len(),
        coded.stream.len(),
        coded.model_bytes.len() + coded.stream.len(),
        coded.switches,
        coded.routes.len(),
        hex_digest(&decoded)
    );
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = std::env::args().collect();
    let out = if args.len() == 3 && args[1] == "--run" {
        Path::new(&args[2])
    } else {
        return Err("usage: specialist_router --run <output_directory>".into());
    };
    fs::create_dir_all(out)?;
    assert!(Path::new("specialists/PREDICTION.hbp").exists());
    println!("SPECIALIST_CONTRACT|schema=QNN-COMPACT-SPECIALISTS-V1|training_from_files=9|validation_files=3|heldout_files=6|trained_parameters_per_expert=3|router=CAUSAL_256_BYTE|coder=EXACT_INTEGER_ARITHMETIC|json=0");
    let mut training = Vec::new();
    let mut total_train_bytes = 0;
    for files in TRAIN {
        let mut group = Vec::new();
        for path in files {
            let mut data = read_required(path)?;
            data.truncate(TRAIN_LIMIT);
            total_train_bytes += data.len();
            group.push(data);
        }
        training.push(group);
    }
    let validation: Vec<Vec<u8>> = VALIDATION
        .iter()
        .map(|path| read_required(path))
        .collect::<Result<_, _>>()?;
    let test_files: Vec<Vec<u8>> = TEST
        .iter()
        .flatten()
        .map(|path| read_required(path))
        .collect::<Result<_, _>>()?;
    let heldout = interleave_piecewise(&test_files);
    let total_test_bytes: usize = test_files.iter().map(Vec::len).sum();
    assert_eq!(heldout.len(), total_test_bytes);
    println!(
        "SPECIALIST_SPLIT|training_bytes={total_train_bytes}|validation_bytes={}|heldout_bytes={}|heldout_sha256={}|overlap_files=0|json=0",
        validation.iter().map(Vec::len).sum::<usize>(),
        heldout.len(),
        hex_digest(&heldout)
    );
    let mut all_training = Vec::new();
    for family in &training {
        for data in family {
            all_training.extend_from_slice(data);
        }
    }
    let generalist = [Expert::from_training(&all_training, 0)];
    run_case("static_generalist", &generalist, &validation, &heldout, out)?;

    let small = build_experts(&training, 9);
    run_case("nine_uncorrected", &small, &validation, &heldout, out)?;
    let mut small_corrected = small.clone();
    for expert in &mut small_corrected {
        expert.fit_correction(&validation[usize::from(expert.family)]);
    }
    run_case(
        "nine_corrected",
        &small_corrected,
        &validation,
        &heldout,
        out,
    )?;

    let large = build_experts(&training, 27);
    run_case(
        "twentyseven_uncorrected",
        &large,
        &validation,
        &heldout,
        out,
    )?;
    let mut corrected = large.clone();
    for expert in &mut corrected {
        expert.fit_correction(&validation[usize::from(expert.family)]);
    }
    run_case(
        "twentyseven_corrected",
        &corrected,
        &validation,
        &heldout,
        out,
    )?;
    let mut shuffled = corrected.clone();
    for (index, expert) in shuffled.iter_mut().enumerate() {
        expert.correction = corrected[(index + 7) % corrected.len()].correction;
    }
    run_case(
        "twentyseven_shuffled_edits",
        &shuffled,
        &validation,
        &heldout,
        out,
    )?;
    println!("SPECIALIST_COMPLETE|scenarios=6|reproduced=6|heldout_files=6|decoder_has_training_data=NO|stream_only_compression_claim=NO|12b_trained_nodes=NO|status=PASS|json=0");
    Ok(())
}
