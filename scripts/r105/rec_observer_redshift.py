"""Measure conditional REI optical-depth anisotropy at fixed normal-observer redshift."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import numpy as np

from bass.recombination.rei_material_history import CASE_Q,FIVE_CASE_PATH,FIVE_CASE_SHA,REI_COMMIT,ReiMaterialHistory


def compute(material):
    z = np.array([.1,.3,.6,1.,2.,3.])
    mu, w = np.polynomial.legendre.leggauss(48)
    leg2 = (3*mu**2-1)/2
    cases = {}
    for case,shear in CASE_Q.items():
        mat = ReiMaterialHistory(material,case)
        if mat.sha256 != FIVE_CASE_SHA:
            raise ValueError("five-case donor required")
        rays=mat.observer_rays()
        v=rays.evaluate(z[:,None],mu[None,:])
        # Subtract the angular monopole before summing the signed quadrupole.
        mono = v.optical_depth @ w / 2
        tau2=(v.optical_depth-mono[:,None]) @ (w*leg2) * (5/2)
        gmono=v.visibility_per_redshift @ w / 2
        vis2=(v.visibility_per_redshift-gmono[:,None]) @ (w*leg2) * (5/2)
        n_iso=rays.N_o-np.log1p(z)
        predicted=2*mat.rate(n_iso)*(np.interp(n_iso,mat.N,mat.b)-rays.b_o)
        quadrature={}
        for order in (12,24):
            axis,weight=np.polynomial.legendre.leggauss(order)
            val=rays.evaluate(z[:,None],axis).optical_depth
            p2=(3*axis**2-1)/2
            estimate=(val-(val@weight/2)[:,None]) @ (weight*p2)*(5/2)
            quadrature[str(order)]=float(np.max(np.abs(estimate-tau2)))
        inverse_err=float(np.max(abs(rays.log_frequency_ratio(v.emission_N,mu)-np.log1p(z[:,None]))))
        iz,im=2,15
        dz=1e-6
        diff=(rays.evaluate(z[iz]+dz,mu[im]).optical_depth-rays.evaluate(z[iz]-dz,mu[im]).optical_depth)/(2*dz)
        jac_err=float(abs(diff/v.depth_per_redshift[iz,im]-1))
        # Check direction-independent opacity on a fixed material slice.
        t=mat.N[len(mat.N)//2]
        angular_z=np.expm1(rays.log_frequency_ratio(t,mu))
        slice_tau=float(np.ptp(rays.evaluate(angular_z,mu).optical_depth))
        if inverse_err>1e-14 or jac_err>1e-6 or slice_tau>2e-14:
            raise ArithmeticError(f"ray tests failed for {case}")
        cases[case]={"q_ref":shear,"b_observer":float(rays.b_o),"tau_monopole":mono.tolist(),
                     "tau_legendre2":tau2.tolist(),"visibility_density_legendre2":vis2.tolist(),
                     "first_order_tau2":predicted.tolist(),"first_order_error_max_abs":float(np.max(abs(tau2-predicted))),
                     "angular_quadrature_vs_48_max_abs":quadrature,"max_log1pz_inverse_error":inverse_err,
                     "tau_angular_range_fixed_material_slice":slice_tau,"dtaudz_centered_fd_relative_error":jac_err,
                     "parallel_perp_optical_depth":rays.evaluate(z[:,None],[1.,0.]).optical_depth.tolist()}
    if max(abs(np.asarray(cases["ZERO"]["tau_legendre2"])))>1e-14:
        raise ArithmeticError("isotropic angular quadrupole")
    odd={}
    for tag,plus,minus in [("0.005","SHEAR_HALF_PLUS","SHEAR_HALF_MINUS"),("0.01","SHEAR_PLUS","SHEAR_MINUS")]:
        odd[tag]=((np.array(cases[plus]["tau_legendre2"])-np.array(cases[minus]["tau_legendre2"]))/2).tolist()
    return {"schema":"htt.r105.rei_observer_rays/1","donor_repo":"cosmosapjw-quantum/rei_bianchi",
            "donor_commit":REI_COMMIT,"donor_path":FIVE_CASE_PATH,"sha256":FIVE_CASE_SHA,
            "observer_mean_redshift":4,"mean_redshift_support":[4,20],"ray_redshift":z.tolist(),
            "angular_basis":"tau=sum_L tau_L P_L(mu_o), mu_o in local normal observer tetrad",
            "ray_redshift_zero_at_observer":True,"cases":cases,"odd_signed_tau2":odd,
            "assumptions":"Non-tilted prescribed axisymmetric Bianchi I; homogeneous hydrogen/helium; 1001 linear-in-N metric and material samples per case. Finite observer at mean z=4.",
            "late_foreground_from_z4_to_today":None,"physical_Pi":None}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    data=parser.add_mutually_exclusive_group(required=True)
    data.add_argument("--donor-repo",type=Path)
    data.add_argument("--material",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory() as temp:
        p=args.material
        if p is None:
            p=Path(temp)/"five_cases.csv.gz"
            with p.open("wb") as f:
                subprocess.run(["git","-C",str(args.donor_repo),"show",f"{REI_COMMIT}:{FIVE_CASE_PATH}"],stdout=f,check=True)
        result=compute(p)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")

if __name__=="__main__":
    main()
