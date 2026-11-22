# So sánh CARLA (profile hiện hành) với bộ động học — ca người đi bộ

Mỗi ca CARLA chạy 3 lần (trung bình ± độ lệch chuẩn).
Định dạng .xosc: patrol-c1 vehicsim.xosc/v14, patrol-c3 vehicsim.xosc/v14, patrol-c7 vehicsim.xosc/v14, sprinter-c1 vehicsim.xosc/v14, sprinter-c3 vehicsim.xosc/v14, sprinter-c7 vehicsim.xosc/v14

| Ca | Chỉ số | CARLA | Bộ động học | CARLA 13/11 (radar, trước v7/v8) |
|---|---|---|---|---|
| patrol-c1 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| patrol-c1 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| patrol-c1 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| patrol-c1 | min_distance_m | 4.056 ± 0.008 | 4.257 |  |
| patrol-c1 | stopping_distance_m | 9.563 ± 0.008 | 9.332 |  |
| patrol-c1 | impact_speed_mps | — | — |  |
| patrol-c1 | ego_impact_speed_mps | — | — |  |
| patrol-c1 | radar_first_detection_t | 1.900 ± 0.000 | — |  |
| patrol-c1 | ground_truth_aeb_decision_t | 2.250 ± 0.000 | — |  |
| patrol-c3 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| patrol-c3 | aeb_decision_t | 1.950 ± 0.000 | 1.850 |  |
| patrol-c3 | brake_onset_t | 2.200 ± 0.000 | 2.100 |  |
| patrol-c3 | min_distance_m | 0.866 ± 0.000 | 2.533 |  |
| patrol-c3 | stopping_distance_m | 15.839 ± 0.040 | 14.089 |  |
| patrol-c3 | impact_speed_mps | — | — |  |
| patrol-c3 | ego_impact_speed_mps | — | — |  |
| patrol-c3 | radar_first_detection_t | 1.950 ± 0.000 | — |  |
| patrol-c3 | ground_truth_aeb_decision_t | 1.900 ± 0.000 | — |  |
| patrol-c7 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| patrol-c7 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| patrol-c7 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| patrol-c7 | min_distance_m | 2.932 ± 0.001 | 3.275 |  |
| patrol-c7 | stopping_distance_m | 10.687 ± 0.001 | 10.314 |  |
| patrol-c7 | impact_speed_mps | — | — |  |
| patrol-c7 | ego_impact_speed_mps | — | — |  |
| patrol-c7 | radar_first_detection_t | 1.900 ± 0.000 | — |  |
| patrol-c7 | ground_truth_aeb_decision_t | 2.250 ± 0.000 | — |  |
| sprinter-c1 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| sprinter-c1 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| sprinter-c1 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| sprinter-c1 | min_distance_m | 3.779 ± 0.019 | 4.257 |  |
| sprinter-c1 | stopping_distance_m | 9.878 ± 0.019 | 9.332 |  |
| sprinter-c1 | impact_speed_mps | — | — |  |
| sprinter-c1 | ego_impact_speed_mps | — | — |  |
| sprinter-c1 | radar_first_detection_t | 1.900 ± 0.000 | — |  |
| sprinter-c1 | ground_truth_aeb_decision_t | 2.300 ± 0.000 | — |  |
| sprinter-c3 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| sprinter-c3 | aeb_decision_t | 1.950 ± 0.000 | 1.850 |  |
| sprinter-c3 | brake_onset_t | 2.200 ± 0.000 | 2.100 |  |
| sprinter-c3 | min_distance_m | 0.947 ± 0.000 | 2.567 |  |
| sprinter-c3 | stopping_distance_m | 15.445 ± 0.040 | 14.089 |  |
| sprinter-c3 | impact_speed_mps | — | — |  |
| sprinter-c3 | ego_impact_speed_mps | — | — |  |
| sprinter-c3 | radar_first_detection_t | 1.950 ± 0.000 | — |  |
| sprinter-c3 | ground_truth_aeb_decision_t | 1.900 ± 0.000 | — |  |
| sprinter-c7 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| sprinter-c7 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| sprinter-c7 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| sprinter-c7 | min_distance_m | 2.657 ± 0.065 | 3.275 |  |
| sprinter-c7 | stopping_distance_m | 11.000 ± 0.065 | 10.314 |  |
| sprinter-c7 | impact_speed_mps | — | — |  |
| sprinter-c7 | ego_impact_speed_mps | — | — |  |
| sprinter-c7 | radar_first_detection_t | 1.900 ± 0.000 | — |  |
| sprinter-c7 | ground_truth_aeb_decision_t | 2.300 ± 0.000 | — |  |
