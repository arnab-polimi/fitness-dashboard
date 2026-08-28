"""
Running metrics, Jack Daniels VDOT / VO2max, Efficiency Factor, and Aerobic Decoupling.
"""
import math
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from src.models.activity import Activity
from src.models.user_profile import UserProfile


def format_pace_sec_km(sec_km: Optional[float], unit: str = "metric") -> str:
    """Formats pace seconds/km to 'mm:ss /km' or 'mm:ss /mi'."""
    if sec_km is None or sec_km <= 0 or math.isnan(sec_km) or sec_km > 2400:
        return "--:--"
    if unit == "imperial":
        sec_mi = sec_km * 1.609344
        mins = int(sec_mi // 60)
        secs = int(sec_mi % 60)
        return f"{mins}:{secs:02d} /mi"
    mins = int(sec_km // 60)
    secs = int(sec_km % 60)
    return f"{mins}:{secs:02d} /km"


def calculate_efficiency_factor(speed_m_s: float, avg_hr: Optional[float]) -> Optional[float]:
    """
    Efficiency Factor (EF) = Speed (m/min) / Average Heart Rate (bpm).
    Higher EF means faster speed at the same cardiac cost (improved aerobic fitness).
    """
    if not avg_hr or avg_hr <= 40 or speed_m_s <= 0:
        return None
    speed_m_min = speed_m_s * 60.0
    return round(speed_m_min / avg_hr, 3)


def calculate_vdot_from_race(distance_meters: float, duration_seconds: float) -> Optional[float]:
    """
    Calculates Jack Daniels VDOT / estimated VO2max from a running performance.
    Uses the Daniels & Gilbert oxygen cost equations.
    """
    if distance_meters < 800 or duration_seconds < 120:
        return None

    t_min = duration_seconds / 60.0
    v = distance_meters / t_min  # velocity in meters/min

    # VO2 cost of running at velocity v (ml/kg/min)
    vo2 = -4.60 + 0.182258 * v + 0.000104 * (v ** 2)

    # % VO2max sustained for duration t_min
    pct_vo2max = 0.8 + 0.1894393 * math.exp(-0.0115 * t_min) + 0.2989558 * math.exp(-0.05 * t_min)

    if pct_vo2max <= 0:
        return None

    vdot = vo2 / pct_vo2max
    return round(min(85.0, max(15.0, vdot)), 1)


def velocity_for_pct_vo2max(vdot: float, pct: float) -> float:
    """
    Inverts the Daniels VO2 equation to find velocity (m/min) for a target VO2 = vdot * pct.
    vo2 = -4.60 + 0.182258 * v + 0.000104 * v^2
    0.000104 * v^2 + 0.182258 * v - (4.60 + target_vo2) = 0
    """
    target_vo2 = vdot * pct
    a = 0.000104
    b = 0.182258
    c = -(4.60 + target_vo2)

    disc = b ** 2 - 4 * a * c
    if disc < 0:
        return 0.0
    v = (-b + math.sqrt(disc)) / (2 * a)
    return v


def get_training_paces_from_vdot(vdot: float) -> Dict[str, Dict[str, Any]]:
    """
    Calculates Jack Daniels training pace zones for a given VDOT:
    - Easy (E): 59 - 74% VO2max
    - Marathon (M): 75 - 84% VO2max
    - Threshold (T): 83 - 88% VO2max
    - Interval (I): 95 - 100% VO2max
    - Repetition (R): 105 - 115% VO2max
    """
    zones = {
        "Easy (E-Pace)": {"pct_range": (0.62, 0.72), "purpose": "Aerobic base building, recovery, capillary growth"},
        "Marathon (M-Pace)": {"pct_range": (0.75, 0.84), "purpose": "Aerobic capacity, marathon race pacing, fuel utilization"},
        "Threshold (T-Pace)": {"pct_range": (0.86, 0.88), "purpose": "Lactate threshold endurance, stamina, 1-hour race pace"},
        "Interval (I-Pace)": {"pct_range": (0.95, 1.00), "purpose": "VO2max expansion, cardiovascular stroke volume"},
        "Repetition (R-Pace)": {"pct_range": (1.05, 1.10), "purpose": "Running economy, neuromuscular speed, anaerobic power"},
    }

    result = {}
    for name, data in zones.items():
        p_low, p_high = data["pct_range"]
        v_low = velocity_for_pct_vo2max(vdot, p_low)
        v_high = velocity_for_pct_vo2max(vdot, p_high)

        pace_high_sec = (60000.0 / v_low) if v_low > 0 else 0.0
        pace_low_sec = (60000.0 / v_high) if v_high > 0 else 0.0

        result[name] = {
            "pace_sec_km_range": (pace_low_sec, pace_high_sec),
            "formatted_range_km": f"{format_pace_sec_km(pace_low_sec, 'metric')} - {format_pace_sec_km(pace_high_sec, 'metric')}",
            "formatted_range_mi": f"{format_pace_sec_km(pace_low_sec, 'imperial')} - {format_pace_sec_km(pace_high_sec, 'imperial')}",
            "purpose": data["purpose"],
        }
    return result


def estimate_activity_aerobic_decoupling(activity: Activity) -> Optional[float]:
    """
    Estimates Aerobic Decoupling (% drift in Pace:HR ratio).
    If full lap/split data exists, computes exact split drift.
    Otherwise, models drift based on duration and heart rate spread.
    """
    if not activity.avg_hr or activity.duration_seconds < 1200:
        return None

    raw = activity.raw_data or {}
    if "laps" in raw and len(raw["laps"]) >= 2:
        laps = [l for l in raw["laps"] if (l.get("distance_meters", 0) > 200 or l.get("elapsed_seconds", 0) > 60)]
        if len(laps) >= 2:
            half = len(laps) // 2
            first_half = laps[:half]
            second_half = laps[half:]

            def get_lap_ef(lap_list):
                speeds = [l.get("speed_m_s", 0) for l in lap_list if l.get("speed_m_s", 0) > 0]
                hrs = [l.get("avg_hr", 0) for l in lap_list if l.get("avg_hr", 0) > 0]
                if speeds and hrs:
                    return (np.mean(speeds) * 60.0) / np.mean(hrs)
                return None

            ef1 = get_lap_ef(first_half)
            ef2 = get_lap_ef(second_half)
            if ef1 and ef2 and ef1 > 0:
                drift = ((ef1 - ef2) / ef1) * 100.0
                return round(drift, 1)

    if activity.max_hr and activity.avg_hr:
        hr_spread = (activity.max_hr - activity.avg_hr) / activity.avg_hr
        duration_factor = min(2.5, activity.duration_seconds / 3600.0)
        estimated_drift = max(0.5, hr_spread * 22.0 * (duration_factor ** 0.5))
        return round(min(25.0, estimated_drift), 1)

    return None


class RunningMetricsCalculator:
    """Consolidated runner analytics calculator."""

    @staticmethod
    def calculate_efficiency_factor(act: Activity) -> Optional[float]:
        """Calculates efficiency factor for an activity."""
        if act.speed_m_s > 0 and act.avg_hr:
            return calculate_efficiency_factor(act.speed_m_s, act.avg_hr)
        return None

    @staticmethod
    def enrich_activities(activities: List[Activity], user_profile: UserProfile) -> List[Activity]:
        """Calculates advanced running metrics on each activity."""
        for act in activities:
            # 1. Efficiency Factor
            if act.speed_m_s > 0 and act.avg_hr:
                act.efficiency_factor = calculate_efficiency_factor(act.speed_m_s, act.avg_hr)

            # 2. Aerobic Decoupling
            act.aerobic_decoupling = estimate_activity_aerobic_decoupling(act)

            # 3. VDOT / VO2max estimate from moving time (more accurate than total elapsed time)
            if act.sport_type in ["run", "trail_run", "treadmill_run"] and act.distance_meters >= 3000:
                effective_time = act.moving_time_seconds if (act.moving_time_seconds and act.moving_time_seconds > 0) else act.duration_seconds
                act.vdot = calculate_vdot_from_race(act.distance_meters, effective_time)

        return activities

    @staticmethod
    def get_peak_vdot(activities: List[Activity], recent_days: int = 120) -> float:
        """Finds highest peak VDOT score from verified running performances."""
        if not activities:
            return 30.0

        cutoff = None
        sorted_acts = sorted(activities, key=lambda a: a.start_time, reverse=True)
        if sorted_acts:
            cutoff = sorted_acts[0].start_time.date() - np.timedelta64(recent_days, 'D')

        valid_vdots = []
        for a in activities:
            if a.sport_type in ["run", "trail_run", "treadmill_run"] and "cycling" not in a.title.lower():
                if a.vdot and a.vdot > 15:
                    if cutoff is None or a.start_time.date() >= cutoff:
                        valid_vdots.append(a.vdot)

        if valid_vdots:
            # Use maximum peak verified VDOT
            return round(float(max(valid_vdots)), 1)
        return 30.0
