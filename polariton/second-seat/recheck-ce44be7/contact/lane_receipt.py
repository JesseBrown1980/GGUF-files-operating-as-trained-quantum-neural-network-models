import hashlib, os, subprocess
root='C:/tmp/opus55/polariton-recheck-contact-20261105'
head=subprocess.run(['git','-C','C:/tmp/qnn-polariton-wt','rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()
rows=['RECHECK_CONTACT|head=%s|seat=opus55|for=ACER-CLAUDE-FABLE5|float_in_model=0|json=0'%head]
files=[]
for dp,dn,fn in os.walk(root):
    dn[:] = [d for d in dn if d not in ('target','pieces')]
    for f in sorted(fn):
        p=os.path.join(dp,f).replace(chr(92),'/')
        if p.endswith('LANE-RECEIPT.hbp') or p.endswith('.sha256'): continue
        files.append(p)
for p in sorted(files):
    b=open(p,'rb').read()
    rows.append('FILE|path=%s|bytes=%d|sha256=%s|json=0'%(p[len(root)+1:],len(b),hashlib.sha256(b).hexdigest()))
data=(chr(10).join(rows)+chr(10)).encode()
open(root+'/LANE-RECEIPT.hbp','wb').write(data)
open(root+'/LANE-RECEIPT.hbp.sha256','w',newline=chr(10)).write(hashlib.sha256(data).hexdigest()+'  LANE-RECEIPT.hbp'+chr(10))
print(len(rows),hashlib.sha256(data).hexdigest())
