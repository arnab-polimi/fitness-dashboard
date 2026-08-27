"""
Race performance predictor for 5K, 10K, Half Marathon, and Marathon.
"""
import math
from typing import List, Optional

from src.models.metrics import RacePrediction
from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.analytics.running_metrics import RunningMetricsCalculator, velocity_for_pct_vo2max


class RacePredictor:
    """Predicts race times from recent peak performances, VDOT, and Chronic Training Load (CTL)."""

    TARGET_DISTANCES = [
        ("5K", 5.0),
        ("10K", 10.0),
        ("Half Marathon", 21.0975),
        ("Marathon", 42.195),
    ]

    @classmethod
    def predict_all(
        cls,
        activities: List[Activity],
        user_profile: UserProfile,
        current_ctl: float = 50.0,
    ) -> List[RacePrediction]:
        """Generates predictions for all standard running race distances."""
        peak_vdot = RunningMetricsCalculator.get_peak_vdot(activities)

        # Baseline predictions from VDOT
        predictions: List[RacePrediction] = []

        # Find best recent anchor run if available (e.g. fastest 5k or 10k)
        anchor_dist = None
        anchor_time = None
        for act in sorted(activities, key=lambda a: a.start_time, reverse=True)[:50]:
            if act.sport_type in ["run", "trail_run", "treadmill_run"] and act.distance_km >= 4.8 and act.duration_seconds > 0:
                pace = act.effective_pace_sec_km
                if pace > 0 and (anchor_time is None or pace < (anchor_time / (anchor_dist or 1))):
                    anchor_dist = act.distance_km
                    anchor_time = act.duration_seconds

        for name, dist_km in cls.TARGET_DISTANCES:
            # 1. VDOT estimate
            vdot_sec = cls._vdot_predict_seconds(peak_vdot, dist_km)

            # 2. Riegel model with CTL endurance adjustment
            if anchor_dist and anchor_time and anchor_dist >= 3.0:
                # Aerobic fatigue exponent: 1.06 base, adjusted by CTL (low CTL = higher fatigue over 21k/42k)
                fatigue_exp = 1.06
                if dist_km >= 21.0:
                    if current_ctl < 40:
                        fatigue_exp = 1.09  # endurance penalty
                    elif current_ctl > 65:
                        fatigue_exp = 1.05  # well-trained endurance base
                riegel_sec = anchor_time * ((dist_km / anchor_dist) ** fatigue_exp)
                # Weighted blend
                final_sec = 0.55 * vdot_sec + 0.45 * riegel_sec
                confidence = "High" if len(activities) >= 15 else "Moderate"
                basis = f"VDOT ({peak_vdot:.1f}) + Anchor {anchor_dist:.1f}km + CTL ({current_ctl:.0f})"
            else:
                final_sec = vdot_sec
                confidence = "Moderate" if len(activities) >= 5 else "Preliminary"
                basis = f"VDOT Formula ({peak_vdot:.1f})"

            pace_sec_km = final_sec / dist_km

            predictions.append(
                RacePrediction(
                    distance_name=name,
                    distance_km=dist_km,
                    predicted_time_seconds=round(final_sec, 1),
                    predicted_pace_sec_km=round(pace_sec_km, 1),
                    confidence_level=confidence,
                    basis=basis,
                )
            )

        return predictions

    @classmethod
    def _vdot_predict_seconds(cls, vdot: float, dist_km: float) -> float:
        """
        Solves for race time using Daniels & Gilbert equations for target distance.
        Uses iterative bisection to match distance = velocity * time.
        """
        dist_m = dist_km * 1000.0

        # Approximate initial time in minutes
        t_low = (dist_km * 2.5)  # world record pace bound
        t_high = (dist_km * 10.0)  # slow jog bound

        for _ in range(30):
            t_mid = (t_low + t_high) / 2.0
            v_mid = dist_m / t_mid

            vo2 = -4.60 + 0.182258 * v_mid + 0.000104 * (v_mid ** 2)
            pct = 0.8 + 0.1894393 * math.exp(-0.0115 * t_mid) + 0.2989558 * math.exp(-0.05 * t_mid)

            calculated_vdot = vo2 / pct
            if calculated_vdot < vdot:
                # Too slow (calculated vdot lower than target) -> reduce time
                t_high = t_mid
            else:
                t_low = t_mid

        return ((t_low + t_high) / 2.0) * 60.0
