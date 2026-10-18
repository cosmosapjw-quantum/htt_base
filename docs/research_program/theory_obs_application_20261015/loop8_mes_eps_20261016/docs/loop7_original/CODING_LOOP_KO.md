# Loop7 Scientific Coding: PR248–258 and PR521 into actual observed-source diagnostics

Date: 2026-10-15 KST. Local repo:
  /home/cosmosapjw/Dropbox/bianchi/htt_base
HEAD 13d8d85fa470d645d008986e8f77d8d0f70fdf54
and branch obs/solver-free-dossier-20261014.
Other dirty files are owned by earlier loops and preserved.
No external raw bytes copied or modified.
No commit/push was attempted.

## C2 source and mathematical-implementation linkage

Input:
docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/legacy_defect_actual_source_bridge_v1/result.json

This already stores actual released same-sky Planck
l2/l3 masked processed source spectra, nine product
identities, precise 2009/2023 velocity-window provenance,
and the prior source conditional legacy scenarios.
The new loop consumes the verified prior source
rather than repeating expensive raw Planck extraction.

Active code:
  htt/src/common/statistical_foundations.py
  htt/src/common/mes_theorem_authority.py
  htt/src/common/typefree_functionals.py
  htt/htt/htt/infer/conditional_legacy_pushforward.py
  docs/observational_upgrade_r2/R2-04/sources/code/legacy_adapter.py

The R2-04 adapter and its immutable legacy bounds.py/ssot.py
bytes are SHA-256 checked against the actual
docs/observational_upgrade_r2/R2-04/RETURN.json before
loading/executing. Old source math is not edited.

## C5 implemented features

htt/obsstat/typed_xqpi_observation_bridge.py:
  exact survival probability for clipped Gaussian
  published bulk speed under explicit beta=V/c hypothesis;
  2048 deterministic paired quantile source atoms;
  dimensionless conditional tilt density;
  PR124 source-admitted geodesic shear/omega anchors
  under explicit eps1=0 source scenario;
  typed mismatch when CF4 local apparent STF is
  passed to wrong physical sector MES anchor;
  finite matched-source strict Pi numerical oracle.

scripts/run_htt_typed_xqpi_observation_20261015.py:
  imports and actually executes R2-04's original
  conditional_legacy_image and frozen LegacyAdapter
  on 2048 paired speed atoms per source window.
  Computes 27 source scenarios (3 windows x 9 same-sky
  Planck maps). Never stacks the nine products
  as independent skies or both CF4 windows as
  independent observations.
  Executes a second R2-04 call with physically
  undefined sectors and checks x/Q mass 1, Pi=[0,1].
  Numeric machine-readable results and two PNG
  observational/method-sensitivity plots create-only.
  Sampling law SAMPLING, not POSTERIOR.

tests/obsstat/test_typed_xqpi_observation_bridge.py:
  exact analytical CDF versus deterministic 8192-node
  paired quantiles; strict threshold atom including
  observed Z<=0 mass; paired denominator-swapping effect;
  typed PR124 geodesic sigma/omega source and
  forbidden four-accel/curvature anchors; invalid inputs.

## C6–C8 actual execution results

Source run command:
  PYTHONPATH=htt:htt/htt:htt/src OPENBLAS_NUM_THREADS=2
  OMP_NUM_THREADS=2 MPLBACKEND=Agg /usr/bin/python3
  scripts/run_htt_typed_xqpi_observation_20261015.py
  --output-dir
  docs/research_program/theory_obs_application_20261015/loop7_typed_defect/results/typed_mes_legacy_xqpi_v1

Run exit=0; scalar source computation ~0.4 seconds,
after reading cached prior science JSON.
Two reported plots and ~50 KiB result.json created.
Maximum allowed analytic vs finite sample
strict Pi discrepancy <=1/2048; source tests pass.

Targeted regression command:
  PYTHONPATH=htt:htt/htt:htt/src OPENBLAS_NUM_THREADS=2
  OMP_NUM_THREADS=2 /usr/bin/python3 -m pytest -q
  tests/obsstat/test_typed_xqpi_observation_bridge.py
  tests/htt/test_conditional_legacy_pushforward.py
  tests/obsstat/test_legacy_defect_conditional_bridge.py
  tests/obsstat/test_cf4_apparent_kinematic_distribution.py
  htt/src/common/test_typefree_functionals.py
  htt/src/common/test_typefree_depth.py
  htt/src/common/test_typefree_fibers.py
  --disable-warnings --maxfail=1

Observed: 52 passed, 0 failure, 1.35 sec;
stored remote actual test output:
  /tmp/htt_typed_xqpi_loop7_tests_20261015.log

Important scope:
  PR124 actually refuses e1=observed solar-motion dipole
  for the strict geodesic residual-cmb hierarchy;
  e1=0 scenario is algebraic and not fully sky calibrated.
  Current physical Bianchi tensor likelihood is absent,
  and no physical total defect Q or Pi is admitted.
  Parent Loop6 actual CF4 modulus shear source is
  an apparent source-processing STF, not sigma_G.

## C9–C10 exact next executable

1. Source-unit-qualified actual Planck EGS multipole
   representation/derivative assumptions and
   same-sky pair response, without reusing nine maps
   as independent stochastic samples.
2. Source CF4 calibrated redshift/optical first-jet
   plus selection and correlated depth covariance:
   infer *actual identifiable physical tensor* before
   signed x_C.
3. Physically registered Bianchi forward source,
   observer/matter/radiation congruences,
   curvature Hamiltonian convention repaired,
   and posterior sample identity to feed PR521
   posterior_legacy_image directly.
4. Theorem for physically qualified total signed x
   anchor required before interpreting Q/Pi as
   a universal fraction. Otherwise use typed
   sector stresses and partial identification.

Native subagent NOT_RUN; no tool exposed.
Commit/push NOT_ATTEMPTED; original owner checkout
and raw source are untouched, only new in-scope
module/script/tests/report result artifacts created.
