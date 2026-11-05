#!/usr/bin/env python3
# t6_figaxis.py -- reads tick positions and marker centres of Fig S23's right panel from its alpha mask and RGB raster. Integers only; the figure is data.
import re, zlib
PATH = 'C:/tmp/opus55/polariton-derivations-20261104/paper/src/figures/figs23.pdf'
raw = open(PATH, 'rb').read()
imgs = []
for m in re.finditer(rb'stream\r?\n', raw):
    start = m.end()
    end = raw.find(b'endstream', start)
    head = raw[raw.rfind(b'obj', 0, m.start()):m.start()]
    wm = re.search(rb'/Width (\d+)', head); hm = re.search(rb'/Height (\d+)', head)
    if not wm or not hm:
        continue
    try:
        d = zlib.decompressobj().decompress(raw[start:end])
    except Exception:
        continue
    imgs.append((int(wm.group(1)), int(hm.group(1)), d))
W, H = 435, 909
mask = [d for (w, h, d) in imgs if w == W and h == H and len(d) == W*H][0]
rgb = [d for (w, h, d) in imgs if w == W and h == H and len(d) == W*H*3][0]
# horizontal rows with the most opaque pixels: axis line
counts = [sum(1 for x in range(W) if mask[y*W + x] > 128) for y in range(H)]
top = sorted(range(H), key=lambda y: -counts[y])[:6]
print('rows with most opaque pixels', [(y, counts[y]) for y in top])
axis_y = max(top)
# ticks: opaque columns in rows just above and below the axis line
for dy in (-14, -10, -6, 6, 10, 14):
    y = axis_y + dy
    if 0 <= y < H:
        cols = [x for x in range(W) if mask[y*W + x] > 128]
        runs = []
        for x in cols:
            if runs and x == runs[-1][1] + 1:
                runs[-1][1] = x
            else:
                runs.append([x, x])
        print('dy', dy, 'runs', runs[:14])
# markers: white centres inside blue rings. find connected white-ish blobs with opaque alpha
seen = set()
blobs = []
for y in range(H):
    for x in range(W):
        i = y*W + x
        if mask[i] > 200 and rgb[3*i] > 230 and rgb[3*i+1] > 230 and rgb[3*i+2] > 230 and (x, y) not in seen:
            stack = [(x, y)]; seen.add((x, y)); pts = []
            while stack:
                a, b = stack.pop(); pts.append((a, b))
                for nx, ny in ((a+1, b), (a-1, b), (a, b+1), (a, b-1)):
                    if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in seen:
                        j = ny*W + nx
                        if mask[j] > 200 and rgb[3*j] > 230 and rgb[3*j+1] > 230 and rgb[3*j+2] > 230:
                            seen.add((nx, ny)); stack.append((nx, ny))
            if 20 < len(pts) < 400:
                blobs.append((sum(p[0] for p in pts)*100//len(pts), sum(p[1] for p in pts)*100//len(pts), len(pts)))
print('marker centres x100 (x, y, size)', blobs)
