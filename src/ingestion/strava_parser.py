"""
Parser for Strava Activity Archive CSV exports.
"""
import io
import re
from datetime import datetime
from typing import List, Union, Optional, Any
import pandas as pd

from src.models.activity import Activity
from src.ingestion.garmin_parser import (
    parse_duration_to_seconds,
    parse_clean_float,
    normalize_sport_type,
    parse_datetime,
)


def speed_to_pace_sec_km(speed_m_s: Optional[float]) -> Optional[float]:
    """Converts speed in meters/second to seconds per kilometer."""
    if speed_m_s is None or speed_m_s <= 0.2:
        return None
    return 1000.0 / speed_m_s


class StravaCSVParser:
    """Parser for Strava export CSV files."""

    @staticmethod
    def parse(file_content: Union[str, bytes, io.StringIO, io.BytesIO]) -> List[Activity]:
        """Parses Strava CSV content into a list of Activity objects."""
        if isinstance(file_content, bytes):
            try:
                text = file_content.decode("utf-8")
            except UnicodeDecodeError:
                text = file_content.decode("latin-1")
            df = pd.read_csv(io.StringIO(text))
        elif isinstance(file_content, str):
            df = pd.read_csv(io.StringIO(file_content))
        elif isinstance(file_content, io.BytesIO):
            try:
                text = file_content.read().decode("utf-8")
            except UnicodeDecodeError:
                file_content.seek(0)
                text = file_content.read().decode("latin-1")
            df = pd.read_csv(io.StringIO(text))
        else:
            df = pd.read_csv(file_content)

        col_map = {c: c.strip().lower() for c in df.columns}
        df_norm = df.rename(columns=col_map)

        activities: List[Activity] = []

        for _, row in df_norm.iterrows():
            try:
                sport_raw = StravaCSVParser._get_val(row, ["activity type", "type", "sport"])
                sport_type = normalize_sport_type(sport_raw or "run")

                date_val = StravaCSVParser._get_val(row, ["activity date", "date", "start time", "start_date"])
                start_time = parse_datetime(date_val)

                title = StravaCSVParser._get_val(row, ["activity name", "name", "title"]) or f"Strava {sport_type.capitalize()}"

                # Strava distances are usually in meters (e.g. 10245.5) or km (e.g. 10.2)
                dist_raw = parse_clean_float(StravaCSVParser._get_val(row, ["distance", "total distance", "dist"]))
                if dist_raw is not None:
                    # If distance is < 100, it's in km/miles, else meters
                    distance_meters = dist_raw if dist_raw > 100 else dist_raw * 1000.0
                else:
                    distance_meters = 0.0

                elapsed_time_raw = StravaCSVParser._get_val(row, ["elapsed time", "time", "duration"])
                duration_seconds = parse_duration_to_seconds(elapsed_time_raw)

                moving_time_raw = StravaCSVParser._get_val(row, ["moving time", "moving_time"])
                moving_time_seconds = parse_duration_to_seconds(moving_time_raw) if moving_time_raw else duration_seconds

                # Speed & Pace
                avg_speed_raw = parse_clean_float(StravaCSVParser._get_val(row, ["average speed", "avg speed", "speed"]))
                max_speed_raw = parse_clean_float(StravaCSVParser._get_val(row, ["max speed", "maximum speed"]))

                avg_pace = None
                if avg_speed_raw and avg_speed_raw > 0:
                    # If average speed > 50, it's already pace in sec/km, else if > 15 it might be km/h, else m/s
                    if avg_speed_raw > 100:
                        avg_pace = avg_speed_raw
                    elif avg_speed_raw > 15:  # km/h
                        avg_pace = 3600.0 / avg_speed_raw
                    else:  # m/s
                        avg_pace = speed_to_pace_sec_km(avg_speed_raw)
                elif distance_meters > 0 and moving_time_seconds > 0:
                    avg_pace = (moving_time_seconds / distance_meters) * 1000.0

                best_pace = None
                if max_speed_raw and max_speed_raw > 0:
                    if max_speed_raw > 100:
                        best_pace = max_speed_raw
                    elif max_speed_raw > 15:
                        best_pace = 3600.0 / max_speed_raw
                    else:
                        best_pace = speed_to_pace_sec_km(max_speed_raw)

                avg_hr = parse_clean_float(StravaCSVParser._get_val(row, ["average heart rate", "avg hr", "avg heart rate", "heart rate"]))
                max_hr = parse_clean_float(StravaCSVParser._get_val(row, ["max heart rate", "max hr", "maximum heart rate"]))

                cadence_raw = parse_clean_float(StravaCSVParser._get_val(row, ["average cadence", "avg cadence", "cadence"]))
                avg_cadence = None
                if cadence_raw:
                    # In Strava, run cadence is often RPM (one leg, e.g. 85-90) -> double to SPM (170-180)
                    avg_cadence = cadence_raw * 2 if cadence_raw < 120 else cadence_raw

                elev_gain = parse_clean_float(StravaCSVParser._get_val(row, ["elevation gain", "total ascent", "gain"])) or 0.0
                elev_loss = parse_clean_float(StravaCSVParser._get_val(row, ["elevation loss", "total descent", "loss"])) or 0.0
                avg_power = parse_clean_float(StravaCSVParser._get_val(row, ["average watts", "avg power", "watts", "power"]))
                calories = parse_clean_float(StravaCSVParser._get_val(row, ["calories", "kcal"]))
                relative_effort = parse_clean_float(StravaCSVParser._get_val(row, ["relative effort", "suffer score", "relative_effort"]))
                perceived_exertion = parse_clean_float(StravaCSVParser._get_val(row, ["perceived exertion", "rpe"]))
                notes = StravaCSVParser._get_val(row, ["activity description", "description", "notes"])

                source_id = str(StravaCSVParser._get_val(row, ["activity id", "id"]) or "")
                fingerprint = Activity.generate_fingerprint_id(start_time, distance_meters, duration_seconds)

                act = Activity(
                    id=f"strava_{fingerprint}",
                    source="strava",
                    source_id=source_id,
                    start_time=start_time,
                    sport_type=sport_type,
                    title=str(title),
                    duration_seconds=duration_seconds,
                    moving_time_seconds=moving_time_seconds,
                    distance_meters=distance_meters,
                    elevation_gain_m=elev_gain,
                    elevation_loss_m=elev_loss,
                    avg_hr=avg_hr,
                    max_hr=max_hr,
                    avg_pace_sec_km=avg_pace,
                    best_pace_sec_km=best_pace,
                    avg_cadence=avg_cadence,
                    avg_power_watts=avg_power,
                    calories=calories,
                    trimp=relative_effort,
                    rpe=int(perceived_exertion) if perceived_exertion else None,
                    notes=str(notes) if notes and pd.notna(notes) else None,
                    raw_data={k: v for k, v in row.to_dict().items() if pd.notna(v)},
                )
                activities.append(act)
            except Exception:
                continue

        return activities

    @staticmethod
    def _get_val(row: pd.Series, possible_keys: List[str]) -> Any:
        for k in possible_keys:
            if k in row.index and pd.notna(row[k]):
                return row[k]
        return None
