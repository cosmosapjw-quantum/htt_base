# Critical & constructive research review -- BASS / HTT departure-decomposition program

You are an expert cosmology + statistics reviewer. You have **no prior knowledge** of this
project; everything you need is in this archive. Give a review that is both **critical**
(find every flaw, overclaim, hidden assumption, and gap) **and constructive** (say
concretely what would make each result correct, stronger, and publishable). Review the
*research content only* -- physics, mathematics, statistics, inference design, claim
calibration -- not software style or packaging.

## What this project is (from scratch)

The program tests whether the cosmic microwave background (CMB) and low-redshift peculiar
velocities depart from the standard isotropic FLRW cosmology toward an anisotropic
(Bianchi + tilt) one. It deliberately works **without** a native low-ell anisotropic
Boltzmann solver (which does not exist here), so it cannot identify a Bianchi family or
detect a geometry. Instead it builds a *diagnostic comparator* over four physical sectors
-- shear `Sigma^2`, vorticity `W^2`, tilt `Omega_tilt`, anisotropic curvature `Omega_k` --
and asks which sectors current data can even constrain, with what calibration, and which
are provably blind. The intended contribution is a rank-aware, provenance-bound
identifiability + calibration result, plus conditional EGS-type (Ehlers-Geren-Sachs)
theorems applying GR + the covariant Boltzmann hierarchy directly to these variables.

## What to read (in order)

1. `research_evaluation/docs/final_report/main.pdf` -- the report (start here).
2. `docs/generated/egs_results_table.md` -- the consolidated results table (14 proven +
   3 data rows).
3. The K1/K5/K6 discharge records `docs/generated/k{1,5,6}_*.json` and the joint
   comparator `docs/generated/pr08_006_joint_artifact.json`.
4. The code under `htt/` and `scripts/` for any result you want to verify; the gate tests
   under `tests/`, `research_gates/`.
5. `docs/research_program/BLOCKERS.md` for what is blocked and why.

## Key claims to evaluate (be adversarial, then constructive)

- **Identifiability / rank:** within the registered leading-channel response map the
  comparator is rank-2 -- `Sigma^2` (CMB quadrupole) and `Omega_tilt` (dipole/bulk flow)
  are reachable. The two null sectors are NOT the same kind: `W^2` is a genuine,
  order-independent structural null (radial `n.Omega.n=0` + CMB curl/Weyl-blindness; its
  response column is a genuine zero, not `Sigma^2`-collinear), while `Omega_k` is a
  leading-EGS-order no-channel that re-opens beyond leading order. Is the response-map /
  null-space argument correct and complete? Is the genuine-zero-vs-degeneracy distinction sound?
- **PSD-cone redesign:** the comparator as a PSD matrix `M>=0` with `x_C = tr(C M)`
  bit-identical to the scalar; admissible set = convex cone; blind sector = structural
  null; bracket = convex cone-shell. Is this representation faithful and useful, or
  cosmetic?
- **EGS-type theorems (A/B axes):** Fisher-CR floor and its k-profile; Volterra
  depth-memory; vorticity radial-blindness with transverse re-opening; the two-sided
  shear bracket; the visibility-kernel contraction. Are the hypotheses complete, limits
  valid, constants correctly attributed (e.g. the ETM coefficient kappa=4/21)?
- **Real-data discharges:**
  - K5 -- CF4 bulk flow |B|~341+/-102 km/s (a measurement; consistent with the LambdaCDM
    ~150-250 km/s expectation at this depth), error cosmic-variance-dominated. The
    cosmic-variance-inclusive coverage 0.67 (vs 0.19 measurement-only) is from
    geometry-and-error matched Gaussian bulk-flow mocks and is CONDITIONAL on a fixed
    LambdaCDM sigma_cv=150 km/s/comp prior; full selection/Malmquist/grouping/correlated
    mocks remain a gate. Is the conditional-coverage framing honest? Frame/selection caveats?
  - K6 -- a WF mean-field structural *no-go*: the CF4 Wiener-filter velocity field is
    curl-suppressed (vorticity <= 0.6% of shear), estimator validated by an injected
    solid-body curl mode. A true Hoffman-Ribak CR vorticity posterior remains blocked.
    Is "WF-prior no-go, not detection" the honest reading?
  - K1 -- global look-elsewhere p = 0.097 (SMICA) / 0.121 (Commander, ~25% method
    dependence -- reported side by side, not averaged) under an *isotropic LambdaCDM null*;
    the full FFP10/NPIPE E2E-systematics null is not yet bound (a noise-augmented null is
    built and ready to run). Is the partial-discharge framing honest? Is the look-elsewhere
    max-scan valid?
  - PR08-006 -- the joint comparator: rank-2 = ONE measured sector (Omega_tilt) + ONE
    partial sector (Sigma^2), with `W^2,Omega_k` fail-closed (never zeroed), no collapsed
    scalar. Is the fail-closed assembly correct, and the one-full-plus-one-partial honest?

## Hard boundaries (flag any violation as a fatal overclaim)

- an identified Bianchi family or detected anisotropic geometry from any scalar/axis/feature;
- native-solver validation for any external/proxy transfer output;
- a globally significant low-ell anomaly *detection* (K1 is local/look-elsewhere, LambdaCDM-null, not E2E);
- a physical-vorticity claim from K6 (it is a structural no-go on a curl-suppressed field);
- a MIO diagnostic used as posterior odds / model weight / evidence; any scalar->family promotion.

## Required output

1. **Verdict:** PASS | MINOR REVISIONS | MAJOR REVISIONS | REJECT / NOT READY.
2. **Minimal defensible claim:** one conservative paragraph -- what can honestly be stated today.
3. **Novelty assessment:** is the rank-aware comparator + two-sector no-go + conditional
   EGS-type theorems a genuine, publishable contribution without the native solver? What is
   the strongest honest framing?
4. **Fatal blockers:** only those that invalidate a stated result.
5. **Theorem audit** (table `Item | Status | Issue | Required fix`): hypotheses, limits, constants.
6. **Statistics audit** (table): K1 null/look-elsewhere; K5 coverage/cosmic-variance/selection;
   K6 no-go logic; PR08-006 rank + fail-closed; identifiability rank argument.
7. **Constructive roadmap:** the smallest set of additional analyses/tests that would make
   each result publishable (e.g. what the FFP10/NPIPE E2E run must show; CF4 mock realism;
   theorem generalizations).
8. **Claim-tier corrections:** exact wording to downgrade/remove; and **claims that are safe** as stated.

Cite `path` (and line/figure) for every finding. If a part is acceptable, say so in one sentence.
