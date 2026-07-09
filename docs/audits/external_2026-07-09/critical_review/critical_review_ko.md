# 제공 연구에 대한 비판적 심사 보고서

## 0. 총평

판정은 **방법론 논문으로는 major revision**, **관측 우주론 결과 논문으로는 현재 형태에서 reject에 가깝다**야. 핵심 아이디어인 “상세 Bianchi/비등방 기하를 성급히 지정하지 않고, 관측 반응공간과 null 방향을 먼저 분리한다”는 방향은 좋다. 특히 signed comparator, partial identification, posterior/diagnostic 분리, manifest 기반 fail-closed 정책은 연구 프로그램으로서 가치가 있다.

하지만 현재 원고는 아직 “증거를 낸 물리 결과”가 아니라 “결과를 내기 위한 형식·감사 프레임워크”다. 수학 정리들은 대체로 유용한 방향이지만, 일부 정리는 가정이 약하거나 문장이 과하다. 데이터 그림들은 대부분 diagnostic-only로 잘 격리되어 있으나, selection/covariance/null/pipeline 재현성이 부족해서 물리적 결론으로 승격할 수 없다.

## 1. 수학적·논리적 정확성

### 강점

1. **vorticity normalization 수정은 방향이 맞다.**
   \(W^2=\omega_{ab}\omega^{ab}/(6H^2)=\omega_a\omega^a/(3H^2)\)로 통일하고, 기존 \(\omega_a\omega^a/H^2\)가 정확히 3배였다는 결함을 인정한 점은 좋다. 이 수정은 shear normalization과 평행하게 맞춰져 있다.

2. **signed comparator를 norm이 아니라 coordinate로 둔 점은 옳다.**
   \[
   x_C=\Sigma^2-W^2+\Omega_{\rm tilt}+\Omega_{k,{\rm aniso}}
   \]
   라고 두고, 이것이 비음수가 아니며 완전한 spacetime invariant도 아니라고 명시한 건 핵심 방어선이다. 이걸 “anisotropy amplitude”로 팔면 바로 틀리는데, 보고서는 그 위험을 상당히 의식하고 있다.

3. **row-space/null-space 구분은 논리적으로 중요하다.**
   관측 반응 \(R\)의 rank가 4보다 작으면 \(g\) 전체가 아니라 \(R\)의 row-space projection만 갱신된다는 주장은 맞다. 특히 vorticity가 radial contraction에서 사라진다는 명제는 대칭/반대칭 contraction으로 바로 증명된다.

4. **partial identification 전환은 좋은 수정이다.**
   결측 성분을 0으로 채우지 않고 \([x_C^-,x_C^+]\)를 보고하거나 EMPTY/UNBOUNDED/CEILING-UNFIT 상태를 내는 구조는 통계적으로 훨씬 정직하다. 동봉 실험 코드도 보고서의 예시 \(\Sigma^2=0.12,\Omega_{\rm tilt}=0.03,U_W=0.04,U_k=0.02\)에서 \([0.11,0.17]\)를 재현한다.

### 치명적 또는 major 수정이 필요한 점

#### 1. \(\Omega_{k,{\rm aniso}}\)의 부호와 cone 정의가 불명확하다

보고서는 네 성분을 “nonnegative component magnitudes”라고 부르지만, 동시에
\[
\Omega_{k,{\rm aniso}}=\Omega_k-\Omega_{k,{\rm ref}}
\]
로 둔다. 이 차이는 일반적으로 음수가 될 수 있다. 이 문제가 해결되지 않으면 다음 세 가지가 동시에 흔들린다.

- \(g\in C_{\rm phys}\)를 nonnegative cone으로 둔 P26류 정리.
- signed comparator 계수 \(c=(1,-1,1,1)\)의 해석.
- curvature null ceiling이 upper endpoint에만 들어간다는 주장.

수정 권고: 둘 중 하나로 고정해야 한다.

- **선택 A:** \(g_k\)를 진짜 signed coordinate로 인정하고 \(C_{\rm phys}\)에서 \(g_k\ge 0\) 가정을 제거한다. 이 경우 P26/P31의 endpoint 분해식을 다시 써야 한다.
- **선택 B:** \(g_k\)를 비음수 curvature-anisotropy magnitude로 재정의하고, parent constraint에서 나오는 signed scalar residual과 분리한다. 이 경우 \(x_C=c^Tg\)가 parent identity의 단순 gradient라는 표현은 약해진다.

#### 2. parent constraint의 domain이 좁게 명시되어야 한다

1+3 Gauss/Friedmann constraint 자체는 합리적이지만, vorticity가 있는 congruence에서 \({}^{3}R\)의 의미는 “전역 spacelike hypersurface의 scalar curvature”가 아니라 local rest-space/projected curvature 성격을 갖는다. 보고서는 frame을 조심한다고 하지만, 이 부분은 정리의 domain에 직접 박아야 한다.

수정 권고: parent identity 앞에 “single registered congruence, projected rest-space curvature convention, no silent frame mixing, residual terms explicitly registered”를 정리 가정으로 넣어라. 그리고 \(H\), \(\Theta\), \(\mu\), \(p\), \(\beta\)가 같은 event/branch/congruence에서 평가되는지 명시해라.

#### 3. P31 “identified-set sharpness”는 물리적 sharpness가 아니다

P31은 추상 cone/box 모델에서는 맞을 수 있다. 하지만 “PSD second-moment cone이 null-sector magnitude를 모두 실현한다”는 논리는 tilt second moment에는 자연스럽지만, shear/vorticity/curvature ceiling을 실제 Einstein constraint/evolution/energy condition까지 만족하는 spacetime 구성으로 실현한다는 뜻은 아니다.

수정 권고: P31 제목을 “Sharpness in the registered convex component model”로 낮춰라. “physical configuration”이라는 표현은 “component-level admissible configuration”으로 바꿔라. full GR solution sharpness를 주장하려면 별도의 constraint-solving theorem이 필요하다.

#### 4. P36의 strict inclusion 문장이 너무 강하다

보고서는 joint feasible \(G_F=N/D\) interval이 naive quotient보다 작고, \(c_N,c_D\ne0\), \(S\) nondegenerate이면 strict라고 말한다. 동봉 코드의 `gf_joint_interval` 실험은 반례를 준다.

반례:
\[
N(s)=2+s,\quad D(s)=5-s,\quad s\in[0,1].
\]
여기서 \(c_N=1\), \(c_D=-1\)로 둘 다 0이 아니고 \(S\)도 nondegenerate다. 그런데 joint interval과 naive interval이 둘 다 \([0.4,0.75]\)로 같다. 즉 “strict whenever”는 틀렸다.

수정 권고: “strict whenever”를 버리고, “strict unless numerator and denominator extremizers are compatible on the same feasible point” 같은 호환성 조건으로 바꿔라. 이건 작은 문장 문제가 아니라 정리 문장의 참/거짓 문제라서 반드시 고쳐야 한다.

#### 5. P35 coverage theorem은 regularity 조건이 부족하다

Imbens–Manski endpoint correction을 도입한 방향은 좋다. 하지만 현재 서술은 endpoint estimator가 같은 Gaussian reachable noise를 공유하고 null-box width가 deterministic일 때의 좋은 경우에 가깝다. 실제 파이프라인에서는 다음이 들어온다.

- covariance estimated from simulations,
- nonlinear transfer/nuisance projection,
- active-set changes at cone/box boundary,
- selected threshold/bin/look-elsewhere,
- low-\(\ell\) non-Gaussian single-sky effects.

수정 권고: theorem을 세 층으로 나눠라.

1. Gaussian known-covariance linear theorem.
2. Estimated covariance theorem: Hartlap 또는 Sellentin–Heavens 보정 포함.
3. Nonsmooth endpoint theorem: directional differentiability 또는 simulation/bootstrap calibration 필요.

## 2. 물리적 해석

### 강점

프레임 분리를 강조한 점은 매우 좋다. local observer boost, homogeneous matter tilt, electron frame, CMB frame을 섞지 말라는 경고는 실제 우주론 논의에서 중요하다. 또한 low-rank response가 detailed geometry를 식별하지 못한다는 결론도 물리적으로 건전하다.

### 약점

1. **\(\Omega_{\rm tilt}\)는 energy-density excess일 뿐 anisotropic stress tensor를 닫지 않는다.**
   보고서는 이 점을 P11/P12에서 인식하고 있지만, 데이터 그림 D23처럼 “Omega_tilt data coordinate”가 보이면 독자가 물리적 matter tilt 검출로 오해할 수 있다. label을 “bulk-flow-derived kinematic proxy”로 낮춰야 한다.

2. **K6 curl/shear diagnostic은 vorticity posterior가 아니다.**
   보고서가 reconstruction-conditioned structural no-go라고 조심하긴 한다. 그래도 figure title과 본문에서 “vorticity channel” 표현이 보이면 실제 spacetime vorticity 제약처럼 읽힐 수 있다. constrained realization, transverse velocity, spin-2 response가 없으면 vorticity inference가 아니라 reconstruction diagnostic이다.

3. **Bianchi V response formula는 constraint algebra일 뿐 dynamics가 아니다.**
   보고서도 이 점을 인정한다. 출판 원고에서는 Bianchi family 이름을 본문 전면에서 더 줄이고 “conditional response toy”로 내려야 한다.

4. **curvature sector는 아직 no-channel이다.**
   \(\Omega_k\) 또는 \(\Omega_{k,{\rm aniso}}\)가 comparator에 들어가지만, 현재 leading-order response가 없다고 되어 있다. 그러면 data-facing comparator point estimate는 원칙적으로 금지되어야 한다. 이건 잘 지켜졌지만, 초록/결론에서 더 세게 말해야 한다.

## 3. 통계 방법론 및 데이터 해석 건전성

### 강점

- diagnostic layer와 HTT posterior/evidence layer를 분리한 건 매우 좋다.
- e-value/Markov calibration을 descriptive exceedance와 분리한 점도 좋다.
- EMPTY/UNBOUNDED/CEILING-UNFIT 상태를 둔 fail-closed 설계는 좋은 통계 엔지니어링이다.
- 동봉 manifest는 각 그림을 diagnostic_only로 격리하고, posterior odds/p-value/family identification 금지를 반복해서 박아둔다.

### major 문제

#### 1. 동봉 zip은 재현성 패키지가 아니다

내 `audit_package_integrity.py` 결과:

- zip 내부 파일: 64개.
- `MANIFEST.json`의 `input_hashes`: 60개.
- 그 60개 중 zip 안에 실제로 포함된 참조 입력: 0개.
- null hash path: 6개.
- figure PNG와 sidecar는 24/24 존재.
- sidecar의 input arrays/scripts도 zip 내부에는 0개.
- sidecar 24개 모두 `diagnostic_only`.
- sidecar 24개 모두 `matched_nulls_not_bound_for_inference`, `full_covariance_not_bound_for_likelihood` failed gate를 갖는다.

즉 이 패키지는 “보고서+렌더링 산출물+hash manifest”이지 “제3자가 rerun 가능한 재현 패키지”가 아니다. 심사자가 원 저장소와 raw/prepared data, generator script, lockfile, 환경을 함께 받지 않으면 핵심 수치와 그림을 재생성할 수 없다.

수정 권고: publication supplement에는 최소한 아래를 포함해야 한다.

- generator scripts,
- small synthetic fixtures,
- exact conda/uv/pip lockfile,
- raw-data download recipe와 checksums,
- prepared arrays의 provenance,
- `make reproduce-report` 단일 명령,
- CI 로그 또는 artifact hash verification.

#### 2. 데이터 그림은 “observed diagnostic”이지 통계 결론이 아니다

D01–D24는 시각적으로 도움이 되지만, 대부분은 null likelihood, joint covariance, selection function, transfer model이 없다. 현재 보고서가 이 점을 인정하고 있긴 하나, figure gallery가 길어서 독자가 “많은 데이터가 이미 같은 결론을 지지한다”고 착각할 위험이 있다.

수정 권고: figure gallery를 appendix로 내리고 본문에는 “왜 아직 inference가 아닌가” 표를 먼저 둬라. 각 figure에는 claim tier와 failed gate를 caption에 붙여라.

#### 3. DESI/CF4 해석은 selection/covariance가 결정적이다

DESI NGC–SGC asymmetry, tracer handoff, BGS target map은 random catalog, angular mask, radial selection, fiber assignment, survey window가 없으면 물리적 dipole/asymmetry로 해석하기 어렵다. CF4 bulk/apex/radial sign transition은 Malmquist bias, grouping, distance indicator heterogeneity, correlated velocity field covariance에 민감하다.

수정 권고: DESI는 data-random estimator와 window-convolved null을 먼저 붙여라. CF4는 hierarchical mock 또는 at least correlated-field mock with selection을 붙여라. bootstrap p16–p84는 descriptive band로만 두고 p-value처럼 말하지 마라.

#### 4. multiple testing/look-elsewhere를 명시해야 한다

K1 max-scan, low-\(\ell\) axes, shell apex track, depth windows, tracer/cap/redshift bins은 모두 선택 자유도가 있다. e-value finite-cover가 장점이 되려면 cover, weights, thresholds가 data-independent로 predeclared되어야 한다.

수정 권고: 모든 scan/threshold/window에 대해 registry를 만들고, “predeclared”, “exploratory”, “post-hoc”를 분리해라.

## 4. 독창성 및 기여 가능성

독창성은 “새로운 우주론 검출”이 아니라 다음 조합에 있다.

1. signed FLRW-departure comparator를 component semantics와 함께 정의.
2. unobserved/null components를 identified set으로 처리.
3. diagnostic object와 posterior/evidence object를 분리.
4. response-rank theorem으로 geometry overclaim을 방지.
5. MES/full-covariance ceiling과 no-result status를 결합.
6. 오래된 family labels를 evidence ranking이 아니라 response class ledger로 재활용.

각 요소는 부분적으로 기존 문헌에 뿌리가 있다. 따라서 원고의 novelty claim은 “new physics result”보다 “integrated identifiability-first audit/inference architecture for anisotropic-cosmology diagnostics”로 쓰는 게 맞다.

## 5. 출판가능성

### 현재 형태의 판정

- **Physical Review D / JCAP급 관측 우주론 결과 논문:** 현재는 어렵다. posterior, likelihood, validated null, transfer, selection-corrected data analysis가 없다.
- **Methods/software/reproducibility paper:** major revision 후 가능성이 있다.
- **Repository technical report:** 현재 형태로도 의미가 있다. 다만 theorem wording과 reproducibility package는 고쳐야 한다.

### 출판 전략

가장 현실적인 길은 두 편으로 나누는 것이다.

1. **Methods paper:** signed comparator, partial identification, response-rank/null semantics, e-value/IM endpoint calibration, manifest/fail-closed architecture. 관측 데이터는 toy 또는 diagnostic appendix로만.
2. **Data paper:** K1/K5/K6 중 하나만 골라서 selection, covariance, null, posterior 또는 calibrated e-value까지 완결.

한 편에 모든 것을 넣으면 논문이 “framework + proof ledger + figure atlas + future plan”으로 너무 넓어져서 심사자가 핵심 기여를 놓친다.

## 6. 구체적 수정 권고

### P0: 반드시 고쳐야 하는 것

1. \(\Omega_{k,{\rm aniso}}\)의 signed/nonnegative status를 재정의.
2. P36 strict inclusion 문장 수정. 현재 문장은 반례가 있다.
3. P31 sharpness를 full physical sharpness로 읽히지 않게 낮춤.
4. zip/reproducibility package에 실제 generator code와 minimal fixtures 포함.
5. 모든 current-data figure caption에 `diagnostic_only`, failed gates, null/covariance status를 노출.
6. “current data pass”가 inference가 아님을 초록과 결론에 명시.

### P1: major revision 안에 넣을 것

1. P35 theorem을 known covariance / estimated covariance / nonsmooth endpoint로 분리.
2. K1 covariance에는 Hartlap/Sellentin–Heavens뿐 아니라 finite simulation uncertainty를 e-value/null calibration 전체로 전파.
3. DESI random/mask/window gate 추가.
4. CF4 selection/Malmquist/grouping/correlated mocks gate 추가.
5. response matrix \(R\)를 figure D23 수준의 proxy가 아니라 실제 observable-to-component map으로 표준화.
6. theorem ledger의 DER/COND 기준을 엄격화: 외부 계수 imported, toy response, synthetic witness는 모두 COND 또는 REGISTERED_EXTERNAL로 표기.

### P2: 논문 품질 개선

1. 초록을 줄이고 “무엇을 주장하지 않는가”를 더 앞에 배치.
2. 24개 그림을 appendix로 보내고 본문에는 4–6개만 남김.
3. 표기 충돌 제거: \(x_C^+\) endpoint, \([x_C]_+\) positive part, \(\Omega_k\) sign, \({}^{3}R\) convention.
4. external literature context에 실제 citation list와 비교표 추가.
5. theorem proof는 “assumptions / statement / proof / failure modes / executable test” 형식으로 통일.

## 7. 동봉 수치 실험 결과 요약

`outputs/experiment_results.json`에 실행 결과가 들어 있다.

1. **Identified set:** 보고서 예시 \([0.11,0.17]\) 재현. UNBOUNDED, CEILING-UNFIT, EMPTY 상태도 작동.
2. **Imbens–Manski coverage:** width가 0에 가까울 때 naive one-sided endpoint interval coverage가 약 0.896으로 떨어지고, IM/projection은 약 0.949를 유지한다. 보고서 방향을 지지한다.
3. **Rank/prior exposure:** null column의 independent prior marginal은 posterior와 같고 KL=0. coupled prior에서는 KL>0이 되지만 prior-driven update다.
4. **GF interval:** generic case에서는 joint interval이 naive보다 좁지만, \(c_N,c_D\ne0\)이어도 equality가 되는 반례가 있다. P36 문장 수정 필요.
5. **Hartlap bias:** \(N_{sim}=300,m=20\)에서 raw precision trace inflation이 약 1.076이고 Hartlap correction 후 약 1.001로 돌아온다. finite simulation covariance 보정 요구는 타당하다.

## 8. 최종 판정

이 연구는 “물리 결과”보다 “과잉해석을 방지하는 수학·통계 인프라”로 보면 꽤 가치가 있다. 하지만 그 가치를 살리려면 논문이 더 겸손하고 더 엄밀해야 한다. 가장 위험한 부분은 데이터 그림이 아니라, 정리 문장 일부가 실제 가정보다 강하게 쓰인 점과, 재현성 패키지가 아직 rerunnable하지 않은 점이다. 이 둘을 고치면 methods paper로 갈 수 있다. 고치지 않으면 심사자는 “좋은 안전장치를 말하지만 정작 스스로도 과한 문장을 쓴다”고 볼 가능성이 높다.
