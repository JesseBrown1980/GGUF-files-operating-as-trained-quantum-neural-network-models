# Land count-weighted reuse (twens 0.4.0, holds H1-H8) on PR #15's head c02c927, rebased from 46b92e8. json=0.
import hashlib
import os
import shutil
import subprocess

WT = "C:/tmp/qnn-bridge-wt/"
PB = WT + "polariton-bridge/"
LANE = "C:/tmp/opus55/count-memo-20261106/rr/proposed/repo/"
REV = "C:/tmp/opus55/review-memo-20261108/proposed/repo/"
M = "C:/tmp/opus55/reuse-landing-20261108/m/"
GR = "C:/tmp/opus55/reuse-gate-run-20261108/"
SP = "C:/Users/acer/AppData/Local/Temp/claude/C--Users-acer/81118dc5-cc7e-4fd7-a2e3-32a1a175bed9/scratchpad/"
LAND = PB + "reviews/fable5-reuse-landing-20261108/"
rows = []


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def sha(p):
    return sha_b(open(p, "rb").read())


def git(*a):
    return subprocess.run(["git", "-C", WT] + list(a), capture_output=True, text=True, check=True).stdout


def head_bytes(path):
    return subprocess.run(["git", "-C", WT, "show", "c02c927:" + path], capture_output=True, check=True).stdout


def put(dst, b):
    assert b"\r" not in b, dst
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "wb").write(b)


assert git("rev-parse", "HEAD").strip().startswith("c02c927"), "worktree head"
assert git("status", "--porcelain").strip() == "", "worktree not clean"
# H1: the engine, byte copies; the files at the PR head must be the 46b92e8 versions the lane replaced
H1 = {"engines/ensemble/src/main.rs": ("723b36745af6c926849ff7a6da74d8c82007dfc4071761795bb639fcd8d4a609", "1d768fa9aba719d0439625f08ea2711cc0d28a5e751b25a81667b4b3d5fcacbb"),
      "engines/ensemble/Cargo.toml": ("ee2f0e6650f8ca7b9cc4bbdacca0e5d26a60f32d5fe7312297ef0214dd3550a8", "9dcc6a6ea537c0ce926cb86c1e33116b1c37cfab7da56446bfce68eab1b6df94"),
      "engines/ensemble/Cargo.lock": ("9c57df215dea030065e5721271525367be7498f3708cef641cf2c187f2a5bea4", "44f9051fb25b2aa44aefffb9edd7eb8ac5935fcab786d9e72a06052af2be46d0")}
for rel, (old, new) in H1.items():
    assert sha_b(head_bytes("polariton-bridge/" + rel)) == old, rel
    b = open(LANE + "polariton-bridge/" + rel, "rb").read()
    assert sha_b(b) == new, rel
    put(PB + rel, b)
    rows.append("LANDING_FILE|hold=H1|path=polariton-bridge/%s|from_sha256=%s|to_sha256=%s|how=byte_copy|json=0" % (rel, old, new))
# H2: the amendment, byte copy
AM = "AMENDMENT-2026-11-06-G-MEMO.hbp"
b = open(LANE + "polariton-bridge/" + AM, "rb").read()
assert sha_b(b) == "9ca167ef7c63ce730e52e16b18fe24c19fb80138f8a67b532a979f86d589c6eb"
assert not os.path.exists(PB + AM)
put(PB + AM, b)
rows.append("LANDING_FILE|hold=H2|path=polariton-bridge/%s|to_sha256=%s|how=byte_copy|json=0" % (AM, sha_b(b)))
# H3: ENGINE-CHANGES = the PR head's 18 lines (17 rows + the jets row) + the reuse row as row 19, its review field filled in
ec_head = head_bytes("polariton-bridge/ENGINE-CHANGES.hbp")
assert sha_b(ec_head) == "ce5ddb85" + sha_b(ec_head)[8:] and ec_head.endswith(b"\n")
lane_ec = open(LANE + "polariton-bridge/ENGINE-CHANGES.hbp", "rb").read()
assert sha_b(lane_ec) == "3ecb0e6fd543e73a7196b0af090f43e224e50a8145b7b1edef79c5c6bf5a99f5"
base_ec = subprocess.run(["git", "-C", WT, "show", "46b92e8:polariton-bridge/ENGINE-CHANGES.hbp"], capture_output=True, check=True).stdout
assert lane_ec.startswith(base_ec) and ec_head.startswith(base_ec)
memo_row = lane_ec[len(base_ec):].decode("utf-8")
assert memo_row.count("\n") == 1 and memo_row.endswith("\n")
OLD_REV = "|review=OPEN(a_second-seat_review_before_the_ensemble_phase)|"
NEW_REV = ("|review=PASS_WITH_HOLDS(second_seat,opus55,review-memo-20261108;twens_0.4.0,binary_33e62fbe;holds_H1-H8_applied,H4_and_H5_in_the_review's_versions;"
           "12_planted_faults,11_caught_by_the_tests,the_batches_or_the_CI_step,F8_stopped_by_the_engine's_count_check;review_seal_64d08a23b2023b1951b5dddd73dcc1dae9ea23e0f7e953603ed1649d97b9e19d;"
           "the_cloud_seat's_acceptance_gate_result=EQUAL_with_its_controls_failing_by_name,reviews/fable5-reuse-landing-20261108/)|")
assert memo_row.count(OLD_REV) == 1
memo_row = memo_row.replace(OLD_REV, NEW_REV)
ec_new = ec_head + memo_row.encode("utf-8")
put(PB + "ENGINE-CHANGES.hbp", ec_new)
EC_SHA = sha_b(ec_new)
rows.append("LANDING_FILE|hold=H3|path=polariton-bridge/ENGINE-CHANGES.hbp|from_sha256=%s|to_sha256=%s|how=the_PR_head's_18_lines_byte_for_byte_then_the_lane's_reuse_row_as_row_19(the_lane_wrote_it_as_row_18_on_46b92e8,where_row_18_did_not_yet_hold_the_jets_row)|field_changed=review:OPEN->PASS_WITH_HOLDS(as_the_jets_row_18_records_its_review)|lane_sha256=3ecb0e6fd543e73a7196b0af090f43e224e50a8145b7b1edef79c5c6bf5a99f5|json=0" % (sha_b(ec_head), EC_SHA))
# H4: README, three-way merge of the review's version (base 46b92e8) onto the PR head, one conflict resolved by hand
t = open(M + "README.merged", encoding="utf-8", newline="").read()
a, rest = t.split("<<<<<<< README.ours\n", 1)
_, rest = rest.split("=======\n", 1)
_, z = rest.split(">>>>>>> README.theirs\n", 1)
assert "<<<<<<<" not in z and "=======\n" not in a + z
RES = """- [`ENGINE-CHANGES.hbp`](ENGINE-CHANGES.hbp) holds one row per engine change's result and per second-seat check: 4 for the
  quantum engine, 8 for the ensemble integrator, 5 for the trajectory integrator, 1 for the flow-map jet.
- The workflow `.github/workflows/polariton-bridge.yml` runs four jobs: `frozen` (PREDICTION.hbp at its pin, every
  SHA256SUMS, LF line endings), `ensemble` (the Rust 1.81 gate, the float scan, binary provenance, the guard's refusals,
  TEST-RUNS-T1B.hbp byte for byte, and `memo=1` against the plain path on four allowed batches with the rows pinned to
  twens 0.3.0's) and `trajectory` (the engine's sums, the reserved check, the tests with and without
  -O, the float scan, the audit, the line-446 gate) and `jet` (the Rust 1.81 gate, the float scan, binary provenance, the
  guard's refusals, the driver's dry run, one analog jet byte for byte).
"""
t = a + RES + z
OLD_B = "  [`reviews/opus55-count-memo-20261106/`](reviews/opus55-count-memo-20261106/).\n"
assert t.count(OLD_B) == 1
t = t.replace(OLD_B, OLD_B[:-1] + " The cloud seat's acceptance gate, run on this engine before the push\n"
              "  (`result=EQUAL` in union and staircase modes, its controls and two planted reuse faults failing by name), and the\n"
              "  rebase onto the jets head are in [`reviews/fable5-reuse-landing-20261108/`](reviews/fable5-reuse-landing-20261108/).\n")
for k, n in (("4 for the\n  quantum engine, 8 for the ensemble integrator", 1),):
    assert t.count(k) == n
put(PB + "README.md", t.encode("utf-8"))
rows.append("LANDING_FILE|hold=H4|path=polariton-bridge/README.md|from_sha256=%s|to_sha256=%s|how=git_merge-file(ours=c02c927,base=46b92e8,theirs=the_review's_34bd5007),one_conflict(the_ENGINE-CHANGES_count_and_the_workflow's_jobs)_joined:quantum_4,ensemble_8,trajectory_5,jet_1;four_jobs;one_sentence_added_pointing_at_this_folder|json=0" % (sha_b(head_bytes("polariton-bridge/README.md")), sha(PB + "README.md")))
# H6: the workflow, a clean three-way merge
y = open(M + "yml.merged", "rb").read()
assert b"<<<<<<<" not in y
put(WT + ".github/workflows/polariton-bridge.yml", y)
rows.append("LANDING_FILE|hold=H6|path=.github/workflows/polariton-bridge.yml|from_sha256=%s|to_sha256=%s|how=git_merge-file(ours=c02c927,base=46b92e8,theirs=the_lane's_079a18e0),clean|json=0" % (sha_b(head_bytes(".github/workflows/polariton-bridge.yml")), sha_b(y)))
# H7, H8: the two review folders, byte copies, each checked against its own SHA256SUMS
for hold, src in (("H7", LANE + "polariton-bridge/reviews/opus55-count-memo-20261106/"), ("H8", REV + "polariton-bridge/reviews/opus55-review-memo-20261108/")):
    dst = PB + "reviews/" + os.path.basename(src.rstrip("/")) + "/"
    assert not os.path.exists(dst)
    n = 0
    for root, _, files in os.walk(src):
        for f in files:
            s = os.path.join(root, f)
            put(dst + os.path.relpath(s, src).replace("\\", "/"), open(s, "rb").read())
            n += 1
    ok = 0
    for line in open(dst + "SHA256SUMS", encoding="utf-8"):
        h, p = line.rstrip("\n").split(None, 1)
        assert sha(dst + p.lstrip("*")) == h, p
        ok += 1
    rows.append("LANDING_FOLDER|hold=%s|path=polariton-bridge/reviews/%s/|files=%d|sha256sums_checked=%d|SHA256SUMS_sha256=%s|how=byte_copy|json=0" % (hold, os.path.basename(dst.rstrip("/")), n, ok, sha(dst + "SHA256SUMS")))
# the landing folder: the cloud seat's gate as run here, its scripts, and these rows
os.makedirs(LAND, exist_ok=True)
for f in ("GATE-RUN.hbp", "GATE-RUN-K4.hbp", "GATE-RUN-K4BIG.hbp"):
    put(LAND + f, open(GR + f, "rb").read())
for f in ("reuse_gate_run.sh", "reuse_gate_k4.sh", "reuse_gate_k4big.sh", "land_memo.py"):
    put(LAND + "tools/" + f, open(SP + f, "rb").read())
for f in ("twens03.stdout", "twens04.stdout", "twens04-memo.stdout"):
    put(LAND + "baseline/" + f, open(GR + f, "rb").read())
# H5: the stage's SHA256SUMS = the PR head's, with the five changed lines replaced and the amendment's line after the F amendment's
s_head = head_bytes("polariton-bridge/SHA256SUMS").decode("utf-8").split("\n")
assert s_head[-1] == ""
CH = {"README.md": sha(PB + "README.md"), "ENGINE-CHANGES.hbp": EC_SHA}
CH.update({k: v[1] for k, v in H1.items()})
out, seen = [], set()
for line in s_head[:-1]:
    h, p = line.split(" ", 1)
    if p in CH:
        line = "%s %s" % (CH[p], p)
        seen.add(p)
    out.append(line)
    if p == "AMENDMENT-2026-11-06-F-SAMPLING.hbp":
        out.append("%s %s" % (sha(PB + AM), AM))
        seen.add(AM)
assert seen == set(CH) | {AM}, seen
s_new = ("\n".join(out) + "\n").encode("utf-8")
put(PB + "SHA256SUMS", s_new)
bad = 0
for line in out:
    h, p = line.split(" ", 1)
    bad += sha(PB + p) != h
assert bad == 0
rows.append("LANDING_FILE|hold=H5|path=polariton-bridge/SHA256SUMS|from_sha256=%s|to_sha256=%s|how=the_PR_head's_%d_lines,5_replaced(README,ENGINE-CHANGES,main.rs,Cargo.toml,Cargo.lock),the_G_amendment's_line_inserted_after_the_F_amendment's|lines_checked=%d_of_%d|json=0" % (sha_b(head_bytes("polariton-bridge/SHA256SUMS")), sha_b(s_new), len(s_head) - 1, len(out), len(out)))
frozen = {"PREDICTION.hbp": "fadd84122e820cc03e9a4d6d5dd47fe7118ab4b16e1d4db93a601fb44c90b892", "AMENDMENT-2026-11-06-F-SAMPLING.hbp": "60c403d3cc55878fcea1859542bf80b7c72886e530204697df02fcc087e779ec", "CORRECTIONS.hbp": "9bfdd27d9b418cb71835a870e527f8e4c83f412aab8bd148c56539af597e9e99"}
for p, h in frozen.items():
    assert sha(PB + p) == h, p
rows.append("LANDING_FROZEN|PREDICTION.hbp=fadd8412|AMENDMENT-F=60c403d3|CORRECTIONS=9bfdd27d|blind/jets-20261108*=untouched_by_this_commit(git_diff_shows_no_path_under_blind/)|json=0")
rows.append("LANDING_ENGINE_CHANGES_PIN|ENGINE-CHANGES_sha256=%s|for=the_driver's_PLAN-BLIND.hbp_head(replaces_the_lane's_3ecb0e6f,which_assumed_row_18_on_46b92e8)|json=0" % EC_SHA)
open(LAND + "LANDING.hbp", "w", encoding="utf-8", newline="\n").write("\n".join(rows) + "\n")
print("EC_SHA=" + EC_SHA)
print("\n".join(r[:220] for r in rows))
