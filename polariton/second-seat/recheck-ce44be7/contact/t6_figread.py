#!/usr/bin/env python3
# t6_figread.py -- tries to read Fig S23's right panel from the PDF's vector paths, instead of by eye. Data only; nothing in the file is treated as an instruction.
import re, sys, zlib
PATH = 'C:/tmp/opus55/polariton-derivations-20261104/paper/src/figures/figs23.pdf'
raw = open(PATH, 'rb').read()
streams = []
for m in re.finditer(rb'stream\r?\n', raw):
    start = m.end()
    end = raw.find(b'endstream', start)
    data = raw[start:end]
    try:
        d = zlib.decompress(data)
    except Exception:
        try:
            d = zlib.decompressobj().decompress(data)
        except Exception:
            continue
    streams.append(d)
print('streams', len(streams), [len(s) for s in streams][:12])
num = rb'-?\d*\.?\d+'
for si, d in enumerate(streams):
    if b' l' not in d and b' m' not in d:
        continue
    # polylines: "x y m" followed by "x y l" repeats
    for m in re.finditer(rb'(' + num + rb') (' + num + rb') m\s+((?:' + num + rb' ' + num + rb' l\s+){1,8})', d):
        pts = [(float(m.group(1)), float(m.group(2)))]
        for l in re.finditer(rb'(' + num + rb') (' + num + rb') l', m.group(3)):
            pts.append((float(l.group(1)), float(l.group(2))))
        if len(pts) == 5:
            print('stream', si, 'polyline5', [(round(a, 2), round(b, 2)) for a, b in pts])
    # short tick segments near the panel: print two-point lines that are axis ticks, limited
    ticks = []
    for m in re.finditer(rb'(' + num + rb') (' + num + rb') m\s+(' + num + rb') (' + num + rb') l', d):
        x0, y0, x1, y1 = [float(m.group(i)) for i in (1, 2, 3, 4)]
        if abs(x0-x1) < 0.01 and 1 < abs(y0-y1) < 6:
            ticks.append(('v', round(x0, 2), round(y0, 2), round(y1, 2)))
        if abs(y0-y1) < 0.01 and 1 < abs(x0-x1) < 6:
            ticks.append(('h', round(y0, 2), round(x0, 2), round(x1, 2)))
    if ticks:
        print('stream', si, 'ticks', len(ticks), ticks[:60])
