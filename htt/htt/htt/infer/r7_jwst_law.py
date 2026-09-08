"""JWST Gaussian host population with distinct measurement-error families."""
from __future__ import annotations
from itertools import product
import math
import numpy as np
from scipy.special import gammaln, logsumexp, roots_genlaguerre
from common.r7_contracts import ScopeKey,CONVENTIONS,VERSION,finite_array,content_id,NumericalUnresolved
from .r7_gaussian_law import JointObservationLaw,decompose_covariance,gaussian_loglik
from common.r7_contracts import UnavailableLaw
from .jwst_host_hierarchy import HostPair,contrast_matrix,contrast_covariance


def _student_loglik(residual,scale,df,support_tol):
    d=decompose_covariance(scale)
    if not d.resolved: raise NumericalUnresolved("Student measurement support rank unresolved")
    if d.null.size and np.linalg.norm(d.null.T@residual)>support_tol: return -math.inf
    if not d.rank: return 0.
    q=float(residual@d.inverse@residual)
    return float(gammaln((df+d.rank)/2)-gammaln(df/2)-d.rank/2*math.log(df*math.pi)
        -.5*np.log(d.eigenvalues[d.positive]).sum()-(df+d.rank)/2*math.log1p(q/df))


def build_jwst_law(host_products,covariance,calibration,measurement_family):
    pid=host_products.get("product_id","JWST")
    if covariance is None or calibration is None:
        return UnavailableLaw(pid,"INPUT_UNAVAILABLE",("full shared measurement covariance or calibration law missing",))
    pairs=tuple(host_products.get("pairs",()))
    if not pairs or any(not isinstance(p,HostPair) for p in pairs):
        return UnavailableLaw(pid,"INPUT_UNAVAILABLE",("ordered source host/method pairs absent",))
    ids=tuple(v for p in pairs for v in (f"{p.dataset}:{p.host}:{p.method_a}",f"{p.dataset}:{p.host}:{p.method_b}"))
    if len(set(ids))!=len(ids): raise ValueError("absolute host measurements may be consumed only once")
    if tuple(covariance["measurement_ids"])!=ids: raise ValueError("JWST full covariance row order mismatch")
    source_y=np.array([v for p in pairs for v in (p.mu_a_mag,p.mu_b_mag)])
    c=decompose_covariance(covariance["matrix"]).covariance
    if c.shape!=(len(ids),len(ids)): raise ValueError("JWST covariance shape")
    h=np.zeros((len(ids),len(pairs)))
    for i in range(len(pairs)):h[2*i:2*i+2,i]=1.
    population=decompose_covariance(calibration["host_population_covariance"])
    if population.covariance.shape!=(len(pairs),len(pairs)): raise ValueError("Gaussian host population covariance shape")
    source_design=finite_array(calibration["design"],ndim=2)
    if len(source_design)!=len(ids): raise ValueError("calibration design row order")
    mode=host_products.get("measurement_mode","CONTRAST")
    if mode=="CONTRAST":
        transform=contrast_matrix(len(pairs));measurement_ids=tuple(f"{pid}:{p.host}:{p.method_a}-{p.method_b}" for p in pairs)
        if not np.allclose(transform@c@transform.T,contrast_covariance(c),rtol=0,atol=1e-14):raise ValueError("contrast covariance implementation mismatch")
    elif mode=="ABSOLUTE":transform=np.eye(len(ids));measurement_ids=ids
    else: raise ValueError("choose original absolute rows or contrasts; composition binds shared-source maps")
    y=transform@source_y;design=transform@source_design;noise=transform@c@transform.T;host=transform@h
    host_scatter=host@population.covariance@host.T
    names=tuple(calibration["parameter_names"]);units=tuple(calibration["parameter_units"])
    if design.shape[1]!=len(names): raise ValueError("calibration parameter layout")
    if measurement_family not in {"GAUSSIAN","STUDENT_T"}: raise ValueError("measurement family must be Gaussian or Student-t")
    spec={"source_ids":[host_products["source_id"],calibration["source_id"]],"selection_law":host_products["selection_id"],
        "covariance_source":covariance["source_id"],"mean_definition":"fixed host/method linear design; geometric distance cancels in same-host contrast",
        "measurement_family":measurement_family,"host_population":"GAUSSIAN","host_covariance":population.covariance,
        "measurement_covariance":c,"measurement_map":transform,"source_measurement_ids":ids,"design":design,
        "calibration":calibration["source_id"],"parameter_names":names,"parameter_units":units}
    support_tol=float(covariance.get("support_tol",0.))
    custom=None;approximation="KNOWN_GAUSSIAN_HOST_AND_MEASUREMENT_MODEL";total=noise+host_scatter
    if measurement_family=="STUDENT_T":
        df=float(calibration["measurement_df"])
        if not math.isfinite(df) or df<=0: raise ValueError("proper positive Student degrees of freedom")
        spec.update(measurement_df=df,normalized_density_definition="Gaussian host population convolved with joint Student-t measurement density")
        if not np.any(host_scatter):
            custom=lambda t,e:_student_loglik(y-design@t,noise,df,support_tol)
            approximation="EXACT_STUDENT_MEASUREMENT_GAUSSIAN_HOST_CANCELLED"
        else:
            # Student noise is a Gamma precision mixture. Integrating precision
            # after adding the Gaussian host covariance preserves enlarged
            # singular support; quadrature over host locations does not.
            order=int(calibration.get("quadrature_order",64))
            if order<2 or order>512:return UnavailableLaw(pid,"NUMERICALLY_UNRESOLVED",("precision quadrature order outside [2,512]",))
            nodes,weights=roots_genlaguerre(order,df/2-1)
            precisions=nodes/(df/2);logweights=np.log(weights)-gammaln(df/2)
            custom=lambda t,e:float(logsumexp([lw+gaussian_loglik(y-design@t,host_scatter+noise/precision,support_tol)
                for precision,lw in zip(precisions,logweights)]))
            spec["quadrature_order"]=order
            approximation="GAUSSIAN_HOST_STUDENT_MEASUREMENT_GAMMA_PRECISION_QUADRATURE_APPROXIMATION"
        total=None  # Student scale is not its covariance, and df may be <=2.
    scope=ScopeKey(pid,content_id(spec),"JWST_"+mode+"_"+measurement_family,(host_products["source_id"],),CONVENTIONS,VERSION,
        "gaussian_acceptance" if measurement_family=="GAUSSIAN" else "student_measurement_acceptance",
        content_id({"alpha":.05,"family":measurement_family,"mode":mode,"design":design}))
    return JointObservationLaw(scope,y,measurement_ids,names,units,lambda t,e:design@finite_array(t,shape=(len(names),)),
        total,spec,"JWST_CALIBRATION_R"+str(len(names)),lambda t,e:np.asarray(t).shape==(len(names),),
        jacobian_theta=lambda t,e:design,jacobian_eta=lambda t,e:np.empty((len(y),0)),
        shared_latent_ids=tuple(calibration.get("shared_latent_ids",())),conditioning_target="FIXED_HOST_SELECTION_AND_CALIBRATION_MODEL",
        support_tol=support_tol,approximation=approximation,log_density=custom)
