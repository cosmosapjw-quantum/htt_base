# HTT R38 — 관측량 중심의 연구 수렴 프로그램

- 기준일: 2026-11-07
- 기준 저장소: cosmosapjw-quantum/htt_base
- 기준 연구 브랜치: research/htt-adaptive-methods-20261023
- 기준 commit: cab89d25af52a1b978a4da8c11eecdc25bb22759 (PR #564 merge)
- 새 작업 브랜치: research/observational-convergence-r38-20261107
- authority: 이 디렉터리의 DAG, claim ledger, 이론·자료 계약 및 실행 receipt

## 1. 결정과 범위

R38은 R37의 finite report-first release를 대체하거나 그 scientific status를 소급 변경하지 않는다. R37은 원래 42개 scientific node와 6개 paper contract를 보존한다. PR #564가 추가한 6개 R37 실행 카드는 실제 실행·qualification 전제로 남아 있으며, PR #564 자체도 solver/ODE, 새 raw catalogue acquisition, MC100 또는 journal submission을 수행하지 않았다. R38은 그 다음의 별도 수렴 epoch다.

R38의 목표는 여섯 연구축을 독립적인 이론 루프로 유지하면서 공통 frame-covariant observable/likelihood layer에 연결하고, real data posterior 및 검증된 no-go/upper-limit 결과 중 하나를 산출하는 것이다. 기존 five-variable tensorized framework는 likelihood 인자 다섯 개가 아니라 joint inference output의 구조화된 상태다.

이번 실행에서 완료된 것은 GitHub/Library 내부 기록 조사, 선택된 과거 PR 계보의 claim audit, 외부 선행연구 대조, 여섯 이론축의 observable/identifiability 설계, full-sky STF 정규화 검산, 자료 취득 우선순위와 local execution contract 작성이다. 실제 Planck/CF4/Pantheon+/Quaia 파일 다운로드, 로컬 checksum audit, 실제 map/catalogue likelihood, Cobaya run, sampler posterior, 코드 test/build는 실행하지 않았다. 이 구분은 claim ledger와 DAG에 보존한다.

## 2. Publishable novelty/significance gate

개별 재료는 novelty로 주장하지 않는다. Low-ell alignment/parity/BiPoSH, masked-sky correction, CMB observer aberration/Doppler, intrinsic dipole degeneracy, covariant observer-dependent Hubble multipoles, direction-dependent distance dipoles, Gaia VSH quadrupole, NVSS/RACS number-count dipoles, Bianchi anisotropy fits는 이미 문헌에 존재한다. 단순히 이 통계량들을 한 문서에 나열하거나 five-variable naming으로 포장하는 것은 충분한 novelty가 아니다.

가장 유망한 후보는 다음의 한정된 주장이다.

> 하나의 명시적 congruence/frame convention과 공통 nuisance-projected covariance를 사용해, (i) local observer boost, (ii) intrinsic CMB dipole/large-scale dipolar potential, (iii) matter-radiation relative tilt, (iv) redshift-evolving global shear/rotation을 각 관측 채널의 서로 다른 response operator로 연결하고, 실제 관측자료에서 식별 가능한 tensor-functional subspace와 남는 null space를 정량화한다.

이 novelty는 아직 candidate다. Makarov–Heinesen–Schücker (2026)의 Gaia DR3 Bianchi-I/VSH 분석, Maartens–Santiago–Clarkson (2024)의 covariant cosmography, Roldan–Notari–Quartin (2016)의 Doppler/aberration degeneracy, 2026년 Pantheon+–BAO directional CDDR dipole 검정, NVSS–RACS joint Bayesian dipole 분석과 차별화되는 실제 response-level contribution이 확인되어야 한다. Novelty gate는 literature review만으로 통과하지 않는다. 적어도 동일 likelihood 안에서 rank/conditioning, selection/nuisance stability, held-out posterior predictive calibration, 그리고 한 개 이상의 실제 관측량에 대한 constrained parameter/upper limit가 필요하다.

가장 강한 결과가 null 또는 partial identification이어도 된다. Local boost와 global tilt가 현재의 support에서 분리되지 않는다면 prior로 rank를 만들지 말고 식별된 조합과 비식별 null direction을 sharp confidence/credible set으로 보고한다. 그 자체가 재현 가능하고 prior-independent라면 의미 있는 방법론적 결과가 될 수 있다.

## 3. 독립 이론 연구 루프 6개

| 루프 | 핵심 질문 | 주 observable | 우선 모델/계산 | 필수 반증·종료 조건 |
|---|---|---|---|---|
| T1 Low-ell morphology → physics | low-ell morphology가 어떤 radiation multipole/stress와 연결되는가? | signed a_lm, STF2/STF3, BipoSH, T/E/B, bandpass-calibrated intensity moments | exact mask/beam response, phase-preserving morphology vector, bolometric/spectral map | T and Q/U processing, FFP/null covariance에 불안정하면 physical attribution 보류 |
| T2 Dipole anomaly | CMB dipole와 number-count dipole가 local boost인가, intrinsic signal인가? | CMB aberration/Doppler mode coupling, kinetic quadrupole, NVSS/RACS/Quaia flux- and z-binned dipoles | beta_RO/beta_RM/beta_MO plus intrinsic dipole and dipolar-potential nuisance | count selection/flux/declination correction 또는 common covariance가 불충분하면 anomaly claim 금지 |
| T3 Beyond-FLRW kinematics | 특정 congruence의 expansion/shear/vorticity/acceleration 중 무엇이 관측 가능한가? | radial distance, transverse proper motion/VSH, optical multipoles, redshift drift | 1+3 covariant response, optical/astrometric joint design rank | source-to-matter response, clock/frame spin/glide, finite-z remainder 미확보 시 geometry identification 금지 |
| T4 Anisotropy/Bianchi classification | local STF anisotropy를 global spatial geometry/family와 어떻게 구분하는가? | spatial Ricci STF, Weyl E/B, shear history, CMB T/E/B transfer | Bianchi I baseline, then II/VII0 existing templates; V/VII_h/others only with qualified transfer | local shear or trace scalar alone으로 Bianchi family label 금지 |
| T5 H(z,n) | directional expansion이 z에 따라 어떻게 변하며 distance/BAO/CF4/SN과 일치하는가? | monopole + dipole + STF quadrupole per z-shell, D_L/D_A, radial/transverse distances | low-z optical law plus finite-z remainder and redshift-window covariance | low-z formula high-z extrapolation 금지; absolute H0 requires calibrated distance ladder |
| T6 Local boost vs global tilt | observer motion, matter-radiation tilt, intrinsic CMB dipole, global shear history를 동시에 분리할 수 있는가? | joint CMB/radio/quasar/SN/CF4/Gaia response and covariance | nuisance-projected whitened response SVD/Fisher plus tensor-functional posterior | response rank/conditioning 부족 시 no-go/upper-limit; prior-induced identifiability 금지 |

각 루프의 물리적 정의와 유도는 THEORY_AND_OBSERVABLES.md, 실제 source, likelihood, code, test 계약은 DATA_AND_SAMPLER_PLAN.md에 둔다. T6는 나머지 다섯 루프를 단일 scalar anomaly test로 합치는 것이 아니라, 동일 물리 parameter와 frame convention을 공유하는 integration layer다.

## 4. 공통 모델 계층

- M0: perturbed-FLRW baseline. Observer local boost, ordinary peculiar velocities, standard radiation transfer, foregrounds, selection, calibration and survey nuisances를 모두 허용한다.
- M1: M0 + intrinsic CMB dipole / large-scale dipolar-potential response. Dipole-only의 정확한 degeneracy가 조건부일 수 있으므로 second-order initial-condition/potential nuisance를 명시한다.
- M2: M1 + global matter-radiation tilt and redshift-dependent kinematic tensors (shear, vorticity, acceleration) with a declared congruence.
- M3-I: M2 parameter restricted to Bianchi I response and exact geometric relations.
- M3-II/VII0/...: qualified family transfer/template가 있는 경우에만 추가한다. 현재 Bianchi design pack의 11 family contract는 11개 full Einstein-Boltzmann solver가 구현됐다는 뜻이 아니다.

각 모델은 동일한 data vector, covariance support, foreground/selection nuisance, prior volume convention을 사용한다. 우선 single-probe posterior predictive check와 response rank를 통과한 뒤 joint sampler로 진행한다. AIC/BIC 또는 서로 다른 covariance의 chi-square를 단순 비교해 물리 해석을 결정하지 않는다.

## 5. 관측자료 취득 원칙

첫 순서는 기존 로컬 자료의 정확한 identity와 SHA256 inventory다. 이전 source catalogue는 옛 경로와 실행 당시 manifest를 기록하지만 현재 파일의 존재/무결성을 증명하지 않는다. 기존 파일을 덮어쓰거나 대량 재다운로드하지 않는다. DATA_AND_SAMPLER_PLAN.md에 우선순위·공식 출처·필요 auxiliary product를 기록했다.

관측 데이터는 Git에 넣지 않는다. Git에는 release identity, exact URL/DOI, byte size, SHA256, FITS header, row-order, mask/beam/bandpass, frame/unit, covariance identity, code commit, retrieval timestamp만 versioned manifest로 저장한다. 대용량 map, covariance, catalogue는 외부 data root에 보존한다.

## 6. Stop rule 및 paper gate

1. 먼저 exact data/response identity와 covariance를 고정한다. Row selection은 data vector와 covariance 양 축에 동일 적용해야 한다.
2. 모든 covariance에 대해 symmetry residual, Cholesky/positive-definiteness, condition number, eigenvalue floor, row-order binding을 검사한다. Covariance를 임의로 대칭화하거나 대각화해 실패를 감추지 않는다.
3. Whitened nuisance-projected response의 singular spectrum을 보고한다. Unsupported or nearly-null directions은 UNIDENTIFIED로 유지한다.
4. 실제 map/catalogue analysis 전에 injection/recovery 및 selection-preserving null coverage를 통과한다. Null simulations은 실제 관측을 대신하지 않고 sampling distribution/coverage를 평가한다.
5. 하나의 actual observable에 대해 posterior/credible region 또는 finite sharp upper bound를 확보해야 물리적 결과로 주장한다. Detection은 독립 채널의 일치와 nuisance sensitivity를 추가로 요구한다.
6. Bianchi family ranking은 family-specific forward response, source frame and transfer uncertainty까지 qualified된 경우에만 수행한다.
7. 실패는 theory no-go, data-quality blocker, numerical failure, implementation/runtime failure, source/permission blocker로 분류한다. 같은 원인의 반복 repair loop를 금지한다.
8. 한 번의 production pass와 한 번의 fresh adversarial review 후 결론을 고정한다. Review는 누락된 claim source, covariance/selection leak, rank mislabeling, data leakage만 본다. 새 scope를 자동 발굴하지 않는다.

## 7. 이번 실행에서 확인한 status

- GitHub 기준 research branch head는 PR #564 merge commit cab89d25af52a1b978a4da8c11eecdc25bb22759다. main은 별도이며 이 작업에서는 수정하지 않았다.
- 전체 PR API 목록 561개를 인벤토리했고, 과학 키워드 기준 71개 후보를 추렸다. 상세 claim audit은 #256/#257/#281/#306/#313/#310/#311/#314/#550/#557/#563/#564 등 핵심 계보에 집중했다. 이 숫자는 모든 561개 diff를 줄 단위로 재검토했다는 뜻이 아니다.
- Library 이론 자료: HTT_FIVE_THEORY_LOOPS (2026-10-26), HTT_physical_research_en (2026-10-25), HTT_METHOD_FOUNDATIONS_20261028, HTT_FOUR_GOALS_FIBRE_20261028, HTT_NOVELTY_STRATEGY_V15 등 확인.
- User-pinned THEOREMS.md at dfaf171c37f2636c942a99bf2b9803b57295ac14를 확인했다. 이는 theorem/method boundary와 current acceptance status를 구분하며, literature novelty를 주장하지 않는다.
- Project catalogue는 10.82GB SQLite asset index (57 compressed chunks)이며 관측 FITS 그 자체가 아니다.
- Wolfram symbolic check: full-sky STF2 fourth-moment normalization difference = 0.
- Native subagents: NOT_RUN. Native delegated research receipt는 생성하지 않았다.
- Runtime: actual data downloads, map/catalogue processing, Cobaya, MCMC/nested sampling, Einstein-Boltzmann evolution는 NOT_RUN.

## 8. 저장소 내 산출물

- RESEARCH_DAG.json: executable-intent DAG와 각 노드의 현재 gate.
- THEORY_AND_OBSERVABLES.md: conventions, derivations, response model, identifiability.
- DATA_AND_SAMPLER_PLAN.md: official source plan, acquisition priorities, covariance and Cobaya contracts.
- PR_LEGACY_AUDIT.md: history/PR/source inventory and claim ceiling.
- CLAIM_LEDGER.json: established/derived/candidate/unresolved/not-run decisions.
- LOCAL_AGENT_RESUME.md: existing local checkout에서 재개할 구체적 작업 prompt.

R38은 논문 제출이나 main merge가 아니다. Local agent가 exact source inventory 및 production computations를 수행한 후, 결과 receipt와 branch commit을 이 DAG에 연결한다.