# 잠재적 출판 기여와 추가 연구로 얻을 결과

평가 기준은 재현되는 비자명한 결과, 원전 대비 기여, 관측·추정 대상의 명확성, 필요한 오차/선택법칙의 정당화, 독립 검토, 그리고 주장에 맞는 실자료 그림이다. 데이터의 존재·다운로드·테스트 통과만으로 논문 준비도를 통과하지 않는다. 여섯 원래 논문은 모두 **NOT_READY_TO_SUBMIT**이다. 아래의 '후보'는 출판 가능성을 검토할 가치가 있다는 뜻이며, 신규성이나 투고 가능성을 인증하지 않는다.

## A. 지금까지 실제로 확보한 기여 후보

| 후보 | 실제 방법/결과 | 가장 자연스러운 논문 위치 | 현재 강점과 부족 |
|---|---|---|---|
| A1 공통처리·support에 민감한 저다중극 형태 통계 | 원래 Planck full/HM/OE finite regression, spin2 response/remainder, L02 parity-aware tensor family,8쌍 IQU noise 민감도. +5%잡음에서 B계수 에너지 최대10.21265%변화 | P2의 방법·재현성 중심 본문 후보 | 현재 가장 구체적인 관측 처리 결과 묶음. 맵의5종/성분을 독립하늘로 세지 않음. 물리anomaly/PTE 주장을 하려면 L03coverage 필요 |
| A2 CF4 중첩창·공동보정에 따른 apparent anisotropy의 부분식별 | 실제20개method/window fit, 전체working covariance, common-gamma LP, 같은그룹holdout,2048coupled draws의소거민감도 | P3, P1의조건부 통계 결과 후보 | 실제자료 수치가 있다. 실제 selection/공통보정/velocity법칙으로 coverage를 검증하기 전 physicalshear/tilt로 승격 불가 |
| A3 두 처리 경로 사이 sharp 공통앵커 기하 | 동일anchor에서 얻은scalar summaries로원래/매칭 추정각55.6426–73.7213도, 최선비음수배율 residual≥82.5533% | P2의처리비교 방법/보조정리 | 명시된공통anchor와E/B직교분해 아래sharp. 표준Gram기하에대한구체적적용; 우주론적신규성 별도 |
| A4 공통angular calibration의관측설계 | 이번 finite nuisance quotient/잔차ball bound,실제6maser방향의dipole quotient rank0,3개의prospective방향 추가시전체rank9 | P3의식별가능성·설계절 또는독립methods note후보 | 수치witness·증명·독립검사. 새GR/no-go정리 아님. 실제같은대상 보정차와methodgamma불확실성 추가필요 |
| A5 실제source-defined 국소boost응답 | 원래native-child support에맞춘유한localLorentz응답과full/half증분검사, V02완료 | P4의방법절 | endpoint local실험을완료. globalhistorytransfer와분리검증 결과는아직없음 |
| A6 CF4 기여표의조건부관측실패 자료 연결 | 기존TF 최종표외에이번GBT628대상의적합385/기타22/혼동29/비검출192,table4membership일치 | P3 선택모형의실자료입력·재현성부록 | 비검출을오차500으로넣는오류방지, selection분모일부확보. 집계자체만으로독립논문기여는약함 |
| A7 외부자료적격성·frame/covariance감사 | Gaia4756기존결과,이번713radio/CRF3입력경로; Pantheon1701행 covariance실제비대칭/중복CID연결 | P6/P3의자료·제한절 | pipeline실패가능성을구체화. 계정없이받을수있다는사실이나routine품질검사만으로sciencepaper완료불가 |

A3의 정확한 원본은 [P2/REPORT.md](../CONTINUATION_20261018/P2/REPORT.md)와 [생성 JSON](../CONTINUATION_20261018/P2/results/PLANCK_ANCHOR_GEOMETRY_20261018.json)이다. 이번 intake HEAD에서 보고서를 확인했고 이전 생성결과를 재사용했다.

원문·실행증거는 이전 CONTINUATION_20261018의각EXECUTION폴더, 이번theory/REPORT_KO.md, distance/HI_COHORT_RESULT.json, PANTHEON_INPUT_RESULT.json에 있다. 오래된 PR본문의14/42값과 현재17/42를혼동하지않는다.

## B. 추가 분석으로 얻을 수 있는 결과

| 목표 결과 | 구체적실험 / 필요한입력 | 완료판단 | 연결 |
|---|---|---|---|
| B1 실제관측실패가보이는범위에서selection sensitivity | GBT628을TF10,737/9,792행→CF4PGC/1PGC에연결. whole-target/group holdout. 검출과linewidth적합조건을분리 | 발표된628대상조건부확률로만모형정의. parenttargeting확률미확보를범위로보존 | H02→H04/P3 |
| B2 SN거리법과CF4의상관된방향·depth비교 | Pantheon+전체covariance, SN/calibrator교차정체성, releasedpeculiarvelocity와적용전후분석 | duplicate/alias·공동보정을명시한jointmodel; 서로독립검증으로부르지않음 | H02,H04,H05,K04 |
| B3 공통angular anchor의식별집합 | 같은거리정의의geometric vsoptical잔차와method별gamma를jointfit. 실제anchor covariance/bounds사용 | quotient식별가능성, 충분한방향, finite-z/방법보정예산아래nontrivialinterval | S02,S04,H02 |
| B4 공개splitnoise로확장한공통하늘null | HM1/HM2/OE1/OE2 ID00000부터원래estimator로처리; fixedweights·beam provenance·공통seed관계확인 | matching/foreground/selectioncoverage를충족한범위만L03. CMBsplit부재는noise로대체하지않음 | L03→L04→L05 |
| B5 retrospective통계군에대한전역보정 | L02통계family/선택전과정고정, qualified독립simulation단위로omnibus/maximumrank calibration | 계수96차원을8표본covariance로역행렬하지않음; tailresolution과MCuncertainty보고 | P2 |
| B6 Gaia+radio비방사운동의관측가능부분공간 | fullCRF3 propermotions+2×2cov, 공간상관민감도, frame nuisanceprojector,radio교차표본 | 프레임정의가제거한mode와남은VSH모드를분리; cosmologicalresponse별도 | K03/K05/P6 |
| B7 flow모형대체시apparent field의변화 | CF4grouped/수정CF4++격자와현재자료의공통기원명시,52단위변환및interpolation검사 | descriptivecontrol/조건부모형비교, 독립관측검증/공분산draw아님 | H04,K04 |
| B8 localboost대globalhistory의식별rank/오차 | 완료V02와이미계산된적격V03외부transfer를동일frame/processing으로비교 | 실제독립응답열과nuisancequotient, priordependent불확실성보고 | P4 |
| B9 Bianchi restrictedfamily의morphology compatibility | parameter/IC/units/frame가있는기존T/E/Ball-m숫자atlas 및L03null | familyequivalence/rotation, subsetcoverage/priors검증; nativefamilyID승격없음 | P5 |
| B10 typedfunctionals의실자료법칙 | 자격있는common-state집합을signedx/Q/F/Pi/G_F로pushforward | undefinedmass/양의분모/sector조건보존, qualifiednarrowerimage가능성검토 | P1,P6 |

B1–B7의자료취득·관측처리·부분식별 계산은 native solver 없이진행할수있다. B8–B10의물리응답은이미계산된외부payload나추가물리가정을필요로한다. 사용자는이세션에서solver를만들거나ODE를풀지않도록요청했으므로해당구축은계획에넣지않았다.

## 원전과의 차이, 중복 출판 방지

- Planck2018 IV(1807.06208)는componentseparation·FFP10신호/잡음과잔차한계를이미다룬다. VII(1906.02552)는isotropy/statistics, VIII(1807.06210)는lensing및HMsimulation/beam조건을제공한다. 우리의후보는repo의정확한finite estimator/공통support/선택절차에대한새로운실자료검사이지기존anomaly재발표가아니다.
- CF4(Tully2023, DOI10.3847/1538-4357/ac94d8)와Kourkchi2020, Dupuy2021의catalogue및calibration은기존기여다. 새로운기여를주장하려면upstreamgenealogy·공동보정·관측실패를함께모형화한결과의실제증분을보여야한다.
- Boubel(2412.14607),Stiskalek(2509.14997),Kalbouneh(2510.02510)의방향거리/flow분석과직접비교가필요하다. 우리의apparentcoefficient를새로운우주비등방검출로바꾸지않는다.
- Lovell1963partialregression,기본선형대수,calibrationgauge는기지방법이다. 이번anchor계산의기여는source-specific설계와명시적witness/정밀도목표다. 단독methods논문은기존방법보다추가유용성과일반화된실자료case를입증해야한다.
- Saadeh2016의제한Bianchi모드결과와AniCLASS는물리transfer원전이다. 공개영상/기존posteriorchain은새로운all-matlas가아니다. 알려진exactBianchiIoptics나localLorentz변환자체의신규성을주장하지않는다.

같은수치/figure를6개논문에중복핵심결과로배치하지않는다. P2에는observerprocessing, P3에는거리selection/calibration, P1에는qualifiedfunctionalimage, P4에는local/globalresponse, P5에는externalatlascompatibility, P6에는observationalkernel/commonstate의독립기여를요구한다. 그기준에미달하면논문수를유지하려고주장을부풀리지말고결과와실패이유를보고한다.
