# HTT C8 finite-shell continuation, S2: theory → streamed algorithm → numerical falsifiers

Date 2026-10-16 KST. Source PR #536 HEAD `37db458319fd10e353a722345cb9a4ea6a39c698`. This is an additive pre-physical source-preserving continuation; existing `main`, the dirty owner checkout and PR #536 have not been modified.

## What was actually achieved

1. Source-bound original K6..16 archived blob SHA-256 `a9aaeb393deba03c97ecf45bf4e1ab74e98e3a8747de7c4bc7a96bff27014007` was independently read and three operator norms verified by NumPy SVD. It is real Planck *processing geometry* evidence from PR #536.
2. Derived source-condition-based upper bound for any selected-pixel ell17..32 finite operator, `||K||_2 <= κ(Y_L) sqrt(800)` from harmonic addition theorem and the presence of constant `Y_00`; under recorded κ=3.6013785311890616 it yields ≲101.86236724. This is not measured actual `K_17..32` and not a bound on actual sky contamination without high-mode amplitude.
3. Implemented SciPy-only per-shell real harmonic generator in exactly the upstream HTT convention (Condon-Shortley; `m0, sqrt(2)Re, sqrt(2)Im`); QR ordinary least squares for ell0..5; streamed ell6..16 and ell17..32 response matrices; masked fixed-direction injection. Only one shell of high harmonic sky pixels is ever materialized at once, not the full 800-column high design.
4. Implemented a separate `run_local_source.py` that reads the *same* full SMICA source-matched mask through PR #536's published helper, verifies the three 2048 native mask and the K1 cache SHA, verifies old K6..16 from scratch, and then computes actual new K17..32. It does not need to reread/rehash the 2 GB source temperature map, because this new objective is strictly geometry of an existing selected map, not a new map measurement.
5. Sandbox tests: **8 passed in 0.47 s**. Real spherical addition, Cartesian ell1 signs, streamed QR vs independent dense least squares, low reconstruction, random injection, PSD bound, strict source SHA, forged-source fail-closed, and invalid selection/range. The local-only entrypoint was syntax-compiled but not executed with original Planck masks, which are not present in the ChatGPT sandbox.

## Manufactured independent numerical experiments

Using deterministic, explicitly *non-HEALPix* Fibonacci-direction masks (`z>-0.8`, `x<0.75`), compare two finite blocks and their concatenation. These are algorithmic tests, not the real Planck observation:

| Full synthetic directions | Selected | low-design condition | norm K6..16 retained ell2..5 | norm K17..32 retained ell2..5 | norm K6..32 |
|--:|--:|--:|--:|--:|--:|
| 255 | 196 | 10.4283 | 8.60691 | 15.56572 | 17.7862 |
| 401 | 308 | 10.8316 | 8.12169 | 11.06905 | 13.7254 |
| 801 | 622 | 9.41716 | 6.77056 | 3.99881 | 7.84166 |
| 1601 | 1243 | 9.26792 | 6.59170 | 2.91297 | 7.1913 |

These results illustrate the necessity of an actual source-locked mask and harmonic resolution. Finite injected sky residuals were 2.22e-15 to 7.55e-15 in coefficient units. The changing sample grid means the table is NOT a rigorous convergence-rate demonstration on the Planck HEALPix source; the mask and sample geometry both change.

## New mathematical contract

For a fixed full-rank masked low matrix Y_L and two omitted, mutually distinct real harmonic column blocks H_a and H_b, define A = Y_L^+ H_a, B = Y_L^+ H_b. Then

    [A,B][A,B]^T = A A^T+B B^T,
    max(||A||_2,||B||_2) <= ||[A,B]||_2 <= hypot(||A||_2,||B||_2).

Wolfram symbolically checked the Gram identity. Numerically, on a *single manufactured mask* all bounds passed. This contract means one must combine old and new blocks on identical selected pixel support. Never concatenate source K6..16 with an unrelated synthetic K17..32 and call it a source result.

## Resource contract

- New ell17..32 has 800 columns; at actual 26,846 selected pixels a dense float64 `Y_high` alone needs about 163.9 MiB, excluding temporary arrays.
- Streamed ell32 largest block contains only 65 columns, about 13.3 MiB of float64 data, excluding intermediate arrays. The final 36x800 K matrix needs around 225 KiB.
- No physical L>32 remainder, actual high-mode coefficient norm, beam, component separation, foreground, E2E covariance, actual residual cosmological eps1, almost-EGS C1/C2 derivatives, or same-congruence Bianchi transfer are estimated.

## Next concrete input-dependent action

Run the published `code/run_local_source.py` **only after** placing this additive package in the existing `htt_base/docs/research_program/theory_obs_application_20261015/loop10_smica_ell17_32_sandbox/` directory. It will use the locally present source-locked PR #536 mask and K1 cache, refuse overwrite, validate exact K6..16 identity and compute the actual 36x800,12x800,32x800 ell17..32 operators. The user need not be asked to download files; the local Codex can fetch the text files from the new GitHub branch and reuse local existing source inputs.

If the hash gate fails or raw masks are not present, record the exact blocker and leave `C8-SMICA-ELL17-32-FINITE-TAIL` as LOCAL_SOURCE_RUN_REQUIRED. Do not upgrade physics claims. Native fresh independent review NOT_RUN in this ChatGPT context.

References: Hivon et al. 2002, ApJ 567, 2, doi:10.1086/338126; Gruetjen and Shellard 2014, PRD 89, 063008, doi:10.1103/PhysRevD.89.063008; Planck 2018 results IV, A&A 641 A4, doi:10.1051/0004-6361/201833881. These contextual references do not independently validate the custom finite-shell code.
