"""Project actual CORAS conditional velocity residuals through the CF4 H02 windows."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import numpy as np


def _sha(path):
    with path.open("rb") as src:
        return hashlib.file_digest(src, "sha256").hexdigest()


def read_radial(path, ids):
    """Read exact integer object identities and one finite radial velocity in km/s."""
    def integer(token):
        if isinstance(token, bytes):
            token = token.decode("ascii")
        if not re.fullmatch(r"[0-9]+", token):
            raise ValueError("invalid catalogue integer")
        return int(token)
    data = np.loadtxt(path, comments="#", ndmin=1, dtype=[("id","<i8"),("v","<f8")],
                      converters={0:integer})
    if not np.array_equal(data["id"], ids):
        raise ValueError(f"CF4 row count, identity or ordering differs in {path}")
    if not np.isfinite(data["v"]).all():
        raise ValueError(f"nonfinite radial velocity in {path}")
    return data["v"]


def cov(draws):
    delta = draws - draws.mean(axis=0)
    return delta.T @ delta / (len(draws)-1)


def rel_diff(a,b):
    den = np.linalg.norm(b)
    return float(np.linalg.norm(a-b)/den) if den else None


def split_diagnostic(draws):
    if len(draws) < 4:
        return dict(status="need_at_least_four_draws")
    a,b=np.array_split(draws,2)
    ca,cb=cov(a),cov(b)
    den=(np.linalg.norm(ca)+np.linalg.norm(cb))*.5
    return dict(half_counts=[len(a),len(b)], trace_first=float(np.trace(ca)),
                trace_last=float(np.trace(cb)), mean_difference_norm=float(np.linalg.norm(a.mean(0)-b.mean(0))),
                symmetric_relative_frobenius=float(np.linalg.norm(ca-cb)/den) if den else None)


def quadratic(residual, covariance):
    chol=np.linalg.cholesky(covariance)
    z=np.linalg.solve(chol,residual)
    return float(z@z)


def summarized(mean, draws, nn, obs, measurement):
    err=cov(draws)
    centered=draws-draws.mean(axis=0)
    sec=mean + draws.mean(axis=0)
    return dict(analytic_mean_36=mean.tolist(), residual_sample_mean_36=draws.mean(axis=0).tolist(),
                ensemble_mean_36=sec.tolist(), sample_covariance_36x36=err.tolist(), ddof=1,
                residual_sample_rank=int(np.linalg.matrix_rank(centered)), covariance_rank=int(np.linalg.matrix_rank(err)),
                rank_upper_bound=min(len(draws)-1,len(mean)), covariance_trace=float(np.trace(err)),
                covariance_eigenvalues=np.linalg.eigvalsh(err).tolist(), split_by_sorted_seed=split_diagnostic(draws),
                analytic_mean_minus_nn_norm=float(np.linalg.norm(mean-nn)), mean_relative_to_nn=rel_diff(mean,nn),
                measurement_only_quadratic={"observed":quadratic(obs,measurement),
                                             "minus_coras":quadratic(obs-mean,measurement),
                                             "minus_nn":quadratic(obs-nn,measurement)},
                measurement_plus_sample_cov_quadratic_minus_coras=quadratic(obs-mean,measurement+err))


def compare_mesh(left, right):
    """Equal integer seeds pair labels; different grids may alter random-mode correspondence."""
    shared=sorted(set(left["draws"]).intersection(right["draws"]))
    out=dict(common_seeds=shared, mean_difference_norm=float(np.linalg.norm(left["mean"]-right["mean"])),
             mean_relative_to_second_mesh=rel_diff(left["mean"],right["mean"]))
    if shared:
        a=np.array([left["draws"][s] for s in shared])
        b=np.array([right["draws"][s] for s in shared])
        out.update(residual_array_relative_to_second_mesh=rel_diff(a,b),
                   paired_residual_rms_norm=float(np.sqrt(np.mean(np.sum((a-b)**2,axis=1)))))
        if len(shared)>=2:
            out["covariance_relative_to_second_mesh"]=rel_diff(cov(a),cov(b))
    return out


def metadata(directory, geometry):
    path=directory/"run.json"
    if not path.is_file():
        raise ValueError(f"missing completed CORAS run receipt in {directory}")
    rec=json.loads(path.read_text())
    first,last=rec["first"],rec["last"]
    if any(type(x)!=int for x in (first,last)) or not (1<=first<=last):
        raise ValueError("invalid seed range")
    keys=("config","donor_commit","source_sha256","binary_sha256","input_sha256","sites_sha256")
    identity={k:rec[k] for k in keys}
    if (rec["donor_commit"]!="45ab25635aa32869ce207511d556ea257ab8a591"
            or not isinstance(rec["input_sha256"],dict)
            or set(rec["input_sha256"])!={"data/2MRS_group_member_catalog.dat","data/CosmicEmu_spectrum_Planck18.dat"}
            or rec["groups"]!=len(geometry["ids"])
            or not {"radial","ell","fft","smoothing_Mpch","growth_fsigma8","external_bulk_galactic_kms"}<=set(rec["config"])):
        raise ValueError("invalid CORAS configuration or sample binding")
    for val in (rec["source_sha256"],rec["binary_sha256"],rec["sites_sha256"],*rec["input_sha256"].values()):
        if not isinstance(val,str) or not re.fullmatch(r"[0-9a-f]{64}",val):
            raise ValueError("invalid input SHA-256")
    sites=directory/"sites.tsv"
    if _sha(sites)!=rec["sites_sha256"]:
        raise ValueError(f"sites digest mismatch: {sites}")
    coords=np.loadtxt(sites, ndmin=1, dtype=[("i","i8"),("r","f8"),("theta","f8"),("phi","f8")])
    theta,phi=coords["theta"],coords["phi"]
    n=np.column_stack((np.sin(theta)*np.cos(phi),np.sin(theta)*np.sin(phi),np.cos(theta)))
    if (not np.array_equal(coords["i"],geometry["ids"])
            or not np.allclose(coords["r"],geometry["radius"],rtol=3.e-13,atol=1e-11)
            or not np.allclose(n,geometry["ng"],rtol=0.,atol=2.e-12)):
        raise ValueError("sites do not match the adopted CF4 geometry")
    return rec,json.dumps(identity,sort_keys=True),identity,first,last


def run(runs, geometry):
    ids=np.asarray(geometry["ids"])
    w=np.asarray(geometry["weights"],float)
    nn=np.asarray(geometry["nn"],float)
    obs=np.asarray(geometry["observed"],float)
    meas=np.asarray(geometry["measurement_cov"],float)
    if (ids.ndim!=1 or not np.issubdtype(ids.dtype,np.integer) or len(set(ids))!=len(ids)
            or w.shape!=(36,len(ids)) or nn.shape!=(36,) or obs.shape!=(36,) or meas.shape!=(36,36)
            or not all(np.isfinite(a).all() for a in (w,nn,obs,meas)) or
            not np.allclose(meas,meas.T,rtol=1.e-11,atol=1.e-17)):
        raise ValueError("incompatible CF4 compression geometry")
    groups={}
    for directory in runs:
        rec, groupkey, description, first,last = metadata(directory,geometry)
        seeds=list(range(first,last+1))
        files={p.name for p in directory.glob("residual_*.tsv")}
        if files!={f"residual_{s}.tsv" for s in seeds} or not (directory/"mean.tsv").is_file():
            raise ValueError(f"incomplete or stale draws in {directory}")
        meanfile=directory/"mean.tsv"
        expected=rec["output_sha256"]
        if set(expected)!=files|{"mean.tsv"}:
            raise ValueError("incomplete file identities in run receipt")
        meanhash=_sha(meanfile)
        if meanhash!=expected["mean.tsv"]:
            raise ValueError("mean SHA-256 mismatch")
        mean=w@read_radial(meanfile,ids)
        current=groups.setdefault(groupkey, dict(description=description,mean=mean,mean_sha256=meanhash,
                                                 draws={},run_files=[]))
        if current["mean_sha256"]!=meanhash:
            raise ValueError("same configuration produced differing conditional-mean bytes")
        hashes={}
        for s in seeds:
            if s in current["draws"]:
                raise ValueError("duplicate seed in same configuration")
            f=directory/f"residual_{s}.tsv"
            hashes[str(s)]=_sha(f)
            if hashes[str(s)]!=expected[f.name]:
                raise ValueError(f"residual SHA-256 mismatch in {f}")
            current["draws"][s]=w@read_radial(f,ids)
        current["run_files"].append(dict(directory=str(directory.resolve()),run_json_sha256=_sha(directory/"run.json"),
                                         seed_range=[first,last],mean_sha256=meanhash,residual_sha256=hashes))
    reports=[]
    seq=list(groups.values())
    for group in seq:
        seeds=sorted(group["draws"])
        if len(seeds)<2:
            raise ValueError("each distinct configuration needs at least two residual seeds")
        draws=np.array([group["draws"][s] for s in seeds])
        reports.append(dict(configuration=group["description"],n_draws=len(seeds),seed_ids=seeds,
                            run_files=group["run_files"],**summarized(group["mean"],draws,nn,obs,meas)))
    comparisons=[]
    for i,left in enumerate(seq):
        for j in range(i+1,len(seq)):
            right=seq[j]
            a,b=left["description"],right["description"]
            numerical={"radial","ell","fft"}
            ca={k:v for k,v in a["config"].items() if k not in numerical}
            cb={k:v for k,v in b["config"].items() if k not in numerical}
            if ca==cb and all(a[k]==b[k] for k in a if k!="config"):
                comparisons.append(dict(config_indices=[i,j],**compare_mesh(left,right)))
    return dict(schema="htt.r105.coras_field_cov/1",n_common=len(ids),
                source_order_sha256=hashlib.sha256(np.ascontiguousarray(ids,dtype='<i8')).hexdigest(),
                projection_sha256=hashlib.sha256(np.ascontiguousarray(w,dtype='<f8')).hexdigest(),
                nn_common_36=nn.tolist(),observed_36=obs.tolist(),configs=reports,mesh_comparisons=comparisons,
                uncertainty="Observed conditional CORAS realization scatter on 2MRS constraints. "
                            "Adding the measurement matrix assumes zero cross-covariance for the descriptive quadratic only.",
                source_qualification="BLOCKED_INPUT",physical_Pi=None,calibrated_p=None)


def main(argv=None):
    from scripts.r105.coras_flow import samples
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runs",nargs="+",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args(argv)
    out=run(args.runs,samples())
    payload=json.dumps(out,indent=2,allow_nan=False)+"\n"
    if args.output.exists():
        if json.loads(args.output.read_text())!=out:
            raise FileExistsError(f"conflicting reduction at {args.output}")
        return
    import os,tempfile
    with tempfile.NamedTemporaryFile(dir=args.output.parent,mode="w",delete=False) as tmp:
        loc=Path(tmp.name)
        try:
            tmp.write(payload);tmp.flush();os.fsync(tmp.fileno())
            try:
                os.link(loc,args.output)
            except FileExistsError:
                if json.loads(args.output.read_text())!=out:
                    raise
        finally:
            loc.unlink(missing_ok=True)


if __name__=="__main__":
    main()
