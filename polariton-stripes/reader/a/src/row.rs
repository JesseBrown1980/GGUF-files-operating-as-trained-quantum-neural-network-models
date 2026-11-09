//! Rows `KIND|key=value|...|json=0`: the exact key sequence of each kind, and canonical integers.

use crate::Stop;
use std::str::FromStr;

/// The values of a row in order, after checking its kind and that its keys are exactly `keys` in order.
pub fn values<'a, S: AsRef<str>>(
    line: &'a str,
    kind: &str,
    keys: &[S],
) -> Result<Vec<&'a str>, Stop> {
    let mut it = line.split('|');
    let found = it.next().unwrap_or("");
    if found != kind {
        return Err(Stop::new(
            "row_kind",
            format!("expected={kind},found={found}"),
        ));
    }
    let mut out = Vec::with_capacity(keys.len());
    for want in keys {
        let want = want.as_ref();
        let tok = it
            .next()
            .ok_or_else(|| Stop::new("row_short", format!("kind={kind},missing={want}")))?;
        let (key, val) = tok.split_once('=').ok_or_else(|| {
            Stop::new(
                "row_field_without_value",
                format!("kind={kind},token={tok}"),
            )
        })?;
        if key != want {
            return Err(Stop::new(
                "row_key",
                format!("kind={kind},expected={want},found={key}"),
            ));
        }
        out.push(val);
    }
    if let Some(extra) = it.next() {
        return Err(Stop::new("row_long", format!("kind={kind},extra={extra}")));
    }
    Ok(out)
}

/// The row kind (text before the first '|').
pub fn kind(line: &str) -> &str {
    line.split('|').next().unwrap_or("")
}

/// An integer written canonically (no sign on zero, no '+', no leading zeros), as the engine prints it.
pub fn int<T: FromStr + ToString>(s: &str, what: &str) -> Result<T, Stop> {
    match s.parse::<T>() {
        Ok(v) if v.to_string() == s => Ok(v),
        _ => Err(Stop::new("bad_integer", format!("field={what},text={s}"))),
    }
}

/// K canonical integers separated by `sep`.
pub fn ints<T: FromStr + ToString + Copy + Default, const K: usize>(
    s: &str,
    sep: char,
    what: &str,
) -> Result<[T; K], Stop> {
    let mut out = [T::default(); K];
    let mut it = s.split(sep);
    for slot in out.iter_mut() {
        let tok = it
            .next()
            .ok_or_else(|| Stop::new("bad_list", format!("field={what},text={s}")))?;
        *slot = int::<T>(tok, what)?;
    }
    if it.next().is_some() {
        return Err(Stop::new("bad_list", format!("field={what},text={s}")));
    }
    Ok(out)
}

/// The value must equal `want` exactly.
pub fn same(what: &str, got: &str, want: &str) -> Result<(), Stop> {
    if got == want {
        Ok(())
    } else {
        Err(Stop::new(
            "field_value",
            format!("field={what},stream={got},expected={want}"),
        ))
    }
}

/// A rational "p/q" or "p" (q > 0) in the guard's text form; returns whether it is zero.
pub fn rational_is_zero(s: &str, what: &str) -> Result<bool, Stop> {
    let (p, q) = match s.split_once('/') {
        Some((a, b)) => (a, b),
        None => (s, "1"),
    };
    let bad = || Stop::new("bad_rational", format!("field={what},text={s}"));
    let p: i128 = p.parse().map_err(|_| bad())?;
    let q: i128 = q.parse().map_err(|_| bad())?;
    if q <= 0 {
        return Err(bad());
    }
    Ok(p == 0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_integers_only() {
        assert_eq!(int::<i64>("-12", "x").ok(), Some(-12));
        assert_eq!(int::<i64>("0", "x").ok(), Some(0));
        for bad in ["-0", "+3", "007", "", " 1", "1 ", "1e3", "--1"] {
            assert!(int::<i64>(bad, "x").is_err(), "{bad}");
        }
        assert!(int::<u64>("-1", "x").is_err());
        assert_eq!(ints::<i64, 3>("1:-2:3", ':', "x").ok(), Some([1, -2, 3]));
        assert!(ints::<i64, 3>("1:-2", ':', "x").is_err());
        assert!(ints::<i64, 3>("1:-2:3:4", ':', "x").is_err());
    }

    #[test]
    fn keys_in_exact_order() {
        let keys = ["a", "b", "json"];
        assert_eq!(
            values("K|a=1|b=x=y|json=0", "K", &keys).ok(),
            Some(vec!["1", "x=y", "0"])
        );
        assert!(values("K|b=1|a=2|json=0", "K", &keys).is_err());
        assert!(values("K|a=1|b=2", "K", &keys).is_err());
        assert!(values("K|a=1|b=2|json=0|z=1", "K", &keys).is_err());
        assert!(values("L|a=1|b=2|json=0", "K", &keys).is_err());
        assert!(values("K|a=1|b|json=0", "K", &keys).is_err());
    }

    #[test]
    fn rationals() {
        assert_eq!(rational_is_zero("0", "y").ok(), Some(true));
        assert_eq!(rational_is_zero("0/7", "y").ok(), Some(true));
        assert_eq!(rational_is_zero("-1/54", "y").ok(), Some(false));
        assert!(rational_is_zero("1/0", "y").is_err());
        assert!(rational_is_zero("a", "y").is_err());
    }
}
