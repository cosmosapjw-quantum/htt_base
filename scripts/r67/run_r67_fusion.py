from pathlib import Path
import argparse,json
from scripts.r67.fusion import run
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--cf4",type=Path,default=Path("/mnt/extdrive/workdir/raw/cf4_full"))
 p.add_argument("--out",type=Path,default=Path("docs/research_program/observational_publication_20261015/R67_SEVEN_AXIS_FUSION_20261118/RESULTS"))
 p.add_argument("--bootstraps",type=int,default=2048)
 p.add_argument("--seed",type=int,default=20261118)
 args=p.parse_args()
 r=run(args.cf4,args.out,args.bootstraps,args.seed)
 print(json.dumps({"pairs":{k:{"groups":v["overlap_groups"],"p_wild":v["wild_group_p_exploratory"],"rms_mag":v["full_sky_model_angular_rms_mag"]} for k,v in r["pairs"].items()},"network":{"groups":r["network"]["connected_group_count"],"triple_groups":r["network"]["triple_method_groups"],"rank":r["network"]["rank_all"],"p_wild":r["network"]["wild_group_p_exploratory"]}},indent=2))
if __name__=="__main__":main()
