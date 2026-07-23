# Executable Asset Catalog

Core commands run with `PYTHONPATH=src`. Optional scripts fail explicitly when their third-party dependency or data file is absent.

| Asset | Purpose | Command | PR use |
|---|---|---|---|
`experiments/rotation_covariance_test.py` | pole SO(3) covariance | `PYTHONPATH=src python experiments/rotation_covariance_test.py` | PR-251
`experiments/lowell_shell_poles_demo.py` | shell/cumulative reference trajectories | `PYTHONPATH=src python experiments/lowell_shell_poles_demo.py` | PR-252
`experiments/binning_stability_demo.py` | detects reference-DGP shell instability | `PYTHONPATH=src python experiments/binning_stability_demo.py` | PR-253/257
`experiments/shell_kernel_conservation_demo.py` | additive shell-kernel conservation gate | `PYTHONPATH=src python experiments/shell_kernel_conservation_demo.py` | PR-253
`experiments/planck_map_family_compare.py` | Planck map-family one-sky nuisance comparison | `PYTHONPATH=src python experiments/planck_map_family_compare.py --map SMICA=... --map COMMANDER=... --mask ...` | PR-258
`experiments/local_boost_global_tilt_benchmark.py` | source discrimination reference | `PYTHONPATH=src python experiments/local_boost_global_tilt_benchmark.py` | PR-256/264
`experiments/remote_fields_demo.py` | remote dipole/quadrupole toy | `PYTHONPATH=src python experiments/remote_fields_demo.py` | PR-259–261
`experiments/pole_response_rank_demo.py` | finite-difference source response SVD | `PYTHONPATH=src python experiments/pole_response_rank_demo.py` | PR-263/268
`experiments/coherent_fraction_demo.py` | set-valued coherent fraction | `PYTHONPATH=src python experiments/coherent_fraction_demo.py` | PR-265
`experiments/planck_lowell_poles.py` | optional actual Planck pole extraction | `PYTHONPATH=src python experiments/planck_lowell_poles.py MAP.fits --mask-fits MASK.fits` | PR-258
`experiments/plugin_probe.py` | optional plugin availability | `PYTHONPATH=src python experiments/plugin_probe.py` | PR-247/248
`experiments/adaptive_scan_evalue_demo.py` | anytime-valid exploration gate | `python experiments/adaptive_scan_evalue_demo.py` | PR-273
`experiments/track_boundary_validator.py` | Track I/II enforcement | `python experiments/track_boundary_validator.py --track II` | PR-248/274
`experiments/run_all.py` | reference suite | `PYTHONPATH=src python experiments/run_all.py` | all
