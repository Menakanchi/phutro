"""Chạy lô: mỗi run một thư mục (run.json + frames.csv), state.json để chạy tiếp, tự xử lý server chết."""

from __future__ import annotations

import csv
import json
import platform
import subprocess
import time
import traceback
from datetime import datetime
from pathlib import Path

from bench import __version__, guard, model
from bench.scene import SceneError, run_case


def new_run_dir(root: Path) -> Path:
    d = root / datetime.now().strftime("%Y-%m-%d_%H%M")
    d.mkdir(parents=True, exist_ok=True)
    return d


def tool_commit(repo: Path) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10)
        dirty = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() + ("-dirty" if dirty.stdout.strip() else "") if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def machine_info(client=None) -> dict:
    info = {"os": platform.platform(), "python": platform.python_version(), "machine": platform.node(), "tool_version": __version__}
    try:
        gpu = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True, text=True, timeout=10)
        info["gpu"] = gpu.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        info["gpu"] = None
    if client is not None:
        info["carla_server"] = client.get_server_version()
        info["carla_client"] = client.get_client_version()
    return info


def write_frames(path: Path, frames: list[dict]) -> None:
    keys: list[str] = []
    for f in frames:
        for k in f:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(frames)


def load_state(run_dir: Path) -> dict:
    p = run_dir / "state.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"done": {}, "failed": {}}


def save_state(run_dir: Path, state: dict) -> None:
    (run_dir / "state.json").write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding="utf-8")


def reference_summary(case, cfg: dict) -> dict:
    """Số tham chiếu (không cần CARLA) cho --dry-run và để ghi kèm run."""
    xe, ph, nd = cfg["xe"], cfg["phanh"], cfg["nguoi_di_bo"]
    mu = float(cfg["thoi_tiet"][case.weather]["mu"])
    full = float(xe["full_brake_decel_mps2"])
    a_e = model.effective_decel(case.a, full, mu)
    v0 = case.ego_kmh / 3.6
    half = model.corridor_half_width(float(xe["width_m"]), float(nd["corridor_margin_m"]))
    out = {"a_e": round(a_e, 3), "pedal_target": round(model.pedal_target(case.a, full), 3)}
    if case.kind in ("brake", "combined"):
        out["stop_dist_m"] = round(model.stopping_distance(v0, a_e, float(ph["jerk_mps3"]), float(ph["delay_s"])), 3)
        out["stop_time_s"] = round(model.stopping_time(v0, a_e, float(ph["jerk_mps3"]), float(ph["delay_s"])), 3)
    if case.kind in ("walker", "combined"):
        out["walker_enter_s"] = round(model.walker_enter_time(float(nd["start_lat_m"]), case.ped_mps, half), 3)
    if case.kind == "combined":
        d_b = model.brake_distance_before_line(v0, a_e, float(ph["jerk_mps3"]), float(ph["delay_s"]), float(ph["margin_m"]))
        ref = model.combined_reference(v0, case.trigger_m, d_b, a_e, float(ph["jerk_mps3"]), float(ph["delay_s"]),
                                       float(nd["start_lat_m"]), case.ped_mps, half, float(cfg["canh"]["step_s"]))
        out.update(d_brake_m=round(d_b, 3), ref_collision=ref.collision,
                   ref_min_gap_m=None if ref.min_gap_m is None else round(ref.min_gap_m, 3))
    return out


def run_all(carla, cfg: dict, runs: list, run_dir: Path, tool_repo: Path, log=print) -> dict:
    state = load_state(run_dir)
    may = cfg["may"]
    client = guard.ensure_server(carla, may, log)
    meta_path = run_dir / "meta.json"
    if not meta_path.exists():
        meta = {"started": datetime.now().isoformat(timespec="seconds"), "tool_commit": tool_commit(tool_repo),
                "machine": machine_info(client), "config": cfg}
        meta_path.write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    todo = [c for c in runs if c.run_id not in state["done"]]
    log(f"{len(runs) - len(todo)} run đã xong, còn {len(todo)}")
    for i, case in enumerate(todo, 1):
        out = run_dir / case.run_id
        out.mkdir(exist_ok=True)
        attempts = int(cfg["gioi_han"]["retries"]) + 1
        for attempt in range(1, attempts + 1):
            log(f"[{i}/{len(todo)}] {case.run_id} (lần {attempt})")
            try:
                info, frames = run_case(client, carla, cfg, case)
            except SceneError as e:
                info, frames = {"scene_error": str(e)}, []
                log(f"  lỗi dựng cảnh: {e}")
            except (RuntimeError, guard.ServerDown) as e:
                log(f"  mất kết nối CARLA: {e}")
                if attempt == attempts:
                    state["failed"][case.run_id] = str(e)
                    save_state(run_dir, state)
                    raise
                time.sleep(5)
                client = guard.ensure_server(carla, may, log)
                continue
            except Exception as e:  # lỗi lạ: ghi lại, chạy run kế
                info, frames = {"scene_error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()}, []
                log(f"  lỗi: {e}")
            record = {"case": case.as_dict(), "reference": reference_summary(case, cfg), "carla": info}
            (out / "run.json").write_text(json.dumps(record, indent=1, ensure_ascii=False), encoding="utf-8")
            if frames:
                write_frames(out / "frames.csv", frames)
            state["done"][case.run_id] = {"end": info.get("end_reason") or info.get("scene_error"), "wall_s": info.get("wall_s")}
            state["failed"].pop(case.run_id, None)
            save_state(run_dir, state)
            log(f"  xong: {state['done'][case.run_id]['end']}, {info.get('sim_duration_s', 0)} s mô phỏng")
            break
    return state
