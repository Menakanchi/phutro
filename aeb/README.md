# Chạy lại mọi ca của 4 đợt bench, có AEB

Bench (đợt 1–4, 1.092 lượt) đo CARLA **open-loop**: lệnh phanh cố định, không AEB. Thư mục này dựng lại mọi ca thành ca xe + người
CP_CROSSING trong VehicSim, nơi AEB thật (lõi Java) quyết định phanh, rồi chạy trên cả CARLA `-xosc15` và bộ động học `kinematic-1.4`;
mỗi biến thể thêm một lượt AEB tắt làm mốc.

- `bien_the.json` (sinh bởi `sinh_bien_the.py`): 18 họ / 197 biến thể, phủ 907 lượt bench.
  - combined: giữ tốc độ xe, tốc độ người, khoảng kích hoạt.
  - brake (không người): thêm người theo tham số mặc định của ca (1,5 m/s, 25 m) để AEB phải phanh; các mức `a` cùng tốc độ gộp một biến thể.
  - walker (không xe): thêm xe 40 km/h; ca người dừng ở lề là ca an toàn — đo phanh oan.
  - Xe model3 / patrol / sprinter chưa hiệu chuẩn của bench gộp với bản `_hc` (VehicSim chỉ có bản đã hiệu chuẩn).
  - Bỏ 185 lượt: 124 ca đổi hệ số ma sát / mô-men / khối lượng, 59 ca xe hgv, 2 ca người 8 m/s (VehicSim tối đa 6 m/s).
- `trigger_m` → `trigger_distance_m` cùng nghĩa (đầu xe cách vạch băng ngang lúc người bắt đầu đi; `XoscExport.walkerTriggerDistance`).
  Bench có pha ổn định tốc độ trước; `.xosc` bắt đầu xe ở tốc độ đích. Mưa: bench μ 0,65, VehicSim 0,70 (mưa to cùng 0,55).
- Mỗi xe một project cá nhân (tài khoản EXPERIENCER) vì xe của project bị khóa khi đã có run.

## Thứ tự chạy (trên máy chủ)

```powershell
python aeb\chay_aeb.py tao --email <email>                    # 4 project, 18 họ
# backend ở chế độ CARLA
python aeb\chay_aeb.py chay --email <email> --sim carla        # 394 run (197 bật + 197 tắt)
python aeb\chay_aeb.py trangthai --email <email>               # lặp tới khi XONG
# đổi backend sang bộ động học (VEHICSIM_SIMULATOR=kinematic), khởi động lại
python aeb\chay_aeb.py chay --email <email> --sim kinematic    # 394 run, vài phút
python aeb\chay_aeb.py xuat --vehicsim <repo VehicSim>         # runs\aeb-v15-<ngày-giờ>\runs.csv
uns.csv
python aeb\so_sanh.py runs\aeb-v15-<ngày-giờ>                  # so_sanh.xlsx
```

`so_sanh.xlsx`: Tóm tắt (khớp va chạm / PASS-FAIL theo xe, lệch T_AEB, khoảng cách nhỏ nhất, quãng phanh, v va chạm, TTC;
va chạm khi AEB tắt → bật; phanh oan / bỏ lỡ), cặp CARLA–KIN từng biến thể (ô đỏ = lệch vượt ngưỡng), tác dụng AEB, run lỗi.
