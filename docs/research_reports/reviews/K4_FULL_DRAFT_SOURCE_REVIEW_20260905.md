# K4 — fixed-source review of the complete kinematical MES draft

Date: 2026-09-05  
Review class: single-assistant source/literature review with explicit direct derivations; not a blind external referee, CAS run, or publication approval.  
Disposition: CHANGES_REQUIRED — one confirmed P1 manuscript normalisation omission and two bounded P2 clarifications. The integrated scientific structure is retained.

## 1. Reviewed object and limits of the review

Repository: `cosmosapjw-quantum/htt_base`, PR #449. The read snapshot was head
`228ce70267fcdd27942a371a54a8c30b0bc1e696`, tree
`5f5870fed7c3855aa40d427761c11b9187b175b5`, base
`687234128d7c12d04e68aad0f303c21d2d470393`.

The reviewed full manuscript is
`docs/research_reports/drafts/HTT_REPORT_A_FULL_KINEMATICAL_MES_DRAFT_K3_20260905.md`,
Git blob `3d509ebcb178bd26b96d994690668e225a133dc9`.

All twelve body sections and four appendices were read across overlapping
line ranges. The forty entries in Appendix A were manually compared with the
intended retained/candidate structure. This is not an automated forty-row
bijection, a new T9 v5, or a proof of all forty claims.

The targeted repository authorities were:

| Source | Git blob | Review role |
|---|---|---|
| `theory_packs/T3_CONDITIONAL_MES_GEOMETRY_THEOREM_PACK.md` | `80149f9d293fac2e4229968e7e3a2abb8e905437` | MES norms, premises and rate conversion |
| `theory_packs/T5_WU010_LOCAL_OBSERVER_RESPONSE_THEOREM_PACK.md` | `108879669f96ddef53fb4df2c75fa0d0f407bb81` | response adjoint, normal matrix, inverse and sharp condition bound |
| `theory_packs/T6_WU011_PROCESSED_RESPONSE_QUOTIENT_THEOREM_PACK.md` | `e1527855888f25961eaaba52b867f97cd725dd54` | estimator, quotient and finite matched-control evidence |
| `theory_packs/T7_CONTINUUM_WIDE_MASK_EVIDENCE_PACK.md` | `d770d7ad1052c3910b7efdca0a83be99807ad403` | continuum ranks, numerical scales and evidence grades |
| `theory_packs/T8_MATRIX_NUMERICAL_ERROR_ENVELOPE_THEOREM_PACK.md` | `57a001918308c32ac80362cba8897ac412728b0d` | perturbation class and whitening threshold |

The listed paths are relative to `docs/research_reports/`. The original
physical-state donor remains separately attributed in the manuscript. This
review does not re-audit every donor implementation or inherit its execution.

## 2. Scientific integration verdict

The missing kinematical MES inheritance lane has been restored. Sections 4–6
now retain all four distinct objects: observable Q/O tensors, typed physical
congruence/frame/geometry state, matched MES sector constraints, and a
response-constrained set. Section 4.4 preserves physical tensor functionals
before scalar diagnostics are formed. Sections 8–11 preserve the available
local radiation–observer response, nuisance quotient and numerical boundary.

No new instance of the following conflations was found in the reviewed text:

- temperature quadrupole identified with congruence shear by representation type;
- scalar MES radius used to manufacture a tensor direction;
- beta_RO identified with beta_RM or beta_MO without a premise;
- geodesic A_a=0 misreported as a measured zero-radius acceleration anchor;
- same-data MES and response constraints treated as independent evidence;
- finite-sample compatibility-set cardinality presented as population identification;
- continuum full row rank promoted to finite-HEALPix robust containment.

This is a source-review result, not certification of a future observational
pipeline. The retired scalar-collection anomaly methodology remains outside
the current report, while the conditional physical MES inequalities remain
inside its central argument.

## 3. Section-level review

| Section | Review performed | Outcome and residual scope |
|---|---|---|
| 1 | scientific question, supersession, old/new physical lanes | integrated scope retained |
| 2 | real-carrier metric, STF dimensions and norm factors | consistent with stated definitions; primary PSTF factors checked |
| 3 | cyclic domain, signed Cholesky section, contraction replay, strata | no new contradiction found; no new all-strata or inverse-code verification |
| 4 | observable/physical separation, parity, 18/15 and 15/12 counts | counts valid only for the declared parameter space and locally free action |
| 5 | MES coefficients, norm convention, physical sectors and gauge | retained coefficients confirmed; common expanding rate convention should be explicit |
| 6 | same-data set intersection, exact affine fibre, sampling distinction | exact-domain argument survives; no population coverage theorem inferred |
| 7 | row/orbit distinction, counterexamples, complete adaptive map | two theorem lanes remain separated; no actual null pool admitted |
| 8 | Lorentz generator, STF response, adjoint, inverse and conditioning | P1: M_Q is a reduced contraction matrix, not B_Q^*B_Q |
| 9 | processing order, structural monopole null, nuisance quotient, finite counts | source-consistent; finite numerical results not replayed |
| 10 | mask, L=12 block ranks and quoted singular values | printed values agree with T7; raw minors and numerical runs not independently replayed |
| 11 | family-ball bound, positive regularisation and robust-rank implication | theorem survives; explicit threshold above one needed in the margin sentence |
| 12 | interpretation, evidence grades and deferred observations | limitations preserved |
| A–D | forty-ID map, source ancestry, citation roles, unperformed work | candidate/noncanonical distinction preserved; no automated citation or byte-diff certificate |

## 4. K4-RESP-01 — a factor of three was omitted from the normal-matrix description

Severity: P1 publication-facing normalisation.  
Affected location: Section 8.2; candidate/retained claim `RA-RESP-002`.  
Root cause: compression from the T5 theorem pack omitted the distinction
between its contraction matrix M_Q and the Frobenius adjoint normal matrix.

The manuscript correctly defines

\[
(B_Qv)_{abc}=3v_{\langle a}Q_{bc\rangle}
\]

and gives

\[
M_Q=q_2I+\frac65Q^2,\qquad q_2=Q:Q.
\]

It then calls M_Q the adjoint normal matrix. Under the Euclidean vector
product and full STF3 Frobenius contraction specified in T5, the exact
relations are instead

\[
(B_Q^*O)_a=3O_{abc}Q_{bc},
\qquad B_Q^*B_Q=3M_Q.
\]

This is already explicit in T5 Sections 5–6. No change to the underlying
physical response is required.

### Direct derivation

For STF3 O, trace terms vanish and symmetry yields

\[
O:B_Qv=3v_aO_{abc}Q_{bc}.
\]

For the Cartesian response

\[
(B_Qv)_{abc}=v_aQ_{bc}+v_bQ_{ca}+v_cQ_{ab}
-\frac25[\delta_{ab}(Qv)_c+\delta_{ac}(Qv)_b+\delta_{bc}(Qv)_a],
\]

contraction with Q gives

\[
(B_Qv):Q=q_2v+2Q^2v-\frac45Q^2v
=\left(q_2I+\frac65Q^2\right)v.
\]

Combining the two identities proves B_Q^*B_Q=3M_Q. In particular,

\[
\|B_Qv\|_F^2=3v^TM_Qv.
\]

The exact witness Q=diag(1,-1,0), v=(0,0,1) gives six nonzero tensor
components: the three permutations of 311 equal +1 and of 322 equal -1.
Thus the squared Frobenius norm is 6, whereas v^T M_Q v=2. This exposes the
factor of three without a numerical matrix package.

### What does not change

The normal equation is

\[
3M_Q\widehat\beta=3(O:Q),
\]

so the correctly scaled coordinate and projector remain

\[
\widehat\beta=M_Q^{-1}(O:Q),
\qquad P_{\operatorname{Im}B_Q}O=B_QM_Q^{-1}(O:Q).
\]

The four-dimensional residual at fixed nonzero Q is unchanged. It remains a
response-orthogonal residual, not a physical intrinsic-octupole estimate.

The sharp condition bound is also unchanged. For a spectrum proportional to
(-1,1-t,t), 0<=t<=1/2,

\[
\kappa_2(M_Q)=\frac{8-5t+5t^2}{5-5t+8t^2},
\]

and the following polynomial identity proves the bound directly:

\[
\frac53-\kappa_2(M_Q)
=\frac{(5t-1)^2}{3(5-5t+8t^2)}\ge0.
\]

Equality occurs at t=1/5, corresponding to (-5,4,1). Moreover,
\(\kappa_2(B_Q^*B_Q)=\kappa_2(M_Q)\), whereas the response-operator condition
number is its square root. Absolute noise amplification, unlike condition
number, still depends on the nonzero quadrupole amplitude.

Disposition: use the replacement text supplied in
`K4_BOUNDED_MANUSCRIPT_REPLACEMENTS_20260905.md`. The original K3 file is not
silently modified by this review. Do not change the correct T5 theorem or
frozen implementation to match the shortened manuscript wording.

## 5. MES audit — retain the 3/2 coefficient; clarify the rate convention

The original Stoeger–Araujo–Gebbie PDF, arXiv astro-ph/9904346v1, was read
with page screenshots. Printed page 3 defines the norm from the sum of squared
tensor components; printed page 4, Eqs. (3)–(4), gives the manuscript's shear
and vorticity coefficient combinations. Printed page 10, Eqs. (17)–(19), gives
the PSTF multipole conversion factors 15/2 and 35/2. The spatial/time derivative
and all-observer premises remain part of the source construction.

With the full tensor norm and H=Theta/3,

\[
\frac{\sigma_{ab}\sigma^{ab}}{6H^2}
<\frac{\Theta^2}{6H^2}B_\sigma^2
=\frac32B_\sigma^2,
\]

and likewise for vorticity. Therefore the retained 3/2 coefficient is not a
factor-of-two mistake. As an algebraic cross-check, the declared epsilon_1=0
scenario gives

\[
U_\omega=\frac{C_2}{4\pi T_0^2}.
\]

This neither makes epsilon_1=0 an observation nor proves the MES premises from
one sky. The component norm is not the alternative scalar convention
\(\sigma^2=\sigma_{ab}\sigma^{ab}/2\). A conversion between those quantities
requires its explicit factor of two.

K4-MES-02, severity P2: Section 5.1 should explicitly retain the expanding
branch Theta>0 and define H=Theta/3 in one consistent rate convention.
For geometrical inverse-length rates from the unit observer, use
H_g=Theta_g/3. For inverse-time rates use H_t=c H_g,
sigma_t=c sigma_g and omega_t=c omega_g. Both quadratic ratios agree;
mixing a geometrical numerator with an inverse-time Hubble denominator does
not. No new acceleration or geometry anchor is proposed.

The use of non-strict inequalities in a closed outer admissible body is a
conservative relaxation of strict source inequalities, not a claim that the
physical bound is saturated. Degenerate zero-radius sectors remain outside
the positive-radius gauge/division formulae.

## 6. K4-RANK-03 — make the robust-rank margin explicit

Severity: P2 mathematical-domain clarification, not a new numerical result.
Section 11.2 correctly states that error-whitened singular values above one
certify nonzero rank, but the subsequent phrase 'above a preregistered margin'
should explicitly put that margin above one.

Let K_obs=K_true+Delta and W=Gamma_E^(-1/2). The assumed error class gives
\(\|W\Delta\|_2\le1\), so the singular-value perturbation inequality yields

\[
s_i(WK_{\rm true})\ge s_i(WK_{\rm obs})-1.
\]

Thus the number of singular values strictly above one is a lower bound on
rank(K_true). If m<=n, a sufficient full-row-rank test is

\[
s_m(WK_{\rm obs})\ge1+\delta,\qquad \delta>0,
\]

with delta fixed before inspecting rank outcomes. A threshold below or equal
to one does not give that positive lower bound. The actual finite-HEALPix
error-class coverage is still unproved here.

## 7. Inherited numerical evidence and statistical semantics

The Section 10 rank ladder (20/24/24 at L=8, 27/29/32 at L=9, and 32/32/32
at L=12) and the three printed smallest singular values agree with T7 at the
printed precision. The stored-real axial rank count is 4+2(4+4+3+2+1)=32.
The Section 9.3 finite matched-control counts (17 ambiguous, one resolved,
zero containment candidates) agree with T6. This is source reconciliation,
not a fresh raw-artifact replay or a numerical proof.

The source makes three important distinctions correctly: deterministic
unrestricted nuisance containment is not a statement about a physical
stochastic prior; a realised noisy-data compatibility set is not automatically
a population identified set or confidence region; and a valid finite-null
rank requires the symmetry of the complete data-derived analysis. Those
boundaries survive this review. No new numerical or observational claim is
needed to repair Section 8.2.

## 8. Citation role and currency

Molinari's arXiv:2004.11751 explicitly describes a review of partial
identification and separately discusses identified-set characterisation,
estimation and confidence statements. Kaido–Molinari–Stoye,
arXiv:1908.09103v4, is research on constraint qualifications. The manuscript's
survey-versus-research distinction is appropriate. Neither source proves the
project-specific MES or response formulas.

A current publisher lookup identifies a newly available accepted version of
Ritzwoller–Romano–Shaikh, *Randomization Inference: Theory and Applications*,
Journal of Political Economy Microeconomics, DOI 10.1086/743457, accepted
31 July 2026. This is a bibliographic-currency note, not a requirement to change
the version deliberately cited under `RANDOMIZATION_2024`. No new volume,
issue or page range is invented, and no citation key or formal bibliography is
changed by this review.

Public sources actually consulted:

- https://arxiv.org/pdf/astro-ph/9904346 — printed pp. 3, 4 and 10;
- https://arxiv.org/abs/1403.6117 — exact d=1 boost background, not the project-specific normal-matrix proof;
- https://arxiv.org/abs/2004.11751 — survey role and set/inference distinction;
- https://arxiv.org/abs/1908.09103 — constraint-qualification research role;
- https://www.journals.uchicago.edu/doi/10.1086/743457 — publisher acceptance metadata.

## 9. Execution and review evidence

Local container and Python calls returned ClientError before observable
execution. The Wolfram connection probe returned MCP/SSE HTTP 404; no kernel
result was produced. The historical attached runtime probe concerns head
0ae24eed..., not the reviewed head, and is not reused as current verification.
No GitHub Actions rerun was requested during this review.

The web calculator evaluated four finite arithmetic checks: the condition
ratio at t=1/5 (approximately 1.6666666666666665), the response witness norm
(6), the axial rank sum (32), and the coefficient product in U_omega (about
0.25). Floating-point calculator output is not exact CAS verification. The
general identities above are direct algebra, additionally reconciled with T5
and T3, not newly executed SymPy, Lean or Wolfram proofs.

Academic Writing Toolkit found zero paragraph-logic issues in a five-paragraph
review synopsis and zero British-English issues in three replacement-summary
paragraphs. These checks do not cover every manuscript sentence or prove the
mathematics. SciSpace located the original MES sources but did not resolve
conventions by abstract alone; the PDF pages supplied that evidence.

The exact named Canonical Memory Verifier was not returned by plugin discovery.
No unrelated plugin was installed. Persistent evidence consists of the pinned
Git source objects and these explicit review records, not an asserted memory
verification service.

## 10. Disposition and next action

K3 remains a complete draft. K4's first whole-source review is delivered with
bounded changes required; K4 canonical acceptance and final release are not
completed. The canonical ledger remains T9 v4/30, the draft map is 40, and
materialised v5 is not created in this pass.

The next substantive edit is to apply the three supplied replacement blocks
(Sections 5.1, 8.2 and the margin passage in 11.2) to the fixed K3 source,
check the affected claims and preserved numbers, and then typeset a reviewed
candidate. No new compiler, CAS-policy redesign or expansion of physical scope
is needed for these edits. Exact compiler/materialised-authority acceptance
and the required formal receipts remain parallel obligations before freeze.

No Planck/FFP10 execution, physical kinematical estimate, global-tilt
attribution, finite-HEALPix containment, Bianchi-family result, native BASS
result, merge or publication approval is introduced.
