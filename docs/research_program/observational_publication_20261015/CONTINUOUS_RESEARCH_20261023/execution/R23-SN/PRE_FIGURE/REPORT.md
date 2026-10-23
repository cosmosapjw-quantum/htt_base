# R23-SN: public MODEL000 covariance diagnostic

Owner HTT; C0 public-model conditional response; transfer source none. This is
an executed numerical diagnostic for the retained SN010010 light curve, with
scientific admission **HOLD** and independent review pending. It does not
qualify V04/H04 or reinterpret the paired reboost results.

## Source and convention audit

The prior [SN010010 report](../../../ADVERSARIAL_AUDIT_20261022/continuation/sn010010/REPORT.md)
binds 59 released PS1MD measurements, a fixed 23-row gri selection, 34 public
source files, compiled original PS1 filter columns and AB primary, relative MJD,
F99 MW attenuation, and the released B21-named MODEL000 surfaces. This candidate
reuses that selection and input manifest. The retained measurement-only fit has
chi-square 61.414238130153144 on 19 degrees of freedom, or 3.2323283226396393,
above the frozen adequacy threshold 3. The code checks its objective at the
stored parameters without rerunning the old optimizer.

The public MODEL000 contains `salt2_lc_relative_variance_{0,1}`,
`salt2_lc_relative_covariance_01`, `salt2_lc_dispersion_scaling`, and
`salt2_color_dispersion`. The [sncosmo 2.13.1 SALT2Source
API](https://sncosmo.readthedocs.io/en/latest/api/sncosmo.SALT2Source.html)
defines their relative model covariance. We fold the same MW attenuation into
each rest-frame filter and compute `C_total = diag(FLUXCALERR^2) +
outer(predicted_FLUXCAL, predicted_FLUXCAL) * C_relative`. The covariance
contains a within-band correlated color-dispersion block. We hold covariance
fixed within each least-squares step, recompute it after each step, and stop
when the largest parameter move is below 2e-7. There is no residual clipping,
global variance tuning, or threshold change. We deliberately do not silently
apply `SALT2.INFO` floors/ERRMAP switches whose mapping to the private nominal
producer fit is unresolved.

The released `PPLUS.yml` gives `PFITdatawithsys` a private
`$PS1_USERS/dscolnic/PANTHEON+/lcfitting/PS1.nml` base and sets
`FITMODEL_NAME` to
`$PANTHEONPLUS/submit_trainSALT2/out_train_v7_1_bd17fix/SALT2.MODEL000`.
That binding is distinct from the public B21-named directory. The actual
nominal model, complete PS1.nml fit settings, and observed PFITdatawithsys
FITRES row for CID 010010/IDSURVEY 15 are not among the retained public inputs.
The retained recursive pinned release-tree inventory has 3223 entries with
`truncated=false`: no `PS1.nml`, no `out_train_v7_1_bd17fix` path, and only
ten simulation FITRES files; there is no observed fit FITRES path.
The public `Pantheon_SH0ES.dat` summary is available (FITCHI2 12.4905,
NDOF 19), but it is not the observed FITRES identity. Consequently neither
producer likelihood parity nor source-equivalent model-error behavior is
established.

## Measured result and limits

| Quantity | Value | Interpretation |
|---|---:|---|
| Original measurement-only chi-square / 19 | 3.2323283226396393 | Frozen adequacy HOLD |
| Public MODEL000 covariance chi-square / 19 | 0.8984302155742678 | Conditional public-source screen only |
| Public fit `x0` relative to summary | -0.8131528561% | Fails frozen 0.1% parity bound |
| Public fit `x1` minus summary | -0.0185353009 | Fails frozen 0.001 bound |
| Public fit `c` minus summary | +0.0039404225 | Fails frozen 0.001 bound |
| Public fit `t0` minus summary | -0.0131718674 d | Fails frozen 0.01 d bound |

The lower conditional chi-square is the effect of using a physically supplied
model covariance with this public source. It is not evidence that the
measurement-only failure was cured in the nominal producer pipeline. The
source binding and FITRES parity questions remain open. No empirical total
reboost coefficient, global standardization, BBC, PV or native solver result
is inferred.

## Verification and first failure

The independent reference test reads the raw MODEL000 grids directly and
uses SciPy spline/bilinear interpolation, rather than the sncosmo model-error
interpolator. For one r-band row, direct relative diagonal 0.0006444801285
and sncosmo 0.0006350176141 differ by -1.46824%; the raw color-dispersion
block 0.0002704099617 and sncosmo 0.0002704099623 differ by 2.04e-9
relative. Different interpolation schemes account for the diagonal comparison
criterion of 3%; no tolerance was enlarged after seeing a failed source
calculation.

The first reference test failed 1/2 because the test applied the negative
variance safeguard `0.0001` as a universal minimum. The sncosmo prescription
applies it only when the interpolated variance is negative. The first failure
gave direct diagonal 0.0025576865474 versus sncosmo 0.0006350176141, a
75.1722% relative discrepancy. Correcting that test formula yielded 2/2
passes. The raw first failure is retained in `RAW_RECEIPT.json`. Five
unchanged Astropy warnings concern excluded `*PS1-*` KCOR columns.

Commands, in the repository root with `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`:

```bash
.venv/bin/python docs/research_program/observational_publication_20261015/CONTINUOUS_RESEARCH_20261023/execution/R23-SN/model_error.py
.venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/CONTINUOUS_RESEARCH_20261023/execution/R23-SN/test_model_error.py
```

For scientific parity, obtain the exact nominal `PS1.nml`, model directory
and its complete error grids/INFO, and the observed nominal PS1 FITRES row
with generation configuration. Then re-evaluate the same row/fit conventions
under an independently reviewed producer binding. The present conditional
result is a bounded diagnostic and remains **HOLD**.
