# Reads the sector mode's rows against the point mode's rows at the same points and names each check that fails.
# The sector mode (src/bin/polariton_first_correction.rs, `sector`) keeps the Q = 0 sector at y = 0 and prints every
# field `point` prints, but array_bytes, which counts its own layout: (min(K, N)/2 + 1) * 104.
# A sabotaged row carries sabotage=NAME; the checks read past that tag, so a sabotage is caught by its numbers alone.
#
# usage: check_sector.py STAGE POINT_ROWS SECTOR_ROWS
# Prints one FC_SECTOR_CHECK row per check and an FC_SECTOR_DONE row; exit 0 when every check passes, 1 otherwise.
import sys

sys.dont_write_bytecode = True

TAG = "POLARITON_FIRST_CORRECTION_READ|"
SECTOR_BYTES_PER_STATE = 104
POINT_BYTES_PER_STATE = 120
IDENTITY = ["N", "K", "delta", "y", "t"]
GROUPS = [
    ("operator_fields_equal", ["even_states", "u", "x", "window", "c", "E", "degree", "reach", "applies", "elem_err_units"]),
    (
        "observable_fields_equal",
        ["jbar_e18", "f_e18", "A_e18", "B_e18", "C1_e18", "C2_e18", "A1_e18", "D2_e18", "V2_e18", "energy_e18", "norm_off_e18"],
    ),
    (
        "certificate_fields_equal",
        [
            "eps_tail_e18",
            "eps_poly_e18",
            "eps_round_e18",
            "eps_e18",
            "C1_err_e18",
            "A1_err_e18",
            "V2_lo_e18",
            "V2_hi_e18",
            "norm_B_s20",
            "tail_max_e18",
            "leak_max_e18",
            "leak_sum_e18",
        ],
    ),
]
OTHER = ["array_bytes", "float_used", "json"]


def rows(path):
    out = []
    for line in open(path, encoding="utf-8", newline=""):
        if not line.startswith(TAG):
            continue
        text = line.rstrip("\n")
        parts = text.split("|")[1:]
        sabotage = ""
        if parts and parts[0].startswith("sabotage="):
            sabotage = parts[0].split("=", 1)[1]
            parts = parts[1:]
        keys = [p.split("=", 1)[0] for p in parts]
        values = dict(p.split("=", 1) for p in parts)
        bare = TAG + "|".join("array_bytes=X" if p.startswith("array_bytes=") else p for p in parts)
        out.append({"keys": keys, "v": values, "bare": bare, "sabotage": sabotage})
    return out


def main():
    stage, point_path, sector_path = sys.argv[1:4]
    pr, sr = rows(point_path), rows(sector_path)
    results = []

    def record(name, bad, n, first):
        results.append((name, bad))
        print(
            "FC_SECTOR_CHECK|stage=%s|check=%s|result=%s|rows=%d|differing_rows=%d|first=%s|json=0"
            % (stage, name, "FAIL" if bad else "PASS", n, bad, first or "none")
        )

    # The point rows carry exactly the fields this reader groups, in one order.
    known = IDENTITY + [k for _, ks in GROUPS for k in ks] + OTHER
    layout_bad = sum(1 for r in pr if sorted(r["keys"]) != sorted(known) or r["sabotage"])
    record("point_rows_carry_the_known_fields", layout_bad, len(pr), None)

    n = min(len(pr), len(sr))
    same_bad = abs(len(pr) - len(sr)) + (1 if n == 0 else 0)
    first = None
    for p, s in zip(pr, sr):
        if [p["v"].get(k) for k in IDENTITY] != [s["v"].get(k) for k in IDENTITY]:
            same_bad += 1
            first = first or "t=%s" % p["v"].get("t")
    record("same_rows", same_bad, n, first)

    for name, keys in GROUPS:
        bad, first = 0, None
        for p, s in zip(pr, sr):
            diff = [k for k in keys if p["v"].get(k) != s["v"].get(k)]
            if diff:
                bad += 1
                first = first or "%s@t=%s" % (diff[0], p["v"].get("t"))
        record(name, bad, n, first)

    bad, first = 0, None
    for p, s in zip(pr, sr):
        k_eff = min(int(s["v"]["K"]), int(s["v"]["N"]))
        want_s = (k_eff // 2 + 1) * SECTOR_BYTES_PER_STATE
        want_p = int(p["v"]["even_states"]) * POINT_BYTES_PER_STATE
        if int(s["v"]["array_bytes"]) != want_s or int(p["v"]["array_bytes"]) != want_p:
            bad += 1
            first = first or "array_bytes@t=%s" % p["v"].get("t")
    record("array_bytes_sector_layout", bad, n, first)

    bad = sum(1 for p, s in zip(pr, sr) if p["v"].get("float_used") != "0" or s["v"].get("float_used") != "0")
    record("float_used_0", bad, n, None)

    bad, first = 0, None
    for p, s in zip(pr, sr):
        if p["bare"] != s["bare"]:
            bad += 1
            first = first or "t=%s" % p["v"].get("t")
    record("every_field_but_array_bytes_byte_equal", bad, n, first)

    failed = [name for name, b in results if b]
    print("FC_SECTOR_DONE|stage=%s|checks_failed=%d|failed=%s|json=0" % (stage, len(failed), ",".join(failed) if failed else "none"))
    sys.exit(1 if failed else 0)


main()
