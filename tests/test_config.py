from pathlib import Path

import pytest

from bench import config

ROOT = Path(__file__).resolve().parents[1]


def runs():
    cfg = config.load_config(ROOT / "config.yaml")
    return config.expand_cases(config.load_yaml(ROOT / "cases.yaml"), cfg)


def test_case_list_matches_design_counts():
    r = runs()
    by_group = {}
    for c in r:
        by_group[c.group] = by_group.get(c.group, 0) + 1
    assert by_group == {"G1": 30, "G2": 5, "G3": 6, "G4": 4, "G5": 5, "G6": 6}
    assert len(r) == 56


def test_ids_and_defaults():
    r = {c.run_id: c for c in runs()}
    assert r["G1-50-8.0"].a == 8.0 and r["G1-20-max"].a == "max"
    assert r["G3-25"].kind == "combined" and r["G3-25"].ego_kmh == 40.0
    assert r["G4-1.5"].stop_at_curb is True
    assert r["G5-40-RAIN"].weather == "RAIN" and r["G5-60-TF"].tire_friction_scale == 0.65
    assert r["G6-a-r2"].same_as == "G1-50-8.0" and r["G6-a-r2"].ego_kmh == 50.0


def test_select_by_group_and_id():
    r = runs()
    assert {c.group for c in config.select(r, "G2,G4")} == {"G2", "G4"}
    assert [c.run_id for c in config.select(r, "G3-25")] == ["G3-25"]


def test_invalid_case_is_rejected():
    cfg = config.load_config(ROOT / "config.yaml")
    doc = {"defaults": {"ego_kmh": 40, "a": 8.0, "ped_mps": 1.5, "trigger_m": 25, "stop_at_curb": False,
                        "weather": "CLEAR", "tire_friction_scale": 1.0},
           "cases": [{"id": "X", "kind": "brake", "weather": "SNOW"}]}
    with pytest.raises(config.ConfigError, match="SNOW"):
        config.expand_cases(doc, cfg)


def test_bad_indentation_gives_line_number(tmp_path):
    bad = tmp_path / "config.local.yaml"
    bad.write_text("may:
  host: 127.0.0.1
  port: 2000
    carla_root: \"D:/CARLA\"
", encoding="utf-8")
    with pytest.raises(config.ConfigError, match="dòng 4"):
        config.load_config(bad)
