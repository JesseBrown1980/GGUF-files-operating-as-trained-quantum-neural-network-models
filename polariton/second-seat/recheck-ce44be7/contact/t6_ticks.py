import re, zlib
PATH = 'C:/tmp/opus55/polariton-derivations-20261104/paper/src/figures/figs23.pdf'
raw = open(PATH, 'rb').read()
imgs = []
for m in re.finditer(rb'stream\r?\n', raw):
    start = m.end(); end = raw.find(b'endstream', start)
    head = raw[raw.rfind(b'obj', 0, m.start()):m.start()]
    wm = re.search(rb'/Width (\d+)', head); hm = re.search(rb'/Height (\d+)', head)
    if not wm or not hm: continue
    try: d = zlib.decompressobj().decompress(raw[start:end])
    except Exception: continue
    imgs.append((int(wm.group(1)), int(hm.group(1)), d))
W, H = 435, 909
mask = [d for (w, h, d) in imgs if w == W and h == H and len(d) == W*H][0]
def runs(y):
    cols = [x for x in range(W) if mask[y*W + x] > 128]
    out = []
    for x in cols:
        if out and x == out[-1][1] + 1: out[-1][1] = x
        else: out.append([x, x])
    return out
for y in list(range(36, 56, 2)) + list(range(740, 766, 2)):
    print('row', y, runs(y)[:12])
