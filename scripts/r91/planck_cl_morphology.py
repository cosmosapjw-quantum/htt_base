"""R91: C_ell-only Planck likelihood loses Bianchi morphology information.

Construct two exact real quadrupoles sharing a Planck PR3 Commander source-
conditional TT C2 while having different eigenvalue invariants not related
by any SO(3) rotation. Numerical HEALPix harmonic check is independent
of analytic tensor-integration identity. No clik installation, likelihood,
Bianchi family label, or Bianchi photon solver is claimed.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import healpy as hp
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
G05=ROOT/"docs/research_program/observational_publication_20261015/R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs/G05_PLANCK/SOLVER_FREE_RESEARCH_RESULT.json"

def analyze(nside:int=64)->dict:
    inp=json.loads(G05.read_text())
    observed=inp["part_a_master_deconvolution"]["eight_observed_maps_master"]["PR3_Commander"]
    c2=float(observed["cl_master_TT_ell2_to_12"][0])
    assert 0<c2<1e-6
    # Tr(Q_i^2)=1 exactly: axisymmetric and zero-eigenvalue shapes.
    q_axis=np.diag([2.,-1.,-1.])/math.sqrt(6)
    q_cross=np.diag([1.,-1.,0.])/math.sqrt(2)
    factor=math.sqrt(c2*75/(8*math.pi))
    n=np.asarray(hp.pix2vec(nside,np.arange(hp.nside2npix(nside)))).T
    reports={}
    for key,Q in [("axisymmetric_eigenvalue",q_axis),
                  ("zero_eigenvalue_biaxial",q_cross)]:
        T=factor*np.einsum("ni,ij,nj->n",n,Q,n,optimize=True)
        alm=hp.map2alm(T,lmax=2,iter=3)
        cl=float(hp.alm2cl(alm)[2])
        evals=np.linalg.eigvalsh(Q)
        q2=float(np.trace(Q@Q))
        chi=float(math.sqrt(6)*np.trace(Q@Q@Q)/(q2**1.5))
        reports[key]={
           "C2_analytical_K2":float(8*math.pi/75*factor**2*q2),
           "C2_HEALPix_K2":cl,
           "relative_C2_HEALPix_vs_analytic":float(cl/c2-1),
           "STF_eigenvalues_Frobenius_unit":evals.tolist(),
           "signed_shape_chi":chi,
           "SO3_equivalence_to_other":"NO_BOTH_SHAPES_HAVE_DISTINCT_EIGENSPECTRA",
        }
    values=list(reports.values())
    assert abs(values[0]["C2_analytical_K2"]-values[1]["C2_analytical_K2"])<1e-24
    assert abs(values[0]["signed_shape_chi"]-values[1]["signed_shape_chi"])>0.9
    return {
        "schema":"htt.r91.planck_clik_loses_angular_morphology/1",
        "source":"R89 PR3 Commander TT source-conditional MASTER C2, not release-matched full-likelihood C2",
        "source_path":str(G05.relative_to(ROOT)),
        "source_sha256":hashlib.sha256(G05.read_bytes()).hexdigest(),
        "source_observed_PR3_Commander_master_C2_K2":c2,
        "input_claim":"TT C_ell-only likelihood uses rotational scalar power; does not store phases or STF shape",
        "mathematical_identity":"C2=8*pi/75*Tr(Q^2), T2(n)=n_i Q_ij n_j, trace(Q)=0",
        "proof":"normalizing TrQ²=1 gives fixed C2; Q_axis and Q_cross have distinct spectra and chi=1 vs chi=0, not SO(3)-conjugate",
        "examples":reports,
        "max_rel_c2_numerical_error":float(max(abs(z["relative_C2_HEALPix_vs_analytic"]) for z in values)),
        "clik_plik_useful_for":"fixed FLRW C_ell nuisance/background likelihood, or benchmark conditional Bianchi C_l power only",
        "clik_plik_not_sufficient_for":"morphology/phase/eigenframe or unique Bianchi family attribution",
        "observed_family_identification":False,"release_matched_null":False,
    }
