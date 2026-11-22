"""R96 explicit old-legacy science-source to maintained-result migration map.

Not another approval gate: a compact map of the old untracked prototype,
demonstrated defect, executable new successor and exact remaining physics
needed to reproduce its intended observable on actual data.
"""
from pathlib import Path
from hashlib import sha256
import json
ROOT=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
R=ROOT/"docs/research_program/observational_publication_20261015/R96_THREE_THEORY_LOOPS_20261122"
OUT=R/"LEGACY_RESCUE_CROSSWALK.json"
source=json.loads((R/"SOURCE_REUSE_AUDIT.json").read_text())["provenance_source_locks"]
def lock(name):
 return {"original_file":source[name]["path"],"original_sha256":source[name]["sha256"],
         "original_remains_intact":True}
def entry(old,defect,new,proof,remaining):
 return {**lock(old),"defect_or_limit":defect,
  "maintained_successor_code":new,
  "actual_verification":proof,
  "still_required_for_physics":remaining}
def build():
 return {"schema":"htt.r96.provenance_bound_legacy_repair_map/1",
  "authority":"original historical legacy files are untracked immutable-source intake; derived maintained successors are committed under scripts/r96",
  "entries":{
    "legacy_biposh_masked":entry("LEGACY_BIPOSH",
      "incorrect positive |a_lm|² A20 and fsky-only covariance; no off-diagonal L2 mask deconvolution",
      ["scripts/r96/legacy_biposh_recovered.py","scripts/r96/cmb_crossfit_null.py"],
      "original API names retained; exact Gaunt + 300 matched FFP10 MC bias/full covariance + LOO; 13 targeted tests",
      "independent same-release MC, mask/beam full injection, foreground and actual Bianchi TEB template"),
    "legacy_projected_multipoles":entry("LEGACY_PR13AG",
      "synthetic gamma/shear and m0 T/E only, not full physical coupled polarized Bianchi",
      ["scripts/r96/spin2_mblock_extension.py"],
      "spin recurrence 1.78e-16; sparse complex m=-2..2 T/E/B L=8,16,32,60; k=0/m0 B-parity null",
      "general Bianchi non-axisymmetric m-mixing and full electron/photon source from R49+REC+REI"),
    "legacy_CF4_bulkflow":entry("LEGACY_CF4",
      "old conditional method covariance not identical to H03 new working noise; source calibration prior ambiguity",
      ["scripts/r96/cf4_covariance_bridge.py"],
      "all 35970 CF4 groups, 3x5 model grid, separate R36/R95 source models, exact Woodbury/dense GLS parity",
      "independent pre-intercalibration zero points and full PV/selection covariance"),
    "legacy_Mayukh_catalog":entry("LEGACY_DOPPLER",
      "legacy exact SR z correction omitted gamma factor in same sign convention",
      ["scripts/r93/legacy_cf4_doppler.py","scripts/r96/cf4_covariance_bridge.py"],
      "real 35970 CF4 source beta correction and current covariance source checks, R93 and R96 tests",
      "true observer/source redshift catalogue and physical peculiar velocity forward model"),
    "legacy_pixel_lowl":entry("LEGACY_PIXEL",
      "historical pixel likelihood and masking assumptions not yet independent full anisotropic coupling verified",
      ["scripts/r95/planck_fullres_teb_analysis.py","scripts/r96/legacy_biposh_recovered.py"],
      "verified source-matched 999/300 PR3 SMICA processing and corrected L2 bias statistics",
      "specific pixel likelihood covariance and full release-matched Commander E2E null"),
  },
  "none_of_these_implies_published_Bianchi_family_detection":True}
if __name__=="__main__":
 if OUT.exists():raise RuntimeError("create-only")
 z=build()
 OUT.write_text(json.dumps(z,indent=2,ensure_ascii=False)+"\n")
 print("SOURCE_RESCUES",len(z["entries"]),list(z["entries"]))
