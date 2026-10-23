"""R24: finite-matrix K03 power audit and exact-method checks; no ODE/solver.

Run: OPENBLAS_NUM_THREADS=1 python analysis.py
Input is a small exact extraction from the pinned K03 RESULT.json.
"""
from pathlib import Path
import hashlib
import json
import platform
import sys
import numpy as np
import scipy
from scipy.stats import norm
from scipy.special import roots_legendre
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent

def main():
    inp = json.loads((ROOT / 'K03_INPUT.json').read_text())
    C = np.asarray(inp['history_covariance_uasyr2'], float)
    if C.shape != (3, 3) or not np.allclose(C, C.T, rtol=0, atol=1e-12):
        raise ValueError('Expected symmetric 3x3 history covariance')
    ev = np.linalg.eigvalsh(C)
    if ev[0] <= 0:
        raise ValueError('Covariance must be positive definite')
    I = np.linalg.solve(C, np.eye(3))
    F = np.asarray(inp['joint_information'], float)
    schur = F[:3, :3] - F[:3, 3:] @ np.linalg.solve(F[3:, 3:], F[3:, :3])
    schur_residual = float(np.max(np.abs(I - schur)))
    assert schur_residual < 1e-10
    R, K, alpha = inp['compensation_R'], inp['K_H_uasyr'], 0.05
    rows = []
    for eps in (0.01, 0.1, 0.3):
        amax = K * eps / R
        dmax = amax / np.sqrt(ev[0])
        rows.append(dict(epsilon=eps,amplitude_max_uasyr=amax,
                         mahalanobis_max=float(dmax),noncentrality_max=float(dmax*dmax),
                         gaussian_level_005_power_upper=float(norm.cdf(norm.ppf(alpha)+dmax))))

    # Degree-4 angular identity, independent Gauss-Legendre x periodic quadrature.
    z, w = roots_legendre(12)
    phi = np.arange(32) * (2*np.pi/32)
    n = np.array([[np.sqrt(1-zz*zz)*np.cos(p),np.sqrt(1-zz*zz)*np.sin(p),zz]
                  for zz in z for p in phi])
    weights = np.repeat(w/64, 32)
    S = np.array([[.3,.07,-.02],[.07,-.1,.04],[-.02,.04,-.2]])
    h2 = np.einsum('ni,ij,nj->n',n,S,n)
    angular_residual = float(abs(weights @ h2**2 - 2*np.sum(S*S)/15))
    assert angular_residual < 1e-14

    # PSD kinetic stress guarantees positive momentum matrix; deterministic tests.
    rng = np.random.default_rng(20261023)
    kinetic_worst = 0.
    for _ in range(100):
        L = rng.normal(size=(3,3)); P = L@L.T; rho=0.4+rng.random()
        g = rng.normal(size=3); a = -np.linalg.solve(rho*np.eye(3)+P,g)
        violation = np.linalg.norm(a)-np.linalg.norm(g)/rho
        kinetic_worst = max(kinetic_worst,float(violation))
    assert kinetic_worst <= 1e-12

    # Rotation invariants and orbit-distance lower bound: no chart inversion.
    q = S
    angle=.43; rot=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])
    qrot=rot@q@rot.T
    rotation_residual=float(abs(np.linalg.norm(q)-np.linalg.norm(qrot)))
    assert rotation_residual < 1e-14
    # Example: norm difference bounds distance for every rotation; one feasible
    # alignment gives an upper bound. This does not certify a generic optimizer.
    q2=1.2*qrot
    orbit_lower=abs(np.linalg.norm(q2)-np.linalg.norm(q))
    orbit_upper=np.linalg.norm(q-rot.T@q2@rot)
    assert abs(orbit_lower-orbit_upper)<1e-14

    # Production G_F is ratio of floored bin means, NOT mean of draw ratios.
    fr=np.array([.1,.9]); fc=np.array([.2,.8]); floor=.05
    gf_means=max(fc.mean(),floor)/max(fr.mean(),floor)
    mean_ratios=np.mean(np.maximum(fc,floor)/np.maximum(fr,floor))
    assert gf_means == 1 and abs(mean_ratios-13/9)<1e-14

    # Full tuple: ellipsoidal gauge and a joint state/anchor perturbation bound.
    W=np.diag([1.,2.,4.]); v=np.array([.2,-.4,.1]); dv=np.array([.02,.01,-.03])
    gauge=lambda x: np.sqrt(x@W@x)
    transformed_W=rot@W@rot.T
    gauge_rotation_error=abs(np.sqrt((rot@v)@transformed_W@(rot@v))-gauge(v))
    eta=.1; anchor_scale=1.05; inner_radius=1/np.sqrt(np.linalg.eigvalsh(W)[-1])
    gauge_lo=max(0.,gauge(v)-np.linalg.norm(dv)/inner_radius)/(1+eta)
    gauge_hi=(gauge(v)+np.linalg.norm(dv)/inner_radius)/(1-eta)
    actual_gauge=gauge(v+dv)/anchor_scale
    assert gauge_lo <= actual_gauge <= gauge_hi and gauge_rotation_error < 1e-14

    # Ball support Hausdorff equality, with a maximizing direction constructed.
    center1=np.array([.2,.4,-.1]); center2=np.array([-.1,.2,.3]); rad1=.8; rad2=.5
    ud=(center1-center2)/np.linalg.norm(center1-center2)
    support_difference=abs(ud@(center1-center2)+rad1-rad2)
    hausdorff=np.linalg.norm(center1-center2)+abs(rad1-rad2)
    assert abs(support_difference-hausdorff)<1e-14

    # Fixed 3x7 contraction fibre: support witness, no uncertain-q substitution.
    L=rng.normal(size=(3,7)); raw=rng.normal(size=7); raw/=np.linalg.norm(raw)
    v3=L@raw; o0=np.linalg.lstsq(L,v3,rcond=None)[0]
    projector=np.eye(7)-np.linalg.pinv(L)@L; direction=rng.normal(size=7)
    null_direction=projector@direction; radius=np.sqrt(1-o0@o0)
    witness=o0+radius*null_direction/np.linalg.norm(null_direction)
    support=direction@o0+radius*np.linalg.norm(null_direction)
    fibre_error=max(abs(direction@witness-support),abs(np.linalg.norm(witness)-1),
                    float(np.max(np.abs(L@witness-v3))))
    assert fibre_error < 1e-12

    # Depth path: keep initial block AND differences, and all cross covariance.
    T=np.array([[1.,0,0],[-1,1,0],[0,-1,1]])
    CY=np.array([[2.,.3,.2],[.3,1.,.1],[.2,.1,1.4]])
    residual=np.array([.3,-.4,.2]); J=np.array([[1.,0],[1.,1.],[1.,2.]])
    CZ=T@CY@T.T; z=T@residual
    depth_likelihood_error=abs(residual@np.linalg.solve(CY,residual)-z@np.linalg.solve(CZ,z))
    depth_fisher_error=float(np.max(np.abs(J.T@np.linalg.solve(CY,J)-(T@J).T@np.linalg.solve(CZ,T@J))))
    assert depth_likelihood_error<1e-14 and depth_fisher_error<1e-13
    assert np.allclose(T[1:]@np.ones(3),0) and np.linalg.matrix_rank(T)==3

    out=dict(owner='HTT method research',scope='fixed K03 Gaussian working experiment; illustrative parameter domains',
             source_commit=inp['source_commit'],original_acceptance_promoted=False,
             assumptions=['same frozen covariance','Gaussian mean experiment','local parameters profiled',
                          'R*norm(b)<=epsilon is an illustrative domain, not a remainder certificate'],
             input_sha256=hashlib.sha256((ROOT/'K03_INPUT.json').read_bytes()).hexdigest(),
             covariance_eigenvalues=ev.tolist(),information_eigenvalues=np.linalg.eigvalsh(I).tolist(),
             rows=rows,checks=dict(schur_absolute_residual=schur_residual,
             angular_norm_absolute_residual=angular_residual,kinetic_bound_max_violation=kinetic_worst,
             rotation_norm_residual=rotation_residual,orbit_scaled_example_lower=float(orbit_lower),
             orbit_scaled_example_upper=float(orbit_upper),G_F_ratio_of_bin_means=gf_means,
             mean_of_draw_ratios=mean_ratios,gauge_rotation_error=float(gauge_rotation_error),
             gauge_perturbation_interval=[float(gauge_lo),float(gauge_hi)],
             gauge_perturbed_value=float(actual_gauge),support_hausdorff_error=float(abs(support_difference-hausdorff)),
             fixed_fibre_witness_error=float(fibre_error),depth_likelihood_error=float(depth_likelihood_error),
             depth_fisher_error=depth_fisher_error),
             environment=dict(python=platform.python_version(),executable=sys.executable,
                              numpy=np.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__))
    (ROOT/'RESULT.json').write_text(json.dumps(out,indent=2)+'\n')
    eps=np.geomspace(.001,.3,200); d=K*eps/R/np.sqrt(ev[0])
    fig,ax=plt.subplots(1,2,figsize=(10,4.2),constrained_layout=True)
    ax[0].loglog(eps,d,color='#17628c',lw=2)
    ax[0].axhline(1,color='#b63b35',ls='--',label='Unit Mahalanobis separation')
    ax[0].scatter([.1],[rows[1]['mahalanobis_max']],color='#17628c')
    ax[0].set(xlabel=r'Illustrative domain $R\|b\|\leq\epsilon$',ylabel='Largest allowed Mahalanobis signal',
              title='Full rank does not ensure useful power')
    ax[0].legend(fontsize=8)
    ax[1].plot(eps,norm.cdf(norm.ppf(alpha)+d),color='#17628c',lw=2)
    ax[1].axhline(alpha,color='#777777',ls=':',label='Test size 0.05')
    ax[1].set(xlabel=r'$\epsilon$',ylabel='Oracle power upper bound',title='Fixed Gaussian working experiment')
    ax[1].ticklabel_format(axis='y',style='plain',useOffset=False)
    ax[1].legend(fontsize=8)
    for a in ax: a.grid(alpha=.18)
    fig.suptitle('K03 retained-summary audit — no new catalogue pass',fontsize=13)
    fig.savefig(ROOT/'K03_POWER.svg',metadata={'Date':None})
    fig.savefig(ROOT/'K03_POWER.png',dpi=160)
    print(json.dumps({'checks':out['checks'],'power':rows},indent=2))

if __name__ == '__main__':
    main()
