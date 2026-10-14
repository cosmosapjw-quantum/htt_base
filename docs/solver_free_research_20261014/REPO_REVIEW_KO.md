# PR와 현재 코드 검토

비교: `7e94477124b60a6c755017acd6b8eb3f7b67dc54` → `89621f4c9a6f63449813587a0fadeb13287f8e10`. GitHub 최신 PR와 갱신 검색에서 새 번호는 확인되지 않았고 PR #532에 7개 commit이 추가됐다. `git diff --shortstat`는 808 files, +214242/−171이다. #532 전체의 898 changed files와 이 추가분의 808은 서로 다른 비교다.

| commit | 실제 증가분 | 검토 판단 |
|---|---|---|
| d1064878 | SMICA tensor·processing scan | 60/240 내부 분리, 같은 sky/simulation 재사용. confirmatory Planck p로 승격 불가 |
| 75109ac2 | dipole·lensing·distance controls | endpoint response와 실제 global history를 구분함 |
| ef02e56c | spectra/polarization/catalogue | release parity·조건부 descriptor와 새 물리 검출을 구분함 |
| d4e190a4 | CF4 selected posterior/latent PPC | 공유 preselection law·같은 draw를 사용. 후속 refinement가 원래 실패를 해소함 |
| a6a59d7c | joint distance/CMB/report | Union3 prior source bridge를 새로 점검할 필요. 조건부 수치는 보존 |
| e9728c88 | Gaia deterministic/statistical error | raw coordinate box의 기저 의존성과 marginal interval 한계를 이번에 보강 |
| 89621f4c | 외부 blocker 인계 | 부족 입력을 여섯 연구 의뢰로 분리. 분석 연구의 불가능 증명이 아님 |

확인한 자료는 기존 13쪽 과학 보고서 및 result inventory, BLOCKERS/RETURN, 핵심 source code/result envelopes, CF4 최신 refinement, 선택적으로 조회한 FFP header/formal report다. 400개 CLASS 계수 NPZ와 모든 원지도 변환을 다시 실행하지 않았다. 기존 성공 계산을 재사용했다.

첨부 `report(1).pdf`는 36쪽 2026-09-13 HTT 이론 compendium이다. 이번에는 §§12–13,19–20의 local-response/nuisance, covariance/coverage, finite-rank bounds를 재대조했다. 유한 rank interval은 이미 compendium §20에 있으므로 이번 CLASS 적용을 새 정리로 부르지 않는다. Dossier는 observer/selection/error 응용의 정당한 전제를 제공하지만 actual history·population law를 대신하지 않는다.

## 실제 발견과 처리

- CF4 selected_v2의 02/05 `quadrature_acceptance=false`는 과거 실패다. 뒤의 quadrature_refinement_v2를 읽어 10⁻⁶ 기준을 만족한 ΔlogL=5.68e−14/1.46e−11을 확인했다. 현재 blocker로 다시 집계하지 않는다.
- Union3 원저자 설명과 공개 Stan cosmo_model=2 분기의 prior가 일치하지 않는다. 실제 FITS 생성 run과 공개 코드의 대응은 미확인이다. 수치를 삭제하거나 임의로 고치는 대신 선언한 Gaussian prior-removal sensitivity를 실행하고 source-binding blocker를 구체화했다.
- 로컬 connector 내용 materialization에서 terminal newline 1개가 덧붙었다. 엄격한 SHA 검사로 발견했고 원격 원본과의 단일 newline 차이임을 확인했다. source bytes와 해시를 교정한 뒤 primary checkout에서 실제 계산을 수행했다. 수학·알고리즘 변경으로 취급하지 않는다.
- 최초 `/home/cosmosapjw/venv/bin/python`에는 astropy가 없었다. 기존 `/usr/bin/python3`의 과학 환경을 사용해 통과했다. 새 package 설치는 하지 않았다.
- branch 전환 hook에서 과거 shared Lean helper 경로 부재 경고가 있었다. 이번 연구는 Lean 검증을 주장하지 않고 그 설치를 변경하지 않았다.

첫 연결은 offline이었다. 그동안 선택 자료와 작은 patch를 준비했고 사용자가 agent를 재시작한 뒤 기존 primary checkout이 clean/정확한 HEAD임을 확인했다. 다른 clone/worktree/full repository copy는 만들지 않았다. 기존 checkout의 새 branch에서 parent 한 명이 통합·검증·게시한다.
