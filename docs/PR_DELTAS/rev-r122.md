# REV-R122 - EGS3 Axis A + Axis B theorem modules (graded comparator + GR/Boltzmann)

owner: COMMON
implementation_scope: common
claim_tier: program_theorem_and_synthetic_mechanics
transfer_source: none
generating_command: `make egs3-gates + run_pr07_wolfram_proofs.py wolfram/egs3_bracket_constants.wls`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Execute the approved EGS3 plan's theorem layer: strong conditional theorems that
apply GR + the covariant Boltzmann hierarchy directly to the statistical
variables, organised on the math/stat and GR/cosmology axes.

## Axis A (math/statistics) - htt/obsstat/egs3_*

- **A1 [flagship] graded-comparator identifiability rank** (`egs3_graded_comparator.py`):
  promote the signed scalar `x_C` to the graded vector `g=(Sigma^2,W^2,Omega_tilt,
  Omega_k)`, `x_C=<c,g>`. From {low-l CMB-T, radial velocity} the identifiable
  subspace of `g` is exactly **rank 2** (Sigma^2, Omega_tilt reachable; W^2,
  Omega_k in the joint null) -> `x_C`'s sign-cancellation is a projection
  artifact. Unifies NT2-B3 + PAPER-A rank on the redesigned variable.
- **A2 reparametrization-invariant floor** (gate; reuses `egs2_fisher`): the
  NT2-A1 fractional floor is scale-free, so one floor bounds all five scalars.
- **A3 Pi e-value calibration** (`egs3_calibration.py`): `E=1[x>t]/alpha` has
  null mean 1 and a Markov false-exceedance bound `P(E>=1/beta)<=beta`; S4
  domination makes the bound-based e-value conservative. Promotes Pi from
  "not-a-probability" to a calibrated certificate with a stated error rate.
- **A4 Rao-Blackwell sufficiency** (`egs3_calibration.py`): the sufficient
  statistic `(a2,a3,dipole)` dominates any raw estimator (`Var_RB <= Var_raw`).

## Axis B (GR/cosmology) - 1+3 covariant Boltzmann on the variables

- **B1 [flagship] semi-native shear->multipole transfer** (`htt/bass/transfer/
  shear_quadrupole_seminative.py`): LOS/Bessel projection of a single
  shear-sourced mode through a recombination visibility -> the response `r_l`,
  replacing NT2-A1's toy. **Honest sharpening:** the genuine floor is a PROFILE
  in the shear scale `k` --- it saturates at the single-l `sqrt(2/5)=0.632` for a
  pure super-horizon (homogeneous) shear (quadrupole-dominated) and drops below
  0.632 only at finite `k` (multi-l band: 0.632 at k*chi~0.1 -> 0.0011 at
  k*chi~28). Partial discharge of `AWAITING_NATIVE_LOWELL_SOLVER`.
- **B2 Volterra depth-memory** (`egs3_volterra_memory.py`): the shear-memory law
  has the exact integrating-factor solution `sigma=sigma_0 K + int K 3H^2 Pi`,
  `K=exp(-3 int H)`, so `Delta_F(z)` is a Volterra functional of `Pi` with an
  exponential memory kernel; verified == the RK4 ODE and bounded by a Gronwall
  envelope (couples NT2-B2 to the B4 memory bound).
- **B3 vorticity re-opening** (`egs3_vorticity_channels.py`): closes NT2-B3's
  "to close" --- the radial channel is identically blind (`n.Om.n=0`) but the
  TRANSVERSE velocity channel re-opens vorticity (`n.Om.m != 0`, rank-3 over the
  three curl modes); CMB B-modes named as the polarization re-opener.
- **B4 covariant bracket constants** (`wolfram/egs3_bracket_constants.wls`):
  symbolically derives the H3 lower coefficient `kappa/(1+R)` and the
  nondegeneracy condition `C_up kappa (1+R) > 1` (satisfied by kappa=4/21,
  C_up=9), turning NT2-B1's bracket into a real exclusion with stated constants.
  Wolfram core PASS (all checks true).

## Claim discipline

Conditional theorems + synthetic mechanics only. B1's honest k-profile is a
*sharpening* of NT2-A1, not a tone-down: it states exactly when the floor beats
0.632. No detection, family/geometry, or native-solver claim. Real CAMB
visibility / H(z) / covariant amplitudes remain the documented to-close.

## Validation

| Command | Status |
| --- | --- |
| `make egs3-gates` (Axis A 7 + Axis B 5) | 12/12 |
| B4 `egs3_bracket_constants.wls` | PASS (all checks true) |
| A1 rank=2, null={W2,Omega_k}; A3 Markov holds; A4 RB dominates | hold |
| B1 floor profile 0.632(k->0) -> 0.0011(k*chi=28); B2 Volterra==ODE + Gronwall; B3 transverse rank 3 | hold |
