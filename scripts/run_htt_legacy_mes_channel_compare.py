#!/usr/bin/env python3
"""Numerical source-specific legacy MES vs current geodesic bound bridge.

Loads exact archived R2 bounds.py + ssot.py through the reviewed R2
LegacyAdapter; compares with current conditional PR124 geodesic C1/C2
operator on the SAME nine processed CMB sky products, eps1=0 scenario.
The two physical theorem authorities have not been proven equivalent.
This is a numerical migration safety audit, NOT a physical upper limit.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from obsstat.legacy_mes_channel_comparison import compare_branch

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/"docs/research_program/observational_publication_20261015/legacy_modern_obs_integration_20261015"
R2_CODE=ROOT/"docs/observational_upgrade_r2/R2-04/sources/code"
INPUT=STUDY/"inputs/r2_htt"
PREVIOUS=ROOT/"docs/research_program/observational_publication_20261015/results/S02_real_planck_typed_partial_v1/result.json"
EXPECTED={
 "r2_bounds":"1c304927fe9f26636cda6cfadf647d439d9d6f7d5b5ca0900559338f5078c76d",
 "r2_ssot":"45ed08cf2fd9649e049c88cb50a3ced8d069fc07efb85c1ead398e3a6e8b8ad8",
 "r2_adapter":"36e38fc013c741b149a69d67478da27740a85003235fc70c1c154d6e35936629",
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def get_adapter():
    for key,path in (("r2_bounds",INPUT/"htt/bounds.py"),
                     ("r2_ssot",INPUT/"htt/ssot.py"),
                     ("r2_adapter",R2_CODE/"legacy_adapter.py")):
        if sha(path)!=EXPECTED[key]:
            raise RuntimeError(f"archived legacy methodology source SHA mismatch {key}")
    sys.path.insert(0,str(R2_CODE))
    from legacy_adapter import LegacyAdapter,AnalysisContract
    contract=AnalysisContract(
       contract_id="HTT_LEGACY_R2_VS_REGISTERED_MES_NO_PHYSICAL_EQUIVALENCE",
       congruence="GEODESIC_SCENARIO_ONLY",
       comparator_id="OLD_VS_CURRENT_OPERATORS_ON_THE_SAME_CMB_SOURCE",
       proof_scope_id="HISTORICAL_R2_AND_CURRENT_GEODESIC_C1C2_UNMATCHED",
       measure_id="ONE_PLANCK_PHYSICAL_SKY_NINE_PROCESSING_METHODS",
       multipole_definition="SAG1997_PSTF_L2_L3_RMS_NORM_SOURCE_CONDITIONAL")
    return LegacyAdapter(INPUT,contract)


def run(out:Path):
    if out.exists():raise FileExistsError("create-only methodology migration output")
    adapter=get_adapter()
    data=json.loads(PREVIOUS.read_text())
    if data["source_sky_realization_count"]!=1 or data["source_processing_product_count"]!=9:
        raise RuntimeError("same-sky Planck processing identities changed")
    rows={}
    for name,case in data["per_same_sky_source"].items():
        c=case["conditional_source_mes"]
        result=compare_branch(0.,c["eps2_source_projection"],
                              c["eps3_source_projection"],adapter)
        if not result["exact_numerical_Bsigma_agreement"]:
            raise RuntimeError("legacy-current Bsigma source normalization mismatch")
        if not np.isclose(
            1.5*result["historical_R2_legacy_Bsigma"]**2,
            float(c["U_sigma"]),rtol=2e-14,atol=0):
            raise RuntimeError("old and modern shared shear normalization failed")
        rows[name]=result
    items=list(rows)
    wr=np.asarray([rows[x]["historical_over_current_W2_ratio"] for x in items])
    if not np.isfinite(wr).all() or np.min(wr)<=0:
        raise RuntimeError("unexpected non-finite positive ratio on source Planck cases")
    out.mkdir(parents=True)
    result={
        "schema":"htt.legacy_vs_modern_MES_source_channel_mismatch/1",
        "date_KST":"2026-10-15",
        "claim":"METHOD_COMPARISON_ONLY_NON_EQUIVALENT_BOUND_AUTHORITIES",
        "all_observer_C1C2_claim":"UNVERIFIED",
        "eps1_intrinsic_dipole":"EQUAL_ZERO_MODEL_SCENARIO_NOT_A_MEASUREMENT",
        "per_source_same_physical_sky":rows,
        "source_processing_case_count":len(rows),
        "source_input_SHA256":sha(PREVIOUS),
        "legacy_input_identity":EXPECTED,
        "vorticity_old_over_new_norm_squared_ratio_minmax":[float(wr.min()),float(wr.max())],
        "vorticity_Bomega_ratio_minmax":[float(np.sqrt(wr.min())),float(np.sqrt(wr.max()))],
        "source_frame_assumption":"no demonstrated equivalence of legacy vs registered modern vorticity theorem coefficients",
        "physical_ranking_of_bounds":"WITHHELD",
        "legacy_accel_vs_current_structural_geodesic_accel":"NOT_SAME_SCOPED_ESTIMAND",
        "x_Q_Pi_F_GF_joint_posterior":"NOT_SUPPLIED",
    }
    (out/"result.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    fig,ax=plt.subplots(figsize=(10,4.4),layout="constrained")
    a=np.arange(len(items))
    old=np.array([rows[z]["historical_R2_legacy_W2_normalizer"] for z in items])
    new=np.array([rows[z]["current_geodesic_W2_normalizer"] for z in items])
    ax.semilogy(a,old,"o-",label="historical R2 B_omega^2 x(3/2), NOT admitted physically")
    ax.semilogy(a,new,"s-",label="modern registered conditional geodesic W2 anchor")
    ax.set_xticks(a,items,rotation=50,ha="right",fontsize=8)
    ax.set(xlabel="Same Planck sky, nine processing products",
           ylabel="Different algebraic conditional W² normalizers (dimensionless)",
           title="Legacy vs modern bound source-authority mismatch")
    ax.legend(fontsize=8);ax.grid(alpha=.3)
    fig.savefig(out/"legacy_modern_vorticity_authority_mismatch.png",dpi=145)
    plt.close(fig)
    (out/"REPORT_KO.md").write_text(
       "# Original R2 Legacy MES vs modern PR124 geodesic vorticity channel\n\n"
       "실제 Planck 같은 하늘 9개 처리 산출물의 동일 eps2/eps3를 두 "
       "원래 함수에 적용했다. Legacy 원본 R2 bounds.py/ssot.py는 "
       "source SHA로 고정해 R2 LegacyAdapter로 실제 로드했다.\n\n"
       "두 공식의 shear Bsigma는 기계오차 내 동일하지만, old Bomega="
       "(3/4)eps1+2eps2+(2/7)eps3와 modern geodesic Bomega="
       "(10/3)eps1+(2/15)eps2는 다른 공식이다. eps1=0 가정에서 "
       f"old/modern W2 upper-normalizer ratio range={result['vorticity_old_over_new_norm_squared_ratio_minmax']}.\n\n"
       "이 결과는 원래 legacy를 '오류'로 판정하거나 현대 theorem이 "
       "자동으로 물리적으로 옳다고 입증한 결과가 아니다. "
       "프레임, 미분 가정, vorticity 정의, 교정/원전 일치가 검증되지 "
       "않았으므로 같은 물리 제약으로 합치지 않는다. "
       "특히 legacy W2를 modern x/Q posterior의 추가 독립 likelihood나 "
       "동일한 normalizer로 넘기는 작업을 보류한다.\n",
       encoding="utf-8")
    print("LEGACY_MODERN_MES_COMPARISON_PASS",len(rows),"RATIO_W2",wr.min(),wr.max())
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",required=True,type=Path)
    a=p.parse_args()
    run(a.output_dir)
