# Links in the READMEs and the body, and which SHA256SUMS entries are in the commit.
import sys, re, subprocess, os
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
out = open(ME + 'out/check_links.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True); out.write(s + '\n')
HEAD = 'ce44be742d9d59d07bb8ec8a9ed6a559da4ec0bd'
def git(*args):
    return subprocess.run(['git', '-C', 'C:/tmp/qnn-polariton-wt'] + list(args), capture_output=True, text=True, encoding='utf-8')
tree = set(l for l in git('ls-tree', '-r', '--name-only', HEAD).stdout.split('\n') if l)
P('files in the tree', len(tree))
dirs = set()
for t in tree:
    p = t
    while '/' in p:
        p = p.rsplit('/', 1)[0]
        dirs.add(p)
LINK = re.compile(r'\[([^\]]*)\]\(([^)\s]+)\)')
readme = open(WT + 'polariton/README.md', encoding='utf-8').read()
root_ = open(WT + 'README.md', encoding='utf-8').read().split('\n')
start = next(i for i, l in enumerate(root_) if l.startswith('## Three-mode polariton test'))
end = next(i for i, l in enumerate(root_) if l.startswith('## Versions at a glance'))
rootsec = '\n'.join(root_[start:end])
body = open(ME + 'out/pr8_body.md', encoding='utf-8').read()
def norm(base, target):
    parts = (base + '/' + target).split('/') if base else target.split('/')
    o = []
    for p in parts:
        if p in ('', '.'):
            continue
        if p == '..':
            o.pop()
        else:
            o.append(p)
    return '/'.join(o)
ext = set()
for name, text, base in (('polariton/README.md', readme, 'polariton'), ('README.md section', rootsec, '')):
    for label, tgt in LINK.findall(text):
        if tgt.startswith('http'):
            ext.add(tgt); continue
        t = norm(base, tgt.split('#')[0])
        status = 'file' if t in tree else 'dir' if t.rstrip('/') in dirs else 'MISSING'
        P(' ', name, repr(label[:40]), tgt, '->', t, status)
for label, tgt in LINK.findall(body):
    m = re.match(r'https://github.com/JesseBrown1980/GGUF-files-operating-as-trained-quantum-neural-network-models/(blob|tree)/([^/]+)/(.+)$', tgt)
    if m:
        t = m.group(3).rstrip('/')
        status = 'file' if t in tree else 'dir' if t in dirs else 'MISSING'
        P('  body', repr(label[:40]), m.group(1), 'ref', m.group(2), t, status)
    else:
        ext.add(tgt)
P('external', sorted(ext))
P()
P('== SHA256SUMS entries against the tree')
lines = [l for l in open(WT + 'polariton/second-seat/SHA256SUMS', encoding='utf-8').read().split('\n') if l.strip()]
names = [re.match(r'[0-9a-f]{64}[ *]+(.+)$', l).group(1) for l in lines]
in_tree = [n for n in names if 'polariton/second-seat/' + n in tree]
not_in = [n for n in names if 'polariton/second-seat/' + n not in tree]
P('listed', len(names), 'in the commit', len(in_tree), 'absent from the commit', len(not_in))
from collections import Counter
P('absent by folder', Counter(n.rsplit('/', 1)[0] for n in not_in))
P('bytes absent', sum(os.path.getsize(WT + 'polariton/second-seat/' + n) for n in not_in))
P('largest absent', sorted(((os.path.getsize(WT + 'polariton/second-seat/' + n), n) for n in not_in), reverse=True)[:5])
ign = git('status', '--short', '--ignored', 'polariton')
P('ignored per git status:', ign.stdout.strip().replace('\n', ' ; '))
P()
P('== Names the texts and findings cite under out/, at this head')
cited = set()
for path in ('polariton/second-seat/derivations/FINDINGS.txt', 'polariton/second-seat/engine/FINDINGS.txt', 'polariton/second-seat/text/FINDINGS.txt'):
    t = open(WT + path, encoding='utf-8').read()
    for m in re.findall(r'out/[A-Za-z0-9_./\-*]+', t):
        cited.add((path.split('/')[2], m.rstrip('.,);')))
P('cited out/ paths in the FINDINGS files', len(cited))
for lane, m in sorted(cited):
    full = 'polariton/second-seat/%s/%s' % (lane, m)
    P('  ', lane, m, 'in_tree' if full in tree else 'not_in_tree', 'on_disk' if os.path.exists(WT + full) else 'not_on_disk')
out.close()
