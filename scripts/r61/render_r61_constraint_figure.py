#!/usr/bin/env python3
"""Render the saved R61 constraint table with a shared, nonoverlapping legend."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();source=Path(a.input).resolve();out=Path(a.output).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('refusing to overwrite final figures')
    out.mkdir(parents=True,exist_ok=True);report=json.loads(source.read_text())
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    names=list(report['variants'])
    fig,axes=plt.subplots(1,3,figsize=(13.5,5.7),sharey=True)
    targets=[('Sigma',r'$\Sigma=\|s\|_F/\sqrt{6}$'),
             ('acceleration_over_cH',r'$|a|=|A|/(cH)$'),
             ('relative_speed_over_c',r'$|\beta|=|V|/c$')]
    for ax,(target,label) in zip(axes,targets):
        for row,name in enumerate(names):
            for mag,color,offset in [('0.0','#24567a',-.13),('0.005','#d56b2b',.13)]:
                value=report['variants'][name]['1.0']['images_by_rms_mag'][mag][target]
                ax.plot([value['lower'],value['upper']],[row+offset]*2,color=color,lw=2.8)
        ax.set_xlabel(label,fontsize=12);ax.grid(axis='x',alpha=.22)
        ax.spines[['top','right']].set_visible(False)
        ax.tick_params(labelsize=10)
    axes[0].set_yticks(range(len(names)),names)
    axes[0].invert_yaxis()
    fig.suptitle('Conditional CF4 kinematic confidence images',fontsize=16,y=.98)
    fig.legend(handles=[Line2D([0],[0],color='#24567a',lw=3,label='0 mmag calibration RMS'),
                        Line2D([0],[0],color='#d56b2b',lw=3,label='5 mmag calibration RMS')],
               loc='upper center',bbox_to_anchor=(.55,.935),ncol=2,frameon=False,fontsize=11)
    fig.text(.55,.025,'One 95% joint 11D ellipsoid per variant; fixed covariance; first-order physical response',
             ha='center',fontsize=10)
    fig.subplots_adjust(left=.16,right=.98,bottom=.15,top=.82,wspace=.18)
    files=[]
    for suffix in ['png','pdf']:
        f=out/('KINEMATIC_CONSTRAINTS_FINAL.'+suffix);fig.savefig(f,dpi=180);files.append(f)
    plt.close(fig)
    receipt={'schema':'htt.r61.figure/1','source':str(source),'source_sha256':sha(source),
        'renderer_sha256':sha(__file__),'outputs':[{ 'file':f.name,'sha256':sha(f)} for f in files],
        'change':'Presentation only: shared legend and shared y labels; numerical endpoints unchanged.',
        'confidence':'conditional simultaneous11; not survey-calibrated coverage'}
    (out/'FIGURE_MANIFEST.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
