# So sánh CARLA (profile hiện hành) với bộ động học — ca người đi bộ

Mỗi ca CARLA chạy 3 lần (trung bình ± độ lệch chuẩn).
Định dạng .xosc: model3-c1 vehicsim.xosc/v15, model3-c3 vehicsim.xosc/v15, model3-c7 vehicsim.xosc/v15, patrol-c1 vehicsim.xosc/v15, patrol-c3 vehicsim.xosc/v15, patrol-c7 vehicsim.xosc/v15, sprinter-c1 vehicsim.xosc/v15, sprinter-c3 vehicsim.xosc/v15, sprinter-c7 vehicsim.xosc/v15

| Ca | Chỉ số | CARLA | Bộ động học | CARLA 13/11 (radar, trước v7/v8) |
|---|---|---|---|---|
| model3-c1 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| model3-c1 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| model3-c1 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| model3-c1 | min_distance_m | 4.221 ± 0.011 | 4.257 |  |
| model3-c1 | stopping_distance_m | 9.398 ± 0.011 | 9.332 |  |
| model3-c1 | impact_speed_mps | — | — |  |
| model3-c1 | ego_impact_speed_mps | — | — |  |
| model3-c1 | radar_first_detection_t | 2.217 ± 0.029 | — |  |
| model3-c1 | ground_truth_aeb_decision_t | 2.300 ± 0.000 | — |  |
| model3-c3 | end_reason | EGO_STOPPED ×3 | TARGET_CLEARED |  |
| model3-c3 | aeb_decision_t | 2.250 ± 0.000 | — |  |
| model3-c3 | brake_onset_t | 2.500 ± 0.000 | — |  |
| model3-c3 | min_distance_m | 0.860 ± 0.000 | 0.888 |  |
| model3-c3 | stopping_distance_m | 14.392 ± 0.046 | — |  |
| model3-c3 | impact_speed_mps | — | — |  |
| model3-c3 | ego_impact_speed_mps | — | — |  |
| model3-c3 | radar_first_detection_t | 2.250 ± 0.000 | — |  |
| model3-c3 | ground_truth_aeb_decision_t | 2.550 ± 0.000 | — |  |
| model3-c7 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| model3-c7 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| model3-c7 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| model3-c7 | min_distance_m | 3.249 ± 0.000 | 3.275 |  |
| model3-c7 | stopping_distance_m | 10.370 ± 0.000 | 10.314 |  |
| model3-c7 | impact_speed_mps | — | — |  |
| model3-c7 | ego_impact_speed_mps | — | — |  |
| model3-c7 | radar_first_detection_t | 2.217 ± 0.029 | — |  |
| model3-c7 | ground_truth_aeb_decision_t | 2.300 ± 0.000 | — |  |
| patrol-c1 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| patrol-c1 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| patrol-c1 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| patrol-c1 | min_distance_m | 4.204 ± 0.029 | 4.257 |  |
| patrol-c1 | stopping_distance_m | 9.415 ± 0.029 | 9.332 |  |
| patrol-c1 | impact_speed_mps | — | — |  |
| patrol-c1 | ego_impact_speed_mps | — | — |  |
| patrol-c1 | radar_first_detection_t | 2.217 ± 0.029 | — |  |
| patrol-c1 | ground_truth_aeb_decision_t | 2.250 ± 0.000 | — |  |
| patrol-c3 | end_reason | EGO_STOPPED ×3 | TARGET_CLEARED |  |
| patrol-c3 | aeb_decision_t | 2.300 ± 0.000 | — |  |
| patrol-c3 | brake_onset_t | 2.550 ± 0.000 | — |  |
| patrol-c3 | min_distance_m | 0.866 ± 0.000 | 0.881 |  |
| patrol-c3 | stopping_distance_m | 15.627 ± 0.016 | — |  |
| patrol-c3 | impact_speed_mps | — | — |  |
| patrol-c3 | ego_impact_speed_mps | — | — |  |
| patrol-c3 | radar_first_detection_t | 2.200 ± 0.000 | — |  |
| patrol-c3 | ground_truth_aeb_decision_t | 2.550 ± 0.000 | — |  |
| patrol-c7 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| patrol-c7 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| patrol-c7 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| patrol-c7 | min_distance_m | 3.136 ± 0.026 | 3.275 |  |
| patrol-c7 | stopping_distance_m | 10.483 ± 0.027 | 10.314 |  |
| patrol-c7 | impact_speed_mps | — | — |  |
| patrol-c7 | ego_impact_speed_mps | — | — |  |
| patrol-c7 | radar_first_detection_t | 2.200 ± 0.000 | — |  |
| patrol-c7 | ground_truth_aeb_decision_t | 2.250 ± 0.000 | — |  |
| sprinter-c1 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| sprinter-c1 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| sprinter-c1 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| sprinter-c1 | min_distance_m | 4.292 ± 0.001 | 4.257 |  |
| sprinter-c1 | stopping_distance_m | 9.365 ± 0.001 | 9.332 |  |
| sprinter-c1 | impact_speed_mps | — | — |  |
| sprinter-c1 | ego_impact_speed_mps | — | — |  |
| sprinter-c1 | radar_first_detection_t | 2.250 ± 0.000 | — |  |
| sprinter-c1 | ground_truth_aeb_decision_t | 2.300 ± 0.000 | — |  |
| sprinter-c3 | end_reason | EGO_STOPPED ×3 | TARGET_CLEARED |  |
| sprinter-c3 | aeb_decision_t | 2.150 ± 0.000 | — |  |
| sprinter-c3 | brake_onset_t | 2.400 ± 0.000 | — |  |
| sprinter-c3 | min_distance_m | 0.947 ± 0.000 | 0.962 |  |
| sprinter-c3 | stopping_distance_m | 14.922 ± 0.001 | — |  |
| sprinter-c3 | impact_speed_mps | — | — |  |
| sprinter-c3 | ego_impact_speed_mps | — | — |  |
| sprinter-c3 | radar_first_detection_t | 2.150 ± 0.000 | — |  |
| sprinter-c3 | ground_truth_aeb_decision_t | 2.750 ± 0.000 | — |  |
| sprinter-c7 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| sprinter-c7 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| sprinter-c7 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| sprinter-c7 | min_distance_m | 3.072 ± 0.000 | 3.275 |  |
| sprinter-c7 | stopping_distance_m | 10.585 ± 0.000 | 10.314 |  |
| sprinter-c7 | impact_speed_mps | — | — |  |
| sprinter-c7 | ego_impact_speed_mps | — | — |  |
| sprinter-c7 | radar_first_detection_t | 2.250 ± 0.000 | — |  |
| sprinter-c7 | ground_truth_aeb_decision_t | 2.300 ± 0.000 | — |  |
