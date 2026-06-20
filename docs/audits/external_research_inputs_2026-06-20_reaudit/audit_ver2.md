## 1. Verdict

**REJECT / NOT READY.**

현재 원고는 방법론·claim-tier framework로는 구제 가능하지만, 양의 Bayes factor, (Q/F) occupancy, global-tilt preference를 현행 결과로 유지하기에는 핵심 수학·추론 조건이 충족되지 않았다. 특히 amplitude-matched contamination null에서 (95/100)이 (\ln B>5)를 내므로, 현재 likelihood는 물리적 global tilt와 관측 dipole systematic을 판별하지 못한다 (`manuscript/htt_base_research_report.pdf:p.180`). 또한 archive에는 지정된 `main.tex`와 chapter source가 없고 PDF만 있어, 아래 manuscript 위치는 PDF page로 인용한다.

## 2. Minimal Defensible Claim

명시된 **단일유체·irrotational Bianchi normal-frame·comparator** 가정 아래, 원고는 FLRW comparator로부터의 departure를 signed coordinate (x_C)로 분해하고 각 해석 단계의 가정 의존성을 기록하는 framework를 제공한다. 현재 HTT 계산은 외부/legacy transfer와 채택된 dipole·bulk-flow Gaussian likelihood 아래에서 nonzero (\beta)-like amplitude가 fit을 개선함을 보여줄 뿐이며, 이는 global tilt, anisotropic geometry, Bianchi family 또는 물리적 filling fraction의 증거가 아니다. MIO와 OBSSTAT 산출물은 diagnostic certificate 및 feature extraction으로만 안전하다.

## 3. Fatal Blockers

| #  | Blocker                                                                                                                                                                                                                                                                                                                               | Evidence                                                                                                              | Required Fix                                                                                                                                                                                                                                              |                                                                                                                                            |                                                                                                                                                                                           |
| -- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| F1 | **현재 (\ln B)는 global tilt를 식별하지 못한다.** 관측된 CatWISE/Radio amplitude를 넣되 true cosmological tilt를 0으로 둔 null에서 (95/100)이 (\ln B>5)를 기록한다.                                                                                                                                                                                                | `manuscript/htt_base_research_report.pdf:p.180`; PDF-derived text 7798–7818                                           | 모든 positive-(\ln B) 문구를 “admitted-amplitude likelihood response”로 재분류한다. 실제 survey scanning law, clustering, mask, selection, CF4 calibration을 생성모형에 넣은 hierarchical null에서 FPR가 사전 기준 아래로 내려가기 전에는 global-tilt evidence를 금지한다.                           |                                                                                                                                            |                                                                                                                                                                                           |
| F2 | **Master identity의 vorticity sector가 frame-inconsistent하다.** 원고는 Bianchi geometry-frame congruence를 group-orbit normal로 선택해 (\omega_{ab}=0)이라고 명시하면서, 같은 geometry-frame Hamiltonian identity에 (W_{\rm std}^2\neq0)를 넣고 tilted VII(_h)를 vortical sector로 분류한다. matter-frame vorticity는 normal-frame Hamiltonian constraint의 동일 항이 아니다. | `manuscript/htt_base_research_report.pdf:pp.33,38–40,55`; PDF-derived text 1397–1404, 1627–1657, 1706–1724, 2471–2477 | slicing identity에서는 (W_{\rm std}=0)로 고정한다. 별도의 threading/matter-frame identity를 전체 boost·constraint 항과 함께 유도하지 못하면 vortical extension, VII(_h) vorticity decomposition, 관련 (x,Q,F) 결과를 철회한다.                                                              |                                                                                                                                            |                                                                                                                                                                                           |
| F3 | **(Q)와 (F)의 denominator가 numerator를 bound하지 않는다.** (x)는 실제 posterior에서 (\Omega_{\rm tilt})가 지배하지만 (x_{\max})는 MES shear bound로부터 얻은 (\Sigma_{\rm std}^2) ceiling이다. 따라서 (x_{\max}\ge                                                                                                                                                  | x                                                                                                                     | )라는 admissible-ceiling 조건이 성립하지 않으며 “9% anisotropy budget” 해석은 정의와 충돌한다.                                                                                                                                                                                  | `manuscript/htt_base_research_report.pdf:pp.41–44,145,150,179,184`; PDF-derived text 1800–1815, 1880–1905, 6495–6505, 7770–7777, 7991–8015 | (\mathbf F=(F_\sigma,F_\omega,F_{\rm tilt},F_k))처럼 component-matched ceiling을 도입하거나, 물리적 admissible set에서 joint supremum (U_C\ge X_C^+)를 증명한다. 그 전에는 기존 (Q,F,\Pi) 수치를 proxy score로만 표기한다. |
| F4 | **Bayes-factor 강도는 prior cutoff와 외부 error bar에 의해 결정된다.** prior narrowing이 (\ln B\simeq+26)을 (-39.1)까지 뒤집고, 거의 같은 bulk-flow amplitude에서 (\sigma_\beta) 변화만으로 (+26\to+44\to+106)이 된다.                                                                                                                                                  | `manuscript/htt_base_research_report.pdf:pp.155,182–183`; PDF-derived text 6835–6845, 7895–7905, 7929–7937            | 물리적으로 정당화된 prior family를 먼저 고정하고 floor×ceiling sensitivity surface를 본문에 제시한다. CF4 likelihood는 estimator/method covariance와 calibration uncertainty를 포함해 다시 구성한다. Bayesian evidence의 prior-volume 민감성은 일반적인 성질이므로 단일 Jeffreys label로 덮을 수 없다. ([arXiv][1]) |                                                                                                                                            |                                                                                                                                                                                           |

## 4. Major Findings

| Severity | Location                                             | Problem                                                                                                                                     | Why It Matters                                                                                         | Required Fix                                                                                                                                                                              |                                                                                                         |                                                                                |
| -------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| High     | `manuscript/htt_base_research_report.pdf:p.12`       | 서론은 “combined significance exceeds (5\sigma)” 및 isotropy challenge라고 단정하지만, 후반부는 source origin을 판별하지 못하고 contaminated-null FPR가 95%임을 인정한다. | opening rhetoric가 최종 검증 결과와 정면 충돌한다.                                                                   | “heterogeneous published amplitude anomalies used as conditional inputs”로 교체한다.                                                                                                           |                                                                                                         |                                                                                |
| High     | `manuscript/htt_base_research_report.pdf:p.145`      | (D_2,D_3) likelihood가 Bianchi contribution을 (D_\ell^{\rm true})에 더한 뒤 central (\chi^2)로 처리한다.                                               | deterministic Bianchi template라면 (\sum_m                                                               | a_{\ell m}                                                                                                                                                                                | ^2)는 noncentral distribution이며 orientation이 필요하다. stochastic anisotropic model이면 full covariance가 필요하다. | mean-template branch와 covariance branch를 분리하고 harmonic-space likelihood를 사용한다. |
| High     | `manuscript/htt_base_research_report.pdf:p.158`      | PPC (p=0.012)를 “data property, not model failure”라고 해석한다.                                                                                   | 이는 single-(\beta) likelihood 또는 covariance model이 해당 channel을 재현하지 못한다는 posterior-predictive failure다. | model inadequacy로 기록하고 해당 channel을 포함한 evidence claim을 block하거나 mixture/outlier model을 비교한다.                                                                                              |                                                                                                         |                                                                                |
| High     | `manuscript/htt_base_research_report.pdf:pp.144,178` | CatWISE/Radio/CF4를 conditional independence로 곱하지만 shared large-scale structure, sky selection, calibration covariance는 직접 추정되지 않는다.         | 같은 latent amplitude의 반복 측정을 독립으로 취급하면 evidence가 과도하게 누적될 수 있다.                                         | joint hierarchical covariance와 survey-specific nuisance를 추정하고 leave-one-survey-out predictive score를 보고한다.                                                                                |                                                                                                         |                                                                                |
| High     | `manuscript/htt_base_research_report.pdf:p.145`      | VII(_h)-specific Saadeh vorticity constraint를 모든 vorticity-bearing type에 적용한다.                                                              | family dynamics와 observable transfer가 다른데 동일 bound를 쓰면 family ranking과 exclusion이 인공적일 수 있다.           | type-specific transfer가 없으면 해당 channel을 family comparison에서 제거한다. Planck의 physically coupled VII(_h) 분석은 no-evidence 결과였으므로 이 제약을 다른 family의 universal likelihood로 확장할 수 없다. ([arXiv][2]) |                                                                                                         |                                                                                |
| High     | `manuscript/htt_base_research_report.pdf:pp.179–180` | structured-null bank는 (0/500)인데 amplitude-matched contamination null은 95% FPR다.                                                             | null bank가 실제 load-bearing confounder를 포함하지 못한다는 뜻이다.                                                  | null amplitude와 covariance를 observed summary에 맞추고, union-FPR와 confidence interval을 다시 계산한다.                                                                                               |                                                                                                         |                                                                                |
| High     | `manuscript/htt_base_research_report.pdf:pp.182–183` | CF4 point Gaussian의 작은 quoted uncertainty가 evidence를 폭증시킨다.                                                                                 | CF4 estimator precision은 survey geometry와 방법에 민감하고 과소평가될 수 있다.                                         | raw likelihood 또는 mock-calibrated estimator covariance를 사용한다. CF4 estimator 연구도 통상 uncertainty 과소평가가 tension을 키울 수 있다고 보고한다. ([arXiv][3])                                                 |                                                                                                         |                                                                                |
| Medium   | `manuscript/htt_base_research_report.pdf:p.177`      | flat comparator를 “most conservative”라고 부른다.                                                                                                 | curvature sign에 따라 flat comparator는 (x)를 키우거나 음수로 만들므로 보편적 ordering이 없다.                               | “fiducial comparator”로만 부르고 comparator envelope를 기본 결과로 둔다.                                                                                                                               |                                                                                                         |                                                                                |
| Medium   | `manuscript/htt_base_research_report.pdf:p.150`      | (G=F(0)/F(z_*)) 예시가 임의의 (\beta(z)) toy laws에서 나온다.                                                                                          | 데이터·GR evolution·selection을 분리하지 못하므로 local/global discriminator가 아니다.                                 | Boltzmann/GR evolution 또는 registered phenomenological model과 redshift-bin covariance를 결합한다.                                                                                               |                                                                                                         |                                                                                |
| Medium   | `reports/result_pack_B.md:39-64`                     | global-tilt claim ceiling을 `conditional`로 두지만 observed-data rank/FPR payload는 없다.                                                           | framework gate를 통과한 것처럼 읽힐 수 있다.                                                                       | current state를 `blocked_observed_inference`; conditional은 synthetic-design 수준에만 허용한다.                                                                                                     |                                                                                                         |                                                                                |
| Medium   | `reports/result_pack_C.md:38-51`                     | MIO rows는 대부분 covariance/null 부재로 blocked인데 report manifest의 `failed_gates=[]`다.                                                            | report-generation gate와 scientific gate가 혼동된다.                                                         | `report_gates`와 `science_gates`를 별도 필드로 내보낸다.                                                                                                                                             |                                                                                                         |                                                                                |
| Medium   | `manuscript/pdf_claim_lint_report.md:25-27`          | 71개 warning에도 failed finding이 0이다.                                                                                                          | lint가 “conditional/legacy” marker만 있으면 강한 숫자와 “decisive” 언어를 사실상 허용한다.                                 | final PDF에서 숫자+odds+Jeffreys label 조합을 failure로 처리한다.                                                                                                                                     |                                                                                                         |                                                                                |
| Medium   | archive structure                                    | prompt가 요구한 `main.tex`와 chapter source는 없고 compiled PDF가 포함됐다.                                                                              | 현재 prose와 generated snippets의 source-level 일치 여부를 검증할 수 없다.                                            | 다음 감사 archive에는 실제 TeX source와 line-stable snapshot을 포함한다.                                                                                                                                |                                                                                                         |                                                                                |

## 5. Physics/Math Audit

| Item                                      | Status                   | Issue                                                                                                       | Required Fix                                                                                           |
| ----------------------------------------- | ------------------------ | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Metric signature and basic dimensions     | PASS                     | ((-,+,+,+)), (H=\Theta/3), dimensionless normalized quantities는 대체로 일관적이다.                                  | 유지.                                                                                                    |
| Shear normalization                       | PASS                     | (\Sigma_{\rm std}^2=\sigma_{ab}\sigma^{ab}/(6H^2)) 및 (\Sigma_{\rm std}^2<(3/2)B_\sigma^2) 변환은 일관적이다.        | 텍스트·코드 convention을 하나로 고정.                                                                             |
| FLRW/comparator limit                     | CONDITIONAL              | matched comparator에서는 (x=0)이 FLRW limit이지만 flat comparator에서는 curved FLRW도 (x\neq0)이다.                      | 모든 (x,Q,F,\Pi)에 comparator label을 붙인다.                                                                 |
| (x_C) as signed coordinate                | PASS WITH CAVEAT         | signed comparator coordinate임을 명시하지만 일부 prose는 “distance” 또는 “departure amount”로 읽힌다.                       | magnitude 언어를 제거하고 component norm/cancellation index를 병기한다.                                            |
| Bianchi normal-frame vorticity            | FAIL                     | normal congruence는 hypersurface-orthogonal인데 (W_{\rm std})를 nonzero geometry-frame variable로 사용한다.          | slicing/threading formalism을 분리하고 frame transformation을 다시 유도한다.                                       |
| Single-fluid tilt split                   | CONDITIONAL              | (\Omega_{\rm tilt}=(1+w)\Omega\sinh^2\beta)는 단일 perfect fluid에는 맞지만 현실적 multi-fluid posterior에 자동 적용되지 않는다. | (\sum_s(1+w_s)\Omega_s\sinh^2\beta_s)와 energy flux/anisotropic stress를 포함한 multi-fluid identity를 유도한다. |
| MES application                           | FAIL FOR (Q/F)           | MES shear bound를 full (x) budget ceiling으로 사용한다.                                                            | component-matched 또는 joint admissible ceiling 필요.                                                      |
| Deterministic template vs covariance      | FAIL                     | D2/D3 likelihood가 두 통계 객체를 구분하지 않는다.                                                                        | mean-template/noncentral branch와 covariance/BiPoSH branch 분리.                                          |
| No-tilt limit                             | PASS LOCALLY             | (\beta=0\Rightarrow\Omega_{\rm tilt}=0) 자체는 맞다.                                                             | multi-fluid·frame identity 수정 후 재검산.                                                                   |
| Zero-denominator and super-ceiling limits | PARTIAL                  | negative/super-ceiling case를 flag하지만 ordinary tilted rows에서 denominator admissibility가 증명되지 않았다.            | certification 전부 해제 후 재구축.                                                                             |
| (G_F) redshift evolution                  | FAIL AS RESULT           | toy (\beta(z)) prescriptions이며 GR/Boltzmann derivation이 아니다.                                                | evolution equation, selection transfer, bin covariance를 명시한다.                                          |
| Family interpretation                     | PASS AT GOVERNANCE LEVEL | family-ID가 blocked라고 명시한다.                                                                                  | legacy family rankings을 main results에서 완전히 제거한다.                                                       |

## 6. Statistics/Inference Audit

| Item                         | Status                | Issue                                                                        | Required Fix                                                                                                                                            |
| ---------------------------- | --------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Likelihood specification     | PARTIAL               | channel formulas는 명시됐지만 shared covariance와 nuisance hierarchy가 불충분하다.        | joint generative likelihood 작성.                                                                                                                         |
| Priors                       | FAIL                  | (\Sigma^2) lower cutoff가 evidence sign과 magnitude를 바꾼다.                      | physically motivated prior family, sensitivity surface, prior predictive checks.                                                                        |
| Bayes factors                | FAIL                  | prior support와 (\sigma_\beta)가 수십–백 nat를 결정한다.                               | 단일 (\ln B) headline 제거; robust range와 alternative scoring rule 보고.                                                                                      |
| Occam penalty interpretation | FAIL                  | “data-dominated” 해석과 prior-floor sensitivity가 충돌한다.                          | posterior/prior information gain과 boundary mass를 보고한다.                                                                                                  |
| Null recovery                | FAIL FOR SOURCE CLAIM | isotropic noise null은 통과하지만 amplitude-matched systematic null은 95% trigger다. | source-matched null이 primary calibration이어야 한다.                                                                                                         |
| Structured nulls             | INADEQUATE            | (0/500)은 injection family/amplitude가 load-bearing confounder를 재현하지 못한다.      | observed-statistic-matched adversarial null 및 exact binomial interval.                                                                                  |
| PPC                          | FAIL                  | channel (b)의 (p=0.012)를 model failure로 인정하지 않는다.                             | likelihood 수정 또는 evidence claim block.                                                                                                                  |
| LOOCV                        | FAIL/LEGACY ONLY      | current observed-data LOOCV가 없고 conditioned legacy figure만 존재한다.             | held-out survey predictive density와 PSIS diagnostics 제출.                                                                                                |
| Channel ablation             | DIAGNOSTIC ONLY       | signal이 b/c amplitude inputs에서 나온다는 사실만 확인한다.                                | 독립 evidence 검증으로 해석 금지.                                                                                                                                 |
| Look-elsewhere               | OPEN                  | thresholds, directions, model families, scenarios 전체 scan correction이 없다.    | pre-registered statistic family와 global null distribution.                                                                                              |
| Local/global discrimination  | BLOCKED               | rank/FPR는 synthetic gate surface이고 observed covariance가 없다.                  | nuisance-projected rank + observed covariance + injection recovery.                                                                                     |
| MIO/HTT separation           | PASS                  | MIO certificate를 HTT evidence에 합치지 않는다.                                      | 유지.                                                                                                                                                     |
| Bootstrap/jackknife          | PASS AS DIAGNOSTIC    | p-value/posterior로 승격하지 않는다고 명시한다.                                           | 유지.                                                                                                                                                     |
| CF4 likelihood               | FAIL                  | point Gaussian이 estimator/systematic uncertainty를 충분히 표현하지 않는다.              | mock-calibrated likelihood 또는 raw peculiar-velocity forward model.                                                                                      |
| CatWISE systematic treatment | FAIL                  | fixed uncertainty inflation은 scanning-law/selection likelihood를 대체하지 못한다.    | exact sky mask와 clustering/selection mocks를 likelihood에 포함한다. 최근 reassessment도 mask·clustering·selection을 함께 모사할 때 significance가 낮아짐을 보인다. ([arXiv][4]) |

## 7. Figure/Result Audit

* `figures/current/fig_revision_tomographic_forecast.manifest.json`
  `paper_main` 사용이 부적절하다. local/global template correlation이 (-0.962), separation score가 (0.038)이므로 이 그림은 discrimination 가능성을 보여주는 것이 아니라 **현재 설계의 거의-degeneracy**를 보여준다.

* `figures/current/fig_revision_prior_support_surface.manifest.json`
  표시된 `proxy_lnb_definition`은 실제 marginal likelihood가 아니다. prior sensitivity의 개념도만 허용되며 (\ln B) 수치 근거로 사용하면 안 된다.

* `figures/current/fig_revision_sigma_beta_band.manifest.json`
  역시 analytic proxy이고 look-elsewhere correction이 display-only다. CF4 evidence robustness를 검증하지 않는다.

* `figures/current/fig_revision_per_channel_occupancy.manifest.json`
  manifest 자체가 `scalar Q blocked for channel mismatch`라고 명시한다. 따라서 원고의 (F\simeq6.3%), (Q\simeq0.09) physical occupancy 문구와 양립하지 않는다.

* `figures/current/fig_current_qfpi_gf_semantic_split.manifest.json`
  proxy bars가 canonical (Q,F,\Pi,G_F)가 아니다. 방법론 schematic 외 사용 금지.

* `figures/current/fig_current_local_global_rank_fpr.manifest.json`
  deterministic mock gate stress plot이며 observed local/global inference가 아니다.

* `figures/observed_current/fig_observed_planck_lowell_residual.manifest.json`
  full covariance, mask coupling, cosmic variance 또는 p-value가 아니다. anomaly significance 또는 Bianchi compatibility로 해석 금지.

* `figures/observed_current/fig_observed_cf4_velocity_density.manifest.json`
  reconstruction diagnostic일 뿐, volume selection과 estimator covariance를 통제한 global-tilt measurement가 아니다.

* `figures/observed_current/fig_observed_cf4_depth_response.manifest.json`
  descriptive percentile band를 (G_F), tomography evidence 또는 coherent global tilt로 해석하면 안 된다.

* `figures/observed_current/fig_observed_desi_footprint_depth.manifest.json` 및 `fig_observed_desi_selection_weights.manifest.json`
  survey-support/systematics inventory이며 local/global discrimination 결과가 아니다.

* `figures/observed_current/fig_observed_longrun_jackknife_bootstrap.manifest.json`
  uncertainty diagnostic일 뿐 p-value, posterior 또는 evidence가 아니다.

* `figures/conditioned_legacy/root__fig_evidence_grand_bar.manifest.json`, `root__fig_pairwise_bf_matrix.manifest.json`, posterior triangle, direction posterior, equivalence-class evidence 계열
  main-text evidence에서 완전히 격리해야 한다. 현 null/covariance/prior/PPC/LOOCV gate를 통과하지 않았다.

## 8. Claim-Tier Corrections

| Current wording                                                                       | Required wording                                                                                                                                                                                                                   |
| ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| “The combined significance now exceeds (5\sigma)… challenges statistical isotropy.”   | “Several heterogeneous surveys report dipole amplitudes above simple kinematic expectations; their common physical origin is not established and they are treated here as conditional inputs.”                                     |
| “The data support a tilt-like degree of freedom, (\ln B\simeq+26).”                   | “Given the admitted dipole/bulk-flow amplitudes, selected priors, and transfer prescription, a shared nonzero (\beta)-like amplitude improves the configured likelihood. This is not evidence that the amplitude is cosmological.” |
| “Odds exceeding (10^{11}:1) in favour of tilted models.”                              | **Remove.**                                                                                                                                                                                                                        |
| “The defect is at roughly 9% of the anisotropy ceiling.”                              | “The signed, tilt-dominated comparator coordinate divided by a shear-derived MES scale is approximately 0.09; this ratio is not a certified occupancy.”                                                                            |
| “The tilt occupies approximately one-sixteenth of the MES-allowed anisotropy budget.” | **Remove.**                                                                                                                                                                                                                        |
| “The pipeline correctly returns null.”                                                | “No triggers occurred in the finite isotropic-noise mocks; however, amplitude-matched contamination mocks triggered in 95% of runs, so source identification fails.”                                                               |
| “The CatWISE+Radio PPC tension is a property of the data, not model failure.”         | “The single-(\beta) likelihood or its covariance model fails the registered PPC criterion for this channel.”                                                                                                                       |
| “CMB carries zero tilt information.”                                                  | “The configured scalar (D_2/D_3) likelihood provides no positive support for the shared-(\beta) parameter.”                                                                                                                        |
| “Flat comparator is the most conservative choice.”                                    | “Flat is the fiducial comparator; no universal conservative ordering exists.”                                                                                                                                                      |
| “Conditional evidence for global tilt.”                                               | “Premise-conditioned amplitude fit.”                                                                                                                                                                                               |
| “Bianchi V corrected evidence/result.”                                                | “Legacy transfer-conditioned likelihood output under the selected proxy model.”                                                                                                                                                    |
| “Decisive/strong evidence” for any legacy (\ln B)                                     | “Large likelihood-ratio/evidence value under prior- and error-budget-sensitive conditioned inputs”; preferably omit Jeffreys adjective entirely.                                                                                   |

## 9. Additional Analyses Required

1. Re-derive the Hamiltonian departure identity in two distinct versions: hypersurface-normal Bianchi slicing with (W_{\rm std}=0), and a genuinely vortical threading formulation with no intrinsic group-orbit (^{3}R) substitution.

2. Derive a multi-fluid departure identity including species-dependent tilts, energy flux (q_a), anisotropic stress (\pi_{ab}), and relative-velocity cross terms.

3. Replace scalar (Q/F) by channel-matched occupancy:
   [
   \mathbf F=(F_\sigma,F_\omega,F_{\rm tilt},F_k),
   ]
   or prove a joint admissible ceiling over the physical constraint manifold.

4. Replace channel (e/h) with either:

   * deterministic (a_{\ell m}) mean-template likelihood with noncentral statistics and orientation marginalisation, or
   * full anisotropic covariance/BiPoSH likelihood.

5. Build one hierarchical generative model for CatWISE, radio, CF4 and local-flow nuisance terms, including cross-survey cosmic covariance, masks, selection functions and calibration parameters.

6. Recompute CF4 likelihood from estimator mocks or raw peculiar-velocity data. Report sensitivity to estimator, depth window and covariance. Do not use the smallest quoted (\sigma_\beta) as a direct Gaussian constraint without this calibration. ([arXiv][3])

7. Run observed-statistic-matched nulls. The contamination amplitude and covariance must be chosen so the mocks reproduce the measured dipole summaries before testing false positives.

8. Report exact binomial confidence bounds for every FPR and increase mock count enough to resolve the preregistered target.

9. Perform actual prior-floor×ceiling evidence runs, not proxy surfaces. Report posterior boundary mass, KL information and model probabilities under multiple physically motivated priors.

10. Treat PPC (p=0.012) as a failure gate; compare single-(\beta), survey-specific amplitudes, mixture/outlier and systematic-response models.

11. Run held-out survey LOOCV or external validation: fit without one survey and predict its amplitude, direction and depth trend.

12. Replace toy (G_F(z)) curves with a registered GR/Boltzmann or phenomenological evolution equation and propagate redshift-selection covariance.

13. Bind all direction claims to identical masks and sky support, with look-elsewhere calibration over axes, multipoles and model families.

14. Keep Bianchi family-ID blocked until native (a_{\ell m}^{T,E,B}), matched nulls, masks, full covariance and family-equivalence tests exist. Existing physically coupled Planck searches found no evidence for Bianchi VII(_h), underscoring that amplitude-only preference is not morphology evidence. ([arXiv][2])

15. Supply line-stable TeX source in the next audit archive so prose claims can be checked against the generated PDF.

## 10. Claims That Are Safe

* The master constraint yields a signed comparator coordinate in the **irrotational normal-frame, single-perfect-fluid** sector under explicit comparator assumptions.

* (x_C) is not an invariant anisotropy magnitude and can be small through signed cancellation.

* Current external/AniCLASS/legacy transfer outputs are transfer-conditional and are not native BASS validation (`reports/transfer_sensitivity_report.md:40-69`).

* MIO certificates are diagnostic reports and are not posterior odds, truth certificates or model rankings (`reports/result_pack_C.md:28-51,73-90`).

* Result Pack B defines useful pre-inference rank and FPR gates, but currently provides no observed-data global-tilt inference (`reports/result_pack_B.md:35-64,82-100`).

* The admitted dipole and bulk-flow amplitudes can be represented by a common nonzero (\beta)-like fit parameter under the configured Gaussian likelihood.

* The configured scalar CMB channels do not provide positive support for that (\beta)-like parameter.

* The amplitude-matched contamination experiment establishes a strong negative result: the current scalar likelihood cannot identify whether the matter-dipole amplitude is cosmological or systematic.

* Current Planck, DESI and CF4 figures are descriptive diagnostics only, as their manifests state.

* Scalar (x,Q,\Pi,F,G_F), directional coherence and low-(\ell) residuals do not identify a Bianchi geometry or family.

[1]: https://arxiv.org/abs/0803.4089 "https://arxiv.org/abs/0803.4089"
[2]: https://arxiv.org/abs/1502.01593 "https://arxiv.org/abs/1502.01593"
[3]: https://arxiv.org/abs/2306.11269?utm_source=chatgpt.com "Evaluating bulk flow estimators for CosmicFlows-4 measurements"
[4]: https://arxiv.org/abs/2511.00822?utm_source=chatgpt.com "The CatWISE2020 Quasar dipole: A Reassessment of the Cosmic Dipole Anomaly"
