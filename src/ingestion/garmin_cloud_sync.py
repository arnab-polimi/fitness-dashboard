"""
Automated Garmin Connect Cloud Synchronizer.
Runs in GitHub Actions (or standalone CLI) to fetch latest activities,
sleep telemetry, and daily metrics directly from Garmin Connect API without local PC.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

try:
    from garminconnect import (
        Garmin,
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    )
except ImportError:
    Garmin = None

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.db.database import DatabaseManager
from src.analytics.training_load import compute_activity_load, TrainingLoadEngine
from src.analytics.running_metrics import RunningMetricsCalculator
from src.analytics.sleep_score import SleepScoreCalculator
from src.ingestion.garmin_parser import normalize_sport_type


class GarminCloudSync:
    """Authenticates and fetches telemetry from Garmin Connect Cloud."""

    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        self.email = email or os.environ.get("GARMIN_EMAIL")
        self.password = password or os.environ.get("GARMIN_PASSWORD")
        if not self.email or not self.password:
            raise ValueError("GARMIN_EMAIL and GARMIN_PASSWORD environment variables are required.")
        self.client: Optional[Garmin] = None

    def login(self) -> bool:
        """Authenticates with Garmin Connect."""
        if not Garmin:
            print("Error: garminconnect package is not installed.")
            return False
        try:
            print(f"Connecting to Garmin Connect as {self.email}...")
            self.client = Garmin(self.email, self.password)
            self.client.login()
            print("Successfully authenticated with Garmin Connect!")
            return True
        except GarminConnectAuthenticationError:
            print("Authentication failed: Check your GARMIN_EMAIL and GARMIN_PASSWORD.")
            return False
        except (GarminConnectConnectionError, GarminConnectTooManyRequestsError) as e:
            print(f"Connection/rate limit error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected login error: {e}")
            return False

    def sync(self, days_back: int = 14, db_path: Optional[str] = None) -> Dict[str, int]:
        """Fetches recent activities and health data and updates SQLite database."""
        if not self.client:
            if not self.login():
                return {"activities": 0, "health_days": 0}

        db = DatabaseManager(db_path)
        user_profile = db.get_user_profile()

        # 1. Fetch & Parse Recent Activities
        print(f"Fetching recent activities (last {days_back} days)...")
        synced_activities = 0
        try:
            raw_activities = self.client.get_activities(0, min(50, days_back * 4))
            parsed_acts: List[Activity] = []

            for raw in raw_activities:
                start_str = raw.get("startTimeLocal") or raw.get("startTimeGMT")
                if not start_str:
                    continue
                start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00")).replace(tzinfo=None)
                if (datetime.now() - start_dt).days > days_back:
                    continue

                act_id = str(raw.get("activityId", ""))
                type_key = raw.get("activityType", {}).get("typeKey", "running")
                sport_type = normalize_sport_type(type_key)
                name = raw.get("activityName") or "Garmin Activity"
                dur = float(raw.get("duration", 0.0) or 0.0)
                dist = float(raw.get("distance", 0.0) or 0.0)
                avg_speed = float(raw.get("averageSpeed", 0.0) or 0.0)
                pace = (1000.0 / avg_speed) if avg_speed > 0 else None

                act = Activity(
                    id=f"garmin_{act_id}",
                    source="garmin",
                    source_id=act_id,
                    start_time=start_dt,
                    sport_type=sport_type,
                    title=name,
                    duration_seconds=dur,
                    moving_time_seconds=float(raw.get("movingDuration", dur) or dur),
                    distance_meters=dist,
                    elevation_gain_m=float(raw.get("elevationGain", 0.0) or 0.0),
                    elevation_loss_m=float(raw.get("elevationLoss", 0.0) or 0.0),
                    avg_hr=float(raw.get("averageHR")) if raw.get("averageHR") else None,
                    max_hr=float(raw.get("maxHR")) if raw.get("maxHR") else None,
                    avg_pace_sec_km=pace,
                    avg_cadence=float(raw.get("averageRunningCadenceInStepsPerMinute")) if raw.get("averageRunningCadenceInStepsPerMinute") else None,
                    max_cadence=float(raw.get("maxRunningCadenceInStepsPerMinute")) if raw.get("maxRunningCadenceInStepsPerMinute") else None,
                    avg_power_watts=float(raw.get("avgPower")) if raw.get("avgPower") else None,
                    calories=float(raw.get("calories")) if raw.get("calories") else None,
                    aerobic_te=float(raw.get("aerobicTrainingEffect")) if raw.get("aerobicTrainingEffect") else None,
                    anaerobic_te=float(raw.get("anaerobicTrainingEffect")) if raw.get("anaerobicTrainingEffect") else None,
                    temperature_c=float(raw.get("minTemperature")) if raw.get("minTemperature") else None,
                    raw_data=raw,
                )

                # Compute TRIMP, TSS, and efficiency factor
                act = compute_activity_load(act, user_profile)
                act.efficiency_factor = RunningMetricsCalculator.calculate_efficiency_factor(act)
                parsed_acts.append(act)

            if parsed_acts:
                db.bulk_save_activities(parsed_acts)
                synced_activities = len(parsed_acts)
                print(f"Saved {synced_activities} activities to database.")
        except Exception as e:
            print(f"Error fetching activities: {e}")

        # 2. Fetch & Parse Daily Health & Sleep Telemetry
        print(f"Fetching daily health and sleep data...")
        health_records: List[Dict[str, Any]] = []
        today = date.today()

        for d_offset in range(days_back + 1):
            curr_d = today - timedelta(days=d_offset)
            d_str = curr_d.isoformat()
            record: Dict[str, Any] = {"date": curr_d}

            # Sleep
            try:
                sleep_raw = self.client.get_sleep_data(d_str)
                dto = sleep_raw.get("dailySleepDTO") or {}
                if dto:
                    record["sleep_duration_seconds"] = float(dto.get("sleepTimeSeconds") or 0.0)
                    record["deep_sleep_seconds"] = float(dto.get("deepSleepSeconds") or 0.0)
                    record["light_sleep_seconds"] = float(dto.get("lightSleepSeconds") or 0.0)
                    record["rem_sleep_seconds"] = float(dto.get("remSleepSeconds") or 0.0)
                    scores = sleep_raw.get("sleepScores") or {}
                    if scores.get("overall", {}).get("value"):
                        record["sleep_score"] = float(scores["overall"]["value"])
            except Exception:
                pass

            # RHR & Summary
            try:
                summary = self.client.get_user_summary(d_str)
                if summary:
                    record["resting_hr"] = float(summary.get("restingHeartRate") or 0.0) or None
                    record["hr_min"] = float(summary.get("minHeartRate") or 0.0) or None
                    record["hr_max"] = float(summary.get("maxHeartRate") or 0.0) or None
                    record["stress_avg"] = float(summary.get("averageStressLevel") or 0.0) or None
                    record["steps"] = int(summary.get("totalSteps") or 0) or None
                    record["calories_total"] = float(summary.get("totalKilocalories") or 0.0) or None
            except Exception:
                pass

            if any(k in record and record[k] is not None for k in ["resting_hr", "sleep_duration_seconds", "steps"]):
                health_records.append(record)

        synced_health = 0
        if health_records:
            # Auto-calculate any missing sleep scores
            health_records = SleepScoreCalculator.calculate_records(health_records, overwrite_existing=False)
            db.save_daily_health_records(health_records)
            synced_health = len(health_records)
            print(f"Saved {synced_health} days of health telemetry.")

        # 3. Recalculate Continuous Daily Load & PMC Corridor
        print("Recomputing chronic training loads (CTL, ATL, TSB)...")
        all_acts = db.get_all_activities()
        if all_acts:
            daily_loads = TrainingLoadEngine.compute_continuous_pmc(all_acts)
            db.save_daily_metrics(daily_loads)
            print("Training loads and PMC corridor updated successfully.")

        return {"activities": synced_activities, "health_days": synced_health}


if __name__ == "__main__":
    email = os.environ.get("GARMIN_EMAIL")
    password = os.environ.get("GARMIN_PASSWORD")
    if not email or not password:
        print("Usage: Set GARMIN_EMAIL and GARMIN_PASSWORD environment variables.")
        sys.exit(1)

    syncer = GarminCloudSync(email, password)
    res = syncer.sync(days_back=14)
    print(f"Sync complete: {res['activities']} activities, {res['health_days']} health days.")
