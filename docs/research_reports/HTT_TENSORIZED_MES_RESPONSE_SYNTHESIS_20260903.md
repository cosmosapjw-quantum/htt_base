# Tensorized Low-ell CMB Anisotropy Inference and Response-Limited Identifiability

## Current `htt_base` methodology, supersession state, and pre-rerun research report

**Evidence cutoff:** 3 September 2026  
**Repository:** `cosmosapjw-quantum/htt_base`  
**Report branch base:** `changeset/mes-tensor-research-integration-20260830@687234128d7c12d04e68aad0f303c21d2d470393`  
**Scope:** HTT/common/obsstat statistical and observer-response methodology only. Native BASS solver construction, Bianchi background evolution, recombination/reionization solvers, and family-level forward inference are excluded.

---

## 1. Executive status

This report replaces the scalar-only MES-centered observational narrative and the later observer-space Q/O result narrative as the current research synthesis for the `htt_base` statistical programme.

The current scientific state is deliberately asymmetric:

1. **The representation and statistical methodology has advanced materially.** The current methodology retains the full stored-real low-multipole carrier, reconstructs correctly normalized STF quadrupole and octupole tensors, preserves the distinction between `SO(3)` and `O(3)`, and exposes a generic conditioned tensor-orbit chart instead of treating a small scalar feature list as complete.
2. **The prior scalar-only MES observational methodology is retired for the forthcoming analysis.** Historical scalar-function values and finite ranks remain provenance-bearing historical computations only. They are not current observational results and are not used as a baseline scientific result in this report.
3. **The old WU-006--008 Q/O, tensor-rank, foreground and carrier-injection interpretations are withdrawn.** The stored harmonic carrier remains usable as input, but the old derived tensor/statistical products are not current authority.
4. **No corrected tensorized Planck anomaly rank is currently admitted.** The corrected map-free representation repair has an implementation and execution contract but still requires local execution, exact input/output binding and independent review. The observation-bearing statistical run must then be repeated locally under the corrected tensor semantics.
5. **A separate observer-response line is substantially stronger.** PMG-WU-010 establishes a convention-locked full-sky scalar local-observer Lorentz pullback and its first-order STF/harmonic response. PMG-WU-011 extends this to the processed cut-sky operator and has strong continuum evidence that high-source multipoles through `L=12` span the retained `ell=2..5` carrier for every registered boost direction under the wide-mask identity-transfer reference problem. The finite HEALPix robust containment statement is nevertheless still unresolved.
6. **Physical attribution is therefore downstream of both tensorized representation and response identifiability.** Neither a scalar ceiling nor a tensor morphology statistic may be interpreted as physical shear, vorticity, global tilt, local boost, foreground origin, or a Bianchi family without a separately verified response/data model.

The principal near-term deliverable is not a new scalar anomaly number. It is a **corrected tensorized local rerun with preregistered statistics and a response-aware claim boundary**.

---

## 2. Authority and supersession map

### 2.1 Foundation: merged vector/tensor framework

PR #367 (`changeset/pr275-proof-atlas-report-v2`) merged the pre-native vector/tensor programme. It introduced typed joint anisotropy states, tensor functionals, orbit catalogues, conditional statistical lanes, depth/response diagnostics, theorem registries, synthetic validation and data-admission boundaries. It explicitly distinguished scalar objects from vector/tensor geometry and kept BASS/native-solver products external.

That programme is retained as framework infrastructure, not as the final authority for the current Planck analysis. Its broad source/proof inventory was intentionally larger than the subset that had actually been independently adjudicated, and its observation-bearing lane had not yet produced admitted data results.

### 2.2 Historical scalar/observer-space report

`codex_emergency` contains `MES_BOUND_CURRENT_RESEARCH_REPORT.tex`. That document already withdrew the later observer-space STF results after a harmonic-to-STF normalization defect was found, but it still treated the scalar MES finite-pool analysis as admitted.

For the present programme this document is **superseded**. Current explicit project policy and the later tensor-integration authority retire the scalar-only methodology as the basis of the next observation analysis. Its scalar values may be used only as historical computational provenance or as a preregistered historical sensitivity question in a new analysis; they are not a current headline result.

### 2.3 Current tensorized semantic authority: PR #440

PR #440, `changeset/mes-tensor-research-integration-20260830@687234128d7c12d04e68aad0f303c21d2d470393`, is the present semantic authority for the tensorized MES/low-ell representation line.

Its controlling disposition is:

- old WU-006--008 success labels are superseded;
- the stored-real harmonic carrier remains valid input;
- old Q/O contractions, tensor ranks, foreground inferences and carrier-domain injection interpretations do not become valid merely because the historical files replay;
- the harmonic basis normalization and original-PSTF MES normalization must both be corrected;
- no replacement anomaly rank is selected during the representation repair;
- corrected statistical questions must be rerun only after representation repair and independent review.

### 2.4 Separate additive observer-response authority: WU-010/WU-011

The local-observer response programme does **not** descend cleanly from PR #440. The PR #440 head and the WU-009/010/011 lineage are Git-diverged branches. This report therefore treats them as two evidence lineages:

- **Lineage T:** tensorized representation/statistics authority, PR #440;
- **Lineage R:** local-observer response/identifiability authority, WU-010/WU-011.

Their integration in this report is semantic and scientific, not a claim that the source branches form one linear ancestry.

---

## 3. Why the scalar-only methodology is no longer the analysis target

There are two different reasons, and they must not be conflated.

### 3.1 Scalar ceilings do not carry the tensor morphology

A scalar MES ceiling is a conditional one-way function of premise-dependent multipole amplitudes. A rotational scalar cannot be promoted into a nonzero direction-indexed vector or STF tensor by an equivariant construction without additional directional information. The current programme therefore does not use scalar ceilings as substitutes for the measured quadrupole/octupole tensor morphology.

The original-PSTF MES functions remain useful as conditional theory-derived scalar functions when their assumptions are stated, but they no longer define the principal observational statistic.

### 3.2 Historical observer-space tensors used an inconsistent carrier interpretation

The stored real harmonic carrier uses

\[
 c_{\ell 0}=a_{\ell0},\qquad
 c_{\ell m,c}=\sqrt{2}\,\Re a_{\ell m},\qquad
 c_{\ell m,s}=-\sqrt{2}\,\Im a_{\ell m}\quad(m>0).
\]

This is an orthonormal real carrier with the Euclidean metric. Applying STF formulas derived for unscaled real/imaginary complex coefficients changes the relative `m=0` and `m>0` weights and therefore changes tensor shape and rotation behavior; it is not a harmless global scale error.

The corrected tensor identities are

\[
 Q:Q=\frac{15}{8\pi}\|c_2\|^2
     =\frac{75}{8\pi}C_2,
\]

\[
 O:O=\frac{35}{8\pi}\|c_3\|^2
     =\frac{245}{8\pi}C_3.
\]

The map-free repair code independently constructs the harmonic-to-STF map by spherical quadrature and checks these radial identities row by row.

### 3.3 Original MES normalization is PSTF, not sky RMS

The second correction is logically independent of the carrier basis. The original MES epsilon is a PSTF temperature-tensor norm. With the same temperature unit for `C_l` and `T0`, the corrected functions used by the current tensor integration are

\[
 \epsilon_2
 = \frac{1}{T_0}\sqrt{\frac{75 C_2}{8\pi}},
 \qquad
 \epsilon_3
 = \frac{1}{T_0}\sqrt{\frac{245 C_3}{8\pi}}.
\]

For a declared residual PSTF dipole norm `epsilon_1`, define

\[
 B_\sigma=\frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3,
 \qquad
 B_\omega=\frac{10}{3}\epsilon_1+\frac{2}{15}\epsilon_2,
\]

and

\[
 U_\sigma=\frac32 B_\sigma^2,
 \qquad
 U_\omega=\frac32 B_\omega^2.
\]

These remain **conditional one-way functions**, not independent observational coordinates and not measurements of physical shear or vorticity. `epsilon_1=0` is an explicit attribution/premise scenario, not a measurement that an intrinsic dipole vanishes.

---

## 4. Tensorized observable representation

### 4.1 Full Q/O tensors are primary

The next observational analysis should preserve the correctly reconstructed STF tensors

\[
 Q_{ij}\in\mathrm{STF}_2(\mathbb R^3),\qquad
 O_{ijk}\in\mathrm{STF}_3(\mathbb R^3),
\]

together with their amplitudes and provenance. A reduced invariant vector is a derived coordinate system on an orbit space, not a replacement for the tensors themselves.

The generic joint `ell=2,3` tensor pair has a nine-dimensional proper-rotation quotient after removing the three rotation degrees from the twelve real harmonic degrees. Consequently an eight-coordinate catalogue cannot generically separate the joint orbit space.

### 4.2 Conditioned Krylov orbit chart

The current additive implementation defines

\[
 v_i=O_{ijk}Q_{jk},
 \qquad
 K=[v,Qv,Q^2v].
\]

On the declared cyclic and numerically conditioned chart, it retains two positive amplitudes and sixteen contractions of the unit-normalized tensor pair:

- `tr(Q^2)` and `tr(Q^3)`;
- `v.v`, `v.Q.v`, `v.Q^2.v`;
- signed `det K`;
- ten symmetric contractions `O(K_i,K_j,K_k)` for `i<=j<=k`.

This packet is an overcomplete **generic proper-rotation representation**. It is not sixteen independent measurements, not a global invariant-ring theorem, and not a physical source identifier.

The sign of the oriented volume matters for `SO(3)`. Purely even octupole invariants may characterize an `O(3)` orbit while losing proper-rotation chirality. The implementation therefore records the action group explicitly.

### 4.3 Degenerate and ill-conditioned strata

If `K=[v,Qv,Q^2v]` is singular or outside the fixed conditioning domain, the chart is unavailable. The correct behavior is to preserve the original Q/O tensors and the row, not to invent a transverse axis and not to remove the row from a null ensemble.

This is essential for finite-null validity: missingness or chart failure cannot be allowed to depend asymmetrically on whether a row is the observation or a simulation.

---

## 5. Statistical framework that survives the tensor correction

The statistical machinery is retained only at its stated conditional scope.

### 5.1 Observation-inclusive finite ranks

For a fixed row-equivariant score applied symmetrically to an observation and a finite reference pool, observation-inclusive ranks can be calibrated under the declared joint exchangeability/null-fidelity assumptions. Tie handling, one- versus two-sided tails and monotone transformations are part of the registered scoring rule.

This does **not** establish unconditional validity for every frozen reference sample. A finite rank is only as scientifically relevant as the null ensemble and row-processing symmetry that justify exchangeability.

### 5.2 Data-dependent statistic selection

A data-dependent selection rule is not automatically invalid if the complete operation is symmetric/equivariant over the joint pool and its conditioning is declared. However, a statistic, kernel, orbit score or tail direction may not be chosen after inspecting the corrected observed rank and then treated as confirmatory.

The new Krylov/kernel/response statistics must therefore be separately preregistered or split into calibration/development and evaluation surfaces.

### 5.3 CMB-only simulation lane

A noisy observed Planck product compared with noise-free CMB-only simulations is not a jointly exchangeable observation-inclusive null experiment. The historical CMB-only-999 lane can be retained as a **descriptive sensitivity diagnostic**, but it is not an independent replication and not a calibrated p-value unless a faithful joint null/noise model is supplied.

Shared CMB realization IDs across alternative processing lanes are also not independent replications.

### 5.4 Multiple shared-data evidence products

Evidence products computed from the same observed sky and overlapping simulations may not be multiplied under an independence assumption merely because they use different scalar/tensor summaries. Any joint evidence construction requires an explicit dependence model or a valid combined row-equivariant statistic.

---

## 6. Local-observer response: full-sky authority

PMG-WU-010 provides a separate, substantially closed observer-response layer.

The fixed conventions are

\[
 g_{ab}=(-,+,+,+),\qquad
 \hat n=-e,\qquad
 \boldsymbol\beta=\boldsymbol v/c,
\]

with an active observer boost `+beta` and thermodynamic-temperature Doppler weight `d=1`.

The implementation contains an exact finite Lorentz pullback for strictly positive absolute thermodynamic blackbody temperature, including aberration/deaberration and the solid-angle Jacobian. It is not an arbitrary frequency-dependent intensity transform and it is not a global matter-frame tilt model.

For a quadrupole tensor `Q`, the first-order boost response contains the induced dipole and STF3 octupole. The STF3 response is

\[
 (B_Q\beta)_{abc}=3\beta_{\langle a}Q_{bc\rangle}.
\]

The associated Gram/normal matrix can be written

\[
 M_Q=q_2 I+\frac65 Q^2,
\]

with the sharp condition bound

\[
 \kappa_2(M_Q)\le\frac53.
\]

WU-010 also contains an independent stored-real harmonic oracle for the first-order `ell=2 -> (ell=1,ell=3)` response and recorded exact-head successful verification on its frozen closeout head. This is a response theorem/API result, not an empirical `beta` measurement.

---

## 7. Processed cut-sky response and high-ell identifiability

PMG-WU-011 studies the operator actually relevant after the observation-processing chain. Its registered baseline is

```text
positive absolute thermodynamic sky
 -> exact finite local-observer boost
 -> source beam/pixel convolution
 -> HEALPix synthesis
 -> fixed weighted joint ell=0..5 solve
 -> post-fit target/source commonization
 -> retained ell=2..5 stored-real carrier
```

The first-order response tensor has source support through `ell=6` and retained output dimension 32. The implemented Jacobian schema is

```text
J.shape = (3, 32, 49)
```

where the source contains the physical monopole plus stored-real `ell=1..6` coordinates. The scientific monopole column is structurally zero; any HEALPix monopole replay leakage is treated separately as a numerical effect.

### 7.1 Full-sky reference

In the full-sky reference, the anisotropy response has rank 48 after the structural monopole null, and the nonzero-subspace exact condition number is

\[
 \sqrt{63/8}\simeq2.80624304008.
\]

This is the well-conditioned reference against which cut-sky processing is compared.

### 7.2 Cut-sky Task-7A/7B negative results

The original reference cut-sky configuration was poorly conditioned and strongly contaminated by raised high-source aliases. A later atlas across mask/transfer variants found no candidate simultaneously satisfying conditioning, alias and tail requirements. This negative result motivated a more explicit nuisance-span formulation rather than choosing a favorable processing configuration post hoc.

### 7.3 Nuisance-span formulation

Let `J_b` denote the low-source response for boost direction `b`, and let `K_b(L)` denote the processed response generated by source multipoles `7<=ell<=L`. The low-source response remaining after high-source nuisance projection is characterized by

\[
 \operatorname{rank}(P_{\operatorname{Im}K_b(L)^\perp}J_b)
 =\operatorname{rank}[K_b(L)\;J_b]-\operatorname{rank}K_b(L).
\]

If at some finite `L0`

\[
 \operatorname{Im}J_b\subseteq\operatorname{Im}K_b(L_0),
\]

then increasing the allowed nuisance band cannot restore identification because the nuisance images are nested.

The first scalar numerical rank policy proved too coarse: most coordinates were ambiguous under matched full-sky controls, with no stable containment terminal. The last byte-exact execution-backed Task-7C scientific state therefore remains `PASS_TASK7C_MATCHED_CONTROL_RANK_UNRESOLVED`.

---

## 8. Continuum wide-mask result

A separate continuum calculation removes the HEALPix discretization layer while retaining the wide-mask weighted joint-fit structure. For the first-order identity-transfer reference, direct harmonic quadrature and independent algebraic routes give the following stored-real row ranks:

| high-source cutoff | Z | transverse X/Y | diagonal directions |
|---:|---:|---:|---:|
| `L=8` | 20 | 24 | 24 |
| `L=9` | 27 | 29 | 32 |
| `L=12` | 32 | 32 | 32 |

At `L=12`, the smallest singular values of the continuum operator are approximately

\[
 \sigma_{\min}^{X/Y}=0.010490334912761,
\]

\[
 \sigma_{\min}^{Z}=0.006905664979696537,
\]

\[
 \sigma_{\min}^{\mathrm{diag}}=0.008510322776380.
\]

The `Z` result also has an exact symbolic nonzero-minor certificate. Independent numerical/algebraic lineages have included Wolfram, SymPy, SciPy/mpmath, and additional Octave/JAS/Julia audit branches.

The safe present statement is therefore:

> Under the registered wide-mask, identity-transfer, first-order continuum problem, source multipoles `7<=ell<=12` span the retained stored-real `ell=2..5` carrier for all six registered boost directions.

This is **not yet** the stronger finite-HEALPix statement. The discrete operator still requires a complete numerical-error certificate and supported-runtime exact-head replay.

---

## 9. Matrix-valued numerical-error envelope

The discrete-rank question is now treated as a structured numerical uncertainty problem rather than by one scalar operator-norm floor.

For a frozen registry of `F` nonempty additive error families, with family matrices `E_{f,i}` and deterministic coefficient-ball radii `r_f`, the current source-level envelope is

\[
 \Gamma_E
 =F\sum_f r_f^2\sum_i E_{f,i}E_{f,i}^{T}
 +\lambda^2 I.
\]

For

\[
 \Delta_f=\sum_i b_{f,i}E_{f,i},\qquad
 \|b_f\|_2\le r_f,
\]

family-level Cauchy--Schwarz gives

\[
 \Delta\Delta^T\preceq
 F\sum_f r_f^2\sum_iE_{f,i}E_{f,i}^T
 \preceq\Gamma_E.
\]

The envelope is invariant under the equivalent compensated family reparameterization

\[
 E_{f,i}\to c_fE_{f,i},\qquad
 r_f\to r_f/c_f,
\]

and the implementation rejects an exactly zero family because adding such a family would leave the perturbation set unchanged while incorrectly incrementing `F`.

The error-whitened response is

\[
 \widetilde K=\Gamma_E^{-1/2}K,
\]

and the generalized singular values satisfy

\[
 KK^T u_i=g_i^2\Gamma_Eu_i.
\]

A sufficient robust full-row condition for the declared numerical-error class is

\[
 g_{\min}>1,
\]

equivalently

\[
 KK^T-\Gamma_E\succ0.
\]

This condition is useful only if the declared error families and radii genuinely contain the relevant discretization error. Family/radius provenance and held-out error completeness therefore remain part of the scientific gate.

Current WU-011 source has the invariant-envelope and zero-family guards plus source-equivalent local behavioral checks, but the byte-exact GitHub Actions jobs have repeatedly failed before runner assignment. This infrastructure failure is not counted as either a code pass or a code failure.

---

## 10. Integrated interpretation: morphology is richer, attribution is harder

The corrected tensorization and the response-identifiability analysis reinforce each other.

### 10.1 Tensorization increases observable information

The full Q/O tensors contain directional, mixed and chirality-sensitive information that a scalar power/ceiling vector or a small low-order invariant family can discard. The next observational analysis should therefore operate on the corrected tensors or on a preregistered statistic whose relationship to their proper-rotation quotient is explicit.

### 10.2 More observable information does not imply source identification

A richer tensor statistic still does not determine a physical source by itself. Local observer motion, intrinsic low multipoles, unresolved high-source multipoles, mask/beam/pixel processing and other nuisances can occupy overlapping response subspaces.

The continuum `L=12` result is especially important: in the unrestricted deterministic high-source nuisance problem, the retained low-ell carrier is generically reproducible by higher source multipoles under the registered processed continuum operator. A source attribution therefore requires one or more of:

- a physically justified high-ell prior/covariance rather than an unrestricted deterministic nuisance;
- additional observables or frequency/polarization/depth channels;
- a verified forward response with non-overlapping components;
- a restricted physical source family with explicit nuisance treatment.

### 10.3 Local boost is not global tilt

The local-observer Lorentz pullback is an output-side response. Global matter-frame tilt, if studied later, belongs to a different physical model. The local boost must not be used as a surrogate for a globally tilted cosmology, and a successful boost fit would not establish the origin of the intrinsic anisotropy.

---

## 11. Current observational status

### 11.1 No current corrected anomaly rank

This report intentionally does **not** quote the historical scalar-only MES ranks or the withdrawn WU-006--008 tensor ranks as current observations.

The observational status is:

```text
CORRECTED_TENSOR_REPRESENTATION_CODE: PRESENT
PINNED_MAP_FREE_REPAIR_CONTRACT: PRESENT
LOCAL_REPRESENTATION_REPAIR: REQUIRED
INDEPENDENT_REVIEW: REQUIRED
CORRECTED_OBSERVATIONAL_RERUN: NOT YET PERFORMED
CURRENT_TENSORIZED_ANOMALY_RANK: NONE
```

### 11.2 What historical products may still be used

The pinned historical stored-real harmonic carriers may be used as immutable **input data** for the map-free representation repair. Old Q/O arrays, invariant features, scalar-function ranks, foreground projection conclusions and injection-power interpretations may not be imported as corrected outputs.

### 11.3 Local rerun order

The next observation-bearing sequence is:

1. run the tensor representation repair from pinned Git objects only;
2. preserve all rows and verify the stored-basis, radial `C_l`, proper-rotation and MES normalization invariants;
3. commit a pending terminal and exact input/output manifest;
4. obtain an independent review bound to the candidate head/tree and artifact manifest;
5. freeze the corrected statistic registry before observing new ranks;
6. rerun the paired observation-plus-CMB+noise analysis locally in a new output namespace;
7. use CMB-only simulations only as descriptive sensitivity unless a faithful observation-matched null is constructed;
8. regenerate report figures and result tables from the corrected outputs.

No raw map reopening is needed for the first representation-repair step. A later full observed rerun may use the local admitted data surface under its own read-only contract.

---

## 12. Proposed first-report scientific structure

The first publication/report generated from this programme should be **HTT-only** and should not wait for native BASS solver completion.

A coherent structure is:

1. **Problem and claim boundary** -- low-ell anisotropy as an observable morphology/identifiability problem.
2. **Tensorized low-ell representation** -- stored-real harmonic carrier, correct STF Q/O projection, `SO(3)`/`O(3)` distinction, degeneracies.
3. **MES-derived conditional functions** -- retained only as premise-conditioned one-way functions, not as the primary observational statistic.
4. **Finite-null statistical design** -- row equivariance, exchangeability, finite ranks, dependence and selection rules.
5. **Tensor-orbit statistics** -- generic Krylov chart, overcomplete 16-contraction packet, preregistration and weak-identification behavior.
6. **Local-observer response** -- exact WU-010 full-sky response.
7. **Processed response and identifiability** -- WU-011 cut-sky/no-go analysis, continuum L12 result, numerical-error envelope.
8. **Corrected Planck analysis** -- to be populated only after the local tensorized rerun.
9. **Discussion** -- what low-ell morphology can and cannot identify without a response/prior.
10. **Claim firewall and future channels** -- no causal source, global tilt or family attribution from this analysis alone.

This organization turns the lack of a current corrected observational rank into an explicit reproducibility boundary rather than filling the gap with superseded results.

---

## 13. Revised research DAG

The report-first programme is:

### R0 — Authority synthesis and pre-rerun report

**State:** this document.  
Freeze the supersession map, mathematical conventions, surviving theorem/statistical boundaries, local-observer response evidence and unresolved gates.

### R1 — Corrected tensor-carrier representation repair

Run the PR #440 local map-free repair on the actual checkout using pinned Git objects. No anomaly rank is generated in this step.

Required gates:

- exact source commit/tree and source hashes;
- independent harmonic-to-STF spherical oracle;
- Q/O radial identities;
- correct original-PSTF MES normalization;
- 301 paired rows and 1000 observation-plus-CMB-only rows with exact IDs;
- no row deletion for noncyclic charts;
- pending terminal only.

### R2 — Independent representation review

Bind the review to exact candidate head/tree, input manifest and output hashes. Source-changing repair requires a new candidate; evidence-only closeout may follow a clean review.

### R3 — Statistic preregistration and local corrected observational rerun

Separate two classes:

- **historical frozen questions**, rerun only to measure how their conclusions change under corrected semantics;
- **new tensor/orbit/response statistics**, registered before observed evaluation with explicit tail, calibration pool, nuisance and power study.

The paired observation+CMB+noise lane is the primary finite-null calibration surface. CMB-only remains descriptive unless noise matching is supplied.

### R4 — Report Results and figure rebuild

Populate the observational section only from R3 outputs. Perform two-width hostile figure audit, rank/table provenance checks and a blind statistical review.

### R5 — Resume WU-011 finite-operator robust identifiability work

Return to the original A4 programme:

- branch-specific validation-fixture seal;
- byte-exact supported-runtime execution;
- error-family/radius provenance hashes;
- resolution/iteration/processing controls;
- independent holdout;
- all-six-direction generalized singular-value adjudication.

Do not require an all-direction finite-HEALPix no-go to publish the corrected tensor observational report; if unresolved, report the continuum theorem/evidence and discrete uncertainty boundary honestly.

### R6 — Final report split/publication decision

After corrected observations exist, decide whether the material is best published as one long methods+data paper or split into:

- tensorized finite-null Planck analysis;
- observer-response and low-ell identifiability theory/methods.

The split must be based on scientific coherence, not on preserving historical work-unit boundaries.

---

## 14. Readiness assessment

| Layer | Current readiness | Main remaining gate |
|---|---:|---|
| supersession/authority reconstruction | 100% for this report scope | external review of report wording |
| stored-real/STF normalization theory | 100% scoped | local execution receipt |
| Krylov16 source implementation | ~90% | actual-checkout tests + independent review |
| finite-null statistical principles | ~90% scoped | bind to corrected statistic/null registry |
| corrected tensor carrier products | 0% admitted | local R1 execution |
| corrected Planck tensorized statistic | 0% | R3 preregistration + rerun |
| WU-010 full-sky local boost | ~100% scoped | already closed with typed limits |
| WU-011 processed operator engineering | ~90% | exact supported-runtime/provenance closeout |
| WU-011 continuum L12 surjectivity evidence | ~95% | portable interval/dual-lineage seal if formal claim desired |
| finite-HEALPix robust containment | unresolved | complete matrix-valued numerical-error adjudication |
| first HTT-only report theory/method sections | ~90--95% | editorial condensation + review |
| first HTT-only report observation Results | 0% current | corrected local observational rerun |

---

## 15. Claims allowed now

The following statements are supported at the present scope:

1. The scalar-only MES observational methodology and the old WU-006--008 tensor/injection interpretations are superseded for the next `htt_base` analysis.
2. The stored-real harmonic carrier must be interpreted with the orthonormal `sqrt(2)` convention, and the corrected Q/O radial identities follow accordingly.
3. Original MES epsilon is a PSTF norm, not sky RMS; the scalar MES functions are premise-conditioned one-way functions rather than independent tensor observations.
4. A generic joint STF2/STF3 pair cannot be represented completely by the old eight-coordinate catalogue; the current conditioned Krylov16 packet is an overcomplete generic `SO(3)` orbit representation with explicit chart failure.
5. WU-010 establishes a scoped full-sky local-observer thermodynamic-temperature Lorentz response with sharp quadrupole-response conditioning.
6. Under the registered wide-mask identity-transfer continuum reference, high-source multipoles through `L=12` span the retained `ell=2..5` carrier for all six registered boost directions.
7. The finite HEALPix robust containment conclusion remains unresolved and is being treated with a matrix-valued numerical-error envelope.
8. No current corrected tensorized Planck anomaly rank has yet been produced.

---

## 16. Claims not allowed now

The following are explicitly excluded from this report's current results:

- any historical scalar-only MES rank as the current Planck result;
- any historical WU-006--008 Q/O, foreground or injection result as corrected tensor evidence;
- a calibrated CMB-only-999 p-value for a noisy observation;
- empirical local-boost `beta` estimation or subtraction;
- identification of global matter-frame tilt from the local-observer response;
- physical shear or vorticity inference from the tensor morphology alone;
- causal foreground attribution;
- Bianchi-family identification;
- a finite-HEALPix all-direction containment theorem before numerical-error closure;
- polarization conclusions from the scalar local-boost programme;
- any claim that native BASS solver output is used or required here.

---

## 17. Immediate conclusion

The `htt_base` programme is no longer best described as a scalar MES anomaly analysis. Its current coherent form is a **tensorized low-multipole inference programme with finite-null calibration and explicit response-limited identifiability**.

The main methodological correction is constructive: preserve the full low-ell harmonic/tensor information, treat MES quantities as conditional scalar functions rather than geometry measurements, and make physical attribution contingent on a verified response and nuisance model.

The main observational conclusion at this evidence cutoff is intentionally negative but precise: **there is no current corrected tensorized Planck rank to report.** The next observation-bearing result must come from a local rerun under the corrected representation and a preregistered tensor/response statistic.

The main theory result added by the later response lineage is complementary: the processed low-ell carrier can be saturated by high-source continuum responses under a broad deterministic nuisance model, so richer morphology does not by itself remove source nonidentification. This motivates a future analysis in which tensor morphology, local-observer response, high-ell priors and any additional observational channels are modelled jointly rather than inferred from scalar low-ell ceilings.
