# Largest residual_1e-12 by tag and N, in the receipt's pin and window rows.
rows = {}
for line in open("C:/tmp/qnn-polariton-wt/polariton/RECEIPT.hbp", encoding="utf-8").read().splitlines():
    tag = line.split("|", 1)[0]
    if tag in ("POLARITON_PIN", "POLARITON_PIN_WINDOW"):
        d = dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f)
        k = (tag, int(d["N"]))
        v = int(d["residual_1e-12"])
        if k not in rows or v > rows[k][0]:
            rows[k] = (v, d["u"], d["x"], d["s"], d["cycles"])
for k in sorted(rows):
    print("RESIDUAL|%s|N=%d|largest_1e-12=%d|at_u=%s|x=%s|s=%s|cycles=%s|json=0" % (k[0], k[1], rows[k][0], rows[k][1], rows[k][2], rows[k][3], rows[k][4]))
