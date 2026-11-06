# R39 code audit and correction record

## Source change

R39 starts from R38 05e9d53449bd02973848da3306f72f63edd7fc54. The current code repair is in htt/src/common/kinematic_response.py, with regression tests in tests/r38/test_kinematic_response.py.

## Exact two-frame Lorentz velocity transformation

The old compose_velocities computed gamma_b and a candidate v_diff but discarded it, returning the collinear expression (v_a-v_b)/(1-v_a·v_b) for arbitrary vectors. This omits the transverse gamma factor and is not the exact non-collinear transform.

For dimensionless velocities beta_a and beta_b in one common inertial frame, the velocity of A in B's standard-boost axes is now

\[
\beta_{A|B}=
\frac{\beta_a-\gamma_b\beta_b+
(\gamma_b-1)(\beta_a\cdot\beta_b)\beta_b/\beta_b^2}
{\gamma_b(1-\beta_a\cdot\beta_b)}.
\]

The beta_b=0 limit is handled separately. Shape, finite-value and subluminal checks are explicit. A non-collinear regression example beta_a=(0.3,0,0), beta_b=(0,0.4,0) yields (0.3 sqrt(1-0.4^2),-0.4,0). Wolfram returned the exact first component 3 sqrt(21)/50. The collinear limit was independently reduced to (a-b)/(1-ab).

This is a specified standard-boost coordinate convention. Non-collinear frame chains may carry Wigner rotation. It does not make the current three-frame beta_MO=beta_RO-beta_RM assignment exact; that remains a first-order closure and must be explicitly tagged.

## Remaining code defects

1. KinematicResponseModel.from_parameters still sets beta_MO=beta_RO-beta_RM. Keep it first-order with declared error/range or replace it with an ordered tetrad-composition object that records axis rotations.
2. directional_hubble_variation subtracts acceleration_vector directly from a dimensionless Delta H/H response. For physical A in m s^-2 the dimensionless term is A·n/(cH). Rename the API input to a_acc_over_cH or require H,c explicitly.
3. R38 likelihood defaults must not be used for observed analysis. Planck/CF4/Gaia zero vectors, identity/diagonal covariance, hard-coded count dipoles and random Pantheon directions are fixtures, not observed likelihoods.
4. Every observed likelihood must require actual data, covariance, selection/window, release, hash, row IDs, frame, units and operator identity; missing inputs raise at preflight.
5. Response matrices must be differentiated from actual estimator/forward operators after source masks, selection and nuisance response are admitted. The manual R38 response matrix is not an observed Jacobian.
6. Cross-probe covariance cannot default to block diagonal. Same-sky Planck products, Quaia-Gaia matches, overlapping large-scale structure and shared calibration need explicit cross blocks or conditional-independence caveats.
7. TensorFunctionalBundle is not yet implemented as a cosmology-wide production object. Reuse ProductIntake, SharedStateEmbedding, fixed_contraction_support and DepthRepresentation, but extend rather than wrapping them in a scalar adapter. A new typed registry must validate rank/parity/action/units/frame/state_id and return functional set images.

## Regression acceptance

- Run pytest tests/r38/test_kinematic_response.py locally and relevant adjacent suites.
- Add randomized non-collinear 4-velocity reference tests and inverse/axis convention tests including Wigner rotation for ordered boosts.
- Unit-test the first-order three-frame closure or implement its exact ordered tetrad map.
- Test acceleration unit conversion.
- Require fail-closed observed likelihoods and separate synthetic fixture entry points.
- Require operator-derived Jacobians, full covariance support and injection/coverage validation.
- Do not report PASS until actual commands, environment, return code and commit SHA are attached.

No local test, CI or sampler was executed in this GitHub-only turn.
