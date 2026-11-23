//! Unsigned 256-bit integers for the block sums whose terms are fourth powers at 2^160 (exact; no float).

use std::fmt;

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct U256([u64; 4]);

impl U256 {
    pub const ZERO: U256 = U256([0; 4]);

    pub fn from_u128(x: u128) -> Self {
        U256([x as u64, (x >> 64) as u64, 0, 0])
    }

    /// The exact product of two u128.
    pub fn mul_u128(a: u128, b: u128) -> Self {
        let x = [a as u64, (a >> 64) as u64];
        let y = [b as u64, (b >> 64) as u64];
        let mut r = [0u64; 4];
        for (i, &xi) in x.iter().enumerate() {
            let mut carry: u128 = 0;
            for (j, &yj) in y.iter().enumerate() {
                let t = u128::from(xi) * u128::from(yj) + u128::from(r[i + j]) + carry;
                r[i + j] = t as u64;
                carry = t >> 64;
            }
            r[i + 2] = carry as u64;
        }
        U256(r)
    }

    pub fn checked_add(self, o: U256) -> Option<U256> {
        let mut r = [0u64; 4];
        let mut carry: u128 = 0;
        for (k, slot) in r.iter_mut().enumerate() {
            let t = u128::from(self.0[k]) + u128::from(o.0[k]) + carry;
            *slot = t as u64;
            carry = t >> 64;
        }
        if carry == 0 {
            Some(U256(r))
        } else {
            None
        }
    }
}

impl fmt::Display for U256 {
    fn fmt(&self, out: &mut fmt::Formatter<'_>) -> fmt::Result {
        const D: u128 = 10_000_000_000_000_000_000;
        let mut limbs = self.0;
        if limbs == [0; 4] {
            return write!(out, "0");
        }
        let mut parts: Vec<u64> = Vec::new();
        while limbs != [0; 4] {
            let mut rem: u128 = 0;
            for limb in limbs.iter_mut().rev() {
                let cur = (rem << 64) | u128::from(*limb);
                *limb = (cur / D) as u64;
                rem = cur % D;
            }
            parts.push(rem as u64);
        }
        let mut it = parts.iter().rev();
        if let Some(first) = it.next() {
            write!(out, "{first}")?;
        }
        for p in it {
            write!(out, "{p:019}")?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn small_products_match_u128() {
        let vals = [
            0u128,
            1,
            7,
            12345,
            u64::MAX as u128,
            1u128 << 70,
            (1u128 << 100) + 9,
        ];
        for &a in &vals {
            for &b in &vals {
                if let Some(p) = a.checked_mul(b) {
                    assert_eq!(U256::mul_u128(a, b).to_string(), p.to_string());
                }
            }
        }
    }

    #[test]
    fn largest_square_in_decimal() {
        // (2^128 - 1)^2 = 2^256 - 2^129 + 1.
        assert_eq!(
            U256::mul_u128(u128::MAX, u128::MAX).to_string(),
            "115792089237316195423570985008687907852589419931798687112530834793049593217025"
        );
    }

    #[test]
    fn addition_carries_and_overflow_is_reported() {
        let a = U256::from_u128(u128::MAX);
        let b = U256::from_u128(1);
        assert_eq!(
            a.checked_add(b).map(|v| v.to_string()),
            Some("340282366920938463463374607431768211456".to_string())
        );
        let top = U256::mul_u128(u128::MAX, u128::MAX);
        let mut huge = top;
        for _ in 0..3 {
            huge = huge.checked_add(top).unwrap_or(U256::ZERO);
        }
        assert_eq!(huge, U256::ZERO);
    }
}
