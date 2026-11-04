# Compare the integer engine's amplitudes with Google's simulator's text output, in exact integers: qsim's decimal strings are read as
# exact rationals over powers of ten. Usage: compare_qsim.py INTEGER_OUT QSIM_OUT [LABEL]. json=0.
import sys


def decimal_at_2_60(text):
    """A decimal string, as a rational (numerator, denominator)."""
    t = text.strip().lower()
    exponent = 0
    if "e" in t:
        t, e = t.split("e")
        exponent = int(e)
    sign = -1 if t.startswith("-") else 1
    t = t.lstrip("+-")
    whole, _, fraction = t.partition(".")
    numerator = int((whole + fraction) or "0") * sign
    exponent -= len(fraction)
    if exponent >= 0:
        return numerator * 10 ** exponent, 1
    return numerator, 10 ** (-exponent)


rows = [r.split("|") for r in open(sys.argv[1], encoding="utf-8").read().splitlines() if r.startswith("FULL_Q24_AMPLITUDE")]
ours = [(int(r[2].split("=")[1]), int(r[3].split("=")[1])) for r in rows]
theirs = [line.split() for line in open(sys.argv[2], encoding="utf-8").read().splitlines() if line.strip()]
assert len(ours) == len(theirs), (len(ours), len(theirs))
SCALE = 1 << 60
worst_num, worst_den, at = 0, 1, -1
over = 0
small = 0
BOUND = (1, 10 ** 6)
for i, ((re, im), (a, b)) in enumerate(zip(ours, theirs)):
    for mine, other in ((re, a), (im, b)):
        n, d = decimal_at_2_60(other)
        diff_num = abs(mine * d - n * SCALE)
        diff_den = d * SCALE
        if diff_num * worst_den > worst_num * diff_den:
            worst_num, worst_den, at = diff_num, diff_den, i
        if diff_num * BOUND[1] > BOUND[0] * diff_den:
            over += 1
label = sys.argv[3] if len(sys.argv) > 3 else "real"
print("COMPARE|run=%s|bitstrings=%d|parts_compared=%d|parts_above_1e-6=%d|largest_difference_in_units_of_1e-12=%d|at_row=%d|json=0" % (
    label, len(ours), 2 * len(ours), over, worst_num * 10 ** 12 // worst_den, at))
mine0 = ours[0]
print("FIRST|ours_re_1e-12=%d|ours_im_1e-12=%d|qsim=%s,%s|json=0" % (mine0[0] * 10 ** 12 // SCALE, mine0[1] * 10 ** 12 // SCALE, theirs[0][0], theirs[0][1]))
total = 0
for re, im in ours:
    total += re * re + im * im
print("MEAN_P_OF_THE_64|times_2^24_ppm=%d|json=0" % (total * (1 << 24) * 10 ** 6 // (64 * SCALE * SCALE)))
