# Item 5. Doctored rows through the route's compare_full, with the even block as committed and with the first read's whole-space centred difference, from a copy in my folder.
# Each row is a real receipt row with one reading changed the way an engine fault would change it. The question: does the change hide a fault the old check would have caught?
import sys, importlib.util, io, contextlib
sys.dont_write_bytecode = True
from fractions import Fraction as F

SRC = "C:/tmp/qnn-polariton-wt/polariton/second_route.py"
spec = importlib.util.spec_from_file_location("second_route", SRC)
route = importlib.util.module_from_spec(spec)
spec.loader.exec_module(route)
TMP = "C:/tmp/opus55/polariton-recheck-window-20261105/out/doctored_rows.hbp"

orig_full_ground = route.full_ground


def run(rows, whole):
    if whole:
        def patched(n, x, u, y, kappa_b=F(0), width=F(1, 1 << 44), kappa_n=F(0), even=False):
            return orig_full_ground(n, x, u, y, kappa_b, width, kappa_n, even=False)
        route.full_ground = patched
    else:
        route.full_ground = orig_full_ground
    with open(TMP, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(rows) + "\n")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = route.compare_full(TMP, 9)
    done = [l for l in buf.getvalue().splitlines() if l.startswith("SECOND_ROUTE_FULL_DONE")][0]
    return rc, done


real = {}
for line in open("C:/tmp/qnn-polariton-wt/polariton/RECEIPT.hbp", encoding="utf-8").read().splitlines():
    if line.startswith("POLARITON_PIN_WINDOW|N=3|") or line.startswith("POLARITON_PIN_WINDOW|N=9|"):
        d = dict(f.split("=", 1) for f in line.split("|")[1:] if "=" in f)
        real[(d["N"], d["u"], d["x"], d["s"])] = line


def edit(line, **kw):
    parts = line.split("|")
    out = []
    for p in parts:
        k = p.split("=", 1)[0]
        if k in kw:
            out.append("%s=%s" % (k, kw[k]))
        else:
            out.append(p)
    return "|".join(out)


doublet = real[("3", "1/4", "-1/4", "0")]
s1 = real[("3", "1/4", "-1/4", "1")]
pw = real[("3", "1", "-1/4", "0")]
pw_s = real[("3", "1", "-1/4", "1/2")]
cases = [
    ("doublet_as_read", doublet),
    ("doublet_B=0_pure_P=+1_state", edit(doublet, B_ppb="0")),
    ("doublet_B=-even_the_odd_member", edit(doublet, B_ppb="-837780860")),
    ("doublet_B_half_a_broken_read", edit(doublet, B_ppb="418890430")),
    ("plane_wave_doublet_as_read", pw),
    ("plane_wave_doublet_B=1e-3", edit(pw, B_ppb="1000000")),
    ("pinned_row_as_read_N3_s1", s1),
    ("pinned_row_B_times_1.001", edit(s1, B_ppb=str(int(int(s1.split("|B_ppb=")[1].split("|")[0]) * 1001 // 1000)))),
    ("pinned_row_B_negated", edit(s1, B_ppb=str(-int(s1.split("|B_ppb=")[1].split("|")[0])))),
    # The odd member's numbers at N = 3, u = 1, x = -1/4, s = 1/2, from out/t1_parity.hbp: E 0.004524 above, B +0.2655 from the even, A +0.0776.
    ("engine_on_the_odd_level_N3", edit(pw_s, energy_ppb=str(int(pw_s.split("|energy_ppb=")[1].split("|")[0]) + 4524000), B_ppb=str(int(pw_s.split("|B_ppb=")[1].split("|")[0]) + 265500000), A_ppb=str(int(pw_s.split("|A_ppb=")[1].split("|")[0]) + 77570000))),
]
for name, row in cases:
    rc_e, done_e = run([row], False)
    rc_w, done_w = run([row], True)
    print("DOCTORED|%s|even_block_flags=%d|whole_space_flags=%d|json=0" % (name, rc_e, rc_w))
    sys.stdout.flush()
