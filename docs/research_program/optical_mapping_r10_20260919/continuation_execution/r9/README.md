# RC-07: 실제 저장 SDSS 응답의 공통 영점 null 방향

Owner: HTT nuisance identifiability / obsstat saved response. DIAGNOSTIC_ONLY.
Donor `870bd67af159993ccde4ede9923424a475c01375`의 현재 local HEAD와 clean 상태를
확인했고, 더 최신 donor 변경이 없어 해당 immutable Git 입력을 재사용했다.
실행은 raw catalogue·mock pool을 반복하지 않고 `git show DONOR:path`로 저장 배열을 읽었다.
해당 commit object가 있는 repo에서 아래 명령을 재현할 수 있다. OUTPUT은 새 경로여야 한다.

```sh
python3 docs/research_program/optical_mapping_r10_20260919/continuation_execution/r9/response_null.py --output OUTPUT
```

관측 SDSS mask 및 네 누적 redshift 창에 대해 저장된 36×36 response R을 사용한다.
이 R은 서로 겹치지 않는 네 shell의 additive logdistance angular coefficient를
실제 누적 창 feature로 보내는 unit-weight SVD response다. boost나 global tilt의
metric response가 아니다. donor의 z_min=.0033, maxima=.025,.05,.075,.1,
in_mask=1, 각 깊이 counts=890,7277,19160,33121을 유지한다.

각 shell의 monopole slot만 1인 c를 만들고, 공통 영점 nuisance delta를 추가하면
`Y=R beta + b delta`, `b=R c`, `A=[R,b]`다. 이 실제 배열에 대해
`v=(-c,1)`은 `A v=0`이다. R의 rank는 36, A는 36(열 37, nullity 1), H R은 27,
초기값을 보존하는 T R은 36이다. `H b≈0`, `T b≈(1,0,...,0)`를 확인했다.

저장된 관측 Y에 맞춘 theta0와 `theta1=theta0+0.00043862234757611747 v`도 같은
36성분 mean response를 낸다. 이것은 공통 영점이 알려지지 않은 상황에서 네 개
자유 shell monopole 평균을 분리할 수 없다는 구체적 unsupported target이다.
초기 anchor는 순수 영점 변화의 민감도를 보존하지만 이 nuisance degeneracy를 없애지는 않는다.

동시에 donor의 실제 CF3–SDSS 294행 진단 보정 전/후 배열이 `delta b`만큼 변하는지,
contrast에서는 상쇄되고 초기 block에서는 남는지 확인했다. 모든 검사 최대 잔차는
`6.6058269965196814e-15`이며 허용오차는 `1e-11`이다. source hash, null vector,
두 parameter tuple, singular values, residual은 result.json에 있다.

Selected observation law, joint covariance/noise law와 물리 boost/tilt response는
**UNAVAILABLE**이다. 같은 평균이 같다는 결과를 전체 확률법칙의 동등성으로
승격하지 않는다. CF3–SDSS 294행은 CF4 selected law가 아니다. alpha 소비 0,
새 mock 호출 0, confidence/rejection/coverage 계산 없음. CMB/CF4/JWST/DESI의 다른
원 DAG 경로는 이 결과와 무관하게 기존 의존성을 따른다. 원 R8 STOP_INVALID,
unresolved pools, P0 quarantine, PR284 deferred, PR4/NPIPE exclusion은 변경하지 않았다.

## MAIN 이후의 target 구분 — 새 데이터 실행 아님

위 저장 rank와 `Y=R beta+R c delta`, R 가역이라는 선형 평균 모형을 전제로,
관측 평균은 `gamma=beta+c delta`를 정한다. 자유로운 beta와 delta의 null 방향은
`(-c,1)`이므로 beta-only target `l^T beta`는 **정확히 `l^T c=0`일 때**
평균응답에서 식별된다. 이 35차원 공간에는 세 독립 shell monopole 상대 조합과
32개 nonmonopole 성분이 들어간다. 기존 target인 네 monopole 평균은
monopole 네 자리의 l을 각각 1/4로 놓으므로 `l^T c=1`이며 식별되지 않는다.

depth contrast는 별도 질문이다. 저장 근거의 `HR c≈0`, `rank(HR)=27`을
조건으로 `row(HR)`는 `c`의 직교공간보다 8차원 작다. 따라서
`l^T c=0`만으로 contrast에서의 식별성을 보장할 수 없고,
`l in row(HR)`를 따로 확인해야 한다. H는 모든 angular 성분의 깊이 공통 모드를
제거하는 contrast이므로 scalar 영점만 제거하는 것보다 더 많은 평균 정보를 버린다.
그 제거가 실제 과학 target에 필요한 nuisance 처리를 나타내는지는 아직 미평가다.
관심 l이 이 row space 밖이면 원 R 또는 가역 T를 보존한 경로가 필요하다.
가역 T도 원 1차원 ambiguity는 없애지 않는다. 높은 rank 자체를 목표로 삼지 않는다.

추가 calibration `z=a^T beta+b delta`가 있을 때 원 null에 대한 응답은
`b-a^T c`이므로 이 값이 0이 아닐 때 구조적 ambiguity를 깬다. 실제 외부
calibration과 selected noise law 없이 hard constraint 또는 임의 prior를
데이터로 대체하지 않는다. 평균의 동등성은 parameter-dependent covariance의
동등성을 함의하지 않는다.

이번 보완은 MAIN의 조건부 대수 결론과 저장 결과를 정리한 것이다. donor NPZ,
`response_null.py`의 수치 계산은 다시 실행하지 않았다. 고정 donor의 observed.json에서
H의 대표 행을 읽어 인접 깊이의 같은 angular 성분을 빼는 정의를 확인했으며,
관측 rank/null/잔차를 재계산하지 않았다. 새 target l 및 새 calibration/
selected law가 제공되지 않아 추가 target의 row(HR) membership과 통계 분석은
`UNEVALUATED`이며 alpha는 0이다. R9 action은 T9/CAS의 대기열에 넣지 않는다.
