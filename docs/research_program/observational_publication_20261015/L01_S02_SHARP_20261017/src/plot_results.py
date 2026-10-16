from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    root=Path(__file__).resolve().parents[1]/'results'
    l=json.loads((root/'L01_SOURCE_FINITE_MINIMAL_LIFT.json').read_text())
    s=json.loads((root/'S02_CONDITIONAL_SHARP_EVENT_ENVELOPES.json').read_text())
    fig,ax=plt.subplots(figsize=(9,4.8))
    rs=l['product_rows']
    ax.barh([r['product'] for r in rs],[r['min_high_l6_32_coeff_norm_microK_if_true_low_set_to_zero'] for r in rs])
    ax.set_xlabel('Minimum high-l coefficient Euclidean norm (microK)')
    ax.set_title('L01: source-locked finite T mask inverse, ell 6-32 only')
    ax.invert_yaxis();fig.tight_layout();fig.savefig(root/'L01_SOURCE_MINIMUM_HIGH_LIFT.png',dpi=160);plt.close(fig)
    labels=['z=.025','z=.040','z=.060','z=.080'];fig,ax=plt.subplots(figsize=(8.0,5.4))
    for i,(name,v) in enumerate(s['scenarios'].items()):
        r=v['working_ratio_joint_event_bounds']['per_window'][1]
        x=[p+i*.12 for p in range(4)]
        ax.errorbar(x,[(u+l)/2 for l,u in zip(r['lower'],r['upper'])],
            yerr=[[(u-l)/2 for l,u in zip(r['lower'],r['upper'])]]*2,fmt='o',capsize=3,label=name)
    ax.set_xticks([p+.12 for p in range(4)],labels)
    ax.set_ylim(-.03,1.04);ax.set_ylabel('Fraction of one 2048-joint working measure')
    ax.set_title('S02: assumed hard-ball sharp bounds, q_app > .05 (NOT physical Q)')
    ax.legend();fig.tight_layout();fig.savefig(root/'S02_SHARP_WORKING_EXCEEDANCE_INTERVALS.png',dpi=160);plt.close(fig)
if __name__=='__main__':main()
