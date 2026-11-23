"""Sinh aeb/bien_the.json: mọi ca của 4 đợt bench, ánh xạ sang họ kịch bản CP_CROSSING của VehicSim để chạy lại có AEB.

Bench chạy open-loop (lệnh phanh cố định "a"). Ở VehicSim, AEB tự quyết định phanh, nên mỗi ca được dựng thành một ca xe + người:
- combined (xe + người): giữ nguyên tốc độ xe, tốc độ người, khoảng kích hoạt.
- brake (xe phanh, không người): thêm người theo tham số mặc định của ca (thường 1,5 m/s, kích hoạt 25 m) để AEB phải phanh;
  đo phanh AEB ở đúng tốc độ / xe / thời tiết của ca. Các mức "a" khác nhau của cùng tốc độ gộp thành một biến thể.
- walker (người, không xe): thêm xe theo tốc độ mặc định của ca (40 km/h); ca người dừng ở lề là ca an toàn, đo phanh oan.
Bỏ ca không biểu diễn được: xe hgv, tire_friction_scale / torque_scale / mass_scale ≠ 1, người > 6 m/s (giới hạn VehicSim),
và cặp tốc độ xe + khoảng kích hoạt mà xe không tới vạch trước 12 s (VehicSim từ chối, bench cho tới 22 s).
Xe chưa hiệu chuẩn của bench (model3 / patrol / sprinter) gộp với bản _hc: VehicSim chỉ có bản đã hiệu chuẩn (migration 016).

Chạy:  .venv\\Scripts\\python aeb\\sinh_bien_the.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bench.config import expand_cases, load_config, load_yaml  # noqa: E402

DOT_FILES = ["cases.yaml", "cases_dot2.yaml", "cases_dot3.yaml", "cases_dot4.yaml"]
# Xe bench → (khóa, chuỗi tìm trong tên xe VehicSim ở GET /projects/vehicle-options, không phân biệt hoa thường).
VEHICLES = {
    "etron": ("etron", "e-tron"),
    "model3": ("model3", "model 3"), "model3_hc": ("model3", "model 3"),
    "patrol": ("patrol", "patrol"), "patrol_hc": ("patrol", "patrol"),
    "sprinter": ("sprinter", "sprinter"), "sprinter_hc": ("sprinter", "sprinter"),
}
VEHICLE_LABEL = {"etron": "e-tron", "model3": "Model 3", "patrol": "Patrol", "sprinter": "Sprinter"}
WEATHERS = {"CLEAR", "RAIN", "HEAVY_RAIN"}
MAX_PED_MPS = 6.0          # FamilyService.MAX_PEDESTRIAN_SPEED_MPS
MAX_DURATION_S = 12.0      # Simulator.MAX_DURATION_S
LEAD_TIME_S = 1.5          # Simulator.LEAD_TIME_S
MAX_AXIS = 20              # FamilyRequest: tối đa 20 giá trị mỗi trục


def reachable(ego_kmh: float, trigger_m: float) -> bool:
    return trigger_m / (ego_kmh / 3.6) + LEAD_TIME_S < MAX_DURATION_S  # FamilyService.arrivalSeconds


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    cfg = load_config(ROOT / "config.yaml")
    points: dict[tuple, list[str]] = defaultdict(list)  # (xe, thời tiết, dừng lề, ego, trigger, người) → lượt bench
    dropped: dict[str, list[str]] = defaultdict(list)
    total = 0
    for dot, name in enumerate(DOT_FILES, 1):
        for c in expand_cases(load_yaml(ROOT / name), cfg):
            total += 1
            label = f"dot{dot}:{c.run_id}"
            if c.vehicle not in VEHICLES:
                dropped[f"xe {c.vehicle} không có trong VehicSim"].append(label)
            elif c.tire_friction_scale != 1.0 or c.torque_scale != 1.0 or c.mass_scale != 1.0:
                dropped["hệ số ma sát / mô-men / khối lượng ≠ 1"].append(label)
            elif c.weather not in WEATHERS:
                dropped[f"thời tiết {c.weather}"].append(label)
            elif c.ped_mps > MAX_PED_MPS:
                dropped["người > 6 m/s"].append(label)
            elif not reachable(c.ego_kmh, c.trigger_m):
                dropped["xe không tới vạch trước 12 s"].append(label)
            else:
                points[(VEHICLES[c.vehicle][0], c.weather, c.stop_at_curb, c.ego_kmh, c.trigger_m, c.ped_mps)].append(f"{label} [{c.kind}]")

    # Họ = tích Đề-các không thừa: trong mỗi (xe, thời tiết, dừng lề, khoảng kích hoạt), gộp các tốc độ người có cùng tập tốc độ xe.
    groups: dict[tuple, dict[float, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (veh, wx, stop, ego, trig, ped) in points:
        groups[(veh, wx, stop, trig)][ped].append(ego)
    # Gộp tiếp các khoảng kích hoạt có cùng (tập tốc độ xe, tập tốc độ người): vẫn là tích Đề-các không thừa.
    blocks: dict[tuple, list[float]] = defaultdict(list)
    for (veh, wx, stop, trig), by_ped in groups.items():
        by_egos: dict[tuple, list[float]] = defaultdict(list)
        for ped, egos in by_ped.items():
            by_egos[tuple(sorted(egos))].append(ped)
        for egos, peds in by_egos.items():
            blocks[(veh, wx, stop, egos, tuple(sorted(peds)))].append(trig)
    order = {"etron": 0, "model3": 1, "patrol": 2, "sprinter": 3}
    families = []
    for (veh, wx, stop, egos, peds), trigs in sorted(blocks.items(), key=lambda kv: (order[kv[0][0]], kv[0][1] != "CLEAR", kv[0][1], kv[0][2], -len(kv[1]) * len(kv[0][3]) * len(kv[0][4]))):
        trigs = sorted(trigs)
        for i in range(0, len(peds), MAX_AXIS):
            chunk = list(peds[i:i + MAX_AXIS])
            variants = [{"ego_speed_kmh": e, "trigger_distance_m": t, "pedestrian_speed_mps": p,
                         "bench_cases": points[(veh, wx, stop, e, t, p)]} for e in egos for t in trigs for p in chunk]
            n = len(families) + 1
            families.append({
                "key": f"{veh}-{n:02d}", "vehicle": veh, "vehicle_match": next(m for k, m in VEHICLES.values() if k == veh),
                "name": f"AEB bench {n:02d} · {VEHICLE_LABEL[veh]} · {wx}{' · dừng lề' if stop else ''}",
                "weather": wx, "stops_at_curb": stop,
                "ego_speeds_kmh": list(egos), "trigger_distances_m": trigs, "pedestrian_speeds_mps": chunk,
                "variants": variants,
            })
    n_var = sum(len(f["variants"]) for f in families)
    out = {
        "note": "Mọi ca của 4 đợt bench → họ CP_CROSSING (DAY), AEB VehicSim thay lệnh phanh cố định. Sinh bởi aeb/sinh_bien_the.py.",
        "bench_runs_total": total,
        "dropped_bench_runs": dropped,
        "families": families,
    }
    Path(__file__).with_name("bien_the.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    kept = sum(len(v) for v in points.values())
    print(f"{total} lượt bench → giữ {kept}, bỏ {total - kept}; {len(families)} họ, {n_var} biến thể")
    for reason, labels in dropped.items():
        print(f"  bỏ {len(labels):4d}: {reason}")
    per_vehicle = defaultdict(int)
    for f in families:
        per_vehicle[f["vehicle"]] += len(f["variants"])
    print("  biến thể theo xe:", dict(per_vehicle))


if __name__ == "__main__":
    main()
