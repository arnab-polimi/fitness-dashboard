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
