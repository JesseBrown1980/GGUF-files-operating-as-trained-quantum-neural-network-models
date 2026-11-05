# For each README-bound or body-bound hold: its substance as phrases, searched in the text at this head. New digits are allowed for; phrases are chosen to survive them.
WT = 'C:/tmp/qnn-polariton-wt/'
ME = 'C:/tmp/opus55/polariton-recheck-text-20261105/'
readme = open(WT + 'polariton/README.md', encoding='utf-8').read()
root = open(WT + 'README.md', encoding='utf-8').read()
body = open(ME + 'out/pr8_body.md', encoding='utf-8').read()
pred = open(WT + 'polariton/PREDICTION.hbp', encoding='utf-8').read()
reader = open(WT + 'polariton/read_prediction.py', encoding='utf-8').read()
wf = open(WT + '.github/workflows/polariton.yml', encoding='utf-8').read()
out = open(ME + 'out/check_disp.txt', 'w', encoding='utf-8', newline='\n')
def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s); out.write(s + '\n')
T = {'R': readme, 'O': root, 'B': body, 'P': pred, 'E': reader, 'W': wf}
CHECK = [
 ('text H1', 'R', ['Yes to the central test at U = J/2, Δ = 0,', 'in the ground state at N = 243 and 729', 'at 2k, at the predicted size', 'U = J/2 is a model point chosen at derivation', 'where the pair state lies below the plane wave']),
 ('text H1 lost?', 'R', ['Contact interactions give U = J, and the pinned ground state there is OPEN', 'no fitted number']),
 ('text H2', 'R', ['with particle number conserved and unitary evolution', 'contact interactions with equal overlaps give u = 1', 'the central result runs at u = 1/2']),
 ('text H3', 'R', ['averaged over about 8 × 10⁶ pulses', 'with its modulation at k_r', 'g¹ by interferometry', 'Here that harmonic is A₁', 'central result is D₂ at 2k', 'g²(x − x′)', 'removal of the linear coupling', 'awaiting that experiment', '0.04 μm⁻¹ at about 2.3 μm⁻¹, or 1.7%', '250 and 430 μW thresholds']),
 ('text H4', 'O', ['at U = J/2, a model point chosen at derivation', 'contact interactions alone give U = J', 'in the full symmetric space of 266,815 states', 'N counts bosons here', '11,943,937 and 21,523,361 states', 'HTTP-0 channel and address counts', 'at three points of the model', 'exact-rational route on 143 levels at N ≤ 243']),
 ('text H5', 'B', ['N counts bosons in the symmetric space', 'tridiagonal fixed-momentum sectors of 11,943,937 and 21,523,361 states', 'at three points of the model', 'in the full symmetric space, at N = 729, of 266,815 states']),
 ('text H6', 'B', ['with every predicted value frozen first', 'a model point chosen at derivation where the pair state lies below the plane wave', '(contact interactions give U = J)']),
 ('text H7', 'B', ['with particle number conserved and unitary evolution', 'reads its modulation at k_r, which is A₁ here', 'central result is D₂ at 2k', '0.04 μm⁻¹ at about 2.3 μm⁻¹, or 1.7%']),
 ('text H8', 'R', ['with charge P = n₊ − n₋', '⌊N/2⌋ + 1 states at P = 0', '11,943,937 states at N = 23,887,872', 'A general state of N qutrits has dimension 3^N', 'finite differences of those levels, with the step in each row']),
 ('text H9-11', 'E', ['TOP = [3 ** 14, 3 ** 15, 23887872, 3 ** 16]', 'BIG + (TOP if']),
 ('text H12', 'R', ['1.4666, 1.4590, 1.4538, 1.4503, 1.4478, 1.4461, 1.4449', '0.6945, 0.6941, 0.6939, 0.6937, 0.6936, 0.6935, 0.6935']),
 ('text H13', 'R', ['Furthest at δ = −1, t = 8, N = 6561: 0.33 of it, with pairs at 0.32% of N', 'At δ = 1, t = 8, N = 6561: 0.79']),
 ('text H13 lost?', 'R', ['δ = −1 has its rows up to N = 6561', 'local exponent', 'Deviation·N/t⁴']),
 ('text H14', 'R', ['Pairs read 9.2% of N there, where the closed form gives 13.8%']),
 ('text H15', 'R', ['scales as A²/4, an expected 0.02%', '0.004%', '(1 − δ)V² ≈ 0.068']),
 ('text H15 lost?', 'R', ['with V the visibility after averaging over pulses']),
 ('text H16', 'R', ['A plain count with the paper\'s Hopfield coefficients', '0.8 to 1.2 J', 'outside this one-parameter form (CONJECTURE)']),
 ('text H17', 'R', ['At u = 1, from |N, 0, 0⟩, the vacuum start of an optical parametric oscillator', 'exciton reservoir and Rayleigh scattering']),
 ('text H18', 'R', ['off-resonant 100 fs pump at 80 MHz', 'exciton reservoir that feeds the ±1 modes', 'BEC lifetime of a few hundred ps', 'about 30 μm', '0.54 for |0⟩ and 0.4 for |±1⟩', '1.7% shift']),
 ('text H19', 'R', ['of 266,815 states']),
 ('text H20', 'W', ['"Cargo.toml"', '"Cargo.lock"', '".gitattributes"']),
 ('text H21', 'W', ['The receipt hash is the one the attempt record', 'The reader, the exact route and their rows are the pinned ones']),
 ('text H22', 'R', ['one commit also raised the precision of the read-out', 'The tolerances stand as frozen']),
 ('text H23', 'R', ['on 85 rows at P = 0, disordered and critical', 'up to 0.06 from exact at small N', '30 on gaps and 12 on pairs', 'rebuilt with this fix alone reads 887 and 31']),
 ('text H24', 'R', ['9.3 × 10⁻¹²', 'median 1.5 × 10⁻¹²', '137 of the 143', "The first run's 143 of 143 counts both errors", 'held 20 fractional bits', 'no row moved between met and missed']),
 ('text H25', 'P', ['POLARITON_ATTEMPT_BESIDE|run=first|second_seat_rebuilt=f47d662_with_the_pivot_fix_alone']),
 ('text H26', 'R', ['the mean-field energy is −Ny² at every α', 'leading-order pinning energy is 0', 'against 0.1953 at u = 1/2', 'leaves the modulation\'s phase unfixed']),
 ('text H27', 'R', ['before any engine run', "hand and Mathieu modes ran first, and f(q) comes from them"]),
 ('text H28', 'R', ['and within 1.9% at N = 243', 'C₂ itself reads 0.0801 at zero field and 0.0798 at yN = 16']),
 ('text H29', 'R', ['group velocity u in δ_j(k) = δ ± u(k − jk_r)', 'measured dispersion of Fig. 1b']),
 ('text H30', 'R', ['ρ is the fraction in each of the ± modes', 'j̄ = ⟨n₊⟩ is the pair count', 'In e(P) and in the rotor, P is the charge']),
 ('text H31', 'R', ['after the first run finished and before its first read', 'holds out 12 C₁ rows at δ = 1', 'at most 200 ppm']),
 ('text H32', 'R', ['sets the 2% against a floor of 1/50, so 0.0004', 'at most 0.015']),
 ('text H33', 'R', ['one pinned row per point at N = 9', "rest on the engine's Lanczos", '9.18 × 10⁻¹⁰']),
 ('text H34', 'R', ['run 41939586670', 'on Ubuntu in 21 minutes', 'first written on Windows']),
 ('text H35', 'B', ['passed in 21 minutes, byte for byte on Ubuntu', 'first written on Windows']),
 ('derivations H1', 'R', ['even mix of the two plane waves', 'D₂ reads 0.00009 there at N = 243, yN = 4', 'gives 0.437']),
 ('derivations H2', 'R', ['ρ₀ > 0 needs δ > −1 + 3u/2', 'c₀ > 0 for δ > (4u − 2)/(2 + u)', '1 − δ < [(4 − 3u) − √(u(4 − 3u))]/2', '−1, −0.4243, −0.1910, −0.0522, 0', '18 points scanned over P', 'A₁/y reads 1.605 against the rotor\'s 3.875', 'D₂ reads 0.0005 against 0.511', 'y → 0 response on the P = 0 branch']),
 ('derivations H2 lost?', 'R', ['So the u = 1 rows at x = −1/4 and −1/8 read the P = 0 branch']),
 ('derivations H3', 'R', ['Takeover constants', '7.18495 g^(1/3)', '0.162869 g^(−1/3)', 'less 0.44 at u = 1/2', 'gap ratio 0.99962', '105.537 against 105.977 − 0.44']),
 ('derivations H3 lost?', 'R', ['x = 0 rows agree']),
 ('derivations H4', 'R', ['q₀ = Ny²/(16c₀²ω)', 'ω = √(2(1 − x²))', 'y scales as N^(−1/2)', '1/ω to within 4×10⁻⁵ at seven x', 'zero-point sum', '⟨B⟩ is positive here']),
 ('derivations H5', 'R', ['[1 + (3 ∓ u)t² + (2/5)(4 ∓ 3u)t⁴]/N', 'coefficient 2/5 at δ = 1 and 14/5 at δ = −1', '0.35 to 1.37 of (first order)²']),
 ('derivations H6', 'R', ['−δ + (3u/2)⟨j²⟩/(N j̄)', '0.5259 against the read 0.5244', '0.0151 against 0.0148']),
 ('derivations H7', 'R', ['w₁ = −t sinh t + (65/12)cosh t − (11/3)cosh 2t + (5/4)cosh 3t − 3', '0.9998, 1.0031, 1.175']),
 ('derivations H8', 'R', ['4.226×10⁻⁵', 'How its Fig. 1e defines A', '**Which harmonic:**', 'D₂ = 0.195 and A₁ = 0.0126']),
 ('derivations H9', 'R', ['N + 2Re(⟨A⟩e^(ikx)) + 2Re(⟨B⟩e^(2ikx))', 'from real amplitudes or from the parity']),
 ('derivations H10', 'R', ['γ⁶J₁ = −(4 − 3δu)sinh²(2γt)/4', 'through t¹⁴ at four (δ, u)', '−(4 − 3δu)J₀²/γ²']),
 ('derivations H11', 'R', ['a = X₁²/X₀² splits u', 'u₂ = 2 − (a + 1/a)/2', 'δ shifts by 2 − 1/a', '4 − 4u₂ + u₁', 'u₁ = 0.741 and the mean-field u is 1.026']),
 ('derivations H13', 'R', ['Exact y → 0 chains to N = 6561', '−6.72']),
 ('derivations H13 lost?', 'R', ['at 9 points']),
 ('engine H9', 'R', ['| x = 3/2: pairs | 0.07735 | 0.07735 |', '| x = 3/2: gap | 3.46410 | 3.46410 |', '86.65 | 105.54', '0.013431 | 0.011038']),
 ('engine H9b', 'R', ['1.4449', '0.6935']),
 ('engine H9c', 'R', ['The squared off-diagonal was floored at 2⁻⁶⁰', '622 units at N = 3¹⁶', '4,755 ppm high', '371 ppm high', '356 ppm low', 'long division', 'within 1 unit at N ≤ 243']),
 ('engine H10', 'R', ['Here √(2C₂) reads 0.40022', 'read one number', 'on all nine rows at N = 81, 243, 729', 'finite-N effect of C₂ on D₂ is OPEN']),
 ('engine H10: its removal of the clause', 'R', ['so the correlation at zero field sets the modulation']),
 ('engine H11', 'R', ['at the residual 8 × 10⁻¹⁰', 'At the residual 1 × 10⁻¹¹ ⟨A⟩ reads −1 ppb', 'within 1 ppb on the 26 y = 0 rows']),
 ('engine H12', 'R', ['**Parity:**', 'stays byte-even', '141,061, 12,014 and 3,059 × 10⁻¹²']),
 ('engine H13', 'R', ['first committed at `099b0c6`', 'floor of 2% of 1/50', 'A constant A₁/y of 2.29']),
 ('engine H14', 'P', ['engine_bug_3=o^2_floored_at_2^-60']),
]
for name, where, phrases in CHECK:
    txt = T[where]
    res = [(p, p in txt) for p in phrases]
    allp = all(v for _, v in res)
    P(('PRESENT' if allp else 'ABSENT ' if not any(v for _, v in res) else 'PARTIAL'), name, '' if allp else [p for p, v in res if not v])
out.close()
