"""Dựng cảnh và chạy một run trên CARLA (thiết kế mục 3).

Hệ tọa độ làn: ``s`` dọc road 40 (m, cùng gốc với OpenDRIVE), ``lat`` ngang so với tâm lane −4, âm về phía lề phải (vỉa hè);
người đi bộ xuất phát ở lat = −3,6 và đi về phía lat dương. Công cụ tự tick ở chế độ đồng bộ 0,01 s.
"""

from __future__ import annotations

import math
import time

from bench import model
from bench.guard import release_world

LOW_SPEED_STOP = 0.05     # m/s: coi là đã dừng
STOP_HOLD_S = 0.5         # giữ dừng bao lâu thì kết thúc run
WALKER_IDLE_S = 1.0       # G2/G4: đứng yên trước khi đi
WALKER_TAIL_S = 2.0       # G4: đứng ở lề bao lâu sau khi dừng


class SceneError(RuntimeError):
    """Lỗi dựng cảnh (spawn hỏng, waypoint không có...) — run bị loại, không phải lỗi server."""


def _dot(a, b) -> float:
    return a.x * b.x + a.y * b.y + a.z * b.z


class LaneFrame:
    """Chiếu vị trí thế giới lên (s, lat) của lane −4 quanh một điểm gốc. Road 40 là đoạn thẳng (kiểm ở `check`)."""

    def __init__(self, wp, s0: float):
        t = wp.transform
        self.origin, self.s0 = t.location, s0
        self.f, self.r = t.get_forward_vector(), t.get_right_vector()
        self.yaw = t.rotation.yaw

    def s(self, loc) -> float:
        return self.s0 + _dot(loc - self.origin, self.f)

    def lat(self, loc) -> float:
        return -_dot(loc - self.origin, self.r)


def setup_world(client, carla, cfg: dict):
    world = client.get_world()
    if world.get_map().name.split("/")[-1] != cfg["canh"]["map"]:
        world = client.load_world(cfg["canh"]["map"])
    release_world(world)
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = float(cfg["canh"]["step_s"])
    settings.no_rendering_mode = False
    world.apply_settings(settings)
    world.tick()
    return world


def _waypoint(world, cfg: dict, s: float):
    c = cfg["canh"]
    wp = world.get_map().get_waypoint_xodr(int(c["road_id"]), int(c["lane_id"]), float(s))
    if wp is None:
        raise SceneError(f"không có waypoint road {c['road_id']} lane {c['lane_id']} s={s:.1f}")
    return wp


def _spawn_vehicle(world, carla, cfg: dict, wp, tire_scale: float):
    xe = cfg["xe"]
    tf = carla.Transform(wp.transform.location + carla.Location(z=0.3), wp.transform.rotation)
    vehicle = world.try_spawn_actor(world.get_blueprint_library().find(xe["blueprint"]), tf)
    if vehicle is None:
        raise SceneError("không spawn được xe (vị trí bị chiếm?)")
    pc = vehicle.get_physics_control()
    pc.mass = float(xe["mass_kg"])
    wheels = list(pc.wheels)  # CARLA trả bản sao: sửa rồi gán lại cả danh sách
    for w in wheels:
        w.max_brake_torque = float(xe["max_brake_torque_nm"])
        w.tire_friction = w.tire_friction * tire_scale
    pc.wheels = wheels
    vehicle.apply_physics_control(pc)
    return vehicle


def _physics_snapshot(vehicle) -> dict:
    pc = vehicle.get_physics_control()
    return {"mass": float(pc.mass),
            "wheels": [{"max_brake_torque": float(w.max_brake_torque), "tire_friction": float(w.tire_friction)} for w in pc.wheels]}


def _spawn_walker(world, carla, cfg: dict, frame: LaneFrame, s_cross: float):
    nd = cfg["nguoi_di_bo"]
    wp = _waypoint(world, cfg, s_cross)
    t = wp.transform
    loc = t.location + t.get_right_vector() * abs(float(nd["start_lat_m"]))
    bp = world.get_blueprint_library().find(nd["blueprint"])
    if bp.has_attribute("is_invincible"):
        bp.set_attribute("is_invincible", "false")
    rot = carla.Rotation(yaw=t.rotation.yaw - 90.0)  # quay mặt về phía làn (ngược vector phải)
    for dz in (1.0, 1.5, 2.0):
        walker = world.try_spawn_actor(bp, carla.Transform(loc + carla.Location(z=dz), rot))
        if walker is not None:
            return walker
    raise SceneError("không spawn được người đi bộ")


def run_case(client, carla, cfg: dict, case) -> tuple[dict, list[dict]]:
    """Chạy một run. Trả (thông tin run, danh sách khung). Luôn dọn actor và trả server về async."""
    world = setup_world(client, carla, cfg)
    actors, frames, info = [], [], {"events": {}}
    dt = float(cfg["canh"]["step_s"])
    weather = cfg["thoi_tiet"][case.weather]
    world.set_weather(getattr(carla.WeatherParameters, weather["preset"]))
    xe, ph = cfg["xe"], cfg["phanh"]
    full = float(xe["full_brake_decel_mps2"])
    a_e = model.effective_decel(case.a, full, float(weather["mu"]))
    v_target = case.ego_kmh / 3.6
    half = model.corridor_half_width(float(xe["width_m"]), float(cfg["nguoi_di_bo"]["corridor_margin_m"]))
    start_s = float(cfg["canh"]["start_s"])
    collisions: list[dict] = []
    wall_start = time.time()
    try:
        wp0 = _waypoint(world, cfg, start_s)
        frame = LaneFrame(wp0, start_s)
        vehicle = walker = None
        front_off = 0.0
        if case.kind in ("brake", "combined"):
            vehicle = _spawn_vehicle(world, carla, cfg, wp0, case.tire_friction_scale)
            actors.append(vehicle)
            bb = vehicle.bounding_box
            front_off = bb.location.x + bb.extent.x
            col = world.spawn_actor(world.get_blueprint_library().find("sensor.other.collision"), carla.Transform(), attach_to=vehicle)
            actors.append(col)
            col.listen(lambda e: collisions.append({"frame": e.frame, "other": e.other_actor.type_id}))
        d_brake = model.brake_distance_before_line(v_target, a_e, float(ph["jerk_mps3"]), float(ph["delay_s"]), float(ph["margin_m"]))
        if case.kind == "combined":
            s_cross = start_s + front_off + v_target * float(cfg["canh"]["settle_s"]) + 10.0 + max(case.trigger_m, d_brake) + 5.0
        else:
            s_cross = start_s + 50.0
        if s_cross > float(cfg["canh"]["road_length_m"]) - 15:
            raise SceneError(f"vạch băng qua s={s_cross:.0f} m vượt đoạn road 40")
        if case.kind in ("walker", "combined"):
            walker = _spawn_walker(world, carla, cfg, frame, s_cross)
            actors.append(walker)
        info.update(s_cross=s_cross, front_offset_m=front_off, d_brake_m=d_brake, a_e=a_e, corridor_half_m=half)

        for _ in range(int(0.5 / dt)):  # tiếp đất
            world.tick()
        if vehicle is not None:
            info["physics"] = _physics_snapshot(vehicle)
            vehicle.enable_constant_velocity(carla.Vector3D(v_target, 0.0, 0.0))

        t0 = world.get_snapshot().timestamp.elapsed_seconds
        last_ts = t0
        t_cmd = t_walk = t_stop_since = t_walker_still = None
        cruising = vehicle is not None
        pedal = 0.0
        walk_dir = carla.Vector3D(-frame.r.x, -frame.r.y, 0.0)
        stop_lat = -float(cfg["canh"]["lane_half_width_m"]) if case.stop_at_curb else None
        timeout = float(cfg["gioi_han"]["run_timeout_s"])
        while True:
            world.tick()
            snap = world.get_snapshot()
            now = snap.timestamp.elapsed_seconds
            t = now - t0
            step = now - last_ts
            last_ts = now
            row = {"t": round(t, 4), "step": round(step, 5)}
            if vehicle is not None:
                tr = vehicle.get_transform()
                vel, acc = vehicle.get_velocity(), vehicle.get_acceleration()
                fwd = tr.get_forward_vector()
                front_s = frame.s(tr.location) + front_off
                v = _dot(vel, fwd)
                row.update(ego_s_front=round(front_s, 4), ego_lat=round(frame.lat(tr.location), 4), ego_v=round(v, 4),
                           ego_a=round(_dot(acc, fwd), 4))
                # --- lệnh phanh ---
                if t_cmd is None:
                    due = (t >= float(cfg["canh"]["settle_s"])) if case.kind == "brake" else (front_s >= s_cross - d_brake)
                    if due:
                        t_cmd = t
                        info["events"]["brake_cmd"] = t
                        info["v_at_cmd"] = v
                        info["s_front_at_cmd"] = front_s
                if t_cmd is not None:
                    tau = t - t_cmd
                    if cruising and tau >= float(ph["delay_s"]):
                        vehicle.disable_constant_velocity()
                        cruising = False
                    pedal = model.pedal_at(tau, case.a, full, float(ph["delay_s"]), float(ph["jerk_mps3"]))
                    if not cruising:
                        vehicle.apply_control(carla.VehicleControl(throttle=0.0, brake=pedal, steer=0.0))
                row.update(pedal_cmd=round(pedal, 4), pedal_applied=round(vehicle.get_control().brake, 4))
            if walker is not None:
                wl = walker.get_location()
                wlat = frame.lat(wl)
                if t_walk is None:
                    due = (t >= WALKER_IDLE_S) if case.kind == "walker" else (row["ego_s_front"] >= s_cross - case.trigger_m)
                    if due:
                        t_walk = t
                        info["events"]["walker_start"] = t
                        info["walker_start_lat"] = wlat
                speed = 0.0
                if t_walk is not None:
                    speed = case.ped_mps if (stop_lat is None or wlat < stop_lat) else 0.0
                walker.apply_control(carla.WalkerControl(direction=walk_dir, speed=speed, jump=False))
                wv = walker.get_velocity()
                row.update(walker_s=round(frame.s(wl), 4), walker_lat=round(wlat, 4),
                           walker_v=round(math.hypot(wv.x, wv.y), 4), walker_cmd=speed)
            row["collision"] = bool(collisions)
            frames.append(row)

            # --- điều kiện kết thúc ---
            if t > timeout:
                info["end_reason"] = "TIMEOUT"
                break
            if vehicle is not None and t_cmd is not None:
                if row["ego_v"] < LOW_SPEED_STOP:
                    t_stop_since = t if t_stop_since is None else t_stop_since
                    if t - t_stop_since >= STOP_HOLD_S:
                        info["events"].setdefault("stopped", t_stop_since)
                        info["end_reason"] = "STOPPED"
                        if case.kind == "brake" or walker is None or row["walker_lat"] > half or t - t_stop_since >= 2.0:
                            break
                else:
                    t_stop_since = None
            if case.kind == "walker" and t_walk is not None:
                if stop_lat is None and row["walker_lat"] >= abs(float(cfg["nguoi_di_bo"]["start_lat_m"])):
                    info["end_reason"] = "CROSSED"
                    break
                if stop_lat is not None and row["walker_v"] < LOW_SPEED_STOP and row["walker_lat"] > stop_lat - 0.5:
                    t_walker_still = t if t_walker_still is None else t_walker_still
                    if t - t_walker_still >= WALKER_TAIL_S:
                        info["end_reason"] = "STOPPED_AT_CURB"
                        break
                else:
                    t_walker_still = None
        info["collisions"] = collisions
        info["sim_duration_s"] = frames[-1]["t"] if frames else 0.0
        info["wall_s"] = round(time.time() - wall_start, 1)
        return info, frames
    finally:
        for a in reversed(actors):
            try:
                if a.type_id.startswith("sensor."):
                    a.stop()
                a.destroy()
            except RuntimeError:
                pass
        try:
            world.tick()
        except RuntimeError:
            pass
        release_world(world)
