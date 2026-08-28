"""
Sleep Score Calculation Engine based on Resting Heart Rate (RHR) and Sleep Architecture.
Calibrated to physiological recovery standards (Firstbeat / Garmin / Oura / NSF models).
"""
from typing import Dict, List, Optional, Any
from datetime import date, datetime
import pandas as pd
import numpy as np


class SleepScoreCalculator:
    """
    Calculates 0-100 Sleep Quality and Recovery Scores using:
    1. Duration Score (0 - 45 pts): Target 7.5 - 8.5 hours
    2. Sleep Architecture / Stage Score (0 - 30 pts): Deep sleep (15 pts) + REM sleep (15 pts)
    3. Cardiovascular RHR Recovery Score (0 - 25 pts): Nightly RHR vs rolling baseline
    """

    @classmethod
    def calculate_single_score(
        cls,
        duration_seconds: Optional[float],
        deep_sleep_seconds: Optional[float] = None,
        rem_sleep_seconds: Optional[float] = None,
        light_sleep_seconds: Optional[float] = None,
        resting_hr: Optional[float] = None,
        baseline_rhr: Optional[float] = None,
        stress_avg: Optional[float] = None,
    ) -> Optional[float]:
        """
        Calculates the sleep score (0-100) for a single night of sleep.
        Returns None if duration_seconds is None or <= 0 (no sleep recorded).
        """
        if duration_seconds is None or duration_seconds <= 0:
            return None

        dur_hrs = duration_seconds / 3600.0

        # 1. Duration Score (0 - 45 points)
        if dur_hrs < 4.0:
            dur_score = (dur_hrs / 4.0) * 15.0
        elif dur_hrs < 7.0:
            dur_score = 15.0 + ((dur_hrs - 4.0) / 3.0) * 25.0
        elif dur_hrs <= 8.5:
            dur_score = 40.0 + ((dur_hrs - 7.0) / 1.5) * 5.0
        elif dur_hrs <= 10.0:
            dur_score = 45.0 - ((dur_hrs - 8.5) / 1.5) * 3.0
        else:
            dur_score = 40.0

        # 2. Stage Quality / Architecture Score (0 - 30 points)
        deep_sec = deep_sleep_seconds or 0.0
        rem_sec = rem_sleep_seconds or 0.0

        if (deep_sec + rem_sec) > 0:
            deep_pct = deep_sec / duration_seconds
            rem_pct = rem_sec / duration_seconds

            # Deep sleep (physical restoration, HGH release) - target 15-25%
            if deep_pct >= 0.15:
                deep_score = 15.0
            elif deep_pct >= 0.10:
                deep_score = 10.0 + ((deep_pct - 0.10) / 0.05) * 5.0
            elif deep_pct >= 0.05:
                deep_score = 5.0 + ((deep_pct - 0.05) / 0.05) * 5.0
            else:
                deep_score = (deep_pct / 0.05) * 5.0

            # REM sleep (cognitive recovery, CNS rejuvenation) - target 20-25%
            if rem_pct >= 0.20:
                rem_score = 15.0
            elif rem_pct >= 0.15:
                rem_score = 10.0 + ((rem_pct - 0.15) / 0.05) * 5.0
            elif rem_pct >= 0.08:
                rem_score = 5.0 + ((rem_pct - 0.08) / 0.07) * 5.0
            else:
                rem_score = (rem_pct / 0.08) * 5.0

            stage_score = deep_score + rem_score
        else:
            # Fallback if stage breakdowns are not recorded
            stage_score = min(30.0, (dur_hrs / 8.0) * 24.0)

        # 3. Cardiovascular Recovery / RHR Score (0 - 25 points)
        if resting_hr is not None and resting_hr > 0:
            eff_baseline = baseline_rhr if (baseline_rhr is not None and baseline_rhr > 0) else resting_hr
            delta_rhr = resting_hr - eff_baseline

            if delta_rhr <= 0:
                rhr_score = 25.0
            else:
                rhr_score = max(0.0, 25.0 - (2.0 * delta_rhr))
        else:
            rhr_score = 20.0

        # Optional stress modifier if available
        stress_deduction = 0.0
        if stress_avg is not None and stress_avg > 35:
            stress_deduction = min(5.0, (stress_avg - 35) * 0.2)

        total_score = dur_score + stage_score + rhr_score - stress_deduction
        return round(float(min(100.0, max(0.0, total_score))), 1)

    @classmethod
    def calculate_dataframe(
        cls,
        health_df: pd.DataFrame,
        overwrite_existing: bool = False,
    ) -> pd.DataFrame:
        """
        Calculates and fills sleep_score for all rows in a DataFrame.
        """
        if health_df.empty or "sleep_duration_seconds" not in health_df.columns:
            return health_df

        df = health_df.copy()

        # Ensure date sorting for rolling baseline
        if "date" in df.columns:
            df["_temp_date"] = pd.to_datetime(df["date"])
            df = df.sort_values("_temp_date", ascending=True)

        # Calculate 14-day rolling baseline RHR
        if "resting_hr" in df.columns and df["resting_hr"].notna().any():
            median_rhr = df["resting_hr"].median()
            df["_baseline_rhr"] = df["resting_hr"].rolling(window=14, min_periods=3).median()
            df["_baseline_rhr"] = df["_baseline_rhr"].bfill().fillna(median_rhr)
        else:
            df["_baseline_rhr"] = None

        scores = []
        for _, row in df.iterrows():
            curr_score = row.get("sleep_score")
            if pd.notna(curr_score) and curr_score > 0 and not overwrite_existing:
                scores.append(float(curr_score))
                continue

            dur = row.get("sleep_duration_seconds")
            deep = row.get("deep_sleep_seconds")
            rem = row.get("rem_sleep_seconds")
            light = row.get("light_sleep_seconds")
            rhr = row.get("resting_hr")
            base_rhr = row.get("_baseline_rhr")
            stress = row.get("stress_avg")

            calc = cls.calculate_single_score(
                duration_seconds=dur,
                deep_sleep_seconds=deep,
                rem_sleep_seconds=rem,
                light_sleep_seconds=light,
                resting_hr=rhr,
                baseline_rhr=base_rhr,
                stress_avg=stress,
            )
            scores.append(calc)

        df["sleep_score"] = scores
        if "_temp_date" in df.columns:
            df = df.drop(columns=["_temp_date"])
        if "_baseline_rhr" in df.columns:
            df = df.drop(columns=["_baseline_rhr"])

        return df

    @classmethod
    def calculate_records(
        cls,
        records: List[Dict[str, Any]],
        overwrite_existing: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Calculates and updates sleep_score across a list of health record dictionaries.
        """
        if not records:
            return records

        df = pd.DataFrame(records)
        updated_df = cls.calculate_dataframe(df, overwrite_existing=overwrite_existing)
        return updated_df.to_dict(orient="records")
