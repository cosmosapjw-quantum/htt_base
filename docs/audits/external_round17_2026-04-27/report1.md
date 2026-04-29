• 1. Claim Reconstruction
     | Claim | Tag |
     |---|---|
     | 1+3 PSTF/tetrad low-ell solver | partially implemented |
     | 11 Bianchi family support | registry/interface + proxy support |
     | orthogonal + globally tilted backgrounds | partially implemented |
     | local boost separated from solver | clearly implemented at output/likelihood boundary |
     | exact transport Tier A | overclaimed; current facade delegates/no-op numerically |
     | low-ell projected hierarchy Tier B | clearly output-producing, with caveats |
     | exact electron-frame Thomson | partially implemented; not full exact tilted authority |
     | family-specific spatial backends | weakly evidenced outside Type I |
     | family-specific IC provenance | mixed; strong for some, template/proxy for others |
     | deterministic/stochastic/boost split | implemented in archive, often zero-filled |
     | harmonic-level outputs | implemented |
     | T,Q,U map outputs | optional helper exists, not default runtime output |
     | validation gate before fitting | enforced in live inference path, not globally |
     | covariance-aware statistics | shell exists; full readiness usually blocked |
     | optimization/performance claims | useful but weakly controlled |
     | production cutoff support | gate exists, evidence weak/default low cutoff |
     | neutrino hierarchy | evolved/exported, not clearly coupled to final observables |
     | polarization B-mode fidelity | conditional/flagged; zero/proxy risk remains |

  Solver-ready: Type-I-centered native Tier-B low-ell harmonic pipeline.
  Output-ready: a_lm^{T,E,B} with metadata/gates; optional map producer via populate_map_outputs.
  Statistics-ready: only gated diagnostic/live paths with full covariance; not general data fitting.
  Development-only/interface-level: exact transport Tier A, broad non-I perturbation/output physics, full tilted Thomson, full anisotropic covariance.

  2. Executable Pipeline Reconstruction
     Actual main path is execute_tier_b_solver → prepare background/visibility/backend → Ver2TierBIntegrator.run() → SolverCoreOutput: htt/bass/runtime/ver2_execution.py:1961,
     htt/bass/runtime/ver2_execution.py:1201, htt/bass/runtime/ver2_execution.py:404. Family selection and all-11 registry are real in TYPE_REGISTRY/ALL_BIANCHI_TYPES, but non-I
     LOS kernels mostly wrap Lowell/legacy paths: htt/bass/los/families/base.py:5, htt/bass/transport/exact_transport.py:3. Background init uses Bianchi algebra/IC projection and
     constraint residuals, but some gates are finiteness/contract gates rather than physical residual gates. Perturbation ICs in runtime are largely FLRW regular seed plus tilt
     promotion. Visibility/TCA/hierarchy are connected. Statistics go through observable/likelihood/live-binding; fitting hard stop is in htt/bass/validation/ver3_gate_stop.py:260
     and live inference htt/bass/inference/live_binding.py:213.
  3. Physics Implementation Audit
     Steelman: the code is not empty scaffolding. It has real PSTF/tetrad data structures, native Tier-B T/E/B/neutrino towers, visibility, TCA, source propagation, harmonic
     output, and gate metadata.

  Strongest objection: multiple “authority” surfaces are contract/proxy/skeleton layers; the exact tilted collision/transport and all-family perturbation claims are not closed.

  Classification:

  - PSTF/tetrad formalism: implemented structurally; not fully validated as exact production formalism.
  - Tetrad/invariant algebra: used in geometry/backend layout, but non-I operator blocks retain placeholders such as identity transport and Type-I-compatible mass/drag terms: htt/
    bass/hierarchy/ver3_layout_protocol.py:597.
  - Background: IC projection is strong; full Einstein-matter propagation is not. Older solve_bianchi_background keeps FLRW-like H while evolving shear.
  - Collision: projected Thomson path is live, but tilted opacity likely double-applies boost and kappa() has propagation-sign risk.
  - Polarization: E path live; B output flagged/conditional, with zero/proxy risk.
  - Neutrinos: co-evolved/exported, not proven to backreact into final source observables.
  - TCA/visibility: connected and useful, but interpolation/sign/tilt details need hard validation.
  - Mode mixing: partial; generic mix scale is suppressed/placeholder in places.
  - Cutoff maturity: development and production cutoffs are distinguished, but default evidence uses L=4,6 and loose cutoff tolerance.

  4. Family / Tilt / Boost Coverage Audit
     Family matrix summary: all 11 have registry/background/IC/backend-contract coverage. Type I is strongest. V, VII_0, VII_h, IX have stronger FLRW-limit/IC provenance. II, III,
     IV, VI_0, VI_h, VIII are mostly template/proxy outside background/registry. Non-I perturbation/output/statistics are limited/proxy/diagnostic.

  Global tilt exists in background/visibility state. Local boost is correctly output-only and separated in metadata/archive/observer likelihood. The separation is real; the
  physical tilted Thomson path is not yet trustworthy enough for strong tilted polarization claims.

  5. Observables / Statistics Readiness
     a_lm^{T,E,B} is the real primary product. Deterministic/stochastic/boost archive split exists, but stochastic and boost are zero-filled unless caller supplies them: htt/bass/
     forward/ver3_output_archive.py:277. T,Q,U maps now have an optional Healpy producer: htt/bass/forward/map_producer.py:228, but default native builders still emit harmonic
     outputs and mark maps as not attached: htt/bass/forward/ver2_solver_output.py:396. Fitting gate is real in live inference, but direct likelihood/surrogate paths can compute
     diagnostics without that hard stop. No broad Planck/data fitting claim is allowed.
  6. Numerical Maturity Audit
     Verdict: stable in a narrow/exploratory regime, not publication-grade numerics. BDF/Radau/RK/IMEX exist; nonfinite outputs are guarded. But η-grid mismatch risk, endpoint-
     clamped interpolation, IMEX orthogonal path without real error estimator, H floors, natural cubic visibility overshoot risk, and residuals recorded rather than enforced block
     a strong maturity claim. Cutoff convergence evidence is too weak for production.
  7. Optimization / Performance Honesty Audit
     Honest pieces: sparse/dense caches, layout caches, parallel-vs-sequential identity tests, and some fairness tests exist: htt/bass/runtime/test_optimization_fairness.py:1.
     Weak pieces: fairness is mostly FLRW/small-L/smoke-level; reduced cutoff evidence uses loose defaults; runtime control tolerances appear at risk of being bypassed in native
     config; no broad same-physics/same-tolerance/same-observable benchmark covers tilted/non-I/exact collision cases. Verdict: useful but weakly controlled.
  8. Docs / Tests / Release Honesty Audit
     Tests are abundant, but many are smoke, skeleton, contract, registry, or proxy tests. Stronger tests exist for algebra, IC projection, visibility, Type-I runtime, output
     split, and gate surfaces. Docs sometimes overstate “production/exact/all-11” relative to code. The best release label is “serious exploratory low-ell Tier-B harmonic solver
     with guarded outputs,” not “journal-grade all-family Einstein-Boltzmann solver.”
  9. CoVe / Contrastive Verification Results
     Key verification questions answered:
  10. Does code produce real harmonic output? Yes.
  11. Does it produce default T,Q,U maps? No; optional helper only.
  12. Are all 11 families genuinely solved? No; registry/contract broad, physics uneven.
  13. Is Type I strongest? Yes.
  14. Is global tilt equal to local boost? No; separation is real.
  15. Is tilted Thomson exact enough? No.
  16. Is exact Tier A real production numerics? No.
  17. Is fitting hard-gated? Yes only in live binding/CLI path.
  18. Is covariance full? Usually no/proxy.
  19. Are neutrinos fully coupled to final observables? Not established.
  20. Are production cutoffs mature? No.
  21. Are optimizations proven same-physics broadly? No.

  H1 is too generous. H3 is too dismissive because the native Tier-B path is real. Best-supported interpretation: H2 — strong exploratory solver, with major revision needed in
  family coverage, tilted collision, validation gates, observables/statistics, and optimization fairness.

  10. Ranked Risk Ledger
     P0: tilted collision opacity/sign bug; exact tilted Thomson overclaim; non-I family overclaim; fitting/data-comparison overclaim.
     P1: background constraint gates too weak; η-grid mismatch; residuals not enforced; production cutoff evidence weak.
     P2: B-mode/proxy confusion; optional maps mistaken as default; neutrino backreaction not closed; optimization fairness too narrow.
     P3: stale docs, skeleton test names, metadata claiming broader scope than evidence.
  11. Top 12 Load-Bearing Risks
  12. Tilt boost factor possibly applied twice in collision.
  13. Tilted visibility kappa() sign convention inconsistency.
  14. “Exact transport” facade delegates to Lowell.
  15. Non-I backends are proxy/delegation rather than native family solvers.
  16. Background gate can pass finite but constraint-violating states.
  17. Bianchi/conservation residual can be tautological.
  18. Runtime perturbation ICs are not truly family-specific.
  19. Neutrino sector exported more than physically coupled.
  20. IMEX orthogonal path lacks adaptive error control.
  21. Cutoff campaign defaults are low and loose.
  22. Full covariance/statistics readiness is mostly unavailable.
  23. Optimization benchmarks do not span same-physics tilted/non-I authority paths.
  24. Minimal Patch / Optimization Plan
  25. Make exact Thomson authority path default or fail closed. Blocks shortcut collision. Required for solver/output/statistics/publication.
  26. Fix tilted opacity double-count and kappa() sign. Blocks wrong tilted physics. Required for tilted claims.
  27. Enforce background Gauss/Codazzi/Bianchi thresholds in gates. Blocks false green gates. Required for solver-ready.
  28. Replace tautological conservation residual with independent residual history. Required for background publication claims.
  29. Add η-grid identity/range checks and no endpoint-clamp mode. Required for numerical maturity.
  30. Add residual magnitude hard stops in runtime. Required for output-ready.
  31. Upgrade cutoff campaign to production L set with strict convergence. Required before publication.
  32. Mark non-I outputs as proxy unless native family kernel used. Required for release honesty.
  33. Add family-specific IC provenance assertions in runtime. Required for broad family claims.
  34. Add harmonic a_lm validator versus deterministic/stochastic/boost split. Required for output/statistics readiness.
  35. Route all fitting APIs through hard gate or label direct likelihood diagnostic-only. Required before data fitting.
  36. Extend optimization fairness to same equations/tolerances/outputs for Type I tilted and representative non-I proxy/native cases. Required for optimized claim.
  37. Final Verdict
     A. Physics implementation: partially implemented; strongly implemented in narrow Tier-B pieces with caveats.
     B. Family coverage: broad registry/contract, partial genuine implementation.
     C. Observables/statistics: harmonic output-ready; not full statistics-ready.
     D. Numerical maturity: narrow stable regime, not publication-grade.
     E. Optimization: useful but weakly controlled.
     F. Overall code verdict: strong exploratory solver with major revision needed.
  38. Headline Claims Allowed / Not Allowed
     Allowed:

  - “Native low-ell Tier-B harmonic Bianchi solver path exists for Type-I-centered workflows.”
  - “All 11 Bianchi families are represented in registry/backend contracts.”
  - “Observer local boost is separated from global tilt at output/likelihood boundary.”
  - “a_lm output and deterministic/stochastic/boost archive schema exist.”
  - “Live inference path includes a fitting hard gate.”

  Not allowed:

  - “Genuine 11-family Einstein-Boltzmann solver.”
  - “Exact tilted electron-frame Thomson polarization solver.”
  - “Statistics-ready Planck/data fitting package.”
  - “Full T,Q,U map production as default solver output.”
  - “Publication-grade numerical convergence/optimization across families.”
  - “C_l agreement alone validates harmonic/template fidelity.”

  Safe for papers: architecture, Type-I/limited low-ell harmonic demonstrations, validation-gated output schema, explicit caveats.
  Must remain internal/dev: non-I exact physics, tilted polarization claims, full likelihood/data fitting, performance speedups beyond narrow same-physics tests.
  Hard-gate before fitting: exact Thomson, tilt/boost split, family backend exactness, background residuals, IC provenance, cutoff convergence, full covariance.

  15. One-Line Reason
     This is a serious, code-backed exploratory low-ell Bianchi framework, but its broad family, exact tilted collision, statistics-ready, and optimization claims currently outrun
     the executable physics evidence.