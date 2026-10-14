# DESI DR1 BGS Bright: retained scalar BAO summary

At z_eff = 0.295234695, the released summary gives **D_V/r_d = 7.924712 ± 0.150734** (one standard deviation).
The corresponding qiso is 0.982880442 ± 0.018695108. All quantities are dimensionless.

This is a re-expression of the retained BGS Bright v1.2 syst likelihood using its fixed Gaussian covariance.
D_V/r_d = qiso × (D_V/r_d)_fid and sigma_D = sigma_q × (D_V/r_d)_fid; the released fiducial ratio is 8.062742860.

| Pointwise conditional coverage | qiso interval | D_V/r_d interval |
|---|---|---|
| 68.268949% | [0.964185334, 1.001575550] | [7.773978, 8.075446] |
| 95.000000% | [0.946238703, 1.019522180] | [7.629279, 8.220145] |

The intervals invert the scalar Gaussian acceptance rule and intersect with the positive prediction domain; a zero lower endpoint is open.
They are pointwise confidence summaries conditional on the released approximation, not posterior credible intervals or simultaneous family coverage.
The historical R9 alpha=1/80 and family allocation remain unchanged; that campaign was not rerun.

![Two views of the same scalar likelihood](desi_bao_summary.png)

The figure holds the observed datum fixed and varies the prediction. Its ordinate is L/L_max, with peak 1; the curve is not a probability density over predictions.
The CSV also retains normalized log sampling densities in the observed qiso and observed D_V/r_d coordinates.
Changing the observed variable gives p_D(D_obs | q_pred) = p_q(D_obs/fid | q_pred)/fid. Changing only the prediction coordinate introduces no Jacobian; relative likelihood is identical in both panels.

| Artifact field | Value |
|---|---|
| owner | htt |
| claim_tier | C1 |
| status | CONDITIONAL |
| artifact_mode | RELEASED_SUMMARY_REEXPRESSION |
| allowed_use | Scalar released-summary measurement and pointwise conditional likelihood |
| transfer_source | none |
| null_mock_status | NOT_RUN_NO_NEW_MOCK_CLAIM |
| covariance_status | FIXED_RELEASED_COVARIANCE_CONDITIONAL |
| Forbidden uses | raw-catalogue coverage; posterior or evidence; angular or depth response; shear or tilt detection; Bianchi family identification |

- Conditional on the released fixed Gaussian summary approximation and its covariance.
- The retained syst product is used once; its stat alternative and raw rows are not independent factors.
- The qiso and D_V/r_d views are deterministic re-expressions of the same scalar observation.
- These pointwise intervals do not alter the historical R9 alpha=1/80 or family allocation.
- No new catalogue fit, posterior, evidence, holdout, mocks, angular response, or native transfer is supplied.

## Source and execution

- Input: `/mnt/extdrive/workdir/raw/desi_dr1_fullshape_bgs_bright_v1.2/likelihood/likelihood_bao-recon_syst_BGS_BRIGHT-21.5_GCcomb_z0.1-0.4.h5`
- Source ID: `DESI_DR1_FULLSHAPE_BGS_v1.2:836a2107c1edfb655f7a5c41701607dd8542efe4dae4309737658829cfe63ba3`
- SHA256: `836a2107c1edfb655f7a5c41701607dd8542efe4dae4309737658829cfe63ba3`; bytes: 22845
- Git HEAD: `6365e36d0ccc6acddb7f6909aacea8d766c0fc4a`; exact active source hashes and worktree status are in `analysis.json`.
- Python: 3.10.22; executable: `/home/cosmosapjw/venv/bin/python`.
- Package versions: `{"h5py": "3.14.0", "matplotlib": "3.10.3", "numpy": "2.2.6", "scipy": "1.15.3"}`.
- Existing intake and Gaussian law are reused; the immutable source is never modified.

```sh
/home/cosmosapjw/venv/bin/python /home/cosmosapjw/Dropbox/bianchi/htt_base/scripts/analyze_desi_bao_summary.py --input /mnt/extdrive/workdir/raw/desi_dr1_fullshape_bgs_bright_v1.2/likelihood/likelihood_bao-recon_syst_BGS_BRIGHT-21.5_GCcomb_z0.1-0.4.h5 --output-dir /home/cosmosapjw/Dropbox/bianchi/htt_base/docs/observational_analysis_20261014/results/desi
```

Outputs: [analysis.json](analysis.json), [likelihood_curve.csv](likelihood_curve.csv), [PNG](desi_bao_summary.png), [PDF](desi_bao_summary.pdf).
