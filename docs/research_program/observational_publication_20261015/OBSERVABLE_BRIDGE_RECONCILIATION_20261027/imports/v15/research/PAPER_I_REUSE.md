# Paper I v15 reuse, replacement map, and entropy-controlled shear response

Owner: `/root/kinematics_loop_20261026`. Date: 2026-10-26. Source: `ANGULAR_CALCULUS_PAPER_I_v15_ACK_CLEAN_OVERLEAF.zip`, SHA-256 `c856939999ea202a5d676059907bfcef7274027299a2664fd55b86eecd69faad`, as recorded in `sources/paper_I/ARCHIVE_IDENTITY.json`. All 944 lines of the main TeX, ten section files and four appendices were read; bibliography entries relevant to entropy geometry, radiation moments, observer response and massive moments were inspected. This replaces the legacy Teff theoretical reference for this extension. No source, publication branch or dynamical solver was changed.

## R1. Question and achieved result

Which v15 statements can replace the earlier effective-temperature machinery, and can their entropy budget provide a useful conditioning certificate for the independently derived radiation-to-shear response?

The answer has three parts: a source-exact inventory; a replacement map preserving the prior A/B/C physical observables; and a proved **global entropy-controlled shear-response lemma**. In physical brightness notation, its main result is
\[
\boxed{\|\mathcal L_I-(8\rho/15)\mathrm{Id}\|_{\rm op}
\le\rho\sqrt{8\delta/3},\qquad
\delta:=\frac{k_B I_{{\rm ang},0}}{S_{\rm iso}}
=1-\langle w^{3/4}\rangle,\quad w=\frac{4\pi I}{\rho}.}
\tag{P1}
\]
It yields an explicit inverse certificate when \(\delta<8/75\). The scalar divergence inequality is established mathematics; the new project bridge is its normalization to v15 angular entropy, the mass-matched operator centering, and the resulting radiation/optical shear consistency contract. It does not assert a new universal positivity criterion or an observational result.

## R2. Exact v15 definition and theorem inventory

The table uses source labels, which remain stable even when compiled equation numbers change. `sections/` and `appendices/` below are relative to `sources/paper_I/`.

| Source | Definition or result; exact label | Premises and reuse consequence |
|---|---|---|
| `02_one_field_state_space.tex` | `eq:observer-split`: \(p^a=E_UU^a/c^2+q_Ue_U^a\), \(U^2=-c^2\). `eq:main-density-normalization`: \(d\Pi_z=\mathcal C_*u^2du,d\Omega\), \(\mathcal C_*=g_sE_*^3/[(2\pi\hbar)^3c^3]\). | Fixed observer, mass, reference energy and state-counting measure. This is observer-frame \(d^3q\), not an invariant scalar entropy measure. |
| Same | `eq:shape-functions`, `eq:entropy-functional`, `eq:bregman-def`: MB/BE/FD occupation, convex negative entropy \(H_\xi\), and its Bregman divergence. | Finite absolute entropy, admissible occupation endpoints; FD \(0\le f\le1\); singular Bose condensates excluded. Divergences have density units. |
| Same | `eq:directional-energy-density`: \(\rho_f=\mathcal C_*\int u^2\epsilon_z f,du\). `eq:Vl`, `eq:retained-moments`: real orthonormal harmonics through \(L\), \((L+1)^2\) energy moments. | Physical directional energy is \(E_*\rho_f\). Angular rank, radial energy weight and velocity degree are distinct indices. |
| `03_radial_quotient.tex` | `eq:fiber-equilibrium-stationarity`, `eq:ray-energy-monotonicity`, `eq:teff-family`: \(f_\rho^\sharp=\Phi_\xi(\epsilon_z\beta)\), \(T_{L,U}=T_{ref}/\beta\), with unique ray-energy inverse. | Energy-only constraints select zero log-fugacity. A number constraint changes the family and belongs to Paper II. A nonthermal ray still has an energy-calibrated temperature. |
| Same | `eq:main-contracted-entropy`: \(F=-b\rho-A(b)\), \(F'=-b\), \(F''=1/A''>0\). `eq:rho-beta-chain`: massless \(A=a_\xi\mathcal C_*b^{-3}\), \(\rho=3a_\xi\mathcal C_*b^{-4}\). | Fixed normalization; all three statistics have the same massless fourth-power energy law, with different coefficients. |
| Same | `eq:matched-physical-entropy-gap`, `eq:main-lift-identity`: spectral entropy gap and exact lift isometry for Bregman divergence. | Finite entropies and absolutely integrable score pairings. Compact positive inverse-temperature ranges suffice. |
| `03b_angular_response.tex` | `eq:physical-radial-response`, `eq:radial-temperature-derivative`: kernel response and derivative weighted by \(W=g(1+\xi g)\). `eq:kinetic-fisher-metric`: quadratic entropy metric. | Convergent radial integrals with differentiation justified; the detector/interaction supplies its actual kernel. |
| Same | `eq:angular-response-expansion`, `eq:dipole-induced-quadrupole`, `eq:dipole-quadrupole-product`, `eq:explicit-gaunt-coupling`. | Uniformly small bounded temperature deformation; temperature, log-temperature and inverse-temperature truncations generate different nonlinear coefficients. These couplings are already in v15. |
| Same | `eq:quadrupolar-ray-temperature`, `eq:quadrupolar-pressure`, `eq:quadrupole-entropy-cost` in §4. | Positive massless thermal rays \(T=T_0(1+aP_2)^{1/4}\), \(-1<a<2\). Zero flux, pressure anisotropy and the cost \(3a^2/160+O(a^3)\) are already derived. |
| Same | `eq:beam-mixing-spectrum`, `eq:energy-matched-mixing-residual`. | Positive normalized energy-independent beam; uniform small contrasts. Energy and number matching leave different spectral residuals. |
| `03c_massive_calculus.tex` | `eq:massive-velocity-hierarchy`, `eq:physical-energy-flux-stress`, `eq:massive-pressure-trace`, `eq:velocity-tensor-degree`. | General massive kinetic moments. Physical flux has an extra \(c\); stress uses \(v^2\). The hierarchy explicitly credits Lewis–Challinor (2002), eqs. (10)–(11). |
| Same | `eq:massive-mode-susceptibility`, `eq:massive-dimensionless-susceptibility`. | Isotropic regular thermal reference, fixed mass, linear temperature perturbation. One positive radial susceptibility for each angular rank. |
| Same | **Theorem `thm:main-poisson-factorization`**, with `eq:poisson-shell-action`, `eq:main-poisson-moment-factorization`, `eq:main-realizability-factorization`. | Positive normalized speed-shell Poisson operator has eigenvalues \(v^\ell\), preserves number/energy and FD bounds, contracts finite entropy. Dressed moment sets lie in direction-only sets; equal at \(z=0\) or \(L=0\); strict set and interior inclusion for \(z>0,L\ge1\). |
| Same / Appendix B | `eq:massive-flux-bound`, `eq:physical-flux-envelope`, `eq:two-band-kernel-witness`; `eq:poisson-cap-ratio`, `eq:interior-score-gram`. | Finite number and energy; concavity gives \(|F|\le\sqrt{\mathcal E^2-z^2\mathcal N^2}\). Compact-shell cap plus background establishes strict interior separation, including FD. This is an existing v15 theorem. |
| `04_two_axis_budget.tex` | **Theorem `thm:representative`**, `eq:beta-family`, `eq:diffeomorphism`. | For fixed \(z,\xi,L\), positive finite natural fields \(\beta_b\in V_L\) map smoothly and bijectively to the interior dual energy-moment cone. Finite-entropy regular representatives uniquely maximize entropy. |
| Same | `eq:exact-two-axis-budget`, `eq:adjacent-angular-budget`. | Finite entropies and score pairings: \(D_H(f\Vert f_L^*)=I_{spec}+I_{ang,L}\), and angular refinement subtracts the divergence between adjacent fits. These are existing matched-projection identities. |
| `05_refinement_obstructions.tex` | `eq:spectral-residual-family`, `eq:spectral-witness-fingerprint`; `eq:nonthermal-angular-direct`, `eq:nonthermal-angular-response`; score-span criterion. | Explicit positive MB witnesses separate spectral from angular refinement. On a compact band, bounded perturbations of an interior positive reference prove the score-span response test. |
| Appendix C | `eq:entropy-budget-tail-construct`, `eq:entropy-tail-moment-growth`. | Massless MB, exact number and energy, any positive entropy-distance allowance: regular positive tail sequences make every \(p>4\) response unbounded. This precise existing result requires a band/tail condition for such targets. |
| `07_physical_interpretation.tex` | `eq:detector-observation-map`, `eq:main-doppler-convention`, `eq:main-boost-leakage`. | Detector kernels include acceptance/speed. Massless scalar occupation gives \(T'=DT\), \(\beta'=\beta/D\). Positive affine \(V_1\) is boost closed; generic \(L\ge2\) natural fields leak to \(L+1\). |
| Appendix D | **Proposition `prop:conditional-observer-bound`**, `app:eq:boost-positive-patch` through `app:eq:first-boost-leakage`. | Common positive bounds on exact, fitted and raw-projected natural fields, plus \(H^1\) control. Information derivative, finite observer bound and leading leakage cost are conditional on that patch. |

Appendix A proves the radial endpoints, BE edge estimates, Bessel expansion, positive Hessian, angular boundary barrier and coercivity used by the representative theorem. The two named theorems and one named proposition above exhaust the numbered theorem environments in Paper I; other displayed results are unnumbered derived statements.

## R3. Legacy replacement map and conventions

| Earlier use | v15 replacement | Preserved physical distinction |
|---|---|---|
| A single Teff treated as a general spectrum | Energy-only ray section `eq:teff-family`, with \(I_{spec}\) retained separately | Nonthermal spectra have a bolometric calibration while energy-dependent rates still need extra spectral information. |
| Finite temperature multipoles treated as the entropy fit | Positive natural field \(\beta_b\in V_L\), theorem `thm:representative` | \(T=1/\beta\), \(I\propto\beta^{-4}\) and their harmonic truncations differ. |
| One scalar information-loss measure | Exact \((I_{spec},I_{ang,L})\) budget with stated domains | Neither refinement universally substitutes for the other. |
| Mechanical inference from a temperature Q alone | Kernel-calibrated brightness moments; v15 pressure example; prior Loop A operator | Radiation stress \(\pi\), optical shear \(\sigma\), temperature STF2 and diagnostic Q remain different quantities. |
| A frame-independent finite cutoff | State–observer–kernel tuple plus boost leakage and positive-patch comparison | Prior Loop B exact phase-space transform remains valid; inward propagation \(e=-n\) changes odd-mode signs. |
| Massive direction-only energy used for flux/stress | Physical \(v^\ell\) weights and positive shell factorization | Massive response needs radial/speed information. Poisson resolution parameter is not physical time. |
| Teff invoked as a dynamical closure/solver | Static reconstruction and declared response calculations | Prior Loop A transport residual and Loop C optical congruence are still independent physical inputs. |

Paper I uses \(U^2=-c^2\); prior A/B/C use unit \(u\), so set \(U=cu\). Both use \((-+++)\). Its angular \(e\) is photon propagation; the observed outward direction in B/C is \(n=-e\). Even radiation moments and the norm bounds below are unchanged. The present user direction selects v15 as the reference, replacing an earlier blanket “Teff legacy” research exclusion only within this scoped theoretical extension. It grants no source/publication/solver changes.

## R4. Candidate bridge and physical units

Let \(I(e)\ge0\) be physical bolometric energy density per solid angle, in J m\(^{-3}\) sr\(^{-1}\), with \(0<\rho=\int I\,d\Omega<\infty\). In Paper I notation \(I=E_*\rho_f\); for two equally populated photon helicities it agrees with Loop A's brightness normalization. Write \(I_0=\rho/(4\pi)\), \(w=I/I_0\), and \(\langle\cdot\rangle=(4\pi)^{-1}\int\cdot,d\Omega\).

The massless contracted entropy has the physical-coordinate form
\[
F^{phys}_\xi(I)=-C_\xi I^{3/4},\qquad
C_\xi=4a_\xi\mathcal C_*(3a_\xi\mathcal C_*E_*)^{-3/4}.
\tag{P2}
\]
This is merely `eq:rho-beta-chain` with \(I=E_*\rho_f\). Its units ensure \(k_B\int F^{phys}\) is entropy density. The isotropic entropy density is \(S_{iso}=k_BC_\xi4\pi I_0^{3/4}\). Because \(\int(I-I_0)=0\), the Bregman tangent term cancels and gives the exact \(\delta\) in (P1). For photons \(S_{iso}=4\rho/(3T_{iso})\).

This is the **angular** information of the energy-matched lift. The underlying \(f\) need not be ray thermal. Any spectral entropy gap is separate. A number-constrained thermochemical section changes the entropy function and must use Paper II's corresponding construction instead of importing (P2).

## R5. Proof of the new bridge

### Scalar divergence step, independently specialized

Define \(\varphi(t)=1-t^{3/4}+3(t-1)/4\), \(D(t)=(7+5t)/12\), and
\(G(t)=D(t)\varphi(t)-3(t-1)^2/32\). Direct differentiation gives
\[
G(1)=G'(1)=G''(1)=0,\qquad
G'''(t)=\frac{35}{256}(t-1)t^{-9/4}.
\tag{P3}
\]
For \(t<1\), integrating this negative third derivative backward from one makes \(G''\ge0\), then \(G'\le0\), then \(G\ge0\). For \(t>1\), all successive forward integrations are nonnegative. Thus
\[
\varphi(t)\ge\frac{3}{32}\frac{(t-1)^2}{D(t)}.
\]
Since \(\langle D(w)\rangle=1\), weighted Cauchy–Schwarz yields
\[
\delta=\langle\varphi(w)\rangle
\ge\frac3{32}\langle|w-1|\rangle^2.
\tag{P4}
\]
The continuous endpoint at \(t=0\) allows zero brightness; positive approximations handle that endpoint. This is the \(\alpha=3/4\) specialization of Gilardoni, [arXiv:cs/0603097](https://ar5iv.labs.arxiv.org/html/cs/0603097), Theorem 3 and Corollaries 4/6. The primary proof was retrieved on 2026-10-26 and the derivative criterion checked directly here. Its constant is sharp as a scalar probability inequality: equal-area two-level contrasts \(w=1\pm\varepsilon\) give \(\delta/\langle|w-1|\rangle^2\to3/32\).

### Centered shear-response step

Prior Loop A established the self-adjoint STF2 operator
\[
\langle S,\mathcal L_I T\rangle
=\int I\,[2(Se)\cdot(Te)-(e^TSe)(e^TTe)],d\Omega
=\int I\langle S,B_eT\rangle,d\Omega,
\tag{P5}
\]
with \(0\le B_e\le\mathrm{Id}\). This is a pointwise finite-tensor result, independent of thermality. Its isotropic average is \(\mathcal L_{I_0}=8\rho\mathrm{Id}/15\). Total-energy matching now supplies a stronger error estimate than an uncentered L1 bound:
\[
\mathcal L_I-\mathcal L_{I_0}
=\int(I-I_0)(B_e-\mathrm{Id}/2)\,d\Omega,
\]
\[
\|\mathcal L_I-\mathcal L_{I_0}\|_{op}
\le\tfrac12\int|I-I_0|\,d\Omega
=\tfrac\rho2\langle|w-1|\rangle.
\tag{P6}
\]
Combining (P4) and (P6) proves (P1). No compact amplitude ceiling on \(I\) is used. Set \(\eta=\sqrt{8\delta/3}\). The resulting finite-dimensional spectral bounds are
\[
\rho(8/15-\eta)\le\lambda_{min}(\mathcal L_I),\qquad
\lambda_{max}(\mathcal L_I)\le\rho\min(1,8/15+\eta).
\tag{P7}
\]
For \(\delta<8/75\), \(\eta<8/15\), so (P7) certifies invertibility and gives the corresponding condition-number bound by dividing its two sides. This threshold is sufficient, not necessary.

If \(\mathcal L_I\sigma=-R\), let \(\sigma_0=-15\widehat R/(8\rho)\) and \(\|R-\widehat R\|\le\varepsilon_R\). Subtraction gives the finite inverse estimate
\[
\boxed{\|\sigma-\sigma_0\|
\le\frac{\varepsilon_R/\rho+\eta\|\sigma_0\|}{8/15-\eta}.}
\tag{P8}
\]
Here \(\sigma\) has inverse-length units and \(R\) has energy density per length, as in Loop A. The operator proof is kinematic; using its transport equation retains Loop A's geodesic, irrotational, collisionless branch and its differentiability/integration conditions.

## R6. Sharpness, proof inspection and limiting cases

The scalar constant in (P4) is sharp. Centering by \(\mathrm{Id}/2\) is optimal given only the common scalar mass and pointwise operator range \([0,1]\): for a normalized off-diagonal STF test matrix, \(\langle S,B_eS\rangle\) attains both zero and one at suitable directions. This does **not** prove that their combined entropy-to-operator constant is sharp for brightness compared with the uniform sky. The half-area scalar extremizers need not optimize the tensor operator.

The uniaxial family already present in v15 makes the conservatism quantitative. For \(w=1+aP_2\),
\[
\langle|w-1|\rangle=\frac{2|a|}{3\sqrt3},\quad
\delta=\frac{3a^2}{160}+O(a^3),\quad
\|\mathcal L_I-\mathcal L_{I_0}\|/\rho=\frac{2|a|}{21}.
\]
The entropy bound behaves as \(|a|/\sqrt{20}\); its leading ratio to the true operator error is \(21/(2\sqrt{20})\simeq2.348\). At \(a=1.5\), the true normalized minimum eigenvalue is 0.390476 while (P7) gives 0.197485. This is useful but conservative.

A general small STF pressure perturbation gives another bridge. Put \(p=\pi/\rho\), and decompose \(w-1=(15/2)p:ee+r\), with \(r\) orthogonal to scalar and quadrupole harmonics. For uniformly small contrasts,
\[
\delta=\frac{45}{64}p:p+\frac3{32}\langle r^2\rangle
+O(\|w-1\|_\infty^3).
\tag{P9}
\]
The fixed-pressure minimal cost therefore starts at \(45\|\pi/\rho\|^2/64\); the rank-two energy-matched representative attains it to quadratic order. This generalizes v15's specific axisymmetric coefficient but uses its existing projection theorem and Fisher metric. It is a useful tensor form rather than a separate priority claim.

The source proof inspection checked Appendix A's integrable massless BE edge and \(b^{-3}\) angular barrier, Appendix B's FD interior perturbations, Appendix C's exact two-moment compensation and tail scaling, and Appendix D's second-argument Hessian and score cancellation. No concrete mathematical failure was found in these inspected steps. This is a bounded verification statement, not a certification of every possible extension. In particular, the observer proposition requires its raw projection to remain positive, and the tail example concerns \(p>4\), not the energy-fixed bolometric response (P5).

## R7. Executed finite checks

`cas/paper_i_check.wl` was run with the connected Wolfram Language evaluator. It returned `{0,{0,0,0},0,0}` for the derivative identity (P3), its three matching values, the coefficient \(45/64\), and the threshold arithmetic. The receipt is `cas/paper_i_check_wolfram_receipt.json`.

`python cas/paper_i_check.py` performed SciPy quadrature of ten exact quadrupolar states, checked (P4)–(P7), and approached the coefficient \(45/64\) with small amplitudes. It also integrated the positive even family \(w\propto e^{k\mu^2}\) in an orthonormal five-component STF basis. At \(k=8\), \(\delta=0.294552\) and the actual minimum response eigenvalue is \(0.128233\rho>0\), while the entropy lower bound is negative. This explicitly shows how a failed certificate leaves the actual operator test available. At \(k=20\) the actual value remains \(0.0501193\rho>0\). The states are smooth and positive; the stronger general positivity premise is directly available from Loop A rather than inferred from entropy.

The script records quadrature tolerances and finite results in `cas/paper_i_check_receipt.json`. All computations are toy quadratures or finite algebra; no transport ODE was solved. The analytic proof above establishes the general inequality; the toy values illustrate its scope and conservatism.

## R8. Reuse and novelty verdict

Existing v15 content includes its ray-energy calibration, massive Poisson theorem, representative theorem, exact information budget, kernel witnesses, pressure example, beam mixing and observer leakage. Those statements must be reused with their labels and conditions rather than counted as additional discoveries in the extended report.

The new bridge (P1), centered estimate (P6), inverse error (P8) and optical consistency use below are derived within this research unit. The scalar ingredient (P4) is existing Gilardoni mathematics with a self-contained specialization. Maximum-entropy radiation pressure and closure are already present in Minerbo, Cernohorsky–Bludman and Mascali–Romano; the primary source search also located Domínguez-Cascante's [anisotropic-radiation information analysis](https://arxiv.org/abs/cond-mat/9709104). Searches on 2026-10-26 did not establish that the exact shear-conditioning composition is a published theorem. Its independent literature novelty therefore remains open. Its present scientific value is concrete: v15's angular entropy now yields a dimensionally explicit bound on a physical inference operator, and states beyond that certificate can still use the measured five-dimensional spectrum.

No broad no-go is proposed. The pre-existing v15 witnesses and strict realizability theorem retain their original quantified domains. They do not change the physical premises of Loop A or the emitter/frame premises of Loop C.

## R9. Physical integration and observable contract

Use the same observer, epoch, bolometric normalization and sky support for (i) the radiation moments, (ii) v15 angular entropy, and (iii) any optical shear estimate. Let \(S_{opt}=c\sigma_{opt}\) be the inverse-time shear recovered by Loop C's E2 response, with \(\|S_{opt}-c\sigma\|\le\varepsilon_S\). Form
\[
\mathcal C=\widehat R+\frac{8\rho}{15c}S_{opt}.
\]
Under the common-congruence and Loop A transport assumptions,
\[
\boxed{\|\mathcal C\|
\le\varepsilon_R+\frac\rho c\varepsilon_S
+\frac{\rho\eta}{c}\|S_{opt}\|.}
\tag{P10}
\]
Indeed, subtract \(R+\mathcal L_I\sigma=0\), use \(\|\mathcal L_I\|\le\rho\), and apply (P1) to \(S_{opt}/c\). This provides a finite cross-channel consistency envelope without identifying a temperature quadrupole with matter shear. A frame/clock/source-motion uncertainty enters \(\varepsilon_S\) or the joint nuisance model, not the entropy gap by fiat.

The required inputs are physical \(I\) or its joint feasible image, its total \(\rho\), an upper bound on the normalized angular information, and \(\widehat R,\varepsilon_R\) for inversion. Frequency bands require a bolometric completion error; v15's high-energy witness remains relevant to that acquisition step. Neither a covariance law nor confidence coverage is created by (P1). For a joint set of allowed brightness/residual/calibration states, evaluate this deterministic map state by state before applying existing x/Q/support-F/exceedance-Pi/depth-G_F functionals. Missing spectral-law or derivative inputs remain explicit unavailable channels.

## R10. Checkpoint and high-value next lemma

The delivered candidate is **the mass-matched entropy-to-shear-response certificate** (P1)–(P8), with the optical application (P10). Its scalar proof and physical units are closed; the finite computations passed. Independent parent review should check the centering identity, entropy normalization, and the factor of \(c\) in (P10).

A high-value further lemma is a moment-aware optimum: minimize the v15 angular information at fixed quadratic form \(\langle S,\mathcal L_I S\rangle\), total energy and declared lower moments. Its target kernel is the explicit quartic polynomial in (P5), so v15's finite representative theorem supplies a positive rank-four natural field and a finite dual problem. This could replace the conservative L1 transfer by a response-specific entropy envelope. The other author's exact rank-four projection result is complementary: preserving all energy moments through four preserves \(\mathcal L_I\) exactly even when angular information remains above that cutoff. No new dynamical closure is required for either calculation.

한국어 요약: v15 논문 I 전체 본문과 부록을 읽고 정의·두 정리·관측자 비교 명제를 원래 label로 정리했다. 에너지 전용 각도 엔트로피를 실제 밝기 \(I\)의 정규화된 비등방성으로 바꾸면 \(\delta=1-\langle w^{3/4}\rangle\)이다. 기존의 발산도 부등식을 직접 검산하고 총에너지 일치에 따른 연산자 중심화를 결합하여 \(\|\mathcal L_I-8\rho\mathrm{Id}/15\|\le\rho\sqrt{8\delta/3}\)를 얻었다. \(\delta<8/75\)이면 전단 역사상의 유한 조건수를 보증하며 광학적 전단과 복사 수송의 일관성도 오차와 함께 검사할 수 있다. 이 문턱은 충분조건이며, 수치 예에서는 문턱을 넘은 양의 밝기도 양의 실제 반응 연산자를 갖는다. 새 기여는 이 물리적 연결이고, v15 정리나 기존 발산도 부등식의 신규성을 다시 주장하지 않는다.
