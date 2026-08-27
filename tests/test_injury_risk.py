"""
Unit tests for transparent Multi-Signal Injury Risk Engine and disclaimer validation.
"""
from datetime import date, timedelta, datetime
import pytest

from src.models.metrics import DailyLoad
from src.models.activity import Activity
from src.analytics.injury_risk import InjuryRiskEngine


def test_injury_risk_balanced_training():
    # 28 days of balanced training with rest days
    daily_loads = []
    base_date = date(2026, 8, 1)
    for i in range(28):
        tss = 50.0 if (i % 3 != 0) else 0.0  # rest every 3rd day
        dl = DailyLoad(
            date=base_date + timedelta(days=i),
            total_tss=tss,
            ctl=45.0,
            atl=42.0,
            tsb=3.0,
            acwr=1.05,  # Sweet spot
            ramp_rate_ctl=2.0,  # Safe
            monotony=1.2,  # Good polarized variance
            strain=200.0,
        )
        daily_loads.append(dl)

    report = InjuryRiskEngine.evaluate(daily_loads, [])
    assert report.composite_score < 40.0
    assert "Optimal" in report.overall_status or "Productive" in report.overall_status
    assert report.acwr_value == 1.05
    assert len(report.signals) == 5
    # Must have explicit disclaimer
    assert "DISCLAIMER" in report.disclaimer
    assert "medical" in report.disclaimer.lower()


def test_injury_risk_spike_detection():
    # High ACWR spike (>1.5) with aggressive ramp rate
    daily_loads = []
    base_date = date(2026, 8, 1)
    for i in range(28):
        dl = DailyLoad(
            date=base_date + timedelta(days=i),
            total_tss=95.0,
            ctl=60.0,
            atl=95.0,
            tsb=-35.0,
            acwr=1.75,  # DANGER ZONE
            ramp_rate_ctl=9.5,  # EXCESSIVE RAMP
            monotony=2.4,  # UNIFORM STRESS
            strain=800.0,
        )
        daily_loads.append(dl)

    report = InjuryRiskEngine.evaluate(daily_loads, [])
    assert report.composite_score >= 65.0
    assert "Caution" in report.overall_status or "High Stress" in report.overall_status or "Overreaching" in report.overall_status
    assert len(report.actionable_guidance) > 0
