from app.core.decision import compute_decision
from app.services.proximity import (
    approximate_road_segment_id,
    direction_from_heading,
    haversine_distance_meters,
    is_driver_approaching_hazard,
    warning_distance_meters,
)


def test_decision_accepts_critical():
    decision = compute_decision("critical")

    assert decision["action"] == "brake"
    assert decision["recommended_speed_kmph"] == 5
    assert decision["risk_level"] == "critical"


def test_haversine_distance_is_reasonable_for_nearby_points():
    distance = haversine_distance_meters(12.9716, 77.5946, 12.9718, 77.5948)

    assert 25 <= distance <= 35


def test_direction_and_segment_are_stable():
    assert direction_from_heading(0) == "north"
    assert direction_from_heading(91) == "east"
    assert direction_from_heading(None) == "unknown"
    assert approximate_road_segment_id(12.97161, 77.59461, 91) == "seg:12.9716:77.5946:east"


def test_driver_heading_filters_behind_hazards():
    assert is_driver_approaching_hazard(12.9716, 77.5946, 12.9726, 77.5946, 0)
    assert not is_driver_approaching_hazard(12.9716, 77.5946, 12.9706, 77.5946, 0)


def test_warning_distance_scales_with_severity_and_speed():
    slow_low = warning_distance_meters("low", 10)
    fast_low = warning_distance_meters("low", 80)
    critical = warning_distance_meters("critical", 10)

    assert fast_low > slow_low
    assert critical > slow_low

