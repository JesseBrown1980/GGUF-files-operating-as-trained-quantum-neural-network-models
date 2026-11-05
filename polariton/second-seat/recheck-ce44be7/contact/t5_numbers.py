#!/usr/bin/env python3
# t5_numbers.py -- numbers quoted in the holds, each from the machine.
import sys
from fractions import Fraction as Fr
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-contact-20261105')
import t5_eval as E
import chebdrv as D
from law import law, dec
# limits of N x deviation at delta=0, y^2 N=1/4, t=2
fo = E.first_order(Fr(0), Fr(1, 18), 81, Fr(2))
print('limit N*dev at delta=0, y2N=1/4, t=2: A1 %s C1 %s V2 %s D2' % (dec(fo['w1']/fo['w0'], 3), dec(fo['C1v']/fo['C0'], 3), dec(2*fo['w1']/fo['w0'] - fo['C1v']/fo['C0'], 3)))
# N x deviation from the receipt rows
REC='C:/tmp/qnn-polariton-wt/polariton/RECEIPT.hbp'
rows=[]
for ln in open(REC,encoding='utf8',newline=''):
    ln=ln.rstrip('\r\n')
    if ln.startswith('POLARITON_QUENCH_CONVERSION|') or ln.startswith('POLARITON_QUENCH_PIN|'):
        rows.append(D.parse_row(ln)|{'tag':ln.split('|')[0]})
ap=[r for r in rows if r['tag']=='POLARITON_QUENCH_CONVERSION' and r['delta']=='0' and r['s']=='1/2' and r['t']=='2']
for r in sorted(ap,key=lambda r:int(r['N'])):
    N=int(r['N']); y=Fr(r['y']); t=Fr(2); L=law(N,0,y,t)
    A=Fr(int(r['A_ppb']),10**9); C1=Fr(int(r['C1_ppb']),10**9)
    A1=2*abs(A)/N; V2=A1*A1/(2*C1)
    fo2=E.first_order(Fr(0),y,N,t)
    print('N=%d y2N=%s N*dev: V2 %s A1 %s C1 %s ; first-order at this y2N: V2 %s A1 %s C1 %s'%(N,dec(y*y*N,4),dec((V2/L['V2']-1)*N,2),dec((A1/L['A1']-1)*N,2),dec((C1/L['C1']-1)*N,2),dec(2*fo2['w1']/fo2['w0']-fo2['C1v']/fo2['C0'],2),dec(fo2['w1']/fo2['w0'],2),dec(fo2['C1v']/fo2['C0'],2)))
# pinned rows: read over the first correction at N=729, y=1/1024, delta=0
for r in rows:
    if r['tag']=='POLARITON_QUENCH_PIN' and r['N']=='729' and r['y']=='1/1024' and r['delta']=='0':
        t=Fr(r['t']); y=Fr(1,1024)
        fo3=E.first_order(Fr(0),y,729,t)
        A=Fr(int(r['A_ppb']),10**9)
        A1=2*abs(A)/729
        # README's w1, s^1 part only
        w1r=E.readme_w1_delta0(t)
        w0=fo3['w0']
        print('PIN N=729 t=%s read/first(full)=%s read/first(README w1)=%s read=%s'%(t,dec(A1/fo3['A1_first'],4),dec(A1/(2*y*abs(w0+w1r/729)),4),dec(A1,6)))
# exact C1 ratio of the first miss
d=[r for r in rows if r['tag']=='POLARITON_QUENCH_CONVERSION' and r['N']=='729' and r['delta']=='0' and r['s']=='1/4' and r['t']=='2'][0]
C1=Fr(int(d['C1_ppb']),10**9); L=law(729,0,Fr(d['y']),2)
print('first miss: C1=%s law=%s ratio=%s'%(dec(C1,7),dec(L['C1'],7),dec(C1/L['C1'],5)))
d=[r for r in rows if r['tag']=='POLARITON_QUENCH_CONVERSION' and r['N']=='2187' and r['s']=='1' and r['t']=='2'][0]
C1=Fr(int(d['C1_ppb']),10**9); L=law(2187,0,Fr(d['y']),2)
print('fourth miss: C1=%s law=%s ratio=%s'%(dec(C1,7),dec(L['C1'],7),dec(C1/L['C1'],5)))
# large-t coefficient checks: epsilon form against machine at delta=0,1/2,-1/2
from law import sqrt_fp, fr
for (delta,s,N,t) in ((Fr(0),Fr(1),729,Fr(2)),(Fr(0),Fr(1,4),729,Fr(3)),(Fr(1,2),Fr(1),729,Fr(3)),(Fr(-1,2),Fr(1),729,Fr(2)),(Fr(0),Fr(4),729,Fr(1))):
    y=s/27
    L=law(N,delta,y,t); g2=1-delta*delta
    from law import exp_fp,mul,fp
    g=sqrt_fp(g2); e2=fr(exp_fp(2*mul(g,fp(t))))
    eps=(5-2*delta)/(8*g2*g2)*e2/N
    Y=L['Y']
    fo4=E.first_order(delta,y,N,t)
    print('epsilon check delta=%s s=%s t=%s eps=%s Y=%s | V2 machine dev %s form %s | A1 machine dev %s form %s | C1 machine dev %s form %s'%(delta,s,t,dec(eps,4),dec(Y,3),
      dec((2*fo4['w1']/fo4['w0']-fo4['C1v']/fo4['C0'])/N,4),dec(eps*Y/(1+Y),4),dec(fo4['w1']/fo4['w0']/N,4),dec(-eps*(1+Y/2),4),dec(fo4['C1v']/fo4['C0']/N,4),dec(-2*eps*(1+2*Y+Y*Y/2)/(1+Y),4)))
