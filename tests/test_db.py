"""
Unit tests for SQLite DatabaseManager operations.
"""
import os
import tempfile
from datetime import datetime
import pytest

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.db.database import DatabaseManager


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, f"test_fitness_{os.getpid()}_{id(temp_dir)}.db")
    manager = DatabaseManager(db_path=db_path)
    yield manager
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass


def test_save_and_retrieve_activity(temp_db):
    dt = datetime(2026, 8, 20, 7, 30)
    act = Activity(
        id="test_act_1",
        source="garmin",
        source_id="g123",
        start_time=dt,
        sport_type="run",
        title="Morning 8k",
        duration_seconds=2400.0,
        distance_meters=8000.0,
        avg_hr=152.0,
        avg_cadence=175.0,
        aerobic_te=3.2,
    )
    temp_db.save_activity(act)

    retrieved = temp_db.get_activity("test_act_1")
    assert retrieved is not None
    assert retrieved.id == "test_act_1"
    assert retrieved.source == "garmin"
    assert retrieved.distance_meters == 8000.0
    assert retrieved.avg_hr == 152.0
    assert retrieved.avg_cadence == 175.0
    assert retrieved.aerobic_te == 3.2


def test_bulk_save_and_query_df(temp_db):
    acts = [
        Activity(
            id=f"act_{i}",
            source="strava",
            start_time=datetime(2026, 8, i + 1, 7, 0),
            sport_type="run",
            distance_meters=5000.0,
            duration_seconds=1500.0,
        )
        for i in range(5)
    ]
    saved_count = temp_db.bulk_save_activities(acts)
    assert saved_count == 5
    assert temp_db.count_activities() == 5

    df = temp_db.get_activities_df()
    assert len(df) == 5
    assert "distance_km" in df.columns


def test_user_profile_persistence(temp_db):
    prof = UserProfile(
        user_id="default_user",
        name="Alex Runner",
        weight_kg=68.5,
        resting_hr=46,
        max_hr=188,
        lthr=166,
        threshold_pace_sec_km=260.0,
        target_race_distance_km=10.0,
        target_race_date="2026-10-15",
        auto_sync_baselines=False,
    )
    temp_db.save_user_profile(prof)

    loaded = temp_db.get_user_profile("default_user")
    assert loaded.name == "Alex Runner"
    assert loaded.weight_kg == 68.5
    assert loaded.resting_hr == 46
    assert loaded.lthr == 166
    assert loaded.threshold_pace_sec_km == 260.0
    assert loaded.target_race_distance_km == 10.0
    assert loaded.target_race_date == "2026-10-15"
    assert loaded.auto_sync_baselines is False


def test_user_profile_restores_from_json_backup_when_db_wiped(temp_db):
    prof = UserProfile(
        user_id="default_user",
        name="Resilient Athlete",
        resting_hr=44,
        weight_kg=62.0,
        target_race_distance_km=5.0,
    )
    temp_db.save_user_profile(prof)

    # Simulate database being wiped, e.g. replaced by remote git pull of empty/default DB
    with temp_db.get_connection() as conn:
        conn.execute("DELETE FROM user_profiles")
        conn.commit()

    # get_user_profile should restore from athlete_profile.json
    restored = temp_db.get_user_profile("default_user")
    assert restored.name == "Resilient Athlete"
    assert restored.resting_hr == 44
    assert restored.weight_kg == 62.0
    assert restored.target_race_distance_km == 5.0

    # Ensure SQLite DB was also re-synchronized
    with temp_db.get_connection() as conn:
        row = conn.execute("SELECT name FROM user_profiles WHERE user_id = 'default_user'").fetchone()
        assert row is not None
        assert row["name"] == "Resilient Athlete"


def test_fenix_7_activity_fields_persistence(temp_db):
    dt = datetime(2026, 9, 28, 8, 0)
    act = Activity(
        id="fenix7_run_1",
        source="garmin",
        source_id="g9999",
        start_time=dt,
        sport_type="run",
        title="Fenix 7 Trail Progression",
        distance_meters=12500.0,
        duration_seconds=3600.0,
        avg_hr=162.0,
        max_hr=178.0,
        aerobic_te=4.1,
        anaerobic_te=1.8,
        garmin_training_load=215.0,
        vertical_oscillation_mm=82.5,
        hrz_1_seconds=120.0,
        hrz_2_seconds=300.0,
        hrz_3_seconds=1800.0,
        hrz_4_seconds=1200.0,
        hrz_5_seconds=180.0,
        avg_respiration_rate=32.0,
        device_name="Fenix 7 (3485435196)",
    )
    temp_db.save_activity(act)

    retrieved = temp_db.get_activity("fenix7_run_1")
    assert retrieved is not None
    assert retrieved.garmin_training_load == 215.0
    assert retrieved.vertical_oscillation_mm == 82.5
    assert retrieved.hrz_1_seconds == 120.0
    assert retrieved.hrz_3_seconds == 1800.0
    assert retrieved.hrz_5_seconds == 180.0
    assert retrieved.avg_respiration_rate == 32.0
    assert retrieved.device_name == "Fenix 7 (3485435196)"


def test_fenix_7_daily_health_persistence(temp_db):
    records = [
        {
            "date": "2026-09-28",
            "resting_hr": 48.0,
            "hr_min": 45.0,
            "hr_max": 178.0,
            "stress_avg": 24.0,
            "steps": 14200,
            "sleep_duration_seconds": 28800,
            "body_battery_charged": 68.0,
            "body_battery_max": 95.0,
            "body_battery_min": 27.0,
            "spo2_avg": 97.5,
            "spo2_min": 94.0,
            "rr_waking_avg": 14.5,
            "floors_climbed": 16.0,
            "sleep_spo2_avg": 96.8,
            "sleep_rr_avg": 13.2,
            "sleep_stress_avg": 15.0,
            "sleep_qualifier": "good",
            "hrv_last_night": 65.0,
            "hrv_weekly_avg": 62.0,
            "hrv_status": "balanced",
        }
    ]
    saved = temp_db.save_daily_health_records(records)
    assert saved == 1

    df = temp_db.get_daily_health_df()
    assert not df.empty
    row = df.iloc[0]
    assert row["body_battery_max"] == 95.0
    assert row["body_battery_min"] == 27.0
    assert row["body_battery_charged"] == 68.0
    assert row["spo2_avg"] == 97.5
    assert row["rr_waking_avg"] == 14.5
    assert row["floors_climbed"] == 16.0
    assert row["hrv_last_night"] == 65.0
    assert row["hrv_weekly_avg"] == 62.0
    assert row["hrv_status"] == "balanced"
    assert row["sleep_qualifier"] == "good"
