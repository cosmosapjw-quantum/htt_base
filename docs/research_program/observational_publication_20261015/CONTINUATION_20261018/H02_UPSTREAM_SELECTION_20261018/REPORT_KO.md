# H02 공개 TF 원천 표의 실제 선택·그룹·파장 경로 연결

2026-10-18. Owner `htt`; scope `actual release membership and contributor diagnostics`; status `DIAGNOSTIC_ONLY`; transfer source `none`. H02 acceptance **HOLD**. 기존 primary checkout과 branch `research/htt-sixpaper-goals-robustness-20261018`, 시작 HEAD `9616f5341e215fcea21b7977a128162842a4f3a4`에서 실행했다. Requested worker `gpt-6.1-sol/high`, observed model/effort `UNKNOWN`. Parent가 별도 독립검토와 publication을 담당한다. 이 패킷은 제출 승인이나 물리 추론이 아니다.

## 새로 확보하고 계산한 결과

공식 [CDS J/ApJ/902/145](https://cdsarc.cds.unistra.fr/ftp/J/ApJ/902/145/ReadMe)의 ReadMe와 압축 배포된 table1/table4를 실제로 내려받았다. ReadMe 날짜는 `21-Apr-2022`이며, 논문은 `2020ApJ...902..145K`, `arXiv:2009.00733v2`다. 일반 `.dat` 주소 두 개의 HTTP404를 보존하고, 같은 공식 배포의 `.dat.gz`에서 HTTP200을 받았다. 브라우저 ReadMe 접근 실패와 실제 로컬 HTTPS 다운로드 성공은 구분한다.

Raw는 Git 밖 `/mnt/extdrive/workdir/htt_open_data/cf4/upstream_20261018/`에 create-only로 저장했다. [ACQUISITION_RECEIPT.json](ACQUISITION_RECEIPT.json)은 정확한 URL, 시각, 상태, 압축 전송 크기, 저장한 해제 바이트의 크기·SHA256 및 첫 HTTP 오류 본문을 담는다. 저장 파일의 SHA는 다음과 같다.

| source | bytes | SHA256 of decompressed source |
|---|---:|---|
| ReadMe | 19,739 | `45fa3cca5346aff29bcf9785e7b08e8ab34b1d67e80b359c0d28bdbd18e42581` |
| table1.dat | 5,368,500 | `ac679ab4548484b02dc17a1cc09bbe8f0a68f45bd5c44efc7302fcabc32d8926` |
| table4.dat | 912,183 | `f4aa0ba0efe7d7a14f044a76ef37f5a033e2788923d586c2d15ed248939455f2` |

기존 CF4 table2/3와 selected NPZ의 고정 SHA를 재사용했다. 이전 H02 회귀·LP·calibration-radius 계산은 반복하지 않았다. 원천 표의 byte-by-byte ReadMe에서 column schema를 읽어 upstream galaxy `PGC → CF4 table2 PGC → 1PGC → selected 35,970 groups`로 연결했다. 중복 PGC는 오류이며 임의 alias/group 재할당은 없다. 공개 패킷에는 aggregate JSON·그림만 들어간다.

## 10,737 대 9,792는 단순한 945개 탈락 목록이 아니다

실제 배포에는 table1 10,737행, table4 9,792행이 있다. 그러나 PGC 교집합은 **9,790개**, table1-only는 **947개**, table4-only는 **2개**다. Table4의 **11개 행은 DMbest 및 모든 band distance가 비어 있다**. 따라서 유효 DMbest가 있는 행은 **9,781개**다. 이 차이를 숨기거나 11개를 0으로 채우지 않았다. 두 table4-only PGC는 CF4 table2에는 연결되지만 selected z window 밖에 있다. 개별 rejected reason/동일 PGC alias를 원천이 제공하지 않았으므로 추정하지 않는다.

| upstream cohort | CF4 galaxy에 없음 | CF4 group release에 없음 | selected 밖 그룹 | selected 그룹에 연결된 은하 |
|---|---:|---:|---:|---:|
| all table1 | 1,144 | 1 | 1,919 | 7,673 |
| all table4 records | 434 | 0 | 1,782 | 7,576 |
| finite DMbest | 433 | 0 | 1,775 | 7,573 |
| table1-only | 710 | 1 | 139 | 97 |

유효 DMbest 7,573개는 **6,697개 selected 그룹**에 연결된다. Table1-only 97개도 다른 source/version을 통한 CF4 존재 가능성을 남기며, 단순한 관측 미검출 집합으로 부르지 않는다. Table4의 blank 행 세 개가 selected 그룹에 연결되므로, 모든 9,792행을 거리측정으로 세면 6,699개 그룹으로 과대 집계된다.

## 실제 파장·품질·창 구성

Optical은 table4의 r/i/z modulus 중 하나 이상이 실제로 존재하는 경로다. W1-only는 optical modulus가 없고 W1 modulus가 있는 경우다. 이 분류는 원천 측정의 band availability이며 pooled CF4 DMzp의 순수 방법 분류가 아니다.

| 원천 band route | table4 은하 | selected 은하 | selected groups |
|---|---:|---:|---:|
| optical + W1 available | 2,025 | 1,430 | 1,101 |
| optical only | 4,747 | 4,087 | 3,854 |
| W1 only | 3,009 | 2,056 | 1,836 |
| no band distance | 11 | 3 | 3 |

하나의 그룹에는 여러 경로의 은하가 들어갈 수 있다. Optical-only와 optical+W1은 77개 그룹, optical+W1과 W1-only는 11개, optical-only와 W1-only는 10개 그룹에서 중첩된다. Optical 경로 합집합과 W1-only의 중첩은 17개다. 따라서 그룹 수와 working-weight 비중을 단순 합하지 않는다. JSON에는 전체 overlap matrix를 저장했다.

기존 Gaussian group windows `(z_c=.025,.04,.06,.08; width=.012)`와 base window를 재사용했다. 각 route의 supporting group을 한 번씩 세고 `kernel/e_DMzp²`의 해당 그룹 질량을 전체 selected-group 질량으로 나누었다. 이는 pooled distance의 **선언된 working weight 비중**이며 upstream 측정의 정보비중·calibration influence·선택 확률은 아니다.

| support | all | z=.025 | z=.040 | z=.060 | z=.080 |
|---|---:|---:|---:|---:|---:|
| finite upstream DMbest | 24.815% | 49.644% | 27.617% | 4.198% | .288% |
| optical only | 13.764% | 27.998% | 18.446% | 3.150% | .230% |
| optical + W1 | 8.063% | 16.327% | 8.673% | 1.152% | .057% |
| W1 only | 7.409% | 14.487% | 5.468% | .377% | .006% |

실제 source coverage가 깊이에 따라 크게 달라진다. 이 차이만으로 깊이별 apparent coefficient 차이를 flow/cosmology로 해석할 수 없다. Window들은 중첩되며 독립으로 세지 않는다. JSON은 kernel 질량, Kish effective group count, weighted direction mean도 보존한다.

QSflag/QWflag는 SDSS/WISE photometry quality다. Table1 전체와 실제 DMbest 교집합 및 selected subset의 모든 quality/attenuation histogram과 6×6 quality cell을 저장했다. 예를 들어 QSflag=5/QWflag=0 cell은 table1 4,179개 중 유효 DMbest 3,856개이고, QSflag=5/QWflag=5는 1,316개 중 1,238개다. 이 비율은 **이미 선택된 table1 안의 release inclusion fraction**이다. 초기 survey targeting/detection의 completeness가 아니다. Rsrc는 attenuation 계산 입력(예측 W2/관측 W1/관측 W2)을 나타내며 HI telescope/ADHI/ALFALFA origin code가 아니다. Table1에도 linewidth error>20 또는 heliocentric velocity>15000인 항목이 있어, 논문 단계별 prose cut을 현재 한 column에 기계적으로 재적용하지 않았다.

## 방법·보정 genealogy에서 실제로 연결된 부분

유효 upstream DMbest가 연결된 6,697개 그룹의 pooled partition은 TF 6,118, FP 81, SN 71, OTHER 427이다. 이 partition은 순수 독립 TF sample을 뜻하지 않는다. 이들 그룹에는 released TF modulus가 모두 존재하지만 positive count도 명시된 것은 6,600개이고 97개는 count가 비어 있다. FP는 positive modulus/count 398개 및 count-missing 7개, SNIA는 173개, CAL은 4개다. Missing method count를 0으로 만들지 않고 별도 필드에 보존했다.

연결된 selected 은하 7,573개 중 7,572개에 CF4 table2 TF modulus가 있다. 이것은 identity+released-method 연결이며, 해당 2020 측정이 수정 없이 실제 MCMC에 들어갔다는 ingest receipt는 아니다.

원래 2020 DMbest와 나중 CF4 table2 registered TF가 모두 있는 **전체 연결 은하**의 descriptive 차이도 저장했다. `CF4 DMtf − 2020 DMbest`의 median과 16–84% quantile은 optical+W1 1,961개에서 `.025 [−.175,.275] mag`, optical-only 4,508개에서 `−.025 [−.275,.195] mag`, W1-only 2,872개에서 `.025 [−.165,.215] mag`다. 서로 다른 calibration/merge version 사이의 차이이며 독립 raw calibration error, covariance, uncertainty bound 또는 empirical tau가 아니다.

[Kourkchi et al. 2020 §§II, III.4, IV](https://arxiv.org/html/2009.00733v2)는 초기 후보와 품질·inclination 선택, luminosity/outlier exclusion, 광학 우선 DMbest, 공통 HI linewidth와 band 간 조정을 설명한다. Published fixed table과 갱신 가능한 EDD table도 구별한다. 이 원전의 calibration/regularization은 관측된 band 간 일치를 독립 null 검증으로 취급할 수 없음을 뒷받침한다. 이번에는 고정 CDS release를 썼으며 현재 EDD를 동일 version으로 대체하지 않았다.

## 검증과 정확한 재개 조건

```bash
.venv/bin/python docs/research_program/observational_publication_20261015/CONTINUATION_20261018/H02_UPSTREAM_SELECTION_20261018/run_validation.py
```

실제 source analysis exit0, focused unittest **10 PASS**, plot exit0. Tests는 ReadMe range/single-byte schema, trailing missing field, duplicate PGC rejection, missing/zero 구분, optical/W1 classification, missing galaxy/group status, 반복 은하의 group weight 중복 방지, empty support, source hash tamper 및 독립 fixed-slice 방식의 실제 947/2/11·7,573/6,697 replay를 포함한다. [RUN_RECEIPT.json](RUN_RECEIPT.json)에 raw stdout/stderr와 명령·cwd·실행 시각·exit status·코드 SHA를 보존했다. Python3.12.3, NumPy2.5.4, Matplotlib3.11.2. 그림의 분모 문구만 정정한 후 `run_validation.py --plot-only`로 이전 분석·tests를 재실행하지 않고 rerender했다. PNG는 시각 점검했다.

[FIRST_FAILURE.txt](FIRST_FAILURE.txt)는 Lrecl을 exact width로 본 첫 parser failure, 잘못 가정한 nested sample failure 및 optional count 처리 failure를 보존한다. Lrecl은 최대폭이며 blank tails는 missing 그대로 읽는다. Source bytes/PGC/tolerances는 변경하지 않았다. No solver/ODE, 이전 완료 실험 재실행, 환경 설치, canonical completion/status 변경, commit/push는 수행하지 않았다.

| claim / input | 이번 상태 | 범위·남은 입력 |
|---|---|---|
| actual public table1/table4 source | acquired; exact source executed | ReadMe/schema와 source SHA 고정 |
| upstream PGC→CF4 PGC→selected group | implemented; 10 tests | missing/blank/version 차이와 aggregate만 보존 |
| quality/band/window composition | DIAGNOSTIC_ONLY | within-release inclusion, grouped pooled working weights |
| shared calibration genealogy | partially linked | actual band/method/group overlap; covariance 미확보 |
| true selection law | UNKNOWN | 초기 targeting/detection 및 rejected/missing ledger, 각 normalization 필요 |
| per-galaxy HI survey ancestry | UNKNOWN | ADHI/ALFALFA 등 contributor/version ledger 필요; Rsrc로 대체 불가 |
| shared calibration/velocity covariance | UNKNOWN | common/relative/angular nuisance covariance 또는 정당한 bound, velocity model 필요 |
| independent calibration holdout/source null | NOT_RUN | 원천 selection·grouping·calibration을 동일하게 통과한 qualified simulation pipeline 필요 |
| physical angular anchor/H02 acceptance | unanchored / **HOLD** | source-qualified law와 독립 심사 없이는 admission 없음 |

Kill-switch는 이 자료를 physical p-value/posterior, empirical angular calibration bound, measured velocity/shear, 또는 geometry/family 판정으로 승격하는 모든 해석이다. 이번 unit의 구체적 완료는 공개 원천 입력 확보와 실제 연결·구성 진단이며 H02 canonical completion은 아니다.

