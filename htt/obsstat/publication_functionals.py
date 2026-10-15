"""Finite HTT posterior/partial-id functionals, preserving undefined mass.

This API handles mathematical posterior *images* only. The input joint atoms
are NOT constructed from data by this module and do not certify a physical
cosmological likelihood, total-x bound, or experiment-calibrated p-value.
MIO reports/certificates are NOT accepted as likelihood or posterior inputs.
"""
from __future__ import annotations
import math
from collections.abc import Mapping,Sequence


class FunctionalDomainError(ValueError):
    pass


def _positive(value):
    return isinstance(value,(int,float)) and math.isfinite(value) and value>0


def _possible_number(value):
    return value is None or (
        isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
    )


def _typed_components(record):
    expected=frozenset(("Sigma2","W2","Omega_tilt","DeltaOmega_k"))
    part=record.get("components")
    if not isinstance(part,Mapping) or set(part)!=expected:
        raise FunctionalDomainError("exact four-sector signed x_C Gauss inputs required")
    if any(not _possible_number(x) for x in part.values()):
        raise FunctionalDomainError("finite or explicit undefined Gauss terms expected")
    if part["Sigma2"] is not None and part["Sigma2"]<0:
        raise FunctionalDomainError("Sigma2 must be nonnegative")
    if part["W2"] is not None and part["W2"]<0:
        raise FunctionalDomainError("W2 must be nonnegative")
    if part["Omega_tilt"] is not None and part["Omega_tilt"]<0:
        raise FunctionalDomainError("normal-frame perfect-fluid tilt sector must be nonnegative")
    if any(x is None for x in part.values()):
        return None
    return (part["Sigma2"]-part["W2"]
            +part["Omega_tilt"]+part["DeltaOmega_k"])


def _f_sector(record):
    val=record.get("sector_value")
    bound=record.get("sector_ceiling")
    if not _possible_number(val) or not _possible_number(bound):
        raise FunctionalDomainError("finite or undefined sign-clean F values")
    if val is None or bound is None:
        return None
    if not _positive(bound) or val < 0 or val > bound:
        raise FunctionalDomainError("sign-clean F needs 0<=sector<=positive ceiling")
    return val/bound


def _q_value(x,record):
    den=record.get("U_sigma")
    if not _possible_number(den):
        raise FunctionalDomainError("finite or undefined shear MES anchor expected")
    if x is None or den is None or den==0:
        return None
    if den<0:
        raise FunctionalDomainError("Q denominator cannot be negative")
    return x/den


def _depth_values(record):
    # Distinct depth F indicators, already derived within the given same-draw law.
    data=record.get("depth_F")
    if not isinstance(data,Mapping) or set(data)!={"reference","comparison"}:
        raise FunctionalDomainError("G_F requires named reference/comparison depth F")
    out={}
    for k in ("reference","comparison"):
        v=data[k]
        if not _possible_number(v) or v is not None and not 0<=v<=1:
            raise FunctionalDomainError("depth F must be in [0,1] or undefined")
        out[k]=v
    return out


def finite_functional_image(atoms:Sequence[Mapping], *,thresholds:Sequence[float],
                            gf_floor:float, common_congruence:str,
                            reference_bin:str, comparison_bin:str):
    """Return partial intervals on original joint measure, without renormalizing.

    Pi_Q(t)=P(Q>t) on defined mass; missing Q event has conservative
    completion interval [known_above, known_above + undefined_mass].
    G_F computed from unconditioned depth-mean F summaries using predeclared
    floor, with a worst-case envelope for missing [0,1]-valued F.
    """
    if not isinstance(common_congruence,str) or not common_congruence.strip():
        raise FunctionalDomainError("explicit common source congruence required")
    if not all(isinstance(v,str) and v.strip() for v in (reference_bin,comparison_bin)) or reference_bin==comparison_bin:
        raise FunctionalDomainError("distinct actual depth-bin identifiers required")
    if not _positive(gf_floor) or gf_floor>1:
        raise FunctionalDomainError("positive G_F floor <=1 required")
    if isinstance(atoms,(str,bytes)) or not isinstance(atoms,Sequence) or len(atoms)==0:
        raise FunctionalDomainError("nonempty finite joint source required")
    try:
        ts=[float(v) for v in thresholds]
    except (TypeError,ValueError) as e:
        raise FunctionalDomainError("real finite thresholds") from e
    if not ts or any(not math.isfinite(v) for v in ts) or ts!=sorted(set(ts)):
        raise FunctionalDomainError("finite unique increasing thresholds required")
    raw_weights=[]
    ids=[]
    records=[]
    for atom in atoms:
        if not isinstance(atom,Mapping):
            raise FunctionalDomainError("raw joined atoms must be typed mappings; no MIO reports")
        if atom.get("owner") == "MIO" or "mio_certificate" in atom:
            raise FunctionalDomainError("MIO reports forbidden as HTT posterior source")
        ident=atom.get("sample_id")
        if not isinstance(ident,str) or not ident:
            raise FunctionalDomainError("unique physical draw ID required")
        if ident in ids:
            raise FunctionalDomainError("duplicate posterior latent draw")
        ids.append(ident)
        w=atom.get("weight")
        if not isinstance(w,(int,float)) or not math.isfinite(w) or w<0:
            raise FunctionalDomainError("nonnegative finite joint sample weights required")
        raw_weights.append(float(w))
        if atom.get("congruence")!=common_congruence:
            raise FunctionalDomainError("mixed u^a congruence/frame invalid for same x")
        x=_typed_components(atom)
        f=_f_sector(atom)
        q=_q_value(x,atom)
        depths=_depth_values(atom)
        records.append({"sample_id":ident,"x_C":x,"Q":q,"F":f,
                        "G_F_depth_values":depths})
    total=math.fsum(raw_weights)
    if not _positive(total):
        raise FunctionalDomainError("joint finite posterior has no mass")
    ww=[w/total for w in raw_weights]
    q_undef=math.fsum(w for w,r in zip(ww,records,strict=True) if r["Q"] is None)
    f_undef=math.fsum(w for w,r in zip(ww,records,strict=True) if r["F"] is None)
    x_undef=math.fsum(w for w,r in zip(ww,records,strict=True) if r["x_C"] is None)
    tails=[]
    for t in ts:
        known=math.fsum(w for w,r in zip(ww,records,strict=True)
                        if r["Q"] is not None and r["Q"]>t)
        tails.append({"threshold":t,"known_strict_exceedance_mass":known,
                      "unconditional_outer_interval":[known,min(1.,known+q_undef)],
                      "undefined_mass":q_undef})
    depth={}
    for k in ("reference","comparison"):
        known=math.fsum(w*r["G_F_depth_values"][k] for w,r in zip(ww,records,strict=True)
                        if r["G_F_depth_values"][k] is not None)
        undefined=math.fsum(w for w,r in zip(ww,records,strict=True)
                            if r["G_F_depth_values"][k] is None)
        depth[k]={"known_unconditional_mean_contribution":known,
                  "unknown_mass":undefined,
                  "mean_F_outer_interval":[known,min(1.,known+undefined)]}
    rc=depth["reference"]["mean_F_outer_interval"]
    cc=depth["comparison"]["mean_F_outer_interval"]
    gmin=max(cc[0],gf_floor)/max(rc[1],gf_floor)
    gmax=max(cc[1],gf_floor)/max(rc[0],gf_floor)
    if gmin>gmax+1e-14:
        raise FunctionalDomainError("G_F interval inconsistent")
    return {
        "schema":"htt.source_functionals_finite_partial_image/1",
        "status":"EXPLICITLY_CONDITIONAL_FINITE_INPUT_NO_LIKELIHOOD_BUILT",
        "common_congruence":common_congruence,
        "sample_ids":ids,
        "normalized_sample_weights":ww,
        "samples":records,
        "missing_mass":{"x_C":x_undef,"Q":q_undef,"F":f_undef},
        "Pi_Q_strict_threshold_outer_intervals":tails,
        "G_F":{"reference_bin":reference_bin,"comparison_bin":comparison_bin,
               "floor":gf_floor,
               "depth_F_mean_ranges":depth,
               "outer_interval":[gmin,gmax],
               "point_identified":depth["reference"]["unknown_mass"]==0
                                  and depth["comparison"]["unknown_mass"]==0},
        "claims":{"F_4_bolometric_is_not_F":True,"Pi_is_not_null_p":True,
                  "Q_anchor_is_shear_only_not_total_x_bound":True,
                  "physical_x_likelihood_provided":False,
                  "mio_posterior_consumed":False},
    }
