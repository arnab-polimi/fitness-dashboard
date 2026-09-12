"""
Unit tests for Sleep Architecture & Telemetry analytics, chart rendering, and data generation.
"""
import pandas as pd
from datetime import date, timedelta

from src.data.synthetic_generator import generate_synthetic_health_records
from src.ui.charts import plot_sleep_stage_breakdown_chart, plot_sleep_score_and_rhr_chart
from src.ui.views.sleep_view import render_sleep_view
from src.models.user_profile import UserProfile
from src.analytics.sleep_score import SleepScoreCalculator
from src.db.database import DatabaseManager


def test_generate_synthetic_health_records():
    """Verify synthetic health and sleep records generation."""
    records = generate_synthetic_health_records(days=30)
    assert len(records) >= 30
    first = records[0]
    assert "sleep_duration_seconds" in first
    assert "deep_sleep_seconds" in first
    assert "rem_sleep_seconds" in first
    assert "sleep_score" in first
    assert "resting_hr" in first
    assert first["sleep_duration_seconds"] > 0
    assert first["sleep_score"] >= 50.0


def test_sleep_charts():
    """Verify Plotly sleep charts render without errors."""
    records = generate_synthetic_health_records(days=14)
    df = pd.DataFrame(records)

    fig_stages = plot_sleep_stage_breakdown_chart(df)
    assert fig_stages is not None
    assert len(fig_stages.data) == 3  # Deep, REM, Light

    fig_score = plot_sleep_score_and_rhr_chart(df)
    assert fig_score is not None
    assert len(fig_score.data) >= 1


def test_sleep_score_calculator_single():
    """Verify physiological scoring for various sleep scenarios."""
    # 1. Optimal 8h sleep with balanced deep/REM and low RHR
    optimal_score = SleepScoreCalculator.calculate_single_score(
        duration_seconds=8.0 * 3600,
        deep_sleep_seconds=1.5 * 3600,  # ~19%
        rem_sleep_seconds=1.8 * 3600,   # ~22.5%
        resting_hr=50.0,
        baseline_rhr=52.0,              # Lower than baseline -> max recovery
    )
    assert optimal_score is not None
    assert 90.0 <= optimal_score <= 100.0

    # 2. Short sleep (4.5h) with elevated RHR
    poor_score = SleepScoreCalculator.calculate_single_score(
        duration_seconds=4.5 * 3600,
        deep_sleep_seconds=0.3 * 3600,
        rem_sleep_seconds=0.5 * 3600,
        resting_hr=64.0,
        baseline_rhr=52.0,              # +12 bpm above baseline -> strain
    )
    assert poor_score is not None
    assert poor_score < 60.0

    # 3. No sleep recorded (0 or None)
    assert SleepScoreCalculator.calculate_single_score(0) is None
    assert SleepScoreCalculator.calculate_single_score(None) is None


def test_sleep_score_calculator_dataframe():
    """Verify batch DataFrame sleep score calculation with rolling baseline."""
    df = pd.DataFrame([
        {
            "date": "2026-05-01",
            "sleep_duration_seconds": 28800.0,
            "deep_sleep_seconds": 5400.0,
            "rem_sleep_seconds": 6400.0,
            "light_sleep_seconds": 17000.0,
            "resting_hr": 52.0,
            "sleep_score": None,
        },
        {
            "date": "2026-05-02",
            "sleep_duration_seconds": 21600.0,
            "deep_sleep_seconds": 2400.0,
            "rem_sleep_seconds": 4000.0,
            "light_sleep_seconds": 15200.0,
            "resting_hr": 56.0,
            "sleep_score": None,
        },
    ])

    result_df = SleepScoreCalculator.calculate_dataframe(df)
    assert "sleep_score" in result_df.columns
    assert result_df["sleep_score"].notna().all()
    assert result_df.loc[0, "sleep_score"] > result_df.loc[1, "sleep_score"]


def test_circadian_timing_calculator():
    """Verify circadian clock conversion, dataframe enrichment, and schedule regularity metrics."""
    from src.analytics.sleep_score import CircadianTimingCalculator

    # 1. Clock time formatting
    assert CircadianTimingCalculator.format_clock_time(23.5, is_bedtime=True) == "11:30 PM"
    assert CircadianTimingCalculator.format_clock_time(24.25, is_bedtime=True) == "12:15 AM"
    assert CircadianTimingCalculator.format_clock_time(7.1, is_bedtime=False) == "7:06 AM"
    assert CircadianTimingCalculator.format_clock_time(None) == "--"

    # 2. Timing DataFrame enrichment
    df = pd.DataFrame([
        {
            "date": "2026-08-01",
            "sleep_duration_seconds": 27000.0,
            "sleep_start": "2026-07-31 23:15:00",
            "sleep_end": "2026-08-01 07:00:00",
        },
        {
            "date": "2026-08-02",
            "sleep_duration_seconds": 28800.0,
            "sleep_start": "2026-08-02 00:30:00",
            "sleep_end": "2026-08-02 08:45:00",
        },
    ])
    timing_df = CircadianTimingCalculator.calculate_timing_dataframe(df)
    assert "bed_decimal" in timing_df.columns
    assert "wake_decimal" in timing_df.columns
    assert "bed_str" in timing_df.columns
    assert "wake_str" in timing_df.columns
    assert "bed_roll_7d" in timing_df.columns
    assert "wake_roll_7d" in timing_df.columns

    # 23:15 is 23.25
    assert abs(timing_df.loc[0, "bed_decimal"] - 23.25) < 0.01
    # 00:30 is 24.5 in continuous nocturnal hours
    assert abs(timing_df.loc[1, "bed_decimal"] - 24.5) < 0.01
    # 07:00 is 7.0
    assert abs(timing_df.loc[0, "wake_decimal"] - 7.0) < 0.01

    # 3. Circadian metrics
    metrics = CircadianTimingCalculator.calculate_circadian_metrics(timing_df)
    assert "avg_bedtime_str" in metrics
    assert "avg_wake_str" in metrics
    assert "midpoint_str" in metrics
    assert "regularity_score" in metrics
    assert metrics["regularity_score"] > 0


def test_sleep_schedule_chart():
    """Verify Plotly sleep schedule & circadian timing chart builds cleanly."""
    from src.ui.charts import plot_sleep_schedule_and_timing_chart

    records = generate_synthetic_health_records(days=14)
    df = pd.DataFrame(records)

    fig = plot_sleep_schedule_and_timing_chart(df, title="Test Sleep Schedule")
    assert fig is not None
    # 4 scatter traces (nightly bedtime, 7d avg bedtime, daily wake, 7d avg wake)
    assert len(fig.data) == 4


def test_database_sleep_times_backfill(tmp_path):
    """Verify DatabaseManager automatically ensures columns and backfills sleep times."""
    import os
    db_path = os.path.join(tmp_path, "test_sleep_backfill.db")
    db = DatabaseManager(db_path=db_path)

    # Insert mock records with missing timestamps
    test_records = [
        {
            "date": "2026-08-10",
            "sleep_duration_seconds": 27000.0,
            "deep_sleep_seconds": 5400.0,
            "light_sleep_seconds": 15000.0,
            "rem_sleep_seconds": 6600.0,
            "sleep_score": 85.0,
            "resting_hr": 50.0,
            "sleep_start": None,
            "sleep_end": None,
        }
    ]
    db.save_daily_health_records(test_records)

    # get_daily_health_df triggers backfill
    df = db.get_daily_health_df()
    assert not df.empty
    assert "sleep_start" in df.columns
    assert "sleep_end" in df.columns
    assert df.loc[0, "sleep_start"] is not None
    assert df.loc[0, "sleep_end"] is not None
