"""The frozen prediction, read from its file and checked against its sha256 before any use."""

import os

from .hbp import RowError, fields_dict, file_sha256, parse_row, read_lines

FROZEN_SHA256 = "3398b0732077679d77e590399236cbc161d612bb06b82e77968e2541c83688a2"
README_SHA256 = "c0d9954da5e98e64c025b396759a65028137e90c85a36689ec74408ed7f7c2d5"
FROZEN_NAME = "PREDICTION-STRIPE-PHASE.hbp"

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATH = os.path.normpath(os.path.join(_HERE, "..", "..", "..", FROZEN_NAME))


class Frozen:
    """Rows of the frozen file by kind and id, and the raw text of each row."""

    def __init__(self, path=DEFAULT_PATH):
        got = file_sha256(path)
        if got != FROZEN_SHA256:
            raise RowError("frozen file sha256 %s, expected %s" % (got, FROZEN_SHA256))
        self.path = path
        self.sha256 = got
        self.lines = read_lines(path)
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
        if end[0] != "STRIPES_END" or int(end[1]["rows"]) != len(self.rows):
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
