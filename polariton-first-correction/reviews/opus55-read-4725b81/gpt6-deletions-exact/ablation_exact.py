# Exact-rational cross-check of GPT-6's ablation table on PR #11 (comment 6667700733): the frozen first-correction forms with single terms removed,
# against the ten K = 1600 rows of RECEIPT-GRID.hbp. No model run. It evaluates the row's text with the reader's own parser in exact fractions,
# which shares nothing with GPT-6's double-precision transcription. json=0.
import sys
from fractions import Fraction as Fr

WT = "C:/tmp/qnn-fc-read-wt/"
src = open(WT + "polariton-first-correction/read_first_correction.py", encoding="utf-8").read()
assert src.rstrip().endswith("main()")
ns = {"__name__": "reader_forms"}
exec(compile(src.rstrip()[: -len("main()")], "read_first_correction.py", "exec"), ns)
Forms, load_rows, E18 = ns["Forms"], ns["load_rows"], ns["E18"]
forms = Forms(open(WT + "polariton/PREDICTION.hbp", encoding="utf-8", newline="").read().split("\n")[47])
rows = [r for r in load_rows(WT + "polariton-first-correction/RECEIPT-GRID.hbp") if r.k == 1600]
assert len(rows) == 10
LIMIT = Fr(1, 1000)

ABLATIONS = [
    ("full", {}),
    ("law_alone", None),
    ("keep_only_w10_C10", {"w11": 0, "C11": 0, "C12": 0}),
    ("remove_C11_and_C12", {"C11": 0, "C12": 0}),
    ("remove_w11", {"w11": 0}),
    ("remove_C12", {"C12": 0}),
    ("remove_C11", {"C11": 0}),
    ("remove_C10", {"C10": 0}),
    ("remove_w10", {"w10": 0}),
]


def evaluate(n, delta, y, t, zero):
    """The row's forms at one point, with the named coefficients set to 0 after they are evaluated."""
    d = Fr(delta)
    g2 = (1 - d * d) * Fr(t) * Fr(t)
    env = {"N": Fr(n), "d": d, "y": Fr(y), "s2": Fr(n) * Fr(y) * Fr(y)}
    env["s4"] = env["s2"] * env["s2"]
    for k in (1, 2, 3, 4):
        env["c_%d" % k] = ns["cosh_series"](k, g2)
        env["gs_%d" % k] = ns["gamma_sinh_series"](k, g2)
    env["SINH_SQ"] = (env["c_2"] - 1) / 2
    for power, value in (("D3", 3), ("D4", 4), ("D5", 5)):
        env[power] = (1 + d) ** value * (1 - d) ** 2
    for name in ("w0", "C0", "w10", "w11", "C10", "C11", "C12"):
        env[name] = forms.evaluate_with_sinh(name, dict(env))
    for name, value in zero.items():
        env[name] = Fr(value)
    a1 = forms.evaluate("A1_first", env)
    c1 = forms.evaluate("C1_first", env)
    return a1, c1, a1 * a1 / (2 * c1)


out = []
for name, zero in ABLATIONS:
    passing = 0
    worst = [Fr(0)] * 3
    for r in rows:
        if zero is None:
            v = forms.values(r.n, r.delta, r.y, r.t)
            a1, c1 = v["A1_law"], v["C1_law"]
            v2 = a1 * a1 / (2 * c1)
        else:
            a1, c1, v2 = evaluate(r.n, r.delta, r.y, r.t, zero)
        offs = [abs(Fr(r.A1, E18) / a1 - 1), abs(Fr(r.C1, E18) / c1 - 1), abs(Fr(r.V2, E18) / v2 - 1)]
        worst = [max(w, o) for w, o in zip(worst, offs)]
        passing += all(o <= LIMIT for o in offs)
    out.append("FC_ABLATION|form=%s|points_passing_all_three=%d|of=10|worst_C1_ppm=%.2f|worst_A1_ppm=%.2f|worst_V2_ppm=%.2f|json=0" % (
        name, passing, worst[1] * 10 ** 6, worst[0] * 10 ** 6, worst[2] * 10 ** 6))
# Which points pass with C12 removed, and by how much C12 matters at each.
for r in rows:
    a1, c1, v2 = evaluate(r.n, r.delta, r.y, r.t, {"C12": 0})
    full = evaluate(r.n, r.delta, r.y, r.t, {})
    out.append("FC_ABLATION_POINT|form=remove_C12|delta=%s|s=%s|C1_off_ppm=%.1f|V2_off_ppm=%.1f|C12_term_over_C1_first_ppm=%.1f|json=0" % (
        r.delta, r.y * 81, (Fr(r.C1, E18) / c1 - 1) * 10 ** 6, (Fr(r.V2, E18) / v2 - 1) * 10 ** 6, (full[1] / c1 - 1) * 10 ** 6))
print("\n".join(out))
