# EGS-Type Low-ell Diagnostic Theorems: Symbolic Proofs (REV-R104)

owner: BASS
implementation_scope: bass_py
claim_tier: program_theorem
transfer_source: none
engine: wolfram (14.3.0 for Linux x86 (64-bit) (July 31, 2025))
source_program: egs_theorem_program.zip (NT-A1, NT-A3, NT-B3)
git_state: 3fa1f28+dirty

## NT-A1 - Quadrupole-filling EGS identity

status: conditional_proved; proof: symbolically_verified_wolfram; QED: true

Hypotheses:
- free-streaming linear ell=2 closure a2 = kappa*Sigma, kappa>0 constant
- shear filling F_shear = Sigma^2 / x_max, x_max>0
- quadrupole power D2 = cD * a2^2, cD>0
- tilt rapidity beta enters the dipole a1 only (a2 independent of beta)

Symbolic steps (Wolfram):
- `F_shear_in_a2` = `a2^2/(kappa^2*xmax)`
- `F_shear_in_D2` = `D2/(cD*kappa^2*xmax)`
- `egs_limit_D2_to_0` = `0`
- `d_Fshear_d_beta` = `0`
- `sphere_avg_n_a_n_b` = `{{1/3, 0, 0}, {0, 1/3, 0}, {0, 0, 1/3}}`

Claim: F_shear is an EGS-bounded functional of the CMB quadrupole: F_shear = a2^2/(kappa^2 x_max) proportional to D2, F_shear -> 0 as D2 -> 0, and F_shear is independent of the tilt rapidity. Conditional on the stated free-streaming linear closure; not a detection.

## NT-A3 - Single-sky sampling dispersion of the standard F_shear estimator

status: proved; proof: symbolically_verified_wolfram; QED: true

Hypotheses:
- F_shear = C2/(kappa^2 x_max) is linear in the quadrupole power C2 (NT-A1)
- the standard ideal full-sky Gaussian power estimator C2_hat has single-sky sampling variance Var(C2) = 2 C2^2/(2l+1) (chi-square, 2l+1 dof)
- shear sources the quadrupole (l=2) only at leading order

Symbolic steps (Wolfram):
- `Var_C2` = `(2*C2^2)/(1 + 2*l)`
- `Var_F_shear` = `(2*C2^2)/(kappa^4*(1 + 2*l)*xmax^2)`
- `Var_F_over_F2` = `2/(1 + 2*l)`
- `fractional_sampling_dispersion` = `Sqrt[2]/Sqrt[1 + 2*l]`
- `fractional_sampling_dispersion_at_l2` = `Sqrt[2/5]`
- `fractional_sampling_dispersion_at_l2_numeric` = `0.6324555320336758664`6.`

Claim: The standard full-sky F_shear estimator has fractional sampling dispersion sigma(F_shear)/F_shear = sqrt(2/(2l+1)); at l=2 this is sqrt(2/5) ~ 0.632. This is the sampling dispersion of that one estimator, NOT a Cramer-Rao bound or a universal floor over all estimators; the genuine multi-multipole Fisher-Cramer-Rao floor (NT2-A1) is strictly below 0.632.

## NT-B3 - Depth-transport EGS limit for G_F

status: conditional_proved; proof: symbolically_verified_wolfram; QED: true

Hypotheses:
- additive filling F(z) = F_shear(z) + F_tilt(z)
- depth gap G_F(z) = F(z)/F(z_ref)
- depth-steady shear: F_shear(z) = Fsh constant in z

Symbolic steps (Wolfram):
- `G_F_no_tilt` = `1`
- `dG_F_dz_no_tilt` = `0`
- `dG_F_dz_power_law_tilt` = `(c*q*z^(-1 + q))/(Fsh + c*zref^q)`
- `dG_F_dz_power_law_tilt_example_value` = `1/2`

Claim: For a depth-steady shear and no tilt, G_F(z) is identically 1 (EGS depth limit: no depth gap); a depth-evolving tilt imprints a nonzero dG_F/dz. Conditional on the additive filling decomposition.

## Caveats

- each theorem is conditional on explicit hypotheses and is a structural/limit statement, not a detection
- kappa = 4/21 is the ETM free-streaming ell=2 coefficient (cited); the theorems hold for any kappa>0
- no native low-ell solver output, HTT evidence, MIO certificate, or Bianchi family identification is produced
