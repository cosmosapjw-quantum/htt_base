# R109 · Python 배경 제약과 초기조건의 Codazzi 부호

**구현·수치 검증.** 정상 직교정규 틀, 계량 부호 `(-,+,+,+)`, 물리적 에너지 플럭스 `qⁱ=T⁰ⁱ`를 사용한다. 동차 공간 절편에서 `DᵢΘ=0`이므로 모멘텀 제약은 `Cᵢ=Dⱼσʲᵢ+κqᵢ=0`이다. 선형 발산 연산자를 `A`, 직교 STF-5 전단 계수를 `x`라고 두면 물리적 플럭스의 초기조건은 `Ax=−κq`이다. 기존 `tilted_bianchi_state`와 `convention_bridge`는 이 규약을 사용했다.

| R108 수치 사례 | 수정 전 | 수정 후 |
|---|---:|---:|
| 생산 VI₋₁/₉ 상태, `ε=10⁻⁵`, 배경 helper의 잔차 / ‖div σ‖ | 2.0000000000000306 | 3.672898575600923×10⁻¹⁴ |
| 같은 상태의 독립 `exact_momentum_divergence`로 계산한 ‖div σ + κq‖ / ‖div σ‖ | 3.666813204760652×10⁻¹⁴ | 3.666813204760652×10⁻¹⁴ |
| 전계수 VI_h, 생성한 초기 전단의 ‖div σ + κq‖ / ‖κq‖ | 2.0000000000001683 | 3.343899986363391×10⁻¹⁵ |
| 같은 초기 전단에서 부호를 반대로 둔 음성 대조군 ‖div σ − κq‖ / ‖κq‖ | 2.1499787838299927×10⁻¹³ | 2.0000000000000013 |

수정 전 기준 커밋은 `6ca0a914d47d3c5eb4935926010970051f2008d3`이다. R108에 게시된 `FRAME/LIE_FLUX_FRAMES.json`의 스키마는 `/2`, SHA-256은 `ed3eaaf403e903192be19e87730ba854c811c98584ab0b2e7178bf7c9a5a4320`이다. 현재 검사기의 스키마는 `/3`이며, 기본 출력 파일은 `LIE_FLUX_FRAMES_V3.json`이다. 동일한 난수열로 양쪽 결과를 재현할 수 있다.

```bash
PYTHONPATH=.:htt:htt/src .venv/bin/python - <<'PY'
import json, numpy as np
from scripts.r108.frame_lie_flux import sign_convention_audit
print(json.dumps(sign_convention_audit(np.random.default_rng(20261124)), indent=2))
PY
```

**코드 경로.** `constraints.codazzi_constraint_residual`은 물리적 `q`를 더하고, `initial_conditions.project_shear_to_codazzi`는 물리적 `target_q`를 받아 음의 발산 목표를 만든 후, 원래 `q`를 넣어 결과를 검산한다. `κ=0`에서도 나눗셈이 필요 없다. `build_tilted_initial_conditions`는 한 번만 소비할 수 있는 종별 입력도 한 번만 물질화하므로 투영과 제약 평가가 같은 물리적 종과 플럭스를 사용한다. `rhs.assemble_background_rhs`, 배경 진화, `seed_compatibility`, 두 native seed 주입 경로는 각 소유자가 정의한 플럭스를 전달한다. 별도 생산 경로인 `tilted_bianchi_state`의 부호는 이미 맞았다.

**수치 조건과 실패 판정.** 직교 STF-5 계수에서 최소 변화량은 `A δx = −(Ax₀+κq)`의 최소 노름 해이다. 직접 SVD 최소제곱 `lstsq(A, ..., rcond=10⁻⁶)`가 이전 Gram 의사역행렬의 상대 고윳값 문턱 `10⁻¹²`을 유지하고 실제 사용한 계수를 반환한다. `n₂=1, n₃=−4, a=(2/3)(1+10⁻⁵)`와 `q=(0.04,0.03,−0.008)`에서 상대 잔차는 Gram 방식 `5.099×10⁻⁷`, 직접 방식 `1.866×10⁻¹²`이었다. 임계값 아래로 축퇴하는 방향은 유효 계수에서 제외한다. 예외적 VI₋₁/₉의 좌영공간 방향 `(0,1,2)/√5`에 `‖q‖=0.125, κ=2.5`를 주면 잔차 `0.3125`로 거부된다.

**검증.** 회귀 테스트는 교환자로부터 Koszul 항등식을 직접 수축하여 일반 전단에 대한 세 성분의 부호를 검사한다. 일반 VI_h에서 κ=0, 0.4, 2.5, 영플럭스, 예외 계열, 근접 축퇴, generator를 통한 기울어진 단일 먼지 성분, Type V seed에서 `3σa=κq`를 검사했다. 다음 실행에서 **179개**가 통과했다.

```bash
PYTHONPATH=.:htt:htt/src .venv/bin/python -m pytest -q \
  htt/bass/background/test_ver2_ic_evolution.py \
  htt/bass/background/test_ver2_constraints_rhs_weyl_skeleton.py \
  htt/bass/background/test_ver3_background_core.py \
  htt/bass/background/test_codazzi_tilt_rhs.py \
  htt/bass/hierarchy/test_ver2_seed_compatibility.py \
  tests/r49/test_gbi02_tilted_state_and_constraints.py \
  tests/r62/test_bianchi_state_constraints.py tests/r62/test_constraint_units.py \
  tests/obsstat/test_r108_frame_lie_flux.py
```

**해석 범위.** 6변수 `codazzi_tilt_rhs`는 각 축의 전단을 복원할 수 없어 음의 Friedmann 여유량을 샘플링한다. 이번 수정은 그 지표를 메타데이터에 표시한다. 세 성분의 Codazzi 검증에는 텐서 상태가 필요하다. 비영 플럭스에서 전단 또는 곡률을 사후 재조정하는 선택적 Hamiltonian closure는 투영 뒤의 Codazzi 만족 여부를 다시 확인해야 한다. 표의 생산 예와 기울어진 종 검산은 `solve_H` 경로다. SQ-LIE-FLUX에 대한 관측 검정에는 독립 전단, 군 틀의 방향 및 그 공분산이 여전히 필요하다.
