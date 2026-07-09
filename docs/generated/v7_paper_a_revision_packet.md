# v7 Paper A Revision Packet

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
config_hash: `sha256:b6b9405cfe99ea5c37fe1882706509a26c9e5e70aa3029252bbb3ee52da86680`
generating_command: `venv/bin/python scripts/build_v7_paper_a_revision_packet.py`

## Replacement Rules

| Target | Replacement | Caveat |
| --- | --- | --- |
| P31 | sharpness is for the registered convex component-box model; full physical realization is deferred | does not certify nonlinear GR realizability |
| P35 | split threshold policy into known_chi2 and estimated_covariance_f with n_sim metadata | finite-simulation covariance requires Hotelling/F threshold |
| P36 | joint interval is a subset of naive; strictness requires a shared-extrema conflict | aligned shared boxes collapse to equality |
| MES | MES epsilon coefficients remain registered_external until a dedicated derivation seal exists | parent identity seal records rederived_here=false for MES coefficients |
| figures | current report figures are appendix diagnostics unless matched null/covariance gates pass | no posterior odds, p-value, native solver output, or morphology-family promotion |

## Paper A Skeleton

| Section | Instruction |
| --- | --- |
| Abstract | Frame the paper as an identifiability and diagnostic-methods paper, not as a detection paper. |
| Component-box theorem | State signed lower/upper component boxes and report open/all curvature branches. |
| Two-stage thresholds | Give separate known-covariance and estimated-covariance threshold policies. |
| Depth-gap interval propagation | State joint subset relation and the strict/equality criterion. |
| Data diagnostic appendix | Put K5/CF4 closure and current data figures in diagnostic appendix lanes until blockers clear. |

## Forbidden Promotions

- native low-ell solver output from current transfer-conditional artifacts
- posterior odds from OBSSTAT/MIO diagnostic cards
- morphology-family promotion from scalar or interval diagnostics
- observed x_C result while any component remains PLUGIN/BLOCKED
