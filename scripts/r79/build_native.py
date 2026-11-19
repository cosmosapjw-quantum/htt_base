"""Build optional C++17/OpenMP and Fortran C ABI R79 kernels into an OUTDIR.

No implicit compile on import and no binary artifact checked in.
"""
import argparse,hashlib,json,platform,shutil,subprocess
from pathlib import Path

NATIVE=Path("htt/obsstat/native")
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    gxx=shutil.which("g++");gfortran=shutil.which("gfortran")
    if not gxx or not gfortran:raise RuntimeError("both g++ and gfortran required for optional native build")
    csrc=NATIVE/"vsh_normal.cpp"
    fsrc=NATIVE/"hemisphere_moments.f90"
    cout=args.out/"libhtt_r79_vsh.so"
    fout=args.out/"libhtt_r79_hemisphere.so"
    # Explicit baseline machine; no -march=native to keep portable binary ISA.
    cc=[gxx,"-O3","-std=c++17","-fPIC","-shared","-fopenmp","-ffp-contract=off","-fno-fast-math",str(csrc),"-o",str(cout)]
    fc=[gfortran,"-O3","-fPIC","-shared","-fno-fast-math",str(fsrc),"-o",str(fout)]
    for command in (cc,fc):
        subprocess.run(command,check=True,capture_output=True,text=True)
    report={"schema":"htt.r79.optional_cpp_fortran_build/1",
      "compiler_cpp":subprocess.check_output([gxx,"--version"],text=True).splitlines()[0],
      "compiler_fortran":subprocess.check_output([gfortran,"--version"],text=True).splitlines()[0],
      "python":platform.python_version(),
      "flags":"C++17 -O3 -fopenmp and Fortran -O3; no fast math; portable x86-64",
      "sources":{str(x):sha(x) for x in (csrc,fsrc)},
      "libraries":{str(x):{"bytes":x.stat().st_size,"sha256":sha(x)} for x in (cout,fout)},
      "commands":[cc,fc],"outputs":{"gaia":str(cout.resolve()),"hemisphere":str(fout.resolve())},
      "status":"COMPILED_NOT_YET_NUMERICALLY_VERIFIED"}
    (args.out/"build_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"built":report["outputs"],"cpp":report["compiler_cpp"],"fortran":report["compiler_fortran"]}))
if __name__=="__main__":main()
