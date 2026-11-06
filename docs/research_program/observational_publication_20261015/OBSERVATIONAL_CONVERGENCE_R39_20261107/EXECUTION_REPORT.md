# R39 execution report

## Completed

- Verified the R38 remote branch and commit.
- Re-read R38 README, DAG, claim ledger, theory/data plans, execution report, scripts, likelihood adapters and selected result JSONs.
- Confirmed the conflict between R38's declared unexecuted status and its DAG/report completion claims.
- Inspected the default joint likelihood behavior and manual response-rank construction.
- Re-read high-leverage PRs #364, #365, #378, #394, #401, #402, #403, #360, #367, #368, #467, #468, #548, #550, #557, #563 and #564; this is a bounded high-relevance re-audit, not a line-by-line review of all 561 PR diffs.
- Re-read the pinned tensorized theorem, R9 model-to-data contract, R9 theory extension, and current R9 common code on the R39 branch.
- Applied vector/tensor x as the principal estimand in VECTOR_TENSOR_X_FRAMEWORK.md, README, theory synthesis, claim ledger, DAG and local-agent prompt. x_C is now an explicit scalar ablation only.
- Defined the common state, sample-axis contract, O(3)/SO(3) and parity action, cosmological functional registry, observation-operator Jacobian, local functional-identifiability criterion and set-valued image.
- Ran bounded prior-art research on CMB boost/intrinsic dipole, radio/quasar counts, covariant cosmography, Pantheon+, Gaia VSH/Bianchi-I and polarized Bianchi transfer.
- Corrected the two-frame non-collinear Lorentz velocity transform and improved its small-beta numerical coefficient; added regression tests.
- Wolfram independently checked the collinear limit and non-collinear exact example.

## Not performed

- No local raw data or maps/catalogues were accessed or rehashed.
- No public dataset was downloaded.
- No local pytest, package import, build, CI or Cobaya sampler was run.
- No new observed statistic, posterior, p-value, Bayes evidence or Bianchi family result was generated.
- No native Bianchi transfer solver was implemented or executed.
- No Remote Desktop or native subagent execution was used.

## Scientific decision

The current publishable candidate is conditional: a source-conditioned, frame-covariant response operator with a nuisance-projected functional-identifiable quotient across CMB, selected source counts and Gaia multipoles, preserving vector/tensor x and its joint set images. The tensorized HTT framework itself and the scalar x_C identity are prior project foundations, not claimed as new mathematics.

The next executable unit is local source/hash reconciliation and fail-closed single-probe implementation, followed by response-derived functional identification and the scalar x_C versus tensor-x ablation. R39 is not an observational convergence result.


## Expanded PR census and novelty correction

A complete GitHub metadata call returned 561 accessible PR records (#2–#564): 430 closed and 131 open, with update dates spanning 2026-07-22 to 2026-10-28. In total, 32 selected high-relevance PR bodies were read and 17 selected full diffs were retrieved. The remaining PR metadata were title/state/date screened only; no all-561 line-by-line diff audit is claimed.

Additional predecessor bodies reviewed: #7 (identifiability-aware low-ell pole kernel), #13 (correlated real-sky shell alm generator), #419 (canonical observable-irrep state), #442 (full-sky local boost pullback and STF2→STF3 response), #443/#444 (processed cut-sky boost design and source-equivalent synthetic execution), #449 (observable tensors and typed kinematical MES report), #533, #540, #544/#545, #552/#553 and #558/#559 (solver-free selection/geometry, CF4 source-window and Planck same-sky/mask/beam work).

This prior art narrows the novelty candidate: tensor x, observable-irrep state, local full-sky Lorentz pullback, STF2→STF3 harmonic coupling, low-ell pole statistics and generic tensor MES are already project predecessors. A remaining candidate is a validated, source-conditioned, processed multi-probe observation operator for the same typed physical state, with justified cross-covariance and a data-supported functional-identifiable quotient across CMB harmonics, selected source counts, Gaia VSH and finite-z distance carriers. It must be compared directly against the existing PR-442/443/444 and six-paper branches, not implemented as a parallel duplicate.


## LOOP C radial–transverse optical response integration

R39 re-read the existing LOOP C kinematics research source and reused its local optical inverse. The finite-source ideal response is now represented as radial \(d(n)=H+\sigma:nn-A\cdot n/c\) plus Fermi-Walker angular drift \(P\sigma n+n\times\omega\). The catalogue drift includes the explicit triad-spin nuisance \(\Omega\), so B1 measures \(\omega+\Omega\) and cannot separate these without an external frame calibration. This also makes clear why the leading radial distance likelihood is blind to vorticity while transverse astrometry may reopen that direction.

Added htt/src/common/kinematical_functionals.py and htt/src/common/test_kinematical_functionals.py. The source contains:
- direct physical theta state and velocity-jet projection adapter;
- direct/normalized/mixed tensor-functional values;
- O(3) transformation and basis-transport contracts;
- local radial/transverse prediction and unwhitened finite-source Jacobian.

The legacy R38 directional_hubble_variation was corrected so physical acceleration cannot be subtracted from a dimensionless Delta H/H: it now requires explicit \(A/(cH_0)\), or physical A together with H0 and c. Its regression test was added. Existing KinematicResponseModel.from_parameters is documented as first-order beta closure only.

The ideal local operator has analytic/symbolic structure inherited from LOOP C; finite-source numerical rank is checked by a new test fixture, but that test has not been run in this environment. No observed Gaia or CF4 likelihood, source selection, covariance or frame-spin calibration was executed.

## Kinematical theta and joint likelihood extension

The user clarified that x must include direct components of the physical congruence kinematics, not only a_lm and other observer-space data carriers. R39 now specifies the field-valued/basis-truncated state theta_K={sigma_AB, omega_A, A_A, beta_RM_A, beta_MO_A}, with beta_RO retained as a derived first-order closure view (exact ordered tetrad composition beyond first order). The pointwise independent core is 17 real components; optional DeltaOmega_k makes 18. These counts are coordinate dimensions, not data rank.

New artifacts:
- KINEMATICAL_LIKELIHOOD_MODEL.md: 1+3 decomposition with explicit c, direct and mixed kinematic functionals, source-conditioned CMB/count/SN/Gaia likelihood blocks, shared-latent dependence, full-covariance Fisher/identifiability and the five HTT outputs.
- KINEMATICAL_FUNCTIONAL_REGISTRY.json: machine-readable design registry for direct state blocks, mixed functionals, observer-space carriers, likelihood requirements and HTT outputs.
- VECTOR_TENSOR_X_FRAMEWORK.md and THEORY_SYNTHESIS.md updated to make direct theta and the likelihood-to-functional map explicit.
- LOCAL_AGENT_RESUME.md updated to require reuse of the existing physical kinematics and observable-irrep contracts and to implement the common likelihood rather than scalar adapters.
- RESEARCH_DAG.json and CLAIM_LEDGER.json updated with design-only status and claim ceiling.

One numerical representation check on a randomly generated improper orthogonal matrix verified that beta·omega flips sign, beta·sigma·beta remains invariant, and beta×omega transforms as a polar vector. This is a bounded algebraic fixture only, not a formal proof or production test.

The local optical relation is recorded as H_u(n)=vartheta/3-A·n/c+sigma_ab n^a n^b for sourceward n, with d_L=cz/H_u(n)+O(z^2) in the local optical domain. The leading symmetric radial projection is blind to vorticity. Observer-MO Doppler and intrinsic congruence acceleration remain separate channels.

No production TensorFunctionalBundle, CMB/count/SN/Gaia joint likelihood, source-bound cross-covariance, new posterior, observed kinematic estimate or native Bianchi transfer has been implemented/run. Local pytest/CI and Cobaya remain NOT_RUN.

### Relative-velocity physical-frame safeguard

The canonical adapter copies beta_RO, beta_RM and beta_MO from the canonical VelocityFrameBundle, where all three components share one coordinate_frame and basis. The radiation/matter/observer frame IDs are endpoint-role identities, not separate component coordinate systems. Spatial FrameTransport changes only the triad axes within that common coordinate frame; external vectors in a genuinely different component coordinate frame require a declared Lorentz/tetrad bridge. The recorded closure residual/status/remainder remain attached to the canonical state.

## Independent numerical and runtime-boundary checks

Using a separate NumPy calculation of the declared source-level optical design (not executing the committed module), the 36×12 radial+transverse Jacobian had rank 12; the radial nine-column sub-block had rank 9; the transverse shear+vorticity eight-column block had rank 8. Adding three catalogue triad-spin columns produced a 36×15 matrix still of rank 12, with the vorticity and triad-spin columns exactly duplicated. The minimum singular value of the 36×12 canonical-STF5 test design was 1.6379206921081488 in the declared mixed s^-1 parameterization. This is a manufactured finite-direction algebra fixture, not an observed Gaia/source response.

A separate random improper O(3) matrix numerically checked: beta·omega flips sign; beta^T sigma beta remains even; sigma beta and beta×omega transform as polar vectors. This checks the declared representation formulas on one finite fixture, not a formal proof or production runtime test.

Desktop Commander reported that its monthly usage limit had been reached when the local runtime configuration was queried; its response instructed not to retry/reconnect. Therefore local checkout inspection, import/compile and pytest are BLOCKED/NOT_RUN in this turn. No local test or CI pass is claimed.



## Canonical state/x integration hardening

The R39 physical-SI `KinematicalState` is an explicitly derived view of the exact canonical `JointAnisotropyState`, not a competing source state. `build_kinematical_x_bundle` evaluates the existing v1 `TensorFunctionalSpec/Result` operators on the canonical normalized state and the direct/mixed physical-SI functional family on the converted view. Both result lanes carry the same canonical `JointAnisotropyState.content_id`; the expansion scalar `Theta` and explicit `c` are recorded as view conversion inputs. The canonical beta_RO carrier/closure residual remain separate from the conditional first-order beta_RM+beta_MO sum.

The five shear components use the canonical Cartesian STF5 ordering `(Sxx,Syy,Sxy,Sxz,Syz)`, `Szz=-Sxx-Syy`. The ideal optical Jacobian basis derivatives are generated from this exact map. This basis is not orthonormal, so any numerical covariance/SVD downstream must use the induced Gram metric or an explicit orthonormal transform. Source code and new manufactured tests are committed/readback verified; runtime import/pytest remains NOT_RUN.


## Vorticity dual normalization boundary

The local optical kernel uses the standard axial dual omega_A=(1/2) epsilon_ABC omega^BC, hence omega_AB omega^AB=2 omega_A omega^A. The R39 functional `OMEGA_VECTOR_NORM2_H` is explicitly omega_A omega^A/H^2. It is not relabelled as the canonical MES W2 target omega_ab omega^ab/(6H^2), which would equal omega_A omega^A/(3H^2) under that dual convention. The K0 crosswalk's exact canonical omega_axial3 metric/normalization mapping is not proven by the current state schema, so no automatic MES W2 anchor binding or Q promotion is performed. The vorticity-vector norm is a typed x functional only.
