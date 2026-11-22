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
    bad.write_text('may:\n  host: 127.0.0.1\n  port: 2000\n    carla_root: "D:/CARLA"\n', encoding="utf-8")
    with pytest.raises(config.ConfigError, match="dòng 4"):
        config.load_config(bad)


def test_local_config_only_overrides_the_machine_section(tmp_path):
    (tmp_path / "config.yaml").write_text((ROOT / "config.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    # bản local chép từ config cũ: thiếu cac_xe, có xe khác; chỉ mục may được dùng
    (tmp_path / "config.local.yaml").write_text(
        'may: {host: 127.0.0.1, port: 2010, carla_root: "D:/CARLA"}\nxe: {blueprint: x, mass_kg: 1}\n', encoding="utf-8")
    cfg = config.load_config(tmp_path / "config.local.yaml")
    assert cfg["may"]["port"] == 2010 and cfg["may"]["carla_root"] == "D:/CARLA" and cfg["may"]["timeout_s"] == 60
    assert cfg["xe"]["mass_kg"] == 2100.0 and "model3" in cfg["cac_xe"]


def test_dot2_case_list_and_vehicle_scaling():
    cfg = config.load_config(ROOT / "config.yaml")
    r = config.expand_cases(config.load_yaml(ROOT / "cases_dot2.yaml"), cfg)
    by_group = {}
    for c in r:
        by_group[c.group] = by_group.get(c.group, 0) + 1
    assert by_group == {"X1": 80, "X2": 36, "X3": 16, "X4": 8, "B1": 6, "B2": 3, "B3": 4, "B4": 2, "B5": 6,
                        "E1": 4, "E2": 4, "E3": 4, "E4": 4, "E5": 6, "E6": 5, "R": 17}
    assert len(r) == 205
    c = {x.run_id: x for x in r}["X1-hgv-t2.5-60"]
    v = config.vehicle_of(cfg, c)
    assert v["blueprint"] == "vehicle.carlamotors.european_hgv" and v["max_brake_torque_nm"] == 3750.0 and v["mass_kg"] == 7000.0
    b4 = {x.run_id: x for x in r}["B4-50-max"]
    assert config.vehicle_of(cfg, b4)["mass_kg"] == 2100.0 * 1.15


def test_dot3_has_exactly_500_runs():
    cfg = config.load_config(ROOT / "config.yaml")
    r = config.expand_cases(config.load_yaml(ROOT / "cases_dot3.yaml"), cfg)
    assert len(r) == 500
    assert {c.group for c in r} == {"D1", "D2", "D3", "D4", "D5", "D6", "D7", "R3"}


def test_dot4_uses_the_calibrated_vehicles_only():
    cfg = config.load_config(ROOT / "config.yaml")
    r = config.expand_cases(config.load_yaml(ROOT / "cases_dot4.yaml"), cfg)
    assert len(r) == 331
    assert {c.group for c in r} == {"P1", "P2", "R4"}
    assert {c.vehicle for c in r} == {"model3_hc", "patrol_hc", "sprinter_hc"}
    v = config.vehicle_of(cfg, next(c for c in r if c.vehicle == "patrol_hc"))
    assert v["max_brake_torque_nm"] == 2250.0 and v["full_brake_decel_mps2"] == 9.90
