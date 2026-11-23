"""Signed Thomson suboperator and optional compiled AniCLASS output checks."""
import argparse
import ast
import hashlib
import json
import platform
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from scipy import __version__ as scipy_version

ANICLASS_HEAD = "be1e43fcb1d7549710ba3ca2baa74bb0216bd228"


def max_abs(values):
    return float(np.max(np.abs(values)))


def thomson_fixture():
    from bass.collision.coherency import ThomsonCoherencyPropagator
    from bass.transport.general_bianchi_transfer import gl_sphere_grid, _spherical_screen_basis
    from bass.transport.general_lie_stokes import (
        GeneralLieStokesOperator, LieGeometry, stokes_maps_to_vector, vector_to_stokes_maps,
    )

    degree, quadrature, depth = 3, 8, 1.0
    op = GeneralLieStokesOperator(degree, n_gl_theta=quadrature)
    zero = LieGeometry(np.zeros((3, 3)), np.zeros(3), np.zeros((3, 3)))
    _, _, n, weights = gl_sphere_grid(quadrature)
    rays = n.reshape(-1, 3)
    e1, e2 = _spherical_screen_basis(rays)
    angular = ThomsonCoherencyPropagator(rays, weights.ravel(), e1, e2)
    # Use both real quadratures of each |m|>0 pair and both initial polarizations.
    examples = 0
    generator_error = finite_error = zero_leak = 0.
    sdirk_errors = {n: 0. for n in (4, 8, 16)}
    # Vicente et al. (2026) Eqs. 18, 19, 22--24. E_BASS = -E_VPP
    # here after stripping the common harmonic phase, for this collision block.
    reference_m = np.array([[-9., -np.sqrt(6.)], [-np.sqrt(6.), -4.]]) / 10.
    basis = np.diag([1., -1.])
    generator = basis @ reference_m @ basis
    p_slow = (np.eye(2) + generator) / .7
    evolution = np.exp(-depth) * (np.eye(2) - p_slow) + np.exp(-.3 * depth) * p_slow
    for m in (0, 1, 2):
        for phase in ((1.,) if m == 0 else (1., 1j)):
            for initial_channel, channel in enumerate(("T", "E")):
                initial = np.zeros(op.dim, dtype=complex)
                initial[op.idx[channel][2, m]] = phase
                initial[op.idx[channel][2, -m]] = (-1)**m * np.conj(phase)
                expected_d = np.zeros_like(initial)
                expected_f = np.zeros_like(initial)
                for mm in {m, -m}:
                    amplitude = initial[op.idx[channel][2, mm]]
                    for j, target in enumerate(("T", "E")):
                        expected_d[op.idx[target][2, mm]] = amplitude * generator[j, initial_channel]
                        expected_f[op.idx[target][2, mm]] = amplitude * evolution[j, initial_channel]
                generator_error = max(generator_error, max_abs(op.apply(initial, zero, 1.) - expected_d))
                sky = vector_to_stokes_maps(initial, op.idx, L=degree, n_gl_theta=quadrature)
                actual = angular.advance(sky.reshape(-1, 4), depth)
                measured = stokes_maps_to_vector(actual, op.idx, op.dim, L=degree, n_gl_theta=quadrature)
                finite_error = max(finite_error, max_abs(measured - expected_f))
                zero_leak = max(zero_leak, max_abs(measured[expected_f == 0]))
                for ns in sdirk_errors:
                    stepped = op.advance_cell(initial, 1., zero, depth, substeps=ns)
                    sdirk_errors[ns] = max(sdirk_errors[ns], max_abs(stepped - expected_f))
                examples += 1
    orders = [float(np.log2(sdirk_errors[n] / sdirk_errors[2*n])) for n in (4, 8)]
    return {
        "fixture": "stationary cold-electron Thomson collision block, all five real quadrupoles; spatial derivatives, sources, expansion and tilt zero",
        "initial_conditions": examples, "depth": depth, "n_gl_theta": quadrature, "ell_max": degree,
        "signed_harmonic_generator_max_abs_error": generator_error,
        "angular_exact_flow_max_abs_error": finite_error, "zero_channel_leakage": zero_leak,
        "sdirk_absolute_errors": sdirk_errors, "sdirk_orders": orders,
        "passed": bool(max(generator_error, finite_error, zero_leak) < 2e-12 and min(orders) > 1.9 and sdirk_errors[16] < 1e-4),
    }


def anilos_ix_fixture(root):
    """Compare independent AniLoS RHS with BASS Lie+collision on the closed tensor sector."""
    from bass.transport.general_lie_stokes import GeneralLieStokesOperator, LieGeometry
    from scipy.integrate import solve_ivp

    source = Path(root).resolve() / "src/anilos/hierarchy.py"
    raw = source.read_bytes()
    oid = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    expected = "d54fdf7d1c757d249105602b19fe40441813d70e"
    if oid != expected:
        raise ValueError(f"AniLoS hierarchy differs from pinned upstream blob: {oid}")
    # Execute the exact NumPy function body. Only the optional Numba signature/
    # compilation decorator is removed. No cosmology or radial kernel is stubbed.
    module = ast.parse(raw, filename=str(source))
    fn = next(x for x in module.body if isinstance(x, ast.FunctionDef) and x.name == "tensor_hierarchy")
    fn.decorator_list.clear()
    exact_function = ast.Module(body=[fn], type_ignores=[])
    ns = {"np":np}
    exec(compile(exact_function, str(source), "exec"), ns)
    tensor_hierarchy = ns["tensor_hierarchy"]
    op = GeneralLieStokesOperator(3, n_gl_theta=8)
    # Set curvature-radius and conformal-distance units to one. IX has K=+1,
    # nu=+/-3 and structure matrix 2*handedness*I in this right-handed tetrad.
    optical_rate, duration = 1.7, .43
    basis = np.diag([1.,-1.,-1.])
    selected = [op.idx[ch][2,2] for ch in ("T","E","B")]
    upstream_indices = np.array([3,4,5])
    max_rhs, max_leak, max_finite = 0., 0., 0.
    for handedness in (+1,-1):
        geometry = LieGeometry(np.zeros((3,3)),np.zeros(3),2.*handedness*np.eye(3))

        def rhs(eta, values):
            # The closed branch only has the tensor quadrupole. rho_g=0 sets
            # gravitational feedback to zero, dynamics isolated to spin and collisions.
            return tensor_hierarchy(eta, values, 3, 3.*handedness, 1., -8., 1., 0., 1.,
                                    0., 0., optical_rate, np.array([2,6]),
                                    np.zeros(1,complex), np.zeros(1,complex), np.ones(3), np.ones(1,complex))

        for initial in np.eye(3):
            up = np.zeros(10,complex)
            up[upstream_indices] = initial
            native = np.zeros(op.dim,complex)
            native[selected] = basis @ initial
            raw_deriv = rhs(0.,up)
            deriv = op.apply(native, geometry, optical_rate)
            max_rhs = max(max_rhs, max_abs(deriv[selected]-basis@raw_deriv[upstream_indices]))
            max_leak = max(max_leak, max_abs(np.delete(deriv,selected)),max_abs(np.delete(raw_deriv,upstream_indices)))
            ext = solve_ivp(rhs,(0.,duration),up,method="DOP853",rtol=1e-12,atol=1e-14)
            if not ext.success:
                raise RuntimeError(ext.message)
            result = op.advance_cell(native,duration,geometry,optical_rate*duration,substeps=128)
            max_finite = max(max_finite,max_abs(result[selected]-basis@ext.y[upstream_indices,-1]))
    return {
        "fixture":"matched closed IX test-photon m=+2 T/E/B block, no metric feedback, constant scattering rate, both spatial orientations",
        "upstream_git_blob":oid,"upstream_source":"jgvicente/AniLoS 9b7a2611882dcca80a1491bcad2b8f05635faca7 src/anilos/hierarchy.py tensor_hierarchy, original NumPy body without JIT decorator",
        "native_basis_relative_to_raw_upstream_TEB":[1,-1,-1],"optical_rate":optical_rate,"duration":duration,
        "initial_conditions":6,"sdirk_substeps":128,"generator_max_abs_error":max_rhs,
        "off_sector_generator_leakage":max_leak,"finite_cross_code_max_abs_error":max_finite,
        "passed":bool(max_rhs < 2e-12 and max_leak < 2e-12 and max_finite < 5e-6),
    }


def aniclass_fixture(root):
    """Run two actual binary solves; changed output convention is the only physical/config difference."""
    import os
    ref = Path(root).resolve()
    head = subprocess.check_output(["git", "-C", str(ref), "rev-parse", "HEAD"], text=True).strip()
    if head != ANICLASS_HEAD:
        raise ValueError(f"AniCLASS source differs from fixture: {head}")
    binary = ref / "class"
    configs = {
        "hierarchy":"tam", "statistics":"non_stochastic", "non_stochastic_type":"bianchi",
        "output":"tCl,pCl", "modes":"t", "Omega_k":"0.01", "z_reio":"7.6711", "gauge":"synchronous",
        "k_output_values":"0.001", "l_max_tensors":"16", "non_stochastic_format":"class",
        "l_max_g_ten":"30", "l_max_pol_g_ten":"30", "l_max_ur_ten":"30",
        "radiation_streaming_approximation":"3", "perturbations_sampling_stepsize":"0.01",
        "tight_coupling_trigger_tau_c_over_tau_h":"0.005", "start_small_omega_tau":"0.001",
        "tol_perturbations_integration":"1e-6", "hyper_x_min":"1e-7",
    }
    tables = {}
    with tempfile.TemporaryDirectory(prefix="htt-r103-aniclass-") as scratch:
        out = Path(scratch)
        for convention in ("observable", "tam"):
            prefix = out / (convention + "_")
            ini = out / (convention + ".ini")
            params = {**configs, "multipole_normalization": convention, "root": str(prefix)}
            ini.write_text("".join(f"{k} = {v}\n" for k,v in params.items()))
            run = subprocess.run([str(binary), str(ini)], cwd=ref, env={**os.environ, "OMP_NUM_THREADS":"1"},
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180)
            if run.returncode:
                raise RuntimeError(f"AniCLASS exited {run.returncode}: {run.stdout[-2000:]}")
            matches = sorted(out.glob(convention + "_*alm_q0_t.dat"))
            if len(matches) != 1:
                raise ValueError(f"AniCLASS produced {len(matches)} matching alm tables")
            tables[convention] = np.loadtxt(matches[0])
    observed, tam = tables["observable"], tables["tam"]
    if not (np.array_equal(tam[:, 0], observed[:, 0]) and {2, 3, 16} <= set(tam[:, 0])):
        raise ValueError("inconsistent or insufficient multipole output")
    ell = observed[:, 0].astype(int)
    obs_z = observed[:,1::2] + 1j*observed[:,2::2]
    tam_z = tam[:,1::2] + 1j*tam[:,2::2]
    mapped = (1j**ell * np.sqrt(4*np.pi/(2*ell+1)))[:,None] * tam_z
    if np.any(np.max(abs(obs_z),axis=0) <= 1.e-12):
        raise ValueError("degenerate polarization benchmark")
    unsigned_b_rel = max_abs(obs_z[:, 2] - mapped[:, 2]) / max_abs(obs_z[:, 2])
    mapped[:, 2] *= -1  # Observable B reverses sign compared with the TAM normalization (Eq. 46).
    channel_rel = np.max(abs(obs_z - mapped),axis=0) / np.max(abs(obs_z),axis=0)
    return {
        "fixture":"AniCLASS compiled deterministic tensor mode, same IC and geometry, observable vs TAM",
        "source_head": head, "executable_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "tracked_source_clean": not bool(subprocess.check_output(["git","-C",str(ref),"status","--porcelain","--untracked-files=no"],text=True).strip()),
        "parameters":configs, "OMP_NUM_THREADS":1, "ell_range":[int(min(ell)),int(max(ell))],
        "channel_order":["T","E","B"], "observable_ell2_real_imag": observed[ell==2,1:].ravel().tolist(),
        "unsigned_B_negative_control_relative_error":unsigned_b_rel,
        "signed_observed_rows_l_ReT_ImT_ReE_ImE_ReB_ImB":observed.tolist(),
        "convention_error_scaled_by_channel_peak":channel_rel.tolist(),
        "passed":bool(np.max(channel_rel) < 1e-10 and unsigned_b_rel > 1.99),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anilos-root", type=Path, help="checkout of pinned AniLoS source")
    parser.add_argument("--aniclass-root", type=Path, help="checkout with local compiled class binary")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    from bass.transport import general_lie_stokes
    native_root = Path(general_lie_stokes.__file__).resolve().parent
    result = {"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy_version,"thomson":thomson_fixture()}
    result["bass_base"] = subprocess.check_output(
        ["git", "-C", str(native_root), "rev-parse", "HEAD"], text=True,
    ).strip()
    if args.anilos_root:
        result["anilos_vs_bass_IX"] = anilos_ix_fixture(args.anilos_root)
    if args.aniclass_root:
        result["aniclass"] = aniclass_fixture(args.aniclass_root)
    result["cross_code_matched_bianchi_alm"] = "not_run: BASS matching regular tensor initial data, source history and frame orientation are required"
    result["pass_scoped"] = all(d["passed"] for d in result.values() if isinstance(d,dict) and "passed" in d)
    encoded = json.dumps(result, indent=2, allow_nan=False)+"\n"
    if args.output:
        args.output.write_text(encoded)
    else:
        print(encoded, end="")
    return 0 if result["pass_scoped"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
