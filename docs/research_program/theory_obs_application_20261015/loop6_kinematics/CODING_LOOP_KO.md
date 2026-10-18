# HTT Loop6 coding 연구: Legacy kinematical distribution × actual CF4 / Planck

Run date 2026-10-15 KST.
Owner checkout /home/cosmosapjw/Dropbox/bianchi/htt_base,
branch obs/solver-free-dossier-20261014,
baseline HEAD 13d8d85fa470d645d008986e8f77d8d0f70fdf54.
User's original uncommitted Loop1–5 research is preserved;
all new work has separate paths. Native subagent dispatch
NOT_RUN (no host agent-spawn tool exposed).

## C1–C2: original physics source vs current result targets

Legacy PDF source SHA256:
c1aefb6ab9d27b423a75274cb6887fe6cb494b7f21e1e2f750577b43c07e0942.
Legacy HTT.zip:
3696f806b2639be1f9ea0fc17e96e89124a8ec5802e58dd7a31b710667e6d8c3.
Uploaded later code_package.zip:
f3a27b49972c3139824a72faf97ce7fff1b96f487c9d2669f1ebc606fd9dee66.

The executed original HTT/obs_defaults file has a
wrong Watkins-2023 source string for old 2009-like
bulk proxy; later code_package _meta corrects it.
The old Bayes factor cannot be presented as a
new CF4 result. We preserve legacy x,Q,Pi math,
not its unqualified physical input identifications.

Current authenticated CF4 2023 tables:
- /mnt/extdrive/workdir/raw/cf4_full/table3.dat
  SHA256 c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d.
- /mnt/extdrive/workdir/raw/cf4_full/table4.dat
  SHA256 b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94.
Registered CF4 38,053 rows; selected 35,970,
z_CMB in 0.01..0.10 by published Vcmb/c and positive
published DMzp sigma and valid angular J2000 positions.
Selected group ID SHA256
f54706b8ff5c50c25a5a74c4b153f7f9e719a28582db044e00e5930dd30e3c88.
The table releases do not specify a true full-sample
selection-corrected velocity likelihood nor the group
shared calibration covariance.

Actual latest Planck source: Loop5 original
9 temperature maps / real low-l 32 harmonics,
single sky with mapped T common support.
Do not treat SMICA/OE/HM/noSZ/NILC as independent
cosmological realizations.

## C3–C5: new code and run paths

A. htt/obsstat/cf4_apparent_kinematic_distribution.py
  - native J2000 unit-vector construction;
  - five orthonormal STF2 basis tensors;
  - zero contraction of antisymmetric velocity
    gradient under radial n.n double contraction;
  - fast Gauss-Legendre 20-point flat-LCDM
    dL(z), analytic d ln(dL)/dz;
  - six method-family intercepts, optional
    per-method centered log-z slopes;
  - nuisance bulk and observer/source-dependent
    angular dipole; physical acceleration not
    inferred from generic nuisance dipole;
  - fixed model angular STF2 Hubble residual
    and conditional diagonal-Gaussian covariance;
  - column-normalized QR, stable no full
    35,970x35,970 matrix inverse;
  - corrected actual Q^TQ identity residual
    (not the earlier tautological R^-1R check);
  - 5D conditional Gaussian norm/3 and
    Sigma2_proxy/6 mapping without physical claims.

B. scripts/run_cf4_apparent_kinematic_distribution_20261015.py
  - actual CF4 Table3/4 hash-authenticated
    materialization into selected in-memory
    arrays and compact NPZ outputs;
  - nine source/nuisance/uncertainty/depth
    model contrasts; an explicit rare family
    pooling alternative for CAL2+SBF14+
    MIXED_OTHER724 -> OTHER740;
  - 12 delete-one HEALPix NSIDE1 sky-region
    rank/method sensitivity tests.
  - Results:
    results/cf4_rawgroup_appHubble_STF2_v1
    results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2
  - Original full six method case preserved;
    2 sky-patch failures were diagnosed as
    disappearing sparse CAL-specific slope,
    not silently removed. In pooled case
    12/12 delete-one-sky-region runs PASS.

C. htt/obsstat/legacy_defect_conditional_bridge.py
  - literal original MES coefficient scenario
    and exact tilt-density scalar formula;
  - explicit scalar Cl/T0 harmonic convention;
  - Gaussian reported bulk speed -> beta_proxy
    -> Omega_tilt -> signed x -> occupancy Q,
    exceedance Pi; no signed negative x clipping.
  - Does not fake true posterior of omega or a.

D. scripts/run_legacy_defect_kinematic_bridge_20261015.py
  - verifies legacy HTT.zip/main_FINAL.pdf
    original SHA256; checks the original
    mislabelled obs_defaults source;
  - 3 report-type velocity sources (2009
    WFH and two correlated CF4 2023 windows)
    x 3 epsilon1 scenarios x 9 processed
    Planck same-sky C2/C3 choices,
    exactly 81 conditional branches.
  - Results:
    results/legacy_defect_actual_source_bridge_v1

E. htt/obsstat/cf4_cmb_stf_frame_and_orientation.py
  - source ICRS J2000 -> Galactic
    active proper SO(3) rotation, Astropy/
    IAU convention; both tensor legs rotated;
  - SO3-invariant normalized STF2 contraction
    and principal-eigenaxis separation.

F. scripts/run_htt_cf4_planck_stf_orientation_20261015.py
  - conditionally sampled full CF4 WLS
    Gaussian (32k samples; scientific limits
    above), physically fixed Planck Galactic
    STF2 and published CMB reference beta.
  - Results:
    results/cf4_planck_STF_morphology_orient_v1

G. Tests:
  tests/obsstat/test_cf4_apparent_kinematic_distribution.py
  tests/obsstat/test_legacy_defect_conditional_bridge.py
  tests/obsstat/test_cf4_cmb_stf_frame_and_orientation.py
  6+5+3=14 targeted tests passed after
  numerical QR diagnostic correction.

## C6–C7: numerical, mathematical, and observational checks

1. Synthetic five-STF basis orthogonality and
tracefree identity. Tests with actual random
antisymmetric gradients show n^TWn = 0 to
~machine precision.

2. Synthetic injection over 1,800 random
directions and z∈[0.015,.08] recovered
5 STF coordinates, known bulk vector and
angular dipole in the exact finite fitted model
to absolute precision 1e-8.

3. Limiting dL(z) for small z matches cz/H0.
Gaussian WLS preserves correlated 5D
coefficient covariance. No manual positive
norm clipping; norm distributions sampled
from 5D Gaussian.

4. Source-z group IDs exactly authenticated,
plus original CF4 method-family distributions
and a declared low-support pooling sensitivity
branch. Real sky-region deletion exposes
source window/model dependence.

5. Published same-sky Planck temperature
Q tensors are compared after a validated ICRS
to Galactic coordinate transformation. A
joint rotation of both tensors preserves
normalized Frobenius cosine and axis spacing.
The physical cosmological null remains unknown.

6. Source reported bulk: 2009 WFH 407±81,
2023 CF4 R150 387±28 and R200 419±36 km/s.
Those are reported scalar speed summaries,
NOT independent new bulk-flow likelihood
recomputations. The two 2023 windows share CF4.

7. Source closure limitation: raw group
magnitudes and Vcmb are calibrated/processed;
no true observer tetrad, shear optical transfer,
full CF4 correlated selection/noise, physical
Bianchi Einstein constraints or geodesic beam
applied. Numerical success does not close
physical inference.

8. Wolfram symbolic:
  n^T W n = 0 for general antisymmetric W;
  hyperbolic 3-metric diag(1,e^2x,e^2x)
  gives Ricci diag(-2,-2e^2x,-2e^2x)
  and scalar -6; this conflicts with
  sign statements of original Bianchi V
  compared with its own FLRW k sign.
  Legacy curvature claims held, not substituted.

## C8: resource and sensitivity

All 35,970 selected group fits + nine
independent processing hypotheses were run
locally in approx. 1.5 sec (2 BLAS threads)
using compact fixed-column QR; RSS ~216 MiB
in the method-pooled branch. Full source
catalogue original retained, no 4 GB C-matrix
inversion. The saved selected-source
numerical cache can be reused without
re-reading original CF4 tables when
source identity is unchanged.

Nominal apparent ||gamma|| 0.0332577,
formal sigma_proxy/Theta median 0.0113925,
90%-plus cosmic uncertainty not estimated.
Leave-one-region conditional norm/3 spans
[0.00872,0.01284].
True selection, shared calibration and
cosmic covariance likely dominate
naive independent-error uncertainty.
Fit chi2/dof ~0.766 is NOT independent
proof that survey systematic variance is
correctly calibrated.

## C9: adversarial physics review, one pass

- Old group-frame/MES curvature convention
  inconsistent across V/IX signs; do not
  import its geometric curvature x pushforward.
- Generic local residual STF2 cannot be
  called homogeneous GR shear, as it
  includes source/calibration/large-scale
  structure and geometry-dependent window.
- Five-formal-source Gaussian posterior
  does not constrain antisymmetric omega.
- The fitted magnitude angular dipole is
  not four-acceleration.
- A published bulk speed divided by c
  is not a unique global geometry-matter
  rapidity beta; same CF4 window 150/200
  are correlated.
- The Planck observer CMB dipole and the
  galaxy number-count dipole have distinct
  source operators, not interchangeable
  almost-EGS epsilon1 measurements.
- MIO comment wrong tilt normalization
  has not been proven to affect executable
  numerical source code. No false bug claim.
- Original sources and earlier uncommitted
  owner research preserved.

## C10: final output, acceptance, next physics

Successful computational outputs are
self-contained JSON, compact NPZ, PNG
and readable REPORT_KO.md per
results/ subfolder. THEORY_LOOP_KO.md,
this report and BLOCKER_DELTA.json,
NEXT_RESEARCH_DAG.json and MANIFEST.json
are stored in this same Loop6 root.

Scientific claim tier:
SOURCE_CONDITIONAL_OBSERVATIONAL_MORPHOLOGY,
NOT PHYSICAL_GLOBAL_BIANCHI_KINEMATICS.
Do not publish new shear, vorticity,
4-accel, beta or nonzero signed defect
posterior from this exploratory model.

Ready next: survey-selection full probability
normalization; calibrated correlated
CF4 source covariance; causal observer/source
optical first-jet; physical forward-response
Bianchi/boltzmann and actual multi-redshift
CMB/CF4 joint null; independent
proper-motion or transverse channel for
rotation; exact curvature-congruence sign
repair before physical evidence.

No commit, PR, remote push or upload-back
performed; keep owner uncommitted changes.
