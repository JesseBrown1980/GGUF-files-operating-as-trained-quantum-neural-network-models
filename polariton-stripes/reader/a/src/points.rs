//! The dump points of PREDICTION-STRIPE-PHASE.hbp (STRIPES_POINT P01-P14, with STRIPES_POINTS_COMMON) and two
//! excluded test points. A known id fixes what each call's stream must be.

pub const COUNT: u64 = 4096;
pub const SEED_PREFIX: &str = "stripes-ens-v1";
pub const MASK_ALL: &str = "VNC,V1,V0,RN,FLIP,LOCK,MODE0,NL";
pub const MASK_VNC: &str = "VNC";

pub struct Point {
    pub id: &'static str,
    pub n: i64,
    pub delta: &'static str,
    pub y: &'static str,
    /// VNC samples at the point: calls 0 .. vnc_count / 4096.
    pub vnc_count: u64,
    /// calls below this index run every variant and NL; the later calls run VNC only.
    pub all_calls: u64,
    pub steps: &'static [u64],
    /// a side file is required for the calls below all_calls (P08 and P13).
    pub side: bool,
    /// a row point of the prediction (false: an excluded test point).
    pub row_point: bool,
}

const S4: &[u64] = &[64, 128, 192, 256];
const S3: &[u64] = &[128, 192, 256];
const S2: &[u64] = &[64, 128];

#[allow(clippy::too_many_arguments)]
const fn row(
    id: &'static str,
    n: i64,
    delta: &'static str,
    y: &'static str,
    vnc: u64,
    all: u64,
    steps: &'static [u64],
    side: bool,
) -> Point {
    Point {
        id,
        n,
        delta,
        y,
        vnc_count: vnc,
        all_calls: all,
        steps,
        side,
        row_point: true,
    }
}

pub const POINTS: [Point; 16] = [
    row("P01", 1296, "1/2", "0", 4_194_304, 64, S4, false),
    row("P02", 1296, "1/2", "1/576", 4_194_304, 64, S4, false),
    row("P03", 1296, "1/2", "1/288", 4_194_304, 64, S4, false),
    row("P04", 1296, "1/2", "1/144", 4_194_304, 64, S4, false),
    row("P05", 1296, "1/2", "1/72", 1_048_576, 64, S4, false),
    row("P06", 1296, "1/2", "1/36", 1_048_576, 64, S4, false),
    row("P07", 729, "-1/4", "0", 1_048_576, 64, S3, false),
    row("P08", 729, "-1/4", "1/54", 1_048_576, 64, S4, true),
    row("P09", 121, "1/2", "0", 1_048_576, 64, S4, false),
    row("P10", 121, "1/2", "1/11", 1_048_576, 64, S4, false),
    row("P11", 1296, "1/2", "1/648", 4_194_304, 64, S4, false),
    row("P12", 324, "1/2", "1/162", 4_194_304, 64, S4, false),
    row("P13", 729, "-1/4", "-1/54", 262_144, 64, S2, true),
    row("P14", 729, "-1/4", "1/108", 1_048_576, 0, S2, false),
    Point {
        id: "X1",
        n: 27,
        delta: "1/4",
        y: "1/40",
        vnc_count: 32_768,
        all_calls: 8,
        steps: S2,
        side: false,
        row_point: false,
    },
    Point {
        id: "X0",
        n: 27,
        delta: "1/4",
        y: "0",
        vnc_count: 32_768,
        all_calls: 8,
        steps: S2,
        side: false,
        row_point: false,
    },
];

pub fn find(id: &str) -> Option<&'static Point> {
    POINTS.iter().find(|p| p.id == id)
}

impl Point {
    pub fn seed_string(&self) -> String {
        format!("{SEED_PREFIX}:N{}:d{}:y{}", self.n, self.delta, self.y)
    }
    pub fn calls(&self) -> u64 {
        self.vnc_count / COUNT
    }
    pub fn mask(&self, call: u64) -> &'static str {
        if call < self.all_calls {
            MASK_ALL
        } else {
            MASK_VNC
        }
    }
    pub fn needs_side(&self, call: u64) -> bool {
        self.side && call < self.all_calls
    }
}

/// An id the reader accepts without a table entry: T followed by letters, digits, '-' or '_' (synthetic tests only).
pub fn is_test_id(id: &str) -> bool {
    id.len() >= 2
        && id.starts_with('T')
        && id[1..]
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_')
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn table_matches_the_frozen_points() {
        let p08 = find("P08").map(|p| p.seed_string());
        assert_eq!(p08.as_deref(), Some("stripes-ens-v1:N729:d-1/4:y1/54"));
        let p13 = find("P13").map(|p| (p.calls(), p.mask(63), p.needs_side(63), p.needs_side(64)));
        assert_eq!(p13, Some((64, MASK_ALL, true, false)));
        let p14 = find("P14").map(|p| (p.calls(), p.mask(0)));
        assert_eq!(p14, Some((256, MASK_VNC)));
        let total: u64 = POINTS
            .iter()
            .filter(|p| p.row_point)
            .map(|p| p.calls())
            .sum();
        assert_eq!(total, 8000);
        assert!(
            is_test_id("Tsyn-1") && !is_test_id("T") && !is_test_id("P99") && !is_test_id("T|x")
        );
    }
}
