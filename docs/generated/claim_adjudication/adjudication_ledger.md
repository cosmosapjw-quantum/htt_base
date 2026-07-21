# Claim-adjudication unlock ledger

28 claim families adjudicated against the external literature on four axes (significance / novelty K-C-P-S / completeness / verification). The Independence gate is never fake-passed.

## Counts by unlock status

- **BLOCKED_ON_DATA_PR151**: 1 (D-DESI)
- **BLOCKED_ON_NATIVE_SOLVER**: 3 (D-TEFF, II-NATIVE, T-SHARP)
- **GENUINELY_INCOMPLETE**: 3 (M-ESTCOV, M-PARTIALID, T-KE)
- **PROCESS_GATE_NO_LITERATURE_AXIS**: 1 (M-DUALAXIS)
- **PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION**: 20 (D-ACT, D-CF4, D-K1, M-CLUSTER, M-DISCRIM, M-EVALUE, M-EVIDENCE, P-LEGACY, T-BIANCHI, T-BRIDGE, T-EGS, T-FRAME, T-JOINT, T-MES, T-MULTIFLUID, T-OMK, T-PARITY, T-RANK2, T-W2, T-XC)

## Promotion queue (all-axes-pass, one non-author adjudication from VALIDATED)

1. **T-OMK** [incremental/P] — Omega_k higher-order slaving Sigma = kappa K + c2 K^2
2. **T-XC** [incremental/C] — Master FLRW-departure identity x_C = Sigma2 - W2 + Omega_tilt + DeltaOmega_k
3. **T-MES** [incremental/C] — MES source-exact shear/vorticity ceilings + attribution surface
4. **T-EGS** [incremental/C] — One-way FLRW/EGS + converse counterexample registry
5. **M-DISCRIM** [incremental/C] — Contamination-aware local/global source discrimination + abstention
6. **D-K1** [incremental/C] — Planck K1 low-multipole BiPoSH structural zero + even-L rank
7. **D-CF4** [incremental/C] — CF4 bulk flow + same-data LambdaCDM cosmic-variance deflation
8. **T-W2** [incremental/K] — Constraint-natural vorticity convention W2 = omega_ab omega^ab/(6H^2)
9. **T-FRAME** [incremental/K] — Congruence-indexed frame algebra + signed carrier + Frobenius gate
10. **M-CLUSTER** [incremental/K] — Cluster-exchangeable finite-null rank
11. **T-PARITY** [marginal/C] — Solver-free parity/handedness identities + reference registry
12. **D-ACT** [marginal/C] — ACT DR6 kappa low-ell isotropy upper limit
13. **T-JOINT** [marginal/K] — Joint feasible-set support theorem (product box a corollary)
14. **T-RANK2** [marginal/K] — Comparator rank-2 non-identification (W2/DeltaOmega_k joint null)
15. **T-MULTIFLUID** [marginal/K] — Multi-fluid moment cone: zero flux does not imply zero stress
16. **T-BRIDGE** [marginal/K] — Finite-window stochastic bulk-flow -> homogeneous-tilt rank bridge
17. **T-BIANCHI** [marginal/K] — Bianchi class A/B structure-constant atlas
18. **M-EVALUE** [marginal/K] — Dependent-merge + anytime e-value / Ville crossing
19. **M-EVIDENCE** [marginal/K] — Coherent normalized evidence + inactive-prior invariance
20. **P-LEGACY** [marginal/K] — Legacy inventory hash-binding + mutation corpus + disposition

## Per-family adjudication

### D-ACT — ACT DR6 kappa low-ell isotropy upper limit

- lane: data; cards: PR-152, PR-177
- literature: ACT DR6 lensing 2023 (Madhavacheril+ / Qu+)
- axes: significance=marginal, novelty=C, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: Cross-check (C) of the ACT DR6 lensing release, not a delta over it. Madhavacheril et al. 2024 (ApJ 962,113, kappa map) and Qu et al. 2024 (ApJ 962,112, power spectrum + 400 recon sims) supply the exact data and sim products this card re-uses. The card's ell=2..10 band lies entirely below the ACT DR6 science range (baseline 40<L<763, signal-dominated only L<150), so the low-ell band is reconstruction-noise/mean-field dominated exactly as those papers characterise it; the p=0.35 null and noise-floor-limited 3.28e-6 upper limit are the expected consistency result, not a new measurement. Closest isotropy prior art — Planck convergence isotropy (arXiv:1708.09793) and ACT DR6 morphological patch analysis (arXiv:2503.17849) — already probe kappa-map isotropy by other estimators. This card adds a specific low-ell band-power UL as an independent-instrument companion to the Planck K1 lane, but on a band with no physical constraining power and a fail-closed theory-g link, so there is no S/P delta over the cited work.
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication

### D-CF4 — CF4 bulk flow + same-data LambdaCDM cosmic-variance deflation

- lane: data; cards: PR-145, PR-146, PR-147, PR-148
- literature: Watkins+ 2023 MNRAS 524,1885; Whitford, Howlett & Davis 2023 arXiv:2306.11269
- axes: significance=incremental, novelty=C, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: Cross-check of specific named studies. The deflation reproduces Whitford, Howlett & Davis 2023 (arXiv:2306.11269 = MNRAS 526, 3051): estimator uncertainties are underestimated, overestimating ΛCDM tension. PR-145 confirms this via an analytic linear-theory Górski (1988) cosmic-variance covariance (A^-1 M A^-1, diag=sigma_v_1d^2) that collapses the noise-only ~8σ to ~1σ; amplitude ~320 km/s is anchored to Watkins+ 2023 (MNRAS 524, 1885, 419±36 km/s). No delta over the cited work is demonstrated: the linear-CV route is a lower-bound (lower-fidelity) version of Whitford's full-mock treatment (literature residual ~2-3σ from nonlinear mocks), and the PR itself defers credible significance to MV/release-matched mocks. PR-148 fσ8=0.386 is ΛCDM-consistent, a null. Hence C, not P.
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication | provenance override: cited_correct: adversarial verify confirmed references.bib Watkins2023 (MNRAS 524,1885) and Whitford2023 (arXiv:2306.11269); the lit-CRAG 'miscited' flag was a false positive | note: lit-CRAG unlock string was refuted (advisory); status re-derived from axes

### D-DESI — DESI number-count dipole survey-conditional null

- lane: data; cards: PR-151, PR-226
- literature: Secrest+ 2021 ApJL 908,L51; DESI DR1 (official EZmock/Abacus)
- axes: significance=incremental, novelty=C, completeness=partial, verification=unverified, provenance=cited_correct
- novelty rationale: Anchor Secrest2021 (ApJL 908 L51) verified correct: CatWISE high-z all-sky quasar number-count dipole, 4.9sigma excess over the kinematic (Ellis-Baldwin) expectation. D-DESI applies the SAME number-count-dipole estimator to DESI DR1 BGS_BRIGHT at 0.1<z<0.4 — a low-z, clustering-dominated sample that is the wrong regime for the kinematic dipole Secrest probes — calibrated against DESI's own clustering-mock covariance (the standard 1000 EZmock + 25 AbacusSummit machinery, cf. DESI DR1 clustering-systematics papers). That makes it a cross-check of the established Secrest/Ellis-Baldwin framework on a different, suboptimal-for-kinematics sample, not a test of Secrest's high-z excess. The only potential P-level delta — a first DESI-BGS official-mock survey-conditional number-count-dipole null (no such published paper found; cf. Chen et al. 2026 A&A 708 A307 is quasar, not BGS) — is claimed but NOT demonstrated: docs/generated/desi_official_mock_card.json does not exist and the sole present artifact is SUPERSEDED_PREFLIGHT_ONLY synthetic. No differentiated result produced, so novelty defaults to C.
- **unlock: BLOCKED_ON_DATA_PR151** — DESI official-mock acquisition (PR-151) not yet terminal

### D-K1 — Planck K1 low-multipole BiPoSH structural zero + even-L rank

- lane: data; cards: PR-149, PR-150
- literature: Pontzen & Challinor 2007; Planck 2018 VII isotropy
- axes: significance=incremental, novelty=C, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: The odd-L diagonal BiPoSH structural zero (A^{LM}_{ll}=0 for odd L, for ANY alm) is a KNOWN algebraic identity from Clebsch-Gordan/Wigner-3j exchange symmetry — originating in Hajian & Souradeep 2003 and formalized in Book, Kamionkowski & Souradeep 2012 (PRD 85, 023010; arXiv:1109.2910), which the card's docstring cites correctly; this component is K, and the card itself labels it 'known result, independently re-proven.' The even-L rank component is a cross-check of Planck 2018 VII 'Isotropy and Statistics of the CMB' (A&A 641, A7; arXiv:1906.02552): it reproduces the established low-multipole isotropy consistency (pooled exchangeable rank p=0.195; L2 p=0.466, L4 p=0.505 — no anomaly) using an FFP10-E2E-conditional exchangeable-rank framing (Hartlap LOO) that refines the earlier GRF-null k1_biposh_smica diagnostic. This is a methodological refinement, NOT a new signal or a demonstrated delta over Planck 2018 VII; no P/S delta exists. Tier C (named-study cross-check, no delta).
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication

### D-TEFF — Teff/BASS-lite certified surrogate contract

- lane: data; cards: PR-218
- literature: reduced-order surrogate modeling (generic); no native oracle available
- axes: significance=marginal, novelty=K, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: Standard reduced-order-surrogate / emulator certification methodology with zero delta over the literature. Cosmological emulators are always trained and validated against a native Boltzmann solver (CLASS/CAMB) over a declared parameter domain with held-out validation accuracy — CosmoPower (Spurio Mancini et al. 2022, MNRAS 511, 1771), CosmicEmu/Mira-Titan (Heitmann/Moran et al.). Statistical modeling of a reduced-order-model error envelope is the ROMES method (Drohmann & Carlberg 2015, arXiv:1405.5170), and domain-of-validity / out-of-distribution gating plus strict dev/eval separation is textbook UQ. PR-218's nested disjoint splits, quantile error envelope, >5x OOD rejection, and no-leakage flag reproduce this template exactly. Moreover both 'surrogate' and 'native_reference' are toy analytic polynomials (native_reference is explicitly commented as NOT a real solver), so there is not even a numerical cross-check of a named study. The only non-standard element is the honest refusal to authorize inference absent a native oracle — a governance stance, not a research novelty. Delta over cited work = none (K).
- **unlock: BLOCKED_ON_NATIVE_SOLVER** — requires an authenticated native Bianchi Boltzmann solver delivery (Track II)

### II-NATIVE — Native Bianchi Boltzmann solver observable-response claims

- lane: theory; cards: PR-229, PR-230, PR-231, PR-232, PR-233, PR-234
- literature: Pontzen & Challinor 2007; Saadeh+ 2016 arXiv:1605.07178 (Planck Bianchi)
- axes: significance=incremental, novelty=K, completeness=incomplete, verification=unverified, provenance=cited_correct
- novelty rationale: The claim family is a native low-ell Bianchi Boltzmann solver producing the CMB observable response (C_{lm,l'm'}(g) / A^{LM}_{ll'}(g) / T+E+B polarization) for a proposed Bianchi geometry. That capability is already established in the cited literature: Pontzen & Challinor 2007 (MNRAS 380, 1387; arXiv:0706.2075) derives the full Bianchi CMB radiative-transfer multipole hierarchy in the near-FRW limit including recombination, E/B polarization and reionization; Saadeh et al. 2016 (PRL 117, 131302; arXiv:1605.07178, with companion framework arXiv:1604.01024 / MNRAS 462, 1802 via ANICOSMO) computes the all-DOF scalar+vector+tensor temperature+polarization observable response and fits it to Planck. The BASS family is unimplemented (no repo evidence file; joint_pv_cmb_forecast raises OutOfScopeError/AWAITING_NATIVE_LOWELL_SOLVER and never fabricates a covariance), so NO delta over the cited work is demonstrated -- it would replicate known/textbook physics. Hence tier K, not C/P/S. The only in-repo work is a single-mode semi-native shear->quadrupole transfer that explicitly makes no family/geometry claim.
- **unlock: BLOCKED_ON_NATIVE_SOLVER** — requires an authenticated native Bianchi Boltzmann solver delivery (Track II)

### M-CLUSTER — Cluster-exchangeable finite-null rank

- lane: method; cards: PR-135, PR-197
- literature: Phipson & Smyth 2010 SAGMB 9,39 (permutation p-values)
- axes: significance=incremental, novelty=K, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: Cross-check of Phipson & Smyth 2010 (SAGMB 9(1):39; arXiv:1603.05766), whose exact-discrete pooled-rank estimator p=(1+b)/(N+1) with conservative >= ties PR-197 verifies to be super-uniform. The only added element is setting the exchangeable unit to the cluster rather than the observation and refusing the naive reused-cluster 'exact' label. That cluster-vs-observation exchangeability distinction is itself textbook-known in cluster-randomized permutation testing (swpermute, PMC7305031; clustered-data exact tests PMC5472394) and in conformal group-exchangeability (arXiv:2005.06095, Exchangeability, Conformal Prediction, and Rank Tests). No new theorem beyond composing two known results; the exact enumeration and Monte-Carlo size control confirm rather than extend the cited theory. Hence C, not P/S: a faithful verification/cross-check of a named study with no demonstrated delta.
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication | note: lit-CRAG unlock string was refuted (advisory); status re-derived from axes

### M-DISCRIM — Contamination-aware local/global source discrimination + abstention

- lane: method; cards: PR-141, PR-221
- literature: Bayesian model comparison; Secrest+ 2021 dipole competitors
- axes: significance=incremental, novelty=C, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: Cross-check of a specific named body of work, no demonstrated delta. The direct precedent is Dam, Lewis & Brewer 2023 (MNRAS 525, 231; arXiv:2212.07733), which already performs Bayesian-evidence model comparison among competing dipole hypotheses (kinematic vs alternatives) on the real Secrest et al. 2021 (ApJ 908, L51) CatWISE quasar sample; the Quaia Bayesian analysis (MNRAS 527, 8497) and the NVSS/RACS Bayesian analysis (MNRAS 531, 4545) further do kinematic-vs-clustering-vs-CMB-aligned model selection with adequacy/support gating on real data. PR-141/PR-221 is a SYNTHETIC linear-Gaussian / BIC-penalised-chi2 re-instantiation of the same model-comparison-with-adequacy machinery over self-generated competitors; its 'mandatory abstention' gate is standard goodness-of-fit-gated Bayesian model comparison (cf. Starkman, Trotta & Vaudrevange 2010; Trotta 2008 'Bayes in the sky') relabeled, and it makes no real-data or detection claim. It does strictly less than the named studies (toy data only), so no P/S delta is demonstrated; it is a clean methodological cross-check (C), with the core Bayesian model comparison itself textbook (K).
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication

### M-DUALAXIS — External-novelty x internal-readiness promotion state machine

- lane: process; cards: PR-185, PR-213
- literature: n/a (governance state machine, no external-literature novelty axis)
- axes: significance=marginal, novelty=K, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: No external-literature novelty axis exists: PR-185 is a governance/process state machine (dual-axis SSoT keeping the K/C/P/S external-novelty tier orthogonal to an 8-state internal readiness axis, six-gate conjunctive promotion), targeting internal audit criticisms H23/H24, with zero cosmology/physics content. The underlying pattern — keeping novelty orthogonal to maturity/readiness — is textbook governance and decision engineering: NASA Technology Readiness Levels held orthogonal to novelty, balanced readiness-level assessment, and multi-axis maturity frameworks (KTH model). It cross-checks/duplicates no named cosmology study and demonstrates no scientific delta over any cited work, so it sits at K (known/standard practice). Not a P/S because there is nothing in the research literature it advances.
- **unlock: PROCESS_GATE_NO_LITERATURE_AXIS** — governance/state-machine card; no external-literature novelty axis

### M-ESTCOV — Finite-covariance Hartlap + Sellentin-Heavens t likelihood

- lane: method; cards: PR-142, PR-225
- literature: Hartlap+ 2007 A&A 464,399; Sellentin & Heavens 2016 MNRAS 456,L132
- axes: significance=incremental, novelty=K, completeness=partial, verification=verified, provenance=cited_correct
- novelty rationale: Textbook reproduction, no delta. The Hartlap factor alpha=(Nsim-m-2)/(Nsim-1)=76/89=0.85393 is reproduced verbatim from Hartlap, Simon & Schneider 2007 (A&A 464, 399) with no methodological change. The anytime e-value axis (E=exp(lam*x-lam^2/2), arithmetic-mean merge, cumulative-product test martingale, Ville crossing P(sup>=20)<=1/20) is standard sequential-inference material (Vovk-Wang merging; Ramdas et al. 2020 anytime-valid martingales). Crucially, Sellentin & Heavens 2016 (MNRAS 456, L132) is named in the claim-family label but its marginalized modified-t likelihood is NOT implemented anywhere in the terminal, so the terminal cannot even be scored as a cross-check (C) of that paper. Net: known/textbook, no delta over any cited work.
- **unlock: GENUINELY_INCOMPLETE** — not yet complete+verified author-side: completeness=partial | note: lit-CRAG unlock string was refuted (advisory); status re-derived from axes

### M-EVALUE — Dependent-merge + anytime e-value / Ville crossing

- lane: method; cards: PR-225
- literature: Ramdas, Grunwald, Vovk & Shafer 2023 (game-theoretic statistics / e-values)
- axes: significance=marginal, novelty=K, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: All three sub-claims are Monte-Carlo re-demonstrations of established/textbook results with no delta over the cited literature. (1) The anytime/Ville-crossing axis (test martingale from cumprod crosses 20 at 0.0212 <= 1/20) is a direct textbook consequence of Ville's inequality as reviewed in the anchor, Ramdas, Grunwald, Vovk & Shafer 2023 (Stat. Sci. 38(4), 576-601, DOI 10.1214/23-STS894). (2) The dependent-merge (arithmetic mean of correlated e-values has mean <= 1) is precisely the arbitrary-dependence averaging result of Vovk & Wang 2021 (Ann. Stat. 49(3), 1736-1754) -- their headline theorem that the arithmetic mean is a valid e-merging function under arbitrary dependence. (3) The Hartlap correction (factor (N-m-2)/(N-1)=76/89=0.85393, calibrating raw chi^2/m 1.181 -> 1.008) is exactly Hartlap, Simon & Schneider 2007 (A&A 464, 399). No new theorem, no delta, no cosmology result -- known machinery numerically confirmed on a toy Gaussian simulation.
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication

### M-EVIDENCE — Coherent normalized evidence + inactive-prior invariance

- lane: method; cards: PR-129, PR-140, PR-220
- literature: MacKay 2003 (Occam factor); thermodynamic integration / bridge sampling
- axes: significance=marginal, novelty=K, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: All content is textbook with no delta over cited work. The headline "inactive normalized parameter creates no Occam penalty" is exactly the Occam-factor property of MacKay 2003 (Information Theory, Inference, and Learning Algorithms, Ch. 28: Occam factor = posterior/prior width = 1 for an unconstrained parameter) and is stated verbatim in the cosmology literature by Trotta 2008 "Bayes in the sky" (arXiv:0803.4089): "the Bayesian evidence does not penalize models with parameters unconstrained by the data" (the prior volume cancels), echoed in arXiv:0802.3185. The two-engine cross-check is a standard validation exercise: thermodynamic integration/path sampling = Gelman & Meng 1998; bridge sampling = Meng & Wong 1996 (Statistica Sinica 6:831-860); both recover the elementary exact conjugate-Gaussian evidence (log BF10=1.6125). The only original element is the governance wrapper (content-addressed receipts, sample-digest independence, 6/6 mutation kills, sympy mass=1 seal) — engineering, not a scientific or statistical delta. Hence K, not P/S.
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication

### M-PARTIALID — Estimated-cov partial-ID confidence set + continuum coverage

- lane: method; cards: PR-136, PR-137, PR-200, PR-225
- literature: Imbens & Manski 2004; Stoye 2009 Econometrica 77,1299
- axes: significance=incremental, novelty=K, completeness=partial, verification=verified, provenance=cited_correct
- novelty rationale: Textbook Imbens & Manski (2004) Econometrica 72(6):1845-1857 construction: im_constant() solves exactly their factor Phi(C+Delta/sigma)-Phi(-C)=1-alpha, and the 'point CI undercovers monotonically' finding is IM's own motivating pathology. No delta over IM 2004 is demonstrated. The one regime that could be a real delta -- estimated covariance / Sellentin-Heavens-t, i.e. precisely the Stoye (2009) Econometrica 77(4):1299-1315 superefficiency/uniformity regime -- is explicitly deferred: coverage_mc() uses a known fixed sigma for both data generation and interval construction. So the delivered artifact is the KNOWN-variance special case, cite IM 2004; no novelty delta.
- **unlock: GENUINELY_INCOMPLETE** — not yet complete+verified author-side: completeness=partial | note: lit-CRAG unlock string was refuted (advisory); status re-derived from axes

### P-LEGACY — Legacy inventory hash-binding + mutation corpus + disposition

- lane: process; cards: PR-209, PR-214, PR-227
- literature: n/a (provenance mechanics; legacy archives are immutable fixtures)
- axes: significance=marginal, novelty=K, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: Pure reproducibility/provenance infrastructure with zero scientific-literature novelty. The mutation kill-matrix / negative-control corpus (PR-214) is textbook mutation testing (DeMillo, Lipton & Sayward, "Hints on Test Data Selection," IEEE Computer 11(4), 1978; first tool Budd 1980) — a "killed mutant" caught by a detector is the canonical construct. The hash-binding + CRC + content-addressed legacy pin (PR-209) is standard content-addressable/Merkle-hash provenance. The 18-card byte-stable reproduction (PR-227) is a direct application of the reproducible-builds standard, which itself defines the author-vs-independent-rebuilder distinction the cards use. No delta over any of these: the mechanics are correct applications of established practice to an internal cosmology-code archive, not a new method. No FLRW/Bianchi/Maartens-Ellis-Stoeger literature is implicated (anchor n/a by construction).
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication

### T-BIANCHI — Bianchi class A/B structure-constant atlas

- lane: theory; cards: PR-214
- literature: Ellis & MacCallum 1969 CMP 12,108 (Bianchi classification)
- axes: significance=marginal, novelty=K, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: The claim is the Bianchi class A/B structure-constant atlas (Class A = {I, II, VI0, VII0, VIII, IX}; Class B = {III, IV, V, VIh, VIIh}), reproduced verbatim in revival_mutation_lab.py. This is exactly the classification of Ellis & MacCallum 1969 (Commun. Math. Phys. 12, 108), defined by the trace vector a_b (a_b=0 for class A, a_b!=0 for class B) in the decomposition C^a_bc = eps_dbc n^{ad} + delta^a_c a_b - delta^a_b a_c with n^{ab}a_b=0. It is the single most textbook-standard result of the Bianchi literature (also in Wainwright-Ellis 1997 non-tilted class A/B chapters, Scholarpedia). ZERO delta over the cited work: the atlas is a QA lookup table used as a negative-control mutation detector (VI0->B / VIIh->A swap flagged as exactly {VI0, VIIh}), not new research. Tier K, no P/S delta demonstrated.
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication | note: lit-CRAG unlock string was refuted (advisory); status re-derived from axes

### T-BRIDGE — Finite-window stochastic bulk-flow -> homogeneous-tilt rank bridge

- lane: theory; cards: PR-222
- literature: Kaiser 1988; minimum-variance bulk-flow estimator (Watkins-Feldman-Hudson)
- axes: significance=marginal, novelty=K, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: The verified content — a single window/scalar bulk-flow amplitude gives Fisher rank 1 and cannot point-identify a 3-component vector, while >=3 independent windows give rank 3 — is the textbook Fisher-information/identifiability structure of the minimum-variance bulk-flow formalism. Kaiser (1988, MNRAS 231, 149) established the Gaussian ML bulk-flow estimator; Watkins-Feldman-Hudson (2009, MNRAS 392, 743) built the minimum-variance estimator F = W^T C^-1 W with ideal window functions (exactly the card's Fisher form); Feldman-Watkins-Hudson (2010, MNRAS 407, 2328) extended it to the bulk-flow/shear/octupole moment expansion = the multi-window -> multi-moment rank structure this card restates. The GLS map A = F^-1 W^T C^-1 is Aitken's textbook BLUE. The card's W is a synthetic 4x3 toy, not derived from CF4 window functions or a Bianchi-tilt transfer, so no delta over the cited MV formalism is demonstrated -> K, not P/S.
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication | note: lit-CRAG unlock string was refuted (advisory); status re-derived from axes

### T-EGS — One-way FLRW/EGS + converse counterexample registry

- lane: theory; cards: PR-126
- literature: Clarkson & Barrett 1999 gr-qc/9906097; Nilsson-Uggla-Wainwright-Lim 1999 ApJL 522,L1 astro-ph/9904252
- axes: significance=incremental, novelty=C, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: Cross-check of two specific named studies, no demonstrated delta. Clarkson & Barrett 1999 (gr-qc/9906097, CQG 16, 3781-3794) proved the one-way EGS structure directly: irrotational perfect-fluid spacetimes with isotropic radiation for every fundamental observer are FLRW iff acceleration vanishes, so isotropy does NOT imply FLRW. Nilsson, Uggla, Wainwright & Lim 1999 (astro-ph/9904252, ApJL 522, L1) gave the almost-case converse counterexample (almost-isotropic CMB with non-negligible Weyl curvature). PR-126's FORWARD (FLRW comparator state => x_C = sigma2 - w2 + omega_tilt + delta_omega_k = 0) is a definitional tautology, and its CONVERSE counterexamples (x_C=0 via signed cancellation, CE-1/CE-2 + 64 draws) re-encode the published EGS-converse failure in the programme's x_C comparator. The algebraic cancellation is weaker than NUWL's exact anisotropic-Weyl solutions; no delta over the cited work. Tier C (cross-check), K-adjacent since the EGS-converse failure is textbook-level in Wainwright & Ellis 1997.
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication | provenance override: cited_correct: registry author string corrected Hsu->Lim (Nilsson, Uggla, Wainwright & Lim 1999, ApJL 522,L1); references.bib was already correct

### T-FRAME — Congruence-indexed frame algebra + signed carrier + Frobenius gate

- lane: theory; cards: PR-125, PR-187, PR-212
- literature: van Elst & Uggla 1997 (1+3 covariant frame formalism)
- axes: significance=incremental, novelty=K, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: The frame-tagged component algebra with boost-only cross-frame bridges is a software encoding of the 1+3 orthonormal-frame discipline of van Elst & Uggla 1997 (CQG 14, 2673; arXiv gr-qc/9603026) and the two-frame tilt structure of King & Ellis 1973 (CMP 31, 209), as expounded in Ellis & van Elst 1999 (gr-qc/9812046). The order type system (Omega_tilt = (1+w)Omega_m sinh^2 beta = O(beta^2); quadrupole O(beta^2); Omega_tilt^2 O(beta^4); 4!=2 refusal) is elementary tilted-cosmology order counting (cf. Ma et al. 2011, PRD 83, 103002). The signed S+^3 x R carrier repackages a known PSD moment-cone plus a signed R factor for DeltaOmega_k. The card itself asserts no physical/geometric/observational claim and regenerates no comparator number, so no physical delta over the cited literature is demonstrated — the contribution is a CAS-sealed type-system correctness guard, hence K (textbook physics encoded as types).
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication

### T-JOINT — Joint feasible-set support theorem (product box a corollary)

- lane: theory; cards: PR-189, PR-215
- literature: Imbens & Manski 2004 Econometrica 72,1845 (identified sets)
- axes: significance=marginal, novelty=K, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: The literature anchor Imbens & Manski 2004 (Econometrica 72(6):1845-1857) is about CONFIDENCE INTERVALS for partially identified scalar parameters (covering the true parameter vs. the identified region), not the joint-vs-product geometry this card proves, so there is no delta over IM on this theorem. The actual result -- identified set of a linear functional c^T g over a compact/polyhedral F equals the support-function interval [inf cTg, sup cTg], with the product box a corollary that holds only when F factorizes and is otherwise strictly wider -- is textbook convex analysis (support function of a polytope; Rockafellar) and standard partial-identification folklore (projection/sharp bounds vs. marginal/product bounds; Manski 2003; Beresteanu-Molinari 2008 support-function characterization). The programme's own CRAG (advocate_rescue_divergence_20260714/06_final_crag.json) concedes the IM-based partial-ID layer carries no novelty. Coupled fixture sup(x+y|x+y<=1)=1 < product sup 2 is a trivial LP instance. Tier K: known/textbook, cite IM 2004 + Beresteanu-Molinari 2008; no demonstrated delta.
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication | note: lit-CRAG unlock string was refuted (advisory); status re-derived from axes

### T-KE — King-Ellis rotating-congruence ten-item program

- lane: theory; cards: PR-181
- literature: King & Ellis 1973 CMP 31,209 (tilted cosmologies)
- axes: significance=incremental, novelty=P, completeness=complete, verification=unverified, provenance=cited_correct
- novelty rationale: Base literature: King & Ellis 1973 (Commun. Math. Phys. 31, 209) already relates rotation/shear/expansion to the Bianchi group for tilted perfect fluids and treats homogeneous vorticity; Ellis-MacCallum 1969 supplies the class; Coley & Hervik 2005 (CQG 22, 579) already exhibit ROTATING tilted Bianchi V perfect-fluid developments. Hence items 1-9 (frame kinematics, the contracted Gauss identity R3 = 2G_uu - (2/3)Theta^2 + sigma^2 + omega^2, Jacobi/structure-constant algebra, Raychaudhuri) are K-level textbook re-derivation, and the KE-OBS vorticity closed form is a P-level refinement of the known fact that oblique tilt is not irrotational. The only candidate delta is the DYNAMICAL DOUBLE OBSTRUCTION at flat anisotropic curvature (DeltaOmega_k=0): single stream excluded by G_ti identically 0 for every homogeneous type-I metric in the class, and the antipodal pair excluded dynamically by Killing+Euler conservation of the tilt-covector direction (omega^2=0 along the development). No published verbatim equivalent was found, but this rests on absence-of-evidence, is a narrow negative/obstruction result on the group-invariant perfect-fluid class, and upholds the programme's own slice-normal W^2 withdrawal rather than adding an independently consequential theorem. Under hostile scrutiny this downgrades the internal S rating to P: a potential delta over King & Ellis 1973 / Coley-Hervik 2005, not a demonstrated significant one.
- **unlock: GENUINELY_INCOMPLETE** — not yet complete+verified author-side: verification=unverified

### T-MES — MES source-exact shear/vorticity ceilings + attribution surface

- lane: theory; cards: PR-217
- literature: Maartens, Ellis & Stoeger 1995 PRD 51,1525; SAG 1997 astro-ph/9904346
- axes: significance=incremental, novelty=C, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: Cross-check of two specific named studies, not a new result. The card's live "geodesic SAG" ceiling coefficients — sigma=(5/3,3,3/7) and omega=(10/3,2/15,0) — are bit-exact reproductions of Stoeger, Araujo & Gebbie 1997 (ApJ 476,435; astro-ph/9904346) eqs (3) and (4), themselves reductions of Maartens, Ellis & Stoeger 1995a (PRD 51,1525). Verified against the SHA-pinned archived source. The non-geodesic omega=(3/4,2,2/7) is correctly quarantined as no_accessible_source (traces to print-only MESb, PRD 51,5942). The only material not in the cited literature — the epsilon1_crit=(43/25)eps2+(9/35)eps3 hierarchy-preservation crossover and the frozen-anchor attribution-surface framing — is an in-house algebraic bookkeeping layer over the published bounds, with no external physical delta. Hence C, not P.
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication

### T-MULTIFLUID — Multi-fluid moment cone: zero flux does not imply zero stress

- lane: theory; cards: PR-223
- literature: relativistic kinetic theory (Israel-Stewart moment hierarchy)
- axes: significance=marginal, novelty=K, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: Textbook, zero delta. The load-bearing fact "zero net flux does not imply zero anisotropic stress" is the elementary statement that the energy flux q_a (first moment) and anisotropic stress pi_ab (traceless second moment) are independent irreducible components of the moment/stress-energy decomposition. This is explicit in the Israel-Stewart moment hierarchy (Israel & Stewart 1979, Ann. Phys. 118, 341-372) and in the 1+3 covariant decomposition that is BASS's home framework: T_ab = mu u_a u_b + 2 q_(a u_b) + p h_ab + pi_ab (EllisMaartens2012 'Relativistic Cosmology'; EllisVanElst1999). The two-antipodal-stream witness (streams +/-e_x giving F=0, K=diag(2,0,0), 3Pi=diag(4,-2,-2)) is the standard free-streaming/counter-streaming anisotropic-stress example (Ma & Bertschinger 1995 neutrino anisotropic stress; general free-streaming kinetic theory produces anisotropic stress at zero net momentum flux). No claimed result exceeds these; it re-derives an identity that holds by construction. Delta over cited work: none.
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication

### T-OMK — Omega_k higher-order slaving Sigma = kappa K + c2 K^2

- lane: theory; cards: PR-131, PR-132, PR-192
- literature: Wainwright & Ellis 1997 dynamical systems in cosmology (LRS Bianchi)
- axes: significance=incremental, novelty=P, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: Framework is textbook Wainwright & Ellis 1997 (WainwrightEllis1997): the Hubble/expansion-normalized LRS Bianchi III / Kantowski-Sachs reduced system, the constraint 1=Omega+Sigma^2+K, the deceleration parameter, and the flat-FLRW saddle/isotropization structure are all established there (K). Center-manifold/invariant-manifold analyses of these EXACT systems already appear in Leon-Coley et al. 'Averaging Generalized Scalar Field Cosmologies I: LRS Bianchi III and open FLRW' (arXiv:2102.05465) and 'Evolution of Bianchi I/III/KS: Isotropization and Inflation' (gr-qc/9802043), which establish isotropization/local stability qualitatively (C). The leading slaving coefficient kappa=-2/(5+3w) is the standard unstable-manifold tangent (I re-derived it: lambda_K=1+3w>0, lambda_Sigma=-3(1-w)/2<0, kappa(5+3w)/2=-1). The genuine delta is the explicit closed-form SECOND-ORDER coefficient c2=-2(9w^2+18w+13)/((3w+5)^2(9w+7)) plus a machine-checked uniform interval-arithmetic cubic-remainder certificate |Sigma-(kappa K+c2 K^2)|<=|K|^3 on a compact (K,w) box, which I did not find published verbatim. This is a quantitative refinement of published qualitative reductions, hence P not S: incremental and a mechanical Taylor/interval extension of established WE1997 + center-manifold methods on an already-analyzed system.
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication

### T-PARITY — Solver-free parity/handedness identities + reference registry

- lane: theory; cards: PR-182
- literature: Pontzen & Challinor 2007 MNRAS 380,1387 (Bianchi polarization)
- axes: significance=marginal, novelty=C, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: Anchor: Pontzen & Challinor 2007, MNRAS 380, 1387 (arXiv:0706.2075). That paper already establishes that Bianchi (VIIh) models break parity and hence produce TB/EB parity-odd cross-correlations, with B-mode power comparable to E-mode, and that axisymmetric configurations give E-only (B=0); VIIh handedness kappa=+/-1 is standard in the McEwen/Jaffe VIIh literature. The card's identities are textbook: I1 (m=0 -> B=0) and I2 (TB/EB parity-odd, TT/EE/BB/TE parity-even) are standard CMB E/B parity; I4 (mu-only Doppler kernel to O(beta^3)) is standard aberration; I3 is a specific VII_h structure-tensor algebra check. Attribution is explicitly CONFIRMATORY, so NO delta over Pontzen-Challinor is demonstrated. The only novel move -- refuting sign(EB/TB)=sign(x_h) via I2/I3 (ratio EB/TB is parity-EVEN => handedness-blind; conventional x_h orientation-even) -- refutes a relation internal to the programme's own roadmap (#pr-182), not any published claim, so it is a self-consistency correction rather than a delta over prior research. Hence C (cross-check of the named study), not P/S.
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication

### T-RANK2 — Comparator rank-2 non-identification (W2/DeltaOmega_k joint null)

- lane: theory; cards: PR-127, PR-219
- literature: PSTF/covariant moment problem; Ellis-MacCallum structure constants
- axes: significance=marginal, novelty=K, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: Anchor EllisMacCallum1969 ("A class of homogeneous cosmological models," Commun. Math. Phys. 12, 108, 1969) supplies the structure-constant classification (class A a_b=0 / class B a_b!=0) that is the true discriminator among BI/BV/BVIIh. The T-RANK2 result is a rank read-off of a self-declared 3x4 map whose W2 and DeltaOmega_k columns are identically zero, so those axes lying in the kernel is a tautology of the map's own definition, not a delta over the literature. The physical reading (a scalar shear/tilt-magnitude comparator cannot identify vorticity or anisotropic curvature) is long established via Collins-Hawking bounds and the Bianchi VII_h CMB-template degeneracy literature (Pontzen-Challinor 2007, MNRAS 380,1387; McEwen astro-ph/0605325). PR-219's quotient atlas at most CROSS-CHECKS (tier C) that adding vorticity + transverse-curvature observables re-separates the classes exactly as Ellis-MacCallum structure constants would predict. No S/P delta demonstrated; the headline rank-2 kernel theorem is textbook linear-identifiability -> K.
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication

### T-SHARP — Physical sharpness ladder algebraic->constraint->local->global

- lane: theory; cards: PR-216
- literature: Einstein-constraint initial data (Choquet-Bruhat); endpoint attainability
- axes: significance=marginal, novelty=K, completeness=partial, verification=verified, provenance=cited_correct
- novelty rationale: The staged ladder (algebraic constraint -> constraint-satisfying initial data -> local existence -> global/maximal development) re-encodes the textbook Einstein Cauchy-problem hierarchy of Choquet-Bruhat 1952 (Acta Math. 88, 141-225, local existence+uniqueness) and Choquet-Bruhat & Geroch 1969 (CMP 14, unique maximal globally hyperbolic development); the "homogeneous momentum constraint = 0" fact is textbook Ellis-MacCallum 1969 orthonormal-frame cosmology, and the endpoint-attainability content is the internal T3-full/PR-131 result. No delta over any of these is demonstrated -- PR-216 is a governance/staging guardrail expressing the standard constraints->evolution structure in the programme's metrology language, not a new theorem.
- **unlock: BLOCKED_ON_NATIVE_SOLVER** — requires an authenticated native Bianchi Boltzmann solver delivery (Track II) | note: lit-CRAG unlock string was refuted (advisory); status re-derived from axes

### T-W2 — Constraint-natural vorticity convention W2 = omega_ab omega^ab/(6H^2)

- lane: theory; cards: PR-186, PR-211
- literature: Ellis 1971 relativistic cosmology (covariant kinematics), textbook
- axes: significance=incremental, novelty=K, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: The core identity omega_ab omega^ab = 2 omega_a omega^a (dual vector omega_a = (1/2) eps_abc omega^bc) and the expansion-normalization of vorticity by Theta = 3H are standard 1+3 covariant kinematics: Ellis 1971 'Relativistic Cosmology' (republished Gen. Relativ. Gravit. 41, 581, 2009), Ellis & van Elst 1999 (gr-qc/9812046), Wainwright & Ellis 1997, and the Ellis-Maartens-MacCallum 2012 textbook. The vorticity-magnitude convention omega^2 = (1/2) omega_ab omega^ab = omega_a omega^a is textbook. PR-186/211 content is (a) a display-bug repair (v10 report showed omega_a omega^a/H^2, exactly 3x the registered omega_a omega^a/(3H^2)) and (b) a normalization choice W^2 = omega_ab omega^ab/(6H^2); the derived ceiling W^2 <= 3B^2/2 follows elementarily from sqrt(omega_ab omega^ab)/Theta <= B. No delta over the cited literature -- the mathematics is textbook and doubly/five-axis verified, not new. Tier K (known/textbook).
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication

### T-XC — Master FLRW-departure identity x_C = Sigma2 - W2 + Omega_tilt + DeltaOmega_k

- lane: theory; cards: PR-126, PR-210, PR-215
- literature: Ellis & van Elst 1999 (cosmological models, covariant 1+3); Maartens 1998
- axes: significance=incremental, novelty=C, completeness=complete, verification=verified, provenance=cited_correct
- novelty rationale: The master identity x_C = Sigma2 - W2 + Omega_tilt + DeltaOmega_k is the standard 1+3 covariant generalized Friedmann/Gauss-Codazzi constraint (1 = Om + OL + Ok + Omega_tilt + Sigma2 - W2) rearranged so the FLRW comparator sits at x_C=0; this is textbook (Ellis & van Elst 1999, gr-qc/9812046; tilt term = King-Ellis 1973). The forward one-way direction is the Ehlers-Geren-Sachs 1968 theorem; the converse (x_C=0 / near-isotropy does NOT imply FLRW) is already published in Nilsson, Uggla, Wainwright & Lim 1999 (ApJL 522 L1, astro-ph/9904252) and Clarkson & Barrett 1999 (gr-qc/9906097). PR-126's counterexample registry (CE-1/CE-2 + 64 seeded cancellations) re-derives this at the comparator-scalar level with a content-addressed premise-DAG governance scaffold. Delta over the cited work: NONE in physics content -- it is a faithful cross-check/re-derivation of named studies plus internal bookkeeping. Hence C (cross-check of specific named studies), not P/S; the load-bearing identity is itself K/textbook.
- **unlock: PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION** — complete + verified + cited-correct author-side; the only remaining gate is one non-author Independence adjudication

