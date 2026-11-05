import sys
sys.path.insert(0,'C:/tmp/opus55/polariton-recheck-engine-20261105/holdcopy/polariton')
sys.dont_write_bytecode=True
import second_route as R
from fractions import Fraction as F
n,u,x,y=3,F(1),F(-1,4),F(1,6)
for bits in (14,18,22):
    st=F(1,1<<bits)
    w=F(1,1<<(bits+34))
    p2=(R.full_ground(n,x,u,y,kappa_c=st,width=w)-R.full_ground(n,x,u,y,kappa_c=-st,width=w))/(2*st)/(n*n)
    print('STEP|2^-%d|P2=%s'%(bits,R.decimal(p2)),flush=True)
