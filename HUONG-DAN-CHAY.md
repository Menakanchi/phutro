# Hướng dẫn chạy (cho người chạy CARLA)

Công cụ chạy 56 ca mô phỏng ngắn trên CARLA (xe phanh, người đi bộ băng ngang), rồi xuất một file Excel. Mất khoảng **20–30 phút**,
không cần biết gì về dự án. Cuối cùng bạn gửi lại **một file zip**.

## Cần có

- Windows, **CARLA 0.9.16** đã giải nén (có `CarlaUE4.exe`), card đồ họa chạy được CARLA.
- **Python 3.12** (có `py` launcher). Chưa có: tải ở https://www.python.org/downloads/release/python-31210/ , khi cài tick
  "Add python.exe to PATH".
- Khoảng 200 MB ổ trống.

## Các bước

**1. Lấy công cụ** — một trong hai cách:

```powershell
git clone https://github.com/Menakanchi/phutro.git
cd phutro
```

hoặc giải nén file zip được gửi, mở PowerShell trong thư mục đó.

**2. Cài (một lần):**

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

Thấy dòng xanh "Cài xong" là được.

**3. (Nên làm) Cho công cụ tự bật lại CARLA nếu CARLA bị tắt giữa chừng:** mở `config.yaml`, sửa dòng `carla_root` thành thư mục chứa
`CarlaUE4.exe`, ví dụ:

```yaml
  carla_root: "D:/CARLA_0.9.16"
```

**4. Bật CARLA:** chạy `CarlaUE4.exe`, đợi cửa sổ CARLA hiện bản đồ (khoảng 30 giây – 1 phút). Tắt mọi chương trình khác đang dùng
CARLA (web VehicSim, ScenarioRunner…).

**5. Kiểm tra:**

```powershell
.venv\Scripts\python bench.py check
```

Phải thấy `Kết quả: SẴN SÀNG`. Có dòng `[LỖI]` thì làm theo gợi ý ngay dưới dòng đó rồi chạy lại.

**6. Chạy:**

```powershell
.venv\Scripts\python bench.py run
```

Màn hình in từng ca `[i/56] ...`. Không đóng cửa sổ CARLA, không thao tác trong cửa sổ CARLA khi đang chạy. Dòng cuối in đường dẫn file
Excel, dạng `runs\2026-11-15_1430\ket-qua.xlsx`.

Nếu bị dừng giữa chừng (CARLA tắt, mất điện…): bật lại CARLA rồi chạy tiếp, các ca đã xong không chạy lại:

```powershell
.venv\Scripts\python bench.py run --resume runs\2026-11-15_1430
```

**7. Đóng gói và gửi lại:**

```powershell
.venv\Scripts\python bench.py pack runs\2026-11-15_1430
```

Gửi file `runs\ket-qua_<tên máy>_2026-11-15_1430.zip` qua Drive / Zalo.

**Đừng `git add` / `git push`** thư mục công cụ: lệnh đó sẽ đẩy cả `.venv` (hàng nghìn file) và cấu hình riêng của máy lên repo. Chỉ gửi file zip.

## Lỗi hay gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `không có server CARLA ở 127.0.0.1:2000` | CARLA chưa bật hoặc chưa nạp xong — đợi thêm rồi chạy lại |
| `time-out ... while waiting for the simulator` | CARLA đang nạp map (lần đầu có thể 1–2 phút) — chạy lại |
| `server 0.9.x, client 0.9.16` | Bản CARLA khác 0.9.16 — cần đúng bản 0.9.16 |
| `bước đo được ...` khác 0,010 | Có chương trình khác đang điều khiển CARLA — tắt nó |
| Cài `carla` lỗi | `.venv\Scripts\pip install <thư mục CARLA>\PythonAPI\carla\dist\carla-0.9.16-cp312-cp312-win_amd64.whl` |
| CARLA tự tắt giữa chừng | Điền `carla_root` (bước 3) rồi `run --resume ...` |

Gặp lỗi khác: gửi lại ảnh màn hình PowerShell và file `runs\<thư mục>\state.json`.
