import numpy as np
from unittest import TestCase
from scipy.integrate import solve_ivp
from scipy.linalg import expm

from bass.kinetic.moving_projection import (projection_blocks, memory_kernel,
                                          initial_hidden_force, integrate_split)


def rotating(s):
    v = np.array([[np.cos(s)], [np.sin(s)]])
    dv = np.array([[-np.sin(s)], [np.cos(s)]])
    return projection_blocks(np.zeros((2, 2)), v, dv)


def test_rotating_observable_memory_without_physical_dynamics():
    grid = np.linspace(0, 2.1, 37)
    a, q, x = integrate_split(grid, [1., 0.], rotating, rtol=1e-12, atol=1e-14)
    np.testing.assert_allclose(a[0], np.cos(grid), atol=2e-10)
    np.testing.assert_allclose(x, np.broadcast_to([[1.], [0.]], x.shape), atol=2e-10)
    np.testing.assert_allclose(memory_kernel(1.7, .2, rotating), [[-1]], atol=2e-10)
    np.testing.assert_allclose(initial_hidden_force(1.7, 0., [0., 1.], rotating), [1], atol=2e-10)
    for i, s in enumerate(grid):
        np.testing.assert_allclose(rotating(s).left @ q[:, i], 0., atol=2e-10)


def weighted(s):
    v = np.array([[1., .2*s], [s, 1.], [.3, -.4*s]])
    dv = np.array([[0., .2], [1., 0.], [0., -.4]])
    w = np.diag(np.exp(np.array([.2, -.4, .1])*s))
    dw = np.diag(np.array([.2, -.4, .1])*np.diag(w))
    a = np.array([[-.4, .2, .1], [-.1, -.3, .5], [.3, -.2, -.7]])
    return projection_blocks(a, v, dv, w, dw)


def test_moving_metric_chain_rule_and_full_reconstruction():
    s = .6
    b = weighted(s)
    eps = 1e-5
    np.testing.assert_allclose(b.left_derivative, (weighted(s+eps).left-weighted(s-eps).left)/(2*eps), rtol=1e-8, atol=1e-9)
    np.testing.assert_allclose(b.complement_derivative, (weighted(s+eps).complement-weighted(s-eps).complement)/(2*eps), rtol=1e-8, atol=1e-9)
    grid = np.linspace(0, 1.5, 31)
    a, q, x = integrate_split(grid, [.5, -.4, .8], weighted, rtol=1e-12, atol=1e-14)
    generator = np.array([[-.4, .2, .1], [-.1, -.3, .5], [.3, -.2, -.7]])
    direct = np.column_stack([expm(generator*t) @ [.5, -.4, .8] for t in grid])
    np.testing.assert_allclose(x, direct, atol=2e-10)
    for i, t in enumerate(grid):
        np.testing.assert_allclose(a[:, i], weighted(t).left @ direct[:, i], atol=2e-10)
        np.testing.assert_allclose(weighted(t).left @ q[:, i], 0., atol=2e-10)


def test_static_block_schur_kernel_and_initial_force():
    a = np.array([[-1., .3, .4], [.1, -2., .2], [.2, .1, -3.]])
    def blocks(t):
        return projection_blocks(a, np.array([[1.], [0.], [0.]]), np.zeros((3, 1)))
    duration = .7
    want = a[:1, 1:] @ expm(duration*a[1:, 1:]) @ a[1:, :1]
    np.testing.assert_allclose(memory_kernel(.9, .2, blocks), want, atol=1e-12)
    force = a[:1, 1:] @ expm(duration*a[1:, 1:]) @ [.6, -.2]
    np.testing.assert_allclose(initial_hidden_force(.9, .2, [.4, .6, -.2], blocks), force, atol=1e-12)


def test_complex_basis_and_hermitian_metric():
    v = np.array([[1.+0j], [1j]])
    b = projection_blocks(np.diag([1j, -1j]), v, np.zeros_like(v), np.array([[2., .1j], [-.1j, 1.]]))
    np.testing.assert_allclose(b.left @ v, np.eye(1), atol=1e-14)
    np.testing.assert_allclose(b.projector @ b.projector, b.projector, atol=1e-14)


def test_real_initial_data_with_complex_generator_preserves_phase():
    generator = np.array([[0, 1j], [1j, 1j]])
    def blocks(t):
        return projection_blocks(generator, np.array([[1.], [0.]]), np.zeros((2, 1)))
    a, q, x = integrate_split([0., 1.], [1., 0.], blocks, rtol=1e-12, atol=1e-14)
    np.testing.assert_allclose(x[:, -1], expm(generator) @ [1., 0.], atol=2e-12)
    np.testing.assert_allclose(initial_hidden_force(1., 0., [0., 1.], blocks), [1j*np.exp(1j)], atol=2e-10)
    def later_complex(t):
        matrix = np.array([[0., 1.], [1., 1j*t]])
        return projection_blocks(matrix, np.array([[1.], [0.]]), np.zeros((2, 1)))
    np.testing.assert_allclose(memory_kernel(1., 0., later_complex), [[np.exp(.5j)]], atol=2e-10)


def test_rank_or_nonfinite_basis_rejected():
    for bad in [np.zeros((2,1)), np.array([[np.nan], [1.]]), np.ones((2,3))]:
        with TestCase().assertRaises(ValueError):
            projection_blocks(np.eye(2), bad, np.zeros_like(bad))


def test_bad_weight_and_reversed_memory_rejected():
    with TestCase().assertRaises(ValueError):
        projection_blocks(np.eye(2), np.ones((2,1)), np.zeros((2,1)), np.diag([1., -1.]))
    with TestCase().assertRaises(ValueError):
        memory_kernel(0., 1., rotating)
    with TestCase().assertRaises(ValueError):
        integrate_split([0., 0.], [1.,0.], rotating)


if __name__ == '__main__':
    tests = [value for key, value in globals().copy().items() if key.startswith('test_')]
    for test in tests:
        test()
        print(test.__name__, 'PASS')
    print(len(tests), 'test functions passed')
