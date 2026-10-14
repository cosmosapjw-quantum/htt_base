# CAS07 conditional synthesis candidate

Owner: htt; transfer_source: none; scope: supplied Euclidean Jacobi system and supplied C² scalar; scientific_admission: HOLD. New validation plan, not historical four-axis adjudication. No C01 dependency or physical existence assertion.

| Obligation | Inputs / reused theorem | Responsible role / tool | New verification / completion |
|---|---|---|---|
| Whole-interval Jacobi bounds | Exact M04 regularity via M05.JacobiPremises; M03 → M04.d_norm/d_minus_si | Analysis author / Lean integration | Accepted interfaces bound to published source and compile synthesis |
| Euclidean matrix conversion, determinant, distance, denominators | M01.eta_bounds, M05.c02_premise/determinant_distance_bridge, C02.CAS_07_C02_full | Analysis author / Lean | Derive signs, not assumptions |
| Scalar remainder | Exact M02 HasDerivAt witnesses on Icc; remainder_bound_physical; Z0=Z(0), H0=c Z1(0) | Analysis author / Lean | Construct C03.Premises from scalar/Jacobi inputs |
| FD1–FD3, refined t bounds | C03.FD1/FD2/FD3; M06.t_domain/eta_order/refined_fd1/no_worse_than_fd2 | Formal integration author / Lean | All conclusions in one universally quantified theorem; axiom print |
| Boundary separation | K=0, H0=0, M2=0, both min branches; s=0 only un-divided bounds | Boundary author / Lean and symbolic reasoning | No eta/distance denominator at s=0; etaL=1 excluded |
| Independent review | Statement/dependencies first, then final source/logs/failures | New read-only reviewer requested gpt-6-astra / ultra (planned request; not dispatched) | Fresh independent review in progress; exact source binding and scoped closeout required |

Current continuation: the separate reviewer is now dispatched in fresh context with requested gpt-6-astra / ultra. Actual matching session/turn metadata records gpt-6-astra / ultra (session 01a11b79-afc0-7282-932e-7fbb7c9777e6, turn 01a11b79-b00b-73c1-a4f5-52e21579b870). Historical source author and build are reused unchanged; no new author execution is represented as independent rediscovery. The old registration block in the prior RETURN describes the previous session only. The current developer guidance explicitly permits native execution without removed CUH-G components.
