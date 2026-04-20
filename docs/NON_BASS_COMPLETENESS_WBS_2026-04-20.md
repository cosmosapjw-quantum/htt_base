# Non-BASS Completion / WBS / PR Ledger

기준 문서: `docs/BASS_PY_HTT_TSC_RESEARCH_PLAN.md`  
기준 시점: 2026-04-20  
범위: `BASS` 제외. 즉 `HTT`, `src/common`, `TSC`, `MIO`, `workspace`, figure/data-artifact 경로만 포함.

## 1. Scoring Rule

두 개의 점수를 분리해서 본다.

| 축 | 의미 |
|---|---|
| `코드 완성도` | 모듈 존재, 계약 정리, 테스트 표면, artifact/figure 경로 존재 여부 |
| `연구 deliverable 완성도` | 계획 문서의 D1–D28 중 non-BASS deliverable이 논문용 production까지 닫혔는지 여부 |

현재 추정치는 다음과 같다.

| 영역 | 코드 완성도 | deliverable 완성도 | 근거 | 주된 공백 |
|---|---:|---:|---|---|
| `TSC` | `90–94%` | `83–88%` | `612 collected`, admissibility 공백 해소, charts/diagnostics/integration 활성, 3D forward placeholder 제거 | 남은 일은 table/export polish와 추가 cross-package lock 위주 |
| `HTT common / infra` | `90–94%` | `84–88%` | `sky_geometry`, `healpix_selection`, `bulkflow_estimator`, `bulkflow_likelihood`, `mock_calibration`, `posterior_summary`가 실사용 가능하고 D8/D14/D16 audit path까지 연결 | science block 자체(D2/D28)는 여전히 별도 |
| `HTT science layer` | `68–75%` | `55–62%` | `evidence/nulls/figures/infer` 표면은 넓고 audit/report artifact가 더 닫힘 | D2, D4 production, D23–D25 다수 prototype |
| `MIO` | `58–68%` | `48–58%` | `144 passed`, HJ-01/HJ-02/HJ-03/HJ-04/registry/certificate 경로 + promoted bundle ingestion bridge | evidence-side ingestion과 science-grade deepening 잔여 |
| `workspace` | `82–90%` | `76–84%` | `26 collected`, contract/G19 surface 안정, placeholder성 코드는 의도된 guard뿐 | 추가 bridge contract가 필요해지면 그때 확장 |
| `비-BASS 전체` | `78–82%` | `63–68%` | 패키지 표면과 테스트는 넓게 확보되고 HTT/TSC/MIO bridge가 더 닫힘 | 논문용 production-grade science deliverable 잔량 큼 |

현재 테스트 표면 스냅샷:

| 패키지 | collect-only |
|---|---:|
| `htt/tsc` | `612` |
| `htt/src/common + htt/htt/tests` | `389` |
| `htt/mio/tests` | `144` |
| `htt/workspace` | `26` |

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
| `null_library_fpr_v1.json` | 완료 | `2397fcf` |
| `cross_channel_coherence_v1.json` | 완료 | `8202bf2` |
| `posterior_predictive_v1.json` | 완료 | `8202bf2` |
| `loocv_report_v1.json` | 완료 | `8202bf2` |
| `redshift_tomography_v1.json` | 완료 | `8202bf2` |
| `mio_flrw_tension_ppp_v1.json` | 완료 | `96737f4` |
| `mio_xc_direct_estimate_v1.json` | 완료 | `96737f4` |
| `mio_evidence_anatomy_v1.json` | 완료 | `ced10d2` |
| `mio_redshift_evidence_tomo_v1.json` | 완료 | `ced10d2` |
| `model_identifiability_audit_v1.json` | 완료 | `5f0754b` |
| `survey_nuisance_report_v1.json` | 완료 | `5f0754b` |
| `shared_cause_report_v1.json` | 완료 | `5f0754b` |
| `theta4_bridge_coeffs_v1.json` | 완료 | `2aecdb2` |
| `mio_promoted_axis_ingest_v1.json` | 완료 | `38b34c5` |
| `general_F_stub` placeholder retire | 완료 | `2aecdb2` |
| `fig_zoa_ladder_mode0` | 완료 | `5f4dcd9` |
| `fig_retention_fraction_vs_posterior` | 완료 | `88b099f` |

### 2.2 Deliverable ledger

`상태`는 `완료 / prototype / 미착수 / 범위외(BASS)` 중 하나로 표기한다.

| Deliverable | 영역 | 계획 문서 기준 | 현재 상태 | 현재 근거 | 다음 닫힘 조건 |
|---|---|---|---|---|---|
| `D1` 15-model evidence ranking | HTT | prototype | `prototype+` | evidence matrix artifact + regression path 확보 | pipeline export + publication ranking consumer |
| `D2` 3-signature discriminator | HTT | 미착수 | `미착수` | W14 블록 아직 없음 | signature template + likelihood + figure/table |
| `D3` direction posterior | HTT | prototype | `prototype+` | `fiducial_posterior_bundle`, direction figure parity 확보 | production dataset wiring + full posterior output |
| `D4` null competition FPR | HTT | prototype | `prototype+` | null-library FPR artifact + regression path 확보 | full pipeline wiring + import hardening 잔여 |
| `D5` filling fraction | HTT/TSC | 부분 완료 | `prototype+` | tsc bridge와 filling fraction tests 활성 | manuscript-grade export/table |
| `D6` three-bound hierarchy | HTT/TSC | 완료 | `완료` | bounds + tsc admissibility cross-check | 유지보수만 필요 |
| `D8` MES audit | HTT | prototype | `prototype+` | `model_identifiability_audit_v1.json` + pipeline 3g export 확보 | promotion gate + downstream consumer wiring |
| `D9` depth tomography | HTT | prototype | `prototype+` | `redshift_tomography_v1.json` artifact + regression path 확보 | figure/table consumer wiring |
| `D10` Savage-Dickey | HTT | prototype | `prototype` | diagnostics shell 존재 | production report + regression |
| `D11` cross-channel coherence + LOOCV | HTT | prototype | `prototype+` | coherence/LOOCV artifact export + schema tests 확보 | figure/table consumer wiring |
| `D12` posterior predictive checks | HTT | prototype | `prototype+` | PPC artifact export + schema tests 확보 | residual figure path + pipeline consumer |
| `D13` matched-complexity report | HTT | prototype | `prototype+` | report artifact + regression path 확보 | pipeline/manuscript consumer wiring |
| `D14` survey nuisance marginalisation | HTT | prototype | `prototype+` | `survey_nuisance_report_v1.json` + acceptance regression 확보 | downstream table/consumer wiring |
| `D15` quadrupole axis + parity | HTT | prototype | `prototype` | geometry discrimination exists | figure/table export |
| `D16` shared-cause test | HTT | prototype | `prototype+` | BF path hardening + `shared_cause_report_v1.json` 확보 | downstream table/consumer wiring |
| `D18` CAMB FLRW V-gate | BASS-linked | 미착수 | `범위외(BASS)` | non-BASS ledger에서 제외 | BASS 쪽 선행 필요 |
| `D19` BiPoSH coefficients | BASS-linked | 미착수 | `범위외(BASS)` | non-BASS ledger에서 제외 | BASS 쪽 선행 필요 |
| `D20` W_R window + frame bias | BASS-linked | 미착수 | `범위외(BASS)` | non-BASS ledger에서 제외 | BASS 쪽 선행 필요 |
| `D21` ZoA-aware directional likelihood | HTT common | 재설계 요구 | `prototype+` | Mode 0/1/2 contracts + 핵심 artifact chain 확보 | full pipeline hook + publication run wiring |
| `D22` mock calibration coverage report | HTT common | 미착수 | `prototype+` | `mock_calibration_report_v1.json` 경로 확보 | full mock suite + production thresholds |
| `D23` depth-by-depth sensitivity | HTT | prototype | `prototype+` | tomography export path 확보 | sensitivity table + publication consumer |
| `D24` type-by-type summary | HTT | prototype | `prototype` | figure exists | data contract stabilization |
| `D25` equivalence class evidence | HTT | prototype | `prototype` | figure exists | report artifact + regression |
| `D26` tilted-FLRW observables dictionary | HTT | 완료 | `완료` | core functions and figure path stable | 유지보수만 필요 |
| `D27` Colin β constraints | HTT | 완료 | `완료` | figure path stable | 유지보수만 필요 |
| `D28` CatWISE vs CMB discrepancy + 3-signature | HTT | 미착수 | `미착수` | D2 미완으로 종속 | D2 선행 후 joint interpretation |

### 2.3 Package-specific diagnosis

| 패키지 | 현황 | 판정 |
|---|---|---|
| `src/common` | Layer A–D 기초 경로가 살아 있고 artifact schema도 늘었으며 HTT audit/report consumer가 더 붙음 | `가장 건강함` |
| `htt/htt/htt` | figures/core/infer/nulls 표면은 넓고 audit/report artifact가 더 닫혔지만 science export는 여전히 잔여가 큼 | `prototype-rich` |
| `htt/tsc` | admissibility 공백은 해소됐고 3D forward placeholder도 제거됨 | `stabilization+polish 단계` |
| `htt/mio` | HJ-01~04와 registry/certificate surface가 모두 살아났고 promoted HTT bundle ingress까지 연결됨 | `구조 공백이 더 줄었음` |
| `htt/workspace` | 계약 층은 안정적이고 placeholder성 동작은 G19 guard뿐 | `거의 close 가능` |

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
- [x] `cross_channel_coherence_v1.json` / `posterior_predictive_v1.json` / `loocv_report_v1.json`
- [x] `redshift_tomography_v1.json` 생성 경로
- [x] `mio_flrw_tension_ppp_v1.json` / `mio_xc_direct_estimate_v1.json`
- [x] `mio_evidence_anatomy_v1.json` / `mio_redshift_evidence_tomo_v1.json`
- [x] `model_identifiability_audit_v1.json` / `survey_nuisance_report_v1.json` / `shared_cause_report_v1.json`
- [x] `tsc.charts.general_F_stub` real 3D Lebedev path
- [x] `theta4_bridge_coeffs_v1.json` 생성 경로
- [x] `mio_promoted_axis_ingest_v1.json` + HTT promoted bundle ingestion bridge
- [x] `TSC admissibility` 테스트 복구
- [x] `MIO` certificate / reporting registry bootstrap
- [x] `MIO tension` minimal public API + tests
- [x] `MIO decomposition` minimal public API + tests
- [x] `HJ-01` Bonferroni-aware FLRW band와 nonconvergence warning

### 3.2 Prototype but usable

- [ ] `D1` evidence ranking의 downstream wiring
- [ ] `D3` final posterior pipeline wiring
- [ ] `D4` null-library FPR의 downstream wiring / import hardening
- [ ] `D5` filling-fraction manuscript export
- [ ] `D8` audit artifact downstream promotion / table wiring
- [ ] `D9/D23` z-bin tomography and sensitivity export
- [ ] `D10` Savage-Dickey report
- [ ] `D11` coherence / LOOCV report
- [ ] `D12` PPC report
- [ ] `D13` matched-complexity report의 downstream wiring
- [ ] `D14` survey nuisance downstream table / consumer wiring
- [ ] `D15` geometry/parity result export
- [ ] `D16` shared-cause downstream table / consumer wiring
- [ ] `D21` ZoA mode chain의 pipeline/publication wiring
- [ ] `D22` full mock-calibration suite promotion
- [ ] `D24/D25` figure-data contract stabilization

### 3.3 미착수 또는 구조 공백

- [ ] `D2` three-signature discriminator
- [ ] `D28` CatWISE vs CMB + 3-signature interpretation
- [ ] `nulls.runner` production artifact and import hardening

## 4. WBS

### 4.1 HTT / common

| WBS ID | 작업 | Deliverable | 산출물 | 상태 |
|---|---|---|---|---|
| `HTT-WBS-01` | Mode artifact chain close | `D21/D22` | `diag_plane_alignment`, `retention_vs_posterior`, mock promotion checks | 진행중 |
| `HTT-WBS-02` | Inference report exports | `D1/D13` | `15model_evidence_matrix`, `matched_complexity_report` | 대기 |
| `HTT-WBS-03` | Null production reports | `D4` | `null_library_fpr_v1.json`, runner smoke hardening | 대기 |
| `HTT-WBS-04` | Audit/report pipeline | `D8/D14/D16` | identifiability, nuisance, shared-cause JSON path | 완료 |
| `HTT-WBS-05` | Posterior diagnostics | `D10/D11/D12` | Savage-Dickey, LOOCV, PPC artifacts | 진행중 |
| `HTT-WBS-06` | Tomography branch | `D9/D23` | z-bin artifacts, migration, sensitivity tables | 진행중 |
| `HTT-WBS-07` | Figure contract stabilization | `D24/D25` | type/equiv data contracts and smoke coverage | 대기 |
| `HTT-WBS-08` | W14 science block | `D2/D28` | 3-signature separator + CatWISE/CMB interpretation | 미착수 |

### 4.2 MIO

| WBS ID | 작업 | 산출물 | 상태 |
|---|---|---|---|
| `MIO-WBS-01` | HJ-01 stabilization complete | stronger certificate/report link | 진행중 |
| `MIO-WBS-02` | `tension` package actual implementation | minimal public API + tests | 완료 |
| `MIO-WBS-03` | `decomposition` package actual implementation | minimal public API + tests | 완료 |
| `MIO-WBS-04` | HTT→MIO promoted artifact ingestion | posterior/evidence contract bridge | 진행중 |

### 4.3 TSC

| WBS ID | 작업 | 산출물 | 상태 |
|---|---|---|---|
| `TSC-WBS-01` | chart/admissibility export polish | publication-facing JSON or table helpers + `theta4_bridge_coeffs` | 진행중 |
| `TSC-WBS-02` | HTT consistency guards | more cross-package regression locks + real 3D forward path | 진행중 |

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
| `NB-PR-014` | HTT null-library FPR | `2397fcf` | `null_library_fpr_v1.json` + heatmap matrix export |
| `NB-PR-016` | HTT coherence / LOOCV / PPC artifacts | `8202bf2` | `cross_channel_coherence`, `posterior_predictive`, `loocv_report`; mixed commit |
| `NB-PR-017` | HTT z-bin tomography export | `8202bf2` | `redshift_tomography_v1.json`; mixed commit |
| `NB-PR-018` | MIO tension minimal implementation | `96737f4` | `mio_flrw_tension_ppp_v1.json`, `mio_xc_direct_estimate_v1.json`; mixed commit |
| `NB-PR-019` | MIO decomposition minimal implementation | `ced10d2` | `mio_evidence_anatomy_v1.json`, `mio_redshift_evidence_tomo_v1.json` |
| `NB-PR-015` | HTT audit/report pipeline closure | `5f0754b` | identifiability / nuisance / shared-cause artifact path + directional self-audit hardening |
| `NB-PR-021` | TSC 3D forward + theta4 bridge artifact | `2aecdb2` | `general_F_stub` placeholder retire + `theta4_bridge_coeffs_v1.json` |
| `NB-PR-022` | MIO promoted bundle ingestion bridge | `38b34c5` | `mio_promoted_axis_ingest_v1.json` + HTT promoted summary → MioCertificate |

### 5.2 다음 우선순위 PR backlog

| PR ID | 우선순위 | 대상 | WBS | 범위 | acceptance |
|---|---|---|---|---|---|
| `NB-PR-020` | `P1` | HTT | `HTT-WBS-08` | 3-signature discriminator skeleton | D2 unblock only |
| `NB-PR-023` | `P2` | TSC | `TSC-WBS-01` | filling-fraction / admissibility publication export helpers | table/json source wiring |
| `NB-PR-024` | `P3` | MIO | `MIO-WBS-04` | evidence-side HTT artifact ingestion | evidence contract bridge close |

### 5.3 권장 실행 순서

1. `NB-PR-020`
2. `NB-PR-023`
3. `NB-PR-024`

## 6. Immediate Next Action

바로 다음 실제 코드 작업은 `NB-PR-020`가 맞다.

이유:

1. `NB-PR-015`, `NB-PR-021`, `NB-PR-022`까지 landed 되면서 HTT/common, TSC placeholder, MIO promoted ingress 공백이 각각 한 단계씩 닫혔다.
2. `workspace`는 audit 기준 추가 코드 변경 없이 close 가능한 상태로 보인다.
3. 남은 가장 큰 미완은 다시 HTT science block의 `D2/D28`이다.
4. 따라서 다음 독립 작업은 `NB-PR-020`이 가장 자연스럽다.
