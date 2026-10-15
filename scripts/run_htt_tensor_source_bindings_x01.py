#!/usr/bin/env python3
"""X01: actual six-paper source-overlap identities and tensorized blocked inputs.

Read the tracked 2026-10-15 research sources and the original historical
PR lineage. Distinguish:
 - identical raw/simulation map vs same CMB sky processing variants;
 - source CF4 35,970 groups vs 24 selected SNe with unverified join;
 - theoretical tensor forward response from observed source statistic;
 - untracked legacy owner checkout vs frozen Git history.

This is a SOURCE BINDING/OVERLAP record, not a CMB+CF4 common-congruence
physical likelihood, external dataset creation or a journal result.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/"docs/research_program/observational_publication_20261015"
OWNER=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
REC=Path("/home/cosmosapjw/Dropbox/bianchi/rec_bianchi")
REI=Path("/home/cosmosapjw/Dropbox/bianchi/rei_bianchi")
PR=PUB/"legacy_modern_obs_integration_20261015/INDEPENDENT_OBSERVATION_PR_CROSSWALK.json"
DESIGN=PUB/"SOURCE_CROSSWALK_AT_DESIGN.json"
TENSOR=PUB/"results/X01_tensorized_stf_planck_ffp999_v2/result.json"
PR_REFS={"PR254":"8aa8d7357","PR255":"d70ad4c7f",
         "PR256":"5867fae35","PR257":"81ab84fc4",
         "PR258":"926ae2de5","PR262":"d567bdcef",
         "PR264":"e5670e969"}


def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for part in iter(lambda:f.read(4<<20),b""):h.update(part)
    return h.hexdigest()


def git(repo,*args):
    return subprocess.check_output(["git","-C",str(repo),*args],
                                   text=True,stderr=subprocess.DEVNULL).strip()


def run(out:Path):
    if out.exists():raise FileExistsError("source graph create-only")
    t=json.loads(TENSOR.read_text())
    d=json.loads(DESIGN.read_text())
    pr=json.loads(PR.read_text())
    if (t["physical_real_CMB_sky_count"]!=1
        or t["FFP10_unique_CMB_source_realizations"]!=999
        or t["FFP10_noise_same_ID_pairs"]!=300
        or pr["scientific_joint_likelihood_admitted"] is not False):
        raise RuntimeError("source graph scientific identities do not match")
    # Local Git staged tracked? New tensor file is not tracked before commit.
    pathrefs={
       "P_CMB_OBS":("docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz",
         "Planck PR3 same one sky","nine correlated component-separated T l2..5 observations"),
       "P_CMB_K1":("docs/research_program/observational_publication_20261015/results/L01_schur_999cmb_300noise_v2/source_lowell_nested_999plus300.npz",
         "One observed masked SMICA K1 and fixed FFP10 999+300",
         "same source 999 simulation maps, paired noise first300 IDs"),
       "P_CMB_SIM":("docs/research_program/htt_mes_eps_loop9_20261015/results_v2/conditional_ffp10_eps_samples.npz",
         "FFP10 999 same common T mask", "simulated conditional eps2/eps3 not physical shear"),
       "CF4_GROUPS":("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz",
         "Cosmicflows-4 35970 grouped catalog", "J2000 redshifts/distances/method labels, one observed catalogue"),
       "CF4_STF_METHOD":("docs/research_program/observational_publication_20261015/results/K02_cf4_transfer_uncertain_v1/result.json",
         "CF4 35970 apparent STF", "same CF4 dataset with conditional unverified transfer scenarios"),
       "LEGACY_R2":("docs/research_program/observational_publication_20261015/legacy_modern_obs_integration_20261015/ORIGINAL_LEGACY_SOURCE_LINEAGE.json",
         "Archived actual legacy source", "byte-preserved hypothesis not observation"),
       "TYPEFREE":("htt/src/common/typefree_functionals.py",
         "PR262 typefree functionals actual current implementation",
         "typed gauge, support, finite joint images and undefined mass"),
       "TENSOR_STF":("htt/obsstat/planck_lowell_irrep_projection.py",
         "Planck real harmonic to Galactic rank2/rank3 STF",
         "not a covariant spacetime shear tensor"),
       "OBSERVER_BOOST":("htt/obsstat/finite_boost_observer_frame.py",
         "one-event local Lorentz transformation",
         "not global R-M source tilt transfer"),
       "K01_OPTICAL":("htt/obsstat/covariant_optical_kinematics.py",
         "one-congruence covariant photon energy loss",
         "not observed CF4 luminosity distance redshift kernel"),
    }
    sources={}
    for name,(rel,release,scope) in pathrefs.items():
        p=ROOT/rel
        if not p.is_file():raise FileNotFoundError(p)
        sources[name]={
          "id":name,"relative_path":rel,"sha256":sha(p),"bytes":p.stat().st_size,
          "release_or_source":release,"estimator_and_scope":scope,
          "is_current_path_tracked":bool(git(ROOT,"ls-files",rel)),
          "actual_scientific_source_present":True,
          "joint_physical_likelihood_qualified":False,
        }
    # Verify the actual 489MB FFP10 K1 bank without copying it to Git:
    # this releases a SHA-pinned *file identity*, NOT a model likelihood.
    raw=OWNER/"workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz"
    raw_sha=sha(raw)
    expected="86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb"
    if raw_sha!=expected:
        raise RuntimeError("original 489MB FFP10 K1 cohort bytes changed")
    sources["K1_FFP10_RAW"]={
       "id":"K1_FFP10_RAW","external_absolute_path":str(raw),
       "sha256":raw_sha,"bytes":raw.stat().st_size,
       "release_or_source":"original FFP10 K1 compact source bank",
       "estimator_and_scope":"999 CMB signal and first300 same-ID noise source masks; not a physical null exchangeability proof",
       "is_current_path_tracked":False,
       "actual_scientific_source_present":True,
       "joint_physical_likelihood_qualified":False}
    original=[]
    for row in d["records"]:
        rel=row["relative_path"]
        base=OWNER if row["authority"]=="LOCAL_ONLY_UNTRACKED_AT_REDESIGN" else ROOT
        path=base/rel
        obj={
          "historical_source_id":row["id"],"relative_path":rel,
          "authority":row["authority"],"historical_sha256":row["sha256_checked_20261015"],
          "actual_readable_now":path.is_file(),
          "scientific_scope":row["scientific_scope"],
          "new_measurement":row["new_measurement"]
        }
        if path.is_file():
            obj["observed_now_sha256"]=sha(path)
            obj["content_equal_to_original_snapshot"]=(obj["observed_now_sha256"]==obj["historical_sha256"])
        original.append(obj)
    if len(original)!=9 or any(x["new_measurement"] for x in original):
        raise RuntimeError("immutable 9-source historical record contract")
    prs={key:git(OWNER,"rev-parse",value) for key,value in PR_REFS.items()}
    overlaps=[
      {"left":"P_CMB_OBS","right":"P_CMB_K1","relation":"SAME_COSMOLOGICAL_CMB_SKY_DISTINCT_PROCESSED_PRODUCTS","independent_likelihood":False},
      {"left":"P_CMB_K1","right":"P_CMB_SIM","relation":"SHARED_FFP10_999_CMB_SOURCE_IDS_AND_SAME_MASK_GATE","independent_likelihood":False},
      {"left":"K1_FFP10_RAW","right":"P_CMB_K1","relation":"EXACT_SAME_K1_FFP10_SIMULATION_BANK_AND_REGISTERED_999_IDS","independent_likelihood":False},
      {"left":"P_CMB_K1","right":"P_CMB_K1_FIRST300_NOISE","relation":"NOISE_FFP10_300_PAIRED_BY_IDENTICAL_SOURCE_ID","independent_likelihood":False},
      {"left":"CF4_GROUPS","right":"CF4_STF_METHOD","relation":"SAME_35970_GROUPS_AND_SOURCE_SELECTION","independent_likelihood":False},
      {"left":"CF4_GROUPS","right":"PR532_CF4_SELECTED_24_SNIa","relation":"SAME_PARENT_CATALOGUE_ID_JOIN_UNVERIFIED","independent_likelihood":"UNKNOWN"},
      {"left":"P_CMB_OBS","right":"CF4_GROUPS","relation":"DIFFERENT_OBS_SOURCES_SHARED_COSMOLOGICAL_CONGRUENCE_TRANSFER_AND_COVARIANCE_MISSING","independent_likelihood":"NOT_ADMITTED"},
      {"left":"P_CMB_OBS","right":"PR531_SMICA_SCATTER","relation":"SAME_CMB_SKY_AND_SHARED_FFP10_K1_BANK","independent_likelihood":False},
      {"left":"P_CMB_OBS","right":"PR532_PLANCK_9_PRODUCTS","relation":"EXACT_SAME_ONE_CMB_SKY","independent_likelihood":False},
    ]
    papers={
      "P1":{"sources":["LEGACY_R2","TYPEFREE","P_CMB_OBS","P_CMB_SIM","K1_FFP10_RAW","CF4_GROUPS"],
            "estimand":"functional-indexed tensor x_phi / anchor Q / directional F / finite-source Pi / depth orbit G_F",
            "missing":"physical full 1+3 sigma,omega,A,beta,curvature common-congruence posterior, actual depth transfer"},
      "P2":{"sources":["P_CMB_OBS","P_CMB_SIM","K1_FFP10_RAW","TENSOR_STF"],
            "estimand":"STF2/STF3 temperature and E/B covariance, morphology/parity and masked transfer",
            "missing":"full Planck release beam/foreground/noise, complete statistically valid end-to-end null"},
      "P3":{"sources":["CF4_GROUPS","CF4_STF_METHOD"],
            "estimand":"CF4 redshift/depth-dependent apparent STF response, covariance and selection",
            "missing":"physical peculiar-velocity correlated selection and method calibration covariance"},
      "P4":{"sources":["OBSERVER_BOOST","P_CMB_OBS","CF4_GROUPS"],
            "estimand":"observer O relative matter M and radiation R tensor response histories",
            "missing":"global R-M full history T/E/B source transfer and common selection/covariance"},
      "P5":{"sources":["TENSOR_STF","P_CMB_OBS","P_CMB_SIM"],
            "estimand":"Bianchi native family all-m T/E/B physical morphology response",
            "missing":"verified native polarized Bianchi all-family transfer atlas and IC constraints"},
      "P6":{"sources":["K01_OPTICAL","CF4_GROUPS","CF4_STF_METHOD","P_CMB_OBS"],
            "estimand":"physical 1+3 H/sigma_ab/omega_a/A_a/beta_a and joint response",
            "missing":"true optical light-cone transfer, nonradial observations and common source covariance"},
    }
    if set(papers)!={"P1","P2","P3","P4","P5","P6"}:
        raise RuntimeError("all six paper binding identities mandatory")
    if any(not all(s in sources for s in row["sources"]) or not row["missing"]
           for row in papers.values()):
        raise RuntimeError("all paper estimands need a source or typed missing physics")
    blockers=json.loads((PUB/"results/EXTERNAL_BLOCKED_PREFLIGHT_20261015_v2/result.json").read_text())
    contracts={
      "S04":{"tensor":"sigma_STF5 + omega_axial3 + A_polar3 + beta_RM3 + signed_curvature","missing":"physical joint latent source law for tensor functional image and typed curvature sector","available":"only CMB STF temperature + CF4 apparent STF, not physical shear"},
      "L03":{"tensor":"T/E/B all-m temperature+spin2 covariance source, masked support","missing":"real Planck end-to-end foreground+beam+noise+split exchangeable simulations","available":"FFP10 CMB 999 + noise300 same K1 source and 8 polarized processing alternatives"},
      "H02":{"tensor":"35970x35970 correlated C_vel+calibration, source dipole/STF and method selection","missing":"true group selection, depth-correlated velocity covariance and released calibration model","available":"35970 group full J2000+method, 5x5 apparent STF conditional Schur"},
      "V03":{"tensor":"beta_RM^a(z),beta_MO^a(z),full polarized radiation transfer","missing":"validated global tilt history/source emission+opacity T/E/B over Bianchi frames","available":"local observer boost and rec_bianchi one-event screen physics"},
      "B02":{"tensor":"all-m spin0/spin2 transfer for 11 Bianchi families + exceptional VI_-1/9","missing":"native full Einstein–Boltzmann polarized source atlas and physical IC/recombination","available":"STF2/STF3 Planck source and partial native rec_bianchi/rei_bianchi theory"},
      "K03":{"tensor":"nonradial proper-motion spin1 vorticity3 + acceleration3 + tilt3","missing":"actual matched transverse channel proper motions and correlated uncertainties","available":"radial CF4 35970 look directions and hypothetical tangent rank8 source preflight"},
      "K04":{"tensor":"common observer congruence response R_{ij}(z,n) for sigma5/omega3/A3/beta3","missing":"full light-cone geometry, H04 CF4 selection/covariance, physically supported posterior","available":"one-event K01 and apparent conditional CF4 K02"},
    }
    assert set(contracts)==set(blockers["blockers"])
    head=git(ROOT,"rev-parse","HEAD")
    result={
      "schema":"htt.X01_six_paper_tensorized_source_binding_graph/1",
      "date_KST":"2026-10-15",
      "parent_commit":head,
      "method_original_later_PR_commits":prs,
      "current_tensor_method_specification":"PR254/255/262/264 typed irrep anchors, response, functional image, not scalar x_C",
      "sources":sources,
      "historical_source_design_rechecked":original,
      "source_id_overlap_edges":overlaps,
      "historical_PR531_PR532_source_crosswalk_sha256":sha(PR),
      "PR531_PR532_exact_commit_source_results":pr["source_results"],
      "source_binding_per_six_papers":papers,
      "external_physics_tensor_requirements":contracts,
      "external_blockers_remain_open":7,
      "real_native_physics_source_qualified_now":0,
      "both_planck_and_CF4_real_sources_available":True,
      "same_cosmological_joint_likelihood_not_built":True,
      "statistical_tensor_outputs_are_empirical_irreps_not_physical_shear":True,
      "X01_completion_scope":"SIX_PAPER_SOURCE_PROVENANCE_OVERLAP_BINDINGS_ONLY",
    }
    out.mkdir(parents=True)
    (out/"SOURCE_BINDINGS.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    (out/"EXTERNAL_TENSOR_INPUTS.json").write_text(
       json.dumps({"schema":"htt.external_blocked_tensor_source_contract/1",
                   "date_KST":"2026-10-15",
                   "reference_external_preflight":"results/EXTERNAL_BLOCKED_PREFLIGHT_20261015_v2/result.json",
                   "physical_new_source_qualified":0,
                   "contracts":contracts},ensure_ascii=False,indent=2)+"\n")
    (out/"REPORT_KO.md").write_text(
      "# X01: 6개 논문 source 단위와 tensorized method 소유권\n\n"
      "PR254/255/256/257/258/262/264 원본 Git commits를 확인하고 PR262 typed "
      "STF2/STF3 통계량을 실제 Planck one sky 9처리+FFP10 999/300과 "
      "CF4 35970 group source overlap graph에 연결했다. 동일 Planck sky "
      "processing alternatives, raw K1 FFP bank와 999 simulation IDs, CF4 "
      "24 SNIa scenario와 부모 35970 group의 overlap 불확실성을 각각 typed "
      "source edge로 남겼다. 모든 6편의 estimand에 source+missing physics를 "
      "동시에 기재하였으며 실제 Planck-CF4 물리적 joint posterior는 없다.\n\n"
      "7 external blocker 노드별 tensor rank/frame/실제 source 필요조건과 "
      "준비자료는 EXTERNAL_TENSOR_INPUTS.json 참고. "
      "7개 물리적으로 해결된 입력은 여전히 0개.\n",encoding="utf-8")
    print("X01_TENSOR_SOURCE_GRAPH",
       "sources",len(sources),"edges",len(overlaps),
       "papers",len(papers),"blockers",len(contracts),
       "historical",len(original),
       "pr_history",len(prs),flush=True)
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args()
    run(args.output_dir)
