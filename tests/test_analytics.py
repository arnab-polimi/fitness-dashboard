"""
Unit tests for Analytics Engine: TRIMP, TSS, EWMA (CTL/ATL/TSB), VDOT, and Race Predictor.
"""
from datetime import datetime, timedelta, date
import pytest

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.analytics.training_load import (
    calculate_banister_trimp,
    calculate_rtss,
    calculate_hrtss,
    TrainingLoadEngine,
)
from src.analytics.running_metrics import (
    calculate_efficiency_factor,
    calculate_vdot_from_race,
    get_training_paces_from_vdot,
    estimate_activity_aerobic_decoupling,
)
from src.analytics.race_predictor import RacePredictor


def test_banister_trimp_calculation():
    profile = UserProfile(resting_hr=50, max_hr=190, gender="male")
    # 60 min at 150 bpm
    trimp = calculate_banister_trimp(duration_seconds=3600, avg_hr=150, user_profile=profile)
    assert trimp > 50.0
    assert trimp < 150.0


def test_rtss_calculation():
    # 1 hour at threshold pace (270s/km) should yield ~100 TSS
    rtss = calculate_rtss(duration_seconds=3600, avg_pace_sec_km=270.0, threshold_pace_sec_km=270.0)
    assert 98.0 <= rtss <= 102.0

    # 1 hour at slower pace (300s/km) should yield lower TSS
    rtss_easy = calculate_rtss(duration_seconds=3600, avg_pace_sec_km=300.0, threshold_pace_sec_km=270.0)
    assert rtss_easy < 90.0


def test_efficiency_factor():
    # Speed 3.33 m/s (200 m/min) at 150 bpm -> EF = 200 / 150 = 1.333
    ef = calculate_efficiency_factor(speed_m_s=3.333, avg_hr=150)
    assert ef is not None
    assert 1.30 <= ef <= 1.36


def test_vdot_and_paces():
    # 5,000m in 20:00 (1200 sec) -> Daniels & Gilbert VDOT ~ 44.8
    vdot = calculate_vdot_from_race(5000.0, 1200.0)
    assert vdot is not None
    assert 42.0 <= vdot <= 48.0

    paces = get_training_paces_from_vdot(vdot)
    assert "Easy (E-Pace)" in paces
    assert "Threshold (T-Pace)" in paces
    assert "Interval (I-Pace)" in paces


def test_race_predictor():
    profile = UserProfile(threshold_pace_sec_km=250.0)
    dt = datetime(2026, 8, 1, 7, 0)
    # Fast 5k anchor run
    act = Activity(
        id="act_5k",
        source="manual",
        start_time=dt,
        sport_type="run",
        distance_meters=5000,
        duration_seconds=1200,  # 20:00 5k
        avg_hr=170,
    )
    preds = RacePredictor.predict_all([act], profile, current_ctl=55.0)
    assert len(preds) == 4
    names = [p.distance_name for p in preds]
    assert "5K" in names
    assert "10K" in names
    assert "Half Marathon" in names
    assert "Marathon" in names

    pred_5k = next(p for p in preds if p.distance_name == "5K")
    assert 1100 <= pred_5k.predicted_time_seconds <= 1350


def test_training_load_engine():
    profile = UserProfile(threshold_pace_sec_km=270.0)
    base_dt = datetime(2026, 8, 1, 7, 0)
    activities = []
    for i in range(14):
        act = Activity(
            id=f"act_{i}",
            source="manual",
            start_time=base_dt + timedelta(days=i),
            sport_type="run",
            distance_meters=10000,
            duration_seconds=2700,
            avg_pace_sec_km=270,
            avg_hr=160,
        )
        activities.append(act)

    daily_loads = TrainingLoadEngine.calculate_daily_metrics(
        activities, profile, start_date=date(2026, 8, 1), end_date=date(2026, 8, 14)
    )
    assert len(daily_loads) >= 14
    # Fitness (CTL) should build up
    assert daily_loads[-1].ctl > daily_loads[0].ctl
    # On the 14th day of continuous hard training, ATL (Fatigue) should exceed CTL (Fitness)
    assert daily_loads[-1].atl > daily_loads[-1].ctl
    # Form (TSB) should be negative (Fatigued)
    assert daily_loads[-1].tsb < 0


def test_training_load_matches_garmin_study_hrtss_and_discrete_updates():
    profile = UserProfile(lthr=178)
    activity = Activity(
        id="threshold_run",
        source="garmin",
        start_time=datetime(2026, 8, 1, 7, 0),
        sport_type="run",
        duration_seconds=3600,
        moving_time_seconds=3600,
        avg_hr=178,
    )

    loads = TrainingLoadEngine.calculate_daily_metrics(
        [activity], profile, start_date=date(2026, 8, 1), end_date=date(2026, 8, 1)
    )

    # Garmin study: TSS = 60 × (178 / 178)^2 × 100 / 60 = 100,
    # then CTL += TSS / 42 and ATL += TSS / 7.
    assert loads[0].total_tss == 100.0
    assert loads[0].ctl == pytest.approx(100 / 42, abs=0.01)
    assert loads[0].atl == pytest.approx(100 / 7, abs=0.01)
    assert loads[0].tsb == pytest.approx((100 / 42) - (100 / 7), abs=0.01)


def test_training_load_excludes_non_running_activities():
    profile = UserProfile(lthr=178)
    activity = Activity(
        id="ride",
        source="garmin",
        start_time=datetime(2026, 8, 1, 7, 0),
        sport_type="cycling",
        duration_seconds=3600,
        moving_time_seconds=3600,
        avg_hr=150,
    )

    assert TrainingLoadEngine.calculate_daily_metrics([activity], profile) == []
