import copy
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('packet',ROOT/'scripts/reboot_task_packet.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)


def plan():return json.loads((ROOT/'docs/observational_reboot_20261014/REBOOT_PLAN.json').read_text())


def test_ready_and_bounded_packets():
    p=plan()
    assert [t['id'] for t in mod.ready_tasks(p)]==['RB01','RB02','RB05','RB07','RB17','RB18','RB20','RB21','RB22']
    for t in p['tasks']:
        assert len(json.dumps(mod.packet(p,t['id']),ensure_ascii=False,indent=2))<=12000


@pytest.mark.parametrize('defect',['cycle','missing','false_completion','duplicate'])
def test_invalid_transition_rejected(defect):
    p=plan()
    if defect=='cycle':p['tasks'][0]['depends']=['RB01']
    if defect=='missing':p['tasks'][1]['depends']=['MISSING']
    if defect=='false_completion':p['tasks'][4]['status']='completed'
    if defect=='duplicate':p['tasks'].append(copy.deepcopy(p['tasks'][0]))
    with pytest.raises(ValueError):mod.validate(p)
