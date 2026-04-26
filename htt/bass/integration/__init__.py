"""bass/integration — solver integration test suite + Round-16 numerics modules.

Originally (LB-6) a test-only subpackage gating the Lowell-Bianchi
solver against Kolb-Turner thermal history, HyRec recombination,
Planck-2018 ``τ_reion``, CAMB Planck-2018 geometry, and the
Bianchi I shear-decay invariants.

Round-16 (PR-S2) extends this package with the production numerics
modules specified in ``docs/V5_ROUND16_04_NUMERICS_AND_RUNTIME.md``:

- :mod:`bass.integration.ark4_tableau` — frozen Kennedy-Carpenter
  ARK4(3)6L[2]SA Butcher tableau (verbatim from Kennedy-Carpenter 2003 /
  SUNDIALS ARKode reference).
- :mod:`bass.integration.imex_ark4` — :class:`IMEXARK4Integrator`
  additive Runge-Kutta stepper with embedded 3rd-order error estimator
  and non-identity mass-matrix support.

References
----------
- ``docs/lowell_bianchi/06_integration_tests_spec.md`` — LB-6 test contract.
- ``docs/V5_ROUND16_04_NUMERICS_AND_RUNTIME.md §1`` — IMEX-ARK4 spec.
- ``docs/IMEX_DECISION_2026-04-18.md`` — IMEX-ARK4 mainline rationale.
"""
