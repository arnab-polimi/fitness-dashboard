"""
Database access layer supporting SQLite and DuckDB.
"""
import os
import json
import sqlite3
from datetime import datetime, date
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
            intensity_factor, efficiency_factor, aerobic_decoupling, vdot, raw_data
        ) VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?
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
            intensity_factor, efficiency_factor, aerobic_decoupling, vdot, raw_data
        ) VALUES (
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?
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
                raw_json,
            ))

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, rows)
            conn.commit()
            return len(rows)

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

    def save_user_profile(self, profile: UserProfile) -> None:
        """Saves user profile."""
        sql = """
        INSERT OR REPLACE INTO user_profiles (
            user_id, name, gender, age, weight_kg, resting_hr, max_hr,
            lthr, threshold_pace_sec_km, ftp_watts, units,
            target_race_distance_km, target_race_date, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, CURRENT_TIMESTAMP
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
            ))
            conn.commit()

    def get_user_profile(self, user_id: str = "default_user") -> UserProfile:
        """Fetches user profile or returns default."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return UserProfile.from_dict(dict(row))
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
            weight_kg, calories_total
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            ))

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, rows)
            conn.commit()
            return len(rows)

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
