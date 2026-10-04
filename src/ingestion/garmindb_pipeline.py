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
from src.analytics.sleep_score import SleepScoreCalculator

DEFAULT_GARMIDB_DIR = os.path.expanduser(r"~\HealthData\DBs")


class GarminDbPipeline:
    """Ingests and synchronizes data directly from local GarminDb SQLite databases."""

    @classmethod
    def get_raw_running_activities(cls, db_dir: Optional[str] = None) -> List[Activity]:
        """Return only raw Garmin running records for load-model parity.

        This deliberately bypasses the dashboard's canonical/deduplicated
        store. It is used for CTL, ATL, and TSB so those metrics are based on
        the same GarminDB records as the standalone Garmin report.
        """
        target_dir = db_dir or DEFAULT_GARMIDB_DIR
        act_db_path = os.path.join(target_dir, "garmin_activities.db")
        if not os.path.exists(act_db_path):
            return []

        activities, _ = cls._extract_activities(act_db_path)
        return [activity for activity in activities if activity.sport_type == "run"]

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

        # 6. Update Athlete Profile with latest Resting HR & Weight (controlled by update_profile_baselines)
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
    def get_connected_devices(cls, db_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns detected Garmin hardware devices."""
        target_dir = db_dir or DEFAULT_GARMIDB_DIR
        garmin_db_path = os.path.join(target_dir, "garmin.db")
        devices: List[Dict[str, Any]] = []
        if os.path.exists(garmin_db_path):
            try:
                with sqlite3.connect(garmin_db_path) as conn:
                    cur = conn.cursor()
                    cur.execute("PRAGMA table_info(devices)")
                    d_cols = {col[1] for col in cur.fetchall()}
                    if "product" in d_cols and "serial_number" in d_cols:
                        cur.execute("SELECT DISTINCT serial_number, product, manufacturer, device_type FROM devices WHERE device_type='fitness_tracker' OR product LIKE '%fenix%' OR product LIKE '%forerunner%'")
                        for sn, prod, mfr, dt in cur.fetchall():
                            clean_prod = str(prod).replace("_", " ")
                            devices.append({
                                "serial_number": str(sn),
                                "product": clean_prod,
                                "manufacturer": mfr or "Garmin",
                                "type": dt,
                                "is_active": "fenix" in clean_prod.lower(),
                            })
            except Exception:
                pass
        if not devices:
            devices = [
                {"serial_number": "3485435196", "product": "Fenix 7", "manufacturer": "Garmin", "type": "fitness_tracker", "is_active": True},
                {"serial_number": "3323545606", "product": "Forerunner 935", "manufacturer": "Garmin", "type": "fitness_tracker", "is_active": False},
            ]
        return devices

    @classmethod
    def _extract_activities(cls, act_db_path: str) -> Tuple[List[Activity], int]:
        """Extracts and standardizes activities from garmin_activities.db."""
        activities: List[Activity] = []
        total_laps = 0

        with sqlite3.connect(act_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Detect available columns
            cur.execute("PRAGMA table_info(activities)")
            act_cols = {col["name"] for col in cur.fetchall()}
            cur.execute("PRAGMA table_info(steps_activities)")
            steps_cols = {col["name"] for col in cur.fetchall()}

            # Device mapping
            device_by_act: Dict[str, str] = {}
            try:
                cur.execute("PRAGMA table_info(activities_devices)")
                if cur.fetchall():
                    cur.execute("SELECT activity_id, device_serial_number FROM activities_devices")
                    for aid, ds in cur.fetchall():
                        ds_str = str(ds)
                        if ds_str.startswith("3485435196"):
                            device_by_act[str(aid)] = "Garmin Fenix 7"
                        elif ds_str.startswith("3323545606"):
                            device_by_act[str(aid)] = "Garmin Forerunner 935"
            except Exception:
                pass

            load_col = "a.training_load" if "training_load" in act_cols else "NULL as training_load"
            hrz1_col = "a.hrz_1_time" if "hrz_1_time" in act_cols else "NULL as hrz_1_time"
            hrz2_col = "a.hrz_2_time" if "hrz_2_time" in act_cols else "NULL as hrz_2_time"
            hrz3_col = "a.hrz_3_time" if "hrz_3_time" in act_cols else "NULL as hrz_3_time"
            hrz4_col = "a.hrz_4_time" if "hrz_4_time" in act_cols else "NULL as hrz_4_time"
            hrz5_col = "a.hrz_5_time" if "hrz_5_time" in act_cols else "NULL as hrz_5_time"
            avg_rr_col = "a.avg_rr" if "avg_rr" in act_cols else "NULL as avg_rr"
            vert_osc_col = "s.avg_vertical_oscillation" if "avg_vertical_oscillation" in steps_cols else "NULL as avg_vertical_oscillation"

            sql = f"""
            SELECT 
                a.activity_id, a.name, a.description, a.sport, a.sub_sport,
                a.start_time, a.stop_time, a.elapsed_time, a.moving_time,
                a.distance, a.avg_hr, a.max_hr, a.calories, a.avg_cadence, a.max_cadence,
                a.avg_speed, a.max_speed, a.ascent, a.descent, a.training_effect,
                a.anaerobic_training_effect, a.avg_temperature,
                {load_col}, {hrz1_col}, {hrz2_col}, {hrz3_col}, {hrz4_col}, {hrz5_col}, {avg_rr_col},
                s.avg_pace, s.avg_moving_pace, s.max_pace, s.avg_steps_per_min,
                s.max_steps_per_min, s.avg_step_length, s.avg_vertical_ratio,
                {vert_osc_col}, s.avg_ground_contact_time, s.vo2_max
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
                title = r["name"] or ""
                sport_type = normalize_sport_type(r["sport"] or "running", title)
                if not title:
                    title = f"Garmin {sport_type.capitalize()}"

                # Distance in GarminDb is in km
                dist_km = float(r["distance"] or 0.0)
                distance_meters = dist_km * 1000.0

                duration_seconds = parse_duration_to_seconds(r["elapsed_time"])
                moving_time_seconds = parse_duration_to_seconds(r["moving_time"]) or duration_seconds

                avg_speed_kmh = float(r["avg_speed"] or 0.0)
                avg_pace_sec_km = (3600.0 / avg_speed_kmh) if avg_speed_kmh > 0 else parse_pace_to_sec_km(r["avg_pace"])
                if not avg_pace_sec_km and distance_meters > 0 and moving_time_seconds > 0:
                    avg_pace_sec_km = (moving_time_seconds / distance_meters) * 1000.0

                max_speed_kmh = float(r["max_speed"] or 0.0)
                best_pace_sec_km = (3600.0 / max_speed_kmh) if max_speed_kmh > 0 else parse_pace_to_sec_km(r["max_pace"])

                # Cadence
                cad_raw = r["avg_steps_per_min"] or r["avg_cadence"]
                avg_cadence = None
                if cad_raw:
                    avg_cadence = float(cad_raw * 2 if cad_raw < 120 else cad_raw)

                max_cad_raw = r["max_steps_per_min"] or r["max_cadence"]
                max_cadence = float(max_cad_raw * 2 if max_cad_raw and max_cad_raw < 120 else max_cad_raw) if max_cad_raw else None

                gct_sec = parse_duration_to_seconds(r["avg_ground_contact_time"])
                gct_ms = gct_sec * 1000.0 if gct_sec > 0 else None

                act_laps = laps_by_act.get(act_id, [])

                # Fenix 7 specific metrics
                training_load_val = float(r["training_load"]) if r["training_load"] is not None else None
                vert_osc_val = float(r["avg_vertical_oscillation"]) if r["avg_vertical_oscillation"] is not None else None
                hrz1_sec = parse_duration_to_seconds(r["hrz_1_time"])
                hrz2_sec = parse_duration_to_seconds(r["hrz_2_time"])
                hrz3_sec = parse_duration_to_seconds(r["hrz_3_time"])
                hrz4_sec = parse_duration_to_seconds(r["hrz_4_time"])
                hrz5_sec = parse_duration_to_seconds(r["hrz_5_time"])
                avg_rr_val = float(r["avg_rr"]) if r["avg_rr"] is not None else None

                dev_name = device_by_act.get(act_id)
                if not dev_name:
                    if training_load_val is not None or (hrz1_sec and hrz1_sec > 0):
                        dev_name = "Garmin Fenix 7"
                    else:
                        dev_name = "Garmin Forerunner 935"

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
                    garmin_training_load=training_load_val,
                    vertical_oscillation_mm=vert_osc_val,
                    hrz_1_seconds=hrz1_sec,
                    hrz_2_seconds=hrz2_sec,
                    hrz_3_seconds=hrz3_sec,
                    hrz_4_seconds=hrz4_sec,
                    hrz_5_seconds=hrz5_sec,
                    avg_respiration_rate=avg_rr_val,
                    device_name=dev_name,
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
        """Extracts and aggregates daily health metrics from garmin.db and garmin_monitoring.db."""
        records_by_date: Dict[date, Dict[str, Any]] = {}

        with sqlite3.connect(garmin_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # 1. Resting HR
            cur.execute("PRAGMA table_info(resting_hr)")
            if cur.fetchall():
                cur.execute("SELECT day, resting_heart_rate FROM resting_hr ORDER BY day ASC")
                for r in cur.fetchall():
                    d = parse_datetime(r["day"]).date()
                    if d not in records_by_date:
                        records_by_date[d] = {"date": d}
                    records_by_date[d]["resting_hr"] = r["resting_heart_rate"]

            # 2. Sleep
            cur.execute("PRAGMA table_info(sleep)")
            sleep_cols = {col["name"] for col in cur.fetchall()}
            start_sel = "start" if "start" in sleep_cols else "NULL as start"
            stop_sel = "stop" if "stop" in sleep_cols else "NULL as stop"
            spo2_sel = "avg_spo2" if "avg_spo2" in sleep_cols else "NULL as avg_spo2"
            rr_sel = "avg_rr" if "avg_rr" in sleep_cols else "NULL as avg_rr"
            stress_sel = "avg_stress" if "avg_stress" in sleep_cols else "NULL as avg_stress"
            qual_sel = "qualifier" if "qualifier" in sleep_cols else "NULL as qualifier"

            cur.execute(f"SELECT day, total_sleep, deep_sleep, light_sleep, rem_sleep, score, {start_sel}, {stop_sel}, {spo2_sel}, {rr_sel}, {stress_sel}, {qual_sel} FROM sleep ORDER BY day ASC")
            for r in cur.fetchall():
                d = parse_datetime(r["day"]).date()
                if d not in records_by_date:
                    records_by_date[d] = {"date": d}
                records_by_date[d]["sleep_duration_seconds"] = parse_duration_to_seconds(r["total_sleep"])
                records_by_date[d]["deep_sleep_seconds"] = parse_duration_to_seconds(r["deep_sleep"])
                records_by_date[d]["light_sleep_seconds"] = parse_duration_to_seconds(r["light_sleep"])
                records_by_date[d]["rem_sleep_seconds"] = parse_duration_to_seconds(r["rem_sleep"])
                records_by_date[d]["sleep_score"] = float(r["score"]) if r["score"] is not None else None
                if r["start"] is not None:
                    records_by_date[d]["sleep_start"] = str(r["start"])
                if r["stop"] is not None:
                    records_by_date[d]["sleep_end"] = str(r["stop"])
                if r["avg_spo2"] is not None:
                    records_by_date[d]["sleep_spo2_avg"] = float(r["avg_spo2"])
                if r["avg_rr"] is not None:
                    records_by_date[d]["sleep_rr_avg"] = float(r["avg_rr"])
                if r["avg_stress"] is not None:
                    records_by_date[d]["sleep_stress_avg"] = float(r["avg_stress"])
                if r["qualifier"] is not None:
                    records_by_date[d]["sleep_qualifier"] = str(r["qualifier"])

            # 3. Daily Summary (HR min/max, stress, steps, calories, body battery, spo2, waking respiration, floors)
            cur.execute("PRAGMA table_info(daily_summary)")
            ds_cols = {col["name"] for col in cur.fetchall()}
            bb_charged_sel = "bb_charged" if "bb_charged" in ds_cols else "NULL as bb_charged"
            bb_max_sel = "bb_max" if "bb_max" in ds_cols else "NULL as bb_max"
            bb_min_sel = "bb_min" if "bb_min" in ds_cols else "NULL as bb_min"
            spo2_avg_sel = "spo2_avg" if "spo2_avg" in ds_cols else "NULL as spo2_avg"
            spo2_min_sel = "spo2_min" if "spo2_min" in ds_cols else "NULL as spo2_min"
            rr_waking_sel = "rr_waking_avg" if "rr_waking_avg" in ds_cols else "NULL as rr_waking_avg"
            floors_sel = "floors_up" if "floors_up" in ds_cols else "NULL as floors_up"

            cur.execute(f"""
                SELECT day, hr_min, hr_max, rhr, stress_avg, steps, calories_total,
                       {bb_charged_sel}, {bb_max_sel}, {bb_min_sel},
                       {spo2_avg_sel}, {spo2_min_sel}, {rr_waking_sel}, {floors_sel}
                FROM daily_summary ORDER BY day ASC
            """)
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
                if r["bb_charged"] is not None:
                    records_by_date[d]["body_battery_charged"] = int(r["bb_charged"])
                if r["bb_max"] is not None:
                    records_by_date[d]["body_battery_max"] = int(r["bb_max"])
                if r["bb_min"] is not None:
                    records_by_date[d]["body_battery_min"] = int(r["bb_min"])
                if r["spo2_avg"] is not None:
                    records_by_date[d]["spo2_avg"] = float(r["spo2_avg"])
                if r["spo2_min"] is not None:
                    records_by_date[d]["spo2_min"] = float(r["spo2_min"])
                if r["rr_waking_avg"] is not None:
                    records_by_date[d]["rr_waking_avg"] = float(r["rr_waking_avg"])
                if r["floors_up"] is not None:
                    records_by_date[d]["floors_climbed"] = float(r["floors_up"])

            # 4. Weight
            cur.execute("PRAGMA table_info(weight)")
            if cur.fetchall():
                cur.execute("SELECT day, weight FROM weight ORDER BY day ASC")
                for r in cur.fetchall():
                    d = parse_datetime(r["day"]).date()
                    if d not in records_by_date:
                        records_by_date[d] = {"date": d}
                    records_by_date[d]["weight_kg"] = float(r["weight"]) if r["weight"] is not None else None

        # 5. Extract Overnight HRV from garmin_monitoring.db
        monitoring_db = os.path.join(os.path.dirname(garmin_db_path), "garmin_monitoring.db")
        if os.path.exists(monitoring_db):
            try:
                with sqlite3.connect(monitoring_db) as mconn:
                    mconn.row_factory = sqlite3.Row
                    mcur = mconn.cursor()
                    mcur.execute("PRAGMA table_info(monitoring_hrv_status)")
                    m_cols = {col["name"] for col in mcur.fetchall()}
                    if "timestamp" in m_cols and "last_night" in m_cols:
                        mcur.execute("""
                            SELECT timestamp, weekly_average, last_night, last_night_average, baseline_low, baseline_high, status 
                            FROM monitoring_hrv_status ORDER BY timestamp ASC
                        """)
                        for mr in mcur.fetchall():
                            d = parse_datetime(mr["timestamp"]).date()
                            if d not in records_by_date:
                                records_by_date[d] = {"date": d}
                            if mr["last_night"] is not None:
                                records_by_date[d]["hrv_last_night"] = float(mr["last_night"])
                            if mr["weekly_average"] is not None:
                                records_by_date[d]["hrv_weekly_avg"] = float(mr["weekly_average"])
                            st_code = mr["status"]
                            status_labels = {0: "Balanced", 1: "Unbalanced", 2: "Low", 3: "Poor"}
                            records_by_date[d]["hrv_status"] = status_labels.get(st_code, "Balanced" if st_code is not None else None)
            except Exception:
                pass

        records = list(records_by_date.values())
        return SleepScoreCalculator.calculate_records(records, overwrite_existing=False)
