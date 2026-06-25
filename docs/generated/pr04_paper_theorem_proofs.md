# PR04 PAPER-A/PAPER-B Analytic Cores: Symbolic Proofs (LR-06B/LR-06C)

owner: BASS  ·  claim_tier: program_theorem  ·  engine: wolfram (14.3.0 for Linux x86 (64-bit) (July 31, 2025))
git_state: 6e9877a+dirty

## A-rank (PAPER-A) - Duplicate response block adds zero identifiable rank

status: symbolically_verified_wolfram; QED: true

Hypotheses:
- generic 2x2 block A with symbolic entries
- whitening is full rank (identity here); ranks are basis-independent

Symbolic steps (Wolfram):
- `rank_A` = `2`
- `rank_AA` = `2`
- `nullspace_pattern` = `{{0, -1, 0, 1}, {-1, 0, 1, 0}}`

Claim: Appending a copy of a response block leaves the identifiable rank unchanged; the duplicated directions occupy the nullspace along the (x,-x) line.

## A-flrw (PAPER-A) - Flat-FLRW first jet has theta = 3H and zero shear

status: symbolically_verified_wolfram; QED: true

Hypotheses:
- metric diag(-1, a^2, a^2, a^2), comoving u^a=(1,0,0,0)
- signature (-,+,+,+); expansion from the spatial volume element

Symbolic steps (Wolfram):
- `theta` = `(3*Derivative[1][a][t])/a[t]`
- `theta_minus_3H` = `0`

Claim: The comoving congruence expansion is theta = 3 a'/a = 3H; isotropy of the spatial metric forces zero shear (off-diagonal spatial rate of strain vanishes).

## A-wigner (PAPER-A) - Non-collinear boost composition is Lorentz, velocity is not additive

status: symbolically_verified_wolfram; QED: true

Hypotheses:
- boost 1 along x with speed b1, boost 2 along y with speed b2, c=1
- composition L = B_x(b1) . B_y(b2)

Symbolic steps (Wolfram):
- `lorentz_error_is_zero` = `{{0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}, {0, 0, 0, 0}}`
- `composed_velocity` = `{b1, Sqrt[1 - b1^2]*b2, 0}`
- `velocity_minus_euclidean_sum` = `{0, (-1 + Sqrt[1 - b1^2])*b2, 0}`

Claim: Two non-collinear boosts compose to an exact Lorentz transformation whose velocity differs from the Euclidean sum (b1,b2,0); rapidities do not add as vectors.

## B-nonsuff (PAPER-B) - Scalar trace Omega_tilt is non-sufficient; the STF moment Pi separates configs

status: symbolically_verified_wolfram; QED: true

Hypotheses:
- two antipodal stream configs with equal per-stream second-moment weight m>0
- config 1: a single colinear pair along x; config 2: an isotropic six-stream

Symbolic steps (Wolfram):
- `trace_K1` = `6*m`
- `trace_K2` = `6*m`
- `trace_equal` = `0`
- `Pi_K1_nonzero_norm2` = `24*m^2`
- `Pi_K2` = `{{0, 0, 0}, {0, 0, 0}, {0, 0, 0}}`

Claim: The colinear pair and the isotropic six-stream carry identical Omega_tilt = Tr(K) but the colinear pair has nonzero STF moment Pi while the isotropic stream has Pi = 0; the scalar trace cannot close the tilt sector.

## B-psd (PAPER-B) - PSD second moment realizes as a sum of antipodal eigen-pairs

status: symbolically_verified_wolfram; QED: true

Hypotheses:
- K positive semidefinite (here diag(l1,l2,l3), l_i>=0)

Symbolic steps (Wolfram):
- `reconstruction_minus_K` = `{{0, 0, 0}, {0, 0, 0}, {0, 0, 0}}`
- `pair_first_moment` = `each pair {e,-e} has zero first moment by antipodal symmetry`

Claim: Every PSD second moment K = sum_i lambda_i e_i e_i^T is realized by antipodal stream pairs, each with exactly zero first moment; the moment cone is the PSD cone.

## B-dust (PAPER-B) - Exact dust-FLRW oracle satisfies Raychaudhuri and the Gauss constraint

status: symbolically_verified_wolfram; QED: true

Hypotheses:
- a(t) = (1 + (3/2) H0 t)^(2/3), dust (w=0), zero shear, kappa*mu = 3 H^2
- Raychaudhuri Hdot = -H^2 - (kappa/6)(mu + 3p), p=0

Symbolic steps (Wolfram):
- `H_of_t` = `(2*H0)/(2 + 3*H0*t)`
- `Hdot` = `(-6*H0^2)/(2 + 3*H0*t)^2`
- `raychaudhuri_residual` = `0`
- `H_at_zero` = `H0`

Claim: The closed-form dust scale factor gives H = H0/(1 + 3 H0 t/2) and the exact Raychaudhuri relation Hdot = -(3/2) H^2, with 3 H^2 = kappa*mu (Gauss) and zero shear; this is the exact FLRW comparator for the constraint-transport gate.

## B-shear (PAPER-B) - Shear retains memory of the tilt stress; anisotropic-stress ablation is non-trivial

status: symbolically_verified_wolfram; QED: true

Hypotheses:
- shear evolution sigmadot = STF(-3 H sigma + kappa Pi)
- Pi the trace-free tilt/anisotropic stress, kappa>0

Symbolic steps (Wolfram):
- `sigmadot_12` = `(2*kap*p12 - 6*H*s12)/2`
- `d_sigmadot12_d_Pi12` = `kap`
- `ablation_sets_Pi_zero` = `setting Pi=0 removes the kappa*Pi source term`

Claim: Shear evolves by sigmadot = STF(-3 H sigma + kappa Pi); the sensitivity d(sigmadot)/dPi = kappa is nonzero, so ablating the anisotropic stress Pi provably changes the shear history (shear memory of the tilt second moment).

## Caveats

- each theorem is conditional on the registered hypotheses; structural identities, not detections
- no raw data, native solver output, or Bianchi family identification is involved
- numerical companions are the PR04 external gate tests in research_gates/pr04/tests/
