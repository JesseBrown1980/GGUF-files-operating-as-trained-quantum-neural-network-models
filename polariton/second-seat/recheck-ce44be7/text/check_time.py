# "about three times the work", the time rows, and the attempt rows against the files.
import sys, re, hashlib
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
out = open(ME + 'out/check_time.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s); out.write(s + '\n')
for name, path in (('third', WT + 'polariton/third-run/TIMING-LOCAL-20261104.hbp'), ('fourth', WT + 'polariton/TIMING-LOCAL-20261104.hbp')):
    d = load(path)
    P(name, {k: len(v) for k, v in d.items()})
    rows = d.get('TIMING', [])
    P(' first', rows[0]['_raw'][:200])
    P(' keys', [k for k in rows[0].keys() if k != '_raw'])
    # sum per stage
    ms_key = next(k for k in rows[0] if 'ms' in k or 'seconds' in k or 'elapsed' in k)
    tot = 0
    by = {}
    for r in rows:
        v = int(r[ms_key])
        tot += v
        st = r.get('stage') or r.get('what') or r['_raw'].split('|')[1]
        by[st] = by.get(st, 0) + v
    P(' key', ms_key, 'total', tot, 'in hours (cpu-sum)', dec(F(tot, 3600000), 3))
    P(' per stage', sorted(by.items(), key=lambda a: -a[1])[:20])
    if d.get('TIMING_MACHINE'):
        P(' machine', d['TIMING_MACHINE'][0]['_raw'][:300])
P()
b = open(WT + 'polariton/RECEIPT.hbp', 'rb').read()
P('receipt sha', hashlib.sha256(b).hexdigest(), 'bytes', len(b), 'CR', b.count(b'\r'), 'lines', b.count(b'\n'))
b3 = open(WT + 'polariton/third-run/RECEIPT.hbp', 'rb').read()
P('third receipt sha', hashlib.sha256(b3).hexdigest(), 'bytes', len(b3), 'lines', b3.count(b'\n'))
P('ratio of receipts bytes', dec(F(len(b), len(b3)), 3))
pred = open(WT + 'polariton/PREDICTION.hbp', encoding='utf-8').read()
for m in re.findall(r'receipt_sha256=([0-9a-f]{64})', pred):
    P(' prediction names', m)
wf = open(WT + '.github/workflows/polariton.yml', encoding='utf-8').read()
P('workflow sha pins', re.findall(r'[0-9a-f]{64}', wf))
for f in ('polariton/RECEIPT.hbp', 'polariton/READ.hbp', 'polariton/read_prediction.py', 'polariton/second_route.py', 'polariton/SECOND-ROUTE.hbp'):
    P(' ', f, hashlib.sha256(open(WT + f, 'rb').read()).hexdigest())
out.close()
