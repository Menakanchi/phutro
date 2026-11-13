"""Mô hình động học lý tưởng (thiết kế mục 2) và profile bàn đạp open-loop (mục 3).

Xe: giữ v0 trong t_d, giảm tốc tăng tuyến tính với tốc độ J tới a_e = min(a, μ·g), rồi giảm tốc đều tới khi dừng.
Người đi bộ: đạt ngay tốc độ v_p, đi vuông góc với làn từ vỉa hè.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

G = 9.81


def target_decel(a: float | str, full_brake: float) -> float:
    """Mức đích danh nghĩa (m/s²): 'max' = phanh 100% đã đo."""
    return full_brake if a == "max" else float(a)


def effective_decel(a: float | str, full_brake: float, mu: float) -> float:
    """a_e = min(a, μ·g)."""
    return min(target_decel(a, full_brake), mu * G)


def pedal_target(a: float | str, full_brake: float) -> float:
    """Bàn đạp đích = a / a_100%, kẹp [0, 1]; 'max' = 1,0."""
    return 1.0 if a == "max" else max(0.0, min(1.0, float(a) / full_brake))


def pedal_at(tau: float, a: float | str, full_brake: float, delay: float, jerk: float) -> float:
    """Bàn đạp ở thời điểm tau (s) kể từ lệnh phanh: 0 trong t_d, rồi tăng với tốc độ J / a_100% tới bàn đạp đích."""
    if tau < delay:
        return 0.0
    return min(pedal_target(a, full_brake), (tau - delay) * jerk / full_brake)


def stopping_distance(v0: float, a_e: float, jerk: float, delay: float) -> float:
    """Quãng dừng (m) tính từ lệnh phanh, dạng đóng."""
    if v0 <= 0:
        return 0.0
    t_r = a_e / jerk
    dv_ramp = a_e * a_e / (2 * jerk)
    if v0 <= dv_ramp:  # dừng ngay trong pha tăng lực: v0 = J t²/2
        t = math.sqrt(2 * v0 / jerk)
        return v0 * delay + v0 * t - jerk * t ** 3 / 6
    v1 = v0 - dv_ramp
    return v0 * delay + v0 * t_r - jerk * t_r ** 3 / 6 + v1 * v1 / (2 * a_e)


def stopping_time(v0: float, a_e: float, jerk: float, delay: float) -> float:
    """Thời gian (s) từ lệnh phanh tới khi dừng."""
    if v0 <= 0:
        return 0.0
    dv_ramp = a_e * a_e / (2 * jerk)
    if v0 <= dv_ramp:
        return delay + math.sqrt(2 * v0 / jerk)
    return delay + a_e / jerk + (v0 - dv_ramp) / a_e


def decel_at(tau: float, a_e: float, jerk: float, delay: float) -> float:
    """Giảm tốc lý tưởng (m/s², dương) ở tau kể từ lệnh phanh, trước khi dừng."""
    if tau < delay:
        return 0.0
    return min(a_e, (tau - delay) * jerk)


def brake_profile(v0: float, a_e: float, jerk: float, delay: float, dt: float, tail_s: float = 0.0) -> list[dict]:
    """Chuỗi (tau, v, s, decel) từ lệnh phanh tới khi dừng (+ tail_s đứng yên), tích phân chính xác từng bước dt."""
    rows, tau, v, s = [], 0.0, v0, 0.0
    t_stopped = None
    while True:
        d = decel_at(tau, a_e, jerk, delay) if v > 0 else 0.0
        rows.append({"tau": round(tau, 6), "v": max(v, 0.0), "s": s, "decel": d})
        # bước kế: trung bình giảm tốc đầu / cuối bước (giảm tốc tuyến tính từng đoạn nên chính xác tới sai số làm tròn)
        d_next = decel_at(tau + dt, a_e, jerk, delay)
        d_avg = (d + d_next) / 2
        v_next = v - d_avg * dt
        if v_next <= 0:
            s += v * v / (2 * d_avg) if d_avg > 0 else 0.0
            v_next = 0.0
        else:
            s += (v + v_next) / 2 * dt
        if v <= 0 and t_stopped is None:
            t_stopped = tau
        if t_stopped is not None and tau >= t_stopped + tail_s - 1e-9:
            return rows
        v, tau = v_next, tau + dt


def corridor_half_width(vehicle_width: float, margin: float) -> float:
    """Nửa hành lang của xe (m): người có |lat| ≤ giá trị này là trong đường đi."""
    return vehicle_width / 2 + margin


def walker_enter_time(start_lat: float, speed: float, half_width: float) -> float:
    """Thời gian (s) từ lúc bắt đầu đi tới khi người chạm hành lang, người đạt ngay tốc độ."""
    return max(0.0, (abs(start_lat) - half_width) / speed)


def walker_lat(t: float, start_lat: float, speed: float, stop_lat: float | None = None) -> float:
    """Vị trí ngang (m) sau t giây; stop_lat = vị trí dừng ở lề (None = đi tiếp)."""
    lat = start_lat + speed * max(0.0, t)
    return min(lat, stop_lat) if stop_lat is not None else lat


def brake_distance_before_line(v0: float, a_e: float, jerk: float, delay: float, margin: float) -> float:
    """G3: xe ra lệnh phanh khi mũi xe còn cách vạch băng qua D_b = quãng dừng tham chiếu + margin."""
    return stopping_distance(v0, a_e, jerk, delay) + margin


def ttc_compensation(v: float, a_band: float | None, a_e: float) -> float | None:
    """ΔTTC (s) cần phanh sớm thêm để bù giảm tốc thực a_band < a_e: v/2 · (1/a_band − 1/a_e)."""
    if not a_band or a_band <= 0 or a_e <= 0:
        return None
    return v / 2 * (1 / a_band - 1 / a_e)


@dataclass(frozen=True)
class CombinedReference:
    """Tham chiếu G3, mốc t = 0 lúc người bắt đầu đi."""

    t_brake: float           # lệnh phanh
    t_enter: float           # người chạm hành lang
    t_stop: float            # xe dừng
    stop_gap_m: float        # mũi xe cách vạch băng qua khi dừng (âm = vượt vạch)
    collision: bool
    min_gap_m: float | None  # khoảng cách nhỏ nhất mũi xe – vạch khi người trong hành lang


def combined_reference(v0: float, trigger: float, d_brake: float, a_e: float, jerk: float, delay: float,
                       start_lat: float, ped_speed: float, half_width: float, dt: float) -> CombinedReference:
    """Mũi xe cách vạch `trigger` lúc người bắt đầu đi; xe ra lệnh phanh khi còn cách d_brake."""
    t_brake = max(0.0, (trigger - d_brake) / v0)
    t_enter = walker_enter_time(start_lat, ped_speed, half_width)
    t_exit = (abs(start_lat) + half_width) / ped_speed  # người ra khỏi hành lang phía bên kia
    profile = brake_profile(v0, a_e, jerk, delay, dt)
    t_stop = t_brake + profile[-1]["tau"]
    stop_gap = trigger - v0 * t_brake - profile[-1]["s"]

    def gap(t: float) -> float:
        if t <= t_brake:
            return trigger - v0 * t
        tau = t - t_brake
        i = min(int(round(tau / dt)), len(profile) - 1)
        return trigger - v0 * t_brake - profile[i]["s"]

    gaps, collision, t = [], False, 0.0
    while t <= max(t_stop, t_exit) + 1e-9:
        if t_enter <= t <= t_exit:
            g = gap(t)
            gaps.append(g)
            if g <= 0:
                collision = True
        t += dt
    return CombinedReference(t_brake=t_brake, t_enter=t_enter, t_stop=t_stop, stop_gap_m=stop_gap, collision=collision,
                             min_gap_m=min(gaps) if gaps else None)
