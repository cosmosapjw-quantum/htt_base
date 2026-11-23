# R101 자료 취득과 분석 인계

R100에서 검증한 SDSS PV와 6dFGSv 표 1은 합계 20,927,710 B다. SDSS에는 공급자 MD5가 있고, 6dFGSv에는 로컬에서 측정한 MD5와 SHA-256, 공급자 응답 길이 기록이 있다. 두 파일은 기존 R100 로컬 경로에서 재사용한다. R101의 BASS/HYREC 복구 기록은 H2248, 보정 입력, 원 소스 manifest, 원자표 다섯 개 등 여덟 파일 481,990 B의 SHA-256 일치를 확인했다. 원 산출물에 대한 입력 복구는 닫혔고, tilted 화학시계와 방사선장 모델의 물리적 검증은 별도다.

## 기존에 명세가 있는 여섯 작업

| 작업 ID | 정확한 바이트 상한 | 사용할 곳 |
|---|---:|---|
| `commander_pr3_ffp10_noise_00000` | 603,987,840 | 기존 PR3/FFP10 Commander fullmission signal 00000과 같은 noise 00000의 첫 쌍 |
| `sdss_randoms_v1_1` | 284,000,071 | SDSS의 각·거리 선택 support |
| `sdss_mocks_v1_1` | 10,643,218,721 | 256개 box별 holdout. 동일 box의 관측자 8개는 같은 fold |
| `sixdf_reconstruction_mocks` | 17,344,070,928 | 재구성 mock의 FP/PV 자료, 절단, 표본 계보를 먼저 판별 |
| `lotss_aux_355` | 6,025,820,160 | DR3 한 모자이크의 weight·RMS·마스크를 확인할 후보. R99 HEAD 200 |
| `lotss_aux_1078` | 4,507,238,400 | 같은 목적의 후보. R99 HEAD 202, 당시 파일 전달 보류 |

위 HTTP 상태는 R99의 과거 관찰이다. LoTSS 두 job의 실행 경로는 현재 HEAD를 먼저 읽고 202면 종료한다. 공급자 MD5가 있는 네 자료는 SDSS randoms·mocks와 LoTSS 두 tar다. Commander와 6dF reconstruction mocks는 R99 manifest에 공급자 checksum이 없다. 공급자 URL·MD5·기존 파일의 SHA-256·작업별 예산 명령은 [DATA_ACQUISITION_PLAN.json](DATA_ACQUISITION_PLAN.json)에 있다.

## 로컬 실행

기존 HTT checkout 루트에서 첫 명령은 6개 작업을 표시한다. 둘째와 셋째는 동일한 R99 입력으로 특정 job의 바이트 예산을 확인한다. 세 명령의 과학 자료 전송량은 0 B다.

```bash
.venv/bin/python -m scripts.r101.acquire
.venv/bin/python -m scripts.r99.acquisition plan --ids commander_pr3_ffp10_noise_00000 --max-bytes 603987840
.venv/bin/python -m scripts.r101.acquire --ids sdss_randoms_v1_1 --max-bytes 284000071
```

Commander 샘플을 실제로 받을 때만 다음을 실행한다. 프로그램은 한 건씩 이전 R100 downloader로 수신하고, 공급자 checksum 유무와 로컬 SHA-256을 JSON으로 표준 출력한다. 기존 파일은 재사용하거나 충돌 상태로 보존한다. 공급자 checksum이 없는 기존 파일의 동일 길이와 로컬 digest는 독립적인 원본 인증과 구분한다.

```bash
.venv/bin/python -m scripts.r101.acquire --execute \
  --ids commander_pr3_ffp10_noise_00000 --max-bytes 603987840 \
  --destination "$HOME/Downloads/htt_r101"
```

## D01–D06에서 남는 것

| 항목 | 이미 확보한 것 | 다음 분석에 필요한 자료 |
|---|---|---|
| D01 CF4 보정 | SDSS 원 공개 표 34,059행과 6dFGSv 표 8,885행, 양쪽 native FP mark의 overlap | 다른 거리 측정법의 보정 전 표, group/calibrator ID와 공분산, SDSS와 6dF의 공식 부호·영점 계보 |
| D02 CF4 선택 | 공개 6dFGSv parent 내 포함 여부. 8,885행 중 비그룹 sentinel 6,219행, 그룹 2,666행. R100의 SDSS 선택 단계 | 전 방법을 합친 CF4의 절단 전 parent·rejected 표본, 중복·검열·선택 결합법칙. SDSS randoms와 6dF 출시 후 표본으로 평가할 수 있는 선택은 각 공개 표본 내부까지다. |
| D03 CMB | PR3 처리 경로와 Commander signal ID 00000 | 먼저 PR3/FFP10 noise 00000의 component·unit·beam·mask·split·simulation ID를 맞춘다. 전체 matched-null에는 독립된 여러 쌍이 필요하다. PR4/NPIPE는 해당 release 자체의 관측맵·짝지은 모의계로 다룬다. |
| D04 Gaia | pmra/pmdec 이력, Quaia redshift bins, 기존 각도별 공분산 감도 | release별 AGIS scan 공간오차 모형과 독립 AGN photocentre 대조 표본 |
| D05 전파 | 1,580개 LoTSS DR3 모자이크의 외곽 support | 내부 weight/RMS, flux·크기별 completeness, association·SED. 두 tar는 각 모자이크에서 확인하는 표본이다. |
| D06 독립 flux | 모델 안에서의 normal-frame 에너지·운동량 장부 | tetrad·단위·covariance가 주어진 독립 광자/물질 flux 관측 또는 그 우도 |

D01의 추가 보정 원자료, D02의 전 방법 reject parent, D04와 D06에는 현재 고정 manifest에서 URL·용량이 단정되는 취득 job이 없다. 여섯 job 중 두 큰 mock 묶음과 LoTSS 아카이브는 실행하지 않았다. 실행한 검증은 고정 manifest의 선택·예산과 fixture 응답을 사용한 보존·checksum·202 처리에 한정된다.
