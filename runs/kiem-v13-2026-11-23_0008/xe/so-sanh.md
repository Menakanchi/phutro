# So sánh CARLA (profile hiện hành) với bộ động học — ca người đi bộ

Mỗi ca CARLA chạy 3 lần (trung bình ± độ lệch chuẩn).
Định dạng .xosc: model3-c1 vehicsim.xosc/v13, model3-c3 vehicsim.xosc/v13, model3-c7 vehicsim.xosc/v13, patrol-c1 vehicsim.xosc/v13, patrol-c3 vehicsim.xosc/v13, patrol-c7 vehicsim.xosc/v13, sprinter-c1 vehicsim.xosc/v13, sprinter-c3 vehicsim.xosc/v13, sprinter-c7 vehicsim.xosc/v13

| Ca | Chỉ số | CARLA | Bộ động học | CARLA 13/11 (radar, trước v7/v8) |
|---|---|---|---|---|
| model3-c1 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| model3-c1 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| model3-c1 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| model3-c1 | min_distance_m | 4.174 ± 0.036 | 4.257 |  |
| model3-c1 | stopping_distance_m | 9.445 ± 0.036 | 9.332 |  |
| model3-c1 | impact_speed_mps | — | — |  |
| model3-c1 | ego_impact_speed_mps | — | — |  |
| model3-c1 | radar_first_detection_t | 1.900 ± 0.000 | — |  |
| model3-c1 | ground_truth_aeb_decision_t | 2.300 ± 0.000 | — |  |
| model3-c3 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| model3-c3 | aeb_decision_t | 1.950 ± 0.000 | 1.850 |  |
| model3-c3 | brake_onset_t | 2.200 ± 0.000 | 2.100 |  |
| model3-c3 | min_distance_m | 1.163 ± 0.001 | 2.530 |  |
| model3-c3 | stopping_distance_m | 14.418 ± 0.000 | 14.089 |  |
| model3-c3 | impact_speed_mps | — | — |  |
| model3-c3 | ego_impact_speed_mps | — | — |  |
| model3-c3 | radar_first_detection_t | 1.950 ± 0.000 | — |  |
| model3-c3 | ground_truth_aeb_decision_t | 1.900 ± 0.000 | — |  |
| model3-c7 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| model3-c7 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| model3-c7 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| model3-c7 | min_distance_m | 3.244 ± 0.009 | 3.275 |  |
| model3-c7 | stopping_distance_m | 10.375 ± 0.009 | 10.314 |  |
| model3-c7 | impact_speed_mps | — | — |  |
| model3-c7 | ego_impact_speed_mps | — | — |  |
| model3-c7 | radar_first_detection_t | 1.900 ± 0.000 | — |  |
| model3-c7 | ground_truth_aeb_decision_t | 2.300 ± 0.000 | — |  |
| patrol-c1 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| patrol-c1 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| patrol-c1 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| patrol-c1 | min_distance_m | 3.793 ± 0.021 | 4.257 |  |
| patrol-c1 | stopping_distance_m | 9.826 ± 0.021 | 9.332 |  |
| patrol-c1 | impact_speed_mps | — | — |  |
| patrol-c1 | ego_impact_speed_mps | — | — |  |
| patrol-c1 | radar_first_detection_t | 1.900 ± 0.000 | — |  |
| patrol-c1 | ground_truth_aeb_decision_t | 2.250 ± 0.000 | — |  |
| patrol-c3 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| patrol-c3 | aeb_decision_t | 1.950 ± 0.000 | 1.850 |  |
| patrol-c3 | brake_onset_t | 2.200 ± 0.000 | 2.100 |  |
| patrol-c3 | min_distance_m | 0.866 ± 0.000 | 2.533 |  |
| patrol-c3 | stopping_distance_m | 16.247 ± 0.016 | 14.089 |  |
| patrol-c3 | impact_speed_mps | — | — |  |
| patrol-c3 | ego_impact_speed_mps | — | — |  |
| patrol-c3 | radar_first_detection_t | 1.950 ± 0.000 | — |  |
| patrol-c3 | ground_truth_aeb_decision_t | 1.900 ± 0.000 | — |  |
| patrol-c7 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| patrol-c7 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| patrol-c7 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| patrol-c7 | min_distance_m | 2.648 ± 0.011 | 3.275 |  |
| patrol-c7 | stopping_distance_m | 10.971 ± 0.011 | 10.314 |  |
| patrol-c7 | impact_speed_mps | — | — |  |
| patrol-c7 | ego_impact_speed_mps | — | — |  |
| patrol-c7 | radar_first_detection_t | 1.900 ± 0.000 | — |  |
| patrol-c7 | ground_truth_aeb_decision_t | 2.250 ± 0.000 | — |  |
| sprinter-c1 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| sprinter-c1 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| sprinter-c1 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| sprinter-c1 | min_distance_m | 3.522 ± 0.001 | 4.257 |  |
| sprinter-c1 | stopping_distance_m | 10.135 ± 0.001 | 9.332 |  |
| sprinter-c1 | impact_speed_mps | — | — |  |
| sprinter-c1 | ego_impact_speed_mps | — | — |  |
| sprinter-c1 | radar_first_detection_t | 1.900 ± 0.000 | — |  |
| sprinter-c1 | ground_truth_aeb_decision_t | 2.300 ± 0.000 | — |  |
| sprinter-c3 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| sprinter-c3 | aeb_decision_t | 1.950 ± 0.000 | 1.850 |  |
| sprinter-c3 | brake_onset_t | 2.200 ± 0.000 | 2.100 |  |
| sprinter-c3 | min_distance_m | 0.947 ± 0.000 | 2.567 |  |
| sprinter-c3 | stopping_distance_m | 15.953 ± 0.056 | 14.089 |  |
| sprinter-c3 | impact_speed_mps | — | — |  |
| sprinter-c3 | ego_impact_speed_mps | — | — |  |
| sprinter-c3 | radar_first_detection_t | 1.950 ± 0.000 | — |  |
| sprinter-c3 | ground_truth_aeb_decision_t | 1.900 ± 0.000 | — |  |
| sprinter-c7 | end_reason | EGO_STOPPED ×3 | EGO_STOPPED |  |
| sprinter-c7 | aeb_decision_t | 2.250 ± 0.000 | 2.250 |  |
| sprinter-c7 | brake_onset_t | 2.500 ± 0.000 | 2.500 |  |
| sprinter-c7 | min_distance_m | 2.335 ± 0.053 | 3.275 |  |
| sprinter-c7 | stopping_distance_m | 11.322 ± 0.053 | 10.314 |  |
| sprinter-c7 | impact_speed_mps | — | — |  |
| sprinter-c7 | ego_impact_speed_mps | — | — |  |
| sprinter-c7 | radar_first_detection_t | 1.900 ± 0.000 | — |  |
| sprinter-c7 | ground_truth_aeb_decision_t | 2.300 ± 0.000 | — |  |
