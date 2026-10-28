# HTT 출판 중심 관측연구 DAG: 여섯 독립 논문

## Current finite convergence route — 2026-10-28

Use [the report-first convergence plan](CONVERGENCE_20261028/README_KO.md) and [existing-session handoff](CONVERGENCE_20261028/HANDOFF_CURRENT_SESSION.md). Produce the initial report, four bounded physical-goal result updates, then refined final reports while completing existing executable work. Original42 and six-paper scientific acceptance remain unchanged. New adaptive frontier creation is disabled only for this finite release; existing packets, repair and resume paths remain authoritative.


작성 2026-10-15 KST · 활성 authority: PUBLICATION_DAG.json / schema htt.observational_six_paper_dag/1.

기본 전략은 단순하다. 하나의 거대 Bianchi+low-ell+CF4+posterior 프로그램을 각 분야의 독립적인 falsifiable 관측 논문 여섯 편으로 분리한다. 서로 재사용하는 수학·source·instrument 연산자는 공유하되, 관측 결론·통계법칙·관측 likelihood·독립적인 투고판정은 각각 둔다. 기존 PR533 및 2026-10-15 CF4 Schur와 Planck–MES 연구의 scoped 결과는 재사용한다. 원래 미커밋 작업 트리와 245개 PR canonical backlog를 수정하지 않으며, 본 프로그램은 publication-specific ACTIVE OVERLAY다.

## Publication portfolio

| Paper | Priority | Publishable-scoped question | First concrete task | Present gate |
|---|---:|---|---|---|
| P2 Low-ell morphology & anomaly | 1 | 실제 Planck T/E/B anomaly 형태가 올바른 공동 null/choice selection 이후 남는가 | L01 | end-to-end null/exchangeability, look-elsewhere |
| P3 Redshift-dependent Hubble | 2 | 관측 H_W(z,n)에서 cosmic velocity와 진짜 방향 팽창을 구별 가능한가 | H01 | CF4 selection/shared calibration, current competing papers |
| P1 x,F,Pi,Q,G_F statistical method | 3 | 관측 posterior/identified sets에 원래 함수들을 사상하여 undefined mass까지 보존 가능한가 | S01 | 실제 admissible observation law 또는 엄밀한 partial-identification |
| P4 Local boost vs global tilt | 4 | 태양계/observer boost와 물질–복사 global tilt를 관측상 분리 가능한가 | V01 | distinct physical history/source-frame transfer |
| P6 Kinematical measurement | 5 | sigma_ab, omega_a, A_a, beta_a의 무엇이 실제 측정 가능하고 어떤 상한인가 | K01 | optical/common-congruence transfer, nonradial channel |
| P5 Bianchi identification | 6 | 가족·모드의 physical T/E/B likelihood 동치류를 가를 수 있는가 | B01 | verified native polarized all-m atlas and matched Planck likelihood |

**우선순위는 현재 자료/방법 경로의 수행 가능성과 신규성 위험을 고려한 실행순서이지 저널 게재확률의 수치예측이 아니다.** P1과 P2를 먼저 작성하든 P3를 병렬로 수행하든 논문은 각각 독립적인 본문/그림/제출 gate를 가진다. P1에서 실제 물리적 총 signed x posterior는 P4–P6 physical response and same-congruence source가 있어야만 승격 가능하며, 관측 부분식별 방법 논문은 그때까지 scope를 제한해 진행한다.

## DAG 핵심 의존성

~~~mermaid
flowchart LR
    E0["E0 PR533 archive"] --> X["X01/X02/X03 source, novelty, selection"]
    E0 --> E1["E1 CF4 Schur 915d8bfd"]
    E1 --> E2["E2 Planck MES 398dc461"]
    E0 --> E3["E3 PR066/PR521 functionals"]
    E3 --> S["P1 statistics: S01→S06"]
    E2 --> L["P2 low-ell: L01→L06"]
    E1 --> H["P3 H(z,n): H01→H06"]
    E1 --> V["P4 boost/tilt: V01→V06"]
    E2 --> V
    E2 --> B["P5 Bianchi: B01→B05"]
    E1 --> K["P6 kinematics: K01→K06"]
    E2 --> K
    H --> V
    H --> K
    L --> B
    L --> V
    V --> K
    X --> S
    X --> L
    X --> H
    X --> B
~~~

이 그림은 논문 간 필요한 과학적 결과 공유를 요약한다. 모든 실제 Task간 간선은 PUBLICATION_DAG.json depends_on만 authoritative하다. 어떤 노드가 외부 transfer 때문에 막혀도 다른 논문의 READY 노드나 동일 논문의 독립 기초 과제를 중단하지 않는다.

## 현재 바로 수행 가능한 9개 노드

| Ready | 실질 산출물 | 당장 실행 시 필요한 연구행동 |
|---|---|---|
| X01 | source and overlap graph | raw CF4 group/Planck fits/SH0ES/FFP source IDs와 release masks/covariance를 재검사, 동일 sky와 독립 source를 구별 |
| X02 | novelty comparator | 각 논문 당 주요 선행과 계산 estimand, 실제 통계법칙, 제공 데이터의 차이를 정확히 적는다 |
| X03 | selection history / claim ledger | mask, tracer, ell, depth, statistic, tail choice를 기존 post-hoc과 앞으로 고정할 검증으로 분리 |
| L01 | Planck T/E/B transfer | NSIDE2048→64 ordering, common mask, spin E/B, beam/mode leakage의 실제 forward injection |
| H01 | H_W(z,n) estimator | CF4 group의 실제 radial windows와 velocity/hubble angular leakage kernel를 계산하고 단위·극한 검산 |
| S01 | functional-domain code | x_C signed, Q anchor, F ceiling, Pi undefined mass, G_F floor·depth에 대한 테스트와 adapter 작성 |
| V01 | typed frame/boost | beta_RO, beta_RM, beta_MO, peculiar bulk B_W 및 rapidity와 v/c 혼동 방지 |
| K01 | physical kinematics sensitivity | 1+3 tensor, n^i omega_ij n^j=0, apparent STF2≠geometry sigma의 data-operator contract |
| B01 | admitted external atlas inventory | Bianchi I–IX 11 branches + exceptional VI_-1/9, physical all-m E/B coverage, sign/IC/source completeness 조사 |

실제 READY 목록은 python3 scripts/htt_publication_dag.py --ready 명령에서 계산한다. 위 표는 2026-10-15 초기 체크포인트 기준이며 별도 백그라운드 실행을 의미하지 않는다.

## 조건부로 진척할 수 있는 각 논문의 핵심 결과

### P1. x,F,Pi,Q,G_F

S01에서 정확한 타입/정의역을 고정한 뒤 S02는 현재 source-conditioned Planck·CF4 결과를 동일 draws에서 functional image로 재사상한다. x_C의 shear·vorticity·tilt·curvature 중 실측되지 않은 sector는 undefined로 보존한다. S03은 anchor family·selection/denominator/floor에 따른 posterior interval의 변화를 보고한다. S04에서 진짜 관측법칙이나 rigorously defined outer identified set을 확보해야 P1의 관측 응용 신규성 gate를 통과한다. 완전한 physical x posterior 없이도 부분식별 방법논문은 가능하지만, synthetic toy/old Bayes factor만으로 논문 제출을 승인하지 않는다.

주요 그림: signed x/sector profile with known-vs-unknown mass; Pi(t) lower/upper curves; G_F depth contrast and floor sensitivity. F4 bolometric angular moment는 F와 다른 함수이므로 별도 표기로 유지한다.

### P2. Low-ell morphology & anomaly

L01은 이미 계산한 FFP10 mask leakage(6≤ell≤8 projected norm)와 9개 Planck 공통 하늘 operator를 출발점으로 하되, L03의 qualified full null bank가 나오기 전에는 새로운 anomaly p를 제시하지 않는다. L02는 Q/O octupole/quadrupole tensor orbit, aligned axes, parity, high-mode/global-choice family를 등록하고 역사적 p=.039를 retrospective로 분류한다. L04의 MC rank와 L05의 source nuisance robustness가 제출 핵심이다. 존재하는 Planck VII (2020)과 무엇을 실제로 추가 측정하는지 확실히 비교한다.

주요 그림: actual tensor morphology on shared sky, masked/beam residuals, matched joint null rank/selected scan correction. Anomaly가 사라지는 결과도 충분히 calibrated되고 새 attribution을 제공하면 가치가 있다.

### P3. Redshift-dependent Hubble factor

H01/H03은 현재 CF4 35,970 group의 observed source H_eff directional response와 window/overlap covariance를 먼저 계산한다. H02는 reported distance calibration/selection, method error correlations, peculiar velocity flow law를 실제 source 자료/heldout mocks로 고정해야 한다. H04는 H(z), D_H(z), STF Q_H(z), q(z)의 competing smooth or binned model을 동일 관측법칙으로 비교한다. H05는 Boubel 2024/25, Duangchan et al 2026, Salzano et al 2026와 null CF4 비교를 반드시 수행한다. 결과가 physical geometry H=Theta/3이 아닌 survey-dependent H_eff라면 그렇게 출판한다.

주요 그림: H_eff(z,sky) with joint radial covariance; velocity/bulk models and source-method leaveout; anisotropic-vs-isotropic injection recovery. 단일 z-shell dipole 재측정만으로는 novelty 미달이다.

### P4. Local boost vs global tilt

V01/V02는 Solar/observer dipole/finite Lorentz 효과를 실제 Planck processing response로 구현하며, CF4 velocity estimator의 B_W와 물리적 beta_RM의 차이를 명시한다. V03의 별도 global-history source transport가 없다면 endpoint boost 신호를 global tilt로 복제하지 않는다. V04는 full nuisance-quotiented singular values와 error margin을 계산하여 식별/비식별 여부를 실제 observation law에서 결정한다. V05는 동일 source covariance 및 calibrated injections를 갖춘 경우에만 posterior odds/likelihood comparison을 수행한다. 처음부터 nonzero global tilt claim을 요구하지 않는다.

주요 그림: beta sector response singular vectors, depth/spectral discrimination; null and injection recovery.

### P5. Bianchi identification

B01은 모드·타입·orientation 동치성 및 source가 실제 구현된 branch를 조사한다. B02 native physical polarized transfer를 검증하지 못하면 B03/B04 family evidence를 실행하지 않는다. 외부 source atlas를 가져와 맞는 부분부터 subset paper를 만들 수 있도록 설계했다. 온도 morphology만 맞고 polarization 때문에 제외되는 historical templates를 physical identification으로 되살리지 않는다. Saadeh et al. 2016 full degrees-of-freedom constraints보다 의미 있는 새 physics 또는 genuinely new equivalence inference가 필요하다.

주요 그림: family-equivalence/Gram matrix, Planck T/E/B posterior predictive, heldout family confusion/injection recovery. 무리한 all-11 claims 대신 verified subset and degeneracy reporting이 대안이다.

### P6. Beyond-FLRW kinematical quantities

K01/K02는 먼저 실제 radial data에서 무엇을 측정할 수 없는지 수학적으로 정확히 판정하고, CF4 apparent STF2의 식별공간을 보존한다. K03의 kSZ, CMB polarization, proper-motion/optical response를 실제 source와 연결하기 전에는 omega_a, A_a 또는 beta_a posterior를 구성하지 않는다. K04/K05는 동일한 geometry/matter congruence, independent source calibration, combined covariance 및 validated transport를 만족한 sector만 추정하고 나머지는 빈틈을 0으로 채우지 않는다. 식별 가능한 shear combination의 신뢰영역과 omega/acceleration의 no-information bounds 자체가 새로운 실자료 결과일 수 있다.

주요 그림: response/nullspace by tensor irreducible sector, observational identified sets with physically allowed priors, actual source-window robustness.

## Canonical and historical DAG relationships

- Existing 245-card docs/codex_handoff/pr_backlog.json is a historical canonical PR backlog and is NOT overwritten, reclassified completed, or falsely merged.
- Published PR533 solver-free PLAN/SF nodes and PR532 observational reboot RB nodes are inherited exactly within their original conditional scopes.
- Prior local, **untracked**, docs/research_program/theory_obs_application_20261015/loop7_typed_defect/NEXT_RESEARCH_DAG.json is an observed source with SHA-256 8b1b6374...; it is not silently replaced on disk.
- 915d8bfd CF4 and 398dc461 Planck MES scientific results are live ancestor commits of this new branch, but remain conditional, not publication admissions.
- Proposed PR-HTT-PUBLICATION-P1..P6 are logical paper cards only, NOT six new GitHub PRs. Further branches shall be scoped to actual executed source/analysis tasks.

## Run, completion and claim policy

Use python3 scripts/htt_publication_dag.py --validate to validate all 42 nodes and 6 terminals; --ready for the nine executable tasks; --paper P3 for one-paper gate; --task H01 for a self-contained packet; --blocked for seven typed missing-input nodes. --export generates deterministic READY_QUEUE.json and does NOT schedule background work. Update a task state from pending to completed_scoped only after the precise source/result/test evidence exists and is read back. This is a finite DAG: one result+verification pass per task, then move to a genuinely runnable sibling. Background native jobs/subagents are capabilities, not mandatory claims.

**Publication decision:** Six potential independent papers; NONE is currently ready to submit. Manuscript writing, a real release-matched observational result, simulations with appropriate error coverage, prior-art novelty, and independent review are all required. Nothing in this DAG implicitly authorizes merging main, journal submission or suppressing a negative scientific finding.
