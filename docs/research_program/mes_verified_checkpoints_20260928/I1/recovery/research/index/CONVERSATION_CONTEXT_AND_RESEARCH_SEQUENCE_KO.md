# 백업 범위와 대화 연결 기록

작성일: 2026-09-28. 이 문서는 이번 백업에서 작성한 색인이다. 원래 대화의 완전한 전사본이 아니다.

## 사용자가 요청한 범위

지금까지의 이 스레드의 모든 연구 내용에 대한 백업본. 맨 처음부터 마지막까지 전부 포함해야 한다.

## 현재 확인 가능한 계보

1. 초기 HTT / Planck MES 연구: 2026-08-26 최초 handoff, scalar MES/Planck 첫 관측, global irrep 및 morphology, tensor/tilt, PMG-WU와 78개 theorem 후보. 2026-08-30 원본 아카이브에 보존된 문서·코드·부분 대화 기록을 그대로 포함한다.
2. 2026-08-31 WU009 이론 dossier와 blocker ledger, Wolfram receipts, PR328 인계.
3. 2026-09-03~06 Paper A 초안·심사·frame repair·K2FE/K2FER1·K4/K5·T9 authority replay·T2 repair 및 로컬 반환.
4. 2026-09-07~08 M1 CMB, theory-only/physical-response/native-theory, adversarial review, 독립 저장소·history·MES/observed lineage 감사, 문헌 DB와 최초 직관 정식화.
5. 2026-09-09~16 카탈로그 탐색, 원문 취득 및 최종 선택, research input foundation, R9 통합 설계, theorem/CMB kinematics/redshift/relativistic optics/광학 사상 초안.
6. R10: PR468의 R9를 바탕으로 36-node DAG. c8bd214a 계획 게시, 48e77f8d 부분 실행 반환, 52ab95f2 MAIN 검토. 광선→복사장→STF 전단 fixture, mixed rank 1 대 physical STF rank 5, R9 영점–monopole null, CAS의 ambient grad 명시, client/pending 결속 차단.
7. 새 이론 루프 R1: 과거 평가를 전제로 삼지 않고 원래 MES 직관에서 재출발. 정확한 국소 전단 연산자, 조건부 잔차 집합, Bianchi I 끝점 광학 텐서와 응력 적분, morphology와 정규화.
8. 새 이론 루프 R2: 특정 Bianchi class 없이 전 운동학과 tilt, 정확한 국소 광학 역산 및 수송 약형, 공통 허용집합 정규화, tensor Q/F/Pi/G 및 likelihood. 현재 제공된 이 스레드 대화의 마지막 연구 결과다.

## 최신 연구 방향을 정한 사용자 원문 (가시 메시지 338)

여기에서는 위 작업과 별도로 이론적 연구 루프를 진행하자. 내 처음 직관에 대해 다시 새 질문을 던지고 현재까지 발전된 방법론도 다 잊고 과거의 부정적인 평가도 배제하고 바닥부터 시작해서 제일 원 동기를 살리는 방법에 대해 논의하고 싶어. 내 처음 생각은 MES theorem을 만족하는 weak anisotropy를 전제로 한다면 CMB observable들을 가지고 kinematic quantity들에 관측적 제약을 줄 수 있지 않을까 하는 것이었어. 그리고 부등식의 최대값을 분모로 잡고 실제 관측값을 분자로 놓아 퍼센트로 나타내면 "deviation percentage"를 해당 전제 하에 표현할 수 있다는 것이었어. 그런데 추후 연구에서 여기서 두 가지를 극복해야 함이 나타났지. 첫번째는 MES theorem의 강햔 전제조건을 만족하지 않는 경우에 대한 inequality들의 확장이고, 두번째는 scalar inequality만으로는 morphology의 정보를 너무 많이 잃어버린다는 것이었지. 그러나 이를 극복하기 위해서 실제 모든 anisotropic case들을 다루는 solver를 세우는 것은 너무나도 방대한 작업이고, 이미 관측된 값들을 가지고 할수있는 분석을 위해 수리물리/해석적 명제를 증명하려고 했고, 이를 구체적인 통계량과 연관지으려고 했어. 실제 dynamics에 대한 정보도 포함하되, numerical ode/pde evolution/boltzmann solver가 필요하지 않은 최선의 방법을 찾고있어. 이를 위해 선택한 것 중 하나가 바로 ellis의 책에 나와있는 relativistic optics이고, 위에 첨부한 문서가 그 첫 결과야. 그 밖에도 내가 기존에 구축한 통계량 (x,Q,Π,F,G_F)의 tensorized 승격된 버전을 동원하고 싶어. 이를 위한 연구 루프를 gpt 6 astra용 연구 스킬/하네스를 동원해 시행해줘. 현재 work thread에서 astra ultra mode가 활성화되어있어.

위 전사는 수식 문자 Π를 표시상 정규화했다. byte-identical 플랫폼 export가 아니다.

## 최신 범위를 정한 사용자 원문 (가시 메시지 349)

vigilode는 이제부터 필요하지 않아서 삭제했어. 그리고 model-independent한 결과, 또는 특정 bianchi class를 선택하지 않고 Lie algebra만 주어진 상태에서 유도할수있는 결과(가능하면 일반화된 결과), shear만이 아니라 모든 kinematical quantity (θ,σ_ab,ω_a,A_a) 및 tilt β_a (global tilt 또는 local boost 모두 가능)를 분석하고싶어. 이미 repo에는 shear 외의 다른 kinematical quantity에 대한 MES-style bound도 존재해. 그리고 궁극적으로 MES bound로 normalize해서 '일정한 기준을 세우고 dimensionless하게 만들어서 값 자체가 아니라 1 - σ_observed(C_ell) / σ_max(C_ell)같은 비율을 비교함으로서 "동일 관측조건 하에서 전제된 이론적 양으로부터의 차이"를 통한 shear이느냐 vorticity이느냐 등이 중요한게 아닌 유형과 무관하게 공평한 비교를 원했었어. 이제 지금은 tensor로 승격했고 redshift도(local boost vs. global tilt 비교를 위해 특별히 더) 고려하니까 일반화하면 T_{A_n}(a_{ell,m}^{X,Y},z,...)같은 양이 될거야. (A_n=a_1 a_2 ... a_n) 그리고 T_theory와 T_obseerved를 비교해서 likelihood를 세우고, 텐서화된 (Q,F,Π,G_F) 등을 가지고 이를 분석하는 툴로 쓰는거야. 이를 반영해서 한번더 연구루프를 수행해줘. 참고로 아직 repo 내 선행연구는 내가 언급한 MES bound 외에는 참고하지마.

위 전사는 LaTeX 수식 표기를 Unicode/plain text로 정규화했다. byte-identical 플랫폼 export가 아니다.

## 가시 메시지 323–355의 연결 색인 (요약)

- 323–328: R9 기준에 광학 12개 노드를 추가하고 PR470 게시. 과학 계약, T9 조건부 진단, 25개 파일 원격 대조 보고.
- 329–333: 반환 결과 검토. RC03/04/07의 범위, rank 불일치, 기준점 및 residual/CAS 조건을 명시. MAIN 검토 문서 게시.
- 334–337: native client worktree mismatch와 registered identity changed가 지속. VS Code 새 로컬 대화에서 실제 checkout 결속 확인 안내. 해당 실행 경로의 HOLD이며 일반 runtime 불가 판정이 아님.
- 338–344: R1 새 이론 연구 요청, MES 원전과 광학·통계 연결 유도, 검산·독립 검토.
- 345–348: 중단 후 R1 원본 35개 항목의 복구 확인 및 최종 전달.
- 349–355: R2 전 운동학 일반화, 정확산술 수송 대조, likelihood 기준점 오류 수정, V3 결과 전달.

완전한 대화 원문은 현재 컨텍스트에도, 기존 초기 아카이브에도 없다. 이 색인은 생략 구간을 복원했다고 주장하지 않는다.

## 연구 authority 구분

역사적 자료의 PASS/HOLD/철회/실패는 수정하지 않는다. 백업 무결성 확인은 과학 재검증이 아니다. R1/R2는 기존 HTT 경로와 분리해서 읽어야 하며, 사용자가 제한한 저장소 선행연구 참조 범위를 이 백업이 변경하지 않는다. VIGILODE는 재개 필수 의존성이 아니다. 같은 이름의 다른 스레드 R3 이후 문서는 이 백업의 최신 연구로 섞지 않는다.
