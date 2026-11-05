import re, zlib, struct
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
def chunk(t, b):
    return struct.pack('>I', len(b)) + t + b + struct.pack('>I', zlib.crc32(t+b) & 0xffffffff)
y0, y1 = 730, 870
rows = []
for y in range(y0, y1):
    line = bytearray()
    for x in range(W):
        v = 255 - mask[y*W + x]
        line += bytes((v, v, v))
    rows.append(b'\x00' + bytes(line))
open('C:/tmp/opus55/polariton-recheck-contact-20261105/out/figs23_axis.png', 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W, y1-y0, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b''.join(rows))) + chunk(b'IEND', b''))
print('ok')
