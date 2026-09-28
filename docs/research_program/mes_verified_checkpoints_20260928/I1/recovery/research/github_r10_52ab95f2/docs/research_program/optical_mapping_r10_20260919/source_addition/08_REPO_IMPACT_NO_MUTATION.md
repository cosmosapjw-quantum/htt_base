# Repository impact — no mutation

Repository:
cosmosapjw-quantum/htt_base
snapshot:
50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb

Affected:
- htt/bass/hierarchy/terms.py: T9 uses -(ell+2);
- htt/bass/hierarchy/hierarchy_rhs.py: adds T9 to sum_T and returns -a*sum_T;
- htt/bass/hierarchy/mode_mixing_blocks.py: pre9 uses -(ell+2);
- tests compare packed/full paths sharing the same source convention;
- docs/lowell_bianchi_solver_reference.md reproduces the negative T9 sign.

Any sign-sensitive Bianchi/CMB result using shear-down coupling must be revalidated after a
source-sealed patch.

Results using only representation algebra, local-observer boost geometry, rank logic, or
independent operators are not automatically invalidated.

No repository write was performed.
