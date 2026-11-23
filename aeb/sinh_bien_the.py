"""Sinh aeb/bien_the.json: các ca xe + người (combined) của 4 đợt bench, ánh xạ sang họ kịch bản CP_CROSSING của VehicSim.

Bench chạy open-loop (lệnh phanh cố định "a"); ở đây AEB của VehicSim tự quyết định phanh, nên bỏ "a".
Ca brake (không người) và walker (không xe) không có nghĩa khi bật AEB nên không lấy.
Bỏ ca không biểu diễn được trong VehicSim: xe hgv (không có trong VehicSim) và tire_friction_scale ≠ 1 (VehicSim chỉ có ma sát theo thời tiết).

Chạy:  .venv\\Scripts\\python aeb\\sinh_bien_the.py
"""
from __future__ import annotations

import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.config import expand_cases, load_config, load_yaml  # noqa: E402

DOT_FILES = ["cases.yaml", "cases_dot2.yaml", "cases_dot3.yaml", "cases_dot4.yaml"]

# Xe bench → chuỗi tìm trong tên xe của VehicSim (GET /projects/vehicle-options, không phân biệt hoa thường).
VEHICLES = {
    "etron": "e-tron",
    "model3_hc": "model 3",
    "patrol_hc": "patrol",
    "sprinter_hc": "sprinter",
}

# Họ kịch bản: lưới tích Đề-các (VehicSim sinh biến thể = ego × trigger × ped). Chọn để phủ hết ca bench với ít biến thể thừa nhất.
FAMILIES = [
    {"key": "etron-D4", "vehicle": "etron", "name": "AEB đối chiếu · e-tron · lưới D4",
     "ego_speeds_kmh": [20, 30, 40, 50, 60], "trigger_distances_m": [15, 25, 40], "pedestrian_speeds_mps": [0.8, 1.0, 1.39, 1.8, 2.5, 3.5]},
    {"key": "etron-trigger", "vehicle": "etron", "name": "AEB đối chiếu · e-tron · khoảng kích hoạt",
     "ego_speeds_kmh": [40], "trigger_distances_m": [5, 15, 20, 25, 30, 40, 60, 80], "pedestrian_speeds_mps": [1.5]},
    {"key": "etron-le", "vehicle": "etron", "name": "AEB đối chiếu · e-tron · ca lẻ",
     "ego_speeds_kmh": [20, 60], "trigger_distances_m": [25], "pedestrian_speeds_mps": [0.5, 3.0]},
    {"key": "model3-P2", "vehicle": "model3_hc", "name": "AEB đối chiếu · Model 3 · P2",
     "ego_speeds_kmh": [20, 40, 60], "trigger_distances_m": [25], "pedestrian_speeds_mps": [1.5]},
    {"key": "patrol-P2", "vehicle": "patrol_hc", "name": "AEB đối chiếu · Patrol · P2",
     "ego_speeds_kmh": [20, 40, 60], "trigger_distances_m": [25], "pedestrian_speeds_mps": [1.5]},
    {"key": "sprinter-P2", "vehicle": "sprinter_hc", "name": "AEB đối chiếu · Sprinter · P2",
     "ego_speeds_kmh": [20, 40, 60], "trigger_distances_m": [25], "pedestrian_speeds_mps": [1.5]},
]


def key(vehicle: str, ego: float, trigger: float, ped: float) -> str:
    return f"{vehicle}|{ego:g}|{trigger:g}|{ped:g}"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    cfg = load_config(ROOT / "config.yaml")
    bench: dict[str, list[str]] = defaultdict(list)
    dropped: list[str] = []
    for dot, name in enumerate(DOT_FILES, 1):
        for c in expand_cases(load_yaml(ROOT / name), cfg):
            if c.kind != "combined":
                continue
            label = f"dot{dot}:{c.run_id}"
            if c.vehicle not in VEHICLES or c.tire_friction_scale != 1.0 or c.torque_scale != 1.0 or c.mass_scale != 1.0 \
                    or c.stop_at_curb or c.weather != "CLEAR":
                dropped.append(label)
                continue
            bench[key(c.vehicle, c.ego_kmh, c.trigger_m, c.ped_mps)].append(label)

    covered: set[str] = set()
    families = []
    for f in FAMILIES:
        variants = []
        for ego, trig, ped in itertools.product(f["ego_speeds_kmh"], f["trigger_distances_m"], f["pedestrian_speeds_mps"]):
            k = key(f["vehicle"], ego, trig, ped)
            covered.add(k)
            variants.append({"ego_speed_kmh": ego, "trigger_distance_m": trig, "pedestrian_speed_mps": ped, "bench_cases": bench.get(k, [])})
        families.append({**f, "vehicle_match": VEHICLES[f["vehicle"]], "variants": variants})

    missing = sorted(set(bench) - covered)
    if missing:
        raise SystemExit(f"Họ chưa phủ ca bench: {missing}")
    out = {
        "note": "Ca combined của 4 đợt bench → họ CP_CROSSING (CLEAR, DAY, không dừng ở lề). Sinh bởi aeb/sinh_bien_the.py.",
        "dropped_bench_cases": dropped,
        "families": families,
    }
    path = Path(__file__).with_name("bien_the.json")
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(f["variants"]) for f in families)
    extra = sum(1 for f in families for v in f["variants"] if not v["bench_cases"])
    print(f"{len(families)} họ, {n} biến thể ({extra} biến thể không có ca bench tương ứng), bỏ {len(dropped)} lượt bench: {dropped}")


if __name__ == "__main__":
    main()
