"""
Physiological Pattern Recognizer & Fitness Age Engine.
Multi-signal pattern recognition across RHR, CTL/Fatigue, Sleep Architecture, and VDOT to compute Fitness Age and detect physiological trends.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from src.models.user_profile import UserProfile


@dataclass
class FitnessAgeReport:
    """Report detailing Fitness Age calculation and physiological breakdown."""
    chronological_age: int
    fitness_age: float
    age_delta: float  # Negative means younger than calendar age
    fitness_score: float  # 0 to 100 overall score
    category: str  # e.g., 'Elite Athlete Level', 'Superior Conditioning', 'Optimal'
    rhr_impact_years: float
    ctl_impact_years: float
    vdot_impact_years: float
    sleep_impact_years: float
    rhr_status_color: str  # Moss green (#c1d37f) if <= 7d avg, Fatigue red (#f87171) if > 7d avg
    detected_patterns: List[Dict[str, str]]


class FitnessAgeEngine:
    """Calculates Fitness Age and performs multi-signal physiological pattern recognition."""

    @classmethod
    def calculate_fitness_age(
        cls,
        user_profile: UserProfile,
        daily_df: Optional[pd.DataFrame] = None,
        health_df: Optional[pd.DataFrame] = None,
        recent_vdot: Optional[float] = None
    ) -> FitnessAgeReport:
        """
        Computes fitness age using RHR, CTL, VDOT, and sleep architecture telemetry.
        """
        chrono_age = user_profile.age or 30
        
        # 1. RHR Analysis
        # Population average RHR by age/gender
        pop_avg_rhr = 68.0 if user_profile.gender == "female" else 65.0
        
        recent_rhr = user_profile.resting_hr
        rhr_status_color = "#c1d37f"  # Moss Green (within limits of 7d avg or below)

        if health_df is not None and not health_df.empty and "resting_hr" in health_df.columns:
            valid_rhr = health_df["resting_hr"].dropna()
            if not valid_rhr.empty:
                recent_rhr = float(valid_rhr.tail(14).mean())
                if len(valid_rhr) >= 2:
                    latest_rhr = float(valid_rhr.iloc[-1])
                    avg_7d_rhr = float(valid_rhr.tail(7).mean())
                    if latest_rhr > avg_7d_rhr:
                        rhr_status_color = "#f87171"  # Fatigue Red (elevated above 7d average)
                    else:
                        rhr_status_color = "#c1d37f"  # Moss Green (within/below 7d average)

        # RHR Impact: ~0.55 years per 1 bpm lower than population average (max offset ±7 years)
        rhr_diff = pop_avg_rhr - recent_rhr
        rhr_impact = max(-8.0, min(8.0, rhr_diff * -0.45))


        # 2. Training Volume & Fitness (CTL) Impact
        recent_ctl = 25.0
        if daily_df is not None and not daily_df.empty and "ctl" in daily_df.columns:
            recent_ctl = float(daily_df["ctl"].iloc[-1])

        # CTL Impact: Higher CTL reduces fitness age (-0.08 years per CTL point up to -6.5 years)
        ctl_impact = max(-7.0, min(2.0, (30.0 - recent_ctl) * 0.10))

        # 3. Aerobic Capacity (VDOT / VO2max) Impact
        vdot = recent_vdot or 45.0
        # Reference VDOT for age 30 is ~42.0 for males, ~38.0 for females
        ref_vdot = 42.0 if user_profile.gender == "male" else 37.0
        vdot_diff = vdot - ref_vdot
        vdot_impact = max(-6.0, min(6.0, vdot_diff * -0.35))

        # 4. Sleep & Circadian Recovery Impact
        avg_sleep_score = 75.0
        if health_df is not None and not health_df.empty and "sleep_score" in health_df.columns:
            valid_sleep = health_df["sleep_score"].dropna()
            if not valid_sleep.empty:
                avg_sleep_score = float(valid_sleep.tail(14).mean())

        # Sleep Impact: High sleep score reduces age (-0.08 years per point above 75)
        sleep_impact = max(-3.0, min(3.0, (75.0 - avg_sleep_score) * 0.08))

        # Total Fitness Age calculation
        raw_fitness_age = chrono_age + rhr_impact + ctl_impact + vdot_impact + sleep_impact
        # Ensure realistic lower boundary (minimum 18)
        fitness_age = max(18.0, round(raw_fitness_age, 1))
        age_delta = round(fitness_age - chrono_age, 1)

        # Overall Fitness Score (0-100)
        # 100 = 10+ years younger than chronological age
        base_score = 75.0 - (age_delta * 2.5)
        fitness_score = max(10.0, min(99.0, round(base_score, 1)))

        # Categorization
        if age_delta <= -7.0:
            category = "Elite Physiological Age"
        elif age_delta <= -3.0:
            category = "Superior Fitness Level"
        elif age_delta <= 1.0:
            category = "Optimal Conditioning"
        elif age_delta <= 5.0:
            category = "Mild Conditioning Lag"
        else:
            category = "Sub-Optimal Conditioning"


        # Detect Physiological Patterns
        patterns = cls.detect_patterns(user_profile, daily_df, health_df)

        return FitnessAgeReport(
            chronological_age=chrono_age,
            fitness_age=fitness_age,
            age_delta=age_delta,
            fitness_score=fitness_score,
            category=category,
            rhr_impact_years=round(rhr_impact, 1),
            ctl_impact_years=round(ctl_impact, 1),
            vdot_impact_years=round(vdot_impact, 1),
            sleep_impact_years=round(sleep_impact, 1),
            rhr_status_color=rhr_status_color,
            detected_patterns=patterns
        )


    @classmethod
    def detect_patterns(
        cls,
        user_profile: UserProfile,
        daily_df: Optional[pd.DataFrame] = None,
        health_df: Optional[pd.DataFrame] = None
    ) -> List[Dict[str, str]]:
        """
        Scans multi-signal telemetry to spot physiological patterns in RHR, CTL, and Sleep.
        """
        patterns = []

        # 1. RHR Downward Trend (Cardiovascular Stroke Volume Expansion)
        if health_df is not None and not health_df.empty and "resting_hr" in health_df.columns:
            h_df = health_df.sort_values("date") if "date" in health_df.columns else health_df
            rhr_series = h_df["resting_hr"].dropna()
            if len(rhr_series) >= 14:
                first_7d = rhr_series.iloc[-14:-7].mean()
                last_7d = rhr_series.iloc[-7:].mean()
                if first_7d - last_7d >= 1.5:
                    patterns.append({
                        "type": "positive",
                        "title": "💓 Cardiovascular Adaptation (Dropping RHR)",
                        "summary": f"Your 7-day average RHR dropped by {first_7d - last_7d:.1f} bpm ({first_7d:.1f} ➔ {last_7d:.1f} bpm). This indicates expanding cardiac stroke volume and stronger parasympathetic tone."
                    })
                elif last_7d - first_7d >= 2.0:
                    patterns.append({
                        "type": "warning",
                        "title": "⚡ Sympathetic Stress Elevation (Rising RHR)",
                        "summary": f"Your 7-day resting HR increased by {last_7d - first_7d:.1f} bpm. Monitor for non-functional fatigue, overtraining, or early immune response."
                    })


        # 2. Autonomic Recovery Synergy (High CTL + Stable/Low RHR)
        if daily_df is not None and not daily_df.empty and health_df is not None and not health_df.empty:
            if "ctl" in daily_df.columns and "resting_hr" in health_df.columns:
                latest_ctl = daily_df["ctl"].iloc[-1]
                latest_rhr = health_df["resting_hr"].iloc[-1] if not health_df["resting_hr"].dropna().empty else user_profile.resting_hr
                if latest_ctl >= 35.0 and latest_rhr <= user_profile.resting_hr + 2:
                    patterns.append({
                        "type": "positive",
                        "title": "🔥 High Load Absorption Capacity",
                        "summary": f"Your Fitness (CTL) is strong at {latest_ctl:.1f} while Resting HR remains suppressed at {latest_rhr:.0f} bpm. Your body is absorbing training load efficiently without autonomic exhaustion."
                    })

        # 3. Circadian Sleep Recovery Pattern
        if health_df is not None and not health_df.empty and "sleep_score" in health_df.columns:
            sleep_series = health_df["sleep_score"].dropna()
            if len(sleep_series) >= 7:
                avg_sleep = sleep_series.tail(7).mean()
                if avg_sleep >= 82.0:
                    patterns.append({
                        "type": "positive",
                        "title": "💤 Deep Sleep & Anabolic Recovery Window",
                        "summary": f"Your 7-day sleep score averages {avg_sleep:.0f}/100. Consistent high-quality sleep accelerates cellular repair and endocrine balance."
                    })
                elif avg_sleep < 68.0:
                    patterns.append({
                        "type": "warning",
                        "title": "⚠️ Circadian Debt Accumulation",
                        "summary": f"Your 7-day sleep score average is low ({avg_sleep:.0f}/100). Sleep debt impairs muscle glycogen resynthesis and increases injury risk."
                    })

        # Fallback if no specific trend triggered
        if not patterns:
            patterns.append({
                "type": "info",
                "title": "📈 Steady State Homeostasis",
                "summary": "Physiological telemetry indicates steady physiological homeostasis. Continue consistent aerobic training and recovery protocols."
            })

        return patterns
