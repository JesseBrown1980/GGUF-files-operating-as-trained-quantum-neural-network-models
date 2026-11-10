"""The frozen prediction, read from its file and checked against its sha256 before any use, with the frozen README
beside it checked against its own."""

import os

from .exact import canon_int
from .hbp import RowError, fields_dict, parse_row, sha256_hex, text_lines

FROZEN_SHA256 = "3398b0732077679d77e590399236cbc161d612bb06b82e77968e2541c83688a2"
README_SHA256 = "c0d9954da5e98e64c025b396759a65028137e90c85a36689ec74408ed7f7c2d5"
FROZEN_NAME = "PREDICTION-STRIPE-PHASE.hbp"
README_NAME = "README.md"

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATH = os.path.normpath(os.path.join(_HERE, "..", "..", "..", FROZEN_NAME))


class Frozen:
    """Rows of the frozen file by kind and id, and the raw text of each row. The rows are parsed from the same bytes
    that were hashed. A moved byte in the file or in the README beside it is a StageBStop (frozen_sha256)."""

    def __init__(self, path=DEFAULT_PATH):
        from .common import StageBStop  # common imports this module

        with open(path, "rb") as f:
            data = f.read()
        got = sha256_hex(data)
        if got != FROZEN_SHA256:
            raise StageBStop("frozen_sha256", "%s sha256 %s, expected %s" % (FROZEN_NAME, got, FROZEN_SHA256))
        readme = os.path.join(os.path.dirname(path), README_NAME)
        if not os.path.isfile(readme):
            raise StageBStop("frozen_sha256", "no %s beside %s" % (README_NAME, FROZEN_NAME))
        with open(readme, "rb") as f:
            got_readme = sha256_hex(f.read())
        if got_readme != README_SHA256:
            raise StageBStop("frozen_sha256", "%s sha256 %s, expected %s" % (README_NAME, got_readme, README_SHA256))
        self.path = path
        self.sha256 = got
        self.lines = text_lines(data, path)
        self.rows = []
        self.by_id = {}
        for ln in self.lines:
            kind, fields = parse_row(ln)
            d = fields_dict(fields)
            self.rows.append((kind, d, ln))
            if "id" in d:
                key = (kind, d["id"])
                if key in self.by_id:
                    raise RowError("frozen id repeated: %s %s" % key)
                self.by_id[key] = (d, ln)
        end = self.rows[-1]
        if end[0] != "STRIPES_END" or canon_int(end[1]["rows"]) != len(self.rows):
            raise RowError("frozen STRIPES_END row count")

    def row(self, kind, rid):
        return self.by_id[(kind, rid)][0]

    def text(self, kind, rid):
        return self.by_id[(kind, rid)][1]

    def predict(self, rid):
        return self.row("STRIPES_PREDICT", rid)

    def predict_text(self, rid):
        return self.text("STRIPES_PREDICT", rid)

    def require(self, kind, rid, phrase):
        """Assert that the frozen row holds the phrase verbatim; returns the phrase."""
        if phrase not in self.text(kind, rid):
            raise RowError("frozen %s %s does not hold: %s" % (kind, rid, phrase))
        return phrase


_CACHE = {}


def load(path=DEFAULT_PATH):
    if path not in _CACHE:
        _CACHE[path] = Frozen(path)
    return _CACHE[path]
