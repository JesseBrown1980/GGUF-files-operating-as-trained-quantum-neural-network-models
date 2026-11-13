//! Fill and test all 6,561 addressable heads of the shared GGUF model.
//! The synthetic fixture is for architecture verification only: real corpus
//! training requires the operator's 6,561 distinct source files.
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

use gguf_qnn::graft_codec::{decode, encode};
use gguf_qnn::sha256::hex_digest;
use gguf_qnn::shared_graft::{
    fit_delta, Counts, Graft, Histogram, RoutingMode, CAPACITY, LEAVES_PER_PARENT, PARENTS,
    TRAIN_LIMIT, VALID_LIMIT,
};
use std::collections::BTreeSet;
use std::error::Error;
use std::fs::{self, File};
use std::io::Read;
use std::path::{Path, PathBuf};
use std::time::Instant;

const TARGET_PER_HEAD: usize = 512;
const FIXTURE_TRAIN_BYTES: usize = 1_024;
const FIXTURE_VALID_BYTES: usize = 512;
const FIXTURE_EXPECTED_TARGET: usize = CAPACITY * TARGET_PER_HEAD;

#[derive(Clone)]
struct Partition {
    validation: Vec<u8>,
}

struct Input {
    counts: Counts,
    parts: Vec<Partition>,
    target: Vec<u8>,
    manifest_digest: String,
    source_digest: String,
    synthetic: bool,
}

fn make_synthetic(slot: usize, phase: u8, length: usize) -> Vec<u8> {
    let parent = slot / LEAVES_PER_PARENT;
    let leaf = slot % LEAVES_PER_PARENT;
    let mut state = (slot as u64 + 1).wrapping_mul(0x9e37_79b9_7f4a_7c15)
        ^ (u64::from(phase) + 1).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    let mut output = Vec::with_capacity(length);
    for index in 0..length {
        state ^= state << 13;
        state ^= state >> 7;
        state ^= state << 17;
        let r = ((state >> 21) as u32).wrapping_add(index as u32);
        // Every parent has a persistent distribution; the first fixture
        // averaged all three groups within every parent and never switched.
        // This revised fixture forces distinct parent-level populations.
        let group = parent % 3;
        let skew = ((parent / 3) % 9 * 2 + leaf % 9) as u32;
        let selector = r % 100;
        let byte = match group {
            0 if selector < 60 + skew => b'a' + (r % 26) as u8,
            1 if selector < 60 + skew => b'0' + (r % 10) as u8,
            2 if selector < 30 + skew => b'\n',
            _ if selector < 10 => b' ',
            _ if selector < 15 => b'\t',
            _ if selector < 45 => b'A' + (r % 26) as u8,
            _ if selector < 75 => b'0' + (r % 10) as u8,
            _ => b";{}|()[]=!@"[(r % 11) as usize],
        };
        output.push(byte);
    }
    output
}

fn fixture_input() -> Result<Input, Box<dyn Error>> {
    let mut counts = Counts::new();
    let mut parts = Vec::with_capacity(CAPACITY);
    let mut target = Vec::with_capacity(FIXTURE_EXPECTED_TARGET);
    let mut fingerprint = Vec::with_capacity(CAPACITY * 64);
    for slot in 0..CAPACITY {
        let training = make_synthetic(slot, 0, FIXTURE_TRAIN_BYTES);
        let validation = make_synthetic(slot, 1, FIXTURE_VALID_BYTES);
        let heldout = make_synthetic(slot, 2, TARGET_PER_HEAD);
        counts.add_file(&training)?;
        fingerprint.extend_from_slice(hex_digest(&training).as_bytes());
        parts.push(Partition { validation });
        target.extend_from_slice(&heldout);
    }
    Ok(Input {
        counts,
        parts,
        target,
        manifest_digest: String::from("SYNTHETIC_FIXED_GENERATOR_V2_PARENT_DISTINCT"),
        source_digest: hex_digest(&fingerprint),
        synthetic: true,
    })
}

/// Source-list format: exactly 6,561 lines in increasing order.
/// Each line is `slot<TAB>path` and points to one actual unique source.
/// The prefix already used for training is divided into training and
/// 512-byte validation; the following 512 bytes are never used to fit.
fn real_input(list_path: &Path) -> Result<Input, Box<dyn Error>> {
    let manifest = fs::read(list_path)?;
    let text = std::str::from_utf8(&manifest)?;
    let mut counts = Counts::new();
    let mut parts = Vec::with_capacity(CAPACITY);
    let mut target = Vec::with_capacity(FIXTURE_EXPECTED_TARGET);
    let mut seen = BTreeSet::<PathBuf>::new();
    let mut fingerprints = Vec::with_capacity(CAPACITY * 64);
    for line in text.lines() {
        let line = line.trim_end_matches('\r');
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let (index, filename) = line
            .split_once('\t')
            .ok_or("expected slot<TAB>source_path")?;
        let slot: usize = index.parse()?;
        if slot != parts.len() || slot >= CAPACITY || filename.is_empty() {
            return Err("source rows must be exactly 0..6560, consecutive and unique".into());
        }
        let canonical = fs::canonicalize(filename)?;
        if !seen.insert(canonical.clone()) {
            return Err("duplicate source file path (including symlink aliases)".into());
        }
        // Only the first 128 KiB plus the next 512 bytes are needed.
        // Reading bounded prefixes prevents multi-GB allocations per file.
        let mut raw = Vec::with_capacity(TRAIN_LIMIT + TARGET_PER_HEAD);
        File::open(&canonical)?
            .take((TRAIN_LIMIT + TARGET_PER_HEAD) as u64)
            .read_to_end(&mut raw)?;
        if raw.len() < 2 * VALID_LIMIT + 1 {
            return Err(format!("source {slot}: need >1024 readable bytes").into());
        }
        let test_start = if raw.len() >= TRAIN_LIMIT + TARGET_PER_HEAD {
            TRAIN_LIMIT
        } else {
            raw.len() - TARGET_PER_HEAD
        };
        let validation_start = test_start - VALID_LIMIT;
        let train = &raw[..validation_start];
        let validation = &raw[validation_start..test_start];
        let heldout = &raw[test_start..test_start + TARGET_PER_HEAD];
        if train.is_empty() || validation.len() != VALID_LIMIT || heldout.len() != TARGET_PER_HEAD {
            return Err("source file partition failed".into());
        }
        counts.add_file(train)?;
        fingerprints.extend_from_slice(hex_digest(&raw).as_bytes());
        parts.push(Partition {
            validation: validation.to_vec(),
        });
        target.extend_from_slice(heldout);
    }
    if parts.len() != CAPACITY || target.len() != FIXTURE_EXPECTED_TARGET {
        return Err(format!("full 6,561 model requires exactly {CAPACITY} source files").into());
    }
    Ok(Input {
        counts,
        parts,
        target,
        manifest_digest: hex_digest(&manifest),
        source_digest: hex_digest(&fingerprints),
        synthetic: false,
    })
}

fn fit_all(counts: Counts, parts: &[Partition]) -> Result<Graft, Box<dyn Error>> {
    if parts.len() != CAPACITY {
        return Err("refuse to label incomplete panel as full 6561".into());
    }
    let start = Instant::now();
    let sources = counts.sources as u32;
    let mut graft = Graft::new(counts.finish(), sources);
    let mut parents = vec![Histogram::default(); PARENTS];
    for (index, part) in parts.iter().enumerate() {
        parents[index / LEAVES_PER_PARENT].add_file(&part.validation);
    }
    for (parent, hist) in parents.iter().enumerate() {
        graft.parents[parent] = Some(fit_delta(&graft.backbone, hist, [0; 3]));
    }
    let parent_time = start.elapsed().as_millis();
    let mut nonzero_leaf = 0_usize;
    for (index, part) in parts.iter().enumerate() {
        let mut hist = Histogram::default();
        hist.add_file(&part.validation);
        let parent = graft.parents[index / LEAVES_PER_PARENT].expect("fitted parent");
        let delta = fit_delta(&graft.backbone, &hist, parent);
        if delta != [0; 3] {
            nonzero_leaf += 1;
        }
        graft.leaves[index] = Some(delta);
    }
    if graft.learned_parents() != PARENTS || graft.learned_leaves() != CAPACITY {
        return Err("failed to populate all 81 parents and all 6561 leaves".into());
    }
    println!(
        "FULL6561_TRAIN|parents={}|leaves={}|nonzero_leaf_deltas={nonzero_leaf}|training_sources={sources}|parent_fit_ms={parent_time}|total_fit_ms={}|status=PASS|json=0",
        graft.learned_parents(),
        graft.learned_leaves(),
        start.elapsed().as_millis()
    );
    Ok(graft)
}

fn write_case(
    tag: &str,
    graft: &Graft,
    target: &[u8],
    mode: RoutingMode,
    out: &Path,
) -> Result<(), Box<dyn Error>> {
    let gguf = graft.gguf();
    let begin = Instant::now();
    let encoded = encode(target, &gguf, mode);
    let encode_ms = begin.elapsed().as_millis();
    let begin = Instant::now();
    let (decoded, routes) = decode(&encoded.stream, &gguf)?;
    let decode_ms = begin.elapsed().as_millis();
    if decoded != target || routes != encoded.routes {
        return Err(format!("{tag}: decoder bytes or routes differ").into());
    }
    let route_bytes: Vec<u8> = routes.iter().flat_map(|x| x.to_le_bytes()).collect();
    fs::write(out.join(format!("{tag}.gguf")), &gguf)?;
    fs::write(out.join(format!("{tag}.stream")), &encoded.stream)?;
    println!(
        "FULL6561_RESULT|name={tag}|mode={}|trained_parents={}|trained_leaves={}|backbone_entries={}|source_bytes={}|gguf_bytes={}|stream_bytes={}|cold_bytes={}|route_blocks={}|parent_switches={}|total_switches={}|model_sha256={}|stream_sha256={}|routes_sha256={}|decoded_sha256={}|encode_ms={encode_ms}|decode_ms={decode_ms}|replay=PASS|json=0",
        mode.id(),
        graft.learned_parents(),
        graft.learned_leaves(),
        graft.backbone.trained_entries(),
        target.len(),
        gguf.len(),
        encoded.stream.len(),
        gguf.len() + encoded.stream.len(),
        routes.len(),
        encoded.parent_switches,
        encoded.total_switches,
        hex_digest(&gguf),
        hex_digest(&encoded.stream),
        hex_digest(&route_bytes),
        hex_digest(&decoded)
    );
    Ok(())
}

fn execute(input: Input, out: &Path) -> Result<(), Box<dyn Error>> {
    fs::create_dir_all(out)?;
    let Input {
        counts,
        parts,
        target,
        manifest_digest,
        source_digest,
        synthetic,
    } = input;
    if parts.len() != CAPACITY || target.len() != FIXTURE_EXPECTED_TARGET {
        return Err("full fixture target or source count mismatch".into());
    }
    println!(
        "FULL6561_INPUT|mode={}|sources=6561|heldout_per_source=512|heldout_bytes={}|train_bytes={}|manifest_sha256={manifest_digest}|source_prefix_digest={source_digest}|target_sha256={}|synthetic={synthetic}|json=0",
        if synthetic { "DETERMINISTIC_SYNTHETIC" } else { "REAL_FILE_LIST" },
        target.len(),
        counts.bytes,
        hex_digest(&target)
    );
    let graft = fit_all(counts, &parts)?;
    let mut base = graft.clone();
    base.parents.fill(None);
    base.leaves.fill(None);
    let mut parents = graft.clone();
    parents.leaves.fill(None);
    let mut zero = graft.clone();
    for delta in zero.parents.iter_mut().flatten() {
        *delta = [0; 3];
    }
    for delta in zero.leaves.iter_mut().flatten() {
        *delta = [0; 3];
    }
    let mut shuffled = graft.clone();
    for parent in 0..PARENTS {
        let start = parent * LEAVES_PER_PARENT;
        for child in 0..LEAVES_PER_PARENT {
            let from = start + (child + 13) % LEAVES_PER_PARENT;
            shuffled.leaves[start + child] = graft.leaves[from];
        }
    }
    fs::write(out.join("target.raw"), &target)?;
    write_case("base", &base, &target, RoutingMode::Base, out)?;
    write_case("parents", &parents, &target, RoutingMode::Parents, out)?;
    write_case("full_tree", &graft, &target, RoutingMode::Tree, out)?;
    write_case("zero_deltas", &zero, &target, RoutingMode::Tree, out)?;
    write_case(
        "shuffled_deltas",
        &shuffled,
        &target,
        RoutingMode::Tree,
        out,
    )?;
    println!(
        "FULL6561_COMPLETE|populated_parent_heads=81|populated_leaf_heads=6561|heldout_bytes=3359232|exact_stream_replays=5|synthetic={synthetic}|result=PASS|json=0"
    );
    Ok(())
}

fn emit_fixture_source_list(out: &Path) -> Result<(), Box<dyn Error>> {
    fs::create_dir_all(out)?;
    let mut manifest = String::with_capacity(CAPACITY * 88);
    for slot in 0..CAPACITY {
        let path = out.join(format!("fixture_{slot:04}.bin"));
        let mut raw = make_synthetic(slot, 0, FIXTURE_TRAIN_BYTES);
        raw.extend(make_synthetic(slot, 1, FIXTURE_VALID_BYTES));
        raw.extend(make_synthetic(slot, 2, TARGET_PER_HEAD));
        fs::write(&path, &raw)?;
        manifest.push_str(&format!("{slot}\t{}\n", path.display()));
    }
    fs::write(out.join("source-list.tsv"), &manifest)?;
    println!(
        "FULL6561_EMITTED_SOURCE_LIST|file_count=6561|each_file_bytes=2048|manifest_sha256={}|synthetic=true|json=0",
        hex_digest(manifest.as_bytes())
    );
    Ok(())
}

fn decode_check(
    model_path: &Path,
    stream_path: &Path,
    raw_path: &Path,
) -> Result<(), Box<dyn Error>> {
    let model = fs::read(model_path)?;
    let stream = fs::read(stream_path)?;
    let original = fs::read(raw_path)?;
    let (decoded, routes) = decode(&stream, &model)?;
    if decoded != original {
        return Err("fresh process did not reproduce source bytes".into());
    }
    let route_bytes: Vec<u8> = routes.iter().flat_map(|x| x.to_le_bytes()).collect();
    println!(
        "FULL6561_EXTERNAL_DECODE|bytes={}|route_blocks={}|route_sha256={}|decoded_sha256={}|result=PASS|json=0",
        decoded.len(),
        routes.len(),
        hex_digest(&route_bytes),
        hex_digest(&decoded)
    );
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = std::env::args().collect();
    match args.as_slice() {
        [_, command, out] if command == "--fixture-6561" => {
            execute(fixture_input()?, Path::new(out))
        }
        [_, command, list, out] if command == "--fit-source-list" => {
            execute(real_input(Path::new(list))?, Path::new(out))
        }
        [_, command, out] if command == "--emit-fixture-source-list" => {
            emit_fixture_source_list(Path::new(out))
        }
        [_, command, list, out] if command == "--verify-fixture-source-list" => {
            let mut input = real_input(Path::new(list))?;
            input.synthetic = true;
            execute(input, Path::new(out))
        }
        [_, command, model, coded, raw] if command == "--decode-check" => {
            decode_check(Path::new(model), Path::new(coded), Path::new(raw))
        }
        _ => Err("usage: shared_6561 --fixture-6561 OUT | --fit-source-list TAB_SEPARATED_ID_PATH_LIST OUT | --decode-check MODEL.gguf STREAM RAW".into()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn deterministic_fixture_has_real_6561_distinct_train_and_validation_records() {
        let first = make_synthetic(0, 0, 1024);
        let next = make_synthetic(1, 0, 1024);
        assert_ne!(first, next);
        assert_ne!(first, make_synthetic(0, 1, 1024));
        assert_eq!(first, make_synthetic(0, 0, 1024));
    }

    #[test]
    fn input_bounds_and_exact_81x81_address_count() {
        assert_eq!(PARENTS, 81);
        assert_eq!(LEAVES_PER_PARENT, 81);
        assert_eq!(CAPACITY, 6561);
        assert_eq!(FIXTURE_EXPECTED_TARGET, 3_359_232);
    }
}
