# Summaries from out/t2_series.hbp: large |x| ratios per u and N, and how far from the zero line the 5% tolerance holds at each listed W.
from fractions import Fraction as F
import collections
rows = [dict(f.split("=",1) for f in l.split("|")[1:] if "=" in f) for l in open("C:/tmp/opus55/polariton-recheck-window-20261105/out/t2_series.hbp",encoding="utf-8").read().splitlines() if l.startswith("LARGE_X|")]
t = collections.defaultdict(list)
for r in rows:
    t[(r["u"],r["N"],r["x"])].append(r)
for (u,N,x),rs in sorted(t.items(), key=lambda kv:(F(kv[0][0]),int(kv[0][1]),F(kv[0][2]))):
    rd=[float(F(r["ratio"])) if False else 0 for r in rs]
print_rows = []
for r in rows:
    pass
# Columns are repeated names, so read by position.
lines=[l.split("|") for l in open("C:/tmp/opus55/polariton-recheck-window-20261105/out/t2_series.hbp",encoding="utf-8").read().splitlines() if l.startswith("LARGE_X|")]
agg=collections.defaultdict(list)
for p in lines:
    d={}
    u=p[1].split("=")[1];x=p[2].split("=")[1];N=p[3].split("=")[1];s=p[4].split("=")[1]
    ratio_a=p[8].split("=")[1]; ratio_d=p[11].split("=")[1]; sign=p[12].split("=")[1]; last=p[13].split("=")[1]; p2=p[5].split("=")[1]; nuw=p[14].split("=")[1]
    agg[(F(u),int(N))].append((F(x),s,F(ratio_a),F(ratio_d),sign,F(p2),F(nuw)))
for (u,N),v in sorted(agg.items()):
    worst=max(v,key=lambda t:abs(t[3]-1))
    worsta=max(v,key=lambda t:abs(t[2]-1))
    print("LARGE_X_SUMMARY|u=%s|N=%d|rows=%d|D2_ratio_furthest=%s_at_x=%s,s=%s,Nu(u-x)=%s|A1_ratio_furthest=%s_at_x=%s,s=%s|signs_ok=%s|json=0"%(u,N,len(v),float(worst[3]).__round__(4),worst[0],worst[1],float(worst[6]).__round__(1),float(worsta[2]).__round__(4),worsta[0],worsta[1],all(t[4]=="1" for t in v)))
