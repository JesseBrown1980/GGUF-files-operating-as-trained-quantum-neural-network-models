# Cantor-27 / V3: exact qutrit control and Gauss boundary

**Experimental bridge. Not evidence that physical spacetime is discrete, not a mass-gap proof, and not quantum hardware.**

## V3 status

V3 records exact norm/inversion and GGUF reload successes. Its preregistered primary targets T1 and T2 failed: circle classification stayed 154/243 correct (majority baseline), and best r=9 Z3 energy stayed 16.000, not below 16. The 24 GGUFs store ninth-root-phase QNN model parameters.

The V3 two-layer Z3 network (Net9S) applies per-link F, phase, F inverse and an unconditional SUM ring. Hence zero trit parameters do **not** make the full circuit the identity; SUM gates still act (although trivially on the all-zero input). Worse, the SUM ring generally fails to preserve the Gauss-invariant subspace. The regression tests show this with an explicit gauge-transformed flat state. This does not invalidate the original V3 energy measurement, whose code explicitly projects its candidate state onto the physical subspace before measuring. It does prevent the raw V3 circuit from being directly used as physical gauge-invariant time evolution.

## Gauge-preserving exact Cantor circuit

The new src/bin/cantor27_z3.rs independently regenerates and verifies the published 729 trits (SHA-256: 1f48fa5083237cd4bdadc3f6c4f9094b864ca1386d7d09b5b27c19b5f27f6913), and validates a real stored V3 r9 GGUF as a provenance anchor. **It does not execute the GGUF-trained V3 circuit.**

Start in an equal-amplitude superposition of two distinct Z3 gauge orbits, 27 configurations each, normalized by sqrt(54). For every time slot t, apply:

    D_t |g> = zeta_9 ^ (f(c_t)*M(g)) |g>
    f(0)=0; f(1)=1; f(2)=-1
    U_t = X0 * X1^(t=1 mod 7) * D_t

M(g)=3 times the count of nontrivial plaquettes; the diagonal phase is gauge invariant. X0 shifts link zero by +1 each slot. X1 shifts link one by +1 only when t modulo 7 equals 1. For abelian Z3, these electric translations commute with all site gauge transformations. The circuit is exactly invertible using inverse order and inverse phase. The gauge-invariant electric coherence, the expectation of X0, is reported as a nine-bin histogram of ninth-root phases over the exact denominator 54.

Controls: Cantor, zero, sign-inverted, and one-slot-rotated input. Numerical approximations are unnecessary: this circuit is a signed-trit, ninth-root-of-unity, exact finite qutrit calculation. It is **not** exp(-i dt (E + r M)), nor a physical 27-second calibration.

## Separate finite S3 route

The existing [finite S3 Cantor integration](https://github.com/JesseBrown1980/Finite-universe-Yang-mills-existence-and-mass-gap-using-HEB-C/pull/61) applies numeric exp(-i dt H_t) to the genuine 211-state S3 gauge-invariant sector at r9/r243. S3 and its Z3 rotation subgroup are different gauge models; their spectral gaps cannot be equated by changing the basis label.

## Reproduce

    cargo +1.81.0 test --release --locked --test v3_gauge_boundary
    cargo +1.81.0 test --release --locked --bin cantor27_z3
    cargo +1.81.0 run --release --locked --bin cantor27_z3 -- results-v3/v3-z3-r9-star.gguf
    cargo +1.81.0 run --release --locked --bin cantor27_z3 -- results-v3/v3-z3-r9-identity.gguf

CI checks Rust 1.81, warnings, exact gates and model provenance. No V3 original preregistration/seal or existing Yang–Mills certificates are changed.

## Next research gate

Construct a truly gauge-commuting V3 variational ansatz, pre-register a trial-energy improvement over the V3 r9 value of 16.000, and replay it independently. Neither the finite circuit nor the current trained models establish fundamental spacetime discreteness, a uniform-volume Yang–Mills gap, or continuum existence.
