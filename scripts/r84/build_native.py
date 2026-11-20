"""R84 build certified source-conditional NVSS Fortran only in temp cache."""
import json
from pathlib import Path
from htt.obsstat import p4_bianchi_fast as f

def main():
    path=Path(f._certified_native())
    data=json.loads(path.with_name("manifest.json").read_text())
    print(json.dumps({"binary":str(path),"binary_bytes":path.stat().st_size,
                      "manifest":data},indent=2,ensure_ascii=False))
if __name__=="__main__":main()
