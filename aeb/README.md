# Chạy lại ca xe + người của 4 đợt bench, có AEB

Bench (đợt 1–4) đo CARLA **open-loop**: lệnh phanh cố định, không AEB. Thư mục này chạy lại các ca **combined** (xe + người)
qua VehicSim, nơi AEB thật (lõi Java) quyết định phanh, trên cả CARLA `-xosc15` và bộ động học `kinematic-1.4`, mỗi biến thể
thêm một lượt AEB tắt làm mốc. Ca brake (không người) và walker (không xe) không có nghĩa khi bật AEB nên không chạy lại.

- `bien_the.json`: 6 họ CP_CROSSING / 111 biến thể (109 khớp ca bench, 2 thừa do lưới), sinh bởi `sinh_bien_the.py`.
  Bỏ 5 lượt bench không biểu diễn được trong VehicSim: xe `hgv`, `tire_friction_scale = 0.3`.
- Ánh xạ: `ego_kmh` → `ego_speed_kmh`, `ped_mps` → `pedestrian_speed_mps`, `trigger_m` → `trigger_distance_m` (cùng nghĩa: đầu xe
  cách vạch băng ngang lúc người bắt đầu đi — `XoscExport.walkerTriggerDistance` = trigger + nửa xe tính từ tâm xe), CLEAR, DAY,
  không dừng ở lề. Cột `a` bỏ vì AEB tự quyết định mức phanh. Bench có pha ổn định tốc độ trước; `.xosc` bắt đầu xe ở tốc độ đích.
- Mỗi xe một project cá nhân (tài khoản EXPERIENCER) vì xe của project bị khóa khi đã có run.

## Thứ tự chạy (trên máy chủ)

```powershell
python aeb\chay_aeb.py tao --email <email>                    # 4 project, 6 họ
# backend ở chế độ CARLA (scripts\dev-carla.ps1 -RestartBackend)
python aeb\chay_aeb.py chay --email <email> --sim carla        # 222 run (111 bật + 111 tắt)
python aeb\chay_aeb.py trangthai --email <email>               # lặp tới khi XONG
# đổi backend sang bộ động học (VEHICSIM_SIMULATOR=kinematic), khởi động lại
python aeb\chay_aeb.py chay --email <email> --sim kinematic    # 222 run, vài phút
python aeb\chay_aeb.py xuat --vehicsim <repo VehicSim>         # runs\aeb-v15-<ngày-giờ>\runs.csv
python aeb\so_sanh.py runs\aeb-v15-<ngày-giờ>                  # so_sanh.xlsx
```

`so_sanh.xlsx`: Tóm tắt (khớp va chạm / PASS-FAIL theo xe, lệch T_AEB, khoảng cách nhỏ nhất, quãng phanh, v va chạm, TTC;
số biến thể va chạm khi AEB tắt → bật), cặp CARLA–KIN từng biến thể (ô đỏ = lệch vượt ngưỡng), tác dụng AEB, run lỗi.
