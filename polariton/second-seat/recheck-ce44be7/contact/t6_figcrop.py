#!/usr/bin/env python3
# t6_figcrop.py -- pulls the raster behind Fig S23 (data only) and writes a crop of its right panel as PNG in my folder, to read the five spread points with more resolution.
import re, zlib, struct, sys
PATH = 'C:/tmp/opus55/polariton-derivations-20261104/paper/src/figures/figs23.pdf'
OUT = 'C:/tmp/opus55/polariton-recheck-contact-20261105/out/figs23_right.png'
raw = open(PATH, 'rb').read()
images = []
for m in re.finditer(rb'stream\r?\n', raw):
    start = m.end()
    end = raw.find(b'endstream', start)
    dict_start = raw.rfind(b'obj', 0, m.start())
    head = raw[dict_start:m.start()]
    wm = re.search(rb'/Width (\d+)', head)
    hm = re.search(rb'/Height (\d+)', head)
    if not wm or not hm:
        continue
    w, h = int(wm.group(1)), int(hm.group(1))
    try:
        d = zlib.decompressobj().decompress(raw[start:end])
    except Exception:
        print('skip stream with Width', w, h)
        continue
    pred = re.search(rb'/Predictor (\d+)', head)
    cs = re.search(rb'/ColorSpace ?(/\w+)?', head)
    print('image', w, h, len(d), 'pred', pred.group(1) if pred else None, 'cs', cs.group(0) if cs else None, 'bpc', re.search(rb'/BitsPerComponent (\d+)', head).group(1) if re.search(rb'/BitsPerComponent (\d+)', head) else None)
    images.append((w, h, d, int(pred.group(1)) if pred else 1))

def unfilter(w, h, d, pred, ch):
    if pred < 10:
        return d
    stride = w*ch
    out = bytearray()
    prev = bytearray(stride)
    i = 0
    for y in range(h):
        ft = d[i]; i += 1
        line = bytearray(d[i:i+stride]); i += stride
        if ft == 1:
            for x in range(ch, stride):
                line[x] = (line[x] + line[x-ch]) & 255
        elif ft == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif ft == 3:
            for x in range(stride):
                a = line[x-ch] if x >= ch else 0
                line[x] = (line[x] + (a + prev[x])//2) & 255
        elif ft == 4:
            for x in range(stride):
                a = line[x-ch] if x >= ch else 0
                b = prev[x]
                c = prev[x-ch] if x >= ch else 0
                p = a + b - c
                pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out += line
        prev = line
    return bytes(out)

def png(path, W, H, rows):
    def chunk(t, b):
        return struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t+b) & 0xffffffff)
    body = b''.join(b'\x00' + r for r in rows)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(body)) + chunk(b'IEND', b''))
for k, (w, h, d, pred) in enumerate(images):
    if len(d) < w*h*3:
        continue
    px = unfilter(w, h, d, pred, 3)
    rows = [px[y*w*3:(y+1)*w*3] for y in range(h)]
    path = 'C:/tmp/opus55/polariton-recheck-contact-20261105/out/figs23_image%d.png' % k
    png(path, w, h, rows)
    print('wrote', path, w, h)
