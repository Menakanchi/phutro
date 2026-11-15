"""Đọc config.yaml và cases.yaml; bung lưới ca thành danh sách run."""

from __future__ import annotations

import itertools
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

KINDS = ("brake", "walker", "combined")
CASE_FIELDS = ("ego_kmh", "a", "ped_mps", "trigger_m", "stop_at_curb", "weather", "tire_friction_scale", "vehicle", "torque_scale",
               "mass_scale")


@dataclass(frozen=True)
class Case:
    """Một run. ``case_id`` là tên ca; ``run_id`` thêm hậu tố ``-r<n>`` khi ca chạy lặp."""

    run_id: str
    case_id: str
    group: str
    kind: str
    ego_kmh: float
    a: float | str          # m/s² hoặc "max" (bàn đạp 1,0)
    ped_mps: float
    trigger_m: float
    stop_at_curb: bool
    weather: str
    tire_friction_scale: float
    same_as: str | None = None
    repeat_index: int = 1
    vehicle: str = "etron"
    torque_scale: float = 1.0
    mass_scale: float = 1.0

    def as_dict(self) -> dict:
        return asdict(self)


class ConfigError(ValueError):
    pass


def load_yaml(path: str | Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        where = f" dòng {mark.line + 1}, cột {mark.column + 1}" if mark else ""
        raise ConfigError(f"{path}{where}: sai cú pháp YAML ({getattr(e, 'problem', e)}). "
                          "Thường do thụt lề: dòng con phải bắt đầu bằng đúng 2 dấu cách như các dòng cùng nhóm, không dùng Tab.") from None
    except OSError as e:
        raise ConfigError(f"không đọc được {path}: {e}") from None
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: không phải một bảng YAML")
    return data


def load_config(path: str | Path) -> dict:
    """Đọc config. ``config.local.yaml`` chỉ được dùng cho mục ``may`` (host, cổng, carla_root...) của máy; các mục khác luôn lấy từ
    ``config.yaml`` cùng thư mục, để bản local chép từ phiên bản cũ không làm lệch cấu hình khi ``config.yaml`` được cập nhật."""
    path = Path(path)
    cfg = load_yaml(path)
    if path.name == "config.local.yaml" and (path.parent / "config.yaml").exists():
        base = load_yaml(path.parent / "config.yaml")
        base["may"] = {**base.get("may", {}), **cfg.get("may", {})}
        cfg = base
    for section in ("may", "canh", "xe", "phanh", "nguoi_di_bo", "thoi_tiet", "gioi_han"):
        if section not in cfg:
            raise ConfigError(f"{path}: thiếu mục '{section}'")
    return cfg


def _label(value) -> str:
    """Giá trị trong id: 50 → '50', 8.0 → '8.0', 'max' → 'max'."""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float) and value.is_integer() and value >= 10:
        return str(int(value))
    return str(value)


def _validate(entry: dict, cfg: dict) -> None:
    if entry["kind"] not in KINDS:
        raise ConfigError(f"{entry['id']}: kind phải thuộc {KINDS}")
    if entry["weather"] not in cfg["thoi_tiet"]:
        raise ConfigError(f"{entry['id']}: thời tiết {entry['weather']} không có trong config.yaml")
    a = entry["a"]
    if a != "max" and not (isinstance(a, (int, float)) and 0 < a <= 12):
        raise ConfigError(f"{entry['id']}: a phải trong (0, 12] m/s² hoặc 'max'")
    if not 10 <= float(entry["ego_kmh"]) <= 130:
        raise ConfigError(f"{entry['id']}: ego_kmh phải trong [10, 130]")
    if not 0.5 <= float(entry["ped_mps"]) <= 8:
        raise ConfigError(f"{entry['id']}: ped_mps phải trong [0.5, 8]")
    if not 5 <= float(entry["trigger_m"]) <= 80:
        raise ConfigError(f"{entry['id']}: trigger_m phải trong [5, 80]")
    if not 0.1 <= float(entry["tire_friction_scale"]) <= 3:
        raise ConfigError(f"{entry['id']}: tire_friction_scale phải trong [0.1, 3]")
    if entry["vehicle"] not in vehicles(cfg):
        raise ConfigError(f"{entry['id']}: xe {entry['vehicle']} không có trong cac_xe của config.yaml")
    if not 0.2 <= float(entry["torque_scale"]) <= 5:
        raise ConfigError(f"{entry['id']}: torque_scale phải trong [0.2, 5]")
    if not 0.5 <= float(entry["mass_scale"]) <= 2:
        raise ConfigError(f"{entry['id']}: mass_scale phải trong [0.5, 2]")


def vehicles(cfg: dict) -> dict:
    """Danh mục xe; config cũ chỉ có mục "xe" thì coi đó là etron."""
    return cfg.get("cac_xe") or {"etron": cfg["xe"]}


def vehicle_of(cfg: dict, case) -> dict:
    """Thông số xe thực dùng cho một ca: mô-men phanh × torque_scale, khối lượng × mass_scale."""
    v = dict(vehicles(cfg)[case.vehicle])
    v["max_brake_torque_nm"] = float(v["max_brake_torque_nm"]) * case.torque_scale
    v["mass_kg"] = float(v["mass_kg"]) * case.mass_scale
    return v


def expand_cases(cases_doc: dict, cfg: dict) -> list[Case]:
    """Bung mọi mục (kể cả lưới) thành danh sách run theo thứ tự trong file. Id trùng là lỗi."""
    defaults = cases_doc.get("defaults", {})
    runs: list[Case] = []
    seen: set[str] = set()
    for item in cases_doc.get("cases", []):
        grid = item.get("grid") or {}
        keys = list(grid)
        for combo in itertools.product(*(grid[k] for k in keys)) if keys else [()]:
            entry = {k: defaults.get(k) for k in CASE_FIELDS}
            entry.setdefault("vehicle", None)
            entry["vehicle"] = entry["vehicle"] or "etron"
            entry["torque_scale"] = entry["torque_scale"] if entry["torque_scale"] is not None else 1.0
            entry["mass_scale"] = entry["mass_scale"] if entry["mass_scale"] is not None else 1.0
            entry.update({k: v for k, v in item.items() if k in CASE_FIELDS})
            entry.update(dict(zip(keys, combo)))
            for k, d in (("vehicle", "etron"), ("torque_scale", 1.0), ("mass_scale", 1.0)):
                if entry.get(k) is None:
                    entry[k] = d
            case_id = item["id"].format(**{k: _label(v) for k, v in entry.items()})
            entry.update(id=case_id, kind=item.get("kind"))
            _validate(entry, cfg)
            repeat = int(item.get("repeat", 1))
            for n in range(1, repeat + 1):
                run_id = case_id if repeat == 1 else f"{case_id}-r{n}"
                if run_id in seen:
                    raise ConfigError(f"id trùng: {run_id}")
                seen.add(run_id)
                runs.append(Case(
                    run_id=run_id, case_id=case_id, group=item.get("group", case_id.split("-")[0]), kind=entry["kind"],
                    ego_kmh=float(entry["ego_kmh"]), a=entry["a"] if entry["a"] == "max" else float(entry["a"]),
                    ped_mps=float(entry["ped_mps"]), trigger_m=float(entry["trigger_m"]),
                    stop_at_curb=bool(entry["stop_at_curb"]), weather=str(entry["weather"]),
                    tire_friction_scale=float(entry["tire_friction_scale"]), same_as=item.get("same_as"), repeat_index=n,
                    vehicle=str(entry["vehicle"]), torque_scale=float(entry["torque_scale"]), mass_scale=float(entry["mass_scale"])))
    missing = {c.same_as for c in runs if c.same_as} - {c.case_id for c in runs}
    if missing:
        raise ConfigError(f"same_as trỏ tới ca không có: {sorted(missing)}")
    return runs


def select(runs: list[Case], only: str | None) -> list[Case]:
    """``--only G1,G3`` lọc theo nhóm hoặc theo id ca."""
    if not only:
        return runs
    wanted = {x.strip() for x in only.split(",") if x.strip()}
    return [c for c in runs if c.group in wanted or c.case_id in wanted or c.run_id in wanted]
