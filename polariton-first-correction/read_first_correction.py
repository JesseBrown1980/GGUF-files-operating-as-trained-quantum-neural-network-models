# The read of POLARITON_FIRST_CORRECTION, the row at line 48 of polariton/PREDICTION.hbp, against the engine's receipts.
# Integers and fractions only. The law and the first correction are evaluated from the row's own text, so nothing is typed twice.
#
# usage: read_first_correction.py baseline PREDICTION PLAN RECEIPT_BASELINE OLD_RECEIPT
#        read_first_correction.py grid PREDICTION PLAN RECEIPT_BASELINE RECEIPT_GRID
#        read_first_correction.py control OLD_RECEIPT RECEIPT_OF_A_SABOTAGED_ENGINE
#
# FC_READ rows answer the frozen prediction: MET or MISS, and a miss stays. FC_CHECK rows test the engine and the certificate: a FAIL exits 1.
import ast
import re
import sys
from fractions import Fraction as Fr

sys.dont_write_bytecode = True
E18 = 10 ** 18
LIMIT = Fr(1, 1000)
SERIES_TERMS = 120
FAILED = []


def say(text):
    sys.stdout.write(text + "|json=0\n")


def check(name, ok, detail=""):
    if not ok:
        FAILED.append(name)
    say("FC_CHECK|name=%s|result=%s%s" % (name, "PASS" if ok else "FAIL", ("|" + detail) if detail else ""))


def fields(line):
    out = {}
    for part in line.strip().split("|")[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            out[key] = value
    return out


def e18(value):
    """A fraction as an integer number of 10^-18, floored, for printing."""
    return (value * E18).__floor__()


def ppb(value):
    return (value * 10 ** 9).__floor__()


# ---- The row's own text.


class Forms:
    """The law and first-correction forms, read from the frozen row and evaluated exactly on a series of known length."""

    def __init__(self, row_line):
        assert row_line.startswith("POLARITON_FIRST_CORRECTION|"), "line 48 is the frozen row"
        self.row = row_line.strip()
        self.text = {}
        for part in self.row.split("|")[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                self.text[key] = value

    def grid(self):
        return [tuple(Fr(v) for v in pair.split(",")) for pair in re.findall(r"\(([^()]*)\)", self.text["(delta,s)"])]

    def blind(self):
        return [tuple(Fr(v) for v in pair.split(",")) for pair in re.findall(r"\(([^()]*)\)", self.text["blind_8"])]

    def touched(self):
        return [tuple(Fr(v) for v in pair.split(",")) for pair in re.findall(r"\((-?[0-9/]+,-?[0-9/]+)\)", self.text["touched_2"])]

    def evaluate(self, name, env):
        source = self.text[name]
        source = source.replace("s^2", "s2").replace("s^4", "s4").replace("^", "**")
        return walk(ast.parse(source, mode="eval").body, env)

    def values(self, n, delta, y, t):
        d = Fr(delta)
        g2 = (1 - d * d) * Fr(t) * Fr(t)  # (gamma t)^2
        env = {"N": Fr(n), "d": d, "y": Fr(y), "s2": Fr(n) * Fr(y) * Fr(y)}
        env["s4"] = env["s2"] * env["s2"]
        for k in (1, 2, 3, 4):
            env["c_%d" % k] = cosh_series(k, g2)
            env["gs_%d" % k] = gamma_sinh_series(k, g2)
        # sinh1 enters only squared, and sinh^2 = (cosh(2 gamma t) - 1)/2 keeps every value a fraction.
        sinh_sq = (env["c_2"] - 1) / 2
        for power, value in (("D3", 3), ("D4", 4), ("D5", 5)):
            env[power] = (1 + d) ** value * (1 - d) ** 2
        env["SINH_SQ"] = sinh_sq
        for name in ("w0", "C0", "w10", "w11", "C10", "C11", "C12"):
            source_env = dict(env)
            env[name] = self.evaluate_with_sinh(name, source_env)
        out = {}
        for name in ("A1_first", "C1_first", "A1_law", "C1_law"):
            out[name] = self.evaluate(name, env)
        out["V2_first"] = self.evaluate("V2_first", dict(env, A1_first=out["A1_first"], C1_first=out["C1_first"]))
        # The closed form behind the row's "predicted f": j0 + the field's pairs, in the pair count of the frozen contact gate.
        j0 = sinh_sq / (1 - d * d)
        nc = env["s2"] * ((env["c_1"] - 1) ** 2 / (1 + d) ** 2 + j0)
        out["f_predicted"] = 2 * (j0 + nc) / Fr(n)
        out["w0"] = env["w0"]
        return out

    def evaluate_with_sinh(self, name, env):
        source = self.text[name].replace("sinh1^2", "SINH_SQ")
        source = source.replace("s^2", "s2").replace("s^4", "s4").replace("^", "**")
        return walk(ast.parse(source, mode="eval").body, env)


def walk(node, env):
    if isinstance(node, ast.BinOp):
        a, b = walk(node.left, env), walk(node.right, env)
        if isinstance(node.op, ast.Add):
            return a + b
        if isinstance(node.op, ast.Sub):
            return a - b
        if isinstance(node.op, ast.Mult):
            return a * b
        if isinstance(node.op, ast.Div):
            return a / b
        if isinstance(node.op, ast.Pow):
            assert b.denominator == 1
            return a ** int(b)
        raise ValueError("operator")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -walk(node.operand, env)
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return Fr(node.value)
    if isinstance(node, ast.Name):
        return env[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "abs" and len(node.args) == 1:
        return abs(walk(node.args[0], env))
    raise ValueError("form: %r" % (node,))


def factorial_table(top):
    out = [1]
    for i in range(1, top + 1):
        out.append(out[-1] * i)
    return out


FACT = factorial_table(2 * SERIES_TERMS + 2)


def cosh_series(k, g2):
    """cosh(k gamma t), summed to a fixed length. Every term is positive. The last printed digit sits far above the tail for k gamma t <= 16."""
    x = Fr(k * k) * g2
    total, power = Fr(0), Fr(1)
    for m in range(SERIES_TERMS):
        total += power / FACT[2 * m]
        power *= x
    return total


def gamma_sinh_series(k, g2):
    """gamma t sinh(k gamma t), a series in (gamma t)^2."""
    x = Fr(k * k) * g2
    total, power = Fr(0), g2 * k
    for m in range(SERIES_TERMS):
        total += power / FACT[2 * m + 1]
        power *= x
    return total


# ---- The engine's rows.


class Row:
    def __init__(self, line):
        f = fields(line)
        self.raw = f
        self.n = int(f["N"])
        self.k = int(f["K"])
        self.delta = Fr(f["delta"])
        self.y = Fr(f["y"])
        self.t = int(f["t"])
        self.window = f["window"]
        self.c = int(f["c"])
        self.big_e = int(f["E"])
        self.dim = int(f["even_states"])
        for name in ("f", "A", "B", "C1", "C2", "A1", "D2", "V2", "energy", "norm_off", "eps_tail", "eps_poly", "eps_round", "eps", "C1_err", "A1_err", "V2_lo", "V2_hi", "jbar"):
            setattr(self, name, int(f[name + "_e18"]))
        self.sabotage = f.get("sabotage", "")

    def key(self):
        return (self.n, self.k, self.delta, self.y, self.t)

    def v2_valid(self):
        return self.V2_hi >= 0

    def c1_interval(self):
        # e18 prints round down, and the two extra units cover that.
        return Fr(self.C1 - self.C1_err - 2, E18), Fr(self.C1 + self.C1_err + 2, E18)

    def a1_interval(self):
        return Fr(self.A1 - self.A1_err - 2, E18), Fr(self.A1 + self.A1_err + 2, E18)

    def v2_interval(self):
        return Fr(self.V2_lo - 2, E18), Fr(self.V2_hi + 2, E18)

    def b_err(self):
        """The certified error of <B>: norm(B) <= (N+1)/2 and norm(B phi) <= norm(B), plus the read-out's roots within 2^-24 on two transition kinds."""
        eps = Fr(self.eps + 1, E18)
        return eps * (self.n + 1) * (1 + eps) + Fr(1, 1 << 22)

    def norm_bound(self):
        """The computed state sits within eta of the block's exact unit state, so |norm^2 - 1| <= 2 eta + eta^2. The sum's floors add under dim 2^-84."""
        eta = Fr(self.eps_poly + self.eps_round + 2, E18)
        return 2 * eta + eta * eta + Fr(self.dim, 1 << 84)

    def energy_bound(self):
        """The block keeps <C> = 0 from |N,0,0>. |<C>_computed| <= eta (2 norm(C) + norm(C) eta), norm(C) <= |c| + E, plus the read-out's rounding."""
        eta = Fr(self.eps_poly + self.eps_round + 2, E18)
        norm_c = abs(self.c) + self.big_e
        read = Fr(1, 1 << 23) * (Fr(1, self.n) + 2 * abs(self.y)) + Fr(self.dim * self.n * self.n, 1 << 70) * (Fr(1, self.n) + abs(self.y))
        return eta * (2 * norm_c + norm_c * eta) + read


def load_rows(path):
    rows = []
    for line in open(path, encoding="utf-8", newline=""):
        if line.startswith("POLARITON_FIRST_CORRECTION_READ|"):
            rows.append(Row(line))
    return rows


def old_receipt_rows(path):
    out = {}
    for line in open(path, encoding="utf-8", newline=""):
        if line.startswith("POLARITON_QUENCH_CONVERSION|"):
            f = fields(line)
            out[(int(f["N"]), Fr(f["delta"]), Fr(f["y"]), int(f["t"]))] = f
    return out


def plan_runs(path, stage):
    out = []
    for line in open(path, encoding="utf-8", newline=""):
        if line.startswith("FC_RUN|"):
            f = fields(line)
            if f["stage"] == stage:
                out.append(f)
    return out


# ---- The checks every row owes.


def internal_checks(rows, label):
    """Norm and energy against the rounding accounting: each row, one name per set, and the worst margin printed."""
    bad_norm, bad_energy, nmax, emax = [], [], Fr(0), Fr(0)
    for r in rows:
        norm = Fr(abs(r.norm_off) + 2, E18)
        energy = Fr(abs(r.energy) + 2, E18)
        if norm > r.norm_bound():
            bad_norm.append(r)
        if energy > r.energy_bound():
            bad_energy.append(r)
        nmax = max(nmax, norm / r.norm_bound())
        emax = max(emax, energy / r.energy_bound())
    check("norm_inside_the_rounding_account_%s" % label, not bad_norm, "rows=%d|worst_read_over_bound_ppm=%d" % (len(rows), (nmax * 10 ** 6).__floor__()))
    check("energy_inside_the_rounding_account_%s" % label, not bad_energy, "rows=%d|worst_read_over_bound_ppm=%d" % (len(rows), (emax * 10 ** 6).__floor__()))
    check("no_sabotage_named_in_%s" % label, all(not r.sabotage for r in rows) or label.startswith("control"))


def against_old_receipt(rows, old, label, relative=Fr(1, 100000)):
    """Each row that has a partner in the full-space engine's receipt: C1, <A>, <B>, f, C2, jbar within 10^-5 relative, with the receipt's ppb rounding beside it."""
    read = bad = 0
    worst = Fr(0)
    worst_frozen = Fr(0)
    for r in rows:
        partner = old.get((r.n, r.delta, r.y, r.t))
        # A small block at N = 729 answers to the full space in the sweep's own check, against its certificate.
        if partner is None or (r.n == 729 and r.k < r.n):
            continue
        for name, mine in (("C1", r.C1), ("A", r.A), ("B", r.B), ("f", r.f), ("C2", r.C2), ("jbar", r.jbar)):
            theirs = int(partner[name + "_ppb"])
            off = abs(Fr(mine, E18) - Fr(theirs, 10 ** 9))
            tolerance = relative * abs(Fr(theirs, 10 ** 9)) + Fr(2, 10 ** 9) + Fr(2 * (r.eps + 1), E18) * r.n
            read += 1
            if theirs:
                worst = max(worst, off / abs(Fr(theirs, 10 ** 9)))
            if off > tolerance:
                bad += 1
                say("FC_RECEIPT_OFF|N=%d|K=%d|delta=%s|y=%s|t=%d|name=%s|mine_e18=%d|receipt_ppb=%d" % (r.n, r.k, r.delta, r.y, r.t, name, mine, theirs))
        # The row's own three observables, at the row's t. V^2 from the receipt is A1^2/(2 C1), with A1 = 2|A|/N.
        if r.t == 2 and r.k == r.n:
            their_c1 = Fr(int(partner["C1_ppb"]), 10 ** 9)
            their_a1 = 2 * abs(Fr(int(partner["A_ppb"]), 10 ** 9)) / r.n
            their_v2 = their_a1 * their_a1 / (2 * their_c1)
            worst_frozen = max(worst_frozen, abs(Fr(r.C1, E18) / their_c1 - 1), abs(Fr(r.A1, E18) / their_a1 - 1), abs(Fr(r.V2, E18) / their_v2 - 1))
    check("agrees_with_the_full_space_receipt_%s" % label, read > 0 and bad == 0 and worst_frozen <= relative, "values=%d|off=%d|worst_C1_A1_V2_at_t=2_relative_ppb=%d|limit_relative_ppb=10000|worst_over_every_value_read_ppb=%d" % (read, bad, ppb(worst_frozen), ppb(worst)))


def sweep_checks(rows):
    """The certificate against the truth: at N = 729 the full space is in reach, so each smaller block's interval has to hold the full value."""
    by_point = {}
    for r in rows:
        by_point.setdefault((r.n, r.delta, r.y, r.t), {})[r.k] = r
    held = total = 0
    for (n, delta, y, t), ks in sorted(by_point.items(), key=lambda item: (item[0][0], item[0][1], item[0][2], item[0][3])):
        if n not in ks or len(ks) < 2:
            continue
        full = ks[n]
        check("full_space_has_no_leak_N=%d_delta=%s_y=%s_t=%d" % (n, delta, y, t), full.eps_tail == 0)
        for k in sorted(ks):
            if k == n:
                continue
            r = ks[k]
            rows_ok = True
            detail = []
            for name, interval, mid_full, full_err in (
                ("C1", r.c1_interval(), Fr(full.C1, E18), Fr(full.C1_err + 2, E18)),
                ("A1", r.a1_interval(), Fr(full.A1, E18), Fr(full.A1_err + 2, E18)),
            ):
                inside = interval[0] - full_err <= mid_full <= interval[1] + full_err
                rows_ok = rows_ok and inside
                value = Fr(getattr(r, name), E18)
                off = abs(value - mid_full)
                bound = (interval[1] - interval[0]) / 2 + full_err
                detail.append("%s_true_off_e18=%d|%s_bound_e18=%d" % (name, e18(off), name, e18(bound)))
            if r.v2_valid():
                low, high = r.v2_interval()
                inside = low <= Fr(full.V2_hi, E18) and Fr(full.V2_lo, E18) <= high
                rows_ok = rows_ok and inside
                detail.append("V2_interval_e18=[%d,%d]|V2_full_e18=[%d,%d]" % (r.V2_lo, r.V2_hi, full.V2_lo, full.V2_hi))
            else:
                detail.append("V2_interval=C1_lower_bound_not_positive")
            total += 1
            held += rows_ok
            say("FC_BLOCK_VS_FULL|N=%d|K=%d|even_states=%d|delta=%s|y=%s|t=%d|eps_tail_e18=%d|eps_poly_e18=%d|eps_round_e18=%d|%s|holds=%d" % (n, k, r.dim, delta, y, t, r.eps_tail, r.eps_poly, r.eps_round, "|".join(detail), rows_ok))
    check("every_certificate_holds_the_full_value", total > 0 and held == total, "rows=%d|held=%d" % (total, held))


def anchor_checks(rows):
    """GPT-6's checklist item 5, on the seen row at N = 6561: K = 512 fails to certify, K = 1000 and K = 1200 certify V^2 inside 1/1000."""
    seen = {r.k: r for r in rows if r.n == 6561 and r.delta == 0 and r.y == Fr(1, 81) and r.t == 2}

    def inside(r):
        if not r.v2_valid():
            return False
        mid = Fr(r.V2, E18)
        return (r.v2_interval()[1] - r.v2_interval()[0]) / 2 < LIMIT * mid

    check("anchor_K=512_does_not_certify", 512 in seen and not inside(seen[512]), "C1_err_e18=%d|C1_e18=%d" % (seen[512].C1_err, seen[512].C1) if 512 in seen else "")
    check("anchor_K=800_does_not_certify", 800 in seen and not inside(seen[800]))
    check("anchor_K=1000_certifies", 1000 in seen and inside(seen[1000]))
    check("anchor_K=1200_certifies", 1200 in seen and inside(seen[1200]))
    if 1200 in seen:
        for k in sorted(seen):
            r = seen[k]
            top = seen[1200]
            ok = abs(r.C1 - top.C1) <= r.C1_err + top.C1_err + 4 and abs(r.A1 - top.A1) <= r.A1_err + top.A1_err + 4
            check("anchor_K=%d_interval_holds_K=1200" % k, ok, "C1_off_e18=%d|C1_err_e18=%d|A1_off_e18=%d|A1_err_e18=%d" % (abs(r.C1 - top.C1), r.C1_err, abs(r.A1 - top.A1), r.A1_err))


def baseline(prediction, plan, receipt, old_path):
    rows = load_rows(receipt)
    runs = plan_runs(plan, "baseline")
    say("FC_READ_START|stage=baseline|seen_rows_only=1|rows=%d|planned_runs=%d" % (len(rows), len(runs)))
    forms = Forms(open(prediction, encoding="utf-8", newline="").read().split("\n")[47])
    # No baseline run sits on a blind point.
    blind = set(forms.blind())
    on_blind = 0
    for run in runs:
        y = Fr(run["y"])
        n = int(run["N"])
        if n == 6561 and (Fr(run["delta"]), y * 81) in blind:
            on_blind += 1
    check("no_baseline_run_on_a_blind_point", on_blind == 0)
    internal_checks(rows, "baseline")
    against_old_receipt(rows, old_receipt_rows(old_path), "baseline")
    sweep_checks([r for r in rows if r.n == 729])
    anchor_checks(rows)
    # The observables at each seen point against law plus first, as a preview of the reader on seen data, kept apart from the frozen read.
    for r in rows:
        if r.k == r.n or (r.n == 6561 and r.k == 1200) or (r.n == 2187):
            if r.t != 2:
                continue
            v = forms.values(r.n, r.delta, r.y, r.t)
            say("FC_SEEN|N=%d|K=%d|delta=%s|y=%s|t=%d|C1_read_over_first_minus_1_ppb=%d|A1_read_over_first_minus_1_ppb=%d|V2_read_over_first_minus_1_ppb=%d|C1_read_over_law_minus_1_ppb=%d|f_predicted_ppb=%d" % (r.n, r.k, r.delta, r.y, r.t, ppb(Fr(r.C1, E18) / v["C1_first"] - 1), ppb(Fr(r.A1, E18) / v["A1_first"] - 1), ppb(Fr(r.V2, E18) / v["V2_first"] - 1), ppb(Fr(r.C1, E18) / v["C1_law"] - 1), ppb(v["f_predicted"])))
    finish("baseline")


# ---- The frozen read.


def read_one(obs, interval, value, first, set_name, r):
    """One observable at one point: MET when the read is within 1/1000 of law plus first. The whole certified interval inside is reported beside it."""
    off = value / first - 1
    margin = LIMIT - abs(off)
    half = (interval[1] - interval[0]) / 2
    certified = interval[0] / first - 1 >= -LIMIT and interval[1] / first - 1 <= LIMIT
    say("FC_READ|set=%s|delta=%s|s=%s|N=%d|K=%d|obs=%s|read_e18=%d|first_e18=%d|abs_off_e18=%d|off_over_first_ppb=%d|limit_ppb=1000000|numerical_half_width_e18=%d|numerical_over_margin_ppm=%d|certified_inside=%d|result=%s" % (
        set_name, r.delta, r.y * 81, r.n, r.k, obs, e18(value), e18(first), e18(abs(value - first)), ppb(off), e18(half), (half / margin * 10 ** 6).__floor__() if margin > 0 else -1, certified, "MET" if abs(off) <= LIMIT and certified else "MISS"))
    return abs(off) <= LIMIT and certified


def grid(prediction, plan, receipt_baseline, receipt_grid):
    forms = Forms(open(prediction, encoding="utf-8", newline="").read().split("\n")[47])
    rows = load_rows(receipt_grid)
    base = load_rows(receipt_baseline)
    points = forms.grid()
    blind, touched = forms.blind(), forms.touched()
    check("the_row_names_10_points_8_blind_2_touched", len(points) == 10 and len(blind) == 8 and len(touched) == 2 and sorted(blind + touched) == sorted(points))
    runs = plan_runs(plan, "grid")
    planned = {(Fr(run["delta"]), Fr(run["y"]) * 81) for run in runs}
    check("the_plan_runs_the_row's_points", planned == set(points) and all(int(run["N"]) == 6561 for run in runs))
    say("FC_READ_START|stage=grid|rows=%d|planned_runs=%d" % (len(rows), len(runs)))
    internal_checks(rows, "grid")
    by_point = {}
    for r in rows:
        check("row_is_the_row's_t_and_N_%d_%s_%s" % (r.k, r.delta, r.y), r.n == 6561 and r.t == 2)
        by_point.setdefault((r.delta, r.y * 81), {})[r.k] = r
    tally = {"blind": [0, 0], "touched": [0, 0]}
    nondiscriminating = []
    for point in points:
        set_name = "blind" if point in blind else "touched"
        ks = by_point[point]
        top = max(ks)
        r = ks[top]
        delta, s = point
        v = forms.values(6561, delta, s / 81, 2)
        good = True
        c_int, a_int, v_int = r.c1_interval(), r.a1_interval(), r.v2_interval()
        check("C1_lower_bound_positive_%s_%s" % (delta, s), r.v2_valid() and c_int[0] > 0)
        good = read_one("C1", c_int, Fr(r.C1, E18), v["C1_first"], set_name, r) and good
        good = read_one("A1", a_int, Fr(r.A1, E18), v["A1_first"], set_name, r) and good
        good = read_one("V2", v_int, Fr(r.V2, E18), v["V2_first"], set_name, r) and good
        # The control: the law alone.
        for obs, value, law in (("C1", Fr(r.C1, E18), v["C1_law"]), ("A1", Fr(r.A1, E18), v["A1_law"])):
            off = value / law - 1
            state = "DISCRIMINATES" if abs(off) > LIMIT else "NONDISCRIMINATING"
            if state == "NONDISCRIMINATING":
                nondiscriminating.append((delta, s, obs))
            say("FC_CONTROL|set=%s|delta=%s|s=%s|obs=%s|read_e18=%d|law_e18=%d|off_over_law_ppb=%d|limit_ppb=1000000|state=%s" % (set_name, delta, s, obs, e18(value), e18(law), ppb(off), state))
        # Predicted f, and the signs with their certified errors.
        f_ok = v["f_predicted"] <= Fr(1, 50)
        say("FC_READ|set=%s|delta=%s|s=%s|obs=f|predicted_f_ppb=%d|read_f_e18=%d|limit=1/50|result=%s" % (set_name, delta, s, ppb(v["f_predicted"]), r.f, "MET" if f_ok else "MISS"))
        good = f_ok and good
        a_err = Fr(r.A1_err + 2, E18) * 6561
        b_err = r.b_err()
        a_ok = Fr(r.A, E18) + a_err < 0
        b_ok = Fr(r.B, E18) - b_err > 0
        say("FC_READ|set=%s|delta=%s|s=%s|obs=signs|A_e18=%d|A_err_e18=%d|B_e18=%d|B_err_e18=%d|result=%s" % (set_name, delta, s, r.A, e18(a_err), r.B, e18(b_err), "MET" if a_ok and b_ok else "MISS"))
        good = a_ok and b_ok and good
        # The certificate, printed on every point.
        say("FC_CERT|set=%s|delta=%s|s=%s|N=6561|K=%d|even_states=%d|eps_tail_e18=%d|eps_poly_e18=%d|eps_round_e18=%d|eps_e18=%d|C1_err_e18=%d|A1_err_e18=%d|V2_e18=[%d,%d]" % (set_name, delta, s, top, r.dim, r.eps_tail, r.eps_poly, r.eps_round, r.eps, r.C1_err, r.A1_err, r.V2_lo, r.V2_hi))
        # Expanding L.
        for k in sorted(ks):
            if k == top:
                continue
            low = ks[k]
            c_off = abs(low.C1 - r.C1)
            a_off = abs(low.A1 - r.A1)
            ok = c_off <= low.C1_err + r.C1_err + 4 and a_off <= low.A1_err + r.A1_err + 4 and low.eps >= r.eps
            say("FC_READ|set=%s|delta=%s|s=%s|obs=expanding_L|K_low=%d|K_high=%d|C1_off_e18=%d|C1_err_low_e18=%d|A1_off_e18=%d|A1_err_low_e18=%d|eps_low_e18=%d|eps_high_e18=%d|result=%s" % (set_name, delta, s, k, top, c_off, low.C1_err, a_off, low.A1_err, low.eps, r.eps, "MET" if ok else "MISS"))
            good = ok and good
            lv = forms.values(6561, delta, s / 81, 2)
            say("FC_AT_LOWER_K|set=%s|delta=%s|s=%s|K=%d|C1_certified_inside=%d|A1_certified_inside=%d|V2_certified_inside=%d" % (
                set_name, delta, s, k,
                low.c1_interval()[0] / lv["C1_first"] - 1 >= -LIMIT and low.c1_interval()[1] / lv["C1_first"] - 1 <= LIMIT,
                low.a1_interval()[0] / lv["A1_first"] - 1 >= -LIMIT and low.a1_interval()[1] / lv["A1_first"] - 1 <= LIMIT,
                low.v2_valid() and low.v2_interval()[0] / lv["V2_first"] - 1 >= -LIMIT and low.v2_interval()[1] / lv["V2_first"] - 1 <= LIMIT,
            ))
        tally[set_name][0 if good else 1] += 1
    say("FC_READ_SET|set=blind|points=%d|all_rows_met=%d|with_a_miss=%d" % (len(blind), tally["blind"][0], tally["blind"][1]))
    say("FC_READ_SET|set=touched|points=%d|all_rows_met=%d|with_a_miss=%d" % (len(touched), tally["touched"][0], tally["touched"][1]))
    say("FC_CONTROL_SET|nondiscriminating=%s" % (",".join("%s:%s:%s" % n for n in nondiscriminating) or "none"))
    # The remainder, N = 729 to N = 6561, at equal s, delta, t.
    full = {(r.delta, r.y * 27): r for r in base if r.n == 729 and r.k == 729 and r.t == 2}
    for delta, s in ((Fr(0), Fr(1, 4)), (Fr(0), Fr(1, 2)), (Fr(1, 2), Fr(1, 4)), (Fr(1, 2), Fr(1, 2))):
        low_n = full[(delta, s)]
        ks = by_point[(delta, s)]
        high_n = ks[max(ks)]
        first_729 = forms.values(729, delta, s / 27, 2)["C1_first"]
        first_6561 = forms.values(6561, delta, s / 81, 2)["C1_first"]
        r729 = abs(Fr(low_n.C1, E18) / first_729 - 1)
        r6561 = abs(Fr(high_n.C1, E18) / first_6561 - 1)
        e729 = Fr(low_n.C1_err + 2, E18) / first_729
        e6561 = Fr(high_n.C1_err + 2, E18) / first_6561
        gap = r729 - 30 * r6561
        rigorous = r729 - e729 >= 30 * (r6561 + e6561)
        below = e729 < r6561 and e6561 < r6561 and e729 < gap and e6561 < gap
        met = rigorous and below
        ratio_lo = (r729 - e729) / (r6561 + e6561) if r6561 + e6561 > 0 else Fr(0)
        say("FC_READ|set=remainder|delta=%s|s=%s|obs=C1_remainder|R729_ppb=%d|R6561_ppb=%d|e729_ppb=%d|e6561_ppb=%d|gap_to_30x_ppb=%d|ratio_times_1000_lo=%d|limit_times_1000=30000|error_below_residual_and_gap=%d|result=%s" % (delta, s, ppb(r729), ppb(r6561), ppb(e729), ppb(e6561), ppb(gap), (ratio_lo * 1000).__floor__(), below, "MET" if met else "MISS"))
    finish("grid")


def control(old_path, receipt):
    """One sabotaged engine's rows, read by the same checks. A real engine passes these. Each sabotage has to fail a named one."""
    rows = load_rows(receipt)
    say("FC_READ_START|stage=control|rows=%d|sabotage=%s" % (len(rows), rows[0].sabotage if rows else "none"))
    internal_checks(rows, "control")
    against_old_receipt(rows, old_receipt_rows(old_path), "control")
    sweep_checks([r for r in rows if r.n == 729])
    finish("control")


def finish(stage):
    say("FC_READ_DONE|stage=%s|checks_failed=%d|failed=%s" % (stage, len(FAILED), ",".join(FAILED) or "none"))
    if FAILED:
        sys.exit(1)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "baseline":
        baseline(*sys.argv[2:6])
    elif mode == "grid":
        grid(*sys.argv[2:6])
    elif mode == "control":
        control(*sys.argv[2:4])
    else:
        sys.stderr.write("usage: read_first_correction.py baseline|grid|control ...\n")
        sys.exit(2)


main()
