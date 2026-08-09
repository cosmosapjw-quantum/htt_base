# 하네스 정렬 · 게이트 해제 프로토콜 · 실데이터 재실행 캠페인 — 한국어 요약

**패키지:** `HARNESS_GATE_REDO_CAMPAIGN_20260802.md` (영어 본문, 4부) · `gate_disposition_and_redo_campaign.yaml` (harness-consumable 미러) · **감사 기준:** HEAD `7214ef7` (PR-248~275 merged) · **작성:** 2026-08-02

---

## 0. 모든 것의 순서를 정하는 단 하나의 발견

`AGENTS.md:145`: **"연속 2개의 assurance-only PR 이후에는 governance 확장을 멈추고, 다음 PR은 반드시 명명된 하류 과학 역량·데이터 실행/통합·실험·해석 가능한 결과를 내야 한다."**

PR-268~275는 **연속 8개의 assurance/proof/governance PR**이다 — registry v3, Pillar-T/S 증명, 4축 CAS, blind synthetic, 데이터를 0/6 admit한 preflight, proof atlas. 데이터 위 과학 결과는 하나도 없다. repo 자신의 brake가 6개 PR째 열려 있다.

이것은 그 작업에 대한 비판이 아니다 — 타입 토대가 이제 완성·기계검증되었기에 다음 이동이 안전한 것이다. 이것은 **순서 판정**이다: **올바른 다음 작업 단위는 또 다른 게이트/레지스트리/증명 카드가 아니라 제4부의 재실행 캠페인이다.** 하네스 정렬(2부)과 게이트 해제 프로토콜(3부)은 최소 활성화 보정 — stale 상태 수리와 해제 *프로토콜*이지 governance 확장이 아니며, 각 항목은 캠페인을 직접 막는 재현된 결함으로 정당화된다.

---

## 제1부 — 텐서 업그레이드 반영 감사

**판정: 충실히 반영, 이탈한 곳은 방어 가능한 hardening.** 오라클은 byte-exact로 착륙(proposal과 `tensor_foundations_oracle.py`의 diff 공백, TF-01~12 전부), 2-pillar registry는 hash-bound로 `theorem_signatures_v3.py`가 로드, proof atlas(PR-275)는 2-pillar를 3축 구조로 일반화. 오너는 제안한 PR-259~265를 넘어 PR-266~275를 추가했고, 여러 곳에서 이탈했는데 감사 결과 **방어 가능한 hardening** — 특히 *보수적인* 것 하나: catalogue-v3의 4축 CAS가 통과한 뒤에도 `generic_orbit_separation_status`를 `UNPROVEN`으로 유지하고 승격을 금지하는 CAS 의무(`vt_t8_global_separation_not_promoted`)를 추가했다. 내가 제안했다면 허용했을 승격을 오너가 막은 것.

**남은 6개 gap** (전부 작고, 전부 특정 greenfield 실데이터 분석의 선결조건이라 닫는 것이 governance가 아니라 과학 역량 작업):
1. **`WEAKLY_IDENTIFIED`가 런타임 게이트에 미배선** — 런타임 `SourceSeparationGateStatus`(`open_set_response_classes.py:76-81`)에 멤버 자체가 없고 `NOT_APPLICABLE`가 그 자리를 차지, `statistical_foundations.py:64`의 enum은 런타임 호출처 0. (개념 자체는 오라클이 명명·계산함 `tensor_foundations_oracle.py:984,1009` — gap은 런타임 배선이지 아이디어가 아님.) 프로덕션에선 full-rank·작은 principal angle 셀이 여전히 `SUM_ONLY`로 감. G8 차단.
2. **catalogue-v3 생성에 Jacobian-rank(9/12/15) 수용검사 미적용** — 오라클 안에만 존재.
3. **`AnisotropyTypeReport`에 `uncovered_directions` 누락** — G7의 정직-기권 절반 차단.
4. **DepthPath에 역마팅게일/Doob 객체 미결합** — G4의 공짜 calibration 차단.
5. **parity-sign 결합이 종속 케이스를 수행 대신 거부** — arbitrary-dependence e-value merge 미배선(보수적이나 교차-rung 검정력 미사용).
6. **(H2) 추정기 P-equivariance 감사 부재** — caller 주장 boolean. G3 전 실행 필요.

→ 6개를 별도 assurance PR이 아니라 **Wave R0/R1에 접어 넣어라**(각각 greenfield 선결조건이므로 brake 하에서 과학 작업으로 카운트됨).

## 제2부 — 하네스 정렬

하네스는 대체로 깨끗하다(`AGENTS.md`, `.codex/`, `harness_templates/`, `prompts/` 무결). stale는 신규 에이전트가 **먼저** 읽는 몇 표면과 HEAD에 뒤처진 생성 산출물 둘에 집중. 각 편집은 방지하는 재현 실패를 명시(`AGENTS.md:144` 준수).

- **H1 `CLAUDE.md` §1(L23)·§5(L55-60):** §1이 `x_C`를 *the* comparator로 제시(PR-248/249가 `LegacyProjectionReport`로 강등, forbidden에 claim-tier promotion 포함). → x_C를 BC1 legacy projection으로 재표기, primary는 `JointAnisotropyState`/functional family로. *방지 실패:* CLAUDE.md 먼저 읽은 에이전트가 pre-typed 그림을 재도출하고 x_C를 primary로 재수출.
- **H2 `02_long_range_PR_backlog.md`(L426-427 등):** x_C kill rule이 PR-249 immutability보다 약함. → LegacyProjectionReport 계약으로 포인터, Wave-9 full-cov MES 라인 supersede 표기.
- **H3 `SYMBOLS.md`:** 모든 subagent에 주입되는 정본 심볼표에 PR-248~261 타입이 0개. → 8개 타입 행 추가(전부 tested/stable). *방지 실패:* 모든 subagent가 타입 존재를 모른 채 작업·모순 생성.
- **H4 `FROZEN_DECISIONS.md`:** PR-248~275 결정 행 부재. → `D-TYPED-FOUNDATION`(reopen=BC1 위반 증명), `D-GOVERNANCE-BRAKE-2026-08` 추가.
- **H5 context pack 재빌드:** `CONTEXT_INDEX.json built_at 2026-07-23`이 PR-248~275보다 이전. → `build_context_pack.py` 재실행.
- **H6 `claim_ledger.json`·`status_matrix.md`가 `source_commit 60022d7a`=PR-252에 동결:** 199행이 PR-252에서 끝남. 단 이들은 *생성 미러*이고 canonical `pr_status.yaml`은 이미 PR-253~275를 COMPLETED_SUCCESS로 담고 있어 판정/과학 wave는 canonical을 읽음. 따라서 H6은 보편 blocker가 아니라 **publication/audit-package 소비자**(`check_publication_claim_freeze.py`, audit 빌더)에 한정 — publication-freeze/audit 단계 *전에* HEAD 재생성. (3·4부의 *실행* 전이 아니라 *보고* 전.)
- (선택·저우선) 타입 수준 `forbidden_use`로 이미 커버되는 문자열 블랙리스트 doubles 정리 — test-backed, 급하지 않음.

## 제3부 — 게이트 해제·격상 프로토콜

게이트 인구는 3:1로 갈린다: 약 3/4는 **타입 강제 불변식**(anti-laundering, ownership firewall, 반박된 정리 금지)로 어떤 증거로도 해제 불가·해제 불가여야 함; 나머지 1/4는 named event에서 해제되는 **증거-조건부 blocker**. 프로토콜은 (a) 첫 부류는 건드리지 않고, (b) 둘째 부류에 감사 가능한 해제 경로를 주고, (c) 순수 process라서 지금 가능한 단 하나의 게이트를 식별한다.

**메타-규칙:** 모든 해제는 `FROZEN_DECISIONS` 형식의 meta-finding이고 4개 필드 필수 — gate_id, discharge_evidence(게이트 자신의 exit 조건을 verbatim 충족하는 산출물), new_state, authorizing_review. C0-C6 강화는 별도 claim-firewall review 필요(roadmap 서문). **프로토콜은 게이트를 약화하지 않는다; 게이트 자신의 exit 조건이 충족된 시점을 기록할 뿐이다.**

**절대 완화 금지(구조적) 12종:** egs_oneway 26구 converse 금지(sealed 반례군), P36/T2p 철회, 반박된 non-geodesic MES triple, LegacyProjectionReport BC1/BC2 불변, MIO/HTT/OBSSTAT ownership forbidden_use, `BLOCKED_PRE_NATIVE_ATLAS` family gate, ORBIT_V3 3종 UNPROVEN, `_state_payload` content-addressing, CAS 5-state/no-majority, pdf_claim_lint 12 strict names, CLAIM_GATES 1/3/4/6행, PR-248~275의 24개 anti-laundering kill rule. **캠페인은 이 안에서만 작동하도록 설계됨.**

**Tier 0 (지금·bookkeeping):** 9.25e-6 blacklist 정리, filling_fraction 문자열 blacklist redundant 표기, 플랫폼 blocker(~110곳, toolchain 설치로 기계적 해제 — claim-firewall review 불필요), 하네스 H1-H6, pdf_claim_lint 2건, stale-artifact 계약 실패 6건.

**Tier A (최고 레버리지 — 데이터도 solver도 불필요): PR-157 per-lane split.** 세 사실: ① adjudication ledger에 **20 family가 `PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION`**, 62행 EVIDENCE_READY·independence:open, 한계가 **"adjudication capacity spend-limited"**(증거가 아니라 process). ② PR-157은 미실행이고 PR-151/155/156 뒤에 전이적으로 고정. ③ **PR-157 자신의 kill rule(`pr_backlog.yaml:3887`)이 per-lane 해결을 허용** — terminal receipt 없는 lane은 **미판정**으로 남고 다른 lane을 막지 않는다. → **terminal receipt가 있고 independence_gate가 열린 20 family에 대해 지금 non-author 패널을 소집**, D-DESI 등은 미판정 유지. all-or-nothing 독해가 가린 의도된 per-lane 의미론이지 완화가 아니다. repo 전체에서 claim-envelope 이동/노력 비율이 가장 높은 단일 행동.

**Tier B (event-gated):** PR-151 terminal(→D-DESI; 단 estimand가 BGS_BRIGHT-21.5 0.1≤z≤0.4로 측정된 BGS_ANY와 **다른 표본** → 재보정이 아니라 신규 결과), CF4 P0 5중 conjunction, CF4 WF residual operator(K6), native low-ℓ solver(PR10 — hard ceiling), PR-274 registry 기입+실행승인(→ 첫 실데이터 admit, G1-G11 해금), PR4/NPIPE(D-PR4-SKIP reopen), B-projector 수리(PR-172).

**하지 않는 것:** claim-tier ceiling 인하 없음, forbidden_use 약화 없음, UNPROVEN 승격 없음, 반박 MES triple 부활 없음, native atlas 없는 family label 없음. 모든 Tier-B 해제는 synthetic stand-in을 calibrated measurement로 바꿀 뿐 family/geometry/native claim을 승인하지 않음(BLOCKERS.md 불변식 보존).

## 제4부 — 실데이터 재실행 캠페인

**두 구조적 전제 먼저:** ① `legacy/`·`workdir/`는 git 미추적·체크아웃 부재 — 모든 CF4 P0/E2E 산출물이 hash로만 존재 → 재실행 전 재취득 필수. ② typed lane에 실데이터 결과 **0개**(PR-274 0/6 admit, PR-275 5개 synthetic). 캠페인 목적은 실수치를 V1/V2 lane에서 typed lane으로 BC1 하에 옮기고(옛 수치는 legacy projection 보존), typed 토대가 새로 가능케 한 greenfield 분석을 실행하는 것.

역추적한 ~45개 실데이터 산출물: **~20 REDO-REQUIRED, ~14 REDO-UPGRADE, ~5 PRESERVE, ~6 BLOCKED**(YAML은 wave별로 열거, 단일 disposition 표는 아님).

- **Wave R0 (선결·brake 준수):** (a) claim_ledger/status_matrix HEAD 재생성(H6), (b) legacy/+workdir/ 재취득·hash 재검증, (c) §1부 6개 gap 닫기(각 greenfield 선결), (d) R1 첫 dataset용 `PR274_DATA_IDENTITY_REGISTRY.yaml` 기입(PR-274가 요구하는 reviewed authority change).
- **Wave R1 (REDO-UPGRADE — 건전한 결과를 typed 계약으로 재계산, BC1로 옛 수치 보존 → typed lane의 첫 실수치):** K1 PR-150 pooled rank p=0.039(boot [0.0263,0.0532])·BipoSH·PR-180 → per-sector `s_Σ/s_ω/s_β` + exact parity-sign(G1·G3 동승); DESI D=9.49e-3·13.55σ·p=0.90 → amplitude SectorStress + Fieller; ACT p=0.35·UL<3.28e-6 → exceedance surface; PR-179 2/20000·PR-153; K6 per-cell→correlated CR(curl/div=0.0089 no-go는 PRESERVE); result pack A/B/C.
- **Wave R2 (REDO-REQUIRED — vintage가 아니라 결함으로 유죄):** gating 결함은 **`D-STAT-BAYES-SEMANTICS`**(공유원인 "Bayes factor"가 fitted logL 차이 — 출시 +29.7이 HEAD에서 −1035.461로 재현, degenerate null −3893~−3899, plug-in residual을 PPC/LOOCV로 오표기). 결정적 falsifier이자 evidence lane 전체의 선결: **정규화 prior·likelihood 등록 + 두 독립 엔진으로 marginal evidence 재현.** 그전까지 V1 Bayesian 체인 전부(ln B=+26.40, β=1.360e-3, F_Bayes, Q̄=0.092, Π_HTT, ch07/ch08 테이블) legacy-only. R2a(추정기 수리)→R2b(재계산; typed 후계는 Bayes factor가 아니라 SectorStress+ConditionalExceedanceSurface+partial-ID envelope+AnisotropyTypeReport 기권). 또한 유일하게 진짜 결함인 K1 표면(`lowell_morphology_real_map_report.json`: diagonal_fiducial_cl_only + mask deconvolution 없음 + look-elsewhere tracked) → 제대로 된 공분산·mask deconvolution으로 재계산.
- **Wave R3 (greenfield — typed 토대가 처음 가능케 함, PR-274 admit 게이트):** G1 실 Planck multipole 위 per-sector stress, G2 conditional exceedance envelope, G3 실 low-ℓ a_lm 위 exact parity-sign, G4 CF4 depth-path coherence, G5 실 (σ,ω,β) orbit-invariant catalogue, G6 실 estimand Fieller partial-ID, G7 기권형 AnisotropyTypeReport, G8 실 CF4+DESI typed local/global. G1-G3은 R1의 admit된 Planck dataset에 동승, G4-G8은 Tier-B event 대기.
- **Wave R4 (BLOCKED — event 발화 시 실행):** CF4 amplitude/fσ8/global-tilt(CF4 5중), PR-151 공식 mock DESI(PR-151 terminal — 신규 표본), ACT RDN0(QE), K6 definitive(WF operator), PR-179 q_cat(response-identifiability), PR08-006 join(upstream CF4 P0).

**순서와 brake:**
```
R0(선결) ─┬─> R1(typed 실수치, BC1) ──> R1 lane들의 Tier-A 판정
          ├─> R2a(evidence 추정기 수리) ──> R2b(evidence lane 재도출)
          └─> R3(greenfield, R0d admit 위)
Tier-B event 발화 시 ──> R4
```
R0+R1이 governance brake가 요구하는 "명명된 하류 과학 역량" — 추가 proof/registry 카드보다 **먼저** 와야 할 다음 PR wave. R2a는 corpus에서 가장 가치 있는 정합성 수리(evidence lane 전체를 유죄 또는 구제). Tier-A per-lane 판정은 데이터 불필요하므로 R0/R1과 병행 가능.

## 한 문단 결론

반영 감사는 통과다 — 텐서 업그레이드는 충실히, 이탈한 곳은 보수적으로 착륙했고 남은 6개 gap은 작고 전부 greenfield 선결조건이다. 그러나 repo 자신의 규칙(`AGENTS.md:145`)이 8개 연속 assurance PR 뒤에 **다음은 과학이어야 한다**고 말하고 있으므로, 이 계획의 무게중심은 게이트나 레지스트리가 아니라 **재실행 캠페인**이다. 하네스는 6곳(H1-H6)만 stale이고 대부분 재생성/재표기로 끝난다. 게이트는 3/4가 절대 건드리면 안 되는 구조적 불변식이고 나머지는 named event 조건부인데, **그중 단 하나 — PR-157 per-lane 판정 — 은 증거가 이미 완비되어 있고(20 family EVIDENCE_READY) 게이트 자신의 kill rule이 per-lane을 허용하므로 지금 데이터 없이 실행 가능한 최고 레버리지 이동**이다. 그리고 실데이터는 R0(선결)→R1(typed 재계산, 옛 수치 BC1 보존)→R2(evidence 추정기 수리 후 재도출)→R3(greenfield)→R4(blocked)로 정리되며, 결정적 단일 수리는 R2a(정규화 marginal evidence 두 엔진 재현)로 evidence lane 전체의 운명을 가른다.
