# RC-04: T9 표현·호출 범위

Owner: HTT R10. DIAGNOSTIC_ONLY; source checkpoint 748dbdeec56ac58ed0b440f04eb4d492ab2cb185
(생산 내용은 tested dcc5c7c215c671dc8036771e520bcafa4056cd65와 동일).
본 문서는 formal eligibility가 아니다. draft 계약의 네 축은 모두 NOT_EXECUTED.

## Direct / 적분 moment / packed

`Pi(e)=sum_l Pi_A_l e^A_l`의 direct STF 전개를 사용한다.
적분 moment `J_A_l=integral Pi(e)e_<A_l>dOmega=Delta_l Pi_A_l`,
`Delta_l=4pi l!/(2l+1)!!`. 그러므로 `Delta2/Delta0=2/15`다.
STF tensor T에서 angular L2 norm은 `Delta_l (T:T)`이다.
`contractions.py:stf_basis/pstf_pack/pstf_unpack`은 Frobenius 정규직교 기저
`Q_l`을 써서 `packed=Q_l^T vec(T)`, `vec(T)=Q_l packed`로 변환한다.
packed norm을 angular norm으로 바로 읽지 않는다. 기저 부호·순서를 외부
spherical m convention과 동일시하지 않는다.

검증할 general-l 명제: `m=l-2`, R³에서 정의한 homogeneous harmonic
`P_m(x)=Pi_A_m x^{A_m}`에 대해 ambient Cartesian 미분 `partial/partial x_i`를
먼저 계산하고 `x=e`, `|e|=1`에 제한한다. `grad_S2=(I-ee^T)grad_R3`이므로
collisionless pure-shear brightness generator의 두 표기는
`L_S P_m=(S e).grad_R3(P_m)|_e-(m+4)(e.S.e)P_m(e)`와
`(S e).grad_S2(P_m)-4(e.S.e)P_m(e)`이다.
동치에 필요한 Euler identity는 `e.grad_R3(P_m)=m P_m`이다.
첫 항의 polynomial degree는 m이므로 rank m+2 harmonic 성분이 없다.
따라서 direct RHS의 l<-l-2 항은 `-(l+2) STF(S tensor Pi_l-2)`다.
이는 draft의 증명 대상이며 이번 실행의 여섯 ell=2 테스트가 general-l 증명을
대체하지 않는다. 에너지 부분 적분에는 `E^4 f -> 0` 양 끝 경계와 적분가능성이 필요하다.
적분 moment RHS는 `-(l+2) Delta_l/Delta_l-2 STF(S tensor J_l-2)`이고,
ell=2에서는 `-(8/15)S J0`이다. ell=0,1에 아래 source는 없다.

MAIN 보완의 exact discriminator는 `m=1`, `ell=3`, `P1=x`,
`S=diag(1,-1,0)`이다. `x(x²-y²)`의 degree-3 harmonic 부분에 대한 계수는
올바른 두 generator에서 -5이며, `grad_S2`에 다시 `-(m+4)`를 붙인 변이에서는
-6이다. [검사 코드](test_gradient_discriminator.py)는 유리수 다항식의 미분과
trace 제거를 직접 실행한다. 이는 한 벡터의 Host diagnostic이며 일반 ell 증명,
등록된 SymPy/CAS 축 또는 native independent review가 아니다.

현재 `terms.py:T9_shear_down`은 **LHS** 항에 `-(l+2)`를 넣는다.
`packed_operators.py:_t9_basis_ops`는 이 함수로 cache를 만든다.
`hierarchy_rhs.py:proper_shear_at_eta`는 `Sigma/a`를 전달하고, 실제 RHS는
`a(K-sum_T)` 또는 충돌이 없으면 `-a sum_T`다. eta 단위는 Mpc이며 proper
길이 시간에 대한 미분에서 conformal 미분으로 a를 곱한다. 따라서 isotropic
ell=2에서 현재 public RHS는 위 물리 reference와 반대이다. 이전 의도적 exit 1
`t9_diagnosis.py` 결과를 재사용하며 덮어쓰지 않았다. photon 및 shared collisionless
neutrino 호출 경로가 영향 범위다. massive species의 별도 물리는 이 증명 범위 밖이다.

## standalone 5m와 실제 mixed runtime의 차이

`mode_mixing_blocks.py`는 각 ell에 다섯 m=-2..2를 배치한다.
ell=0,1에는 비물리 padded slot이 있고 ell>2에는 full STF의 2ell+1개보다 적다.
유효한 원소만 채워도 일반 shear의 반복 작용에 닫힌 공간이라는 보장은 없다.
문서상의 sigma 좌표는 `(plus,minus,xy,xz,yz)`이고 tensor Frobenius norm 제곱은
`2 sum(sigma5²)`다. `shear_5vec_to_quadrupole_components`는 이를
`(xy,yz,minus,xz,plus)`로 순열한다. 이 실기저 순열을 complex Wigner-3j 기저와
동일시할 수 없다. 필요한 실/복소 basis adapter와 위상은 아직 결속되지 않았다.

`probe_mixed.py`는 물리적으로 유효한 isotropic `(ell=0,m=0)`만 1로 채운 뒤
실제 builder를 다섯 전단 방향에 적용했다. 출력 rank는 **1**이고 direct STF
물리 응답 rank는 **5**다. `_C9`가 source/target ell을 반대로 넘겨 `abs(m)>ell-2`
에서 차단하는 것이 이 사례의 구조적 원인이다. invertible convention 변환이나
전체 부호 반전은 rank를 고칠 수 없다. 이 수치 counterexample은 ell=2 / Lmax=2 /
ell_min=0에 한정한다. mixed 전체 T7/T8/T9 수정이나 admission으로 확대하지 않는다.

mixed 계약의 대상은 negative theorem이다. 가역 A,B와 `k!=0`에 대해
`rank(k A M B)=rank(M)`이므로 rank 1 map의 4차원 kernel은 정규화로 복구되지
않는다. 1차원 shear 제한 모델을 새로 정의하는 것은 full STF 동등성을 입증하지
않는다. 이 obstruction이 네 축에서 증명되더라도 standalone/ver3에 대한
`T9_CONSUMER_ELIGIBLE`은 false이다. full/packed 일반 ell 계약도 별도 scope다.

호출 추적:

- `rg -n 'mode_mixing_blocks|assemble_A_mix_block' htt --glob '*.py' --glob '!test*'`
  에서 이 standalone builder의 tracked production caller는 발견되지 않았다.
  b_mode_projector의 일치는 설명과 주석이다. 이는 이 검색 범위에 대한 결과다.
- 실제 `ver2_native_integrator.py:_AuxiliaryOperatorSample.drive`는
  `+ mode_ops.A_mix @ vector`를 RHS에 더한다.
- `los/family_backend_protocol.py`가 이를 구성할 때 호출하는 것은
  **다른 함수** `ver3_layout_protocol.py:assemble_mixing_block`이다. 그 함수는
  full m와 backend mix/twist scale을 쓰며 standalone C9 builder를 호출하지 않는다.

따라서 같은 A_mix 이름만으로 standalone 부호를 실제 runtime에 적용할 수 없다.
실제 ver3 operator의 물리 유도/adapter 입증은 미완료다. full/packed 계약과
mixed 계약을 분리하고 mixed는 unresolved로 유지한다. 전체 RHS 반전은 금지다.

## CAS와 수정 경계

두 schema-v2 draft는 source byte hash, 의미, 대상, 축별 의무를 제공한다.
아직 native 검수와 toolchain seal이 해결되지 않아 frozen execution contract가 아니다.
계약 version 2에는 위 gradient 정의와 test vector, 표현·시간·단위 정의를 직접
포함했다. 이 README에는 Host 유도와 rank 결과가 있으므로 blind 축의 입력에서
제외한다. source identity 목록은 전달 allowlist가 아니다. 특히 유도가 포함된
SCIENTIFIC_CONTRACT, probe/검사 코드, 저장 결과와 반환 문서도 축에 전달하지 않는다.
공유 target은 증명 대상이며, 그 target을 확인한 Host 풀이를 공유하지 않는다.
현재 실제 client cwd는 맞지만 기존 pending의 source/sandbox/scope와 지원되는
continuation 결속은 해결되지 않았다. RC-01이 막혀 RC-05를 실행하지 않았다.
네 엔진 독립 실행과 `cas_gate.py run-adjudicate`는 수행하지 않았다.
저장된 이전 adjudication, host derivation, 이 수치 probe, preflight가 이를 대신하지 않는다.
일반 ell 계수를 수정하려면 general-l 의무와 적용 public/shared 경로 regression,
별도 physical RED→GREEN 및 old-sign mutation FAIL이 필요하다.
RC-06은 수행하지 않았다. 현재 상태는 `PATCH_REQUIRED_DIAGNOSIS / PATCH_NOT_AUTHORIZED_BY_GATES`다.
