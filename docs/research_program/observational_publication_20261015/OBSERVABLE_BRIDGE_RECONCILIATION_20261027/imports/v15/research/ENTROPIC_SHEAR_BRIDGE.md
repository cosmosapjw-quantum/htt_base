# Entropy projection preserves the massless shear response at angular rank four

Internal conditional theory and executed static toy, 2026-10-26. Owner: common/obsstat for reconstruction and response algebra; MIO for a declared diagnostic image; HTT for any later posterior pushforward. Claim tier C0, transfer source none. No physical ODE, native solver, source-paper edit, repository push, or empirical CMB analysis is included.

## R1 — Question and achieved result

For massless radiation, exact energy-moment matching through angular cutoff L=4 preserves the complete five-dimensional radiative shear operator. This remains true when the unresolved angular entropy and radial spectral entropy are positive. Consequently an entropy projection may lose descriptive information while preserving this specified mechanical response exactly.

For L=2 or 3, only the unmatched energy hexadecapole affects the operator. On a declared bounded brightness domain, the reduced entropy curvature gives an explicit bound on that response error and, when transport derivatives are separately available, on the conditional shear inverse. A static maximum-entropy calculation below compares L=2 and L=4 and verifies the distinction numerically.

This research unit builds on the earlier Loop A positivity theorem. The general kernel-span principle and moment-matching existence are already in v15 Paper I; the present work specializes them to the exact shear operator, derives the response-specific error constant, and performs the finite projection experiment.

## R2 — Sources and comparison with v15

The source archive is ANGULAR_CALCULUS_PAPER_I_v15_ACK_CLEAN_OVERLEAF.zip, SHA-256 c856939999ea202a5d676059907bfcef7274027299a2664fd55b86eecd69faad, as recorded in sources/paper_I/ARCHIVE_IDENTITY.json. The following original source locations were read directly:

| v15 source | Reused mathematical content |
|---|---|
| §2, eq:directional-energy-density, eq:retained-moments | Physical brightness I=E_*ρ_f; retained moments are energy moments, not temperature coefficients |
| §3, eq:main-contracted-entropy, eq:rho-beta-chain, eq:main-lift-identity | Convex reduced entropy, massless three-quarter power, exact lift divergence |
| §3b, eq:quadrupolar-pressure and eq:kinetic-fisher-metric | Concrete mechanical angular response and local curvature interpretation |
| §4, thm:representative, eq:exact-two-axis-budget, eq:adjacent-angular-budget | Positive finite entropy representative; spectral/angular decomposition; refinement |
| §5, subsec:score-span-identification | A response kernel in the span of retained kernels is already determined |

The earlier research/LOOP_A_LOWELL.md in HTT_INTERNAL_THEORY_20261026 supplies the exact positive shear operator and its transport inverse. It reuses the attached Ellis textbook, PDF p. 299, Eqs. (11.1)–(11.2), and explicitly resolves the 2/7 versus 10/7 source discrepancy using angular Liouville transport.

Thus v15 already contains the abstract mechanism needed for exact preservation. It does not display the shear operator, the cutoff-four mechanical corollary, the rank-four Bregman-to-response constant below, or the executed L=2 versus 4 comparison. This is a bounded source comparison, not a literature-wide novelty claim. A new SciSpace query on entropy closures and response errors was also executed; its summaries were used for discovery only. The cited v15 source and inherited primary transport derivation support the equations here. The separate Paper I reuse study by the parent team owns the global isotropic entropy inequality; this report uses a finite-amplitude local curvature bound for an arbitrary finite projection.

## R3 — Physical and entropy conventions

Keep c, ħ and k_B explicit and use signature (−,+,+,+). V15 uses a physical four-velocity U·U=−c² and photon energy E=−p·U. Set u=U/c, so u·u=−1 as in Loop A. Its dot derivative is u·∇ per proper length cτ. Consequently shear σ and expansion Θ have units m⁻¹; their proper-time rates are multiplied by c. Angular directions are photon propagation directions e, opposite to outward sky directions.

For the two photon helicities,

\[
 I(e)=\mathcal D\int_0^\infty E^3 f(E,e)\,dE,\qquad
 \mathcal D=\frac{2}{(2\pi\hbar)^3c^3},\qquad
 \rho=\int I\,d\Omega .
 \tag{ES1}
\]

I has energy-density per solid-angle units; solid angle is dimensionless in SI. It differs from the energy-resolved radiance c𝒟E³f used in v15 §3b by the explicit factor c. The present I is the directional energy density used in the local moment equation.

Define q=∫Ie, π=∫I e_⟨a e_b⟩, H₃=∫I e_⟨a e_b e_c⟩ and H₄=∫I e_⟨a e_b e_c e_d⟩. Physical energy flux is cq. The entropy lift may be applied to an arbitrary nonthermal occupation with the specified regular finite-entropy assumptions: f itself need not be Planckian.

The photon energy-matched ray lift has

\[
 I=C_\gamma T_E^4,\quad C_\gamma=\frac{\pi k_B^4}{60\hbar^3c^3},
 \qquad h(I)=-C I^{3/4},\quad C=\frac{4C_\gamma^{1/4}}{3k_B}.
 \tag{ES2}
\]

Here 𝓗[I]=∫h(I)dΩ is negative entropy divided by k_B, with number-density units; S_ray=−k_B𝓗. The coefficient follows from s_ray=4I/(3T_E). Substitution of the v15 massless formula, with I=E_*ρ_f, gives the same C and cancels the arbitrary reference energy E_*.

For the quantitative estimate impose 0<I_min≤I,J≤M<∞ almost everywhere. Equivalently their energy-calibrated temperatures lie in a common compact positive interval, with T_E≤(M/Cγ)^(1/4). This supplies finite scores and a common curvature bound. It is an amplitude-domain assumption, not an assumption that all frequency-resolved spectra are thermal.

## R4 — The retained response kernels

On spatial STF2, let

\[
 \mathcal L_I S=\frac{8\rho}{15}S+\frac{10}{7}\operatorname{STF}(S\pi)-H_4:S
 =\int I(e) B_eS\,d\Omega,
 \tag{ES3}
\]
\[
 B_eS=2\operatorname{STF}(See^T)-\operatorname{STF}(ee^T)(e^TSe).
 \tag{ES4}
\]

Loop A proved self-adjointness and 0≤B_e≤Id. Each matrix entry of B_e is an even polynomial of angular degree at most four. Hence its only spherical harmonic sectors are ℓ=0,2,4. This is a statement about bolometric energy multipoles, not the low multipoles of T_E, log T_E, or β=T_ref/T_E.

Let f_L be the v15 entropy maximizer matching the complete energy moments through L and put J=I_L. Its inverse-temperature field belongs to V_L and is strictly positive on the stated interior moment domain. The resulting brightness generally contains harmonics beyond L. Matching measured moments and truncating the nonlinear brightness field are distinct operations.

## R5 — Exact preservation and an entropy error theorem

**Preservation theorem.** If ∫(I−J)Z_ℓm=0 for every retained harmonic through L≥4, then 𝓛_I=𝓛_J. More minimally, equality of the ℓ=0,2,4 energy moments suffices.

**Proof.** Each entry of B_e belongs to V₄, so the difference of the two angular integrals in Eq. (ES3) vanishes. Equivalently, Eq. (ES3) uses only equal ρ, π and H₄. This argument applies to any moment-matching representative, not only the entropy maximizer. Any radial redistribution that leaves I unchanged also leaves 𝓛 unchanged. Thus unresolved radial shape and higher energy multipoles may carry positive entropy costs while this operator is preserved. ∎

The reduced Bregman divergence is

\[
 D_{\mathcal H}(I\Vert J)=\int[h(I)-h(J)-h'(J)(I-J)]\,d\Omega .
 \tag{ES5}
\]

For the entropy representative, h'(J) is a fixed multiple of its fitted β∈V_L, so moment matching removes the tangent term. The physical angular entropy increment is ΔS_ang=k_B D_𝓗(I∥I_L). V15's exact two-axis budget supplies this identity and keeps the spectral cost separate.

**Finite-amplitude bound.** Direct differentiation gives

\[
 h''(I)=\frac{3C}{16}I^{-5/4}\ge\kappa_M:=\frac{3C}{16M^{5/4}} .
 \tag{ES6}
\]

Taylor's integral remainder along the segment between I and J therefore yields

\[
 \|I-J\|_{L^2(d\Omega)}^2
 \le\frac{32M^{5/4}}{3C}D_{\mathcal H}(I\Vert J).
 \tag{ES7}
\]

This uses the stated finite domain rather than a small-anisotropy expansion.

For every L≥2, ρ and π match, so δ𝓛=−δH₄:S. Let P₄ denote the orthogonal harmonic projector. The standard STF angular identity has coefficient

\[
 \Delta_4=\frac{4\pi\,4!}{9!!}=\frac{32\pi}{315},\qquad
 \|\delta H_4\|_F^2=\Delta_4\|P_4(I-J)\|_2^2 .
 \tag{ES8}
\]

To verify the second equality, write P₄(I−J)=A_⟨abcd⟩eᵃeᵇeᶜeᵈ. Orthogonality gives δH₄=Δ₄A and ∥P₄(I−J)∥²=Δ₄∥A∥². Contraction of a rank-four tensor with a unit STF2 has output norm at most its Frobenius norm. Combining this fact, Eq. (ES8), and Eq. (ES7) proves

\[
 \boxed{\|\mathcal L_I-\mathcal L_{I_L}\|_{\rm op}
 \le\epsilon_{\rm ent}:=
 \left[\frac{1024\pi}{945C}M^{5/4}D_{\mathcal H}(I\Vert I_L)\right]^{1/2}}
 \quad (L\ge2).
 \tag{ES9}
\]

Replacing D_𝓗 by ΔS_ang/k_B gives physical entropy units. Replacing it by the larger full spectral-plus-angular divergence is valid but loses the separation relevant to this response. At L≥4 the structural error bound is exactly zero and is sharper than a positive entropy-only estimate. The constant in Eq. (ES9) is sufficient; no optimality claim is made.

## R6 — Transport, shear error, and what matching does not supply

In a smooth geodesic irrotational congruence with collisionless radiation, the exact quadrupole equation is

\[
 \mathcal L_I\sigma=-R,\qquad
 R=\dot\pi_{\langle ab\rangle}+\frac43\Theta\pi_{ab}
 \;+\frac25D_{\langle a}q_{b\rangle}+D^cH_{abc}.
 \tag{ES10}
\]

Suppose an approximate residual R_L is supplied with ∥R−R_L∥≤ε_R. Set σ_L=−𝓛_J⁻¹R_L and λ_L=λ_min(𝓛_J). If λ_L>ε_ent, subtract the two equations and use the lower Rayleigh estimate for 𝓛_I:

\[
 \boxed{\|\sigma-\sigma_L\|\le
 \frac{\epsilon_R+\epsilon_{\rm ent}\|\sigma_L\|}
 {\lambda_L-\epsilon_{\rm ent}}.}
 \tag{ES11}
\]

Operator and denominator units are energy density, while R has energy-density per length units, so the output has shear units m⁻¹. For L≥4 use ε_ent=0. The remaining term is ε_R/λ_L.

Matching moment values at one event does not determine their spatial or time derivatives. If an exact L≥4 projection is instead defined on an open neighborhood in the same fixed smooth congruence, equality of q, π and H₃ as fields implies equality of their derivatives there, and hence of R. That stronger supplied-field construction preserves both sides of the transport relation. The local algebra alone does not produce the required observational jets.

The zero-density and narrow-support degeneracies remain those in Loop A. For positive full-sky I, λ_min(𝓛_I)>0; the usable lower certificate λ_min(ρh/3+π) is also preserved already at L=2. A common lower certificate can therefore survive while the actual operator changes through H₄.

## R7 — Executed finite entropy projection

The toy is the positive axisymmetric field

\[
 w(\mu)=I/I_0=1+0.3P_2(\mu)+0.2P_4(\mu)+0.15P_6(\mu),\quad
 \rho_0=4\pi I_0.
 \tag{ES12}
\]

Its exact polynomial minimum is 0.878125 and maximum 1.65. The fitted fields are w_L=β_L⁻⁴, with β_L=∑_even≤L b_ℓP_ℓ. The full harmonic solution reduces to this even axisymmetric subspace because the data have these symmetries and the v15 representative is unique.

The code minimizes the convex dual ⟨β⁻³⟩/3+∑b_ℓ⟨wP_ℓ⟩ using its analytic gradient and Hessian 4⟨β⁻⁵P_iP_j⟩. Newton steps enforce positivity over the entire polynomial interval using all real derivative roots, plus line-search descent. No kinetic evolution is integrated.

Fitting uses 96 Gauss–Legendre nodes and an independent refinement with 192. Evaluation uses 256 and 320 nodes; twelve azimuthal nodes integrate the degree-four operator exactly in azimuth. The largest retained-moment residual is 1.51×10⁻¹⁵. Coefficients and reported entropy/operator quantities change by less than 4.6×10⁻¹⁵ under refinement. These are numerical consistency checks, not interval quadrature certificates.

| Result | L=2 fit | L=4 fit |
|---|---:|---:|
| ΔS_ang/S_iso | 3.73709609×10⁻⁴ | 9.37160903×10⁻⁵ |
| Actual ∥δ𝓛∥/ρ₀ | 0.00654243536 | 1.23×10⁻¹⁵ |
| Curvature bound, Eq. (ES9), /ρ₀ | 0.0137593740 | 0.00689030783 |
| Structural preservation bound /ρ₀ | — | 0 exactly |
| Same-residual shear error /σ_ref | 0.00737521276 | 1.78×10⁻¹⁵ |
| Eq. (ES11) shear bound /σ_ref | 0.0280335840 | 0 exactly |

For the shear control, the true STF-basis coordinates are σ_ref(1,1,1,1,1)/√5 and R is manufactured from the target operator, with ε_R=0. The L=4 nonzero floating errors are roundoff; the structural theorem is exact. This control is explicitly algebraic and does not supply physical derivative data.

An independent exact axisymmetric identity is also checked: if c₄ is the unmatched P₄ brightness coefficient, then ∥δ𝓛∥/ρ₀=4|c₄|/105. Wolfram returned the corresponding eigenvalue slopes (−4/105,8/315,−2/315) for m=0,|m|=1,|m|=2. It also checked h'', Δ₄, and the coefficient 1024π/(945C).

The runnable script is cas/entropic_shear_projection.py; numerical and exact outputs are cas/entropic_shear_results.json and cas/entropic_shear_constants_results.json. The three-panel figure figures/entropic_shear_projection.pdf/.png displays the angular fits, positive entropy residual, and the disappearing operator error. It is an analytical toy, not measured CMB.

## R8 — Evidence verdict and failure correction

The preservation theorem and error bounds are DERIVED under their displayed assumptions. The projection is IMPLEMENTED and the scoped static toy passed its moment, positivity, entropy cancellation, independent operator identity, isotropic limit, inverse-error and resolution checks. The general theorem is supported by the proof, not by the finite sample.

The first numerical call failed because an einsum retained an azimuthal index after that index had been averaged away. Changing the contraction from n,npab,n to n,nab,n corrected the implementation; the full scientific checks then passed. One authoring-tool call had a JavaScript syntax error before creating its requested CAS file; a subsequent call created and executed the same bounded coefficient check. Neither failure changes the theoretical argument.

No strong no-go is asserted. The result identifies a sufficient retained set for one response. The v15 linear-span criterion is acknowledged as existing work; the explicit mechanical application and quantitative response bound are the extension documented here. Fresh independent review remains a separate parent-owned step.

## R9 — Reusable implementation contract

Inputs are a fixed observer/congruence, bolometric energy-moment convention, a positive interior moment vector, cutoff L, and—when invoking Eq. (ES9)—a common finite M and a reduced Bregman or angular-entropy defect. Outputs are the fitted β_L and energy moments, the symmetric 5×5 response matrix, its minimum eigenvalue, and the appropriate structural or entropy error certificate. Shear inference additionally consumes R_L and ε_R.

Record moment-fit errors separately from projection error. An approximate L=4 fit can have a small residual operator error bounded directly from its ρ, π and H₄ mismatches; exact preservation must not be assigned from cutoff metadata alone. Frequency-band data additionally require the bolometric completion and energy-boundary controls inherited from Loop A.

All tensorized diagnostics remain typed as before: legacy F_cert=x_C/U is a certified diagnostic rejecting material/volume occupancy; current F_sup is directional support utilization; F_ν is occupancy under a separately specified measure and support. The reduced entropy 𝓗 is none of these quantities. No new empirical law, occupancy measure, depth covariance, posterior or native transfer is inferred.

## R10 — Checkpoint and next use

The requested bridge, constants, proof, projection experiment, figure and reusable code are complete within the author unit. The next empirical use is to form the energy moments through ℓ=4 with their covariance and bolometric-error budget, then supply transport jets before evaluating the shear inverse. The original R32 morphology results and Loop A theorem remain unchanged.

한국어 요약: v15의 에너지 모멘트 일치 원리를 복사 전단 연산자에 구체적으로 연결했다. ℓ=0,2,4 에너지 모멘트를 보존하면 미해결 스펙트럼과 높은 각도 모드의 엔트로피가 남아도 전단 반응 연산자는 정확히 보존된다. L=2에서 남는 사중극차수 4의 오차는 제한된 밝기 영역의 엔트로피 곡률로 제어했다. 실제 정적 최대엔트로피 계산에서 L=4의 엔트로피 잔차는 양수지만 연산자 오차는 반올림 수준이었다. 전단의 관측적 역추론에는 여전히 복사 수송 미분값이 필요하다.
