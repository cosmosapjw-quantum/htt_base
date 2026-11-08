from pathlib import Path
import importlib.util, json
import numpy as np
from scipy.stats import chi2
source=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-04-CLASSIFICATION/classification.py')
spec=importlib.util.spec_from_file_location('candidate_review_falsifier',source)
c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
from matplotlib.figure import Figure
captured={}
def capture(fig,destination,*args,**kwargs):
    captured[Path(destination).name]=fig
Figure.savefig=capture
r95=float(np.sqrt(chi2.ppf(.95,6)))
c.plot(np.linspace(0,1,9),np.array([.03,.06,.12,.18,.27]),np.array([0,.1,.2]),r95,[])
ax=captured['adequacy_residual.pdf'].axes[0]
x,y=ax.lines[0].get_data(); marker=ax.collections[0].get_offsets()[0]
tau=r95*.12+.1
raw_shift=.6; correct=raw_shift/np.sqrt(2); plotted=float(np.interp(raw_shift,x,y))
ii=np.diag([.5,-.5,-.5]);vii=np.diag([-.5,1.5,-1.5]);datum=c.raw_mean(ii);datum[0]+=raw_shift
record={'x_axis_label':ax.get_xlabel(),'probe_raw_trace_shift':raw_shift,'actual_plotted_adequacy':plotted,'expected_adequacy':float(correct),'tube':tau,'compatible_set':c.exact_compatibility(datum,{'II':ii,'VII0matched':vii},tau),'actual_marker':list(map(float,marker)),'expected_marker':[1.,float(1/np.sqrt(2))],'pdf_files_written':0}
print(json.dumps(record,indent=2),flush=True)
assert np.allclose(y,np.asarray(x)/np.sqrt(2),rtol=0,atol=1e-14), 'Raw trace-shift plot overstates profiled adequacy by sqrt(2) and changes rejection decisions'
assert np.allclose(marker,[1.,1/np.sqrt(2)],rtol=0,atol=1e-14)
