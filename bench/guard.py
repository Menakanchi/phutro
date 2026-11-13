"""Canh server CARLA: kiểm cổng, kết nối, tự bật lại CarlaUE4.exe (nếu có đường dẫn), trả server về trạng thái sạch."""

from __future__ import annotations

import socket
import subprocess
import time
from pathlib import Path


class ServerDown(RuntimeError):
    """Server CARLA không phản hồi."""


def port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def connect(carla, may: dict):
    """Client đã kết nối và nạp được world; lỗi thì ServerDown."""
    if not port_open(may["host"], int(may["port"])):
        raise ServerDown(f"không có server CARLA ở {may['host']}:{may['port']}")
    client = carla.Client(may["host"], int(may["port"]))
    client.set_timeout(float(may.get("timeout_s", 60)))
    try:
        client.get_world()
    except RuntimeError as e:  # time-out khi server đang nạp map hoặc treo
        raise ServerDown(str(e)) from e
    return client


def start_server(may: dict, log=print) -> bool:
    """Bật CarlaUE4.exe nếu config có carla_root. Trả False khi không có đường dẫn (người chạy phải bật tay)."""
    root = (may.get("carla_root") or "").strip()
    if not root:
        return False
    exe = Path(root) / "CarlaUE4.exe"
    if not exe.exists():
        raise ServerDown(f"không thấy {exe} — sửa may.carla_root trong config.yaml")
    log(f"  bật lại CARLA: {exe}")
    flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen([str(exe), *may.get("carla_args", [])], cwd=str(exe.parent), creationflags=flags,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


def wait_ready(carla, may: dict, timeout_s: float = 240.0, log=print):
    """Đợi cổng mở rồi đợi get_world() trả lời (map nạp xong)."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if port_open(may["host"], int(may["port"])):
            try:
                return connect(carla, may)
            except ServerDown:
                pass
        time.sleep(3)
    raise ServerDown(f"CARLA chưa sẵn sàng sau {int(timeout_s)} s")


def ensure_server(carla, may: dict, log=print):
    """Client dùng được. Server chết: bật lại (nếu được phép) và đợi; không được phép: ServerDown kèm hướng dẫn."""
    try:
        return connect(carla, may)
    except ServerDown:
        if not start_server(may, log):
            raise ServerDown("CARLA không chạy. Bật CarlaUE4.exe (Town04) rồi chạy lại với --resume, "
                             "hoặc điền may.carla_root trong config.yaml để công cụ tự bật.") from None
        return wait_ready(carla, may, log=log)


def release_world(world) -> None:
    """Trả server về chế độ không đồng bộ — không để server đứng ở synchronous mode khi công cụ thoát."""
    try:
        settings = world.get_settings()
        settings.synchronous_mode = False
        settings.fixed_delta_seconds = None
        world.apply_settings(settings)
    except RuntimeError:
        pass
