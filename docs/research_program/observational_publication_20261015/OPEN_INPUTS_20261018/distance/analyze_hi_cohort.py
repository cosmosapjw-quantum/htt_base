from pathlib import Path
from collections import Counter
import json,hashlib,argparse
parser=argparse.ArgumentParser()
parser.add_argument("--raw-root",type=Path,default=Path(__file__).parent)
parser.add_argument("--output-dir",type=Path,default=Path(__file__).parent)
args=parser.parse_args()
R=args.raw_root
O=args.output_dir
O.mkdir(parents=True,exist_ok=True)
expected={"cf4_hi_readme.observed":"bb5e9748e2b35d0dbc3271eb739913c1998a024fd00c2457bdf45d03ab83b7a7","cf4_hi_table2_plain.observed":"2e7e9f979aeb862ae59ac40b377953de7602c2574515b2c880c0b55cb838249c","cf4_hi_table4_plain.observed":"88e453c7c559f663fa61782707e4b47fdc2b752dcfda84d5dccd0d9103c4b8a3"}
aliases={'cf4_hi_readme.observed':'ReadMe','cf4_hi_table2_plain.observed':'table2.dat','cf4_hi_table4_plain.observed':'table4.dat'}
def source(name):
 return R/aliases[name] if (R/aliases[name]).exists() else R/name
for filename,digest in expected.items():
 assert hashlib.sha256(source(filename).read_bytes()).hexdigest()==digest, "source bytes mismatch: "+filename
lines2=source('cf4_hi_table2_plain.observed').read_text().splitlines()
lines4=source('cf4_hi_table4_plain.observed').read_text().splitlines()
assert len(lines2)==628 and len(lines4)==1274
assert all(len(s)==63 for s in lines2) and all(len(s)==32 for s in lines4)
t2=[dict(pgc=int(s[:7]),name=s[8:18].strip(),vhel=int(s[19:24]),v50=int(s[25:30]),w50=int(s[31:35]),e_w50=int(s[36:39]),sn=float(s[40:44])) for s in lines2]
t4=[dict(pgc=int(s[:7]),tel=s[8:14].strip(),vhel=int(s[15:20]),wmx=int(s[21:24]),e_wmx=int(s[25:27]),sn=float(s[28:32])) for s in lines4]
assert len({x['pgc'] for x in t2})==628 and len({x['pgc'] for x in t4})==1274
sets={k:{x['pgc'] for x in t2 if v(x)} for k,v in {'non_detection':lambda x:x['e_w50']==500,'confused':lambda x:x['e_w50']==100,'linewidth_error_le20':lambda x:x['e_w50']<=20,'other_detected_quality':lambda x:20<x['e_w50']<100}.items()}
gbt={x['pgc'] for x in t4 if x['tel']=='GBT'};nan={x['pgc'] for x in t4 if x['tel']=='Nancay'}
assert gbt==sets['linewidth_error_le20']
assert len(set.union(*sets.values()))==628 and sum(map(len,sets.values()))==628
result={'owner':'htt','scope':'fixed published 628-target GBT conditional outcome cohort and 1274-row contributor catalogue','claim_tier':'DIAGNOSTIC_ONLY','nodes':['H02','S02','K04'],'catalogue':'J/A+A/646/A113','source_identity':'2021A&A...646A.113D; official article aa39025-20; CDS ReadMe06-Jan-2021','counts':{'gbt_targets':628,'non_detection_e500':len(sets['non_detection']),'confused_e100':len(sets['confused']),'accepted_linewidth_error_le20':len(sets['linewidth_error_le20']),'detected_other_linewidth_quality':len(sets['other_detected_quality']),'detections_excluding_nondetection_and_confusion':628-len(sets['non_detection'])-len(sets['confused']),'table4_total':1274,'table4_gbt':len(gbt),'table4_nancay':len(nan),'table4_gbt_matches_accepted_target_set':gbt==sets['linewidth_error_le20']},'e_w50_histogram':dict(sorted(Counter(x['e_w50'] for x in t2).items())),'conditional_fractions':{k:len(s)/628 for k,s in sets.items()},'ids_by_outcome':{k:sorted(s) for k,s in sets.items()},'table4_telescope_ids':{'GBT':sorted(gbt),'Nancay':sorted(nan)},'schema_corrections':['CDS table4 actually exposes PGC,Tel,Vhel,Wmx,e_Wmx,S/N; no Source bibliography column despite journal illustrative table.','ReadMe descriptive paragraph says 685 adequate GBT measurements; impossible with628 total and contradicted by paper385, actual table4GBT385 and actual e_W50<=20set385; retain as upstream typo.','e_W50=500 is explicit non-detection,100 confused; these are sentinels, not ordinary errors.'],'closes':['Actual selected-target outcome ledger for bounded GBT programme628; contributor telescope identity for1274rows; exact accepted385 membership check.'],'does_not_close':['Global CF4 parent-target probability, all rejected survey ledger, intermethod calibration covariance, velocity law, optical-to-kinematic map.','GBT628 conditional fractions do not estimate targeting/detection completeness of CF4.','table4 no bibliography per-row source; Telescope does not identify full survey/version ancestry.'],'join_status':'NOT_RUN: existing source raw datasets absent in this scratch export; parent can join PGC against frozen J/ApJ/902/145 and CF4PGC/group maps.','checks':['628/1274counts','exact63/32columnwidths','uniquePGC','disjoint+exhaustive4outcomes','table4GBTset equals table2e_W50<=20set'],'source_files':[]}
# Avoid unverified DOI guess: source is identified by exact article and catalogue.
result['source_identity']='2021A&A...646A.113D; official article https://www.aanda.org/articles/aa/full_html/2021/02/aa39025-20/aa39025-20.html; CDS ReadMe06-Jan-2021'
for n in ['cf4_hi_readme','cf4_hi_table2_plain','cf4_hi_table4_plain']:
 p=source(n+'.observed');result['source_files'].append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(O/'HI_COHORT_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k in ['counts','conditional_fractions','schema_corrections','checks']},indent=2))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(8.5,4.6))
labels=['TF-acceptable\n(linewidth error ≤20)','Other detected\nquality','Confused\n(e=100 sentinel)','Non-detection\n(e=500 sentinel)']
values=[len(sets[k]) for k in ['linewidth_error_le20','other_detected_quality','confused','non_detection']]
bars=ax.barh(labels[::-1],values[::-1],color=['#9d4b4b','#b68133','#7e9fb4','#24688d'])
ax.bar_label(bars,padding=5)
ax.set_xlim(0,440);ax.set_xlabel('Number of galaxies in the 628 published GBT targets')
ax.set_title('Published GBT target outcomes: J/A+A/646/A113')
ax.spines[['top','right']].set_visible(False)
fig.text(.02,.025,'Conditional on the 628 observed targets. These counts do not estimate CF4 targeting completeness.',fontsize=9)
fig.tight_layout(rect=(0,.07,1,1))
for ext in ['png','pdf','svg']:fig.savefig(O/('HI_GBT_OUTCOMES.'+ext),dpi=180,bbox_inches='tight')
