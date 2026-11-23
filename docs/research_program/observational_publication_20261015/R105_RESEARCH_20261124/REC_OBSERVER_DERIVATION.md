# 유한 적색편이에서 본 REI 방향별 광학깊이

**결과.** 평균 적색편이 4에서 물질과 함께 움직이는 관측자가 측정하는 광자 적색편이를 기준으로, 다섯 REI 이력에서 산란 깊이와 가시도 밀도를 계산했다. 광자 적색편이 0.6에서 tau의 2차 Legendre 계수는 초기 전단 +0.01에서 −5.41096485×10⁻⁵, −0.01에서 +5.41495290×10⁻⁵였다. 동일한 방출 시각에서의 깊이는 방향과 무관하다. 차이는 서로 다른 방향에서 같은 관측 적색편이가 서로 다른 방출 시각을 선택하는 데서 생긴다.

## R1–R5. 원본 정의와 유도

REI 기준 커밋은 56dc609ea9b801c88d3364aed3eee140b3a20d46이다. five_case_abundances.csv.gz의 전단 부호, 축변형 b, 수소·헬륨·전자 시료 1001개씩과 원본 AXBI_REVIEW.md의 축 규약을 사용했다. 평균 적색편이 지원 구간은 [4,20]이고, 선요소는 ds²=−c²dt²+a²exp(−2b)(dx²+dy²)+a²exp(4b)dz_axis²이다. 공간 Killing 운동량 p_i를 따라 법선 관측자의 E∝sqrt(sum p_i²/a_i²)가 보존 운동량과 시간에 의해 결정된다. N=ln(a), d=b(N)−b(N_o), mu=관측점 국소 직교틀의 대칭축 방향코사인으로 놓으면

    1+z_ray = exp(N_o−N) sqrt[(1−mu²) exp(2d) + mu² exp(−4d)].
    w_parallel = mu²/[mu²+(1−mu²)exp(6d)].
    −d ln(1+z_ray)/dN = 1 + b′(3 w_parallel−1).

z_ray=0은 관측점 자체다. 양의 두 주축 팽창률 1−b′, 1+2b′가 표본 전체에서 한 방출사건을 보장한다. 기하학적 정의와 비교 가능한 Bianchi I 광선 방정식은 Fleury, Pitrou & Uzan (2015) §III에 있다. [원 논문](https://arxiv.org/abs/1410.8473)

원본의 정상계 proper n_e, 양의 H와 q_op=c sigma_T n_e/H를 사용하면 d tau/dz=q_op/[(1+z_ray)(1+b′(3w_parallel−1))]. 양의 가시도 밀도는 g(z_ray)=exp(−tau) d tau/dz이며 주파수, τ, z_ray 및 N은 무차원이다. 하나의 N에서 τ(N)=∫_N^N_o q_op dN′는 모든 방향에서 같다. 고정된 z_ray에서 FLRW 방출시각 N_* = N_o−ln(1+z_ray)을 중심으로 1차 전개하면 delta N=−2P2(mu)[b(N_*)−b_o]이고, tau2=2 q_op(N_*)[b(N_*)−b_o]+O(b²)이다. 이는 통계적 분위가 아닌 부호를 갖는 주파수-방출시각 응답이다.

## R6–R10. 대조와 채택 범위

축방향·수직방향의 일정 b′와 일정 q_op에서는 tau=q_op ln(1+z_ray)/(1+2b′)와 tau=q_op ln(1+z_ray)/(1−b′)가 각각 정확하다. 혼합 방향에서 d tau/dz는 독립 중심차분으로, b의 상수 이동은 축 정규화의 자유도로 검사했다. 등방 경우 전단 응답이 사라진다. 전 구간 수소·헬륨 분율과 시계는 원본 시나리오에 조건부다. 이 자료에는 오늘까지 이어지는 0≤평균 z<4 물질 이력이 없으며, htt_base의 Planck2018 HYREC 검산표 헤더도 재이온화 미포함을 명시한다. 관측자 시점을 옮기려면 해당 시나리오에 부합하는 추가 기하 및 전자밀도 이력이 필요하다.

## C1–C10. 수치 구현과 확인

ReiMaterialHistory.observer_rays(observer_z_mean=4).evaluate(z,mu)는 방출 N, τ, dτ/dz, g(z)를 반환한다. 원본의 b를 N에서 구간 선형으로 보간한다. 끝점을 포함한 이분법으로 방출 시각을 얻고, 한 번의 정렬로 전체 방향에서 서로 다른 N들의 원본 물질 적분을 합친다. 미분이 불연속인 원본 마디에서 높은 적색편이 쪽의 Jacobian을 취한다. 옛 H/He 전용 입력도 계속 적분할 수 있으며 각도 계산에는 b가 필요하다. 서로 다른 Ω_m·Y_He 또는 프레임의 원본을 자동으로 합치지 않는다.

다섯 화학 이력 × 여섯 광자 적색편이 × 48개 관측각의 signed response를 저장했다. 24→48 Gauss–Legendre 각도에서 tau2의 차이는 최대 1.16×10⁻¹², 주파수 역함수의 log(1+z) 잔차는 4.45×10⁻¹⁶ 이하이다. 입력 시료의 분해능과 물리 모델 오차는 별도다. R103 셀-가시도와 R105 광선 검산 여섯 개가 owner checkout에서 통과했다. K03·B02 등 타 과제의 원래 과학 수용 조건은 이 계산만으로 충족되지 않는다.

재현 명령은 htt_base 기존 checkout에서 다음과 같다.

```sh
PYTHONPATH=.:htt:htt/src:htt/htt OPENBLAS_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/obsstat/test_r103_rei_material.py tests/obsstat/test_r105_rei_observer.py
PYTHONPATH=.:htt:htt/src:htt/htt OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/r105/rec_observer_redshift.py --donor-repo ../rei_bianchi --output /tmp/REC_OBSERVER_REDSHIFT.json
```
