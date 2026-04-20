# FB-6 literature-shape fixtures

These files are the qualitative FB-6.3 literature templates consumed by
`htt/bass/integration/test_full_bianchi_coverage.py`.

- They are **not** digitized external-code outputs.
- They are deterministic low-ell shape envelopes used to pin the
  Pontzen-Challinor 2009 morphology checks until the full FB-7 LOS +
  covariance stack lands.
- Every `.npz` stores:
  - `ell` : integer multipole grid `[2, 30]`
  - `template` : normalized qualitative shape on that grid
  - `oracle_name` : stable fixture identifier
  - `source_note` : short provenance string

The CAMB numeric oracle remains the shipped production fixture
`data/camb_ref_planck2018.npz`; the FB-6 literature files here are only
the qualitative side of the regression suite.
