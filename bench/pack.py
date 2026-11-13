"""Đóng gói kết quả để gửi đi (máy chạy CARLA) và nhập vào repo VehicSim (máy người nhận)."""

from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from bench import metrics

MAX_PUBLISH_BYTES = 10 * 1024 * 1024  # thiết kế: quá 10 MB thì bỏ frames.csv


def pack(run_dir: Path) -> Path:
    """Zip cả thư mục run (Excel, meta, run.json, frames.csv). Thiếu Excel thì xuất trước."""
    run_dir = Path(run_dir)
    if not (run_dir / "ket-qua.xlsx").exists():
        from bench.excel import export
        export(run_dir)
    meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
    machine = (meta.get("machine", {}).get("machine") or "may").replace(" ", "-")
    out = run_dir.parent / f"ket-qua_{machine}_{run_dir.name}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(run_dir.rglob("*")):
            if p.is_file():
                z.write(p, Path(run_dir.name) / p.relative_to(run_dir))
    return out


def _summary_readme(run_dir: Path, rows: list[dict], frames_kept: bool) -> str:
    meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
    m = meta.get("machine", {})
    valid = sum(1 for r in rows if r["valid"])
    lines = [f"# Lần chạy {run_dir.name}", "",
             "| Mục | Giá trị |", "|---|---|",
             f"| Bắt đầu | {meta.get('started')} |",
             f"| Commit công cụ (phutro) | `{meta.get('tool_commit')}` |",
             f"| Máy | {m.get('machine')} — {m.get('os')} |",
             f"| GPU | {m.get('gpu')} |",
             f"| CARLA server / gói | {m.get('carla_server')} / {m.get('carla_client')} |",
             f"| Run hợp lệ / tổng | {valid} / {len(rows)} |",
             f"| frames.csv | {'có' if frames_kept else 'bỏ (vượt 10 MB) — xem gói zip gốc'} |", "",
             "## Nhận xét", "", "_(điền sau khi đọc ket-qua.xlsx)_", ""]
    bad = [r for r in rows if not r["valid"]]
    if bad:
        lines += ["## Run bị loại", ""] + [f"- `{r['run_id']}`: {r['reasons']}" for r in bad] + [""]
    return "\n".join(lines)


def import_zip(zip_path: Path, target: Path) -> Path:
    """Giải nén gói, chép Excel + meta + run.json (+ frames.csv nếu tổng ≤ 10 MB) vào target/<tên lần chạy>/ kèm README."""
    target = Path(target)
    if not target.exists():
        raise FileNotFoundError(f"không có thư mục {target} (cần trỏ tới docs/vehicsim/carla-ped-bench/ket-qua của repo VehicSim)")
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_path) as z:
            for name in z.namelist():  # chặn đường dẫn thoát khỏi thư mục tạm
                if name.startswith("/") or ".." in Path(name).parts:
                    raise ValueError(f"đường dẫn lạ trong zip: {name}")
            z.extractall(tmp)
        dirs = [p for p in Path(tmp).iterdir() if p.is_dir()]
        if len(dirs) != 1 or not (dirs[0] / "meta.json").exists():
            raise ValueError("zip không phải gói của bench.py pack")
        src = dirs[0]
        dst = target / src.name
        if dst.exists():
            raise FileExistsError(f"{dst} đã có — xoá hoặc đổi tên trước khi nhập lại")
        frames_size = sum(p.stat().st_size for p in src.rglob("frames.csv"))
        keep_frames = frames_size + (src / "ket-qua.xlsx").stat().st_size <= MAX_PUBLISH_BYTES
        dst.mkdir(parents=True)
        for name in ("ket-qua.xlsx", "meta.json"):
            shutil.copy2(src / name, dst / name)
        for run in sorted(p for p in src.iterdir() if (p / "run.json").exists()):
            (dst / run.name).mkdir()
            shutil.copy2(run / "run.json", dst / run.name / "run.json")
            if keep_frames and (run / "frames.csv").exists():
                shutil.copy2(run / "frames.csv", dst / run.name / "frames.csv")
        meta = json.loads((src / "meta.json").read_text(encoding="utf-8"))
        rows = [metrics.analyse_run(p, meta["config"]) for p in sorted(src.iterdir()) if (p / "run.json").exists()]
        (dst / "README.md").write_text(_summary_readme(src, rows, keep_frames), encoding="utf-8")
    return dst
