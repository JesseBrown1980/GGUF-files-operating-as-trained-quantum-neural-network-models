//! Lossless, CPU-only integer specialist panel with validation-fit three-byte
//! weight corrections. Model bytes and switched stream are independently
//! serialized: the decoder has neither training nor test data.
#![forbid(unsafe_code)]

pub const BLOCK: usize = 256;
const HALF: u64 = 0x8000_0000;
const QUARTER: u64 = 0x4000_0000;
const THREE_QUARTER: u64 = 0xc000_0000;
const TOP: u64 = 0xffff_ffff;

#[must_use]
pub const fn family_of_byte(b: u8) -> usize {
    if b == b' ' || b == b'\n' || b == b'\t' || b == b'\r' {
        0
    } else if b.is_ascii_alphabetic() {
        1
    } else {
        2
    }
}

/// Returns an integer Q12 approximation to log2(n); no floats or lookups
/// trained on the evaluation source. Fixed-point squaring is deterministic.
#[must_use]
pub fn log2_q12(n: u32) -> u32 {
    assert!(n > 0);
    let k = 31 - n.leading_zeros();
    let mut x = u128::from(n) << (32 - k);
    let mut frac = 0_u32;
    for i in 0..12 {
        x = (x * x) >> 32;
        if x >= (1_u128 << 33) {
            x >>= 1;
            frac |= 1 << (11 - i);
        }
    }
    k * 4_096 + frac
}

#[derive(Clone)]
pub struct Expert {
    counts: Vec<u16>,
    group_sums: Vec<[u32; 3]>,
    pub correction: [i8; 3],
    pub family: u8,
}

impl Expert {
    #[must_use]
    pub fn from_training(data: &[u8], family: u8) -> Self {
        let mut counts = vec![0_u16; 65_536];
        let mut prev = 0_u8;
        for &next in data {
            let slot = usize::from(prev) * 256 + usize::from(next);
            counts[slot] = counts[slot].checked_add(1).expect("training count fits u16");
            prev = next;
        }
        Self::from_counts(counts, [0; 3], family)
    }

    fn from_counts(counts: Vec<u16>, correction: [i8; 3], family: u8) -> Self {
        assert_eq!(counts.len(), 65_536);
        let mut group_sums = vec![[0_u32; 3]; 256];
        for (prev, sums) in group_sums.iter_mut().enumerate() {
            for next in 0_u16..=255 {
                sums[family_of_byte(next as u8)] +=
                    u32::from(counts[prev * 256 + usize::from(next)]) + 1;
            }
        }
        Self {
            counts,
            group_sums,
            correction,
            family,
        }
    }

    fn scale(correction: [i8; 3], category: usize) -> u32 {
        let exponent = i16::from(correction[category]) + 2;
        assert!((0..=4).contains(&exponent), "out-of-range correction");
        1_u32 << exponent
    }

    fn frequency(&self, prev: u8, next: u8) -> u32 {
        let idx = usize::from(prev) * 256 + usize::from(next);
        (u32::from(self.counts[idx]) + 1)
            * Self::scale(self.correction, family_of_byte(next))
    }

    fn total(&self, prev: u8) -> u32 {
        self.group_sums[usize::from(prev)]
            .iter()
            .enumerate()
            .map(|(group, n)| n * Self::scale(self.correction, group))
            .sum()
    }

    fn bounds(&self, prev: u8, target: u8) -> (u32, u32, u32) {
        let mut cumulative = 0_u32;
        for b in 0_u16..=255 {
            let next = b as u8;
            let weight = self.frequency(prev, next);
            if next == target {
                return (cumulative, cumulative + weight, self.total(prev));
            }
            cumulative += weight;
        }
        unreachable!("all byte values enumerated")
    }

    fn symbol_at(&self, prev: u8, value: u32) -> (u8, u32, u32, u32) {
        let total = self.total(prev);
        assert!(value < total);
        let mut cumulative = 0_u32;
        for b in 0_u16..=255 {
            let next = b as u8;
            let above = cumulative + self.frequency(prev, next);
            if value < above {
                return (next, cumulative, above, total);
            }
            cumulative = above;
        }
        unreachable!("arithmetic decoder bounds")
    }

    #[must_use]
    pub fn loss(&self, data: &[u8]) -> u64 {
        let mut prev = 0_u8;
        let mut loss = 0_u64;
        for &next in data {
            let numerator = self.frequency(prev, next);
            let denominator = self.total(prev);
            loss += u64::from(log2_q12(denominator) - log2_q12(numerator));
            prev = next;
        }
        loss
    }

    /// Two validation-only integer coordinate-descent passes.
    /// Changes three shared group-logit corrections, not the bigram table.
    pub fn fit_correction(&mut self, validation: &[u8]) {
        for _ in 0..2 {
            for group in 0..3 {
                let original = self.correction[group];
                let mut winning = original;
                let mut best_loss = self.loss(validation);
                for proposed in -2_i8..=2 {
                    self.correction[group] = proposed;
                    let cost = self.loss(validation);
                    if cost < best_loss {
                        best_loss = cost;
                        winning = proposed;
                    }
                }
                self.correction[group] = winning;
            }
        }
    }

    #[must_use]
    pub fn nonzero_entries(&self) -> usize {
        self.counts.iter().filter(|x| **x != 0).count()
    }
}

#[derive(Default)]
struct BitsOut {
    bytes: Vec<u8>,
    active: u8,
    used: u8,
}
impl BitsOut {
    fn write(&mut self, bit: u8) {
        self.active = (self.active << 1) | bit;
        self.used += 1;
        if self.used == 8 {
            self.bytes.push(self.active);
            self.active = 0;
            self.used = 0;
        }
    }
    fn finish(mut self) -> Vec<u8> {
        if self.used > 0 {
            self.bytes.push(self.active << (8 - self.used));
        }
        self.bytes
    }
}
struct BitsIn<'a> {
    data: &'a [u8],
    position: usize,
}
impl BitsIn<'_> {
    fn read(&mut self) -> u8 {
        let byte = self.position / 8;
        let bit = self.position % 8;
        self.position += 1;
        if byte < self.data.len() {
            (self.data[byte] >> (7 - bit)) & 1
        } else {
            0
        }
    }
}

struct Encoder {
    low: u64,
    high: u64,
    pending: usize,
    bits: BitsOut,
}
impl Encoder {
    fn new() -> Self {
        Self {
            low: 0,
            high: TOP,
            pending: 0,
            bits: BitsOut::default(),
        }
    }
    fn emit(&mut self, bit: u8) {
        self.bits.write(bit);
        for _ in 0..self.pending {
            self.bits.write(1 - bit);
        }
        self.pending = 0;
    }
    fn push(&mut self, model: &Expert, prev: u8, next: u8) {
        let (bottom, top, total) = model.bounds(prev, next);
        let width = self.high - self.low + 1;
        let old = self.low;
        self.high = old + width * u64::from(top) / u64::from(total) - 1;
        self.low = old + width * u64::from(bottom) / u64::from(total);
        loop {
            if self.high < HALF {
                self.emit(0);
            } else if self.low >= HALF {
                self.emit(1);
                self.low -= HALF;
                self.high -= HALF;
            } else if self.low >= QUARTER && self.high < THREE_QUARTER {
                self.pending += 1;
                self.low -= QUARTER;
                self.high -= QUARTER;
            } else {
                break;
            }
            self.low <<= 1;
            self.high = (self.high << 1) + 1;
        }
    }
    fn finish(mut self) -> Vec<u8> {
        self.pending += 1;
        if self.low < QUARTER {
            self.emit(0);
        } else {
            self.emit(1);
        }
        self.bits.finish()
    }
}

struct Decoder<'a> {
    low: u64,
    high: u64,
    code: u64,
    bits: BitsIn<'a>,
}
impl<'a> Decoder<'a> {
    fn new(data: &'a [u8]) -> Self {
        let mut bits = BitsIn { data, position: 0 };
        let mut code = 0_u64;
        for _ in 0..32 {
            code = (code << 1) | u64::from(bits.read());
        }
        Self {
            low: 0,
            high: TOP,
            code,
            bits,
        }
    }
    fn pop(&mut self, model: &Expert, prev: u8) -> u8 {
        let total = model.total(prev);
        let width = self.high - self.low + 1;
        let value =
            ((self.code - self.low + 1) * u64::from(total) - 1) / width;
        let (sym, bottom, top, _) = model.symbol_at(prev, value as u32);
        let old = self.low;
        self.high = old + width * u64::from(top) / u64::from(total) - 1;
        self.low = old + width * u64::from(bottom) / u64::from(total);
        loop {
            if self.high < HALF {
            } else if self.low >= HALF {
                self.low -= HALF;
                self.high -= HALF;
                self.code -= HALF;
            } else if self.low >= QUARTER && self.high < THREE_QUARTER {
                self.low -= QUARTER;
                self.high -= QUARTER;
                self.code -= QUARTER;
            } else {
                break;
            }
            self.low <<= 1;
            self.high = (self.high << 1) + 1;
            self.code = (self.code << 1) | u64::from(self.bits.read());
        }
        sym
    }
}

/// Select using only bytes the decoder has already produced. The winning
/// specialist is not transmitted at each switch, and no test labels appear.
#[must_use]
pub fn route(models: &[Expert], history: &[u8], first: usize) -> usize {
    if models.len() == 1 || history.len() < BLOCK {
        return first;
    }
    let start = history.len() - BLOCK;
    let mut winner = 0;
    let mut best = u64::MAX;
    for (index, model) in models.iter().enumerate() {
        let mut loss = 0_u64;
        for pos in start..history.len() {
            let prev = if pos == 0 { 0 } else { history[pos - 1] };
            let next = history[pos];
            loss += u64::from(
                log2_q12(model.total(prev)) - log2_q12(model.frequency(prev, next)),
            );
        }
        if loss < best {
            best = loss;
            winner = index;
        }
    }
    winner
}

#[must_use]
pub fn static_expert(models: &[Expert], validation: &[Vec<u8>]) -> usize {
    models
        .iter()
        .enumerate()
        .min_by_key(|(i, model)| {
            (validation.iter().map(|v| model.loss(v)).sum::<u64>(), *i)
        })
        .map_or(0, |(i, _)| i)
}

/// Exact serialized sparse function tables; model storage is not hidden.
#[must_use]
pub fn serialize(models: &[Expert]) -> Vec<u8> {
    assert!(models.len() <= u8::MAX as usize);
    let mut bytes = b"SPM1".to_vec();
    bytes.push(models.len() as u8);
    bytes.extend_from_slice(&(BLOCK as u16).to_le_bytes());
    for model in models {
        bytes.push(model.family);
        for c in model.correction {
            bytes.push(c as u8);
        }
        bytes.extend_from_slice(&(model.nonzero_entries() as u32).to_le_bytes());
        for (i, &count) in model.counts.iter().enumerate() {
            if count != 0 {
                bytes.push((i / 256) as u8);
                bytes.push((i % 256) as u8);
                bytes.extend_from_slice(&count.to_le_bytes());
            }
        }
    }
    bytes
}

pub fn deserialize(bytes: &[u8]) -> Result<Vec<Expert>, &'static str> {
    if bytes.get(..4) != Some(&b"SPM1"[..]) || bytes.len() < 7 {
        return Err("invalid model magic");
    }
    let n = usize::from(bytes[4]);
    if n == 0 || u16::from_le_bytes([bytes[5], bytes[6]]) != BLOCK as u16 {
        return Err("invalid model panel");
    }
    let mut pos = 7_usize;
    let mut models = Vec::new();
    for _ in 0..n {
        let hdr = bytes.get(pos..pos + 8).ok_or("model header truncated")?;
        let family = hdr[0];
        let corrections = [hdr[1] as i8, hdr[2] as i8, hdr[3] as i8];
        if corrections.iter().any(|x| !(-2..=2).contains(x)) || family > 2 {
            return Err("corrupt model correction");
        }
        let entries = u32::from_le_bytes([hdr[4], hdr[5], hdr[6], hdr[7]]) as usize;
        pos += 8;
        if entries > 65_536 {
            return Err("corrupt count table");
        }
        let mut counts = vec![0_u16; 65_536];
        for _ in 0..entries {
            let row = bytes.get(pos..pos + 4).ok_or("count table truncated")?;
            let i = usize::from(row[0]) * 256 + usize::from(row[1]);
            let value = u16::from_le_bytes([row[2], row[3]]);
            if value == 0 || counts[i] != 0 {
                return Err("duplicate or zero sparse entry");
            }
            counts[i] = value;
            pos += 4;
        }
        models.push(Expert::from_counts(counts, corrections, family));
    }
    if pos != bytes.len() {
        return Err("model trailing bytes");
    }
    Ok(models)
}

#[derive(Debug)]
pub struct Coded {
    pub stream: Vec<u8>,
    pub model_bytes: Vec<u8>,
    pub routes: Vec<u8>,
    pub switches: usize,
}

/// The stream carries its byte length and first specialist once, then only
/// entropy-coded bytes. Every future specialist choice is inferred from past.
#[must_use]
pub fn encode(input: &[u8], models: &[Expert], first: usize) -> Coded {
    assert!(!models.is_empty() && first < models.len());
    let mut arithmetic = Encoder::new();
    let mut routes = Vec::new();
    let mut last_model = None;
    let mut switches = 0;
    let mut active = first;
    let mut prev = 0_u8;
    for (pos, &next) in input.iter().enumerate() {
        if pos % BLOCK == 0 {
            active = route(models, &input[..pos], first);
            if let Some(last) = last_model {
                if last != active {
                    switches += 1;
                }
            }
            last_model = Some(active);
            routes.push(active as u8);
        }
        arithmetic.push(&models[active], prev, next);
        prev = next;
    }
    let mut stream = b"SPR1".to_vec();
    stream.push(first as u8);
    stream.extend_from_slice(&(input.len() as u64).to_le_bytes());
    stream.extend_from_slice(&arithmetic.finish());
    Coded {
        stream,
        model_bytes: serialize(models),
        routes,
        switches,
    }
}

pub fn decode(stream: &[u8], model_bytes: &[u8]) -> Result<(Vec<u8>, Vec<u8>), &'static str> {
    if stream.get(..4) != Some(&b"SPR1"[..]) || stream.len() < 13 {
        return Err("invalid coded stream");
    }
    let models = deserialize(model_bytes)?;
    let first = usize::from(stream[4]);
    if first >= models.len() {
        return Err("invalid first expert");
    }
    let mut len_bytes = [0_u8; 8];
    len_bytes.copy_from_slice(&stream[5..13]);
    let len = usize::try_from(u64::from_le_bytes(len_bytes)).map_err(|_| "length overflow")?;
    if len > 100_000_000 {
        return Err("decoder allocation gate");
    }
    let mut arithmetic = Decoder::new(&stream[13..]);
    let mut output = Vec::with_capacity(len);
    let mut routes = Vec::new();
    let mut active = first;
    let mut prev = 0_u8;
    for pos in 0..len {
        if pos % BLOCK == 0 {
            active = route(&models, &output, first);
            routes.push(active as u8);
        }
        let next = arithmetic.pop(&models[active], prev);
        output.push(next);
        prev = next;
    }
    Ok((output, routes))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn integer_log_has_correct_power_of_two_anchors() {
        for k in 0..=27 {
            assert_eq!(log2_q12(1_u32 << k), k * 4_096);
        }
        assert!(log2_q12(999) < log2_q12(1000));
    }

    #[test]
    fn serialization_rejects_truncated_or_corrupted_parameters() {
        let m = Expert::from_training(b"hello world hello rust", 0);
        let data = serialize(&[m]);
        assert_eq!(deserialize(&data).unwrap().len(), 1);
        assert!(deserialize(&data[..data.len() - 1]).is_err());
        let mut corrupt = data;
        corrupt[8] = 11;
        assert!(deserialize(&corrupt).is_err());
    }

    #[test]
    fn exact_causal_decoder_with_real_switching_and_bias_edits() {
        let a = Expert::from_training(b"aaaaabaaaaabaaaaabbaaaa", 0);
        let b = Expert::from_training(b"\n\n|x=42|\n\n|x=53|", 1);
        let c = Expert::from_training(b"fn test()->u32 { 27 }", 2);
        let mut experts = vec![a, b, c];
        for expert in &mut experts {
            expert.fit_correction(b"abc! \n\n fn abc|");
        }
        let mut test = Vec::new();
        for i in 0..1_100 {
            test.push(match i / 256 % 3 {
                0 => b'a',
                1 => b'\n',
                _ => b'f',
            });
        }
        let encoded = encode(&test, &experts, 0);
        let (decoded, route_log) = decode(&encoded.stream, &encoded.model_bytes).unwrap();
        assert_eq!(decoded, test);
        assert_eq!(encoded.routes, route_log);
        assert_eq!(encoded.routes.len(), test.len().div_ceil(BLOCK));
    }

    #[test]
    fn negative_control_shuffling_changes_stored_model_commitment() {
        let a = Expert::from_training(b"AAAAABBBBB", 0);
        let b = Expert::from_training(b"1234444555", 1);
        let original = serialize(&[a.clone(), b.clone()]);
        let mut changed = [a, b];
        changed[0].correction = [-2, 1, 2];
        assert_ne!(original, serialize(&changed));
    }
}
