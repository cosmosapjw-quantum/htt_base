# Commander FFP10 00002–00006: bounded official-source binding and download

## Task

현재 htt_base 호스트에서 Commander FFP10의 누락/불완전 실현 00002–00006만 대상으로,
공식 제품 조회 → 제한된 원격 응답 검사 → 조건을 충족한 파일의 실제 다운로드를 수행해.
이 문서는 설치 작업이나 science-validation 작업의 재개 지시가 아니다.
“URL이 아직 manifest에 없다”는 이유로 원격 조회를 생략하지 마.
실제 조회 실패와 조회하지 않은 상태를 구별해.

## Source and knowledge boundary

ChatGPT는 이번 조사에서 다음을 확인했다.

- ESA PLA는 공식 Planck 제품 아카이브이며 파일명 검색을 제공한다.
- 공개 논문의 데이터 링크와 htt_base의 기존 코드 모두 다음 시뮬레이션 AIO 주소 형식을 사용한다.
  https://pla.esac.esa.int/pla/aio/product-action?SIMULATED_MAP.FILE_ID=<EXACT_BASENAME>
- htt_base의 c505b69cdc5b3fdcb06cb26d2654b37696cfaa96에서 확인한 참고 코드:
  - pla_aio_download_diagnostics.py, 첫 220줄: HOST와 AIO_PATH 정의.
  - K1_FFP10_SMICA_FULL_CMB_NOISE.sh: SMICA의 위 endpoint 사용 예.
- 이것은 Commander 다섯 파일의 존재, exact basename, release, HTTP 성공 또는 전체 전송의 증거가 아니다.
- ChatGPT 웹 도구의 해당 바이너리 URL 조회는 유효한 제품 응답을 확인하지 못했다.
  이를 호스트에서의 HTTP 404나 전 세계적인 archive outage로 기록하지 마.
- 호스트의 최신 .pending receipt와 payload는 ChatGPT가 직접 읽지 못했다.

공식 자료:
1. https://pla.esac.esa.int/
2. https://www.cosmos.esa.int/web/planck/pla
3. https://lambda.gsfc.nasa.gov/product/planck/curr/planck_prod_esa.html
4. https://academic.oup.com/mnras/article/524/3/3712/7224010
   Footnote 3의 SIMULATED_MAP.FILE_ID 링크는 endpoint 형식의 예시일 뿐,
   Commander 제품이나 PR3/PR4 equivalence의 근거로 사용하지 마.

## Preserve

- EXTERNAL-FUSION-FOLLOWUP-20260829와 이를 참조하는 MES 포인터를 덮어쓰지 마.
- 현재 .pending 관례를 먼저 읽고 고유 run ID로 새 receipt를 작성해.
  예: COMMANDER-FFP10-DOWNLOAD-<UTC timestamp>-<random suffix>.
- 기존 partial 파일, local prefix hashes, 기존 expected hashes 및 old receipts를 보존해.
- sbibm core/main venv, CONCEPT native, 패키지 설치 상태를 변경하지 마.
- main NVMe로 payload를 쓰지 마. Dropbox 제외와 external venv 링크를 유지해.
- git checkout/reset/clean, push/merge, 전역 process/cache 정리, 시스템 네트워크 튜닝을 하지 마.
- 참고 코드 전체를 그대로 실행하지 마: 기존 SMICA bulk downloader나 네트워크 benchmark는 이번 범위 밖이다.

## 1. Intake: local facts, not a re-audit campaign

현재 저장소와 적용되는 AGENTS.md를 확인해.
최신 .pending receipt, 직전 Commander 조사 기록, 기존 acquisition manifest와 URL 목록을 읽어.
정확한 다섯 basename, 현재 보유 bytes, 예상 전체 크기의 근거,
FITS HDU/column/NSIDE/ORDERING/단위 정보, 기존 원래 source URL을 작은 표로 정리해.

가능하면 기존 PLA URL 목록/다운로드 로그에서 provenance를 복구해.
외장 경로의 이전 downloads/pla/urls, downloads/pla/logs는 후보이며
실제 존재와 해당 Commander 파일과의 관련성을 확인한 뒤에만 사용해.
범용 재귀 payload scan, 전체 NVMe hash 재계산은 하지 마.

실현 번호만으로 파일명을 새로 만들어 공식명이라고 주장하지 마.
SMICA라는 문자열을 commander로 바꾼 이름도 확인 전에는 hypothesis일 뿐이다.
이미 local receipt에 정확한 basename이 있으면 그 값을 재사용하고 사용자에게 다시 묻지 마.

## 2. Official query: permit tested candidates, forbid invented evidence

우선 HTTPS PLA AIO에 각 local basename을 URL-encode하여 정확히 질의해:

    endpoint = "https://pla.esac.esa.int/pla/aio/product-action"
    params = {"SIMULATED_MAP.FILE_ID": exact_local_basename}

이렇게 생성한 주소는 CANDIDATE_QUERY_URL이다.
공식 archive의 실제 응답 및 제품 정보로 검증되기 전에는 VERIFIED_PRODUCT_URL로 부르지 마.
일반 관측맵의 MAP.MAP_ID와 시뮬레이션의 SIMULATED_MAP.FILE_ID를 혼동하지 마.

직접 query에서 제품을 식별하지 못하면 공식 PLA의 filename search를 사용해.
공식 UI에서 얻은 product record, URL 또는 export된 검색 결과를 보존해.
대체 mirror는 공식 배포 페이지가 해당 제품으로 연결한 경로만 사용해.
없는 NERSC 디렉터리나 undocumented API를 무차별로 순회하지 마.

파일당 HEAD 1회와 최대 64 KiB의 bounded GET/Range probe를 기본으로 해.
HEAD가 405/501이어도 즉시 파일 부재라고 판정하지 마: GET과 다를 수 있다.
서버가 Range를 무시하여 200 전체 응답을 보내면 stream을 64 KiB에서 닫아.
requests.get(...).content 같은 무제한 body 읽기는 하지 마.
전송/429/5xx 재시도는 Retry-After를 존중하며 파일당 최대 2회로 제한해.
404/명백한 제품 불일치에서는 같은 주소를 반복 재시도하지 마.

기록: requested URL, final URL, redirects, HTTP status, Content-Type,
Content-Disposition, Content-Length 또는 Content-Range total,
ETag/Last-Modified(있을 때), probe byte count와 hash, 제품 관련 FITS cards.
TLS verification을 끄지 마. HTTP downgrade를 성공 경로로 사용하지 마.

바인딩은 exact query와 반환 제품의 일치, 공식 제품/배포 정보,
FITS 구조 및 local target specification을 함께 대조하여 판정해.
HEALPix/FITS 구조가 맞는다는 이유만으로 release를 추정하지 마.
반대로 원본 FITS에 SIM_ID, RELEASE, CHECKSUM 카드가 없다는 것만으로
새 형식 요구사항을 만들어 막지도 마: 공식 record/파일명/문서로 확인 가능한 항목은 그 근거를 써.
HTML/XML/JSON 오류 body는 HTTP 200이어도 FITS 다운로드 성공이 아니다.

## 3. Acquisition approval and budget

보고된 가용 공간은 478,762,262,528 bytes지만 실행 직전 df/statvfs를 다시 읽어.
이번 Commander lane의 신규 payload + staging + logs 최대 동시 할당은 8 GiB로 제한해.
외장 가용 공간 최소 300 GiB를 전 과정에서 유지해.
8 GiB는 실제 파일 크기에 대한 주장이나 채워야 할 목표가 아니라 이번 lane의 상한이다.

기존 workdir/prepare_external_download_dir.sh의 사용 계약을 먼저 읽고,
그 경로 준비기를 통해 외장 전용 raw/planck_ffp10/commander 아래 새 candidate 위치를 마련해.
실제 resolved path, mount source/device 및 외장 mount 존재를 확인해.
외장이 unmounted인데 동일한 /mnt/... 디렉터리에 main NVMe 파일이 생기게 하지 마.

각 원격 객체의 전체 예상 크기가 알려졌다면 남은 추가 peak를 계산해.
Content-Length가 없으면 무조건 막지 말고 FITS 구조의 크기 근거 또는
기존 공식 크기와 hard byte cap으로 제한된 candidate transfer가 가능한지 판정해.
크기/형식 정보만으로 제품 identity를 확정하는 것은 여전히 금지다.
유효한 bound 없이 크기를 알 수 없는 대용량 archive를 받지 마.

공식 제품 바인딩 및 공간 조건이 충족된 대상은 실제로 내려받아.
또 다른 사용자 승인이나 “공식 checksum을 가져오라”는 요청으로 미루지 마.
단, 기존 frozen admission contract가 외부 expected digest를 필수로 요구한다면
그 계약은 유지하고 이 실행의 다운로드 결과를 독립 candidate로만 보존해.

## 4. Transfer and integrity

다섯 파일만 한 번에 하나씩 .part로 내려받아.
다른 pipeline, 다른 release, 관측 Commander 맵, 전체 simulation suite를 대체/추가 취득하지 마.
기존 local prefix hash만으로 안전한 resume라고 판정하지 마.
resume는 same remote object/representation와 기존 bytes의 일치 근거가 있을 때만 사용해.
그 근거가 없으면 기존 partial을 보존하고 새 candidate로 처음부터 받아.

streaming 중 source URL/validator 변화, byte ceiling, remaining disk를 확인해.
전송 중단 시 partial과 실패 receipt를 남겨. 실패를 성공 파일명으로 rename하지 마.
완료 후 전체 SHA-256을 계산하고 FITS 전체 구조/데이터 접근을 검사해.
원본 CHECKSUM/DATASUM이 있으면 검증하되 없으면 ABSENT로 기록해.
배포자 checksum이 있으면 정확히 그 값과 비교해.
배포자 checksum이 없다면 publisher_checksum=null,
local_sha256=<실제 계산값>으로 분리해.
새 checksum을 원본 FITS에 삽입하거나 headers를 수정하지 마.

파일 크기, units, ordering, HDUs, field/shape가 target과 일치하는지 확인해.
완결된 candidate는 같은 파일시스템 내 atomic rename으로 확정하고
payload 복제 없이 경로를 receipt에 연결해.

## 5. Closeout

새 고유 run에 다음만 남겨:
- COMMANDER_PRODUCT_BINDING.json: 다섯 개별 제품의 query와 source evidence.
- COMMANDER_DOWNLOAD_RECEIPT.json: URL, size, hash, transfer/format status.
- COMMANDER_STORAGE_RECEIPT.json: 시작/끝 가용 공간, 신규 peak, 실제 저장 mount.
- COMMANDER_CLOSEOUT.md: 실제로 실행한 명령, 성과, 남은 한계.

다음 축을 분리해:
product_binding / download_complete / local_integrity /
publisher_checksum_verification / existing_science_admission.
성공 3개·실패 2개이면 그대로 기록해. 다섯 개 모두 READY로 만들려고 사실을 바꾸지 마.
다운로드 완료를 covariance calibration, null-pool adequacy 또는 과학 claim 검증으로 승격하지 마.

실패 시 WAIT_FOR_OFFICIAL_PRODUCT_BINDING 하나로 뭉개지 말고
NETWORK_DNS, TLS_FAILURE, AUTH_REQUIRED, HTTP_404, RATE_LIMITED,
PRODUCT_MISMATCH, BODY_NOT_FITS, TRANSFER_INCOMPLETE, SOURCE_CHANGED,
LOCAL_INTEGRITY_FAILURE, STORAGE_GUARD 등 실제 근거에 맞춰 분류해.
웹 UI/인증 지원이 없으면 그 도구 한계를 구체적으로 적어.
독립된 이미-consumable 데이터셋의 scientific-use 작업은 이 optional lane 때문에 막지 마.
