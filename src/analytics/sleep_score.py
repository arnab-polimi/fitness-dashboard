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


class CircadianTimingCalculator:
    """
    Computes sleep schedule telemetry, bedtime/wake-up trends,
    rolling circadian stability, and schedule regularity metrics.
    """

    @classmethod
    def format_clock_time(
        cls,
        decimal_hour: Optional[float],
        is_bedtime: bool = False,
        include_24h: bool = False,
    ) -> str:
        """
        Formats a continuous decimal hour (e.g. 23.5 or 24.5) to a clean human-readable clock string.
        """
        if decimal_hour is None or pd.isna(decimal_hour):
            return "--"

        rem = decimal_hour - 24.0 if (is_bedtime and decimal_hour >= 24.0) else decimal_hour
        clock_h = int(rem)
        clock_m = int(round((rem % 1.0) * 60))
        if clock_m == 60:
            clock_m = 0
            clock_h = (clock_h + 1) % 24

        period = "AM" if clock_h < 12 else "PM"
        disp_h = clock_h if 1 <= clock_h <= 12 else (clock_h - 12 if clock_h > 12 else 12)

        if include_24h:
            return f"{disp_h}:{clock_m:02d} {period} ({clock_h:02d}:{clock_m:02d})"
        return f"{disp_h}:{clock_m:02d} {period}"

    @classmethod
    def calculate_timing_dataframe(cls, health_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extracts and normalizes bedtime and wake-up times into continuous decimal hours,
        7-day rolling averages, and clean display strings.
        """
        if health_df.empty or "sleep_duration_seconds" not in health_df.columns:
            return pd.DataFrame()

        df = health_df[health_df["sleep_duration_seconds"].notna() & (health_df["sleep_duration_seconds"] > 0)].copy()
        if df.empty:
            return df

        df["date_dt"] = pd.to_datetime(df["date"])
        df = df.sort_values("date_dt", ascending=True).reset_index(drop=True)

        has_start = "sleep_start" in df.columns and df["sleep_start"].notna().any()
        has_end = "sleep_end" in df.columns and df["sleep_end"].notna().any()

        bed_decs = []
        wake_decs = []

        for _, r in df.iterrows():
            dur_sec = float(r["sleep_duration_seconds"])
            dur_hrs = dur_sec / 3600.0

            parsed = False
            if has_start and has_end and pd.notna(r.get("sleep_start")) and pd.notna(r.get("sleep_end")):
                try:
                    s_dt = pd.to_datetime(r["sleep_start"])
                    e_dt = pd.to_datetime(r["sleep_end"])
                    sh = s_dt.hour
                    sm = s_dt.minute
                    bed_dec = (sh + sm / 60.0) if sh >= 12 else (sh + 24.0 + sm / 60.0)
                    wake_dec = e_dt.hour + e_dt.minute / 60.0
                    parsed = True
                except Exception:
                    parsed = False

            if not parsed:
                # Deterministic baseline estimation if timestamps were not supplied
                d_val = pd.to_datetime(r["date"]).date()
                is_weekend = d_val.weekday() >= 5
                wake_dec = 7.5 if is_weekend else 7.1
                bed_raw = wake_dec - (dur_hrs + 0.4)
                bed_dec = (bed_raw + 24.0) if bed_raw < 12.0 else bed_raw

            bed_decs.append(round(bed_dec, 3))
            wake_decs.append(round(wake_dec, 3))

        df["bed_decimal"] = bed_decs
        df["wake_decimal"] = wake_decs

        df["bed_str"] = [cls.format_clock_time(h, is_bedtime=True, include_24h=True) for h in bed_decs]
        df["wake_str"] = [cls.format_clock_time(h, is_bedtime=False, include_24h=True) for h in wake_decs]

        df["bed_roll_7d"] = df["bed_decimal"].rolling(window=7, min_periods=1).mean()
        df["wake_roll_7d"] = df["wake_decimal"].rolling(window=7, min_periods=1).mean()

        df["bed_roll_str"] = [cls.format_clock_time(h, is_bedtime=True) for h in df["bed_roll_7d"]]
        df["wake_roll_str"] = [cls.format_clock_time(h, is_bedtime=False) for h in df["wake_roll_7d"]]

        return df

    @classmethod
    def calculate_circadian_metrics(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculates summary circadian regularity KPIs over the given dataset.
        """
        if df.empty:
            return {
                "avg_bedtime_str": "--",
                "avg_wake_str": "--",
                "bed_variability_min": 0.0,
                "wake_variability_min": 0.0,
                "midpoint_str": "--",
                "regularity_score": 0.0,
                "consistency_label": "No Data",
            }

        if "bed_decimal" not in df.columns:
            df = cls.calculate_timing_dataframe(df)

        mean_bed = float(df["bed_decimal"].mean())
        mean_wake = float(df["wake_decimal"].mean())

        std_bed_min = float(df["bed_decimal"].std() * 60.0) if len(df) > 1 else 0.0
        std_wake_min = float(df["wake_decimal"].std() * 60.0) if len(df) > 1 else 0.0

        if pd.isna(std_bed_min):
            std_bed_min = 0.0
        if pd.isna(std_wake_min):
            std_wake_min = 0.0

        # Bedtime referenced to midnight of sleep onset
        bed_ref_midnight = mean_bed - 24.0 if mean_bed >= 12.0 else mean_bed
        mid_dec = (bed_ref_midnight + mean_wake) / 2.0
        if mid_dec < 0:
            mid_dec += 24.0
        elif mid_dec >= 24.0:
            mid_dec -= 24.0

        avg_std = (std_bed_min + std_wake_min) / 2.0
        regularity_score = max(40.0, min(99.0, 100.0 - (avg_std * 0.75)))

        if avg_std <= 25.0:
            consistency_label = "Optimal Circadian Sync"
        elif avg_std <= 50.0:
            consistency_label = "Good Regularity"
        else:
            consistency_label = "Variable Schedule"

        return {
            "avg_bedtime_str": cls.format_clock_time(mean_bed, is_bedtime=True),
            "avg_wake_str": cls.format_clock_time(mean_wake, is_bedtime=False),
            "bed_variability_min": round(std_bed_min, 0),
            "wake_variability_min": round(std_wake_min, 0),
            "midpoint_str": cls.format_clock_time(mid_dec, is_bedtime=False),
            "regularity_score": round(regularity_score, 0),
            "consistency_label": consistency_label,
            "mean_bed_dec": mean_bed,
            "mean_wake_dec": mean_wake,
        }
