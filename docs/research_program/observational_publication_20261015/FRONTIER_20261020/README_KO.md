# 2026-10-20 solver-free 연구 재개

최신 변경은 새 PR 번호가 아니라 **draft #561에 추가된17개 커밋**이다. 조사 기준 HEAD는 `69870ee249cd98a869f35e442105d17c927d28fc`, 이전 게시 HEAD는 `1528ebd3c4ace48a561b9dcaa6d5f891121a22a5`다. [INTAKE.json](INTAKE.json)에 최신 PR 목록, 커밋 및 기존 CI 상태를 기록했다. 이 문서는 기존 실행의 독립 재현을 주장하지 않는다. 각 실행 보고서·검토 결과를 재사용하고 이번에 바뀐 이론·자료 경로·실행 지시만 검증한다.

원래 과학 DAG는 **17/42 completed_scoped, 직접 외부입력8개, 그 의존 노드17개**다. 여섯 논문의 `NOT_READY_TO_SUBMIT`과 기존 HOLD/UNKNOWN을 유지한다. 실행 완료된 데이터 작업과 원래 과학 acceptance의 완료를 구별한다.

## 재사용해야 하는 실제 성과

| 최근 실행 | 현재 확보한 근거 | 남은 조건 |
|---|---|---|
| HI–CF4 | 628개 대상의 결과·계보,627개 점수/1개UNKNOWN | 전체 parent targeting/detection/quality 법칙 |
| Pantheon–CF4·SH0ES | 1,701행 covariance,654 host association, 실제3,492행/47모수 사다리와37 host support | 정확한 SN contributor·교차조사 공동 보정·선택법칙 |
| Planck PR3 | 네604MB split-noise 제품, 원래 추정량 처리, beam archive 및100GHz E5 제한 응답 | 같은 처리의 신호·잡음·foreground·가중치선택 공동법칙과 통계량 coverage |
| Gaia·radio | Gaia1,614,173개 완전 표본, radio713개, frame projection, 공분산 상계 | 실제 spatial/NNR/calibration 공동오차와 비방사 물리 응답 |
| CF4 flow·공동 보정 | 수정 CF4++ 보간,97개 LP, 제한된 보정 quotient | grouped64 producer contract의SOURCE_CONFLICT, 절대 보정과 물리 사상 |
| SDSS source null | 10.643GB 원천 archive, 고정64개 box/observer fit | box 독립성·실제CF4 선택법칙은 자동 승계되지 않음 |
| 외부 transfer | 공식 legacy 온도 test pair, 단위비2725 및169열 | 편광 all-m·전역 이력 전체 atlas |

상세 수치·기존 실패·원래 사용량은 [기존 실행 재개점](../OPEN_INPUTS_20261018/EXECUTION_20261018/RESUME.md)과 [논문별 판정](../OPEN_INPUTS_20261018/EXECUTION_20261018/PUBLICATION_ASSESSMENT_KO.md)이 소유한다. 완료 캠페인을 다시 돌리지 않는다. 특히 Gaia 전체 스트림,64개SDSS fit,97개LP, 과거54history/432광학비교를 이번 작업의 테스트로 재사용 실행하지 않는다.

## 이번 연구의 소비 지점

- `theory/`: 같은 기준계에서 보상된 dust+radiation 모형의 해석적 시간 응답을 유도하고, local observer boost와 깊이 응답을 구별한다. 유한 대수·Lorentz·극한 검산만 사용한다. ODE solver를 만들거나 실행하지 않는다.
- `distance/`: CF4 작성자의 SN 생성 노트북/제한된 fixture와 최근 공동 보정–속도 forward model의 원전 계약을 확인한다. 공개 covariance를 한 번만 소비하는 조건부 대안을 구분한다.
- `cmb_astrometry/`: PR4 NPIPE의 실제 공개 A/B 경로, 서로 다른 픽셀 ordering, 고정 foreground·전처리 근사 조건을 조사한다. 공개 low-ell spectral likelihood와 all-m morphology를 구별한다.
- [관측자료](OBSERVATIONAL_DATA_KO.md), [개발 DAG](RESEARCH_DAG_KO.md), [자율 인계](HANDOFF_PROMPT_KO.md), [획득 manifest](ACQUISITION_MANIFEST.json)를 연결한다. 기존 `CONTINUATION_TASKS.json`의 D01–D08 상태를 실제 실행 기록에 맞춰 교정한다.

해석적 제한 모형의 시간 응답은 원래 V03의 전체 Einstein–Boltzmann 이력 승인과 다르다. 새로운 PR4 경로는 PR3 L03 입력을 이름만 바꿔 대체하지 않는다. 논문 원전의 redshift-only forward response와 완전한 광학 Doppler 응답도 같은 것으로 쓰지 않는다.

## 논문화 후보와 다음 결과

| 현재 가능한 기여 후보 | 추가 입증해야 할 것 |
|---|---|
| Mask/beam/고차 누출의 유한 응답·보정 quotient 방법론 | 원전 대비 실제 새 기여와 지정 estimator에서의 적용 범위 |
| 공유 보정·부분식별과 SDSS source-null 비교 | 과학 모수에 대한 공동 선택·오차법칙 또는 정당한 coverage 외부구간 |
| Gaia/radio의 제한된 공분산 envelope | 실제 marginal calibration·frame 제약; 주변 최악값을 공동 달성 가능값으로 취급하지 않음 |
| 보상된 다유체의 local/global 깊이 응답 사례 | 실제 관측의 각도·nuisance 투영 rank, 유효 redshift/작은 속도 범위, remainder와 source law |
| 공개 제품의 계보·처리 계약을 통한 재현 연구 | 동일 release의 입출력 완전성, 독립 재현, 신규성이 있는 과학적 귀결 |

이는 투고 승인 목록이 아니다. 특히 실제 검출 유의도, global tilt 측정, Bianchi family identification은 아직 확보되지 않았다. 다음 결과 목표는 새 원천을 고정한 calibration/velocity response의 rank 분석, PR4의 별도 release-specific 저차 관측 설계, 해석적 이력 모형의 실제 sky/depth nuisance quotient다. 방법론상 유효한 negative/partial-identification 결과도 원래 acceptance를 충족하면 성과로 기록한다.

## 새 물리·자료 결과

해석적 응답은 $\delta d_L/\bar d_L=\boldsymbol n\cdot[A(z)\boldsymbol\ell+h(z)\boldsymbol b]$, $h=1+z-zA$다. 보존된 이력을 포함하면 $h/A$의 미분이 $H\prime\chi/c$가 되어 이상적 radial design에서 local/global 두 열의 차이를 증명할 수 있다. 실제 sky·nuisance 투영과 물리 remainder는 별도다. [전체 유도](theory/THEORY.md), [그림](theory/history_response.png), [벡터 PDF](theory/history_response.pdf)를 제공한다.

CF4 전체계보의 일부인6개 source-claimed SN→host→group identity를 추출했다. 추가로 [NPIPE frame 조사](cmb_astrometry/FRAME_BINDING_ADDENDUM.md)는 공식 producer 코드가 Galactic/COSMO를 의도한다는 근거를 찾았다. 정확한 cache→PLA packaging 증거는 없으므로 탐색적 조건부 사용과 exact-product 확인을 구분한다.
