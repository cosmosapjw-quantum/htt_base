# R113-CLOUD 결과 기록: Lie 대수 생성 PSTF 엔진과 비섭동 배경 C_lm^XY

이 디렉터리는 클라우드 세션의 native Rust 개발 기록이다. 과학적 의미와 수치의
소유자는 BASS/REC/REI 코드, 테스트, 계약 문서이며, 이 기록은 그것을 가리킬 뿐
권위가 아니다. pin과 해시는 `NATIVE_PINS.json`, 지역 에이전트 작업 지시는
`LOCAL_AGENT_HANDOFF.md`, 상세 유도와 검증은 BASS
`research/r113_cloud_universal_lie_sky/` (`THEORY.md`, `README_KO.md`, `RESULTS/`)에 있다.

## 사실

- BASS `db72d1b` (base `4062672`, R112): 모든 Bianchi family를 하나의 식으로
  다루는 Lie 대수 생성 spin-harmonic PSTF 경로 (`--route harmonic`), 무충돌 중성미자,
  radiation energy frame / local boost / global tilt 보고와 관측자 frame 선택,
  REC matched recombination coupling (`--recombination matched`). 기본값 (`rays`)의
  R112 CLI TSV 출력 20개는 byte-identical. `cargo test --release --locked` 218 passed.
- REC `05db545` (base `3752213`): `matched_history::implicit_matched_step` (FLRW
  항등식 1e-14, 1차 수렴, stiff 극한). 129 passed.
- REI `503508f`: 변경 없음, 271 passed.
- 검증 V1-V13 모두 합격선 안 (BASS `README_KO.md` 4절). 대표 수치:
  계층 행렬 대 정확한 characteristic generator 1.1e-7 - 1.4e-7 (유한차분 오차 차수),
  정지 전자 충돌 대 PSTF BE 닫힌 꼴 3.3e-14, 13 경우 cross-route 차이는 L 무관하고
  시간 간격 절반마다 1/4 (2차), z = 1100 -> 0 VII_h 시연의 LoS l <= 64 경로 차이 9e-9.
- matched recombination: shear 1e-2, tilt 1e-3 창에서 delta x_e 최대 3.2e-7
  (상대 2.9e-6), l = 2 C_l 변화 TT -3.8e-6, EE +2.1e-5; rays와 harmonic의 delta x_e
  차이 2e-15.
- push 상태: 클라우드 세션의 권한 분류기가 git push를 거부했다. 세 커밋은 git
  bundle로 소유자에게 전달했다. REC `05db545`가 GitHub에 올라가기 전에는 BASS
  `db72d1b`의 cargo git pin이 해석되지 않는다.

## 해석

- BASS native 쪽에서는 off-axis 회전 데이터를 포함한 12 family + VI*가 같은 코드
  경로로 비섭동 C_lm^XY template을 낸다. 이것은 htt_base Python/PSTF 소유 dispatch의
  coverage envelope (CLAUDE.md 1절: full-mode LoS는 FLRW, I, V, IX)을 바꾸지 않는다.
  경계 변경은 소유 dispatch와 scientific contract를 갱신하는 별도 작업이다.
- 결과는 하나의 결정론적 배경 history에서 나온 template이다. R78 science DAG의 노드
  상태, 원래 42개 acceptance, 관측 claim ceiling은 바뀌지 않는다. ensemble 공분산,
  family attribution, 보정된 p-값은 없다.

## 미해결

헬륨과 물질 온도의 진화 변수화, offset의 Strang 분할, 스펙트럼 수송, REI 표와 결합한
재이온화 구간, harmonic 경로의 Gaunt-정확 이동 전자 충돌, matched step 비용, z_emit >=
1600 표로 tight-coupling 시작. 지역 에이전트 작업 순서는 `LOCAL_AGENT_HANDOFF.md`.
