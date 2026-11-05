#!/usr/bin/env python3
# make_holds.py -- writes HOLDS.txt. Each OLD is cut from the file at this head by exact markers, so it matches byte for byte; then every OLD is checked to occur exactly once.
import sys, subprocess, re

WT = 'C:/tmp/qnn-polariton-wt/'
HEAD = subprocess.run(['git', '-C', 'C:/tmp/qnn-polariton-wt', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
assert HEAD == 'ce44be742d9d59d07bb8ec8a9ed6a559da4ec0bd', HEAD
README = 'polariton/README.md'
raw = open(WT + README, 'rb').read().decode('utf-8')

def cut(start, end):
    i = raw.index(start)
    j = raw.index(end, i) + len(end)
    return raw[i:j]

holds = []

holds.append((README, 'high',
    cut("""- **Past the depletion range:**""", """has returned to f = 0.047."""),
    """- **Past the depletion range:** on the 35 rows at N ≥ 243 with predicted f above 1/10, all at t ≤ 3, V² reads 0.96 to 1.15 of the law, while A₁ reads down to 0.06 of its form and C₁ down to 0.004 of its form. On the 14 rows with Y ≤ 1, Y_read = V²/(1 − V²) is 0.96 to 1.18 of Y, with read f up to 0.49 and C₁ down to 0.29 of its form. On the 21 rows with Y > 1, all above the law, the ratio has a ceiling near 1/law, 1.04 to 1.91, and Y_read is 1.12 to 6.4 of Y, with one row above 1. The row at A₁ 0.06 of its form, N = 243, y√N = 4, t = 3, is on its fall: the same chain reads 1.007, 0.883, 0.472, 0.070 of the law at t = 3, 3.25, 3.5, 3.75.
- **How far it reaches:** exact traces at N = 729, y√N from 1/8 to 4, read V²/law at the first maximum of f as 0.90 to 1.14 at δ = 0, 0.87 to 1.11 at δ = 1/2, 0.98 to 1.13 at δ = −1/2 and 1.01 to 1.32 at δ = −1. At small Y it leaves 5% with C₁ at 0.09 to 0.42 of its form, and at Y near 1 it reaches 1.05 with C₁ at 0.55 to 0.75.
- **The reason:** at large γt, with ε = (5 − 2δ)e^(2γt)/(8γ⁴N), the first correction gives A₁/law = 1 − ε(1 + Y/2), C₁/law = 1 − 2ε(1 + 2Y + Y²/2)/(1 + Y) and V²/law = 1 + εY/(1 + Y), so the ε term of V² vanishes at small Y. Past first order, a truncated Wigner sample in integers at N = 59049, y√N = 1/8, reads V²/Y = ⟨ρ|ζ|⟩²/(⟨|ζ|²⟩⟨ρ²⟩) within 1.5% to t = 7, past the peak of f at t = 6.5, with ρ = |A|/N and ζ the seed of the growing mode at t = 0. That ratio is 1 while ρ grows in proportion to |ζ|, stationary at first order, and π/4 when ρ is constant. The position stays at arg ζ, with cos(θ − arg ζ) at 1.000 through t = 8, while V²/law falls to 0.48, so V² reads the position's spread near the peak of f, where ρ is nearly constant. The exact state at this N is OPEN; at N = 729 exact V²/Y reads 1.12 of the sampled ratio at the peak.
- **At a return:** at N = 81, y√N = 4, f returns to 0.047 at t = 3, where V² reads 0.02 against 0.96, ⟨A²⟩/⟨A†A⟩ reads −0.75 and ⟨B⟩ is negative, with the weight of A on its imaginary axis and the k pattern at ±π/2 from its first position. V² then rises to 0.91 at t = 4.75 and falls to 0.005 at t = 6.25. At small Y a return goes above the law: N = 243, y√N = 1/8 reads 0.21 against 0.029 at t = 6.5, f = 0.047. Over t ≤ 12 at N = 729, V²/law runs from 0.001 to 22.5, and on the receipt's rows at N = 81 from 0.02 to 1.27.""",
    """V2 "holds well past each of its parts" rests on rows at t<=3: 21 of 35 have Y>1, where Y_read/Y reads 1.12..6.42 under a ceiling, and the extreme row falls to 0.070 of the law 0.75 later; small-Y V2/law reads 0.865..0.93 at the f peak at N=729, 0.84 at N=59049 (TW), 22.5 after the return. Runs: t4_split.py, t4_summary.py, t4_cs.py, t4_small_y.py; FINDINGS F4."""))

holds.append((README, 'medium',
    cut("""- **The first correction to C₁ and A₁ at general (δ, y),**""", """and why V² holds past both."""),
    """- **The first correction to C₁ and A₁ at general (δ, y),** and V² past the first maximum of f, where it leaves the law on both sides.""",
    """The item presumes V2 holds past both parts; exact traces read V2/law from 0.001 to 22.5 at N=729 past the first f peak. FINDINGS F4.2. F5 holds the first correction in closed form, for use when the author closes this item."""))

holds.append((README, 'low',
    """Each deviation falls as 1/N.""",
    """N times each deviation reads 6.0, 8.3, 10.5, 11.5 for V², −20.2, −27.5, −32.1, −34.0 for A₁, and −38.5, −58.1, −72.2, −78.5 for C₁, approaching the first correction's limits of 12.1, −35.1 and −82.4 at y²N = 1/4 from below, within 6% by N = 2187.""",
    """Successive ratios for N x 3 read 2.19, 2.37, 2.75 (V2), 2.20, 2.57, 2.84 (A1), 1.99, 2.42, 2.76 (C1), where 1/N needs 3; t5_numbers.py, out/t5_numbers.txt."""))

holds.append((README, 'low',
    """It reads 1.20 on one row at N = 81 and 1.015 on one at N = 243.""",
    """It reads above 1 on three rows at N = 81, at 1.02, 1.06 and 1.20, and on one at N = 243, at 1.015. At δ > 1 it reads above 1 at each N read, where Y < −1, since Var(A) falls below the shot term at leading order: 1.1887 against the law's 1.1887 at δ = 2, N = 729, y√N = 1/2, t = 2, and below 0 where −1 < Y < 0.""",
    """Four conversion rows read above 1, three at N=81 (1.0244, 1.0566, 1.1979); outside the band V2>1 holds at N>=243 on 81 of 81 rows with |Y|>1, and C1<0 with V2<0 on 97 of 99 with |Y|<1; t7_readme_check.py, t3_read.py; FINDINGS F2.5, F3."""))

holds.append((README, 'low',
    """Read over it at N = 729: 0.9998, 1.0031, 1.175 for t = 1, 2, 3.""",
    """Read over it at N = 729: 1.0000, 1.0032, 1.175 for t = 1, 2, 3.""",
    """A_ppb gives 1.00004, 1.00322, 1.17518; the README digits come from the rounded A1_ppm integer 2113 for 2113.53; t7b.py, out/t7b.txt."""))

holds.append((README, 'low',
    """it reads 0.916 of its form at N = 729""",
    """it reads 0.917 of its form at N = 729""",
    """C1 0.0709458 over law 0.0774092 = 0.91650, which rounds to 0.917; 0.916 comes from the rounded 0.0709/0.0774; t5_numbers.py."""))

holds.append((README, 'low',
    """− 3. Read over it at N = 729""",
    """− 3, for y√N small; at general y, w₁ gains Ny²[17t sinh t − (53/4)cosh t − 8cosh 2t + (5/4)cosh 3t + 20]. Read over it at N = 729""",
    """Without the term the read over law+first is 0.9609 at N=729, y sqrt N=4, t=1 and 0.9752 at y sqrt N=1, t=2; with it 1.0019 and 1.0084; t7b.py, t5_firstcorr.py; FINDINGS F5."""))

holds.append((README, 'low',
    """- A₁ = 4|y|(cosh γt − 1)/(1 + δ), with ⟨A⟩ opposite to y and ⟨B⟩ positive""",
    """- A₁ = 4|y|(cosh γt − 1)/(1 + δ), with ⟨A⟩ opposite to y at δ < 1, the same sign as y at δ ≥ 1, and ⟨B⟩ positive up to the first return of f""",
    """Rows at N>=243: <A> opposite to y on 612 of 612 at delta<1, same sign on 252 of 252 at delta>=1 (at delta=+1: 72 of 72, where the law gives A1=0); <B> negative at returns, N=81 delta=0 y sqrt N=4 t=3 reads -0.122; t7b.py, out/t7b.txt, t2_anchor.py."""))

holds.append((README, 'medium',
    """from a vacuum start. The paper's seeded ±1 modes enter there.""",
    """from a vacuum start. The paper's seeded ±1 modes enter there. At those values the law gives a nearly uniform phase, with a shot-to-shot spread of cos θ of 0.68 to 0.70 against 0.71 for a uniform phase. The paper's Fig. S23, under continuous pumping with threshold near 14 mW, reads 0.35, 0.18, 0.12, 0.13 at 15, 18, 22, 25 mW, which through the same phase distribution is Y about 1.4 to 4.2 and y√N about 0.8 to 1.4 at δ = 0, with its axis read as cos θ from its 0.7 at random phase. The pulsed reading and the continuous one differ by 4 to 16 times in y√N, and what lies between them is OPEN. The law also gives C₁ = 4ρ(1 − δ), about 0.02(1 − δ) at the paper's Bragg fraction, independent of V², which is the next step's sharpest test.""",
    """Arithmetic of 0.017, 0.068, 0.09, 0.19 reproduced; the reading predicts spread 0.68..0.70 while SI Fig S23 reads 0.118..0.353 above threshold (markers read off the figure's raster against its ticks, +-0.003; phi taken as cos theta from 0.7 at random phase). t6_paper.py, t6_spread.py, t6_figaxis.py; FINDINGS F6 and its correction."""))

out = []
for k, (path, sev, old, new, reason) in enumerate(holds, 1):
    n = raw.count(old)
    assert n == 1, (k, n, old[:60])
    out.append('HOLD H%d | file=%s | severity=%s\nOLD<<<\n%s\n>>>\nNEW<<<\n%s\n>>>\nREASON: %s\n' % (k, path, sev, old, new, reason))
    low = new.lower()
    for bad in (' not ', "n't", ' no ', 'rather than', 'instead of', ' never ', ' nor '):
        if bad in low:
            print('WORD_CHECK H%d contains %r' % (k, bad))
text = '\n'.join(out)
open('C:/tmp/opus55/polariton-recheck-contact-20261105/HOLDS.txt', 'w', encoding='utf-8', newline='\n').write(text)
print('holds', len(holds), 'head', HEAD)
back = open('C:/tmp/opus55/polariton-recheck-contact-20261105/HOLDS.txt', encoding='utf-8', newline='').read()
cnt = 0
for m in re.finditer(r'HOLD H(\d+) \| file=(\S+) \| severity=(\w+)\nOLD<<<\n(.*?)\n>>>\nNEW<<<\n(.*?)\n>>>\nREASON: ', back, re.S):
    old = m.group(4)
    assert raw.count(old) == 1, m.group(1)
    cnt += 1
print('verified_blocks', cnt, 'each_OLD_occurs_once=1')
