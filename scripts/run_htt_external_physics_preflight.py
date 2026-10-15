#!/usr/bin/env python3
"""Seven blocked external-physics HTT tasks: factual source preflight.

Does not change actual DAG state, fabricate source data, count theoretical
one-event transport as native global Bianchi atlas, or infer availability
from file names. Identifies useful already local artifacts and EXACT missing
data/physics contract for each externally blocked publication task.

This can run independently alongside the P1 S02 finite FFP10 source runner.
Only local path/small file hashes and actually checked data metadata.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OWNER=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
REC=Path("/home/cosmosapjw/Dropbox/bianchi/rec_bianchi")
REI=Path("/home/cosmosapjw/Dropbox/bianchi/rei_bianchi")
PUB=ROOT/"docs/research_program/observational_publication_20261015"
DAG=PUB/"PUBLICATION_DAG.json"

# These are concrete existing work products, NOT qualification certificates.
CANDIDATES={
 "S04":[("legacy original and functional engine",ROOT/"htt/obsstat/publication_functionals.py"),
        ("Planck real conditional physical-unknown source",PUB/"results/S02_real_planck_typed_partial_v1/result.json"),
        ("K02 CF4 physical transfer degeneracy",PUB/"results/K02_cf4_transfer_uncertain_v1/result.json")],
 "L03":[("FFP10 999/300 selected-map compact bank",OWNER/"workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz"),
        ("Planck actual native-mask gate",ROOT/"docs/research_program/htt_mes_eps_loop9_20261015/results_v2/result.json"),
        ("999 source forward high-l nuisance exact operator",ROOT/"htt/obsstat/masked_schur_highl_temperature.py")],
 "H02":[("35,970 CF4 grouped source",ROOT/"docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"),
        ("observed CF4 method sensitivity",PUB/"results/H02_cf4_method_calibration_v2/result.json"),
        ("CF4 source flat-LCDM response",PUB/"results/H02_flrw_method_decomposition_v2/result.json")],
 "V03":[("observer one-event Lorentz frame transport",ROOT/"htt/obsstat/finite_boost_observer_frame.py"),
        ("recombination 1-event photon-screen Rust source",REC/"rust/rec_microphysics/src/screen.rs"),
        ("recombination 1-event physical frame Rust source",REC/"rust/rec_microphysics/src/frame.rs")],
 "B02":[("recombination photon screen polarization",REC/"rust/rec_microphysics/src/screen.rs"),
        ("recombination frame photon",REC/"rust/rec_microphysics/src/frame.rs"),
        ("Planck spin 2 actual observation",ROOT/"htt/obsstat/planck_spin2_source_response.py")],
 "K03":[("K01 covariant photon local energy transport",ROOT/"htt/obsstat/covariant_optical_kinematics.py"),
        ("K02 actual CF4 transfer null",PUB/"results/K02_cf4_transfer_uncertain_v1/result.json"),
        ("recombination exact photon local screen",REC/"rust/rec_microphysics/src/screen.rs")],
 "K04":[("K01 exact one-event physical operator",PUB/"results/K01_covariant_optical_CF4_Planck_v1/result.json"),
        ("K02 conditional actual CF4 transfer",PUB/"results/K02_cf4_transfer_uncertain_v1/result.json"),
        ("actual CF4 source method stress",PUB/"results/H02_cf4_method_calibration_v2/result.json")]
}
REQUIRED={
 "S04":{"missing":"A common-congruence joint physical posterior OR a qualified source-validated narrower identified functional with signed x sectors","next_work":"derive observationally selected partial-ID law with exact unknown-sector support; do not use processing maps as independent posterior","release_type":"physical posterior/source-validated identification interval"},
 "L03":{"missing":"End-to-end Planck component-separation matched CMB+noise+foreground beam/filter null, with exchangeable simulations and predeclared statistic family","next_work":"verify raw source null simulation IDs and reproduce actual masks, foreground/split frequency and release-effective transfer for the selected low-ell statistic","release_type":"simulated foreground/beam/noise and Planck release effective transfer"},
 "H02":{"missing":"CF4 true method calibration and group selection law plus angular-depth correlated peculiar velocity covariance and injection coverage","next_work":"request group-level selection/completeness and calibration covariance or prepare velocity-field simulation with exact group IDs and cosmological mock provenance","release_type":"CF4 survey calibration + peculiar velocity covariance and selection"},
 "V03":{"missing":"Validated global radiation–matter tilted Bianchi history integrated from emission through scattering and source frame to observed T/E/B","next_work":"audit rec_bianchi/rei_bianchi existing one-event screen and recombination code against all-m Bianchi photon line-of-sight and create physical history unit-gated interface","release_type":"global-tilt source-history transfer and proper tetrad/clock IC"},
 "B02":{"missing":"Bianchi I–IX and VI_-1/9 native polarized all-m high-ell Einstein–Boltzmann atlas, checked IC/BC, curvature sign and recombination","next_work":"run per-family validation manifest against rec_bianchi/rei_bianchi physical source and identify verifiable subset, not treating a local screen kernel as full atlas","release_type":"native T/E/B sky transfer atlas + source physical solver"},
 "K03":{"missing":"Nonradial observable carrying vorticity curl, acceleration and matter–radiation tilt with source/selection covariance and shared frame","next_work":"derive proper-motion and polarization/gradient projection candidates with actual units and assign required survey release and frequency/redshift coverage","release_type":"source-matched nonradial vector/curl and acceleration channels"},
 "K04":{"missing":"Physical 1+3 optical luminosity-distance response and CF4 method/peculiar velocity/selection covariance; H04 must be qualified","next_work":"preserve rank-zero sectors as unbounded; construct forward operator in shared u^a once actual H04 calibration passes","release_type":"physical 1+3 light-cone/survey joint likelihood"}
}


def sha_small(p:Path):
    if not p.is_file() or p.stat().st_size>7*1024*1024:
        return None
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(path):
    p=subprocess.run(["git","-C",str(path),"rev-parse","HEAD"],
                      text=True,capture_output=True,check=False)
    return p.stdout.strip() if p.returncode==0 else "UNAVAILABLE"


def run(out:Path):
    if out.exists():raise FileExistsError("preflight results immutable create-only")
    dag=json.loads(DAG.read_text())
    blocked={z["id"]:z for z in dag["nodes"] if z["external_missing"]}
    if set(blocked)!=set(REQUIRED) or set(blocked)!=set(CANDIDATES):
        raise RuntimeError("frozen seven scientifically external blocked task IDs changed")
    rows={}
    for id_,node in blocked.items():
        files=[]
        for label,path in CANDIDATES[id_]:
            v={"label":label,"path":str(path),"exists":path.is_file(),
               "size_bytes":path.stat().st_size if path.is_file() else None,
               "sha256_if_less_than_7MiB":sha_small(path)}
            files.append(v)
        rows[id_]={
          "paper":node["paper"],
          "objective":node["objective"],
          "authoritative_DAG_state":node["state"],
          "authoritative_DAG_external_missing":node["external_missing"],
          "authoritative_dependencies":node["depends_on"],
          "local_candidate_artifacts":files,
          "count_local_existing_artifacts":sum(p["exists"] for p in files),
          "qualified_real_physical_source_satisfied":False,
          "preparation":REQUIRED[id_],
          "source_type_policy":"candidate present != physically qualified delivered observable",
          "next_execution_when_source_available":
              "run exact source-byte + timestamp + IC + response + independent convergence/coverage tests",
        }
    assert all(not z["qualified_real_physical_source_satisfied"] for z in rows.values())
    result={
       "schema":"htt.seven_external_blocked_source_input_preflight/1",
       "date_KST":"2026-10-15",
       "current_observational_source_commit":git_head(ROOT),
       "original_owner_checkout_HEAD":git_head(OWNER),
       "external_physical_repo_heads":{
          "rec_bianchi":git_head(REC),"rei_bianchi":git_head(REI)},
       "external_blocked_node_count":7,
       "real_physical_qualified_new_sources":0,
       "local_candidates_existing_count":sum(v["count_local_existing_artifacts"] for v in rows.values()),
       "blockers":rows,
       "scientific_admission":"PREPARATORY_SOURCE_DISCOVERY_NOT_BLOCKER_RESOLUTION",
       "no_DAG_status_modified_by_preflight":True,
       "scope":"prepare executable external source checklists in parallel with substantive S02",
    }
    out.mkdir(parents=True)
    (out/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    (out/"NEXT_EXTERNAL_INPUTS_KO.md").write_text(
        "# 외부 물리·관측 입력 7개 병렬 준비 상태\n\n"
        "이 문서는 기존 DAG를 수정하지 않으며 local source 후보와 필요한 물리 입력을 "
        "바이트·파일 존재 여부로 분리해 기록한다. "
        "원격 재결합/재이온화 저장소의 local code 존재가 곧 올바른 global-tilt "
        "수송이나 Bianchi 모든 가족 T/E/B atlas 완료라는 뜻은 아니다.\n\n"+
        "\n".join(f"**{k} ({v['paper']})**: 기존 source 파일 후보 "
                  f"{v['count_local_existing_artifacts']}/{len(v['local_candidate_artifacts'])}개. "
                  f"미해결: {v['preparation']['missing']}. "
                  f"준비 경로: {v['preparation']['next_work']}."
                  for k,v in rows.items())+
        "\n\n사용되는 파일과 HEAD 및 실제 후속 검증 요구는 result.json 참고.\n",
        encoding="utf-8")
    print("EXTERNAL_PREFLIGHT_SEVEN",len(rows),
          "CANDIDATES_PRESENT",result["local_candidates_existing_count"],
          "SOURCE_PHYSICS_QUALIFIED",result["real_physical_qualified_new_sources"],flush=True)
    return result


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    run(args.output_dir)
