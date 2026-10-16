"""Generate internal, non-claim-bearing finite Planck processed-image visuals."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def make(result_path,out):
 r=json.loads(Path(result_path).read_text());out=Path(out)
 if out.exists():raise FileExistsError('create-only plot directory')
 out.mkdir(parents=True)
 d=r['polarization_same_sky_differences']
 keys=list(d)
 X=np.arange(len(keys)); E=np.array([d[k]['E_norm_microK'] for k in keys]);B=np.array([d[k]['B_norm_microK'] for k in keys])
 fig,ax=plt.subplots(figsize=(10,4.5),layout='constrained')
 ax.bar(X-.2,E,width=.4,label='finite E processed contrast');ax.bar(X+.2,B,width=.4,label='finite B processed contrast')
 ax.set_xticks(X,[k.replace('_','\n') for k in keys],rotation=25,ha='right');ax.set_ylabel('Coefficient contrast norm [microK]');ax.set_title('One observed Planck sky, common polar mask: finite coefficients');ax.legend(fontsize=8)
 fig.savefig(out/'POLARIZED_EB_SAME_SKY_PROCESSING.png',dpi=160);plt.close(fig)
 cases=r['source_mask_mathematical_experiment']['statistics'];x=np.arange(len(cases));
 fig,ax=plt.subplots(figsize=(8.5,4.2),layout='constrained')
 ax.plot(x,[z['full_high_ell6_8_to_low_ell2_5_operator_norm'] for z in cases],marker='o',label='full (E,B) transfer')
 ax.plot(x,[z['B_low_from_E_high_norm'] for z in cases],marker='s',label='E high → B low')
 ax.set_xticks(x,[z['case'] for z in cases]);ax.set_ylabel('Induced operator norm');ax.set_title('Manufactured spin-2 sky: pixel support geometry sensitivity');ax.legend();ax.grid(alpha=.2)
 fig.savefig(out/'SYNTHETIC_SPIN2_MASK_LEAKAGE.png',dpi=160);plt.close(fig)

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--result',required=True);a.add_argument('--output',required=True);z=a.parse_args();make(z.result,z.output)
