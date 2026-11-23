"""Build the htt_base scalar radial-velocity driver against the pinned CORAS source."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import time

UPSTREAM = "https://github.com/rlilow/CORAS.git"
REVISION = "45ab25635aa32869ce207511d556ea257ab8a591"
TREE = "dc7259f94bc6535156f538b5f6603a56b052fe20"
DATA = ("data/2MRS_group_member_catalog.dat", "data/CosmicEmu_spectrum_Planck18.dat")
DRIVER = Path(__file__).resolve().with_name("coras_radial.cpp")


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def git(donor, *args):
    return subprocess.check_output(["git","-C",str(donor),*args], text=True).strip()


def prepare_build(result, existing):
    root = Path(result).resolve()
    donor = None if existing is None else Path(existing).resolve(strict=True)
    if donor and (root.is_relative_to(donor) or donor.is_relative_to(root)):
        raise ValueError("choose disjoint source and build directories")
    root.mkdir(parents=True, exist_ok=False)
    if donor is None:
        donor = root/"CORAS"
        subprocess.run(["git","clone","--no-checkout",UPSTREAM,str(donor)],check=True)
        subprocess.run(["git","-C",str(donor),"checkout","--quiet","--detach",REVISION],check=True)
    return root, donor


def donor_sources(donor):
    if git(donor,"rev-parse","HEAD") != REVISION or git(donor,"rev-parse","HEAD^{tree}") != TREE:
        raise ValueError("CORAS revision/tree differs from the pinned source")
    raw = git(donor,"ls-tree","-r","--name-only",REVISION,"--","src").splitlines()
    src = sorted(p for p in raw if Path(p).suffix in (".cpp",".hpp",".tpp",".h"))
    selected = [*src,"configuration.hpp",*DATA]
    # Any additional header under src can shadow a canonical include.
    if git(donor,"status","--porcelain","--untracked-files=all","--","src","configuration.hpp",*DATA):
        raise ValueError("source or run-time input differs from the clean donor")
    expected=set(src)
    for path in (donor/"src").iterdir():
        if path.suffix in (".hpp",".tpp",".h",".cpp") and path.relative_to(donor).as_posix() not in expected:
            raise ValueError(f"untracked or ignored donor source {path}")
    return src,{p:sha(donor/p) for p in selected}


def track_runtime(binary):
    text = subprocess.check_output(["ldd",str(binary)],text=True)
    if "not found" in text:
        raise RuntimeError(text)
    linked = {}
    for soname, name in re.findall(r"^\s*(\S+)\s+=>\s+(/\S+)\s+\(",text,re.M):
        path=Path(name).resolve(strict=True)
        linked[soname]={"path":str(path),"sha256":sha(path)}
    return linked


def build(args):
    t0=time.monotonic()
    if args.jobs<=0:
        raise ValueError("jobs must be positive")
    if not DRIVER.is_file():
        raise FileNotFoundError(DRIVER)
    root,donor=prepare_build(args.build_dir,args.donor)
    sources,inputs=donor_sources(donor)
    compiler = shutil.which(args.cxx)
    ar=shutil.which("ar")
    if compiler is None or ar is None:
        raise FileNotFoundError("C++ compiler and ar are required")
    includes=["-I",str(donor)]
    for p,header in [(args.gsl_include,"gsl/gsl_version.h"),(args.fftw_include,"fftw3.h")]:
        if p is not None:
            include=p.resolve(strict=True)
            if not (include/header).is_file():
                raise FileNotFoundError(include/header)
            includes.extend(["-I",str(include)])
    # Header paths are captured from compiler dependencies, including system installs.
    objects=root/"objects"
    objects.mkdir()
    env={**os.environ,"LC_ALL":"C"}
    base=[compiler,"-std=c++11","-O3","-fopenmp",*includes]
    def compile_one(pair):
        source,obj=pair
        cmd=[*base,"-MD","-MF",str(obj.with_suffix(".d")),"-c",str(source),"-o",str(obj)]
        subprocess.run(cmd,env=env,check=True)
        return cmd
    library_sources=[(donor/p,objects/(Path(p).stem+".o")) for p in sources if p.endswith(".cpp")]
    driver_object=objects/"coras_radial.o"
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        commands=list(pool.map(compile_one,[*library_sources,(DRIVER,driver_object)]))
    archive=root/"libcoras.a"
    ar_cmd=[ar,"rcs",str(archive),*(str(o) for _,o in library_sources)]
    subprocess.run(ar_cmd,env=env,check=True)
    binary=root/"coras_radial"
    link_command=[compiler,"-fopenmp",str(driver_object),str(archive),"-o",str(binary)]
    for directory in args.lib_dir:
        link_command.extend(["-L",str(directory.resolve(strict=True))])
    link_command.extend([args.gsl_link,args.gslcblas_link,args.fftw_omp_link,args.fftw_link])
    subprocess.run(link_command,env=env,check=True)
    runtime=track_runtime(binary)
    smoke=subprocess.run([str(binary)],cwd=donor,capture_output=True,text=True,timeout=15)
    if smoke.returncode!=2 or "usage: coras_radial sites output_dir first last" not in smoke.stderr:
        raise RuntimeError(f"driver usage smoke failed: {smoke.returncode}: {smoke.stderr}")
    # GCC dependency files use Make backslash escapes. Parse spaces in roots,
    # keep headers whose bytes determine the GSL/FFTW interface selected here.
    import shlex
    headers=set()
    for deps in objects.glob("*.d"):
        body=deps.read_text().replace("\\\n"," ")
        for tok in shlex.split(body.split(":",1)[1]):
            dep=Path(tok)
            if dep.is_file() and (dep.name=="fftw3.h" or dep.parent.name=="gsl"):
                headers.add(dep.resolve())
    inputs_final={p:sha(donor/p) for p in inputs}
    if inputs_final!=inputs or git(donor,"rev-parse","HEAD")!=REVISION:
        raise RuntimeError("donor inputs changed during compilation")
    result={"status":"built_and_usage_checked","donor_url":UPSTREAM,"donor_commit":REVISION,"donor_tree":TREE,
            "donor":str(donor),"inputs_sha256":inputs,"driver_path":str(DRIVER),"driver_sha256":sha(DRIVER),
            "frontend_sha256":sha(Path(__file__)),"external_headers_sha256":{str(p):sha(p) for p in sorted(headers)},
            "compiler":compiler,"compiler_version":subprocess.check_output([compiler,"--version"],text=True).splitlines()[0],
            "ar":ar,"platform":platform.platform(),"jobs":args.jobs,"compile_commands":commands,
            "archive_command":ar_cmd,"archive_sha256":sha(archive),"link_command":link_command,
            "runtime_libraries":runtime,"binary":str(binary),"binary_sha256":sha(binary),
            "driver_usage_exit":smoke.returncode,"elapsed_s":time.monotonic()-t0}
    receipt=root/"build_receipt.json"
    receipt.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(receipt)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build-dir",type=Path,required=True,help="new output directory")
    p.add_argument("--donor",type=Path,help="existing checkout at pinned revision; otherwise clone")
    p.add_argument("--cxx",default="g++")
    p.add_argument("--jobs",type=int,default=2)
    p.add_argument("--gsl-include",type=Path)
    p.add_argument("--fftw-include",type=Path)
    p.add_argument("--lib-dir",type=Path,action="append",default=[])
    p.add_argument("--gsl-link",default="-lgsl",help="one linker argument, e.g. --gsl-link=-l:libgsl.so.27")
    p.add_argument("--gslcblas-link",default="-lgslcblas")
    p.add_argument("--fftw-omp-link",default="-lfftw3_omp")
    p.add_argument("--fftw-link",default="-lfftw3")
    build(p.parse_args())


if __name__=="__main__":
    main()
