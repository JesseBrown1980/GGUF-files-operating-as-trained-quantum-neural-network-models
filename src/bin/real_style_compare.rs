//! Real, whole-file-disjoint code/document classification benchmark.
//! Four classes from frozen Git blobs, with integer-only predictors and
//! measured on-disk model bytes. No knowledge or 6561 real-head claims.
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

use gguf_qnn::sha256::hex_digest;
use gguf_qnn::shared_graft::{
    fit_delta, Counts, Graft, Histogram, Router, RoutingMode, BLOCK, PARENTS,
};
use gguf_qnn::specialists::{family_of_byte, log2_q12};
use std::collections::BTreeSet;
use std::error::Error;
use std::fs;
use std::path::Path;
use std::process::Command;
use std::time::Instant;

const BASE: &str = "2ee84bfaa3163ea8f0fe405e1d0af0915652f1e0";
const SPLIT: &str = include_str!("../../grafts/REALSTYLE-SPLIT.tsv");
const CLASSES: [&str; 4] = ["rust", "python", "markdown", "hbp"];
const NCLASS: usize = 4;
const TRAIN_BYTES: usize = 1_536;
const LEAF_BYTES: usize = 512;
const FULL_SYNTHETIC_SHA: &str = "606c4d8478b8dbd72dfda0dad6c6ef1895c081a7cd5d5bb6c363525f57b941b2";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Partition {
    Train,
    Validation,
    Test,
}

struct Document {
    class: usize,
    partition: Partition,
    path: String,
    blob: String,
    data: Vec<u8>,
}

fn git_output(args: &[&str]) -> Result<Vec<u8>, Box<dyn Error>> {
    let output = Command::new("git").args(args).output()?;
    if !output.status.success() {
        return Err(format!("git failed: {}", args.join(" ")).into());
    }
    Ok(output.stdout)
}

fn load_frozen_documents() -> Result<Vec<Document>, Box<dyn Error>> {
    let mut docs = Vec::new();
    let mut seen_paths = BTreeSet::new();
    let mut seen_blobs = BTreeSet::new();
    let mut balance = [[0_usize; 3]; NCLASS];
    let anchor = String::from_utf8(git_output(&["rev-parse", BASE])?)?;
    if anchor.trim() != BASE {
        return Err("frozen repository commit unavailable".into());
    }
    for line in SPLIT
        .lines()
        .filter(|x| !x.starts_with('#') && !x.is_empty())
    {
        let row: Vec<&str> = line.split('\t').collect();
        if row.len() != 5 {
            return Err("frozen split has wrong field count".into());
        }
        let class = CLASSES
            .iter()
            .position(|x| *x == row[0])
            .ok_or("bad class")?;
        let partition = match row[1] {
            "train" => Partition::Train,
            "validation" => Partition::Validation,
            "test" => Partition::Test,
            _ => return Err("bad partition".into()),
        };
        let path = row[4];
        if path.contains('\n') || !seen_paths.insert(path.to_string()) {
            return Err("duplicate path in frozen manifest".into());
        }
        if !seen_blobs.insert(row[2].to_string()) {
            return Err("identical Git blob appears in multiple frozen files".into());
        }
        let blob_ref = format!("{BASE}:{path}");
        let actual = String::from_utf8(git_output(&["rev-parse", &blob_ref])?)?;
        if actual.trim() != row[2] {
            return Err(format!("source SHA mismatch: {path}").into());
        }
        let bytes = git_output(&["show", &blob_ref])?;
        let declared_size: usize = row[3].parse()?;
        if bytes.len() != declared_size || bytes.len() < 2_048 {
            return Err(format!("source length mismatch: {path}").into());
        }
        let index = match partition {
            Partition::Train => 0,
            Partition::Validation => 1,
            Partition::Test => 2,
        };
        balance[class][index] += 1;
        docs.push(Document {
            class,
            partition,
            path: path.to_string(),
            blob: row[2].to_string(),
            data: bytes,
        });
    }
    if docs.len() != 72 || balance.iter().any(|x| *x != [6, 3, 9]) {
        return Err("frozen split must be 6/3/9 per class; total 72 unique sources".into());
    }
    Ok(docs)
}

struct Baselines {
    group: [[u32; 3]; NCLASS],
    unigram: Vec<[u32; 256]>,
    bigram: Vec<Vec<u16>>,
    row_sum: Vec<[u32; 256]>,
    group_sum: [u32; NCLASS],
    unigram_sum: [u32; NCLASS],
}

impl Baselines {
    fn train(docs: &[Document]) -> Self {
        let mut model = Self {
            group: [[0; 3]; NCLASS],
            unigram: vec![[0; 256]; NCLASS],
            bigram: vec![vec![0; 65_536]; NCLASS],
            row_sum: vec![[0; 256]; NCLASS],
            group_sum: [0; NCLASS],
            unigram_sum: [0; NCLASS],
        };
        for doc in docs.iter().filter(|d| d.partition == Partition::Train) {
            let bytes = &doc.data[..TRAIN_BYTES];
            let c = doc.class;
            let mut previous = 0_u8;
            for &byte in bytes {
                model.group[c][family_of_byte(byte)] += 1;
                model.unigram[c][usize::from(byte)] += 1;
                let entry = usize::from(previous) * 256 + usize::from(byte);
                model.bigram[c][entry] += 1;
                model.row_sum[c][usize::from(previous)] += 1;
                previous = byte;
            }
            model.group_sum[c] += bytes.len() as u32;
            model.unigram_sum[c] += bytes.len() as u32;
        }
        model
    }

    fn group_score(&self, c: usize, data: &[u8]) -> u64 {
        let total = log2_q12(self.group_sum[c] + 3);
        data.iter()
            .map(|&byte| u64::from(total - log2_q12(self.group[c][family_of_byte(byte)] + 1)))
            .sum()
    }

    fn unigram_score(&self, c: usize, data: &[u8]) -> u64 {
        let total = log2_q12(self.unigram_sum[c] + 256);
        data.iter()
            .map(|&byte| u64::from(total - log2_q12(self.unigram[c][usize::from(byte)] + 1)))
            .sum()
    }

    fn bigram_score(&self, c: usize, data: &[u8]) -> u64 {
        let mut previous = 0_u8;
        let mut score = 0_u64;
        for &byte in data {
            let slot = usize::from(previous) * 256 + usize::from(byte);
            let total = self.row_sum[c][usize::from(previous)] + 256;
            score += u64::from(log2_q12(total) - log2_q12(u32::from(self.bigram[c][slot]) + 1));
            previous = byte;
        }
        score
    }

    fn centroid_score(&self, c: usize, data: &[u8]) -> i128 {
        let mut hist = [0_u32; 256];
        for &byte in data {
            hist[usize::from(byte)] += 1;
        }
        let train_n = i128::from(self.unigram_sum[c]);
        let test_n = data.len() as i128;
        hist.iter()
            .zip(self.unigram[c])
            .map(|(&observed, trained)| {
                let diff = i128::from(observed) * train_n - i128::from(trained) * test_n;
                diff * diff
            })
            .sum()
    }

    fn classify(&self, variant: usize, data: &[u8]) -> usize {
        (0..NCLASS)
            .min_by_key(|&c| {
                if variant == 3 {
                    self.centroid_score(c, data)
                } else {
                    i128::from(match variant {
                        1 => self.group_score(c, data),
                        2 => self.unigram_score(c, data),
                        4 => self.bigram_score(c, data),
                        _ => 0,
                    })
                }
            })
            .unwrap_or(0)
    }

    fn serialized(&self, variant: usize) -> Vec<u8> {
        let mut bytes = match variant {
            0 => b"MAJ1".to_vec(),
            1 => b"GRP1".to_vec(),
            2 => b"UNI1".to_vec(),
            3 => b"CEN1".to_vec(),
            4 => b"BIG1".to_vec(),
            _ => unreachable!("unknown baseline"),
        };
        if variant == 0 {
            bytes.push(0);
            return bytes;
        }
        for c in 0..NCLASS {
            bytes.push(c as u8);
            if variant == 1 {
                for &count in &self.group[c] {
                    bytes.extend_from_slice(&count.to_le_bytes());
                }
            } else if variant == 2 || variant == 3 {
                for &count in &self.unigram[c] {
                    bytes.extend_from_slice(&count.to_le_bytes());
                }
            } else {
                for (i, &count) in self.bigram[c].iter().enumerate() {
                    if count > 0 {
                        bytes.extend_from_slice(&(i as u16).to_le_bytes());
                        bytes.extend_from_slice(&count.to_le_bytes());
                    }
                }
            }
        }
        bytes
    }
}

fn train_graft(docs: &[Document]) -> Result<Graft, Box<dyn Error>> {
    let mut counts = Counts::new();
    for doc in docs.iter().filter(|d| d.partition == Partition::Train) {
        counts.add_file(&doc.data[..TRAIN_BYTES])?;
    }
    let mut graft = Graft::new(counts.finish(), 24);
    for c in 0..NCLASS {
        let mut hist = Histogram::default();
        for doc in docs
            .iter()
            .filter(|d| d.partition == Partition::Validation && d.class == c)
        {
            hist.add_file(&doc.data[..1_024]);
        }
        graft.parents[c] = Some(fit_delta(&graft.backbone, &hist, [0; 3]));
    }
    for c in 0..NCLASS {
        let mut leaf = 0_usize;
        for doc in docs
            .iter()
            .filter(|d| d.partition == Partition::Train && d.class == c)
        {
            let mut hist = Histogram::default();
            hist.add_file(&doc.data[TRAIN_BYTES..TRAIN_BYTES + LEAF_BYTES]);
            let parent = graft.parents[c].expect("trained parent");
            graft.leaves[c * 81 + leaf] = Some(fit_delta(&graft.backbone, &hist, parent));
            leaf += 1;
        }
        assert_eq!(leaf, 6);
    }
    assert_eq!(graft.learned_parents(), 4);
    assert_eq!(graft.learned_leaves(), 24);
    Ok(graft)
}

fn routed_parent(graft: &Graft, bytes: &[u8], mode: RoutingMode) -> usize {
    assert!(bytes.len() % BLOCK == 0);
    let mut router = Router::new(graft, mode);
    for end in (BLOCK..=bytes.len()).step_by(BLOCK) {
        router.select(graft, &bytes[..end], mode);
    }
    router.active / 81
}

fn readout_for_synthetic(graft: &Graft, docs: &[Document], take: usize) -> [u8; PARENTS] {
    let mut votes = [[0_u16; NCLASS]; PARENTS];
    for doc in docs.iter().filter(|d| d.partition == Partition::Validation) {
        let parent = routed_parent(graft, &doc.data[..take], RoutingMode::Tree);
        votes[parent][doc.class] += 1;
    }
    let mut map = [0_u8; PARENTS];
    for (parent, counts) in votes.iter().enumerate() {
        map[parent] = counts
            .iter()
            .enumerate()
            .max_by_key(|(c, n)| (**n, std::cmp::Reverse(*c)))
            .map_or(0, |(c, _)| c as u8);
    }
    map
}

fn predict(
    method: usize,
    base: &Baselines,
    graft: &Graft,
    synthetic: &Graft,
    map: &[u8; PARENTS],
    bytes: &[u8],
) -> usize {
    match method {
        0 => 0,
        1..=4 => base.classify(method, bytes),
        5 => routed_parent(graft, bytes, RoutingMode::Parents),
        6 => routed_parent(graft, bytes, RoutingMode::Tree),
        7 => usize::from(map[routed_parent(synthetic, bytes, RoutingMode::Tree)]),
        _ => unreachable!("bad method"),
    }
}

const METHOD_NAMES: [&str; 8] = [
    "majority",
    "three_group_nb",
    "byte_unigram_nb",
    "byte_centroid",
    "byte_bigram_nb",
    "shared_graft_parents",
    "shared_graft_tree",
    "synthetic_6561_transfer",
];

fn run(synthetic_path: &Path, out: &Path) -> Result<(), Box<dyn Error>> {
    fs::create_dir_all(out)?;
    let docs = load_frozen_documents()?;
    let begin = Instant::now();
    let baseline = Baselines::train(&docs);
    let baselines_us = begin.elapsed().as_micros();
    let begin = Instant::now();
    let graft = train_graft(&docs)?;
    let graft_us = begin.elapsed().as_micros();
    let synthetic_bytes = fs::read(synthetic_path)?;
    if hex_digest(&synthetic_bytes) != FULL_SYNTHETIC_SHA {
        return Err("wrong fixed pretrained 6561 synthetic GGUF model".into());
    }
    let synthetic = Graft::from_gguf(&synthetic_bytes)?;
    if synthetic.learned_leaves() != 6_561 {
        return Err("pretrained full 6561 head count mismatch".into());
    }
    let graft_bytes = graft.gguf();
    let mut parent = graft.clone();
    parent.leaves.fill(None);
    let parent_bytes = parent.gguf();
    fs::write(out.join("real_graft_tree.gguf"), &graft_bytes)?;
    fs::write(out.join("real_graft_parents.gguf"), &parent_bytes)?;
    for (method, name) in METHOD_NAMES.iter().enumerate().take(5) {
        fs::write(out.join(format!("{name}.model")), baseline.serialized(method))?;
    }
    let model_sizes: [usize; 8] = [
        baseline.serialized(0).len(),
        baseline.serialized(1).len(),
        baseline.serialized(2).len(),
        baseline.serialized(3).len(),
        baseline.serialized(4).len(),
        parent_bytes.len(),
        graft_bytes.len(),
        synthetic_bytes.len() + PARENTS,
    ];
    let mut report = format!(
        "REALSTYLE_CONTRACT|schema=QNN-REAL-STYLE-COMPARE-V1|base={BASE}|train_sources=24|validation_sources=12|test_sources=36|classes=rust,python,markdown,hbp|leakage=NONE_BY_WHOLE_GIT_BLOB|synthetic_pretrained_not_retrained=YES|json=0\nREALSTYLE_MODELS|real_parent_heads=4|real_leaf_heads=24|synthetic_parent_heads=81|synthetic_leaf_heads=6561|real_graft_train_us={graft_us}|baseline_train_us={baselines_us}|json=0\n"
    );
    report.push_str(&format!(
        "REALSTYLE_INPUT|manifest_sha256={}|real_graft_sha256={}|synthetic_graft_sha256={FULL_SYNTHETIC_SHA}|json=0\n",
        hex_digest(SPLIT.as_bytes()),
        hex_digest(&graft_bytes)
    ));

    for take in [256_usize, 1_024_usize] {
        let label_map = readout_for_synthetic(&synthetic, &docs, take);
        fs::write(
            out.join(format!("synthetic_{take}_label_map.bin")),
            label_map,
        )?;
        for method in 0..METHOD_NAMES.len() {
            let mut matrix = [[0_usize; NCLASS]; NCLASS];
            let mut count = 0_usize;
            let start = Instant::now();
            let mut checksum = 0_usize;
            // Repeat for less noisy per-example timing; input reading is excluded.
            for _ in 0..10 {
                for doc in docs.iter().filter(|d| d.partition == Partition::Test) {
                    let observed = &doc.data[..take];
                    let result =
                        predict(method, &baseline, &graft, &synthetic, &label_map, observed);
                    checksum += result;
                }
            }
            let elapsed_us = start.elapsed().as_micros();
            for doc in docs.iter().filter(|d| d.partition == Partition::Test) {
                let result = predict(
                    method,
                    &baseline,
                    &graft,
                    &synthetic,
                    &label_map,
                    &doc.data[..take],
                );
                matrix[doc.class][result] += 1;
                count += 1;
                report.push_str(&format!(
                    "REALSTYLE_PRED|method={}|prefix={take}|true={}|pred={}|correct={}|blob={}|path={}|json=0\n",
                    METHOD_NAMES[method],
                    CLASSES[doc.class],
                    CLASSES[result],
                    usize::from(result == doc.class),
                    doc.blob,
                    doc.path
                ));
            }
            let correct: usize = (0..NCLASS).map(|c| matrix[c][c]).sum();
            if count != 36 {
                return Err("test source count not 36".into());
            }
            report.push_str(&format!(
                "REALSTYLE_RESULT|method={}|prefix={take}|correct={correct}|total={count}|model_bytes={}|inference_10_pass_us={elapsed_us}|timing_checksum={checksum}|json=0\n",
                METHOD_NAMES[method], model_sizes[method]
            ));
            for (truth, row) in matrix.iter().enumerate() {
                report.push_str(&format!(
                    "REALSTYLE_CONFUSION|method={}|prefix={take}|true={}|rust={}|python={}|markdown={}|hbp={}|json=0\n",
                    METHOD_NAMES[method],
                    CLASSES[truth],
                    row[0],
                    row[1],
                    row[2],
                    row[3]
                ));
            }
        }
        // By construction, the parent selection is independent of leaf weights.
        let mut equal = true;
        for doc in docs.iter().filter(|d| d.partition == Partition::Test) {
            let x = routed_parent(&graft, &doc.data[..take], RoutingMode::Parents);
            let y = routed_parent(&graft, &doc.data[..take], RoutingMode::Tree);
            equal &= x == y;
        }
        assert!(equal);
        report.push_str(&format!(
            "REALSTYLE_INVARIANT|prefix={take}|parent_only_vs_tree_classification_equal=PASS|why=leaf_weights_do_not_affect_parent_selection|json=0\n"
        ));
    }
    report.push_str("REALSTYLE_COMPLETE|heldout_real_source_files=36|classes=4|methods=8|prefixes=2|all_16_confusion_matrices=FILED|synthetic_6561_actual_GGUF=TESTED|json=0\n");
    fs::write(out.join("REALSTYLE-RESULT.hbp"), &report)?;
    print!("{report}");
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = std::env::args().collect();
    match args.as_slice() {
        [_, flag, synthetic, out] if flag == "--run" => run(Path::new(synthetic), Path::new(out)),
        _ => Err("usage: real_style_compare --run SYNTHETIC_6561_GGUF OUTPUT_DIR".into()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn frozen_file_manifest_contains_four_balanced_categories() {
        assert_eq!(SPLIT.lines().filter(|x| !x.starts_with('#')).count(), 72);
        for category in CLASSES {
            assert_eq!(
                SPLIT
                    .lines()
                    .filter(|x| x.starts_with(&format!("{category}\t")))
                    .count(),
                18
            );
        }
    }

    #[test]
    fn categorical_models_score_distinct_predefined_samples() {
        let b = Baselines {
            group: [[0; 3]; NCLASS],
            unigram: vec![[0; 256]; NCLASS],
            bigram: vec![vec![0; 65_536]; NCLASS],
            row_sum: vec![[0; 256]; NCLASS],
            group_sum: [0; NCLASS],
            unigram_sum: [0; NCLASS],
        };
        assert_eq!(b.classify(0, b"test"), 0);
        assert_eq!(b.classify(1, b"test"), 0);
        assert_eq!(b.classify(2, b"test"), 0);
        assert_eq!(b.classify(3, b"test"), 0);
        assert_eq!(b.classify(4, b"test"), 0);
    }
}
