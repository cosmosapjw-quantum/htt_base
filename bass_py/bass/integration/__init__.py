"""bass/integration (LB-6) — end-to-end regression suite.

This subpackage holds the LB-6 integration tests that gate the
Lowell-Bianchi solver against Kolb-Turner thermal history, HyRec
recombination, Planck-2018 ``τ_reion``, CAMB Planck-2018 geometry,
and the Bianchi I shear-decay invariants.

No production code lives here — only ``test_*.py`` modules. The
``bass/integration`` package is discovered by pytest via the usual
auto-collection rules.

Reference
---------
``docs/lowell_bianchi/06_integration_tests_spec.md`` — full contract.
"""
