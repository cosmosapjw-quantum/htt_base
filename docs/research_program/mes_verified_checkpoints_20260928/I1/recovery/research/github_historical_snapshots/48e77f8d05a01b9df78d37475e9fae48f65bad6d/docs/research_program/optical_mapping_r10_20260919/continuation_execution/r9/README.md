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
