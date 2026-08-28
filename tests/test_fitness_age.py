"""
Unit tests for Fitness Age Engine and Physiological Pattern Recognizer.
"""
import pytest
import pandas as pd
from datetime import date, timedelta

from src.models.user_profile import UserProfile
from src.analytics.fitness_age import FitnessAgeEngine, FitnessAgeReport


def test_fitness_age_calculation():
    profile = UserProfile(age=30, resting_hr=48, gender="male")
    
    # Mock daily dataframe with CTL
    daily_data = {
        "date": [date.today() - timedelta(days=i) for i in range(30)],
        "ctl": [45.0 for _ in range(30)],
    }
    daily_df = pd.DataFrame(daily_data)

    # Mock health dataframe with resting HR and sleep score
    health_data = {
        "date": [date.today() - timedelta(days=i) for i in range(30)],
        "resting_hr": [48.0 for _ in range(30)],
        "sleep_score": [85.0 for _ in range(30)],
    }
    health_df = pd.DataFrame(health_data)

    report = FitnessAgeEngine.calculate_fitness_age(
        user_profile=profile,
        daily_df=daily_df,
        health_df=health_df,
        recent_vdot=52.0
    )

    assert isinstance(report, FitnessAgeReport)
    assert report.chronological_age == 30
    assert report.fitness_age < 30.0  # Should be younger due to low RHR, high CTL & VDOT
    assert report.age_delta < 0
    assert report.fitness_score > 75.0
    assert len(report.detected_patterns) > 0


def test_pattern_recognizer_trends():
    profile = UserProfile(age=35, resting_hr=50, gender="male")
    
    # Mock RHR dropping trend (first 7 days 54, last 7 days 50)
    rhr_list = [54.0]*7 + [50.0]*7
    health_df = pd.DataFrame({
        "date": [date.today() - timedelta(days=i) for i in range(14)],
        "resting_hr": list(reversed(rhr_list)),
        "sleep_score": [85.0]*14
    })

    patterns = FitnessAgeEngine.detect_patterns(profile, health_df=health_df)
    assert any("Cardiovascular Adaptation" in p["title"] for p in patterns)
