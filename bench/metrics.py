"""Chỉ số (thiết kế mục 6) và quy tắc hợp lệ (mục 7) từ run.json + frames.csv."""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path

from bench import model

BAND_LOW_MPS = 6.0          # dưới mức này CARLA "dừng tức thì" (TD-17 của VehicSim)
BAND_MIN_SAMPLES = 5
BAND_MIN_S = 0.3
SMOOTH_N = 10               # trung bình trượt 0,1 s cho gia tốc
SPEED_TOL_KMH = 1.0         # chạy đều của CARLA dao động ~±0,4 km/h
MASS_TOL = 1e-3
STOPPED = 0.05


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load_run(run_path: Path) -> tuple[dict, list[dict]]:
    record = json.loads((run_path / "run.json").read_text(encoding="utf-8"))
    frames = []
    fp = run_path / "frames.csv"
    if fp.exists():
        with open(fp, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                frames.append({k: (v if k == "collision" else _f(v)) for k, v in row.items()})
    return record, frames


def _centered(values: list[float], half: int = SMOOTH_N // 2) -> list[float]:
    """Trung bình trượt đối xứng (±half khung). Tốc độ CARLA dao động xen kẽ ±0,1 m/s giữa các tick khi chạy đều."""
    out = []
    for i in range(len(values)):
        w = values[max(0, i - half): i + half + 1]
        out.append(sum(w) / len(w))
    return out


def _decel_series(frames: list[dict], half: int = SMOOTH_N // 2) -> list[float]:
    """Giảm tốc (m/s², dương) từ tốc độ đã làm mượt, sai phân trung tâm ±half khung (0,1 s)."""
    vs = _centered([f["ego_v"] for f in frames], half)
    out = []
    for i in range(len(frames)):
        a, b = max(0, i - half), min(len(frames) - 1, i + half)
        dt = frames[b]["t"] - frames[a]["t"]
        out.append(-(vs[b] - vs[a]) / dt if dt > 0 else 0.0)
    return out


def speed_at_cmd(frames: list[dict], t_cmd: float) -> float | None:
    """Tốc độ lúc ra lệnh phanh = trung bình 0,1 s trước lệnh (khử dao động xen kẽ)."""
    w = [f["ego_v"] for f in frames if t_cmd - 0.1 - 1e-9 <= f["t"] <= t_cmd + 1e-9 and f.get("ego_v") is not None]
    return sum(w) / len(w) if w else None


def _r(x, nd=3):
    return None if x is None else round(x, nd)


def validity(record: dict, frames: list[dict], cfg: dict) -> list[str]:
    """Danh sách lý do loại; rỗng = hợp lệ."""
    case, info = record["case"], record["carla"]
    reasons = []
    if info.get("scene_error"):
        return [f"lỗi dựng cảnh: {info['scene_error']}"]
    if not frames:
        return ["không có khung dữ liệu"]
    if info.get("end_reason") == "TIMEOUT":
        reasons.append("hết thời gian mô phỏng")
    step = float(cfg["canh"]["step_s"])
    bad_steps = [f["step"] for f in frames[1:] if f.get("step") is not None and abs(f["step"] - step) > 1e-4]
    if bad_steps:
        reasons.append(f"bước mô phỏng khác {step} s ở {len(bad_steps)} khung")
    if case["kind"] in ("brake", "combined"):
        phys = info.get("physics") or {}
        mass = phys.get("mass")
        if mass is None or abs(mass - float(cfg["xe"]["mass_kg"])) > MASS_TOL * float(cfg["xe"]["mass_kg"]):
            reasons.append(f"khối lượng đọc lại {mass}")
        torques = [w["max_brake_torque"] for w in phys.get("wheels", [])]
        if not torques or any(abs(t - float(cfg["xe"]["max_brake_torque_nm"])) > 1 for t in torques):
            reasons.append(f"mô-men phanh đọc lại {torques}")
        t_cmd = info.get("events", {}).get("brake_cmd")
        v = speed_at_cmd(frames, t_cmd) if t_cmd is not None else None
        if v is None:
            reasons.append("không có lệnh phanh")
        elif abs(v * 3.6 - case["ego_kmh"]) > SPEED_TOL_KMH:
            reasons.append(f"tốc độ lúc phanh {v * 3.6:.2f} km/h lệch đích {case['ego_kmh']} quá {SPEED_TOL_KMH}")
    if case["kind"] in ("brake", "walker") and info.get("collisions"):
        reasons.append(f"va chạm ngoài dự kiến: {info['collisions'][0].get('other')}")
    if case["kind"] in ("walker", "combined") and info.get("events", {}).get("walker_start") is None:
        reasons.append("người đi bộ không bắt đầu đi")
    return reasons


def brake_metrics(record: dict, frames: list[dict], cfg: dict) -> dict:
    info, ph = record["carla"], cfg["phanh"]
    td, jerk = float(ph["delay_s"]), float(ph["jerk_mps3"])
    t_cmd, a_e = info["events"]["brake_cmd"], info["a_e"]
    v0 = speed_at_cmd(frames, t_cmd)
    decel_all = _decel_series(frames)
    first = next(i for i, f in enumerate(frames) if f["t"] >= t_cmd - 1e-9)
    after, decel = frames[first:], decel_all[first:]
    stop_i = next((i for i, f in enumerate(after) if f["t"] > t_cmd + td and f["ego_v"] < STOPPED), None)
    moving = after[: stop_i + 1] if stop_i is not None else after
    out = {"v0_kmh": _r(v0 * 3.6, 2), "a_e": _r(a_e)}
    # dải đo pha phanh đều: sau khi mô hình đã đạt đủ lực (t_d + a_e/J), từ ≤ 0,95·v0 xuống 6 m/s. Trễ tăng lực đo riêng bằng t90.
    t_full = t_cmd + td + a_e / jerk
    band = [(f["t"], f["ego_v"]) for f in moving if f["t"] >= t_full and BAND_LOW_MPS <= f["ego_v"] <= 0.95 * v0]
    a_band = None
    if len(band) >= BAND_MIN_SAMPLES and band[-1][0] - band[0][0] >= BAND_MIN_S:
        a_band = -statistics.linear_regression([t for t, _ in band], [v for _, v in band]).slope
    out["a_band"] = _r(a_band)
    out["eta"] = _r(a_band / a_e) if a_band else None
    # đỉnh trong vùng tốc độ cao (≥ 7 m/s): làm mượt 0,1 s quanh 6 m/s vẫn kéo cú "dừng tức thì" vào nếu lấy sát ngưỡng
    hi = [d for f, d in zip(moving, decel) if f["ego_v"] >= BAND_LOW_MPS + 1.0 and f["t"] >= t_cmd + td]
    out["a_peak"] = _r(max(hi) if hi else None)
    t90 = next((f["t"] - t_cmd for f, d in zip(moving, decel) if f["t"] >= t_cmd and d >= 0.9 * a_e), None)
    out["t90_carla_s"] = _r(t90)
    out["t90_ref_s"] = _r(td + 0.9 * a_e / jerk)
    out["t90_delta_s"] = _r(t90 - out["t90_ref_s"]) if t90 is not None else None
    # vùng tốc độ thấp: từ lúc v < 6 m/s tới khi dừng
    if stop_i is not None and v0 > BAND_LOW_MPS:
        i6 = next(i for i, f in enumerate(moving) if f["t"] >= t_cmd + td and f["ego_v"] < BAND_LOW_MPS)
        f6, fs = moving[i6], moving[-1]
        out["low_speed_decel"] = _r(f6["ego_v"] / (fs["t"] - f6["t"])) if fs["t"] > f6["t"] else None
    else:
        out["low_speed_decel"] = None
    ref_d = model.stopping_distance(v0, a_e, jerk, td)
    out["stop_dist_ref_m"] = _r(ref_d)
    if stop_i is not None:
        d = moving[-1]["ego_s_front"] - info["s_front_at_cmd"]
        out["stop_dist_carla_m"] = _r(d)
        out["stop_dist_delta_m"] = _r(d - ref_d)
        out["stop_time_carla_s"] = _r(moving[-1]["t"] - t_cmd)
    else:
        out.update(stop_dist_carla_m=None, stop_dist_delta_m=None, stop_time_carla_s=None)
    out["stop_time_ref_s"] = _r(model.stopping_time(v0, a_e, jerk, td))
    out["dttc_s"] = _r(model.ttc_compensation(v0, a_band, a_e))
    out["pedal_max"] = _r(max((f.get("pedal_applied") or 0) for f in after))
    return out


def walker_metrics(record: dict, frames: list[dict], cfg: dict) -> dict:
    case, info = record["case"], record["carla"]
    ws, lat0 = info["events"]["walker_start"], info["walker_start_lat"]
    vp, half = case["ped_mps"], info["corridor_half_m"]
    after = [f for f in frames if f["t"] >= ws - 1e-9]
    out = {"start_lat_m": _r(lat0)}
    t90 = next((f["t"] - ws for f in after if (f["walker_v"] or 0) >= 0.9 * vp), None)
    out["walker_t90_s"] = _r(t90)
    enter = next((f["t"] - ws for f in after if f["walker_lat"] >= -half), None)
    ref_enter = model.walker_enter_time(lat0, vp, half)
    out.update(enter_carla_s=_r(enter), enter_ref_s=_r(ref_enter),
               enter_delta_s=_r(enter - ref_enter) if enter is not None else None)
    if case["stop_at_curb"]:
        edge = -float(cfg["canh"]["lane_half_width_m"])
        final = after[-1]["walker_lat"]
        out.update(curb_stop_lat_m=_r(final), curb_overshoot_m=_r(final - edge))
    return out


def combined_metrics(record: dict, frames: list[dict], cfg: dict) -> dict:
    case, info, ph, nd = record["case"], record["carla"], cfg["phanh"], cfg["nguoi_di_bo"]
    ws = info["events"]["walker_start"]
    half = info["corridor_half_m"]
    start = next(f for f in frames if f["t"] >= ws - 1e-9)
    gaps = [f["walker_s"] - f["ego_s_front"] for f in frames if f["t"] >= ws and abs(f["walker_lat"]) <= half]
    v_start = speed_at_cmd(frames, start["t"])
    carla_coll = any("walker" in c.get("other", "") for c in info.get("collisions", []))
    trigger_meas = start["walker_s"] - start["ego_s_front"]
    ref = model.combined_reference(v_start, trigger_meas, info["d_brake_m"], info["a_e"], float(ph["jerk_mps3"]),
                                   float(ph["delay_s"]), info["walker_start_lat"], case["ped_mps"], half, float(cfg["canh"]["step_s"]))
    min_gap = min(gaps) if gaps else None
    return {"trigger_meas_m": _r(trigger_meas), "min_gap_carla_m": _r(min_gap), "min_gap_ref_m": _r(ref.min_gap_m),
            "min_gap_delta_m": _r(min_gap - ref.min_gap_m) if min_gap is not None and ref.min_gap_m is not None else None,
            "collision_carla": carla_coll or (min_gap is not None and min_gap <= 0), "collision_ref": ref.collision,
            "class_mismatch": (carla_coll or (min_gap is not None and min_gap <= 0)) != ref.collision}


def analyse_run(run_path: Path, cfg: dict) -> dict:
    record, frames = load_run(run_path)
    case = record["case"]
    row = {**{k: case[k] for k in ("run_id", "case_id", "group", "kind", "ego_kmh", "a", "ped_mps", "trigger_m", "stop_at_curb",
                                   "weather", "tire_friction_scale", "same_as")},
           "end_reason": record["carla"].get("end_reason")}
    reasons = validity(record, frames, cfg)
    row["valid"] = not reasons
    row["reasons"] = "; ".join(reasons)
    if reasons and (record["carla"].get("scene_error") or not frames):
        return row
    try:
        if case["kind"] in ("brake", "combined"):
            row.update(brake_metrics(record, frames, cfg))
        if case["kind"] in ("walker", "combined"):
            row.update(walker_metrics(record, frames, cfg))
        if case["kind"] == "combined":
            row.update(combined_metrics(record, frames, cfg))
    except (KeyError, StopIteration, ValueError, TypeError, ZeroDivisionError) as e:
        row["valid"] = False
        row["reasons"] = (row["reasons"] + "; " if row["reasons"] else "") + f"không tính được chỉ số: {type(e).__name__} {e}"
    return row


REPEAT_KEYS = ("a_band", "eta", "stop_dist_carla_m", "stop_dist_delta_m", "walker_t90_s", "enter_carla_s", "min_gap_carla_m")


def repeat_stats(rows: list[dict]) -> list[dict]:
    """Nhóm lặp: ca gốc (same_as) + các run -r<n>. Trả min / max / dải của từng chỉ số."""
    groups: dict[str, list[dict]] = {}
    base_of = {r["case_id"]: r["same_as"] for r in rows if r.get("same_as")}
    for r in rows:
        if not r["valid"]:
            continue
        key = base_of.get(r["case_id"]) or (r["case_id"] if r["case_id"] in base_of.values() else None)
        if key:
            groups.setdefault(key, []).append(r)
    out = []
    for base, items in groups.items():
        for k in REPEAT_KEYS:
            vals = [i[k] for i in items if i.get(k) is not None]
            if len(vals) >= 2:
                out.append({"base": base, "metric": k, "n": len(vals), "min": min(vals), "max": max(vals),
                            "range": round(max(vals) - min(vals), 4), "values": ", ".join(str(v) for v in vals)})
    return out
