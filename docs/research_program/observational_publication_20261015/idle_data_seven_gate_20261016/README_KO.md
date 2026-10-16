# htt_base idle-data seven-gate research loop

Authority: Draft PR #547 @ `b942c4dba6c8eab6d0f791c7532874d35664f2a7`.
Independent theoretical/algorithmic research during the user's local CF4/Planck data downloads. 6-paper DAG stays **14/42 scoped completed**; 7 physical input gates unresolved, L01/S02 pending. Five independent *subprocess* test suites; host-native subagent execution NOT_RUN.

## Install and execute

```bash
python -m venv .venv
source .venv/bin/activate
pip install numpy scipy pytest matplotlib
PYTHONPATH="$PWD/src" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests
PYTHONPATH="$PWD/src" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python scripts/run_precursors.py
python scripts/run_parallel_suites.py
```

Acceptance of this packet: scope-conditional algebra and reproducible numerical examples only; it is **not** a real CF4 likelihood, Planck processing E2E null, Bianchi Einstein–Boltzmann polarization solver, or genuine material-tilt/vorticity inference.

Module split:
- `selected_sources.py`: hierarchical fixed-count selected mixtures, analytic normalisation, calibration-zeropoint gauge, wrong-but-normalized counterexample (H02/S04).
- `shared_sky.py`: one null unit per independent sky, shared method scans, exact rank (L03/L01).
- `kinematic_bridge.py`: distinct observer-boost anchor and quasar frame-spin/glide conditional rank (V03/K03).
- `bianchi_i.py`: exact Bianchi-I collisionless redshift, finite-time correction and unpolarized screen baseline (K04/B02).
- `partial_selection.py`: unknown event mass and Gamma-restricted relative selection-odds envelope (S04).

Full derivations and literature: `docs/SCOPED_THEORY_RESEARCH_KO.md`. Source identity and execution: `results/PROVENANCE_AND_SCOPE.json`, `results/MANIFEST_SHA256.json`, `results/PARALLEL_TEST_RECEIPT.json`, `results/MANUFACTURED_RESULTS.json`.

## Required local physical data after download

1. H02: unique original CF4 table2/3/4 source and parent W1-TF objects, parent selection/completeness, original method calibrations and source-group overlap IDs; source-selected mock coverage.
2. L03: PR3 T/Q/U mask/beams/split/FFP10 method and independent sky ID controls, foreground/systematic joint null.
3. V03: verified Bianchi/kinetic source-history T/E/B/visibility kernel and independent aberration anchor.
4. B02: AniCLASS or BASS physical source/IC branch pin and Boltzmann recombination, constraints, spectral/mode convergence.
5. K03: independent Gaia CRF3 quasar spin/glide calibration and galaxy PM+distance frame-matched sample; heldout nuisance-projected singular ranks.
6. K04: finite-z null Jacobi/distance transfer, emitter/observer 1+3 clocks, selection-corrected source likelihood.
7. S04: all known/unknown physical sector support or a correctly normalized joint likelihood before F/Q/Pi inference.

Source archives from user's legacy attachments are not redistributed here; the prior PR #547 preserved an immutable legacy source SHA ledger. No link to local user's drive is assumed accessible in this sandbox.
