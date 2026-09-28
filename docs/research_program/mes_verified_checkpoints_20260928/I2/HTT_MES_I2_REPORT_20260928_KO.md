# HTT/MES I2 — 물리 잔차의 한계와 local Codex 인계

2026-09-28. I1에 이어 GPT-6 연구 하네스 v4.0.0으로 이론 루프를 수행했다. **독립 판정은 DEFENDED_CONDITIONAL, 필수 수정 없음**이다. 현재 main은 다시 조회해 I1과 같은 `cc162c804eecb3c588efc6edadbe057a8a67301f`, tree `f14a536e7934d99bbe67489d1b81e5da0079cb09`임을 확인했다. 전체 저장소 조사를 반복하지 않았다. 과학 계산은 가벼운 Wolfram 대수이며 ODE/PDE evolution이나 관측 likelihood는 실행하지 않았다.

## 이번에 닫은 부분

I1은 radiation residual을 알 때 target \(Z=\sigma-\operatorname{STF}(\beta a^T)\)를 복원했다. 이번에는 그 residual을 단순히 0으로 놓지 않고, 물리 source를 정확히 정한 경우에도 정적인 sky만으로 전단을 제한할 수 있는지 검토했다.

선택한 분기는 **Einstein–Vlasov Bianchi I, massless collisionless radiation only, \(\Lambda=0\), 측지 정규 congruence, \(\beta=0\)**다. 이 분기에서 \(a=0\)이고 \(Z=\sigma\)다. 실제 우주 전체를 이 모형으로 채택한 것은 아니며 일반 finite-tilt 프로그램도 유지한다.

고정된 매끄러운 radial 초기 분포 \(f_0(q)=F(|q|)\), 초기 \(g=I\), \(\rho_0>0\)에 대해
\[
\sigma_\lambda=\lambda\operatorname{diag}(2,-1,-1),\qquad
H_\lambda=\sqrt{\lambda^2+\frac{8\pi G\rho_0}{3c^2}}
\]
를 선택하면 Einstein constraints를 만족하는 국소 해가 존재한다. 모든 초기 방향별 팽창률은 양수다. 모든 \(\lambda\)에서 같은 complete isotropic radiation snapshot이지만 \(\|\sigma_\lambda\|_F=\sqrt6\lambda\)는 임의로 커진다.

따라서 이 domain에서 **정적 snapshot만으로 유한한 절대 전단 상한은 얻을 수 없다.** 다만 \(H\)도 함께 변하므로 normalized shear가 무한하다는 뜻은 아니다. \(\|\sigma\|_F/H\to\sqrt6\)이고, 정확한 순간 등방성도 almost-FLRW를 강제하지 못한다. 같은 과거 광원·재결합 역사나 실제 CMB 적합성을 갖는 가족이라고 주장하지 않는다.

빠져 있던 시간미분은 구체적으로
\[
\dot\pi(t_0)=-\frac8{15}\rho_0\sigma(t_0),\qquad
r_2=-\dot\pi
\]
다. 충돌과 공간항이 사라져도 이 항은 남는다. 기존 almost-EGS의 시공간 derivative 전제와 모순되는 반례가 아니라, 그 전제를 snapshot에서 자동으로 얻을 수 없음을 보여주는 구성이다.

## 양의 결과: 별도 H 입력이 주는 조건부 허용집합

독립적인 같은 상태의 \((H,\rho)\)가 주어지면
\[
\mathcal S(H,\rho)=\{\sigma\in\mathrm{STF}_2:
\|\sigma\|_F^2=6H^2-16\pi G\rho/c^2\}
\]
를 얻는다. 음의 우변은 empty, 0이면 isotropic point, 양수이면 STF sphere다. 이는 전단의 크기를 제한하지만 tensor 방향·모양은 정하지 않는다. 공동 불확실성은 \((H,\rho)\)의 같은 joint set 위 union으로 전파한다. 모든 방향의 팽창을 요구한다면 \(HI+\sigma\succ0\) 조건을 더한다.

이 결과는 radiation-only Bianchi I의 Einstein constraint에 조건부다. 실제 데이터로 정당화된 \(H\) 범위는 아직 없으며 FLRW/ΛCDM에서 추론한 \(H_0\)를 그대로 대입하지 않는다. MES의 관측 상한이나 새로운 universal theorem으로 부르지 않는다.

## 근거와 완성도

| 구분 | 실제 근거 / 상태 |
|---|---|
| Einstein–Vlasov 기본 식 | Rendall 원문 §2 확인, `literature-supported` |
| Local smooth solution, 반례족, 조건부 집합 | 가정과 단위·부호를 명시한 직접 유도, `derived` |
| Moment 계수·Hamiltonian·constraint 보존·극한 | 현재 Wolfram exact-symbolic 실행 |
| 독립 판정 | `DEFENDED_CONDITIONAL`, 필수 수정 없음; decision JSON과 검토 원문이 권위 |
| 실관측 유한 interval / likelihood | `UNRESOLVED / NOT_RUN` |
| Production adapter / 저장소 CAS4 | `NOT_RUN`; 기존 gate 유지 |

Exact-symbolic 실행에서 일반 STF moment 잔차, constraint 분해·반례족·보존 잔차는 0이었다. 첫 brightness derivative 비교는 단위구면 제약의 배수로 출력되어 그 범위를 보존했고, 해당 비교만 polynomial ideal로 추가 환원해 0을 확인했다. 실제 full numerical evolution은 수행하지 않았다.

## 다음 연구와 전달

다음 I3는 **동일 congruence의 독립적인 expansion/optical shear 또는 radiation time-jet 입력 하나**를 정하는 작업이다. Norm bound만 필요한지 tensor morphology가 필요한지를 구분한다. 전자는 \(H,\rho\) 경로로, 후자는 directional optical/jet 경로로 접근한다. 이론식과 같은 자료를 순환적으로 독립 prior로 만들지 않는다.

`HTT_MES_LOCAL_CODEX_FULL_20260928.zip`에는 원본 연구 백업 01/02/03, I1 checkpoint, 이번 I2 checkpoint, 복원 도구와 시작·반환 prompt가 들어 있다. 파일당 512MiB 제한으로 `.part01`, `.part02` 두 조각을 제공하며 로컬에서 연결한 뒤 전체 SHA-256을 확인한다. **현재 확보한 누적 연구 산출물 전체를 전달하는 묶음**이다. 회수하지 못한 대화 전문, 원격 Git 모든 브랜치의 전체 checkout, 별도 BASS toolchain/vendor 첨부를 포함한다는 뜻은 아니다.

원본 3 ZIP의 바이트를 그대로 보존한다. DB는 복원하지 않았고 삭제할 새 DB 원본도 없다. Local Codex는 새 clone/worktree를 만들지 않고 기존 repo에서 현재 상태를 대조한다. 완료된 I1/R1–R5 검산이나 R9 D2 bridge를 반복하지 않도록 인계했다.

읽기 순서: `handoff_i2/README_KO.md` → 복원 receipt → I2 `state/RESEARCH_STATE.md` → 독립 판정 → `HTT_MES_I3_NEXT_PROMPT_20260928_KO.md`. 원래 입력 백업은 unchanged 참조로 남기고 후속 local 결과만 별도 ZIP으로 반환한다.

원문: [Rendall (1995/1996), §2](https://arxiv.org/pdf/gr-qc/9505017v1), [Ellis–van Elst, §8.5.1](https://arxiv.org/pdf/gr-qc/9812046v5). 전체 유도·정확한 문헌 읽기 범위·raw 계산·독립 판정은 I2 checkpoint에 포함한다.
