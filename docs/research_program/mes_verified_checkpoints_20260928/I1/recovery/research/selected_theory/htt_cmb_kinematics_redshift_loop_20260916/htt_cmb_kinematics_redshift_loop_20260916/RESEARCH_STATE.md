# HTT PAPER-A research loop — CMB/STF ↔ kinematics + redshift-dependent observables
Date: 2026-09-16
Mode: analytic / literature / symbolic validation
Production mutation: NO
Repository: cosmosapjw-quantum/htt_base
Repository reference inspected: 50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb

## Scope
This loop is restricted to two questions:

1. What is the physically correct and statistically usable mapping between CMB/radiation STF multipoles and the congruence kinematics
   theta, sigma_ab, omega_a, A_a?
2. Which redshift-dependent observables can provide independent response kernels, and under what conditions do they improve identifiability?

No new real-data inference, Planck fit, Bianchi-family attribution, or native-solver claim is made.

## Conventions
- Metric signature: (-,+,+,+).
- u^a u_a = -1.
- h_ab = g_ab + u_a u_b.
- Congruence decomposition:
  ∇_a u_b = -u_a A_b + (theta/3) h_ab + sigma_ab + omega_ab.
- Outward sky direction n^a is opposite to photon propagation direction e^a:
  n^a = -e^a.
- Unless otherwise stated, all local identities are proper-time identities.

## Evidence-state vocabulary
ESTABLISHED: standard result in primary literature.
LITERATURE-SUPPORTED: source-backed but not independently rederived in full here.
DERIVED: explicitly derived in this loop.
WOLFRAM-EXACT: checked algebraically/symbolically with exact arithmetic.
IMPLEMENTATION-VERIFIED: source code path inspected and consistent with the stated formula.
CONJECTURAL: plausible research direction without proof.
UNRESOLVED: incomplete literature/novelty or physics binding.
BLOCKED: prevented by a concrete external requirement.

## Harness
Loaded GPT-6 Astra physmath research harness v4.0.0 from Library.
SHA-256:
dae76c90f2e5d691bcdd595dadbe470bacacba3bb2a036ff9788ffe7d3bfabb7

The harness requires independent decision review for final PROMOTE.
No independent final decision reviewer is available in this turn.
Final promotion state therefore remains HOLD / INDEPENDENT_REVIEW_UNAVAILABLE.
