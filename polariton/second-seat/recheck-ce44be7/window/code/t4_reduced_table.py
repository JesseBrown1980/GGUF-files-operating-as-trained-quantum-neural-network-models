rows=[dict(f.split("=",1) for f in l.split("|")[1:] if "=" in f) for l in open("C:/tmp/opus55/polariton-recheck-window-20261105/out/t4_reduced.hbp",encoding="utf-8").read().splitlines() if l.startswith("REDUCED|")]
pts=[]
for r in rows:
    k=(r["u"],r["x"])
    if k not in pts: pts.append(k)
for k in pts:
    for s in ("1","4","16"):
        rs=[r for r in rows if (r["u"],r["x"])==k and r["s"]==s]
        print("u=%s x=%s s=%s q=%s |"%(k[0],k[1],s,rs[0]["q"]), " ".join("N=%s R=%s T=%s A=%s"%(r["N"],r["D2_ratio"],r["N(D2_ratio-1)"],r["A1_ratio"]) for r in rs))
    print("receipt_offs:", [ (r["N"],r["s"],r.get("receipt_E_off"),r.get("receipt_A_off"),r.get("receipt_B_off")) for r in rows if (r["u"],r["x"])==k and r["N"] in ("243","729") and r["s"]=="16"])
