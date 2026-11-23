# Manticore-Local 속도장 접근과 CF4 인수인계

2026-11-23 17:31 UTC에 분석 머신에서 8개 URL에 익명 HTTPS GET을 실행했다. 각 응답의 첫 4,096바이트만 읽는 상한을 두고 요청했다. Stockholm의 카탈로그와 저자 노트북은 바이트를 반환했다. 2M++로 제약된 Manticore-Local 3차원 속도 실현 두 개에서 받은 바이트는 0이다. 각 응답의 시각, URL, 상태, ETag, 수신 길이와 부분 SHA-256은 [MANTICORE_ROUTE_PROBE.json](MANTICORE_ROUTE_PROBE.json)에 있다.

| 제품과 경로 | 분석 머신에서 확인한 결과 | 활용 범위 |
|---|---|---|
| [Stockholm 공식 공개 목록](https://digitaltwin.fysik.su.se/data-access.html) | HTTP 206, 4,096 / 37,001 B | z=0 실현 80개, 1,000 Mpc 상자와 256³ 격자를 안내한다. 속도장 접근은 저자 패키지와 튜토리얼로 연결된다. |
| [Stockholm posterior cluster HDF5](https://digitaltwin.fysik.su.se/downloads/manticore_local_posterior_associations/manticore_local_posterior_cluster_catalog.h5) 및 [자료 설명](https://digitaltwin.fysik.su.se/downloads/manticore_local_posterior_associations/README.md) | 각각 HTTP 206. HDF5는 4,096 / 29,062,384 B, 첫 8바이트의 HDF5 서명 확인. 설명은 4,096 / 12,477 B | 401개 cluster association의 위치·속도 등 halo 단위 posterior. CF4의 임의 위치에서 보간할 Cartesian 속도 격자는 제공하지 않는다. |
| [저자 튜토리얼의 고정 커밋](https://raw.githubusercontent.com/stuartmcalpine/manticore_public_scripts/7b345b4d7c4de505fa585ab0af1176a8219ba7bb/manticore_data_tutorial.ipynb) | HTTP 206, 4,096 / 1,224,825 B | R103에서 확인한 버킷과 객체 키, 공개 접근 절차. 노트북 자체에는 전체 격자 자료가 들어 있지 않다. |
| [저자 패키지 v2.0.1](https://pypi.org/project/manticore-data/2.0.1/) 및 [IAP 공개 접근 구성](https://manticore.web.data-2-osu.iap.fr/public-keys.json) | 패키지 sdist 22,400 B, SHA-256 `a9a2ffc7e9b6ba43fc9961cefaccca98dbda64bd99a20b63db07218f9cc8cf49`. IAP 접근 구성 GET은 5초 연결 제한에 도달, HTTP 응답 전 0 B | 패키지 소스의 기본 S3 endpoint는 `https://data-2-osu.iap.fr`. R104의 패키지 경유 실제 fetch도 같은 호스트 구성 단계에서 135.77초 후 종료됐다. |
| IAP의 경로 형식으로 요청한 [draw 0](https://data-2-osu.iap.fr/manticore-local/R1024/mcmc_0/velocity_fields/N256/field.h5), [draw 1](https://data-2-osu.iap.fr/manticore-local/R1024/mcmc_1/velocity_fields/N256/field.h5) | 두 GET 모두 연결 시간 초과, 0 B. 서버의 HTTP 상태와 익명 객체 권한은 미확인 | 패키지의 bucket/key로 구성한 직접 요청이다. 실제 속도장 존재·HDF5 내용·체크섬 판정은 접속 복구 후 가능하다. |
| [Aquila Consortium 공개 목록](https://aquila-consortium.org/?m=data) | 검색 색인에서 Manticore 항목 확인. 분석 머신 직접 GET은 연결 시간 초과, 0 B | 이번 조사에서 검증한 독립적인 격자 다운로드 경로는 없다. Zenodo 제목 검색에서도 대응하는 배포 레코드를 찾지 못했다. |

## 분석 재개

재연결 후 저장소 루트에서 R104와 같은 Python 환경(`manticore-data==2.0.1`)으로 아래 명령을 실행한다. raw 데이터의 전체 SHA-256, 객체 키, ETag, 크기를 남기는 기존 fetcher를 사용한다. 두 draw는 입출력과 부호 검증용이며, 이때 36차원 표본 공분산의 계수는 최대 1이다.

```bash
env -u PYTHONPATH "$field_py" -B -m scripts.r103.manticore_cf4_pv fetch \
  --indices 0 1 --directory "$HOME/Downloads/htt_r103/manticore" --max-bytes 800000000
```

격자 차원·좌표축·원점·단위와 관측자 속도 기준을 고정하고 시뮬레이션 기준과 관측자 속도 차감 기준을 비교한다. 후속 posterior 공분산은 동일 선택·동일 창함수에 투영한 고유 실현들로 구성한다. R104에서 이미 실행한 2MRS 재구성 투영은 별도 입력과 대상을 가진 민감도 분석이다. 현재 R105는 Manticore를 이용한 CF4 공분산·유의도 값을 산출하지 않았다.

Manticore-Local 모형과 2M++ 조건화에 대한 원 논문은 McAlpine et al. (2025)의 [MNRAS 논문 DOI 10.1093/mnras/staf767](https://doi.org/10.1093/mnras/staf767)다. DOI는 논문을 식별하며 개별 격자 바이트의 식별자는 bucket/key와 수신 파일의 체크섬이다.
