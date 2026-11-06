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

The beta_b=0 limit is handled separately. Shape, finite-value and subluminal checks are explicit. The transverse coefficient is evaluated using the cancellation-stable identity (gamma-1)/beta_b^2 = gamma^2/(gamma+1). A small-beta regression test checks continuity. A non-collinear regression example beta_a=(0.3,0,0), beta_b=(0,0.4,0) yields (0.3 sqrt(1-0.4^2),-0.4,0). Wolfram returned the exact first component 3 sqrt(21)/50. The collinear limit was independently reduced to (a-b)/(1-ab).

This is a specified standard-boost coordinate convention. Non-collinear frame chains may carry Wigner rotation. It does not make the current three-frame beta_MO=beta_RO-beta_RM assignment exact; that remains a first-order closure and must be explicitly tagged.

## R39 direct kinematical state and optical-response implementation

New source: htt/src/common/kinematical_functionals.py; targeted tests: htt/src/common/test_kinematical_functionals.py.

The module:
- declares a physical-SI KinematicalState with STF2 sigma, axial-dual omega, physical acceleration, independent beta_RM/beta_MO and per-vector basis identities; missing blocks remain unavailable;
- adapts the existing relativistic_kinematics.kinematics_from_velocity_jet into the spatial triad, extracting H, sigma_AB, omega_A and A_A;
- evaluates direct, H-normalized and mixed scalar/vector/pseudoscalar/STF functional values with content-based state identity;
- applies O(3) actions with polar versus axial transformation rules and requires explicit frame transports for mixed contractions;
- evaluates the LOOP C leading local radial rate and Fermi-Walker/catalogue angular drift, with explicit triad rotation and source-direction basis;
- builds an unwhitened source-level local optical Jacobian. Its triad-spin nuisance columns duplicate the physical vorticity B1 columns, preserving the exact leading-order degeneracy.

The module is source-posted and readback verified; local pytest/import/compile was NOT_RUN. The ideal Jacobian is not a source-selected Gaia or CF4 estimator.

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

## Existing likelihood adapter source audit

The current branch was read at these exact files:
- htt/src/common/cobaya_adapters/likelihoods.py blob 751822a5702f3758855f04cc7526c28f83bfa6d6;
- htt/htt/htt/rest_frame/cf4_likelihood.py blob 61b48a10c71d1dbbbf4712fdb3e541e9f27be7e8;
- htt/bass/likelihood/observer_frame_adapter.py blob 121ade17571e2234e46acdd33e3b79d5ce378ee8;
- htt/src/common/bulkflow_likelihood.py blob e8368c732d8dddb2f596fd958f99a6b3af547720;
- htt/bass/inference/planck_likelihood.py blob ec6b9dc9ed7ada16a3b3e7e4dcb4bc2aebd3995c;
- htt/htt/htt/infer/dipole_vector_likelihood.py blob 770ac92278b1f25307fc11e737830b916ac69416.

Confirmed defects/limits in the R38 Cobaya joint adapter:
- Planck initializes a zero data vector and diagonal covariance; the prediction is also mostly zero with only a placeholder boost quadrupole slice.
- NVSS and Quaia initialize hard-coded dipole amplitude/direction and diagonal covariance rather than reading source catalogues/selections.
- CF4 initializes a zero 20-vector and diagonal covariance, then compares it with repeated STF shear amplitudes.
- Pantheon has a zero/random-direction fallback when source files are absent.
- Gaia starts from zero VSH modes/diagonal covariance.
- The joint likelihood adds each probe's marginal logp in a loop without an admitted shared latent/cross-probe covariance construction.
- DESI has a zero-vector fallback for missing source products.

The separate CF4 forward module explicitly reports diagnostic_only, diagonal_diagnostic_gaussian_score, diagonal_only_no_group_method_covariance, matched_nulls_not_bound, group_method_calibration_covariance_not_bound, and ppc_loocv_not_bound. It is not an evidence-grade likelihood.

Reuse decisions:
- BulkFlowLikelihood is a properly normalized source-level Gaussian radial bulk-flow component with optional sampling covariance and explicit active-row semantics; it is not the full tensor kinematic likelihood.
- ObserverFrameLikelihood reuses the boost-remapping architecture around FB-7, but its marginalise_boost is a finite support-point average. It needs quadrature/prior-weight convergence before continuous-prior marginalization can be claimed.
- PlanckLikelihood is a useful fail-closed synthetic/real dataset gate, but its C_l-only route does not replace a full anisotropic T/E/B harmonic likelihood.
- DipoleVectorLikelihood is a directional amplitude/axis projection, not the joint physical theta likelihood.

Therefore none of these current adapters should be passed as the completed R39 multi-probe likelihood. Reuse their scoped components and contracts, but create a new observed-data path that preflights exact source/row/selection/covariance/operator identity, admits shared latent fields/cross-covariance, and fails closed when those inputs are missing.

### Relative-velocity frame identity safeguard

The kinematical functional kernel now stores beta_RM_frame_id and beta_MO_frame_id in addition to their spatial basis IDs. It distinguishes an axis-only FrameTransport from a physical Lorentz/tetrad bridge. If the relative-velocity vector belongs to a different physical frame, its direct value remains available, but mixed functionals and beta_RO first-order closure return RELATIVISTIC_FRAME_BRIDGE_REQUIRED. A spatial 3x3 rotation cannot satisfy this requirement. A new regression test checks this boundary. Local pytest remains NOT_RUN.

### Independent numerical design check and runtime limit

A separate NumPy construction of the declared ideal local optical source-level Jacobian gave radial rank 9, transverse rank 8, joint 36x12 rank 12, and rank 12 after adding three duplicate triad-spin columns (36x15). A random improper O(3) fixture also checked the mixed-functional parity transformations. These are independent algebra fixtures, not executions of the posted Python module.

Desktop Commander was online but its first read-only configuration call returned the monthly usage-limit blocker and instructed no retry/reconnect. The committed module and tests therefore remain source/readback verified only; local import/compile/pytest are NOT_RUN.

