# How many of the P = +-1 grid points of out/t3_scan_small.hbp lie above the plane-wave edge, inside the window, for each N. Integers and rationals only.
import sys
from fractions import Fraction as F
from math import isqrt
SC = 10**24
def edge(u):
    r = u*(4-3*u)
    w = ((4-3*u) - F(isqrt(r.numerator*SC*SC//r.denominator), SC))/2
    return 1-w-u
tab = {}
for line in open("C:/tmp/opus55/polariton-recheck-window-20261105/out/t3_scan_small.hbp", encoding="utf-8").read().splitlines():
    if not line.startswith("SMALL_PARTIAL|"):
        continue
    d = dict(f.split("=",1) for f in line.split("|")[1:] if "=" in f)
    N,u,x,P = int(d["N"]),F(d["u"]),F(d["x"]),int(d["P"])
    t = tab.setdefault(N, dict(all=0,inside=0,inside_c0=0,top=None,ulist=set()))
    t["all"] += 1
    if u > 0 and u <= 1 and x > edge(u):
        t["inside"] += 1
        delta = u+x
        if delta < 1:
            rho=(1-delta)/(4-3*u)
            rho0=1-2*rho
            if rho0>0 and rho0/rho-u>0:
                t["inside_c0"] += 1
        t["ulist"].add(u)
        if t["top"] is None or x>t["top"][1]:
            t["top"]=(u,x)
for N in sorted(tab):
    t=tab[N]
    print("PARTIAL_INSIDE|N=%d|P=1_grid_points=%d|above_the_edge=%d|above_with_rho0>0_and_c0>0=%d|u_values_above=%s|highest=%s|json=0"%(N,t["all"],t["inside"],t["inside_c0"],sorted(str(a) for a in t["ulist"])[:12],t["top"]))
