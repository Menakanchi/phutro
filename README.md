# carla-ped-bench

Công cụ chạy ngoài, đo độ lệch của CARLA 0.9.16 (xe phanh, người đi bộ) so với mô hình động học lý tưởng cho ca người đi bộ băng ngang,
bằng lệnh phanh cố định (không AEB), rồi xuất file Excel kết quả.

**Thiết kế:** [THIET-KE.md](THIET-KE.md) — bản chép; bản gốc ở [VehicSim `docs/vehicsim/carla-ped-bench/`](https://github.com/Menakanchi/SEP490-FA26-G15/tree/main/docs/vehicsim/carla-ped-bench).
Dữ liệu chạy xong đưa về [`ket-qua/`](https://github.com/Menakanchi/SEP490-FA26-G15/tree/main/docs/vehicsim/carla-ped-bench/ket-qua) của repo đó bằng `--publish`.

**Trạng thái:** chưa có code — chờ duyệt thiết kế.

## Yêu cầu

- Server CARLA 0.9.16 đang chạy (`127.0.0.1:2000`).
- Python 3.12.

## Cài và chạy (sau khi có code)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python bench.py --dry-run
.venv\Scripts\python bench.py
```

Không chạy cùng lúc với web VehicSim hay runner khác trên cùng server CARLA.
