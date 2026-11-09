#!/usr/bin/env python3
"""float_evidence.py: the folder rows of polariton-stripes/FLOAT-EVIDENCE.txt, checked against the tree.

A folder row reads `folder/ | tree=H | reason`, the format of the 4D repo's scripts/FLOAT-EVIDENCE.txt. H is the
sha256 of one line per entry under the folder, `<mode> <sha256 of the bytes> <path>\\n`, in git's order (paths sorted
as bytes), the rule of tree_line and tree_pin in that repo's scripts/no_float_gate.py. The entries are the files git
would track there (`git ls-files --cached --others --exclude-standard`), read from the working tree, so the check
holds before and after the commit. A new file, a mode change or an edited byte moves H.

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


def entries(repo, folder):
    """[(mode, sha256, path)] of the files under folder, in git's order."""
    out = subprocess.run(["git", "-C", repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--",
                          folder], capture_output=True, check=True, stdin=subprocess.DEVNULL).stdout
    paths = sorted({p for p in out.split(b"\0") if p}, key=bytes)
    rows = []
    for p in paths:
        full = os.path.join(repo, p.decode("utf-8", "surrogateescape"))
        st = os.lstat(full)
        if stat.S_ISLNK(st.st_mode):
            mode, data = "120000", os.readlink(full).encode("utf-8", "surrogateescape")
        elif stat.S_ISREG(st.st_mode):
            mode = "100755" if st.st_mode & stat.S_IXUSR else "100644"
            with open(full, "rb") as f:
                data = f.read()
        else:
            raise SystemExit("FLOAT_EVIDENCE|not_a_file=%s|json=0" % p.decode("utf-8", "replace"))
        rows.append((mode, hashlib.sha256(data).hexdigest(), p.decode("utf-8", "surrogateescape")))
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
            rows = entries(repo, folder)
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
        rows = entries(repo, folder)
        got = tree_pin(rows) if rows else "none"
        ok = got == want
        fails += not ok
        print("FLOAT_EVIDENCE|folder=%s|files=%d|listed=%s|actual=%s|result=%s|json=0" % (
            folder, len(rows), want, got, "equal" if ok else "pin_moved"))
    print("FLOAT_EVIDENCE_DONE|folders=%d|failed=%d|json=0" % (len(folders), fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
