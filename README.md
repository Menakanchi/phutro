# carla-ped-bench

Công cụ chạy ngoài, đo độ lệch của CARLA 0.9.16 (xe phanh, người đi bộ) so với mô hình động học lý tưởng cho ca người đi bộ băng ngang,
bằng lệnh phanh cố định (không AEB), rồi xuất file Excel kết quả.

**Thiết kế:** [THIET-KE.md](THIET-KE.md) — bản chép; bản gốc ở [VehicSim `docs/vehicsim/carla-ped-bench/`](https://github.com/Menakanchi/SEP490-FA26-G15/tree/main/docs/vehicsim/carla-ped-bench).
Dữ liệu chạy xong đưa về [`ket-qua/`](https://github.com/Menakanchi/SEP490-FA26-G15/tree/main/docs/vehicsim/carla-ped-bench/ket-qua) của repo đó bằng `--publish`.

**Trạng thái:** chạy được; đã thử 13 run trên CARLA 0.9.16. Người chạy CARLA đọc [HUONG-DAN-CHAY.md](HUONG-DAN-CHAY.md).

## Yêu cầu

- Server CARLA 0.9.16 đang chạy (`127.0.0.1:2000`).
- Python 3.12.

## Cài và chạy

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1     # venv + thư viện + test
.venv\Scripts\python bench.py check                      # kiểm máy và server
.venv\Scripts\python bench.py run                        # 56 run → runs\<ngày-giờ>\ket-qua.xlsx
.venv\Scripts\python bench.py pack runs\<ngày-giờ>       # zip để gửi lại
```

Các lệnh khác (`dry-run`, `run --only/--resume`, `excel`, `import`): `python bench.py -h` và mục 9 của [THIET-KE.md](THIET-KE.md).
`config.local.yaml` (không commit, chép từ `config.yaml`) dùng cho thiết lập riêng của máy, ví dụ `carla_root`.

Không chạy cùng lúc với web VehicSim hay runner khác trên cùng server CARLA.
