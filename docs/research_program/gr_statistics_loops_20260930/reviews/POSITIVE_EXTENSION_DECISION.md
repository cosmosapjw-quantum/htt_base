# Independent decision: positive recovery and operational extensions

Date: 2026-09-30. Reviewer: `/root/gr_independent_decision`, separate from the two supplement proposers. This is a new decision for the user's additional supplied materials and requested constructive results. The earlier **18 GR and 12 statistical decisions remain unchanged**.

**The constructive results pass analytical review under their explicit information contracts.** Of the 16 supplement ledger records, 15 receive `PROMOTE_ANALYTIC_CONDITIONAL`; the still-unspecified full nonlinear CMB/parameter-identification target remains `HOLD`. Two of the 15 accepted records are adopted lemmas from supplied TEFF manuscripts, and one is the derivative-information limitation with its conditional replacement. They are distinguished from the fresh assemblies below. The operational book supplies six standard identity/scope checks, not six new research contributions.

## 1. What can now be recovered

1. The optical intercept and slope already recover the source value and symmetric derivative. **Two nonparallel, calibrated source-spatial derivative measurements recover the three missing vorticity components**, completing the first jet, with an explicit singular-value error bound.
2. Alternatively, **independently supplied radiation derivative and collision residuals recover vorticity through a finite quadrupole commutator**. One quadrupole with distinct eigenvalues suffices. Two nonisotropic axisymmetric channels with different axes can also suffice jointly. Only brightness moments through rank four enter the weak residual formula.
3. **A certified kinetic entropy budget, occupation envelope, and retained moments give a joint observable-error ellipsoid**, including selected moments of a specified linear collision operator. This provides a concrete residual set for a subsequent inverse.
4. Within a fixed common-shape thermal-mixture prior, **retaining number and energy gives a cubic-width certificate for calibrated smooth bandpass observables**, with measurement-error terms added explicitly.
5. If the spacelike homogeneous-orbit tangent distribution is independently known, the recovered source velocity yields its relative tilt by a normalized dual-wedge construction. The optical data do not themselves identify that distribution.

These are positive sufficient-information results. The added inputs must actually be measured, independently constrained, or bounded; the forward equations cannot be solved with a trial unknown and then reused as independent evidence for that unknown.

## 2. Inputs, provenance, and corrections

Actually read: `supplements/TEFF_POSITIVE_BRIDGE.md`, `supplements/TEFF_CLAIMS.json`, `supplements/DOSSIER_POSITIVE_BRIDGE.md`, `supplements/DOSSIER_CLAIMS.json`, and `ADDED_BOOK_INTEGRATION.md`. The reviewer checked the supplied TEFF Paper II text around Eqs. (24)–(31), Appendix B, and Eqs. (119)–(130), as well as the supplied manuscripts' identities and abstracts and the RBK book's opening statement of its reconstruction layers. The review does not certify all seven PDFs, all high-rank hierarchy coefficients, or the entire 404-page book. Input hashes are recorded in the companion JSON.

The TEFF papers and five dossiers are **user-supplied project manuscripts**, not automatically established external literature. The RBK book explicitly combines original-source excerpts, extracted claims, modern reconstruction, and commentary; its theorem numbers are project numbers. Its use here clarifies operational inputs. It does not replace a primary-source proof of an EPS or causal-reconstruction theorem.

| First finding | Correction or retained boundary |
|---|---|
| TEFF Eq. (A6) initially omitted the plus sign before the uncertain-moment term. As printed, the product would fail even when matching error is zero. | The proposer corrected it to `sqrt(2ε)||K-a·φ||_W + |a·Δm|` before the reviewed final snapshot. The two terms have different sources and must be added. |
| The book addendum initially wrote `I=1+Z0`, conflicting with the packet's definition of `Z0` as the full redshift factor at the vertex. | Root corrected it to `I=Z0=m+b·n` before the final snapshot. |
| A transport-Fisher bound controls a differentiated moment only after handling the kernel and measure derivatives. | Accept the displayed bound where the parallel-tetrad/fixed-kernel construction makes these contributions vanish. Any nonzero differentiated-kernel/measure contribution must be added separately. |
| Dossier vorticity and rotating-tetrad symbols can share a letter. | The recovery uses derivative-first source vorticity, not arbitrary tetrad spin. The common transport reference is an essential input. |

## 3. TEFF decisions

| Claim | Decision and exact accepted scope | Evidence origin |
|---|---|---|
| TEFF-A0 | **PROMOTE_ANALYTIC_CONDITIONAL.** The stated regular, finite-divergence number–energy representatives give the nested Bregman identity under the same measure, observer and moment map. | Adopted project lemma; independently checked matched-moment cancellation. No whole-paper certification. |
| TEFF-A1 | **PROMOTE_ANALYTIC_CONDITIONAL.** A divergence bound and the pointwise reciprocal-Hessian envelope imply the finite-amplitude moment-residualized observable bound, with the displayed weighted integrability and matching assumptions. | Fresh assembly of standard convexity and projection arguments. |
| TEFF-A2 | **PROMOTE_ANALYTIC_CONDITIONAL.** All channels sharing the same state pair, entropy bound, envelope and moment constraints obey `e in range(R)` and `e^T R†e≤2ε`. Singular Gram matrices are allowed. | Fresh simultaneous residual representation. |
| TEFF-A3 | **PROMOTE_ANALYTIC_CONDITIONAL.** Replacing channel kernels by a specified linear collision adjoint gives the corresponding collision-moment ellipsoid; a retained adjoint kernel gives an exact moment. | Fresh conditional application; not nonlinear collision closure. |
| TEFF-A4 | **PROMOTE_ANALYTIC_CONDITIONAL.** The common Planck upper envelope produces the displayed infrared-integrable and exponentially decaying weight for bounded-angular, nonnegative polynomial-energy kernels. | Direct endpoint/integrability proof. |
| TEFF-B1 | **PROMOTE_ANALYTIC_CONDITIONAL.** Under the fixed probability-mixture support and calibrated `C³` response, the number–energy estimator has the stated cubic remainder bound. The energy-only comparison has the stated quadratic bound. | Fresh bandpass extension of a standard Hermite-interpolation mechanism. |
| TEFF-B2 | **PROMOTE_ANALYTIC_CONDITIONAL.** Under the fixed positive support and feasible number–energy moments, the stated moment intervals, positive-interval relative-minimax predictor, and possible failure of the entropy-selected reference to remain in that prior are accepted. | Adopted project result, with bounded independent analytic checks below. Reported numerical percentages are not recertified. |
| TEFF-H1 | **PROMOTE_ANALYTIC_CONDITIONAL.** Static entropy/angular information does not by itself control spacetime derivatives; the explicit horizontal-transport Fisher budget supplies the stated conditional derivative bound after kernel/measure terms are handled. | Counterexample and standard Cauchy–Schwarz replacement. |
| TEFF-H2 | **HOLD.** Full nonlinear CMB collision accuracy and cosmological parameter identification remain unspecified targets. | No adequate collision, medium, propagation, data or inverse-rank contract for that stronger claim. |

### Finite-amplitude ellipsoid

For the stated kinetic entropies, `h''(z)=1/[z(1+ξz)]`. The envelope on every segment between the two occupations gives

`d_h(f||g) ≥ (f-g)²/(2W)`.

Integrating and applying weighted Cauchy–Schwarz yields the scalar bound. Exact moment matching permits subtraction of any retained score combination, so orthogonal projection gives the best bound within their span. Applying it to every linear combination of target channels gives `|a·e|²≤2ε a^T R a`. A null vector of `R` annihilates `e`; on its range, substitution of `a=R†e` proves the ellipsoid inequality. This argument is finite-amplitude and does not invoke Fisher linearization.

The Planck envelope behaves as `W=O(E^-2)` at zero energy, so multiplication by the massless `CE²dE dΩ` measure removes the infrared singularity. The exponential tail handles the stated polynomial kernels. Both the unknown state and its reference must satisfy the envelope. Neither the envelope nor the divergence of the unknown state follows from fitting a bolometric temperature.

The displayed elastic scalar scattering kernel is normalized and has eigenvalues `p0=1`, `p2=1/10`, and zero at other ranks. Thus its adjoint action is exactly `τ(E)(p_l-1)` on the stated separated kernels. This verifies the restricted example, including the exact retained-moment case for constant rate. It does not license replacement of polarized or energy-redistributing collisions by that model.

### Bandpass certificate and adopted moment identities

Independent substitution confirms that `q(y)=c0+c3 y³+c4 y⁴` matches the response's value, first derivative and second derivative at one. Its third derivative is `6c3+24c4 y`; Taylor's integral remainder and the support bound prove the cubic certificate. The energy-only polynomial matches one fewer derivative and yields the stated quadratic certificate. Both comparisons use the same target and support prior. Exact retained-span responses and special boundary data are allowed exceptions to the generic order comparison.

For the adopted Bregman split, the difference of entropy gradients of the two regular representatives is a linear combination of number and energy scores. Its contraction with the matched residual is zero, giving the three-point identity's exact cancellation. This checks the lemma used here without certifying all other claims of either TEFF paper.

For the adopted sharp moment intervals, the lower interpolant in `span{1,y³,y⁴}` agrees with `y^p` at `a` and agrees in value and derivative at `u`; the upper interpolant agrees in value and derivative at `d` and in value at `b`. For `p>4`, the derivative of the difference divided by `y²` is a strictly convex function of `y`. Its two zeros force the lower interpolation error to be nonnegative and the upper error nonpositive on the support. The endpoint/interior two-point measures match the specified moments and attain the bounds. Monotonic secant slopes of `x^(4/3)` give the required interior nodes for the stated interior feasible data. Boundary cases are limits. This establishes the needed continuum bounds independently of a numerical grid.

On a positive interval `[L,U]`, equalizing worst relative error at the two endpoints gives `2LU/(L+U)`, with relative error `(U-L)/(U+L)`. The warning about a changed-fugacity MaxEnt reference is substantive. In the Maxwell–Boltzmann case its `p>4` prediction is `m4^(p-3)/m3^(p-4)`. Jensen's inequality for the probability measure proportional to `y³ dπ` puts every nondegenerate fixed-prior response strictly above this quantity. Compact support makes the minimum attained. Thus interior fixed-prior data can indeed place that reference below the admissible response interval, without relying on the manuscript's decimal examples.

## 4. Dossier-based positive inverse decisions

All seven DP claims receive **PROMOTE_ANALYTIC_CONDITIONAL**. The forward dossiers motivate the inputs, but the proof review uses the supplement's explicit local equations and finite-dimensional inverses.

| Claim | Exact accepted statement |
|---|---|
| DP01 | Given the stated independently determined local derivative vectors and optical symmetric rates, two nonparallel source-spatial directions determine all three vorticity components by the displayed normal-matrix inverse. |
| DP02 | The fixed-direction error bound and the perturbed-operator bound hold with the stated positive singular-value denominator and, for operator uncertainty, a true amplitude bound. |
| DP03 | With independently supplied horizontal brightness derivative and collision moments in one physical frame, the stated residual has second moment `[M,W]`. Distinct eigenvalues of `M` give a unique inverse; the weak formula uses brightness moments through rank four. |
| DP04 | The exact and perturbed quadrupole inverse bounds hold in the stated Frobenius/operator norms, with all optical, radiation, collision, transport and boundary errors included in the residual budget. |
| DP05 | Stacked channels are injective exactly when their antisymmetric commuting subspaces intersect trivially. Two nonisotropic axisymmetric channels with nonparallel axes suffice if each has its independent residual. |
| DP06 | The stated restricted coherency Thomson map has the conservative `5Γ/2` operator bound, and the scalar product quadrature is exact under the displayed true bandlimits and degree requirement. |
| DP07 | Independently supplied spacelike homogeneous-orbit generators determine the future unit normal through the dual wedge; the recovered source velocity then determines its relative Lorentz factor and tilt. |

### Signs, ray derivatives and the finite inverse

Because the derivative index comes first, contraction of the antisymmetric derivative with a spatial vector is `-W x`, not `W x`. Hence `J(x)-Dx=-Wx=ω×x`. The triple-product identity produces `G=Σw(I-xx^T)`; its quadratic form is `Σw|v×x|²`. It is positive precisely when the supplied directions are not all parallel. The advertised inverse and singular-value bounds follow directly. The explicit three-component formula has the correct signs.

For the radiation route, put `L=U+ce`. Photon geodesicity gives `∇_L L=R L` and `L ln E=-R`. The spatial derivative of `U` along `L` is `A+c(De-We)`, giving

`h∇_L e=-P_e(A/c+σe)+We`.

Integrating the energy derivative against `E³` gives the factor four, subject to the declared endpoint terms. This is a ray transport identity with a separately defined horizontal derivative, not observer-time image drift.

The sphere field `We` is divergence-free. Integration by parts therefore gives `R=MW-WM`, whose off-diagonal entries in an eigenbasis of `M` are `(m_i-m_j)W_ij`. Independent expansion of the weak residual confirms Eq. (B5), including cancellation of the acceleration-direction coefficient multiplying `ee^T`. This removes angular differentiation; it does not manufacture the independent spacetime derivative moment.

The commutator's three singular values are the absolute pairwise eigenvalue gaps in the stated Frobenius norms. The perturbation estimate follows from `||[ΔM,W]||F≤2||ΔM||op||W||F`. For stacked channels the displayed Gram matrix is their normal matrix. In the axisymmetric example, `R_j n_j/β_j=ω×n_j`, confirming the reduction to the direct-channel inverse and the need for nonparallel axes.

### Collision, quadrature, readout and tilt

The coherency gain has operator norm at most `3/2` by Cauchy–Schwarz and the contraction of orthogonal screen projections; adding the loss gives `5/2`. This bound is useful for propagating a coherency error in the declared cold, elastic, rest-electron regime. It is not a theorem about an unknown collision operator. Polarization and electron-frame information cannot be discarded when they alter the gain.

For the scalar angular quadrature, products in the weak equation have total spherical-polynomial degree at most `max(L+4,LC+2,LT+2)`. The azimuth grid removes every nonzero Fourier order through that degree; the remaining polynomial is integrated exactly by the stated Gauss–Legendre order. Tails, masks and nonpolynomial coefficients require separate bounds.

The auxiliary remote-readout statement is also correct: a lower response bound `β` on the three-dimensional commutator range, combined with a commutator gap `δ`, gives a composite lower singular value at least `βδ`. A mere upper norm bound on a propagator does not provide that result. Finally, the dual-wedge normal has squared norm `-det Gram` and is orthogonal to every supplied orbit generator, giving the stated conditional tilt construction. This does not identify an orbit distribution from local optics.

## 5. Operational book addendum: standard identities verified

The following are accepted as standard mathematical identities or scope requirements, not new theorem-priority claims. The corrected `ADDED_BOOK_INTEGRATION.md` was used for the final snapshot.

| Existing ID | Decision and clarification |
|---|---|
| AB-T1 | **PASS_STANDARD.** Constant `g→λ²g` preserves the redshift factor and relative velocity, scales distances by `λ`, and scales measured tetrad rates and acceleration norm by `λ^-1`. Covariant coordinate components of `B` scale by `λ`; contravariant coordinate acceleration scales by `λ^-2`. |
| AB-T2 | **PASS_STANDARD.** The source second-ray-derivative bound and the screen optical tidal norm scale by `λ^-2`; the length endpoint scales by `λ`. The dimensionless Jacobi/Taylor certificate is therefore covariant under the common constant scale. |
| AB-T3 | **PASS_STANDARD.** For variable conformal factor, `A'^a=e^-2φ(A^a+c²h^{ab}∇_bφ)`. Null paths are preserved but timelike geodesicity need not be. Endpoint redshift changes by `exp(φ_o-φ_e)` for the stated eikonal correspondence, so this is not an equal-calibrated-data counterexample. |
| AB-T4 | **PASS_STANDARD.** A synchronization coordinate change applied consistently to the same tensors preserves scalar observables and relative rapidity. |
| AB-T5 | **PASS_STANDARD.** Replacing the physical observer changes the measured energy/direction pattern; this is distinct from changing coordinates or tetrad components for the same observer. |
| AB-T6 | **PASS_SCOPE.** Absolute dimensionful output needs the corresponding calibrated metric/clock/distance inputs. If only constant scale is missing, report its orbit; if the full conformal representative is missing, the larger ambiguity cannot be reduced to a constant scale without further assumptions. |

The conformal acceleration formula follows by inserting `U'=e^-φU` into the standard connection difference. The terms involving `U(φ)U` combine with `c² grad φ` into the spatial projector. A common constant scale is its special case. The source/observer energy normalization yields the stated endpoint frequency factor. These checks do not establish the converse claim that arbitrary causal data uniquely determine a calibrated metric, nor do they recertify the book's reconstruction program.

## 6. Limits, novelty, and closeout

The positive extension is analytically complete at its declared gates. Its strongest useful feature is a **specified path from additional information to a finite inverse or error set**, with the missing vorticity components explicitly recovered under two different information contracts. The TEFF bounds can supply selected deterministic collision/observable residual constraints for those inverses when their state and medium assumptions hold. They do not themselves supply spacetime derivative data, a response matrix, or its lower singular value.

No static sky is newly proved to determine all twelve kinematic rates without additional input. No trial-parameter solution of a forward equation becomes independent evidence. No supplied manuscript is recertified wholesale. No real-data recovery, full nonlinear CMB accuracy, optimality of every bound, or original publication priority is established.

Standard convexity, interpolation, transport, commutator and pseudoinverse principles underlie the results. The explicit physical assembly is useful, but its novelty remains **UNESTABLISHED / NO PRIORITY CLAIM**. The earlier decisions remain intact, and no further scientific runtime is required to establish the bounded analytic statements reviewed here.
