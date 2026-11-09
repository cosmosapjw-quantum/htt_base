# R48 — Tensorized physical-state likelihood and observational convergence

Date: 2026-11-09 (Asia/Seoul)  
Parent: aae07cb83b8899dd7495d550722068d8bcbf3bcb (R47 / PR #571)  
Branch: research/r48-tensorized-observational-convergence-20261109  
Status: research plan and restart contract. This authoring session did not download local data, run production Cobaya chains, or patch local runtime code.

## Decision

- Empirical discovery paper: **HOLD**.
- Methods paper: **conditional candidate**.
- Internal theory: several scoped derivations survive internal review; they are not observational evidence.
- First empirical target: source-bound, temperature-only low-ell likelihood plus one independent redshift-resolved tracer. Do not begin with an opaque 17-parameter five-probe production run.

## Candidate contribution

The HTT object T=(x,Q,Pi,F,G_F) is a correlated push-forward of one physical-state posterior, not five independent likelihood variables. The candidate novelty is a **frame-, epoch-, source- and observation-operator-aware joint posterior over tensor kinematics, followed by target-specific information-certified HTT readouts and calibrated adversarial comparison with established inference methods**.

This is a hypothesis, not a first-ever claim. BipoSH, multipole vectors, covariant directional cosmography, local-boost/intrinsic-dipole separation and score/nuisance-hardened compression all have substantial prior art.

## Primary documents

- Publication assessment: PUBLICATION_ASSESSMENT_KO.md
- Research DAG: RESEARCH_DAG.json
- Joint likelihood contract: OBSERVATION_LIKELIHOOD_SPEC.json
- Data intake manifest: DATASET_INTAKE_MANIFEST.json
- Historical source and contradiction ledger: SOURCE_REUSE_AND_CONTRADICTION_LEDGER.json
- Mutation and anti-drift gates: MUTATION_GATE_CONTRACT.json
- Local-agent restart prompt: LOCAL_AGENT_RESTART_PROMPT_KO.md


## Bianchi geometry-only review follow-up (2026-11-09)

A bounded geometry-only branch extension is recorded in:
- Hypothetical independent referee report: INDEPENDENT_GEOMETRY_REVIEW_KO.md
- Claim-by-claim evidence ledger: GEOMETRY_CLAIM_LEDGER.json
- Updated novelty assessment: BIANCHI_NOVELTY_AND_SIGNIFICANCE_ASSESSMENT_KO.md

The referee verdict is **MAJOR REVISION / NOVELTY HOLD**. Ferrando–Sáez (2020, 2024) and a 2026 unreviewed Clifford-algebraic author preprint create substantial overlap risk for broad Bianchi-geometry novelty. The defensible scope is restricted to a reproducible BASS geometry-only diagnostic and rank-stratified normal-frame tilt identifiability. Jacobi/domain guards and a dedicated Python 3.10–3.13 test workflow have been added; targeted CI is pending. The previous broad PR04 gate still has an unrelated optional-dependency collection failure (Cobaya/Astropy), so it is not reported as PASS.

## Resume

Start with R48-T1 only. Each later loop is a separate bounded work session. Do not launch production sampling before the physical response, observation operator, source-byte identity, likelihood oracle and synthetic calibration gates pass.


## R48-T1 result (2026-11-09)

R48-T1 is PASS_SCOPED for remote static source reconciliation. The current R42 implementation still contains response defaults, cached-chain diagnostic fallbacks, a synthetic-null/matched-null naming conflict, an unverified G_F transport placeholder, and cross-probe covariance/parameter-dimension limitations. The earlier "R42 Stage B repaired" status is not accepted as a blanket implementation or empirical pass.

Cobaya-independent paths and numerical evidence are documented in HISTORICAL_SOURCE_MATRIX.json, PHYSICAL_STATE_FRAME_EPOCH_CONTRACT.md, R42_CONTRADICTION_REPLAY_PLAN.md, COBAYA_FREE_ANALYSIS_PATHS.md and R48_T1_SOURCE_AUDIT_REPORT.md.

The 40,000-draw R46 target-compression replication and independent Bianchi-I small-amplitude quadrature are synthetic/theory checks only. Empirical discovery remains HOLD. Local tests, observed-data inference, native transfer and independent review were not run. The next DAG task is R48-T2 after exact-head local validation.


## R48-T2 scoped theory/oracle result (2026-11-09)

The Bianchi-I collisionless temperature map is now derived with explicit c bookkeeping from conserved spatial momenta. An independent deterministic oracle checked the exact positive map, antipodal parity, SO(3) covariance, eigenvalue permutation, stored-real harmonic/STF consistency, quadrature convergence, the \(Q(B_\star)=B_\star+O(B_\star^2)\) limit, and the angular monopole through cubic order:
\[
\langle T_0/\bar T_0-1\rangle=-2\,\mathrm{tr}(B_\star^2)/15+4\,\mathrm{tr}(B_\star^3)/315+O(\|B_\star\|^4).
\]
The finite-amplitude map generates higher even multipoles but no odd ones. The target remains \(B_\star\), not \(\sigma(t_0)\).

R48-T2 remains PENDING: repository implementation/tests and the source-matched beam/mask/pixel/noise/foreground/transfer covariance are not yet available. This theory/oracle work is Cobaya-independent and does not create an observational likelihood.


## R48 geometry-only all-Bianchi tilt similarity extension (2026-11-09)

The active scope is now limited to all eleven Bianchi algebra types and the relative tilt orbit of a matter congruence with respect to the homogeneous-slice normal. It does not extend the Bianchi-I temperature map into an all-type Boltzmann program.

A pure-NumPy diagnostic module and tests have been added under htt/bass/diagnostics. The method separates (i) the Bianchi group-action label from (a,n), (ii) intrinsic 3D Ricci curvature, and (iii) the SO(3)-orbit of normal-frame matter tilt. Two exact curvature-only no-go examples are encoded: the flat I/VII_0 representative pair and the constant-negative-curvature V/special-VII_h pair. The Class-A/B tilt invariants expose rank and repeated-eigenvalue azimuth degeneracies.

A standalone canonical-fixture oracle passed 35 tests and 1,100 randomized SO(3)/positive-homothety cases. Exact repository import/pytest remains NOT_RUN and is the next local-agent task. Novelty priority is provisional pending an adversarial review of metric-Lie-algebra equivalence and invariant theory.

Scope firewall: no Boltzmann solver, LOS, CMB Cl/polarization, Cobaya/MCMC, observational family claim, or all-type constraint-satisfying tilted-fluid claim.


## Targeted Bianchi CI receipt and next task (2026-11-09)

The dedicated Bianchi workflow passed all four Python interpreters at exact HEAD effb46279cbc69138c9e72503a1a86a35013ed4e: 49 tests per version plus compileall. See `BIANCHI_TARGETED_CI_REPORT.json`. The separate PR04 broad fast-regression remains failed at collection because optional Cobaya (four modules) and Astropy (three modules) dependencies are unavailable. DAG next task is R48-T21: prove the constrained tilt-orbit stabilizers and O(3) transformations.
