"""
Unit tests for Activity Deduplication and intelligent merging.
"""
from datetime import datetime, timedelta
import pytest

from src.models.activity import Activity
from src.ingestion.deduplicator import ActivityDeduplicator


def test_activity_deduplication_exact_match():
    dt = datetime(2026, 8, 20, 7, 0, 0)
    act1 = Activity(
        id="garmin_1",
        source="garmin",
        start_time=dt,
        sport_type="run",
        title="Garmin Run",
        duration_seconds=3000,
        distance_meters=10000,
        avg_hr=155,
        avg_cadence=174,
        aerobic_te=3.5,
    )
    act2 = Activity(
        id="strava_1",
        source="strava",
        start_time=dt + timedelta(minutes=1),  # 1 min difference
        sport_type="run",
        title="Morning 10k with friends",
        duration_seconds=2990,  # 10s difference
        distance_meters=10020,  # 20m difference
        avg_hr=155,
        rpe=6,
    )

    assert ActivityDeduplicator.are_activities_duplicate(act1, act2) is True

    # Test merge
    merged = ActivityDeduplicator.merge_activities(act1, act2)
    assert merged.title == "Morning 10k with friends"  # Preferred Strava custom name
    assert merged.avg_cadence == 174  # Preserved Garmin cadence
    assert merged.aerobic_te == 3.5  # Preserved Garmin TE
    assert merged.rpe == 6  # Preserved Strava RPE


def test_activity_deduplication_non_match():
    dt1 = datetime(2026, 8, 20, 7, 0, 0)
    dt2 = datetime(2026, 8, 20, 18, 0, 0)  # Evening run (different session)

    act1 = Activity(
        id="garmin_1",
        source="garmin",
        start_time=dt1,
        sport_type="run",
        duration_seconds=3000,
        distance_meters=10000,
    )
    act2 = Activity(
        id="garmin_2",
        source="garmin",
        start_time=dt2,
        sport_type="run",
        duration_seconds=3000,
        distance_meters=10000,
    )

    assert ActivityDeduplicator.are_activities_duplicate(act1, act2) is False


def test_deduplicate_list_workflow():
    dt = datetime(2026, 8, 20, 7, 0, 0)
    act1 = Activity(id="g1", source="garmin", start_time=dt, distance_meters=5000, duration_seconds=1500)
    act2 = Activity(id="s1", source="strava", start_time=dt, distance_meters=5010, duration_seconds=1505)
    act3 = Activity(id="g2", source="garmin", start_time=dt + timedelta(days=1), distance_meters=8000, duration_seconds=2400)

    deduped, stats = ActivityDeduplicator.deduplicate_list([act1, act2, act3])
    assert stats["total_incoming"] == 3
    assert stats["duplicates_found"] == 1
    assert stats["total_canonical"] == 2
