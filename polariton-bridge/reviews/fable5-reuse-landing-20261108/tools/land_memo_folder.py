# Finish polariton-bridge/reviews/fable5-reuse-landing-20261108/: driver rows, the dry run, README, SHA256SUMS. json=0.
import hashlib
import os

PB = "C:/tmp/qnn-bridge-wt/polariton-bridge/"
LAND = PB + "reviews/fable5-reuse-landing-20261108/"
D = "C:/tmp/opus55/bridge-blind-driver-20261106/"
L = "C:/tmp/opus55/reuse-landing-20261108/"
SP = "C:/Users/acer/AppData/Local/Temp/claude/C--Users-acer/81118dc5-cc7e-4fd7-a2e3-32a1a175bed9/scratchpad/"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def put(dst, b):
    assert b"\r" not in b, dst
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "wb").write(b)


put(LAND + "driver/PLAN-BLIND-CHANGE-20261108-G-MEMO.hbp", open(D + "PLAN-BLIND-CHANGE-20261108-G-MEMO.hbp", "rb").read())
put(LAND + "driver/DRY-ENSEMBLE.out", open(L + "DRY-ENSEMBLE.out", "rb").read())
put(LAND + "tools/driver_memo_change.py", open(SP + "driver_memo_change.py", "rb").read())
put(LAND + "tools/land_memo_folder.py", open(SP + "land_memo_folder.py", "rb").read())
dry = open(L + "DRY-ENSEMBLE.out", encoding="utf-8").read().split("\n")
counts = [r for r in dry if r.startswith("DRY_COUNTS|")][0]
rows = [
    "LANDING_DRIVER|plan=PLAN-BLIND.hbp|from_sha256=44b9547033839b48e5abe3e7c6ebe1d1ee3b471d53ee2db675ffa801a1724335|to_sha256=%s|lane_proposal_sha256=63982c38e3786a0f4c8a9e6fd5f4cbc0832cbc05ca89e0b04ef7c32b4bcf0a7c|difference_from_the_proposal=the_head's_ENGINE-CHANGES_sha256(f4f3f794_for_3ecb0e6f)|checked=348_lines_differ_from_44b95470:the_head_and_the_347_ensemble_rows,each_row_the_binary_sha256_and_~memo=1_at_the_end_of_argv|json=0" % sha(D + "PLAN-BLIND.hbp"),
    "LANDING_DRIVER|file=PLAN-BLIND-CHANGE-20261108-G-MEMO.hbp|sha256=%s|copy=driver/|json=0" % sha(D + "PLAN-BLIND-CHANGE-20261108-G-MEMO.hbp"),
    "LANDING_DRIVER|file=run_blind.py|from_sha256=35ba739d46c5d88a...(kept_as_run_blind.py.pre-20261108-memo)|to_sha256=%s|change=BIN_ALLOWED['ensemble']_gains_33e62fbe0837aeddc916a57d67848338cbc258aa1dfb85a01cfba53fb8a4e03f|json=0" % sha(D + "run_blind.py"),
    "LANDING_DRIVER|file=bin/twens-33e62fbe0837aedd|sha256=%s|json=0" % sha(D + "bin/twens-33e62fbe0837aedd"),
    "LANDING_DRY|%s" % counts,
    "LANDING_DRY|launches_with_twens-33e62fbe0837aedd_and_memo=1=%d|status_PENDING=%d|json=0" % (
        sum(1 for r in dry if r.startswith("DRY_LAUNCH|") and "twens-33e62fbe0837aedd" in r and "memo=1" in r),
        sum(1 for r in dry if r.startswith("DRY_LAUNCH|") and "|status=PENDING|" in r)),
    "LANDING_GATE|by=the_cloud_seat's_review-tools/cloud-seat-reuse-gate-20261108(SHA256SUMS_checked)|points=N81_delta1/2_y1/18,N729_delta-1/4_y1/27(allowed_in_bridge_plan.reserved_and_in_twens_guard)|"
    "baseline_0.3.0=byte_equal_to_its_filed_BASELINE.out|0.4.0_plain_and_memo=1=the_same_stdout(4daf841d...)|cross_files=8_of_8_equal_to_0.3.0_after_the_head_row|"
    "union=EQUAL(1722,1722,2648_fields)|stair=EQUAL(2928_fields)|controls=6_of_6_CONTROL_rows_fail_by_name_on_each_engine(the_gate's_README_says_7;its_filed_BASELINE.out_has_6_CONTROL_rows_plus_the_thread-invariance_row)|json=0",
    "LANDING_GATE_FAULTS|batch=N81_delta1/2_y1/18,mask_VNC,LOCK,20000_samples(K2_box_in_use:5481+8568_distinct_starts)|memo=EQUAL|F1_key_merges_two_starts=CMP_FAIL|check=sum_differs:zr:('TWB','0','LOCK')|F3_dropped_count=EQUAL(its_path,the_K4_ball,is_off_below_2^22_samples:k4=none)|json=0",
    "LANDING_GATE_FAULTS|batch=N81_delta1/2_y1/18,mask_V1,4194304=2^22_samples(K4_ball_in_use:3736948_in_core,3685002_distinct)|memo=EQUAL(264_fields)|F3_dropped_count=CMP_FAIL|check=sum_differs:zr:('TWENS','0','V1')|wall_ms=40352(0.3.0),38606(memo),41306(F3)|json=0",
    "LANDING_NOTE|H8_folder=26_files:SHA256SUMS,README.md_and_24_under_review/(the_review's_report_says_23);SHA256SUMS_lists_25,25_of_25_check|json=0",
]
with open(LAND + "LANDING.hbp", "a", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(rows) + "\n")
put(LAND + "README.md", """# Count-weighted reuse on PR #15: the acceptance gate and the landing, November 8, 2026

This folder records how twens 0.4.0 (`memo=1`) was placed on PR #15 and the cloud seat's acceptance gate as run on it before the push.

- **The engine and its review.** The build lane's files are in [`../opus55-count-memo-20261106/`](../opus55-count-memo-20261106/) and the second-seat review, verdict PASS_WITH_HOLDS, in [`../opus55-review-memo-20261108/`](../opus55-review-memo-20261108/). Holds H1–H8 are applied as the review gives them.
- **The rebase.** Both lanes worked on `46b92e8`. PR #15's head `c02c927` holds the jets row as row 18 of `ENGINE-CHANGES.hbp`, so the reuse row lands as row 19 and the file reads `f4f3f794…`. Its review field records the review, as the jets row does. The README and the workflow are three-way merges onto the jets head; [`LANDING.hbp`](LANDING.hbp) gives every file's hashes.
- **The cloud seat's gate** ([`GATE-RUN.hbp`](GATE-RUN.hbp)), at the allowed points N = 81, δ = 1/2, y = 1/18 and N = 729, δ = −1/4, y = 1/27:
  - 0.3.0 reproduces the gate's filed `BASELINE.out` byte for byte, and 0.4.0 plain and with `memo=1` give the same output;
  - union mode `result=EQUAL` on 1,722, 1,722 and 2,648 integer fields across the two engines, staircase mode `EQUAL` on 2,928;
  - the gate's six control rows fail by name on every engine.
- **Planted reuse faults** ([`GATE-RUN-K4.hbp`](GATE-RUN-K4.hbp), [`GATE-RUN-K4BIG.hbp`](GATE-RUN-K4BIG.hbp)):
  - F1, a key that merges two starts, fails as `sum_differs:zr` on a LOCK batch of 20,000 samples;
  - F3, a dropped count in the 4-ball path, fails as `sum_differs:zr` on a V1 batch of 2²² samples, the size at which that path is in use (3,685,002 distinct starts);
  - the correct engine reads `EQUAL` on both batches.
- **The driver.** `PLAN-BLIND.hbp` reads `3eca4df9…`: the build lane's proposal with the head's `ENGINE-CHANGES` pin set to `f4f3f794…`. The change record is in [`driver/`](driver/). The dry run accepts 347 of 347 ensemble launches, each running `twens-33e62fbe0837aedd` with `memo=1`, and the plan's total work is unchanged at 94353772847/16.
- **Frozen inputs** read the same as before: PREDICTION `fadd8412…`, the F amendment `60c403d3…`, CORRECTIONS `9bfdd27d…`, and every file under `blind/`.

The scripts that produced these rows are in [`tools/`](tools/).
""".encode("utf-8"))
names = []
for root, _, files in os.walk(LAND):
    for fn in files:
        rel = os.path.relpath(os.path.join(root, fn), LAND).replace("\\", "/")
        if rel != "SHA256SUMS":
            names.append(rel)
names.sort()
open(LAND + "SHA256SUMS", "w", encoding="utf-8", newline="\n").write("".join("%s  %s\n" % (sha(LAND + n), n) for n in names))
print("LANDING_FOLDER|files=%d|SHA256SUMS=%s|json=0" % (len(names) + 1, sha(LAND + "SHA256SUMS")))
