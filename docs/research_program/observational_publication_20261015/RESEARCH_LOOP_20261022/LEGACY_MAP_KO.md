# 과거 아이디어의 현재 재사용 지도

2026-10-22에 GitHub가 반환한 PR **558개**(#2–#561, 번호1/445/448은 PR목록에
없음)의 제목·본문·상태를 전수 수집했다. 427 closed,131 open,76 merged,423 draft다.
최초 생성은2026-07-22이다. [PR_INDEX.json](PR_INDEX.json)은 전체 metadata 색인이다.
본문 원본1,305,178bytes는 Git밖 `research20261022/intake/all_prs.jsonl`에 보존했다
(SHA256 ad0585ce7bc094e331d599170c24021239e619d720b9daccdf05dcbbe346d090).
모든 diff의 line-by-line review를 했다는 뜻은 아니다. 기존75개 PR 조사와
legacy 원문·코드 지도를 재사용하고 물리 연결에 중요한 아래 경로를 직접 읽었다.

| 원래 아이디어·PR | 살릴 내용 | 현재 적용과 남은 입력 |
|---|---|---|
| #108/PR-066, R2-04 legacy adapter | 같은 상태의 signed x→Q→Pi, 미관측 질량 보존 | 새로운 joint-law 표본에 적용; 물리상태·분모·측도 자격 필요 |
| #411,#417,#440 tensor MES | full harmonic/STF, 공통 proper rotation, 진폭과 방향 분리 | scalar ceiling 대신 원 tensor 보존; singular/ill-conditioned chart와 철회된 WU 주장은 그대로 |
| #449 Report A | 하나의 공동 물리 feasible set에서 functional 최적화 | 이번 normalized selection polytope로 연결; 자료 likelihood 자체는 외부 의무 |
| #466 tensor_joint_r7 | nuisance quotient, bounded/Gaussian calibration, confidence images | 무제한 nuisance rank와 prior가 있는 정보는 다른 실험; 선택한 경우만 계산 |
| legacy Teff moment | dipole+STF finite ansatz의 정확한4차 구면 moment와 remainder | 낮은 비용의 algebra oracle; 광자 spectrum·polarization·동역학 closure 입력은 별도 |
| legacy H(d),q(d),#544 | 반경법칙을 실제 survey window에 통과시키기, radial skew blindness | 현재 depth response 후보; 물리전단/와도 해석에는 optical/congruence map 필요 |
| #470 optical,#479–486/#506 CAS | 주어진 curvature majorant에서 유한 optical/no-caustic bound | 물리 curvature, affine-redshift,clock/screen 입력 필요; #470 본문 경로는 현 checkout에 없어 body만 확인 |
| #533,#552,#553 | catalogue normalizer, coupled event interval, 공통 STF calibration | [THEORY.md](THEORY.md)의 joint weight/selection 경계로 실제 확장 |
| #561 A,h와 K03 제한식 | compensated history와 실제 sky/depth rank, E1 drift 제한식 | 두-redshift source contract를 추가; 기존 실험은 재실행하지 않음 |

직접 읽은 핵심 자료:

- [R2-04 코드 지도](../../../observational_upgrade_r2/R2-04/sources/research/LEGACY_CODE_REUSE.md)
  및 [이론 지도](../../../observational_upgrade_r2/R2-04/sources/research/LEGACY_THEORY_REUSE.md).
- `docs/codex_handoff/mes_tensor_research_integration/RESEARCH_SYNTHESIS.md`.
- `docs/research_reports/final_candidate_20260907/HTT_REPORT_A_EVIDENCE_INTEGRATED_R3.md`.
- `docs/research_program/tensor_joint_r7/THEORY.md`.
- `docs/solver_free_research_20261014/research/THEOREM.md`.
- `docs/observational_reboot_20261014/research/LEGACY_REBOOT_REVIEW.md`.
- 기존 `physical_input_3week_audit_20261016/{PHYSICAL_INPUT_RESEARCH_KO,TEFF_HTT_BRIDGE_KO}.md`.

옛 수치와 그림의 조건은 유지한다. MES는 같은 CMB에서 나온 함수이므로 독립
likelihood로 한 번 더 곱하지 않는다. rapidity와 v/c, C_l와 D_l, shear ceiling과
signed 전체 x의 상한을 구별한다. Teff는 제한 oracle로 재사용하며 새 solver로
부활시키지 않는다. 검증되었던 제한 결과와 미해결 물리 입력을 함께 보존한다.
