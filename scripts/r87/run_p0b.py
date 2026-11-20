"""R87 SQ-CF4 P0-B: exact-public-release source method/sky diagnostic.

Run only on original pinned CDS table3/table4 and selected 35970 source.
Writes a new create-only source-conditional report; no science DAG mutation.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

import numpy as np

from htt.obsstat import cf4_p0b as p
from htt.obsstat.catalogs.cf4_grouped_observations import load_grouped_observations,METHODS

ROOT=Path("docs/research_program/observational_publication_20261015")
OUTPUT=ROOT/"R87_SQ_CF4_P0B_METHOD_COV_HELDOUT_20261120/RESULT.json"
MODELS=((0.,1.5),(150.,0.),(150.,1.5))


def serialize(obj):
    # A gauge-fixed SNIA delta=0 has no measured absolute error: publish
    # a JSON null, never NaN/Infinity or a spuriously zero uncertainty.
    if isinstance(obj,np.ndarray):return serialize(obj.tolist())
    if isinstance(obj,np.generic):return serialize(obj.item())
    if isinstance(obj,float):
        return obj if np.isfinite(obj) else None
    if isinstance(obj,dict):return {key:serialize(value) for key,value in obj.items()}
    if isinstance(obj,(list,tuple)):return [serialize(value) for value in obj]
    if isinstance(obj,(bool,int,str)) or obj is None:return obj
    raise TypeError(f"unsupported result type {type(obj)}")


def summary():
    s=p.load_cf4_method_source()
    assert p.validate_source_identity(s)
    info=p.profile_source_method_offsets(s)
    held=p.spatial_group_heldout(s)
    full=p.load_grouped_observations(p.RAW/"table3.dat",p.RAW/"table4.dat",p.RAW/"ReadMe")
    gids=full.group_id
    is_sel=np.isin(gids,s.group_id,assume_unique=True)
    assert is_sel.sum()==35970 and len(gids)==38053
    # R54/R58 inclusion is a *known analysis selection*, not astronomical
    # detection probability over objects absent from the released CF4 table.
    ra=np.arctan2(full.direction[:,1],full.direction[:,0])%(2*np.pi)
    footprint=[]
    for q in range(4):
        mk=(ra>=q*np.pi/2)&(ra<(q+1)*np.pi/2)
        footprint.append({"quadrant":q,"raw_count":int(mk.sum()),
              "selected_count":int(np.sum(is_sel&mk)),
              "conditional_analysis_inclusion_fraction":float(np.mean(is_sel[mk]))})
    inclusion_by_method={}
    for j,name in enumerate(METHODS):
        where=full.method_presence[:,j]
        inclusion_by_method[name]={
          "original_released_group_count":int(where.sum()),
          "included_selected_group_count":int(np.sum(where&is_sel)),
          "fraction_included_given_original_released_group_with_method":
              float(np.mean(is_sel[where])) if np.any(where) else None}
    pairs=np.asarray(s.method_presence,dtype=int).T @ np.asarray(s.method_presence,dtype=int)
    n_full=s.method_presence.sum(axis=1)
    n_use=np.isfinite(s.method_sigma).sum(axis=1)
    pv=[]
    for bulk,shear in MODELS:
        z=p.pv_sensitivity_scenario(s,bulk_sigma_kms=bulk,
                                  shear_sigma_kms_per_mpc=shear)
        pv.append({
          "sigma_bulk_km_per_s":bulk,
          "sigma_shear_km_per_s_per_Mpc":shear,
          "velocity_modes_source_assumed_rank":z["source_assumed_low_rank_modes"],
          "relative_distance_to_H03_apparent_mean_span":
                z["source_modes_distance_to_H03_mean_span_relative"],
          "all_PV_modes_inside_original_H03_mean_design":z["source_modes_fully_in_mean_span"],
          "exact_linear_gaussian_covariance_theorem_relative_error":z["source_span_theorem_covariance_relative_error"],
          "working_H03_beta9_with_source_PV":z["working_gls_beta_with_assumed_PV"].tolist(),
          "working_H03_beta9_diagonal_only":z["working_gls_beta_only_diagonal"].tolist(),
          "working_H03_beta9_maxabs_difference":z["working_gls_beta_max_abs_difference"],
          "source_working_coefficient_cov_trace_ratio":z["covariance_trace_ratio"],
          "physical_PV_field_ensemble_qualified":False,
          "physical_selection_covariance_qualified":False
        })
    assert len(pv)==3 and pv[0]["working_H03_beta9_maxabs_difference"]<1e-8
    assert pv[1]["working_H03_beta9_maxabs_difference"]>0
    assert pv[2]["working_H03_beta9_maxabs_difference"]>0
    assert len(held["folds"])==4
    assert all(row["unique_group_ID_train_vs_test_overlap"]==0 for row in held["folds"])
    raw_presence_zero=int((n_full==0).sum())
    noncal_zero=int((n_use==0).sum())
    assert raw_presence_zero==185 and noncal_zero==187
    assert (n_full>1).sum()==926 and (n_use>1).sum()==922
    clinical=p.p0b_claim_gate(s)
    all_counts=dict(zip(METHODS,np.asarray(s.method_presence,dtype=int).sum(axis=0).astype(int).tolist()))
    out={
      "schema":"htt.r87.actual_CDS_CF4_method_overlap_PV_sensitivity_spatial_holdout/1",
      "science_node":"SQ-CF4",
      "R78_science_state_unchanged":True,
      "source_sha256":s.source_sha256,
      "source_array_canonical_bytes_sha256":s.source_array_fingerprint,
      "selected_original_group_count":len(s.group_id),
      "original_released_group_count":len(gids),
      "selected_group_ID_sha256":__import__("hashlib").sha256(
           np.ascontiguousarray(s.group_id.astype("<i8")).tobytes()).hexdigest(),
      "original_selected_method_family_counts":s.selected_family_counts,
      "seven_original_method_presence_counts":all_counts,
      "seven_method_original_pair_overlap_matrix":pairs.tolist(),
      "original_multi_method_presence_group_count":int(np.sum(n_full>1)),
      "usable_six_methods_with_released_positive_error_multigroup_count":int(np.sum(n_use>1)),
      "zero_seven_original_method_flags":raw_presence_zero,
      "zero_six_usable_method_modulus_with_errors":noncal_zero,
      "CAL_only_source_group_IDs":s.group_id[(n_full>0)&(n_use==0)].tolist(),
      "seven_presence_multiple_but_six_methods_only_one_with_errors_IDs":s.group_id[(n_full>1)&(n_use==1)].tolist(),
      "published_CAL_modulus_without_per_CAL_uncertainty_count":int(np.sum(np.isfinite(s.CAL_modulus))),
      "six_methods_with_released_errors":list(s.method_names),
      "method_modulus_input_semantics":s.raw_method_field_role,
      "source_group_projected_method_fit":{
          "chosen_gauge":"SNIA=0; source coordinate only, not absolute zero-point reference posterior",
          "fisher6":info["F"].tolist(),
          "score6":info["b"].tolist(),
          "fisher_null_constant_maxabs":info["fisher_null_one_max"],
          "source_six_method_overlap_graph_rank":info["rank_effective"],
          "supported_distinct_groups":info["n_distinct_supported_groups"],
          "relative_method_residual_mag":info["delta_mag"].tolist(),
          "working_conditional_sigma_mag":np.sqrt(np.diag(info["cov_working_mag2"])).tolist(),
          "working_law":"Within-group per-method conditional independent quoted errors; method residual after CF4 upstream global MCMC calibration. Not an independent raw calibration covariance or astronomical confidence interval"},
      "heldout_disjoint_group_sky_quadrants":held,
      "source_selected_vs_released_footprint_RA_quadrants":footprint,
      "source_selected_vs_released_inclusion_method":inclusion_by_method,
      "source_conditional_correlated_PV_low_rank_scenarios":pv,
      "identification_obstruction":{
        "same_group_method_contrasts_cancel":"actual group distance, common group peculiar velocity, any common group shift",
        "physical_C_components":{
           "Nstat":"only working diagonal from CF4 quoted e_DMzp after conversion; actual cross-method/error independence not established",
           "S_PV":"source positions and assumed low-rank bulk/shear scenarios; independently calibrated cosmological ensemble is NOT provided",
           "J_cal_Sigma_cal_J_cal_T":"post-intercalibrated method contrast residuals do NOT identify upstream zero-point posterior or exact CF4 MCMC-to-grouped response",
           "C_selection":"selected-vs-released angular/method analysis footprint measured, but survey completeness covariance is NOT provided"},
        "sky_heldout":"four RA quadrants are disjoint groups but original CF4 products globally intercalibrated; not statistically independent zero-point calibration or physical coverage",
        "true_physics_Pi":None,
        "normal_frame_physical_shear":None,
        "r78_SQ_CF4_gate":"still source-conditional only, not fully science-qualified"},
      "claim_gate":clinical,
      "no_synthetic_source_for_missing_blocks":True,
      "scientific_result_tier":"SOURCE_REAL_METHOD_OVERLAP_AND_SKY_OUT_OF_SAMPLE_DIAGNOSTIC_NUMERICALLY_CHECKED; FULL_PV_CAL_SELECTION_C_BLOCKED"
    }
    return out


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=OUTPUT)
    parser.add_argument("--print",action="store_true")
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"create-only output exists: {args.output}")
    result=summary()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(serialize(result),indent=2,ensure_ascii=False,allow_nan=False)+"\n")
    print(json.dumps({
     "source_N":result["selected_original_group_count"],
     "table3_multimethod":result["original_multi_method_presence_group_count"],
     "usable_contrast_groups":result["usable_six_methods_with_released_positive_error_multigroup_count"],
     "rank":result["source_group_projected_method_fit"]["source_six_method_overlap_graph_rank"],
     "mean_residuals":result["source_group_projected_method_fit"]["relative_method_residual_mag"],
     "skyfold_loss_differences":[row["heldout_predictive_loss_difference"] for row in result["heldout_disjoint_group_sky_quadrants"]["folds"]],
     "PV_H03_beta_shift":[row["working_H03_beta9_maxabs_difference"] for row in result["source_conditional_correlated_PV_low_rank_scenarios"]],
     "gate":result["claim_gate"]["P0_B_physics_status"]
    },ensure_ascii=False))
if __name__=="__main__":main()
