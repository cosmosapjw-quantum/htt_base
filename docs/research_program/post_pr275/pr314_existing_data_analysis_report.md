# Existing-data observational analysis report — PR-314

## Executive result

This work unit exhausted the observational analyses that were executable from
the already available local data under the currently validated lane operators,
without acquiring another observational or mock data set.

One observed analysis qualified: a Planck PR3 **SMICA-only** low-ell diagnostic
against exactly 300 paired FFP10 `CMB_i + noise_i` realizations. Its conservative
observation-inclusive twelve-feature family rank is

\[
p_{\mathrm{finite\ family}} = \frac{19}{43},
\]

with finite-ensemble resolution floor `1/301`. This value is not unusually
small within the declared finite reference ensemble. It is a diagnostic-only,
SMICA- and null-ensemble-conditional result. It does not establish Commander
robustness, a joint Planck result, a global response, source attribution, a
native-solver result, or Bianchi-family identification.

The generated numerical source is
[`pr314_planck_pr3_smica_existing_result.json`](../../generated/pr314_planck_pr3_smica_existing_result.json).
The independent compact replay source is
[`pr314_planck_pr3_smica_existing_replay.json`](../../generated/pr314_planck_pr3_smica_existing_replay.json).

## Analysis contract

The observed input is the Planck PR3 R3.00 SMICA intensity product in Galactic
coordinates. The null ensemble contains release IDs `00000` through `00299`,
with each row formed by adding its SMICA CMB and SMICA noise maps in delivered
`K_CMB` before one shared reduction to `microK_CMB`. The separate 999-row
CMB-only archive was not pooled with this ensemble.

Observation and null rows use the same common temperature mask, SMICA intensity
beam, output pixel window, full band-limited mask-coupling inverse, harmonic
convention, multipole-vector convention, and frozen feature order. The retained
band is `2 <= ell <= 5`. Planck's zero placeholders at `ell=0,1` are represented
as a unit no-op after the weighted monopole and dipole removal; the positive
beam requirement is retained over `ell=2..5`.

The raw `12 x 12` covariance is preserved. Its rank is 12/12 and its Cholesky
factor exists. Because the feature vector mixes `microK_CMB^2` and dimensionless
quantities, the condition gate is evaluated after diagonal standardization and
is invariant to a nonzero per-feature unit rescaling. The standardized condition
number is `1279.9885708671413`; the raw mixed-unit value
`11395606370.999586` is retained as a scale-dependent diagnostic and is not the
gate. The finite family rank itself is computed from conservative
observation-inclusive per-feature ranks and does not use covariance whitening.

## Frozen feature result

The first four feature values have units `microK_CMB^2`; the remaining values
are dimensionless.

| Feature | Observed value | Exact local finite rank |
|---|---:|---:|
| `cl_l2` | 193.8224608082074 | `75/301` |
| `cl_l3` | 482.81500504720276 | `239/301` |
| `cl_l4` | 221.71407529901884 | `32/43` |
| `cl_l5` | 296.0984207099504 | `16/301` |
| `parity_even_over_odd_l2_l5` | 0.5334823131380724 | `88/301` |
| `power_tensor_gap_l2` | 0.4715528740410001 | `19/43` |
| `power_tensor_gap_l3` | 0.5407968062652974 | `52/301` |
| `multipole_l2_absdot` | 0.07924088316110656 | `122/301` |
| `multipole_l3_absdot_0` | 0.35210890475144285 | `20/301` |
| `multipole_l3_absdot_1` | 0.38719563264076345 | `29/43` |
| `multipole_l3_absdot_2` | 0.5199976611586113 | `278/301` |
| `multipole_plane_alignment_max_l2_l3` | 0.9560413115686207 | `115/301` |

These local ranks are members of the preregistered twelve-feature scan. They
must not be selected post hoc as separate discovery claims. The family-level
finite rank above is the reportable primary diagnostic for this work unit.

## Reproducibility and execution evidence

The successful attended execution is bound to:

- code commit `b6411109a54d4f2ac05bc60cac270d936c1b9417`;
- code tree `ab2d595e2d6246f5f3a5fa91e49694499d05276c`;
- acceptance hash `sha256:82e427f2ba8c0c63516c6b52d9bcc46f36ad4610865c292860aca74fbb3f07c9`;
- observed SMICA raw hash `sha256:60952c645eb33d151905ddf5837477e15ca02a3261feca4ceca3c3feece4f9ac`;
- ordered null-ID hash `sha256:f40e60de955bb241543e81215636485af9bb3429ec1de983093c476e6592671f`;
- result hash `sha256:898d08fc7c70205fbb8c7580fbaef1074357a8b3255ac77afd8273b92511da97`;
- compact observed-map hash `sha256:681fae58f57c61d814010db73ba74e3dcad169ceddb9f6ac60454c8499108823`.

The compact replay returned `REPLAY_MATCH`, scientific projection hash
`sha256:0cf5c6933b5d21e0c0c9d3e021adc72476367076b8c6a2d010bc4ab7f879e56b`,
and `observed_raw_reopened=false`.

The successful off-repository result directory is
`/mnt/sn850x2t/htt_base_e2e/workdir/analysis_outputs/planck_pr3_smica_pr314_r2`.
The preceding directory without the `_r2` suffix is intentionally retained as
raw failure evidence: it contains a start record followed by a direct-CLI
import failure, no observed payload read, and no scientific result. Preparation
also stopped before observed access on the release beam placeholder and
mixed-unit condition-gate defects; both received focused regression tests.

No raw scientific input was deleted or compressed in this work unit. One
runtime exception to the no-download objective is recorded: the first call to
`healpy.pixwin(nside=16)` fetched the official 8.6 KiB healpy pixel-window
auxiliary table. This was not a new observational or mock data set, but it is
still a network-acquired runtime dependency and is not hidden.

## Other locally inventoried lanes

The distinction below is between local bytes and an executable scientific
contract. A directory containing partial source material is not treated as an
admitted analysis input.

| Lane | Local material | Current numerical disposition |
|---|---|---|
| Planck Commander/joint | Incomplete Commander and unmatched SMICA archives | `DEFERRED_INCOMPLETE_COMMANDER`; no joint covariance or robustness result |
| DESI | BGS_BRIGHT-21.5 NGC/SGC inputs, 1,000 EZmock and 25 Abacus realization trees | `BLOCKED_NO_COMPLETE_CANONICAL_ADMISSION`; the required ordered 1,028-record admission and compact observed/selection/covariance components do not exist |
| ACT DR6 | Fourteen release map variants and historical derived stores | `BLOCKED_NO_400_SIMULATION_ADMISSION`; no exact 400-row release simulation inventory or seven-component admission |
| CF4 | Raw and compact CF4-named material | `BLOCKED_NO_ADMITTED_CF4_DESCRIPTOR_OR_FULL_COVARIANCE`; no nine-component typed binding or validated full off-diagonal covariance |
| JWST-SN | Eight source-material files totaling 57,850,123 bytes | `BLOCKED_NO_FIVE_COMPONENT_BUNDLE_OR_2MRS_FORWARD_MODEL`; no typed row/covariance/competitor admission |
| HSC/KiDS | No matching local candidate data root | `REJECTED_NOT_PRESENT` |

Consequently no other observed statistic was computed. Existing historical
DESI PR-151 producers remain invalidated, and no retired CF4 numerical output
was revived. Synthetic profiles from prior closure PRs are implementation
evidence, not additional observed-data results in this report.

## Scientific interpretation and claim ceiling

Within the exact SMICA-only operator and the 300 paired FFP10 reference rows,
the observed twelve-feature family is not in a small finite-rank tail. This is
a useful negative diagnostic at the current resolution; it is not a statement
that all Planck component-separation, mask, response, or transfer uncertainties
have closed.

No source or geometry label is inferred. Local response rank is not computed
for this SMICA-only slice, the global response is missing, and the native
low-ell morphology atlas is unavailable. The admissible wording is therefore
`Planck PR3 SMICA-only, FFP10-conditional low-ell diagnostic`. All stronger
component-separation, source-attribution, native-transfer, or Bianchi-family
claims remain blocked.

## Artifact metadata

```yaml
owner: OBSSTAT
scope: PR-314 existing-data execution without new scientific dataset acquisition
claim_tier: diagnostic_only
transfer_source: none
source_release: Planck PR3 R3.00 plus FFP10 v3
sky_support_status: Galactic frame with Planck PR3 common temperature mask
null_mock_status: exact 300 SMICA CMB-plus-noise rows, observation-inclusive finite calibration
generating_procedure: scripts/observed_runs/run_planck_pr3.py
public_use: false
caveats:
  - SMICA only; Commander robustness not evaluated
  - no local or global response claim
  - no source, native-solver, or family-identification claim
  - other local lanes remained blocked and produced no observed statistic
```
