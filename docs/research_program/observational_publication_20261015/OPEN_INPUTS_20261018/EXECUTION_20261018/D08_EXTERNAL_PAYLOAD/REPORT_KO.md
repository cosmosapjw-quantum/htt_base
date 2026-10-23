# D08: 공개된 기존 수치 온도 응답의 실제 intake

Owner obsstat, DIAGNOSTIC_ONLY. Native solver/ODE 없이 공식 저장소가 이미
배포한 BIANCHI v1.1 두 온도 지도를 읽고 유한 회귀와 단위 검사를 실행했다.
[공식 설명](https://astro-informatics.github.io/bianchi/)과 pinned commit
`1c90b9867b96eedf93983e33de72b3394f39d58e`의 README는 이 경로가
dark-energy 없는 legacy VIIh 온도 모형임을 명시한다. 편광 atlas가 아니다.

공식 HTTPS의 README/parameter/license/FITS 두 개를 Git 밖에 받았다.
`SOURCE_MANIFEST.json`은 실제 다운로드 소비자 입력이며 `ACQUISITION.log`는
성공 기록이다. 두 FITS는 204480 bytes씩, RING NSIDE64, 49152개 유한
float32 값, simulation 한 열뿐이다. Git blob identity를 실제 bytes에서
계산해 official pinned tree의 두 blob과 비교했다. SHA256도 RESULT에 있다.
TUNIT/COORDSYS는 둘 다 없으며 절대 하늘 frame은 UNKNOWN으로 유지했다.
[같은 pinned 공식 문서의 Testing절](https://raw.githubusercontent.com/astro-informatics/bianchi/1c90b9867b96eedf93983e33de72b3394f39d58e/doc/index.html)
은 param.par 실행 결과가 단위에 따라 test 파일 중 하나와 같아야 한다고
명시한다. 따라서 parameter binding은 **upstream-declared**이며, 이 세션의
독립 실행 검증은 NOT_RUN이다. 최초 보고의 '근거 없음'은 독립 리뷰의
구체 finding에 따라 이 source-defined 관계로 바로잡았다. 코드는 실행하지 않았다.

두 원본의 최소제곱 배율은 2724.999989152853, 2725 고정 배율의 상대
잔차는 5.6100806e-8이다. 이는 공식 설명의 기본 DeltaT/T와 mK 변환
Tcmb=2.725K에 수치적으로 부합한다. float32 파일끼리의 단위 일관성
기준은 relative 2e-6로 명시했다. 실제 물리 gate의 허용오차가 아니다.

파일의 각도 chart에서 full-sky pixel design l=0…12를 함께 회귀했다.
169개 실수 열, rank169, condition1.00065717; 입력 RMS1.93233371e-6,
회귀 잔차 RMS2.59587033e-7, 잔차 비율0.13433861이다. 그러므로 이
projection을 원지도의 정확한 all-l harmonic transfer라고 부르지 않는다.
계수는 `[Y_l0,sqrt(2)ReY_lm,sqrt(2)ImY_lm]` 열의 유한 회귀 좌표다.
관측 mask·지도와 맞추거나 이 지도의 frame을 Galactic이라 추정하지 않았다.
PNG/PDF에는 ell별 계수 제곱합과 단위 잔차가 표시된다.

실행 및 좁은 검증:

```
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D08_EXTERNAL_PAYLOAD/legacy_intake.py
.venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D08_EXTERNAL_PAYLOAD/test_legacy_intake.py
```

이 새 입력의 소비자는 external legacy processing 연구뿐이다. E/B는 미공급이며
0으로 채우지 않았다. global-history/polarized all-m response, frame/beam,
source-calibrated cosmology와 coefficient mapping이 없어 원래 B02는 HOLD다.
기존 AniCLASS notebook/chains/movies의 부적합 판정을 재계산하지 않았다.
공개 대체자료에서 발견한 한 실수치 fixture이며 모든 다른 atlas가 없다는
보편적 주장도 하지 않는다. 요청 Sol/high, 실제 runtime 관측 UNKNOWN.
새 clone/worktree, native solver/ODE, 과학 노드 승격은 없다. 이 수정은
source-binding metadata만 고쳤으며 수치 계산을 불필요하게 재실행하지 않았다.
독립 검토 closeout 대기.
