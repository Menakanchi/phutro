import pytest

from bench import model


def test_stopping_distance_matches_hand_calculation():
    # 40 km/h, a 8, J 20, t_d 0,15: 11,111·0,15 + 11,111·0,4 − 20·0,4³/6 + (11,111 − 1,6)²/16
    v0 = 40 / 3.6
    expected = v0 * 0.15 + v0 * 0.4 - 20 * 0.4 ** 3 / 6 + (v0 - 1.6) ** 2 / 16
    assert model.stopping_distance(v0, 8.0, 20.0, 0.15) == pytest.approx(expected)
    assert expected == pytest.approx(11.552, abs=1e-3)


def test_stop_during_ramp_branch_is_continuous():
    a_e, j = 8.0, 20.0
    edge = a_e * a_e / (2 * j)  # 1,6 m/s
    below = model.stopping_distance(edge - 1e-9, a_e, j, 0.15)
    above = model.stopping_distance(edge + 1e-9, a_e, j, 0.15)
    assert below == pytest.approx(above, abs=1e-6)


def test_integrated_profile_matches_closed_form():
    for kmh in (20, 40, 70):
        v0 = kmh / 3.6
        rows = model.brake_profile(v0, 8.0, 20.0, 0.15, 0.01)
        assert rows[-1]["v"] == 0.0
        assert rows[-1]["s"] == pytest.approx(model.stopping_distance(v0, 8.0, 20.0, 0.15), abs=0.02)


def test_wet_road_caps_decel_at_mu_g():
    assert model.effective_decel(8.0, 9.13, 0.65) == pytest.approx(0.65 * 9.81)
    assert model.effective_decel(4.0, 9.13, 0.65) == 4.0
    assert model.effective_decel("max", 9.13, 1.0) == 9.13


def test_pedal_profile_delay_ramp_and_hold():
    assert model.pedal_at(0.10, 8.0, 9.13, 0.15, 20.0) == 0.0
    assert model.pedal_at(0.25, 8.0, 9.13, 0.15, 20.0) == pytest.approx(0.1 * 20 / 9.13)
    assert model.pedal_at(5.0, 8.0, 9.13, 0.15, 20.0) == pytest.approx(8.0 / 9.13)
    assert model.pedal_at(5.0, "max", 9.13, 0.15, 20.0) == 1.0


def test_walker_enter_time_and_curb_stop():
    half = model.corridor_half_width(1.93, 0.3)  # 1,265
    assert model.walker_enter_time(-3.6, 1.5, half) == pytest.approx((3.6 - 1.265) / 1.5)
    assert model.walker_lat(10.0, -3.6, 1.5, stop_lat=-1.75) == -1.75


def test_combined_reference_brakes_in_time_with_margin():
    v0 = 40 / 3.6
    a_e, j, td = 8.0, 20.0, 0.15
    d_b = model.brake_distance_before_line(v0, a_e, j, td, 2.0)
    ref = model.combined_reference(v0, 25.0, d_b, a_e, j, td, -3.6, 1.5, 1.265, 0.01)
    assert ref.stop_gap_m == pytest.approx(2.0, abs=0.05)
    assert not ref.collision
    assert ref.min_gap_m == pytest.approx(2.0, abs=0.05)


def test_ttc_compensation():
    # 50 km/h, thực đạt 6 thay vì 8: ≈ 0,145 s
    assert model.ttc_compensation(13.9, 6.0, 8.0) == pytest.approx(13.9 / 2 * (1 / 6 - 1 / 8))
    assert model.ttc_compensation(13.9, None, 8.0) is None
