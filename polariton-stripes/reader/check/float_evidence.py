#!/usr/bin/env python3
"""float_evidence.py: the folder rows of polariton-stripes/FLOAT-EVIDENCE.txt, checked against the tree.

A folder row reads `folder/ | tree=H | reason`, the format of the 4D repo's scripts/FLOAT-EVIDENCE.txt. H is the
sha256 of one line per entry under the folder, `<mode> <sha256 of the bytes> <path>\\n`, in git's order (paths sorted
as bytes), the rule of tree_line and tree_pin in that repo's scripts/no_float_gate.py. The entries are git's index
under the folder (`git ls-files -s`, as that gate takes them): each mode comes from the index, never from the file
system, so a checkout with core.filemode=false (Windows, WSL /mnt/c) gives the pin a Linux checkout gives; the bytes
are read from the working tree. An untracked file under the folder, an unmerged entry, an index entry missing from
the working tree and a mode change git sees but the index does not hold are faults (stage a new file with git add
first). A staged new file, a staged mode change or an edited byte moves H.

    python3 -I float_evidence.py [--repo DIR]          checks every folder row; prints one row each, exit 1 on a fault
    python3 -I float_evidence.py [--repo DIR] --pins FOLDER/...   prints `FOLDER/ | tree=H | ` for a person to finish
    python3 -I float_evidence.py [--repo DIR] --folders            prints the listed folders, one per line"""

import hashlib
import os
import re
import stat
import subprocess
import sys

LIST = "polariton-stripes/FLOAT-EVIDENCE.txt"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class Fault(Exception):
    """A folder whose pin cannot be taken: the text is one field of a FLOAT_EVIDENCE row."""


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, check=False, stdin=subprocess.DEVNULL)
    if p.returncode != 0:
        raise Fault("git_%s_rc=%d" % (args[0], p.returncode))
    return p.stdout


def records(out):
    return [r for r in out.split(b"\0") if r]


def text(path):
    return path.decode("utf-8", "surrogateescape")


def index_entries(repo, folder):
    """[(mode, oid, path)] of git's index under folder (`git ls-files -s`), in git's order (paths sorted as bytes)."""
    rows = []
    for rec in records(git(repo, "ls-files", "-s", "-z", "--", folder)):
        meta, path = rec.split(b"\t", 1)
        mode, oid, stage = meta.decode("ascii").split(" ")
        if stage != "0":
            raise Fault("unmerged=" + text(path))
        rows.append((mode, oid, path))
    return sorted(rows, key=lambda r: r[2])


def entries(repo, folder):
    """[(mode, sha256, path)] of the files under folder, in git's order: the mode from git's index, the bytes from the
    working tree. Raises Fault on an untracked file, an index entry missing from the working tree, a mode change git
    sees in the working tree (git diff-files, which follows core.filemode) and a mode other than a file or a link."""
    untracked = records(git(repo, "ls-files", "-z", "--others", "--exclude-standard", "--", folder))
    if untracked:
        raise Fault("untracked=" + text(sorted(untracked, key=bytes)[0]))
    diff = records(git(repo, "diff-files", "-z", "--", folder))
    for meta, path in zip(diff[0::2], diff[1::2], strict=True):
        src, dst = meta.decode("ascii").lstrip(":").split(" ")[:2]
        if src != dst and dst != "000000":  # 000000: a deleted file, a fault below
            raise Fault("mode_not_in_the_index=%s:%s:%s" % (text(path), src, dst))
    rows = []
    for mode, _oid, p in index_entries(repo, folder):
        full = os.path.join(repo, text(p))
        try:
            if mode == "120000":
                data = os.readlink(full).encode("utf-8", "surrogateescape")
            elif mode in ("100644", "100755") and stat.S_ISREG(os.lstat(full).st_mode):
                with open(full, "rb") as f:
                    data = f.read()
            else:
                raise Fault("not_a_file=%s:%s" % (text(p), mode))
        except OSError as e:
            raise Fault("not_in_the_working_tree=" + text(p)) from e
        rows.append((mode, hashlib.sha256(data).hexdigest(), text(p)))
    return rows


def tree_line(mode, pin, path):
    return "%s %s %s\n" % (mode, pin, path)


def tree_pin(rows):
    return hashlib.sha256("".join(tree_line(*r) for r in rows).encode("utf-8", "surrogateescape")).hexdigest()


def parse_list(path):
    """{folder: H} of the folder rows, and the faults of the list; '#' lines and blank lines are not rows."""
    folders, bad = {}, []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|", 2)]
            row = parts[0]
            if not row.endswith("/"):
                bad.append("not_a_folder_row=" + row)
                continue
            if row in folders:
                bad.append("row_twice=" + row)
                continue
            pin = parts[1] if len(parts) > 1 else ""
            reason = parts[2] if len(parts) > 2 else ""
            if not pin.startswith("tree=") or not HEX64.match(pin[5:]):
                bad.append("row_without_a_pin=" + row)
                continue
            if not any(ch.isalpha() for ch in reason):
                bad.append("row_without_a_reason=" + row)
            folders[row] = pin[5:]
    return folders, bad


def main(argv):
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    args = argv[1:]
    if len(args) >= 2 and args[0] == "--repo":
        repo, args = args[1], args[2:]
    if args and args[0] == "--pins":
        for folder in args[1:]:
            try:
                rows = entries(repo, folder)
            except Fault as e:
                print("FLOAT_EVIDENCE|folder=%s|%s|result=fault|json=0" % (folder, e))
                return 1
            if not rows or not folder.endswith("/"):
                print("FLOAT_EVIDENCE|no_files=%s|json=0" % folder)
                return 1
            print("%s | tree=%s | " % (folder, tree_pin(rows)))
        return 0
    folders, bad = parse_list(os.path.join(repo, LIST))
    if args == ["--folders"]:
        for folder in sorted(folders):
            print(folder)
        return 1 if bad else 0
    if args:
        sys.stderr.write(__doc__)
        return 2
    fails = 0
    for row in bad:
        print("FLOAT_EVIDENCE|%s|json=0" % row)
        fails += 1
    for folder, want in sorted(folders.items()):
        try:
            rows = entries(repo, folder)
        except Fault as e:
            fails += 1
            print("FLOAT_EVIDENCE|folder=%s|listed=%s|%s|result=fault|json=0" % (folder, want, e))
            continue
        got = tree_pin(rows) if rows else "none"
        ok = got == want
        fails += not ok
        print("FLOAT_EVIDENCE|folder=%s|files=%d|listed=%s|actual=%s|result=%s|json=0" % (
            folder, len(rows), want, got, "equal" if ok else "pin_moved"))
    print("FLOAT_EVIDENCE_DONE|folders=%d|failed=%d|json=0" % (len(folders), fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
