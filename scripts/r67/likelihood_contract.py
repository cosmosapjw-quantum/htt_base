"""R67 typed cross-probe inference: prevent unqualified double counting.

Score/Fisher are standard Gaussian finite-dimensional algebra. No new Bayesian
evidence, sky null or cosmological transfer is inferred by data packaging.
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class GaussianProbe:
    name: str
    physical_parameter: str
    frame: str
    epoch: str
    source_group: str
    covariance_qualified: bool
    response_qualified: bool
    C: np.ndarray
    J: np.ndarray
    N: np.ndarray | None = None


def source_joint_ready(
    probes: list[GaussianProbe], cross_covariance=None, *,
    joint_covariance_qualified: bool = False,
    independence_qualified: bool = False,
    provenance: str = "",
):
    """Gate a *declared* common-referent Gaussian experiment.

    No source-independent claim follows from different source-group labels.
    The caller must supply its source-overlap/covariance provenance before
    a block-diagonal product or a supplied full cross-covariance is accepted.
    This check cannot authenticate the caller's scientific evidence.
    """
    if not probes:
        raise ValueError("No probes")
    identities = {(x.physical_parameter, x.frame, x.epoch) for x in probes}
    if len(identities) != 1:
        return {"status": "INCOMPATIBLE_PHYSICAL_REFERENT",
                "referents": [list(a) for a in sorted(identities)]}
    if not all(x.response_qualified and x.covariance_qualified for x in probes):
        return {"status": "UNQUALIFIED_RESPONSE_OR_COVARIANCE"}
    for x in probes:
        Cp = np.asarray(x.C, float)
        Jp = np.asarray(x.J, float)
        if (Cp.ndim != 2 or Cp.shape[0] != Cp.shape[1] or
                Jp.ndim != 2 or Jp.shape[0] != Cp.shape[0] or
                not np.all(np.isfinite(Cp)) or
                not np.allclose(Cp, Cp.T, rtol=1e-10, atol=1e-12) or
                np.linalg.eigvalsh(Cp).min() <= 0):
            raise ValueError("Probe covariance or response invalid")
    groups = [x.source_group for x in probes]
    if cross_covariance is not None:
        C = np.asarray(cross_covariance, float)
        total = sum(x.C.shape[0] for x in probes)
        if (C.shape != (total, total) or
                not np.all(np.isfinite(C)) or
                not np.allclose(C, C.T, rtol=1e-10, atol=1e-12) or
                np.linalg.eigvalsh(C).min() <= 0):
            raise ValueError("Invalid explicit joint covariance")
        offset = 0
        for x in probes:
            n = x.C.shape[0]
            if not np.allclose(C[offset:offset+n, offset:offset+n],
                               x.C, rtol=1e-9, atol=1e-12):
                raise ValueError("Supplied joint covariance conflicts with probe marginal")
            offset += n
        if not joint_covariance_qualified or not provenance.strip():
            return {"status": "JOINT_COVARIANCE_PROVENANCE_REQUIRED"}
        return {"status": "JOINT_COVARIANCE_EXPLICIT", "dimension": total}
    if len(groups) > len(set(groups)):
        return {"status": "SHARED_SOURCE_CROSS_COVARIANCE_REQUIRED"}
    if not independence_qualified or not provenance.strip():
        return {"status": "INDEPENDENCE_NOT_ESTABLISHED"}
    return {"status": "BLOCK_DIAGONAL_CONDITIONALLY_ALLOWED"}


def nuisance_profile_fisher(J: np.ndarray, C: np.ndarray, N: np.ndarray|None=None):
    """Schur information; full source covariance must already be supplied."""
    J,C=np.asarray(J,float),np.asarray(C,float)
    if C.shape!=(len(J),len(J)) or not np.allclose(C,C.T):
        raise ValueError("Bad covariance shape")
    if np.linalg.eigvalsh(C).min()<=0:
        raise ValueError("Covariance not positive definite")
    Ci=np.linalg.inv(C)
    if N is None or np.asarray(N).size==0:
        P=Ci
    else:
        N=np.asarray(N,float)
        if N.shape[0]!=len(J):raise ValueError("Bad nuisance dimension")
        H=N.T@Ci@N
        P=Ci-Ci@N@np.linalg.pinv(H)@N.T@Ci
    F=J.T@P@J
    F=(F+F.T)/2
    return {"F":F,"rank":int(np.linalg.matrix_rank(F)),
            "dim":len(F),"singular_values":np.linalg.svd(F,compute_uv=False)}
