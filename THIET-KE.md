# carla-ped-bench — đo độ lệch CARLA so với mô hình động học lý tưởng (ca người đi bộ)

**Trạng thái:** đã có code (repo phutro); thử trên CARLA 0.9.16 máy người làm ngày 14/11/2026 (13 run: G1 20–30 km/h, 1 ca mỗi nhóm G2–G4),
chờ chạy đủ 56 run trên máy chạy CARLA. **Ngày:** 14/11/2026.
**Nguồn ca:** [kế hoạch đo độ lệch người đi bộ](https://github.com/Menakanchi/SEP490-FA26-G15/blob/main/docs/exec-plans/active/2026-11-13-do-do-lech-carla-dong-hoc.md) (commit `a139b20`),
chuyển sang dạng **không có AEB (open-loop)**.

**Bố trí:** repo này ([phutro](https://github.com/Menakanchi/phutro)) giữ **code chạy**. Bản gốc của tài liệu này và **dữ liệu** thu về từ CARLA nằm trong repo VehicSim:
[docs/vehicsim/carla-ped-bench/](https://github.com/Menakanchi/SEP490-FA26-G15/tree/main/docs/vehicsim/carla-ped-bench) ([ket-qua/](https://github.com/Menakanchi/SEP490-FA26-G15/tree/main/docs/vehicsim/carla-ped-bench/ket-qua)) — sửa thiết kế thì sửa bản gốc rồi chép sang đây.

## 1. Mục tiêu và phạm vi

Đo riêng độ lệch của **bộ mô phỏng CARLA** — xe phanh ra sao, người đi bộ di chuyển ra sao — so với **mô hình động học lý tưởng** dùng cùng đầu
vào, rồi xuất một file Excel kết quả.

- **Không có AEB.** Thời điểm và profile phanh cố định trước cho mỗi ca, nên kết quả không lẫn quyết định của AEB.
- **Code độc lập hoàn toàn với VehicSim:** không gọi Java, không dùng ScenarioRunner, không đọc / ghi DB, không import gì từ repo này. Công
  cụ chỉ cần một server CARLA 0.9.16 đang chạy. Kết quả về repo VehicSim qua `pack` (máy chạy CARLA) → `import` (máy người nhận) (mục 9).
- **Ngoài phạm vi:** đánh giá AEB, so với code bộ động học của project, ca xe phía trước (CCR).

## 2. Mô hình tham chiếu (tính trong công cụ)

### Xe phanh

Đầu vào: tốc độ đầu $v_0$, thời điểm ra lệnh phanh $t_b$, trễ $t_d$ = 0,15 s, tốc độ tăng lực phanh $J$ = 20 m/s³, mức đích $a$, ma sát $\mu$.
Mức đích hiệu dụng $a_e = \min(a, \mu g)$.

| Pha | Thời gian | Chuyển động |
|---|---|---|
| Trễ | $t_d$ | Giữ $v_0$ |
| Tăng lực | $t_r = a_e / J$ | Giảm tốc tăng tuyến tính 0 → $a_e$ |
| Phanh đều | đến khi dừng | Giảm tốc $a_e$ |

Quãng dừng tính từ lúc ra lệnh:

$$d = v_0 t_d + v_0 t_r - \frac{J t_r^3}{6} + \frac{v_1^2}{2 a_e}, \qquad v_1 = v_0 - \frac{a_e^2}{2J}$$

(nếu $v_0 \le a_e^2 / 2J$ thì xe dừng ngay trong pha tăng lực — tính riêng). Công cụ cũng tính $v(t)$, $x(t)$ theo bước 0,01 s để so từng khung.

### Người đi bộ

Xuất phát trên vỉa hè ở $y_0$ = −3,6 m (cách mép làn ego 1,85 m), đi vuông góc với làn, **đạt ngay** tốc độ $v_p$ khi bắt đầu. Bắt đầu đi khi
mũi xe còn cách vạch băng qua `trigger_distance_m`. Vào đường đi khi mép người chạm hành lang của xe:

$$t_{vào} = \frac{|y_0| - w_h}{v_p}, \qquad w_h = \text{nửa bề ngang xe} + \text{lề} \;(\text{mặc định } 0{,}965 + 0{,}3 \text{ m, chỉnh được})$$

Ca dừng ở lề: người dừng đúng tại mép làn ($y$ = −1,75 m).

## 3. Cảnh CARLA

| Mục | Giá trị |
|---|---|
| Server | CARLA 0.9.16, `127.0.0.1:2000`, Town04 (tự nạp nếu đang ở map khác) |
| Bước | Đồng bộ, `fixed_delta_seconds` = 0,01; công cụ tự tick |
| Đoạn đường | Road 40 / lane −4 (đoạn thẳng repo dùng), vạch băng qua đặt ở giữa đoạn |
| Xe | `vehicle.audi.etron`, ép `mass` 2100 kg, `max_brake_torque` 1800 N·m mọi bánh; đọc lại physics sau khi ép |
| Người đi bộ | `walker.pedestrian.0001`, điều khiển bằng `WalkerControl` (hướng + tốc độ) mỗi tick |
| Chạy đều | `enable_constant_velocity` tới tốc độ đích, ổn định 1,5 s trước điểm phanh / điểm kích hoạt |
| Phanh | Tắt chạy đều, áp `VehicleControl(brake=p(t))` mỗi tick theo profile bên dưới |
| Cảm biến | Cảm biến va chạm trên xe; không camera (nhanh, nhẹ) |
| Thời tiết | Preset `ClearNoon`, `WetNoon` (RAIN), `HardRainNoon` (HEAVY_RAIN) |

**Profile bàn đạp (open-loop):** sau trễ $t_d$, bàn đạp tăng tuyến tính từ 0 tới $p_{đích} = a / a_{100\%}$ trong $a/J$ giây rồi giữ nguyên, với
$a_{100\%}$ = 9,13 m/s² (phanh 100% đã đo của e-tron 1800 N·m). Mức "100%" giữ bàn đạp 1,0. Không có phản hồi theo giảm tốc đo được — đúng
nghĩa open-loop.

## 4. Danh sách ca

Mặc định: người 1,5 m/s, kích hoạt 25 m, không dừng lề, CLEAR, $\mu$ = 1,0, seed không cần (CARLA đồng bộ không có ngẫu nhiên ở phép phanh).

### G1 — Phanh (gộp BR + V của kế hoạch repo), không người đi bộ

| ID | Ego (km/h) | Mức đích $a$ (m/s²) | Bàn đạp đích |
|---|---|---|---|
| G1-v-4.0 | 20, 30, 40, 50, 60, 70 | 4,0 | 0,44 |
| G1-v-5.6 | 20, 30, 40, 50, 60, 70 | 5,6 | 0,61 |
| G1-v-6.8 | 20, 30, 40, 50, 60, 70 | 6,8 | 0,74 |
| G1-v-8.0 | 20, 30, 40, 50, 60, 70 | 8,0 | 0,88 |
| G1-v-max | 20, 30, 40, 50, 60, 70 | 100% | 1,00 |

30 run. Phanh tại một vị trí cố định trên road 40 sau khi chạy đều.

### G2 — Người đi bộ (S), không xe

| ID | $v_p$ (m/s) | Ghi chú |
|---|---|---|
| G2-1.0 / 1.5 / 2.2 / 3.0 / 5.0 | 1,0; 1,5; 2,2; 3,0; 5,0 | Người đi qua hết làn; đo tăng tốc và thời điểm vào hành lang |

5 run. Bỏ xe vì chuyển động của người không phụ thuộc xe — tránh va chạm làm nhiễu số đo.

### G3 — Xe và người cùng lúc (T)

| ID | Kích hoạt (m) | Ghi chú |
|---|---|---|
| G3-15 / 20 / 25 / 30 / 40 / 60 | 15; 20; 25; 30; 40; 60 | Ego 40 km/h, người 1,5 m/s, phanh 8 m/s² |

6 run. **Điểm phanh cố định:** xe ra lệnh phanh khi mũi xe cách vạch băng qua $D_b = d_{tham\,chiếu} + 2$ m (tính trước từ mô hình, như nhau
cho cả hai bên — không đọc trạng thái người đi bộ). Đo khoảng cách nhỏ nhất xe – người, có va chạm hay không, so với mô hình.

### G4 — Dừng ở lề (C), không xe

| ID | $v_p$ (m/s) | Ghi chú |
|---|---|---|
| G4-1.0 / 1.5 / 2.2 / 3.0 | 1,0; 1,5; 2,2; 3,0 | Người ra lệnh dừng ở mép làn; đo vị trí dừng thật, độ nhô vào làn |

4 run. Khác kế hoạch repo (C theo tốc độ xe): độ nhô phụ thuộc tốc độ người, không phụ thuộc xe.

### G5 — Đường ướt (W)

| ID | Ego (km/h) | Thời tiết | Ghi chú |
|---|---|---|---|
| G5-40-RAIN / G5-60-RAIN | 40; 60 | RAIN ($\mu$ 0,65) | Phanh 8 m/s²; mô hình kẹp $a_e$ = 6,4 |
| G5-40-HEAVY | 40 | HEAVY_RAIN ($\mu$ 0,55) | Mô hình kẹp $a_e$ = 5,4 |
| G5-40-TF / G5-60-TF | 40; 60 | CLEAR + `tire_friction` × 0,65 | Kiểm ma sát lốp có làm CARLA phanh kém đi không |

5 run.

### G6 — Độ lặp lại

| ID | Ca lặp | Số lần thêm |
|---|---|---|
| G6-a | G1 ego 50, 8,0 m/s² | 2 |
| G6-b | G2 1,5 m/s | 2 |
| G6-c | G3 kích hoạt 25 m | 2 |

6 run. Bỏ nhóm ban đêm (N) của kế hoạch repo: không có perception nên ban đêm không đổi gì.

**Tổng:** 56 run, mỗi run 5–20 s → khoảng 15–20 phút.

## 5. Dữ liệu ghi mỗi tick (0,01 s)

`t`, `ego_s` (quãng dọc làn), `ego_lat`, `ego_v`, `ego_a` (vi phân vận tốc, lọc 0,1 s), `pedal_cmd` (lệnh công cụ gửi), `pedal_applied`
(`get_control().brake`), `walker_x`, `walker_y` (theo hệ làn: dọc / ngang), `walker_v`, `gap_m` (mũi xe – người, dọc làn), `collision`;
cùng số tham chiếu `ref_v`, `ref_s`, `ref_walker_y` ở cùng thời điểm.

Mỗi run ghi thêm: physics đọc lại (khối lượng, mô-men phanh từng bánh, ma sát lốp), thời tiết, `fixed_delta_seconds` thật, phiên bản server.

## 6. Chỉ số

| Chỉ số | Cách tính | Nhóm |
|---|---|---|
| $a_{dải}$ | Hồi quy $v(t)$ (đã làm mượt 0,1 s) trong pha phanh đều: sau $t_d + a_e/J$ kể từ lệnh, từ ≤ 0,95·$v_0$ xuống 6 m/s. Ở 20–30 km/h dải này quá ngắn nên không đo được — dùng Δ quãng dừng và giảm tốc vùng thấp | G1, G3, G5 |
| η | $a_{dải}$ / $a_e$ | G1, G5 |
| Trễ đạt lực | Thời điểm giảm tốc đạt 90 % $a_e$ (CARLA) − (mô hình) | G1 |
| Giảm tốc vùng thấp | Giảm tốc trung bình dưới 6 m/s (vùng "dừng tức thì") | G1 |
| Δ quãng dừng | Quãng dừng CARLA − mô hình | G1, G3, G5 |
| Trễ tăng tốc người | Thời điểm người đạt 90 % $v_p$ | G2 |
| Δ vào đường đi | $t_{vào}$ CARLA − mô hình | G2, G3 |
| Độ nhô vào làn | $y$ dừng thật − (−1,75 m) | G4 |
| Δ khoảng cách nhỏ nhất | `gap_min` CARLA − mô hình; khác loại (một bên va chạm) tô đỏ | G3 |
| ΔTTC cần bù | $\frac{v}{2}\left(\frac{1}{a_{dải}} - \frac{1}{a_e}\right)$ | G1 |

## 7. Quy tắc hợp lệ

Loại run (ghi lý do vào sheet Bị loại) khi: physics đọc lại sai (khối lượng lệch > 0,1 %, mô-men không phải 1800 ở mọi bánh); bước thật khác
0,01; tốc độ lúc phanh lệch đích quá 0,3 km/h; xe va chạm trong G1 / G5; người không spawn được; server mất kết nối giữa run.

## 8. File Excel `ket-qua.xlsx`

| Sheet | Nội dung |
|---|---|
| Tổng quan | Ngày giờ, phiên bản CARLA, xe và physics đã ép, $t_d$, $J$, $a_{100\%}$, hành lang; số run hợp lệ / bị loại |
| Danh sách ca | Tham số từng run |
| Phanh | G1 + G5: mỗi run một dòng — $a_{dải}$, η, trễ đạt lực, giảm tốc vùng thấp, quãng dừng CARLA / mô hình / Δ, ΔTTC |
| Theo tốc độ | Bảng η và Δ quãng dừng theo tốc độ × mức đích; biểu đồ đường η(v), Δd(v) |
| Người đi bộ | G2 + G4: trễ tăng tốc, Δ vào đường đi, độ nhô vào làn |
| Xe + người | G3: khoảng cách nhỏ nhất CARLA / mô hình / Δ, va chạm hai bên, cờ khác loại |
| Độ lặp lại | G6: min / max / dải từng chỉ số |
| Khung hình | Dữ liệu từng tick của mọi run (dạng dài, ~25.000 dòng) |
| Bị loại | Run và lý do |

Kèm mỗi run một thư mục `runs/<ngày-giờ>/<id>/` (`frames.csv`, `run.json`) để xuất lại Excel không cần chạy lại CARLA.

**Dữ liệu đưa về repo VehicSim:** máy chạy CARLA đóng gói bằng `bench.py pack` (zip cả thư mục run); người nhận chạy
`bench.py import <zip> --to <repo VehicSim>/docs/vehicsim/carla-ped-bench/ket-qua`, lệnh này chép `ket-qua.xlsx`, `meta.json`,
`run.json` và `frames.csv` của mỗi run vào
`docs/vehicsim/carla-ped-bench/ket-qua/<ngày-giờ>/` kèm `README.md` ghi phiên bản công cụ (commit repo code), máy, server CARLA. Ước lượng
vài MB một lần chạy; vượt 10 MB thì chỉ đưa Excel + `run.json`, `frames.csv` để ở repo code / ổ riêng và ghi đường dẫn. Đây là bộ dữ liệu
bằng chứng có chọn lọc, khác thư mục `data/` (artifact chạy web, không commit).

## 9. Cấu trúc code và cách dùng (repo phutro)

```
carla-ped-bench/
├─ README.md            cách cài / chạy
├─ THIET-KE.md          bản chép của tài liệu này
├─ bench.py             lệnh chính
├─ cases.yaml           danh sách ca (mục 4), sửa tay được
├─ config.yaml          host / port, đường dẫn CarlaUE4.exe, xe, t_d, J, a_100, hành lang
├─ config.local.yaml   (tùy chọn, không commit) bản riêng của máy — ưu tiên hơn config.yaml
├─ bench/
│  ├─ model.py          mô hình tham chiếu (mục 2)
│  ├─ scene.py          dựng cảnh, profile bàn đạp, điều khiển người, ghi tick
│  ├─ guard.py          kiểm server, tự bật lại CarlaUE4.exe, luôn trả server về async + dọn actor
│  ├─ metrics.py        chỉ số (mục 6), quy tắc hợp lệ (mục 7)
│  └─ excel.py          xuất Excel (mục 8)
├─ tests/               test model.py và metrics.py (không cần CARLA)
├─ requirements.txt     carla==0.9.16, pyyaml, openpyxl
└─ runs/
```

```powershell
py -3.12 -m venv .venv; .venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python bench.py check                          # kiểm máy + server trước khi chạy
.venv\Scripts\python bench.py dry-run                        # số tham chiếu, không cần CARLA
.venv\Scripts\python bench.py run                            # chạy mọi ca, xuất runs\<ngày-giờ>\ket-qua.xlsx
.venv\Scripts\python bench.py run --only G1,G3               # chỉ một số nhóm / ca
.venv\Scripts\python bench.py run --resume runs\<thư mục>    # chạy tiếp, bỏ run đã xong
.venv\Scripts\python bench.py excel runs\<thư mục>           # xuất lại Excel
.venv\Scripts\python bench.py pack runs\<thư mục>            # máy chạy CARLA: đóng gói zip để gửi
.venv\Scripts\python bench.py import <zip> --to <repo VehicSim>\docs\vehicsim\carla-ped-bench\ket-qua   # máy người nhận
```

## 10. An toàn khi chạy CARLA

- Không chạy cùng lúc với web VehicSim hay runner khác trên cùng server (một server, một client giữ tick).
- Mọi run kết thúc trong `finally`: hủy actor, trả server về chế độ không đồng bộ — không để server đứng ở synchronous mode.
- Server mất kết nối: bật lại `CarlaUE4.exe` (đường dẫn trong `config.yaml`), đợi cổng 2000 và map nạp xong, chạy lại run đó tối đa 2 lần.
- Không giết tiến trình giữa run để thử lại.

## 11. Giới hạn

1. **Open-loop:** controller trong project có khâu bù theo giảm tốc đo được, nên khi AEB chạy thật độ lệch sẽ nhỏ hơn số đo ở đây. Kết quả nói
   về bộ mô phỏng, không phải về AEB.
2. **Người đi bộ điều khiển trực tiếp** bằng `WalkerControl`, còn project đi qua ScenarioRunner (`PedestrianControl`): dáng tăng tốc và cách
   dừng có thể hơi khác. Giữ cùng map, blueprint, vị trí xuất phát cho gần nhất.
3. **Mô hình tham chiếu là mô hình lý tưởng** viết trong công cụ, không phải code bộ động học của project (có thêm lọc, chu kỳ perception…).
4. Bàn đạp đích tính bằng $a / 9{,}13$ giả định bàn đạp tuyến tính — chính G1 sẽ đo xem giả định này lệch bao nhiêu.

## 12. Các bước làm

| Bước | Việc | Kiểm chứng |
|---|---|---|
| 1 | `model.py` + `cases.yaml` + `--dry-run` | Test công thức (quãng dừng, $t_{vào}$) khớp tính tay |
| 2 | `scene.py` + `guard.py`: chạy 1 ca G1 và 1 ca G2 trên CARLA thật | Physics đọc lại đúng; frames.csv hợp lý |
| 3 | `metrics.py` + `excel.py` | Mở file Excel, kiểm từng sheet với 2 run ở bước 2 |
| 4 | Chạy cả 56 run | Số run hợp lệ, sheet Bị loại |
| 5 | Máy chạy CARLA `pack` gửi zip; người nhận `import` vào repo VehicSim, điền nhận xét trong `README.md` của lần chạy, commit | — |
