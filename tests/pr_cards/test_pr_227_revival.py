from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_reproduction import RUNNERS  # noqa: E402
from scripts.codex_harness import run_pr227_reproduce as runner  # noqa: E402
CARD = REPO/"docs/generated/pr227_result_card.json"

def test_eighteen_runners_registered():
    assert len(RUNNERS) == 18

def test_card_verified_independence_open():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["result"]["reproduction"]["all_byte_stable"] is True
    assert c["metadata"]["independence_gate"] == "OPEN"
    assert c["terminal"] == "TRACK_I_AUTHOR_REPRODUCTION_VERIFIED_INDEPENDENCE_OPEN"


def test_check_rebuilds_the_live_capsule(monkeypatch, capsys):
    c = json.loads(CARD.read_text())
    monkeypatch.setattr(
        runner, "reproduce_all", lambda: c["result"]["reproduction"]
    )
    monkeypatch.setattr(
        runner, "environment_recipe", lambda: c["result"]["environment_recipe"]
    )
    assert runner.main(["--check"]) == 0
    observed = json.loads(capsys.readouterr().out)
    assert observed["ok"] is True
    assert observed["live_author_reproduction"] == "VERIFIED"
    assert observed["failed_cards"] == []


def test_check_rejects_a_failed_live_runner(monkeypatch, capsys):
    c = json.loads(CARD.read_text())
    reproduction = json.loads(json.dumps(c["result"]["reproduction"]))
    reproduction["all_byte_stable"] = False
    reproduction["author_reproduction"] = "FAILED"
    reproduction["per_card"]["PR-209"]["byte_stable"] = False
    reproduction["per_card"]["PR-209"]["exit"] = 1
    monkeypatch.setattr(runner, "reproduce_all", lambda: reproduction)
    monkeypatch.setattr(
        runner, "environment_recipe", lambda: c["result"]["environment_recipe"]
    )
    assert runner.main(["--check"]) == 1
    observed = json.loads(capsys.readouterr().out)
    assert observed["ok"] is False
    assert observed["live_author_reproduction"] == "FAILED"
    assert observed["failed_cards"] == ["PR-209"]
