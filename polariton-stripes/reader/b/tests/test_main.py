"""The READ-file audit of stripes_read_b/__main__.py on a small hand-built READ file: one read per PREDICT row."""

import contextlib
import io
import os
import re
import shutil
import subprocess
import sys
import unittest

import stripes_read_b.__main__ as sb
from stripes_read_b import VERSION, qint
from stripes_read_b import common as c
from stripes_read_b import frozen
from stripes_read_b.exact import ExactError
from stripes_read_b.hbp import sha256_hex

from .util import TempDir

FZ = frozen.load()
ORDER = [d["id"] for k, d, _ in FZ.rows if k == "STRIPES_PREDICT"]


def read_row(rid, read="r1", scored=True, why="symmetry", verdict=c.MET):
    return ("STRIPES_READ|row=%s|read=%s|at=x|kind=exact|scored=%d|why=%s|value=none|lo=none|hi=none|band=none|"
            "frozen=none|verdict=%s|detail=none|json=0" % (rid, read, 1 if scored else 0, why, verdict))


def verdict_row(rid, reads=2, scored=1, met=1, miss=0, falsifier="none", verdict=c.MET):
    p = FZ.predict(rid)
    return ("STRIPES_VERDICT|row=%s|name=%s|tag=%s|reads=%d|scored=%d|report=%d|met=%d|miss=%d|not_resolved=0|"
            "not_measured=0|falsifier=%s|verdict=%s|json=0" % (rid, p["name"], p["tag"], reads, scored,
                                                               reads - scored, met, miss, falsifier, verdict))


def build(reads=None, verdicts=None):
    head = ("STRIPES_READ_HEAD|reader=stripes-read-b|reader_version=%s|frozen=polariton-stripes/"
            "PREDICTION-STRIPE-PHASE.hbp|frozen_sha256=%s|rows=%s|json=0" % (VERSION, FZ.sha256, ",".join(ORDER)))
    reads = reads or {rid: [read_row(rid), read_row(rid, "r2", False, "X08", c.REPORT)] for rid in ORDER}
    verdicts = verdicts or {rid: verdict_row(rid) for rid in ORDER}
    body = [head] + [x for rid in ORDER for x in reads[rid]] + [verdicts[rid] for rid in ORDER]
    h = sha256_hex("".join(x + "\n" for x in body).encode("ascii"))
    return body + ["STRIPES_READ_END|rows=%d|sha256=%s|json=0" % (len(body), h)]


def reason(lines, table=False):
    try:
        sb.audit_lines(lines, FZ, table=table)
    except c.StageBStop as e:
        return e.reason
    return None


class Audit(unittest.TestCase):
    def test_clean_file(self):
        self.assertIsNone(reason(build()))

    def test_scoring_table_of_the_reader(self):
        lines = build()
        self.assertEqual(reason(lines, table=None), "scoring_table")  # SCORING is the real rows' table
        got = sb.audit_lines(lines, FZ, table=False)
        self.assertIsNone(reason(lines, table=got))
        tbl = dict(got)
        tbl["E15"] = (2, 2, tbl["E15"][2])
        self.assertEqual(reason(lines, table=tbl), "scoring_table")

    def test_end_hash(self):
        lines = build()
        lines[1] = lines[1].replace("|value=none|", "|value=1|")
        self.assertEqual(reason(lines), "read_file_sha256")

    def test_promoted_read(self):
        reads = {rid: [read_row(rid), read_row(rid, "r2", False, "X08", c.REPORT)] for rid in ORDER}
        reads["E17"][1] = read_row("E17", "r2", True, "X08", c.MET)
        v = {rid: verdict_row(rid) for rid in ORDER}
        v["E17"] = verdict_row("E17", scored=2, met=2)
        self.assertEqual(reason(build(reads, v)), "scored_read")

    def test_falsifier_on_report_read(self):
        v = {rid: verdict_row(rid) for rid in ORDER}
        v["E17"] = verdict_row("E17", falsifier="r2:" + FZ.predict("E17")["falsifier"], verdict=c.NOT_MET)
        self.assertEqual(reason(build(verdicts=v)), "falsifier")
        v["E17"] = verdict_row("E17", falsifier="r1:not_the_frozen_text", verdict=c.NOT_MET)
        self.assertEqual(reason(build(verdicts=v)), "falsifier")
        v["E17"] = verdict_row("E17", falsifier="r1:" + FZ.predict("E17")["falsifier"], verdict=c.NOT_MET)
        self.assertIsNone(reason(build(verdicts=v)))

    def test_counts_and_verdict_rule(self):
        v = {rid: verdict_row(rid) for rid in ORDER}
        v["Q03"] = verdict_row("Q03", met=0)
        self.assertEqual(reason(build(verdicts=v)), "verdict_counts")
        v["Q03"] = verdict_row("Q03", verdict=c.NOT_RESOLVED)
        self.assertEqual(reason(build(verdicts=v)), "verdict_rule")
        reads = {rid: [read_row(rid), read_row(rid, "r2", False, "X08", c.REPORT)] for rid in ORDER}
        reads["Q03"][0] = read_row("Q03", verdict=c.MISS)
        v["Q03"] = verdict_row("Q03", met=0, miss=1, verdict=c.NOT_MET)
        self.assertIsNone(reason(build(reads, v)))

    def test_one_verdict_per_predict_row(self):
        lines = build()
        drop = [k for k, ln in enumerate(lines) if ln.startswith("STRIPES_VERDICT|row=E09|")][0]
        body = lines[:drop] + lines[drop + 1:-1]
        h = sha256_hex("".join(x + "\n" for x in body).encode("ascii"))
        self.assertEqual(reason(body + ["STRIPES_READ_END|rows=%d|sha256=%s|json=0" % (len(body), h)]),
                         "verdict_rows")

    def test_row_verdict_rule(self):
        met, miss = {"verdict": c.MET}, {"verdict": c.MISS}
        nm, nr = {"verdict": c.NOT_MEASURED}, {"verdict": c.NOT_RESOLVED}
        self.assertEqual(sb._row_verdict([met, met], False), c.MET)
        self.assertEqual(sb._row_verdict([met, miss], False), c.NOT_MET)
        self.assertEqual(sb._row_verdict([met], True), c.NOT_MET)
        self.assertEqual(sb._row_verdict([], False), c.NONE)
        self.assertEqual(sb._row_verdict([nm, nm], False), c.NOT_MEASURED)
        self.assertEqual(sb._row_verdict([met, nr], False), c.NOT_RESOLVED)
        self.assertEqual(sb._row_verdict([met, nm], False), c.NOT_RESOLVED)

    def test_rules_agree_with_common(self):
        for outs, fals in (((c.MET, c.MET), False), ((c.MET, c.MISS), False), ((c.NOT_MEASURED,), False),
                           ((c.MET, c.NOT_RESOLVED), False), ((c.MET,), True)):
            rs = [c.Read("T", "r%d" % k, "x", "exact", c.scored(), o) for k, o in enumerate(outs)]
            self.assertEqual(sb._row_verdict([{"verdict": r.verdict} for r in rs], fals), c.row_verdict(rs, fals))


FLOAT_EVIDENCE = os.path.join(os.path.dirname(sb.B_DIR), "check", "float_evidence.py")


def git(repo, *args, data=None):
    p = subprocess.run(["git", "-C", repo] + list(args), input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       check=False)
    if p.returncode != 0:
        raise AssertionError("git %s: %s" % (" ".join(args), p.stderr.decode("ascii", "replace")[-300:]))
    return p.stdout


def index_pin(repo, rel):
    """The tree pin of rel/ from git's index alone (review M2): each mode from `git ls-files -s`, each sha256 from the
    index's blob, never from the working tree."""
    rows = []
    for rec in git(repo, "ls-files", "-s", "-z", "--", rel).split(b"\0"):
        if rec:
            meta, path = rec.split(b"\t", 1)
            mode, oid, _ = meta.decode("ascii").split(" ")
            rows.append((path, mode, oid))
    rows.sort()
    out = git(repo, "cat-file", "--batch", data="".join(r[2] + "\n" for r in rows).encode("ascii"))
    lines, k = [], 0
    for path, mode, oid in rows:
        nl = out.index(b"\n", k)
        head = out[k:nl].decode("ascii").split(" ")
        if head[:2] != [oid, "blob"]:
            raise AssertionError("cat-file " + " ".join(head))
        size = c.canon_int(head[2])
        lines.append("%s %s %s\n" % (mode, sha256_hex(out[nl + 1:nl + 1 + size]), path.decode("utf-8")))
        k = nl + 1 + size + 1
    return sha256_hex("".join(lines).encode("utf-8"))


def scratch_repo(root):
    """A git repository laid out like this one, with a small reader/b in its index; returns (repo, b_dir)."""
    b = os.path.join(root, "polariton-stripes", "reader", "b")
    os.makedirs(os.path.join(b, "pkg", "__pycache__"))
    for rel, text in (("run.py", "x = 1\n"), ("pkg/a.py", "y = 2\n"), ("pkg/__pycache__/a.cpython.pyc", "")):
        with open(os.path.join(b, rel), "w") as f:
            f.write(text)
    os.chmod(os.path.join(b, "run.py"), 0o755)
    with open(os.path.join(root, ".gitignore"), "w") as f:
        f.write("__pycache__/\n")
    git(root, "init", "-q")
    git(root, "config", "core.filemode", "true")
    git(root, "add", "-A")
    return root, b


class Provenance(unittest.TestCase):
    """The READ file names the stage B that wrote it (quantum review 2, M3), and stray floats end in a STOP row."""

    def test_version(self):
        self.assertEqual((VERSION, c.READER_VERSION), ("0.2.0", "0.2.0"))

    def test_tree_pin(self):
        if not os.path.exists(os.path.join(sb.REPO, ".git")):
            self.skipTest("no git checkout around this stage B")
        path, pin = sb.stage_b_tree()
        self.assertEqual(path, "polariton-stripes/reader/b")
        self.assertTrue(re.fullmatch("[0-9a-f]{64}", pin))
        # review M2: the pin of git's index alone (modes and blobs), not a second reader of the working tree
        want = index_pin(sb.REPO, path)
        if pin != want:
            changed = git(sb.REPO, "diff", "--name-only", "--", path).decode("utf-8", "replace").split()
            self.fail("stage B's pin %s, git's index gives %s; stage these edits first: %s" % (
                pin, want, ",".join(changed) or "none"))
        p = subprocess.run([sys.executable, "-I", FLOAT_EVIDENCE, "--repo", sb.REPO, "--pins", path + "/"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual((p.returncode, p.stdout.decode("ascii")), (0, "%s/ | tree=%s | \n" % (path, want)))

    def test_tree_pin_takes_modes_from_the_index(self):
        with TempDir() as d:
            repo, b = scratch_repo(d)
            rel = "polariton-stripes/reader/b"
            self.assertEqual(sb.stage_b_tree(b, repo), (rel, index_pin(repo, rel)))
            # a checkout with core.filemode=false (Windows, WSL /mnt/c) reads every file as 100755: the gate keeps
            # the index pin, and stage B refuses to write a READ file there
            git(repo, "config", "core.filemode", "false")
            os.chmod(os.path.join(b, "pkg", "a.py"), 0o755)
            p = subprocess.run([sys.executable, "-I", FLOAT_EVIDENCE, "--repo", repo, "--pins", rel + "/"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            self.assertEqual((p.returncode, p.stdout.decode("ascii")), (0, "%s/ | tree=%s | \n" % (
                rel, index_pin(repo, rel))))
            with self.assertRaises(c.StageBStop) as cm:
                sb.stage_b_tree(b, repo)
            self.assertEqual(cm.exception.reason, "stage_b_modes")
            # with core.filemode=true the gate refuses an unstaged mode change too
            git(repo, "config", "core.filemode", "true")
            p = subprocess.run([sys.executable, "-I", FLOAT_EVIDENCE, "--repo", repo, "--pins", rel + "/"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            self.assertEqual(p.returncode, 1)
            self.assertIn("|mode_not_in_the_index=%s/pkg/a.py:100644:100755|" % rel, p.stdout.decode("ascii"))
            os.chmod(os.path.join(b, "pkg", "a.py"), 0o644)
            # the index's mode, not the file system's: an index mode change moves the pin
            before = sb.stage_b_tree(b, repo)[1]
            git(repo, "update-index", "--chmod=+x", rel + "/pkg/a.py")
            with self.assertRaises(c.StageBStop) as cm:
                sb.stage_b_tree(b, repo)
            self.assertEqual(cm.exception.reason, "stage_b_modes")
            os.chmod(os.path.join(b, "pkg", "a.py"), 0o755)
            self.assertNotEqual(sb.stage_b_tree(b, repo)[1], before)
            self.assertEqual(sb.stage_b_tree(b, repo)[1], index_pin(repo, rel))

    def test_tree_pin_refuses_files_git_does_not_hold(self):
        with TempDir() as d:
            repo, b = scratch_repo(d)
            rel = "polariton-stripes/reader/b"
            with open(os.path.join(b, "pkg", "new.py"), "w") as f:
                f.write("z = 3\n")
            with self.assertRaises(c.StageBStop) as cm:
                sb.stage_b_tree(b, repo)
            self.assertEqual((cm.exception.reason, cm.exception.detail), ("stage_b_tree", "not in git's index: " + rel
                                                                          + "/pkg/new.py"))
            p = subprocess.run([sys.executable, "-I", FLOAT_EVIDENCE, "--repo", repo, "--pins", rel + "/"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            self.assertEqual(p.returncode, 1)
            self.assertIn("|untracked=%s/pkg/new.py|" % rel, p.stdout.decode("ascii"))
            git(repo, "add", rel + "/pkg/new.py")
            self.assertEqual(sb.stage_b_tree(b, repo)[1], index_pin(repo, rel))
            os.remove(os.path.join(b, "pkg", "new.py"))
            with self.assertRaises(c.StageBStop) as cm:
                sb.stage_b_tree(b, repo)
            self.assertEqual(cm.exception.reason, "stage_b_tree")
            p = subprocess.run([sys.executable, "-I", FLOAT_EVIDENCE, "--repo", repo, "--pins", rel + "/"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            self.assertIn("|not_in_the_working_tree=%s/pkg/new.py|" % rel, p.stdout.decode("ascii"))
        with TempDir() as d:
            # no git checkout around stage B: no pin, so no READ file
            with self.assertRaises(c.StageBStop) as cm:
                sb.stage_b_tree(os.path.join(d), d)
            self.assertEqual(cm.exception.reason, "stage_b_tree")

    def test_stage_a_tree_is_the_git_tree_of_reader_a(self):
        # review M4: the reader_a note names stage A's source as the git tree of reader/a
        with TempDir() as d:
            repo, _ = scratch_repo(d)
            rel = "polariton-stripes/reader/a"
            a = os.path.join(repo, *rel.split("/"))
            # a name that sorts beside a folder's ("src.rs" before "src/"), nested folders, an executable file
            for path, text in (("Cargo.toml", "[package]\n"), ("src.rs", "x\n"), ("src/lib.rs", "pub fn f() {}\n"),
                               ("src/a-b.rs", "y\n"), ("tests/common/mod.rs", "z\n"), ("run.sh", "#!/bin/sh\n")):
                os.makedirs(os.path.dirname(os.path.join(a, path)), exist_ok=True)
                with open(os.path.join(a, path), "w") as f:
                    f.write(text)
            os.chmod(os.path.join(a, "run.sh"), 0o755)
            with open(os.path.join(repo, ".gitignore"), "a") as f:
                f.write("target/\n")
            git(repo, "add", "-A")
            git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "t")
            head = git(repo, "rev-parse", "HEAD:" + rel).decode("ascii").strip()
            self.assertEqual(sb.stage_a_tree(a, repo), (rel, head))
            os.makedirs(os.path.join(a, "target", "release"))
            with open(os.path.join(a, "target", "release", "stripes-read-a"), "w") as f:
                f.write("ignored\n")
            self.assertEqual(sb.stage_a_tree(a, repo), (rel, head), "an ignored build folder is not source")
            with open(os.path.join(a, "src", "lib.rs"), "a") as f:
                f.write("// edit\n")
            with self.assertRaises(c.StageBStop) as cm:
                sb.stage_a_tree(a, repo)
            self.assertEqual(cm.exception.reason, "stage_a_tree")
            self.assertIn(rel + "/src/lib.rs: working tree", cm.exception.detail)
            git(repo, "add", rel + "/src/lib.rs")
            staged = git(repo, "write-tree", "--prefix=" + rel + "/").decode("ascii").strip()
            self.assertNotEqual(staged, head)
            self.assertEqual(sb.stage_a_tree(a, repo), (rel, staged))
            with open(os.path.join(a, "build.rs"), "w") as f:
                f.write("fn main() {}\n")
            with self.assertRaises(c.StageBStop) as cm:
                sb.stage_a_tree(a, repo)
            self.assertEqual((cm.exception.reason, cm.exception.detail), ("stage_a_tree",
                                                                          "not in git's index: " + rel + "/build.rs"))
            os.remove(os.path.join(a, "build.rs"))
            os.chmod(os.path.join(a, "src.rs"), 0o755)
            with self.assertRaises(c.StageBStop) as cm:
                sb.stage_a_tree(a, repo)
            self.assertIn(rel + "/src.rs: working tree 100755", cm.exception.detail)
            os.chmod(os.path.join(a, "src.rs"), 0o644)
            os.remove(os.path.join(a, "src", "a-b.rs"))
            with self.assertRaises(c.StageBStop) as cm:
                sb.stage_a_tree(a, repo)
            self.assertEqual(cm.exception.detail, "in git's index, not in the working tree: " + rel + "/src/a-b.rs")
        with TempDir() as d:
            with self.assertRaises(c.StageBStop) as cm:
                sb.stage_a_tree(os.path.join(d, "a"), d)
            self.assertEqual(cm.exception.reason, "stage_a_tree")

    def test_stage_a_tree_of_this_checkout(self):
        if not os.path.exists(os.path.join(sb.REPO, ".git")):
            self.skipTest("no git checkout around this stage B")
        rel = "polariton-stripes/reader/a"
        try:
            path, tree = sb.stage_a_tree()
        except c.StageBStop as e:
            self.fail("%s: %s (stage reader/a first)" % (e.reason, e.detail))
        self.assertEqual(path, rel)
        self.assertTrue(re.fullmatch("[0-9a-f]{40}", tree))
        if subprocess.run(["git", "-C", sb.REPO, "diff", "--cached", "--quiet", "HEAD", "--", rel],
                          check=False).returncode == 0:
            self.assertEqual(tree, git(sb.REPO, "rev-parse", "HEAD:" + rel).decode("ascii").strip())

    def test_read_refuses_a_tree_whose_modes_git_does_not_hold(self):
        # review M2: build() (read, and verify after its audit) takes the tree pin first and writes nothing when a
        # working-tree mode differs from git's index
        with TempDir() as d:
            repo, b = scratch_repo(os.path.join(d, "repo"))
            os.chmod(os.path.join(b, "pkg", "a.py"), 0o755)
            out = os.path.join(d, "READ.hbp")
            text = io.StringIO()
            saved = sb.B_DIR, sb.REPO
            sb.B_DIR, sb.REPO = b, repo
            try:
                with contextlib.redirect_stdout(text):
                    rc = sb.main(["stripes_read_b", "read"] + [x for k in sb.INPUT_KEYS for x in (k, d)]
                                 + ["--out", out])
                with self.assertRaises(c.StageBStop) as cm:
                    sb.build(dict.fromkeys(sb.INPUT_KEYS, d))
            finally:
                sb.B_DIR, sb.REPO = saved
            self.assertEqual((rc, os.path.exists(out), cm.exception.reason), (3, False, "stage_b_modes"))
            self.assertIn("|reason=stage_b_modes|detail=polariton-stripes/reader/b/pkg/a.py:", text.getvalue())

    def test_no_flag_skips_the_sums(self):
        # review M3: --no-sums is gone from read and verify; any flag is a usage STOP
        for cmd in ("read", "verify"):
            argv = [x for k in sb.INPUT_KEYS for x in (k, "x")] + ["--out" if cmd == "read" else "--read", "y"]
            text = io.StringIO()
            with contextlib.redirect_stdout(text):
                rc = sb.main(["stripes_read_b", cmd, "--no-sums"] + argv)
            self.assertEqual(rc, 3)
            self.assertIn("|reason=usage|detail=--no-sums|", text.getvalue())
        self.assertNotIn("no-sums", sb.__doc__)

    def _main(self, fn):
        sb.COMMANDS["probe_exit"] = fn
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                rc = sb.main(["stripes_read_b", "probe_exit"])
        finally:
            del sb.COMMANDS["probe_exit"]
        return rc, out.getvalue()

    def test_stray_float_is_a_stop_row(self):
        rc, text = self._main(lambda argv: qint.make(1, 3) * qint.make(1, 2) + True)  # a bool is not an int here
        self.assertEqual(rc, 3)
        self.assertRegex(text, r"^STOP\|reader=stripes-read-b\|reader_version=%s\|reason=qint\|detail=QintError:" %
                         re.escape(VERSION))
        rc, text = self._main(lambda argv: qint.div(1, 0))
        self.assertEqual(rc, 3)
        self.assertIn("|reason=qint|detail=ZeroDivisionError:", text)

    def test_value_and_arithmetic_faults_are_stop_rows(self):
        # review N12: //, % and int() on a Q raise QintError; a ValueError or ArithmeticError is a STOP row too
        def arithmetic(argv):
            raise ArithmeticError("isqrt check failed")

        for fn, want in ((lambda argv: qint.make(1, 3) // 2, "QintError"), (lambda argv: qint.make(1, 3) % 2,
                                                                             "QintError"),
                         (lambda argv: int(qint.make(1, 3)), "QintError"), (lambda argv: divmod(qint.ONE, 2),
                                                                           "QintError"),
                         (lambda argv: qint.isqrt(-1), "ValueError"), (arithmetic, "ArithmeticError")):
            rc, text = self._main(fn)
            self.assertEqual(rc, 3)
            self.assertIn("|reason=qint|detail=%s:" % want, text)
            self.assertEqual(text.count("\n"), 1)

    def test_no_read_file_after_a_qint_stop(self):
        def build(a):
            raise ValueError("a value build() cannot use")

        saved = sb.build
        sb.build = build
        try:
            with TempDir() as d:
                out = os.path.join(d, "READ.hbp")
                text = io.StringIO()
                with contextlib.redirect_stdout(text):
                    rc = sb.main(["stripes_read_b", "read"] + [x for k in sb.INPUT_KEYS for x in (k, d)]
                                 + ["--out", out])
                self.assertEqual((rc, os.path.exists(out)), (3, False))
                self.assertIn("|reason=qint|detail=ValueError:", text.getvalue())
        finally:
            sb.build = saved


class FrozenFile(unittest.TestCase):
    """The frozen file and its README at their sha256 (review N1, N3, M8)."""

    def copy(self, d, edit=None, readme_edit=None, readme=True):
        path = os.path.join(d, frozen.FROZEN_NAME)
        with open(frozen.DEFAULT_PATH, "rb") as f:
            data = f.read()
        with open(path, "wb") as f:
            f.write(edit(data) if edit else data)
        if readme:
            with open(os.path.join(os.path.dirname(frozen.DEFAULT_PATH), "README.md"), "rb") as f:
                text = f.read()
            with open(os.path.join(d, "README.md"), "wb") as f:
                f.write(readme_edit(text) if readme_edit else text)
        return path

    def reason(self, path):
        try:
            frozen.Frozen(path)
        except c.StageBStop as e:
            return e.reason, e.detail
        return None

    def test_clean_copy_reads(self):
        with TempDir() as d:
            fz = frozen.Frozen(self.copy(d))
        self.assertEqual(fz.sha256, frozen.FROZEN_SHA256)
        # the rows are parsed from the bytes that were hashed (N3)
        self.assertEqual(sha256_hex("".join(ln + "\n" for ln in fz.lines).encode("ascii")), frozen.FROZEN_SHA256)
        self.assertEqual(len(fz.rows), 118)

    def test_moved_byte_is_a_stop(self):
        with TempDir() as d:
            moved = self.reason(self.copy(d, edit=lambda b: b[:100] + bytes([b[100] ^ 1]) + b[101:]))
            crlf = self.reason(self.copy(d, edit=lambda b: b.replace(b"\n", b"\r\n")))
            readme = self.reason(self.copy(d, readme_edit=lambda b: b + b"\n"))
            shutil.rmtree(d)
            os.makedirs(d)
            no_readme = self.reason(self.copy(d, readme=False))
        for got in (moved, crlf):
            self.assertEqual(got[0], "frozen_sha256")
            self.assertTrue(got[1].startswith(frozen.FROZEN_NAME + " sha256 "), got)
        self.assertEqual(readme[0], "frozen_sha256")
        self.assertTrue(readme[1].startswith("README.md sha256 "), readme)
        self.assertEqual(no_readme, ("frozen_sha256", "no README.md beside " + frozen.FROZEN_NAME))

    def test_moved_frozen_file_ends_read_with_a_stop_row(self):
        with TempDir() as d:
            path = self.copy(d, edit=lambda b: b + b"\n")
            saved = frozen.load
            frozen.load = lambda p=path: frozen.Frozen(p)
            try:
                text = io.StringIO()
                with contextlib.redirect_stdout(text):
                    rc = sb.main(["stripes_read_b", "read"] + [x for k in sb.INPUT_KEYS for x in (k, d)]
                                 + ["--out", os.path.join(d, "READ.hbp")])
            finally:
                frozen.load = saved
            self.assertEqual(rc, 3)
            self.assertIn("|reason=frozen_sha256|detail=%s_sha256_" % frozen.FROZEN_NAME, text.getvalue())
            self.assertFalse(os.path.exists(os.path.join(d, "READ.hbp")))

    def test_frozen_integers_are_canonical(self):
        # review N16: the frozen N, steps and row count go through canon_int ('+729' or '7_29' is not an int there)
        class Edited:
            def __init__(self, field, value):
                self.field, self.value = field, value
                self.rows = FZ.rows

            def row(self, kind, rid):
                d = dict(FZ.row(kind, rid))
                if (kind, rid) == ("STRIPES_POINT", "P07"):
                    d[self.field] = self.value
                return d

        self.assertTrue(c.check_tables(FZ))
        for field, value in (("N", "+729"), ("N", "7_29"), ("N", " 729"), ("steps", "128,192,+256")):
            with self.assertRaises(ExactError):
                c.check_tables(Edited(field, value))


if __name__ == "__main__":
    unittest.main()
