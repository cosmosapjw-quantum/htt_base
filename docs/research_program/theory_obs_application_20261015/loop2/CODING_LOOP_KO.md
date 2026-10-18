# HTT 이론·관측 2차 코딩 연구 루프: C1–C10

원시자료: 기존 /mnt/extdrive/workdir, raw readonly.
기존 checkout과 역사적인 uncommitted 변경사항 유지.
HEAD: 13d8d85fa470d645d008986e8f77d8d0f70fdf54.
native subagent: NOT_RUN (current host delegation tool unavailable).

C1–C2: 원리와 구현 위치는 THEORY_LOOP_KO.md 참조.
동일 Planck sky pair ID와 6개 processing variant를
재사용하며 새 independent mock을 생성하지 않는다.
CF4의 PR179 등록 design/covariance와 H_ONLY status를 변경하지 않는다.

C3–C5: 다음 코드가 실제 작성되었다.
- htt/obsstat/paired_highmode_control.py: train-only
  ridge B, shrinkage covariance, ties-safe finite rank.
- scripts/run_htt_paired_highmode_stat_20261015.py:
  실제 Planck paired coefficients, BIC 아닌 선택된
  3개 ridge+baseline 및 두 mask의 8-feature joint max,
  같은 sky의 heldout predictive ablation,
  실제 관측 source-surrogate의 J_R Fisher proxy.
- htt/obsstat/cf4_q_information_budget.py:
  Generalized eig 및 ideal independent-source info budget.
- scripts/run_htt_cf4_q_information_budget_20261015.py:
  해시 인증한 실제 외장 CF4, PR179의 5-fold
  response/nuisance 재활용, registered scalar gate 불변 대조.
- 두 새로운 tests/obsstat/test_* module:
  null rank, rotation invariant, lambda/covariance guards,
  complex harmonic fail-closed, Gram SPD/PSD/unit-change guards.

C6–C8: 성공적으로 생성된 결과
- results/cmb_paired_highmode_v1 : 최초 실행 기록.
- results/cmb_paired_highmode_v2 : authoritative source
  lineage validation 및 같은 calibration 240개 paired
  bootstrap MSE 진단 추가.
- results/cf4_q_budget_v1 : 실제 q 정보 고유값 결과.
각 결과는 result.json, 한국어 보고서, PNG 및 일부 NPZ를 보존한다.

실험용 8-score joint null 139/241, naive 32D ridge
out-of-sample MSE +2~13%; 비교 후 더 나은
decontamination이라는 주장은 철회한 상태다.
CF4는 35,549개에 대한 5-fold 결과가 이전
q-info scalar ratio와 1e-11 수준에서 일치했고,
새 relative eig 정보가 0.0023~0.0029인 것이 확인됐다.

C9–C10: 두 모듈의 코드/물리 우려는 위
결과 등급(conditional diagnostic only)과 raw-convention
계약으로 제한했다. 소스와 모의 데이터가 같은
하늘의 서로 다른 관측처리라는 물리적 상관 구조를
유지했다. 원본 Planck/Cosmicflows raw를 수정하지 않았다.
Native 별도 reviewer는 이번 호스트에서 불가능하므로
독립 fresh-context PASS를 표방하지 않는다.
코드·수치 검증과 과학적 수용은 별개 상태다.
다음 실제 단계는 저차원 physically anchored
control의 simulation-only CV, Planck 실제 split
null source 확보, 독립 q 정보 source model 구축이다.
