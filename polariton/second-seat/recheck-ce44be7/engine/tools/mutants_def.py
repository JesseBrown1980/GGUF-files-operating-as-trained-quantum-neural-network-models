# id, group, list of (old,new) applied to the lite copy of the engine at ce44be7.
# The 59 of the 8dfa11a lane, adapted where the code moved, then the new paths.
# Groups name the stages rerun, see GROUPS in mutate_run.py.
PAIR_ROUND = "round_div(rescale(root, from, bits), big) as i64"
DIR = "d += round_div((u.n * (n0 * sum + plus * minus)) << SCALE, u.d * big * big);"
O2 = "let mut rem = ((plus + 1) * (minus + 1) * n0 * (n0 - 1)) as u128;"
LIMBS = "            for _ in 0..5 {\n                rem <<= 18;\n                quo = (quo << 18) + rem / den;\n                rem %= den;\n            }\n            quo as i128"
HEAD = "    let half = SCALE + 1;\n    op.apply_into(u, work, half);\n    for (slot, k) in v.iter_mut().zip(work.iter()) {\n        *slot -= *k;\n    }\n    for step in 0..steps {"
TAIL = "    op.apply_into(u, work, half);\n    for (slot, k) in v.iter_mut().zip(work.iter()) {\n        *slot += *k;\n    }\n}"
Q_C1 = "let c1 = 2 * wk / (big * (big - 1));\n        let c2 = 2 * r.np_nm / (big * (big - 1));\n        let predicted_c1"
CONV_C1 = "let wk = r.n0_pairs + 2 * r.re_p;\n        let c1 = 2 * wk / (big * (big - 1));\n        let c2 = 2 * r.np_nm / (big * (big - 1));\n        let energy = (r.pairs * par.x.n) / par.x.d"
CONV_ROW = "            ppb(r.pairs / 2),\n            ppb(r.pairs / big),\n            ppb(r.a),\n            ppb(r.b),\n            ppb(c1),\n            ppb(c2),\n            ppb(energy),\n            ppb(r.norm - (1i128 << SCALE))\n        ));\n    }\n    rows\n}"
LIST = "let list = [(16, 1), (8, 1), (4, 1), (2, 1), (1, 1), (1, 2), (0, 1)];"
IS_WINDOW = "make as usize == window_row as usize"
YLINE = "let y = Q { n: sn, d: sd * big };"

M = [
    # ---- sector and rotor
    ("S01_o2_no_bose", "S", [(O2, "let mut rem = (n0 * (n0 - 1)) as u128;")]),
    ("S02_o2_n0n0", "S", [(O2, "let mut rem = ((plus + 1) * (minus + 1) * n0 * n0) as u128;")]),
    ("S03_o2_minus_off_by_one", "S", [(O2, "let mut rem = ((plus + 1) * (minus + 2) * n0 * (n0 - 1)) as u128;")]),
    ("S04_d_drop_npnm", "S", [(DIR, "d += round_div((u.n * (n0 * sum)) << SCALE, u.d * big * big);")]),
    ("S05_d_double_npnm", "S", [(DIR, "d += round_div((u.n * (n0 * sum + 2 * plus * minus)) << SCALE, u.d * big * big);")]),
    ("S06_d_n0minus1", "S", [(DIR, "d += round_div((u.n * ((n0 - 1) * sum + plus * minus)) << SCALE, u.d * big * big);")]),
    ("S07_d_x_sum_plus1", "S", [("let mut d = round_div((x.n * sum) << SCALE, x.d * big);", "let mut d = round_div((x.n * (sum + 1)) << SCALE, x.d * big);")]),
    ("S08_zero_pivot_uncounted", "SL", [("let mut count = usize::from(q < 0);", "let mut count = usize::from(d[0] - lambda < 0);")]),
    ("S09_roots_16_bits_each", "F", [("let bits = (126 - (128 - m.leading_zeros())) / 2;", "let bits = 16u32;")]),
    ("S11_fd_f_double", "S", [("let f = i128::from(up - down) << (m - 1);", "let f = i128::from(up - down) << m;")]),
    ("S12_fd_s_double", "S", [("let s = i128::from(k_up - k_down) << (m - 1);", "let s = i128::from(k_up - k_down) << m;")]),
    ("S13_gap_index2", "S", [("let e1 = if d0.len() > 1 {\n        level(&d0, &o2, 1, gap_seed,", "let e1 = if d0.len() > 2 {\n        level(&d0, &o2, 2, gap_seed,")]),
    ("S14_c1c2_no_N_over_Nm1", "S", [("big * (1 << 20) / (big - 1)", "1 << 20")]),
    ("S15_c2_half", "S", [("let c2 = (2 * s * n_over) >> 20;", "let c2 = (s * n_over) >> 20;")]),
    ("S16_c1_wk_f3s", "S", [("let wk = f - 4 * s + e - xf - uterm;", "let wk = f - 3 * s + e - xf - uterm;")]),
    ("S17_rotor_o2_no_charge", "S", [("let n0 = big - 2 * minus - i128::from(charge);", "let n0 = big - 2 * minus;")]),
    ("S18_rotor_d_n0", "S", [("let n0 = big - plus - minus;\n            let sum = plus + minus;", "let n0 = big - 2 * minus;\n            let sum = plus + minus;")]),
    ("S19_fd_sum_plus1", "S", [("d += round_div(dx.sign * (sum << (SCALE - dx.m)), big);", "d += round_div(dx.sign * ((sum + 1) << (SCALE - dx.m)), big);")]),
    ("S20_o2_minus_one_unit_of_2^60", "S", [("            quo as i128", "            (quo as i128 - (1i128 << 30)).max(0)")]),
    # ---- the full-space elements
    ("F01_pair_sign", "F", [(PAIR_ROUND, "-(" + PAIR_ROUND + ")")]),
    ("F02_pair_bose_pp", "F", [("let bose = if no_bose { 1 } else { (p + 1) * (m + 1) };", "let bose = if no_bose { 1 } else { (p + 1) * (p + 1) };")]),
    ("F03_pair_n0n0", "F", [("root_bits((bose * n0 * (n0 - 1)) as u128)", "root_bits((bose * n0 * n0) as u128)")]),
    ("F04_pair_reverse_nonherm", "F", [("coef.push(pair_element(p - 1, m - 1, n0 + 2, big, bits, par.no_bose));", "coef.push(pair_element(p - 1, m - 1, n0 + 1, big, bits, par.no_bose));")]),
    ("F05_direct_drop_pm", "F", [("par.u.n * (n0 * sum + p * m) * par.x.d", "par.u.n * (n0 * sum) * par.x.d")]),
    ("F06_direct_n0minus1", "F", [("par.u.n * (n0 * sum + p * m) * par.x.d", "par.u.n * ((n0 - 1) * sum + p * m) * par.x.d")]),
    ("F07_x_on_plus_only", "F", [("par.x.n * sum * par.u.d * big", "par.x.n * (2 * p) * par.u.d * big")]),
    ("F08_linear_sign", "F", [("-(round_div(rescale(root * y.n, from, bits), y.d) as i64)", "round_div(rescale(root * y.n, from, bits), y.d) as i64")]),
    ("F09_linear_up_nonherm", "F", [("let value = linear_element(p + 1, n0, par.y, bits);", "let value = linear_element(p + 1, n0 + 1, par.y, bits);")]),
    ("F10_linear_down_nonherm", "F", [("let value = linear_element(p, n0 + 1, par.y, bits);", "let value = linear_element(p, n0, par.y, bits);")]),
    ("F11_linear_minus_half", "F", [("let value = linear_element(m + 1, n0, par.y, bits);", "let value = linear_element(m + 1, n0, par.y, bits) / 2;"), ("let value = linear_element(m, n0 + 1, par.y, bits);", "let value = linear_element(m, n0 + 1, par.y, bits) / 2;")]),
    # ---- the integrator
    ("T01_symplectic_euler", "F", [(HEAD, "    for step in 0..steps {"),
        ("let right = if step + 1 == steps { half } else { SCALE };", "let right = SCALE; let _ = step;"),
        ("    let half = SCALE + 1;\n    for step in 0..steps {\n        let right = if step == 0 { half } else { SCALE };", "    for step in 0..steps {\n        let right = SCALE; let _ = step;"),
        (TAIL, "}")]),
    ("T02_retreat_swapped", "V", [("        let right = if step == 0 { half } else { SCALE };\n        op.apply_into(u, work, right);\n        for (slot, k) in v.iter_mut().zip(work.iter()) {\n            *slot += *k;\n        }\n        op.apply_into(v, work, SCALE);\n        for (slot, k) in u.iter_mut().zip(work.iter()) {\n            *slot -= *k;\n        }", "        let right = if step == 0 { half } else { SCALE };\n        op.apply_into(v, work, SCALE);\n        for (slot, k) in u.iter_mut().zip(work.iter()) {\n            *slot -= *k;\n        }\n        op.apply_into(u, work, right);\n        for (slot, k) in v.iter_mut().zip(work.iter()) {\n            *slot += *k;\n        }")]),
    ("T03_step_4x_larger", "F", [("let need = if n <= 243 { 64 * n } else { 4 * n };", "let need = if n <= 243 { 16 * n } else { n };")]),
    ("T04_step_16x_larger", "F", [("let need = if n <= 243 { 64 * n } else { 4 * n };", "let need = if n <= 243 { 4 * n } else { n / 4 };")]),
    ("T05_first_kick_full", "F", [(HEAD, HEAD.replace("op.apply_into(u, work, half);", "op.apply_into(u, work, SCALE);")),
        (TAIL, TAIL.replace("op.apply_into(u, work, half);", "op.apply_into(u, work, SCALE);"))]),
    # ---- the read-out
    ("R01_A_sign", "F", [("r.a += (product(t, i) * root) >> 32;\n                }\n                if let Some(t) = space.index(p, m + 1) {\n                    let root = isqrt((((m + 1) * n0) as u128) << 64) as i128;\n                    r.a += (product(t, i) * root) >> 32;", "r.a -= (product(t, i) * root) >> 32;\n                }\n                if let Some(t) = space.index(p, m + 1) {\n                    let root = isqrt((((m + 1) * n0) as u128) << 64) as i128;\n                    r.a -= (product(t, i) * root) >> 32;")]),
    ("R02_A_second_term_zero", "F", [("let root = isqrt((((m + 1) * n0) as u128) << 64) as i128;", "let root = 0 * isqrt((((m + 1) * n0) as u128) << 64) as i128;")]),
    ("R03_B_root_pm", "F", [("let root = isqrt(((p * (m + 1)) as u128) << 64) as i128;", "let root = isqrt(((p * m) as u128) << 64) as i128;")]),
    ("R04_B_sign", "F", [("r.b += (product(t, i) * root) >> 32;", "r.b -= (product(t, i) * root) >> 32;")]),
    ("R05_P_root_n0n0", "F", [("let root = isqrt((((p + 1) * (m + 1) * n0 * (n0 - 1)) as u128) << 64) as i128;", "let root = isqrt((((p + 1) * (m + 1) * n0 * n0) as u128) << 64) as i128;")]),
    ("R06_P_sign", "F", [("r.re_p += (product(t, i) * root) >> 32;", "r.re_p -= (product(t, i) * root) >> 32;")]),
    ("R07_npnm_pp", "F", [("r.np_nm += weight * p * m;", "r.np_nm += weight * p * p;")]),
    ("R08_n0pairs_plus1", "F", [("r.n0_pairs += weight * (big - p - m) * (p + m);", "r.n0_pairs += weight * (big - p - m + 1) * (p + m);")]),
    ("R09_pairs_plus1", "F", [("r.pairs += weight * (p + m);", "r.pairs += weight * (p + m + 1);")]),
    ("R10_pin_a1_half", "L", [("let a1 = 2 * r.a.abs() / big;\n    let d2 =", "let a1 = r.a.abs() / big;\n    let d2 =")]),
    ("R11_pin_d2_half", "L", [("let d2 = 2 * r.b.abs() / big;", "let d2 = r.b.abs() / big;")]),
    ("R12_pin_c1_sign", "L", [("let d2 = 2 * r.b.abs() / big;\n    let wk = r.n0_pairs + 2 * r.re_p;", "let d2 = 2 * r.b.abs() / big;\n    let wk = r.n0_pairs - 2 * r.re_p;")]),
    ("R13_pin_c2_denominator", "L", [("(2 * wk / (big * (big - 1)), 2 * r.np_nm / (big * (big - 1)))", "(2 * wk / (big * (big - 1)), 2 * r.np_nm / (big * big))")]),
    ("R14_pin_f_not_per_N", "L", [("ppm(r.pairs / big),\n        ground.cycles", "ppm(r.pairs),\n        ground.cycles")]),
    ("R15_pin_energy_double", "L", [("let energy = i128::from(ground.theta) << bits;", "let energy = i128::from(ground.theta) << (bits + 1);")]),
    ("R16_predicted_A1_is_read", "Q", [("let predicted_a1 = (4 * par.y.n.abs() * (cosh_term << 20)) / par.y.d;", "let predicted_a1 = a1 + 0 * cosh_term;")]),
    ("R17_closed_is_read", "Q", [("let closed_fix = closed << 20;", "let closed_fix = if par.no_bose { closed << 20 } else { jbar };")]),
    ("R18_predicted_C1_is_read", "Q", [("        let predicted_c1 = {\n            let top = 4 * (delta.d - delta.n) * jbar;\n            top / (delta.d * big)\n        };", "        let predicted_c1 = c1;")]),
    ("R19_energy_off_zero", "Q", [("ppb(energy_fix),", "ppb(energy_fix * 0),")]),
    ("R20_quench_c1_uses_big2", "Q", [(Q_C1, Q_C1.replace("let c1 = 2 * wk / (big * (big - 1));", "let c1 = 2 * wk / (big * big);"))]),
    # ---- Lanczos
    ("L01_tol_2^44", "L", [("let tol = (1i128 << 30) >> bits;", "let tol = (1i128 << 44) >> bits;")]),
    ("L02_second_ritz", "L", [("theta = level(d, &o2, 0, theta, 1 << 40);", "theta = level(d, &o2, d.len().min(2) - 1, theta, 1 << 40);")]),
    ("L03_one_cycle", "L", [("lanczos(&op, start.clone(), krylov, tol, 600)", "lanczos(&op, start.clone(), krylov, tol, 1)")]),
    ("L04_start_not_even", "L", [("table[m * side + p] = value;", "let _ = m;")]),
    # ---- new: run_window and the chain it uses
    ("W01_u_wrong_in_list", "W", [("let everywhere = [\n        (q(1, 4), q(-1, 4)),", "let everywhere = [\n        (q(1, 3), q(-1, 4)),")]),
    ("W02_x_wrong_in_list", "W", [("(q(3, 4), q(1, 8)),", "(q(3, 4), q(1, 4)),")]),
    ("W03_s_list_6_for_8", "W", [(LIST, "let list = if %s { [(16, 1), (6, 1), (4, 1), (2, 1), (1, 1), (1, 2), (0, 1)] } else { [(16, 1), (8, 1), (4, 1), (2, 1), (1, 1), (1, 2), (0, 1)] };" % IS_WINDOW)]),
    ("W04_y_sign_window_only", "W", [(YLINE, "let y = Q { n: if %s { -sn } else { sn }, d: sd * big };" % IS_WINDOW)]),
    ("W05_y_half_window_only", "W", [(YLINE, "let y = Q { n: sn, d: if %s { 2 * sd * big } else { sd * big } };" % IS_WINDOW)]),
    ("W06_y_label_only", "W", [("rows.push(make(&space, par, &ground, bits, &y.text(), &s_text));", "let label = if %s { Q { n: sn, d: 2 * sd * big }.text() } else { y.text() };\n        rows.push(make(&space, par, &ground, bits, &label, &s_text));" % IS_WINDOW)]),
    ("W07_P2_sum_not_difference", "W", [("charge_squared += weight * (p - m) * (p - m);", "charge_squared += weight * (p + m) * (p + m);")]),
    ("W08_P2_constant", "W", [("let share = (charge_squared / (big * big) * 1_000_000) / norm.max(1);", "let share = 1_000_000 + 0 * (charge_squared / (big * big)) / norm.max(1);")]),
    ("W09_P2_abs_times_N", "W", [("charge_squared += weight * (p - m) * (p - m);", "charge_squared += weight * (p - m).abs() * space.n;")]),
    ("W10_chain_upward", "W", [(LIST, "let list = if %s { [(0, 1), (1, 2), (1, 1), (2, 1), (4, 1), (8, 1), (16, 1)] } else { [(16, 1), (8, 1), (4, 1), (2, 1), (1, 1), (1, 2), (0, 1)] };" % IS_WINDOW)]),
    ("W11_generic_start_each_row", "L", [("let ground = if sn == 0 {", "let ground = if sn >= 0 {")]),
    ("W12_drop_a_point", "W", [("        (q(3, 4), q(-1, 8)),\n    ];\n    let small", "    ];\n    let small")]),
    ("W13_small_list_shorter", "W", [("let small = [(q(1, 4), q(-1, 4)), (q(3, 4), q(0, 1)), (q(1, 1), q(-1, 4))];", "let small = [(q(1, 4), q(-1, 4))];")]),
    ("W14_tag_lost", "W", [('.replace("POLARITON_PIN|", "POLARITON_PIN_WINDOW|")\n', '.replace("POLARITON_PIN|", "POLARITON_PIN_WINDOW2|")\n')]),
    # ---- new: conversion_chain and run_conversion
    ("C01_x_is_delta", "C", [("x: add(delta, q(-1, 1)),\n        u: q(1, 1),\n        y,", "x: delta,\n        u: q(1, 1),\n        y,")]),
    ("C02_u_half", "C", [("x: add(delta, q(-1, 1)),\n        u: q(1, 1),\n        y,", "x: add(delta, q(-1, 1)),\n        u: q(1, 2),\n        y,")]),
    ("C03_c1_big2", "C", [(CONV_C1, CONV_C1.replace("let c1 = 2 * wk / (big * (big - 1));", "let c1 = 2 * wk / (big * big);"))]),
    ("C04_c1_P_sign", "C", [(CONV_C1, CONV_C1.replace("r.n0_pairs + 2 * r.re_p", "r.n0_pairs - 2 * r.re_p"))]),
    ("C05_f_not_per_N", "C", [(CONV_ROW, CONV_ROW.replace("ppb(r.pairs / big),", "ppb(r.pairs),"))]),
    ("C06_A_sign", "C", [(CONV_ROW, CONV_ROW.replace("ppb(r.a),", "ppb(-r.a),"))]),
    ("C07_B_sign", "C", [(CONV_ROW, CONV_ROW.replace("ppb(r.b),", "ppb(-r.b),"))]),
    ("C08_stale_time", "C", [("advance(&op, &mut a, &mut b, &mut w, ((t - now) << k) as u64);", "advance(&op, &mut a, &mut b, &mut w, (t << k) as u64);")]),
    ("C09_k_plus_1", "C", [('time_bits(*n),\n            "POLARITON_QUENCH_CONVERSION",', 'time_bits(*n) + 1,\n            "POLARITON_QUENCH_CONVERSION",')]),
    ("C10_k_minus_3", "C", [('time_bits(*n),\n            "POLARITON_QUENCH_CONVERSION",', 'time_bits(*n) - 3,\n            "POLARITON_QUENCH_CONVERSION",')]),
    ("C11_energy_A_sign", "C", [("- (2 * r.a * par.y.n) / par.y.d;\n        rows.push(format!(\n            \"{tag}|N={big}", "+ (2 * r.a * par.y.n) / par.y.d;\n        rows.push(format!(\n            \"{tag}|N={big}")]),
    ("C12_energy_zero", "C", [(CONV_ROW, CONV_ROW.replace("ppb(energy),", "ppb(energy * 0),"))]),
    ("C13_norm_off_zero", "C", [(CONV_ROW, CONV_ROW.replace("ppb(r.norm - (1i128 << SCALE))", "ppb(0 * r.norm)"))]),
    ("C14_root_243_is_15", "C", [("(243, 16)", "(243, 15)")]),
    ("C15_delta_quarter", "C", [("for &delta in &[q(0, 1), q(1, 2)] {\n            for &(sn, sd) in &fields {", "for &delta in &[q(0, 1), q(1, 4)] {\n            for &(sn, sd) in &fields {")]),
    ("C16_jbar_double", "C", [(CONV_ROW, CONV_ROW.replace("ppb(r.pairs / 2),", "ppb(r.pairs),"))]),
    ("C17_start_not_vacuum", "C", [("a[space.index(0, 0).unwrap()] = 1i64 << SCALE;\n    let mut rows = Vec::new();", "a[space.index(1, 0).unwrap()] = 1i64 << SCALE;\n    let mut rows = Vec::new();")]),
    ("C18_y_sign", "C", [("jobs.push((n, delta, q(sn, sd * root), s, ", "jobs.push((n, delta, q(-sn, sd * root), s, ")]),
    ("C19_s_label", "C", [("&s.text(),", '"0",')]),
    ("C20_c2_big2", "C", [(CONV_C1, CONV_C1.replace("let c2 = 2 * r.np_nm / (big * (big - 1));", "let c2 = 2 * r.np_nm / (big * big);"))]),
    # ---- new: the Taylor convert rows
    ("TC1_k_10", "C", [('"taylor", &[t], 16, "POLARITON_TAYLOR_CONVERT"', '"taylor", &[t], 10, "POLARITON_TAYLOR_CONVERT"')]),
    ("TC2_k_6", "C", [('"taylor", &[t], 16, "POLARITON_TAYLOR_CONVERT"', '"taylor", &[t], 6, "POLARITON_TAYLOR_CONVERT"')]),
    ("TC3_one_point_only", "C", [("let more: [(u64, Q, Q, i128); 4] = [\n        (27, q(0, 1), q(1, 5), 1),\n        (27, q(0, 1), q(1, 5), 2),\n        (27, q(1, 2), q(2, 5), 1),\n        (9, q(0, 1), q(1, 3), 2),\n    ];", "let more: [(u64, Q, Q, i128); 1] = [\n        (27, q(0, 1), q(1, 5), 1),\n    ];")]),
    # ---- new: sector_o2
    ("O01_one_fewer_limb_scale_off", "S", [("for _ in 0..5 {", "for _ in 0..4 {")]),
    ("O02_one_fewer_limb_scale_kept", "S", [(LIMBS, LIMBS.replace("0..5", "0..4").replace("quo as i128", "(quo as i128) << 18"))]),
    ("O03_order_rem_before_quo", "S", [("                rem <<= 18;\n                quo = (quo << 18) + rem / den;\n                rem %= den;", "                rem <<= 18;\n                rem %= den;\n                quo = (quo << 18) + rem / den;")]),
    ("O04_order_shift_last", "S", [("                rem <<= 18;\n                quo = (quo << 18) + rem / den;\n                rem %= den;", "                quo = (quo << 18) + rem / den;\n                rem %= den;\n                rem <<= 18;")]),
    ("O05_den_N3_Nminus1", "S", [("let den = (big * big * big * big) as u128;", "let den = (big * big * big * (big - 1)) as u128;")]),
    ("O06_bose_plus_plus", "S", [(O2, "let mut rem = ((plus + 1) * (plus + 1) * n0 * (n0 - 1)) as u128;")]),
    ("O07_quo_plus_1_unit_of_2^90", "S", [("            quo as i128", "            quo as i128 + 1")]),
    # ---- new: count_below
    ("P01_pivot_shift_29", "SL", [("(*ok << 30) / q", "(*ok << 29) / q")]),
    ("P02_pivot_shift_31", "SL", [("(*ok << 30) / q", "(*ok << 31) / q")]),
    ("P03_zero_pivot_positive", "SL", [("let signed = |q: i128| if q == 0 { -1 } else { q };", "let signed = |q: i128| if q == 0 { 1 } else { q };")]),
    ("P04_o2_floor_2^60_in_pivot", "SL", [("(*ok << 30) / q", "((*ok >> 30) << 60) / q")]),
    ("P05_lambda_one_unit", "SL", [("i128::from(*dk - lambda) - (*ok << 30) / q", "i128::from(*dk - lambda + 1) - (*ok << 30) / q")]),
    ("P06_first_pivot_not_counted", "SL", [("let mut count = usize::from(q < 0);", "let mut count = 0usize;")]),
    # ---- new: the Lanczos o^2
    ("Z01_lanczos_o2_shift_31", "L", [("(i128::from(*b) * i128::from(*b)) >> 30)", "(i128::from(*b) * i128::from(*b)) >> 31)")]),
    ("Z02_lanczos_o2_shift_29", "L", [("(i128::from(*b) * i128::from(*b)) >> 30)", "(i128::from(*b) * i128::from(*b)) >> 29)")]),
    ("Z03_lanczos_o2_floor_2^60", "L", [("(i128::from(*b) * i128::from(*b)) >> 30)", "((i128::from(*b) * i128::from(*b)) >> 60) << 30)")]),
    # ---- new: the energy read of the pinned quench
    ("Q01_quench_energy_A_sign", "Q", [("- (2 * r.a * par.y.n) / par.y.d;\n        let a1 = 2 * r.a.abs() / big;", "+ (2 * r.a * par.y.n) / par.y.d;\n        let a1 = 2 * r.a.abs() / big;")]),
]

# Run on the whole sector stage, against the real reader and the top route: what the holds H1, H2 and H8 were for.
TOP = [
    ("X01_o2_floor_2^60", [(LIMBS, LIMBS.replace("quo as i128", "(quo as i128 >> 30) << 30"))]),
    ("X02_old_fd_step", [("let m = if critical { 20 + power / 2 } else { 20 };", "let m = if critical { 20 + 3 * power / 4 } else { 20 };")]),
    ("X03_o2_quantised_256_units", [(LIMBS, LIMBS.replace("quo as i128", "(quo as i128 >> 38) << 38"))]),
    ("X04_one_fewer_limb_scale_kept", [(LIMBS, LIMBS.replace("0..5", "0..4").replace("quo as i128", "(quo as i128) << 18"))]),
    ("X05_o2_minus_one_unit_of_2^60", [("            quo as i128", "            (quo as i128 - (1i128 << 30)).max(0)")]),
    ("X06_o2_floor_2^80", [(LIMBS, LIMBS.replace("quo as i128", "(quo as i128 >> 10) << 10"))]),
    ("X07_o2_floor_2^70", [(LIMBS, LIMBS.replace("quo as i128", "(quo as i128 >> 20) << 20"))]),
]
