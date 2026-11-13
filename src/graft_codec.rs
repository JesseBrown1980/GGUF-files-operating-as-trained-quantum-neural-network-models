//! Exact integer arithmetic stream for shared model plus sparse graft heads.
//! Encoder and decoder independently derive every parent and leaf choice.
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

use crate::sha256::digest;
use crate::shared_graft::{Graft, Router, RoutingMode, BLOCK};

const HALF: u64 = 0x8000_0000;
const QUARTER: u64 = 0x4000_0000;
const THREE_QUARTERS: u64 = 0xc000_0000;
const TOP: u64 = 0xffff_ffff;
const HEADER_LEN: usize = 111;

#[derive(Default)]
struct BitsOut {
    data: Vec<u8>,
    current: u8,
    used: u8,
}
impl BitsOut {
    fn bit(&mut self, bit: u8) {
        self.current = (self.current << 1) | bit;
        self.used += 1;
        if self.used == 8 {
            self.data.push(self.current);
            self.current = 0;
            self.used = 0;
        }
    }
    fn finish(mut self) -> Vec<u8> {
        if self.used > 0 {
            self.data.push(self.current << (8 - self.used));
        }
        self.data
    }
}
struct BitsIn<'a> {
    data: &'a [u8],
    pos: usize,
}
impl BitsIn<'_> {
    fn bit(&mut self) -> u8 {
        let index = self.pos / 8;
        let shift = 7 - self.pos % 8;
        self.pos += 1;
        self.data.get(index).map_or(0, |b| (b >> shift) & 1)
    }
}

struct Encoder {
    low: u64,
    high: u64,
    pending: usize,
    out: BitsOut,
}
impl Encoder {
    fn new() -> Self {
        Self {
            low: 0,
            high: TOP,
            pending: 0,
            out: BitsOut::default(),
        }
    }
    fn emit(&mut self, bit: u8) {
        self.out.bit(bit);
        for _ in 0..self.pending {
            self.out.bit(1 - bit);
        }
        self.pending = 0;
    }
    fn push(&mut self, lo: u32, hi: u32, total: u32) {
        assert!(lo < hi && hi <= total && total <= (1 << 20));
        let span = self.high - self.low + 1;
        let previous = self.low;
        self.high = previous + span * u64::from(hi) / u64::from(total) - 1;
        self.low = previous + span * u64::from(lo) / u64::from(total);
        assert!(self.low <= self.high, "probability underflow");
        loop {
            if self.high < HALF {
                self.emit(0);
            } else if self.low >= HALF {
                self.emit(1);
                self.low -= HALF;
                self.high -= HALF;
            } else if self.low >= QUARTER && self.high < THREE_QUARTERS {
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
        self.emit(if self.low < QUARTER { 0 } else { 1 });
        self.out.finish()
    }
}

struct Decoder<'a> {
    low: u64,
    high: u64,
    code: u64,
    input: BitsIn<'a>,
}
impl<'a> Decoder<'a> {
    fn new(data: &'a [u8]) -> Self {
        let mut input = BitsIn { data, pos: 0 };
        let mut code = 0_u64;
        for _ in 0..32 {
            code = (code << 1) | u64::from(input.bit());
        }
        Self {
            low: 0,
            high: TOP,
            code,
            input,
        }
    }

    fn value(&self, total: u32) -> u32 {
        let span = self.high - self.low + 1;
        (((self.code - self.low + 1) * u64::from(total) - 1) / span) as u32
    }

    fn advance(&mut self, lo: u32, hi: u32, total: u32) {
        let span = self.high - self.low + 1;
        let previous = self.low;
        self.high = previous + span * u64::from(hi) / u64::from(total) - 1;
        self.low = previous + span * u64::from(lo) / u64::from(total);
        loop {
            if self.high < HALF {
            } else if self.low >= HALF {
                self.low -= HALF;
                self.high -= HALF;
                self.code -= HALF;
            } else if self.low >= QUARTER && self.high < THREE_QUARTERS {
                self.low -= QUARTER;
                self.high -= QUARTER;
                self.code -= QUARTER;
            } else {
                break;
            }
            self.low <<= 1;
            self.high = (self.high << 1) + 1;
            self.code = (self.code << 1) | u64::from(self.input.bit());
        }
    }
}

pub struct Encoded {
    pub stream: Vec<u8>,
    pub routes: Vec<u16>,
    pub parent_switches: usize,
    pub total_switches: usize,
}

#[must_use]
pub fn encode(input: &[u8], model_bytes: &[u8], mode: RoutingMode) -> Encoded {
    let model = Graft::from_gguf(model_bytes).expect("validated graft GGUF");
    let mut router = Router::new(&model, mode);
    let initial = router.active;
    let mut arithmetic = Encoder::new();
    let mut prev = 0_u8;
    let mut routes = Vec::with_capacity(input.len().div_ceil(BLOCK));
    let mut parent_switches = 0;
    let mut last_parent = initial / 81;
    for (index, &next) in input.iter().enumerate() {
        if index % BLOCK == 0 {
            let slot = router.select(&model, &input[..index], mode);
            if slot / 81 != last_parent {
                parent_switches += 1;
                last_parent = slot / 81;
            }
            routes.push(slot as u16);
        }
        let (lo, hi, total) = model
            .backbone
            .bounds(prev, next, model.shifts(router.active, mode));
        arithmetic.push(lo, hi, total);
        prev = next;
    }
    let payload = arithmetic.finish();
    let mut stream = b"SGS1".to_vec();
    stream.push(mode.id());
    stream.extend_from_slice(&(initial as u16).to_le_bytes());
    stream.extend_from_slice(&(input.len() as u64).to_le_bytes());
    stream.extend_from_slice(&digest(model_bytes));
    stream.extend_from_slice(&digest(input));
    stream.extend_from_slice(&digest(&payload));
    assert_eq!(stream.len(), HEADER_LEN);
    stream.extend_from_slice(&payload);
    Encoded {
        stream,
        routes,
        parent_switches,
        total_switches: router.switches,
    }
}

pub fn decode(raw: &[u8], model_bytes: &[u8]) -> Result<(Vec<u8>, Vec<u16>), &'static str> {
    if raw.len() < HEADER_LEN || raw.get(..4) != Some(&b"SGS1"[..]) {
        return Err("bad stream magic or length");
    }
    let mode = RoutingMode::parse(raw[4])?;
    let first = u16::from_le_bytes([raw[5], raw[6]]) as usize;
    let mut length_bytes = [0_u8; 8];
    length_bytes.copy_from_slice(&raw[7..15]);
    let n = usize::try_from(u64::from_le_bytes(length_bytes)).map_err(|_| "length overflow")?;
    if n > 100_000_000 {
        return Err("decoder allocation limit");
    }
    if raw[15..47] != digest(model_bytes) || raw[79..111] != digest(&raw[HEADER_LEN..]) {
        return Err("model or stream hash mismatch");
    }
    let model = Graft::from_gguf(model_bytes)?;
    if mode == RoutingMode::Tree && model.learned_leaves() == 0 {
        return Err("no trained leaves");
    }
    if mode == RoutingMode::Parents && model.learned_parents() == 0 {
        return Err("no trained parent");
    }
    let mut router = Router::new(&model, mode);
    if router.active != first {
        return Err("unexpected initial slot");
    }
    let mut arithmetic = Decoder::new(&raw[HEADER_LEN..]);
    let mut output = Vec::with_capacity(n);
    let mut routes = Vec::with_capacity(n.div_ceil(BLOCK));
    let mut prev = 0_u8;
    for index in 0..n {
        if index % BLOCK == 0 {
            routes.push(router.select(&model, &output, mode) as u16);
        }
        let weights = model.shifts(router.active, mode);
        let total = model.backbone.bounds(prev, 0, weights).2;
        let value = arithmetic.value(total);
        let (next, lo, hi, _) = model.backbone.symbol_at(prev, value, weights);
        arithmetic.advance(lo, hi, total);
        output.push(next);
        prev = next;
    }
    if raw[47..79] != digest(&output) {
        return Err("decoded content hash mismatch");
    }
    Ok((output, routes))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::shared_graft::{Counts, Graft};

    fn sample_model() -> Vec<u8> {
        let mut counts = Counts::new();
        counts.add_file(b"abcabcabc\nHELLO123").unwrap();
        let mut g = Graft::new(counts.finish(), 1);
        g.parents[0] = Some([2, -2, 0]);
        g.parents[80] = Some([-2, 2, 0]);
        g.leaves[0] = Some([1, 0, -1]);
        g.leaves[1] = Some([-2, 1, 2]);
        g.leaves[6560] = Some([0, 1, 0]);
        g.gguf()
    }

    #[test]
    fn independent_model_stream_roundtrip_and_hash_attacks() {
        let model = sample_model();
        let input = b"abcabcabcHELLO123\n\n9999999990000000000".repeat(100);
        for mode in [RoutingMode::Base, RoutingMode::Parents, RoutingMode::Tree] {
            let encoded = encode(&input, &model, mode);
            let (decoded, routes) = decode(&encoded.stream, &model).unwrap();
            assert_eq!(decoded, input);
            assert_eq!(routes, encoded.routes);
            let mut tampered = encoded.stream.clone();
            let n = tampered.len() - 1;
            tampered[n] ^= 1;
            assert!(decode(&tampered, &model).is_err());
            let mut bad_model = model.clone();
            bad_model[0] ^= 1;
            assert!(decode(&encoded.stream, &bad_model).is_err());
        }
    }
}
