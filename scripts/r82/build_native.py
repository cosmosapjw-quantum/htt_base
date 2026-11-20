"""R82 compile source-SHA-certified P1 optional C++/Fortran into temp only."""
import json
from pathlib import Path
from htt.obsstat import p1_fast

def main():
    result={}
    for kind in ("tails","floor"):
        lib=Path(p1_fast._certified_native(kind))
        result[kind]={"path":str(lib),"manifest":json.loads(lib.with_name("manifest.json").read_text()),
                      "library_bytes":lib.stat().st_size}
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
