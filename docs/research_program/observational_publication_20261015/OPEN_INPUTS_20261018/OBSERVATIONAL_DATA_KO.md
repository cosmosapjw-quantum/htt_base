# 필요한 관측자료와 실제 접근 상태

판정 시각2026-10-18. `공개 페이지`, `헤더 일부 수신`, `전체 payload 수신`, `통계모형 자격`은 서로 다르다. 원본 제품은 Git 밖 기존 `/mnt/extdrive/workdir/htt_open_data`에 보관한다. 이미 완료된 CF4 및 Planck full/HM/OE,8쌍 cache는 다시 받거나 다시 처리하지 않는다. 여기서 확보한 scratch 원본이 로컬에 없다면 같은 manifest로 취득한다.

| 우선순위 / 자료 | 필요한 노드 | 이번에 확인·실행한 것 | 추가로 필요한 것 |
|---|---|---|---|
| 1. [CF4 H I 관측 대상/실패 목록](https://cdsarc.cds.unistra.fr/ftp/J/A+A/646/A113/ReadMe), table2/table4 | H02,S02,K04 | 무인증 전체GET. GBT628대상=적합385+기타품질22+혼동29+비검출192. Table4 GBT385와 정확히 같은 PGC집합 | 기존 TF J/ApJ/902/145 및 CF4 galaxy/group에 join. 이628대상의 조건부 선택과정부터 모델링; 전체 CF4 parent probability로 일반화하지 않음 |
| 1. [Pantheon+ 거리·STAT+SYS covariance](https://github.com/PantheonPlusSH0ES/DataRelease/tree/c447f0fea703fcd0fff57de5000947b5ca81286b/Pantheon%2B_Data/4_DISTANCES_AND_COVAR) | H02,H04,S04,K04 | 무인증 전체GET:0.58MB+33.28MB.1701행과1701²행렬 파싱,1543고유CID문자열/77calibrator행 확인 | CF4/SN 이름과 calibrator genealogy 교차연결, covariance 행순서 유지, shared calibration joint처리. 고유CID 수를 canonical 고유천체 수로 부르지 않음 |
| 1. [SMICA PR3 weights](https://wiki.cosmos.esa.int/planck-legacy-archive/index.php?title=SMICA_propagation_code) | L03 | ESA무인증 전체GET74,625,775bytes, tar목록·가중치/transition/beam처리 소스 읽음; 실행 안함 | 실제 estimator의 고정weights·beam response 연결. Foreground fitting/weights 재선택 법칙은 별도 |
| 1. [PR3 HM1/HM2/OE1/OE2 noise simulations](https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/CMB_maps) | L03 | 네 ID00000 제품 모두 무인증HTTP200와 FITS헤더5760bytes. I/Q/U,RING,NSIDE2048,K_CMB 확인 | 각 제품 약604MB data section의 전체파일 획득·semantic검사. upstream 같은 실현/seed 관계, CMB split response, foreground/statistic coverage 추가 |
| 2. [HFI RIMO beam archive](https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/HFI_RIMO_BEAMS_R3.01.tar.gz) | L03 | Range206,gzip헤더,총86,556,876bytes 확인 | beam conventions 및 유효 response검사. 이 파일만으로 비등방/pixel-dependent split transfer가 완성되지는 않음 |
| 2. [Gaia-CRF3 membership](https://www.cosmos.esa.int/web/gaia/edr3-frame) + [ARI public TAP](https://gaia.ari.uni-heidelberg.de/tap) | K03 | 회원목록 gzip56.06MB의 일부GET, 전체와 같은 join의 TOP2 성공 | 전체 proper motion+오차+상관계수, overflow 없는 결과, frame-rotator 포함여부/공간상관. DR3/EDR3 astrometry는 독립 재관측 아님 |
| 2. [VLBA713 proper motions](https://cdsarc.cds.unistra.fr/ftp/J/ApJS/233/3/ReadMe) | K03 | table6전체GET99,085bytes,713행 | Gaia/ICRF 중첩·radio jet·NNR frame연결. 누락된 cross-component covariance를0으로 가정하지 않음 |
| 2. [공개 CF4 grouped flow grids / CF4++](https://projets.ip2i.in2p3.fr/cosmicflows/) | H04,K04 | grouped velocity부분FITS와 CF4++부분NPZ/예제소스 확인 | 기존CF4와 동일자료 의존성, 좌표/단위, jointcovariance. CF4++의vr_data는2026-10-13수정본 사용; mean/std를posterior draw로 다루지 않음 |
| 3. [Pantheon+ selection simulations](https://github.com/PantheonPlusSH0ES/DataRelease/tree/c447f0fea703fcd0fff57de5000947b5ca81286b/Pantheon%2B_Data/6_SIMULATIONS) | H02,H04 | SIM0001전체GET0.51MB,3235모의행. 원천10FITRES제품과 LOWZ설정 확인 | FITRES에RA/DEC없음. 외부SIMLIB/KCOR/selection효율 필요; 단독 directionalnull로 사용 금지 |
| 3. [SH0ES 거리사다리 행렬](https://github.com/PantheonPlusSH0ES/DataRelease/tree/c447f0fea703fcd0fff57de5000947b5ca81286b/SH0ES_Data) | H02/S02앵커 연구 | L/y공개파일과README 확인 | C의133byte Git객체는 LFS pointer. 실제 covariance를 얻어 검증해야 함; pointer를FITS로 처리하지 않음 |
| 별도 외부 이론 입력: polarized all-m atlas / global-history response | B02,V03 | 공개AniCLASS/Zenodo후보 검토. 영상·코드·chain은 수치atlas와 구분 | 적격한 기존계산 결과를 찾으면 units/frame/IC/parameter/equivalence를 검증해 사용. 이번에 충분한 payload는 확보하지 못함 |

## 획득 계획과 실행

표의 관측자료 대부분은 추가 계정 없이 받을 수 있다. 새 NERSC/CMB-S4 portal은 metadata가 공개여도 파일에Globus 인증을 요구하므로 현재 우선경로에서 제외한다. ESA직접PR3 endpoint가 우선이다. `ACQUISITION_MANIFEST.json`은17개 직접 제품을 위한 실행 가능한 목록이며, 더 넓은 조사 범위는 cmb/DATA_CMB.json과distance/DATA_DISTANCE.json에 보존한다.

```bash
.venv/bin/python scripts/htt_fetch_open_inputs.py
.venv/bin/python scripts/htt_fetch_open_inputs.py --fetch
# 약2.42GB의 새 split-noise 한 세트. 실제 bytes는 헤더/다운로드로 확인한다.
.venv/bin/python scripts/htt_fetch_open_inputs.py --fetch --budget-gib 4 \
  --ids SMICA_NOISE_HM1_00000 SMICA_NOISE_HM2_00000 \
        SMICA_NOISE_OE1_00000 SMICA_NOISE_OE2_00000
.venv/bin/python scripts/htt_fetch_open_inputs.py --fetch \
  --ids GAIA_CRF3_MEMBERSHIP HFI_RIMO_BEAMS_PR3 CF4_GROUPED_VELOCITY CF4_GROUPED_VELOCITY_CUBE_ERROR
```

기본 실행은plan,`--fetch`는 사용자 지시에 따라 Codex가 스스로 실행한다. 추가 승인 질문이 아니다. HTTPS/호스트목록·예산·여유공간·길이/hash/형식검사를 수행하고 receipt가 맞는 기존 파일을 재사용한다. 원본·미확인 파일을 덮어쓰지 않으며 내려받은 코드를 실행하거나 archive를 자동추출하지 않는다. 현재 기본 자동항목은 약127MB의 최대전송예산이다(실제 합계는manifest출력 기준). 대용량 항목은 위와 같이 한 세트씩 실행한다. 대용량 원본과 observer map의 기존 range-resume 도구를 섞지 않는다: 새 도구는 interrupted `.part`를 보존하지만 자동 이어받기를 구현하지 않았다. 전송 중단 후에는 원인과 `.part`를 먼저 검사하고, ETag/길이/Content-Range를 검증하는 이어받기를 구현하거나 정당한 새 전송을 선택한다. 같은 실패를 반복 다운로드하지 않는다.

## Gaia 전체 질의

`GAIA_CRF3_QUERY.adql`에는 이번TOP2에서 실제 확인한 열만 사용하는 전체join질의가 있다. TOP를 붙인 smoke 결과를 전체 표본으로 쓰지 않는다. ARI의 공개 UWS async로 제출하고 VOTable의QUERY_STATUS/OVERFLOW, 반환행 수와CRF3회원수를 대조한다. CSV만 받으면 overflow메타데이터가 없으므로 명시적source_id구간 분할·구간별COUNT와 회원집합 비교가 필요하다. fullquery 자체는 이 세션에서 실행하지 않았다. 회원표에서 ICRF/프레임 제작 포함여부를 연결하고 형식상2×2 covariance와 천체 사이 공간상관을 구분한다.

## 새 Pantheon 행렬 검사에서 드러난 것

실제 raw covariance의 최대 비대칭은 `3.0e-8 mag²`로 초기1e-10엄격검사가 실패했다. 원본은 그대로 보존했다. 별도로 명시한 `(C+Cᵀ)/2`의 최소고유값은0.00080278165mag², raw와의Frobenius차이는2.3227e-7mag²이다. 이것은 입력 진단이며 자동으로 likelihood covariance를 교체했다는 뜻이 아니다. 동일CID191쌍의 symmetric-part 상관 중앙값은0.407775로, 행을 독립으로 취급하면 안 된다는 구체적 경고다. CIDalias를 검증하기 전에는 천체의 독립성에 대한 결론도 제한한다. 모든 수치와 생성 코드는 PANTHEON_INPUT_RESULT.json/check_pantheon_inputs.py에 있다.

## 자료를 얻어도 남는 조건

H02의 공통angular calibration은 relative method차이만으로 고정되지 않는다. S02/K04에는 common-congruence optical→kinematic응답과 finite-z/flow remainder가 필요하다. L03에는 동일처리된 jointsplit/foreground/selection법칙과 통계량별coverage가 필요하다. B02/V03의전송은 외부의이미계산된결과를 받아야 한다. 이 조건을 데이터다운로드 성공으로 대체하지 않고, 확보한부분으로 가능한조건부·부분식별 연구를 계속한다.
