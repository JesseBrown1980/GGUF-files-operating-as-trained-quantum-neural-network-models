# Item 3. The margin of the lowest other P above the crossing of the low branch and the plane wave, at large |x|, with digits, since the sectors nearly tie there.
import sys
from fractions import Fraction as F
sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from sec_lib import chain, ground_level, K, fx
def level(N,u,x,P):
    d,o2=chain(N,u,x,P)
    return ground_level(d,o2,stop=1<<(K-125))
def sci(v):
    v=F(v,1<<K)
    if v==0: return "0"
    s="-" if v<0 else ""
    v=abs(v); e=0
    while v>=10: v/=10; e+=1
    while v<1: v*=10; e-=1
    return "%s%d.%03de%d"%(s,int(v),int((v-int(v))*1000),e)
for N in (12,13,40,41,81,82,121,122,243,244):
    for x in (F(-1),F(-3),F(-5),F(-10),F(-50)):
        lo,hi=F(0),F(3,2)
        px=(x*N)
        pw=(px.numerator<<K)//px.denominator
        for _ in range(80):
            mid=(lo+hi)/2
            mid=F((mid.numerator<<100)//mid.denominator,1<<100)
            if min(level(N,mid,x,0),level(N,mid,x,1))-pw<0: lo=mid
            else: hi=mid
        u=(lo+hi)/2
        ref=level(N,u,x,N)
        low=min(level(N,u,x,0),level(N,u,x,1))
        rows=[]
        best=None
        for P in range(2,N):
            e=level(N,u,x,P)
            if best is None or e<best[0]: best=(e,P)
        print("MARGIN|N=%d|x=%s|u_cross=%s|N*u*(u-x)=%s|low_minus_plane=%s|lowest_other_P=%d|other_minus_plane=%s|json=0"%(N,x,fx((u.numerator<<K)//u.denominator,7),fx(((N*u*(u-x)).numerator<<K)//(N*u*(u-x)).denominator,5),sci(low-ref),best[1],sci(best[0]-ref)))
        sys.stdout.flush()
