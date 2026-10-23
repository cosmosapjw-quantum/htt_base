# R23-DISTANCE — selected-cohort distance factor

**Owner:** HTT. **Tier:** C0 conditional diagnostic. **Transfer:** none. **Outcome:** `HOLD_MISSING_JOINT_DISTANCE_LAW`. This is a new numerical consumer of A22's retained cohort, not H02/S02 scientific admission.

## Assumptions and calculation

Condition on the actual 628 observed GBT targets, their outcome and distance-availability marks, and the released width/redshift fields. Let `o` distinguish accepted, other quality, confused, and nondetection; let `r` indicate an available released distance modulus. The working mark probabilities are the empirical 8-cell frequencies `pi_or=n_or/628`. For the 274 rows with `r=1`, a **supplied** source-qualified mean vector `m` and one positive-definite **total** covariance `C_total` define

`log L = sum_or n_or log(pi_or) - 1/2 [274 log(2*pi) + log det(C_total) + (DMbest-m)^T C_total^-1 (DMbest-m)]`.

The remaining 354 rows contribute their outcome/availability masses; their distance coordinates are integrated out and remain undefined. The covariance argument is used exactly once. A producer must state whether the reported `e_DMbest` statistical error already absorbs line-width uncertainty, and identify the shared calibration and peculiar-velocity contributions or a justified total covariance. The code does not add `e_logWmxi` to `e_DMbest`, invent a PV scatter, or interpret `Vcmb` as a true distance. Group labels are carried into the extraction, not assumed to specify a covariance. The joint factor is normalized for a positive-definite `C_total`; an outcome-dependent mean/covariance can be supplied as a vector/matrix across the 274 observed rows.

## Actual source extraction

`RELEASED_ROWS.csv` contains all 274 released `DMbest` and `e_DMbest` values joined by PGC to `logWmxi`, `e_logWmxi`, `Vcmb`, outcome, and the available CF4 group label. Source hashes are in `EXTRACTION.json`. The eight counts are `[[116,269],[21,1],[26,3],[191,1]]` in missing/present order, including the four confused/nondetection rows with a released modulus. The undefined mass is `354/628 = 0.5636942675`. Released moduli span 28.10–36.44 mag; statistical errors 0.11–1.26 mag; `logWmxi` 1.756–2.796. Five released rows have no group label, and five nonempty labels repeat. The old mark-only working log likelihood is `-834.3958584571346`; it is **not** a distance fit.

The [official CF4 TF catalog description](https://vizier.cds.unistra.fr/cgi-bin/VizieR-3?-source=J%2FApJ%2F902%2F145%2Ftable4) labels `e_DMbest` a statistical error. No 274-by-274 shared calibration/PV covariance was identified in the retained inputs from the [original catalog paper](https://arxiv.org/abs/2009.00733) and ReadMe. The repository's [source-bound conditional model](../../../FRONTIER_20261020/distance/CONDITIONAL_MODEL.md) describes an alternative latent TFR/flow construction, but its required selection, calibration and flow inputs have not been bound to these rows. This absence is a model/input question, not a numerical failure.

Two actual first-row errors, 0.29 and 0.30 mag, admit both `diag(e²)` and `0.5 diag(e²)+0.5 ee^T`; both have exactly the same marginal errors. For a residual `(0.29,0)` mag their Gaussian log densities are 0.103970093918 and 0.081144463477. Thus the released errors do not determine a joint likelihood or interval coverage. A diagonal 274-row fit would make a new independence assumption. No bounded physical sensitivity range is supported by these inputs, so none is reported.

## Numerical checks and claim audit

The 1D factor integrated to 1 within `1e-10`. A constructed 8-group, four-member-per-group covariance included one common calibration and one group term. A 90% GLS interval covered its true common offset in `3724/4096 = 0.90918` whole-group draws. This checks the code path under its own declared mock law; it is not selected-survey coverage. Three focused tests pass. The first run failed only an overstrict infinite-domain quadrature error-estimate bound (`2.634e-10` while the integral was exactly 1 to displayed precision); the integration was changed to ±8 Gaussian standard deviations, with omitted tail below `1.3e-15`, and the same normalization tolerance passed. The first failure is retained in `RAW_RECEIPT.json`.

**Claim audit:** The factor is `IMPLEMENTED` and toy-checked. The actual selected-cohort distance fit, its source-specific interval coverage, physical selection law, bounded sensitivity law, and H02/S02 admission are `NOT_EVALUABLE` or `HOLD`. This calculation supports no MIO inference, native transfer, Bianchi family classification, or physical distance/velocity inference.

## Exact next model question

For these 274 released targets, what source-qualified conditional law gives `p(DMbest_274 | selected 628 marks, released widths/errors, redshifts, shared calibration, group/PV state)`? It must specify a mean or latent-distance construction, selection-conditioned normalization, a proper joint calibration/PV law or total covariance, whether and where the released modulus and width errors enter, and the genealogy of repeated groups/calibrators. If the proposed law also predicts the 354 missing moduli, it must supply the outcome/confusion/nondetection and distance-missingness mechanism. Then fit the actual rows and check coverage by resampling whole selected groups under that law. The 5460-target parent inclusion law cannot be learned from the retained 628 alone.

No original physical acceptance, paper gate, or source publication state is changed here. An independent reviewer who did not author this candidate must inspect it before any scoped admission.
