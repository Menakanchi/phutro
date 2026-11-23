"""So sánh CARLA (-xosc15) với bộ động học (kinematic-1.4) cho các ca xe + người chạy lại có AEB.

Ghép theo biến thể (scenario_version_id) + chế độ AEB; cùng biến thể thì cùng seed (RunService.seedFor).
  python aeb\\so_sanh.py runs\\aeb-v15-<ngày-giờ>        → so_sanh.xlsx trong cùng thư mục
"""
from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

METRICS = [  # (cột CSV, tên hiển thị, ngưỡng lệch đáng chú ý)
    ("aeb_activation_time_s", "T_AEB (s)", 0.05),
    ("min_distance_m", "Khoảng cách nhỏ nhất (m)", 0.3),
    ("stopping_distance_m", "Quãng phanh (m)", 0.5),
    ("impact_speed_mps", "Vận tốc va chạm tương đối (m/s)", 0.5),
    ("rms_jerk_mps3", "RMS jerk (m/s³)", None),
    ("min_ttc_s", "TTC nhỏ nhất (s)", 0.1),
    ("max_deceleration_mps2", "Giảm tốc lớn nhất (m/s²)", None),
]
BAD = PatternFill("solid", fgColor="F8CBAD")
HEAD = Font(bold=True)


def num(x: str):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def flag(x: str):
    return {"1": True, "0": False}.get(str(x).strip())


def find(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = find(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find(v, key)
            if r is not None:
                return r
    return None


def bench_index(spec: dict) -> dict:
    out = {}
    for fam in spec["families"]:
        for v in fam["variants"]:
            kinds = sorted({c.rsplit("[", 1)[-1].rstrip("]") for c in v["bench_cases"] if "[" in c})
            out[(fam["name"], float(v["ego_speed_kmh"]), float(v["trigger_distance_m"]), float(v["pedestrian_speed_mps"]))] = {
                "cases": v["bench_cases"], "kinds": ", ".join(kinds),
                "weather": fam.get("weather", "CLEAR"), "stop": fam.get("stops_at_curb", False)}
    return out


def write_table(ws, header, rows, bad_cells=None):
    ws.append(header)
    for c in ws[1]:
        c.font = HEAD
    for i, r in enumerate(rows, 2):
        ws.append(r)
        for col in (bad_cells or {}).get(i - 2, []):
            ws.cell(row=i, column=col).fill = BAD
    for i, h in enumerate(header, 1):
        ws.column_dimensions[get_column_letter(i)].width = max(10, min(40, len(str(h)) + 2))
    ws.freeze_panes = "A2"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    folder = Path(sys.argv[1])
    spec = json.loads((folder / "bien_the.json").read_text(encoding="utf-8"))
    benches = bench_index(spec)
    with open(folder / "runs.csv", encoding="utf-8-sig") as f:
        runs = list(csv.DictReader(f))

    failed = [r for r in runs if r["status"] != "COMPLETED"]
    groups: dict[tuple, dict] = defaultdict(dict)
    meta: dict[str, dict] = {}
    for r in runs:
        if r["status"] != "COMPLETED":
            continue
        sim = "CARLA" if r["simulator_type"] == "CARLA" else "KIN"
        key = (r["scenario_version_id"], r["aeb_mode"])
        if sim in groups[key]:  # chạy lặp: giữ run mới nhất
            if int(r["run_id"]) < int(groups[key][sim]["run_id"]):
                continue
        groups[key][sim] = r
        if r["scenario_version_id"] not in meta:
            ir = json.loads(r["run_config_json"]) if r["run_config_json"] else {}
            meta[r["scenario_version_id"]] = {
                "family": r["family"], "vehicle": r["vehicle"],
                "ego": num(find(ir, "ego_speed_kmh")), "trig": num(find(ir, "trigger_distance_m")), "ped": num(find(ir, "pedestrian_speed_mps")),
            }

    versions = sorted(meta, key=lambda v: (meta[v]["family"], meta[v]["ego"] or 0, meta[v]["trig"] or 0, meta[v]["ped"] or 0))
    wb = Workbook()
    ws = wb.active
    ws.title = "AEB bật - cặp"
    header = ["Họ", "Xe", "Thời tiết", "Dừng lề", "ego km/h", "trigger m", "người m/s", "Loại ca bench", "Số lượt bench", "Ca bench",
              "Kết luận CARLA", "Kết luận KIN", "Va chạm CARLA", "Va chạm KIN", "Khớp va chạm"]
    for _, label, _ in METRICS:
        header += [f"{label} CARLA", f"{label} KIN", f"Δ {label}"]
    rows, bad = [], {}
    deltas: dict[str, list] = defaultdict(list)
    by_vehicle = defaultdict(lambda: {"n": 0, "coll_agree": 0, "verdict_agree": 0})
    for v in versions:
        pair = groups.get((v, "ON"), {})
        if "CARLA" not in pair or "KIN" not in pair:
            continue
        c, k, m = pair["CARLA"], pair["KIN"], meta[v]
        cc, kc = flag(c["collision_occurred"]), flag(k["collision_occurred"])
        b = benches.get((m["family"], m["ego"], m["trig"], m["ped"]), {"cases": [], "kinds": "", "weather": "", "stop": None})
        row = [m["family"], m["vehicle"], b["weather"], b["stop"], m["ego"], m["trig"], m["ped"], b["kinds"], len(b["cases"]),
               ", ".join(b["cases"][:12]) + (" …" if len(b["cases"]) > 12 else "") or "(không có)",
               c["verdict"], k["verdict"], cc, kc, cc == kc]
        marks = [] if cc == kc else [len(row)]
        for name, _, tol in METRICS:
            a, b = num(c[name]), num(k[name])
            d = None if a is None or b is None else round(a - b, 3)
            if d is not None:
                deltas[name].append(d)
                if tol is not None and abs(d) > tol:
                    marks.append(len(row) + 3)
            elif (a is None) != (b is None):
                marks.append(len(row) + 3)
            row += [a, b, d]
        bad[len(rows)] = marks
        rows.append(row)
        s = by_vehicle[m["vehicle"]]
        s["n"] += 1
        s["coll_agree"] += cc == kc
        s["verdict_agree"] += c["verdict"] == k["verdict"]
    write_table(ws, header, rows, bad)

    ws2 = wb.create_sheet("Tác dụng AEB")
    rows2 = []
    for v in versions:
        m = meta[v]
        line = [m["family"], m["vehicle"], m["ego"], m["trig"], m["ped"]]
        for sim in ("CARLA", "KIN"):
            off, on = groups.get((v, "OFF"), {}).get(sim), groups.get((v, "ON"), {}).get(sim)
            line += [flag(off["collision_occurred"]) if off else None, flag(on["collision_occurred"]) if on else None,
                     num(off["impact_speed_mps"]) if off else None, num(on["impact_speed_mps"]) if on else None]
        rows2.append(line)
    write_table(ws2, ["Họ", "Xe", "ego km/h", "trigger m", "người m/s",
                      "CARLA va chạm (tắt)", "CARLA va chạm (bật)", "CARLA v va chạm (tắt)", "CARLA v va chạm (bật)",
                      "KIN va chạm (tắt)", "KIN va chạm (bật)", "KIN v va chạm (tắt)", "KIN v va chạm (bật)"], rows2)

    ws3 = wb.create_sheet("Tóm tắt", 0)
    ws3.append(["Mục", "Giá trị"])
    for cell in ws3[1]:
        cell.font = HEAD
    ws3.append(["Run trong CSV", len(runs)])
    ws3.append(["Run không COMPLETED", len(failed)])
    ws3.append(["Cặp AEB bật đủ CARLA + KIN", len(rows)])
    for veh, s in sorted(by_vehicle.items()):
        ws3.append([f"{veh}: khớp va chạm", f"{s['coll_agree']}/{s['n']}"])
        ws3.append([f"{veh}: khớp kết luận PASS/FAIL", f"{s['verdict_agree']}/{s['n']}"])
    for name, label, _ in METRICS:
        d = deltas.get(name)
        if d:
            ad = sorted(abs(x) for x in d)
            p95 = ad[min(len(ad) - 1, int(0.95 * len(ad)))]
            ws3.append([f"Δ {label} (CARLA − KIN)", f"trung bình {statistics.mean(d):+.3f}, trung vị {statistics.median(d):+.3f}, "
                                                    f"|Δ| p95 {p95:.3f}, |Δ| max {ad[-1]:.3f} (n = {len(d)})"])
    for sim in ("CARLA", "KIN"):
        off = sum(1 for v in versions if flag(groups.get((v, "OFF"), {}).get(sim, {}).get("collision_occurred")))
        on = sum(1 for v in versions if flag(groups.get((v, "ON"), {}).get(sim, {}).get("collision_occurred")))
        ws3.append([f"{sim}: số biến thể va chạm, AEB tắt → bật", f"{off} → {on}"])
        fp = sum(1 for v in versions if flag(groups.get((v, "ON"), {}).get(sim, {}).get("is_false_positive")))
        fn = sum(1 for v in versions if flag(groups.get((v, "ON"), {}).get(sim, {}).get("is_false_negative")))
        ws3.append([f"{sim}: AEB bật — phanh oan / bỏ lỡ", f"{fp} / {fn}"])
    ws3.append(["Ô được tô đỏ ở sheet cặp", "lệch vượt ngưỡng: T_AEB 0,05 s; khoảng cách 0,3 m; quãng phanh 0,5 m; v va chạm 0,5 m/s; TTC 0,1 s; "
                                       "hoặc một bên có số, bên kia không"])
    ws3.column_dimensions["A"].width = 45
    ws3.column_dimensions["B"].width = 110
    if failed:
        ws4 = wb.create_sheet("Run lỗi")
        write_table(ws4, ["run_id", "family", "simulator_version", "aeb_mode", "status", "error_message"],
                    [[r["run_id"], r["family"], r["simulator_version"], r["aeb_mode"], r["status"], r["error_message"][:300]] for r in failed])
    out = folder / "so_sanh.xlsx"
    wb.save(out)
    print(f"{len(rows)} cặp AEB bật, {len(failed)} run lỗi → {out}")


if __name__ == "__main__":
    main()
