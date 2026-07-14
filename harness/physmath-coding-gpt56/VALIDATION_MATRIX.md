# VALIDATION_MATRIX.md — BASS/HTT (htt_base) instantiation

| Requirement | Test/check | Level | Expected | Status | Evidence |
|---|---|---|---|---|---|
| import 가능 | `venv/bin/python -m pytest tests/contracts --collect-only` | software | collects | PASS | 427 collected (v9 cycle) |
| 계약 게이트 | `venv/bin/python -m pytest tests/contracts -q` | software | 1 pre-existing fail only | PASS | cf4pp network-blocked fail documented |
| EGS3 정리 게이트 | `make egs3-gates` (+egs2/teff/pr07-gates) | scientific | all pass | PASS | 342+ gates (rev-r190 count) |
| D_2 회귀 앵커 | Rust `bass_rs dump_dl_spectrum_sparse` | scientific | 1002.086744 μK² bit-identical | PASS | 14+ commits (Rust path); PSTF `test_d2_pstf_closure.py` xfail (PR-024c open) |
| x_C bit-identity | comparator gate suite | scientific | bit-identical | PASS | egs3-gates PSD/A1 |
| 카드 결정성 | every card/figure `--check` | operational | byte-stable | PASS | rev-r19x cards; NOTE v6 builder re-enumerates live tree (test_frozen_package_freeze.py pins via git) |
| 단위 일관성 | dimension/unit-provenance gate | scientific | exact | **CONCERN** | NSC audit: cz-as-Mpc bug class confirmed twice (C1/C9); no unit-provenance gate class exists yet |
| 알려진 극한 | σ_v closed form; visibility floor 0.632456 | scientific | within tolerance | PASS | test_cf4_mv_bulkflow 0.04%; CAMB crosscheck 0.2% |
| 보존/제약 잔차 | Gauss+momentum monitors | scientific | <1e-10 | PASS | v7 seals; KE/OMK monitors <1.6e-10 |
| GRF 스펙트럼 충실도 | generator band-variance vs analytic | numerical | ratio ~1 per component | **FAIL** | NSC audit V2: (0.843,0.829,0.997) — Hermitian-plane defect open in pv_forward_mocks.py |
| systematics 주입 | monopole/spectrum injection gates | scientific | leak nulled | **NOT_RUN** | NSC audit item 10: gate class absent; monopole leak passed all existing gates |
| 수렴성 | R_v finer-grid; DESI z-quadrature | numerical | converged | **CONCERN** | R_v conv PASS; DESI nz=40 C_1 ×1.36 unconverged (NSC C4-P1) |
| 재현성 | fixed-seed rerun + `make reproduce-v9` | operational | reproducible | PASS | 74/74 + 36/36 hashes verify in-zip |
| 성능 | single-run wall clock | operational | 10–15 s target | CONCERN | ksolve=93% measured bottleneck (perf memory); target not yet met |

Status: `PASS / CONCERN / FAIL / NOT_RUN / NOT_APPLICABLE`

_FAIL/CONCERN/NOT_RUN rows = NSC self-adversarial audit findings
(`docs/audits/self_adversarial_audit_20260713_nsc/08_final_referee_report.md` §5 must-fix);
remediation is REV-R199+ scope pending owner sign-off._
