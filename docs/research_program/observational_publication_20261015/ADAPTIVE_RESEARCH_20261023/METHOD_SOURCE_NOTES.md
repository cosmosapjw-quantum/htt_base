# Primary-source method intake

Owner: HTT research planning. Scope: exploratory source/method synthesis for the
adaptive solver-free campaign; no original scientific admission. Source base:
10f3ea585c6608e794900efe7e4f8f42c0747a3b. Access date: 2026-10-23.
Native read-only advisers `/root/r25_statistics_theory` and
`/root/r25_cmb_physics_theory` requested/selected Astra xhigh; observed UNKNOWN.
Their proofs and numeric contracts are planning inputs, not independent result
review or historical four-axis validation. Primary sources were browsed; these
notes paraphrase methods and distinguish our proposed extensions.

| Scope | Primary source | Usable method and applicability limit |
|---|---|---|
| Covariance uncertainty, P1/P3/P6 | [Cocci and Plagborg-Moller](https://arxiv.org/pdf/2109.08109), section3, appendixA.3 | Worst-case dependence with supplied marginal uncertainty; published general nonlinear results are asymptotic. Our finite trace/Markov bound is separately derived and needs a justified actual covariance upper bound. |
| Joint bias and variance, P6 | [More and Sorensen](https://epubs.siam.org/doi/10.1137/0904038), [original report](https://cds.cern.ch/record/136890/files/CM-P00069193.pdf) | Convex trust-region least squares yields exact bias witnesses and robustness thresholds. An unmeasured coefficient bias radius is a scenario, not an observed Gaia bound. |
| Correlated model comparison, P3 | [Universal Inference](https://arxiv.org/html/1912.11436v4), sections2,5–6, especially De-randomization and Conditional likelihood for non-i.i.d. data | The source already treats averaging dependent split statistics and conditional likelihood for non-iid observations. Our correlated-catalogue application specializes these existing methods under explicitly qualified conditional densities/null suprema; it is not a novel dependent-data extension. Fixed averages remain valid; arbitrary dependent products need separate justification. |
| Selection and transport, P1/P3 | [Deville and Sarndal](https://www.tandfonline.com/doi/abs/10.1080/01621459.1992.10475217) | Auxiliary-total calibration offers a source-overlap feasibility experiment. Balancing does not establish missing-at-random or recover missing outcomes/parent inclusion probabilities. |
| Unknown anchors, P1 | [von Luxburg and Franz](https://arxiv.org/pdf/0711.0198) | Fieller/geometric inversion retains unbounded/disconnected ratio sets. Requires an actual joint numerator/anchor law; the computational radius10 is not a physical MES anchor. |
| Missing dependence, P1/P3/P6 | [Makarov](https://www.mathnet.ru/php/archive.phtml?jrnid=tvp&option_lang=eng&paperid=3510&wshow=paper) | Fixed-marginal extremal laws permit partial identification. Pointwise sharp bounds need not share one attaining coupling; no fabricated common physical marginal law. |
| SN calibration, P3/P4 | [Brout et al.](https://arxiv.org/abs/2112.03864) | Shared cross-calibration and its covariance are relevant; do not add another PV/calibration term to the consumed released total covariance. Private nominal producer parity is a separate target. |
| Astrometric systematics, P6 | [Lindegren et al.](https://arxiv.org/abs/2012.03380) | Source of Gaia calibration/spatial covariance context. Full HTML access failed403 and PDF extraction exceeded tool size here; no numerical covariance ceiling was imported. |
| Harmonic Gaussianity and isotropy, P2 | [Baldi and Marinucci](https://arxiv.org/pdf/math/0606709), propositions1,5; [Dennis and Land](https://arxiv.org/pdf/0704.3657), section3 | SO3 orbit/shape conditioning differs from uniform coefficient-sphere/Gram conditioning. Isotropy alone does not imply Gaussian coefficient symmetry. |
| Group-reference testing, P2 | [Hemerik and Goeman](https://pmc.ncbi.nlm.nih.gov/articles/PMC6405018/), section3 | Exchangeable group ranks with ties; compact-Haar extension is derived separately. Randomization cannot repair a non-invariant observed mask/operator. |
| Foreground response, P2 | [Planck IV](https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html), section2.4/appendixD | Blind mixing ambiguity and actual processing matter. Released polarization weights include beam correction and LFI recalibration. |
| Constrained spectral cleaning, P2 | [Constrained ILC](https://arxiv.org/pdf/1006.5599), section2.6; [moment ILC](https://arxiv.org/abs/2006.08628) | Known responses permit explicit nulling; spectral variation needs extra moments. Compressed SMICA alone cannot recover arbitrary frequency contrasts. |
| Optical response, P3/P4 | [Heinesen](https://arxiv.org/pdf/2010.06534), sections3-5 | Phenomenological local cosmographic tensors can be derived without Einstein evolution. Smoothness does not provide a finite-redshift numerical remainder bound. |
| Physical family comparison, P5 | [Saadeh et al.](https://arxiv.org/abs/1605.07178) | Physical temperature/polarization calculation is a literature comparator, not a supplied full native family atlas. |
| Adaptive research | [Bayesian Workflow](https://arxiv.org/abs/2011.01808) | Iterative model criticism, comparison and revision are standard workflow activities; fitting a model does not validate its source law. |
| Data-selected claims | [Berk et al.](https://arxiv.org/abs/1306.1059) | Simultaneous inference can protect an explicitly specified model/function family. Naming a new method after inspecting data does not retroactively give prospective coverage. |
| Sequential validation | [Howard et al.](https://arxiv.org/abs/1810.08240) | Confidence sequences allow time-uniform coverage under stated stochastic assumptions. They cannot create fresh independent observations from repeatedly processing one sky. |
| Computational calibration | [Talts et al.](https://arxiv.org/abs/1804.06788) | Simulation-based calibration diagnoses inference computation under a generative model; it does not prove that model matches the observational selection/foreground process. |

The first executable changes are full24 depth-constancy covariance sensitivity,
then its bias/variance frontier, and a shared60-carrier shape-versus-orientation
reference experiment. Further candidates are conditional model e-values on the
retained274 distance rows, released SMICA spectral-compression nullspace witnesses,
and target-frame calibration feasibility. None requires replaying the one-use
Gaia pass. The original physical predicates remain separate.


## Additional theory source context — pending independent review

Actual read-only Astra contribution: [host transcription](reviews/THEORY_ADVISOR_SUPPLEMENT.md), `/root/r25_statistics_theory`, requested Astra/xhigh, observed UNKNOWN. New T7–T10 are elementary derivations from its stated assumptions, **PENDING_FRESH_INDEPENDENT_REVIEW**. Existing T1–T6 retain the bounded [PLAN_REVIEW_CLOSEOUT](reviews/PLAN_REVIEW_CLOSEOUT.md) scope; no source-adviser contribution is itself independent admission.

| Proposition | Primary context | Exact applicability boundary |
|---|---|---|
| T7 calibration geometry and tensor transport | [Survey calibration §2 equations3–7](https://www150.statcan.gc.ca/n1/pub/12-001-x/2005001/article/8091-eng.pdf) | Convex-hull/Farkas and shared finite tensor-law identities are directly proved here. Survey sampling/transport assumptions are additional; balance does not prove MAR or bound missing outcomes. |
| T8 angular pair, spin and covariance | [Darling angular construction](https://arxiv.org/pdf/1310.0500), [Gaia AppendixE](https://arxiv.org/html/2204.12574v2#A5), [Truebenbach §III](https://arxiv.org/html/1808.07103v1#S3) | Angular-rate context, within-source tangent/spin covariance and shared objects respectively; these sources do not supply a calibrated cross-source Gaia law or our STF derivation. Full-kernel theorem does not establish compressed-image completeness. |
| T8 Gaussian quadratic-form reference | [Quadratic forms in normal variables](https://academic.oup.com/biomet/article-abstract/57/3/567/253370) | Exact projector/whitening gives chi-square. Computed small residual is control only; certified spectral delta gives the separately derived conservative inflation bound. No new numerical-certification algorithm is claimed. |
| T9 conditional evidence and union-null maximum | [Universal Inference §§5–6](https://arxiv.org/html/1912.11436) | Training-measurable normalized q suffices without training-uncertainty integration; conditioning/adaptive data choice and numerical null-supremum certification remain distinct obligations. Existing distance candidate wording is changed only through its actual review/repair, not this document. |
| T10 perturbation context | [Matrix perturbation primary context](https://link.springer.com/article/10.1007/BF01933494) | The displayed triangle-inequality proof is supplied explicitly; no unchecked equation is attributed to this paper. Singular ratio or independent-code agreement alone gives no deterministic error bound. |

No new browsing, numerical experiment or original scientific admission accompanied this source-context assembly. The primary references above were supplied by the actual adviser; formula-level application is exposed in THEOREMS rather than presented as already independently validated literature results.
