# R39 PR and legacy audit

## Scope

R38 reports 561 PR records inventoried and 71 title-screened, while its own scope note says only core ancestry bodies were reviewed in depth. R39 re-read the following high-leverage PRs and pinned tensor/statistical documents. It does not claim a line-by-line diff audit of all 561 PRs.

## High-leverage lineage

| GitHub PR | Verified role | Boundary retained |
|---|---|---|
| #364 (PR-256) | Frame-labelled beta_RO, beta_RM, beta_MO and local/global response geometry. | First-order closure and synthetic separability only; not observed global-tilt detection. |
| #365 (PR-257) | Typed low-ell O(3)/SO(3), phase/orientation/parity and signed harmonic morphology. | Synthetic benchmark only; not observed attribution or native Bianchi transfer. |
| #378 (PR-281) | Orbit/type acceptance and historical replay. | Pre-native family identification remains blocked. |
| #394 (PR-306) | Planck PR3 operator/profile, mask/beam/FFP and matched-null preparation. | Its own record says no observed statistic or observed science execution. |
| #401/#402 (PR-311) | DESI DR1 BGS selection and successor observer-side operator; 1000 EZmock plus 25 held-out Abacus synthetic closure. | No observed statistic or complete canonical data admission. This is DR1, not DR2. |
| #403 (PR-314, open) | Attended Planck SMICA diagnostic over 300 paired FFP10 CMB+noise rows with replay receipt. | No Commander robustness, joint Planck result, local/global response or Bianchi family claim. |
| #360 (PR-248–252) | Statistical-foundation migration separating signed departure, typed MES/anchor stress, data-identified sets/likelihoods and parity morphology. | No native solver or observed-source atlas. |
| #367 (PR-259–275) | Vector/tensor MES programme, typed state, functional set/path reports, O(3) action and pre-native observatory. | No native low-ell Bianchi solver or observed family atlas. |
| #368 (PR-190) | Refutes one specified Bianchi-I/W2 comparator under the sealed hypersurface-orthogonal congruence using Frobenius. | Premise-specific negative result, not a universal Bianchi no-go theorem. |
| #467 (R8 design, closed not merged) | Vector/tensor rank, support and joint physical inference design. | Synthetic/design work; no production observational inference. |
| #468 (R9 design, closed not merged) | Model-to-observation and conditional inference design. | Research-design handoff only; no native solver or raw observational campaign. |
| #548/#550 (open drafts) | Six-paper theory, selection and CF4 raw-source audit work. | Local source files/hashes are not rehashed by this GitHub-only session. |
| #557 (open draft) | Planck mask geometry and R8/C8 spectral stability. | Physical high-ell tail and matched beam/noise/foreground/FFP validation remain open. |
| #563/#564 | R32/R37 integration, finite report-first DAG and controller convergence. | Controller integration is not six completed observational studies. |

## Tensorized authority re-read

1. METHOD_REBOOT_20261023/THEOREMS.md at dfaf171c37f2636c942a99bf2b9803b57295ac14. x is sample × functional and retains each functional's rank/parity. T7 provides one common typed state and simultaneous functional images.
2. tensor_joint_r9/revision2/MODEL_TO_DATA.md. Distinguishes physical state, observed Q/O carriers, shared nuisance, anchor, response, full covariance and typed TensorFunctionalBundle.
3. tensor_joint_r9/revision2/THEORY_EXTENSION.md. D1–D4 preserve full joint path law, covariance cross-blocks, singular support and initial level; F1–F3 give simultaneous functional images and fixed-contraction support conditions.
4. htt/src/common/r9_product.py. ProductIntake enforces exact feature/covariance row order and explicit source/frame/epoch/selection/calibration/mask/law metadata. SharedStateEmbedding preserves roles and requires explicit unit conversion.
5. htt/src/common/tensor_functionals.py. Only a numerical fixed 3×7 contraction fibre is implemented; uncertain q returns JOINT_Q_INVERSE_IMAGE_REQUIRED. Not a confidence certificate.
6. htt/src/common/depth_path.py. The complete ordered covariance blocks are required; missing blocks return unavailable rather than assuming independence.
7. docs/generated/claim_adjudication/literature_verdicts.json. The master x_C identity is judged a standard 1+3 constraint rearrangement with no new physics delta.

## R38 execution conflicts

R38 branch research/observational-convergence-r38-20261107 points to 05e9d53449bd02973848da3306f72f63edd7fc54 and compares two commits ahead of its declared base cab89d25af52a1b978a4da8c11eecdc25bb22759.

The R38 README says observed-map/catalogue analysis, code tests and Cobaya MCMC were not performed in that scoped work. The R38 DAG/claim ledger and EXECUTION_REPORT claim these were complete.

Source review found:
- likelihood adapters default Planck/CF4/Gaia to zero vectors and identity/diagonal covariance;
- NVSS/Quaia summary dipoles are hard-coded;
- Pantheon+ has a zero/random fallback if source paths are absent;
- DESI has a zero-vector fallback;
- run_joint_cobaya.py instantiates adapters with empty dictionaries;
- run_response_rank.py constructs manual response blocks and diagonal covariance;
- chain summary parameters is an empty object;
- identifiability JSON reports rank 13 with condition number ~2.5342e17;
- Bianchi decision text says Delta BIC=17.2 while the table gives M3-M0 approximately +40.08.

These do not prove that no earlier valid single-probe analysis exists. They do mean the R38 joint posterior/rank/BIC claim is not source-replayable from the examined code.

## Literature overlap and novelty ceiling

Closest primary literature:
- Planck intrinsic CMB dipole / Doppler-aberration: https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.127.101301
- Bayesian NVSS/RACS counts: https://arxiv.org/html/2406.01871v1
- Radio/infrared dipole tension and likelihood correction: https://arxiv.org/html/2509.18689v1
- Covariant observer-dependent Hubble parameter: https://arxiv.org/pdf/2312.09875
- Pantheon+ directional Hubble: https://link.springer.com/article/10.1140/epjc/s10052-025-14222-w
- Pantheon+/BAO directional CDDR: https://arxiv.org/html/2604.04436v1
- Gaia acceleration and angular power systematics: https://arxiv.org/html/2605.30367v3
- Gaia Bianchi-I VSH: https://arxiv.org/abs/2605.30579
- Bianchi polarized transfer: https://ar5iv.labs.arxiv.org/html/0706.2075
- Bianchi anisotropy likelihood: https://arxiv.org/pdf/1604.01024
- Low-ell mask sensitivity: https://arxiv.org/html/2509.03720v1

The candidate novelty is not tensor x itself, CMB/radio/Gaia combination, or x_C. It is conditional on a validated source-conditioned cosmological observation operator and data-supported tensor-functional quotient.
