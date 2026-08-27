"""
Direct Pipeline for GarminDb SQLite databases (garmin_activities.db, garmin.db, garmin_summary.db).
Extracts activities, second-by-second records, laps, and daily health metrics (RHR, sleep, stress, weight).
"""
import os
import sqlite3
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple

from src.models.activity import Activity
from src.models.user_profile import UserProfile
from src.db.database import DatabaseManager
from src.ingestion.garmin_parser import (
    parse_duration_to_seconds,
    parse_pace_to_sec_km,
    normalize_sport_type,
    parse_datetime,
)
from src.ingestion.deduplicator import ActivityDeduplicator
from src.analytics.training_load import compute_activity_load
from src.analytics.running_metrics import RunningMetricsCalculator

DEFAULT_GARMIDB_DIR = os.path.expanduser(r"~\HealthData\DBs")


class GarminDbPipeline:
    """Ingests and synchronizes data directly from local GarminDb SQLite databases."""

    @classmethod
    def is_garmindb_available(cls, db_dir: Optional[str] = None) -> bool:
        """Checks if GarminDb databases exist in the specified or default directory."""
        target_dir = db_dir or DEFAULT_GARMIDB_DIR
        if not os.path.exists(target_dir):
            return False
        act_db = os.path.join(target_dir, "garmin_activities.db")
        garmin_db = os.path.join(target_dir, "garmin.db")
        return os.path.exists(act_db) or os.path.exists(garmin_db)

    @classmethod
    def get_garmindb_stats(cls, db_dir: Optional[str] = None) -> Dict[str, Any]:
        """Returns summary metadata of available GarminDb databases."""
        target_dir = db_dir or DEFAULT_GARMIDB_DIR
        stats = {
            "available": False,
            "path": target_dir,
            "activity_count": 0,
            "health_days_count": 0,
            "laps_count": 0,
            "latest_activity_date": None,
        }
        if not os.path.exists(target_dir):
            return stats

        act_db = os.path.join(target_dir, "garmin_activities.db")
        if os.path.exists(act_db):
            try:
                with sqlite3.connect(act_db) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT count(*), max(start_time) FROM activities")
                    row = cur.fetchone()
                    stats["activity_count"] = row[0] or 0
                    stats["latest_activity_date"] = row[1]
                    cur.execute("SELECT count(*) FROM activity_laps")
                    stats["laps_count"] = cur.fetchone()[0] or 0
            except Exception:
                pass

        garmin_db = os.path.join(target_dir, "garmin.db")
        if os.path.exists(garmin_db):
            try:
                with sqlite3.connect(garmin_db) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT count(*) FROM resting_hr")
                    stats["health_days_count"] = cur.fetchone()[0] or 0
            except Exception:
                pass

        stats["available"] = (stats["activity_count"] > 0 or stats["health_days_count"] > 0)
        return stats

    @classmethod
    def sync_all(
        cls,
        target_db: DatabaseManager,
        user_profile: UserProfile,
        db_dir: Optional[str] = None,
        update_profile_baselines: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes full synchronization pipeline:
        1. Ingests all activities from garmin_activities.db + steps_activities + laps.
        2. Ingests daily health metrics from garmin.db (resting HR, sleep, stress, weight).
        3. Enriches activities with TRIMP, rTSS, VDOT, EF, Decoupling.
        4. Deduplicates against existing activities in target database.
        5. Saves activities & daily health metrics to database.
        6. Updates athlete profile physiological baselines (resting HR & weight).
        """
        target_dir = db_dir or DEFAULT_GARMIDB_DIR
        if not os.path.exists(target_dir):
            raise FileNotFoundError(f"GarminDb folder not found at: {target_dir}")

        act_db_path = os.path.join(target_dir, "garmin_activities.db")
        garmin_db_path = os.path.join(target_dir, "garmin.db")

        parsed_activities: List[Activity] = []
        health_records: List[Dict[str, Any]] = []
        laps_total = 0

        # 1. Parse Activities from garmin_activities.db
        if os.path.exists(act_db_path):
            parsed_activities, laps_total = cls._extract_activities(act_db_path)

        # 2. Parse Health Metrics from garmin.db
        if os.path.exists(garmin_db_path):
            health_records = cls._extract_daily_health(garmin_db_path)

        # 3. Enrich Activities with Physiological Metrics
        enriched_acts = []
        for act in parsed_activities:
            act = compute_activity_load(act, user_profile)
            enriched_acts.append(act)
        enriched_acts = RunningMetricsCalculator.enrich_activities(enriched_acts, user_profile)

        # 4. Deduplicate against existing DB activities
        existing_acts = target_db.get_all_activities()
        deduped_acts, dedup_stats = ActivityDeduplicator.deduplicate_list(enriched_acts, existing_acts)

        # 5. Bulk Save to Target Database
        saved_acts_count = target_db.bulk_save_activities(deduped_acts)
        saved_health_count = target_db.save_daily_health_records(health_records)

        # 6. Update Athlete Profile with latest Resting HR & Weight
        updated_rhr = None
        updated_weight = None
        if update_profile_baselines and health_records:
            recent_rhrs = [r["resting_hr"] for r in health_records[-30:] if r.get("resting_hr") and r["resting_hr"] > 30]
            if recent_rhrs:
                updated_rhr = int(round(sum(recent_rhrs) / len(recent_rhrs)))
                user_profile.resting_hr = updated_rhr

            recent_weights = [r["weight_kg"] for r in health_records if r.get("weight_kg") and r["weight_kg"] > 30]
            if recent_weights:
                updated_weight = float(recent_weights[-1])
                user_profile.weight_kg = updated_weight

            target_db.save_user_profile(user_profile)

        return {
            "status": "success",
            "activities_extracted": len(parsed_activities),
            "activities_canonical_saved": saved_acts_count,
            "health_days_saved": saved_health_count,
            "laps_processed": laps_total,
            "duplicates_merged": dedup_stats["merged_count"],
            "updated_resting_hr": updated_rhr,
            "updated_weight_kg": updated_weight,
        }

    @classmethod
    def _extract_activities(cls, act_db_path: str) -> Tuple[List[Activity], int]:
        """Extracts and standardizes activities from garmin_activities.db."""
        activities: List[Activity] = []
        total_laps = 0

        with sqlite3.connect(act_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Query activities joined with steps_activities
            sql = """
            SELECT 
                a.activity_id, a.name, a.description, a.sport, a.sub_sport,
                a.start_time, a.stop_time, a.elapsed_time, a.moving_time,
                a.distance, a.avg_hr, a.max_hr, a.calories, a.avg_cadence, a.max_cadence,
                a.avg_speed, a.max_speed, a.ascent, a.descent, a.training_effect,
                a.anaerobic_training_effect, a.avg_temperature,
                s.avg_pace, s.avg_moving_pace, s.max_pace, s.avg_steps_per_min,
                s.max_steps_per_min, s.avg_step_length, s.avg_vertical_ratio,
                s.avg_vertical_oscillation, s.avg_ground_contact_time, s.vo2_max
            FROM activities a
            LEFT JOIN steps_activities s ON a.activity_id = s.activity_id
            ORDER BY a.start_time ASC
            """
            cur.execute(sql)
            rows = cur.fetchall()

            # Extract laps grouped by activity_id
            cur.execute("""
                SELECT activity_id, lap, start_time, elapsed_time, moving_time,
                       distance, avg_hr, max_hr, avg_speed, avg_cadence, ascent, descent
                FROM activity_laps
                ORDER BY activity_id, lap ASC
            """)
            lap_rows = cur.fetchall()
            laps_by_act: Dict[str, List[Dict[str, Any]]] = {}
            for lr in lap_rows:
                act_id = str(lr["activity_id"])
                if act_id not in laps_by_act:
                    laps_by_act[act_id] = []
                speed_kmh = float(lr["avg_speed"] or 0.0)
                speed_m_s = (speed_kmh / 3.6) if speed_kmh > 0 else 0.0
                cad = lr["avg_cadence"]
                full_cad = (cad * 2 if cad and cad < 120 else cad)
                laps_by_act[act_id].append({
                    "lap": lr["lap"],
                    "start_time": lr["start_time"],
                    "elapsed_seconds": parse_duration_to_seconds(lr["elapsed_time"]),
                    "distance_meters": float(lr["distance"] or 0.0) * 1000.0,
                    "avg_hr": lr["avg_hr"],
                    "max_hr": lr["max_hr"],
                    "speed_m_s": speed_m_s,
                    "cadence": full_cad,
                    "ascent": lr["ascent"],
                })
                total_laps += 1

            for r in rows:
                act_id = str(r["activity_id"])
                start_dt = parse_datetime(r["start_time"])
                sport_type = normalize_sport_type(r["sport"] or "running")
                title = r["name"] or f"Garmin {sport_type.capitalize()}"

                # Distance in GarminDb is in km
                dist_km = float(r["distance"] or 0.0)
                distance_meters = dist_km * 1000.0

                duration_seconds = parse_duration_to_seconds(r["elapsed_time"])
                moving_time_seconds = parse_duration_to_seconds(r["moving_time"]) or duration_seconds

                # Speed & Pace (avg_speed in GarminDb is km/h)
                avg_speed_kmh = float(r["avg_speed"] or 0.0)
                avg_pace_sec_km = (3600.0 / avg_speed_kmh) if avg_speed_kmh > 0 else parse_pace_to_sec_km(r["avg_pace"])
                if not avg_pace_sec_km and distance_meters > 0 and moving_time_seconds > 0:
                    avg_pace_sec_km = (moving_time_seconds / distance_meters) * 1000.0

                max_speed_kmh = float(r["max_speed"] or 0.0)
                best_pace_sec_km = (3600.0 / max_speed_kmh) if max_speed_kmh > 0 else parse_pace_to_sec_km(r["max_pace"])

                # Cadence (GarminDb activities has single-leg, steps_activities has SPM)
                cad_raw = r["avg_steps_per_min"] or r["avg_cadence"]
                avg_cadence = None
                if cad_raw:
                    avg_cadence = float(cad_raw * 2 if cad_raw < 120 else cad_raw)

                max_cad_raw = r["max_steps_per_min"] or r["max_cadence"]
                max_cadence = float(max_cad_raw * 2 if max_cad_raw and max_cad_raw < 120 else max_cad_raw) if max_cad_raw else None

                gct_sec = parse_duration_to_seconds(r["avg_ground_contact_time"])
                gct_ms = gct_sec * 1000.0 if gct_sec > 0 else None

                act_laps = laps_by_act.get(act_id, [])

                act = Activity(
                    id=f"garmin_{act_id}",
                    source="garmin",
                    source_id=act_id,
                    start_time=start_dt,
                    sport_type=sport_type,
                    title=title,
                    duration_seconds=duration_seconds,
                    moving_time_seconds=moving_time_seconds,
                    distance_meters=distance_meters,
                    elevation_gain_m=float(r["ascent"] or 0.0),
                    elevation_loss_m=float(r["descent"] or 0.0),
                    avg_hr=float(r["avg_hr"]) if r["avg_hr"] is not None else None,
                    max_hr=float(r["max_hr"]) if r["max_hr"] is not None else None,
                    avg_pace_sec_km=avg_pace_sec_km,
                    best_pace_sec_km=best_pace_sec_km,
                    avg_cadence=avg_cadence,
                    max_cadence=max_cadence,
                    calories=float(r["calories"]) if r["calories"] is not None else None,
                    aerobic_te=float(r["training_effect"]) if r["training_effect"] is not None else None,
                    anaerobic_te=float(r["anaerobic_training_effect"]) if r["anaerobic_training_effect"] is not None else None,
                    stride_length_m=float(r["avg_step_length"]) if r["avg_step_length"] is not None else None,
                    vertical_ratio=float(r["avg_vertical_ratio"]) if r["avg_vertical_ratio"] is not None else None,
                    ground_contact_time_ms=gct_ms,
                    temperature_c=float(r["avg_temperature"]) if r["avg_temperature"] is not None else None,
                    vdot=float(r["vo2_max"]) if r["vo2_max"] is not None else None,
                    raw_data={
                        "garmin_activity_id": act_id,
                        "laps": act_laps,
                        "sub_sport": r["sub_sport"],
                        "description": r["description"],
                    },
                )
                activities.append(act)

        return activities, total_laps

    @classmethod
    def _extract_daily_health(cls, garmin_db_path: str) -> List[Dict[str, Any]]:
        """Extracts and aggregates daily health metrics from garmin.db."""
        records_by_date: Dict[date, Dict[str, Any]] = {}

        with sqlite3.connect(garmin_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # 1. Resting HR
            cur.execute("SELECT day, resting_heart_rate FROM resting_hr ORDER BY day ASC")
            for r in cur.fetchall():
                d = parse_datetime(r["day"]).date()
                if d not in records_by_date:
                    records_by_date[d] = {"date": d}
                records_by_date[d]["resting_hr"] = r["resting_heart_rate"]

            # 2. Sleep
            cur.execute("SELECT day, total_sleep, deep_sleep, light_sleep, rem_sleep, score FROM sleep ORDER BY day ASC")
            for r in cur.fetchall():
                d = parse_datetime(r["day"]).date()
                if d not in records_by_date:
                    records_by_date[d] = {"date": d}
                records_by_date[d]["sleep_duration_seconds"] = parse_duration_to_seconds(r["total_sleep"])
                records_by_date[d]["deep_sleep_seconds"] = parse_duration_to_seconds(r["deep_sleep"])
                records_by_date[d]["light_sleep_seconds"] = parse_duration_to_seconds(r["light_sleep"])
                records_by_date[d]["rem_sleep_seconds"] = parse_duration_to_seconds(r["rem_sleep"])
                records_by_date[d]["sleep_score"] = float(r["score"]) if r["score"] is not None else None

            # 3. Daily Summary (HR min/max, stress, steps, calories)
            cur.execute("SELECT day, hr_min, hr_max, rhr, stress_avg, steps, calories_total FROM daily_summary ORDER BY day ASC")
            for r in cur.fetchall():
                d = parse_datetime(r["day"]).date()
                if d not in records_by_date:
                    records_by_date[d] = {"date": d}
                records_by_date[d]["hr_min"] = float(r["hr_min"]) if r["hr_min"] is not None else None
                records_by_date[d]["hr_max"] = float(r["hr_max"]) if r["hr_max"] is not None else None
                records_by_date[d]["stress_avg"] = float(r["stress_avg"]) if r["stress_avg"] is not None else None
                records_by_date[d]["steps"] = int(r["steps"]) if r["steps"] is not None else None
                records_by_date[d]["calories_total"] = float(r["calories_total"]) if r["calories_total"] is not None else None
                if not records_by_date[d].get("resting_hr") and r["rhr"]:
                    records_by_date[d]["resting_hr"] = float(r["rhr"])

            # 4. Weight
            cur.execute("SELECT day, weight FROM weight ORDER BY day ASC")
            for r in cur.fetchall():
                d = parse_datetime(r["day"]).date()
                if d not in records_by_date:
                    records_by_date[d] = {"date": d}
                records_by_date[d]["weight_kg"] = float(r["weight"]) if r["weight"] is not None else None

        return list(records_by_date.values())
