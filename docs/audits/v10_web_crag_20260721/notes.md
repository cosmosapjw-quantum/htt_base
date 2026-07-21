# v10 report web CRAG — external-literature cross-check ledger (2026-07-21)

Purpose: adjudicate the K/C/P/S novelty tier for every claim rendered in the
v10 external audit report. All queries executed inline on 2026-07-21
(subagent lanes unavailable — external API spend limit; inline execution
disclosed per the PR-132 precedent). Each entry: finding → citation →
tier consequence. This ledger is an internal evidence file; the report
renders only the resulting tags and citations, never this process text.

## Rubric (frozen for v10)

- **K (known)**: the mathematical fact or method is standard/published;
  our contribution is at most an independent re-derivation or an
  implementation-level verification.
- **C (cross-check)**: our measured number/result cross-checks a published
  external number (agreement or registered disagreement), or an external
  result cross-checks ours.
- **P (potential advance)**: analysis or theorem plausibly beyond the
  published literature (CRAG-evidenced absence of a published equivalent),
  but not promotable to a significant claim today under its own
  conditionality/validation status.
- **S (significant claimable)**: a result whose claim gates permit
  asserting a novel significant scientific result now. Assignment strictly
  bounded by the internal claim ledger; a gate-held candidate is tagged P
  with its condition stated.

Tier tags compose: e.g. "K (method) / C (number)" where a known method
produces a cross-checked value.

## Cluster findings

### A1. CF4 bulk flow (Watkins+ 2023; Whitford+ 2023)
- Watkins et al. 2023 (MNRAS 524, 1885; arXiv:2302.02028): CF4 MV bulk
  flow |B| = 419 ± 36 km/s at R = 200 h^-1 Mpc; >4σ tension quoted
  (~0.015% probability under ΛCDM+CMB parameters).
- Whitford, Howlett & Davis 2023 (MNRAS 526, 3051; arXiv:2306.11269):
  estimator uncertainties are typically UNDER-estimated (non-linear
  velocities) → tension over-stated; MLE 408 ± 165 km/s @ 49 h^-1 Mpc,
  MVE 428 ± 108 km/s @ 173 h^-1 Mpc (0.11% chance of larger chi^2).
- Tier consequences: our MV reproduction (|B|(200) = 405 km/s, apex 8.5°
  from published at R = 50) = **C**. Our full-covariance significance
  deflation (~1σ honest vs ~8σ noise-only) and the significance-withheld
  discipline = **P** (the deflation mechanism parallels Whitford's
  simulation finding but is derived analytically from the estimator-matched
  linear cosmic-variance covariance; CRAG found no published CF4 analysis
  reporting the full-cov Mahalanobis deflation as the primary treatment).

### A2. CMB Doppler boost (Planck 2013 XXVII)
- Planck 2013 XXVII (A&A 571, A27; arXiv:1303.5087): aberration+modulation
  detection at beta = 1.23e-3 expected; measured 384 ± 78 km/s in the
  dipole direction (l,b) = (264°, 48°). High-ell (500 < l < 2000)
  harmonic-space estimator.
- Tier consequences: boost physics + detection = **K**. Our PR-180
  zero-parameter LOW-ell (2..10) residual consistency test against the
  BOOSTED FFP10 null (p = 0.854) = **P**: literature measures/fits the
  boost amplitude at high ell; CRAG found no published zero-parameter
  low-ell residual-excitation consistency test conditioned on
  boost-carrying end-to-end simulations.

### A3. Boosted FFP10 ensemble
- Planck 2018 III + Planck 2018 VII confirm FFP10 CMB MC include Doppler
  boosting (dipolar modulation + aberration). Mukherjee & Souradeep-line
  CoNIGS work generates boosted statistically-anisotropic realizations.
- Tier consequence: FFP10 boost content = **K** (documented sim property);
  its use as the identical-treatment null for a residual statistic = part
  of the PR-180 **P**.

### A4. BiPoSH formalism and odd-L structural zero
- Hajian & Souradeep BiPoSH formalism = **K**.
- Book, Kamionkowski & Souradeep 2012 (PRD 85, 023010; arXiv:1109.2910)
  and prior BiPoSH literature state the exchange symmetry
  A^{LM}_{l1 l2} = (-1)^{l1+l2-L} A^{LM}_{l2 l1}; for l1 = l2 = l the
  diagonal A^{LM}_{ll} exists for even L and VANISHES for odd L.
- Tier consequence: the PR-149 odd-L diagonal structural-zero theorem is
  **K** (known symmetry result), independently re-proven here by a sympy
  Wigner-3j oracle and verified on reality-violating alm; the
  trials-quotient application inside our look-elsewhere accounting = C-level
  implementation verification. NOT tagged P.

### A5. Low-ell anomalies + look-elsewhere
- Planck 2018 VII (A&A 641, A7; arXiv:1906.02552): anomalies persist at
  ~2-3σ; look-elsewhere handled by MC counting over 10^4 sims; no single
  anomaly promotes to a detection. Schwarz et al. 2016 (CQG 33, 184001)
  review: alignment ~4.9% level, missing correlation ~0.1%, posterior-
  selection caveats.
- Tier consequences: existence and approximate significance of low-ell
  features = **K**. Our PR-150 exchangeable pooled-rank look-elsewhere
  global p = 0.0365 over six pre-registered statistics under the
  SMICA-processed FFP10 E2E null = **C** (consistent with the 2-3σ
  literature band) + **P** for the exchangeable-support finite-null
  construction with hard floor validation (Phipson-Smyth exact-discrete
  global rank over a registered statistic set; CRAG found no published
  low-ell analysis using this exact estimator).

### A6. Bianchi/anisotropy limits
- Saadeh et al. 2016 (PRL 117, 131302; arXiv:1605.07178): general Bianchi
  VII_h test on Planck T+P; vector mode (sigma_V/H)_0 < 4.7e-11 (95% CI),
  weakest regular-tensor limit 1.0e-6.
- Pontzen & Challinor 2007 (MNRAS 380, 1387; arXiv:0706.2075): Bianchi
  multipole hierarchy with polarization; B-mode power comparable to E and
  parity-violating (TB/EB) correlations predicted in anisotropic models.
- Tier consequences: comparison rows quoting Saadeh = **K/C**
  (model-conditional external ceiling, used comparison-only). PR-182
  parity identities are consistent with and attributed to Pontzen &
  Challinor (CONFIRMATORY) = **K** for the physics content; the
  four-axis exact verification + the registered refutation of the
  program-internal sign(EB/TB) = sign(x_h) relation (ratio parity-even)
  = internal corrective mathematics, **K** tier (elementary once stated),
  recorded for completeness.
- Ellis & MacCallum 1969 (Comm. Math. Phys. 12, 108) canonical structure
  constants and curvature scalars = **K**; PR-175's 11-type exact
  Koszul == anchor equality = implementation-grade verification (**K**,
  with the dual-engine bound 8.2e-10 as C-level cross-check).

### A7. DESI DR1 dipole context
- DESI DR1 BGS documentation (data.desi.lbl.gov/doc/releases/dr1) = the
  release used. QSO-based LSS-dipole work on DESI DR1 (2606.00551-line)
  reports bulk-velocity 443.8 ± 204.1 km/s consistent with 370 km/s at
  1.56σ with directional offsets, sample-dependent.
- Tier consequences: our window-corrected BGS number-count dipole
  D = 9.49e-3, clustering-dominated, consistent with ΛCDM clustering
  mocks (p = 0.90) = **C** (adds a BGS low-z data point to the dipole
  literature; consistent-null direction). Exact-selection per-mock refit
  machinery on the real random density (PR-151 card) = **P**
  (methodological; official-mock significance deferred, stated as a data-
  availability condition).

### A8. ACT DR6 lensing
- Madhavacheril et al. 2024 / Qu et al. 2024 (ApJ 962, 112/113;
  arXiv:2304.05203): DR6 map 9400 deg^2, reconstruction from
  600 < l < 3000, signal-dominated L < 150; release provides map + 400
  sims + N0/N1 products.
- Tier consequences: our low-L mean-field-debiased isotropy consistency
  (p = 0.35) and the 95% band-power UL = **C** (consistent with the
  release's own isotropy expectations); the leave-one-simulation cross-fit
  mean-field construction at low L = **P** (method-level; disclosed exact
  ((n-1)/n)^2 scaling); the raw-QE availability result (RDN0 unformable
  from public products) = **C** (documents a release property).

### A9. fsigma8 from peculiar velocities
- Courtois et al. 2023 (A&A 670, L15): CF4 pairwise fsigma8 = 0.38 ± 0.04
  (ungrouped), 0.36 ± 0.05 (grouped); CF4-based MCMC local values ~0.4.
- Tier consequence: our field-level ML fsigma8 = 0.40 ± 0.02 (stat) ± 0.10
  (jackknife-conservative) = **C** (agrees with CF4 literature; Planck
  ~0.44 consistent). Whitened-eigenbasis O(N) field-level ML on grouped
  CF4 = method detail, not claimed novel.

### A10. Directional H0 anisotropy from CF4 (PR-179 context)
- A CF4 Tully-Fisher W1 zeropoint-dipole analysis reports a 3.9σ dipole
  (0.063 ± 0.016 mag, ~3% H0 variation; Boubel et al. line). A 2025
  forward-modelling reanalysis (MNRAS staf2048; arXiv:2509.14997, "No
  evidence for local H0 anisotropy from Tully-Fisher or supernova
  distances") attributes such signals to un-modelled selection/velocity
  systematics.
- Tier consequences: PR-179's H-only exact rank 2/20000 CONDITIONAL on
  selection systematics (all q-block results withheld by the cubic
  falsifier) = **C** (our conditionality independently lands on the same
  systematics interpretation as the 2025 reanalysis) + **P** for the
  reconstruction-independent directional estimand with pre-registered
  falsifier gates. NOT S: the selection channel is open; promotion path
  runs through the official-mock and adjudication stages (data-availability
  condition).

### A11. Partial identification methods in PV cosmology
- Imbens & Manski 2004 (Econometrica 72, 1845) + Manski partial-
  identification literature = **K** (econometrics). CRAG search found NO
  published application of identified-set/Imbens-Manski machinery to bulk
  flow / peculiar-velocity nuisance treatment.
- Tier consequences: PR-136 exact identified-set engine, PR-137
  simultaneous IM coverage at least-favorable boundaries, PR-147
  nuisance-box identified sets for the CF4 flow (bounded-widening result)
  = **P** (methodological transfer with no published cosmology equivalent
  found).

### A12. Statistical methods (tags K)
- Phipson & Smyth 2010 (permutation p-values never zero; exact-discrete
  (1+b)/(N+1)) = K. Imbens & Manski 2004 = K. Talts et al. 2018 SBC = K.
  Vehtari, Gelman & Gabry 2017 (ELPD/PSIS-LOO); Vehtari et al. 2015
  PSIS = K. Hartlap et al. 2007 / Sellentin & Heavens 2016 (finite-sim
  covariance corrections) = K. Gorski 1988 velocity correlation
  Psi_par/Psi_perp = K. Eisenstein & Hu 1998 P(k) = K.
- Our contribution on these = correct composition + fail-closed
  implementations (implementation-grade, not method novelty).

## S-tier adjudication (v10)

No result is tagged S in v10. Every S-candidate is held by an explicit
condition: the CF4 directional statistic (A10) by the open selection-
systematics channel and pending official-mock validation stages; the K1
global rank (A5) by its E2E conditionality and single-pipeline support;
the theory stack (MES re-freeze, OMK slaving, KE program) is exact
mathematics tagged K/C/P per item and is publishable as
theory/methods content, but the program does not assert a novel
significant OBSERVATIONAL claim from it. The report states each condition
scientifically (what data/analysis would close it), never as process
narrative.

## Access record

All queries via inline web search, 2026-07-21 (UTC+9 session). Citation
identifiers (arXiv ids, journal refs) recorded above; the report's
bibliography renders these as standard citations. Primary-source PDFs for
MES/SAG/MESa lineage were already SHA-archived in-repo
(docs/audits/mes_primary_sources/, docs/audits/...) during earlier cycles
and are reused as the authority for those items.

## v2 re-adjudication (2026-07-21, owner-directed)

Owner directive: the tier is an EXTERNAL-NOVELTY adjudication only —
internal diagnostic-only gates must not drive it. Ledger rewritten to
schema v2: every K carries a citation or explicit textbook-level note;
every C names the exact study and quantity cross-checked; every P/S
states the delta over the named closest literature. Scope/conditionality
stays in each result's claim boundary, separate from the tier.

Additional CRAG (3 queries, inline):
- Converse failure of EGS is PUBLISHED: Nilsson, Uggla, Wainwright & Hsu
  1999, "An almost isotropic cosmic microwave temperature does not imply
  an almost isotropic universe" (astro-ph/9904252) -> G-EGS converse
  retagged K+C (was framed as program-novel).
- KS/Bianchi-III center-manifold literature is qualitative (Collins-
  Ellis 1979; Hewitt-Wainwright 1992; Wainwright-Ellis 1997 book): no
  published exact slaving coefficient kappa = -1/(2+q) or certified
  remainder found -> G-OMK tagged S with stated delta.
- Tilted-model literature (King-Ellis 1973; Coley-Hervik line): no
  published dynamical double obstruction at flat anisotropic curvature
  found -> G-KE tagged S with stated delta.

S set (v2): G-MES-REFREEZE, G-OMK, G-KE, T-IDSET (+CF4 application),
D-K1-BOOST. Each S entry's adjudication text carries the base
literature and the delta; data-side S items remain
conditionality-labelled in their result sections (the tier asserts
novelty + completeness, never a detection).
