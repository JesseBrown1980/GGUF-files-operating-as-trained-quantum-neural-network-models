# Checks every block of my HOLDS.txt against the blob at this head, byte for byte, and writes the held files to holdcopy/.
import os
import re
import subprocess
import sys

W = "C:/tmp/opus55/polariton-recheck-engine-20261105"
WT = "C:/tmp/qnn-polariton-wt"
HEAD = "ce44be742d9d59d07bb8ec8a9ed6a559da4ec0bd"
text = open(W + "/HOLDS.txt", encoding="utf-8", newline="").read()
assert "\r" not in text
blocks = re.findall(r"HOLD (H\w+) \| file=(\S+) \| severity=(\w+)\nOLD<<<\n(.*?)\n>>>\nNEW<<<\n(.*?)\n>>>\nREASON: (.*?)(?:\n|$)", text, re.S)
print("HOLDS|blocks=%d|json=0" % len(blocks))
files = {}
bad = 0
for name, path, sev, old, new, reason in blocks:
    if path not in files:
        files[path] = subprocess.run(["git", "-C", WT, "show", "%s:%s" % (HEAD, path)], capture_output=True, check=True).stdout.decode("utf-8")
    c = files[path].count(old)
    print("HOLD_OLD|hold=%s|file=%s|severity=%s|old_count=%d|json=0" % (name, path, sev, c))
    if c != 1:
        bad += 1
        continue
    files[path] = files[path].replace(old, new)
for path, data in files.items():
    out = W + "/holdcopy/" + path
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8", newline="\n").write(data)
print("HOLDS_APPLIED|files=%d|bad=%d|json=0" % (len(files), bad))
sys.exit(1 if bad else 0)
