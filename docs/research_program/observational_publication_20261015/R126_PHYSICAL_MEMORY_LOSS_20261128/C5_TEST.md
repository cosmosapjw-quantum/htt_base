# C5 RED/GREEN and native smoke

RED: module absent
    from common.physical_memory_budget import build_context,metric_weights,collision_action,observation,integrate_budget,whiten,adjoint_objective
E   ModuleNotFoundError: No module named 'common.physical_memory_budget'
=========================== short test summary info ============================
ERROR tests/r126/test_r126_memory_budget.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.48s

First GREEN attempt: m0 test erroneously sliced full all-m flattened rows; corrected comparison to exact m0 rows, production implementation unchanged.
=========================== short test summary info ============================
FAILED tests/r126/test_r126_memory_budget.py::test_collision_and_observation[0]
1 failed, 6 passed in 1.63s

GREEN:
.......                                                                  [100%]
7 passed in 1.53s
