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
    )
    temp_db.save_user_profile(prof)

    loaded = temp_db.get_user_profile("default_user")
    assert loaded.name == "Alex Runner"
    assert loaded.weight_kg == 68.5
    assert loaded.resting_hr == 46
    assert loaded.lthr == 166
    assert loaded.threshold_pace_sec_km == 260.0
