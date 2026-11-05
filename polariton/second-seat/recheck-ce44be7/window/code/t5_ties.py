# Item 5. Exact ties at y = 0 between the lowest sector and another sector, on a rational grid, N <= 27. A tie between P and P + 2 is an exact doublet inside the even block, where the even-block centred difference in kappa also crosses a cusp.
import sys
from fractions import Fraction as F
sys.dont_write_bytecode = True
sys.path.insert(0, "C:/tmp/opus55/polariton-recheck-window-20261105/code")
from sec_lib import chain, ground_level, K, fx
US = [F(k, 16) for k in range(0, 25)]
XS = [F(k, 16) for k in range(-48, 25)]
stop = 1 << (K - 100)
tol = 1 << (K - 80)
for N in range(2, 28):
    ties = 0
    for u in US:
        for x in XS:
            lv = []
            for P in range(0, N + 1):
                d, o2 = chain(N, u, x, P)
                lv.append((ground_level(d, o2, stop=stop), P))
            lv.sort()
            if lv[1][0] - lv[0][0] < tol:
                ties += 1
                print("TIE|N=%d|u=%s|x=%s|P=%d,%d|E=%s|B_couples=%d|json=0" % (N, u, x, lv[0][1], lv[1][1], fx(lv[0][0], 9), abs(lv[0][1] - lv[1][1]) == 2 or (lv[0][1] == 1 and lv[1][1] == 1)))
    print("TIES_DONE|N=%d|points=%d|ties=%d|json=0" % (N, len(US) * len(XS), ties))
    sys.stdout.flush()
