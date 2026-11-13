"""Chỉ số và quy tắc hợp lệ trên dữ liệu tổng hợp (không cần CARLA)."""

import csv
import json
from pathlib import Path

import pytest

from bench import config, metrics, model

ROOT = Path(__file__).resolve().parents[1]
CFG = config.load_config(ROOT / "config.yaml")


def _brake_run(tmp: Path, a_true: float, alternate: float = 0.11, torque: float = 1800.0) -> Path:
    """Run G1 giả: 40 km/h, chạy đều 1,5 s rồi phanh theo đúng mô hình với giảm tốc a_true; tốc độ dao động xen kẽ như CARLA."""
    dt, v0, t_cmd = 0.01, 40 / 3.6, 1.5
    prof = model.brake_profile(v0, a_true, 20.0, 0.15, dt, tail_s=0.6)
    frames, s = [], 10.0
    for i in range(int(t_cmd / dt)):
        frames.append({"t": round(i * dt, 4), "step": dt, "ego_s_front": s, "ego_v": v0 + (alternate if i % 2 else -alternate)})
        s += v0 * dt
    s_cmd = s
    for p in prof:
        frames.append({"t": round(t_cmd + p["tau"], 4), "step": dt, "ego_s_front": s_cmd + p["s"], "ego_v": p["v"]})
    for f in frames:
        f.update(ego_lat=0.0, ego_a=0.0, pedal_cmd=0.0, pedal_applied=0.5, collision=False)
    run = tmp / "G1-40-8.0"
    run.mkdir()
    case = {"run_id": "G1-40-8.0", "case_id": "G1-40-8.0", "group": "G1", "kind": "brake", "ego_kmh": 40.0, "a": 8.0, "ped_mps": 1.5,
            "trigger_m": 25.0, "stop_at_curb": False, "weather": "CLEAR", "tire_friction_scale": 1.0, "same_as": None, "repeat_index": 1}
    info = {"events": {"brake_cmd": t_cmd}, "v_at_cmd": v0, "s_front_at_cmd": s_cmd, "a_e": 8.0, "end_reason": "STOPPED",
            "physics": {"mass": 2100.0, "wheels": [{"max_brake_torque": torque, "tire_friction": 3.5}] * 4}, "collisions": []}
    (run / "run.json").write_text(json.dumps({"case": case, "reference": {}, "carla": info}), encoding="utf-8")
    with open(run / "frames.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(frames[0]))
        w.writeheader()
        w.writerows(frames)
    return run


def test_ideal_run_matches_reference(tmp_path):
    row = metrics.analyse_run(_brake_run(tmp_path, 8.0), CFG)
    assert row["valid"], row["reasons"]
    assert row["v0_kmh"] == pytest.approx(40.0, abs=0.05)       # dao động xen kẽ bị khử
    assert row["a_band"] == pytest.approx(8.0, abs=0.05)
    assert row["eta"] == pytest.approx(1.0, abs=0.01)
    assert row["stop_dist_delta_m"] == pytest.approx(0.0, abs=0.05)
    assert row["t90_carla_s"] == pytest.approx(row["t90_ref_s"], abs=0.03)


def test_weaker_brake_is_measured_as_eta_below_one(tmp_path):
    row = metrics.analyse_run(_brake_run(tmp_path, 6.0), CFG)
    assert row["eta"] == pytest.approx(0.75, abs=0.02)
    assert row["stop_dist_delta_m"] > 2.0
    assert row["dttc_s"] == pytest.approx(model.ttc_compensation(40 / 3.6, 6.0, 8.0), abs=0.01)


def test_wrong_torque_invalidates_run(tmp_path):
    row = metrics.analyse_run(_brake_run(tmp_path, 8.0, torque=1000.0), CFG)
    assert not row["valid"] and "mô-men" in row["reasons"]


def test_repeat_stats_groups_base_and_repeats():
    rows = [{"case_id": "G1-50-8.0", "same_as": None, "valid": True, "eta": 1.00},
            {"case_id": "G6-a", "same_as": "G1-50-8.0", "valid": True, "eta": 1.02},
            {"case_id": "G6-a", "same_as": "G1-50-8.0", "valid": True, "eta": 0.99}]
    stats = {s["metric"]: s for s in metrics.repeat_stats(rows)}
    assert stats["eta"]["n"] == 3 and stats["eta"]["range"] == pytest.approx(0.03)
