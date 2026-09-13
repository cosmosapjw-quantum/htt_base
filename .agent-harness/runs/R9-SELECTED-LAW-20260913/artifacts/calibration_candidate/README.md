# CF3--SDSS PV public-input calibration candidate

`cf3_sdss_calibration_candidate.py` is deliberately a standalone candidate for
eventual ownership by `htt.infer`.  It contains no feature extraction and makes
no confidence, coverage, or official-zero-point claim.

The downloaded primary-source inputs are VizieR `J/AJ/152/50` (`CF3_ReadMe.txt`,
`CF3_table3.dat.gz`) and VizieR `J/A+A/602/A100`
(`Tempel2017_ReadMe.txt`, `Tempel2017_table1.dat.gz`).  `CF3_table3.dat` is the
decompressed exact public table used by the executable diagnostic.  The local
SDSS release input is
`/mnt/sn850x2t/htt_base_e2e/workdir/raw/sdss_pv_zenodo_6824749/SDSS_PV_public.dat`
with its adjacent `data_description.pdf`.

The PDF says `logdist_corr` is the preferred group-richness FP measurement and
requires group-level zero-point calibration; it does not state that a CF3 shift
is already applied.  The individual candidate therefore uses unshifted
`logdist`, while retaining `corrected=True` as a distinct, unshifted option.
Its CF3 convention is explicitly

```
eta_CF3 = log10(D_comoving(z; H0=75 km/s/Mpc, Omega_m=.31)
                / (D_L,CF3 / (1+z)))
```

where both distances are physical Mpc.  There is no additional factor of `h`.
The public diagnostic uses CF3 `Vcmb/c` only as a visible proxy for the paper's
individual redshift, and is never a paper replay.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q artifacts/calibration_candidate/tests
PYTHONDONTWRITEBYTECODE=1 python3 artifacts/calibration_candidate/run_public_input_diagnostic.py
```

The exact PGC join finds 296 rows.  Applying the CF3 ReadMe's documented
Tully--Fisher source-code rule (`r_Dist` H or I) retains 294 rows and excludes
PGC 39712 and 59838.  This is `RULE_BASED_PUBLIC294`, not a byte-exact replay
of the authors' pair-selection implementation.  The exact individual-redshift
convention is supplied by SDSS `zcmb`, but the CF3-to-Tempel membership
crosswalk and joint SDSS--CF3 covariance are not public here.  Thus outputs
retain `joint_covariance_status` as `UNAVAILABLE_NOT_ZERO_FILLED`: quoted
per-row widths define a descriptive weighted point estimate only, never its
standard error or a confidence law.  `IDgroupT17 == 0` creates a separate
singleton for every row.

For a future supplied realization with an explicit joint covariance, the
module returns an offset coefficient vector `l` for ordered inputs
`[SDSS-anchor rows, CF3 rows]`.  Given a full-depth SDSS projection `M`, use
`G = [M, 0] + (M @ 1) l` and propagate `G C_joint G^T`.  This keeps shared
offset covariance in the initial level; contrast rows with zero sum cancel the
additive offset.  Per-object posterior widths may set declared consensus
weights only and never provide `C_joint` by themselves.
