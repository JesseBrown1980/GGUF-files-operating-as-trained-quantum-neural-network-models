#!/bin/bash
# The workflow's pin steps, run on a copy of the tracked files with one edit at a time, so that what each edit trips is a read and not a guess.
# Commands copied from .github/workflows/polariton.yml at this head.
W=C:/tmp/opus55/polariton-recheck-engine-20261105
T=$W/out/pin_test
pins() {
  ( cd "$1" || exit 9
    test "$(head -n 29 polariton/PREDICTION.hbp | sha256sum | cut -d' ' -f1)" = "91d6a6e706c606be959cd8deb590f973a315fc923cf7589095aff8e489371f4e" || { echo "FAILS_AT=first_29_rows"; exit 1; }
    test "$(sha256sum polariton/RECEIPT.hbp | cut -d' ' -f1)" = "347480a5b9467017d07b9a52334edb1536c5b4e72df58c3a4afd85e2be0b9681" || { echo "FAILS_AT=receipt_hash"; exit 1; }
    grep -q "receipt_sha256=347480a5b9467017d07b9a52334edb1536c5b4e72df58c3a4afd85e2be0b9681" polariton/PREDICTION.hbp || { echo "FAILS_AT=attempt_row"; exit 1; }
    test "$(sha256sum polariton/read_prediction.py | cut -d' ' -f1)" = "b1e14433d722b950cc45c970a8f0d75a163f1578bce31e3c73eb716c2c99329f" || { echo "FAILS_AT=reader_pin"; exit 1; }
    test "$(sha256sum polariton/READ.hbp | cut -d' ' -f1)" = "f0f10236e6e50064c0e5790fb62160e69b1ae4c288e7c59e69cf84b4b57b1bb7" || { echo "FAILS_AT=read_pin"; exit 1; }
    test "$(sha256sum polariton/second_route.py | cut -d' ' -f1)" = "41638616460448a18304edbf90a406e59ab413f780ab4e122b579d7474e2a5d0" || { echo "FAILS_AT=route_pin"; exit 1; }
    test "$(sha256sum polariton/SECOND-ROUTE.hbp | cut -d' ' -f1)" = "bc8109c5e8994de9365496419d98990a43c6b65340258e9dd37bb0eb5d2ac916" || { echo "FAILS_AT=route_rows_pin"; exit 1; }
    echo "ALL_PINS_PASS"
  )
}
fresh() {
  rm -rf "$T"
  mkdir -p "$T"
  git -C C:/tmp/qnn-polariton-wt archive ce44be742d9d59d07bb8ec8a9ed6a559da4ec0bd polariton Cargo.toml Cargo.lock .gitattributes .github | tar -x -C "$T"
}
fresh
echo "EDIT|none|$(pins "$T")"
# A frozen tolerance in an added row, row 39: 5 percent to 50 percent on V2.
sed -i '39s/V2_5_percent/V2_50_percent/' "$T/polariton/PREDICTION.hbp"
echo "EDIT|prediction_row_39_tolerance|rows_changed=$(git -C C:/tmp/qnn-polariton-wt show ce44be742d9d59d07bb8ec8a9ed6a559da4ec0bd:polariton/PREDICTION.hbp | cmp - "$T/polariton/PREDICTION.hbp" >/dev/null 2>&1; echo $?)|$(pins "$T")"
fresh
sed -i '37s/D2_20_percent/D2_40_percent/' "$T/polariton/PREDICTION.hbp"
echo "EDIT|prediction_row_37_tolerance|$(pins "$T")"
fresh
sed -i '10s/f_1_percent/f_9_percent/' "$T/polariton/PREDICTION.hbp"
echo "EDIT|prediction_row_10_frozen|$(pins "$T")"
fresh
sed -i 's/F(5, 100)/F(9, 100)/' "$T/polariton/read_prediction.py"
echo "EDIT|reader_tolerance|$(pins "$T")"
fresh
sed -i 's/overflow-checks = true/overflow-checks = false/' "$T/Cargo.toml"
echo "EDIT|cargo_overflow_checks_off|$(pins "$T")|hash_of_Cargo_toml_read_by_workflow=$(grep -c 'sha256sum Cargo.toml' "$T/.github/workflows/polariton.yml")"
fresh
printf 'data/google-qsim/* text eol=lf\n' > "$T/.gitattributes"
echo "EDIT|gitattributes_polariton_line_removed|$(pins "$T")|hash_of_gitattributes_read_by_workflow=$(grep -c 'sha256sum .gitattributes' "$T/.github/workflows/polariton.yml")"
rm -rf "$T"
echo "SHA_ROWS_36_41_AT_89A026A|$(git -C C:/tmp/qnn-polariton-wt show 89a026a:polariton/PREDICTION.hbp | sed -n 36,41p | sha256sum | cut -d' ' -f1)"
echo "SHA_ROWS_36_41_AT_HEAD|$(git -C C:/tmp/qnn-polariton-wt show ce44be742d9d59d07bb8ec8a9ed6a559da4ec0bd:polariton/PREDICTION.hbp | sed -n 36,41p | sha256sum | cut -d' ' -f1)"
echo "SHA_CARGO_TOML|$(git -C C:/tmp/qnn-polariton-wt show ce44be742d9d59d07bb8ec8a9ed6a559da4ec0bd:Cargo.toml | sha256sum | cut -d' ' -f1)"
echo "SHA_GITATTRIBUTES|$(git -C C:/tmp/qnn-polariton-wt show ce44be742d9d59d07bb8ec8a9ed6a559da4ec0bd:.gitattributes | sha256sum | cut -d' ' -f1)"
