# For each block of the earlier engine HOLDS.txt: is its NEW text present at this head's git blob, and is its OLD text gone?
# Reads the blobs through git show, so CRLF in a working copy cannot mislead it. Writes HBP rows.
import re
import subprocess
import sys

WT = "C:/tmp/qnn-polariton-wt"
HEAD = "ce44be742d9d59d07bb8ec8a9ed6a559da4ec0bd"
BASE = "8dfa11a"
HOLDS = "C:/tmp/opus55/polariton-engine-20261104/HOLDS.txt"


def show(rev, path):
    return subprocess.run(["git", "-C", WT, "show", "%s:%s" % (rev, path)], capture_output=True, check=True).stdout.decode("utf-8")


text = open(HOLDS, encoding="utf-8", newline="").read().replace("\r\n", "\n")
blocks = re.findall(r"HOLD (H\w+) \| file=(\S+) \| severity=(\w+)\nOLD<<<\n(.*?)\n>>>\nNEW<<<\n(.*?)\n>>>\nREASON: (.*?)\n", text, re.S)
print("HOLD_BLOCKS|count=%d|json=0" % len(blocks))
blobs = {}
for name, path, sev, old, new, reason in blocks:
    if path not in blobs:
        blobs[path] = (show(HEAD, path), show(BASE, path))
    head, base = blobs[path]
    print("HOLD_CHECK|hold=%s|file=%s|old_in_base=%d|old_count_head=%d|new_count_head=%d|json=0" % (name, path, base.count(old), head.count(old), head.count(new)))
