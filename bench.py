"""carla-ped-bench — lệnh chính.

    python bench.py check                       kiểm máy và server CARLA trước khi chạy
    python bench.py dry-run                     in số tham chiếu của mọi ca (không cần CARLA)
    python bench.py run [--only G1,G3]          chạy và xuất Excel vào runs/<ngày-giờ>/
    python bench.py run --resume runs/<thư mục> chạy tiếp, bỏ qua run đã xong
    python bench.py excel runs/<thư mục>        xuất lại Excel từ dữ liệu đã có
    python bench.py pack runs/<thư mục>         đóng gói zip để gửi đi
    python bench.py import <file.zip> --to <thư mục ket-qua của repo VehicSim>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from bench import config  # noqa: E402


def _console_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def load(args):
    cfg = config.load_config(args.config)
    runs = config.select(config.expand_cases(config.load_yaml(args.cases), cfg), getattr(args, "only", None))
    return cfg, runs


def cmd_dry_run(args) -> int:
    from bench.runner import reference_summary
    cfg, runs = load(args)
    for c in runs:
        print(f"{c.run_id:<16} {c.kind:<9} {reference_summary(c, cfg)}")
    print(f"{len(runs)} run")
    return 0


def cmd_check(args) -> int:
    from bench.check import run_checks
    cfg, _ = load(args)
    return run_checks(cfg)


def cmd_run(args) -> int:
    import carla

    from bench import runner
    cfg, runs = load(args)
    run_dir = Path(args.resume) if args.resume else runner.new_run_dir(ROOT / "runs")
    print(f"Thư mục kết quả: {run_dir}")
    state = runner.run_all(carla, cfg, runs, run_dir, ROOT)
    print(f"Xong {len(state['done'])} run, lỗi kết nối {len(state['failed'])}.")
    if not args.no_excel:
        from bench.excel import export
        print(f"Excel: {export(run_dir)}")
    return 0 if not state["failed"] else 3


def cmd_excel(args) -> int:
    from bench.excel import export
    print(f"Excel: {export(Path(args.run_dir))}")
    return 0


def cmd_pack(args) -> int:
    from bench.pack import pack
    print(f"Gói: {pack(Path(args.run_dir))}")
    return 0


def cmd_import(args) -> int:
    from bench.pack import import_zip
    print(f"Đã nhập vào: {import_zip(Path(args.zip), Path(args.to))}")
    return 0


def main(argv=None) -> int:
    _console_utf8()
    p = argparse.ArgumentParser(description="Đo độ lệch CARLA so với mô hình động học lý tưởng (ca người đi bộ, không AEB)")
    local = ROOT / "config.local.yaml"  # bản riêng của máy (không commit), ưu tiên nếu có
    p.add_argument("--config", default=str(local if local.exists() else ROOT / "config.yaml"))
    p.add_argument("--cases", default=str(ROOT / "cases.yaml"))
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    d = sub.add_parser("dry-run")
    d.add_argument("--only")
    d.set_defaults(fn=cmd_dry_run)
    r = sub.add_parser("run")
    r.add_argument("--only")
    r.add_argument("--resume")
    r.add_argument("--no-excel", action="store_true")
    r.set_defaults(fn=cmd_run)
    e = sub.add_parser("excel")
    e.add_argument("run_dir")
    e.set_defaults(fn=cmd_excel)
    k = sub.add_parser("pack")
    k.add_argument("run_dir")
    k.set_defaults(fn=cmd_pack)
    m = sub.add_parser("import")
    m.add_argument("zip")
    m.add_argument("--to", required=True)
    m.set_defaults(fn=cmd_import)
    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except config.ConfigError as e:
        print(f"Lỗi cấu hình: {e}")
        return 2
    except Exception as e:  # noqa: BLE001
        if type(e).__name__ == "ServerDown":
            print(f"\n[DỪNG] {e}")
            return 4
        raise


if __name__ == "__main__":
    sys.exit(main())
