# Transfer Provenance Review

Review transfer provenance and downstream report-card status.

Required checks:

- Every transfer-dependent row has an explicit transfer source and transfer id.
- External and empirical-proxy paths remain transfer-conditional.
- Future native rows are schema-only until external solver artifacts and gates
  exist.
- Family labels in transfer metadata are provenance labels only.
- MIO budget, Q, F, Pi, and G_F rows preserve section-specific provenance.

Return any row that lacks transfer source, calibration status, input-domain
metadata, caveats, or owner separation.
