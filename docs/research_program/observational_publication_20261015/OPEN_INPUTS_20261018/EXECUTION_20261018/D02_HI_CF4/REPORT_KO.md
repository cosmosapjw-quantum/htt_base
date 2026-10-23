# D02: 실제 GBT628 → TF2020 → CF4 연결과 표적 내부 선택 진단

2026-10-18. Owner `htt`, `DIAGNOSTIC_ONLY`, exploratory actual-data artifact.
Transfer `none`. 용도는 관측된 GBT628의 결과·배포본 구성과 조건부 예측
진단이다. 물리 covariance 또는 우주론적 null 검정은 수행하지 않았다.
전체 CF4 targeting/detection probability, 독립 보정 또는 물리 비등방성의
근거로 사용하지 않는다. 원래42노드 수용기준과 H02/S02/K04 HOLD는 유지한다.

Intake `1528ebd3c4ace48a561b9dcaa6d5f891121a22a5`, 기존 primary checkout과
`research/htt-open-input-theory-20261018`에서 실행했다. 요청 runtime은
`gpt-6.1-sol/high`, 독립 관측은 `UNKNOWN`이다. Python `.venv/bin/python`,
NumPy2.5.4, BLAS/OMP/MKL 각2threads. 하위 agent, 새 clone/worktree,
solver/ODE, 기존20fits/TF 전역 진단 재실행은 없었다.

## 원자료와 실제 연결

원자료는 parent D01이 받은 [Dupuy et al.의 CDS J/A+A/646/A113](https://cdsarc.cds.unistra.fr/ftp/J/A+A/646/A113/ReadMe)
ReadMe/table2/table4다. 배포 ReadMe는 입력 `Vhel`을 LEDA 값으로,
`v50`, linewidth, flux, S/N을 측정 결과로 구별한다. 세 HI SHA,
이전에 검토된 TF2020 J/ApJ/902/145 ReadMe/table1/table4 SHA,
CF4 J/ApJ/944/94 ReadMe/table2/table3 SHA, 선택 NPZ
`86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`를
모두 검사했다. 정확한 값과 생성 코드 SHA는 `D02_RESULT.json`에 있다.
기존 검토 parser를 import했지만 기존 연구 run/fit은 호출하지 않았다.
현재 source 의미의 근거는 실제 받은 공식 CDS ReadMe다. 웹도구와 stdlib의
저널 본문 요청은403, 웹 CDS는 접근 실패했다. 첫 보조 요청은 requests
미설치로 실패했고 dependency를 추가하지 않았다. 이 실패들은 결과에 보존했다.

628개를 전부 유지했다. 결과는 적합385, 기타 검출품질22, 혼동29,
비검출192이며 네 집합이 서로소이고 전체다. 적합385의 PGC 집합은
HI table4의 GBT385 집합과 정확히 같다. e_W50=100/500은 분류에만
사용하며 회귀의 수치 오차 또는 예측자로 쓰지 않았다. ReadMe 설명의
685 adequate 오기는 실제385로 대체한 원본을 만들지 않고 기존 기록을 유지했다.

| GBT 결과 | 대상 수 | TF2020 data+distance | data only | TF 두 표 모두 없음 | CF4 selected | CF4 없음 | selected 밖 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 적합 |385|269|8|108|269|114|2|
| 기타 검출품질 |22|1|0|21|1|21|0|
| 혼동 |29|3|1|25|5|24|0|
| 비검출 |192|1|0|191|7|185|0|
| 전체 |628|274|9|345|282|344|2|

TF data는10,737행, distance는9,792행, CF4 galaxy는55,877행,
group은38,053행이며 frozen selected는35,970개다. 모든 조인은 정확한
PGC→CF4 galaxy의1PGC→group→selected identity로 했으며 alias 추측은 없다.
이 cohort에는 TF distance only나 CF4 group-release 누락 사례는 없었다.
TF의274 matched distance 모두 DMbest가 있었다. 전체 CF4 등록TF는275개,
그중 적합268·기타1·혼동4·비검출2개다. 비검출 한 개는 TF2020에도 있다.
이는 배포 시기·대체 측정·보정 차이가 존재함을 보여준다. 개별 대체 측정의
계보를 확인하지 않았으므로 해당 관측이 그대로 편입되었다거나 품질 거절을
복원했다고 해석하지 않는다.

284개 CF4 galaxy는278개 고유 그룹에 속한다. 선택 그룹은276개이며
6개 그룹에 둘 이상의 표적이 있다. 적합 표적의 selected support는265그룹,
기타1·혼동5·비검출7그룹이다. 적합/혼동 및 적합/비검출 사이 각각1그룹이
겹치므로 그룹 support를 더하면 중복된다. `full_route_counts`와 outcome
그룹 overlap 행렬은 JSON에 있고, 전체628 PGC별 join/결측/예측/fold ledger는
Git 밖 `/mnt/extdrive/workdir/htt_open_data/cf4/D02_HI_CF4_20261018/TARGET_JOIN_AND_OOF.csv`
에 있다. 경로·SHA·628행 수를 결과 JSON에 기록했다.

## 사전 입력과 조건부 모형

원표의 inclination은2개, B magnitude는8개가 없으므로 회귀에서 제외했다.
관측 결과인 v50, linewidth, 오차·sentinel, S/N, flux, 배포 거리 및
CF4 선택 여부도 예측자로 쓰지 않았다. 입력 LEDA `Vhel`만 사용했다.
단, PGC1095542의 Vhel=-1은 공식 sentinel이라는 설명이 없어
`AMBIGUOUS_SOURCE_VALUE`로 보존했다. 값 자체가 주는 물리 깊이를 추측하지
않고 이 한 행의 예측을 UNKNOWN으로 남겼다. 이 규칙은 outcome과 독립적인
원자료 값의 의미에 따른다. 전체 결과/조인은628개, 회귀 점수는627개다.
후속 관측 v50=8352로 대체하지 않았다. 미정 예측질량은1/628이며,
전체628의 평균 예측은 그 한 확률을[0,1]에 둘 때만 구간으로 보고한다.

두 단계는 `D=1{e_W50 !=500}` 및 `A=1{e_W50<=20}`다.
D에는29개 혼동이 포함되므로 secure target HI detection으로 부르지 않는다.
407은 비검출과 혼동을 모두 제외한 단순 count이며 별도 독립 표본이 아니다.
모형은 각각 `logit P(D|T=1,Vhel)` 및 `logit P(A|D=1,T=1,Vhel)`이고,
design은 `[1,(Vhel−10000)/5000]`, 단위km/s, slope L2 penalty1,
intercept 무벌점이다. Hyperparameter tuning은 없었다.
전체 적합확률은 같은 fold의 두 확률 곱이어서 항상 `P(A)≤P(D)`다.

known CF4 group은 통째로 같은 fold에 넣고, CF4에 없는344개는
`unresolved_pgc:<PGC>` 표적 블록으로 배정했다. SHA256 고정5fold,
전체 genealogy622블록 중627 scored domain은621블록이다. 동일 표적·알려진
동일 그룹이 학습/검증에 걸치지 않는다. 미해결344개가 실제로 그룹을
공유하지 않는다는 증거는 없으며 이 한계는 남는다. TF/CF4 배포 거리를
검증 정답이나 독립 보정으로 사용하지 않았다.

|627개 scored-domain 검증|Brier|같은 folds 상수 기본모형|AUROC|
|---|---:|---:|---:|
|D: 비검출 제외, 혼동 포함|0.20896719|0.21333306|0.58009511|
|A: 두 단계 전체 적합|0.23442203|0.23799492|0.56301921|
|A given D:436개 내 적합|0.10386256|0.10366944|0.41102623|

고정 seed2026101802로 whole-block bootstrap300회, 실패0회였다.
각 bootstrap에서 두 단계 coefficient를 함께 다시 적합했다. 검증 score 구간은
저장된 out-of-fold prediction에 조건부인 whole-block 재표집 구간이며,
학습집합 재구성에 따른 모든 crossvalidation 변동을 포괄하지 않는다.
블록의 교환가능성도 작업 가정이다. 물리 속도 covariance 추정이 아니다.
Brier−기본모형의95% 구간은 D `[-0.00943227,0.00130933]`,
전체A `[-0.00807328,0.00126976]`, conditionalA
`[-0.00007143,0.00039341]`로 모두0을 포함한다.
검출의 in-sample slope는5000km/s당 odds ratio0.40494744,
bootstrap95% `[0.23889617,0.68320586]`이나, 이를 우수한 heldout 예측력이나
전체 CF4 선택법칙의 증거로 승격하지 않는다. 검출 뒤 적합성 OR는0.96263439,
구간 `[0.49029411,1.91818011]`이다.

고정 확률 bin calibration에서는 D의 높은 확률 bin34개의 평균 예측0.815634에
관측23/34=0.676471로 과신 경향이 있다. A의 두 occupied bin은254개에서
0.552376 대139/254=0.547244,373개에서0.656179 대246/373=0.659517이다.
적합 conditional 모형의 AUROC0.411과 기본모형보다 큰 Brier는 이 단일 입력으로
추가적인 linewidth-success 구별력을 확보하지 못했음을 보여준다.
bin 수가 작아 calibration 검증 완료로 부르지 않는다.

미정 한 표적을 포함한628 평균 예측의 허용 구간은 D
`[0.69441703,0.69600939]`, A `[0.61315007,0.61474243]`다.
실제628의 marginal 결과436/628,385/628은 완전히 관측되어 있으며,
이 구간은 결과 count의 불확실성이 아닌 해당 모형의 미정 예측 부분이다.

처음에는 원문 -1을 숫자 그대로 사용한628-row fit을 실행했다. source audit에서
의미 문제가 드러나 부모 지시에 따라 이를 명시적 민감도로 보존했다.
`D02_RAW_VHEL_SENSITIVITY.json`은 첫 결과 그대로이고, 당시 generator와
ledger는 외부 같은 폴더의 `RAW_VHEL_FIRST_GENERATOR.py`와
`RAW_VHEL_FIRST_TARGET_JOIN_AND_OOF.csv`다. 첫 D Brier0.21013915,
전체A Brier0.23517854였다. 최종627 primary와 비교해 약한 예측력이라는
해석이 바뀌지 않는다. 첫 실행을 덮어쓴 성공으로 꾸미지 않았다.

## 검증, 산출물과 다음 전이

실제 실행:

```bash
.venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D02_HI_CF4/hi_cf4.py
.venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D02_HI_CF4/test_hi_cf4.py
```

첫 raw-value fit session18856 exit0; 새 source finding에 따른627 primary
session56829 exit0. **8tests PASS**. 테스트는 raw SHA/628·385집합,
누락 없는 조인, 동일 그룹 holdout 무누출, -1 예측 UNKNOWN,
저장된 한 fold의 두 단계를 실제 재적합해 일치 확인, 전체 saved-score 재계산,
계층적확률, 버전차이/비검출 편입 유지, 합성 단조 회귀 및 첫 sensitivity 보존을
검사했다. 기존 과학 fit/전체 suite/원고 build는 재실행하지 않았다.
그림은 `D02_COHORT.png/.pdf`, 전체 집계·모형·interval은 `D02_RESULT.json`이다.

다음 계산 소비자는 D07 및 H02/S02/K04의 source-conditioned 분석이다.
이 ledger는 표적 결과별 actual group-support와 미정 예측질량을 넘길 수 있지만,
전체 CF4 parent law, shared angular calibration, 공통 optical→kinematic response,
finite-z/flow remainder 또는 physical velocity law를 제공하지 않는다.
D03의 공통 genealogy/공분산 입력이 완성되기 전에는 그 물리·joint acceptance를
완료 처리할 수 없다. 독립 fresh review와 publication은 부모의 별도 단계다.

Claim audit: 새 주장은 실제628 join 및 조건부 진단 `DIAGNOSTIC_ONLY` 두 종류이며,
owner `htt`, evidence actual sealed-source computation/test, transfer `none`이다.
물리 claim 승격·MIO posterior·native transfer 또는 family identification은 없다.
