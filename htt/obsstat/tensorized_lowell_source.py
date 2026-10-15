"""Actual Planck irrep-resolved tensor anchor methods on FFP10 source cohort.

PR-254/255/262/264: retain even STF2 (5) and odd STF3 (7) channels,
their directional convex support and source-conditional finite empirical
functional images rather than replacing them with scalar temperature C_l,
legacy x_C or inferred physical congruence sigma/omega/A/beta.

This is an empirical 999 FFP10 CMB simulation statistical body; its
covariance is NOT a Bianchi/MES theorem, no selection-calibrated Planck
null p, no Bayesian posterior. Genuine physical kinematic tensor records
remain typed MISSING, preserving full undefined mass.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from common.anchor_geometry import AnchorBodySpec,AnchorGeometryKind
from common.typefree_functionals import (
    FunctionalSpec,FunctionalRecord,FiniteJointSource,
    evaluate_paired_anchor,support_utilization,finite_joint_pushforward,
    strict_exceedance,UndefinedValue
)


class TensorSourceError(ValueError):
    pass


@dataclass(frozen=True)
class TensorEmpiricalBody:
    spec: FunctionalSpec
    body: AnchorBodySpec
    source_mean: np.ndarray
    covariance: np.ndarray
    invcovariance: np.ndarray
    eigvals: np.ndarray
    n_source: int
    ell: int


def _real(a,columns):
    x=np.asarray(a)
    if (x.ndim!=2 or x.shape[1]!=columns or len(x)<12
        or np.iscomplexobj(x) or not np.isfinite(x).all()):
        raise TensorSourceError("12+ finite registered real source harmonic samples needed")
    return np.asarray(x,float)


def empirical_irrep_anchor(coeff,*,ell,source_hash):
    """Fixed unit-RMS empirical source covariance ellipsoid, no threshold."""
    if ell not in (2,3) or not isinstance(source_hash,str) or len(source_hash)!=64:
        raise TensorSourceError("ell2 or ell3 with exact 64 hex source identity")
    n=2*ell+1
    x=_real(coeff,n)
    mean=x.mean(axis=0)
    cov=np.cov(x,rowvar=False,ddof=1)
    cov=(cov+cov.T)/2
    eig=np.linalg.eigvalsh(cov)
    if eig[0]<=0 or eig[-1]/eig[0]>1e7:
        raise TensorSourceError("empirical covariance rank/conditioning inadequate")
    inv=np.linalg.inv(cov)
    labels=tuple(f"ell{ell}_real_mode_{i}" for i in range(n))
    frame="GALACTIC_CONDON_SHORTLEY_HEALPIX_TEMPERATURE"
    normal="FFP10_K1_CMB_999_ONE_MASK_EMPIRICAL_STF_IRREP_COVARIANCE"
    order="SOURCE_PROCESSED_LEADING_LOWELL"
    branch="CMB_SIGNAL_ONLY_NOT_OBSERVED_BIANCHI_TRANSPORT"
    spec=FunctionalSpec(
      definition_id=f"htt.PR262.FFP10.STF{ell}.REAL_SOURCE_DELTA/1",
      coordinate_labels=labels,output_shape=(n,),rank=ell,
      parity="EVEN_STF2" if ell==2 else "ODD_STF3",
      basis=f"ORTHONORMAL_REAL_Y{ell}M_GALACTIC",
      units="microK_thermodynamic",frame=frame,
      epoch="ACTUAL_PLANCK_2018_PR3_LOWELL_SOURCE",
      domain_id=f"FFP10_SELECTED_MASK_CMB_ONLY_ELL{ell}",
      normalization=normal,perturbative_order=order,branch=branch)
    body=AnchorBodySpec(
      body_id=f"htt.ffp10.empirical.Stf{ell}.unit_cov_ellipsoid",
      geometry=AnchorGeometryKind.ELLIPSOID,
      coordinate_labels=labels,frame=frame,
      normalization=normal,perturbative_order=order,branch=branch,
      premise_identity=f"source-sha256:{source_hash}",
      quadratic_form=tuple(tuple(float(q) for q in row) for row in inv),
      assumptions=(
       "empirical second-moment body of 999 source-conditioned simulation maps",
       "no calibrated coverage or physical MES theorem",
       "same selected mask and harmonic estimator on each source"),
    )
    return TensorEmpiricalBody(spec,body,mean,cov,inv,eig,len(x),ell)


def record(body:TensorEmpiricalBody,latent_id,value,*,physical_defined=True):
    if not physical_defined:
        return FunctionalRecord(latent_id,body.spec,None,None,
                                status="MISSING_PHYSICAL_LIGHTCONE_RESPONSE")
    v=np.asarray(value)
    if v.shape!=(2*body.ell+1,) or np.iscomplexobj(v) or not np.isfinite(v).all():
        raise TensorSourceError("finite source irreducible coefficient vector")
    return FunctionalRecord(latent_id,body.spec,np.asarray(v,float),
                            body.source_mean,anchor=body.body)


def empirical_gauge_image(body:TensorEmpiricalBody,source_coeff,source_ids,*,thresholds=(1.,2.)):
    x=_real(source_coeff,2*body.ell+1)
    ids=np.asarray(source_ids)
    if len(ids)!=len(x) or len(set(map(str,ids)))!=len(x):
        raise TensorSourceError("exact one-to-one unique original source IDs")
    records=tuple(record(body,f"ffp10-cmb-{z}",row)
                  for z,row in zip(ids,x,strict=True))
    source=FiniteJointSource(
        joint_id=f"K1_CMB_999_ELL{body.ell}_SAME_IDS",
        records=records,law_kind="EMPIRICAL",
        domain_id=body.spec.domain_id)
    image=finite_joint_pushforward(source,
        lambda rec: np.asarray(evaluate_paired_anchor(rec).gauge),
        definition_id=f"htt.anchor.empirical.Q_STF{body.ell}/1",
        target_domain_id="EMPIRICAL_IRREP_GAUGE_NOT_SHEAR_OR_PI_PHYSICAL")
    if image.status!="DEFINED" or image.undefined_mass!=0:
        raise TensorSourceError("empirical coefficient source unexpectedly unidentified")
    q=np.asarray([float(atom.value) for atom in image.atoms])
    oracle=np.sqrt(np.einsum("ni,ij,nj->n",x-body.source_mean,
                             body.invcovariance,x-body.source_mean,optimize=True))
    if np.max(abs(q-oracle))>1e-10:
        raise TensorSourceError("PR262 typed gauge differs from direct quadratic oracle")
    tail=[]
    for t in thresholds:
        z=strict_exceedance(image,float(t))
        tail.append({"threshold":z.threshold,
                     "source_empirical_known_exceedance_mass":z.known_exceedance_mass,
                     "source_empirical_undefined_mass":z.undefined_mass,
                     "status":"RETROSPECTIVE_SIMULATION_RANK_NOT_PLANCK_P_VALUE"})
    return {"gauge":q,"image":image,"source":source,"tail":tail}


def physical_unmeasured_tensor_image(body:TensorEmpiricalBody,source_ids):
    ids=np.asarray(source_ids)
    if len(ids)!=body.n_source:raise TensorSourceError("source IDs not same empirical count")
    records=tuple(record(body,f"phys-unknown-{z}",None,physical_defined=False)
                  for z in ids)
    src=FiniteJointSource(
        joint_id=f"PHYSICAL_MISSING_{body.ell}_SIMULATION_COHORT",
        records=records,law_kind="EMPIRICAL",domain_id="PHYSICS_UNQUALIFIED_CMB_TRANSFER")
    image=finite_joint_pushforward(src,lambda r: UndefinedValue("MISSING_PHYSICAL_LIGHTCONE_RESPONSE"),
         definition_id="physical_sigma_NOT_CALIBRATED",
         target_domain_id="PHYSICAL_STF_NOT_FROM_CMB_ELL")
    tail=strict_exceedance(image,1.)
    if abs(image.undefined_mass-1)>5e-13 or tail.lower!=0 or abs(tail.upper-1)>5e-13:
        raise TensorSourceError("physical missing irrep mass must remain 100%")
    return {"physical_tensor_image_undefined_mass":image.undefined_mass,
            "physical_tensor_exceedance_outer":[tail.lower,tail.upper],
            "physical_claim":"NO_SOURCE_SELECTED_PHYSICAL_KINEMATIC_POSTERIOR"}


def measured_directional_support(body:TensorEmpiricalBody,value,u):
    rec=record(body,"actual-Planck-SMICA_K1_ONE_SKY",value)
    direction=np.asarray(u,float)
    if direction.shape!=(2*body.ell+1,) or not np.isfinite(direction).all():
        raise TensorSourceError("source chart direction must be finite 5/7 vector")
    out=support_utilization(rec,direction)
    if out.status!="DEFINED":
        raise TensorSourceError("source support unusable without physical claim")
    analytic=float(direction@(np.asarray(value)-body.source_mean)/
                   np.sqrt(direction@body.covariance@direction))
    if abs(out.value-analytic)>3e-11:
        raise TensorSourceError("typed support function incompatible with CMB source covariance")
    return {"support":out.support,
            "numerator":out.numerator,
            "F_directional_support_ratio":out.value,
            "status":"EMPIRICAL_F_DIRECTION_ONLY_NOT_SIGN_CLEAN_LEGACY_F"}
