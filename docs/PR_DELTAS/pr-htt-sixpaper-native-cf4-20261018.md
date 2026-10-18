# Six-paper native CF4 continuation — draft PR #560

The retained CF4 joint summaries did not establish a physical sector mapping,
and the earlier calibration frontier had no observed method centers. This
increment calculates a common-angular-calibration obstruction on the unchanged
2048 joint draws and actual apparent-distance centers/coupled calibration sets
from the exact 35,970 selected groups. It preserves the original 42 acceptances.

Baseline: `research/htt-sixpaper-goals-robustness-20261018` at
`1e095a2749cce9b28e45aac043a82218c21f84e5`, stacked on draft #559. Primary
checkout and the official `.venv` were used. No new clone/worktree was made.

- S02: exact generalized-eigenvalue extrema plus directed-cycle minimax;
  common differential residual median 0.03011962061 mag. In 135/2048 original
  draws a three-window consistency condition strengthens every pair bound.
  All draw IDs/weights and physical NaNs are retained; physical unknown mass 1.
- H02: 20 actual fit blocks, source-linked method/group overlap, 40×40 working
  window covariance blocks, 720 conditional interval rows and shared-calibration
  LP projections. Gaussian working-law nx compatibility requires relative
  delta 0.01946163556665 mag; variance-only working bounds admit delta zero.
  Common angular calibration remains unbounded. Released-distance holdouts are
  post-calibration diagnostics, not independent upstream validation.

Code, tests, numerical results, figures and reports are under
`docs/research_program/observational_publication_20261015/CONTINUATION_20261018/`
in `S02_EXECUTION_20261018/` and `H02_EXECUTION_20261018/`.
`INDEPENDENT_REVIEW_NATIVE_CF4_20261018.md` records one fresh read-only Astra
review and closure of its one source-label finding. Requested implementations:
`gpt-6.1-sol/high`; reviewer `gpt-6-astra/xhigh`; observed identities UNKNOWN.

Validation: primary S02 12/12 and H02 13/13 tests; independent reviewer reran
both suites and reproduced all H02 actual fits by independent full-intercept
SVD. Goal-terminal semantics 5/5. The publication DAG/derived queue validate:
42 nodes, 14 completed, 28 unfinished. S02's missing physical response is now
explicitly recorded as blocked_input; dependencies and acceptance are unchanged.
L01 is the remaining ready node and is executing separately. H02 remains blocked
on true selection/shared-calibration/velocity law and source null simulations.

Scientific outputs remain conditional; all six papers NOT_READY_TO_SUBMIT.
No raw observational rows are added, no physical unknown is zero-filled, and
there is no native solver/ODE, main merge or journal submission. The unchanged
245-card engineering backlog and its historical task/accounting records are
not relabelled as new scientific completions.
