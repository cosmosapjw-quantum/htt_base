# Detector-specific response bounds after number–energy calibration

**Evidence status:** derived finite-amplitude extremizer identity; literature-supported convex-duality method; implementation-verified MB/BE/FD static toy. This chapter extends the v15 calibrated-kernel discussion into a computable response interval. It uses no transport solver.

## R1 — The physical question

Two measured moments can calibrate a ray's population and energy while leaving its detector response uncertain. Paper II already identifies the residual kernel after projecting out number and energy. The useful next step is to compute how far that response can move within a declared spectral entropy budget, while preserving the measured moments exactly.

For a finite detector band this yields an actual upper/lower response frontier. It can replace an arbitrary coordinate-space nuisance radius with a radius tied to the kinetic entropy of compatible states. The entropy budget remains an input to be measured or physically justified.

## R2 — Source and retained result

The input is Paper II v15, sections 02, 03 and 05: the fixed-observer number–energy calibration, the spectral–population information split, and the Fisher projection of a response kernel on the retained moment span. Paper I v15 section 05 and Appendix C explain why an unfiltered superlinear high-energy kernel needs an additional tail condition. We use a bounded detector kernel.

The optimization mechanism is standard convex information geometry. Related expectation bounds and local square-root divergence expansions are developed by Henry Lam, *Robust Sensitivity Analysis for Stochastic Systems*, Mathematics of Operations Research 41 (2016), DOI [10.1287/moor.2015.0776](https://doi.org/10.1287/moor.2015.0776), [arXiv:1303.0326](https://arxiv.org/abs/1303.0326), and by Dupuis, Katsoulakis, Pantazis and Plecháč, *Path-space information bounds for uncertainty quantification and sensitivity analysis of stochastic dynamics*, [arXiv:1503.05136](https://arxiv.org/abs/1503.05136), DOI [10.1137/15M1025645](https://doi.org/10.1137/15M1025645). The particular application below preserves kinetic number–energy constraints and all three occupation statistics. General entropy duality is not a novelty claim.

## R3 — Occupation, units and admissible response

Fix one observer and one ray. For a massless species,
\[
d\nu_U=\mathcal D E^2\,dE,\qquad
\mathcal D=\frac{g_s}{(2\pi\hbar)^3c^3}.
\tag{F1}
\]
Angular integration can be added for a declared angular channel. Let \(h_\xi\) be the v15 convex negative-entropy density and \(g\) a regular reference, with \(0<g<1\) for FD and \(g>0\) for MB/BE. Its score and fluctuation weight are
\[
s_0=h_\xi'(g),\qquad W=[h_\xi''(g)]^{-1}=g(1+\xi g).
\tag{F2}
\]
Use \(\xi=0,+1,-1\) for MB, BE and FD respectively. Let \(\phi=(1,E)^T\), and impose \(\int\phi f\,d\nu_U=\int\phi g\,d\nu_U=m\). The divergence
\[
D(f\Vert g)=\int[h_\xi(f)-h_\xi(g)-s_0(f-g)]\,d\nu_U
\tag{F3}
\]
has number-density units; \(k_BD\) has entropy-density units. A dimensionless bounded kernel \(K(E)\) defines \(\mathcal O_K(f)=\int Kf\,d\nu_U\), also with number-density units.

Assume the required integrals and score pairings are finite. The response family below must remain in the regular entropy domain, and its number–energy moment Jacobian must be nonsingular locally. For BE this includes the sign/domain of the score; for FD it includes the occupation cap.

## R4 — Finite-amplitude construction

Choose a signed response multiplier \(t\) and solve the two moment equations for \(\lambda(t)\):
\[
h_\xi'(g_t)=s_0+tK-\lambda(t)^T\phi,\qquad
\int\phi g_t\,d\nu_U=m.
\tag{F4}
\]
At \(t=0\), \(g_0=g\) and \(\lambda(0)=0\). In explicit form,
\[
g_t=(h_\xi')^{-1}(s_0+tK-\lambda^T\phi).
\tag{F5}
\]
For MB this is an exponential tilt; BE and FD use the corresponding quantum occupation inverse. Only two static calibration variables are solved at each \(t\). No time evolution is involved.

## R5 — Exact response-frontier identity

**Proposition F1.** Suppose \(g_t\) exists in the stated regular domain and has the same retained moments as \(g\). For every compatible \(f\),
\[
D(f\Vert g)
=D(f\Vert g_t)+D(g_t\Vert g)
+t[\mathcal O_K(f)-\mathcal O_K(g_t)].
\tag{F6}
\]
Consequently, at budget \(\epsilon_t=D(g_t\Vert g)\), \(g_t\) attains the largest compatible response when \(t>0\), and the smallest when \(t<0\).

**Proof.** Expand the three Bregman terms and cancel their common entropy contributions. The remaining cross term is
\[
\int[h_\xi'(g_t)-h_\xi'(g)](f-g_t)\,d\nu_U.
\]
Insert (F4). Its \(\lambda^T\phi\) part vanishes by exact moment matching; its remaining part is the last term in (F6). If \(D(f\Vert g)\le\epsilon_t\), nonnegativity of \(D(f\Vert g_t)\) gives
\[
t[\mathcal O_K(f)-\mathcal O_K(g_t)]\le0.
\]
The reference \(g_t\) itself is feasible and reaches equality. Strict convexity identifies the equality state up to null sets. This proves attainment for every constructed regular \(t\), without assuming that all conceivable entropy budgets are covered.

The construction applies to a signed linear combination of several detector channels. Thus repeating (F4) for support directions builds the boundary of a joint response set rather than independent marginal intervals.

## R6 — The calibrated Fisher coefficient

Define
\[
G=\int W\phi\phi^T\,d\nu_U,\qquad
b_K=\int W\phi K\,d\nu_U,\qquad
K_\perp=K-\phi^TG^{-1}b_K.
\tag{F7}
\]
Differentiating the moment equations at zero gives \(\lambda'(0)=G^{-1}b_K\), and therefore
\[
\dot g_0=WK_\perp,\qquad
\chi_K=\left.\frac{d\mathcal O_K(g_t)}{dt}\right|_0
=\int WK_\perp^2\,d\nu_U.
\tag{F8}
\]
The cross term vanishes because \(K_\perp\) is orthogonal to both retained scores. If the family is sufficiently smooth,
\[
D(g_t\Vert g)=\frac{t^2\chi_K}{2}+O(t^3),\qquad
\mathcal O_K(g_t)-\mathcal O_K(g)=t\chi_K+O(t^2).
\tag{F9}
\]
For \(\chi_K>0\), the two local frontiers are
\[
\mathcal O_K^\pm(\epsilon)
=\mathcal O_K(g)\pm\sqrt{2\epsilon\chi_K}+O(\epsilon).
\tag{F10}
\]
The square-root term is an asymptotic approximation, not a finite-budget upper bound. Equation (F6) gives the finite-amplitude result.

For several kernels, the residual susceptibility is the Schur complement
\[
C^\perp_{ij}
=\int WK_iK_j\,d\nu_U-b_i^TG^{-1}b_j.
\tag{F11}
\]
It is positive semidefinite. A null direction means the corresponding response combination belongs to the retained score span almost everywhere in the positive weight; that combination is already fixed by calibration. This is the computational connection to the v15 response criterion.

## R7 — Static toy experiment

The executable experiment uses \(x=E/(k_BT_*)\), measure \(x^2dx\), and
\[
K(x)=\exp[-(x-4)^2/(2\times0.8^2)].
\tag{F12}
\]
It compares MB with \(\eta_0=0\), BE with \(\eta_0=-0.5\), and FD with \(\eta_0=1\), all at inverse-temperature coefficient one. Every trial preserves its own reference number and energy. The detector is illustrative; it is not a fit to an instrument.

The code solves two nonlinear algebraic equations at each signed \(t\), evaluates both frontiers, checks the exact three-point identity on positive moment-preserving competitors, and repeats quadrature at 32 and 128 nodes per subinterval. It records the remaining inverse-temperature margin and compares the calibrated Fisher width with the unprojected kernel width.

Response changes, divergence budgets and susceptibility coefficients in the plotted results are normalized by the reference ray number. Write \(n_0=\int x^2g\,dx\), returned as the unnormalized dimensionless `number`; physical ray number is \(N_{\rm ref}=\mathcal D(k_BT_*)^3n_0\). Multiply the normalized response, divergence and susceptibility by \(N_{\rm ref}\) to restore physical units. The returned `energy` is the unnormalized integral \(\int x^3g\,dx\), whose physical conversion is \(\mathcal D(k_BT_*)^4\). An energy-valued detector kernel carries its additional declared energy unit. The numerical integration covers \(0\le x\le64\) with exponentially small reference tails. The record separates this floating-point quadrature from the continuum proof.

The actual toy output is:

| Statistics | \(\chi_K/N_{\rm ref}\) | Projected/unprojected local width | Maximum relative moment residual |
|---|---:|---:|---:|
| MB | 0.10447052 | 0.70324332 | \(7.41\times10^{-16}\) |
| BE | 0.10034471 | 0.71016168 | \(1.06\times10^{-15}\) |
| FD | 0.10611575 | 0.67370767 | \(1.03\times10^{-15}\) |

The 32-versus-128 quadrature comparison changed the selected frontier values by at most \(1.77\times10^{-13}\). The three-point identity residual was below \(6.25\times10^{-16}\) after number normalization. These are numerical checks of the specified toy and do not set an observational error budget.

## R8 — Meaning of the result

The projected kernel is the spectral redistribution the detector can see after number and energy have been held fixed. Its Fisher norm measures the leading information cost of that redistribution. The finite-amplitude extremizer answers a sharper question: which positive compatible spectrum produces the greatest detector change at the assigned entropy budget?

An unprojected variance counts changes in already measured population and energy as if they were unknown. The Schur complement removes those directions. Conversely, declaring a zero budget would assume that the calibrated spectrum is exact. A real application must supply the residual budget or infer it jointly from additional spectral channels.

## R9 — Connection to the previous HTT report

The earlier bandpass geometry permits finite moment/error regions but leaves their physical radius to an external model. Equations (F6) and (F11) provide one such physical family: positive occupations with calibrated moments and a stated kinetic entropy allowance. A support direction in the tensorized \(x\) coordinates defines a corresponding linear combination of kernels \(K_i\), so the same static solve produces support values for \(F_{\rm sup}\) or a gauge relative to a declared body.

The statistical law and kinetic entropy are distinct inputs. A deterministic entropy-budget region is not automatically a confidence region. To obtain coverage, propagate an actual likelihood or a separately calibrated confidence event for the moments, detector response and entropy allowance.

This extension is especially useful for bounded CMB bandpasses and other finite spectral channels. Paper I's high-energy-tail construction remains the correct boundary for unfiltered superlinear rates. A measured tail constraint can be included as another component of \(\phi\).

## R10 — Scientific position and next decisive comparison

The general variational method and local Fisher projection have clear prior art. The contribution worth developing is the combined quantum-statistical, detector-specific response construction coupled to an actual HTT observable and uncertainty budget. The next decisive calculation is a bandpass response built from a real published instrument kernel, with shared calibration and angular response, compared at equal accuracy with the earlier unconstrained moment ball.

A useful paper would report how much the positive entropy-constrained region tightens a physical observable, which retained measurements cause that improvement, and how robust it is to the residual entropy/tail input. That comparison would establish practical significance beyond reformulating maximum entropy.
