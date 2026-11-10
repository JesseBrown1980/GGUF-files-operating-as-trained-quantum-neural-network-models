"""The row grammar shared by the frozen file, the engines and both reader stages: KIND|key=value|...|json=0."""

import hashlib

from .exact import ExactError


class RowError(ExactError):
    """A row outside the grammar."""


def printable(text):
    return all(32 <= ord(c) < 127 for c in text)


def parse_row(line, kind=None, keys=None):
    """(kind, [(key, value)]) of one row without its newline; the last field must be json=0.

    A value is everything after the field's first '='. With `keys`, the key sequence must be exactly that."""
    if not printable(line):
        raise RowError("row has a byte outside printable ASCII")
    parts = line.split("|")
    if len(parts) < 2:
        raise RowError("row without fields: " + line[:60])
    k = parts[0]
    if kind is not None and k != kind:
        raise RowError("row kind %s, expected %s" % (k, kind))
    fields = []
    for p in parts[1:]:
        if "=" not in p:
            raise RowError("field without '=' in %s: %s" % (k, p[:40]))
        key, val = p.split("=", 1)
        if not key:
            raise RowError("empty key in " + k)
        fields.append((key, val))
    if fields[-1] != ("json", "0"):
        raise RowError("row %s does not end with json=0" % k)
    if keys is not None:
        got = [f[0] for f in fields]
        want = list(keys) + ["json"]
        if got != want:
            raise RowError("row %s keys %s, expected %s" % (k, ",".join(got), ",".join(want)))
    return k, fields


def fields_dict(fields):
    d = {}
    for key, val in fields:
        if key in d:
            raise RowError("repeated key " + key)
        d[key] = val
    return d


def clean(text):
    """Field text safe inside a row: printable ASCII, '|' and space replaced by '_'."""
    return "".join(c if (32 < ord(c) < 127 and c != "|") else "_" for c in str(text))


def emit(kind, pairs):
    """One row (without its newline) from (key, value) pairs; json=0 is appended."""
    out = [kind]
    for key, val in pairs:
        if not isinstance(val, (str, int)) or isinstance(val, bool):
            raise RowError("row value of key %s is %s, not str or int" % (key, type(val).__name__))
        out.append("%s=%s" % (key, clean(val)))
    out.append("json=0")
    return "|".join(out)


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def read_lines(path):
    """The lines of a text file; every line must end with '\\n' and be printable ASCII."""
    with open(path, "rb") as f:
        return text_lines(f.read(), path)


def text_lines(data, path):
    """The lines of the bytes of a text file (read_lines, on bytes already read and hashed)."""
    if data and not data.endswith(b"\n"):
        raise RowError("%s: last line unterminated" % path)
    text = data.decode("ascii")
    lines = text.split("\n")[:-1] if text else []
    for i, ln in enumerate(lines):
        if not printable(ln):
            raise RowError("%s line %d: byte outside printable ASCII" % (path, i + 1))
    return lines
