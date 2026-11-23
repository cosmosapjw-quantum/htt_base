# R99 다음 작업 인계

날짜: 2026-11-23 Asia/Seoul. 이번 요청은 SQ-CF4에서 재진입한 제5차 이론 R1–R10과 코딩 C1–C10이다. 핵심 결론은 [REPORT_KO.md](REPORT_KO.md), 단계별 실행은 [CYCLE_RECORD.md](CYCLE_RECORD.md), 최종 검증은 [VALIDATION.json](VALIDATION.json)에 있다.

## 실행 위치와 기준

- 기존 checkout: `/home/cosmosapjw/Dropbox/bianchi/htt_base`.
- branch: `research/r69-observable-physics-bridges-20261118`.
- interpreter: `.venv/bin/python`, Python 3.12.3.
- R99 출력: `docs/research_program/observational_publication_20261015/R99_FIFTH_BLOCKER_RESOLUTION_20261123`.
- science SSOT: 원래 R78 INTEGRATED_DAG, 60 nodes/129 edges. SHA `90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11`.
- 기존 완료는 18 completed_scoped, 신규 scientific promotion 0. 모든 원본 수락 조건·상태·간선을 유지한다.
- 다음 science node는 SQ-CF4. 직접 열린 의무: D01, D02, M01, A01.

실행 환경에서는 OMP/OpenBLAS/MKL/NumExpr를 각 1 thread로 둔다. 전체 35,970-square 공분산을 생성하지 않는다. 기존 Gaia/radio source cache는 full hashes와 저장소 fingerprint가 유지되는 범위에서 재사용한다. `NODE60_EXECUTION_PREPARATION.json`의 source와 producer/result SHA가 현재 입력을 구별한다.

## 저장된 결과의 검증과 재생성

기존 checkout에서:

~~~bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
.venv/bin/python -B -m scripts.r99.validate_cycle
~~~

이 명령은 R99 범위 테스트, 원래 strict science-authority 검사, current preparation identity, SQ-CF4의 의도된 차단, bounded download plan을 수행한다. 대형 카탈로그 전체 분석과 과거 repo 전체 회귀검사를 다시 수행하는 명령이 아니다. 각 subprocess의 실제 exit code와 로그, source/result SHA를 VALIDATION.json에 저장한다.

각 계산의 독립 재생성은 다음 entrypoint를 사용한다.

| 계산 | 명령 | 관측한 규모 |
|---|---|---|
| CF4 | `.venv/bin/python -B -m scripts.r99.cf4_source_law` | 35,970 groups, 39,282 modes, 3 typed observables |
| optics | `.venv/bin/python -B -m scripts.r99.optical` | 5 backgrounds ×12 directions ×9 redshifts; 216 frame controls |
| Gaia shared field | `.venv/bin/python -B -m scripts.r99.gaia_shared_field` | 10 fits, 48 patches, 16 coefficients/fit |
| acquisition preparation | `.venv/bin/python -B -m scripts.r99.acquisition all` | bounded public responses and 1,580-polygon union; no full science payload |
| node overlay | `.venv/bin/python -B -m scripts.r99.program_preparation prepare` | all 60 original node contracts plus actual current result identities |

production 재실행 후 source/result SHA가 달라지면 overlay를 재생성하고 `program_preparation --check`로 확인한다. `--run-package`로 명시한 하나의 새 계산만 실행할 수도 있다. 무조건 60개 worker를 띄우거나 변경 없는 full-source archive를 다시 scan하지 않는다.

~~~bash
.venv/bin/python -B -m scripts.r99.program_preparation --check
.venv/bin/python -B -m scripts.r99.program_preparation science --node SQ-CF4
~~~

첫 명령의 현재 기대 종료코드는 0, 두 번째는 **3**이다. 두 번째 명령은 D01/D02/M01/A01이 미충족인 것을 출력하며 `science_command_executed=false`, `promoted=false`를 반환한다. 이것은 runtime 장애가 아니라 해당 과학 수락의 아직 열린 상태다.

## 다음 최소 데이터 작업

첫 intake 후보는 다음 두 제품이다.

| 제품 | bytes | 공개 checksum |
|---|---:|---|
| SDSS_PV_public.dat, v1.1.0 | 20,231,640 | MD5 b5b6e31caf7ea469c2ac2cb775fa8d14 |
| 6dFGSv table1.txt | 696,070 | upstream checksum 없음; full download 후 SHA256 기록 |
| 합계 | **20,927,710** | prefix hashes와 full hashes를 구분 |

이미 실행한 준비 명령:

~~~bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
.venv/bin/python -B -m scripts.r99.acquisition plan \
  --ids sdss_pv_v1_1 sixdf_pv_table1 --max-bytes 22000000
~~~

이는 payload를 다운로드하지 않는다. 이번 실행에서도 downloaded_bytes=0이었다. 실제 후속 intake가 시작되면 stable URL, fresh status/size, range 의미, full checksum을 확인하고 raw columns를 보존한다. SDSS objid/specObjID는 float64를 경유하지 않는다. source/host/group 관계를 대조하고, group-level zero point와 mean/std/skew의 매개변수 정의를 보존한다. 6dF Groupid/cz_group sentinel -1은 실제 음수 적색편이로 읽지 않는다.

SDSS mocks는 256개의 독립 simulation box와 각 box의 8개 observer를 구분한다. 총 2,048 viewpoint를 2,048개의 독립 holdout으로 세지 않는다. SDSS selection/randoms를 전체 CF4 union의 rejected denominator로 대체하지 않는다.

LoTSS HP-1078은 조회 시 HTTP202 JSON으로 deferred였다. Online이라는 metadata만으로 전송 성공 처리하면 안 된다. HP-355는 당시 HEAD200였으나 다음 전송에서 상태를 다시 확인한다. Commander는 PR3/FFP10 fullmission noise ID00000에 고정되어 있다. 현재 PR3 signal에 PR4/NPIPE를 섞지 않는다. tape staging이나 타인에게 연락하는 작업은 실행하지 않았다.

## 이론·코드 후속 순서

1. **CF4 upstream intake → source-type assignment.** 공개 subset과 CF4의 실제 ID를 연결하고 원래 FP/거리 정의를 정한다. D01 joint calibration과 D02 rejected-parent support의 아직 없는 부분을 별도 남긴다.
2. **실제 summary의 누락 k 대역.** R99 source response를 유지하면서 low/high-k를 \(A S A^\mathsf T\)에 직접 투영한다. 현재 55.7631%는 단일 source linear smoothed velocity variance 비교값이며 36D summary의 비율이 아니다.
3. **position drift.** 새 Jacobi solver와 같은 background, observer/emitter worldline, source normal frame에서 방향의 관측시간 변화와 \(T_C,T_G\)를 계산한다. 거리만 계산한 현재 SQ-OPTICAL을 완료로 바꾸지 않는다.
4. **radio 내부 valid exposure.** 외곽 polygon fraction 위에 weight/RMS holes와 flux/size/SED completeness를 붙인다. 195/195/204개 cached zero cells를 검증된 빈 하늘로 간주하지 않는다.
5. **Gaia와 cross-probe의 교정된 법칙.** coarse shared field를 release-specific AGIS와 독립 AGN controls에 연결한다. 160D 중 rank47가 지지하지 않는 성분을 임의 covariance로 채우지 않고 자료로 구별한다.
6. **나머지 theory/analysis 의무.** R98-EXT의 한 번의 복사 feedback에서 실제 수렴으로, 그리고 독립 normal-frame stress/flux와 지정 초기조건 atlas로 진행한다. 해당 외부 입력을 다운로드 몇 개만으로 얻었다고 간주하지 않는다.

모든 노드의 직접·상속 의무와 exact package는 [BLOCKER_ACTIONS.md](BLOCKER_ACTIONS.md)와 준비표에 있다. 새 의무를 무제한 추가하기 위한 문서가 아니라 기존 수락 조건에 현재 결과를 대응시킨 것이다.

## 실패와 수정 이력

- 원래 R98 mag/log-distance mismatch는 별도 R99 교정 결과로 남겼고 R98 artifact는 보존했다.
- C9 독립 검토의 영분산 CF4, 극소-z optical root, Gaia unit-rescaling 세 결함을 수정했다. 실제 생산 범위 결과의 영향을 각 EXECUTION 문서와 로그에 기록했다.
- 독립 심사의 정확한 원 실행 stdin, shell commands, source hashes, 실패/성공 PID는 [review/INDEPENDENT_REVIEW.md](review/INDEPENDENT_REVIEW.md)와 review/commands.json에 있다. 이 파일들은 수정 전 심사를 기록한다.
- 수학적 오류, 수치 경계 오류, runtime 도구 오류, 외부 입력 미비를 구분했다. bounded tests나 DAG validation이 과거 전 저장소 회귀 또는 cosmological claim을 인증하지 않는다.

Git publication receipt는 [PUBLICATION_RECEIPT.json](PUBLICATION_RECEIPT.json)에 기록한다. 그 receipt는 자신을 포함하는 commit을 재귀적으로 기록하지 않고, 검증된 scientific deliverable commit과 당시 origin ref를 기록한다.

## Runtime 및 publication 경계

현재 프로젝트 실행 지침은 docs/harness/CURRENT_CODEX_RUNTIME.md와 AGENTS.md의 native-execution/owner publication 조항이다. 과거 CUH-G descriptor/hooks는 현재 authority로 재구성하지 않았다. 이번 실제 runtime receipt는 VALIDATION.json, lane EXECUTION 문서, review/commands.json이며 사용한 native task는 /root/cf4_theory, /root/optical_theory, /root/legacy_evidence, /root/independent_review다. 기존 source budget·historical outcome·미확인 상태를 새 PASS로 바꾸지 않았다. 기존 checkout의 source publication과 로컬 harness 설치·client activation은 구분한다. 이번 작업은 source와 연구 산출물의 commit/push이며 runtime 설치나 client activation을 수행한 것이 아니다.

검증된 연구 산출물 commit은 `21241ebaf826138640f9e1e463809af750848ab4`이며 기존 연구 branch의 origin SHA와 일치함을 확인했다. 이 인계의 최종 C10 기록·publication receipt는 그 뒤의 문서 commit으로 추가한다. 정확한 검증과 scientific source는 위 commit 및 PUBLICATION_RECEIPT.json을 사용한다.
