"""Standalone aggregate plots of actual CF4 apparent centers and overlap."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent


def main():
    p=HERE/'results';r=json.loads((p/'h02_actual_centers.json').read_text())
    methods=['FP','TF','SN','OTHER'];basis=r['basis']
    fig,axes=plt.subplots(2,4,figsize=(13,6),sharex=True,layout='constrained')
    # All 160 reported contrasts share this familywise conditional error law.
    from h02_actual import critical_value
    z=critical_value(.05,160,'gaussian_marginals')
    for j,ax in enumerate(axes.flat):
        for i,m in enumerate(methods):
            fit=r['fits']['all_selected'][m]
            ax.errorbar(i,fit['coefficients_mag'][j],yerr=z*np.sqrt(fit['working_covariance'][j][j]),fmt='o',capsize=3)
        ax.axhline(0,color='.7',lw=.8);ax.set_title(basis[j],fontsize=10)
        ax.set_xticks(range(4),methods,rotation=25);ax.set_ylabel('coefficient [mag]')
    fig.suptitle('Actual CF4 pooled-partition centers\n95% simultaneous Gaussian working bounds (160 contrasts); selection/shared calibration UNKNOWN',fontsize=12)
    fig.savefig(p/'h02_actual_centers.png',dpi=160);fig.savefig(p/'h02_actual_centers.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
    for j,b in enumerate(basis):
        rows=[v for v in r['intervals']['rows'] if v['law']=='gaussian_marginals' and v['window']=='all_selected' and v['contrast']==b]
        d=np.array([v['delta_relative_mag'] for v in rows]);lo=np.array([v['lower_mag'] for v in rows]);hi=np.array([v['upper_mag'] for v in rows]);ok=lo<=hi
        color=plt.get_cmap('tab10')(j)
        axes[0].plot(d[ok],lo[ok],lw=1,color=color,label=b);axes[0].plot(d[ok],hi[ok],lw=1,color=color)
    axes[0].set(xlabel='assumed relative calibration bound delta [mag]',ylabel='compatible common+shared coefficient [mag]',title='Observed base-window coordinate outer sets')
    axes[0].legend(fontsize=7,ncol=2)
    overlap=np.array(r['overlap']['selected_method_overlap_counts']);labels=r['overlap']['method_labels']
    im=axes[1].imshow(np.log10(1+overlap),cmap='viridis')
    for a in range(len(labels)):
        for b in range(len(labels)):axes[1].text(b,a,str(overlap[a,b]),ha='center',va='center',fontsize=7,color='white' if overlap[a,b]<500 else 'black')
    axes[1].set_xticks(range(len(labels)),labels,rotation=45);axes[1].set_yticks(range(len(labels)),labels)
    axes[1].set_title('Same selected groups with both released methods\ncolor=log10(1+count); post-calibration source')
    fig.colorbar(im,ax=axes[1],shrink=.75)
    fig.suptitle('Conditional apparent coefficients; no physical confidence or empirical calibration law',fontsize=12)
    fig.savefig(p/'h02_observed_sets_overlap.png',dpi=160);fig.savefig(p/'h02_observed_sets_overlap.pdf');plt.close(fig)


if __name__=='__main__':main()
