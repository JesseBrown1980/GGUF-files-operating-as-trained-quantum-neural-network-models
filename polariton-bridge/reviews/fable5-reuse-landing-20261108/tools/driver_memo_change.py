# The driver-side change for count-weighted reuse, rebased: the lane's proposed plan with the ENGINE-CHANGES pin of the
# landed file (row 19 after the jets row), the change record, the allowed binary, and the binary itself. json=0.
import hashlib
import os
import shutil
import stat

D = "C:/tmp/opus55/bridge-blind-driver-20261106/"
P = "C:/tmp/opus55/count-memo-20261106/rr/proposed/driver/"
EC_OLD = "3ecb0e6fd543e73a7196b0af090f43e224e50a8145b7b1edef79c5c6bf5a99f5"
EC_NEW = "f4f3f794da5db958d0ab614bb5f192547c8fdfd0b2103634805159bc95eee240"
BIN = "33e62fbe0837aeddc916a57d67848338cbc258aa1dfb85a01cfba53fb8a4e03f"


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def sha(p):
    return sha_b(open(p, "rb").read())


def keep(p, tag):
    q = p + ".pre-20261108-memo"
    assert not os.path.exists(q), q
    shutil.copyfile(p, q)
    os.chmod(q, stat.S_IREAD)
    return sha(q)


assert sha(D + "PLAN-BLIND.hbp") == "44b9547033839b48e5abe3e7c6ebe1d1ee3b471d53ee2db675ffa801a1724335"
assert sha(P + "PLAN-BLIND.hbp") == "63982c38e3786a0f4c8a9e6fd5f4cbc0832cbc05ca89e0b04ef7c32b4bcf0a7c"
cur = open(D + "PLAN-BLIND.hbp", "rb").read().decode("utf-8").split("\n")
prop = open(P + "PLAN-BLIND.hbp", "rb").read().decode("utf-8").split("\n")
assert len(cur) == len(prop)
diff = [i for i in range(len(cur)) if cur[i] != prop[i]]
ens = [i for i in range(len(cur)) if cur[i].startswith("PLAN_LAUNCH|") and "|phase=ensemble|" in cur[i]]
assert diff == [0] + ens and len(ens) == 347, (len(diff), len(ens))
for i in ens:
    fs = cur[i].replace("|binary_sha256=75530df9c7414b9a1b28f7408cbacd512f35d48836e2a6823beefb4941b9598d|", "|binary_sha256=%s|" % BIN, 1).split("|")
    ai = [j for j, f in enumerate(fs) if f.startswith("argv=")]
    assert len(ai) == 1
    fs[ai[0]] += "~memo=1"
    assert prop[i] == "|".join(fs), i
assert prop[0].count(EC_OLD) == 1 and sum(l.count(EC_OLD) for l in prop) == 1
prop[0] = prop[0].replace(EC_OLD, EC_NEW)
new_plan = "\n".join(prop).encode("utf-8")
assert b"\r" not in new_plan
k1 = keep(D + "PLAN-BLIND.hbp", "plan")
k2 = keep(D + "PLAN-BLIND.hbp.sha256", "sidecar")
k3 = keep(D + "run_blind.py", "driver")
open(D + "PLAN-BLIND.hbp", "wb").write(new_plan)
PS = sha_b(new_plan)
open(D + "PLAN-BLIND.hbp.sha256", "w", encoding="utf-8", newline="\n").write("%s  PLAN-BLIND.hbp\n" % PS)
# the change record: the lane's, with the landed ENGINE-CHANGES pin and row number, and a row saying why
c = open(P + "PLAN-BLIND-CHANGE-20261108-G-MEMO.hbp", encoding="utf-8", newline="").read()
for old, new, n in (("63982c38e3786a0f4c8a9e6fd5f4cbc0832cbc05ca89e0b04ef7c32b4bcf0a7c", PS, None),
                    ("ENGINE-CHANGES_sha256=" + EC_OLD, "ENGINE-CHANGES_sha256=" + EC_NEW, 1),
                    ("ENGINE-CHANGES.hbp_row_18", "ENGINE-CHANGES.hbp_row_19", None),
                    ("|engine_changes_row=18|", "|engine_changes_row=19|", 1)):
    k = c.count(old)
    assert k >= 1 and (n is None or k == n), (old, k)
    c = c.replace(old, new)
assert EC_OLD not in c
c += ("PLAN_CHANGE_REBASE|date=2026-11-08|seat=ACER-CLAUDE-FABLE5|why=the_lane_wrote_its_ENGINE-CHANGES_row_as_row_18_on_46b92e8;PR_#15's_head_c02c927_holds_the_jets_row_there,"
      "so_the_reuse_row_lands_as_row_19_and_ENGINE-CHANGES_reads_%s_in_place_of_%s|plan_lines_changed_by_this=the_head's_ENGINE-CHANGES_sha256_only|"
      "lane_plan_sha256=63982c38e3786a0f4c8a9e6fd5f4cbc0832cbc05ca89e0b04ef7c32b4bcf0a7c|plan_sha256_after=%s|kept=PLAN-BLIND.hbp.pre-20261108-memo(%s),run_blind.py.pre-20261108-memo(%s)|json=0\n"
      % (EC_NEW, EC_OLD, PS, k1, k3))
open(D + "PLAN-BLIND-CHANGE-20261108-G-MEMO.hbp", "w", encoding="utf-8", newline="\n").write(c)
open(D + "PLAN-BLIND-CHANGE-20261108-G-MEMO.hbp.sha256", "w", encoding="utf-8", newline="\n").write(
    "%s  PLAN-BLIND-CHANGE-20261108-G-MEMO.hbp\n" % sha(D + "PLAN-BLIND-CHANGE-20261108-G-MEMO.hbp"))
# the driver line and the binary
r = open(D + "run_blind.py", encoding="utf-8", newline="").read()
OLD = "BIN_ALLOWED = {'quantum': {bp.Q_BIN_SHA, '6bf8ebf2309700cb5be4cce25d82e5c4ee70fbc49521d4d7686cfc1649aa0a21'}, 'ensemble': {bp.E_BIN_SHA}, 'trajectory': {bp.T_SRC_SHA}}"
NEW = "BIN_ALLOWED = {'quantum': {bp.Q_BIN_SHA, '6bf8ebf2309700cb5be4cce25d82e5c4ee70fbc49521d4d7686cfc1649aa0a21'}, 'ensemble': {bp.E_BIN_SHA, '%s'}, 'trajectory': {bp.T_SRC_SHA}}" % BIN
OLDC = "# the binaries ENGINE-CHANGES names, by engine (2026-11-08: the Q = 0 sector binary, ENGINE-CHANGES row 17)"
NEWC = "# the binaries ENGINE-CHANGES names, by engine (2026-11-08: the Q = 0 sector binary, ENGINE-CHANGES row 17; twens 0.4.0, row 19)"
assert r.count(OLD) == 1 and r.count(OLDC) == 1
r = r.replace(OLD, NEW).replace(OLDC, NEWC)
open(D + "run_blind.py", "w", encoding="utf-8", newline="").write(r)
src = "C:/tmp/opus55/count-memo-20261106/rr/bin/engine/twens"
assert sha(src) == BIN
dst = D + "bin/twens-33e62fbe0837aedd"
shutil.copyfile(src, dst)
assert sha(dst) == BIN
print("DRIVER_CHANGE|plan_sha256=%s|change_sha256=%s|run_blind.py_sha256=%s|binary=%s|json=0" % (PS, sha(D + "PLAN-BLIND-CHANGE-20261108-G-MEMO.hbp"), sha(D + "run_blind.py"), sha(dst)))
