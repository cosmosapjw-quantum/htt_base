# 관측 분석 실행 준비

기준 HEAD: `6365e36d0ccc6acddb7f6909aacea8d766c0fc4a`

입력 접근과 실행 환경을 확인한 결과다. 관측법칙·공분산의 타당성 판정은 각 분석의 별도 결과를 따른다.

| 경로 | 입력·환경 | 현재 가능한 산출물 | 실제 적합 상태 |
|---|---|---|---|
| DESI_RELEASE_SUMMARY | 실행 입력 준비됨 | Released scalar qiso likelihood, DV/rd re-expression and pointwise conditional intervals | RELEASED_SUMMARY_REEXPRESSION; no new catalogue or physical cosmology fit |
| CF4_GROUPED_DIAGNOSTIC | 실행 입력 준비됨 | Observed grouped coverage and conditional response sensitivity; synthetic injection remains a separate validation section | ACTUAL_PHYSICAL_POSTERIOR_HOLD |
| CMB_SAME_SKY_DIAGNOSTIC | 실행 입력 준비됨 | Four common-mask same-sky product contrasts at retained ell=2..5 | DESCRIPTIVE_ONLY; calibrated physical likelihood remains open |

## DESI_RELEASE_SUMMARY

```bash
/home/cosmosapjw/venv/bin/python -B scripts/analyze_desi_bao_summary.py --input workdir/raw/desi_dr1_fullshape_bgs_bright_v1.2/likelihood/likelihood_bao-recon_syst_BGS_BRIGHT-21.5_GCcomb_z0.1-0.4.h5 --output-dir /home/cosmosapjw/Dropbox/bianchi/htt_base/docs/observational_analysis_20261014/results/preparation/runs/desi
```

- Implement a source-bound theta-to-DV/rd response and sound-horizon/absolute-scale assumptions before cosmological fitting.
- Do not interpret an isotropic qiso as an angular Bianchi response; use justified release/window forward mapping.

## CF4_GROUPED_DIAGNOSTIC

```bash
/home/cosmosapjw/venv/bin/python -B scripts/r2_cf4_product_diagnostic.py --source workdir/raw/cf4_full --output /home/cosmosapjw/Dropbox/bianchi/htt_base/docs/observational_analysis_20261014/results/preparation/runs/cf4.json
```

- 기존 검증 결과 재사용이 기본이다. 위 명령은 해당 입력이나 코드가 바뀐 경우에만 실행한다.
- Publish a source-supported selected-catalogue model or supported subset; Table 3 method presence is not DMzp method-mixing weights.
- Bind heliocentric Vh measurement convention, true-redshift/source-motion model, velocity uncertainty and group/flow covariance.
- Supply a proper shared calibration/absolute-scale prior and finite-distance remainder bound or explicitly declared truncation scenario.
- Fit latent distances with original DMzp,Vh; derived Dist/Vpec are not extra independent observations.

## CMB_SAME_SKY_DIAGNOSTIC

```bash
/usr/bin/python -B scripts/r2_cmb_product_diagnostic.py --controls docs/generated/tensor_joint_r8/owned_controls/cmb/cmb_controls.npz --metadata docs/generated/tensor_joint_r8/owned_controls/cmb/cmb.json --output /home/cosmosapjw/Dropbox/bianchi/htt_base/docs/observational_analysis_20261014/results/preparation/runs/cmb.json
```

- 기존 검증 결과 재사용이 기본이다. 위 명령은 해당 입력이나 코드가 바뀐 경우에만 실행한다.
- Bind released map response, beam/pixel/removal and full selected-sky measurement covariance, using supported simulations or split products rather than scatter between component maps.
- Supply a physical low-mode response and, only for physical F4, sourced angular-mean T0 and restored physical dipole with uncertainties.
- Control omitted modes in the norm actually used; masked residual RMS is not a full-sphere sup-norm bound.

전체 후속 작업은 ANALYSIS_PLAN.json과 CODEX_HANDOFF_KO.md를 따른다. 기존 검증 로그를 덮어쓰지 않는다.
