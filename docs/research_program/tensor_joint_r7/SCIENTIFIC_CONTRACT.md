# R7 scientific contract

**Scope:** 수학/물리/통계 이론과 구현 설계. Production 구현, CAS, 합성자료·실자료 분석의 실행 주체는 워크스테이션 Local Codex다. 이 계약의 `SPECIFIED`는 실행 성공을 뜻하지 않는다.

## 1. 추론 대상과 규약

- 계량 `(-,+,+,+)`. 천구 `n`은 관측자로부터 소스를 향하는 outward 방향. `beta_o=v_o/c`는 무차원 local observer boost.
- 조화계수는 실수 orthonormal basis, `integral Y_a Y_b dOmega=delta_ab`. 온도 단위는 K, C_l는 K². FITS 단위는 헤더·제품 규약에서 명시 변환하고 표준편차로 추측하지 않는다.
- `T_2(n)=Q_ab n_a n_b`, `T_3(n)=O_abc n_a n_b n_c`; Q는 STF2, O는 STF3. `Q:Q=75 C_2/(8 pi)`, `O:O=245 C_3/(8 pi)`. Frobenius 축약은 대칭 성분 다중도를 포함한다.
- 물리 shear와 vorticity는 지정한 관측자 congruence의 proper-time rate, 단위 s⁻¹. `Theta=3H>0`; `S_ab=sigma_ab/Theta`, `W_ab=omega_ab/Theta`. `s2=S:S/2`, `w2=W:W/2`를 본 캠페인의 dimensionless norm invariants로 고정한다. 기존 `Sigma²`, `W²`, `x_C`와 연결할 때는 기존 정의의 H/Theta 및 1/2 계수를 명시하는 변환기를 사용한다.
- 관측 Q와 MIO 정책 정규화 점수 `mathcal Q`는 다른 타입이다. `x_C`는 부호 있는 comparator, `Pi`는 임계 초과확률, `F`는 정의역이 검증된 점유율, `G_F`는 같은 물리 상태에서 계산한 깊이 차이다.
- geometry, observer velocity, matter tilt, stochastic perturbation, instrumental/calibration nuisance를 별도 변수로 유지한다. Source-response 행렬을 velocity Jacobian으로 이름만 바꾸지 않는다.

## 2. 공동 실험

물리 모수 `theta`, 공통 하늘/LSS 실현 `Z`, 공유 보정·선택 변수 `eta`, 제품별 입력 `Y_s`에 대해

\[
p(Y\mid\theta,M)=\int p(Z,\eta\mid\theta,M)\,p(Y\mid Z,\eta,\theta,M)\,dZ\,d\eta.
\]

조건부 독립이 정당화된 센서·객체 블록에만 두 번째 인자를 곱으로 분해한다. 같은 원자료에서 얻은 carrier·불변량·추정값은 이 likelihood의 결정론적 함수이며 독립 likelihood 항을 추가하지 않는다. 관측 하늘의 사후표본과 새로운 null 하늘 실현은 다른 sample type이다.

**실자료 기본선:** PR3 SMICA 및 제품 대응이 검증된 signal/noise pool; CF4 raw distance/group/calibration 제품; DESI 허용된 raw catalogue와 random/selection products; JWST CCHP/SH0ES host 제품. 이름만으로 실제 존재·호환성을 인정하지 않는다. 각 데이터셋의 이용 가능성은 INTAKE가 판정한다. 보조·대체·보정·독립 구현 비교에 쓸 전체 보유 자산은 [OWNED_ASSETS.md](OWNED_ASSETS.md)의 제품별 경로를 따른다.

PR3의 기존 signal 999개와 noise 300개는 999개 독립 null을 주지 않는다. 재사용 없는 고정 300쌍이 최대 기본 후보이며, 이것도 자동 교환가능성을 보장하지 않는다. ID·보정·joint law가 일치한 고정 pool만 rank용으로 사용한다. 표본 하나가 계산 미해결이면 삭제하지 않고 해당 pool의 최종 rank를 미해결로 기록한다. 300개가 유효할 때 최소 rank는 `1/301`이다.

CF4·DESI·JWST의 raw/corrected/merged 제품은 estimator target, frame, row/group IDs, selection law, covariance support가 호환될 때만 같은 likelihood에 편입한다. Covariance나 selection을 추정할 근거가 없으면 `SCENARIO_ONLY` 또는 해당 자료를 뺀 분석으로 간다. 자료가 없다는 사실을 영점 관측으로 입력하지 않는다.

## 3. 물리 가설과 nuisance 법칙은 별개 축

| 물리 모델 | 정의 | 가장 가까운 경쟁자 | 허용 결론 |
|---|---|---|---|
| P0 | FLRW stochastic sky/LSS + local observer + 제품 nuisance | foreground/calibration extension | 모형 적합성·선언된 anomaly 검정 |
| P1 | P0 + 관측공간의 coherent low-ell/depth templates | P0/systematics | 관측 패턴의 추가 필요성; geometry 명칭 부여 안 함 |
| P2 | R3 LRS counterstreaming Bianchi I + collisionless photons + Lambda | local-only 또는 non-LRS templates | 보존·광학 benchmark, 해당 모형의 조건부 비교 |
| P3 | 지원 모드가 확인된 외부 near-isotropic Bianchi transfer + stochastic sky | P0/P1/지원되는 다른 모드 | external-transfer-conditional 모형 제약 |

P2/P3의 공통 모수·초기조건·광학 응답이 정의되지 않은 자료끼리는 공동 물리 fit을 하지 않는다. 각자의 부분 분석과 그 불일치를 보고한다. 공개 AniLoS/AniCLASS가 지원하지 않는 scalar/initial-condition branch를 성공 output으로 채우지 않는다. 새로운 일반 native solver의 작성은 이 캠페인의 선행조건이 아니다.

각 물리 모형에 대해 high-source H0(무제한 결정론), H1(진폭 제한), H2(확률모형), H3(추가 관측모드로 제약)를 비교한다. H0에서 비식별이라는 결론은 H2/H3의 자동 기각이 아니다. H2/H3의 좁은 구간은 H0의 모형 독립 결과가 아니다. 가정 강건성은 p의 최솟값이나 confidence set의 교집합으로 만들지 않는다.

## 4. Tensorized MES의 세 사용 수준

1. **관측 tensor 수준:** Q/O, 방향 moments, 외부축과의 축약, full covariance, chart status. 항상 실행 가능한 최소 과학 단위.
2. **조건부 physical set:** 명시된 복사장 moment/derivative 관계와 범위 안에서 `X=(S,W,tilt,curvature, radiation derivatives)`를 유지한다. 관측 confidence region의 역상과 물리 제약을 함께 취하고, 모든 불변량을 같은 X에서 계산한다.
3. **모형별 likelihood:** 검증된 동역학/transfer가 미분·원격장·거리 응답을 공급할 때만 해당 물리 모수 posterior/confidence를 만든다.

하나의 CMB sky는 (2)의 모든 관측자·시공간 미분 envelope를 제공하지 않는다. 이 입력이 없으면 무조건적 shear/vorticity 상한을 만들지 않고 envelope 계수에 따른 조건부 곡면을 보고한다. `B_sigma>B_omega` 같은 별개 상한의 순서를 물리 허용조건으로 강제하지 않는다.

## 5. 선택과 오류 예산

주 분석은 full Q/O 관측 uncertainty와 선언된 joint set다. `f_B`, signed Krylov packet, multipole-vector 정렬, power는 동시 진단/비교 대상이다. SO(3) 공동 회전은 불변량 null을 생성하지 않는다. 외부 방향·mask는 실제 관측 프레임에 남긴다.

이미 공개 하늘과 과거 분석을 본 연구이므로 이 재계획은 독립 blind discovery의 사전등록이라고 부르지 않는다. 실행 전 analysis lock은 재현성을 확보한다. 명시된 유한 선택 family를 전체 null row에 대칭 적용한 보정과, 전체 joint confidence set의 동시 coverage를 사용한다. 기록되지 않은 과거 탐색 전체까지 보정했다고 주장하지 않는다.

오차는 입력/처리 불확실성, 확률적 측정 오차, 유한 시뮬레이션 오차, 수치 오차, 모형/transfer 오차를 분리한다. 결정론적 rank certificate의 양의 slack은 실제 포함성이 먼저 성립하면 사후 보고 가능하다. 오차 반경을 줄여 억지로 인증하지 않는다.

## 6. 완료 조건

각 분기는 수식과 구현의 단위·부호·정의역 → 독립 oracle → 합성 실험 → 실제 제품 검사 → 추론으로 진행한다. 모든 종료는 `process_status`, `scientific_outcome`, `scope`, `evidence`를 갖는다. 계산 실패는 가설 기각으로 변환하지 않는다. 모든 독립 분기가 정리되면 SYNTHESIS는 성공·기각·부분 식별·자료 한계를 함께 서술한다. 자료가 없는 경우에도 설계/비식별 정리는 끝낼 수 있지만 관측적 결론을 대신 만들어 내지 않는다.
