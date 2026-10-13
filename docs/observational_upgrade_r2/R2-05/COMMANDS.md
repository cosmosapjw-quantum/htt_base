# R2-05 commands

Working directory: `/home/cosmosapjw/Dropbox/bianchi/htt_base`.
Frozen base: `4571756afa75b17ecc199bfca80fd4da0fb2a684`, tree `68d581424a99d68b67d90b2e1affea733ce2379e`.
Branch: `r2/05-shared-latent-density-20261014`.

Initial status and remote metadata are preserved in raw/initial_status.txt and raw/initial_remote.txt. Existing dirty/untracked files were preserved. No checkout or staging operation was used.

First run, exit 0, 22 passed:

```bash
/usr/bin/python -m pytest tests/r7/test_selected_joint_density.py tests/r7/test_joint_experiment.py tests/r9/test_intake_depth.py -q
```

Final affected run, exit 0, 79 passed:

```bash
/usr/bin/python -m pytest tests/r7/test_selected_joint_density.py tests/r7/test_joint_experiment.py tests/r9/test_intake_depth.py tests/r7/test_gaussian_law.py tests/r7/test_catalogue_laws.py tests/r7/test_evidence_binding.py -q
```

Raw stdout/stderr are combined in raw/tests_first.log and raw/tests_affected.log. No failed first execution exists for this candidate. Numeric tolerances and injection seed are committed to the candidate test source; no rerun-derived tolerance relaxation occurred.

Reviewer regressions before repair, pytest exit 1, five failed (raw preserved):

```bash
/usr/bin/python -m pytest tests/r7/test_selected_joint_density.py -q -k reviewer
```

Repaired affected run, pytest exit 0, 85 passed in 4.06 s:

```bash
/usr/bin/python -m pytest tests/r7/test_selected_joint_density.py tests/r7/test_joint_experiment.py tests/r9/test_intake_depth.py tests/r7/test_gaussian_law.py tests/r7/test_catalogue_laws.py tests/r7/test_evidence_binding.py -q
```

Logs: raw/reviewer_regressions_first_failure.log and raw/repair_tests_affected.log. Original logs are unchanged.
