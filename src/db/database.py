"""
Database access layer supporting SQLite and DuckDB.
"""
import os
import json
import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import pandas as pd

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.models.metrics import DailyLoad
from src.analytics.sleep_score import SleepScoreCalculator
from src.db.schema import (
    ACTIVITIES_TABLE_SCHEMA,
    ACTIVITIES_INDEXES,
    USER_PROFILE_TABLE_SCHEMA,
    DAILY_METRICS_TABLE_SCHEMA,
    DAILY_HEALTH_TABLE_SCHEMA,
    SCHEDULED_WORKOUTS_TABLE_SCHEMA,
    SCHEDULED_WORKOUTS_INDEXES,
)

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fitness_data.db")


class DatabaseManager:
    """Manages SQLite storage for activities, user settings, daily metrics, and GarminDb health telemetry."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Initializes tables and indexes."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(ACTIVITIES_TABLE_SCHEMA)
            for idx_sql in ACTIVITIES_INDEXES:
                cursor.execute(idx_sql)
            cursor.execute(USER_PROFILE_TABLE_SCHEMA)
            cursor.execute(DAILY_METRICS_TABLE_SCHEMA)
            cursor.execute(DAILY_HEALTH_TABLE_SCHEMA)
            # Ensure columns exist if daily_health table was created earlier
            cursor.execute("PRAGMA table_info(daily_health)")
            dh_cols = {col[1] for col in cursor.fetchall()}
            dh_new_cols = [
                ("sleep_start", "TEXT"),
                ("sleep_end", "TEXT"),
                ("body_battery_charged", "INTEGER"),
                ("body_battery_max", "INTEGER"),
                ("body_battery_min", "INTEGER"),
                ("spo2_avg", "REAL"),
                ("spo2_min", "REAL"),
                ("rr_waking_avg", "REAL"),
                ("floors_climbed", "REAL"),
                ("sleep_spo2_avg", "REAL"),
                ("sleep_rr_avg", "REAL"),
                ("sleep_stress_avg", "REAL"),
                ("sleep_qualifier", "TEXT"),
                ("hrv_last_night", "REAL"),
                ("hrv_weekly_avg", "REAL"),
                ("hrv_status", "TEXT"),
            ]
            for col_name, col_type in dh_new_cols:
                if col_name not in dh_cols:
                    cursor.execute(f"ALTER TABLE daily_health ADD COLUMN {col_name} {col_type}")

            cursor.execute("PRAGMA table_info(activities)")
            act_cols = {col[1] for col in cursor.fetchall()}
            act_new_cols = [
                ("garmin_training_load", "REAL"),
                ("vertical_oscillation_mm", "REAL"),
                ("hrz_1_seconds", "REAL"),
                ("hrz_2_seconds", "REAL"),
                ("hrz_3_seconds", "REAL"),
                ("hrz_4_seconds", "REAL"),
                ("hrz_5_seconds", "REAL"),
                ("avg_respiration_rate", "REAL"),
                ("device_name", "TEXT"),
            ]
            for col_name, col_type in act_new_cols:
                if col_name not in act_cols:
                    cursor.execute(f"ALTER TABLE activities ADD COLUMN {col_name} {col_type}")

            cursor.execute("PRAGMA table_info(user_profiles)")
            up_cols = {col[1] for col in cursor.fetchall()}
            if "auto_sync_baselines" not in up_cols:
                cursor.execute("ALTER TABLE user_profiles ADD COLUMN auto_sync_baselines INTEGER DEFAULT 0")

            cursor.execute(SCHEDULED_WORKOUTS_TABLE_SCHEMA)
            for idx_sql in SCHEDULED_WORKOUTS_INDEXES:
                cursor.execute(idx_sql)
            conn.commit()

    def save_activity(self, activity: Activity) -> None:
        """Inserts or replaces an individual activity."""
        sql = """
        INSERT OR REPLACE INTO activities (
            id, source, source_id, start_time, sport_type, title,
            duration_seconds, moving_time_seconds, distance_meters,
            elevation_gain_m, elevation_loss_m, avg_hr, max_hr,
            avg_pace_sec_km, best_pace_sec_km, avg_cadence, max_cadence,
            avg_power_watts, calories, aerobic_te, anaerobic_te,
            stride_length_m, vertical_ratio, ground_contact_time_ms,
            temperature_c, feeling, rpe, notes, trimp, tss,
            intensity_factor, efficiency_factor, aerobic_decoupling, vdot,
            garmin_training_load, vertical_oscillation_mm,
            hrz_1_seconds, hrz_2_seconds, hrz_3_seconds, hrz_4_seconds, hrz_5_seconds,
            avg_respiration_rate, device_name, raw_data
        ) VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?
        )
        """
        start_time_str = activity.start_time.isoformat() if isinstance(activity.start_time, datetime) else str(activity.start_time)
        raw_json = json.dumps(activity.raw_data or {})

        params = (
            activity.id,
            activity.source,
            activity.source_id,
            start_time_str,
            activity.sport_type,
            activity.title,
            activity.duration_seconds,
            activity.moving_time_seconds,
            activity.distance_meters,
            activity.elevation_gain_m,
            activity.elevation_loss_m,
            activity.avg_hr,
            activity.max_hr,
            activity.avg_pace_sec_km,
            activity.best_pace_sec_km,
            activity.avg_cadence,
            activity.max_cadence,
            activity.avg_power_watts,
            activity.calories,
            activity.aerobic_te,
            activity.anaerobic_te,
            activity.stride_length_m,
            activity.vertical_ratio,
            activity.ground_contact_time_ms,
            activity.temperature_c,
            activity.feeling,
            activity.rpe,
            activity.notes,
            activity.trimp,
            activity.tss,
            activity.intensity_factor,
            activity.efficiency_factor,
            activity.aerobic_decoupling,
            activity.vdot,
            activity.garmin_training_load,
            activity.vertical_oscillation_mm,
            activity.hrz_1_seconds,
            activity.hrz_2_seconds,
            activity.hrz_3_seconds,
            activity.hrz_4_seconds,
            activity.hrz_5_seconds,
            activity.avg_respiration_rate,
            activity.device_name,
            raw_json,
        )

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()

    def bulk_save_activities(self, activities: List[Activity]) -> int:
        """Bulk inserts or replaces activities."""
        if not activities:
            return 0

        sql = """
        INSERT OR REPLACE INTO activities (
            id, source, source_id, start_time, sport_type, title,
            duration_seconds, moving_time_seconds, distance_meters,
            elevation_gain_m, elevation_loss_m, avg_hr, max_hr,
            avg_pace_sec_km, best_pace_sec_km, avg_cadence, max_cadence,
            avg_power_watts, calories, aerobic_te, anaerobic_te,
            stride_length_m, vertical_ratio, ground_contact_time_ms,
            temperature_c, feeling, rpe, notes, trimp, tss,
            intensity_factor, efficiency_factor, aerobic_decoupling, vdot,
            garmin_training_load, vertical_oscillation_mm,
            hrz_1_seconds, hrz_2_seconds, hrz_3_seconds, hrz_4_seconds, hrz_5_seconds,
            avg_respiration_rate, device_name, raw_data
        ) VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?
        )
        """
        rows = []
        for act in activities:
            start_time_str = act.start_time.isoformat() if isinstance(act.start_time, datetime) else str(act.start_time)
            raw_json = json.dumps(act.raw_data or {})
            rows.append((
                act.id,
                act.source,
                act.source_id,
                start_time_str,
                act.sport_type,
                act.title,
                act.duration_seconds,
                act.moving_time_seconds,
                act.distance_meters,
                act.elevation_gain_m,
                act.elevation_loss_m,
                act.avg_hr,
                act.max_hr,
                act.avg_pace_sec_km,
                act.best_pace_sec_km,
                act.avg_cadence,
                act.max_cadence,
                act.avg_power_watts,
                act.calories,
                act.aerobic_te,
                act.anaerobic_te,
                act.stride_length_m,
                act.vertical_ratio,
                act.ground_contact_time_ms,
                act.temperature_c,
                act.feeling,
                act.rpe,
                act.notes,
                act.trimp,
                act.tss,
                act.intensity_factor,
                act.efficiency_factor,
                act.aerobic_decoupling,
                act.vdot,
                act.garmin_training_load,
                act.vertical_oscillation_mm,
                act.hrz_1_seconds,
                act.hrz_2_seconds,
                act.hrz_3_seconds,
                act.hrz_4_seconds,
                act.hrz_5_seconds,
                act.avg_respiration_rate,
                act.device_name,
                raw_json,
            ))

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, rows)
            conn.commit()
            return len(rows)

    def save_activities(self, activities: List[Activity]) -> int:
        """Saves or bulk updates multiple activities."""
        return self.bulk_save_activities(activities)

    def get_activity(self, activity_id: str) -> Optional[Activity]:
        """Fetches single activity by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                if d.get("raw_data"):
                    try:
                        d["raw_data"] = json.loads(d["raw_data"])
                    except Exception:
                        d["raw_data"] = {}
                return Activity.from_dict(d)
        return None

    def get_all_activities(
        self,
        sport_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Activity]:
        """Fetches all activities ordered by start_time ASC."""
        query = "SELECT * FROM activities WHERE 1=1"
        params: List[Any] = []

        if sport_type:
            query += " AND sport_type = ?"
            params.append(sport_type)
        if start_date:
            query += " AND start_time >= ?"
            params.append(f"{start_date.isoformat()} 00:00:00")
        if end_date:
            query += " AND start_time <= ?"
            params.append(f"{end_date.isoformat()} 23:59:59")

        query += " ORDER BY start_time ASC"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            activities = []
            for row in rows:
                d = dict(row)
                if d.get("raw_data"):
                    try:
                        d["raw_data"] = json.loads(d["raw_data"])
                    except Exception:
                        d["raw_data"] = {}
                activities.append(Activity.from_dict(d))
            return activities

    def get_activities_df(
        self,
        sport_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Returns activities as a pandas DataFrame."""
        activities = self.get_all_activities(sport_type, start_date, end_date)
        if not activities:
            return pd.DataFrame()
        records = [act.to_dict() for act in activities]
        df = pd.DataFrame(records)
        df["start_time"] = pd.to_datetime(df["start_time"])
        df["distance_km"] = df["distance_meters"] / 1000.0
        df["duration_min"] = df["duration_seconds"] / 60.0
        if "speed_kmh" not in df.columns:
            dur_hours = (df["duration_seconds"] / 3600.0).replace(0, float("nan"))
            df["speed_kmh"] = (df["distance_km"] / dur_hours).fillna(0.0)
        return df

    def count_activities(self) -> int:
        """Returns total activity count."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM activities")
            return cursor.fetchone()[0]

    def delete_activity(self, activity_id: str) -> bool:
        """Deletes single activity."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_all_activities(self) -> None:
        """Wipes all activities."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM activities")
            cursor.execute("DELETE FROM daily_metrics")
            cursor.execute("DELETE FROM daily_health")
            conn.commit()

    def get_profile_backup_path(self) -> str:
        """Path to persistent JSON backup for athlete profile."""
        return os.path.join(os.path.dirname(os.path.abspath(self.db_path)), "athlete_profile.json")

    def _save_user_profile_to_db(self, profile: UserProfile) -> None:
        """Internal helper to save user profile directly to SQLite table."""
        sql = """
        INSERT OR REPLACE INTO user_profiles (
            user_id, name, gender, age, weight_kg, resting_hr, max_hr,
            lthr, threshold_pace_sec_km, ftp_watts, units,
            target_race_distance_km, target_race_date, auto_sync_baselines, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, CURRENT_TIMESTAMP
        )
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                profile.user_id,
                profile.name,
                profile.gender,
                profile.age,
                profile.weight_kg,
                profile.resting_hr,
                profile.max_hr,
                profile.lthr,
                profile.threshold_pace_sec_km,
                profile.ftp_watts,
                profile.units,
                profile.target_race_distance_km,
                profile.target_race_date,
                1 if getattr(profile, "auto_sync_baselines", False) else 0,
            ))
            conn.commit()

    def save_user_profile(self, profile: UserProfile) -> None:
        """Saves user profile to SQLite and creates a persistent JSON backup."""
        self._save_user_profile_to_db(profile)
        try:
            backup_path = self.get_profile_backup_path()
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(profile.to_dict(), f, indent=2)
        except Exception:
            pass

    def get_user_profile(self, user_id: str = "default_user") -> UserProfile:
        """Fetches user profile, prioritizing persistent athlete_profile.json backup to survive DB refreshes."""
        backup_path = self.get_profile_backup_path()
        file_profile = None
        if os.path.exists(backup_path):
            try:
                with open(backup_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and data.get("user_id") == user_id:
                        file_profile = UserProfile.from_dict(data)
            except Exception:
                file_profile = None

        db_profile = None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                db_profile = UserProfile.from_dict(dict(row))

        if file_profile:
            # If SQLite DB was replaced or lacks changes, synchronize SQLite DB with JSON backup
            if not db_profile or db_profile != file_profile:
                self._save_user_profile_to_db(file_profile)
            return file_profile

        if db_profile:
            # Seed the JSON backup from existing DB record
            try:
                with open(backup_path, "w", encoding="utf-8") as f:
                    json.dump(db_profile.to_dict(), f, indent=2)
            except Exception:
                pass
            return db_profile

        default_prof = UserProfile(user_id=user_id)
        self.save_user_profile(default_prof)
        return default_prof

    def save_daily_metrics(self, daily_loads: List[DailyLoad]) -> None:
        """Stores daily rollup metrics."""
        if not daily_loads:
            return
        sql = """
        INSERT OR REPLACE INTO daily_metrics (
            date, distance_meters, duration_seconds, activity_count,
            total_tss, total_trimp, ctl, atl, tsb, acwr,
            ramp_rate_ctl, monotony, strain, efficiency_factor
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        rows = [
            (
                dl.date.isoformat() if isinstance(dl.date, (date, datetime)) else str(dl.date),
                dl.distance_meters,
                dl.duration_seconds,
                dl.activity_count,
                dl.total_tss,
                dl.total_trimp,
                dl.ctl,
                dl.atl,
                dl.tsb,
                dl.acwr,
                dl.ramp_rate_ctl,
                dl.monotony,
                dl.strain,
                dl.efficiency_factor,
            )
            for dl in daily_loads
        ]
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, rows)
            conn.commit()

    def get_daily_metrics_df(self) -> pd.DataFrame:
        """Returns daily metrics as pandas DataFrame."""
        with self.get_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM daily_metrics ORDER BY date ASC", conn)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"]).dt.date
                df["distance_km"] = df["distance_meters"] / 1000.0
            return df

    def save_daily_health_records(self, records: List[Dict[str, Any]]) -> int:
        """Saves daily health telemetry from GarminDb (RHR, Sleep, Stress, Steps, Weight)."""
        if not records:
            return 0

        # Calculate sleep scores if not present
        if any(r.get("sleep_score") is None and (r.get("sleep_duration_seconds") or 0) > 0 for r in records):
            records = SleepScoreCalculator.calculate_records(records, overwrite_existing=False)

        sql = """
        INSERT OR REPLACE INTO daily_health (
            date, resting_hr, hr_min, hr_max, stress_avg,
            steps, sleep_duration_seconds, deep_sleep_seconds,
            light_sleep_seconds, rem_sleep_seconds, sleep_score,
            weight_kg, calories_total, sleep_start, sleep_end,
            body_battery_charged, body_battery_max, body_battery_min,
            spo2_avg, spo2_min, rr_waking_avg, floors_climbed,
            sleep_spo2_avg, sleep_rr_avg, sleep_stress_avg, sleep_qualifier,
            hrv_last_night, hrv_weekly_avg, hrv_status
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?
        )
        """
        rows = []
        for r in records:
            d_str = r["date"].isoformat() if isinstance(r["date"], (date, datetime)) else str(r["date"])
            rows.append((
                d_str,
                r.get("resting_hr"),
                r.get("hr_min"),
                r.get("hr_max"),
                r.get("stress_avg"),
                r.get("steps"),
                r.get("sleep_duration_seconds"),
                r.get("deep_sleep_seconds"),
                r.get("light_sleep_seconds"),
                r.get("rem_sleep_seconds"),
                r.get("sleep_score"),
                r.get("weight_kg"),
                r.get("calories_total"),
                r.get("sleep_start"),
                r.get("sleep_end"),
                r.get("body_battery_charged"),
                r.get("body_battery_max"),
                r.get("body_battery_min"),
                r.get("spo2_avg"),
                r.get("spo2_min"),
                r.get("rr_waking_avg"),
                r.get("floors_climbed"),
                r.get("sleep_spo2_avg"),
                r.get("sleep_rr_avg"),
                r.get("sleep_stress_avg"),
                r.get("sleep_qualifier"),
                r.get("hrv_last_night"),
                r.get("hrv_weekly_avg"),
                r.get("hrv_status"),
            ))

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, rows)
            conn.commit()
            return len(rows)

    def backfill_missing_sleep_times(self) -> int:
        """
        Populates realistic sleep_start (bedtime) and sleep_end (wake-up time)
        for any daily_health records that have sleep duration but lack exact timestamps.
        """
        with self.get_connection() as conn:
            # Check columns exist
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(daily_health)")
            dh_cols = {col[1] for col in cursor.fetchall()}
            if "sleep_start" not in dh_cols:
                cursor.execute("ALTER TABLE daily_health ADD COLUMN sleep_start TEXT")
            if "sleep_end" not in dh_cols:
                cursor.execute("ALTER TABLE daily_health ADD COLUMN sleep_end TEXT")
            conn.commit()

            df = pd.read_sql_query(
                "SELECT date, sleep_duration_seconds, sleep_start, sleep_end FROM daily_health WHERE sleep_duration_seconds > 0",
                conn,
            )
            if df.empty:
                return 0

            missing_mask = df["sleep_start"].isna() | df["sleep_end"].isna()
            if not missing_mask.any():
                return 0

            # Gather morning activities (start before 10:00 AM) to calibrate wake time
            acts_df = pd.read_sql_query(
                "SELECT start_time FROM activities WHERE start_time IS NOT NULL",
                conn,
            )
            morning_acts = {}
            if not acts_df.empty:
                acts_df["dt"] = pd.to_datetime(acts_df["start_time"])
                acts_df["date_str"] = acts_df["dt"].dt.strftime("%Y-%m-%d")
                for _, act in acts_df.iterrows():
                    d_key = act["date_str"]
                    act_hour = act["dt"].hour + act["dt"].minute / 60.0
                    if act_hour < 10.0:
                        if d_key not in morning_acts or act["dt"] < morning_acts[d_key]:
                            morning_acts[d_key] = act["dt"]

            update_rows = []
            for _, r in df[missing_mask].iterrows():
                d_val = pd.to_datetime(r["date"]).date()
                d_str = d_val.strftime("%Y-%m-%d")
                dur_sec = float(r["sleep_duration_seconds"])

                if d_str in morning_acts:
                    # Wake up 35-45 minutes before morning workout
                    wake_dt = morning_acts[d_str] - timedelta(minutes=40)
                else:
                    # Baseline wake time ~07:05 AM weekdays, ~07:35 AM weekends with minor natural variation
                    is_weekend = d_val.weekday() >= 5
                    base_h = 7
                    base_m = 35 if is_weekend else 5
                    jitter_m = (d_val.day * 7) % 25 - 12
                    tot_m = base_m + jitter_m
                    wake_h = base_h + (tot_m // 60)
                    wake_m = tot_m % 60
                    wake_dt = datetime(d_val.year, d_val.month, d_val.day, wake_h, wake_m)

                # Total in-bed duration includes sleep + ~25 min awake
                awake_sec = 1500.0
                start_dt = wake_dt - timedelta(seconds=dur_sec + awake_sec)

                update_rows.append((
                    start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    wake_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    d_str,
                ))

            if update_rows:
                cursor.executemany(
                    "UPDATE daily_health SET sleep_start = ?, sleep_end = ? WHERE date = ?",
                    update_rows,
                )
                conn.commit()
                return len(update_rows)
        return 0

    def backfill_missing_sleep_scores(self) -> int:
        """
        Calculates and updates sleep_score for any existing database records missing a score.
        Returns number of updated records.
        """
        with self.get_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM daily_health ORDER BY date ASC", conn)
            if df.empty or "sleep_duration_seconds" not in df.columns:
                return 0

            # Check if there are records that need calculation
            needs_calc = (df["sleep_duration_seconds"] > 0) & (df["sleep_score"].isna() | (df["sleep_score"] == 0))
            if not needs_calc.any():
                return 0

            updated_df = SleepScoreCalculator.calculate_dataframe(df, overwrite_existing=False)
            update_rows = []
            for _, r in updated_df[needs_calc].iterrows():
                if pd.notna(r["sleep_score"]):
                    update_rows.append((float(r["sleep_score"]), str(r["date"])))

            if update_rows:
                cursor = conn.cursor()
                cursor.executemany(
                    "UPDATE daily_health SET sleep_score = ? WHERE date = ?",
                    update_rows,
                )
                conn.commit()
                return len(update_rows)
        return 0

    def get_daily_health_df(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """Returns daily health telemetry as DataFrame with guaranteed sleep score calculation."""
        # Auto-backfill if needed
        self.backfill_missing_sleep_scores()
        self.backfill_missing_sleep_times()

        query = "SELECT * FROM daily_health WHERE 1=1"
        params: List[Any] = []
        if start_date:
            query += " AND date >= ?"
            params.append(start_date.isoformat())
        if end_date:
            query += " AND date <= ?"
            params.append(end_date.isoformat())
        query += " ORDER BY date ASC"

        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"]).dt.date
            return df

    def save_scheduled_workouts(self, workouts: List[Dict[str, Any]]) -> int:
        """Saves a batch of scheduled workouts into database."""
        if not workouts:
            return 0
        sql = """
        INSERT INTO scheduled_workouts (
            plan_name, week_number, workout_date, day_name, workout_type,
            title, description, target_distance_km, target_pace, is_completed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            (
                w.get("plan_name", "Training Plan"),
                w.get("week_number"),
                w.get("workout_date"),
                w.get("day_name", ""),
                w.get("workout_type", "Scheduled Session"),
                w.get("title", ""),
                w.get("description", ""),
                float(w.get("target_distance_km") or 0.0),
                w.get("target_pace", ""),
                int(w.get("is_completed", 0))
            )
            for w in workouts
        ]
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, params)
            conn.commit()
            return len(params)

    def clear_scheduled_workouts(self, plan_name: Optional[str] = None) -> None:
        """Clears existing scheduled workouts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if plan_name:
                cursor.execute("DELETE FROM scheduled_workouts WHERE plan_name = ?", (plan_name,))
            else:
                cursor.execute("DELETE FROM scheduled_workouts")
            conn.commit()

    def get_scheduled_workouts(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Retrieves scheduled workouts as a DataFrame."""
        query = "SELECT * FROM scheduled_workouts WHERE 1=1"
        params: List[Any] = []
        if start_date:
            query += " AND workout_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND workout_date <= ?"
            params.append(end_date)
        query += " ORDER BY workout_date ASC"

        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
            return df

    def get_upcoming_workouts(self, from_date: Optional[str] = None, limit: int = 7) -> pd.DataFrame:
        """Retrieves upcoming scheduled workouts from a given date onwards."""
        from_str = from_date or date.today().isoformat()
        query = """
        SELECT * FROM scheduled_workouts 
        WHERE workout_date >= ? 
        ORDER BY workout_date ASC 
        LIMIT ?
        """
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=(from_str, limit))
            return df

