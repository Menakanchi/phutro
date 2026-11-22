# So sánh CARLA (profile hiện hành) với bộ động học — ca người đi bộ

Mỗi ca CARLA chạy 3 lần (trung bình ± độ lệch chuẩn).
Định dạng .xosc: c1 vehicsim.xosc/v13, c2 vehicsim.xosc/v13, c3 vehicsim.xosc/v13, c4 vehicsim.xosc/v13, c5 vehicsim.xosc/v13, c6 vehicsim.xosc/v13, c7 vehicsim.xosc/v13

| Ca | Chỉ số | CARLA | Bộ động học | CARLA 13/11 (radar, trước v7/v8) |
|---|---|---|---|---|
| c1 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED | EGO_STOPPED |
| c1 | aeb_decision_t | 2.250 ± 0.000 | 2.250 | 2.250 |
| c1 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| c1 | min_distance_m | 4.237 ± 0.012 | 4.257 | 2.609 |
| c1 | stopping_distance_m | 9.361 ± 0.012 | 9.332 | 11.413 |
| c1 | impact_speed_mps | — | — |  |
| c1 | ego_impact_speed_mps | — | — |  |
| c1 | radar_first_detection_t | 1.900 ± 0.000 | — |  |
| c1 | ground_truth_aeb_decision_t | 2.250 ± 0.000 | — |  |
| c2 | end_reason | TARGET_CLEARED ×3 | TARGET_CLEARED | COLLISION |
| c2 | aeb_decision_t | — | — | 2.350 |
| c2 | brake_onset_t | — | — |  |
| c2 | min_distance_m | 0.568 ± 0.000 | 0.644 |  |
| c2 | stopping_distance_m | — | — |  |
| c2 | impact_speed_mps | — | — |  |
| c2 | ego_impact_speed_mps | — | — | 16.627 |
| c2 | radar_first_detection_t | 1.800 ± 0.000 | — |  |
| c2 | ground_truth_aeb_decision_t | — | — |  |
| c3 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| c3 | aeb_decision_t | 1.950 ± 0.000 | 1.850 | 2.100 |
| c3 | brake_onset_t | 2.200 ± 0.000 | 2.100 |  |
| c3 | min_distance_m | 1.137 ± 0.004 | 2.580 | 0.990 |
| c3 | stopping_distance_m | 14.628 ± 0.008 | 14.089 |  |
| c3 | impact_speed_mps | — | — |  |
| c3 | ego_impact_speed_mps | — | — |  |
| c3 | radar_first_detection_t | 1.950 ± 0.000 | — |  |
| c3 | ground_truth_aeb_decision_t | 1.950 ± 0.000 | — |  |
| c4 | end_reason | TARGET_CLEARED ×3 | TARGET_CLEARED | EGO_STOPPED |
| c4 | aeb_decision_t | — | — | 4.250 |
| c4 | brake_onset_t | — | — |  |
| c4 | min_distance_m | 3.412 ± 0.000 | 3.429 | 5.692 |
| c4 | stopping_distance_m | — | — |  |
| c4 | impact_speed_mps | — | — |  |
| c4 | ego_impact_speed_mps | — | — |  |
| c4 | radar_first_detection_t | 1.950 ± 0.000 | — |  |
| c4 | ground_truth_aeb_decision_t | — | — |  |
| c5 | end_reason | COLLISION ×3 | COLLISION | COLLISION |
| c5 | aeb_decision_t | 1.900 ± 0.000 | 2.200 | 2.050 |
| c5 | brake_onset_t | 2.150 ± 0.000 | 2.450 |  |
| c5 | min_distance_m | 0.000 ± 0.000 | 0.000 |  |
| c5 | stopping_distance_m | 16.226 ± 0.127 | 15.960 |  |
| c5 | impact_speed_mps | 8.846 ± 0.093 | 10.203 |  |
| c5 | ego_impact_speed_mps | 8.704 ± 0.094 | 10.092 | 11.577 |
| c5 | radar_first_detection_t | 1.833 ± 0.029 | — |  |
| c5 | ground_truth_aeb_decision_t | 2.600 ± 0.000 | — |  |
| c6 | end_reason | TARGET_CLEARED ×3 | TARGET_CLEARED | TARGET_CLEARED |
| c6 | aeb_decision_t | — | — | — |
| c6 | brake_onset_t | — | — |  |
| c6 | min_distance_m | 14.135 ± 0.000 | 19.441 | 14.135 |
| c6 | stopping_distance_m | — | — |  |
| c6 | impact_speed_mps | — | — |  |
| c6 | ego_impact_speed_mps | — | — |  |
| c6 | radar_first_detection_t | 1.950 ± 0.000 | — |  |
| c6 | ground_truth_aeb_decision_t | — | — |  |
| c7 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| c7 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| c7 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| c7 | min_distance_m | 3.284 ± 0.009 | 3.275 |  |
| c7 | stopping_distance_m | 10.314 ± 0.009 | 10.314 |  |
| c7 | impact_speed_mps | — | — |  |
| c7 | ego_impact_speed_mps | — | — |  |
| c7 | radar_first_detection_t | 1.900 ± 0.000 | — |  |
| c7 | ground_truth_aeb_decision_t | 2.250 ± 0.000 | — |  |
