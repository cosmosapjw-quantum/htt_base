# Low-ell Morphology of the Real Planck Map (REV-R102)

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: full_sky_cleaned_map
null_mock_status: null_calibrated_isotropic_lcdm_ensemble
config_hash: `sha256:20b745f9e2be82822d9959b2bc5a46502e3894a4a4f2961f3aad1f635c8c0102`
input_hashes:
- sha256:90780c4c42c6c4d371ea17d98de3db01d104a016bae2af58e8d9a6c304f88867
- sha256:6a51719d224dad50a3e85aa79ec126dab03ea4fbb8996699b11a8d8d4c91c942
- sha256:3217b51b4c6d88a6df71375c98b3922e1a175f657aece8f67d673b0bd4146e6a
generating_command: `python scripts/make_lowell_morphology_real_map.py`
git_commit_or_worktree_state: `7888011+dirty`

## Null-calibrated low-ell statistics (Planck PR3 SMICA NSIDE=16)

| Statistic | Observed | p-value | Tail |
| --- | --- | --- | --- |
| s_one_half | 6096.9 | 0.0593 | P(null S_1/2 <= observed) |
| parity_even_over_odd_ratio | 0.62804 | 0.0175 | P(null even/odd ratio <= observed) |
| parity_asymmetry | -0.22847 | 0.0175 | P(null asymmetry <= observed) |
| planarity_mean | 0.51791 | 0.0426 | P(null planarity >= observed) |
| qo_axis_alignment_deg | 69.219 | 0.6495 | P(null ell2-ell3 angle <= observed) |
| axis_to_cmb_dipole_deg | 72.935 | 0.7050 | P(null axis-to-apex angle <= observed) |

Low-ell (ell=2,3) preferred axis (Galactic l,b): 326.6, -1.0 deg.

## Caveats

- model-independent low-ell feature p-values; not evidence for any Bianchi model and not a source-identification claim
- ell2-ell3 axis alignment is a power-inertia-axis diagnostic, not the multipole-vector axis-of-evil statistic
- no native low-ell solver output or morphology atlas is used
- no Bianchi family identification or geometry detection is claimed
- full-sky cleaned map; no mask deconvolution or full pixel-pixel covariance
- look-elsewhere across the tested statistics is tracked, not globally corrected
- null ensemble is isotropic LambdaCDM synfast (n=10000, seed=12345); cross-healpy-version reproducibility may vary at the synfast RNG level
