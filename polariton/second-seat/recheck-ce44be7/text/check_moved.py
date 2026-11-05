# Which rows moved between the third run's receipt (8dfa11a) and this head's receipt.
import sys
sys.path.insert(0, 'C:/tmp/opus55/polariton-recheck-text-20261105')
from lib import *
out = open(ME + 'out/check_moved.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s); out.write(s + '\n')
T3 = load(WT + 'polariton/third-run/RECEIPT.hbp')
KEYS = {'POLARITON_SECTOR': ('N', 'u', 'x', 'P'), 'POLARITON_PIN': ('N', 'u', 'x', 'y', 's'), 'POLARITON_QUENCH': ('N', 'u', 'x', 'y', 't', 'delta'), 'POLARITON_QUENCH_PIN': ('N', 'u', 'x', 'y', 't', 'delta'), 'POLARITON_QUENCH_BAND': ('N', 'u', 'x', 'y', 'delta'), 'POLARITON_REVERSAL': ('N', 'full', 'y'), 'POLARITON_WAVEVECTOR': ('N', 'u'), 'POLARITON_CONTROL_NO_BOSE': ('N', 't'), 'POLARITON_TAYLOR_POINT': ('N', 'u', 'x', 'y', 't'), 'POLARITON_SYMMETRY': ('N', 's'), 'POLARITON_QUENCH_OTHER_U': ('N', 'u', 'x', 't'), 'POLARITON_SECTOR_EQUALS_FULL': ('N',)}
for tag, ks in KEYS.items():
    a = {tuple(r[k] for k in ks): r['_raw'] for r in T3.get(tag, [])}
    b = {tuple(r[k] for k in ks): r['_raw'] for r in R.get(tag, [])}
    same = sum(a[k] == b.get(k) for k in a)
    only3 = len(set(a) - set(b)); only4 = len(set(b) - set(a))
    P(tag, 'third', len(a), 'fourth', len(b), 'byte-equal', same, 'only third', only3, 'only fourth', only4)
    if tag in ('POLARITON_PIN',):
        moved = [k for k in a if k in b and a[k] != b[k]]
        for k in moved[:4]:
            P('  ', a[k][:170]); P('  ', b[k][:170])
    if tag == 'POLARITON_SECTOR':
        moved = [k for k in a if k in b and a[k] != b[k]]
        P('   moved by N', {n: sum(int(k[0]) == n for k in moved) for n in sorted({int(k[0]) for k in moved})})
        import collections
        # how many moved rows change any value besides e_at_2^60 at N<=243
        small = [k for k in moved if int(k[0]) <= 243]
        P('   moved at N<=243', len(small))
out.close()
