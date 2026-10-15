#!/usr/bin/env python3
"""Illustrative P1 finite functional image; SYNTHETIC atoms, not observed sky."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from obsstat.publication_functionals import finite_functional_image

def run(out:Path):
    if out.exists():raise FileExistsError("create-only P1 demonstration")
    source=[
        {"sample_id":"math-0","weight":2.,"congruence":"one-normal-frame",
         "components":{"Sigma2":.4,"W2":.6,"Omega_tilt":0.,"DeltaOmega_k":-.1},
         "U_sigma":.5,"sector_value":.25,"sector_ceiling":.5,
         "depth_F":{"reference":.5,"comparison":.3}},
        {"sample_id":"math-1","weight":1.,"congruence":"one-normal-frame",
         "components":{"Sigma2":.4,"W2":.1,"Omega_tilt":.1,"DeltaOmega_k":0.},
         "U_sigma":.4,"sector_value":.1,"sector_ceiling":.4,
         "depth_F":{"reference":.25,"comparison":.5}},
        {"sample_id":"math-2","weight":1.,"congruence":"one-normal-frame",
         "components":{"Sigma2":None,"W2":.05,"Omega_tilt":None,"DeltaOmega_k":.1},
         "U_sigma":None,"sector_value":None,"sector_ceiling":None,
         "depth_F":{"reference":None,"comparison":None}},
    ]
    result=finite_functional_image(source,thresholds=[-1.,-.61,0.,1.,2.],
        gf_floor=.01,common_congruence="one-normal-frame",
        reference_bin="low-z-demo",comparison_bin="high-z-demo")
    out.mkdir(parents=True)
    record={"schema":"htt.P1_S01_synthetic_math_oracle/1",
            "input_kind":"MANUFACTURED_THREE_ATOMS_NOT_OBSERVATIONAL_DATA",
            "source_sectors":"dimensionless invented test scalars; NOT a fitted GR state",
            "source_atoms":source,"finite_image":result,
            "claim":"MATHEMATICAL_CODE_TEST_NOT_COSMOLOGICAL_POSTERIOR",
            "rank_status":"NO_REAL_DATA_LIKELIHOOD"}
    (out/"result.json").write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n")
    tr=result["Pi_Q_strict_threshold_outer_intervals"]
    tx=[q["threshold"] for q in tr]
    lo=[q["unconditional_outer_interval"][0] for q in tr]
    hi=[q["unconditional_outer_interval"][1] for q in tr]
    fig,ax=plt.subplots(figsize=(7,4),layout="constrained")
    ax.step(tx,lo,where="post",label="known P(Q>t)")
    ax.step(tx,hi,where="post",label="known+undefined upper")
    ax.fill_between(tx,lo,hi,step="post",alpha=.2)
    ax.set(xlabel="synthetic threshold t for signed Q",
           ylabel="unconditional mass, NOT p-value",
           title="SYNTHETIC: finite Pi(t) with missing sectors (not observed)")
    ax.set_ylim(0,1.03);ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.savefig(out/"synthetic_strict_Pi_outer_interval.png",dpi=145)
    plt.close(fig)
    (out/"STAT_FUNCTIONAL_CONTRACT_KO.md").write_text(
        "# S01: x,F,Pi,Q,G_F 정의역 및 수치 검산\n\n"
        "서로 다른 물리적 의미를 가진 함수들을 구분하고 HTT joint finite atom의 "
        "signed/undefined mass를 보존하는 코드를 구현했다. 예시 데이터는 완전히 "
        "**합성된 세 원자**이므로 어떠한 실제 Planck/CF4 posterior, anisotropy 발견,"
        " model p-value도 추정하지 않는다.\n\n"
        "x_C=Sigma2-W2+Omega_tilt+DeltaOmega_k; Q=x_C/U_sigma, U_sigma>0 "
        "인 구역만 정의; Q는 total-x 물리적 포화율이 아니다. "
        "F=sector_value/sector_ceiling은 sign-clean 구역과 양의 sector bound를 요구한다. "
        "Pi_Q(t)=P(Q>t)는 strictly greater-than이며 정의되지 않은 Q의 원래 posterior "
        "질량을 지워 재정규화하지 않는다. "
        "G_F는 명시적 depth bins의 F mean과 사전 지정 floor δ로만 계산한다. "
        "F4=<T^4>/T0^4 볼로메트릭 모멘트는 F가 아니다.\n\n"
        f"합성 예시의 undefined Q mass={result['missing_mass']['Q']}; "
        f"G_F outer interval={result['G_F']['outer_interval']}. "
        "실자료 적용은 동일 physical likelihood와 sample IDs/cross-source covariance, "
        "공통 tetrad/curvature/frame가 식별된 경우만 observational claim으로 허용된다.\n",encoding="utf-8")
    print("S01_SYNTHETIC_ONLY_FINITE_IMAGE n",len(source),
          "undefined_Q",result["missing_mass"]["Q"],
          "GF",result["G_F"]["outer_interval"])
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",type=Path,required=True)
    a=parser.parse_args()
    run(a.output_dir)
