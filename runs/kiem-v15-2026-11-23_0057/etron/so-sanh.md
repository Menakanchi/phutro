# So sánh CARLA (profile hiện hành) với bộ động học — ca người đi bộ

Mỗi ca CARLA chạy 3 lần (trung bình ± độ lệch chuẩn).
Định dạng .xosc: c1 vehicsim.xosc/v15, c3 vehicsim.xosc/v15, c7 vehicsim.xosc/v15

| Ca | Chỉ số | CARLA | Bộ động học | CARLA 13/11 (radar, trước v7/v8) |
|---|---|---|---|---|
| c1 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED | EGO_STOPPED |
| c1 | aeb_decision_t | 2.250 ± 0.000 | 2.250 | 2.250 |
| c1 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| c1 | min_distance_m | 4.222 ± 0.050 | 4.257 | 2.609 |
| c1 | stopping_distance_m | 9.376 ± 0.050 | 9.332 | 11.413 |
| c1 | impact_speed_mps | — | — |  |
| c1 | ego_impact_speed_mps | — | — |  |
| c1 | radar_first_detection_t | 2.200 ± 0.000 | — |  |
| c1 | ground_truth_aeb_decision_t | 2.250 ± 0.000 | — |  |
| c3 | end_reason | EGO_STOPPED ×3 | TARGET_CLEARED |  |
| c3 | aeb_decision_t | 2.300 ± 0.000 | — | 2.100 |
| c3 | brake_onset_t | 2.550 ± 0.000 | — |  |
| c3 | min_distance_m | 0.976 ± 0.000 | 1.008 | 0.990 |
| c3 | stopping_distance_m | 14.577 ± 0.016 | — |  |
| c3 | impact_speed_mps | — | — |  |
| c3 | ego_impact_speed_mps | — | — |  |
| c3 | radar_first_detection_t | 2.200 ± 0.000 | — |  |
| c3 | ground_truth_aeb_decision_t | 2.750 ± 0.000 | — |  |
| c7 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| c7 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| c7 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| c7 | min_distance_m | 3.273 ± 0.027 | 3.275 |  |
| c7 | stopping_distance_m | 10.325 ± 0.027 | 10.314 |  |
| c7 | impact_speed_mps | — | — |  |
| c7 | ego_impact_speed_mps | — | — |  |
| c7 | radar_first_detection_t | 2.200 ± 0.000 | — |  |
| c7 | ground_truth_aeb_decision_t | 2.250 ± 0.000 | — |  |
