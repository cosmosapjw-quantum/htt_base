# R98: exact 60-node execution preparation

R78 authority is unchanged. DATA / MODEL / ADDITIONAL_ANALYSIS apply to each obligation, not mutually exclusive node labels.

| ID | Topic | Original state | Direct blockers | Inherited blockers | Preparation |
|---|---|---|---|---|---|
| E0 | COMMON | completed_scoped | — | — | CROSS |
| E1 | COMMON | completed_scoped | — | — | CF4 |
| E2 | COMMON | completed_scoped | — | — | CMB_CACHE |
| E3 | COMMON | completed_scoped | — | — | CF4 |
| X01 | COMMON | completed_scoped | — | — | CROSS |
| X02 | COMMON | completed_scoped | — | — | CROSS |
| X03 | COMMON | completed_scoped | — | — | CROSS |
| S01 | P1 | completed_scoped | — | — | CF4 |
| S02 | P1 | blocked_input | D01, D02, M01, M02, M03 | D01, D02, M01, M02, M03 | CF4 |
| S03 | P1 | pending | A05 | A05, D01, D02, M01, M02, M03 | CF4 |
| S04 | P1 | pending | M03, A01 | A01, A05, D01, D02, M01, M02, M03 | CF4 |
| S05 | P1 | pending | A06 | A01, A05, A06, D01, D02, M01, M02, M03 | CF4 |
| S06 | P1 | pending | A06 | A01, A05, A06, D01, D02, M01, M02, M03 | CF4 |
| L01 | P2 | completed_scoped | — | — | CMB_CACHE, CMB_SPLITS |
| L02 | P2 | completed_scoped | — | — | CMB_CACHE, CMB_SPLITS |
| L03 | P2 | pending | D03, M04 | A02, D03, M04 | CMB_CACHE, CMB_SPLITS |
| L04 | P2 | pending | A02 | A02, D03, M04 | CMB_CACHE, CMB_SPLITS |
| L05 | P2 | pending | A06 | A02, A06, D03, M04 | CMB_CACHE, CMB_SPLITS |
| L06 | P2 | pending | A06 | A02, A06, D03, M04 | CMB_CACHE, CMB_SPLITS |
| H01 | P3 | completed_scoped | — | — | CF4 |
| H02 | P3 | pending | D01, D02, M01 | A01, D01, D02, M01 | CF4 |
| H03 | P3 | completed_scoped | — | — | CF4 |
| H04 | P3 | pending | A01, M02 | A01, D01, D02, M01, M02 | CF4 |
| H05 | P3 | pending | A06 | A01, A06, D01, D02, M01, M02 | CF4 |
| H06 | P3 | pending | A06 | A01, A06, D01, D02, M01, M02 | CF4 |
| V01 | P4 | completed_scoped | — | — | RADIO, BIANCHI |
| V02 | P4 | completed_scoped | — | — | RADIO, BIANCHI |
| V03 | P4 | completed_scoped | — | — | RADIO, BIANCHI |
| V04 | P4 | pending | M07, A04 | A01, A04, A05, D01, D02, D05, M01, M02, M06, M07 | RADIO, BIANCHI |
| V05 | P4 | pending | A04, A05 | A01, A04, A05, D01, D02, D05, M01, M02, M06, M07 | RADIO, BIANCHI |
| V06 | P4 | pending | A06 | A01, A04, A05, A06, D01, D02, D05, M01, M02, M06, M07 | RADIO, BIANCHI |
| B01 | P5 | completed_scoped | — | — | BIANCHI |
| B02 | P5 | pending | M08, M09, A03 | A03, M08, M09 | BIANCHI |
| B03 | P5 | pending | A02, A03 | A02, A03, D03, M02, M04, M07, M08, M09 | BIANCHI |
| B04 | P5 | pending | A03, A04 | A02, A03, A04, D03, M02, M04, M07, M08, M09 | BIANCHI |
| B05 | P5 | pending | A06 | A02, A03, A04, A06, D03, M02, M04, M07, M08, M09 | BIANCHI |
| K01 | P6 | completed_scoped | — | — | GAIA, CF4, BIANCHI |
| K02 | P6 | completed_scoped | — | — | GAIA, CF4, BIANCHI |
| K03 | P6 | pending | D04, M02, M05 | A05, D04, M02, M05 | GAIA, CF4, BIANCHI |
| K04 | P6 | pending | M02, A01 | A01, D01, D02, M01, M02, M07 | GAIA, CF4, BIANCHI |
| K05 | P6 | pending | M05, M07, A04 | A01, A04, A05, D01, D02, D04, D05, M01, M02, M05, M06, M07 | GAIA, CF4, BIANCHI |
| K06 | P6 | pending | A06 | A01, A04, A05, A06, D01, D02, D04, D05, M01, M02, M05, M06, M07 | GAIA, CF4, BIANCHI |
| SQ-CF4 | P3 | ready_scoped | D01, D02, M01, A01 | A01, D01, D02, M01 | CF4 |
| SQ-GAIA | P6 | ready_scoped | D04, M05, A05 | A05, D04, M05 | GAIA, CF4, BIANCHI |
| SQ-RADIO | P4 | ready_scoped | D05, M06, A05 | A05, D05, M06 | RADIO, BIANCHI |
| SQ-FRAME | COMMON | ready_scoped | M02, M07 | M02, M07 | BIANCHI, GAIA, RADIO |
| SQ-P1-ANCHOR | P1 | blocked_physical_anchor | M03 | M03 | CF4 |
| SQ-CMB-NULL | P2 | blocked_source | D03, M04, A02 | A02, D03, M04 | CMB_CACHE, CMB_SPLITS |
| SQ-PHOTON-FLUX | P2 | blocked_source | D06, M08 | D06, M08 | CMB_CACHE, CMB_SPLITS |
| SQ-LIE-FLUX | P5 | blocked_source | D06, M08 | D06, M08 | BIANCHI |
| SQ-OPTICAL | COMMON | pending_conditional | M02 | M02, M07 | BIANCHI |
| SQ-CROSS-COV | COMMON | pending_dependency | A04 | A01, A04, A05, D01, D02, D04, D05, M01, M02, M05, M06, M07 | CF4, CMB_CACHE, RADIO, GAIA, CROSS |
| SQ-NATIVE | P5 | blocked_external | M08, M09, A03 | A03, M08, M09 | BIANCHI |
| PHY-01 | CROSS | theory_verified_physical_data_pending | M02, A04 | A01, A04, D01, D02, D06, M01, M02, M07, M08 | CROSS |
| PHY-02 | CROSS | theory_verified_physical_data_pending | D06, M08 | A02, D03, D06, M04, M08 | CROSS |
| PHY-03 | CROSS | theory_verified_physical_data_pending | M06, M07, A04 | A04, A05, D05, D06, M02, M06, M07, M08 | CROSS |
| PHY-04 | CROSS | theory_verified_physical_data_pending | M02, M05, A04 | A04, A05, D04, D05, M02, M05, M06, M07 | CROSS |
| PHY-05 | CROSS | theory_verified_physical_data_pending | D06, A04 | A04, D06, M02, M07, M08 | CROSS |
| PHY-06 | CROSS | theory_verified_physical_data_pending | M08, M09 | A02, D03, D06, M02, M04, M07, M08, M09 | CROSS |
| PHY-07 | CROSS | theory_verified_physical_data_pending | M01, M02, M06, A04 | A01, A04, A05, D01, D02, D05, M01, M02, M06, M07 | CROSS |

## Blocker actions

### D01 — DATA: CF4 upstream calibration

Pre-intercalibration joint zero-point law, anchor training membership and DirectCal cross-covariance are absent.

Obtain source-signed upstream law; preserve 7-method order and gauge. Do not estimate it again from globally registered moduli.

R98 evidence: `MISSING_INPUT_CONTRACTS.json#CF4_UPSTREAM_CALIBRATION`

### D02 — DATA: CF4 selection

Targeting, rejected-source denominators and method-specific inclusion law are absent.

Acquire source selection metadata, join all 38053 groups and 55877 galaxy rows; fit a selection likelihood including rejected sources.

R98 evidence: `MISSING_INPUT_CONTRACTS.json#CF4_PV_SELECTION`

### M01 — MODEL: CF4 physical correlated PV

R36 low-k selected covariance and R98 log-noise dispersion are working alternatives, not the full source-space PV law.

Build a cosmology-conditioned velocity covariance operator and source distance likelihood; compare physical PV alternatives on all eligible rows.

R98 evidence: `CF4_P1_RESULTS.json`

### M02 — MODEL: finite-redshift optical/frame transfer

Apparent log expansion, radial velocity, proper-motion and normal-frame kinematics need a shared finite-z response.

Extend R49 geodesic/Sachs transport along the same background, include observer/emitter tilt and source distances; verify Jacobi/optical limits.

R98 evidence: `BIANCHI_HISTORY_RESULTS.json`

### M03 — MODEL: P1 physical anchor and finite law

The 2048 weights define a coupled working finite measure, without the physical body/anchor or calibrated joint law.

Map the admitted source law through a signed physical carrier; retain unknown mass and common nuisance, with no per-draw nuisance maximization.

R98 evidence: `CF4_P1_RESULTS.json#P1`

### D03 — DATA: CMB matched simulation genealogy

Observed splits and full bank exist. A qualified common split/noise/systematics/foreground law, including Commander noise, is still absent.

Use official PR3 product index and existing files; acquire missing component-specific simulations with exact IDs/beam/masks and prove the joint law.

R98 evidence: `CMB_OBSERVED_SPLITS.json`

### M04 — MODEL: CMB foreground/selected-weight null

Repeated noise groups, foreground residuals and selected nuisance fits need a matched null for each statistic.

Keep group-wise cross-fitting, add paired residual/foreground and weight-selection generative model; calibrate on held-out noise groups.

R98 evidence: `CMB_GROUPED_FULL_CACHE.json`

### D04 — DATA: Gaia angular astrometric/AGN covariance

Per-source pm covariance and 48-patch diagnostics exist; AGIS/spatial correlated error and independent AGN-source null are not qualified.

Use all source_id joins and official angular-systematics references; acquire release-specific correlated error evidence where available.

R98 evidence: `GAIA_FULL_SHARED_PATCH.json`

### M05 — MODEL: Gaia source/normal-frame relation

E2/B2 apparent tangent fields combine scan, source centroids, frame spin and cosmological transport.

Fit spatial low-rank scan+AGN nuisance and finite-z optical response jointly; reference-frame spin/vorticity degeneracy stays explicit.

R98 evidence: `GAIA_FULL_SHARED_PATCH.json`

### D05 — DATA: radio footprint/completeness/SED

Five full catalogues exist; all-sky tile/RMS/zero-source coverage, resolved components and spectral-index response are incomplete.

Use recorded official RMS/mask links with size/checksum preflight; join catalog components and multi-frequency source matches before response calibration.

R98 evidence: `ACQUISITION_PREFLIGHT.json`

### M06 — MODEL: radio LSS and selection response

NB1 conditional cell law improves overdispersion treatment but is not a shared-source LSS/selection simulation law.

Develop Cox/LSS mocks with flux-size completeness and spectral-index distribution; jointly propagate shared-object and shared-sky covariance.

R98 evidence: `RADIO_FULL_MODELS.json`

### M07 — MODEL: local/global velocity transfer

Finite observer boost and source-history global tilt require common-frame, distinct calibrated response columns.

Compute common-operator Jacobians for both mechanisms, test singular values under observational covariance rather than arbitrary column normalization.

R98 evidence: `BIANCHI_HISTORY_RESULTS.json`

### D06 — DATA: independent normal-frame matter/photon flux

Independent rho,j,pi in a common normal frame are absent; Codazzi inversion alone cannot supply a new observation.

Prepare source/units/frame contracts; seek independent matter or photon observables. No generic catalogue download supplies all these moments.

R98 evidence: `CROSS_PHY_RESULTS.json`

### M08 — MODEL: Einstein–Boltzmann feedback/IC atlas

R98 evolves Einstein–Euler backgrounds and passive prescribed-xe all-m radiation; photon backreaction and primordial mode family are open.

Couple radiation moments to background Euler/Einstein equations; define regular/irregular IC families and compare scope-matched external solvers.

R98 evidence: `BIANCHI_HISTORY_RESULTS.json`

### M09 — MODEL: anisotropic recombination/reionization closure

Main sky uses prescribed HyRec2+tanh. A finite Peebles window response exists, not a self-consistent anisotropic radiative closure.

Extend retained rec/rei source operators along actual H/clock with photons and density; verify conserved energy, opacity and chemical closure.

R98 evidence: `BIANCHI_THEORY_CODE_KO.md`

### A01 — ADDITIONAL_ANALYSIS: source-law coverage and independent validation

Current full-data processing is complete within its stated working models; physical-law coverage tests still depend on new law inputs.

After D01/D02/M01, execute complete-source posterior predictive and truly independent holdout/selection injections, with old diagnostic retained.

R98 evidence: `CF4_P1_RESULTS.json`

### A02 — ADDITIONAL_ANALYSIS: CMB statistic-specific calibration

999 signal/paired and 300 noise grouped diagnostics plus 10 observed maps are complete; physical null coverage remains open.

Once D03/M04 are qualified, rerun all groups and all candidate statistics with a prospective multiplicity protocol; retain noise genealogy.

R98 evidence: `CMB_GROUPED_FULL_CACHE.json`

### A03 — ADDITIONAL_ANALYSIS: Bianchi atlas and convergence

Five declared histories and L12 all-m have run; complete I–IX/exceptional mode families and stronger source/collision convergence are pending.

Expand admissible parameter/IC atlas with constraint monitoring; test scalar/vector/tensor limits, radiation feedback and external near-FLRW agreement.

R98 evidence: `BIANCHI_HISTORY_RESULTS.json`

### A04 — ADDITIONAL_ANALYSIS: cross-probe calibrated covariance

Joint spatial patch diagnostics are computed; a common physically calibrated source/selection/transport null remains absent.

Use all catalog overlap IDs and common mock sky/light cone, not product of per-survey likelihoods; compare alternative source and transfer models.

R98 evidence: `GAIA_FULL_SHARED_PATCH.json`

### A05 — ADDITIONAL_ANALYSIS: selection robustness/injection and all-source comparison

Full radio/Gaia working-law fits and paired model contrasts are available; source-model injection/coverage is not.

Repeat all flux/redshift/model combinations on qualified matched mocks, including missing/zero-source regions and systematic model alternatives.

R98 evidence: `RADIO_FULL_MODELS.json`

### A06 — ADDITIONAL_ANALYSIS: publication and novelty adjudication

Publication gates require completed upstream claims and a matched primary-literature comparison.

Use source-qualified results to decide informative null/partial identification/model discrimination, then draft; keep retrospective statistics retrospective.

R98 evidence: `REPORT_KO.md`
