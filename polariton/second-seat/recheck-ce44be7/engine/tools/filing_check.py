# Step 4: the filing, through git show so that CRLF cannot mislead the read. Nothing is written in the worktree.
import hashlib
import subprocess

WT = "C:/tmp/qnn-polariton-wt"
HEAD = "ce44be742d9d59d07bb8ec8a9ed6a559da4ec0bd"
OUT = "C:/tmp/qnn-polariton-out/fourth"


def blob(rev, path):
    return subprocess.run(["git", "-C", WT, "show", "%s:%s" % (rev, path)], capture_output=True, check=True).stdout


def sha(data):
    return hashlib.sha256(data).hexdigest()


def row(tag, **kw):
    print(tag + "|" + "|".join("%s=%s" % kv for kv in kw.items()) + "|json=0")


pins = {
    "polariton/RECEIPT.hbp": "347480a5b9467017d07b9a52334edb1536c5b4e72df58c3a4afd85e2be0b9681",
    "polariton/read_prediction.py": "b1e14433d722b950cc45c970a8f0d75a163f1578bce31e3c73eb716c2c99329f",
    "polariton/READ.hbp": "f0f10236e6e50064c0e5790fb62160e69b1ae4c288e7c59e69cf84b4b57b1bb7",
    "polariton/second_route.py": "41638616460448a18304edbf90a406e59ab413f780ab4e122b579d7474e2a5d0",
    "polariton/SECOND-ROUTE.hbp": "bc8109c5e8994de9365496419d98990a43c6b65340258e9dd37bb0eb5d2ac916",
}
wf = blob(HEAD, ".github/workflows/polariton.yml").decode("utf-8")
for path, want in pins.items():
    data = blob(HEAD, path)
    row("PIN", file=path, in_workflow=int(want in wf), blob_sha_equal=int(sha(data) == want), cr_count=data.count(b"\r"), lf_count=data.count(b"\n"))

pred = blob(HEAD, "polariton/PREDICTION.hbp")
lines = pred.split(b"\n")
first29 = b"\n".join(lines[:29]) + b"\n"
want29 = "91d6a6e706c606be959cd8deb590f973a315fc923cf7589095aff8e489371f4e"
row("PREDICTION_29", head_sha=sha(first29), equal_pin=int(sha(first29) == want29), in_workflow=int(want29 in wf), rows_total=len([l for l in lines if l]), cr=pred.count(b"\r"))
fce = blob("fce08f9", "polariton/PREDICTION.hbp")
row("PREDICTION_FCE08F9", sha=sha(fce), rows=fce.count(b"\n"), equal_first29_of_head=int(fce == first29))

for rev in ("fce08f9", "099b0c6", "84778fb", "8dfa11a", "89a026a", HEAD):
    data = blob(rev, "polariton/PREDICTION.hbp")
    row("PREDICTION_AT", rev=rev[:7], rows=data.count(b"\n"), prefix_of_head=int(pred.startswith(data)), sha=sha(data)[:16])
at89 = blob("89a026a", "polariton/PREDICTION.hbp")
extra = pred[len(at89):].decode("utf-8").splitlines()
row("PREDICTION_SINCE_89A026A", rows_gained=len(extra), rows=";".join(l.split("|")[0] + ":" + l.split("|")[1] for l in extra))
at8 = blob("8dfa11a", "polariton/PREDICTION.hbp")
extra = pred[len(at8):].decode("utf-8").splitlines()
row("PREDICTION_SINCE_8DFA11A", rows_gained=len(extra), rows=";".join(l.split("|")[0] for l in extra))

# The third run's files against the 8dfa11a blobs.
for path in ("RECEIPT.hbp", "READ.hbp", "SECOND-ROUTE.hbp", "TIMING-LOCAL-20261104.hbp"):
    a = blob("8dfa11a", "polariton/" + path)
    b = blob(HEAD, "polariton/third-run/" + path)
    row("THIRD_RUN", file=path, equal_to_8dfa11a_blob=int(a == b), sha_8dfa11a=sha(a)[:16], sha_head=sha(b)[:16], cr_a=a.count(b"\r"), cr_b=b.count(b"\r"))
tree = subprocess.run(["git", "-C", WT, "ls-tree", "-r", HEAD, "polariton/third-run/"], capture_output=True, check=True).stdout.decode().splitlines()
row("THIRD_RUN_TREE", files=";".join(t.split("\t")[1].split("/")[-1] for t in tree))

# first-run unchanged since it was filed.
d = subprocess.run(["git", "-C", WT, "diff", "--stat", "8dfa11a", HEAD, "--", "polariton/first-run"], capture_output=True, check=True).stdout.decode()
row("FIRST_RUN_DIFF_SINCE_8DFA11A", lines=len(d.splitlines()))
d = subprocess.run(["git", "-C", WT, "log", "--format=%h", HEAD, "--", "polariton/first-run"], capture_output=True, check=True).stdout.decode().split()
row("FIRST_RUN_COMMITS", commits=",".join(d))

# The receipt's assembly from the fourth run's stage outputs.
stages = "taylor control reversal wavevector rotor quench_pin quench pin sector window conversion".split()
parts = []
for s in stages:
    data = open("%s/%s.out" % (OUT, s), "rb").read()
    row("STAGE_OUT", stage=s, bytes=len(data), cr=data.count(b"\r"), lines=data.count(b"\n"), done_rows=sum(l.startswith(b"POLARITON_DONE") for l in data.split(b"\n")))
    parts.extend(l for l in data.split(b"\n") if l and not l.startswith(b"POLARITON_DONE"))
built = b"\n".join(parts) + b"\n" + ("POLARITON_DONE|stages=%s|json=0\n" % ",".join(stages)).encode()
receipt = blob(HEAD, "polariton/RECEIPT.hbp")
row("RECEIPT_ASSEMBLY", built_sha=sha(built), receipt_sha=sha(receipt), equal=int(built == receipt), rows=receipt.count(b"\n"))
for name, path in (("RECEIPT.hbp", "polariton/RECEIPT.hbp"), ("READ.out", "polariton/READ.hbp"), ("route.out", "polariton/SECOND-ROUTE.hbp"), ("route-first-read.out", "polariton/SECOND-ROUTE-FIRST-READ.hbp")):
    a = open(OUT + "/" + name, "rb").read()
    b = blob(HEAD, path)
    row("OUT_VS_BLOB", out=name, blob=path, equal=int(a == b), cr_out=a.count(b"\r"))

# Timing file: stage lines against the out folder's timing.
tim = blob(HEAD, "polariton/TIMING-LOCAL-20261104.hbp")
errs = b"".join(open("%s/%s.err" % (OUT, s), "rb").read() for s in stages)
row("TIMING_FILE", bytes=len(tim), equal_to_concat_of_err=int(tim == errs), rows=tim.count(b"\n"))

# The second-seat filing against its own sums.
sums = blob(HEAD, "polariton/second-seat/SHA256SUMS").decode().splitlines()
good, bad, seen = 0, [], 0
for line in sums:
    if not line.strip():
        continue
    want, name = line.split(None, 1)
    name = name.lstrip("*").strip()
    seen += 1
    try:
        got = sha(blob(HEAD, "polariton/second-seat/" + name))
    except subprocess.CalledProcessError:
        bad.append(name + ":absent")
        continue
    if got == want:
        good += 1
    else:
        bad.append(name)
row("SECOND_SEAT_SUMS", listed=seen, good=good, bad=len(bad), first_bad=",".join(bad[:5]))

# Is the engine source pinned anywhere? Which tracked paths does the workflow hash?
row("WORKFLOW_HASHES", sha256sum_targets=";".join(sorted(set(l.split("sha256sum ")[1].split(" ")[0] for l in wf.splitlines() if "sha256sum " in l))))
row("WORKFLOW_MENTIONS", cargo_toml_hash=int("sha256sum Cargo.toml" in wf), gitattributes_hash=int("sha256sum .gitattributes" in wf), engine_hash=int("sha256sum src/bin" in wf), added_rows_hash=int("sed -n" in wf), toolchain_in_paths=int("rust-toolchain" in wf))
