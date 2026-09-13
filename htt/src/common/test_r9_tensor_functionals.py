import numpy as np
from common.tensor_functionals import fixed_contraction_support


def test_fibre_boundary_nonregularity_and_uncertain_q_refusal():
    l = np.eye(7)[:3]; direction = np.eye(7)[3]
    for t in (.01, .0001, .000001):
        v = np.array([1-t, 0, 0])
        result = fixed_contraction_support(l, v, direction, q_is_fixed=True)
        assert abs(result['support']-np.sqrt(2*t-t*t)) < 1e-10
        np.testing.assert_allclose(l@result['witness'], v, atol=1e-10)
        assert abs(result['witness']@result['witness']-1) < 1e-10
    assert fixed_contraction_support(l, [1, 0, 0], direction, q_is_fixed=True)['status'] == 'BOUNDARY_NUMERICALLY_UNRESOLVED'
    assert fixed_contraction_support(l, [1.1, 0, 0], direction, q_is_fixed=True)['status'] == 'EMPTY_FIBRE'
    assert fixed_contraction_support(l, [0, 0, 0], direction, q_is_fixed=False)['status'] == 'JOINT_Q_INVERSE_IMAGE_REQUIRED'
