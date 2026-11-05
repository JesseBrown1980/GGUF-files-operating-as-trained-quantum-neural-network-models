import sys
sys.path.insert(0, r'C:/tmp/opus55/polariton-recheck-contact-20261105')
import t1_identity as T
import random
rng = random.Random(2026110501)
# replay the same random stream as main() up to the state loop
c=0; bad=[]
for N in (2,3,4,5,6,8,12):
    for (par,cx,label) in ((True,False,'parity_real'),(True,True,'parity_complex'),(False,False,'noparity_real'),(False,True,'noparity_complex')):
        for rep in range(4):
            psi=T.rand_state(N,rng,par,cx,sparse=(None if rep<2 else 0.5))
            r=T.run_state(N,psi,label+'#%d'%rep)
            c+=1
            if 'identity_exact=True' not in r:
                bad.append((N,label,rep,[str(x) for x in r],sorted(psi.keys())))
print('tot',c,'nonexact',len(bad))
for b in bad: print(b)
