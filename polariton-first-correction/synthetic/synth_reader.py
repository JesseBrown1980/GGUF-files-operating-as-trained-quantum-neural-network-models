# synth_reader.py: SYNTHETIC grid receipts, built from the row's closed forms typed in forms_mine.py and then perturbed, read by read_first_correction.py grid.
# Every row here is marked synthetic=1, every file starts with a SYNTHETIC line. No engine runs, no model runs: nothing here calls polariton_first_correction or run_stage.
# Each scenario writes its own receipt, runs the reader, and tests what the reader printed against what the row's words ask.
import os
import re
import subprocess
import sys
from fractions import Fraction as Fr

sys.dont_write_bytecode = True
# usage: synth_reader.py READER OUT_DIR. It exits 1 when a scenario reads otherwise than the row asks.
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from forms_mine import Point
from math import isqrt

WT = os.path.dirname(os.path.dirname(HERE))
D = WT + "/polariton-first-correction"
READER = sys.argv[1]
SYN = sys.argv[2]
TAG = "battery"
PRED = WT + "/polariton/PREDICTION.hbp"
PLAN = D + "/PLAN.hbp"
PY = ["python3", "-I", "-B", "-X", "utf8"]
E18 = 10 ** 18
GRID = [(Fr(1, 2), Fr(1, 4)), (Fr(1, 2), Fr(1, 2)), (Fr(0), Fr(1, 4)), (Fr(0), Fr(1, 2)), (Fr(1, 4), Fr(1, 4)), (Fr(1, 4), Fr(1, 2)), (Fr(1, 4), Fr(1)), (Fr(-1, 4), Fr(1, 4)), (Fr(-1, 4), Fr(1, 2)), (Fr(-1, 4), Fr(1))]
BLIND = [(Fr(1, 2), Fr(1, 4)), (Fr(1, 2), Fr(1, 2)), (Fr(1, 4), Fr(1, 4)), (Fr(1, 4), Fr(1, 2)), (Fr(1, 4), Fr(1)), (Fr(-1, 4), Fr(1, 4)), (Fr(-1, 4), Fr(1, 2)), (Fr(-1, 4), Fr(1))]
REMAINDER = [(Fr(0), Fr(1, 4)), (Fr(0), Fr(1, 2)), (Fr(1, 2), Fr(1, 4)), (Fr(1, 2), Fr(1, 2))]
CACHE = {}


def forms_at(n, d, y):
    key = (n, d, y)
    if key not in CACHE:
        CACHE[key] = Point(n, d, y, 2).forms()
    return CACHE[key]


def e(value):
    return (Fr(value) * E18).__floor__()


class Row:
    """A synthetic receipt row with the engine's fields in the engine's order, from values given as Fractions."""

    def __init__(self, n, k, d, y):
        self.n, self.k, self.d, self.y = n, k, d, y
        f = forms_at(n, d, y)
        self.t = 2
        self.c1 = f["C1_first"]
        self.a1 = f["A1_first"]
        self.v2 = None  # None: A1^2/(2 C1), its definition
        self.a = None  # None: -A1 N/2
        self.b = Fr(10)
        self.c1_err = Fr(1, 10 ** 13)
        self.a1_err = Fr(1, 10 ** 12)
        self.v2_lo = None  # None: monotone division on C1 and A1
        self.v2_hi = None
        self.v2_err = None  # set: a printed interval of this half width
        self.eps_tail = Fr(0) if k >= n else Fr(2, 10 ** 11) if k == 1200 else Fr(1, 10 ** 11)
        self.eps_poly = Fr(1, 10 ** 16)
        self.eps_round = Fr(1, 10 ** 12)
        self.eps = None
        self.norm_off = Fr(0)
        self.energy = Fr(0)
        self.f = f["f"]
        self.x = None
        self.extra = ""
        self.sabotage = ""

    def line(self):
        dim = sum(q // 2 + 1 for q in range(self.k + 1))
        eps = self.eps if self.eps is not None else self.eps_tail + self.eps_poly + self.eps_round
        v2 = self.v2 if self.v2 is not None else self.a1 * self.a1 / (2 * self.c1)
        a = self.a if self.a is not None else -self.a1 * self.n / 2
        if self.v2_err is not None:
            v2_lo, v2_hi = v2 - self.v2_err, v2 + self.v2_err
        else:
            v2_lo = (self.a1 - self.a1_err) ** 2 / (2 * (self.c1 + self.c1_err))
            v2_hi = (self.a1 + self.a1_err) ** 2 / (2 * (self.c1 - self.c1_err)) if self.c1 > self.c1_err else Fr(-1, E18)
        v2_lo = self.v2_lo if self.v2_lo is not None else v2_lo
        v2_hi = self.v2_hi if self.v2_hi is not None else v2_hi
        x = self.x if self.x is not None else self.d - 1
        full = self.k >= self.n
        norm_b = 0 if full else 1000 << 20
        tail = Fr(1, 10 ** 13)
        leak_max = Fr(0) if full else Fr(1, 10 ** 11)
        leak_sum = Fr(27, E18) if full else Fr(1, 10 ** 12)
        sab = "sabotage=%s|" % self.sabotage if self.sabotage else ""
        return (
            "POLARITON_FIRST_CORRECTION_READ|%sN=%d|K=%d|even_states=%d|array_bytes=%d|u=1|x=%s|y=%s|delta=%s|t=%d|window=2^-6|c=0|E=1000|degree=40|reach=81|applies=10200|elem_err_units=2|"
            "jbar_e18=%d|f_e18=%d|A_e18=%d|B_e18=%d|C1_e18=%d|C2_e18=%d|A1_e18=%d|D2_e18=%d|V2_e18=%d|energy_e18=%d|norm_off_e18=%d|"
            "eps_tail_e18=%d|eps_poly_e18=%d|eps_round_e18=%d|eps_e18=%d|C1_err_e18=%d|A1_err_e18=%d|V2_lo_e18=%d|V2_hi_e18=%d|norm_B_s20=%d|tail_max_e18=%d|leak_max_e18=%d|leak_sum_e18=%d|float_used=0|synthetic=1%s|json=0\n"
            % (sab, self.n, self.k, dim, dim * 120, x, self.y, self.d, self.t,
               e(self.f * self.n / 2), e(self.f), e(a), e(self.b), e(self.c1), e(self.c1 / 100), e(self.a1), e(2 * abs(self.b) / self.n), e(v2), e(self.energy), e(self.norm_off),
               e(self.eps_tail), e(self.eps_poly), e(self.eps_round), e(eps), e(self.c1_err), e(self.a1_err), e(v2_lo), e(v2_hi), norm_b, e(tail), e(leak_max), e(leak_sum), self.extra)
        )


def nominal_grid(off=Fr(1, 10000)):
    """K = 1200 and K = 1600 at every point, reads on first * (1 + off) for C1, near first for A1 and V2."""
    rows = {}
    for d, s in GRID:
        y = s / 81
        for k in (1200, 1600):
            r = Row(6561, k, d, y)
            r.c1 = r.c1 * (1 + off)
            rows[(d, s, k)] = r
    return rows


def nominal_base(r729=Fr(11, 1000)):
    """K = 729 at N = 729 at the 4 remainder points, residual r729 on C1."""
    rows = {}
    for d, s in REMAINDER:
        y = s / 27
        r = Row(729, 729, d, y)
        r.c1 = r.c1 * (1 + r729)
        rows[(d, s)] = r
    return rows


COUNT = {"pass": 0, "fail": 0}
OUT = []
RESULTS = {}


def write(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("SYNTHETIC|values_from_closed_forms_typed_from_F5=1|engine_runs=0|model_runs=0|json=0\n")
        for r in rows:
            handle.write(r.line())


def read(tag, grid_rows, base_rows):
    gpath = "%s/out-%s/%s-grid.hbp" % (SYN, TAG, tag)
    bpath = "%s/out-%s/%s-base.hbp" % (SYN, TAG, tag)
    write(gpath, grid_rows)
    write(bpath, base_rows)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run(PY + [READER, "grid", PRED, PLAN, bpath, gpath], capture_output=True, text=True, env=env, encoding="utf-8")
    open("%s/out-%s/%s-read.hbp" % (SYN, TAG, tag), "w", encoding="utf-8", newline="\n").write(p.stdout + ("\nSTDERR|" + p.stderr if p.stderr else ""))
    return p.returncode, p.stdout, p.stderr


def lines_of(text, *needles):
    return [line for line in text.splitlines() if all(n in line for n in needles)]


def field(line, key):
    m = re.search(r"\|%s=([^|]*)" % re.escape(key), line)
    return m.group(1) if m else None


def report(name, ok, detail=""):
    COUNT["pass" if ok else "fail"] += 1
    OUT.append("SYN|scenario=%s|as_the_row_asks=%d|%s|json=0" % (name, ok, detail))


def read_row(text, delta, s, obs):
    got = lines_of(text, "FC_READ|", "|delta=%s|" % delta, "|s=%s|" % s, "|obs=%s|" % obs)
    return got[0] if got else None


def done(text):
    got = lines_of(text, "FC_READ_DONE")
    return got[0] if got else "NO_DONE_ROW"


def set_counts(text, name):
    got = lines_of(text, "FC_READ_SET|set=%s|" % name)
    return (field(got[0], "points"), field(got[0], "all_rows_met"), field(got[0], "with_a_miss")) if got else None


def main():
    os.makedirs(SYN + "/out-" + TAG, exist_ok=True)
    # S00 nominal.
    g = nominal_grid()
    b = nominal_base()
    rc, out, err = read("S00", list(g.values()), list(b.values()))
    blind_counts, touched_counts = set_counts(out, "blind"), set_counts(out, "touched")
    report("S00_nominal_all_met", rc == 0 and blind_counts == ("8", "8", "0") and touched_counts == ("2", "2", "0"), "rc=%s|blind=%s|touched=%s|done=%s" % (rc, blind_counts, touched_counts, field(done(out), "failed")))
    rem = lines_of(out, "set=remainder")
    report("S00_nominal_remainder_rows", len(rem) == 4 and all(field(x, "result") == "MET" for x in rem), "rows=%d|results=%s" % (len(rem), ",".join(field(x, "result") for x in rem)))
    report("S00_cert_printed_on_every_point", len(lines_of(out, "FC_CERT|")) == 10, "FC_CERT_rows=%d" % len(lines_of(out, "FC_CERT|")))
    report("S00_denominator_and_absolute_error_printed", all("first_e18=" in x and "abs_off_e18=" in x for x in lines_of(out, "FC_READ|", "|obs=C1|")), "")

    # S01 just inside and just outside 1/1000, each observable, each sign, at a blind point and at a touched point.
    gap = Fr(1, 10 ** 9)
    for d, s, set_name in ((Fr(1, 4), Fr(1), "blind"), (Fr(0), Fr(1, 2), "touched")):
        f = forms_at(6561, d, s / 81)
        for obs, key, attr in (("C1", "C1_first", "c1"), ("A1", "A1_first", "a1"), ("V2", "V2_first", "v2")):
            for sign, sign_name in ((1, "plus"), (-1, "minus")):
                for offset, want, label in ((Fr(1, 1000) - gap, "MET", "inside"), (Fr(1, 1000) + gap, "MISS", "outside")):
                    g = nominal_grid(Fr(0))
                    for k in (1200, 1600):
                        r = g[(d, s, k)]
                        if obs == "V2":
                            # V2 moved through A1, on V2's definition: A1 = first sqrt(1 + off), rational within 10^-30.
                            ratio = 1 + sign * offset
                            root = Fr(isqrt((ratio.numerator * 10 ** 60) // ratio.denominator), 10 ** 30)
                            r.a1 = f["A1_first"] * root
                        else:
                            setattr(r, attr, f[key] * (1 + sign * offset))
                            r.v2 = f["V2_first"]
                            r.v2_err = Fr(1, 10 ** 12)
                    rc, out, err = read("S01-%s-%s-%s-%s" % (set_name, obs, sign_name, label), list(g.values()), list(nominal_base().values()))
                    row = read_row(out, d, s, obs)
                    got = field(row, "result") if row else None
                    want_counts = ("8", "8", "0") if want == "MET" else ("8", "7", "1") if set_name == "blind" else ("8", "8", "0")
                    report("S01_%s_%s_%s_%s" % (set_name, obs, sign_name, label), got == want and set_counts(out, "blind") == want_counts, "off_ppb=%s|result=%s|certified_inside=%s|blind=%s|touched=%s|rc=%s" % (field(row, "off_over_first_ppb"), got, field(row, "certified_inside"), set_counts(out, "blind"), set_counts(out, "touched"), rc))

    # S02 a wide certificate: the read inside, the interval over the limit. The row: combined error smaller than the margin to 1/1000.
    d, s = Fr(1, 4), Fr(1)
    f = forms_at(6561, d, s / 81)
    for obs, attr_err, key in (("C1", "c1_err", "C1_first"), ("A1", "a1_err", "A1_first")):
        for ratio, want, label in ((Fr(9, 10), "MET", "under_limit"), (Fr(11, 10), "MISS", "over_limit")):
            g = nominal_grid(Fr(0))
            for k in (1200, 1600):
                setattr(g[(d, s, k)], attr_err, f[key] * Fr(1, 1000) * ratio)
            rc, out, err = read("S02-%s-%s" % (obs, label), list(g.values()), list(nominal_base().values()))
            row = read_row(out, d, s, obs)
            report("S02_wide_certificate_%s_%s" % (obs, label), field(row, "result") == want, "abs_off_ppb=%s|numerical_half_width_e18=%s|certified_inside=%s|result=%s|rc=%s" % (field(row, "off_over_first_ppb"), field(row, "numerical_half_width_e18"), field(row, "certified_inside"), field(row, "result"), rc))
    # V2, each side of the interval alone.
    fv = f["V2_first"]
    for side, lo_ratio, hi_ratio, want in (("lo_out", Fr(-11, 10), Fr(1, 10), "MISS"), ("hi_out", Fr(-1, 10), Fr(11, 10), "MISS"), ("both_in", Fr(-9, 10), Fr(9, 10), "MET")):
        g = nominal_grid(Fr(0))
        for k in (1200, 1600):
            r = g[(d, s, k)]
            r.v2_lo = fv * (1 + lo_ratio / 1000)
            r.v2_hi = fv * (1 + hi_ratio / 1000)
        rc, out, err = read("S02-V2-%s" % side, list(g.values()), list(nominal_base().values()))
        row = read_row(out, d, s, "V2")
        report("S02_wide_certificate_V2_%s" % side, field(row, "result") == want, "certified_inside=%s|result=%s" % (field(row, "certified_inside"), field(row, "result")))

    # V2 read outside the limit with its printed interval inside: the read's own clause reads this one.
    g = nominal_grid(Fr(0))
    for k in (1200, 1600):
        r = g[(d, s, k)]
        r.v2 = fv * (1 + Fr(2, 1000))
        r.v2_lo = fv * (1 - Fr(1, 2000))
        r.v2_hi = fv * (1 + Fr(1, 2000))
    rc, out, err = read("S02-V2-read-outside-its-interval", list(g.values()), list(nominal_base().values()))
    row = read_row(out, d, s, "V2")
    report("S02_V2_read_outside_its_interval_MISS", field(row, "result") == "MISS", "certified_inside=%s|result=%s" % (field(row, "certified_inside"), field(row, "result")))

    # S03 the printed ratio numerical_over_margin: half width in absolute units over a margin in relative units.
    g = nominal_grid(Fr(0))
    d, s = Fr(1, 2), Fr(1, 4)
    f = forms_at(6561, d, s / 81)
    for k in (1200, 1600):
        g[(d, s, k)].c1_err = f["C1_first"] * Fr(5, 10000)  # half the limit
    rc, out, err = read("S03", list(g.values()), list(nominal_base().values()))
    row = read_row(out, d, s, "C1")
    printed = int(field(row, "numerical_over_margin_ppm"))
    # (half/first)/margin with margin = 1/1000 - |off| and off = 0: 0.5, so 500000 ppm.
    report("S03_numerical_over_margin_printed_in_one_unit", abs(printed - 500000) <= 1000, "printed_ppm=%d|asked_ppm_half_over_first_over_margin=500000|first_e18=%s" % (printed, field(row, "first_e18")))

    # S04 blind and touched apart, one miss at a time, and several misses at one point count once.
    for tag, miss_points, want_blind, want_touched in (
        ("one_blind", [(Fr(1, 2), Fr(1, 4))], ("8", "7", "1"), ("2", "2", "0")),
        ("one_touched", [(Fr(0), Fr(1, 4))], ("8", "8", "0"), ("2", "1", "1")),
        ("two_touched", [(Fr(0), Fr(1, 4)), (Fr(0), Fr(1, 2))], ("8", "8", "0"), ("2", "0", "2")),
        ("all_blind", BLIND, ("8", "0", "8"), ("2", "2", "0")),
    ):
        g = nominal_grid(Fr(0))
        for p in miss_points:
            f = forms_at(6561, p[0], p[1] / 81)
            for k in (1200, 1600):
                r = g[(p[0], p[1], k)]
                r.c1 = f["C1_first"] * Fr(102, 100)
                r.a1 = f["A1_first"] * Fr(102, 100)
        rc, out, err = read("S04-%s" % tag, list(g.values()), list(nominal_base().values()))
        report("S04_%s" % tag, set_counts(out, "blind") == want_blind and set_counts(out, "touched") == want_touched, "blind=%s|touched=%s|rc=%s" % (set_counts(out, "blind"), set_counts(out, "touched"), rc))
        sets = {field(x, "set") for x in lines_of(out, "FC_READ|", "|obs=C1|") if field(x, "delta") == str(Fr(0))}
        report("S04_%s_delta0_rows_labelled_touched" % tag, sets == {"touched"}, "sets=%s" % sorted(sets))

    # S05 the nondiscriminating mark: the read on the law.
    d, s = Fr(1, 4), Fr(1, 2)
    f = forms_at(6561, d, s / 81)
    g = nominal_grid(Fr(0))
    for k in (1200, 1600):
        g[(d, s, k)].c1 = f["C1_law"] * (1 + Fr(5, 10000))
    rc, out, err = read("S05-C1", list(g.values()), list(nominal_base().values()))
    ctrl = lines_of(out, "FC_CONTROL|", "|delta=1/4|", "|s=1/2|", "|obs=C1|")
    ctrl_set = lines_of(out, "FC_CONTROL_SET")
    report("S05_C1_on_law_marked_nondiscriminating", field(ctrl[0], "state") == "NONDISCRIMINATING" and "1/4:1/2:C1" in ctrl_set[0], "state=%s|set=%s|C1_result=%s" % (field(ctrl[0], "state"), field(ctrl_set[0], "nondiscriminating"), field(read_row(out, d, s, "C1"), "result")))
    g = nominal_grid(Fr(0))
    for k in (1200, 1600):
        g[(d, s, k)].a1 = f["A1_law"] * (1 + Fr(5, 10000))
    rc, out, err = read("S05-A1", list(g.values()), list(nominal_base().values()))
    ctrl = lines_of(out, "FC_CONTROL|", "|delta=1/4|", "|s=1/2|", "|obs=A1|")
    report("S05_A1_on_law_marked_nondiscriminating", field(ctrl[0], "state") == "NONDISCRIMINATING", "state=%s" % field(ctrl[0], "state"))
    # Just over the law's limit: discriminates.
    g = nominal_grid(Fr(0))
    for k in (1200, 1600):
        g[(d, s, k)].c1 = f["C1_law"] * (1 + Fr(1, 1000) + Fr(1, 10 ** 9))
    rc, out, err = read("S05-C1-just-over", list(g.values()), list(nominal_base().values()))
    ctrl = lines_of(out, "FC_CONTROL|", "|delta=1/4|", "|s=1/2|", "|obs=C1|")
    report("S05_C1_just_over_law_discriminates", field(ctrl[0], "state") == "DISCRIMINATES", "state=%s" % field(ctrl[0], "state"))
    # Nominal: all 20 discriminate, set says none.
    g = nominal_grid(Fr(0))
    rc, out, err = read("S05-nominal", list(g.values()), list(nominal_base().values()))
    report("S05_nominal_none", field(lines_of(out, "FC_CONTROL_SET")[0], "nondiscriminating") == "none" and len(lines_of(out, "FC_CONTROL|")) == 20, "rows=%d" % len(lines_of(out, "FC_CONTROL|")))

    # S06 the remainder, on intervals.
    def remainder_case(tag, r729, r6561, err729=Fr(1, 10 ** 14), err6561=Fr(1, 10 ** 14), want="MET", sign6561=1):
        g = nominal_grid(Fr(0))
        b = nominal_base(r729)
        for k in (1200, 1600):
            r = g[(Fr(0), Fr(1, 4), k)]
            r.c1 = forms_at(6561, Fr(0), Fr(1, 324))["C1_first"] * (1 + sign6561 * r6561)
            r.c1_err = err6561
        b[(Fr(0), Fr(1, 4))].c1_err = err729
        rc, out, err = read("S06-%s" % tag, list(g.values()), list(b.values()))
        row = lines_of(out, "set=remainder", "|delta=0|", "|s=1/4|")[0]
        report("S06_%s" % tag, field(row, "result") == want, "R729_ppb=%s|R6561_ppb=%s|e729_ppb=%s|e6561_ppb=%s|gap_ppb=%s|ratio_x1000_lo=%s|below=%s|result=%s" % (field(row, "R729_ppb"), field(row, "R6561_ppb"), field(row, "e729_ppb"), field(row, "e6561_ppb"), field(row, "gap_to_30x_ppb"), field(row, "ratio_times_1000_lo"), field(row, "error_below_residual_and_gap"), field(row, "result")))

    r6561 = Fr(1, 10000)
    remainder_case("above_30x", 40 * r6561, r6561, want="MET")
    remainder_case("just_above_30x", 30 * r6561 * (1 + Fr(1, 10 ** 5)), r6561, want="MET")
    remainder_case("just_below_30x", 30 * r6561 * (1 - Fr(1, 10 ** 5)), r6561, want="MISS")
    # Point value over 30x, interval under: the gap is 30e-4 * 1e-5 = 3e-8; e6561 relative 2e-8 is under gap and under the residual, but 30 e6561 is over the gap.
    c1f = forms_at(6561, Fr(0), Fr(1, 324))["C1_first"]
    remainder_case("point_over_interval_under", 30 * r6561 * (1 + Fr(1, 10 ** 5)), r6561, err6561=c1f * Fr(2, 10 ** 8), want="MISS")
    # Interval over 30x with the error above the N=6561 residual: e6561 > r6561 at a tiny r6561.
    remainder_case("error_above_residual", 40 * Fr(1, 10 ** 6), Fr(1, 10 ** 6), err6561=c1f * Fr(2, 10 ** 6), want="MISS")
    # Interval far over 30x, error above the N=6561 residual: the row's error clause alone reads this one.
    remainder_case("error_above_residual_interval_over_30x", Fr(1, 1000), Fr(1, 10 ** 6), err6561=c1f * Fr(2, 10 ** 6), want="MISS")
    # e729 above the gap.
    c1f729 = forms_at(729, Fr(0), Fr(1, 108))["C1_first"]
    remainder_case("e729_above_gap", 30 * r6561 * (1 + Fr(1, 10 ** 5)), r6561, err729=c1f729 * Fr(4, 10 ** 8), want="MISS")
    remainder_case("residual_sign_flip_reads_on_abs", 40 * r6561, r6561, want="MET", sign6561=-1)

    # S07 signs, with their errors.
    d, s = Fr(-1, 4), Fr(1, 4)

    def sign_case(tag, setter, want):
        g = nominal_grid(Fr(0))
        for k in (1200, 1600):
            setter(g[(d, s, k)])
        rc, out, err = read("S07-%s" % tag, list(g.values()), list(nominal_base().values()))
        row = read_row(out, d, s, "signs")
        report("S07_%s" % tag, field(row, "result") == want, "A_e18=%s|A_err_e18=%s|B_e18=%s|B_err_e18=%s|result=%s" % (field(row, "A_e18"), field(row, "A_err_e18"), field(row, "B_e18"), field(row, "B_err_e18"), field(row, "result")))

    def a_positive(r):
        r.a = Fr(1, 100)

    def a_small_negative(r):
        r.a = -Fr(1, 10 ** 12)

    def b_negative(r):
        r.b = -Fr(1, 100)

    def b_small_positive(r):
        r.b = Fr(1, 10 ** 8)  # b_err >= 2^-22 = 2.4e-7

    def a_within_err(r):
        r.a1_err = r.a1 * Fr(11, 20)

    sign_case("A_positive_MISS", a_positive, "MISS")
    sign_case("A_negative_inside_its_error_MISS", a_small_negative, "MISS")
    sign_case("A_negative_err_just_too_wide_MISS", a_within_err, "MISS")
    sign_case("B_negative_MISS", b_negative, "MISS")
    sign_case("B_positive_inside_its_error_MISS", b_small_positive, "MISS")
    sign_case("nominal_MET", lambda r: None, "MET")

    # S08 expanding L.
    d, s = Fr(1, 2), Fr(1, 2)

    def el_case(tag, setter, want):
        g = nominal_grid(Fr(0))
        setter(g)
        rc, out, err = read("S08-%s" % tag, list(g.values()), list(nominal_base().values()))
        row = read_row(out, d, s, "expanding_L")
        counts = set_counts(out, "blind")
        report("S08_%s" % tag, row is not None and (field(row, "result") == want or rc != 0), "rc=%s|row=%s|blind=%s" % (rc, "%s,C1_off=%s,A1_off=%s,eps_low=%s,eps_high=%s" % (field(row, "result"), field(row, "C1_off_e18"), field(row, "A1_off_e18"), field(row, "eps_low_e18"), field(row, "eps_high_e18")) if row else "none", counts))

    el_case("converged_MET", lambda g: None, "MET")

    def c1_apart(g):
        g[(d, s, 1200)].c1 += Fr(1, 10 ** 10)

    def a1_apart(g):
        g[(d, s, 1200)].a1 += Fr(1, 10 ** 9)

    def eps_rises(g):
        g[(d, s, 1600)].eps_tail = Fr(1, 10 ** 9)

    def v2_apart(g):
        base_v2 = forms_at(6561, d, s / 81)["V2_first"]
        g[(d, s, 1200)].v2 = base_v2 * Fr(10015, 10000)
        g[(d, s, 1600)].v2 = base_v2
        g[(d, s, 1200)].v2_err = Fr(1, 10 ** 12)

    el_case("C1_apart_MISS", c1_apart, "MISS")
    el_case("A1_apart_MISS", a1_apart, "MISS")
    # eps carries a rounding floor that grows with K, measured on seen rows by the second seat at 2d77636. The row asks the intervals to meet, so eps rising alone reads MET.
    el_case("eps_rises_with_K_MET", eps_rises, "MET")
    # V2 apart across K while C1 and A1 sit still: the row's "expanding_L_converges" with V2 not read there.
    el_case("V2_apart_only", v2_apart, "MISS")

    # S09 one K missing.
    def missing_case(tag, drop, want_rows, want_red):
        g = nominal_grid(Fr(0))
        for key in drop:
            del g[key]
        rc, out, err = read("S09-%s" % tag, list(g.values()), list(nominal_base().values()))
        d0, s0 = drop[0][0], drop[0][1]
        el = read_row(out, d0, s0, "expanding_L")
        c1 = read_row(out, d0, s0, "C1")
        report("S09_%s" % tag, (el is not None) == want_rows and (rc != 0) == want_red, "rc=%s|expanding_L_row=%s|verdict_K=%s|blind=%s|touched=%s|done=%s|stderr_tail=%s" % (rc, el is not None, field(c1, "K") if c1 else None, set_counts(out, "blind"), set_counts(out, "touched"), field(done(out), "failed"), err.strip().split("\n")[-1][:120] if err else ""))

    # The row asks expanding L on every point, so a missing K has to turn red or read MISS. want_red=True is the row's ask.
    missing_case("K1600_missing_at_blind_point", [(Fr(1, 2), Fr(1, 4), 1600)], False, True)
    missing_case("K1200_missing_at_blind_point", [(Fr(1, 2), Fr(1, 4), 1200)], False, True)
    missing_case("K1600_missing_at_touched_point", [(Fr(0), Fr(1, 4), 1600)], False, True)
    missing_case("both_K_missing_at_a_point", [(Fr(1, 2), Fr(1, 4), 1200), (Fr(1, 2), Fr(1, 4), 1600)], False, True)
    # All K = 1600 rows gone: the plan's larger K everywhere absent.
    g = nominal_grid(Fr(0))
    for p in GRID:
        del g[(p[0], p[1], 1600)]
    rc, out, err = read("S09-all-1600-missing", list(g.values()), list(nominal_base().values()))
    report("S09_all_K1600_missing", rc != 0, "rc=%s|blind=%s|touched=%s|expanding_L_rows=%d|planned_runs_printed=%s|rows_printed=%s" % (rc, set_counts(out, "blind"), set_counts(out, "touched"), len(lines_of(out, "obs=expanding_L")), field(lines_of(out, "FC_READ_START")[0], "planned_runs"), field(lines_of(out, "FC_READ_START")[0], "rows")))

    # S10 a duplicate row: two rows at the same K, one good and one bad. The later one wins.
    d, s = Fr(1, 4), Fr(1, 4)
    f = forms_at(6561, d, s / 81)
    g = nominal_grid(Fr(0))
    bad = Row(6561, 1600, d, s / 81)
    bad.c1 = f["C1_first"] * Fr(12, 10)
    rows = [bad] + list(g.values())
    rc, out, err = read("S10-duplicate-bad-first", rows, list(nominal_base().values()))
    report("S10_duplicate_row_with_a_miss_turns_red", rc != 0, "rc=%s|C1_result=%s|rows_printed=%s|planned=%s" % (rc, field(read_row(out, d, s, "C1"), "result"), field(lines_of(out, "FC_READ_START")[0], "rows"), field(lines_of(out, "FC_READ_START")[0], "planned_runs")))

    # S11 an extra row at a point outside the row: unread, no flag.
    g = nominal_grid(Fr(0))
    extra = Row(6561, 1600, Fr(3, 4), Fr(1, 324))
    rc, out, err = read("S11-extra-point", list(g.values()) + [extra], list(nominal_base().values()))
    report("S11_extra_row_off_the_plan_turns_red", rc != 0, "rc=%s|done=%s" % (rc, field(done(out), "failed")))

    # S12 the model's fields the row fixes: x, float_used, window, u.
    g = nominal_grid(Fr(0))
    for r in g.values():
        r.x = r.d + 1
    rc, out, err = read("S12-x-wrong", list(g.values()), list(nominal_base().values()))
    report("S12_x_is_not_delta_minus_1_turns_red", rc != 0, "rc=%s|blind=%s" % (rc, set_counts(out, "blind")))

    # S13 V2 against its own definition: V2 on first, C1 and A1 pushed so A1^2/(2 C1) sits outside 1/1000, each inside by itself.
    d, s = Fr(1, 4), Fr(1)
    f = forms_at(6561, d, s / 81)
    g = nominal_grid(Fr(0))
    for k in (1200, 1600):
        r = g[(d, s, k)]
        r.c1 = f["C1_first"] * (1 - Fr(9, 10000))
        r.a1 = f["A1_first"] * (1 + Fr(9, 10000))
        r.v2 = f["V2_first"]
        r.v2_err = Fr(1, 10 ** 12)
    rc, out, err = read("S13-v2-inconsistent", list(g.values()), list(nominal_base().values()))
    implied = (f["A1_first"] * (1 + Fr(9, 10000))) ** 2 / (2 * f["C1_first"] * (1 - Fr(9, 10000))) / f["V2_first"] - 1
    report("S13_V2_off_its_own_definition_turns_red", rc != 0, "rc=%s|V2_result=%s|A1_squared_over_2C1_over_first_minus_1_ppb=%d|blind=%s" % (rc, field(read_row(out, d, s, "V2"), "result"), (implied * 10 ** 9).__floor__(), set_counts(out, "blind")))

    # S14 V2's interval against the C1, A1 intervals: printed V2_lo, V2_hi narrower than the propagation of C1_err and A1_err asks.
    g = nominal_grid(Fr(0))
    for k in (1200, 1600):
        r = g[(d, s, k)]
        r.c1_err = f["C1_first"] * Fr(4, 10000)
        r.a1_err = f["A1_first"] * Fr(4, 10000)
        r.v2_err = Fr(1, 10 ** 12)
    rc, out, err = read("S14-v2-interval-narrow", list(g.values()), list(nominal_base().values()))
    report("S14_V2_interval_narrower_than_propagation_turns_red_or_MISS", rc != 0 or field(read_row(out, d, s, "V2"), "result") == "MISS", "rc=%s|V2_result=%s|V2_certified_inside=%s|propagated_relative_half_width_about_ppm=1200" % (rc, field(read_row(out, d, s, "V2"), "result"), field(read_row(out, d, s, "V2"), "certified_inside")))

    # S15 eps printed under its parts.
    g = nominal_grid(Fr(0))
    for r in g.values():
        r.eps = Fr(1, 10 ** 15)
    rc, out, err = read("S15-eps-under-parts", list(g.values()), list(nominal_base().values()))
    report("S15_eps_under_the_sum_of_its_parts_turns_red", rc != 0, "rc=%s|blind=%s" % (rc, set_counts(out, "blind")))

    # S16 the log against the certificate: leak_sum above eps_tail.
    g = nominal_grid(Fr(0))
    for r in g.values():
        r.extra = ""
    # leak_sum is 1e-18 in the row builder; here the certificate is printed under the log.
    for r in g.values():
        r.eps_tail = Fr(0)
    rc, out, err = read("S16-eps-tail-zero", list(g.values()), list(nominal_base().values()))
    report("S16_eps_tail_0_at_K_below_N_turns_red", rc != 0, "rc=%s|blind=%s|note=eps_tail_0_printed_at_K=1200,1600_N=6561" % (rc, set_counts(out, "blind")))

    # S17 a sabotage name in a grid row, and in the base file.
    g = nominal_grid(Fr(0))
    g[(Fr(1, 2), Fr(1, 4), 1600)].sabotage = "norm_drift"
    rc, out, err = read("S17-sab-grid", list(g.values()), list(nominal_base().values()))
    report("S17_sabotage_in_grid_turns_red", rc != 0 and "no_sabotage_named_in_grid" in done(out), "rc=%s|failed=%s" % (rc, field(done(out), "failed")))
    b = nominal_base()
    b[(Fr(0), Fr(1, 4))].sabotage = "norm_drift"
    rc, out, err = read("S17-sab-base", list(nominal_grid(Fr(0)).values()), list(b.values()))
    report("S17_sabotage_in_baseline_file_turns_red", rc != 0, "rc=%s|failed=%s" % (rc, field(done(out), "failed")))

    # S18 a row at the wrong t and N.
    g = nominal_grid(Fr(0))
    g[(Fr(1, 2), Fr(1, 4), 1200)].t = 3
    rc, out, err = read("S18-wrong-t", list(g.values()), list(nominal_base().values()))
    report("S18_row_at_wrong_t_turns_red", rc != 0, "rc=%s|failed=%s" % (rc, field(done(out), "failed")))

    # S19 C1 lower bound at or under zero.
    g = nominal_grid(Fr(0))
    r = g[(Fr(1, 4), Fr(1), 1600)]
    r.c1_err = r.c1 * 2
    r.v2_lo = Fr(0)
    r.v2_hi = Fr(-1, E18)
    rc, out, err = read("S19-c1-lower", list(g.values()), list(nominal_base().values()))
    report("S19_C1_lower_bound_not_positive_turns_red", rc != 0 and field(read_row(out, Fr(1, 4), Fr(1), "V2"), "result") == "MISS", "rc=%s|failed=%s|V2_result=%s" % (rc, field(done(out), "failed"), field(read_row(out, Fr(1, 4), Fr(1), "V2"), "result")))

    # S20 norm and energy past the account.
    g = nominal_grid(Fr(0))
    g[(Fr(1, 4), Fr(1), 1600)].norm_off = Fr(1, 10 ** 9)
    rc, out, err = read("S20-norm", list(g.values()), list(nominal_base().values()))
    report("S20_norm_past_the_account_turns_red", rc != 0, "rc=%s|failed=%s" % (rc, field(done(out), "failed")))
    g = nominal_grid(Fr(0))
    g[(Fr(1, 4), Fr(1), 1600)].energy = Fr(1, 10 ** 3)
    rc, out, err = read("S20-energy", list(g.values()), list(nominal_base().values()))
    report("S20_energy_past_the_account_turns_red", rc != 0, "rc=%s|failed=%s" % (rc, field(done(out), "failed")))

    # S21 the baseline file missing a remainder point.
    b = nominal_base()
    del b[(Fr(1, 2), Fr(1, 2))]
    rc, out, err = read("S21-base-missing", list(nominal_grid(Fr(0)).values()), list(b.values()))
    report("S21_baseline_row_missing_turns_red", rc != 0, "rc=%s|done_row_printed=%s|stderr_tail=%s" % (rc, bool(lines_of(out, "FC_READ_DONE")), err.strip().split("\n")[-1][:100] if err else ""))

    with open(SYN + "/SYNTH-READ-%s.hbp" % TAG, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("SYN_RUN|scope=synthetic_receipts_read_by_read_first_correction.py_grid|engine_runs=0|model_runs=0|scenarios_as_the_row_asks=%d|scenarios_otherwise=%d|json=0\n" % (COUNT["pass"], COUNT["fail"]))
        handle.write("\n".join(OUT) + "\n")
    print("SYN_DONE|as_the_row_asks=%d|otherwise=%d|json=0" % (COUNT["pass"], COUNT["fail"]))
    for line in OUT:
        if "as_the_row_asks=0" in line:
            print(line[:420])
    if COUNT["fail"]:
        sys.exit(1)


main()
