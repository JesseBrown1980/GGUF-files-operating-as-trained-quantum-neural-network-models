//! Train, export, encode and independently decode a shared-graft GGUF model.
//! Corpus-manifest and demo commands never use held-out bytes for fitting.
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

use gguf_qnn::graft_codec::{decode, encode};
use gguf_qnn::sha256::hex_digest;
use gguf_qnn::shared_graft::{
    fit_delta, Counts, Graft, Histogram, RoutingMode, BLOCK, CAPACITY, TRAIN_LIMIT, VALID_LIMIT,
};
use std::collections::{BTreeMap, BTreeSet};
use std::error::Error;
use std::fs;
use std::path::Path;

#[derive(Clone)]
struct Record {
    slot: usize,
    validation: Vec<u8>,
}

fn train_model(counts: Counts, records: &[Record]) -> Result<Graft, Box<dyn Error>> {
    if records.is_empty() {
        return Err("no trained heads".into());
    }
    let sources = counts.sources as u32;
    let mut model = Graft::new(counts.finish(), sources);
    let mut by_parent: BTreeMap<usize, Histogram> = BTreeMap::new();
    for record in records {
        if record.slot >= CAPACITY || record.validation.is_empty() {
            return Err("invalid slot or empty validation".into());
        }
        by_parent
            .entry(record.slot / 81)
            .or_default()
            .add_file(&record.validation);
    }
    for (parent, histogram) in &by_parent {
        model.parents[*parent] = Some(fit_delta(&model.backbone, histogram, [0; 3]));
    }
    for record in records {
        let mut history = Histogram::default();
        history.add_file(&record.validation);
        let parent = model.parents[record.slot / 81].expect("trained parent");
        model.leaves[record.slot] = Some(fit_delta(&model.backbone, &history, parent));
    }
    Ok(model)
}

fn read_source(path: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let bytes = fs::read(path)?;
    if bytes.is_empty() {
        return Err(format!("source is empty: {path}").into());
    }
    Ok(bytes)
}

fn train_manifest(manifest: &Path, model_path: &Path) -> Result<(), Box<dyn Error>> {
    let manifest_bytes = fs::read(manifest)?;
    let text = std::str::from_utf8(&manifest_bytes)?;
    let mut counts = Counts::new();
    let mut records = Vec::new();
    let mut seen_slots = BTreeSet::new();
    let mut seen_train = BTreeSet::new();
    let mut seen_validation = BTreeSet::new();
    let mut all_hashes = Vec::new();
    for (line_number, line) in text.lines().enumerate() {
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let fields: Vec<&str> = line.split('\t').collect();
        if fields.len() != 3 {
            return Err(format!(
                "manifest line {} must have id, train_path, validation_path",
                line_number + 1
            )
            .into());
        }
        let slot: usize = fields[0].parse()?;
        if slot >= CAPACITY || !seen_slots.insert(slot) {
            return Err("duplicate or out-of-bounds slot".into());
        }
        if fields[1] == fields[2]
            || !seen_train.insert(fields[1].to_string())
            || !seen_validation.insert(fields[2].to_string())
        {
            return Err("train/validation paths overlap or repeat".into());
        }
        let train = read_source(fields[1])?;
        let validation = read_source(fields[2])?;
        all_hashes.extend_from_slice(hex_digest(&train).as_bytes());
        all_hashes.extend_from_slice(hex_digest(&validation).as_bytes());
        counts.add_file(&train[..train.len().min(TRAIN_LIMIT)])?;
        records.push(Record {
            slot,
            validation: validation[..validation.len().min(VALID_LIMIT)].to_vec(),
        });
    }
    if seen_train.iter().any(|path| seen_validation.contains(path)) {
        return Err("validation path also used in training".into());
    }
    let n = records.len();
    let training_bytes = counts.bytes;
    let model = train_model(counts, &records)?;
    let gguf = model.gguf();
    fs::write(model_path, &gguf)?;
    println!(
        "GRAFT_TRAIN|manifest_sha256={}|sources_sha256={}|trained_sources={n}|trained_parents={}|trained_leaves={}|training_bytes={training_bytes}|model_bytes={}|model_sha256={}|full_6561_trained={}|json=0",
        hex_digest(&manifest_bytes),
        hex_digest(&all_hashes),
        model.learned_parents(),
        model.learned_leaves(),
        gguf.len(),
        hex_digest(&gguf),
        if n == CAPACITY { 1 } else { 0 }
    );
    Ok(())
}

const TRAIN: [[&str; 3]; 3] = [
    ["src/qnn.rs", "src/gguf_model.rs", "src/qutrit.rs"],
    ["README.md", "polariton/README.md", "spatial12b/README.md"],
    [
        "PREREG.hbp",
        "PREREG-YM-Z3.hbp",
        "spatial12b/PREDICTION.hbp",
    ],
];
const VALID: [&str; 3] = [
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

fn interleave(files: &[Vec<u8>]) -> Vec<u8> {
    let mut offset = vec![0; files.len()];
    let mut out = Vec::with_capacity(files.iter().map(Vec::len).sum());
    loop {
        let mut more = false;
        for (data, next) in files.iter().zip(offset.iter_mut()) {
            let end = (*next + BLOCK).min(data.len());
            if *next < end {
                out.extend_from_slice(&data[*next..end]);
                *next = end;
                more = true;
            }
        }
        if !more {
            return out;
        }
    }
}

fn case(
    name: &str,
    model: &Graft,
    mode: RoutingMode,
    input: &[u8],
    output: &Path,
) -> Result<(), Box<dyn Error>> {
    let gguf = model.gguf();
    let start = std::time::Instant::now();
    let result = encode(input, &gguf, mode);
    let micros = start.elapsed().as_micros();
    let (decoded, routes) = decode(&result.stream, &gguf)?;
    if decoded != input || routes != result.routes {
        return Err(format!("failed byte or route replay: {name}").into());
    }
    let model_path = output.join(format!("{name}.gguf"));
    let stream_path = output.join(format!("{name}.stream"));
    fs::write(model_path, &gguf)?;
    fs::write(stream_path, &result.stream)?;
    let route_bytes: Vec<u8> = result.routes.iter().flat_map(|x| x.to_le_bytes()).collect();
    println!(
        "GRAFT_RESULT|name={name}|mode={}|trained_parents={}|trained_leaves={}|nonzero_bigram_entries={}|source_bytes={}|model_gguf_bytes={}|stream_bytes={}|cold_total_bytes={}|route_blocks={}|parent_switches={}|total_switches={}|routes_sha256={}|output_sha256={}|encode_us={micros}|replay=PASS|json=0",
        mode.id(),
        model.learned_parents(),
        model.learned_leaves(),
        model.backbone.trained_entries(),
        input.len(),
        gguf.len(),
        result.stream.len(),
        gguf.len() + result.stream.len(),
        routes.len(),
        result.parent_switches,
        result.total_switches,
        hex_digest(&route_bytes),
        hex_digest(&decoded)
    );
    Ok(())
}

fn demo(out: &Path) -> Result<(), Box<dyn Error>> {
    fs::create_dir_all(out)?;
    let mut counts = Counts::new();
    let mut records = Vec::new();
    let mut validations = Vec::new();
    for path in VALID {
        validations.push(read_source(path)?);
    }
    let mut paths = BTreeSet::new();
    for (family, files) in TRAIN.iter().enumerate() {
        for (file_no, path) in files.iter().enumerate() {
            if !paths.insert(*path) {
                return Err("duplicate source".into());
            }
            let raw = read_source(path)?;
            let truncated = &raw[..raw.len().min(1_400)];
            counts.add_file(truncated)?;
            let parent = family * 3 + file_no;
            for leaf in 0..3 {
                let validation = &validations[family];
                let start = leaf * VALID_LIMIT;
                let end = (start + VALID_LIMIT).min(validation.len());
                if end <= start {
                    return Err("validation too small for demo shard".into());
                }
                records.push(Record {
                    slot: parent * 81 + leaf,
                    validation: validation[start..end].to_vec(),
                });
            }
        }
    }
    let model = train_model(counts, &records)?;
    if model.learned_leaves() != 27 || model.learned_parents() != 9 {
        return Err("demo fitted counts wrong".into());
    }
    let test_files: Vec<Vec<u8>> = TEST
        .iter()
        .flatten()
        .map(|p| read_source(p))
        .collect::<Result<_, _>>()?;
    let target = interleave(&test_files);
    fs::write(out.join("heldout.raw"), &target)?;
    println!("GRAFT_DEMO_CONTRACT|data=PREVIOUSLY_INSPECTED_QNN_TEST_FILES|blind=NO|training_files=9|validation_files=3|heldout_files=6|learned_parents=9|learned_leaves=27|address_capacity=6561|json=0");
    let mut baseline = model.clone();
    baseline.parents.fill(None);
    baseline.leaves.fill(None);
    case("shared_base", &baseline, RoutingMode::Base, &target, out)?;
    let mut parent_only = model.clone();
    parent_only.leaves.fill(None);
    case(
        "parents_only",
        &parent_only,
        RoutingMode::Parents,
        &target,
        out,
    )?;
    case("shared_tree", &model, RoutingMode::Tree, &target, out)?;
    let mut zero = model.clone();
    for value in zero.parents.iter_mut().flatten() {
        *value = [0; 3];
    }
    for value in zero.leaves.iter_mut().flatten() {
        *value = [0; 3];
    }
    case("zero_deltas", &zero, RoutingMode::Tree, &target, out)?;
    let mut shuffled = model.clone();
    let indices: Vec<usize> = (0..CAPACITY)
        .filter(|&id| model.leaves[id].is_some())
        .collect();
    for (i, &id) in indices.iter().enumerate() {
        shuffled.leaves[id] = model.leaves[indices[(i + 7) % indices.len()]];
    }
    case(
        "shuffled_deltas",
        &shuffled,
        RoutingMode::Tree,
        &target,
        out,
    )?;
    println!("GRAFT_DEMO_COMPLETE|cases=5|exact_replays=5|address_capacity=6561|learned_leaves=27|full_6561_corpus=NOT_AVAILABLE|trained_full_LLM=NO|quantum_simulation=NO|json=0");
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = std::env::args().collect();
    match args.as_slice() {
        [_, command, out] if command == "--demo" => demo(Path::new(out)),
        [_, command, manifest, model] if command == "--fit-manifest" => {
            train_manifest(Path::new(manifest), Path::new(model))
        }
        [_, command, model, input, stream, mode] if command == "--encode" => {
            let gguf = fs::read(model)?;
            let source = fs::read(input)?;
            let route = match mode.as_str() {
                "base" => RoutingMode::Base,
                "parents" => RoutingMode::Parents,
                "tree" => RoutingMode::Tree,
                _ => return Err("mode must be base, parents or tree".into()),
            };
            let result = encode(&source, &gguf, route);
            fs::write(stream, &result.stream)?;
            println!(
                "GRAFT_ENCODE|source_bytes={}|stream_bytes={}|model_bytes={}|trained_leaves={}|sha256={}|json=0",
                source.len(),
                result.stream.len(),
                gguf.len(),
                Graft::from_gguf(&gguf)?.learned_leaves(),
                hex_digest(&result.stream)
            );
            Ok(())
        }
        [_, command, model, stream, output] if command == "--decode" => {
            let gguf = fs::read(model)?;
            let coded = fs::read(stream)?;
            let (data, routes) = decode(&coded, &gguf)?;
            fs::write(output, &data)?;
            println!(
                "GRAFT_DECODE|decoded_bytes={}|route_blocks={}|sha256={}|status=PASS|json=0",
                data.len(),
                routes.len(),
                hex_digest(&data)
            );
            Ok(())
        }
        [_, command, model] if command == "--inspect" => {
            let raw = fs::read(model)?;
            let g = Graft::from_gguf(&raw)?;
            println!(
                "GRAFT_INSPECT|capacity=6561|trained_parents={}|trained_leaves={}|shared_entries={}|model_bytes={}|sha256={}|json=0",
                g.learned_parents(),
                g.learned_leaves(),
                g.backbone.trained_entries(),
                raw.len(),
                hex_digest(&raw)
            );
            Ok(())
        }
        _ => Err("usage: shared_graft --demo OUT | --fit-manifest MANIFEST.tsv MODEL.gguf | --encode MODEL.gguf IN OUT.stream {base,parents,tree} | --decode MODEL.gguf INPUT.stream OUT | --inspect MODEL.gguf".into()),
    }
}
