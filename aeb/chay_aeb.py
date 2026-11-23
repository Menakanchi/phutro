"""Chạy lại mọi ca của 4 đợt bench qua VehicSim (dựng thành ca xe + người), có AEB (và lượt AEB tắt làm mốc), trên CARLA và bộ động học.

Cần: VehicSim đang chạy (backend :8001, MySQL trong Docker), một tài khoản EXPERIENCER (tự đăng ký trên web là EXPERIENCER).
Mỗi xe một project cá nhân, vì xe của project bị khóa khi đã có run.

  python aeb\\chay_aeb.py tao      --email <email>             # tạo 4 project + 18 họ (không chạy)
  python aeb\\chay_aeb.py chay     --email <email> --sim carla  # xếp hàng run AEB bật + tắt; backend phải đang ở chế độ đó
  python aeb\\chay_aeb.py trangthai --email <email>             # số run còn chờ / đang chạy
  python aeb\\chay_aeb.py xuat     --vehicsim <thư mục repo VehicSim>   # CSV run → runs\\aeb-v15-<ngày-giờ>\\

Mật khẩu: biến môi trường AEB_PASSWORD hoặc nhập khi được hỏi. Trạng thái (id project/họ, đã chạy simulator nào) ở aeb\\state.json.
"""
from __future__ import annotations

import argparse
import csv
import getpass
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SPEC = HERE / "bien_the.json"
STATE = HERE / "state.json"
API = "/api/v1/vehicsim"


class Client:
    def __init__(self, base: str, email: str):
        self.base = base.rstrip("/")
        password = os.environ.get("AEB_PASSWORD") or getpass.getpass(f"Mật khẩu {email}: ")
        self.token = self.call("POST", "/api/v1/auth/login", {"email": email, "password": password}, auth=False)["access_token"]
        role = self.call("GET", "/api/v1/auth/me").get("role")
        if role != "EXPERIENCER":
            raise SystemExit(f"Tài khoản là {role}; cần EXPERIENCER (project cá nhân, chọn xe theo project). Đăng ký tài khoản mới trên web.")

    def call(self, method: str, path: str, body=None, project: int | None = None, auth: bool = True):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if auth:
            req.add_header("Authorization", f"Bearer {self.token}")
        if project is not None:
            req.add_header("X-VehicSim-Project", str(project))
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as e:
            raise SystemExit(f"{method} {path} → HTTP {e.code}: {e.read().decode(errors='replace')[:800]}") from None
        return json.loads(raw) if raw else None


def load_state() -> dict:
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"projects": {}, "families": {}}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_tao(c: Client, args) -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    state = load_state()
    options = c.call("GET", f"{API}/projects/vehicle-options")
    for fam in spec["families"]:
        bench_vehicle = fam["vehicle"]
        if bench_vehicle not in state["projects"]:
            match = [o for o in options if fam["vehicle_match"] in o["name"].lower()]
            if len(match) != 1:
                raise SystemExit(f"Không xác định được xe '{fam['vehicle_match']}' trong {[o['name'] for o in options]}")
            p = c.call("POST", f"{API}/projects", {"name": f"AEB đối chiếu bench · {match[0]['name']}",
                                                   "description": "Mọi ca của 4 đợt carla-ped-bench, chạy lại có AEB (phutro aeb/).",
                                                   "carla_vehicle_model_id": match[0]["id"]})
            state["projects"][bench_vehicle] = {"id": p["id"], "vehicle": match[0]["name"]}
            save_state(state)
            print(f"project {p['id']}: {match[0]['name']}")
        if fam["key"] in state["families"]:
            print(f"đã có họ {fam['key']} (id {state['families'][fam['key']]['scenario_id']})")
            continue
        pid = state["projects"][bench_vehicle]["id"]
        created = c.call("POST", f"{API}/families", {
            "name": fam["name"], "category": "CP_CROSSING",
            "description": "Ca của 4 đợt carla-ped-bench (phutro aeb/); AEB VehicSim thay lệnh phanh cố định.",
            "ego_speeds_kmh": fam["ego_speeds_kmh"], "trigger_distances_m": fam["trigger_distances_m"],
            "pedestrian_speeds_mps": fam["pedestrian_speeds_mps"], "stops_at_curb": [fam["stops_at_curb"]],
            "weathers": [fam["weather"]], "times_of_day": ["DAY"], "run_baseline": False}, project=pid)
        if created["variants"] != len(fam["variants"]):
            raise SystemExit(f"Họ {fam['key']}: VehicSim sinh {created['variants']} biến thể, bien_the.json có {len(fam['variants'])}")
        state["families"][fam["key"]] = {"scenario_id": created["scenario_id"], "project_id": pid, "ran": []}
        save_state(state)
        print(f"họ {fam['key']}: id {created['scenario_id']}, {created['variants']} biến thể")


def current_simulator(c: Client, pid: int) -> str:
    status = c.call("GET", f"{API}/carla/status", project=pid)
    sim = str(status.get("simulator") or "kinematic") if status.get("configured") else "kinematic"
    return "carla" if sim.startswith("carla") else "kinematic"


def cmd_chay(c: Client, args) -> None:
    state = load_state()
    if not state["families"]:
        raise SystemExit("Chưa có họ: chạy 'tao' trước")
    first = next(iter(state["families"].values()))["project_id"]
    sim = current_simulator(c, first)
    if sim != args.sim:
        raise SystemExit(f"Backend đang ở chế độ {sim}, không phải {args.sim}. Khởi động lại backend đúng chế độ rồi chạy lại.")
    total = 0
    for k, fam in state["families"].items():
        if args.sim in fam["ran"]:
            print(f"bỏ qua {k}: đã xếp hàng trên {args.sim}")
            continue
        r = c.call("POST", f"{API}/families/{fam['scenario_id']}/run", {"with_aeb_off": True}, project=fam["project_id"])
        fam["ran"].append(args.sim)
        save_state(state)
        total += r["queued_runs"]
        print(f"{k}: {r['queued_runs']} run")
    print(f"Đã xếp {total} run trên {args.sim}. Theo dõi: python aeb\\chay_aeb.py trangthai --email ...")


def cmd_trangthai(c: Client, args) -> None:
    state = load_state()
    left = 0
    for k, fam in state["families"].items():
        active = c.call("GET", f"{API}/families/{fam['scenario_id']}/runs/active", project=fam["project_id"])
        n = len(active.get("runs", active) if isinstance(active, dict) else active)
        left += n
        print(f"{k}: còn {n} run chờ / đang chạy (đã xếp: {', '.join(fam['ran']) or 'chưa'})")
    print("XONG" if left == 0 else f"Còn {left} run")


EXPORT_SQL = """
SELECT r.id AS run_id, r.project_id, r.scenario_id, s.name AS family, r.scenario_version_id, m.name AS vehicle,
       r.aeb_mode, r.simulator_type, r.simulator_version, r.purpose, r.status, r.random_seed,
       r.run_config_json, r.verdict, r.end_reason, r.simulated_duration_s, r.collision_occurred,
       r.first_detection_time_s, r.first_detection_distance_m, r.fcw_activated, r.fcw_time_s,
       r.aeb_activated, r.aeb_activation_time_s, r.is_false_positive, r.is_false_negative,
       r.rms_jerk_mps3, r.impact_speed_mps, r.stopping_distance_m, r.min_distance_m, r.min_ttc_s,
       r.braking_response_time_s, r.max_deceleration_mps2, r.mean_deceleration_mps2, r.max_jerk_mps3,
       r.error_message, r.started_at, r.ended_at
FROM simulation_runs r
JOIN scenarios s ON s.id = r.scenario_id
JOIN carla_vehicle_models m ON m.id = r.carla_vehicle_model_id
WHERE r.scenario_id IN ({ids})
ORDER BY r.scenario_id, r.scenario_version_id, r.simulator_type, r.aeb_mode, r.id
"""


def cmd_xuat(args) -> None:
    state = load_state()
    ids = ",".join(str(int(f["scenario_id"])) for f in state["families"].values())
    if not ids:
        raise SystemExit("state.json chưa có họ nào")
    sql = EXPORT_SQL.format(ids=ids).replace("\n", " ")
    cmd = ["docker", "compose", "exec", "-T", "mysql", "sh", "-c",
           'mysql --default-character-set=utf8mb4 -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" --batch -e "$0"', sql]
    res = subprocess.run(cmd, cwd=args.vehicsim, capture_output=True)
    if res.returncode != 0:
        raise SystemExit(f"Truy vấn MySQL lỗi:\n{res.stderr.decode(errors='replace')}")
    rows = list(csv.reader(io.StringIO(res.stdout.decode("utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE))
    out = ROOT / "runs" / f"aeb-v15-{datetime.now():%Y-%m-%d_%H%M}"
    out.mkdir(parents=True)
    with open(out / "runs.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow(["" if x == "NULL" else x.replace("\\n", "\n").replace("\\t", "\t") for x in r])
    shutil.copy(SPEC, out / "bien_the.json")
    shutil.copy(STATE, out / "state.json")
    n = len(rows) - 1
    print(f"{n} run → {out}")
    print("Đẩy lên: git add -f " + str(out.relative_to(ROOT)) + " && git commit -m \"data: AEB đối chiếu bench (-xosc15 / kinematic-1.4)\" && git push")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("lenh", choices=["tao", "chay", "trangthai", "xuat"])
    p.add_argument("--api", default="http://localhost:8001")
    p.add_argument("--email")
    p.add_argument("--sim", choices=["carla", "kinematic"])
    p.add_argument("--vehicsim", help="thư mục repo VehicSim (chứa docker-compose.yml) — cho lệnh xuat")
    args = p.parse_args()
    if args.lenh == "xuat":
        if not args.vehicsim:
            p.error("xuat cần --vehicsim")
        cmd_xuat(args)
        return
    if not args.email:
        p.error(f"{args.lenh} cần --email")
    if args.lenh == "chay" and not args.sim:
        p.error("chay cần --sim carla|kinematic")
    c = Client(args.api, args.email)
    {"tao": cmd_tao, "chay": cmd_chay, "trangthai": cmd_trangthai}[args.lenh](c, args)


if __name__ == "__main__":
    main()
