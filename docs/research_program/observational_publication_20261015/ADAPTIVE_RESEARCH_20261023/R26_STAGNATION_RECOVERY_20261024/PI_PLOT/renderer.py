"""Plot-only rendering of frozen Pi arrays. No estimation or new draws."""
from pathlib import Path
import hashlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path(__file__).resolve().parent
SOURCE=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/CONTINUATION_20261018/P1/results/FUNCTIONAL_SENSITIVITY_RESULT.json')
EXPECTED='80792f508bd2be07fae153f662c9726ce5dc0ddabf78ea15ef66a0d27219355b'
b=SOURCE.read_bytes();assert hashlib.sha256(b).hexdigest()==EXPECTED
j=json.loads(b);pi=j['physical_functionals']['Pi'];paired=SOURCE.parent/'paired_functional_arrays.npz'
with np.load(paired,allow_pickle=False) as f:
 ids=f['sample_id'].tolist();weights=f['weights'].tolist()
 assert len(ids)==2048 and len(set(ids))==2048
 assert all(w==1/2048 for w in weights) and sum(weights)==1
 reasons={key:dict(zip(*[x.tolist() for x in np.unique(f[key],return_counts=True)])) for key in ('physical_Q_reason','physical_F_G_reason')}
 assert all(np.isnan(f[k]).all() for k in ('physical_x','physical_Q','physical_F','physical_G_F'))
assert j['physical_functionals']['unknown_mass']==1
plt.rcParams.update({'font.size':11,'axes.titlesize':13,'pdf.fonttype':42,'savefig.facecolor':'white'})
fig,axes=plt.subplots(1,3,figsize=(13.4,6.2),sharey=True)
checks=[]
for ax,key,title,reason in zip(axes,('Q','F','G_F'),(r'$\Pi_Q$',r'$\Pi_F$',r'$\Pi_{G_F}$'),('Unmeasured-defined','Domain uncertified','Domain uncertified')):
 d=pi[key];x=np.asarray(d['thresholds']);lo=np.asarray(d['lower']);hi=np.asarray(d['upper'])
 assert d['unknown_mass']==1 and d['known_mass']==0
 # Segments and endpoint artists consume the saved arrays directly.
 seg=ax.vlines(x,lo,hi,color='#28668a',lw=3,zorder=2)
 lower,=ax.plot(x,lo,'_',ms=19,mew=2,color='#28668a',label='Saved lower / upper')
 upper,=ax.plot(x,hi,'_',ms=19,mew=2,color='#28668a')
 np.testing.assert_array_equal(lower.get_xdata(),x);np.testing.assert_array_equal(lower.get_ydata(),lo)
 np.testing.assert_array_equal(upper.get_xdata(),x);np.testing.assert_array_equal(upper.get_ydata(),hi)
 for i,s in enumerate(seg.get_segments()):np.testing.assert_array_equal(s,np.array([[x[i],lo[i]],[x[i],hi[i]]]))
 checks.append({'functional':key,'thresholds':d['thresholds'],'lower':d['lower'],'upper':d['upper'],'artist_arrays_exact':True,'segment_arrays_exact':True})
 ax.set(title=title+'\n'+reason,xlabel='Threshold t (saved values)',xticks=x,xlim=(-.08,1.08),ylim=(-.06,1.08),yticks=[0,.25,.5,.75,1])
 ax.grid(axis='y',alpha=.22);ax.text(.5,.5,'Unknown mass = 1\nKnown mass = 0',transform=ax.transAxes,ha='center',va='center',bbox={'facecolor':'white','edgecolor':'none','alpha':.9})
 if key=='F':ax.text(.5,-.30,'t = 1: saved upper = 1 is conservative;\nnot physically sharp for F in [0, 1].',transform=ax.transAxes,ha='center',va='top',fontsize=9)
 if key=='G_F':ax.text(.5,-.30,r'$G_F$ is not a depth measurement.',transform=ax.transAxes,ha='center',va='top',fontsize=9)
axes[0].set_ylabel(r'Strict-tail finite-law mass $\Pi_Z(t)$: saved interval')
fig.suptitle('unrestricted mathematical-completion diagnostic outer envelope;\nphysical completion unqualified',fontsize=15,y=.97)
fig.subplots_adjust(left=.07,right=.98,bottom=.32,top=.76,wspace=.20)
fig.text(.5,.105,r'Full context: $x, F, \Pi, Q, G_F$; $x_C$ unmeasured. All 2048 original joint IDs and exact weights retained.',ha='center',fontsize=10)
fig.text(.5,.065,'One coupled four-window source; unknown mass is not renormalized. No calibrated posterior or sharp physical-set claim.',ha='center',fontsize=9)
fig.text(.5,.025,'Owner: HTT research diagnostics | diagnostic-only | transfer: none | null: unqualified | covariance: inherited conditional working law',ha='center',fontsize=8)
fig.savefig(OUT/'PI_INTERVALS.png',dpi=180)
fig.savefig(OUT/'PI_INTERVALS.pdf',metadata={'Title':'Saved Pi diagnostic outer envelopes','Subject':'Physical completion unqualified; source-bound plot only'})
plt.close(fig)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
metadata={'source':str(SOURCE),'source_sha256':EXPECTED,'json_pointer':'/physical_functionals/Pi','paired_source':str(paired),'paired_source_sha256':hashlib.sha256(paired.read_bytes()).hexdigest(),'joint_unit':j['joint_unit'],'sample_id':ids,'weights':weights,'sample_count':2048,'weight_sum':1,'unknown_mass':1,'physical_functionals':j['physical_functionals'],'missing_reason_counts':reasons,'plotted_arrays':checks,'owner':j['owner'],'claim_tier':'diagnostic_only','artifact_mode':'PLOT_ONLY_SAVED_ARRAY_RENDER','allowed_use':'Inspect saved unrestricted mathematical-completion diagnostic outer envelopes only','transfer_source':j['transfer_source'],'null_status':'PHYSICAL_COMPLETION_UNQUALIFIED','covariance_status':j['covariance_assumption'],'forbidden_uses':['calibrated physical posterior','sharp physical set','native solver or family identification','depth measurement from G_F','scalar replacement of full tensor source'],'new_fits':0,'new_draws':0,'new_threshold_searches':0}
(OUT/'SOURCE_CAPTION_METADATA.json').write_text(json.dumps(metadata,indent=2))
print(json.dumps({'status':'RENDERED_ARRAYS_EXACT','panels':3,'figure_count':1,'formats':['png','pdf'],'ids_retained':len(ids),'exact_weight_each':1/2048,'missing_reasons':reasons,'new_fits':0,'new_draws':0}))
