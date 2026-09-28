# RC-03: 평탄 전단 characteristic의 국소 미분

Owner: HTT R10 local research. Scope: exploratory, DIAGNOSTIC_ONLY.
독립 native 검수·CAS·관측 admission은 없다. 생산 코드를 호출하거나 변경하지 않는다.

## 문제와 단위

Minkowski 좌표 `x0=ct`, signature `(-,+,+,+)`, `c=1` 길이 단위를 쓴다.
상수 실대칭 trace-free `S`의 단위는 inverse length, `h>0`는 길이다.
`u(x)=gamma(1,Sx)`, 관측 사건 `(h,0)`, 초기 source 면 `x0=0`이다.
광선 운동 방향을 `e`, 관측 하늘 방향을 `n=-e`로 구별한다.
직선 null ray의 source 위치는 `-h e`이다. 전체 하늘에서 `h||S||op<1`을 요구한다.
초기 분포는 각 source의 국소 rest frame에서 등방이고 같은 스펙트럼이다.
source 면은 이 congruence에 직교하지 않으며, 원점 밖 가속도는 일반적으로 0이 아니다.
원점에서만 `A=theta=omega=0, sigma=S`이다. 우주론적 전단 해나 새 Bianchi solver가 아니다.

코드는 `-u_src.g.p_obs`로 에너지 비를 구성한다. 점별 비교식은
`g=(1+h e.S.e)/sqrt(1-h² e.S².e)`이다.
충돌 없는 occupation 보존 후 `epsilon_obs³ F(g epsilon_obs)`를 Gauss–Laguerre
적분한다. brightness fixture는 `F(E)=exp(-E/E*)`, `E*=1`, 따라서 `Pi0=6`이다.
독립적인 Planck 스펙트럼 fixture는 세 주파수에서 occupation으로부터 온도를
역산한다. 두 스펙트럼은 모두 초기 등방이지만 동일한 절대 blackbody 정규화를
공유한다고 가정하지 않는다. 밝기는 `6 g^-4`, 온도는 `T0/g`와 점별 비교한다.

구면 적분은 direct STF 계수를 복원한다:
`Pi2=(15/8pi) integral Pi(n) n_<ab> dOmega`,
`Pi3=(35/8pi) integral Pi(n) n_<abc> dOmega`.
`Theta=T/<T>-1`의 quadrupole도 같은 정규화로 얻는다.
초기 계수가 0이므로 `Pi2(h)/h -> -4 Pi0 S`, `Theta2(h)/h -> -S`를 검사한다.
짝대칭인 `g(e)` 때문에 dipole/octupole은 0이다. 이 유한 테스트는 모든 홀수
multipole에 대한 형식 증명이 아니다. scalar mean이 변하는 것은 허용한다.

## 실행·최초 실패

`attempt01`의 source/config/traceback을 보존한다. 모든 방향의 미분·점별 적분·
부호와 power negative control을 지나 고정 h 격자 검사에서 exit 1이었다.
coarse angular grid 8의 grid 32 대비 차이 `8.28577e-11`까지 최종 허용오차
`2e-11`을 요구했기 때문이다. grid 16의 차이는 `4.61805e-14`였다.

한 번의 검사 구현 수정으로 가장 미세한 두 angular grid에 원래 허용오차를
적용하고 coarse→fine 오차 감소도 요구했다. energy grid 비교는 모두 같은
허용오차를 적용했다. **허용오차, 물리 reference, h 값은 바꾸지 않았다.**
이 변경은 admission 기준의 적용 범위 수정이며 최초 실패를 PASS로 다시 쓰지 않는다.
`attempt02`가 최종 탐색 실행이다. result.json과 convergence.png에 모든 수치를 남겼다.

여섯 S(다섯 정규직교 STF와 혼합 하나), 각 일곱 h를 썼다. Richardson 검사와
단방향 차분을 함께 기록한다. fixed-h quadrature convergence와 h→0 truncation
limit은 별도 검사다. 아주 작은 h의 cancellation은 diagnostic-only이다.
잘못된 source velocity 부호와 brightness power `g^-1`은 같은 미분 reference에서
실패해야 한다. 생산 T9 mutation test나 production RED→GREEN을 수행한 것은 아니다.

실행: repo root에서 아래 명령의 OUTPUT은 존재하지 않아야 한다.

```sh
python3 docs/research_program/optical_mapping_r10_20260919/continuation_execution/shear_ray/run.py --output OUTPUT
```

이 결과만으로 광학 jet의 실제 selected law, 곡률 remainder bound, native transfer,
T9 formal eligibility를 공급하지 않는다. missing provider의 whole-domain 상태는 유지한다.
