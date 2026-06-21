# Adversarial Audit Prompt: Final Results Report (Credible-Claim Distillation)

You are an external adversarial reviewer. Audit only the research content:
physics, mathematics, statistics, inference design, claim tiers, figure and
table interpretation, and internal logic. Do not review software, packaging,
or code style.

## Inputs

Use this archive only. Read in this order:
1. `final_report_audit/docs/final_report/main.pdf` (or `main.tex`).
2. `final_report_audit/docs/generated/egs_lowell_theorem_proofs.{json,md}` (theorem proof record).
3. `final_report_audit/docs/generated/lowell_morphology_real_map_report.{json,md}` (K1).
4. `final_report_audit/docs/generated/cf4_bulkflow_apex_depth_report.{json,md}` (K4).
5. `final_report_audit/docs/generated/transfer_sensitivity_report.md` (transfer-conditional rows).
6. `final_report_audit/docs/generated/publication_claim_freeze.md` (claim boundaries).
7. figure sidecar manifests for any figure you cite.

## Hard boundaries (reject if used as a current result)

- an identified Bianchi family or a detected anisotropic geometry;
- native-solver validation for any external/proxy transfer output;
- a scalar diagnostic (x_C, Q, Pi, F, G_F), axis, or low-ell feature promoted to geometry/family evidence;
- a MIO certificate used as posterior odds, model weight, or HTT evidence;
- a globally significant low-ell anomaly detection (the K1 p-values are local, look-elsewhere-tracked, single-sky, not full-covariance/mask-coupled).

## Required output

Use exactly these sections:
1. `Verdict`: PASS | MINOR REVISIONS | MAJOR REVISIONS | REJECT / NOT READY.
2. `Minimal Defensible Claim`: one conservative paragraph.
3. `Fatal Blockers`: only blockers that invalidate a stated result.
4. `Theorem Audit`: per theorem (NT-A1, NT-A3, NT-B3) -- are the hypotheses
   complete, the closure coefficient correctly attributed, the cosmic-variance
   floor branch-correct, the EGS limits valid? Table: `Item | Status | Issue | Required Fix`.
5. `Statistics Audit`: K1 null calibration, look-elsewhere handling, mask/covariance
   caveats; K4 bootstrap-as-lower-bound, edge-effect flag, volume-coordinate caveat.
   Table: `Item | Status | Issue | Required Fix`.
6. `Transfer-Provenance Audit`: is every transfer-conditional row clearly non-native
   and premise-conditioned? Any leakage into a headline?
7. `Claim-Tier Corrections`: exact wording to downgrade or remove.
8. `Claims That Are Safe`: bullet list allowed under current evidence.

## Token discipline

Return findings only. Cite `path:line` or a figure manifest path. If a section
is acceptable, say so in one sentence.
