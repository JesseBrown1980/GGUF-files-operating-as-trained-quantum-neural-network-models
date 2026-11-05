#!/bin/bash
# The held route on the P2 mutants' own rows at N = 3, and on C05's taylor rows. Each prints its DONE row.
export PYTHONDONTWRITEBYTECODE=1
export MSYS_NO_PATHCONV=1
W=C:/tmp/opus55/polariton-recheck-engine-20261105
O=$W/out/hold_route
mkdir -p "$O"
for m in m_w07_p2_sum_not_difference m_w08_p2_constant m_w09_p2_abs_times_n; do
  "$W/target/release/$m.exe" window 2>/dev/null | grep '^POLARITON_PIN_WINDOW|N=3|' > "$O/$m.rows"
  echo "HELD_ROUTE|mutant=$m|rows=$(wc -l < "$O/$m.rows")|$(python3 -I -X utf8 "$W/holdcopy/polariton/second_route.py" full_compare "$O/$m.rows" 3 | tr -d '\r' | tail -1)"
  echo "FILED_ROUTE|mutant=$m|$(python3 -I -X utf8 "$W/clean/polariton/second_route.py" full_compare "$O/$m.rows" 3 | tr -d '\r' | tail -1)"
done
for m in m_c05_f_not_per_n; do
  "$W/target/release/$m.exe" taylor 2>/dev/null | grep '^POLARITON_TAYLOR_CONVERT|' > "$O/$m.rows"
  echo "HELD_ROUTE|mutant=$m|rows=$(wc -l < "$O/$m.rows")|$(python3 -I -X utf8 "$W/holdcopy/polariton/second_route.py" convert_compare "$O/$m.rows" | tr -d '\r' | tail -1)"
  echo "FILED_ROUTE|mutant=$m|$(python3 -I -X utf8 "$W/clean/polariton/second_route.py" convert_compare "$O/$m.rows" | tr -d '\r' | tail -1)"
done
echo HOLD_ROUTE_DONE
