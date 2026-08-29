# Codex 실행 프롬프트 — External Fusion: 기능별 복구와 용량 제한 데이터 보완

작성 기준일: 2026-08-29 (Asia/Seoul)
문서 역할: 웹 조사에 근거한 실행 지시서. 이 문서 작성 과정에서 사용자 호스트의 설치, 다운로드, 데이터 검증을 실행한 것은 아니다.

## 1. 작업 목표

`htt_base`의 외부 도구와 데이터에 대해 다음을 수행하라.

- 이미 통과한 sbibm isolated core를 보존하고, 실제 지원 경로와 미충족 패키지 의존성을 분리한다.
- CONCEPT 네이티브 설치의 소진된 재시도 예산을 유지하면서, 공식 1.0.1 컨테이너를 별도 경로로 검증한다.
- Commander 00002–00006의 정확한 제품 식별과 공식 배포 경로를 복원한다. 확인되지 않은 URL이나 checksum을 만들지 않는다.
- 10개 제한 데이터셋의 문제가 누락 파일인지, 아직 구현되지 않은 분석 소비 코드인지, 검증 공백인지 구분한다.
- 필요성이 확인된 소규모 보조제품부터 선택적으로 다운로드하고, 실제 소비 코드에 연결한다.
- 설치·파일 읽기·분석 경로 동작·과학적 검증·통계 추론 허용을 서로 다른 상태로 유지한다.

계획만 제출하지 말고, 아래 경계 안에서 가능한 수정·소규모 실행·검증을 수행하라. 한 외부 구성요소가 막혔다고 독립적인 나머지 작업을 중단하지 않는다. 기존 하네스와 downloader를 재사용하고, 새로운 범용 프레임워크나 대규모 리팩터링은 만들지 않는다.

## 2. 기준 상태와 우선순위

최신 사용자 보고는 다음과 같다. 이 보고를 이전 문서보다 우선하되, 실제 실행 전 로컬 receipt를 읽어 검증한다.

```text
SBIBM_RESULT=SBIBM_ISOLATED_CORE_PASS
sbibm=1.1.0
Python=3.11.15
PyTorch=2.13.0+cu132
GPU=NVIDIA GeForce RTX 3090
passed=import,task-list,two_moons-prior,simulator,reference-posterior,C2ST
ELFI=not-installed
GPy=not-installed
receipt=/mnt/sn850x2t/htt_base_e2e/workdir/external_tools/logs/sbibm-core-smoke/receipt.json

CONCEPT_RESULT=CONCEPT_TYPED_BLOCKER
version=1.0.1
native-install-attempts=2-of-2-exhausted
first-failure=fcompiler
last-failure=Pythran-TypeError-after-compatibility-correction
official-example=not-executed-successfully
incomplete-runtime=removed
official-image=jmddk/concept:1.0.1
image-local=absent-at-last-report
image-pull=not-yet-attempted
receipt=/mnt/sn850x2t/htt_base_e2e/workdir/external_tools/logs/concept-1.0.1-final/receipt.json

COMMANDER_RESULT=WAIT_FOR_OFFICIAL_PLA_OR_HASH
requested-ids=00002,00003,00004,00005,00006
missing=official-product-route,release-identity,publisher-checksum-binding

SCIENCE_READINESS_MATRIX=.agent-harness/runs/EXTERNAL-FUSION-FOLLOWUP-20260829/artifacts/SCIENCE_READINESS_MATRIX.json
SCIENCE_READINESS_MATRIX_SHA256=9aed29dc801b7a6f3ce8e71951877c8a26b7d5048be0ab73a53ce10328a5bccf
representative-payloads-tested=15
READY=5
READY_WITH_LIMITATION=10
BROKEN_LOCAL_PAYLOAD=0

limited=Planck-PR4-selected-LFI,WMAP,QUIJOTE,ACT-DR6-primary,ACT-DR6-lensing,KiDS,HSC,WebSky,CLASS,COSMOS-Web
external-workdir-bytes=1207578873856
external-free-bytes=479302074368
Dropbox-ignore=1
```

보고된 경로 후보는 다음과 같다. 실제 `realpath`, Git 원격, 파일시스템을 확인하여 바인딩한다.

```text
REPO=/home/cosmosapjw/Dropbox/bianchi/htt_base
EXTERNAL_ROOT=/mnt/sn850x2t/htt_base_e2e
WORKDIR=/mnt/sn850x2t/htt_base_e2e/workdir
repository=cosmosapjw-quantum/htt_base
```

원격에서 확인된 이전 설치 문서:

```text
docs/codex_handoff/EXTERNAL_FUSION_INSTALL_STATUS_20260829.md
observed-document-branch=changeset/document-external-fusion-install-status-20260829
observed-document-commit=c505b69cdc5b3fdcb06cb26d2654b37696cfaa96
```

이 문서는 FOLLOWUP 이전 INSTALL 상태를 요약하며 sbibm을 아직 blocked로 기록한다. 이것을 최신 로컬 결과에 덮어씌우지 않는다. 위 브랜치를 현재 작업 브랜치라고 가정하지 않는다. 원래 receipt와 원본 matrix는 수정하지 않고, 새 결과가 무엇을 supersede하는지 명시한다.

## 3. 먼저 확인할 것

1. 로컬 `AGENTS.md`, 적용되는 글로벌 하네스, 저장소의 기존 실행·출판 정책을 읽는다.
2. `git status`, 현재 branch/HEAD/tree/remote를 기록한다. 다른 작업의 변경을 reset/stash/checkout/삭제하지 않는다.
3. 위 두 receipt와 matrix를 읽고 matrix SHA-256을 확인한다. 파일이 이동했다면 기존 manifest에서 위치를 찾는다. 확인 실패를 전체 환경 재설치나 전체 데이터 재다운로드의 이유로 삼지 않는다.
4. 실제 Python 실행 파일, 각 격리 환경, 현재 GPU를 직접 확인한다. 저장된 과거 하드웨어 프로필로 RTX 3090 보고를 덮어쓰지 않는다.
5. `findmnt`, `realpath`, `statvfs` 또는 동등한 방법으로 외장 파일시스템과 가용 공간을 확인한다. 경로 이름만으로 외장 장치라고 판단하지 않는다.
6. workdir의 Dropbox 제외와 저장소 venv의 외장 링크를 보존한다. 기존 데이터의 read-only 소비를 우선한다.
7. 기존 guard `workdir/prepare_external_download_dir.sh`가 실제 존재하면 내용을 읽고 사용한다. 전달 인자도 로컬 구현과 맞춘다. 별도의 우회 downloader를 만들지 않는다.

1.2 TB 전체를 다시 복사하거나 반복 전수 해시하지 않는다. 기존 inventory와 검증 receipt를 재사용하고, 이번에 추가·변경·실제로 소비할 파일만 필요한 수준으로 확인한다.

## 4. 저장공간 정책

모든 예산은 `GiB = 2**30 bytes`로 계산한다. 숫자는 이번 작업의 운영 정책이며, SSD 제조사 요구사항이나 데이터셋 크기 예측이 아니다.

```text
reported_free = 479302074368 bytes = 446.3848419189453 GiB
minimum_free = 300 GiB = 322122547200 bytes
maximum_new_retained_allocation = 100 GiB = 107374182400 bytes
maximum_transient_allocation = 20 GiB = 21474836480 bytes
maximum_incremental_peak = 120 GiB = 128849018880 bytes
initial_small_batch_retained_cap = 20 GiB = 21474836480 bytes
```

먼저 20 GiB 이하 소규모 묶음을 선택한다. 후속 묶음도 아래 적격성을 만족하면 총 100 GiB 이내에서 실행 가능하지만, 예산을 채우는 것이 목적은 아니다. 필요한 파일이 이미 있으면 다운로드 0 bytes가 올바른 결과다.

기존 상태가 변하지 않는다는 계산상 가정에서, 100 GiB 영구 증가 후 여유는 346.38 GiB, 120 GiB 최대 증가 시점의 여유는 326.38 GiB다. 실제 실행에는 이 계산값이 아니라 매번 재측정한 가용 공간을 사용한다.

다운로드 전 후보마다 다음을 산정하라.

```text
remaining_transfer_bytes
retained_new_bytes
remaining_peak_additional_bytes
archive_plus_extracted_overlap_bytes
container_compressed_and_unpacked_bytes
cache_and_output_bytes
existing_valid_reusable_bytes
```

압축 파일과 해제 파일을 동시에 보관하면 둘 다 센다. Docker/OCI 저장소, 이미지 writable layer, 임시파일, 패키지 cache, 파생 산출물도 포함한다. 이미 보관된 바이트를 다시 신규 예산으로 중복 계산하지 않는다.

작업 시작 조건:

```text
new_retained_total <= 100 GiB
transient_live_total <= 20 GiB
incremental_peak_total <= 120 GiB
free_now - remaining_peak_additional_bytes >= 300 GiB
```

병렬 작업과 공간을 공유한다는 점을 반영해 다운로드 예약을 직렬화하거나 기존 reservation lock을 사용한다. 다운로드·압축 해제 중에도 공간을 모니터링한다. 다른 작업이 공간을 소진하면 새 획득부터 중단한다. 남은 read-only 검사는 가능하다.

금지:
- main NVMe의 `/tmp`, 기본 pip cache, 기본 Docker/containerd 저장소로 payload를 흘리는 것.
- 전역 daemon 설정 변경·재시작·저장소 이전·Docker prune·다른 작업의 cache 삭제.
- 기존 payload를 하네스 패키지, Git 또는 Dropbox에 복제하는 것.
- 크기를 모르는 대형 archive를 제한 없이 내려받거나 해제하는 것.

HEAD가 지원되지 않는다는 이유만으로 제품이 없다고 판단하지 않는다. 필요한 경우 제한된 Range GET으로 metadata를 보완하되, 서버가 Range를 무시하면 지정한 바이트 한도에서 읽기를 중단한다. 크기를 확정할 수 없으면 명시적 최대 수신량·최대 해제량을 강제하는 작은 후보에만 허용한다.

## 5. sbibm — 정상 core 보존과 패키지 계약 분리

공식 `main/pyproject.toml`에는 `elfi>=0.7.6`, `diffeqtorch`, `sbi>=0.20.0,<0.22.0`가 일반 dependencies로 선언되어 있다[S01]. 따라서 ELFI/GPy 부재를 곧바로 “공식 optional extras 생략”이라고 부르지 않는다. 다만 이 선언만으로 이미 실행된 two_moons/C2ST 경로의 성공을 부정하지도 않는다.

- 먼저 실제 설치된 sbibm 1.1.0의 `importlib.metadata` / dist-info METADATA / 설치 출처와 source revision을 읽는다. upstream main을 설치된 wheel과 동일시하지 않는다.
- 해당 Python으로 `pip check`를 실행하고 exit code와 원문을 남긴다. 미충족 의존성이 있으면 `CORE_FUNCTIONAL / PACKAGE_DEPENDENCIES_INCOMPLETE`로 병기한다. 설치 메타데이터를 편집해서 녹색으로 만들지 않는다.
- sbibm Python 3.11 환경, 저장소 Python 3.12 환경, 기존 sbi inference 환경을 합치거나 상호 downgrade하지 않는다.
- 현재 inference 환경과 연동이 필요하면 각 환경의 Python을 명시한 subprocess와 작은 NPZ/JSON 교환으로 경계를 유지한다. parameter ordering, shape/dtype, observation ID, seed, sample provenance를 기록한다. pickle이나 전체 환경 복제로 연결하지 않는다.
- 기존 core smoke를 재현하고, 실제 다음 소비 경로에 필요한 task 하나까지만 추가한다. Julia/ODE task와 전체 benchmark suite의 설치·실행은 이번 범위에서 제외한다.
- C2ST는 분리된 reference sample 묶음의 null control과 명백히 다른 분포의 positive control로 기능을 확인한다. seed, 표본 수, classifier, split/CV, sample 중복 여부를 기록한다. 관측 결과에 맞춰 허용구간을 조정하지 않는다.
- CUDA tensor smoke, simulator device, C2ST classifier device를 별도로 기록한다. CUDA PyTorch 설치만으로 전체 sbibm/C2ST가 GPU에서 계산됐다고 주장하지 않는다.
- ELFI/GPy 기반 알고리즘을 실제 소비하는 작업이 없다면 이번에 추가 설치하지 않는다. 필요성이 생기면 별도 legacy 환경에 대한 계획만 남기고 정상 core를 건드리지 않는다.

허용 결과:
`SBIBM_ISOLATED_CORE_PASS`, 테스트된 task/metric 범위, 배포 의존성 충족 여부.
불허 결과:
full sbibm benchmark support, 모든 SBI 알고리즘 검증, 과학적 posterior calibration 입증.

## 6. CONCEPT — 세 번째 네이티브 시도 금지, 공식 컨테이너 경로

### 6.1 기존 실패를 좁혀 기록

두 번의 네이티브 시도 예산은 소진되었다. 로컬 마지막 로그에서 최초 인과 오류, 실패 패키지, Pythran 호출 stack, build-isolation 환경의 Python/NumPy/SciPy/Pythran/Cython/gast 버전을 읽어 정리한다. 전체 traceback 없이 특정 버전 pin을 정답처럼 지정하지 않는다. 이 단계에서 다시 설치하지 않는다.

### 6.2 컨테이너 preflight

공식 문서와 개발자 Docker Hub는 `jmddk/concept` 배포 및 `1.0.1` 태그를 안내한다[S02,S03]. 그러나 이번 조사에서 해당 태그의 현재 registry digest, architecture, 정확한 크기와 pull 성공은 검증하지 않았다.

다음을 로컬에서 수행하라.

1. 기존 사용 가능한 Docker, rootless Podman 또는 Apptainer를 확인한다. 불필요한 새 runtime 설치나 전역 daemon 재구성은 하지 않는다.
2. 실제 이미지 저장소·snapshotter·writable layer·cache·임시 디렉터리가 외장 장치에 있는지 확인한다. Docker에서는 `DockerRootDir` 확인만으로 끝내지 않는다. containerd image store를 쓰면 그것의 persistent root도 별도로 확인한다[S05,S06].
3. 안전한 기존 runtime이 없거나 외장 저장이 보장되지 않으면 `CONCEPT_CONTAINER_BLOCKED_RUNTIME_OR_STORAGE`로 끝내고, 필요한 최소 호스트 설정을 적는다. 다른 데이터 소비 작업은 계속한다.
4. 공식 tag의 registry manifest를 조회해 host architecture에 맞는 digest와 compressed layer 크기를 저장한다. multi-platform index digest와 선택한 platform manifest digest를 구별한다. registry 요청은 같은 원인에 대해 최대 2회로 제한한다.
5. 공간 예약 후 선택한 digest로 한 번의 pull transaction을 수행한다. 전송 중단 복구는 같은 digest에 대한 한 번의 resume까지만 허용한다. `latest`, `test-build`, 제3자 임의 이미지로 대체하지 않는다.
6. run에 사용하는 이미지 identity를 receipt에 고정한다. compressed size를 unpacked peak로 오인하지 않는다.

### 6.3 기능 확인

입력은 read-only, output/cache는 외장 전용 경로로 연결한다. 전체 home, SSH keys, Docker socket을 컨테이너 안으로 mount하지 않는다. privileged나 host-network를 사용하지 않는다. 다운로드 이후 실행은 가능하면 network disabled로 한다. 작동에 필요한 최소 writable 경로만 허용하고, CPU 4개 이하·RAM 8 GiB 이하·출력 2 GiB 이하의 bounded run을 사용한다. timeout은 실행 한도이지 완료 시간 예측이 아니다.

- 버전/help 및 `concept --local` 진입을 확인한다.
- 이미지 버전에 포함된 공식 tutorial/예제의 파라미터와 일치하는 작은 smoke를 수행한다.
- 공식 첫 tutorial의 `initial_conditions + a_begin + output_times` 예제는 **중력 상호작용을 활성화하지 않는 예제**임에 주의한다[S04]. 이것만 통과하면 `NO_FORCE_EXAMPLE_PASS`이지 gravity solver 검증이 아니다.
- 가능하면 공식 gravity-on 예제를 바탕으로 `N=16**3`, `potential_options=32`, 짧은 scale-factor 구간, power-spectrum 출력만 사용하는 작은 파생 사례를 실행한다. 실제 v1.0.1 CLI/parameter parser와 맞는지 먼저 확인한다. 축소·변경 내역을 기록하고 “공식 예제 무변경 replay”라고 부르지 않는다.
- 출력 파일의 parse, finite 값, k 순서와 설정된 종료점 도달을 확인한다. 물리 유효성·정밀도·수렴을 이 smoke로 승격하지 않는다.
- 필요할 때만 동일 조건의 force-off/force-on 대조를 추가한다. 무리한 풀 test suite나 과학적 대형 시뮬레이션은 실행하지 않는다.
- 정상 예제 실행까지 실패하면 stdout/stderr/exit code를 보존하고 해당 경로를 typed blocker로 남긴다. 네이티브 installer나 Dockerfile build로 자동 fallback하지 않는다.

상태는 둘로 유지한다.

```text
CONCEPT_NATIVE=BLOCKED_AFTER_TWO_ATTEMPTS
CONCEPT_CONTAINER=NOT_ATTEMPTED|PASS_SCOPED|BLOCKED_<REASON>
```

컨테이너 성공은 네이티브 설치가 고쳐졌다는 뜻이 아니다. CONCEPT를 `native_bianchi_boltzmann`의 대체 구현으로 등록하지 않는다.

## 7. Commander 00002–00006 — 제품 식별과 배포 증거 복원

이전 원격 상태 문서는 이 후보들을 FFP10 Commander optional remainder로 기록한다. 그러나 `BCommander`가 공식 archive product ID라고 가정하지 않는다. 먼저 로컬 manifest와 partial 파일의 실제 basename, release, CMB/noise 구분, Stokes, NSIDE, split, realization ID를 복원한다.

- PLA, Planck 공식 문서, 공식 NERSC 배포와 NASA의 공식 archive 연결을 통해 실제 제품을 조회한다[S07,S08,S09]. 공개 논문에 나온 filename 패턴은 검색 단서일 뿐 URL·release·checksum의 증거가 아니다.
- 번호를 대입해 추측 URL을 대량 생성하지 않는다. 정확한 metadata나 공식 export/download 결과에서 URL을 얻는다.
- proxy/DNS/TLS 오류, 인증 오류, 실제 archive의 404를 구분한다. 검색 결과 없음이나 proxy 404만으로 upstream 파일 부재라고 선언하지 않는다.
- 이미 가지고 있는 정확한 정상 파일이 있으면 재사용한다. partial 파일은 격리 상태를 유지한다.
- resume은 동일 release/object와 server validator를 결합할 수 있을 때만 한다. 그렇지 않으면 old partial을 보존한 채 새 candidate 이름으로 완전 획득한다. 중복되는 peak 공간은 예산에 포함한다.

### checksum 때문에 새 인공 blocker를 만들지 말 것

다음 세 가지를 구별한다.

```text
publisher_checksum: 원 배포자가 제공한 값; 없으면 null
local_sha256: 실제 획득 바이트의 로컬 재현성 digest
semantic_product_identity: release/방법/성분/실현번호/split/NSIDE/좌표/단위
```

공식 checksum이 공개되어 있으면 반드시 대조한다. 공개되지 않았더라도 공식 배포 URL과 정확한 제품 identity가 확인되고 전체 전송·형식 검사가 통과했다면 `OFFICIAL_SOURCE_VERIFIED_LOCAL_HASH_ONLY` 후보로 기록할 수 있다. 로컬 hash를 “공식 hash”라고 부르지 않는다.

기존에 고정된 admission contract가 독립적인 expected digest를 요구한다면 이를 몰래 완화하지 말고 candidate/quarantine에 둔다. 그런 요구가 없다면 이번 작업이 새로 publisher SHA-256 필수 조건을 발명하여 모든 획득을 막지 않는다. 경로도 release identity도 불분명한 현재 상태는 자체 계산 hash만으로 풀 수 없다.

제품이 식별되면 현재 5개 후보만 대상으로 바이트 예산 안에서 선택 획득한다. 식별되지 않으면 `WAIT_FOR_OFFICIAL_PRODUCT_BINDING`을 유지하고, 문의에 필요한 정확한 basename·기존 receipt·오류·요청 metadata를 포함한 공식 helpdesk 문의 초안만 생성한다. 메일은 보내지 않는다.

SMICA/NILC/SEVEM, PR4/NPIPE, 자체 생성 mock을 Commander FFP10의 동일 제품으로 대체하지 않는다. 이 optional lane이 다른 데이터와 도구의 운영 검증을 막지 않게 한다.

## 8. 데이터별 선택 획득 정책

아래는 모든 파일을 받으라는 뜻이 아니다. 먼저 기존 matrix와 실제 파일을 대조하고, 누락된 항목에만 적용하라. 각 후보에는 구체적인 consumer와 닫히는 limitation을 적는다. 소비 경로가 없다면 작은 consumer를 먼저 설계·시험하고, 데이터 수집부터 시작하지 않는다.

| 대상 | 이번에 우선할 일 | 다운로드 허용 범위 | 지금 보류할 것 |
|---|---|---|---|
| HSC | 기존 Y3 SACC를 실제 읽어 vector/covariance/n(z) 정합 확인 | 누락된 Y3 SACC, PSF NPZ 2종; object-level 검사가 필요하면 한 field/tract의 calibrated shape·PSF·mask subset | 전체 이미지, 전체 photo-z PDF, 대규모 mock catalog suite |
| CLASS 관측 | 이름이 CLASS 실험인지 로컬 provenance로 확정; Q/U/V 및 transfer 적용 소비 경로 | 해당 40 GHz release의 mapping TF, beam, bandpass, mask, 필요한 noise archive; 필요 시 reobserved 비교 지도 | CLASS/classy solver로 대체, 전체 신규 관측 모음, combined map의 독립 데이터 오인 |
| ACT DR6 lensing | 기존 code와 data release를 고정하고 하나의 data-vector 소비 경로 실행 | 누락된 matching likelihood bundle; map 분석에 실제 필요할 때만 matching map auxiliaries | 다른 release로 자동 업그레이드, 전 simulation suite |
| ACT DR6 primary | 현재 가진 제품이 primary 어느 release인지 확인 | 같은 release의 SACC/data vector, covariance, bandpower windows, beam·calibration 및 해당 consumer mask | DR6.02를 무조건 최신이라는 이유로 교체, full-resolution map bulk |
| WMAP | 기존 nine-year/DA/foreground-reduced 여부와 resolution 확인 | 같은 선택의 mask·beam·bandpass; low-resolution Q/U를 실제 쓰면 matching nine-year covariance | 90개 single-year covariance 전체, TOD·telemetry |
| QUIJOTE | MFI survey인지 Quijote N-body인지 먼저 확정 | MFI인 경우 기존 release의 mask, beam, filtering 설명·보정, 필요한 split/noise 제품 | N-body Quijote로 대체, 모든 주파수·모든 product version 일괄 수집 |
| Planck PR4 selected LFI | 정확한 NPIPE/PR4 제품·주파수·split·처리 확인 | 사용하는 LFI channel의 beam/transfer/mask와 작은 matched split/simulation test subset | 전체 NPIPE simulation 복제, PR3 FFP10을 matched PR4 noise로 승격 |
| KiDS | 이미 있는 archive에서 선택한 statistic의 vector/covariance/n(z) consumer 먼저 닫기 | 정말 없는 matching calibration/mask 또는 작은 vector bundle | 기존 16 GB catalog/전체 archive 재다운로드, 불필요한 posterior chains |
| COSMOS-Web | 기존 catalog release와 사용 tile을 확인 | 필요한 경우만 v1.1 catalog 또는 공식 subset; 기존 tile에 대응하는 PSF/star mask/ERR/WHT | 전 tile·전 filter mosaic, 30/60 mas 중복 imagery, unrelated LSS bundle |
| WebSky | 기존 selected 7 components의 성분·단위·실현 identity와 소비 경로 확인 | README/cosmology 및 구체적인 교차검사에 빠진 component 1개 수준 | halo catalog·전체 CIB 주파수·전체 light cone 일괄 획득 |

작은 보조제품 우선순위는 HSC compressed observables → CLASS 40 GHz transfer/noise → ACT lensing bundle → 기존 map의 WMAP/QUIJOTE auxiliary다. 로컬 중복·실제 consumer 의존성에 따라 순서를 바꿀 수 있지만 이유를 기록한다. 첫 묶음은 20 GiB 이내로 끝내고 효과를 확인한다.

### 공개 배포 정보에 근거한 주의점

- ACT lensing 공식 목록은 `ACT_dr6_likelihood_v1.2.tgz`를 361 MB로 표시한다[S10]. 이는 게시된 전송 크기이지 압축 해제 peak 보증이 아니다.
- CLASS 40 GHz 공개 목록에는 TF 2×11 MB, noise 3×308 MB, mask·beam·bandpass가 있다[S12]. 실제 transfer matrix와 map coordinate/Stokes ordering을 그대로 사용한다.
- HSC Y3 Fourier SACC는 EE vector, covariance, n(z)를 포함한다. 공개 파일은 BB/EB를 포함하지 않는다. EE 파일만으로 독립 B-mode 검증을 끝냈다고 쓰지 않는다[S13].
- HSC object e1/e2는 distortion이다. 공식 responsivity·multiplicative/additive·selection correction 없이 g1/g2로 이름만 바꾸지 않는다[S13].
- QUIJOTE 공식 안내는 다른 survey와 비교 전 filtering을 확인하도록 명시한다[S15]. beam smoothing만 맞춘다고 비교가 완성된다고 가정하지 않는다.
- COSMOS-Web은 2026-05-04 v1.1로 갱신되었으며 B5/B9/B10의 MIRI photometry와 photo-z를 수정하고 download link를 같은 위치에서 교체했다고 밝힌다[S17]. 파일명·URL만으로 버전 일치를 판정하지 않는다. 기존 분석의 release를 몰래 바꾸지 않는다.
- COSMOS-Web morphology/ellipticity와 calibrated weak-lensing shear를 구분한다. 필요한 shear calibration이 없으면 그 소비 경로만 제한한다[S18].
- WebSky 성분들의 단위가 같지 않다. component별 단위와 같은 simulation realization 여부를 확인하며, 현재 보유 component를 먼저 재사용한다[S19].

## 9. 실제 소비 경로 검사와 claim 경계

각 데이터셋에 하나의 blanket READY 대신 다음 축을 기록한다. 기존 matrix schema가 있으면 호환되게 확장한다.

```text
product_identity
payload_integrity
release_and_selection_coverage
auxiliary_completeness
consumer_operability
numerical_or_statistical_validation
allowed_claims
remaining_limitations
```

`READY=15`를 목표로 삼지 않는다. 원래 5개 READY 역시 당시 명시된 범위의 상태이지 모든 분석 준비 완료라는 뜻이 아니다. 새 검사에서 실제 손상이 드러나면 정직하게 기록한다.

최소 consumer 검사는 파일 read 반복에 그치지 않는다.

- 실제 선택·mask·단위·좌표·beam/transfer 적용 → 의도한 관측량 또는 요약값 출력까지 이어지는 작은 경로를 실행한다.
- map의 FITS column 이름을 사용한다. Q/U/V를 I/Q/U로 임의 해석하지 않는다. RING/NESTED, Galactic/equatorial 및 polarization basis를 명시한다.
- K_CMB/µK_CMB/K_RJ/MJy sr^-1의 차이와 bandpass 의존성을 처리한다. 좌표 회전은 spin-2 polarization basis 회전도 포함한다.
- data vector의 bin 선택을 covariance와 windows에 동일하게 적용한다. covariance가 PSD/singular이면 정의된 subspace를 사용하고 임의 jitter로 불일치를 감추지 않는다.
- lensing φ와 κ, C_ell과 D_ell을 구분하고 선택한 reader convention에 대한 known-limit/normalization test를 둔다.
- independent split, 같은 하늘을 공유하는 survey, combined map의 상관성을 무시한 joint likelihood를 만들지 않는다.
- 신규 map/shape adapter에는 작고 알려진 입력의 round-trip 또는 sign/unit mutation test를 둔다. 실데이터 결과를 본 뒤 허용오차를 튜닝하지 않는다.
- 일부 simulation을 읽은 tiny test는 표본 수 충분성·tail p-value·coverage validation을 뜻하지 않는다.
- 이번 작업에서 posterior fitting, anomaly significance 재평가, Bianchi-family identification 또는 기존 논문 수치를 변경하지 않는다. `scientific_claim_promotion=false`를 유지한다.

수치 변환 또는 consumer를 고친 경우에는 실제 생성 데이터로 before/after 또는 reference residual plot 하나를 만들고 직접 판독한다. 설치-only 작업에는 장식용 physics plot을 요구하지 말고 `not applicable`과 이유를 기록한다.

## 10. 작은 패치와 실패 보존

수정 대상은 기존 reader/adapter, downloader guard, version/source manifest, receipt, operational documentation의 작은 변경으로 제한한다. 의존성 또는 runtime 수정을 위해 scientific solver·관측 데이터·동결된 null pool을 변경하지 않는다.

최소 회귀검사:
- 외장 mount 미존재, 공간 부족, unknown size, 과다 압축 해제 시 획득이 중단되는지.
- valid local file의 재다운로드를 건너뛰는지.
- checksum 불일치·HTML 오류 payload·release 불일치·불완전 전송을 정상 파일로 승격하지 않는지.
- publisher checksum 부재와 실제 checksum 불일치를 서로 다른 상태로 처리하는지.
- sbibm core 환경에 ELFI/GPy 설치나 다른 sbi 버전 변경이 일어나지 않았는지.
- 고친 consumer가 정상 control과 잘못된 단위/부호/필드 control을 구별하는지.

이 검사는 기존 테스트 구조에 추가한다. 다운로드 보호 기능이 없어서 새 helper가 필요한 경우에만 최소 구현을 만들고 그 helper 자체를 테스트한다. 실패 원인별로 한 번의 최소 패치를 시험하되, 같은 원인이 반복되면 typed blocker로 남긴다. 원인 확인 없이 패키지 버전 조합을 연속 탐색하지 않는다.

## 11. 산출물 및 종료

기존 run 구조를 따르는 새 run ID를 사용한다. 대형 실행 로그·payload·환경은 외장에, 작은 manifest/코드/요약만 저장소에 둔다. 다음 정보를 기존 파일에 통합하거나 아래 파일로 저장한다. 같은 내용을 여러 문서에 반복 복제할 필요는 없다.

1. `RESOLUTION_REPORT.md`: 해결·부분해결·외부차단, 근거와 허용 claim.
2. `RESOLUTION_LEDGER.json`: 시작 상태, 실제 environment, 명령/exit code/receipt, before/peak/after storage.
3. `DOWNLOAD_DECISIONS.json`: 후보, 소비 코드, 누락 이유, 공식 source, release, publisher/local hash 구분, 예상/실제 byte, 받음/생략/보류 결정.
4. `SCIENCE_READINESS_MATRIX_v2.json`: 원본 matrix hash 링크와 기능별 새 상태.
5. 필요한 작은 테스트·receipt와 기존 설치 상태 문서의 최신 FOLLOWUP 추가 또는 명시적 supersession.

commit/push/PR은 저장소의 기존 승인된 출판 정책을 따르며 이번 요청을 무조건 merge 권한으로 확대하지 않는다. 다른 worktree의 변경이나 원시 데이터를 stage하지 않는다. 원격 게시를 실제 하지 않았다면 했다고 보고하지 않는다.

종료 요약은 다음 항목을 포함한다.

```text
SBIBM_CORE_RESULT:
SBIBM_DISTRIBUTION_DEPENDENCY_STATUS:
CONCEPT_NATIVE_RESULT:
CONCEPT_CONTAINER_RESULT:
COMMANDER_SOURCE_AND_ACQUISITION_RESULT:
CONSUMER_CHECKS_COMPLETED:
NEW_DATA_DOWNLOADED_BYTES:
NEW_RETAINED_ALLOCATION_BYTES:
PEAK_INCREMENTAL_ALLOCATION_BYTES:
EXTERNAL_FREE_BYTES_FINAL:
MAIN_NVME_PAYLOAD_LEAK:
DROPBOX_IGNORE_STATUS:
SCIENCE_CLAIM_PROMOTION: false
REMAINING_TYPED_BLOCKERS:
ONE_RECOMMENDED_NEXT_ACTION:
```

실행하지 않은 단계를 성공으로 추정하지 않는다. optional lane의 blocked 상태도 유효한 종료다. 확인된 기능의 범위를 넓히고 실제 검증 공백을 줄이는 것이 완료 기준이며, 모든 상태를 녹색으로 만드는 것이 아니다.

## 12. 공식 조사 출발점

이 목록은 검색 출발점이다. 파일을 받기 전 실제 release와 source 링크를 재확인한다. 디렉터리 전체를 재귀 다운로드하지 않는다.

- [S01] sbibm package declaration: https://raw.githubusercontent.com/sbi-benchmark/sbibm/main/pyproject.toml
- [S02] CONCEPT installation: https://jmd-dk.github.io/concept/installation.html
- [S03] Developer image registry: https://hub.docker.com/r/jmddk/concept
- [S04] CONCEPT first simulations: https://jmd-dk.github.io/concept/tutorial/first_simulations.html
- [S05] Docker data roots: https://docs.docker.com/engine/daemon/
- [S06] Docker containerd image store: https://docs.docker.com/engine/storage/containerd/
- [S07] Planck Legacy Archive: https://pla.esac.esa.int/
- [S08] ESA PLA documentation/helpdesk route: https://www.cosmos.esa.int/web/planck/pla
- [S09] NASA links to official Planck archives: https://lambda.gsfc.nasa.gov/product/planck/curr/planck_prod_esa.html
- [S10] ACT DR6 lensing likelihood: https://lambda.gsfc.nasa.gov/product/act/actadv_dr6_lensing_lh_get.html
- [S11] ACT primary release entry: https://lambda.gsfc.nasa.gov/product/act/act_dr6.02/index.html
- [S12] CLASS observation products: https://lambda.gsfc.nasa.gov/product/class/class_prod_table.html
- [S13] HSC S19A shape/Y3 data: https://hsc-release.mtk.nao.ac.jp/doc/index.php/s19a-shape-catalog-pdr3/
- [S14] WMAP nine-year products: https://lambda.gsfc.nasa.gov/product/wmap/dr5/m_products.html
- [S15] QUIJOTE MFI product information: https://lambda.gsfc.nasa.gov/product/quijote/quijote_mfi_data_info.html
- [S16] KiDS-1000 cosmic shear: https://kids.strw.leidenuniv.nl/DR4/KiDS-1000_cosmicshear.php
- [S17] COSMOS-Web release updates: https://cosmos2025.iap.fr/
- [S18] COSMOS-Web catalog schema: https://cosmos2025.iap.fr/catalog.html
- [S19] WebSky official archive: https://lambda.gsfc.nasa.gov/simulation/mocks_data.html
- [S20] NPIPE official release entry: https://portal.nersc.gov/project/cmb/planck2020/
- [S21] CONCEPT v1.0.1 Dockerfile: https://github.com/jmd-dk/concept/blob/v1.0.1/Dockerfile
- [S22] SBI benchmark definitions: https://sbi-benchmark.github.io/

끝.
