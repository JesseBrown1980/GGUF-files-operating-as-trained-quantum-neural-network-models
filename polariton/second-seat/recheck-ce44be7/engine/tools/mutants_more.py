# A second set of mutants, added after reading the reader: columns it still takes on the engine's word, and the Lanczos tolerance.
M2 = [
    ("Q03_jbar_over_N_not_per_N", "Q", [("ppm(jbar / big),\n            ppm(c1),", "ppm(jbar),\n            ppm(c1),")]),
    ("Q04_band_largest_constant", "Q", [("largest_f = largest_f.max(f);", "largest_f = largest_f.max(f / 2);")]),
    ("V02_reversal_flag_constant", "V", [("u8::from(u == u0 && v == v0)", "1u8")]),
    ("V03_equals_full_counts_zero", "Q", [("if uf[i] != us[j] || vf[i] != vs[j] {\n                    on_line_different += 1;\n                }", "let _ = j;"), ("} else if uf[i] != 0 || vf[i] != 0 {\n                off_line_nonzero += 1;\n            }", "}")]),
    ("L05_tol_2^36", "L", [("let tol = (1i128 << 30) >> bits;", "let tol = (1i128 << 36) >> bits;")]),
    ("L08_tol_2^34", "L", [("let tol = (1i128 << 30) >> bits;", "let tol = (1i128 << 34) >> bits;")]),
    ("L06_residual_print_zero", "L", [("let residual_units = ((ground.residual << bits) * 1_000_000_000_000) >> SCALE;", "let residual_units = 0i128 * ((ground.residual << bits) * 1_000_000_000_000) >> SCALE;")]),
    ("L07_cycle_cap_3", "L", [("lanczos(&op, start.clone(), krylov, tol, 600)", "lanczos(&op, start.clone(), krylov, tol, 3)")]),
    ("S21_C1N_not_times_N", "S", [("ppm(c1 * big),\n", "ppm(c1),\n")]),
    ("S22_e_ppb_shift_1e-6", "S", [("ppb(e),\n        ppb(f),", "ppb(e) + 1000,\n        ppb(f),")]),
    ("C21_conv_a_half", "C", [("let r = read(&space, &a, &b);\n        let big = space.n;\n        let wk", "let mut r = read(&space, &a, &b);\n        r.a /= 2;\n        let big = space.n;\n        let wk")]),
]
