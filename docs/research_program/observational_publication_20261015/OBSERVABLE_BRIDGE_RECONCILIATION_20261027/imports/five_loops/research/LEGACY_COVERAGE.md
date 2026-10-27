# Legacy and current-source coverage — 2026-10-26

Owner: internal source-reuse investigation. Scope: read-only scientific source mapping for the five theory loops; no repository mutation, solver/ODE, numerical producer, CAS replay, or Git push. This report is non-claim-bearing. Repository: cosmosapjw-quantum/htt_base. Current science pin: a55036ad09c53a9215dee3282e425d37cfb95443 (research/htt-adaptive-methods-20261023). Historical synthesis pin: 0d5ab96bdb55398076629099664c77517ec33bb4; historical mathematical branch pin: 2f10fbd64cfd0810a976bf2720186fd56b7bfde7.

## What was actually covered

| Coverage unit | Count | What the count establishes |
|---|---:|---|
| All currently accessible PR metadata | 559 | Paginated GitHub GET /pulls?state=all&per_page=100, pages 1–6: 100,100,100,100,100,59. Number range 2–562; issue numbers need not be consecutive. Bodies, title, state, refs/SHA, merge/close dates retained. |
| PR states | 131 open; 77 merged; 351 closed unmerged | Current endpoint metadata, not scientific validity or proof review. |
| All live branch metadata | 297 | GET /branches pages 1–4: 100,100,97,0. Names, heads, protected flag. Deleted/unreachable branches remain outside this enumeration. |
| Selected current repo files acquired | 114 | Exact source copies in sources/repo; SOURCE_PINS.json records head/hash. 88 copies match available Git blob identities, zero mismatches; 26 are commit-pinned raw files with local hashes. Acquisition is not proof reading. |
| Bounded scientific/code reading units below | 21 | Full short records or substantive equation/code sections, explicitly distinguished below. This is not 21 fresh theorem verifications. |
| Current R32 product directories listed | 9 | All listed; root results/status fields inspected, and selected science/report/manuscript files acquired. Final repaired paths distinguished from original candidates. |
| Inherited theorem-family synthesis | 26 | Reused prior source synthesis and representative statements, not a fresh independent reading of every original proof. |
| Legacy registry entries | 65 | Historical registry: 33 ACTIVE,26 ACTIVE_CONDITIONAL,4 SUPERSEDED,2 RETRACTED. Labels are retained registry assertions. |
| Successor registry entries | 65 | 12 CHECKED signatures,53 MIGRATION_PENDING. No status changed. |
| Historical static evidence groups | 345 | Catalog content/version/assumption groups, not 345 independent theorems. |
| Legacy attachment archives centrally listed | 8 / 9,104 entries | Directory metadata only first; toolchain/xAct archives and vendor payloads were not extracted. |
| Selected legacy87 source texts extracted | 10 | Report/derivation/contract/audit texts, not solver execution. |

The previous theorem inventory counted 558 PRs,76 merged and the same297 branches. Current enumeration adds PR562 (R32 publication route), merged into the adaptive branch; it does not imply a new empirical result. The comparison endpoint in LATEST_DELTA.json returns only300 changed filenames across19 commits. That API cap prevents using its missing paths as evidence of unchanged science.

The full prior inventory is now available at:
sources/repo/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/evidence/research/theorem_inventory.json
(blob17d927f1124a33fe10f3a0e18114bd605dbdf027;2,275,594 bytes).
Raw/contents range retrieval failed or returned empty because of size; fetch_blob succeeded. Its own limits explicitly say all PR/branch metadata were enumerated while every PR/branch source was not read. The current task preserves that limitation.

The21 bounded reading units are: baseline research/theory_expansion.md (full); R32-01 science/RESEARCH_NOTE.md (full); R32-01 science/MANUSCRIPT.md (chirality section plus carrier excerpts); R32-01 report/README.md (full); R32-05 repair_01/science/MANUSCRIPT.md (finite response/inverse sections); R32-07 science/manuscript.md (instantaneous constraint/image sections); current filling_fraction.py (full); tensor_functionals.py (full); depth_path.py (full); typefree_functionals.py (support function/docstring sections); typefree_depth.py (transport/covariance sections); inherited theorem_physical_chapter.md (bounded sections); legacy_reconstruction_chapter.md (full); R34 README.md and AUDIT_GUIDE.md (full); R35 CF4 README.md (full); R35 WMAP independent_review/REVIEW.md (full); final R32-09 repair closeout REVIEW.md (full); R35 CF4 FORMAL_BINDING_RESULT.json (full); PUBLICATION_RESULTS_INDEX.md (full); R32-04 repair_05/report/main.tex (model/geometry/boundary-policy sections). Applicable repository skill files and test-name/function excerpts were additional context reads. The other acquired files remain available for the loop owners' direct reading. No claim is made that all114 source files or all559 PR proofs were read.

## Newly available science after the prior R32 proposal

The current PUBLICATION_RESULTS_INDEX.md records seven manuscripts and two scientific frontiers, all with scoped formal completion. That is a stronger deliverable state than the old d37eab61a62feab4210e65d1c9d12e8c49f34870 proposal. It is not original42 scientific admission. Actual scientific equations and their domain restrictions are the useful delta.

All paths in this table are under docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/.

| Product | Current useful scientific content | Correct source / residual condition |
|---|---|---|
| R32-01-QO-METHODS | Attained STF3 contraction ellipsoid and fibres; sharp Q/O chirality constant; nonlinear local optical octupole; finite chirality margin and remainder; ideal inverse | science/MANUSCRIPT.md; report/main.tex; science/RESEARCH_NOTE.md. Deterministic/conditional, not stochastic parity violation or finite-redshift sky result. |
| R32-02-P1-SELECTED | Selected-cohort tensor likelihood, conditional normalization, coupled functionals | sections/02_identification.tex through07_proofs.tex; root README/RESULT. Parent inclusion law and actual physical response still absent. |
| R32-03-H03-STRUCTURED | Full-covariance finite-window structured sensitivity design | Qualified repair_01/RESULT.json and README; original first HOLD retained. Physical calibration Jacobian unavailable. |
| R32-04-BANDPASS-BOUNDS | Exact compatible signed24 target ball, least moment cost, one-foreground/pairwise radii | Qualified repair_05/RESULT.json and report/main.tex; boundary/center/range repairs matter. Free signed nine-moment class with stipulated metric, not physical moment calibration. |
| R32-05-P6-OPTICAL | Finite optical inverse/support with residual compatibility and error-radius shear frontier | Qualified repair_01/science/MANUSCRIPT.md and repair_01/report/main.tex. Common-event/congruence/frame/error inputs remain conditional. |
| R32-06-P4-DESIGN | Two-radius response design separates observer, bulk and two-mode history in stipulated finite model | science/MANUSCRIPT.md, report/main.tex. Baseline/either-addition/both-additions ranks12/15/18; equal-radius controls8/11/14. No actual external history kernel. |
| R32-07-P5-ALGEBRA | Complete instantaneous LRS BianchiV constraint image; exact kinematic BianchiI radiation-history degeneracy | report/manuscript.tex preferred over corrupt science Markdown. Instantaneous compatibility is not a dynamical Einstein-matter history solution. |
| R32-08-H03-PAPER | Manuscript consuming source-bound full covariance structured frontier | main.tex, PUBLICATION_STATUS.json. Apparent CF4 statistic remains distinct from physical tensor. |
| R32-09-BANDPASS-PAPER | Source-defined spectral geometry with dust/LFI/HFI normalization made explicit | Qualified repair_01/report/main.tex; independent_review/r35_bandpass_paper_definition_fresh_closeout/REVIEW.md.33 numerical assets unchanged by definition repair. |

Root RESULT.json files often retain PENDING fields from candidate creation. Later PUBLICATION_STATUS.json, exact review closeout and the current index close only their stated scoped component. Do not flatten this chronology into a universal PASS or treat every old PENDING as the latest state.

R34 is a cutoff audit export with original failed CF4 and WMAP producer attempts; it did not claim a result for failed attempts. R35 then adds actual accepted finite components:

* CF4 saved-bound closeout qualifies PRODUCT.npz:band_joint,total_joint,tensor_covariance for candidate88b177047bd50170592f63f6454a957cd93c6540bcbf514d9a9a399c33d0359c. Five STF coordinates,15 joint coordinates and full15×15 covariance remain. Global rigorous Type3 enclosure remains NOT_ESTABLISHED; H02/H04 and physical x,F,Pi,Q,G_F remain HOLD/undefined.
* WMAP+Planck F2 independent review reports nuisance rank9/augmented rank10 in all24 finite systems (12 conventions×12/17 rows), minimum principal-angle sine3.628399453e-5, maximum condition1.067851692e6, maximum Euclidean weight norm7955.991019. This establishes conditional quotient escape in the specified spectral response, not real-noise utility. Exported-weight residual probes separately close the original checker coverage gap.
* The final post-nine checkpoint reports no_action then HOLD_UNRESOLVED_BRANCHES,ready=[], no outstanding adaptive packet. It records29 residual input requirements; original42 acceptance is unchanged.

## Equations worth retaining, with their limits

**Sharp Q/O geometry.** For nonzero STF2 Q, C_Q O=O:Q, C_Q*=L_Q and M_Q=C_QC_Q*=(Q:Q)I/3+2Q²/5. With ||O||=o the attained contraction image is vᵀM_Q^-1v≤o². Interior fixed-norm fibres are S³, boundary fibres singleton; unconstrained fibres are affine4-spaces. If Q=0, the rank/normalization sectors change. For χ=det[v,Qv,Q²v],
|χ|≤(4√2/135)||Q||⁶||O||³.
Nontrivial global equality requires trQ³=0, spectrum(-√(t/2),0,+√(t/2)), and minimum-norm boundary lifts with v_i=±o√(m_i/3). Covariant determinant/discriminant prior art is acknowledged; no priority claim follows.

**Local magnitude response.** With one smooth congruence, signature(-+++), H>0,
H_u(n)=H-A·n/c+σ:nn,
d=-A/(cH),S=σ/H,q=d·n+S:nn,
f_mu=-κlog(1+q),κ=5/ln10.
The complete ideal angular inverse is r=exp(-f/κ)/<exp(-f/κ)>, d=3<rn>, S=(15/2)<r(nn-I/3)>; an intercept cancels. This is neither a noisy/truncated harmonic estimator nor a finite-redshift inversion. For sup|q|≤ε<1,
O_mu=κL_Sd+R3, ||R3||≤√(35/2)κ ε³/[3(1-ε)].
K_S=(S:S)I/3+2S²/5 and d_hat=κ^-1K_S^-1(O:S) for S≠0; the four-dimensional residual complement is retained. Pure-dipole S=0 is a distinct cubic sector. These formulas are already retained, not new loop findings.

**Finite inverse compatibility.** For z=Aθ+e,e∈E,
E_z={e∈E:(I-AA⁺)(z-e)=0},
Θ={A⁺(z-e)+k:e∈E_z,k∈kerA}.
Feasibility requires E_z≠∅. Identifiable J obeys kerA⊂kerJ. Then
h_JΘ(a)=aᵀJA⁺z+h_Ez(-A⁺ᵀJᵀa).
Empty-set support is-∞; nonempty unresolved kernel support is+∞. Applying A⁺ to arbitrary errors while ignoring residual compatibility can invent a nonempty inverse for inconsistent data; the repaired P6 source fixes that.

**Bounded spectral moments.** For Y=a sᵀ+FU, tr(UᵀMU)≤ρ², K=FM^-1Fᵀ, c_M=M^-1FᵀK^-1a, ℓ_M²=aᵀK^-1a, the least compensator for target displacement v is-c_Mvᵀ. The exact compatible target set is
Sρ(Y)={s∈R24:J0+ℓ_M²||s-s0||²≤ρ²}.
One foreground hides norm≤ρ/ℓ_M; two separately bounded foregrounds permit separation≤2ρ/ℓ_M. Current common-metric ℓ_M=3.117720–3.118388; raw-coordinate identity metric59.572829–59.592192. These are metric-conditional finite response numbers, not physical foreground radii. Numerical boundary/range HOLDs preserve representation limits; abstract real-ball certification is separate from arbitrary later rounded sampling.

**LRS BianchiV instantaneous image.** In the declared single-perfect-fluid branch K>0,0≤w≤1,|β|<1,
1=K+z_s²+Ω_n+Ω_Λ,
2√K z_s=(1+w)Ωβ/(1-β²),
Ω_n=Ω(1+wβ²)/(1-β²).
Set A=(1+w)²β²/[4K(1-β²)²], B=(1+wβ²)/(1-β²), D=1-K. For0<K≤1,
Ω_max=2D/[B+√(B²+4AD)],0≤Ω≤Ω_max.
K>1 is empty in this sector. β at Ω=0 is not a defined material velocity. This is complete instantaneous algebra; time development and radiation constraints require additional equations/data.

**Affine local flow already retained.** v(x)=b+Ax, A=θI/3+S+Ω gives
v_r=n·b+r(θ/3+nᵀSn);
radial data lose antisymmetric rotation. In the declared low-z weighted through-origin slope,
Hhat-H=b·Σw r n/Σw r²+θ/3+Σw r² nᵀSn/Σw r².
A bulk speed divided by depth is not divergence. This recipe, the integrated-shear endpoint counterexample and corrected mixed brightness coefficient8/5 are already in legacy_reconstruction_chapter.md.

## F is presently several different mathematical objects

Do not announce the36-page report's §23 tensor-support definition wrong because a skill uses older prose. Actual implementation and dates distinguish namespaces.

| Source/namespace | Actual object | Evidence |
|---|---|---|
|36-page report §23 | F+(u)=h_I(u)/h_B(u); antipodal profile max(h_I(u),h_I(-u))/h_B(u), positive denominator required | text/20-report-1-.txt PDFpp24–25 / printedpp21–22. Explicitly not material volume occupancy; finite directions not full sphere. |
| Current typefree_functionals.py | support_utilization(record,u)=(u·difference)/h_B(u), signed and premise-relative; unavailable/zero-support statuses | Last commitbc45fb9292a4cfb095d7b61d4e5c02a32fb39c5c,2026-09-30. Module explicitly does not replace legacy scalar definitions. Tests include value-1 and zero-support status. |
| Legacy mio/formalism/filling_fraction.py | Samplewise F=x_C/U,0≤F≤1 in sign-clean certified-ceiling sector; companion unsigned M | Last commitfb6ad922f27f9fde65e7882c8a5dfc0937c9e8be,2026-06-18. Code explicitly forbids physical/material occupancy and volume fraction interpretations. |
| R32-01 manuscript carrier paragraph | Arbitrary declared measure occupancy F_nu(B)=nu(B∩D)/nu(D) | Different mathematical construction; undefined without domain/measure. It is not numerically interchangeable with either support ratio or ceiling utilization. |
| Repository skill htt-xqpi-fg-formalism | Occupancy/support/ceiling prose inherited across revisions | Guidance cannot settle these distinctions against actual code or source domains; preserve explicit names. |

depth_path.py (lastc532862651235ed0586a0677b61a43b2e09b3c85,2026-09-13) constructs contrasts y_(j+1)-K_jy_j and anchored invertible representation; typefree_depth.py retains signed shared-latent contrasts and full covariance. Missing cross-blocks return unavailable; a fitted transport requires joint-law treatment. This is not simply a scalar difference of arbitrary F values. The report's old referenced tensor_departure_statistics.py and conditional_exceedance.py are404 at the current head; the current typefree modules are available. No universal namespace migration is inferred from those missing paths.

## Retained errors, corrections and archive lessons

The fetched65-entry registry preserves concrete superseded/retracted claims:

* P36 and T2p strict depth-ratio iff claims are RETRACTED. S=[0,1],N(s)=s,D(s)=1+s has positive coefficient product yet joint lower endpoint equals the product-relaxation lower endpoint; N_min=0 neutralizes denominator conflict. T2G replaces the universal statement; stronger sign criteria require additional positive-numerator/nondegeneracy assumptions.
* P26 one-sided curvature box is superseded by signed ΔΩ_k treatment; additive endpoint decomposition requires product factorization.
* P31 algebraic-box sharpness does not imply physical constraint-surface or dynamical attainability. A BianchiI slice normal has ω=0; antipodal matter streams cancel flux but do not create normal-frame vorticity.
* P35 known-covariance chi-square coverage is superseded by the estimated-covariance Hotelling/F branch; a deterministic-width special-model endpoint theorem has narrower scope.
* U4 v8 statistics are superseded by fuller disclosed v9 provenance; this is not a finding that the old numbers were incorrect.

Source-text defect newly observed here: R32-07 science/manuscript.md contains8 literal U+000B and21 U+0008 controls, consistent with escaped \varepsilon/\beta text. Its report/manuscript.tex has no such controls. The source copy is preserved unchanged; use the TeX for exact equations. This is text corruption, not a demonstrated mathematical counterexample.

The legacy87 archive's own audit preserves actual prior defects: screen spatial-only transport broke parallel transport/reciprocity; rotation generator vs commutator sign references disagreed; classB Ampère relative sign was wrong; mocked/hard-coded stability calculations and span-only gates missed coefficient errors. Its corrected derivation reports these as historical fixes, not independently rerun results in this task.

Legacy87 Q-CONTRACT §§9–9.1 states the coherency carrier J, Π=I-nn, and
(KJ)_ab(n')=(3/8π)∫Π_ac(n')J_cd(n)Π_db(n')dΩ;
the integrated map has symmetric eigenvalues1,7/10 and antisymmetric1/2. It restricts ψ=0 to the canonical transported screen map: a fixed external tetrad/global polarization basis can retain Wigner phase. It explicitly retracts the description “E/B is only linear theory”: global spin2 E/B exists nonperturbatively; its local screen gauge failed stable convergence. These are useful convention/error examples, not permission to revive Teff as the active native solver.

No Rust toolchain, Cargo vendor payload, xAct bundle, scientific solver binary or ODE was run. No external message or push occurred. The useful next work is the five independent physical derivations against these retained results, with new claims limited to differences actually established by those derivations.

