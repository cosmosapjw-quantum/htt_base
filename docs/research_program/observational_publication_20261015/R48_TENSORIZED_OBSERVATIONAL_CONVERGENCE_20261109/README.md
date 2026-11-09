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

## Resume

Start with R48-T1 only. Each later loop is a separate bounded work session. Do not launch production sampling before the physical response, observation operator, source-byte identity, likelihood oracle and synthetic calibration gates pass.


## R48-T1 result (2026-11-09)

R48-T1 is PASS_SCOPED for remote static source reconciliation. The current R42 implementation still contains response defaults, cached-chain diagnostic fallbacks, a synthetic-null/matched-null naming conflict, an unverified G_F transport placeholder, and cross-probe covariance/parameter-dimension limitations. The earlier "R42 Stage B repaired" status is not accepted as a blanket implementation or empirical pass.

Cobaya-independent paths and numerical evidence are documented in HISTORICAL_SOURCE_MATRIX.json, PHYSICAL_STATE_FRAME_EPOCH_CONTRACT.md, R42_CONTRADICTION_REPLAY_PLAN.md, COBAYA_FREE_ANALYSIS_PATHS.md and R48_T1_SOURCE_AUDIT_REPORT.md.

The 40,000-draw R46 target-compression replication and independent Bianchi-I small-amplitude quadrature are synthetic/theory checks only. Empirical discovery remains HOLD. Local tests, observed-data inference, native transfer and independent review were not run. The next DAG task is R48-T2 after exact-head local validation.
