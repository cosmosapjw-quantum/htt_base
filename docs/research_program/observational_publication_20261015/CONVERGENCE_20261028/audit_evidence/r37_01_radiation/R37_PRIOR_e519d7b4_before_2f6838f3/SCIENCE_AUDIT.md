# Physics, formalism, and validation audit

## Physics/math audit verdict

Scoped conditional synthetic methods image. No measured shear, transport derivative, native transfer, or Bianchi family identification follows.

## Assumptions and conventions

The observer and outward sky direction use the R36 convention, metric `(-,+,+,+)` and photon propagation `e=-n`. `rho_ref` normalizes energy density; the declared toy time normalizes `gamma_T=0.4`. STF2 coordinates use R36's Frobenius-orthonormal basis. The positive source is the saved R36 boosted `a=0.02,b=0.3` synthetic temperature sky, converted by the Planckian-ray bolometric fourth power. No empirical E-mode coefficient is identified with integrated screen polarization. The positive screen perturbation has amplitude 0.12, and circular polarization is fixed to zero.

## Equation and definition audit

| Item | Status | Issue | Required fix |
|---|---|---|---|
| `L_I` from direct quadrature and `(rho,pi,H4)` | PASS | Equality is numerical at finite quadrature | Retain declared 2e-10 normalized tolerance |
| `L_I Sigma = -(R_tau-C_pi)` | CONDITIONAL | `R_tau` central value is constructed from a declared target | Keep derivative allowance as sensitivity axis |
| `C_pi=-gamma_T(0.9 pi+P_star/5)` | PASS in finite fixed-frame model | Integrated screen STF is a modeled source | Require measured calibrated polarization for empirical use |
| `F` directional support | CONDITIONAL | It is a deterministic image of one joint two-dimensional error body | Do not call it a probability or calibrated significance |

## Dimensional/sign/limit checks

`L_I` has energy-density units; `R_tau` and `C_pi` have energy-density per toy-time units; `Sigma` has inverse toy-time units. The declared `epsilon_R` grid has normalized energy-density per toy-time units and `epsilon_P` normalized energy-density units. The common primitive `z` is dimensionless. At `epsilon_R=epsilon_P=0`, physical support is zero. At `P_star=0`, polarized and unpolarized centers coincide. The positive-source matrix has five strictly positive eigenvalues; a rank-deficient or nonpositive matrix would be an explicit failure. The sign of the omission difference is checked against the finite inverse and its coercive upper bound. The gain-only closure sets only `H4` to zero while retaining `rho`, `pi` and `P_star`; its nonzero bias is a calculated loss of response information.

## Claim-tier implications

The common carrier is a deterministic tensor image, not a scalar geometry certificate. `pi` here is the radiation anisotropic stress tensor, not the `Pi` threshold-exceedance statistic. No `Q`, `Pi`, occupancy `F`, or depth-gap `G_F` is inferred from the saved oracle draws. Matched coverage describes only the frozen synthetic temperature law at the constructed derivative center; the physical remainder has a support body, not a probability law.

## Fatal blockers

Empirical shear needs a source-qualified proper-time derivative/transport remainder, calibrated bolometric intensity and polarization law, and frame/congruence response. These inputs are absent. They do not block the conditional finite result.

## Safe claims

Full/common response preservation, finite gain-only and polarization omission biases, and directional support versus declared physical budgets on the saved synthetic source.

## Required tests or artifacts

`test_radiation_image.py` checks direct/common parity on three saved draws, positive coercivity, common-error support recomputation, and matched-law counts. The R36 core tests remain passing. `RADIATION_IMAGE_RESULT.json`, tables, vector figures and `REPORT_DELTA.md` give the calculated image and provenance. Preserve the first test assertion failure as `FIRST_FAILURE.txt`; the corrected assertion is tolerance based.
