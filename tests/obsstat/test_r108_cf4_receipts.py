"""Fast offline tests for scripts/r108/cf4_receipts.py (open() trace, pre-existing-input receipts, summary)."""
import json
import subprocess
import sys
from pathlib import Path

from scripts.r108 import cf4_receipts as m

ROOT = Path(__file__).resolve().parents[2]


def test_open_trace_records_reads_and_writes(tmp_path):
    data = tmp_path / "in.dat"
    data.write_text("x")
    log = tmp_path / "trace.jsonl"
    code = (f"from scripts.r108.cf4_receipts import install_open_trace as t; t({str(log)!r}, 'unit'); "
            f"open({str(data)!r}).read(); open({str(tmp_path / 'out.txt')!r}, 'w').write('y')")
    subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, check=True, env={"PYTHONPATH": str(ROOT), "PATH": ""})
    header, reads, writes = m.read_trace(log)
    assert header["label"] == "unit"
    assert str(data) in reads and str(tmp_path / "out.txt") in writes


def test_is_data_path_and_round():
    assert not m.is_data_path("/x/lib/python3.12/site-packages/numpy/core.py", prefixes=set())
    assert not m.is_data_path("/usr/share/zoneinfo/UTC", prefixes=set())
    assert not m.is_data_path("/home/u/.astropy/config/astropy.cfg", home="/home/u", prefixes=set())
    assert m.is_data_path("/home/u/Downloads/htt_r100/source_intake/table1.txt", home="/home/u", prefixes=set())
    assert m.originating_round("/home/u/Downloads/htt_r105_coras/sixdf8/residual_1.tsv") == "R105"
    assert m.originating_round(f"{ROOT}/docs/x/R106_RESEARCH_20261124/CF3/a.json.gz") == "R106"
    assert m.originating_round(f"{ROOT}/.agent-harness/runs/R9-SELECTED-LAW-20260913/a.txt") == "R9"
    assert m.originating_round("/mnt/extdrive/workdir/raw/cf4_full/table2.dat").startswith("pre-R108 external")


def test_pre_existing_lines_dedupe_cover_and_summary(tmp_path):
    dl = tmp_path / "cf4"
    (dl / "D01").mkdir(parents=True)
    fetched = dl / "D01" / "t.vot"
    fetched.write_text("fetched")
    old = tmp_path / "htt_r100" / "table1.txt"
    old.parent.mkdir()
    old.write_text("pre-existing")
    out = tmp_path / "result.json"
    receipts = dl / "RECEIPTS.jsonl"
    receipts.write_text(json.dumps(dict(id="D01", name="t.vot", path=str(fetched), status="FETCHED",
                                        sha256=m.sha256_file(fetched))) + "\n")
    log = tmp_path / "trace.jsonl"
    log.write_text("\n".join(json.dumps(r) for r in (
        dict(trace_header=True, label="scripts.r108.cf4_x"),
        dict(pid=1, path=str(fetched), mode="rb", flags=0), dict(pid=1, path=str(old), mode="r", flags=0),
        dict(pid=1, path=str(out), mode="w", flags=0), dict(pid=1, path=str(out), mode="rb", flags=0),
        dict(pid=1, path=str(receipts), mode="r", flags=0))) + "\n")
    rows, covered = m.pre_existing_lines([log], receipts, dl, candidates=[])
    out.write_text("{}")
    assert covered == [str(fetched)] and len(rows) == 1
    r = rows[0]
    assert r["status"] == m.PRE_STATUS and r["path"] == str(old) and r["sha256"] == m.sha256_file(old)
    assert r["bytes"] == len("pre-existing") and r["originating_round"] == "R100" and r["read_by"] == ["scripts.r108.cf4_x"]
    with open(receipts, "a") as fh:
        fh.write(json.dumps(r) + "\n")
    assert m.pre_existing_lines([log], receipts, dl, candidates=[])[0] == []      # no duplicate line
    items = m.summarize(receipts, dl)
    assert items[m.PRE_ID]["pre_existing"][0]["sha256_on_disk_matches"] is True
    assert items["D01"]["fetched"][0]["sha256_on_disk_matches"] is True and "pre_existing" not in items["D01"]
    old.write_text("changed")
    assert len(m.pre_existing_lines([log], receipts, dl, candidates=[])[0]) == 1   # a changed file gets a new line


def test_origin_pointers_find_sha(tmp_path):
    f = tmp_path / "rec.json"
    f.write_text(json.dumps({"sha256": "ab" * 32}))
    hits = m.origin_pointers(["ab" * 32, "cd" * 32], [f])
    assert hits["ab" * 32] == [str(f)] and hits["cd" * 32] == []


def test_input_coverage_flags_unreceipted_inputs(tmp_path):
    (tmp_path / "A.json").write_text(json.dumps(dict(
        input_sha256={"code": "00" * 32, "raw": "ab" * 32, "other": "cd" * 32},
        input_paths={"code": "/x/s.py", "raw": "/d/raw.dat", "other": "/d/o.dat"})))
    receipts = [dict(status="FETCHED", sha256="ab" * 32), dict(status=m.PRE_STATUS, sha256="ef" * 32)]
    cov = m.input_coverage(tmp_path, receipts)
    assert cov["A.json"]["n_inputs_checked"] == 2 and cov["A.json"]["missing"] == {"other": "cd" * 32}
    receipts.append(dict(status=m.PRE_STATUS, sha256="cd" * 32))
    assert m.input_coverage(tmp_path, receipts)["A.json"]["missing"] == {}


def test_sibling_run_json_is_an_origin_candidate(tmp_path):
    d = tmp_path / "marks"
    d.mkdir()
    (d / "residual_1.tsv").write_text("x")
    (d / "run.json").write_text("{}")
    (d / "other.json").write_text("{}")
    assert m.sibling_records([str(d / "residual_1.tsv")]) == [d / "run.json"]
    assert m.git_head_blob_matches(tmp_path / "residual_1.tsv") is None
