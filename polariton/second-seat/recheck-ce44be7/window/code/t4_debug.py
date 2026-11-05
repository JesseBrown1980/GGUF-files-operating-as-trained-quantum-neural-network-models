import sys
sys.dont_write_bytecode=True
sys.path.insert(0,'C:/tmp/opus55/polariton-recheck-window-20261105/code')
from fractions import Fraction as F
from math import isqrt
import t4_reduced as tr
from resp_lib import constants, dec
N=int(sys.argv[1]); u=F(1,4); x=F(-1,4); Pm=int(sys.argv[2]); L=int(sys.argv[3])
K,ONE=tr.K,tr.ONE
c,lv,Um,Bm,B1=tr.build(N,u,x,Pm,L)
e0=lv[0][0][0]
for P in range(0,Pm+1,max(1,Pm//12)):
    print(P,[dec(F(lv[P][k][0]-e0,ONE)*(N if k==0 else 1),6) for k in range(min(4,len(lv[P])))], 'c0P2=',dec(F(1,4)*P*P,4))
print('U00',[dec(F(Um[P][(0,0)],ONE),6) for P in range(0,min(Pm,8))],'pred',[dec(F(isqrt(5<<80),1<<40)/2*(2*P+1)/4,6) for P in range(0,min(Pm,8))])
print('U10',[dec(F(Um[P][(1,0)],ONE),3) for P in range(0,min(Pm,8))])
print('U01',[dec(F(Um[P][(0,1)],ONE),3) for P in range(0,min(Pm,8))])
print('B20',[dec(F(Bm[P][(0,0)],ONE)/N,5) for P in range(0,min(Pm-1,8))],'B1',dec(F(B1[(0,0)],ONE)/N,5))
