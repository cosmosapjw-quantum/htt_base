CAS15-C03 spectral helper validation, 2026-10-08.

- Source: `Spectral.lean`, SHA-256 `166f85718c297f70094dd901b08d1d252a566bae0de0ea119a3576c6cfa2437a`.
- Notes: `SPECTRAL_NOTES.md`, SHA-256 `f4c5f98c89c162a23907d98e776b3aa40b47f34a44e6e3e82c98566019a462ce`.
- Working directory: `/home/cosmosapjw/lean_oracles/viii_oracle`.
- Command: `lake env lean /home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-15/ls_projection_continuation_v1_20261008/Spectral.lean`.
- Pinned environment: Lean `v4.31.0`, mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`.
- Final raw execution: `attempt4.stdout`, `attempt4.stderr`, `attempt4.exit` = `0`. Both printed theorem axiom sets are `[propext, Classical.choice, Quot.sound]`.
- `attempt1` failed at parser tokens; `attempt2` failed on inner-product notation; `attempt3` failed from passing the map in place of its applied vector. These are source/type elaboration errors, not mathematical counterexamples. Raw outputs and exit codes are retained.
- Formal scope: Rayleigh unit-vector perturbation estimate and ordered-gap deduction from three pointwise matches. Rotated coercivity and ordered eigenvalue matching are derived in `SPECTRAL_NOTES.md`, but have no Lean kernel proof here.
