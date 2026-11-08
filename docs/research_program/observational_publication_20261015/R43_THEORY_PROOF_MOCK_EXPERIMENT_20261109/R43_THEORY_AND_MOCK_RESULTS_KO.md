# R43: 함수량 식별성 정리와 tensor five-variable mock experiment

- Date: 2026-11-09 (Asia/Seoul)
- Parent: R42 `b8c2d851b4db59d43cf5c0044c42a041b97c44c6`
- Status: synthetic-only theory and numerical design study
- Seed: 20261109
- Scope: latest tensorized posterior-pushforward `T=(x,Q,Pi,F,G_F)` versus physical generative competitors and inference/readout methods. Scalar `x_C` is not the primary comparator.

## 1. Physical/statistical contract

Use the 17-dimensional kinematic chart
[
\theta_K=(\sigma_{ab}/H,\ \omega_a/H,\ A_a/(cH),\ \beta_{RM},\ \beta_{MO})
\in\mathbb R^{5+3+3+3+3}.
]
The five objects are derived jointly from one data/model posterior or compatibility law:
[
T=(x,Q,\Pi,F,G_F)=\mathcal T\{p(\theta_K,\psi,\eta\mid d,M,S,W)\}.
]
They are neither independent parameters nor independent likelihood factors. In particular, multiplying marginal densities for x,Q,Pi,F,G_F is not a valid joint likelihood construction.

## 2. Theorem: nuisance-projected local functional identifiability

Let the local mean model be
[
Y=\mu(\theta,\eta)+\epsilon,\qquad \epsilon\sim\mathcal N(0,C),\quad C\succ0,
]
where \(\theta\in\mathbb R^p\) are physical coordinates and \(\eta\in\mathbb R^q\) are nuisance coordinates. At the point of interest define
[
J_\theta=\partial_\theta\mu,\quad J_\eta=\partial_\eta\mu,\quad
B=C^{-1/2}J_\eta,\quad
P_\eta=BB^+.
]
Then the efficient Fisher matrix for \(\theta\), after projecting out the linear nuisance tangent space, is
[
I_{\rm eff}
=J_\theta^TC^{-1/2}(I-P_\eta)C^{-1/2}J_\theta\succeq0.
]
For a differentiable target functional \(\phi(\theta)\in\mathbb R^r\), the regular first-order local identifiability condition is
[
\boxed{\ker I_{\rm eff}\subseteq\ker D\phi.}
]
Equivalently, every physical perturbation that can be cancelled by a nuisance perturbation must leave the target unchanged.

**Proof.** For any direction h,
[
h^TI_{\rm eff}h=
\|(I-P_\eta)C^{-1/2}J_\theta h\|^2.
]
Thus \(h\in\ker I_{\rm eff}\) iff \(C^{-1/2}J_\theta h\in\operatorname{col}(C^{-1/2}J_\eta)\), equivalently iff some k satisfies
\(J_\theta h+J_\eta k=0\). Such h is an infinitesimal observational-equivalence direction. A target is invariant along every such direction exactly when \(D\phi h=0\), giving the boxed condition. This proves a local, first-order statement only.

When \(I_{\eta\eta}\) is nonsingular, this equals the usual Schur complement
\(I_{\theta\theta}-I_{\theta\eta}I_{\eta\eta}^{-1}I_{\eta\theta}\). With singular nuisance blocks, use the projector/generalized inverse and check the range condition rather than silently inverting the block.

**Scope guard.** This is not global identification. A global claim requires \(\phi\) to be constant on every full observational-equivalence fibre, including disconnected branches. Structural rank is also distinct from practical weak identification/large posterior uncertainty. For parameter-dependent Gaussian covariance, include
[
I_{ab}=\mu_{,a}^TC^{-1}\mu_{,b}
+\tfrac12\operatorname{tr}(C^{-1}C_{,a}C^{-1}C_{,b}),
]
not only the mean-response term.

## 3. Consequences for the five kinematic sectors

The deliberately synthetic design includes redshift-shell dipoles
\(d(z)=g_{RM}(z)\beta_{RM}+\beta_{MO}+d_{\rm int}\), shear response
\(s(z)=g_\sigma(z)\sigma+q_{\rm cal}\), curl
\(c=\omega+\omega_{\rm frame}\), and acceleration
\(a(z)=g_A(z)A+a_{\rm cal}\).

- Without independent velocity/frame anchors, \(\beta_{MO}\) and intrinsic dipole share a 3-dimensional null fibre; \(\omega\) and frame spin share another 3-dimensional null fibre.
- Redshift variation of \(g_{RM}\) makes \(\beta_{RM}\) distinguishable from a redshift-independent intrinsic dipole in this mock. When tomography is removed (constant response), three further null directions appear.
- The STF shear functional is identifiable in this design, conditional on the chosen shear response and nuisance model.
- Anchors remove the six exact null directions in the mock design. This is a design fact, not evidence that actual catalogues provide such anchors.
- The direct leading contraction \(e^ae^b\omega_{ab}=0\) follows from symmetric × antisymmetric contraction. It does not prove that vorticity cannot enter higher-order distance-redshift coefficients.

## 4. Posterior readout and information inequality

For a regular model with score \(s_Y=\nabla_\theta\log p(Y\mid\theta)\), any deterministic readout T(Y) has score
[
s_T(T)=\mathbb E[s_Y\mid T],\qquad
I_T=\operatorname{Var}(\mathbb E[s_Y\mid T])\preceq
\operatorname{Var}(s_Y)=I_Y.
]
Equality holds iff the raw score is measurable with respect to T (under the relevant law). Therefore a derived five-variable readout cannot manufacture raw-data Fisher information. Its possible value is semantic typing, gauge/null-fibre disclosure, calibration diagnostics, directional functionals, and cross-shell structure. It beats a competing method only on a declared decision/prediction/calibration task, not by having more information than the input data.

For a fixed linear-Gaussian model \(Y\mid\theta\sim N(X\theta,\bar C)\) with known \(X,\bar C\) and Gaussian prior \(N(0,\Lambda_\theta)\),
[
V=(\Lambda_\theta^{-1}+X^T\bar C^{-1}X)^{-1},\quad
m=VX^T\bar C^{-1}Y,
\]
hence \(X^T\bar C^{-1}Y=V^{-1}m\). The complete Gaussian posterior \((m,V)\) recovers the score for \(\theta\) in this fixed family. This does not imply Bayes-factor sufficiency across different generative models: evidence can also depend on data-only quadratic terms, cross terms, model-specific covariance, selection, and nuisance integration.

## 5. Mock experiment

All data are generated in-code. No observational catalogue, mask, selection function, physical Bianchi solver/transfer, Planck MC, Gaia scan-law, Pantheon covariance, or Cobaya chain was used. The mock contains 17 physical coordinates and 14 explicit nuisance coordinates, five redshift shells, correlated AR(1) shell noise, and synthetic independent proxies for matter-observer velocity and frame spin. Response functions are design functions, not calibrated cosmological transfer functions.

The model registry contains:
- M0: isotropic model plus common nuisance law;
- M1: local observer boost;
- M2: two-fluid tilt plus boost;
- M3: STF shear kinematic proxy plus boost (explicitly **not** a Bianchi I/V/VII_h solution);
- M4: full 17-dimensional kinematic model.

Common Gaussian nuisance priors are analytically integrated. Physical parameter priors are explicit independent Gaussian priors. Held-out score is the conditional Gaussian log predictive density for the last redshift shell, conditional on earlier shells and retaining the cross-shell covariance. These scores are for one seeded mock realization and are not universal rankings.

### 5.1 Numerical results

| Quantity | Result |
|---|---:|
| unanchored physical Fisher rank / nullity | 11 / 6 |
| anchored physical Fisher rank / nullity | 17 / 0 |
| rank without redshift tomography | 8 / nullity 9 |
| full-sky directional-Hubble design rank | 9 / 9 |
| hemisphere design rank | 9 / 9 |
| full-sky / hemisphere condition number | 1.73235 / 18.28026 |
| scalar \(\beta_{MO}\)-norm projection: retained raw Fisher trace | 1.75786% |
| full Gaussian posterior score reconstruction relative residual | 1.57e-15 |
| F rotation-equivariance max absolute error | 4.34e-19 |
| SBC mean 95% coverage over 17 coordinates, 1000 prior-predictive mocks | 94.835% |

The 9 directional-Hubble modes are monopole 1 + acceleration dipole 3 + STF shear quadrupole 5. The hemispherical design remains full rank but is materially less conditioned. Cross-block dipole/quadrupole Gram leakage in the finite full-sky Fibonacci design is 2.67e-4.

Matched-mock null calibration used 1000 null calibration realizations and 2000 independent null evaluation draws per target, plus-one empirical tail estimates, and 1000 one-block alternative draws:
| Target | empirical FPR | power | interpretation |
|---|---:|---:|---|
| local \(\beta_{MO}\) | 4.15% | 90.5% | well detected under this mock amplitude/noise |
| global \(\beta_{RM}\) | 5.45% | 15.7% | weak power despite structural identifiability |
| STF shear | 5.65% | 10.8% | weak power; structural ID is not detection |

The one-mock observed tail probabilities under the corresponding matched mock nulls were \(\Pi_{MO}=0.001999\), \(\Pi_{RM}=0.113943\), and \(\Pi_\sigma=0.107446\). The binomial Monte Carlo errors are reported in `MOCK_EXPERIMENT_RESULTS.json`.

For the chosen synthetic priors, the one-realization marginal log-evidence / held-out last-shell conditional log predictive density were:
| Model | log evidence | held-out log predictive density |
|---|---:|---:|
| M0 isotropic+nuisance | 522.505 | 96.515 |
| M1 local boost | 524.524 | 96.285 |
| M2 two-fluid tilt+boost | 526.022 | 97.034 |
| M3 shear proxy+boost | 524.617 | 96.784 |
| M4 full 17-D | 525.082 | 98.064 |

The full model best predicts this particular last shell, while M2 has the highest integrated evidence in this single realization. The discrepancy is expected to depend on prior volume, truth, shell holdout, and simulated covariance. It does not establish superiority of HTT over Bianchi or over actual observations.

Directional support F uses 512 Fibonacci directions and a declared synthetic Gaussian 95%-ellipsoid anchor; the radial occupancy is constrained nonnegative. Maximum-support gap to a spectral upper bound decreases from 1.72e-5 at 64 directions to 2.71e-7 at 2048 directions. (G_F) uses the full synthetic cross-shell data covariance plus posterior push-forward covariance; its depth-like scalar is explicitly an in-sample inverse-covariance surrogate, not empirical halfspace depth or a physical growth/transport law.

## 6. R42 current-run provenance reconciliation

The R42 API can accept `matched_null_samples`, `shell_data_vectors`, and `cross_shell_data_cov`, but the inspected Cobaya runner calls `construct_r42_five_variable_state(bundle, samples_17, PARAM_NAMES_17, n_quadrature_dirs=100)` without those inputs. The implementation therefore enters its fallback seeded Gaussian null path and posterior-only shell path for that invocation. The saved Cobaya receipt also says `has_data_covariance=false`, `effective_sample_size=53`, and `ess_passed=false`. Thus capability-level implementation and execution-level provenance are distinct.

Other current R42 limitations:
- Its two-layer benchmark constructs several source operators with `verify_sha=False`.
- BIC uses a fixed `n_data_eff=1_720_000`, which needs an effective independent-data derivation.
- The regularized optimizer minimizes `-loglike + penalty`, but the reported quantity is called loglike/BIC; it is not automatically an unpenalized MLE.
- Its SBC loop perturbs the injected truth and draws approximate posterior clouds instead of drawing data from the generative likelihood and sampling the true posterior. Reported `fpr_n0` and some power values are hard-coded.
- R42 has six research-loop documents; their existence does not by itself reproduce a source-bound observational likelihood or validate the empirical claims.

These are input/provenance or implementation-validation limitations, not refutations of the five-variable mathematical construction. Do not promote the empirical claim tier based on R43 mock results.

## 7. Reproducibility and gates

Code in `scripts/r43/run_identifiability_mock.py`; tests in `tests/r43/test_identifiability_mock.py`. Run:
```bash
python scripts/r43/run_identifiability_mock.py --seed 20261109 --sbc 1000 --output MOCK_EXPERIMENT_RESULTS.json
pytest -q tests/r43
python -m compileall -q scripts/r43 tests/r43
```
Verified in the authoring environment: **9 tests passed**, compileall passed, same-seed output byte-identical, JSON/YAML parsed, all reported numerical invariants finite. This is a local synthetic-code verification receipt, not GitHub CI or an observational validation.

## 8. Claim ledger

- Established/derived: nuisance-projected Fisher functional criterion under the stated regular local Gaussian mean model; deterministic-readout score contraction; Gaussian posterior score recovery in the fixed family.
- Numerically checked: ranks/null fibres, directional-Hubble design, Fisher contraction, matched-mock calibration, prior-predictive SBC, directional quadrature convergence, covariance-separated shell depth surrogate.
- Synthetic-only: model evidence/predictive ranking, FPR/power, Pi tails, GF path.
- Unresolved: actual source-conditioned (p(d\mid\theta_K,\psi,\eta,M)), real-data matched nulls, physical Bianchi transfer competition, full posterior predictive validation across catalogue selection/overlap/calibration, empirical local/global boost-vs-tilt identification, observational claim promotion.

## References

1. T. J. Rothenberg (1971), “Identification in Parametric Models,” *Econometrica* 39, 577–591, DOI: 10.2307/1913267.
2. A. Heinesen (2021), “Multipole decomposition of the general luminosity distance Hubble law,” *JCAP* 05 (2021) 008, DOI: 10.1088/1475-7516/2021/05/008; arXiv:2010.06534.
3. A. Pontzen & A. Challinor (2007), “Bianchi model CMB polarization and its implications for CMB anomalies,” *MNRAS* 380, 1387–1398, arXiv:0706.2075.
4. S. Yasini & E. Pierpaoli (2017), “A relativistic treatment of the cosmic dipole,” *Phys. Rev. D* 96, 103502, arXiv:1610.00015.
5. A. Ferreira & M. Quartin (2021), “A brighter (and redder) side of the Universe: the cosmic-distance duality relation and the cosmic dipole,” *Phys. Rev. Lett.* 127, 101301.
6. J. Alsing & B. Wandelt (2019), “Nuisance hardened data compression for fast likelihood-free inference,” *MNRAS* 488, 5093–5103, DOI: 10.1093/mnras/stz1900; arXiv:1903.01473.
