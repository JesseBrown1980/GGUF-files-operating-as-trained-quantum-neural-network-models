# Each OLD must occur exactly once, byte for byte, in its file at this head. The PR body is read from my saved copy of the live body.
import re, subprocess, sys
ME = 'C:/tmp/opus55/polariton-recheck-text-20261105/'
HEAD = 'ce44be742d9d59d07bb8ec8a9ed6a559da4ec0bd'
def at_head(path):
    r = subprocess.run(['git', '-C', 'C:/tmp/qnn-polariton-wt', 'show', HEAD + ':' + path], capture_output=True)
    assert r.returncode == 0, path
    return r.stdout
body = open(ME + 'out/pr8_body.md', 'rb').read()
title = open(ME + 'out/pr8_title.txt', 'rb').read()
text = open(ME + 'HOLDS.txt', encoding='utf-8', newline='').read()
blocks = re.split(r'(?m)^(?=HOLD H\d+ \| )', text)
blocks = [b for b in blocks if b.strip()]
bad = 0
sev = {}
seen = set()
for b in blocks:
    m = re.match(r'HOLD (H\d+) \| file=(\S+) \| severity=(high|medium|low)\nOLD<<<\n(.*?)\n>>>\nNEW<<<\n(.*?)\n>>>\nREASON: (.+?)\n*$', b, re.S)
    if not m:
        print('FORM', b[:80]); bad += 1; continue
    h, f, s, old, new, why = m.groups()
    assert h not in seen; seen.add(h)
    sev[s] = sev.get(s, 0) + 1
    data = body if f == 'PR#8-body' else title if f == 'PR#8-title' else at_head(f)
    n = data.count(old.encode('utf-8'))
    if n != 1:
        print('COUNT', h, f, n, repr(old[:70])); bad += 1
    if '\n' in why.strip():
        print('REASON two lines', h); bad += 1
    if old == new:
        print('SAME', h); bad += 1
print('blocks', len(blocks), 'severity', sev, 'bad', bad)
