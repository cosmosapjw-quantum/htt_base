# Theorem Candidates

Each candidate below is designed to be strong enough to preserve novelty and narrow enough to remain true without the native low-ell solver.

## Math/Stat Theory Axis

### T1. Rank-Aware Comparator Identifiability

Statement candidate:

Let `R: Theta -> X` be the registered linearized response map from physical sectors to observable features after masking, nuisance projection, and fixed preprocessing. Then only `im(R)` is identifiable from the feature vector without additional prior information. Components in `ker(R)` are blind sectors. Any scalar comparator `x_C = c^T theta` is data-identified only through its projection onto `row(R)`.

Strong consequence:

- A rank-2 reachable comparator plus named blind sectors is a positive result, not a failed detection.
- Missing sectors cannot be set to zero in PR08-006.

Numerical witness:

- simulate a response matrix with two reachable columns and two blind columns;
- verify rank, null columns, and row-space projection;
- verify local/global response-overlap after nuisance projection.

Executable hook:

```bash
venv/bin/python docs/research_program/publishable_analysis_pack_2026-06-26/scripts/candidate_experiments.py --experiment rank_evalue
```

### T2. Mixture E-Value Calibration For Registered Look-Elsewhere Scans

Statement candidate:

If `E_j >= 0` are registered null e-values with `E_0[E_j] <= 1`, then any convex mixture `E_mix = sum_j w_j E_j`, `w_j >= 0`, `sum_j w_j = 1`, is an e-value. Therefore `P_0(E_mix >= 1/alpha) <= alpha`. This supports a registered low-ell max/mixture scan without pretending the selected statistic was fixed after seeing data.

Strong consequence:

- K1 can make a global calibration claim after FFP10/NPIPE E2E summaries are bound.
- The result is not a family/classification claim.

Numerical witness:

- simulate null e-values with unit mean;
- verify empirical threshold exceedances stay near the Markov envelope;
- report finite-sample uncertainty separately.

### T3. Finite-Mock Coverage Decomposition

Statement candidate:

For release-matched mocks, bulk-flow uncertainty decomposes into measurement variance plus cosmic-variance coverage only if the mocks share the release selection, frame, distance-error model, and estimator. A self-injection or non-release mock cannot estimate the same coverage functional.

Strong consequence:

- K5 can publish a coverage result once mock ownership is present.
- Without release-matched mocks, only mechanics and diagnostics are claimable.

## GR/Cosmology Theory Axis

### G1. Visibility-Weighted Boltzmann Transfer Contraction

Statement candidate:

For a single shear-sourced low-ell mode with source `S(eta)` and normalized visibility `g(eta)`, the line-of-sight response

```text
T_l(k) = integral g(eta) S(eta) j_l(k(eta0 - eta)) d eta
```

obeys

```text
|T_l(k)| <= integral g(eta) |S(eta)| d eta
```

because `|j_l(x)| <= 1`. For `l > 0`, the superhorizon response has the expected small-`k` scaling from the spherical-Bessel expansion. This is a direct Boltzmann-equation transfer statement for the single-mode bridge, not a native atlas.

Strong consequence:

- The semi-native single-mode transfer can support bounded low-ell response profiles.
- It cannot support native-atlas-dependent family/classification language.

Numerical witness:

- evaluate `T_2(k)` and `T_3(k)` over a registered `k` grid;
- verify the contraction bound;
- verify small-`k` scaling ratios.

Executable hook:

```bash
venv/bin/python docs/research_program/publishable_analysis_pack_2026-06-26/scripts/candidate_experiments.py --experiment boltzmann_visibility
```

### G2. Volterra Depth-Memory Stability

Statement candidate:

For a depth response `F(z)` obeying a first-order relaxation equation with source `Pi(z)`, the Volterra integral representation with positive damping kernel is equivalent to the ODE solution and has Gronwall-stable perturbation bounds. If the source is depth-steady, the normalized depth gap is unity; sign-definite depth growth creates a non-unit gap.

Strong consequence:

- `G_F` is a meaningful depth-memory diagnostic when depth bins, covariance, and null status are recorded.
- It is not by itself a global-tilt evidence term.

Numerical witness:

- solve ODE and Volterra forms on the same grid;
- check max discrepancy and gap monotonicity.

### G3. Radial Vorticity Blindness And Transverse Reopening

Statement candidate:

For antisymmetric vorticity tensor `Omega_ij`, radial velocity projection satisfies `n_i Omega_ij n_j = 0` for every line of sight `n`. Therefore a radial-only field is structurally blind to that sector, while a transverse or affine realization channel can reopen rank.

Strong consequence:

- K6 must use realization-conditioned field information, not a curl-suppressed point field.
- A no-go result is publishable if the field owner only supplies curl-suppressed reconstructions.

## Data Interpretation Axis

### D1. K1 Public E2E Global Calibration

Statement candidate after exit gate:

The registered K1 low-ell morphology statistic has global rank `p` under the matched public E2E simulation ensemble and frozen max-scan configuration.

Blocked until:

- FFP10/NPIPE input manifests and per-simulation summaries are bound.

### D2. K5 Release-Matched Cosmic-Variance Coverage

Statement candidate after exit gate:

The CF4 bulk-flow apex/depth estimator has component and amplitude coverage under release-matched forward mocks, with bias and frame/depth ablations reported.

Blocked until:

- release-matched mock ownership exists.

### D3. K6 Realization-Conditioned Curl Posterior Or Structural No-Go

Statement candidate after exit gate:

The CF4 field-realization ensemble gives a realization-conditioned posterior for the affine curl sector, or the provided reconstruction is structurally curl-suppressed and no physical curl statement is available.

Blocked until:

- constrained 3D field realizations are bound.

