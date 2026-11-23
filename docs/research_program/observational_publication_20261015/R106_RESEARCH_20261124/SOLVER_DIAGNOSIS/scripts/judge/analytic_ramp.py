"""Analytic special solution for the photon cell (FLRW zero geometry, tiny beta):
a' = R(u)(beta(u) - a), a(0)=0, R = R0 exp(-k u), beta = vf*u  =>
a(u) = vf*[u - exp(-tau(u)) * exp(R0/k)/k * (E1(w(u)) - E1(R0/k))], tau(u)=(R0/k)(1-e^{-ku}), w(u)=(R0/k)e^{-ku}.
Compares R105 frozen-rate vs stage-time-rate variants of _advance_moving_photon_cell."""
import importlib.util, sys, math, json
import numpy as np
from scipy.special import exp1
import bass.transport.coupled_einstein_boltzmann as repo
from bass.recombination.opacity_history import OpacityHistory
from bass.transport.general_lie_stokes import GeneralLieStokesOperator, LieGeometry
spec = importlib.util.spec_from_file_location("htt_r106_judge_ramp", sys.argv[1])
mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
op = GeneralLieStokesOperator(2, n_gl_theta=8)
zero = LieGeometry(np.zeros((3, 3)), np.zeros(3), np.zeros((3, 3)))
out = {}
for R0, k in ((60.0, 5.0), (30.0, 9.6)):
    vf = 1e-8
    nodes = np.linspace(0, 1, 4001); opac = OpacityHistory(nodes, R0*np.exp(-k*nodes))
    w = lambda u: (R0/k)*math.exp(-k*u); tau = lambda u: (R0/k)*(1-math.exp(-k*u))
    exact = vf*(1 - math.exp(-tau(1.0))*math.exp(R0/k)/k*(exp1(w(1.0)) - exp1(R0/k)))
    slip = exact - vf
    for mode in ("frozen", "stage"):
        mod.RATE_MODE = mode
        for cap in (1.0, 0.5, 0.25, 0.125):
            edges, ds = repo._optical_substeps(opac, 0., 1., 2, cap)
            st = mod._advance_moving_photon_cell(op, np.zeros(op.dim, complex), 1., zero, np.zeros(op.dim, complex), ds,
                                                 lambda u: np.array([0., 0., vf*u]), sub_edges=edges,
                                                 rate_at=lambda u: float(opac.rate(min(u, 1.0))))
            meas = -st[op.idx["T"][1, 0]].real/np.sqrt(4*np.pi/3)
            out[f"R0={R0},k={k},{mode},cap={cap}"] = (meas-exact)/slip
            print(f"R0={R0} k={k} {mode:6s} cap={cap:<6} substeps={len(ds):4d} (meas-exact)/slip={(meas-exact)/slip:+.4e}  slip/vf={slip/vf:+.4e}")
    # constant-rate regression: stage == frozen to roundoff
    copac = OpacityHistory([0, 1], [6., 6.])
    edges, ds = repo._optical_substeps(copac, 0., 1., 2, 1.0); res = []
    for mode in ("frozen", "stage"):
        mod.RATE_MODE = mode
        res.append(mod._advance_moving_photon_cell(op, np.zeros(op.dim, complex), 1., zero, np.zeros(op.dim, complex), ds,
                   lambda u: np.array([0., 0., 1e-6*(-np.expm1(-5*u))]), sub_edges=edges, rate_at=lambda u: float(copac.rate(u))))
    print("constant-rate stage vs frozen max|diff|/max|state| =", float(np.max(np.abs(res[0]-res[1]))/np.max(np.abs(res[0]))))
json.dump(out, open(sys.argv[2], "w"), indent=1)
