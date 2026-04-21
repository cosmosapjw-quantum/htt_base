# 07A. PR Deliverable Map
## file-level outputs / API signatures / regression artifacts / opened claims

---

## 0. purpose

이 문서는 WBS를 file/API/test granularity로 보강한다.
각 PR는 아래 네 가지를 반드시 가진다.

- touched files
- new or modified signatures
- regression artifact
- the strongest claim allowed after merge

---

## PR-00 — authority freeze
- files: `README_INDEX.md`, `00_AUTHORITY_TREE.md`
- artifact: authority-diff note
- claim opened: authority frozen only

## PR-01 — tensor helper layer
- files: `conventions.py`, `state.py`, tests
- API: `gamma_trace`, `gamma_norm2_tensor`, `pstf_gamma`, `raise_vector`, `lower_vector`
- artifact: invariant-basis contraction matrix
- claim opened: tensor helper frozen

## PR-02 — family registry
- files: `registry.py`, `03_FAMILY...`, tests
- API: `get_family_spec(name, h=None)`
- artifact: family metadata dump + \(h\)-consistency table
- claim opened: registry-complete for all 11 families

## PR-03 — geometry core
- files: `geometry.py`, `01A...`, tests
- API: `build_geometry`, `connection_from_commutators`, `spatial_ricci_from_connection`, `spatial_ricci_from_compact_formula`
- artifact: Type I/V/IX + scaling regression
- claim opened: geometry-ready for named family branch only

## PR-04 — matter projection
- files: `background.py`, tests
- API: `project_species_to_normal_frame`, `total_matter_projection`
- artifact: orthogonal vs tilted source-pack table
- claim opened: normal-frame matter projection frozen

## PR-05 — background core
- files: `background.py`, tests
- API: `background_rhs`, `background_constraint_residuals`
- artifact: residual summary bundle
- claim opened: background-ready for named family branch only

## PR-06 — exact Thomson
- files: `collision.py`, tests, `01_SSOT...`
- API: `exact_thomson_source`
- artifact: isotropic-null-limit regression + monopole/directional separation test
- claim opened: exact collision contract frozen

## PR-07 — visibility/reionization adapter
- files: `visibility.py`, tests
- API: `opacity_from_physical_inputs`, `optical_depth`, `visibility_function`, `homogeneous_reionization_history`
- artifact: monotonic opacity/visibility summary
- claim opened: source-history contract frozen

## PR-08 — family backend protocol
- files: `backends.py`, `03A...`, family submodules, tests
- API: `build_backend`, `operator_factory`, `seed_factory`, `label_translator`
- artifact: backend card instantiation report
- claim opened: backend-contract-complete for named family branch

## PR-09 — hierarchy layout and IMEX packing
- files: `hierarchy.py`, `02A...`, tests
- API: `flatten`, `unflatten`, `assemble_mass_matrix`, `assemble_explicit_block`, `assemble_implicit_block`, `assemble_source_vector`
- artifact: sparse layout manifest
- claim opened: hierarchy layout frozen

## PR-10 — output split layer
- files: `output.py`, `06...`, `06A...`, tests
- API: `write_output_archive`, `observer_boost_output`
- artifact: archive schema validation bundle
- claim opened: output split gate frozen, no fitting yet

## PR-11 — validation gate and hard stop
- files: `validation.py`, `05...`, tests
- API: `hard_gate_before_fitting`, `score_branch_readiness`
- artifact: gate report schema
- claim opened: fitting gate may evaluate only if all upstream bundles exist

---

## 1. mandatory regression artifact schema

Every PR artifact must contain:
- branch/family labels
- file/API version
- residual summary
- known-limit checks
- forbidden-shortcut checks
- opened claim

---

## 2. claims that remain forbidden even after PR-11

- all-family implementation-complete
- statistics-ready
- full exact tier-A complete
- unavailable analytic backends complete
- output gate implies fitting evidence

---

## 3. one-line summary

이 deliverable map의 목적은  
**각 PR가 끝났을 때 무엇이 실제로 생겨야 하는지와, 그때 비로소 어떤 claim이 열리는지를 파일/API 단위로 고정하는 것** 이다.
