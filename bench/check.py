"""`bench.py check` — kiểm máy và server trước khi chạy; mỗi lỗi kèm cách sửa (tiếng Việt)."""

from __future__ import annotations

import importlib.metadata
import math
import sys

from bench import guard


def _ok(msg):
    print(f"  [OK]   {msg}")


def _fail(msg, fix):
    print(f"  [LỖI]  {msg}\n         → {fix}")


def run_checks(cfg: dict) -> int:
    errors = 0
    print("Kiểm tra máy:")
    if sys.version_info[:2] == (3, 12):
        _ok(f"Python {sys.version.split()[0]}")
    else:
        errors += 1
        _fail(f"Python {sys.version.split()[0]}", "cần Python 3.12 (gói carla 0.9.16 cho Windows chỉ có bản cp312); chạy lại setup.ps1")
    try:
        import carla
        ver = importlib.metadata.version("carla")
        _ok(f"gói carla {ver}")
    except Exception as e:  # noqa: BLE001
        _fail(f"không import được carla: {e}", "chạy setup.ps1 (pip install carla==0.9.16)")
        return 1
    for mod in ("yaml", "openpyxl"):
        try:
            __import__(mod)
            _ok(f"gói {mod}")
        except ImportError:
            errors += 1
            _fail(f"thiếu gói {mod}", "chạy setup.ps1")

    print("Kiểm tra server CARLA:")
    may = cfg["may"]
    try:
        client = guard.connect(carla, may)
    except guard.ServerDown as e:
        _fail(str(e), "bật CarlaUE4.exe (đợi cửa sổ CARLA hiện map) rồi chạy lại check; kiểm host/port trong config.yaml")
        return 1
    server, client_ver = client.get_server_version(), client.get_client_version()
    if server.split("-")[0] == client_ver.split("-")[0] and server.startswith("0.9.16"):
        _ok(f"server {server}, client {client_ver}")
    else:
        errors += 1
        _fail(f"server {server}, client {client_ver}", "cần CARLA 0.9.16 cho cả server và gói carla; kết quả khác phiên bản không so được")
    if any(m.endswith(cfg["canh"]["map"]) for m in client.get_available_maps()):
        _ok(f"có map {cfg['canh']['map']}")
    else:
        errors += 1
        _fail(f"không có map {cfg['canh']['map']}", "cài bản CARLA đầy đủ (có Town04)")
        return errors
    world = client.get_world()
    if world.get_map().name.split("/")[-1] != cfg["canh"]["map"]:
        print(f"  ...   đang nạp {cfg['canh']['map']} (có thể mất 1–2 phút)")
        world = client.load_world(cfg["canh"]["map"])
    lib = world.get_blueprint_library()
    for bp in (cfg["xe"]["blueprint"], cfg["nguoi_di_bo"]["blueprint"], "sensor.other.collision"):
        if lib.filter(bp):
            _ok(f"blueprint {bp}")
        else:
            errors += 1
            _fail(f"thiếu blueprint {bp}", "cài bản CARLA 0.9.16 đầy đủ")
    c = cfg["canh"]
    m = world.get_map()
    a = m.get_waypoint_xodr(int(c["road_id"]), int(c["lane_id"]), 10.0)
    b = m.get_waypoint_xodr(int(c["road_id"]), int(c["lane_id"]), float(c["road_length_m"]) - 10.0)
    if a is None or b is None:
        errors += 1
        _fail(f"không có road {c['road_id']} lane {c['lane_id']}", "map Town04 khác bản 0.9.16?")
    else:
        dyaw = abs((a.transform.rotation.yaw - b.transform.rotation.yaw + 180) % 360 - 180)
        dist = a.transform.location.distance(b.transform.location)
        straight = dyaw < 1.0 and abs(dist - (float(c["road_length_m"]) - 20)) < 1.0
        (_ok if straight else lambda msg: _fail(msg, "đoạn đường không thẳng — báo lại người gửi công cụ"))(
            f"road {c['road_id']} thẳng: lệch hướng {dyaw:.2f}°, dài {dist:.1f} m")
        errors += 0 if straight else 1
    try:
        settings = world.get_settings()
        settings.synchronous_mode, settings.fixed_delta_seconds = True, float(c["step_s"])
        world.apply_settings(settings)
        t0 = world.get_snapshot().timestamp.elapsed_seconds
        for _ in range(10):
            world.tick()
        step = (world.get_snapshot().timestamp.elapsed_seconds - t0) / 10
        if math.isclose(step, float(c["step_s"]), abs_tol=1e-4):
            _ok(f"chế độ đồng bộ, bước {step:.3f} s")
        else:
            errors += 1
            _fail(f"bước đo được {step:.4f} s", "có client khác đang tick server? tắt web VehicSim / runner khác")
    finally:
        guard.release_world(world)
    print("Kết quả:", "SẴN SÀNG" if errors == 0 else f"{errors} lỗi — sửa rồi chạy lại check")
    return 0 if errors == 0 else 1
