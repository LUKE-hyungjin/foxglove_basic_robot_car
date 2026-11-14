import pytest

from robot_car_sim.wheel_debug import expected_wheel_speeds

RADIUS = 0.05
SEPARATION = 0.2


def test_straight_line_spins_both_wheels_equally():
    assert expected_wheel_speeds(0.1, 0.0, RADIUS, SEPARATION) == pytest.approx((2.0, 2.0))


def test_turning_left_in_place_spins_wheels_opposite():
    # Left wheel backward, right wheel forward: 1 rad/s * 0.1 m / 0.05 m = 2 rad/s.
    assert expected_wheel_speeds(0.0, 1.0, RADIUS, SEPARATION) == pytest.approx((-2.0, 2.0))


def test_arc_adds_both_parts():
    assert expected_wheel_speeds(0.2, 0.5, RADIUS, SEPARATION) == pytest.approx((3.0, 5.0))
