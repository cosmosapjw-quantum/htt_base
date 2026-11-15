# HTT R49: General tilted-Bianchi convergence

Date: 2026-11-12 (Asia/Seoul)  
Repository: cosmosapjw-quantum/htt_base  
Status: design and source audit posted; local implementation and observed-data sampling not run  
Claim ceiling: C0 / conditional design

This R49 continuation extends the R48 six-loop observational programme from a Bianchi-I-centred physical transfer path to a general tilted-Bianchi programme. It is a successor package; R48 artefacts remain immutable historical inputs.

## Read in this order

1. R49_GENERAL_TILTED_BIANCHI_KO.md — scientific state, equations, novelty boundary, observational design, and publication assessment.
2. R49_DAG.json — machine-readable execution DAG, dependencies, acceptance tests, source lanes, and mutation gates.
3. R49_OBSERVATION_CONTRACT.json — typed physical state, frame semantics, source/operator schema, likelihood contract, data lanes, and fail-closed rules.
4. R49_CLAIM_LEDGER.json — evidence status by scientific claim.
5. LOCAL_AGENT_RESTART_PROMPT_KO.md — copy-ready implementation and analysis handoff for a local coding agent.

## Immutable parent evidence

- R48 integrated package branch: research/htt-six-loop-core00-20261109
- Parent package head: 1b8abb1399f9f80b8e69bd57c2cc1592e2d1bcd4
- Parent draft PR: #573
- Companion code-repair draft PR: #574, head 8a6ae269751a8a6878eaf9e1192c28fe1c067523
- R48 DAG: HTT_SIX_LOOP_INTEGRATED_20261109/INTEGRATED_SIX_LOOP_DAG.json
- R48 physical contract audit: HTT_SIX_LOOP_INTEGRATED_20261109/PHYSICAL_STATE_CONTRACT_AUDIT.json
- General Bianchi algebra: htt/bass/background/bianchi_types.py
- General Bianchi background: htt/bass/background/einstein_bianchi.py
- Reduced-family non-perturbative tilt RHS: htt/bass/background/nonperturbative_tilt.py
- Codazzi-gated reduced tilt evolution: htt/bass/background/codazzi_tilt_rhs.py
- Bianchi-I photon hierarchy: htt/bass/transport/bianchi_i_hierarchy.py

## Important scope rule

R49 does not claim that general tilted Bianchi dynamics, a native all-family CMB solver, or an observed all-family posterior already exists. It defines the exact next implementation and validation path. The local agent is responsible for local source inspection, code repair, test execution, real-data replay and Cobaya sampling; GitHub-only work in this turn did not execute those local operations.

## Main scientific contribution candidate

The proposed contribution is not the rediscovery of tilted-Bianchi field equations. It is a source-conditioned, frame-covariant, tensor-valued multi-probe inference and partial-identification framework that preserves:
- the homogeneous-orbit normal versus each tilted matter/radiation congruence versus the local observer frame;
- the complete Bianchi Class-A/Class-B algebra and type-dependent constraint fibres;
- vector/tensor kinematic state, parity, units, triad and epoch identity;
- deterministic CMB morphology and stochastic harmonic covariance as one generative law;
- the joint HTT five-view push-forward (x,Q,Pi,F,G_F) from one common posterior/compatibility law;
- uncertainty about the Bianchi group action itself when different actions induce the same local geometry or observational law.

This contribution remains conditional until implementation, source-bound observational inference, calibrated adversarial benchmarks and independent review are completed.
