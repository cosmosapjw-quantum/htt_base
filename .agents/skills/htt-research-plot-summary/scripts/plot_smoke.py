#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, numpy as np
import matplotlib.pyplot as plt
OUT=Path('docs/harness/plots'); OUT.mkdir(parents=True, exist_ok=True)
x=np.linspace(0,1,200); y=np.exp(-x)*np.sin(8*np.pi*x)
fig,ax=plt.subplots(); ax.plot(x,y); ax.set_xlabel('x [diagnostic units]'); ax.set_ylabel('diagnostic quantity [diagnostic units]'); ax.set_title('SMOKE diagnostic only')
png=OUT/'smoke_diagnostic.png'; fig.savefig(png,dpi=160,bbox_inches='tight')
meta={'category':'SMOKE','script':str(Path(__file__)),'output':str(png),'claim_tier':'C0','note':'Template smoke plot only; not validation.'}
(OUT/'smoke_diagnostic_metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print(png)
