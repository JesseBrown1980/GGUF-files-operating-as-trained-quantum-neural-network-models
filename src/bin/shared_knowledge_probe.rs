//! A falsifiable factual-question test of the *actual* 6,561-head GGUF model.
//! This model is byte-bigram prediction plus three signed integer class shifts,
//! not a text LLM. Expected answers are used only for post-generation scoring.
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

use gguf_qnn::sha256::hex_digest;
use gguf_qnn::shared_graft::{Graft, Router, RoutingMode, BLOCK, CAPACITY};
use std::collections::BTreeSet;
use std::error::Error;
use std::fs;
use std::path::Path;

const MODEL_SHA256: &str = "606c4d8478b8dbd72dfda0dad6c6ef1895c081a7cd5d5bb6c363525f57b941b2";
const SAMPLE_SEED: u64 = 20_261_113;
const OUTPUT_LEN: usize = 64;
const QUESTIONS: [(&str, &str); 8] = [
    ("What is the capital of France?", "Paris"),
    ("What is the capital of Japan?", "Tokyo"),
    ("What is two plus two?", "4"),
    ("Who developed general relativity?", "Einstein"),
    ("What is the chemical formula for water?", "H2O"),
    ("How many sides does a triangle have?", "3"),
    ("Which planet is called the Red Planet?", "Mars"),
    ("What is the largest ocean?", "Pacific"),
];

fn question_prompt(question: &str, extended: bool) -> String {
    let mut prompt = String::new();
    if extended {
        let instructions =
            "Read the user question carefully. Respond only when you know the answer. ";
        while prompt.len() < 320 {
            prompt.push_str(instructions);
        }
    }
    prompt.push_str("Question: ");
    prompt.push_str(question);
    prompt.push_str("\nAnswer: ");
    prompt
}

fn sample_next(model: &Graft, prev: u8, active: usize, mode: RoutingMode, state: &mut u64) -> u8 {
    *state ^= *state << 13;
    *state ^= *state >> 7;
    *state ^= *state << 17;
    let delta = model.shifts(active, mode);
    let total = model.backbone.bounds(prev, 0, delta).2;
    let selected = (*state % u64::from(total)) as u32;
    model.backbone.symbol_at(prev, selected, delta).0
}

fn greedy_next(model: &Graft, prev: u8, active: usize, mode: RoutingMode) -> u8 {
    let delta = model.shifts(active, mode);
    let mut winner = 0_u8;
    let mut max_freq = 0_u32;
    for candidate in 0_u16..=255 {
        let (lo, hi, _) = model.backbone.bounds(prev, candidate as u8, delta);
        let weight = hi - lo;
        if weight > max_freq {
            winner = candidate as u8;
            max_freq = weight;
        }
    }
    winner
}

#[derive(Clone)]
struct Response {
    bytes: Vec<u8>,
    initial_head: usize,
}

fn complete(model: &Graft, prompt: &str, mode: RoutingMode, stochastic: bool) -> Response {
    let mut history = prompt.as_bytes().to_vec();
    let mut router = Router::new(model, mode);
    // Starting selection can inspect the prompt, not any generated future byte.
    let initial_head = router.select(model, &history, mode);
    let mut state = SAMPLE_SEED;
    let mut output = Vec::with_capacity(OUTPUT_LEN);
    for position in 0..OUTPUT_LEN {
        if position != 0 && position % BLOCK == 0 {
            router.select(model, &history, mode);
        }
        let prev = *history.last().unwrap_or(&0);
        let next = if stochastic {
            sample_next(model, prev, router.active, mode, &mut state)
        } else {
            greedy_next(model, prev, router.active, mode)
        };
        output.push(next);
        history.push(next);
    }
    Response {
        bytes: output,
        initial_head,
    }
}

fn grade(output: &[u8], answer: &str) -> bool {
    let line = output
        .split(|&b| b == b'\n' || b == b'\r')
        .next()
        .unwrap_or(output);
    let mut left = 0;
    while left < line.len() && line[left].is_ascii_whitespace() {
        left += 1;
    }
    let candidate = &line[left..];
    let answer_bytes = answer.as_bytes();
    if candidate.len() < answer_bytes.len() {
        return false;
    }
    if !candidate[..answer_bytes.len()].eq_ignore_ascii_case(answer_bytes) {
        return false;
    }
    candidate.len() == answer_bytes.len() || !candidate[answer_bytes.len()].is_ascii_alphanumeric()
}

fn escape_bytes(data: &[u8]) -> String {
    let mut out = String::new();
    for &b in data {
        match b {
            b'\n' => out.push_str("\\n"),
            b'\r' => out.push_str("\\r"),
            b'\t' => out.push_str("\\t"),
            b'\\' => out.push_str("\\\\"),
            32..=126 => out.push(char::from(b)),
            _ => out.push_str(&format!("\\x{b:02x}")),
        }
    }
    out
}

fn mode_name(mode: RoutingMode) -> &'static str {
    match mode {
        RoutingMode::Base => "shared_backbone",
        RoutingMode::Parents => "parent_router",
        RoutingMode::Tree => "full_6561_tree",
    }
}

fn run(model_path: &Path, output_dir: &Path) -> Result<(), Box<dyn Error>> {
    fs::create_dir_all(output_dir)?;
    let bytes = fs::read(model_path)?;
    let actual = hex_digest(&bytes);
    if actual != MODEL_SHA256 {
        return Err(format!("different GGUF model: sha256={actual}; expected fixed synthetic checkpoint {MODEL_SHA256}").into());
    }
    let model = Graft::from_gguf(&bytes)?;
    if model.learned_leaves() != CAPACITY || model.learned_parents() != 81 {
        return Err("not the complete trained 6,561-head model".into());
    }

    let modes = [RoutingMode::Base, RoutingMode::Parents, RoutingMode::Tree];
    let mut report = String::new();
    report.push_str(
        "PROBE_FREEZE|schema=QNN-6561-KNOWLEDGE-PROBE-V1|questions=8|contexts=2|generation_methods=2|modes=3|source=DETERMINISTIC_SYNTHETIC|json=0\n",
    );
    report.push_str(&format!(
        "PROBE_MODEL|sha256={actual}|parent_heads={}|leaf_heads={}|trained_on_factual_text=NO|json=0\n",
        model.learned_parents(),
        model.learned_leaves()
    ));

    let mut correctness = [[0_usize; 2]; 3];
    let mut unique_completions: Vec<[BTreeSet<Vec<u8>>; 2]> =
        (0..3).map(|_| [BTreeSet::new(), BTreeSet::new()]).collect();
    let mut initial_heads: Vec<[BTreeSet<usize>; 2]> =
        (0..3).map(|_| [BTreeSet::new(), BTreeSet::new()]).collect();
    let mut results = Vec::new();
    let mut first_expected = None::<Vec<u8>>;

    for (mode_index, &mode) in modes.iter().enumerate() {
        for extended in [false, true] {
            let context = usize::from(extended);
            for (question_id, &(question, expected)) in QUESTIONS.iter().enumerate() {
                let prompt = question_prompt(question, extended);
                assert!(!prompt.contains(expected));
                for stochastic in [false, true] {
                    let response = complete(&model, &prompt, mode, stochastic);
                    if !stochastic {
                        let correct = grade(&response.bytes, expected);
                        correctness[mode_index][context] += usize::from(correct);
                        unique_completions[mode_index][context].insert(response.bytes.clone());
                        initial_heads[mode_index][context].insert(response.initial_head);
                        if mode == RoutingMode::Base && !extended {
                            if let Some(ref first) = first_expected {
                                assert_eq!(first, &response.bytes);
                            } else {
                                first_expected = Some(response.bytes.clone());
                            }
                        }
                    }
                    let line = format!(
                        "PROBE_RESPONSE|mode={}|context={}|qid={question_id}|generator={}|question={}|expected={expected}|head={}|correct={}|output_sha256={}|escaped={} |json=0\n",
                        mode_name(mode),
                        if extended { "long" } else { "short" },
                        if stochastic { "seeded_sampling" } else { "greedy" },
                        question.replace('|', "/"),
                        response.initial_head,
                        if !stochastic && grade(&response.bytes, expected) { 1 } else { 0 },
                        hex_digest(&response.bytes),
                        escape_bytes(&response.bytes)
                    );
                    report.push_str(&line);
                    if !stochastic {
                        results.push((mode_name(mode), context, question_id, response));
                    }
                }
            }
        }
    }
    for (i, &mode) in modes.iter().enumerate() {
        for context in 0..=1 {
            report.push_str(&format!(
                "PROBE_SCORE|mode={}|context={}|correct={}|total=8|unique_greedy_outputs={}|distinct_initial_heads={}|json=0\n",
                mode_name(mode),
                if context == 0 { "short" } else { "long" },
                correctness[i][context],
                unique_completions[i][context].len(),
                initial_heads[i][context].len()
            ));
        }
    }
    let all_correct: usize = correctness.iter().flatten().sum();
    report.push_str(&format!(
        "PROBE_COMPLETE|scored_greedy_questions=48|total_exact_answers={all_correct}|all_bytes_generated_by_GGUF=YES|external_answer_engine=NO|route_context_limited=256_past_bytes|byte_predictor_order=1|json=0\n"
    ));

    // Explicit first-order Markov claim for two different questions with a
    // common suffix. Question contents never enter the shared base predictor.
    let a = question_prompt(QUESTIONS[0].0, false);
    let b = question_prompt(QUESTIONS[1].0, false);
    assert_eq!(a.as_bytes().last(), b.as_bytes().last());
    let base_a = complete(&model, &a, RoutingMode::Base, false);
    let base_b = complete(&model, &b, RoutingMode::Base, false);
    assert_eq!(base_a.bytes, base_b.bytes);
    report.push_str("PROBE_CAUSAL_COUNTEREXAMPLE|different_country_questions=France_Japan|same_final_byte=true|base_greedy_completion_identical=true|semantic_discrimination=FAIL|json=0\n");

    // Keep an unambiguous raw-byte response file for each question and arm.
    for (mode, context, id, response) in results {
        fs::write(
            output_dir.join(format!(
                "{mode}-{}-{id}.bin",
                if context == 0 { "short" } else { "long" }
            )),
            response.bytes,
        )?;
    }
    fs::write(output_dir.join("KNOWLEDGE-RESULT.hbp"), &report)?;
    print!("{report}");
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = std::env::args().collect();
    match args.as_slice() {
        [_, action, model, output] if action == "--probe" => {
            run(Path::new(model), Path::new(output))
        }
        _ => Err("usage: shared_knowledge_probe --probe FULL_TREE.gguf OUTPUT_DIR".into()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn grader_accepts_correct_short_answers_but_not_partial_words() {
        assert!(grade(b"Paris.\n", "Paris"));
        assert!(grade(b"  EINSTEIN, and others", "Einstein"));
        assert!(!grade(b"Parisian", "Paris"));
        assert!(!grade(b"Not Paris", "Paris"));
        assert!(!grade(b"Paris is the answer", "Tokyo"));
    }

    #[test]
    fn prompts_have_identical_endings_without_containing_their_answers() {
        let a = question_prompt(QUESTIONS[0].0, false);
        let b = question_prompt(QUESTIONS[1].0, false);
        assert_eq!(a.as_bytes().last(), Some(&b' '));
        assert_eq!(a.as_bytes().last(), b.as_bytes().last());
        assert!(question_prompt(QUESTIONS[0].0, true).len() > BLOCK);
        for &(question, answer) in &QUESTIONS {
            assert!(!question_prompt(question, false).contains(answer));
            assert!(!question_prompt(question, true).contains(answer));
        }
    }
}
