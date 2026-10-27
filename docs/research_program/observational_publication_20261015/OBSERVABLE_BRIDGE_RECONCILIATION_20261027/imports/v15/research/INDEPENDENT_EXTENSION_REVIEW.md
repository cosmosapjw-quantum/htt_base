# Independent review of the v15 extension

Reviewer: `/root/internal_five_loop_review_20261026`. Date: 2026-10-26. Scope: `PAPER_I_REUSE`, `PAPER_II_REUSE`, `ENTROPIC_SHEAR_BRIDGE`, and `RESPONSE_FRONTIER`, including their supplied computations, plus a final formula/numerical consistency skim of `V15_INTEGRATION`. This was one fresh review of the changed interface, followed by targeted repair checks. The reviewer did not author or edit the candidates, change either v15 manuscript, launch nested agents, solve a transport ODE, or push a repository.

**Verdict: PASS_SCOPED_AFTER_TARGETED_REPAIRS.** Five concrete findings were repaired and checked. No mathematical blocker remains for these internal conditional constructions. This verdict does not establish observational calibration, publication novelty, a dynamical closure, or the validity of every theorem in the two source manuscripts.

## Findings and closeout

| ID | Severity | Finding | Verified repair |
|---|---|---|---|
| EXT-01 | Medium: physical normalization | Frontier R7 said its number-normalized response, divergence and susceptibility could be dimensionalized by the common density-of-states scale alone. This omitted the dimensionless reference number n0. | R7 now states N_ref = Dcal (k_B T_*)³ n0 and multiplies the normalized outputs by N_ref. It separately identifies the raw number/energy integrals and their conversions. CLOSED. |
| EXT-02 | Medium: family premise | II's counterflow claimed fixed total number while explicitly fixing only K0 and b0. Its total number also depends on a0. | The note and JSON now fix K0, a0 and b0 and vary d0 inside (−a0,a0). The propagation-angle convention is also explicit. CLOSED. |
| EXT-03 | Low: equation transcription | II10 omitted the literal plus before its little-o remainder. | The addition is restored in the final display. CLOSED. |
| EXT-04 | Medium: thermodynamic terminology | The integration text called the energy-only reference “zero-fugacity”. Eta=0 instead means unit fugacity. | It now explicitly says zero chemical potential, eta=0 and unit fugacity. CLOSED. |
| EXT-05 | Low: retained variable binding | The integration paragraph used x for the underlying tensor state, blurring the original sample-by-functional definition. | X now denotes the underlying state carrier; x remains its declared sample-by-functional array. CLOSED. |

The repairs change a dimensional conversion, an explicit parameter-family premise, a displayed equation and two integration definitions. They do not require different numerical toy solutions. Integration equations V1–V9 and all quoted numerical examples agree with the reviewed candidates after these wording repairs.

## Definition and unit binding

The relevant v15 state-space, radial-calibration, entropy and response sections were read directly from the extracted sources. Paper I's energy-only representative and Paper II's number–energy representative are different constrained entropy problems. An energy-calibrated temperature is not a claim that the input spectrum is thermal. The extra spectral defect remains a separate input.

The source convention U²=−c² is mapped to the preceding report by U=cu. A geometric shear has inverse-length units; its proper-time rate is c times that shear. Propagation e and outward sky n have opposite signs. The massless shear operator and its entropy bounds use even moments, while the counterflow current requires the explicitly restored propagation-angle convention.

I=E_* rho_f is directional energy density, whereas the source's spectral radiance contains an extra factor c. The reduced negative entropy has number-density units, and k_B times its Bregman divergence has entropy-density units. A kinetic divergence is not an observational covariance or confidence radius. Paper I's dimensionless inverse-temperature field, Paper II's physical inverse temperature, and the dimensionless observer velocity must not be interchanged. The angular toy defines its natural field by w_L=beta_L^−4, fixing the corresponding brightness-reference normalization.

The three F namespaces remain distinct: certified ceiling utilization, directional support utilization, and occupancy under an independently declared measure. None is supplied by a kinetic entropy defect alone.

## Paper I: global angular entropy to shear response

P2 has the correct reference-energy conversion. From rho_f=3a_xi C_* beta^−4 and the contracted entropy −4a_xi C_* beta^−3, substituting I=E_* rho_f yields the displayed coefficient. Equal total brightness cancels the Bregman tangent term and gives delta=1−〈w^(3/4)〉. This angular defect concerns the energy-matched lift even for a nonthermal original occupation.

The scalar inequality is valid globally, including its continuous zero-brightness endpoint. The stated third derivative of G has the correct coefficient and sign. Integrating backward or forward from one establishes nonnegativity; weighted Cauchy–Schwarz with 〈D(w)〉=1 gives delta≥3〈|w−1|〉²/32. The small equal-area contrast verifies sharpness of this scalar constant.

For the operator step, equal total mass permits subtracting Id/2 inside the integral. Because 0≤B_e≤Id, the centered operator norm is at most 1/2. Combining this estimate with the scalar inequality gives P1 and the sufficient threshold delta<8/75. The report correctly does not claim that the combined entropy-to-operator constant is sharp, or that failure of this certificate means singular response.

P8 follows by subtracting the exact and isotropic approximate transport equations, with denominator 8/15−eta. P9's coefficient is also correct: the quadrupole part has mean square (15/2)(pi/rho):(pi/rho), giving 45/64 after multiplication by the entropy curvature 3/32. The pressure-only quadratic optimum is a local consequence of the existing entropy representative, not a separate general novelty claim.

For P10, set v=S_opt/c. Then the consistency residual is (Rhat−R)+L_I(v−sigma)+(L_0−L_I)v. The bound ||L_I||≤rho supplies the stated epsilon_S term, and the entropy bound supplies the last term. All three terms have energy-density per length units. This application still requires the common congruence and the collisionless, geodesic, irrotational transport branch; static entropy does not supply its derivative jets.

The scalar divergence result is established prior art. The scoped project addition is the normalization and centered transfer to the physical shear operator, its inverse estimate, and its optical consistency application.

## Paper II: resolved rays, finite beams and particle current

Substitution E'=DE into the fixed-ray radial integrals gives number and energy weights three and four. Their quotient therefore has Doppler weight zero at corresponding aberrated rays. This does not preserve multipole coefficients or make the ratio of angularly averaged moments invariant. The inverse gives remapped eta and weight-one temperature only on the stated regular calibration branch.

The beam proof was checked independently by setting X=T³/a³. At fixed mean m, convexity maximizes the fourth-temperature moment on the endpoint secant. Minimizing m⁴/(Am+B)³ gives m*=−4B/A, the stated hot weight, and the displayed lower ratio. The upper equality requires constant temperature. The lower equality is attained by an endpoint two-temperature distribution with the specified hot weight; a particular fixed discrete instrument need not allow every such allocation. The universal interval is sharp over the stated class of admissible beam distributions.

The scalar lower constant is exactly the established generalized Kantorovich specialization K(r³,4/3)^−3. Furuta's primary Definition 1 and Theorem A were inspected, and the supplied comparison identifies the same constant. It must not be sold as a new scalar inequality. The physical extension is its propagation through the number–energy inverse and its use as a finite beam-mixing envelope. The common fugacity, common nonnegative energy-independent beam and positive temperature interval are essential.

The full-sky Doppler integrals, their small-velocity expansion, the r=2 endpoint fraction, and the Planck-boundary inverse are consistent. A mixed Planck spectrum's fitted negative eta is an entropy-selected two-moment parameter, not evidence for a measured chemical distortion. The source's one-sided Bose boundary qualification is retained.

For the repaired counterflow, total number is 8 pi Dcal K0 a0 and total energy is 24 pi Dcal K0. Fixing K0 and a0 while varying d0 preserves both; isotropic directional energy preserves the full stress-energy tensor. Integrating the propagation dipole gives j_z/(cn)=b0 d0/(3a0). The resulting timelike-current frame relation is local and does not construct a matter history.

The contrast covariance contains the correct −24 cross term. The finite inverse-conditioning bound follows from a positive lower bound on J_xi. The MB design has rank two, its thermal/boost kernel is explicit, and common gain is degenerate with its chemical column. These are correctly framed as conditional response properties rather than a new universal impossibility theorem.

## Rank-four entropy projection bridge

Every entry of B_e is an even angular polynomial with sectors only 0, 2 and 4. Matching these bolometric moments therefore preserves the complete STF2 operator exactly, irrespective of unresolved radial entropy or higher angular information. Entropy maximization supplies one representative; it is not necessary for this linear preservation theorem. Temperature or inverse-temperature truncation alone would not establish it.

On the common finite brightness domain, h''=3C I^−5/4/16 has the stated positive lower bound. Taylor's integral remainder gives ES7. For a pure harmonic-four coefficient A, delta H4=Delta4 A and ||P4 delta I||²=Delta4 ||A||², with Delta4=32 pi/315. Contraction by a unit STF2 tensor is bounded by the rank-four Frobenius norm. Combining these facts yields the ES9 coefficient 1024 pi/(945 C). The constant is sufficient and is not claimed optimal.

ES11 is the correct perturbation-of-inverse bound when lambda_L exceeds the operator error. At exact L≥4 matching, only the separately supplied residual error remains. Equality of moment values at one event does not determine derivatives; the note correctly requires equality as smooth fields on a neighborhood for the stronger derivative-preservation statement.

The static toy genuinely fits a positive natural-field polynomial, rather than merely truncating brightness. The dual gradient and Hessian have the correct signs, and positivity is checked on the polynomial interval. The bound's normalized coefficient 256/945 follows from dividing by rho0² and converting the normalized entropy integral. The constructed same-residual shear test is an algebraic control, not observed transport data.

## Detector response frontier

The three-point Bregman identity F6 has the correct sign. At budget D(g_t||g), nonnegativity of D(f||g_t) gives the extremal response with the appropriate sign of t. The constructed g_t itself attains the bound, and strict convexity fixes the equality state up to null sets. The theorem wisely covers every constructed regular branch point, rather than asserting that every entropy budget or Bose boundary has such a representative.

Differentiating the two moment constraints gives the Gram-projected kernel and lambda'(0)=G^−1 b_K. Consequently chi_K=∫W K_perp² and the local entropy cost is t² chi_K/2. The square-root response expression is asymptotic, not a finite-budget error bar. The multichannel susceptibility is the positive-semidefinite Schur complement; its null directions are retained-score combinations under the positive weight.

The common physical-density conversion is correct after EXT-01. The MB/BE/FD toy respects its respective occupation domains at the numerical points, matches number and energy, and checks the exact identity with positive convex competitors. Its finite quadrature to x=64 is not an interval proof on the infinite energy domain. The regular-domain theorem and the numerical illustration remain separate.

The variational method and local entropy-response expansion have direct precedents, including Lam's Theorem 3.1 and Proposition 3.1, inspected in the retrieved primary text. The quantum-statistical detector application and its achieved response region are the useful project construction; a new general information-projection theorem is not established.

## Executed review checks and evidence limits

The reviewer executed the supplied numerical kernels in memory with output-writing sections disabled. No candidate receipt or figure was overwritten.

* Paper I's ten quadrupolar states, strong-anisotropy states and broad scalar-inequality probes passed. At k=20, the actual normalized minimum eigenvalue remains 0.0501193 although the entropy lower certificate is negative.
* Paper II's 1,200 beam cases, exact r=2 fraction, direct Doppler quadratures, pointwise quotient and covariance/rank checks passed. The maximum quotient error was 9.99×10^−16.
* The angular projection was independently rerun at 128 fit and 288 evaluation nodes. L2 gives operator error 0.0065424353558177; L4 gives 1.33×10^−15 with positive entropy defect 9.3716090272×10^−5. Moment residuals remain below 5.3×10^−15.
* The three frontier statistics were rerun at 96 quadrature nodes and six signed tilts. Moment residuals were below 6×10^−16 and three-point residuals below 1.6×10^−16. The projected susceptibilities reproduce the recorded values.

One reviewer wrapper initially used a filename substring that classified `paper_ii` as `paper_i` and raised a KeyError while summarizing already executed checks. The corrected Paper II-only wrapper completed successfully. This was not a candidate mathematical or numerical failure. The author-recorded implementation failures remain preserved in their existing receipts.

The reported numerical tolerances are floating-point consistency evidence. The proofs establish the general claims. The full source-paper theorem inventories were checked against the definitions and theorem domains needed here; this review does not independently certify every proof or all potential extensions in v15. The preceding five-loop report is reused only through the changed shear, observer and optical interfaces.

## Final disposition

All five findings are closed. The four candidates and the bounded integration summary support internal DERIVED/CONDITIONAL status, with executed static toy evidence where specified. Their application still needs real response kernels, joint calibration/measurement laws, bolometric completion, entropy or tail budgets, and transport derivatives when shear inversion is requested. Neither kinetic entropy nor a deterministic feasible set supplies those observations automatically.

Final reviewed candidate identities are recorded in `INDEPENDENT_EXTENSION_REVIEW.json`. No source manuscript, production ownership, original DAG acceptance, native-solver state, or remote publication state is changed by this review.
