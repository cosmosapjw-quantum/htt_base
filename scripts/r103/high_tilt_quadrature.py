"""Select the smallest tested GL sky for a signed, bolometric Thomson four-force."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import time

import numpy as np
import scipy
from scipy.special import sph_harm_y

from bass.collision import coherency, electron_frame, moving_thomson
from bass.transport import general_bianchi_transfer, general_lie_stokes, moving_collision_stage
from common import relativistic_kinematics


# Independent real sky specified by its nonnegative-m harmonic coefficients.
# Input normalization is S/(4 I_0) and an additional isotropic I_bg=1/4.
MODES = [
    ("T",1,0,.013,0.), ("T",2,2,.023,-.011), ("T",4,1,-.019,.006),
    ("T",5,3,.007,.005), ("E",2,1,.014,.004), ("B",3,2,-.008,.005),
    ("V",5,4,.003,-.002),
]


def coefficients(op):
    y = np.zeros(op.dim, dtype=complex)
    for channel, ell, m, re, im in MODES:
        amp = complex(re, im)
        y[op.idx[channel][ell,m]] = amp
        y[op.idx[channel][ell,-m]] = (-1)**m * amp.conjugate()
    return y


def independent_moments(beta):
    # Independent normal sky, scalar SciPy harmonics, and an orthonormal
    # (-,+,+,+) normal tetrad. Products have degree <=7 on this fixture.
    x, w_theta = np.polynomial.legendre.leggauss(20)
    th, ph = np.meshgrid(np.arccos(x), np.arange(40)*np.pi/20, indexing="ij")
    w = np.broadcast_to(w_theta[:,None]*(np.pi/20),th.shape)
    sky = np.stack((np.sin(th)*np.cos(ph), np.sin(th)*np.sin(ph), np.cos(th)), axis=-1)
    p = np.concatenate((np.ones(th.shape+(1,)), -sky),axis=-1)
    intensity = np.full(th.shape, .25)
    for channel, ell, m, re, im in MODES:
        if channel=="T":
            intensity += (1 if m==0 else 2) * (complex(re,im)*sph_harm_y(ell,m,th,ph)).real
    tensor = np.einsum("ij,ija,ijb->ab",w*intensity,p,p)
    # F = -(I+u u_flat)·(-T·u_flat)/gamma in the conserved anchor clock.
    gamma = 1/np.sqrt(1-beta@beta)
    u = gamma*np.r_[1.,beta]
    u_flat = u.copy()
    u_flat[0] *= -1
    flux = -tensor @ u_flat
    f_ref = -(flux+u*(u_flat@flux))/gamma
    return f_ref, u_flat


def measured_force(op, rate):
    # Only the scalar monopole/dipole contribute to the integrated four-force.
    # Treat the latter as a real Cartesian vector using p=-n.
    a00 = rate[op.idx["T"][0,0]]
    a10 = rate[op.idx["T"][1,0]]
    a11 = rate[op.idx["T"][1,1]]
    q = np.array([-np.sqrt(3/(2*np.pi))*a11.real, np.sqrt(3/(2*np.pi))*a11.imag,
                   np.sqrt(3/(4*np.pi))*a10.real])
    return np.r_[np.sqrt(4*np.pi)*a00.real,-(4*np.pi/3)*q]


def run(beta, orders, target):
    if beta.shape!=(3,) or not np.all(np.isfinite(beta)) or not 0<beta@beta<1:
        raise ValueError("velocity must be finite with 0 < |beta| < 1")
    if orders!=sorted(set(orders)) or not orders or min(orders)<9:
        raise ValueError("use strictly increasing GL ring counts >=9 for ell_max=5")
    if not np.isfinite(target) or target<=0.:
        raise ValueError("relative target must be finite and positive")
    f_ref, u_flat = independent_moments(beta)
    scale = float(np.linalg.norm(f_ref))
    if not scale>0:
        raise ValueError("relative four-force target undefined at zero reference")
    rows = []
    t0 = time.perf_counter()
    for order in orders:
        begin = time.perf_counter()
        op = general_lie_stokes.GeneralLieStokesOperator(5, n_gl_theta=order)
        constructed = time.perf_counter()
        y = coefficients(op)
        stage = moving_collision_stage.MovingCollisionStage(op,beta)
        candidate = measured_force(op,stage.apply(y) + stage.emission)
        end = time.perf_counter()
        err = float(np.linalg.norm(candidate-f_ref)/scale)
        rows.append({"n_theta":order, "n_rays":2*order**2, "four_force":candidate.tolist(),
                     "relative_four_force_error":err, "abs_u_dot_F_over_force":float(abs(u_flat@candidate)/scale),
                     "lie_setup_seconds":constructed-begin,"moving_stage_and_force_seconds":end-constructed,
                     "target_met":bool(np.isfinite(err) and err<=target)})
    chosen = next((r["n_theta"] for r in rows if r["target_met"]), None)
    files = [Path(m.__file__) for m in (coherency, electron_frame, moving_thomson,
             general_bianchi_transfer, general_lie_stokes, moving_collision_stage, relativistic_kinematics)]
    files.append(Path(__file__))
    root = Path(__file__).resolve().parents[2]
    hashes = {p.resolve().relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    return {"status":"pass_scoped" if chosen is not None else "target_unmet",
            "scope":"one fixed harmonic sky; threshold applies to its integrated four-force",
            "basis":"normal outward n; propagation -n; conserved_anchor; (-,+,+,+)",
            "beta":beta.tolist(),"speed":float(np.linalg.norm(beta)),"ell_max":5,
            "I_bg":.25,"nonnegative_m_modes_channel_ell_m_re_im":MODES,
            "reference_four_force":f_ref.tolist(),"target_relative":target,
            "smallest_tested_n_theta_meeting_target":chosen,"rows":rows,
            "wall_seconds":time.perf_counter()-t0,
            "python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__,
            "OPENBLAS_NUM_THREADS":os.getenv("OPENBLAS_NUM_THREADS"),"source_sha256":hashes}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--beta",nargs=3,type=float,default=[.9,.1,0.])
    parser.add_argument("--orders",nargs="+",type=int,default=[14,16,24,32])
    parser.add_argument("--target",type=float,default=1e-8)
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    result=run(np.asarray(a.beta),a.orders,a.target)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(result["status"],result["smallest_tested_n_theta_meeting_target"])
    return 0 if result["status"]=="pass_scoped" else 1


if __name__=="__main__":
    raise SystemExit(main())
