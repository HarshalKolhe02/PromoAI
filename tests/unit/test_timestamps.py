"""
Unit tests for timestamp parsing, seconds normalization, and duration calculation.
"""
import pytest
from app.utils.timestamps import (
    parse_timestamp_to_seconds,
    format_seconds_to_timestamp,
    calculate_duration,
    is_duration_within_promo_bounds,
    compute_interval_overlap,
    compute_jaccard_overlap
)


def test_parse_timestamp_formats():
    # MM:SS
    assert parse_timestamp_to_seconds("01:23") == 83.0
    # MM:SS.mmm
    assert parse_timestamp_to_seconds("01:23.45") == 83.45
    # (MM:SS.ss)
    assert parse_timestamp_to_seconds("(00:04.80)") == 4.80
    # [MM:SS]
    assert parse_timestamp_to_seconds("[02:18.00]") == 138.0
    # HH:MM:SS
    assert parse_timestamp_to_seconds("01:02:03") == 3723.0
    # Missing / None
    assert parse_timestamp_to_seconds(None) is None
    assert parse_timestamp_to_seconds("") is None
    assert parse_timestamp_to_seconds("None") is None
    assert parse_timestamp_to_seconds("invalid") is None


def test_format_seconds_to_timestamp():
    assert format_seconds_to_timestamp(83.0) == "01:23"
    assert format_seconds_to_timestamp(3723.0) == "01:02:03"
    assert format_seconds_to_timestamp(4.80, include_millis=True) == "00:04.80"
    assert format_seconds_to_timestamp(None) == "00:00"


def test_duration_calculation_and_bounds():
    # Valid 35s promo
    dur = calculate_duration(10.0, 45.0)
    assert dur == 35.0
    assert is_duration_within_promo_bounds(dur) is True

    # Under 20s (15s)
    short_dur = calculate_duration(10.0, 25.0)
    assert short_dur == 15.0
    assert is_duration_within_promo_bounds(short_dur) is False

    # Over 60s (65s)
    long_dur = calculate_duration(10.0, 75.0)
    assert long_dur == 65.0
    assert is_duration_within_promo_bounds(long_dur) is False

    # Invalid sequence (end < start)
    assert calculate_duration(50.0, 20.0) is None


def test_jaccard_overlap():
    # Identical intervals
    assert compute_jaccard_overlap(10.0, 40.0, 10.0, 40.0) == 1.0
    # Disjoint intervals
    assert compute_jaccard_overlap(10.0, 20.0, 30.0, 40.0) == 0.0
    # Partial overlap [10, 40] and [20, 50]: intersection=20, union=40 -> 0.5
    assert compute_jaccard_overlap(10.0, 40.0, 20.0, 50.0) == 0.5
