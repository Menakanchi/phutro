"""Xuất ket-qua.xlsx (thiết kế mục 8) từ một thư mục runs/<ngày-giờ>/."""

from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from bench import metrics
from bench.metrics import load_run

HEAD = PatternFill("solid", fgColor="DDDDDD")
RED = PatternFill("solid", fgColor="F4CCCC")
GREY = PatternFill("solid", fgColor="EEEEEE")

CASE_COLS = [("run_id", "Run"), ("group", "Nhóm"), ("kind", "Loại"), ("ego_kmh", "Ego (km/h)"), ("a", "Mức đích (m/s²)"),
             ("ped_mps", "Người (m/s)"), ("trigger_m", "Kích hoạt (m)"), ("stop_at_curb", "Dừng lề"), ("weather", "Thời tiết"),
             ("tire_friction_scale", "Hệ số ma sát lốp"), ("same_as", "Lặp của")]
BRAKE_COLS = [("run_id", "Run"), ("ego_kmh", "Ego đích (km/h)"), ("a", "Mức đích"), ("weather", "Thời tiết"),
              ("tire_friction_scale", "Ma sát lốp ×"), ("v0_kmh", "v lúc phanh (km/h)"), ("a_e", "a_e mô hình (m/s²)"),
              ("pedal_max", "Bàn đạp tối đa"), ("a_band", "a_dải CARLA (m/s²)"), ("eta", "η = a_dải / a_e"),
              ("a_peak", "Đỉnh giảm tốc ≥7 m/s"), ("t90_carla_s", "Đạt 90% lực CARLA (s)"), ("t90_ref_s", "Đạt 90% mô hình (s)"),
              ("t90_delta_s", "Δ đạt lực (s)"), ("low_speed_decel", "Giảm tốc dưới 6 m/s"), ("stop_dist_carla_m", "Quãng dừng CARLA (m)"),
              ("stop_dist_ref_m", "Quãng dừng mô hình (m)"), ("stop_dist_delta_m", "Δ quãng dừng (m)"),
              ("stop_time_carla_s", "Thời gian dừng CARLA (s)"), ("stop_time_ref_s", "Thời gian dừng mô hình (s)"),
              ("dttc_s", "ΔTTC cần bù (s)")]
WALKER_COLS = [("run_id", "Run"), ("ped_mps", "Người đích (m/s)"), ("stop_at_curb", "Dừng lề"), ("start_lat_m", "Vị trí đầu (m)"),
               ("walker_t90_s", "Đạt 90% tốc độ (s)"), ("enter_carla_s", "Vào hành lang CARLA (s)"),
               ("enter_ref_s", "Vào hành lang mô hình (s)"), ("enter_delta_s", "Δ vào hành lang (s)"),
               ("curb_stop_lat_m", "Vị trí dừng lề (m)"), ("curb_overshoot_m", "Nhô vào làn (m)")]
COMBINED_COLS = [("run_id", "Run"), ("trigger_m", "Kích hoạt đích (m)"), ("trigger_meas_m", "Kích hoạt đo (m)"),
                 ("v0_kmh", "v lúc phanh (km/h)"), ("enter_carla_s", "Người vào hành lang CARLA (s)"),
                 ("enter_ref_s", "Người vào hành lang mô hình (s)"), ("stop_dist_delta_m", "Δ quãng dừng (m)"),
                 ("min_gap_carla_m", "Khoảng cách nhỏ nhất CARLA (m)"), ("min_gap_ref_m", "Khoảng cách nhỏ nhất mô hình (m)"),
                 ("min_gap_delta_m", "Δ khoảng cách (m)"), ("collision_carla", "Va chạm CARLA"), ("collision_ref", "Va chạm mô hình"),
                 ("class_mismatch", "Khác loại kết quả")]
FRAME_COLS = ["t", "step", "ego_s_front", "ego_lat", "ego_v", "ego_a", "pedal_cmd", "pedal_applied", "walker_s", "walker_lat",
              "walker_v", "walker_cmd", "collision"]


def _header(ws, labels: list[str], row: int = 1) -> None:
    for i, label in enumerate(labels, 1):
        c = ws.cell(row=row, column=i, value=label)
        c.font, c.fill = Font(bold=True), HEAD
        c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = f"B{row + 1}"  # chuỗi: ws.cell(...) sẽ tạo ô rỗng làm append ghi lùi một dòng


def _widths(ws, width: int = 14, first: int = 18) -> None:
    for i in range(1, ws.max_column + 1):
        ws.column_dimensions[get_column_letter(i)].width = first if i == 1 else width


def _table(ws, rows: list[dict], cols: list[tuple[str, str]], red_key: str | None = None) -> None:
    _header(ws, [label for _, label in cols])
    for r in rows:
        ws.append([r.get(k) for k, _ in cols])
        if red_key and r.get(red_key):
            for c in ws[ws.max_row]:
                c.fill = RED
    _widths(ws)


def _pivot(ws, rows: list[dict], key: str, title: str, top: int) -> int:
    """Bảng key theo tốc độ (dòng) × mức đích (cột) cho G1; trả dòng cuối."""
    speeds = sorted({r["ego_kmh"] for r in rows})
    levels = sorted({str(r["a"]) for r in rows}, key=lambda x: (x == "max", float(x) if x != "max" else 0))
    ws.cell(row=top, column=1, value=title).font = Font(bold=True)
    _header(ws, ["Ego (km/h)"] + [f"a = {lv}" for lv in levels], row=top + 1)
    for i, sp in enumerate(speeds):
        ws.cell(row=top + 2 + i, column=1, value=sp)
        for j, lv in enumerate(levels):
            hit = [r for r in rows if r["ego_kmh"] == sp and str(r["a"]) == lv]
            ws.cell(row=top + 2 + i, column=2 + j, value=hit[0].get(key) if hit else None)
    return top + 2 + len(speeds), len(levels)


def _chart(ws, title: str, y_title: str, top: int, n_rows: int, n_levels: int, anchor: str) -> None:
    ch = LineChart()
    ch.title, ch.y_axis.title, ch.x_axis.title = title, y_title, "Ego (km/h)"
    data = Reference(ws, min_col=2, max_col=1 + n_levels, min_row=top + 1, max_row=top + 1 + n_rows)
    ch.add_data(data, titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=top + 2, max_row=top + 1 + n_rows))
    ch.height, ch.width = 8, 16
    ws.add_chart(ch, anchor)


def export(run_dir: Path) -> Path:
    run_dir = Path(run_dir)
    meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
    cfg = meta["config"]
    run_paths = sorted(p for p in run_dir.iterdir() if (p / "run.json").exists())
    rows = [metrics.analyse_run(p, cfg) for p in run_paths]
    valid = [r for r in rows if r["valid"]]
    wb = Workbook()

    ws = wb.active
    ws.title = "Tổng quan"
    m = meta.get("machine", {})
    info = [("Bắt đầu", meta.get("started")), ("Máy", m.get("machine")), ("Hệ điều hành", m.get("os")), ("GPU", m.get("gpu")),
            ("CARLA server", m.get("carla_server")), ("Gói carla", m.get("carla_client")), ("Python", m.get("python")),
            ("Phiên bản công cụ", m.get("tool_version")), ("Commit công cụ", meta.get("tool_commit")),
            ("Xe", f"{cfg['xe']['blueprint']}, {cfg['xe']['mass_kg']} kg, mô-men phanh {cfg['xe']['max_brake_torque_nm']} N·m"),
            ("Phanh 100% dùng đổi bàn đạp (m/s²)", cfg["xe"]["full_brake_decel_mps2"]),
            ("Trễ t_d (s) / tăng lực J (m/s³)", f"{cfg['phanh']['delay_s']} / {cfg['phanh']['jerk_mps3']}"),
            ("Hành lang (nửa, m)", round(cfg["xe"]["width_m"] / 2 + cfg["nguoi_di_bo"]["corridor_margin_m"], 3)),
            ("Bản đồ / đoạn", f"{cfg['canh']['map']} road {cfg['canh']['road_id']} lane {cfg['canh']['lane_id']}, bước {cfg['canh']['step_s']} s"),
            ("Số run", len(rows)), ("Hợp lệ", len(valid)), ("Bị loại", len(rows) - len(valid)),
            ("Ghi chú", "Open-loop: lệnh phanh cố định, không AEB. Mô hình tham chiếu là động học lý tưởng (thiết kế mục 2). "
                        "η > 1: CARLA phanh mạnh hơn mức đích ở bàn đạp tương ứng."),
            ("Nhận xét", "")]
    for k, v in info:
        ws.append([k, v])
        ws.cell(row=ws.max_row, column=1).font = Font(bold=True)
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 34, 90

    ws = wb.create_sheet("Danh sách ca")
    _table(ws, rows, CASE_COLS + [("valid", "Hợp lệ"), ("end_reason", "Kết thúc")])

    brake_rows = [r for r in valid if r["kind"] == "brake"]
    ws = wb.create_sheet("Phanh")
    _table(ws, brake_rows, BRAKE_COLS)

    ws = wb.create_sheet("Theo tốc độ")
    g1 = [r for r in brake_rows if r["group"] == "G1"]
    if g1:
        end1, nlv = _pivot(ws, g1, "eta", "η = a_dải / a_e (G1)", 1)
        _chart(ws, "η theo tốc độ", "η", 1, end1 - 3, nlv, "I2")
        top2 = end1 + 2
        end2, _ = _pivot(ws, g1, "stop_dist_delta_m", "Δ quãng dừng CARLA − mô hình (m) (G1)", top2)
        _chart(ws, "Δ quãng dừng theo tốc độ", "m", top2, end2 - top2 - 2, nlv, f"I{top2 + 1}")
        top3 = end2 + 2
        _pivot(ws, g1, "dttc_s", "ΔTTC cần bù (s) (G1)", top3)
        top4 = top3 + 10
        _pivot(ws, g1, "low_speed_decel", "Giảm tốc dưới 6 m/s (m/s²) (G1)", top4)
    _widths(ws, 12, 12)

    ws = wb.create_sheet("Người đi bộ")
    _table(ws, [r for r in valid if r["kind"] == "walker"], WALKER_COLS)

    ws = wb.create_sheet("Xe + người")
    _table(ws, [r for r in valid if r["kind"] == "combined"], COMBINED_COLS, red_key="class_mismatch")

    ws = wb.create_sheet("Độ lặp lại")
    stats = metrics.repeat_stats(rows)
    _table(ws, stats, [("base", "Ca gốc"), ("metric", "Chỉ số"), ("n", "Số mẫu"), ("min", "Nhỏ nhất"), ("max", "Lớn nhất"),
                       ("range", "Dải"), ("values", "Các giá trị")])

    ws = wb.create_sheet("Khung hình")
    _header(ws, ["run_id"] + FRAME_COLS)
    for p in run_paths:
        _, frames = load_run(p)
        for f in frames:
            ws.append([p.name] + [f.get(k) for k in FRAME_COLS])
    _widths(ws, 11, 16)

    ws = wb.create_sheet("Bị loại")
    _table(ws, [r for r in rows if not r["valid"]], [("run_id", "Run"), ("group", "Nhóm"), ("reasons", "Lý do")])
    ws.column_dimensions["C"].width = 100

    out = run_dir / "ket-qua.xlsx"
    wb.save(out)
    return out
