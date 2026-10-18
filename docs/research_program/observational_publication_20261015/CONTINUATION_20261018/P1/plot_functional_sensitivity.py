"""Scientific figure generated solely from saved paired arrays and result JSON."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent


def plot():
    folder=ROOT/'results'
    result=json.loads((folder/'FUNCTIONAL_SENSITIVITY_RESULT.json').read_text())
    data=np.load(folder/'paired_functional_arrays.npz',allow_pickle=False)
    plt.rcParams.update({'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False,
                         'savefig.dpi':180,'font.family':'DejaVu Sans'})
    colors=['#355C9A','#C5522D','#2C826B','#7C559C']
    fig,axes=plt.subplots(2,2,figsize=(11.5,8.5))
    z=data['centers']; q=np.array(result['q_app_quantiles_05_50_95'])
    ax=axes[0,0]
    ax.errorbar(z,q[1],yerr=[q[1]-q[0],q[2]-q[1]],fmt='o',capsize=4,color=colors[0],
                label='Joint working-law median + 5–95% range')
    actual=result['actual_north_weighted_fit']
    ax.plot(z,actual['baseline_q_app'],'s--',color='#555555',ms=5,label='Original deterministic fit')
    ax.plot(z,actual['north_q_app'],'D-',color=colors[1],ms=5,label='North-weighted deterministic fit')
    ax.set(xlabel='Gaussian redshift-window center',ylabel=r'$A_j=\|s_j\|/H_j$',
           title='A  Actual-data summary and selection perturbation')
    ax.legend(fontsize=8,loc='upper left')
    ax.grid(alpha=.16)
    ax=axes[0,1]
    records=result['strict_exceedance'];t=[x['threshold'] for x in records]
    band=np.array([x['selection_envelopes']['2.0'] for x in records])
    ax.fill_between(t,band[:,0],band[:,1],color=colors[0],alpha=.2,label=r'Assumed normalized density bound $\Gamma=2$')
    ax.plot(t,[x['any_window'] for x in records],'o-',color=colors[0],ms=4,label='Coupled finite-law mass')
    ax.set(xlabel='Strict threshold t',ylabel=r'Mass of $\max_j A_j>t$',ylim=(-.03,1.03),
           title='B  Selection sensitivity of one joint event')
    ax.legend(fontsize=8,loc='upper right');ax.grid(alpha=.16)
    ax.text(.005,.08,'Physical x, Q, F, G remain unknown mass = 1',fontsize=8,color='#444444')
    ax=axes[1,0]
    floors=np.array([x['amplitude_floor'] for x in result['floor_depth_sensitivity']])
    for j,label in enumerate(['0.040 / 0.025','0.060 / 0.025','0.080 / 0.025']):
        vals=np.array([x['quantiles_05_50_95'] for x in result['floor_depth_sensitivity']])[:,:,j]
        ax.plot(floors,vals[:,1],'o-',color=colors[j+1],label=label,ms=4)
    ax.axhline(1,color='#777777',ls=':',lw=1)
    ax.set(xlabel=r'Effective floor $B\delta$ in $A$ units',ylabel='Median floored apparent depth ratio',
           title='C  Floor can erase apparent depth contrast')
    ax.legend(title='Comparison / reference z',fontsize=8,title_fontsize=8);ax.grid(alpha=.16)
    ax=axes[1,1]
    anchors=result['anchor_sensitivity']['anchors'];tails=np.array(result['anchor_sensitivity']['strict_mass_score_gt_1'])
    for j,center in enumerate(z):ax.plot(anchors,tails[:,j],'o-',color=colors[j],label=f'z = {center:.3f}',ms=4)
    ax.set(xlabel='Declared dimensionless anchor B',ylabel=r'Mass of $A_j/B>1$',ylim=(-.03,1.03),
           title='D  Anchor changes the reported threshold event')
    ax.legend(fontsize=8);ax.grid(alpha=.16)
    fig.suptitle('CF4 source-conditioned sensitivity: 2048 coupled four-window draws',fontsize=15,y=.985)
    fig.text(.5,.018,'Actual CF4 sufficient statistics + assumed Gaussian working covariance. No physical posterior, certified F, or anomaly p-value.',
             ha='center',fontsize=9,color='#444444')
    fig.tight_layout(rect=[0,.04,1,.96],h_pad=2.5,w_pad=2.5)
    fig.savefig(folder/'functional_sensitivity.png')
    fig.savefig(folder/'functional_sensitivity.svg')
    plt.close(fig)


if __name__=='__main__':plot()
