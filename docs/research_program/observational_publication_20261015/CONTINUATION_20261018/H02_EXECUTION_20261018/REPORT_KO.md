# H02 실제 CF4 중심·보정 식별집합·방법 중첩 실행

2026-10-18. Owner `htt`; scope: selected-source apparent angular regression and conditional calibration sensitivity; claim status `CONDITIONAL` / diagnostic-only. Transfer source `none`; no physical inference. Requested worker `gpt-6.1-sol/high`, observed runtime model/effort `UNKNOWN`. 기존 branch `research/htt-sixpaper-goals-robustness-20261018`, 시작 HEAD `1e095a2749cce9b28e45aac043a82218c21f84e5`. Parent가 별도 독립검토와 publication을 담당한다. 이 문서는 H02 admission이나 제출 승인이 아니다.

## 실제로 새로 계산한 결과

기존 P3의 “방법별 중심 부재”를 해소했다. 원본 35,970개 그룹 NPZ에서 네 partition의 8개 apparent 계수, 전체 centered Gram/RHS 및 working covariance를 계산했다. Base window와 H03의 동일한 네 Gaussian 창 `(z_c=.025,.04,.06,.08; width=.012)`을 사용해 20개의 fit block 및 방법별 40×40 cross-window covariance를 저장했다. 원 H02의 네 partition count와 각 Gram의 최소·최대 고유값 8개가 모두 재현되었다.

Raw CDS table3/4와 selected NPZ의 group ID, CMB redshift, J2000 방향, DMzp, e_DMzp를 대조했다. selected ID 집합은 raw 38,053개 그룹 중 `.01<=z_CMB<=.1`에 든 전체 그룹 집합과 정확히 같다. **이것은 분석 cut의 재현이지 관측 completeness 또는 true selection law의 복원이 아니다.**

Base-window의 실제 계수 중심은 다음과 같다. 단위 mag, 열은 고정된 raw Cartesian basis다. FP/TF/SN/OTHER는 pooled DMzp catalogue의 **서로 겹치지 않는 partition**이며 순수한 독립 방법별 거리측정 표본이 아니다.

| partition | n | nx | ny | nz | nx²−nz² | ny²−nz² | 2nxny | 2nxnz | 2nynz |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FP | 26916 | −.044360 | .012700 | .065272 | .058521 | .028613 | .013644 | −.054162 | −.006174 |
| TF | 7614 | .055583 | −.022876 | .104163 | −.008871 | −.012189 | −.034222 | −.055658 | −.027437 |
| SN | 700 | .040222 | −.000363 | .077826 | .041583 | −.010320 | −.016841 | −.025004 | .012566 |
| OTHER | 740 | .017485 | .007305 | .124760 | .029054 | .025193 | −.047033 | −.019500 | −.057331 |

## Estimand와 working-law 경계

`y_i=DMzp_i−25−5 log10(c z_CMB,i)`, `c=299792.458 km/s`의 angular coefficient를 fit했다. 수치 H reference 변경은 각 partition/window에서 profile하는 intercept에만 영향을 준다. `X=(nx,ny,nz,nx²−nz²,ny²−nz²,2nxny,2nxnz,2nynz)`, 방향은 J2000 equatorial이다. 이 y는 apparent distance–redshift residual이며 measured expansion scalar, peculiar velocity, geometry shear가 아니다. H03와 cohort/windows는 같지만 H03의 `cz ~ d*(H+D.n+n.Q.n)` estimand와 단위는 다르므로 계수값을 직접 합치지 않는다.

각 창의 weight는 `w_i=k_i/e_DMzp,i²`이다. Weighted-mean으로 X와 y를 center하고 `G=XcᵀWXc`, `r=XcᵀWyc`, `b=G⁻¹r`를 저장한다. Slope map `A=G⁻¹XcᵀW`를 사용해 `C_ww'=A_w diag(e_DMzp²) A_w'ᵀ`를 계산했다. 부드러운 창에서는 `C_ww != G_w⁻¹`; 이 차이를 독립 SVD test로 확인한다. Base에서는 `C=G⁻¹`이다. 네 covariance block은 PSD이고 최소 고유값은 FP `2.5783e−7`, TF `5.4626e−7`, SN `6.5812e−7`, OTHER `4.9478e−7`이다. Base와 z=.025 창의 같은 좌표 상관은 FP .589–.807, TF .961–.969, SN .739–.849, OTHER .931–.960이다. 중첩 창을 독립 표본으로 세지 않는다.

여기서 diagonal error law는 **선언된 working law**다. 실제 selection, correlated calibration, common velocity field covariance는 UNKNOWN이다. Disjoint partition 사이 zero covariance도 이 working law에만 해당한다. Residual model error 또는 조건부 평균 bias가 존재하면 centered-error 가정 자체가 실패할 수 있다. Reported error를 fit residual RMS로 재보정하거나 tau prior를 empirical covariance로 바꾸지 않았다.

## 관측 중심을 넣은 deterministic calibration 집합

각 고정 좌표 j와 창 w에서 `b_mw=theta_w+eta+gamma_m+epsilon_mw`로 두었다. `|gamma_m|<=delta`는 방법별 상대 angular calibration bound이고 **같은 gamma_m를 모든 창에 공유**한다. eta는 방법·창 모두에 공통인 angular calibration이다. 방법 중첩으로 eta를 anchor할 수 없다.

5 windows ×4 methods ×8 predeclared coordinates =160 comparisons 전체를 포함한다. Gaussian centered marginals의 임계값은 `Phi⁻¹(1−.05/320)`이고 variance-only는 `sqrt(160/.05)`다. Union bound이므로 window/method 독립성을 요구하지 않는다. 단, marginal variance가 위 working covariance로 bound된다는 가정은 별도다. 720개 개별창 interval rows와, same-gamma coupling을 실제로 강제하는 HiGHS LP의 16개 contrast/law 결과 및 64개 delta scenario를 저장했다. LP의 theta_w는 깊이별로 자유이며 eta와 합쳐진 좌표다. LP는 각 contrast error/calibration box 안에서의 coordinate projection이며 correlated-error ellipsoid 자체를 사용한 confidence region은 아니다.

Gaussian working law에서 `nx`의 joint relative delta 최소값은 **.01946163556665044 mag**다. 나머지 7좌표는 delta=0에서 호환된다. Variance-only에서는 모든 좌표가 delta=0에서 호환된다. 이 값은 해당 모형에서 관측 중심을 호환시키기 위한 bound이고 **실제 calibration 오차 측정치가 아니다**.

예를 들어 base `nx`에서 delta=.02의 개별창 outer interval은 `[.0099562061,.0110329350] mag`, delta=.05에서는 `[−.0200437939,.0410329350] mag`다. 표본과 오차모형·delta 선택에 민감하다. 공집합은 common-estimand/calibration/error-law 조합에 대한 모형 불일치이지 cosmology 단독 반증이 아니다. 연속적으로 관측 후 선택한 모든 방향에 대한 동시 보장도 아니다.

eta가 무제한이면 physical theta_w의 각 좌표는 **unbounded**다. 외부에서 `|eta_j|<=rho`를 정당화하면 theta_w+eta의 nonempty endpoint를 rho만큼 넓혀 theta_w의 outer interval을 얻는다. 이번 자료는 empirical rho를 제공하지 않는다. 절대 zero-point scalar shift는 intercept 제거로 사라지지만 공통 angular shift는 사라지지 않는다. 두 경우를 별도 test했다.

## 실제 같은 그룹의 방법 중첩과 genealogy

CDS table3의 method presence/count/modulus sidecar를 1PGC로 join했다. 작은 수의 presence는 숨기지 않았다.

| released methods | raw parent overlap | selected overlap |
|---|---:|---:|
| FP–TF | 682 | 638 |
| SNIA–FP | 196 | 182 |
| SNIA–TF | 281 | 209 |
| CAL–SNIA | 42 | 7 |
| CAL–FP | 7 | 3 |
| CAL–TF | 88 | 5 |

CAL이 있는 그룹은 parent 336개, selected 11개다. 따라서 selected high-z partition만으로 absolute anchor genealogy를 재학습할 수 없다. Source paper의 요약 수와 이 release의 group count/overlap을 강제 일치시키지 않았다.

Table2의 55,877 galaxy rows를 1PGC로 연결했다. Distinct 1PGC는 38,035개이며 그중 12개는 table3/4 group release에 없다. 이들을 임의 재할당하지 않았다. Selected groups에는 52,810개 galaxy rows가 연결된다. Galaxy-per-group quantile `[min,median,p90,p99,max]=[1,1,2,9,278]`이다. Parent raw rows와 selected arrays는 기존 로컬 경로에 그대로 두고, 이 패킷에는 aggregate만 썼다.

SNIA–FP, SNIA–TF, FP–TF의 **동일 그룹 내 released modulus 차이**로 constant offset 대 8-shape 모델의 heldout 예측을 기술적으로 비교했다. SHA256(group-ID) mod5로 whole group을 holdout했다. Training/test를 measurement별로 나누지 않는다. Weights는 `1/(e_left²+e_right²)`라는 working diagnostic weights이며 true difference variance라는 주장은 없다.

| pair | train/test groups | constant heldout WRMS | angular heldout WRMS |
|---|---:|---:|---:|
| SNIA–FP | 149 /33 | .303796 mag | .306344 mag |
| SNIA–TF | 162 /47 | .324443 mag | .357259 mag |
| FP–TF | 529 /109 | .475214 mag | .471794 mag |

Angular model은 두 SNIA pair에서 오히려 악화된다. FP–TF의 작은 개선을 검정 유의도나 power로 해석하지 않는다. 이 거리들은 이미 release 전체를 사용한 공동 calibration의 산물이므로, 이 holdout은 **upstream calibration으로부터 독립이 아니다**. Selected sample 내 차이/과적합 진단이며 H02의 independent calibration validation acceptance를 충족시키지 않는다.

## 원전 확인으로 좁힌 다음 입력

[Tully et al. 2023, §§IV, X, Appendix](https://arxiv.org/html/2209.11238v2)는 group overlap을 통한 공동 zero-point merging과 6dFGSv의 selection-dependent normalization 및 simulation recalibration을 설명한다. 따라서 같은 그룹의 table3 distances를 independent raw recalibration으로 취급할 수 없다. 본 패킷의 release-level 중첩과 residual은 그 genealogy를 진단하는 자료이며 그보다 상류의 selection normalizer를 대신하지 않는다.

[Kourkchi et al. 2020, §§II, IV](https://arxiv.org/html/2009.00733)는 H I/photometry/inclination 품질 선택 뒤의 10,737개 data catalogue와 9,792개 distance catalogue를 구별한다. [공식 CDS J/ApJ/902/145](https://cdsarc.cds.unistra.fr/viz-bin/cat/J/ApJ/902/145)의 table1/table4와 [EDD column description](https://edd.ifa.hawaii.edu/describe_columns.php?table=kcf4tfdistpaper)이 다음 PGC join 대상이다. 이 table1은 모든 미검출/탈락 대상의 true parent selection probability를 제공하는 complete parent로 자동 인정되지 않는다. 이번 unit에서는 이 추가 raw catalog를 내려받거나 selection likelihood를 재구축하지 않았다. Browser의 CDS ReadMe open은 inaccessible, EDD page는 HTTP502였고 arXiv primary text는 성공했다. 검색으로 확인한 EDD metadata상 DMbest는 optical을 우선하므로, pooled TF distance를 W1-only measurement로 이름만 바꾸지 않는다.

H02를 재개하려면 (i) upstream survey/sample→galaxy PGC→group 1PGC의 contributor/version join, rejected/missing-target와 품질 cut 및 distance-dependent normalization, (ii) shared zero-point/calibration posterior 또는 허용 가능한 covariance/bounds와 relative/angular/common 성분의 구분, (iii) joint velocity error model, (iv) 해당 selection·grouping·calibration을 동일하게 통과한 source null simulations가 필요하다. 이번 계산은 (i)의 공개 final-group 연결 일부와 실제 중심·충분통계만 해소했다. Calibration gauge의 외부 angular anchor는 여전히 없다.

## 검증, claim audit와 acceptance

실행:

```bash
.venv/bin/python docs/research_program/observational_publication_20261015/CONTINUATION_20261018/H02_EXECUTION_20261018/h02_actual.py
.venv/bin/python -m unittest discover -s docs/research_program/observational_publication_20261015/CONTINUATION_20261018/H02_EXECUTION_20261018 -p 'test_h02_actual.py' -v
.venv/bin/python docs/research_program/observational_publication_20261015/CONTINUATION_20261018/H02_EXECUTION_20261018/plot_h02_actual.py
```

Runner exit0; tests **13 PASS**, no skip/failure; plotting exit0. Tests include independent full-intercept SVD, Gaussian-modulus distance mean-bias identity, zero-point/constant-source controls, shared angular gauge, nontrivial window covariance, scalar sharp-box threshold, coupled-window incompatibility and constructed LP witness. These synthetic controls validate implementation; source physical nulls are NOT_RUN. Stdout retained in RUN_RECEIPT.json. Python `.venv/bin/python`3.12.3; NumPy2.5.4, SciPy1.18.1, Matplotlib3.11.2. PNGs visually inspected. No installer/environment modification, ODE/solver execution, whole expensive experiment, canonical DAG/status edit, commit/push occurred in this worker.

| claim / acceptance component | status | evidence / remaining blocker |
|---|---|---|
| actual selected source centers/full G/RHS | IMPLEMENTED; source executed | JSON, exact NPZ pin and original spectra replay |
| overlapping-window working covariance | CONDITIONAL; tested | full40×40 blocks per partition, independent SVD/map controls |
| shared-method calibration identified set | CONDITIONAL; tested | 160-comparison marginal-law box, common-gamma LP; eta unbounded |
| method/group overlap | actual descriptive source result | table2/3/4 aggregate genealogy |
| independent heldout calibration fit | NOT_SATISFIED | released measurements already jointly calibrated upstream |
| full correlated selection/velocity likelihood | UNKNOWN | missing source laws/covariance |
| reproduce source selection/calibration null simulations | NOT_RUN | source-qualified mocks/input pipeline missing |
| H02 original node acceptance | **HOLD** | no completion or downstream physical admission |

Scientific risk/kill-switch: stop any p-value, posterior, physical theta/shear/tilt or native-family promotion unless the above external inputs qualify the law and independent review accepts the corresponding scope. Parent must obtain a fresh read-only review of this actual candidate before publication/admission. Physical inference and submission remain unperformed.
