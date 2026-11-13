//! HEB-C-style 27-channel addressing and sparse virtual QNN state.
//!
//! Capacity is twelve billion *addresses*, never a dense allocation. Each
//! occupied address carries a 27-valued 3-trit state. The 27-coefficient
//! integer network generates a context-specific 3x3 input matrix on demand.
//! This is a discrete surrogate; it is not a physical quantum-state simulator.

#![forbid(unsafe_code)]

use crate::sha256::hex_digest;
use std::collections::BTreeMap;
use std::time::Instant;

pub const CAPACITY: u64 = 12_000_000_000;
pub const CHANNELS: u64 = 27;
pub const WIDTH: u64 = 1_024;
pub const PLANE: u64 = WIDTH * WIDTH;
pub const N_ACTIVE: usize = 4_096;
pub const TICKS: usize = 3;
pub const RUNGS: [u64; 4] = [23_887_872, 100_000_000, 1_000_000_000, CAPACITY];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Address {
    pub x: u16,
    pub y: u16,
    pub z: u16,
    pub channel: u8,
}

#[must_use]
pub fn decode_address(id: u64) -> Option<Address> {
    if id >= CAPACITY {
        return None;
    }
    let room = id / CHANNELS;
    Some(Address {
        x: (room % WIDTH) as u16,
        y: ((room / WIDTH) % WIDTH) as u16,
        z: (room / PLANE) as u16,
        channel: (id % CHANNELS) as u8,
    })
}

#[must_use]
pub fn encode_address(a: Address) -> Option<u64> {
    if u64::from(a.x) >= WIDTH || u64::from(a.y) >= WIDTH || u64::from(a.channel) >= CHANNELS {
        return None;
    }
    let room = u64::from(a.z)
        .checked_mul(PLANE)?
        .checked_add(u64::from(a.y) * WIDTH)?
        .checked_add(u64::from(a.x))?;
    let id = room
        .checked_mul(CHANNELS)?
        .checked_add(u64::from(a.channel))?;
    (id < CAPACITY).then_some(id)
}

/// All virtual addresses admit an exact 22-trit path. This is an address,
/// not a quantum amplitude and not a learned network parameter.
#[must_use]
pub fn to_path(id: u64) -> Option<[u8; 22]> {
    if id >= CAPACITY {
        return None;
    }
    let mut digits = [0_u8; 22];
    let mut left = id;
    for d in &mut digits {
        *d = (left % 3) as u8;
        left /= 3;
    }
    (left == 0).then_some(digits)
}

#[must_use]
pub fn from_path(path: &[u8; 22]) -> Option<u64> {
    let mut n = 0_u64;
    for &d in path.iter().rev() {
        if d > 2 {
            return None;
        }
        n = n.checked_mul(3)?.checked_add(u64::from(d))?;
    }
    (n < CAPACITY).then_some(n)
}

/// Direction is an HEB-C-compatible D3Q27 offset: x major, z minor.
/// Boundary or non-existent partial-final-room neighbors return None.
#[must_use]
pub fn neighbor_within(id: u64, direction: u8, capacity: u64) -> Option<u64> {
    if direction >= 27 || id >= capacity || capacity > CAPACITY {
        return None;
    }
    let a = decode_address(id)?;
    let dx = i32::from(direction / 9) - 1;
    let dy = i32::from((direction / 3) % 3) - 1;
    let dz = i32::from(direction % 3) - 1;
    let x = i32::from(a.x) + dx;
    let y = i32::from(a.y) + dy;
    let z = i32::from(a.z) + dz;
    if !(0..1_024).contains(&x) || !(0..1_024).contains(&y) || z < 0 {
        return None;
    }
    let target = encode_address(Address {
        x: x as u16,
        y: y as u16,
        z: z as u16,
        channel: a.channel,
    })?;
    (target < capacity).then_some(target)
}

/// Exactly 27 integer coefficients; no distinct matrix stored at each node.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Generator {
    base: [[i16; 3]; 3],
    low_u: [i16; 3],
    low_v: [i16; 3],
    output: [[i16; 3]; 3],
    bias: [i16; 3],
}

impl Default for Generator {
    fn default() -> Self {
        Self {
            base: [[3, -1, 2], [-2, 3, 1], [1, 2, -2]],
            low_u: [1, -1, 2],
            low_v: [1, 0, -1],
            output: [[2, -1, 0], [-1, 3, 1], [0, -2, 2]],
            bias: [1, 0, -1],
        }
    }
}

impl Generator {
    /// Compact context-dependent low-rank weight generation: B + g*u*v^T.
    #[must_use]
    pub fn matrix(&self, a: Address) -> [[i16; 3]; 3] {
        let trit_sum =
            u32::from(a.x) % 3 + u32::from(a.y) % 3 + u32::from(a.z) % 3 + u32::from(a.channel) % 3;
        let gate = (trit_sum % 3) as i16 - 1;
        let mut m = self.base;
        for (i, row) in m.iter_mut().enumerate() {
            for (j, v) in row.iter_mut().enumerate() {
                *v += gate * self.low_u[i] * self.low_v[j];
            }
        }
        m
    }

    /// An integer three-input, three-hidden, three-output neural surrogate.
    /// Neighbor states enter two inputs. Outputs are independently quantized
    /// to 0,1,2 and packed into one of 27 states.
    #[must_use]
    pub fn infer(&self, id: u64, state: u8, near_z: u8, near_y: u8) -> Option<u8> {
        if state >= 27 || near_z >= 27 || near_y >= 27 {
            return None;
        }
        let a = decode_address(id)?;
        let m = self.matrix(a);
        let input = [
            i32::from(state % 3) - 1,
            i32::from((state / 3) % 3) + i32::from(near_z % 3) - 2,
            i32::from(state / 9) + i32::from((near_y / 3) % 3) - 2,
        ];
        let mut hidden = [0_i32; 3];
        for (j, out) in hidden.iter_mut().enumerate() {
            let sum: i32 = (0..3).map(|i| input[i] * i32::from(m[i][j])).sum();
            *out = sum.max(0);
        }
        let mut packed = 0_u8;
        for j in 0..3 {
            let logit: i32 = (0..3)
                .map(|i| hidden[i] * i32::from(self.output[i][j]))
                .sum::<i32>()
                + i32::from(self.bias[j]);
            let trit = if logit < 0 {
                0
            } else if logit <= 3 {
                1
            } else {
                2
            };
            packed += trit * [1, 3, 9][j];
        }
        Some(packed)
    }

    #[must_use]
    pub fn coeff_hash(&self) -> String {
        let mut raw = Vec::with_capacity(54);
        for row in self.base {
            for w in row {
                raw.extend_from_slice(&w.to_le_bytes());
            }
        }
        for w in self.low_u.into_iter().chain(self.low_v) {
            raw.extend_from_slice(&w.to_le_bytes());
        }
        for row in self.output {
            for w in row {
                raw.extend_from_slice(&w.to_le_bytes());
            }
        }
        for w in self.bias {
            raw.extend_from_slice(&w.to_le_bytes());
        }
        assert_eq!(raw.len(), 54);
        hex_digest(&raw)
    }

    #[must_use]
    pub fn changed_one_weight(&self) -> Self {
        let mut m = *self;
        m.base[0][0] += 1;
        m
    }
}

/// State zero is implicit; only nonzero active states are actually allocated.
/// No query or step enumerates the twelve-billion-address namespace.
#[derive(Clone, Default)]
pub struct SparseNodes {
    nodes: BTreeMap<u64, u8>,
}

impl SparseNodes {
    #[must_use]
    pub fn len(&self) -> usize {
        self.nodes.len()
    }

    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.nodes.is_empty()
    }

    pub fn set(&mut self, id: u64, value: u8, capacity: u64) -> Result<(), &'static str> {
        if id >= capacity || capacity > CAPACITY || value >= 27 {
            return Err("invalid address or state");
        }
        if value == 0 {
            self.nodes.remove(&id);
        } else {
            self.nodes.insert(id, value);
        }
        Ok(())
    }

    #[must_use]
    pub fn get(&self, id: u64) -> u8 {
        self.nodes.get(&id).copied().unwrap_or(0)
    }

    /// Synchronous active-only update; no nonlinear power-of-three jump.
    /// A jump theorem has not been established for this neural surrogate.
    pub fn tick(&mut self, capacity: u64, generator: &Generator) -> usize {
        let old = self.nodes.clone();
        let mut updated = BTreeMap::new();
        for (&id, &s) in &old {
            let zn = neighbor_within(id, 14, capacity)
                .map(|near| old.get(&near).copied().unwrap_or(0))
                .unwrap_or(0);
            let yn = neighbor_within(id, 16, capacity)
                .map(|near| old.get(&near).copied().unwrap_or(0))
                .unwrap_or(0);
            let new_value = generator
                .infer(id, s, zn, yn)
                .expect("validated stored state and address");
            if new_value != 0 {
                updated.insert(id, new_value);
            }
        }
        self.nodes = updated;
        old.len()
    }

    #[must_use]
    pub fn sha256(&self) -> String {
        let mut bytes = Vec::with_capacity(self.nodes.len() * 9);
        for (&id, &state) in &self.nodes {
            bytes.extend_from_slice(&id.to_le_bytes());
            bytes.push(state);
        }
        hex_digest(&bytes)
    }
}

#[must_use]
pub fn seed_nodes(capacity: u64) -> SparseNodes {
    assert!(capacity <= CAPACITY && capacity >= 2 * N_ACTIVE as u64);
    let mut s = SparseNodes::default();
    let mut i = 0_u64;
    while s.len() < N_ACTIVE {
        let id = (i * 1_000_003) % capacity;
        let state = (id % 26 + 1) as u8;
        s.set(id, state, capacity).expect("generated valid address");
        if let Some(adjacent) = neighbor_within(id, 14, capacity) {
            if s.len() < N_ACTIVE {
                s.set(adjacent, state, capacity)
                    .expect("valid adjacent address");
            }
        }
        i += 1;
    }
    s
}

pub struct RungResult {
    pub capacity: u64,
    pub before: usize,
    pub after: usize,
    pub evaluations: usize,
    pub elapsed_microseconds: u128,
    pub digest: String,
}

#[must_use]
pub fn run_rung(capacity: u64) -> RungResult {
    assert!(RUNGS.contains(&capacity));
    let generator = Generator::default();
    let start = Instant::now();
    let mut nodes = seed_nodes(capacity);
    let before = nodes.len();
    let mut evaluations = 0;
    for _ in 0..TICKS {
        evaluations += nodes.tick(capacity, &generator);
    }
    RungResult {
        capacity,
        before,
        after: nodes.len(),
        evaluations,
        elapsed_microseconds: start.elapsed().as_micros(),
        digest: nodes.sha256(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn full_range_roundtrips_ternary_and_hebc_coordinates() {
        let probes = [0, 1, 26, 27, 1_048_576 * 27 - 1, CAPACITY - 2, CAPACITY - 1];
        for id in probes {
            assert_eq!(encode_address(decode_address(id).unwrap()), Some(id));
            assert_eq!(from_path(&to_path(id).unwrap()), Some(id));
        }
        assert_eq!(to_path(CAPACITY), None);
        assert_eq!(decode_address(CAPACITY), None);
        assert_eq!(
            encode_address(Address {
                x: 0,
                y: 0,
                z: 424,
                channel: 0
            }),
            None
        );
        assert_eq!(from_path(&[2; 22]), None);
        let mut bad_path = [0; 22];
        bad_path[11] = 3;
        assert_eq!(from_path(&bad_path), None);
    }

    #[test]
    fn bounded_neighbor_and_final_room_rejection() {
        let a = Address {
            x: 50,
            y: 50,
            z: 50,
            channel: 5,
        };
        let id = encode_address(a).unwrap();
        let z_plus = neighbor_within(id, 14, CAPACITY).unwrap();
        assert_eq!(decode_address(z_plus).unwrap().z, 51);
        let y_plus = neighbor_within(id, 16, CAPACITY).unwrap();
        assert_eq!(decode_address(y_plus).unwrap().y, 51);
        assert_eq!(neighbor_within(id, 27, CAPACITY), None);
        assert_eq!(neighbor_within(CAPACITY - 1, 14, CAPACITY), None);
        assert_eq!(neighbor_within(0, 0, CAPACITY), None);
        assert_eq!(neighbor_within(id, 13, CAPACITY), Some(id));
    }

    #[test]
    fn generator_is_contextual_integer_only_and_tamper_sensitive() {
        let generator = Generator::default();
        let a = Address {
            x: 4,
            y: 4,
            z: 4,
            channel: 0,
        };
        let b = Address {
            x: 5,
            y: 4,
            z: 4,
            channel: 0,
        };
        assert_ne!(generator.matrix(a), generator.matrix(b));
        assert_ne!(
            generator.coeff_hash(),
            generator.changed_one_weight().coeff_hash()
        );
        let id = encode_address(a).unwrap();
        for s in 0..27 {
            let v = generator.infer(id, s, 1, 2).unwrap();
            assert!(v < 27);
            assert_eq!(v, generator.infer(id, s, 1, 2).unwrap());
        }
        assert_eq!(generator.infer(id, 27, 0, 0), None);
        assert_eq!(generator.infer(CAPACITY, 1, 0, 0), None);
    }

    #[test]
    fn sparse_replay_does_real_updates_without_dense_allocation() {
        let generator = Generator::default();
        for capacity in RUNGS {
            let original = seed_nodes(capacity);
            assert_eq!(original.len(), N_ACTIVE);
            let mut a = original.clone();
            let mut b = original;
            let mut count = 0;
            for _ in 0..TICKS {
                count += a.tick(capacity, &generator);
                b.tick(capacity, &generator);
            }
            assert!(count > 0);
            assert!(count <= TICKS * N_ACTIVE);
            assert_eq!(a.sha256(), b.sha256());
            assert!(a.len() <= N_ACTIVE);
            assert!(a.nodes.keys().all(|id| *id < capacity));
        }
    }

    #[test]
    fn actual_nearby_nodes_change_updated_neural_state() {
        let generator = Generator::default();
        let center = encode_address(Address {
            x: 0,
            y: 3,
            z: 3,
            channel: 0,
        })
        .unwrap();
        let near_z = neighbor_within(center, 14, CAPACITY).unwrap();
        let near_y = neighbor_within(center, 16, CAPACITY).unwrap();
        let mut without = SparseNodes::default();
        without.set(center, 1, CAPACITY).unwrap();
        without.set(near_y, 3, CAPACITY).unwrap();
        let mut with = without.clone();
        with.set(near_z, 2, CAPACITY).unwrap();
        assert_eq!(generator.infer(center, 1, 0, 3), Some(2));
        assert_eq!(generator.infer(center, 1, 2, 3), Some(1));
        without.tick(CAPACITY, &generator);
        with.tick(CAPACITY, &generator);
        assert_eq!(without.get(center), 2);
        assert_eq!(with.get(center), 1);
    }

    #[test]
    fn active_memory_and_negative_controls() {
        let capacity = CAPACITY;
        let mut nodes = SparseNodes::default();
        nodes.set(27, 1, capacity).unwrap();
        assert_eq!(nodes.get(27), 1);
        assert!(nodes.set(CAPACITY, 1, capacity).is_err());
        assert!(nodes.set(27, 27, capacity).is_err());
        let before = nodes.sha256();
        nodes.set(27, 2, capacity).unwrap();
        assert_ne!(nodes.sha256(), before);
        nodes.set(27, 0, capacity).unwrap();
        assert!(nodes.is_empty());
        assert_eq!(nodes.get(27), 0);
    }
}
