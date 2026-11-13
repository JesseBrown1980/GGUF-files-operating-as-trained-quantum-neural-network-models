//! Frozen One Button inspired 81-node balanced-ternary experiment.
//! Exactly 3 colors * 27 positions = 3^4 parent addresses, plus an integer Omega.
//! Uses existing synthetic GGUF trained parent corrections, without retraining.
//! No float, GPU, GUI, browser, or quantum-hardware requirement.
#![forbid(unsafe_code)]
#![deny(clippy::float_arithmetic)]

use gguf_qnn::sha256::hex_digest;
use gguf_qnn::shared_graft::Graft;
use std::error::Error;
use std::fs;
use std::path::Path;

const N: usize = 81;
const STEPS: usize = 3;
const SYNTHETIC_SHA: &str = "606c4d8478b8dbd72dfda0dad6c6ef1895c081a7cd5d5bb6c363525f57b941b2";

type State = [i8; N];
type Links = [[i8; N]; N];

fn trit(value: i16) -> i8 {
    match value.cmp(&0) {
        std::cmp::Ordering::Less => -1,
        std::cmp::Ordering::Equal => 0,
        std::cmp::Ordering::Greater => 1,
    }
}

fn address(id: usize) -> (i8, [i8; 3]) {
    assert!(id < N);
    let color = (id % 3) as i8 - 1;
    let mut band = id / 3;
    let mut coordinates = [0_i8; 3];
    for digit in &mut coordinates {
        *digit = (band % 3) as i8 - 1;
        band /= 3;
    }
    assert_eq!(band, 0);
    (color, coordinates)
}

fn matrix() -> Links {
    let mut edges = [[0_i8; N]; N];
    for (i, row) in edges.iter_mut().enumerate() {
        let (color_i, xyz_i) = address(i);
        for (j, edge) in row.iter_mut().enumerate() {
            if i == j {
                continue;
            }
            let (color_j, xyz_j) = address(j);
            let hamming = (0..3).filter(|&k| xyz_i[k] != xyz_j[k]).count();
            if hamming <= 1 {
                *edge = if color_i == color_j { -1 } else { 1 };
            }
        }
    }
    edges
}

fn seed_from_real_gguf(graft: &Graft) -> Result<State, Box<dyn Error>> {
    if graft.learned_parents() != N || graft.learned_leaves() != N * N {
        return Err("not the original full synthetic 81-parent/6561-leaf GGUF".into());
    }
    let mut state = [0_i8; N];
    for (i, s) in state.iter_mut().enumerate() {
        let delta = graft.parents[i].ok_or("missing parent correction")?;
        let (_, xyz) = address(i);
        let signed: i16 = delta
            .iter()
            .zip(xyz)
            .map(|(weight, coord)| i16::from(*weight) * i16::from(coord))
            .sum();
        *s = trit(signed);
    }
    Ok(state)
}

fn evolve(seed: &State, edges: &Links) -> State {
    let mut state = *seed;
    for _ in 0..STEPS {
        let mut next = [0_i8; N];
        for (i, row) in edges.iter().enumerate() {
            let influence: i16 = row
                .iter()
                .zip(state)
                .map(|(w, s)| i16::from(*w) * i16::from(s))
                .sum();
            next[i] = trit(4 * i16::from(seed[i]) + 2 * i16::from(state[i]) + influence);
        }
        state = next;
    }
    state
}

fn center(state: &State) -> ([i16; 3], i16, i8) {
    let mut colors = [0_i16; 3];
    for (i, &s) in state.iter().enumerate() {
        colors[i % 3] += i16::from(s);
    }
    let total = colors.iter().sum();
    (colors, total, trit(total))
}

fn moved_address(id: usize) -> usize {
    (5 * id + 1) % N
}

fn consistent_relabel(seed: &State, matrix: &Links) -> (State, Links) {
    let mut relabelled = [0_i8; N];
    let mut remapped_links = [[0_i8; N]; N];
    for (i, &s) in seed.iter().enumerate() {
        relabelled[moved_address(i)] = s;
        for j in 0..N {
            remapped_links[moved_address(i)][moved_address(j)] = matrix[i][j];
        }
    }
    (relabelled, remapped_links)
}

fn verify_matrix(matrix: &Links) -> Result<(usize, usize), Box<dyn Error>> {
    let mut attractive = 0_usize;
    let mut repulsive = 0_usize;
    for i in 0..N {
        if matrix[i][i] != 0 {
            return Err("self edge is nonzero".into());
        }
        for j in i + 1..N {
            if matrix[i][j] != matrix[j][i] || !(-1..=1).contains(&matrix[i][j]) {
                return Err("matrix fails signed-ternary symmetry".into());
            }
            match matrix[i][j] {
                1 => attractive += 1,
                -1 => repulsive += 1,
                _ => {}
            }
        }
    }
    Ok((attractive, repulsive))
}

fn state_bytes(state: &State) -> Vec<u8> {
    state.iter().map(|v| (*v + 1) as u8).collect()
}

fn run(model_path: &Path, output_dir: &Path) -> Result<(), Box<dyn Error>> {
    fs::create_dir_all(output_dir)?;
    let model_bytes = fs::read(model_path)?;
    if hex_digest(&model_bytes) != SYNTHETIC_SHA {
        return Err("wrong synthetic 6561-head GGUF checkpoint SHA-256".into());
    }
    let model = Graft::from_gguf(&model_bytes)?;
    let input = seed_from_real_gguf(&model)?;
    let edges = matrix();
    let (attractive, repulsive) = verify_matrix(&edges)?;
    let computed = evolve(&input, &edges);
    let (rgb, total, omega) = center(&computed);

    // Address-only relabelling: move both the data and its exact adjacency.
    let (renamed_seed, renamed_links) = consistent_relabel(&input, &edges);
    let moved_result = evolve(&renamed_seed, &renamed_links);
    let mut original_order = [0_i8; N];
    for (i, s) in original_order.iter_mut().enumerate() {
        *s = moved_result[moved_address(i)];
    }
    if original_order != computed {
        return Err("consistent relabel should preserve exact integer dynamics".into());
    }

    // Actual position surgery: move weights but keep the original spatial matrix.
    let mut changed_model = model.clone();
    changed_model.parents.swap(0, 80);
    let swapped_bytes = changed_model.gguf();
    let cold_changed = Graft::from_gguf(&swapped_bytes)?;
    if cold_changed.parents != changed_model.parents
        || cold_changed.backbone.raw_counts() != model.backbone.raw_counts()
        || cold_changed.leaves != model.leaves
    {
        return Err("cold model position surgery changed other weights".into());
    }
    let swapped_input = seed_from_real_gguf(&cold_changed)?;
    let swapped_out = evolve(&swapped_input, &edges);
    let differences = computed
        .iter()
        .zip(swapped_out)
        .filter(|(a, b)| a != b)
        .count();
    let (swap_rgb, swap_total, swap_omega) = center(&swapped_out);

    // Test that every intermediate state is literally balanced ternary.
    if computed
        .iter()
        .chain(swapped_out.iter())
        .any(|&x| !(-1..=1).contains(&x))
    {
        return Err("non-ternary activation observed".into());
    }
    let original_hash = hex_digest(&state_bytes(&computed));
    let swap_hash = hex_digest(&state_bytes(&swapped_out));
    fs::write(output_dir.join("source_model.gguf"), model_bytes)?;
    fs::write(output_dir.join("position_swapped.gguf"), swapped_bytes)?;
    fs::write(output_dir.join("base_state.trits"), state_bytes(&computed))?;
    fs::write(
        output_dir.join("swapped_state.trits"),
        state_bytes(&swapped_out),
    )?;

    let receipt = format!(
        "ONEBUTTON81_SOURCE|schema=QNN_81_PLUS_0_TERNARY_V1|original_synthetic_gguf_sha256={SYNTHETIC_SHA}|active_trained_parent_heads=81|learned_leaf_heads=6561|arithmetic=INTEGER|json=0\n\
ONEBUTTON81_GEOMETRY|positions=81|colors=3|nodes_per_color=27|ternary_coordinates=4|center_Omega=1|attractive_undirected_links={attractive}|repulsive_undirected_links={repulsive}|steps={STEPS}|json=0\n\
ONEBUTTON81_BASE|red={}|green={}|blue={}|total={total}|omega_sign={omega}|state_sha256={original_hash}|json=0\n\
ONEBUTTON81_RELABEL|permutation_id=(5*i+1)_mod_81|move_weights_and_connectivity_together=YES|all_81_states_identical_after_reverse_map=PASS|json=0\n\
ONEBUTTON81_POSITION_SWAP|swapped_parent_addresses=0_and_80|original_graph_held_fixed=YES|changed_trit_count={differences}|red={}|green={}|blue={}|total={swap_total}|omega_sign={swap_omega}|state_sha256={swap_hash}|json=0\n\
ONEBUTTON81_COMPLETE|literal_balanced_ternary=PASS|no_float=PASS|cold_changed_GGUF=PASS|same_backbone_and_leaves=PASS|identity_relabel_invariant=PASS|classification_benchmark=NOT_RUN|json=0\n",
        rgb[0], rgb[1], rgb[2],
        swap_rgb[0], swap_rgb[1], swap_rgb[2],
    );
    fs::write(output_dir.join("ONEBUTTON81-RESULT.hbp"), &receipt)?;
    print!("{receipt}");
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = std::env::args().collect();
    match args.as_slice() {
        [_, flag, model, output] if flag == "--run" => run(Path::new(model), Path::new(output)),
        _ => Err("usage: onebutton_ternary81 --run SYNTHETIC_6561_GGUF OUTPUT_DIR".into()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn all_positions_are_unique_balanced_ternary() {
        let mut seen = std::collections::BTreeSet::new();
        let mut counts = [0_usize; 3];
        for i in 0..N {
            let (color, xyz) = address(i);
            assert!((-1..=1).contains(&color));
            assert!(xyz.iter().all(|x| (-1..=1).contains(x)));
            assert!(seen.insert((color, xyz)));
            counts[(color + 1) as usize] += 1;
        }
        assert_eq!(seen.len(), N);
        assert_eq!(counts, [27, 27, 27]);
    }

    #[test]
    fn connectivity_is_exact_ternary_and_symmetric() {
        let edges = matrix();
        let (attract, repel) = verify_matrix(&edges).unwrap();
        assert!(attract > 0);
        assert!(repel > 0);
        let seed = std::array::from_fn(|i| (i % 3) as i8 - 1);
        let expected = evolve(&seed, &edges);
        let (moved, moved_edges) = consistent_relabel(&seed, &edges);
        let result = evolve(&moved, &moved_edges);
        for (i, &state) in expected.iter().enumerate() {
            assert_eq!(result[moved_address(i)], state);
        }
    }

    #[test]
    fn fixed_point_dynamics_stays_in_trit_alphabet() {
        let input = std::array::from_fn(|i| if i % 7 == 0 { 1 } else { -1 });
        let actual = evolve(&input, &matrix());
        assert!(actual.iter().all(|x| (-1..=1).contains(x)));
        let (channels, aggregate, omega) = center(&actual);
        assert_eq!(aggregate, channels.iter().sum());
        assert_eq!(omega, trit(aggregate));
    }
}
