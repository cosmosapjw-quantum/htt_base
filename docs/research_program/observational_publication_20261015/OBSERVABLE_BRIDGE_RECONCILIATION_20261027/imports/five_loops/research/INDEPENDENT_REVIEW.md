# Independent review of the five internal theory loops

Reviewer: `/root/internal_five_loop_review_20261026`. Date: 2026-10-26. Requested reviewer profile supplied by the parent: Astra, xhigh; observed runtime identity and effort: UNKNOWN. This is a fresh, bounded review of the internal theory candidate. The reviewer did not author the candidate, changed no candidate/source/CAS files, launched no nested agents, and performed no push, solver, ODE or observational fit. This document and its JSON companion are the only reviewer-owned outputs.

**Final verdict: PASS_SCOPED_AFTER_TARGETED_REPAIRS.** All five internal theory units are suitable for the stated conditional-theory use. Six bounded findings were repaired and independently checked; no scoped mathematical blocker remains. This is not empirical validation or historical four-axis CAS admission.

## Assumptions and conventions

The controlling project source is `sources/AGENTS.md`. The project physics/math, claim-firewall, claim-provenance and xQPiFG skills were read and applied. Their substantive controls are preserved: signature (−+++), declared congruences and units, distinction between deterministic images and statistical laws, and no conversion of scalar/tensor morphology into a native Bianchi-family identification. The current task authorizes a single scientific review with targeted repair closeout, not a recursive audit.

Each note states its own units. In particular C's h and S are time rates; D's h and S, E's h and A's shear have inverse-length units. Combining their images requires the explicit factors of c, a common frame and the same physical congruence. A temperature quadrupole, radiation anisotropic stress, local kinematic shear and spatial STF Ricci remain different tensors.

## Findings and minimum repairs

| ID | Severity | Finding | Minimum repair and current closeout |
|---|---|---|---|
| IR-01 | Medium, equation transcription | A5 omitted the plus before the dipole-gradient term; A8 omitted two plus signs; the following STF(M4:S) identity omitted the isotropic plus. The rendered equations therefore differed from the valid derivation and CAS input. | Restore the four additions. Author repair was independently read and all four terms now agree. **CLOSED.** |
| IR-02 | Low, definition transcription | D's first paragraph contained two literal U+000B controls before `arepsilon_N`, and many inline mathematical expressions had lost LaTeX delimiters. | Restore epsilon and inline delimiters without changing equations. Candidate now has no unintended controls. **CLOSED.** |
| IR-03 | Medium, scientific namespace | A R9 called the current skill's occupancy-F a “legacy/application object”. The legacy implementation explicitly rejects material/volume occupancy; this wording could undo the three-way distinction already established by the code inventory. | A R9 and its F-TYPING override now separately identify the certified x_C/U diagnostic, directional support utilization and declared-measure occupancy. Both repairs were read against the source inventory. **CLOSED.** |
| IR-04 | Low, optional precision | D called the II/VII0 Ricci difference “rank-two”. It is a two-index tensor, but the displayed matrix difference is u² diag(−1,2,−1), of matrix rank three. | The repaired note says “STF Ricci difference”. **CLOSED.** |
| IR-05 | Medium, missing statistical premise | E21 originally assumed true propensity positivity without positivity of the working propensity in its denominator. | E now explicitly assumes positive working propensity on parent support and integrability; its claim record agrees. **CLOSED.** |
| IR-06 | Low, application order | E R10 originally proposed fitting two distance coefficients while also reporting the cubic invariant J. | E now reports h0/h1 from the first two coefficients and requires a supported cubic d3 before reporting J. **CLOSED.** |

No mathematical counterexample was found in the reviewed A–E claims under their stated premises after the above repairs. The unresolved empirical inputs below are application obligations, not new impossibility results.

## Equation and proof audit

### A — Exact radiative shear operator

The occupation normalization gives bolometric angular energy density with the stated units, and Planck integration gives the correct coefficient. The pure temperature-dipole example produces the stated nonzero radiation quadrupole through T⁴; its temperature Q and O nevertheless vanish. This correctly prevents identifying a temperature truncation with a stress-energy truncation.

The Liouville angular-drift calculation independently checks the central sign. With a=eᵀσe and v=σe−ae, the redshift term 4aI plus integration by parts of −v·∇I gives 2 STF(σM2)−STF(M4:σ). The six-term STF4 decomposition then gives **10/7**, not 2/7. The source discrepancy is real in the inspected pages: Ellis et al. Eq. (11.2), PDF 299, displays 10/7; MGE arXiv v2 Eq. (89), PDF 15, displays 2/7. MGE Eq. (71)'s 5ℓ/(2ℓ+3) coefficient gives 10/7 at ℓ=2. The derivation resolves the coefficient for this note's convention; it does not certify a journal erratum.

The quadratic form is ∫I[2|Se|²−(eᵀSe)²]. Its lower bound follows from (eᵀSe)²≤|Se|² and tr(S²M2)≥λmin(M2)||S||². The stated pointwise upper bound follows by rotating e to the third axis. Polarization proves self-adjointness. The inverse requires a positive response eigenvalue; a single beam can have a kernel, while a positive full-sphere brightness satisfies the sufficient condition. No small-anisotropy premise was inserted into this argument.

For A13, subtracting the exact and reconstructed equations gives L_I(σ−σhat)=−(R−Rhat)−(L_I−L_Ihat)σhat. The pointwise operator norm is at most one, and the Rayleigh bound gives λmin(L_I)≥λhat−epsilon_I. The displayed error radius follows with the correct denominator and dimensions. Finite spectral coverage and derivative-jet errors are explicitly required. The non-coaxial witness is correctly confined to the local algebraic transport relation rather than asserted as a global Einstein–Liouville spacetime.

### B — Lorentz, spectral and statistical dipole channels

The incoming/outward sign and the exact Doppler and aberration maps agree: a forward-looking moving observer sees a hotter monopole. Expanding at fixed observed direction yields the stated mean, a=β+d, K=Q+STF(ββ)+2 STF(βd), and K−STF(aa)=Q−STF(dd). The intrinsic-quadrupole envelope gives the displayed necessary finite interval; it is not advertised as an exact attained identified set for every observed tensor.

The known-boost map has Gram form 2β²|d|²+(2/3)(β·d)², so its minimum singular value and inverse are correct. The independent Planck derivative expansion gives the G/H spectral terms, including d², and the frequency generator reproduces the mixed leakage. The adjacent-mode covariance response follows from the stated weight-one harmonic recurrence. Its interpretation as observer velocity remains conditional on the rest-frame covariance, actual map modulation, mask and competing physical responses.

For B14–B15, P annihilates the whitened nuisance image and PA=A. Thus the covariance of A⁺PC^−1/2 epsilon is (AᵀA)^−1. The marginal three-dimensional Gaussian ellipsoid and the deterministic operator-norm bias bound give the stated coverage inequality. Known fixed covariance/design and the projected remainder are indispensable. The note explicitly does not treat products of Gaussian sky modes as exactly Gaussian, and supplies a calibrated norm-event alternative. Rank-deficient component estimability is correctly expressed by annihilation of ker A. No observed intrinsic dipole or global matter-tilt history is measured here.

### C — Local optical inverse and congruence cancellation

The null contraction gives h+S:nn−alpha·n, with antisymmetric vorticity removed. The leading proper-motion statement requires more than simultaneous separation; C5 supplies the missing null-boundary argument. The endpoint factor 1/(1+z) contributes a vector parallel to u at leading order, removed by the screen projector. Hence PA−P(A−∇_n u)=P∇_n u: acceleration cancels at distance order zero for the common smooth congruence.

This was independently checked against the actual primary HTML of Heinesen–Korzyński arXiv:2406.06167v2, Appendix C equations (37), (38), (44) and (46), retrieved through Exa. Its final leading term is exactly the projected spatial gradient. The search-service fetch had failed; that failure was not used as evidence. The source and the direct endpoint derivation agree.

The full-sphere inverse coefficients, E2/B1 normalization and joint norm follow from second/fourth sphere moments. With the chosen epsilon convention, omega_ij n_j=(n×omega)_i; the inverse v=−3〈n×mu〉/2 and catalogue spin v_cat=v+Omega consequently have the correct signs. The exact-rational catalogue script independently reran with ranks 9, 8 and 12, and three unknown-spin kernel dimensions. These ranks concern the displayed finite design. The leading distance limit, calibrated clocks/triad/source population and finite-distance remainder remain explicit application premises.

### D — Homogeneous curvature and initial constraints

Koszul's formula, curvature contraction and the Jacobi restriction produce the stated Ricci tensors. The IX/V sectional signs and the II sectional curvatures match the declared curvature convention. The Hamiltonian term is +S:S/2−R3/2 in 3h², and all terms have inverse-square-length units.

The momentum sign was checked independently of the candidate's Ricci program. Starting from D1–D2, −D^j S_ij was evaluated with exact Fraction arithmetic on all four structure-coefficient basis directions and all five STF basis tensors. All 20 bilinear pairs give 3a S_1i+epsilon_ijk n_j S_jk. Together with K=−(hI+S) and T0i=−q_i, this verifies D7's sign. The existing six-case exact-rational Ricci script also reran successfully.

II with n=(u,0,0) and VII0 with n=(0,2u,u) have equal scalar curvature and zero momentum for the same diagonal S, but inequivalent Ricci spectra. The stated positive-density inequality supplies legitimate instantaneous dust constraint data. A future dynamical development is not calculated. The flat I/VII0 example is correctly treated as different simply transitive presentations of the same local Euclidean geometry. Neither example establishes an observed family distinction or a universal no-go theorem.

### E — Hubble anomaly and joint observational response

The past-directed convention makes E'=E²h with the stated negative acceleration term. Differentiating this equation gives E5. The regular-vertex focusing equation gives D_A=lambda−R0 lambda³/12, because optical shear is O(lambda). Reversing the redshift series and applying reciprocity then produces all three coefficients in E7. The derivative h2 includes both time/direction evolution and the evolving affine energy normalization. Omitting these would corrupt the cubic coefficient.

The FLRW substitutions give the correct curvature sign. Independent special limits are consistent: flat de Sitter gives D_L=(z+z²)/h0; Milne gives (z+z²/2)/h0; Einstein–de Sitter gives cubic coefficient −1/(8h0). H_ratio and H_diff have the different first-order coefficients claimed. H_diff uses a transverse comoving distance and is therefore not generally the FLRW H(z) in curved models.

E11–E12 are an exact equivalence in the stated finite jet coordinates for h0 nonzero. Recovering h0/h1 from d1/d2 and multiplying d3 by 6h0⁴ yields J=h2+h0 R0/2. The displayed one-dimensional change preserves J. The FLRW family with fixed H0, q0 and j−Omega_k supplies local realizability when the matter equation of state is left free. This is not a claim that every arbitrary jet obeys a fixed matter model or energy condition. The lemma gives a specific unresolved direction, not a universal no-go.

Conserved spatial photon momenta give n_i'/n_i=E(H_i−H_n)/c. Differentiating H_n along the ray yields the factor-two directional variance in E15. The direct Kasner Ricci formula vanishes because sum p_i=sum p_i²=1. Substitution gives q_eff=(2+21x−27x²)/(2−3x)² and the stated values 1/2 and 23. The divergence at x=2/3 is a failed redshift-coordinate denominator, not a spacetime Ricci singularity. The note properly retains the affine formulation there.

E19 follows from reciprocal monotonicity only on the stated positive-denominator domain and with an externally justified remainder bound. The residual-compatible linear image retains both empty-data compatibility and unresolved kernels. The target-kernel inclusion is necessary for point identification, not by itself a claim that bounded observational errors have zero width.

For fixed working nuisance functions, conditional expectation under the stated mean-selection assumption gives E22 exactly. The repaired working-propensity positivity and integrability make the expression well-defined. Random fitted nuisance functions require appropriate conditioning/sample splitting; the note's cross-fitting instruction is an application design, not a new dependent-data asymptotic theorem. For E23, the compressed score is the conditional expectation of the original score; total covariance gives the PSD information difference under the stated regularity and finite score moment. These are credited statistical identities applied to a named physical response, not measurements or new general statistical theorems.

## Evidence scope and claim implications

The written derivations, A–E claim records, the associated finite CAS scripts/receipts, relevant textbook pages and primary MGE/Heinesen–Korzyński expressions were inspected. `research/LEGACY_COVERAGE.md` and the actual `typefree_functionals.py`, `typefree_depth.py`, and `htt/mio/formalism/filling_fraction.py` were read for namespace and legacy boundaries. The report/typefree support quantity, legacy certified ceiling utilization and explicit-measure occupancy are distinct mathematical objects; a finite deterministic set has no probability law by itself.

The pure-Wolfram xAct receipt returns zero symmetric/antisymmetric contraction, the expected null-gradient contraction, and zero target residual. The additional repaired gradient-square calculation returns B_ab B^ba=Theta²/3+S:S−W:W and a zero residual, using trace-free shear and orthogonality rules. These are successful finite tensor algebra. The earlier binary-path attempt ended in an unresolved `Hold[Throw[Null]]`; the original gradient-square attempt had an undeclared-index failure. Those attempts remain failed evidence. The successful checks do not prove the optical endpoint argument, full Raychaudhuri dynamics, all spacetime equations, the five loops as a whole, or the historical four-axis gate. E's initial series-code syntax failure also remains separate from its successful repaired output.

Literature supplies the Liouville hierarchy, Lorentz response, local optical geometry and homogeneous field equations. The project-level additions are the particular positive-operator/error formulation, joint response contracts and explicit matched example. This review does not establish literature-wide novelty. All empirical outputs remain SPECIFIED/CONDITIONAL; conditional derivations can be retained at internal C0. No posterior, native transfer, observed Hubble/dipole anomaly or Bianchi-family identification is promoted.

## Final closeout

All six findings are closed on the final candidate identities recorded in `INDEPENDENT_REVIEW.json`. The finite identities and written proofs support internal DERIVED/CONDITIONAL status; the observation contracts remain SPECIFIED until their actual input products, common frames, calibration laws and finite remainders are supplied. The source snapshot identity was supplied by the parent; the extracted tree has no Git metadata with which to verify its commit independently.

No review step changed original-42 scientific acceptance, external-history obligations, native-solver status, publication readiness or literature-wide novelty. A useful next consuming step is one declared source-level joint response with its calibration/remainder budget, retaining the demonstrated kernels and all cross-channel covariance. This review does not prescribe another assurance-only loop.
