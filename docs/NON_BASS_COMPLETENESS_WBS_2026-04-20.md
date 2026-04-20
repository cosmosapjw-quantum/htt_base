# Non-BASS Completion / WBS / PR Ledger

기준 문서: `docs/BASS_PY_HTT_TSC_RESEARCH_PLAN.md`  
기준 시점: 2026-04-20  
범위: `BASS` 제외. 즉 `HTT`, `src/common`, `TSC`, `MIO`, figure/data-artifact 경로만 포함.

## 1. Scoring Rule

두 개의 점수를 분리해서 본다.

| 축 | 의미 |
|---|---|
| `코드 완성도` | 모듈 존재, 계약 정리, 테스트 표면, artifact/figure 경로 존재 여부 |
| `연구 deliverable 완성도` | 계획 문서의 D1–D28 중 non-BASS deliverable이 논문용 production까지 닫혔는지 여부 |

현재 추정치는 다음과 같다.

| 영역 | 코드 완성도 | deliverable 완성도 | 근거 | 주된 공백 |
|---|---:|---:|---|---|
| `TSC` | `88–92%` | `80–85%` | `603 collected`, admissibility 공백 해소, charts/diagnostics/integration 활성 | 확장 deliverable보다 정교화 위주 잔여 |
| `HTT common / infra` | `85–90%` | `78–83%` | `sky_geometry`, `healpix_selection`, `bulkflow_estimator`, `bulkflow_likelihood`, `mock_calibration`, `posterior_summary`가 실사용 가능 | Mode artifact chain 일부 미완 |
| `HTT science layer` | `65–72%` | `50–58%` | `evidence/nulls/figures/infer` 표면은 넓음 | D2, D4 production, D8–D16, D23–D25 다수 prototype |
| `MIO` | `40–50%` | `30–40%` | `122 collected`, HJ-01/HJ-02/registry/certificate 경로 존재 | `tension`, `decomposition` 본체 부재 |
| `비-BASS 전체` | `75% 안팎` | `60% 안팎` | 패키지 표면과 테스트는 넓게 확보 | 논문용 production-grade science deliverable 잔량 큼 |

현재 테스트 표면 스냅샷:

| 패키지 | collect-only |
|---|---:|
| `htt/tsc` | `603` |
| `htt/src/common + htt/htt/tests` | `363` |
| `htt/mio/tests` | `122` |

## 2. Current Status Table

### 2.1 최근 반영된 non-BASS carry

| 구간 | 상태 | 최근 반영 |
|---|---|---|
| `PreferredAxis production gate` | 완료 | `d4caf0b` |
| `HJ-01 Bonferroni FLRW band` | 완료 | `8dea346` |
| `theta4 native coefficient table` | 완료 | `ea796c1` |
| `direction posterior fixture parity` | 완료 | `53314e4` |
| `fiducial_posterior_bundle_v1.json` | 완료 | `c1ceb78` |
| `MIO certification/reporting registries` | 완료 | `d3c375d` |
| `diag_zoa_ladder_v1.json` | 완료 | `0d13a82` |
| `diag_plane_alignment_v1.json` | 완료 | `88b099f` |
| `baseline_selection_aware_v1.json` | 완료 | `0d13a82` |
| `mock_calibration_report_v1.json` | 완료 | `0d13a82` |
| `retention_vs_posterior_v1.json` | 완료 | `88b099f` |
| `matched_complexity_report_v1.json` | 완료 | `e331a86` |
| `15model_evidence_matrix_v1.json` | 완료 | `37e92ae` |
| `fig_zoa_ladder_mode0` | 완료 | `5f4dcd9` |
| `fig_retention_fraction_vs_posterior` | 완료 | `88b099f` |

### 2.2 Deliverable ledger

`상태`는 `완료 / prototype / 미착수 / 범위외(BASS)` 중 하나로 표기한다.

| Deliverable | 영역 | 계획 문서 기준 | 현재 상태 | 현재 근거 | 다음 닫힘 조건 |
|---|---|---|---|---|---|
| `D1` 15-model evidence ranking | HTT | prototype | `prototype+` | evidence matrix artifact + regression path 확보 | pipeline export + publication ranking consumer |
| `D2` 3-signature discriminator | HTT | 미착수 | `미착수` | W14 블록 아직 없음 | signature template + likelihood + figure/table |
| `D3` direction posterior | HTT | prototype | `prototype+` | `fiducial_posterior_bundle`, direction figure parity 확보 | production dataset wiring + full posterior output |
| `D4` null competition FPR | HTT | prototype | `prototype` | null families/runner/tests 존재 | `null_library_fpr_v1.json` + sys.path 정리 |
| `D5` filling fraction | HTT/TSC | 부분 완료 | `prototype+` | tsc bridge와 filling fraction tests 활성 | manuscript-grade export/table |
| `D6` three-bound hierarchy | HTT/TSC | 완료 | `완료` | bounds + tsc admissibility cross-check | 유지보수만 필요 |
| `D8` MES audit | HTT | prototype | `prototype` | pipeline/identifiability surface 존재 | audit artifact + promotion gate |
| `D9` depth tomography | HTT | prototype | `prototype` | advanced diagnostics 존재 | z-bin artifact + figure/table |
| `D10` Savage-Dickey | HTT | prototype | `prototype` | diagnostics shell 존재 | production report + regression |
| `D11` cross-channel coherence + LOOCV | HTT | prototype | `prototype` | code exists | artifact export + figure/table |
| `D12` posterior predictive checks | HTT | prototype | `prototype` | code exists | JSON/HDF5 artefact + residual figure path |
| `D13` matched-complexity report | HTT | prototype | `prototype+` | report artifact + regression path 확보 | pipeline/manuscript consumer wiring |
| `D14` survey nuisance marginalisation | HTT | prototype | `prototype` | infer module exists | pipeline wiring + acceptance tests |
| `D15` quadrupole axis + parity | HTT | prototype | `prototype` | geometry discrimination exists | figure/table export |
| `D16` shared-cause test | HTT | prototype | `prototype` | infer module exists | BF/report artifact |
| `D18` CAMB FLRW V-gate | BASS-linked | 미착수 | `범위외(BASS)` | non-BASS ledger에서 제외 | BASS 쪽 선행 필요 |
| `D19` BiPoSH coefficients | BASS-linked | 미착수 | `범위외(BASS)` | non-BASS ledger에서 제외 | BASS 쪽 선행 필요 |
| `D20` W_R window + frame bias | BASS-linked | 미착수 | `범위외(BASS)` | non-BASS ledger에서 제외 | BASS 쪽 선행 필요 |
| `D21` ZoA-aware directional likelihood | HTT common | 재설계 요구 | `prototype+` | Mode 0/1/2 contracts + 핵심 artifact chain 확보 | full pipeline hook + publication run wiring |
| `D22` mock calibration coverage report | HTT common | 미착수 | `prototype+` | `mock_calibration_report_v1.json` 경로 확보 | full mock suite + production thresholds |
| `D23` depth-by-depth sensitivity | HTT | prototype | `prototype` | h0_sensitivity/diagnostics 존재 | z-bin coupling and report export |
| `D24` type-by-type summary | HTT | prototype | `prototype` | figure exists | data contract stabilization |
| `D25` equivalence class evidence | HTT | prototype | `prototype` | figure exists | report artifact + regression |
| `D26` tilted-FLRW observables dictionary | HTT | 완료 | `완료` | core functions and figure path stable | 유지보수만 필요 |
| `D27` Colin β constraints | HTT | 완료 | `완료` | figure path stable | 유지보수만 필요 |
| `D28` CatWISE vs CMB discrepancy + 3-signature | HTT | 미착수 | `미착수` | D2 미완으로 종속 | D2 선행 후 joint interpretation |

### 2.3 Package-specific diagnosis

| 패키지 | 현황 | 판정 |
|---|---|---|
| `src/common` | Layer A–D 기초 경로가 살아 있고 artifact schema도 늘고 있음 | `가장 건강함` |
| `htt/htt/htt` | figures/core/infer/nulls 표면은 넓지만 science export가 덜 닫힘 | `prototype-rich` |
| `htt/tsc` | 계획 문서의 “admissibility test 부재”는 이미 해소 | `거의 stabilization 단계` |
| `htt/mio` | HJ-01/HJ-02와 registry는 살아났지만 tension/decomposition이 비어 있음 | `가장 큰 구조 공백` |

## 3. Checklist

### 3.1 완료

- [x] `PreferredAxis.production_allowed` gate 도입
- [x] `PR13AM` native/uniform fallback production gate 정리
- [x] `HTT common` 4-layer 기반 모듈 활성화
- [x] `diag_zoa_ladder_v1.json` 생성 경로
- [x] `baseline_selection_aware_v1.json` 생성 경로
- [x] `fiducial_posterior_bundle_v1.json` 생성 경로
- [x] `mock_calibration_report_v1.json` 생성 경로
- [x] `fig_direction_posterior`의 fiducial bundle parity
- [x] `fig_zoa_ladder_mode0` 추가
- [x] `TSC admissibility` 테스트 복구
- [x] `MIO` certificate / reporting registry bootstrap
- [x] `HJ-01` Bonferroni-aware FLRW band와 nonconvergence warning

### 3.2 Prototype but usable

- [ ] `D1` evidence ranking의 downstream wiring
- [ ] `D3` final posterior pipeline wiring
- [ ] `D4` null-library FPR export
- [ ] `D5` filling-fraction manuscript export
- [ ] `D8` identifiability audit artifact
- [ ] `D9/D23` z-bin tomography and sensitivity export
- [ ] `D10` Savage-Dickey report
- [ ] `D11` coherence / LOOCV report
- [ ] `D12` PPC report
- [ ] `D13` matched-complexity report의 downstream wiring
- [ ] `D14` survey nuisance production path
- [ ] `D15` geometry/parity result export
- [ ] `D16` shared-cause BF export
- [ ] `D21` ZoA mode chain의 pipeline/publication wiring
- [ ] `D22` full mock-calibration suite promotion
- [ ] `D24/D25` figure-data contract stabilization

### 3.3 미착수 또는 구조 공백

- [ ] `D2` three-signature discriminator
- [ ] `D28` CatWISE vs CMB + 3-signature interpretation
- [ ] `MIO tension` 본체
- [ ] `MIO decomposition` 본체
- [ ] `nulls.runner` production artifact and import hardening

## 4. WBS

### 4.1 HTT / common

| WBS ID | 작업 | Deliverable | 산출물 | 상태 |
|---|---|---|---|---|
| `HTT-WBS-01` | Mode artifact chain close | `D21/D22` | `diag_plane_alignment`, `retention_vs_posterior`, mock promotion checks | 진행중 |
| `HTT-WBS-02` | Inference report exports | `D1/D13` | `15model_evidence_matrix`, `matched_complexity_report` | 대기 |
| `HTT-WBS-03` | Null production reports | `D4` | `null_library_fpr_v1.json`, runner smoke hardening | 대기 |
| `HTT-WBS-04` | Audit/report pipeline | `D8/D14/D16` | identifiability, nuisance, shared-cause JSON path | 대기 |
| `HTT-WBS-05` | Posterior diagnostics | `D10/D11/D12` | Savage-Dickey, LOOCV, PPC artifacts | 대기 |
| `HTT-WBS-06` | Tomography branch | `D9/D23` | z-bin artifacts, migration, sensitivity tables | 대기 |
| `HTT-WBS-07` | Figure contract stabilization | `D24/D25` | type/equiv data contracts and smoke coverage | 대기 |
| `HTT-WBS-08` | W14 science block | `D2/D28` | 3-signature separator + CatWISE/CMB interpretation | 미착수 |

### 4.2 MIO

| WBS ID | 작업 | 산출물 | 상태 |
|---|---|---|---|
| `MIO-WBS-01` | HJ-01 stabilization complete | stronger certificate/report link | 진행중 |
| `MIO-WBS-02` | `tension` package actual implementation | minimal public API + tests | 미착수 |
| `MIO-WBS-03` | `decomposition` package actual implementation | minimal public API + tests | 미착수 |
| `MIO-WBS-04` | HTT→MIO promoted artifact ingestion | posterior/evidence contract bridge | 대기 |

### 4.3 TSC

| WBS ID | 작업 | 산출물 | 상태 |
|---|---|---|---|
| `TSC-WBS-01` | chart/admissibility export polish | publication-facing JSON or table helpers | 대기 |
| `TSC-WBS-02` | HTT consistency guards | more cross-package regression locks | 진행중 |

## 5. PR List

### 5.1 이미 landed 된 PR-sized slices

| PR ID | 범위 | commit | 메모 |
|---|---|---|---|
| `NB-PR-001` | HTT SSOT drift fix | `0fe61ba` | `T0_uK` 일관성 |
| `NB-PR-002` | MIO HJ-01 gamma warning | `64aca9c` | 수렴 실패 경고 |
| `NB-PR-003` | HTT PreferredAxis collapse | `d4caf0b` | production gate 기반 |
| `NB-PR-004` | MIO HJ-01 Bonferroni band | `8dea346` | family-wise false flag 완화 |
| `NB-PR-005` | HTT theta4 coefficient table | `ea796c1` | finite-difference 대체 |
| `NB-PR-006` | HTT direction posterior fixture parity | `53314e4` | fiducial bundle input 경로 |
| `NB-PR-007` | HTT fiducial posterior bundle | `c1ceb78` | Mode 2 artifact |
| `NB-PR-008` | MIO certification/reporting registries | `d3c375d` | figure smoke unblock |
| `NB-PR-009` | HTT directional artifact builders | `0d13a82` | Mode 0/1 + mock report |
| `NB-PR-010` | HTT Mode0 ZoA ladder figure | `5f4dcd9` | F44 path |
| `NB-PR-011` | HTT retention-vs-posterior / plane alignment | `88b099f` | `diag_plane_alignment`, `retention_vs_posterior`, F102 path |
| `NB-PR-012` | HTT matched-complexity report | `e331a86` | `matched_complexity_report_v1.json` + deterministic hash |
| `NB-PR-013` | HTT 15-model evidence matrix | `37e92ae` | `15model_evidence_matrix_v1.json` + deterministic hash |

### 5.2 다음 우선순위 PR backlog

| PR ID | 우선순위 | 대상 | WBS | 범위 | acceptance |
|---|---|---|---|---|---|
| `NB-PR-014` | `P1` | HTT | `HTT-WBS-03` | `null_library_fpr_v1.json` + import hardening | runner smoke + JSON export |
| `NB-PR-015` | `P1` | HTT | `HTT-WBS-04` | identifiability audit artifact | pipeline subphase export + audit tests |
| `NB-PR-016` | `P1` | HTT | `HTT-WBS-05` | LOOCV/coherence/PPC artifacts | three report builders + schema tests |
| `NB-PR-017` | `P1` | HTT | `HTT-WBS-06` | z-bin tomography export and figure data | `redshift_tomography_v1.json` |
| `NB-PR-018` | `P1` | MIO | `MIO-WBS-02` | `mio.tension` minimal implementation | import/test surface 확보 |
| `NB-PR-019` | `P1` | MIO | `MIO-WBS-03` | `mio.decomposition` minimal implementation | import/test surface 확보 |
| `NB-PR-020` | `P2` | HTT | `HTT-WBS-08` | 3-signature discriminator skeleton | D2 unblock only |

### 5.3 권장 실행 순서

1. `NB-PR-014`
2. `NB-PR-016`
3. `NB-PR-017`
4. `NB-PR-018`
5. `NB-PR-019`
6. `NB-PR-015`
7. `NB-PR-020`

## 6. Immediate Next Action

바로 다음 실제 코드 작업은 `NB-PR-014`가 맞다.

이유:

1. `NB-PR-012`와 `NB-PR-013`에서 report-family artifact contract가 이미 굳었다.
2. `D4` null-library FPR은 다음 독립 report slice라 같은 패턴을 바로 재사용할 수 있다.
3. `nulls.runner`는 현재 prototype 표면이 있어 write-set이 비교적 제한적이다.
4. pipeline audit이나 MIO 본체보다 먼저 닫는 편이 리스크가 낮다.
