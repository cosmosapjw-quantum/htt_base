"""R85 optional source-SHA certified K02 method-profiled 12D Fortran build."""
import json
from pathlib import Path
from htt.obsstat.p5p6_fast import _certified_fortran

def main():
    lib=Path(_certified_fortran())
    print(json.dumps({"library":str(lib),"bytes":lib.stat().st_size,
                      "manifest":json.loads(lib.with_name("manifest.json").read_text())},indent=2))
if __name__=="__main__":main()
