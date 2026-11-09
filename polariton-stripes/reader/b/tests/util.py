"""Paths to the excluded-point fixtures and small builders for the tests."""

import os
import shutil
import tempfile

from stripes_read_b import common
from stripes_read_b.hbp import sha256_hex

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
AGG = os.path.join(DATA, "agg")
RUN = os.path.join(DATA, "run")
QE9 = os.path.join(DATA, "qe9")

# Excluded test points (AGG-FORMAT.md section 9 has X1, X0 with 8 calls; the fixtures hold calls 0 and 1).
X1 = common.DumpPoint("X1", 27, "1/4", "1/40", 2 * 4096, 2, (64, 128), False)
X0 = common.DumpPoint("X0", 27, "1/4", "0", 2 * 4096, 2, (64, 128), False)
XR1 = common.RunPoint("XR1", 27, "1/4", "1/40", 4096, (32, 64, 128), batches=8)
XR0 = common.RunPoint("XR0", 27, "1/4", "0", 4096, (32, 64), batches=8)


class TempDir:
    def __enter__(self):
        self.path = tempfile.mkdtemp(prefix="stripes-b-test-")
        return self.path

    def __exit__(self, *a):
        shutil.rmtree(self.path)


def read(path):
    with open(path, "rb") as f:
        return f.read().decode("ascii")


def write(path, text):
    with open(path, "wb") as f:
        f.write(text.encode("ascii"))


def with_trailer(agg_text, rc=0, rc_reader=0):
    return agg_text + "rc=%d rc_reader=%d\n" % (rc, rc_reader)


def rehash(agg_text):
    """Recompute AGG_END after an edit (a sabotage that also forges the block's own hash)."""
    lines = agg_text.split("\n")[:-1]
    body = lines[:-1]
    end = lines[-1].split("|")
    h = sha256_hex("".join(ln + "\n" for ln in body).encode("ascii"))
    end = [p if not p.startswith("agg_sha256=") else "agg_sha256=" + h for p in end]
    return "\n".join(body + ["|".join(end)]) + "\n"


ENGINE_FAULT = "TWB_FAULT|reason=rounding_bound_hL_above_1/2|json=0\n"


def point_dir(tmp, files, engine_err=True):
    """tmp/<name> for {name: text}; returns tmp. With engine_err, each call file <stem>.hbp not given its
    <stem>.eng.err gets the one the run script files: empty after a completed call, a TWB_FAULT row after rc=4."""
    for name, text in files.items():
        write(os.path.join(tmp, name), text)
        if engine_err and name.endswith(".hbp") and name[:-4] + ".eng.err" not in files:
            stop = text.split("\n")[-2].startswith("rc=4 ")
            write(os.path.join(tmp, name[:-4] + ".eng.err"), ENGINE_FAULT if stop else "")
    return tmp
