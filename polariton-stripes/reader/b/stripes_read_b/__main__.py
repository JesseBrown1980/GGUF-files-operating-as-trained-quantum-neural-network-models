"""stripes-read-b: python3 -I reader/b/stripes_read_b/__main__.py <command> ...

  read   --agg D --runs D --qe P --cost P --qe-rc P --guard P --out P
         every STRIPES_PREDICT row from the per-call aggregates (D/P01..P14/<call>.hbp, each point's files checked
         against its SHA256SUMS; no flag skips that check),
         the run receipts (R1-R4, 64 batches each) and the QE receipts (stdout, stderr and the wrapper's QE-RC.hbp);
         writes READ-STRIPE-PHASE.hbp
  audit  --read P
         checks a READ file alone: its hash, one VERDICT per PREDICT row, every count and verdict from its READ rows,
         falsifiers on scored reads only, and the scored and read-and-report reads of each row against SCORING
  verify --read P --agg D --runs D --qe P --cost P --qe-rc P --guard P
         rebuilds the READ file from the inputs, the SHA256SUMS checks included, and compares it line for line
  scoring --read P
         prints the SCORING table of a READ file (to review a change of the row modules)

read and verify first take stage B's own tree pin (stage_b_tree): each file's mode from git's index, its bytes from
the working tree. They write nothing when a file under reader/b is not in the index or a working-tree mode differs
from the index's (a checkout with core.filemode=false, such as WSL /mnt/c: run stage B from a POSIX checkout).

Exit 0 on success; 3 with one STOP row on stdout when stage B has nothing to decide, or a check fails; 2 on usage."""

import hashlib
import os
import stat
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
if os.path.dirname(HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(HERE))

from stripes_read_b import VERSION  # noqa: E402
from stripes_read_b import common as c  # noqa: E402
from stripes_read_b import frozen as frozen_mod  # noqa: E402
from stripes_read_b import qe as qe_mod  # noqa: E402
from stripes_read_b import rows_e_mom, rows_e_sym, rows_q, runs  # noqa: E402
from stripes_read_b.exact import ExactError  # noqa: E402
from stripes_read_b.qint import QintError  # noqa: E402

B_DIR = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(B_DIR)))
NOT_TRACKED = ("__pycache__", ".ruff_cache")  # the folders reader/.gitignore names
from stripes_read_b.hbp import RowError, emit, fields_dict, file_sha256, parse_row, read_lines, sha256_hex  # noqa: E402

READ_KEYS = ("row", "read", "at", "kind", "scored", "why", "value", "lo", "hi", "band", "frozen", "verdict", "detail")
VERDICT_KEYS = ("row", "name", "tag", "reads", "scored", "report", "met", "miss", "not_resolved", "not_measured",
                "falsifier", "verdict")
# The `why` of a read-and-report read: rule EXPOSED (X08), a repair row (RP13, RP17) or a phrase of its row.
REPORT_WHYS = frozenset(("X08", "RP13", "RP17", "row_text", "about_no_band", "expected_verdicts_beside",
                         "t3-4_read_and_report"))

# Per PREDICT row: (reads, scored, sha256 of the sorted "read:scored:why" lines). The partition into scored and
# read-and-report reads follows from the frozen text and rule EXPOSED alone, never from data, so a read promoted to
# scored (or demoted) changes this table. `scoring --read` prints it for review when a row module changes.
SCORING = {
    "Q01": (28, 28, "a541f02b4c5448b940eb3dd0142bd7fcdad72ae714ac40b481e3dec0bc92aee8"),
    "Q02": (14, 7, "db569688b96fce2f7f69e28bb4fcfcaa40a2db9469f2b08a6484579b8f4887b3"),
    "Q03": (14, 11, "069ba7210256bd3b469ea8c0433db753e0cdf78385dc258e6a7511ae064a5a17"),
    "Q04": (6, 5, "f5ef11ea8dbbb33a87320bba31c752820c9fa30ef88a402941ce6d8ab3294dd7"),
    "Q05": (5, 2, "04f60c035973b07803d3b4b83eee45455005552de61bbb459736803ede455731"),
    "Q06": (12, 4, "343f5c4c73f87bb6e55cc6cf1335830ad7a28ea05682c6e002d54f65e6fdb566"),
    "Q07": (26, 9, "93f367d3e2cf97c89830dab217734b23c3aefa93de7a553354dd10a368e15f00"),
    "E01": (86, 77, "e188b25ced9c865d87c7746183be70718d5e98483a696940c79d16a199dbac6d"),
    "E02": (1102, 834, "27afaa3a18df2b2bc3419ff143a8d125907e297ed342ce46dc4fa9a2d54ce93c"),
    "E03": (154, 154, "8940eb0eb51322f439378435e3287fed81704641b104a8b6498917f0a0415065"),
    "E04": (17, 16, "7b4c2d872ac2947598834ac10ecb264499fe6c27f1aff6c9d073f5d69237098e"),
    "E05": (185, 147, "984d1e51e1f1f0cda37c81d840eb76ff45be78c4a6bcc3e01d2af64f3d90bb15"),
    "E06": (172, 147, "b9db1a5639b19c6e9a9276294b195e9ae29074d058c2de2afab433bdbec8d4fb"),
    "E07": (44, 33, "bf7569ed69a8d229d6259f7ff78ed1c357e095ca80e37fb6ed7787d7074fce76"),
    "E08": (132, 66, "27b4c965d6ff4545e5f11723b7a012243048071f30f8647a833327bd51c3b98a"),
    "E09": (40, 5, "2ae59f2ab55476f72e2a6e41d68b6130ab74542f28fb30242db0ea41d6c178af"),
    "E10": (20, 3, "2d2fdf15fb567a5df9b9942e5d23e18c2f981c7d4791cbb1c824bc5db085f4eb"),
    "E11": (8, 8, "980e69c9cceeb90e7d8daf4d207b7ab3321cccafc243492e877e78db6b6097f6"),
    "E12": (422, 422, "398c7e37ab53839b4832af27395ca2a1a93c090a5e47a291726d73f15abacc89"),
    "E13": (50, 14, "1f9e636708a5839f0d931eedf3399e72d9f2b49d0755834e1074d58b6509d400"),
    "E14": (6, 1, "e395947eea2ec7dc1ab1555562ecc8348d277fe38d0531c03590d39cdc3e1c0a"),
    "E15": (30, 11, "78630c7ad8fa0f7526e4b4011f60b9047b87d461ee9747df7a8a17ec30d29801"),
    "E16": (24, 24, "91637e2d954a51a7c7037f5d45881a1a7ea0932c0fda8a7cb1e5b97af6043612"),
    "E17": (64, 0, "a6ab0ac389aac6125f3419e8ab734dc78d144fae1d9d67bd3fb22d3890775195"),
    "E18": (5, 2, "386e684fb6026de1062118652b832b1e9aee0e92e7c720b67c4f722fb3c067d8"),
    "E19": (12, 12, "f1b348ae5ff81ced138f7d68b521e66d95ff93d2126e1351ca47582e1b64d6bb"),
}

# How stage B reads the frozen text where it allows two readings (STRIPES_READ_NOTE rows of the READ file).
READINGS = (
    ("reading_E06_sector", "0_mismatches_with_abs(B)>=2^-20:_MET_if_none_where_either_B_is_big,_MISS_if_one_where_both"
                           "_are,_else_NOT_RESOLVED"),
    ("reading_E16", "conservative:_D+=t1,_D-=t3_certified;_every_ambiguous_cell_(t2,t5,t6,t7,t8)"
                    "_and_every_sample_outside_the_common_non-atom_set_counts_as_possibly_discordant,_so_D++D-<=D_max"
                    "_and_SE_pair=sqrt(D_max)/(2M)_is_an_upper_bound_of_the_frozen_SE_pair_at_every_placement;_the"
                    "_ambiguous_samples_also_widen_the_bracket_of_the_difference;_MET_if_the_prediction"
                    "_abs(Pi_V-Pi_VNC)+3SE_pair<=Pi_VNC/20_holds_at_every_placement_(then_the_recipe_with"
                    "_(D+-D-)/(2M),_half_of_it,_holds_too),_MISS_if_the_recipe_fails_at_every_placement_(then_the_prediction_fails_too),_else"
                    "_NOT_RESOLVED"),
    ("reading_E15_cross", "a_scored_cross-read_other_than_predicted_is_a_falsifier_when_certified_(MISS);"
                          "_NOT_RESOLVED_leaves_the_row_NOT_RESOLVED,_since_READ3_counts_falsifiers_on_outcomes_and"
                          "_NOT_RESOLVED_is_not_certified"),
    ("reading_E02_counts", "integer_intervals_keyed_by_sample_count_and_variant_class;_[0,51]_also_on_the_first_2^18"
                           "_controls;_read_only_on_the_full_nominal_set"),
    ("reading_E04_ratios", "MET_inside_[1/4-1/100-4SE,1/4+1/100+4SE],_MISS_outside,_the_frozen_band_and_falsifier"),
    ("reading_Pi_hat", "Pi_hat_counts_every_sample,_atoms_by_their_own_sign_states;_H8_and_B16_leave_atoms_out"),
    ("reading_E01_atoms", "the_Klein_atom_masses_(about_3.108e-4_M,_0.042097_M)_have_no_band:_read_and_report"),
    ("reading_E12_E13_n", "in_E12_and_the_E13_tolerance_reads_n=4..4096_is_every_power_of_2_from_4_to_4096_with_at"
                          "_least_1024_blocks_in_the_nominal_sample_count;_after_a_lost_call_a_size_left_with_fewer"
                          "_than_1024_measured_blocks_is_NOT_MEASURED,_so_that_read_is_NOT_RESOLVED_at_best;_the_E13"
                          "_bands_take_the_frozen_n=4^k"),
    ("reading_E10_falsifier", "P02_not_resolved_above_0_at_3_SE:_the_low_end_of_the_ambiguity_bracket"
                              "_(O+-O--A)/(2M),_minus_3SE,_is_at_or_below_0"),
    ("reading_E18_zero", "E_VNC[abs(B_W)^2]=0_is_a_ratio_of_0:_MISS"),
    ("reading_E19_nstar", "n*_is_not_estimable_when_abs(Bbar)^2_u<=0_on_the_set_or_a_leave-one-out_set:_NOT_RESOLVED"),
    ("reading_Q_unbounded", "a_ratio_whose_denominator_interval_reaches_0_is_read_as_the_half-line_[lo,+inf),_or_both"
                            "_half-lines_when_the_denominator_crosses_0:_MISS_when_every_piece_is_disjoint_from_the"
                            "_band,_else_NOT_RESOLVED"),
    ("reading_Q06_c", "c_from_the_signed_B_interval_(D2_q=2B_e18/N);_B_e18<=0_is_MISS_(the_falsifier),_else_READ3_on"
                      "_c"),
    ("reading_QE_exit", "a_QE_command_filed_with_rc!=0_in_QE-RC.hbp_leaves_every_read_of_its_rows_NOT_MEASURED,"
                        "_the_rows_it_printed_before_the_exit_included;_its_COST_rows_and_other_stderr_text_are_kept"
                        "_out_of_the_COST_match;_stderr_text_other_than_COST_rows_with_every_rc=0_is_a_STOP"),
    ("reading_STOP_tries", "a_dump_call_or_run_batch_exiting_4_(rc=4,_nothing_on_stdout,_a_TWB_FAULT_row_on_stderr)"
                           "_is_kept_as_<call>.attempt<k>_and_rerun_with_its_last_record_dropped;_a_block_with_r_of_R"
                           "_records_needs_attempts_1..R-r,_a_lost_call_or_batch_1..R-1;_any_other_exit_is_a_STOP;"
                           "_the_4096_indices_of_a_lost_call_are_NOT_MEASURED_and_the_other_calls_are_read;_a_run_batch"
                           "_whose_one-record_try_exits_4_too_reached_no_record,_so_its_run_point_keeps_no_record"
                           "_(the_records_all_64_batches_reached)_and_every_read_of_that_point_is_NOT_MEASURED,"
                           "_stating_the_loss"),
    ("reading_GUARD", "the_guard_is_a_function_of_(N,delta,y)_alone:_one_allowed_line_is_filed_before_each_QE_command"
                      "_and_before_each_dump_or_run_point,_whose_calls_and_batches_follow_it;_a_refusal_counts_only"
                      "_at_a_plan_triple"),
    # review note N6: the frozen R1 row files s=1/2, and the reader never takes s from a STRIPES_POINT row
    ("frozen_R1_s", "STRIPES_POINT_R1_(frozen_line_19)_files_s=1/2,_while_y_sqrt(N)=(1/27)_sqrt(729)=1;_stage_B"
                    "_computes_s=y_sqrt(N)_itself_from_N_and_y_(rule_EXPOSED_reads_abs(s)=1_at_R1)_and_no_read_uses"
                    "_the_filed_s;_the_frozen_bytes_stay_as_they_are"),
    # the owner rulings of the receipt's GATE row that the frozen text closes (local seat, PR #18 comment 6749660971);
    # line numbers are those of PREDICTION-STRIPE-PHASE.hbp at 1977d45
    ("closed_STOP_runs", "closed_by_the_frozen_text,_the_literal_reading:_frozen_line_37_(rule_STOP)_gives_the_dump"
                         "_clause_its_own_sentence_for_a_call_that_never_completes_(its_4096_indices_NOT_MEASURED)"
                         "_and_the_run_clause_none:_the_point_keeps_only_the_records_all_64_batches_reached;_a_lost"
                         "_batch_reached_none,_so_every_read_of_its_run_point_is_NOT_MEASURED_and_states_the_loss"),
    ("closed_E16_bracket", "closed_by_the_frozen_text,_the_bracket_reading:_frozen_line_30_(rule_SECTOR)_has_every"
                           "_ambiguous_cell_bracketed_in_every_test,_so_D++D-<=D_max_over_every_placement;_frozen_line"
                           "_114_(E16)_holds_the_statement_abs(Pi_V-Pi_VNC)_and_the_recipe_(D+-D-)/(2M):_MET_when_the"
                           "_statement_passes_at_every_placement,_MISS_when_the_recipe_fails_at_every_placement,_else"
                           "_NOT_RESOLVED"),
    ("closed_E02_counts", "closed_by_the_frozen_text,_counts_keyed_by_sample_count_and_variant_class:_frozen_line_4"
                          "_(STRIPES_POINTS_COMMON)_gives_calls_i<64_every_variant_and_NL,_so_the_controls_cover_the"
                          "_first_2^18_indices;_frozen_line_100_(E02)_keys_its_intervals_by_sample_count_and_variant"
                          "_class,_[0,51]_at_2^18_on_those_indices;_a_partial_set_after_a_lost_call_has_a_count_no"
                          "_interval_is_keyed_to,_so_its_count_is_NOT_MEASURED"),
)


def _args(argv, keys):
    """{key: value} of `--key value` pairs; no command takes a flag (none skips a check)."""
    out, i = {}, 0
    while i < len(argv):
        a = argv[i]
        if a in keys and i + 1 < len(argv) and a not in out:
            out[a] = argv[i + 1]
            i += 2
        else:
            raise c.StageBStop("usage", a)
    return out


def _need(a, keys):
    for k in keys:
        if k not in a:
            raise c.StageBStop("usage", "missing " + k)


def guard_triples():
    """One (N, delta, y) per guarded command of the campaign (rule GUARD): each QE command, each dump point (its
    calls follow its guard line) and each run point (its batches follow it)."""
    t = list(qe_mod.plan_guards())
    t += [(p.N, p.delta, p.y) for p in c.DUMP_POINTS.values()]
    t += [(p.N, p.delta, p.y) for p in c.RUN_POINTS.values()]
    return sorted(t)


def _git(repo, *args, reason="stage_b_tree"):
    p = subprocess.run(["git", "-C", repo] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       stdin=subprocess.DEVNULL, check=False)
    if p.returncode != 0:
        raise c.StageBStop(reason, "git %s exited %d: %s" % (args[0], p.returncode,
                                                             p.stderr.decode("ascii", "replace")[:120]))
    return p.stdout


def stage_b_index(b_dir=None, repo=None):
    """{path: mode} of git's index under reader/b (`git ls-files -s`), paths from the repo root."""
    b_dir, repo = b_dir or B_DIR, repo or REPO
    rel = os.path.relpath(b_dir, repo).replace(os.sep, "/")
    out = {}
    for rec in _git(repo, "ls-files", "-s", "-z", "--", rel).split(b"\0"):
        if not rec:
            continue
        meta, path = rec.split(b"\t", 1)
        mode, _oid, st = meta.decode("ascii").split(" ")
        if st != "0":
            raise c.StageBStop("stage_b_tree", "unmerged index entry: " + path.decode("utf-8", "replace"))
        out[path.decode("utf-8", "surrogateescape")] = mode
    return out


def stage_b_tree(b_dir=None, repo=None):
    """(path, pin) of this stage B's tree, reader/b, by the rule of check/float_evidence.py (tree_line of the 4D
    repo): the sha256 of one line `<mode> <sha256 of the bytes> <path>` per file, paths from the repo root sorted as
    bytes, the mode from git's index (`git ls-files -s`) and the bytes from the working tree. On a clean checkout it
    is the pin that `float_evidence.py --pins polariton-stripes/reader/b/` prints, so a READ file names the code that
    wrote it. StageBStop when a file under reader/b (the folders reader/.gitignore names aside) is not in the index,
    an index entry is not in the working tree, or a working-tree mode differs from the index's (stage_b_modes)."""
    b_dir, repo = b_dir or B_DIR, repo or REPO
    index = stage_b_index(b_dir, repo)
    rows, seen = [], set()
    for top, dirs, files in os.walk(b_dir):
        links = [d for d in dirs if os.path.islink(os.path.join(top, d))]
        dirs[:] = sorted(d for d in dirs if d not in NOT_TRACKED and d not in links)
        for nm in files + links:
            full = os.path.join(top, nm)
            path = os.path.relpath(full, repo).replace(os.sep, "/")
            if path not in index:
                raise c.StageBStop("stage_b_tree", "not in git's index: " + path)
            st = os.lstat(full)
            if stat.S_ISLNK(st.st_mode):
                have, data = "120000", os.readlink(full).encode("utf-8", "surrogateescape")
            else:
                have = "100755" if st.st_mode & stat.S_IXUSR else "100644"
                with open(full, "rb") as f:
                    data = f.read()
            if have != index[path]:
                raise c.StageBStop("stage_b_modes", "%s: working tree %s, git's index %s (run stage B from a POSIX"
                                   " checkout)" % (path, have, index[path]))
            seen.add(path)
            rows.append((path.encode("utf-8", "surrogateescape"),
                         "%s %s %s\n" % (index[path], hashlib.sha256(data).hexdigest(), path)))
    gone = sorted(set(index) - seen)
    if gone:
        raise c.StageBStop("stage_b_tree", "in git's index, not in the working tree: " + gone[0])
    rows.sort()
    pin = hashlib.sha256("".join(r[1] for r in rows).encode("utf-8", "surrogateescape")).hexdigest()
    return os.path.relpath(b_dir, repo).replace(os.sep, "/"), pin


def git_tree_id(entries):
    """The id git gives the tree of {path below the tree: (mode, blob id)} (sha1 object format): entries sorted by name,
    a folder's name compared as if it ended in '/', each `<mode> <name>\\0<20-byte id>`."""
    root = {}
    for path, leaf in entries.items():
        node = root
        *dirs, name = path.split("/")
        for d in dirs:
            node = node.setdefault(d, {})
        node[name] = leaf

    def tree_of(node):
        items = []
        for name, val in node.items():
            nm = name.encode("utf-8", "surrogateescape")
            if isinstance(val, dict):
                items.append((nm + b"/", b"40000 " + nm + b"\0" + int(tree_of(val), 16).to_bytes(20, "big")))
            else:
                items.append((nm, val[0].encode("ascii") + b" " + nm + b"\0" + int(val[1], 16).to_bytes(20, "big")))
        body = b"".join(e for _, e in sorted(items))
        return hashlib.sha1(b"tree %d\0" % len(body) + body).hexdigest()

    return tree_of(root)


def stage_a_tree(a_dir=None, repo=None):
    """(path, git tree id) of stage A's source, reader/a, from git's index (`git ls-files -s`): on a commit it is what
    `git rev-parse <commit>:polariton-stripes/reader/a` prints, the tree the stage A pin of reader/README.md is built
    from. StageBStop('stage_a_tree') when a file under reader/a that git does not ignore is not in the index, or an
    index entry is missing from the working tree or differs from it in bytes or mode (stage the edits first)."""
    repo = repo or REPO
    a_dir = a_dir or os.path.join(os.path.dirname(B_DIR), "a")
    rel = os.path.relpath(a_dir, repo).replace(os.sep, "/")
    entries = {}
    for rec in _git(repo, "ls-files", "-s", "-z", "--", rel, reason="stage_a_tree").split(b"\0"):
        if not rec:
            continue
        meta, path = rec.split(b"\t", 1)
        mode, oid, st = meta.decode("ascii").split(" ")
        path = path.decode("utf-8", "surrogateescape")
        if st != "0" or len(oid) != 40 or not path.startswith(rel + "/"):
            raise c.StageBStop("stage_a_tree", "index entry %s %s %s %s" % (mode, oid[:12], st, path))
        entries[path] = (mode, oid)
    if not entries:
        raise c.StageBStop("stage_a_tree", "git's index holds nothing under " + rel)
    others = [x for x in _git(repo, "ls-files", "--others", "--exclude-standard", "-z", "--", rel,
                              reason="stage_a_tree").split(b"\0") if x]
    if others:
        raise c.StageBStop("stage_a_tree", "not in git's index: " + others[0].decode("utf-8", "replace"))
    for path, (mode, oid) in sorted(entries.items()):
        full = os.path.join(repo, *path.split("/"))
        try:
            st = os.lstat(full)
        except FileNotFoundError:
            raise c.StageBStop("stage_a_tree", "in git's index, not in the working tree: " + path) from None
        if stat.S_ISLNK(st.st_mode):
            have, data = "120000", os.readlink(full).encode("utf-8", "surrogateescape")
        elif stat.S_ISREG(st.st_mode):
            have = "100755" if st.st_mode & stat.S_IXUSR else "100644"
            with open(full, "rb") as f:
                data = f.read()
        else:
            raise c.StageBStop("stage_a_tree", "not a file or a link: " + path)
        blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
        if (have, blob) != (mode, oid):
            raise c.StageBStop("stage_a_tree", "%s: working tree %s %s, git's index %s %s (stage it, or run from a POSIX"
                               " checkout)" % (path, have, blob[:12], mode, oid[:12]))
    return rel, git_tree_id({p[len(rel) + 1:]: v for p, v in entries.items()})


def run_listing(run_dir):
    """sha256sum-style listing of the run receipts R1-R4 (the run's own receipt, in memory)."""
    names = sorted(n for n in os.listdir(run_dir) if n.split(".", 1)[0] in c.RUN_POINTS)
    return "".join("%s  %s\n" % (file_sha256(os.path.join(run_dir, n)), n) for n in names), len(names)


def build(a):
    """The READ file of the inputs named in a (read and verify)."""
    tree_path, tree_pin = stage_b_tree()  # first: no READ file from a tree whose modes or files git does not hold
    a_path, a_tree = stage_a_tree()  # stage A's source as git holds it, named in the reader_a note
    fz = frozen_mod.load()
    c.check_tables(fz)
    c.check_exposure_text(fz)
    qe_mod.check_plan(fz)
    c.check_guard_file(a["--guard"], guard_triples())
    points = {pid: c.load_point(os.path.join(a["--agg"], pid), spec, require_sums=True)
              for pid, spec in c.DUMP_POINTS.items()}
    for pt in points.values():
        if pt.spec.side:
            pt.verify_sides()  # every side file a block names, paired at E04 or not: its size and sha256
    run_points = runs.load_runs(a["--runs"])
    qv, qe_reads = rows_q.read_q(a["--qe"], a["--cost"], a["--guard"], fz, a["--qe-rc"])
    sv = rows_e_sym.read_e_sym(points, run_points, fz)
    mv = rows_e_mom.read_e_mom(rows_e_mom.Inputs(points, run_points, qe_reads), fz)
    verdicts = {v.row: v for v in qv + sv + mv}
    order = [d["id"] for k, d, _ in fz.rows if k == "STRIPES_PREDICT"]
    if sorted(verdicts) != sorted(order) or len(qv + sv + mv) != len(order):
        raise c.StageBStop("verdict_rows", "rows read %s, frozen %s" % (len(verdicts), len(order)))
    rf = c.ReadFile(fz)
    rf.add_input("QE", a["--qe"])
    rf.add_input("QE_COST", a["--cost"])
    rf.add_input("QE_RC", a["--qe-rc"])
    rf.add_input("GUARD", a["--guard"])
    for pid in c.DUMP_POINTS:
        rf.add_input("AGG_" + pid, os.path.join(a["--agg"], pid, "SHA256SUMS"))  # load_point checked each one
    listing, n = run_listing(a["--runs"])
    rf.notes.append(("runs", "files=%d,sha256_of_listing=%s" % (n, sha256_hex(listing.encode("ascii")))))
    rf.notes.append(("reader_b", "%s_%s,integer_pairs,tree_%s/_%s,frozen_%s" % (
        c.READER, VERSION, tree_path, tree_pin, fz.sha256)))
    rf.notes.append(("reader_a", "%s_%s_(per_block_AGG_HEAD),git_tree_%s/_%s" % (
        c.READER_A, c.READER_A_VERSION, a_path, a_tree)))
    for pid, pt in points.items():
        rf.notes.append(("point_" + pid, "calls=%d,read=%d,lost=%s,steps=%s,not_measured=%s,attempts=%d" % (
            pt.spec.calls, len(pt.calls), ":".join(str(i) for i, _ in pt.lost) or "none",
            ":".join(map(str, pt.steps)) or "none", ":".join(map(str, pt.not_measured)) or "none",
            len(pt.attempts))))
    for rid, r in run_points.items():
        # rule STOP: a lost batch leaves the point no record (steps none), so no batch of it is read
        rf.notes.append(("run_" + rid, "batches=%d,checked=%d,read=%d,lost=%s,steps=%s,not_measured=%s,attempts=%d" % (
            r.spec.batches, len(r.batches), len(r.batches) if r.steps else 0,
            ":".join(str(j) for j, _ in r.lost) or "none", ":".join(map(str, r.steps)) or "none",
            ":".join(map(str, r.not_measured)) or "none", r.attempts)))
    miss = qe_mod.missing(qe_reads)
    rf.notes.append(("qe_rows", "%d_read,%d_missing_(NOT_MEASURED)" % (len(qe_reads), len(miss))))
    rf.notes.append(("qe_rc", "commands=%d,rc_nonzero=%s,stderr_lines_not_COST=%d" % (
        len(qe_mod.PLAN), ";".join("%s:rc=%d" % f for f in qe_reads.failed) or "none", qe_reads.stderr_lines)))
    rf.notes.append(("qe_binary", "sha256=%s,lane_build_%s=%s" % (
        qe_reads.binary, qe_mod.LANE_BINARY_SHA256[:8], "equal" if qe_reads.binary == qe_mod.LANE_BINARY_SHA256
        else "differs")))
    rf.notes.extend(READINGS)
    for rid in order:
        rf.add(verdicts[rid])
    lines = rf.lines()
    audit_lines(lines, fz)
    return lines


def write_lines(path, lines):
    data = "".join(ln + "\n" for ln in lines).encode("ascii")
    with open(path, "wb") as f:
        f.write(data)
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------------------------------------------------
# Audit: what a READ file must satisfy on its own.


def _rows(lines, kind, keys):
    out = []
    for ln in lines:
        if ln.startswith(kind + "|"):
            try:
                out.append(fields_dict(parse_row(ln, kind, keys)[1]))
            except RowError as e:
                raise c.StageBStop("read_file_row", str(e)) from e
    return out


def scoring_table(reads_by_row):
    """{row: (reads, scored, sha256 of the sorted read:scored:why lines)}."""
    out = {}
    for rid, rs in reads_by_row.items():
        lines = sorted("%s:%s:%s" % (r["read"], r["scored"], r["why"]) for r in rs)
        out[rid] = (len(rs), sum(1 for r in rs if r["scored"] == "1"),
                    sha256_hex("".join(x + "\n" for x in lines).encode("ascii")))
    return out


def audit_lines(lines, fz=None, table=None):
    """Every check a READ file must pass on its own; raises StageBStop. Returns the scoring table."""
    fz = fz or frozen_mod.load()
    if not lines or not lines[-1].startswith("STRIPES_READ_END|"):
        raise c.StageBStop("read_file", "no STRIPES_READ_END row")
    end = fields_dict(parse_row(lines[-1], "STRIPES_READ_END", ("rows", "sha256"))[1])
    body = lines[:-1]
    if end["rows"] != str(len(body)) or end["sha256"] != sha256_hex("".join(x + "\n" for x in body).encode("ascii")):
        raise c.StageBStop("read_file_sha256", "STRIPES_READ_END does not cover the rows before it")
    head = fields_dict(parse_row(body[0], "STRIPES_READ_HEAD", ("reader", "reader_version", "frozen", "frozen_sha256",
                                                                 "rows"))[1])
    order = [d["id"] for k, d, _ in fz.rows if k == "STRIPES_PREDICT"]
    if head["frozen_sha256"] != fz.sha256 or head["rows"].split(",") != order:
        raise c.StageBStop("read_file_head", "frozen hash or row list")
    reads = _rows(body, "STRIPES_READ", READ_KEYS)
    verdicts = _rows(body, "STRIPES_VERDICT", VERDICT_KEYS)
    if [v["row"] for v in verdicts] != order:
        raise c.StageBStop("verdict_rows", "one VERDICT per PREDICT row, in frozen order")
    by_row = {rid: [] for rid in order}
    seen = set()
    for r in reads:
        if r["row"] not in by_row or (r["row"], r["read"]) in seen:
            raise c.StageBStop("read_rows", "%s %s: unknown row or read twice" % (r["row"], r["read"]))
        seen.add((r["row"], r["read"]))
        by_row[r["row"]].append(r)
        if r["scored"] == "1":
            if r["why"] in REPORT_WHYS or r["verdict"] not in (c.MET, c.MISS, c.NOT_RESOLVED, c.NOT_MEASURED):
                raise c.StageBStop("scored_read", "%s %s: scored with why=%s verdict=%s" % (
                    r["row"], r["read"], r["why"], r["verdict"]))
        elif r["scored"] == "0":
            if r["why"] not in REPORT_WHYS or r["verdict"] not in (c.REPORT, c.NOT_MEASURED):
                raise c.StageBStop("report_read", "%s %s: read-and-report with why=%s verdict=%s" % (
                    r["row"], r["read"], r["why"], r["verdict"]))
        else:
            raise c.StageBStop("read_rows", "scored=" + r["scored"])
    for v in verdicts:
        rs = by_row[v["row"]]
        p = fz.predict(v["row"])
        if (v["name"], v["tag"]) != (p["name"], p["tag"]):
            raise c.StageBStop("verdict_rows", v["row"] + " name or tag")
        sc = [r for r in rs if r["scored"] == "1"]
        want = {"reads": len(rs), "scored": len(sc), "report": len(rs) - len(sc)}
        for key, o in (("met", c.MET), ("miss", c.MISS), ("not_resolved", c.NOT_RESOLVED),
                       ("not_measured", c.NOT_MEASURED)):
            want[key] = sum(1 for r in sc if r["verdict"] == o)
        for key, n in want.items():
            if v[key] != str(n):
                raise c.StageBStop("verdict_counts", "%s %s=%s, its READ rows give %d" % (v["row"], key, v[key], n))
        fals = [] if v["falsifier"] == "none" else v["falsifier"].split(":", 1)[0].split(",")
        scored_ids = {r["read"] for r in sc}
        for f in fals:
            if f not in scored_ids:
                raise c.StageBStop("falsifier", "%s: falsifier on a read that is not scored: %s" % (v["row"], f))
        if v["falsifier"] != "none" and v["falsifier"].split(":", 1)[1] != p["falsifier"]:
            raise c.StageBStop("falsifier", v["row"] + ": falsifier text is not the frozen one")
        if v["verdict"] != _row_verdict(sc, bool(fals)):
            raise c.StageBStop("verdict_rule", "%s: verdict %s does not follow READ3" % (v["row"], v["verdict"]))
    got = scoring_table(by_row)
    table = SCORING if table is None else table
    if table is not False:
        for rid in order:
            if table.get(rid) != got[rid]:
                raise c.StageBStop("scoring_table", "%s: reads/scored/fingerprint %s, the reader's table %s" % (
                    rid, got[rid][:2], (table.get(rid) or (None, None))[:2]))
    return got


def _row_verdict(scored_reads, falsifier):
    if any(r["verdict"] == c.MISS for r in scored_reads) or falsifier:
        return c.NOT_MET
    if not scored_reads:
        return c.NONE
    if all(r["verdict"] == c.MET for r in scored_reads):
        return c.MET
    if all(r["verdict"] == c.NOT_MEASURED for r in scored_reads):
        return c.NOT_MEASURED
    return c.NOT_RESOLVED


# ---------------------------------------------------------------------------------------------------------------------
# Commands.

INPUT_KEYS = ("--agg", "--runs", "--qe", "--cost", "--qe-rc", "--guard")


def cmd_read(argv):
    a = _args(argv, INPUT_KEYS + ("--out",))
    _need(a, INPUT_KEYS + ("--out",))
    lines = build(a)
    h = write_lines(a["--out"], lines)
    vs = [fields_dict(parse_row(ln)[1]) for ln in lines if ln.startswith("STRIPES_VERDICT|")]
    tally = {}
    for v in vs:
        tally[v["verdict"]] = tally.get(v["verdict"], 0) + 1
    print(emit("STRIPES_B_WROTE", [("path", a["--out"]), ("sha256", h), ("rows", str(len(lines))),
                                    ("verdict_rows", str(len(vs))),
                                    ("verdicts", ",".join("%s:%d" % kv for kv in sorted(tally.items())))]))
    return 0


def cmd_audit(argv):
    a = _args(argv, ("--read",))
    _need(a, ("--read",))
    lines = read_lines(a["--read"])
    audit_lines(lines)
    print(emit("STRIPES_B_AUDIT", [("path", a["--read"]), ("sha256", file_sha256(a["--read"])),
                                    ("rows", str(len(lines))), ("result", "pass")]))
    return 0


def cmd_verify(argv):
    a = _args(argv, INPUT_KEYS + ("--read",))
    _need(a, INPUT_KEYS + ("--read",))
    have = read_lines(a["--read"])
    audit_lines(have)
    want = build(a)
    for k, (x, y) in enumerate(zip(have, want, strict=False)):
        if x != y:
            raise c.StageBStop("verify", "line %d differs from the rebuilt file" % (k + 1))
    if len(have) != len(want):
        raise c.StageBStop("verify", "%d lines, the rebuilt file has %d" % (len(have), len(want)))
    print(emit("STRIPES_B_VERIFY", [("path", a["--read"]), ("sha256", file_sha256(a["--read"])),
                                     ("rows", str(len(have))), ("result", "equal")]))
    return 0


def cmd_scoring(argv):
    a = _args(argv, ("--read",))
    _need(a, ("--read",))
    got = audit_lines(read_lines(a["--read"]), table=False)
    for rid, (n, s, h) in got.items():
        print('    "%s": (%d, %d, "%s"),' % (rid, n, s, h))
    return 0


COMMANDS = {"read": cmd_read, "audit": cmd_audit, "verify": cmd_verify, "scoring": cmd_scoring}


def main(argv):
    if len(argv) < 2 or argv[1] not in COMMANDS:
        sys.stderr.write(__doc__)
        return 2
    try:
        return COMMANDS[argv[1]](argv[2:]) or 0
    except c.StageBStop as e:
        print(emit("STOP", [("reader", c.READER), ("reader_version", VERSION), ("reason", e.reason),
                            ("detail", e.detail or "none")]))
        return 3
    except (ExactError, KeyError, OSError) as e:
        print(emit("STOP", [("reader", c.READER), ("reader_version", VERSION), ("reason", type(e).__name__),
                            ("detail", str(e)[:300] or "none")]))
        return 3
    except (QintError, ValueError, ArithmeticError) as e:
        # a value that is not a checked integer pair (a stray float, Q / int), an exact division by zero, or another
        # value or arithmetic fault: one STOP row, and build() wrote no READ file
        print(emit("STOP", [("reader", c.READER), ("reader_version", VERSION), ("reason", "qint"),
                            ("detail", ("%s:_%s" % (type(e).__name__, e))[:300])]))
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
