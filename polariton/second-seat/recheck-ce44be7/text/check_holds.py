# Dispositions: one row per hold block, and CR counts in the unfiled row files.
import re, os, sys
WT='C:/tmp/qnn-polariton-wt/'; SS=WT+'polariton/second-seat/'
OUT=open('C:/tmp/opus55/polariton-recheck-text-20261105/out/check_holds.txt','w',encoding='utf-8',newline='\n')
def P(*a):
    s=' '.join(str(x) for x in a); print(s); OUT.write(s+'\n')
rows={}
for l in open(SS+'HOLDS-APPLIED.hbp',encoding='utf-8'):
    if not l.startswith('HOLD_APPLIED'): continue
    d=dict(f.split('=',1) for f in l.strip().split('|')[1:] if '=' in f)
    rows[(d['lane'],d['hold'])]=d
P('rows',len(rows))
blocks={}
for lane in ('derivations','engine','text'):
    t=open(SS+lane+'/HOLDS.txt',encoding='utf-8').read()
    for m in re.finditer(r'^HOLD (H[0-9]+[a-z]?) \| file=(\S+) \| severity=(\w+)',t,re.M):
        blocks[(lane,m.group(1))]=(m.group(2),m.group(3))
P('blocks',len(blocks),'by lane',{k:sum(1 for b in blocks if b[0]==k) for k in ('derivations','engine','text')})
P('blocks with no row',sorted(set(blocks)-set(rows)))
P('rows with no block',sorted(set(rows)-set(blocks)))
for k,(f,sev) in sorted(blocks.items()):
    w=rows[k]['where']
    if k in rows and not (w==f or (f=='PR#8-body' and w=='the_body_of_PR_8')):
        P(' where differs',k,'file',f,'where',w,'disp',rows[k]['disposition'])
from collections import Counter
P('dispositions',Counter(re.sub(r'_(with|by).*','',r['disposition']) for r in rows.values()))
crs=0;files=0;nul=0;tot=0
for lane in ('derivations','engine'):
    for root,d,fs in os.walk(SS+lane+'/out'):
        for f in fs:
            b=open(os.path.join(root,f),'rb').read(); tot+=1
            if b.count(b'\r'): files+=1; crs+=b.count(b'\r'); P('  CR in',lane,f,b.count(b'\r'))
            if b.count(b'\0'): nul+=1
P('files',tot,'with CR',files,'CR bytes',crs,'with NUL',nul)
