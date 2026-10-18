# D06: 실제 CF4 유속 입력과 D03 host 위치의 종속적 민감도

2026-10-18. Owner `htt`, `DIAGNOSTIC_ONLY`, non-claim-bearing exploratory
actual-data artifact. Transfer `empirical_proxy`. 용도는 입력 유속장의 의미 검증,
실제 host의 redshift-space cell query, 선언한 H100 거리 proxy의 민감도다.
우주론적 null, joint covariance, 독립 CF4 검증, physical luminosity-distance
보정 또는 원래42노드의 과학 승격으로 사용하지 않는다.

요청 `Sol/high`, exact requested model `UNVERIFIED` (원래 accepted spawn settings는
worker context에서 확인할 수 없음), observed `UNKNOWN`. 기존 primary checkout과
`research/htt-open-input-theory-20261018`에서 실행했다. 최초 source intake는
`1528ebd3c4ace48a561b9dcaa6d5f891121a22a5`; D02 출판 이후 실제 시작 HEAD는
`4a6b26bff0eadae8243054c2eb99add2b6bdc34f`였다. D03는 고정 candidate
`c326fc79b4cfd255d4655cb47b27a4b399403179c3342ac30ae7113c80dcc388`의
graph/host cache/parser identity를 소비한다. 기존 large fit, native solver,
ODE, 새 clone/worktree, 자식 agent, commit/push는 실행하지 않았다.

## 실제 원자료 확보에서 발견한 stale link

[공식 Cosmicflows 배포 페이지](https://projets.ip2i.in2p3.fr/cosmicflows/)는
grouped CF4 velocity 및 error에52를 곱하고 spatial 순서를 SGZ,SGY,SGX로
설명한다. 별도 CF4++ 안내는 radial 값의 2026-10-13 수정을 알린다.
같은 페이지에 연결된 author query script를 읽었으며 실행하지 않았다.

다음 전체 payload를 무인증 HTTPS로 받고 길이·SHA·HTTP metadata를 보존했다.
원본은 Git 밖 `/mnt/extdrive/workdir/htt_open_data/cf4/d06_flow_20261018/`이다.

|제품|전체 bytes|HTTP Last-Modified|용도|
|---|---:|---|---|
|CF4gp_new_64-z008_velocity.fits|3,150,720|2023-01-23|grouped finite field 및52배 검사|
|CF4gp_new_64-z008_velocity_cube_error.fits|2,102,400|2023-01-23|스칼라 error field 검사|
|CF4pp_mean_std_grids.npz|167,773,716|2025-05-05|페이지 href의 오래된 제품, 첫 진단 보존|
|new_CF4pp_mean_std_grids.npz|167,773,886|2026-10-13|공식 script가 요구하는 별도 수정 제품|

페이지 링크의 label 및 script는 `new_CF4pp_mean_std_grids.npz`인데 실제 href는
`CF4pp_mean_std_grids.npz`였다. 실제로 두 URL 모두 존재하며 서로 다른 bytes다.
처음 받은 href 제품은 2025-05-05 ETag를 유지했고, 그 radial mean은 declared
XYZ 성분을 voxel-center 반경 방향에 투영한 값과 대략[-4696,+3367]km/s나
달랐다. 이 결과를 수정된 radial field라고 받아들이지 않았다.
공식 script에 명시된 파일을 별도로 Range probe했더니 수정일2026-10-13,
크기167,773,886을 확인했고 이 파일을 전체 확보했다. 파일명을 임의로 alias하거나
이전 파일을 덮어쓰지 않았다. 정확한 URL·SHA·길이·ETag·시간은
`ACQUISITION_RECEIPT.json` 및 최종 `D06_RESULT.json`에 있다.

수정본 SHA는 `b2c8c695c522c286d330a81774334829a2f8b92544990c6978cd8b0d4d43bf3f`,
구 href 제품은 `78c0515c8330066a034f5e8afb3663e6c81ddf033db302a921c662344639bc91`다.
수정 archive의 실제 keys는 `d_mean,d_std,vr_mean,vr_std,v_mean,v_std,N`이며,
공식 예제는 여전히 이전 `_CF4pp` 접미사를 기대한다. 이 API 차이도 실제 발견했다.
scalar `N=9739`의 의미는 query script에 없으므로 기록만 하고 공간 해상도에 쓰지
않았다. 공간128³은 배열 shape와 author의 query 규칙에서 확인한다.

처음 linked 제품의 계산 결과는 `STALE_LINKED_NPZ_DIAGNOSTIC.json`이며
수정본으로 자격을 얻지 못한 탐색적 기록이다. 당시 generator와494-host ledger는
외부 폴더의 `FIRST_LINKED_NPZ_GENERATOR.py` 및
`STALE_LINKED_NPZ_HOST_QUERIES.csv`로 보존했다. 이 파일의 이전
`corrected` 표기는 실패한 초기 자격 가정으로 읽어야 하며, 최종 소비자는
script-named 수정본 결과만 사용한다. 이전 결과를 성공으로 재기록하지 않았다.

## grouped FITS의 정확한 정지 지점

velocity shape은 `[3,64,64,64]`, error shape은 `[64,64,64]`다.
따라서 error 파일은3개 성분의 covariance가 아니다. FITS 헤더에는
BITPIX/NAXIS와 차원만 있고, WCS의 CRVAL/CRPIX/CDELT/CTYPE/CUNIT가 없다.
페이지의52배와 spatial 순서는 검증할 수 있지만 원점·격자 간격·성분 방향의
완전한 contract는 확보하지 못했다. 별도 CF4++의1000/128 geometry를64-grid에
그대로 빌려 쓰지 않았다. grouped 위치 query 및 scalar RMS의 radial 변환은
이 입력 부족으로 `HOLD`다. 원자료 자체의 유한성·범위와52배한 값은 결과에 있다.

## 수정 CF4++ query의 의미

[공식 예제 script](https://projets.ip2i.in2p3.fr//cosmicflows/retrieve_CF4pp_grid_values.py)
는 FK5/J2000 또는 Galactic 좌표를 Supergalactic으로 회전하고,
입력 CMB velocity를100으로 나눈 radius를 사용한다. L=1000, N=128,
delta=7.8125, `(ix,iy,iz)` lookup이다. 이 별도 CF4++에 grouped52배를
적용하지 않는다. 모델의 평균/RMS 성격과 CF4에 대한 의존성은
[CF4++ 원논문 §3](https://arxiv.org/html/2502.01308v2#S3)과 함께 읽는다.

본 코드는 source의 floor-cell query를 구현하면서 cube 밖 좌표를 clip하지 않는다.
각 좌표의 유효 영역은[-500,500)이고, 밖·비유한값은 UNKNOWN/NaN이다.
CF4 galaxy ReadMe의 J2000 host RA/DEC, CMB Vcmb를 사용했다. 수치 radius는
Vcmb/100 h^-1Mpc인 redshift-space proxy이며 실제 comoving 거리 추정이 아니다.
Astropy FK5/J2000→Galactic→Supergalactic과 독립 Cartesian basis
(북극 Galactic47.37°,6.32°, SGX 기준137.37°,0°)를 비교했다.
이는 좌표 회전 검사이지 물리 optical→kinematic mapping 자격이 아니다.

실제 D03 graph의654 matched rows→494 hostPGC→482그룹을 유지한다.
동일 host·group 또는 같은 source cell을 여러 독립 속도로 세지 않는다.
대체 입력으로 Pantheon SN RA/DEC와 zCMB를 query한 결과도 보존해 source
좌표·redshift 차이에 따른 cell 변경을 드러낸다. 이것을 더 정확한 위치라고
선택하거나 관측 유속을 새로 추정하는 데 쓰지 않는다.

민감도는 선택한 `d_proxy=(cz-u)/100`의 정확한 대수식
`delta_mu_proxy=5log10((cz-u)/cz)`다. cz>0 및 cz-u>0에서만 정의한다.
u=0이면0, 양의 outward u는 음의 proxy shift가 되는 부호를 테스트했다.
`u_mean±RMS`는 pointwise 시나리오이며 confidence interval, 공동 realization
envelope 또는 물리 finite-z remainder bound가 아니다. 이미 배포된 D03
MU_SH0ES/CF4 distance를 수정하지 않았다.

수정본의 실제 계산 결과는 다음과 같다.

수정본 전체2,097,152 voxel에서 radial 평균과 XYZ 평균의 voxel-center 투영의
최대 차이는 **7.28e-12km/s**로, 구 제품의 수천km/s 불일치가 해소됐다.
새 radialmean의 배열 위치/부호/성분 해석을 이 불변량으로 검증했다. old→new
vr_mean 차이는[-3367.29,+4696.26]km/s, vr_std는[-170.78,+632.43]km/s였다.
density 평균과 RMS는 최대3.3e-9, Cartesian mean은2.25e-6km/s 이내의
작은 수치차이였지만, Cartesian RMS는 최대12.11km/s 바뀌었다. 정확한 이유를
추측하지 않으며, 'radial만 바뀌고 나머지 bytes가 동일'이라고 쓰지 않는다.
SHA 차이는 제품/버전 identity이며 그 자체가 scientific-integrity failure는 아니다.

좌표 회전의 독립 basis 최대 오차는8.64e-16이다. D03 host494개 모두 cube 안의
양의 radius에 있었고, 고유 source cell은460개였다. 전체654 matched SN rows는
482개의 그룹 및494 host를 반복 사용하므로654개의 독립 유속이 아니다.

|실제494-host query|최소|16%|중앙|84%|최대|
|---|---:|---:|---:|---:|---:|
|수정 radial mean km/s|−1435.30|−500.44|−15.09|316.81|1513.27|
|수정 radial RMS km/s|20.13|42.17|86.30|236.96|788.86|
|u/cz|−0.30996|−0.05724|−0.00221|0.05111|0.73248|
|H100 proxy shift mag|−2.86325|−0.11393|0.00479|0.12088|0.58629|

모든494개에서 mean±RMS의 chosen proxy도 양의 argument를 유지했다. 그 중앙값은
u+RMS에서−0.02078mag, u−RMS에서+0.03081mag이다. 가장 가까운 일부 대상에서는
|u/cz|가 작지 않으므로 low-z 선형 perturbation으로 근사하지 않았다. 위 exact
log는 선택한 proxy 안에서만 exact이며 물리 광도거리 보정의 정확성 주장이 아니다.
Pantheon SN 위치/zCMB로 바꾸면654행 중53행이 다른 voxel에 들어가고 mean 유속의
차이는[-462.87,+413.79]km/s였다. 이 효과는 위치/깊이/voxelization 선택 민감도이며
새 독립 관측 차이가 아니다. source radial 값은 voxel-center 방향에 대한 것이며
coarse cell 안 host의 실제 방향으로 다시 투영한 측정값으로 부르지 않는다.

`D06_HOST_FLOW.png/.pdf`는 고유494 host의 query값과 proxy 민감도를 보여준다.
점마다 이미 얻은 RMS를 색으로 나타내며 joint error bar나 confidence region을
그리지 않았다. 전체 host ledger는 외부 폴더의 `D03_HOST_FLOW_QUERIES.csv`이며
최종 JSON에 path/494행/SHA를 기록했다.

## 재현과 상태

```bash
.venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D06_FLOW/acquire_flow.py
.venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D06_FLOW/flow_control.py
.venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D06_FLOW/test_flow_control.py
```

첫 analysis session54273은 HTML을UTF-8로 읽어 UnicodeDecodeError/exit1이었다.
페이지의 선언은ISO-8859-1이므로 reader만 수리했고 원본은 바꾸지 않았다.
`FIRST_FAILURE.txt`에 보존했다. linked NPZ 진단 session43666 exit0는
수정본 scientific admission이 아니다. 웹 A&A 본문403도 남겨 source 접근성의
차이를 구별했다. 통계·물리 주장 기준을 낮춰 실행 성공으로 만들지 않는다.

수정본의 첫 schema 실행51284는 old key를 기대한 KeyError, 이어65337은
metadata N을 resolution이라고 잘못 해석한 guard로 exit1이었다. 실제 keys와
N의 역할 미정을 검사하고 두 오류를 `FIRST_FAILURE.txt`에 남겼다.
최종 수정본 처리 **session55325 exit0**, 전체 affected suite **8tests PASS
(0.51s)**. 좌표/경계/부호 준비 검사는 앞서4PASS였다. 수정 전후 source 보존,
정확 raw-cell query, whole-host/그룹/cell counts, hard outside-domain rejection,
NaN 보존, corrected projection invariant,52배 및 groupedWCS HOLD,
D03 source seal을 검사했다. 원래 large fit 또는 전체 repository suite는 재실행하지
않았다. PNG를 실제 열어 좌표·점·범례·전체 outlier 범위를 확인했다.
runtime label은 model self-description을 요청/관측 증거로 쓰지 않도록 고쳤다.
동일 source의 작은 aggregate generator를 이 metadata 수정에 맞춰 다시 실행하고
candidate freeze 후 부모의 독립 review로 넘긴다.

metadata-refresh82494가 끝나기 전에 final identity tests87057을 먼저 실행한
작업 순서 오류도 보존했다.7PASS/1FAIL은 stale JSON의 generator SHA가 갱신된
소스와 다름을 올바르게 검출한 것이며 freeze는 실행되지 않았다. 갱신 완료를
기다려 같은 source/identity tests와 freeze만 다시 수행한다. raw 입력이나 수치
결과의 불일치를 숨기거나 과학 검사를 완화하지 않았다.

최종 metadata-refresh82494는exit0으로 완료했다. 그 완료 후 실행한26722는
**8PASS/7.58s,exit0**이며 JSON generator seal·외부 host ledger·입력 identity가
모두 최종 파일에 맞는다. 수치 연구는 더 실행하지 않고 frozen candidate를 넘긴다.

## 독립 검토 P2의 단일 경계 수리

Fresh Astra consolidated P2는 first candidate
`f52a622f6e8df9774bef25bf6a3b203edb3c613aae3aa8a71ff090c9d3cb231f`의
actual source/quantiles/plot/host 결과를 독립 확인했으나 lookup 경계 결함을
발견해 한 번의 targeted repair를 승인했다. 수정 전에 직접 재현했다:
`floor((x+500)/delta)`는 내부·상단 경계 바로 아래의 인접 float96/128개를
다음 cell로 올렸다. `nextafter(500,-inf)`는 index128, 원문 재현값
`-242.18750000000003`은32가 아닌33이었다.

원래 finite 및[-500,500) mask를 유지하고, 이진수로 정확히 표현되는
`edges=linspace(-500,500,129)`에 대해
`searchsorted(edges,accepted_coordinates,side='right')-1`을 적용했다.
밖의 입력은 clip하지 않는다. 정확한129개 경계와 양쪽 nextafter를 모든 축에서
검사하고, 상하 endpoint와 비유한값을 실제 query에 넣어 범위 밖 접근·0채움이
없음을 확인했다. 원래 predicate의 의미를 바꾸거나 과학 tolerances를 완화하지 않았다.

**targeted suite session1417 exit0:11PASS/4.21s**. 저장된494 host의 SG 좌표를
새 lookup에 통과시켜 모든 cell index가 기존 ledger와 정확히 같음을 확인했다.
최초 RESULT와 최종 RESULT의 모든 과학 필드는 JSON 값 수준에서 정확히 같고,
외부 ledger 및 PNG/PDF도 최초 candidate SHA와 같다. 변경은 lookup 설명,
현재 generator seal 및 수리 provenance metadata뿐이다. **flow_control.run이나
full-grid analysis를 다시 실행하지 않았다.**

최초 `CANDIDATE_INITIAL.json`, `D06_RESULT_INITIAL.json`과 기존 raw failures를
남겼다. 최초 수치 생성 code의 SHA는
`003e6b2eabde6ad64df2790e037cbc298baf275dbe572cf3c9f66d7862b4a4d9`이며
외부 `BOUNDARY_INITIAL_FLOW_CONTROL.py`에도 보존했다. 현재 generator SHA는
`470929fc61b89af3dfead88e40d37d737b18c06ad0f1fe0c2daeb04ce4d458d0`이다.
최종 RESULT의 boundary_repair는 이 원래 수치 producer와 현재 source seal을
따로 기록한다. 같은 Astra reviewer의 단일 repair closeout으로 되돌린다.

원래 H02/H04/S02/S04/K04 HOLD는 그대로다. 이 결과는 실제 공개 source의
누락/오류 경로를 해결하고 조건부 sensitivity 입력을 제공한다. physical flow law,
공통 optical→kinematic response, CF4/Pantheon joint covariance 또는 선택법칙은
여전히 추가 입력이다. 독립 fresh review 및 publication은 부모의 별도 단계다.
