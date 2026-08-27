"""
Training Load, TRIMP, TSS, and EWMA Fitness/Fatigue (CTL/ATL/TSB) calculations.
"""
import math
from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.models.metrics import DailyLoad


def calculate_banister_trimp(
    duration_seconds: float,
    avg_hr: Optional[float],
    user_profile: UserProfile,
) -> float:
    """
    Calculates Banister's TRIMP (Training Impulse).
    TRIMP = duration_min * delta_hr * 0.64 * exp(1.92 * delta_hr) [male]
    delta_hr = (avg_hr - resting_hr) / (max_hr - resting_hr)
    """
    if not avg_hr or avg_hr <= user_profile.resting_hr or duration_seconds <= 0:
        return 0.0

    duration_min = duration_seconds / 60.0
    hrr = max(1.0, float(user_profile.max_hr - user_profile.resting_hr))
    delta_hr = min(1.0, max(0.0, (avg_hr - user_profile.resting_hr) / hrr))

    # Gender coefficient
    b = 1.92 if user_profile.gender.lower() == "male" else 1.86
    y = 0.64 if user_profile.gender.lower() == "male" else 0.86

    trimp = duration_min * delta_hr * y * math.exp(b * delta_hr)
    return round(trimp, 2)


def calculate_rtss(
    duration_seconds: float,
    avg_pace_sec_km: Optional[float],
    threshold_pace_sec_km: float,
) -> float:
    """
    Calculates Running Training Stress Score (rTSS).
    rTSS = (t * IF^2 / 3600) * 100
    where IF = Threshold_Pace / Avg_Pace (or Avg_Speed / Threshold_Speed)
    """
    if not avg_pace_sec_km or avg_pace_sec_km <= 0 or duration_seconds <= 0 or threshold_pace_sec_km <= 0:
        return 0.0

    # Intensity factor
    intensity_factor = threshold_pace_sec_km / avg_pace_sec_km
    # Cap intensity factor at reasonable physiological limit (e.g., 1.5 for sprints)
    intensity_factor = min(1.6, max(0.3, intensity_factor))

    rtss = (duration_seconds * (intensity_factor ** 2) / 3600.0) * 100.0
    return round(rtss, 2)


def calculate_hrtss(
    duration_seconds: float,
    avg_hr: Optional[float],
    lthr: int,
) -> float:
    """
    Calculates Heart Rate Training Stress Score (hrTSS) as fallback.
    hrTSS = (t * (avg_hr / LTHR)^2 / 3600) * 100
    """
    if not avg_hr or avg_hr <= 0 or duration_seconds <= 0 or lthr <= 0:
        return 0.0

    hr_factor = avg_hr / float(lthr)
    hr_factor = min(1.4, max(0.4, hr_factor))
    hrtss = (duration_seconds * (hr_factor ** 2) / 3600.0) * 100.0
    return round(hrtss, 2)


def compute_activity_load(activity: Activity, user_profile: UserProfile) -> Activity:
    """Calculates TRIMP, TSS, and Intensity Factor for an individual activity."""
    # 1. TRIMP
    activity.trimp = calculate_banister_trimp(
        activity.duration_seconds,
        activity.avg_hr,
        user_profile,
    )

    # 2. TSS
    effective_pace = activity.effective_pace_sec_km
    if effective_pace > 0 and user_profile.threshold_pace_sec_km > 0 and activity.sport_type in ["run", "trail_run", "treadmill_run"]:
        activity.tss = calculate_rtss(
            activity.duration_seconds,
            effective_pace,
            user_profile.threshold_pace_sec_km,
        )
        activity.intensity_factor = round(user_profile.threshold_pace_sec_km / effective_pace, 3)
    elif activity.avg_hr and user_profile.lthr > 0:
        activity.tss = calculate_hrtss(
            activity.duration_seconds,
            activity.avg_hr,
            user_profile.lthr,
        )
        activity.intensity_factor = round(activity.avg_hr / float(user_profile.lthr), 3)
    else:
        # Fallback estimation based on duration (~50 TSS / hr)
        activity.tss = round((activity.duration_seconds / 3600.0) * 50.0, 2)
        activity.intensity_factor = 0.70

    # 3. Running Efficiency Factor: Speed (m/min) / HR
    if activity.avg_hr and activity.avg_hr > 0 and activity.speed_m_s > 0:
        speed_m_min = activity.speed_m_s * 60.0
        activity.efficiency_factor = round(speed_m_min / activity.avg_hr, 3)

    return activity


class TrainingLoadEngine:
    """Calculates continuous daily training load, CTL (Fitness), ATL (Fatigue), TSB (Form), and ACWR."""

    # Time constants (days)
    CTL_TAU = 42.0  # Fitness time constant
    ATL_TAU = 7.0   # Fatigue time constant

    @classmethod
    def calculate_daily_metrics(
        cls,
        activities: List[Activity],
        user_profile: UserProfile,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[DailyLoad]:
        """
        Builds a continuous day-by-day sequence of training load and EWMA metrics.
        """
        if not activities:
            return []

        # Ensure activities have calculated load
        enriched_acts = [compute_activity_load(act, user_profile) for act in activities]

        # Determine date span
        sorted_acts = sorted(enriched_acts, key=lambda a: a.start_time)
        first_act_date = sorted_acts[0].start_time.date()
        last_act_date = sorted_acts[-1].start_time.date()

        actual_start = start_date or (first_act_date - timedelta(days=1))
        actual_end = end_date or max(last_act_date, date.today())

        # Map activities by date
        acts_by_date: Dict[date, List[Activity]] = {}
        for act in sorted_acts:
            d = act.start_time.date()
            if d not in acts_by_date:
                acts_by_date[d] = []
            acts_by_date[d].append(act)

        # Decay constants
        k_ctl = 1.0 - math.exp(-1.0 / cls.CTL_TAU)
        k_atl = 1.0 - math.exp(-1.0 / cls.ATL_TAU)

        ctl = 0.0
        atl = 0.0

        daily_loads: List[DailyLoad] = []
        recent_daily_tss: List[float] = []

        curr_date = actual_start
        while curr_date <= actual_end:
            day_acts = acts_by_date.get(curr_date, [])
            day_dist = sum(a.distance_meters for a in day_acts)
            day_dur = sum(a.duration_seconds for a in day_acts)
            day_tss = sum(a.tss or 0.0 for a in day_acts)
            day_trimp = sum(a.trimp or 0.0 for a in day_acts)
            efs = [a.efficiency_factor for a in day_acts if a.efficiency_factor is not None]
            day_ef = sum(efs) / len(efs) if efs else None

            # Update EWMA
            ctl = ctl + (day_tss - ctl) * k_ctl
            atl = atl + (day_tss - atl) * k_atl
            tsb = ctl - atl

            recent_daily_tss.append(day_tss)

            # Rolling 7-day and 28-day metrics for ACWR and Monotony
            acwr = None
            ramp_rate = None
            monotony = None
            strain = None

            if len(recent_daily_tss) >= 7:
                last_7 = recent_daily_tss[-7:]
                mean_7 = float(np.mean(last_7))
                std_7 = float(np.std(last_7))
                sum_7 = float(np.sum(last_7))

                # Foster's Monotony & Strain
                if std_7 > 0:
                    monotony = round(mean_7 / std_7, 2)
                    strain = round(sum_7 * monotony, 1)
                else:
                    monotony = 1.0
                    strain = round(sum_7, 1)

            if len(recent_daily_tss) >= 28:
                last_7_sum = sum(recent_daily_tss[-7:])
                last_28_sum = sum(recent_daily_tss[-28:])
                avg_weekly_28 = last_28_sum / 4.0 if last_28_sum > 0 else 1.0
                acwr = round(last_7_sum / avg_weekly_28, 2) if avg_weekly_28 > 0 else 1.0

            # 7-day Ramp Rate in CTL
            if len(daily_loads) >= 7:
                ramp_rate = round(ctl - daily_loads[-7].ctl, 2)

            daily_load = DailyLoad(
                date=curr_date,
                distance_meters=round(day_dist, 1),
                duration_seconds=round(day_dur, 1),
                activity_count=len(day_acts),
                total_tss=round(day_tss, 2),
                total_trimp=round(day_trimp, 2),
                ctl=round(ctl, 2),
                atl=round(atl, 2),
                tsb=round(tsb, 2),
                acwr=acwr,
                ramp_rate_ctl=ramp_rate,
                monotony=monotony,
                strain=strain,
                efficiency_factor=round(day_ef, 3) if day_ef else None,
            )
            daily_loads.append(daily_load)
            curr_date += timedelta(days=1)

        return daily_loads
