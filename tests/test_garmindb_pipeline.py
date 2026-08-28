"""
Unit tests for GarminDb SQLite Direct Pipeline.
"""
import os
import tempfile
import sqlite3
from datetime import datetime, date
import pytest

from src.models.user_profile import UserProfile
from src.db.database import DatabaseManager
from src.ingestion.garmindb_pipeline import GarminDbPipeline


@pytest.fixture
def mock_garmindb_dir():
    """Creates a mock GarminDb directory with garmin_activities.db and garmin.db."""
    temp_dir = tempfile.mkdtemp()
    act_db_path = os.path.join(temp_dir, "garmin_activities.db")
    garmin_db_path = os.path.join(temp_dir, "garmin.db")

    # 1. Setup garmin_activities.db
    with sqlite3.connect(act_db_path) as conn:
        conn.execute("""
        CREATE TABLE activities (
            activity_id TEXT PRIMARY KEY, name TEXT, description TEXT, sport TEXT, sub_sport TEXT,
            start_time TEXT, stop_time TEXT, elapsed_time TEXT, moving_time TEXT, distance REAL,
            avg_hr REAL, max_hr REAL, calories REAL, avg_cadence REAL, max_cadence REAL,
            avg_speed REAL, max_speed REAL, ascent REAL, descent REAL, training_effect REAL,
            anaerobic_training_effect REAL, avg_temperature REAL
        )
        """)
        conn.execute("""
        CREATE TABLE steps_activities (
            activity_id TEXT PRIMARY KEY, steps INTEGER, avg_pace TEXT, avg_moving_pace TEXT, max_pace TEXT,
            avg_steps_per_min REAL, max_steps_per_min REAL, avg_step_length REAL, avg_vertical_ratio REAL,
            avg_vertical_oscillation REAL, avg_ground_contact_time TEXT, vo2_max REAL
        )
        """)
        conn.execute("""
        CREATE TABLE activity_laps (
            activity_id TEXT, lap INTEGER, start_time TEXT, elapsed_time TEXT, moving_time TEXT,
            distance REAL, avg_hr REAL, max_hr REAL, avg_speed REAL, avg_cadence REAL, ascent REAL, descent REAL
        )
        """)
        # Insert sample activity
        conn.execute("""
        INSERT INTO activities VALUES (
            '1001', 'Morning Tempo Run', 'Felt smooth', 'running', 'generic',
            '2026-08-20 07:00:00.000000', '2026-08-20 07:45:00.000000', '00:45:00.000000', '00:45:00.000000',
            10.0, 160.0, 175.0, 650.0, 88.0, 95.0, 13.33, 16.0, 50.0, 45.0, 3.8, 1.5, 22.0
        )
        """)
        conn.execute("""
        INSERT INTO steps_activities VALUES (
            '1001', 7920, '00:04:30.000000', '00:04:30.000000', '00:03:45.000000',
            176.0, 190.0, 1.25, 7.5, 8.2, '00:00:00.235000', 52.0
        )
        """)
        conn.execute("""
        INSERT INTO activity_laps VALUES (
            '1001', 0, '2026-08-20 07:00:00.000000', '00:22:30.000000', '00:22:30.000000',
            5.0, 158.0, 168.0, 13.33, 88.0, 25.0, 20.0
        )
        """)
        conn.execute("""
        INSERT INTO activity_laps VALUES (
            '1001', 1, '2026-08-20 07:22:30.000000', '00:22:30.000000', '00:22:30.000000',
            5.0, 162.0, 175.0, 13.33, 88.0, 25.0, 25.0
        )
        """)

    # 2. Setup garmin.db
    with sqlite3.connect(garmin_db_path) as conn:
        conn.execute("CREATE TABLE resting_hr (day TEXT PRIMARY KEY, resting_heart_rate REAL)")
        conn.execute("CREATE TABLE sleep (day TEXT PRIMARY KEY, total_sleep TEXT, deep_sleep TEXT, light_sleep TEXT, rem_sleep TEXT, score REAL)")
        conn.execute("CREATE TABLE daily_summary (day TEXT PRIMARY KEY, hr_min REAL, hr_max REAL, rhr REAL, stress_avg REAL, steps INTEGER, calories_total REAL)")
        conn.execute("CREATE TABLE weight (day TEXT PRIMARY KEY, weight REAL)")

        conn.execute("INSERT INTO resting_hr VALUES ('2026-08-20 00:00:00.000000', 51.0)")
        conn.execute("INSERT INTO sleep VALUES ('2026-08-20 00:00:00.000000', '07:45:00.000000', '01:15:00.000000', '04:30:00.000000', '02:00:00.000000', 88.0)")
        conn.execute("INSERT INTO daily_summary VALUES ('2026-08-20 00:00:00.000000', 48.0, 175.0, 51.0, 22.0, 12500, 2400.0)")
        conn.execute("INSERT INTO weight VALUES ('2026-08-20 00:00:00.000000', 65.5)")

    yield temp_dir


def test_garmindb_pipeline_sync(mock_garmindb_dir):
    temp_target_dir = tempfile.mkdtemp()
    target_db_path = os.path.join(temp_target_dir, "test_target.db")
    target_db = DatabaseManager(db_path=target_db_path)
    profile = UserProfile(resting_hr=60, weight_kg=75.0)

    # Check stats
    stats = GarminDbPipeline.get_garmindb_stats(mock_garmindb_dir)
    assert stats["available"] is True
    assert stats["activity_count"] == 1
    assert stats["laps_count"] == 2
    assert stats["health_days_count"] == 1

    # Perform Sync
    result = GarminDbPipeline.sync_all(
        target_db=target_db,
        user_profile=profile,
        db_dir=mock_garmindb_dir,
    )
    assert result["status"] == "success"
    assert result["activities_extracted"] == 1
    assert result["activities_canonical_saved"] == 1
    assert result["health_days_saved"] == 1
    assert result["laps_processed"] == 2

    # Verify Activity saved in target DB
    acts = target_db.get_all_activities()
    assert len(acts) == 1
    act = acts[0]
    assert act.source == "garmin"
    assert act.distance_meters == 10000.0
    assert act.avg_hr == 160.0
    assert act.avg_cadence == 176.0
    assert act.aerobic_te == 3.8
    assert "laps" in act.raw_data
    assert len(act.raw_data["laps"]) == 2

    # Verify Profile updated
    assert profile.resting_hr == 51
    assert profile.weight_kg == 65.5


def test_raw_running_activities_reads_only_garmin_runs(mock_garmindb_dir):
    activities = GarminDbPipeline.get_raw_running_activities(mock_garmindb_dir)

    assert len(activities) == 1
    assert activities[0].source == "garmin"
    assert activities[0].sport_type == "run"
