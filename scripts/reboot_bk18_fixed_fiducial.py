#!/usr/bin/env python3
"""BK18 BB-only, fixed-fiducial HL descriptor from the native released tables.

This evaluates one fixed reference shape. It does not fit r, foregrounds or
cosmology, calibrate a tail probability, or reproduce the full BK likelihood.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

import numpy as np
from scipy.linalg import cho_factor, cho_solve

RELEASE_REL = Path("workdir/cobaya_packages/data/bicep_keck_2018/BK18_cosmomc")
DATA_REL = Path("data/BK18lf_dust")
NMAP = 11
NBIN = 9
NPAIR = 66
NATIVE_TRANSFORM = "cobaya.likelihoods.base_classes.cmblikes.CMBlikes.transform"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def parse_dataset(path: Path) -> dict[str, str]:
    settings = {}
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if key in settings:
            raise ValueError("duplicate dataset key: " + key)
        settings[key] = value
    return settings


def release_order(settings: dict[str, str]) -> tuple[list[str], list[str], list[tuple[int, int]]]:
    required = ("cl_fiducial_order", "cl_hat_order", "cl_noise_order", "covmat_cl",
                "bin_window_in_order")
    orders = [settings[name].split() for name in required]
    if any(order != orders[0] or len(order) != NPAIR for order in orders):
        raise ValueError("66-pair fiducial/hat/noise/covariance/window order mismatch")
    names = settings["map_names"].split()
    if len(names) != NMAP or len(set(names)) != NMAP or settings["map_fields"].split() != ["B"]*NMAP:
        raise ValueError("BK18 BB-only 11-map contract mismatch")
    pairs = []
    for name in orders[0]:
        maps = name.split("x")
        if len(maps) != 2 or any(part not in names for part in maps):
            raise ValueError("unrecognized configured B-pair: " + name)
        pairs.append(tuple(names.index(part) for part in maps))
    if len({tuple(sorted(pair)) for pair in pairs}) != NPAIR:
        raise ValueError("configured pair names do not cover 11 symmetric maps")
    return names, orders[0], pairs


def pair_matrix(values: np.ndarray, pairs: list[tuple[int, int]]) -> np.ndarray:
    values = np.asarray(values)
    if np.iscomplexobj(values) or values.shape != (NPAIR,) or not np.isfinite(values).all():
        raise ValueError("finite real 66-pair bandpowers required")
    matrix = np.empty((NMAP, NMAP), float)
    for value, (i, j) in zip(values, pairs):
        matrix[i, j] = matrix[j, i] = value
    return matrix


def pair_vector(matrix: np.ndarray, pairs: list[tuple[int, int]]) -> np.ndarray:
    matrix = np.asarray(matrix)
    if (matrix.shape != (NMAP,NMAP) or np.iscomplexobj(matrix) or
            not np.isfinite(matrix).all() or not np.allclose(matrix,matrix.T,rtol=1e-12,atol=0)):
        raise ValueError("finite symmetric 11-map matrix required")
    return np.array([matrix[i,j] for i,j in pairs])  # no sqrt(2) on cross terms


def positive_symmetric(matrix: np.ndarray, name: str) -> np.ndarray:
    value = np.asarray(matrix)
    if value.ndim != 2 or value.shape[0] != value.shape[1] or np.iscomplexobj(value) or not np.isfinite(value).all():
        raise ValueError("finite real square " + name + " required")
    asym = np.linalg.norm(value-value.T,ord="fro") / np.linalg.norm(value,ord="fro")
    if not np.isfinite(asym) or asym > 1e-10:
        raise ValueError(name + " antisymmetry exceeds 1e-10")
    sym = (value+value.T)/2
    if np.linalg.eigvalsh(sym)[0] <= 0:
        raise np.linalg.LinAlgError(name + " is not SPD")
    return sym


def hl_g(eigenvalues: np.ndarray) -> np.ndarray:
    lam = np.asarray(eigenvalues)
    if np.iscomplexobj(lam) or not np.isfinite(lam).all() or np.any(lam <= 0):
        raise ValueError("positive finite real HL eigenvalues required")
    delta = lam-1
    penalty = delta-np.log1p(delta)
    near = np.abs(delta) < 1e-3
    d = delta[near]
    # Alternating log1p expansion avoids cancellation close to lambda=1.
    penalty[near] = d*d*(.5-d/3+d*d/4-d**3/5+d**4/6-d**5/7+d**6/8)
    return np.sign(delta)*np.sqrt(2*penalty)


def hl_matrix(fiducial: np.ndarray, observed: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    F = positive_symmetric(fiducial,"fiducial plus noise")
    H = positive_symmetric(observed,"observed plus noise")
    ef,V = np.linalg.eigh(F)
    Fhalf = (V*np.sqrt(ef))@V.T
    Finvhalf = (V/np.sqrt(ef))@V.T
    whitened = positive_symmetric(Finvhalf@H@Finvhalf,"whitened observed")
    lam,U = np.linalg.eigh(whitened)
    X = Fhalf@((U*hl_g(lam))@U.T)@Fhalf
    return (X+X.T)/2,Fhalf,lam


def native_transform_parity(F: np.ndarray, H: np.ndarray, Fhalf: np.ndarray,
                            candidate: np.ndarray) -> dict:
    from cobaya.likelihoods.base_classes.cmblikes import CMBlikes
    native = F.copy()
    CMBlikes.transform(native,H,Fhalf)
    if not np.isfinite(native).all():
        raise FloatingPointError("Cobaya native HL transform is nonfinite")
    difference = float(np.linalg.norm(candidate-native,ord="fro"))
    unit = float(max(np.linalg.norm(F,ord="fro"),np.linalg.norm(native,ord="fro")))
    if difference > 1e-10*unit:
        raise AssertionError("native Cobaya HL matrix parity failed")
    return {"native_kernel":NATIVE_TRANSFORM,"frobenius_difference_uK2":difference,
            "relative_to_native_fiducial_unit":difference/unit,
            "tolerance":"1e-10 times per-bin fiducial/native Frobenius uK^2 scale"}


def quadratic(vector: np.ndarray, covariance: np.ndarray) -> float:
    vector = np.asarray(vector)
    cov = positive_symmetric(covariance,"joint 594 covariance")
    if vector.shape != (cov.shape[0],) or np.iscomplexobj(vector) or not np.isfinite(vector).all():
        raise ValueError("aligned finite real joint vector required")
    chol = cho_factor(cov,lower=True,check_finite=True)
    return float(vector @ cho_solve(chol,vector,check_finite=True))


def load_release(root: Path) -> dict:
    release = root/RELEASE_REL
    base = release/DATA_REL
    dataset = base/"BK18lf_dust.dataset"
    readme = release/"BK18_README.txt"
    settings = parse_dataset(dataset)
    if (settings.get("like_approx") != "HL" or settings.get("binned") != "T" or
            settings.get("nbins") != "9" or settings.get("cl_lmin") != "2" or
            settings.get("cl_lmax") != "600" or
            settings.get("cl_hat_includes_noise") != "F" or
            settings.get("cl_fiducial_includes_noise") != "F"):
        raise ValueError("BK18 BB-only fixed-fiducial HL settings/flags mismatch")
    if "B-modes only data" not in readme.read_text():
        raise ValueError("BK18 release README BB-only identity missing")
    names,order,pairs = release_order(settings)
    files = [dataset,readme]
    arrays = {}
    for key in ("cl_fiducial","cl_hat","cl_noise"):
        path=base/settings[key+"_file"]
        table=np.loadtxt(path)
        if (table.shape != (NBIN,NPAIR+1) or not np.isfinite(table).all() or
                not np.array_equal(table[:,0],np.arange(1,NBIN+1))):
            raise ValueError(key+" 9x67 bin table mismatch")
        arrays[key]=table[:,1:]
        files.append(path)
    covpath=base/settings["covmat_fiducial"]
    covariance=np.loadtxt(covpath)
    if covariance.shape != (NBIN*NPAIR,NBIN*NPAIR):
        raise ValueError("594x594 released covariance required")
    covariance_antisymmetry=float(np.linalg.norm(covariance-covariance.T,ord="fro")/
                                  np.linalg.norm(covariance,ord="fro"))
    covariance=positive_symmetric(covariance,"joint 594 covariance")
    files.append(covpath)
    tails=[];window_files=[]
    for b in range(1,NBIN+1):
        path=base/(settings["bin_window_files"].replace("%u",str(b)))
        window=np.loadtxt(path)
        if (window.shape != (999,NPAIR+1) or not np.isfinite(window).all() or
                not np.array_equal(window[:,0],np.arange(1,1000))):
            raise ValueError("released window ell 1..999 / 66-pair shape mismatch")
        weight=window[:,1:]
        outside=(window[:,0]<2)|(window[:,0]>600)
        tails.append({"bin":b,"nonzero_outside_ell_2_600":int(np.count_nonzero(weight[outside])),
                      "outside_abs_weight_fraction":float(np.abs(weight[outside]).sum()/np.abs(weight).sum()),
                      "outside_frobenius_fraction":float(np.linalg.norm(weight[outside])/np.linalg.norm(weight))})
        window_files.append(path)
    files += window_files
    return {"settings":settings,"map_names":names,"pair_order":order,"pairs":pairs,
            "fiducial":arrays["cl_fiducial"],"hat":arrays["cl_hat"],
            "noise":arrays["cl_noise"],"covariance":covariance,
            "covariance_antisymmetry":covariance_antisymmetry,
            "window_tails":tails,"files":files}


def evaluate(release: dict) -> tuple[dict,dict]:
    fid,hat,noise=release["fiducial"],release["hat"],release["noise"]
    pairs=release["pairs"]
    x=np.empty((NBIN,NPAIR));linear=np.empty_like(x)
    matrices=np.empty((NBIN,NMAP,NMAP));per_bin=[]
    for b in range(NBIN):
        F=pair_matrix(fid[b]+noise[b],pairs)
        H=pair_matrix(hat[b]+noise[b],pairs)
        X,Fhalf,lam=hl_matrix(F,H)
        parity=native_transform_parity(F,H,Fhalf,X)
        x[b]=pair_vector(X,pairs)
        linear[b]=hat[b]-fid[b]
        matrices[b]=X
        per_bin.append({"bin":b+1,"min_F_eigenvalue_uK2":float(np.linalg.eigvalsh(F)[0]),
                        "min_H_eigenvalue_uK2":float(np.linalg.eigvalsh(H)[0]),
                        "min_whitened_eigenvalue":float(lam[0]),
                        "hl_frobenius_norm_uK2":float(np.linalg.norm(X,ord="fro")),
                        "native_parity":parity})
    cov=release["covariance"]
    qhl=quadratic(x.reshape(-1),cov)
    qlinear=quadratic(linear.reshape(-1),cov)
    # Independent native-vector parity, beyond each 11x11 matrix comparison.
    from cobaya.likelihoods.base_classes.cmblikes import CMBlikes
    native_x=np.empty_like(x)
    for b in range(NBIN):
        F=pair_matrix(fid[b]+noise[b],pairs)
        H=pair_matrix(hat[b]+noise[b],pairs)
        ef,V=np.linalg.eigh(F)
        Fhalf=(V*np.sqrt(ef))@V.T
        native=F.copy();CMBlikes.transform(native,H,Fhalf)
        native_x[b]=pair_vector((native+native.T)/2,pairs)
    qnative=quadratic(native_x.reshape(-1),cov)
    delta_q=abs(qhl-qnative)
    whitened_delta=np.sqrt(quadratic((x-native_x).reshape(-1),cov))
    if delta_q>1e-8*(1+abs(qhl)) or whitened_delta>1e-6*(1+np.sqrt(qhl)):
        raise AssertionError("native Cobaya joint-vector HL parity failed")
    result={"owner":"HTT","scope":"BK18_BB_ONLY_FIXED_FIDUCIAL_HL_DESCRIPTOR",
            "release":"BICEP/Keck June 2021 BK18lf_dust BB-only",
            "release_product_url":"https://lambda.gsfc.nasa.gov/product/bicepkeck/bicep2_prod_table.html",
            "dataset":str(DATA_REL/"BK18lf_dust.dataset"),
            "map_names":release["map_names"],"pair_order":release["pair_order"],
            "units":"released binned spectra in uK^2 CMB; native Cobaya theory input is D_ell in uK^2 and is windowed before HL",
            "vector_order":"nine bins outer, configured 66 pair names inner; no sqrt(2) cross weights",
            "noise_convention":"hat and fiducial exclude noise; one addition to each before HL",
            "fiducial_convention":"released fiducial already binned; no window reconvolution",
            "window_audit":{"raw_ell_support":[1,999],"native_theory_ell_support":[2,600],
                            "tails_retained_not_zeroed":True,"bins":release["window_tails"]},
            "joint_covariance":{"shape":[594,594],"antisymmetry_relative_frobenius":release["covariance_antisymmetry"],
                                "antisymmetry_relative_frobenius_max":1e-10,
                                "symmetrized_before_cholesky":True,"single_joint_11_channel_covariance":True},
            "Q_HL":qhl,"fixed_fiducial_unnormalized_logL":-qhl/2,
            "Q_linear_residual_separate_gaussian_descriptor":qlinear,
            "native_vector_parity":{"native_kernel":NATIVE_TRANSFORM,"Q_native":qnative,
                                    "absolute_Q_difference":delta_q,
                                    "whitened_vector_difference":whitened_delta},
            "per_bin":per_bin,"calibrated_PTE":None,"evidence":None,"r_fit":None,
            "claim_tier":"CONDITIONAL_DIAGNOSTIC","scientific_admission":"NOT_EVALUATED",
            "caveats":["One released fixed fiducial, not the foreground/cosmology likelihood",
                       "Q_HL and linear residual Q are distinct descriptors",
                       "All 11 channels share one 594-dimensional covariance",
                       "No calibrated PTE, evidence, r inference, or native Bianchi result"]}
    artifacts={"x_HL_uK2":x,"x_linear_uK2":linear,"X_HL_matrices_uK2":matrices,
               "fiducial_binned_uK2":fid,"observed_binned_uK2":hat,"noise_binned_uK2":noise}
    return result,artifacts


def plot(result: dict, artifacts: dict, output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    order=result["pair_order"]
    chosen=[name+"x"+name for name in result["map_names"] if name.startswith(("BK18_K95", "BK18_150", "P353e"))]
    fig,axes=plt.subplots(1,2,figsize=(11,4.4))
    for name in chosen:
        i=order.index(name)
        axes[0].plot(np.arange(1,10),artifacts["x_HL_uK2"][:,i],marker="o",label=name.split("_Bx")[0])
    axes[0].set(xlabel="Released bin",ylabel="Fixed-fiducial HL auto component (uK^2)")
    axes[0].legend(fontsize=7)
    cov=artifacts["source_covariance"][:NPAIR,:NPAIR]
    sd=np.sqrt(np.diag(cov))
    corr=cov/np.outer(sd,sd)
    image=axes[1].imshow(corr,cmap="coolwarm",vmin=-1,vmax=1,origin="lower")
    axes[1].set(xlabel="Configured spectrum index, bin 1",ylabel="Configured spectrum index, bin 1")
    fig.colorbar(image,ax=axes[1],fraction=.045)
    fig.suptitle("BK18 BB-only fixed fiducial HL diagnostic")
    fig.tight_layout()
    for suffix in ("png","pdf"):
        fig.savefig(output/("diagnostic."+suffix),dpi=150)
    plt.close(fig)


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args(argv)
    root=args.repo_root.resolve();output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    receipt={"task":"BK18_FIXED_FIDUCIAL_HL","command":sys.argv,"repo_root":str(root),
             "requested_author_runtime":"gpt-6-sol/high","observed_author_runtime":"UNKNOWN",
             "python":sys.version,"numpy":np.__version__}
    for key,command in (("git_head",["rev-parse","HEAD"]),("git_status",["status","--porcelain=v1"])):
        call=subprocess.run(["git","-C",str(root),*command],capture_output=True,text=True)
        receipt[key]=call.stdout.strip() if call.returncode==0 else "UNAVAILABLE"
    try:
        release=load_release(root)
        result,artifacts=evaluate(release)
        artifacts["source_covariance"]=release["covariance"]
        npz=output/"fixed_fiducial_vectors.npz"
        np.savez_compressed(npz,**artifacts)
        result["vector_artifact"]={"path":npz.name,"sha256":digest(npz)}
        result["source_files"]=[{"path":str(path.relative_to(root)),"sha256":digest(path),
                                 "size_bytes":path.stat().st_size} for path in release["files"]]
        import importlib.metadata
        import inspect
        from cobaya.likelihoods.base_classes import cmblikes
        native_version=importlib.metadata.version("cobaya")
        if native_version != "3.6.2":
            raise ValueError("native Cobaya 3.6.2 parity version required")
        native_path=Path(inspect.getfile(cmblikes))
        result["native_code_source"]={"version":native_version,"kernel":NATIVE_TRANSFORM,
                                      "path":str(native_path),"sha256":digest(native_path)}
        (output/"result.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
        plot(result,artifacts,output)
        report=("# BK18 BB-only fixed-fiducial HL diagnostic\n\n"
                f"Q_HL = {result['Q_HL']:.9g}; unnormalized fixed-fiducial logL = {-result['Q_HL']/2:.9g}. "
                f"Separate linear residual Q = {result['Q_linear_residual_separate_gaussian_descriptor']:.9g}.\n\n"
                "The 66 configured spectra from all 11 B channels use one joint 594x594 covariance. "
                "The released fiducial and data each receive noise once. Native Cobaya transform and joint-vector parity are checked.\n\n"
                "Windows are audited on raw ell 1..999; the native theory uses ell 2..600. "
                "Their nonzero tails are recorded and never physically zeroed or renormalized.\n\n"
                "This fixed fiducial is not a foreground or cosmological fit. There is no calibrated PTE, evidence, r constraint, or Bianchi result.\n")
        (output/"report.md").write_text(report)
        receipt["exit_code"]=0
    except Exception as error:
        receipt["exit_code"]=1
        receipt["error"]=type(error).__name__+": "+str(error)
        (output/"failure.log").write_text(traceback.format_exc())
    receipt["elapsed_seconds"]=time.monotonic()-started
    receipt["code_sha256"]=digest(Path(__file__))
    (output/"execution_receipt.json").write_text(json.dumps(receipt,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"exit_code":receipt["exit_code"],"output":str(output)}))
    return receipt["exit_code"]


if __name__=="__main__":
    raise SystemExit(main())
