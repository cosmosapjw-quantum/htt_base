# Adversarial Research Audit Prompt: PR04 + LR-06 + PR07 Program

You are an external adversarial reviewer. Audit only the research content:
physics, mathematics, statistics, theorem hypotheses, estimator design, claim
tiers, and figure/measurement interpretation. Do not grade code style.

## Inputs

This archive only. Start from `docs/final_report/main.pdf`, then the proof
records, the theorem implementations, the gate tests, and the measurement
reports.

## Required output sections

1. `Verdict`: PASS | MINOR REVISIONS | MAJOR REVISIONS | REJECT / NOT READY.
2. `Theorem Audit`: per core (A-rank with full-column-rank qualifier, A-flrw,
   A-boost vs A-first-jet split, A-radial-novortex, A-shell-degeneracy,
   A-temporal-rank; B-nonsuff, B-psd, B-dust, B-shear; NT-A1 closure-conditional
   identity, NT-A3 estimator sampling variance, NT-B3 additive contrast) -- are
   the hypotheses complete and the symbolic claim correct (cross-check against
   `pr07_wolfram_proofs.json`)? Is the registered Bianchi-I branch stated? Was
   any forbidden token (EGS identity, cosmic-variance floor, CRLB, Wigner-angle,
   minimum-variance estimator) reintroduced? Table `Item | Status | Issue |
   Required Fix`.
3. `Estimator/Statistics Audit`: K1 null calibration + max-scan look-elsewhere;
   K4/K5/K6 bulk-flow + affine decomposition -- weighted-GLS (not minimum-variance)
   with conditional inverse-Fisher covariance, sigma_star nuisance, hierarchical
   random-effect coverage (`pr07_k5_*`), forward-mock coverage, K6 curl-suppression
   structural non-identifiability (`pr07_k6_*`), selection/Malmquist caveats. Are
   the synthetic mechanics correctly separated from observational claims?
4. `Independent-Verification Audit`: does the chain-rule dynamics verifier
   (`pr07_paper_b.json`) re-derive conservation/transport independently of the
   production RHS, and does the CoVe report (`pr07_cove_report.json`) terminate
   blocked lanes in registered blocker codes rather than substitute numbers?
5. `Claim-Tier Corrections`: exact wording to downgrade or remove.
6. `Blocked-Item Check`: confirm no scalar->family, no global-tilt-from-CF4, no
   MIO-as-odds, no native-solver inheritance, no radial-vorticity claim leaked.
7. `Claims That Are Safe`: bullet list allowed under current evidence.

## Hard boundaries (reject if used as a current result)

- an identified Bianchi family or detected anisotropic geometry;
- a global-tilt claim from CF4 distance data alone;
- native-solver validation for any external/proxy transfer output;
- a MIO diagnostic certificate used as a model-dependent inference input;
- a vorticity detection from a curl-suppressed reconstruction;
- a globally significant low-ell anomaly (K1 p-values are local, single-sky,
  look-elsewhere-tracked, not full-covariance/mask-coupled).

Cite `path:line` or a figure manifest path. Prefer concise tables.
