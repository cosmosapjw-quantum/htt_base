# New Real-Data Results Package (REV-R102 / REV-R103)

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: mixed_full_sky_map_and_cf4_reconstruction_grid
null_mock_status: mixed_null_calibrated_and_bootstrap
generating_command: `Codex new-results plan K1 + K4`
git_commit_or_worktree_state: pending_commit

## Scope

Two genuinely new, model-independent results produced from real data already in
the repository, using the existing OBSSTAT estimator stack plus minimal drivers.
Both are diagnostic-only: no Bianchi family identification, geometry detection,
native low-ell solver output, HTT posterior/evidence, or MIO certificate is
produced. They are excluded from the existing manuscript result set.

The honest publishable framing is methods + model-independent measurement +
rigorous null: the framework recovers the established low-ell anomalies as
calibrated model-independent features and measures the CF4 bulk-flow apex
profile, while producing no false Bianchi/source-identification claim.

## K1 - Null-calibrated low-ell morphology of the real Planck PR3 map

Driver: `scripts/make_lowell_morphology_real_map.py`. Data: Planck PR3 SMICA
NSIDE=16 temperature map; isotropic LambdaCDM (CAMB ref) synfast null ensemble
n=10000, seed=12345. Report: `docs/generated/lowell_morphology_real_map_report.{json,md}`.

| Statistic | Observed | p-value | Tail |
| --- | --- | --- | --- |
| S_{1/2} | 6.10e3 | 0.059 | P(null <= obs) |
| parity even/odd ratio | 0.628 | 0.018 | P(null <= obs) |
| parity asymmetry | -0.228 | 0.018 | P(null <= obs) |
| planarity mean | 0.518 | 0.043 | P(null >= obs) |
| ell2-ell3 axis alignment | 69.2 deg | 0.65 | P(null <= obs) |
| axis-to-CMB-dipole-apex | 72.9 deg | 0.71 | P(null <= obs) |

- The map recovers the parity (odd-power excess) and large-angle (S_{1/2})
  low-ell anomalies as model-independent features; planarity is marginal.
- The power-inertia ell2-ell3 axis and the axis-to-CMB-apex show NO anomaly in
  this estimator (honest nulls; this is not the multipole-vector axis-of-evil
  statistic).
- Look-elsewhere across the six statistics is tracked, not globally corrected:
  the parity p=0.018 over six trials is not globally significant.
- No Bianchi or source-identification claim is made.

## K4 - CF4++ bulk-flow apex versus depth

Driver: `scripts/make_cf4_bulkflow_apex_depth.py`. Data: CF4++ reconstruction
grid (163,760 cells), 7 radial shells 90-450 Mpc/h. Report:
`docs/generated/cf4_bulkflow_apex_depth_report.{json,md}`.

- Bulk-flow amplitude rises to ~590 km/s at 250-300 Mpc/h, then falls to
  ~130-190 km/s in the deep shells.
- The apex stays within ~5-46 deg of the full-sample apex out to 300 Mpc/h, then
  reverses (~120-149 deg) at the reconstruction edge (flagged as a likely edge
  effect).
- Bootstrap apex dispersion over correlated reconstruction cells is a lower
  bound on the true direction uncertainty, not a full covariance.
- Model-independent kinematic descriptor; not a frame-violation or Bianchi
  claim.

## Excluded candidates (critically filtered)

- Joint common-axis posterior over the four dipoles: the built `latent_axis`
  likelihood has no directional term, so the common axis is prior-flat; the
  result collapses to a non-result or a re-presentation of the already-reported
  shared-cause/concordance. Excluded as empty.
- DESI footprint resultant-dipole systematics floor: the resultant amplitude is
  footprint-dominated and already shipped as the longrun jackknife diagnostic.
  Excluded as re-presentation.
- DESI cosmological clustering dipole: blocked (no matched randoms/masks).
- Any positive Bianchi/tilt evidence: blocked (amplitude-matched contamination
  null, no native morphology atlas).

## Standing blocks

Bianchi family identification and geometry detection remain blocked pending the
native low-ell morphology atlas, matched masks/randoms, full covariance, and the
equivalence-class gates. Nothing here lifts those blocks.
