"""excl_unpack.py: the real excluded-point dumps of reader/b/tests/data/excl (N = 27, delta = 1/4 only; no row point),
unpacked into a folder outside the repo for the checks that read the dumps. No engine runs.

    python3 -I excl_unpack.py --out DIR

Every file of the folder must be listed in its SHA256SUMS, and every file listed must be there, or be one of the dumps
X1.0.txt X1.1.txt X0.0.txt X0.1.txt kept as an xz copy, or be X1s4.0.txt (listed by sha256 only). Each file present is
checked against its line; each dump is decompressed to DIR (lzma of the Python standard library) and checked against
its own line; the other files are copied beside the dumps. Then DIR serves, from reader/:

    (cd a && STRIPES_EXCL_DIR=DIR cargo +1.81.0 test --locked --offline --release --test excluded_dumps -- --ignored)
    python3 -I check/compare.py --ra RA --excl DIR
    python3 -I check/compare_b.py --excl DIR
    STRIPES_EXCL_DIR=DIR sabotage/run.sh

Exit 0 with an EXCL_UNPACK row when every file checks; 3 with one EXCL_UNPACK_STOP row otherwise; 2 on usage."""

import hashlib
import lzma
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
READER = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(READER))
EXCL = os.path.join(READER, "b", "tests", "data", "excl")
DUMPS = ("X1.0.txt", "X1.1.txt", "X0.0.txt", "X0.1.txt")
SHA256_ONLY = ("X1s4.0.txt",)
CHUNK = 1 << 20


class Stop(Exception):
    pass


def sums(path):
    """[(name, sha256)] of a sha256sum list: `<64 hex>  <name>` per line, every name once."""
    out, seen = [], set()
    with open(path, "rb") as f:
        text = f.read().decode("ascii")
    if not text.endswith("\n"):
        raise Stop("SHA256SUMS does not end in a newline")
    for ln in text.split("\n")[:-1]:
        h, sep, name = ln.partition("  ")
        if not sep or len(h) != 64 or set(h) - set("0123456789abcdef") or not name or "/" in name or name in seen:
            raise Stop("SHA256SUMS line: " + ln[:120])
        seen.add(name)
        out.append((name, h))
    return out


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def unxz(src, dst):
    """Decompress src to dst through a .part file; the sha256 of what was written."""
    h = hashlib.sha256()
    part = dst + ".part"
    with lzma.open(src, "rb") as f, open(part, "wb") as o:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
            o.write(chunk)
    os.replace(part, dst)
    return h.hexdigest()


def unpack(out, excl=EXCL):
    listed = sums(os.path.join(excl, "SHA256SUMS"))
    names = {n for n, _ in listed}
    present = sorted(os.listdir(excl))
    for nm in present:
        if nm != "SHA256SUMS" and nm not in names:
            raise Stop("not in SHA256SUMS: " + nm)
    checked, dumps, only = 0, [], []
    for nm, h in listed:
        if nm in present:
            got = file_sha256(os.path.join(excl, nm))
            if got != h:
                raise Stop("%s: sha256 %s, SHA256SUMS %s" % (nm, got, h))
            checked += 1
        elif nm in DUMPS and nm + ".xz" in present:
            dumps.append((nm, h))
        elif nm in SHA256_ONLY:
            only.append(nm)
        else:
            raise Stop("listed, not here: " + nm)
    if sorted(n for n, _ in dumps) != sorted(DUMPS):
        raise Stop("dumps: " + ",".join(n for n, _ in dumps))
    os.makedirs(out, exist_ok=True)
    for nm, h in dumps:
        got = unxz(os.path.join(excl, nm + ".xz"), os.path.join(out, nm))
        if got != h:
            raise Stop("%s unpacked: sha256 %s, SHA256SUMS %s" % (nm, got, h))
    for nm in present:
        if not nm.endswith(".xz"):
            shutil.copyfile(os.path.join(excl, nm), os.path.join(out, nm))
    return checked, len(dumps), only


def main(argv):
    if len(argv) != 3 or argv[1] != "--out":
        sys.stderr.write(__doc__)
        return 2
    out = os.path.realpath(argv[2])
    if (out + os.sep).startswith(os.path.realpath(REPO) + os.sep):
        sys.stderr.write("excl_unpack.py: --out must be outside the repo\n")
        return 2
    try:
        checked, n, only = unpack(out)
    except (Stop, OSError, lzma.LZMAError) as e:
        print("EXCL_UNPACK_STOP|detail=%s|json=0" % str(e).replace("|", "_").replace(" ", "_")[:300])
        return 3
    print("EXCL_UNPACK|out=%s|checked=%d|dumps_unpacked=%d|sha256_only=%s|point=X1,X0|N=27|delta=1/4|engine_runs=0"
          "|json=0" % (out, checked, n, ",".join(only) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
